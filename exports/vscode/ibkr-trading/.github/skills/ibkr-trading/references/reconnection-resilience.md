# Reconnection and Resilience

IBKR connectivity is *scheduled* to break at least once a day (daily reset, nightly Gateway restart; schedules and automation in `gateway-automation.md`), and ib_async **has no built-in auto-reconnect**. Everything below is about surviving that: reconnect correctly, distrust liveness flags, and make sure the recovery layers cannot all lie at once.

## Reconnection Pattern with ib_async

The `disconnectedEvent` handler runs **on the event loop**: it must never call the sync `ib.connect()` or `time.sleep()` (that blocks all message processing, including the reconnect itself). Spawn a task and use the async forms:

```python
import asyncio, logging, random

log = logging.getLogger(__name__)

def on_disconnect():
    log.warning("Disconnected. Scheduling reconnect...")
    asyncio.create_task(reconnect_with_backoff())

async def reconnect_with_backoff(base=2.0, cap=60.0, max_attempts=10):
    for attempt in range(max_attempts):
        try:
            await ib.connectAsync("127.0.0.1", 4002, clientId=1, timeout=10)  # 4002 paper; 4001 is LIVE
            if not ib.isConnected():
                # connectAsync can return without raising while the API
                # channel is half-open (mid-warmup Gateway). Without this,
                # connectedEvent never fires and the supervisor sleeps forever.
                raise RuntimeError("connectAsync returned but isConnected() is False")
            await asyncio.wait_for(ib.reqCurrentTimeAsync(), timeout=10)  # active probe
            await resubscribe_all_data()
            await verify_positions_and_orders()
            return
        except asyncio.CancelledError:
            ib.disconnect()   # tear down the half-open socket or the next
            raise             # start() collides with it (error 326)
        except Exception:
            ib.disconnect()   # reset zombie client state before the next attempt
            delay = min(cap, base * (2 ** attempt))
            delay = delay / 2 + random.uniform(0, delay / 2)   # equal jitter
            log.error(f"Attempt {attempt+1} failed. Retry in {delay:.1f}s")
            await asyncio.sleep(delay)
    log.critical("Reconnect attempts exhausted -- escalating")

ib.disconnectedEvent += on_disconnect
```

Jitter is not decoration: N sibling processes sharing one Gateway land synchronized `connectAsync` waves after a shared drop unless every client randomizes its schedule.

### Post-Reconnection Mandatory Steps

After every reconnection:
1. Call `reqPositions()` to verify positions
2. Call `reqOpenOrders()` for open orders
3. Re-subscribe all market data (especially after error **1101** -- data lost)
4. Call `reqExecutions()` for fills that occurred during disconnection
5. **Clear the qualified-contract cache** -- `conId`s can change across a reconnect (contract roll, paper/live swap, different Gateway); see `venue-boundary-failure-modes.md`
6. Resume strategy logic only after state is verified

These steps are mandatory because the library remembers nothing: ib_async's `Wrapper.reset()` clears
trades, fills, positions, tickers and account state on every disconnect (verified on 2.1.0), so all
post-reconnect knowledge comes from the requests above. Two holes in that recovery are known:
`reqOpenOrders`/`reqAllOpenOrders` do **not** return orders staged with `transmit=False` (observed,
maintainer-confirmed), so staged bracket legs must be reconciled from your own records; and an order
transmitted mid-session after being staged is picked up only after an explicit `reqOpenTrades()`
resync.

## What the terminal itself preserves

Two different outages, two different guarantees:

- **The terminal stays up while IBKR connectivity drops**: with "Maintain and resubmit orders when
  connection is restored" (Global Configuration, API, Settings; enabled by default since TWS/Gateway
  10.28, extended in 10.40 to cover auto-restart), orders received while connectivity is lost are
  saved and resubmitted on restore. Documented caveat: "if the Trader Workstation is closed during
  this time, the orders are deleted regardless of the setting".
- **The terminal itself dies**: orders resting natively at the venue live on server-side; order types
  the terminal simulates locally (stops on venues without native stops, conditionals) have no
  documented survival story across a process crash. Treat a dead Gateway holding simulated stops as
  an unprotected position until measured otherwise; the register in `venue-questions-and-probes.md`
  carries the experiment.

## The `isConnected()` Zombie Blind Spot

**`isConnected()` can lie.** After a *failed* `connectAsync` (typical during a Gateway restart window), the ib_async client can be left in a zombie state where `isConnected()` returns `True` while no socket exists. Every recovery layer that trusts that flag then fails silently and simultaneously:

- A reconnect supervisor whose retry loop is guarded by `if not ib.isConnected(): retry` makes attempt #1, fails, and never attempts again -- the zombie flag says "connected", so the guard exits with **zero log output**.
- A periodic polled fallback that checks the same flag never re-arms the supervisor.
- The process stays alive and healthy-looking for hours while completely disconnected.

**Hardening rules:**

- **Probe, don't trust the flag.** The authoritative liveness check is an active round-trip: `await asyncio.wait_for(ib.reqCurrentTimeAsync(), timeout=10)`. `isConnected()` is at best a fast-path hint, never the gate that decides whether to keep retrying.
- **Defensive `disconnect()` after every failed connect attempt.** It resets the client state so the next attempt starts clean instead of inheriting a half-open zombie.
- **Decorrelate the recovery layers.** If the supervisor, the heartbeat, and the polled fallback all read the same boolean, one lying flag defeats all three at once. At least one layer must be an independent active probe.
- **Escalate on silence.** A reconnect supervisor that stops producing attempt logs is itself a failure mode. Alert when no attempt/success log has appeared within N seconds of a disconnect -- do not rely on the supervisor to report its own death.

```python
async def is_really_connected(ib, timeout=10):
    if not ib.isConnected():          # fast-path hint only
        return False
    try:                              # authoritative active probe
        await asyncio.wait_for(ib.reqCurrentTimeAsync(), timeout=timeout)
        return True
    except (asyncio.TimeoutError, Exception):
        ib.disconnect()               # reset zombie client state
        return False
```

### Forensics: the Gateway log is ground truth

When diagnosing "which client actually reconnected" after a Gateway restart, read the **IB Gateway log**: it records every connection attempt per `clientId` with timestamps. A client with zero attempts in the Gateway log after the restart, whose own process logs nothing either, is the zombie signature. Your own application logs cannot prove the absence of attempts; the Gateway log can.

## Beyond the zombie: the supervisor itself is a failure surface

- **The recovery task can die.** Any exception escaping the reconnect supervisor kills the task with a traceback that reaches local stderr only, turning every future reconnect signal into a no-op. Have an independent long-lived loop (a market-state poller, a heartbeat) call an `ensure_supervisor_alive()` that respawns it when it exited abnormally -- while leaving *deliberate* exits (cancellation, terminal config error) alone.
- **Classify terminal vs retryable.** A missing IBC path or bad credentials must stop the supervisor with a clear error, not retry forever; a refused socket must retry. Retrying the unretryable hides a config error as a connectivity flap.
- **Half-open teardown on cancellation.** If a connect attempt is cancelled mid-handshake, explicitly `disconnect()` before propagating: a lingering Gateway-side session otherwise collides with the next attempt as error 326.
- **`ib_async.ibcontroller.Watchdog` exists** as a packaged alternative: it starts/monitors TWS or Gateway via IBC and exposes lifecycle events (`startingEvent`, `softTimeoutEvent`, `hardTimeoutEvent`, ...). Its own docs warn you should not use it unless you understand exactly what it does and does not do; the failure modes in this file apply to it too.

## Multi-Client State Hygiene (same account, many clientIds)

Several clients on one account are **redundant monitors of the same account-level state**, with one asymmetry: `openOrders` visibility is **per-clientId** (each client sees its own orders unless it binds/requests all). Differing order counts across clients on the same account are visibility, not different accounts.

The dangerous pattern: each client periodically publishes a full account snapshot (positions/orders) to shared state, and the consumer applies **last-writer-wins replace**. A single zombie-disconnected client then publishes *empty* snapshots from its empty local cache and wipes the good data written by healthy clients on every cycle -- a degraded component actively destroying shared state.

- **Health-gate every snapshot publish**: a client that cannot pass the active liveness probe must not publish (especially not an empty snapshot -- "no positions" from a dead client is not information).
- **Fix both sides, not one**: gate the producer *and* teach the consumer to reject snapshots flagged as coming from a disconnected publisher. A single-sided fix leaves the class open (see the producer+consumer rule in `venue-boundary-failure-modes.md`).
- Prefer electing a **single account-state monitor** over N redundant publishers with replace semantics.
- On the consumer side, treat "snapshot suddenly empty while another publisher reports non-empty" as a health signal, not data.

## Reviewing Recovery Paths: the Silent-Failure Signature

Audit every recovery/resilience path (reconnect, failover, fallback, retry) against five traits. A path with several of them will one day fail silently for hours:

1. **Lying health flag** -- the path's gate is a cached boolean (`isConnected()`, `is_healthy`) rather than an active probe.
2. **Correlated trust** -- multiple independent-looking layers all read that same flag, so they fail together.
3. **Swallowed errors** -- exceptions inside handlers/listeners are caught by a framework and logged somewhere your pipeline does not ship (see the eventkit trap in `event-driven-data.md`).
4. **Active harm** -- the degraded component keeps acting (publishing empty snapshots, force-replacing shared state) instead of going quiet.
5. **No escalation** -- nothing alerts when the recovery path itself stops making progress.

Fixing any single trait breaks the chain; fix the flag first (active probes), then the escalation.

## Critical Error Codes

### Connectivity (reqId = -1)

| Code | Meaning | Action |
|------|---------|--------|
| 1100 | Connectivity lost | Enter reconnect mode, halt trading. IBKR's note for this code lists "a competing session" among the causes: if another login took the session, backoff will not fix it |
| 1101 | Connectivity restored, **data lost** | Re-subscribe all market data |
| 1102 | Connectivity restored, data maintained | Resume normal operations |
| 2104/2106/2158 | Data farms connected (informational) | Log and ignore |
| 2103/2105 | Data farms disconnected | Wait, log, and **alert if it persists**: dated operator reports show farm connections that never recover while the socket stays healthy, restored only by a terminal restart. Farm health is a separate signal from socket health |
| 2107/2108 | Data farm **inactive** (dormant) | Documented as "available upon demand": the farm reconnects when the next request arrives. Not an outage; do not alert on it |

Error **502** (couldn't connect) is the immediate symptom of the daily reset window; error **326** (clientId in use) after your own restart usually means a half-open session was left behind. Both scheduled outage windows are listed in `gateway-automation.md`.

### Handling Error Events

```python
def on_error(reqId, errorCode, errorString, contract):
    if errorCode in (1100,):
        log.critical(f"CONNECTIVITY LOST: {errorString}")
        halt_trading()
    elif errorCode == 1101:
        log.warning("Connectivity restored, DATA LOST -- resubscribing")
        resubscribe_all_data()
    elif errorCode == 1102:
        log.info("Connectivity restored, data maintained")
    elif errorCode in (2104, 2106, 2158):
        log.debug(f"Farm connected: {errorString}")
    elif errorCode in (2103, 2105):
        log.warning(f"Farm disconnected: {errorString}")
    elif errorCode == 201:
        log.error(f"ORDER REJECTED reqId={reqId}: {errorString}")
    else:
        log.warning(f"Error {errorCode} reqId={reqId}: {errorString}")

ib.errorEvent += on_error
```

## Heartbeat and Health Check

Use `reqCurrentTime()` as heartbeat, calling every 30-60 seconds. In ib_async, `ib.setTimeout()` sets a timeout for incoming messages and emits `timeoutEvent` if no data arrives for too long. Monitor last tick timestamps per instrument -- during market hours, if no update for >60 seconds on a liquid instrument, data may be stale.

The heartbeat's active round-trip is the **authoritative** liveness signal -- `isConnected()` is only a hint and can report `True` on a dead client (see the zombie blind spot above). Never gate the heartbeat's loop or its escalation on the flag: a `while ib.isConnected():` heartbeat exits silently on a false negative, which is trait #5 of the silent-failure signature.

```python
async def heartbeat_loop(ib):
    while True:                        # the probe decides, never the flag
        try:
            server_time = await asyncio.wait_for(
                ib.reqCurrentTimeAsync(), timeout=10
            )
            log.debug(f"Heartbeat OK: server_time={server_time}")
        except asyncio.TimeoutError:
            log.error("Heartbeat timeout -- connection may be dead")
            on_disconnect()
            return
        await asyncio.sleep(30)
```

## Related

- `gateway-automation.md` -- scheduled outage windows, IBC, launcher patterns, Windows deployment
- `order-lifecycle-contracts.md` -- order verdicts and state after reconnects
- `venue-boundary-failure-modes.md` -- qualified-contract cache invalidation, rejection ingress
- `event-driven-data.md` -- 1101/1102 data reconciliation, listener contracts, logger routing
