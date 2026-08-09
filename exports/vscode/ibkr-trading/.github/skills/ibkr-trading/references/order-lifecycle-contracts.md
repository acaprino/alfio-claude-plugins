# Order Lifecycle Contracts (Verdicts, Grades, Presets, Netted Closes)

`placeOrder` returning is the *beginning* of an order's story, not its outcome. The venue's verdict arrives asynchronously; the same error code means different things depending on order state; the terminal's own configuration can veto orders the venue would accept; and on a netted account a "close" is just an order like any other -- including a wrong one. This file is the contract layer for all of that.

Distilled from production incidents on a live multi-strategy FX/metals CFD deployment (retail EU entity), including a wrong-side close that doubled a short position several times before detection.

## When to use

Writing or reviewing the code that decides "did this order succeed?", routes error codes into an order lifecycle, closes positions, or debugs orders that die with no visible cause. Complements `order-execution.md` (how to place) and `venue-boundary-failure-modes.md` (how rejections arrive).

## placeOrder is a positive contract: await the verdict

`placeOrder` returns as soon as the local reqId is allocated. The venue's verdict typically lands a few hundred milliseconds later (observed ~600 ms) via `orderStatusEvent`. Callers that report success immediately convert every later rejection into a silent divergence: the system believes an order is working that the venue killed.

Await the verdict with a bounded window and asymmetric semantics:

```python
_ORDER_ACK_TIMEOUT_S = 2.0     # verdicts observed ~600 ms; 2 s bounds the wait
_ORDER_REFUSED  = {"Cancelled", "ApiCancelled"}
_ORDER_UNDECIDED = {"PendingSubmit", ""}
# "Inactive" is deliberately in NEITHER set: an Inactive order can still be
# live at the venue, and calling it a refusal would make the caller re-enter
# on top of a working order.

async def await_broker_verdict(trade):
    deadline = asyncio.get_running_loop().time() + _ORDER_ACK_TIMEOUT_S
    while asyncio.get_running_loop().time() < deadline:
        status = trade.orderStatus.status
        if status in _ORDER_REFUSED:
            return False, _refusal_reason(trade)
        if status not in _ORDER_UNDECIDED:
            return True, None          # PreSubmitted / Submitted / Filled
        await asyncio.sleep(0.02)
    return True, "verdict timeout"     # report PLACED and log the uncertainty
```

- **The asymmetry rule**: on timeout, report the order as **placed** and log the uncertainty. Claiming failure on a possibly-live order makes the caller re-enter on top of it; claiming success on a dead one is caught by reconciliation. Choose the recoverable error.
- **The refusal reason is not in `orderStatus`.** When ib_async flips a pending order to cancelled, it appends the cause as a `TradeLogEntry` with an `errorCode` on `trade.log`. Read it there; the status object alone says only "Cancelled".

## Warning-grade vs rejection-grade codes: the isDone() rule

ib_async cancels an order in response to an error **only `if not trade.isDone()`**. The same code therefore means different things by order state:

- On an order still in `PendingSubmit`: codes like **110** (tick conformance) kill it; ib_async itself emits `orderStatusEvent(Cancelled)`. This is the state in which the 110 -> 135 bracket cascade happens.
- On a **working** order (`PreSubmitted`/`Submitted`): the same **110**, a **105** (modify mismatch), or a **10349** are *warning-grade*: ib_async sets the pseudo-status `ValidationError` and the order **stays live at the venue**.

Consequence: **adding a code to your rejection-routing set is not free.** Routing a warning-grade code as a rejection emits a synthetic cancellation for an order the venue still considers working: your system believes it dead, the venue believes it live, and the order is orphaned. In production, 105 and 110 had to be *removed* from the rejection set for exactly this reason, and the rule is pinned by a test (`test_warning_grade_codes_do_not_cancel_live_orders`). The pending-state kills you would catch via the error set already arrive via `orderStatusEvent`, so you lose nothing by keeping the set narrow.

## Canonical order-state set

Handle all of these; several are commonly forgotten:

`PendingSubmit`, `PendingCancel`, `PreSubmitted`, `Submitted`, `ApiCancelled`, `Cancelled`, `Filled`, `Inactive`, plus the client-level `ApiPending` (ib_async-side, not a TWS state) and ib_async's `ValidationError` pseudo-status (warning-grade error on a working order, see above). `Inactive` deserves special care: it means "not currently working" (rejected, halted, or awaiting reactivation), not "dead"; never treat it as a terminal refusal without corroboration.

## Terminal order presets are invisible input (error 10349)

TWS/Gateway **order presets** configured in the GUI apply to API orders. They live in the terminal, not in your code, your config, or your repo: an unversioned input that can veto or mutate orders. Observed in production: every bracket entry cancelled ~620 ms after `PendingSubmit` with `10349 "Order TIF was set to DAY based on order preset"`, wholesale, despite the code being correct.

- **The discriminator**: pull `reqContractDetails` for the instrument and read the permitted TIF list. When the order is refused for an attribute the contract details say is permitted (GTC listed, GTC rejected), **the rejector is the terminal, not the venue**.
- **Diagnose with a reversible config test first**: change/remove the preset in the terminal and retry, before touching code. If a preset is the cause, code-side "fixes" (e.g. lowering bracket children to DAY) trade a visible failure for a silent protection downgrade; the preset must be removed instead.
- **The GTC-bracket recipe is necessary, not sufficient** (see `order-execution.md`): a preset can override child TIFs or cancel staged orders outright. Worst case if mutated children *do* transmit: GTC children resting for a position that never opened, which a reaper hooked on position-closed events cannot collect because no position ever existed. Audit the preset configuration of every terminal your bots talk to, and re-audit after terminal upgrades.

## Closing a netted position: side is data, not arithmetic

IBKR CFD/FX accounts are **netted**: one position per contract, and a "close" is an ordinary opposite-side order. Two properties make the close path the most dangerous code in the adapter:

- **A wrong-side close is not a no-op and not an error.** IBKR CFD orders are not reduce-only. Closing a short with a SELL does not fail: it **doubles the short**. Production incident: the close side was derived from `sign(position.volume)` while the position store kept volumes as absolute values with direction in a separate `position_type` field, so every "close" went out as SELL; a USD.JPY short walked from -113,998 to -683,988, one doubling per economic event, and no error was ever raised.
- **Fan-out multiplies it.** Sibling executors sharing one account and one netted conId can each react to the same event with a close for the same position.

**Rules:**

- Derive the close side from the **authoritative direction field** (`position_type` or the signed venue position), never from the sign of a volume you may have stored as an absolute value.
- **Refuse the close when the direction is unresolved.** The wrong side doubles the position; no order leaves it untouched. Guessing is the only losing move.
- Scope event-driven closes to the symbols the executor owns, so one account-level event does not fan out into N closes.
- **Verify the close verdict like any order** (see the verdict contract above). A close path that builds its own success result without querying the venue leaves a position open that the system believes closed. If you consciously defer fixing such a hole, record the deferral and its reason where the next auditor will find it -- an applied instance of "audit the whole family" from `venue-boundary-failure-modes.md`.

## Attribution traps (why a correct rejection handler still loses events)

- **Pre-placement rejections have no order snapshot to look up.** The symbol must be recovered from the raw contract, and `contract.symbol` on a Forex contract is the **base currency alone** (`"EUR"`, not `"EURUSD"`). An event keyed on that fails every downstream subscription filter and the rejection silently vanishes. Reconstruct pair symbols from `symbol + currency`.
- **reqId and orderId share one counter.** An `Error 300, reqId 111` arriving 25 ms before `orderId=113` looks order-correlated; it is a market-data subscription error. Triage by id *type*, not proximity.
- **IBKR exposes no per-order broker timestamp** via `openTrades()`. Stamp detection time yourself, on the same clock convention as your snapshot path. And beware present-but-null keys: `payload.get("broker_timestamp", 0.0)` returns `None` when the key exists with a null value, and one `None` reaching a staleness comparison inside a catch-all handler froze a position registry at its opening state.

## Write the attribution map before placeOrder

A synthetic rejection event is only as good as its enrichment. An `order_cancelled` carrying `strategy_id=0` routes to the orphan bucket, misses every subscriber, and dies **while looking wired**. Two ordering rules:

- **Write the correlation map (`orderId`/`conId` -> strategy, symbol) *before* calling `placeOrder`**, in both single-leg and bracket paths, with rollback on placement exception. `errorEvent` can fire before a post-placement map write completes.
- **Cache an order snapshot at placement** (kind, action, quantity, price) so a synthetic lifecycle event carries real fields instead of zeros. Consumers silently drop empty events.

## When the venue fails quietly: the incident-spec method

The failure modes in this file were diagnosed with a document shape worth stealing. For any incident on a venue that fails silently, write the analysis spec *before* proposing fixes:

1. **Proven facts**, each with a timestamp and source (venue log, app log, order record).
2. **Unproven inferences**, explicitly labelled as such.
3. **Open questions**, each with the method that would close it.
4. **Competing hypotheses**, each with the *discriminating prediction* that separates it from the others.
5. **Closure criteria**: every open question ends with an explicit benign/not-benign verdict. **"Assumed benign" is not a verdict.**
6. **Out-of-scope**, stated, so deferrals are decisions rather than omissions.

## Related

- `order-execution.md` -- placing orders, brackets, fills, paper-gateway probing
- `venue-boundary-failure-modes.md` -- async rejection ingress, rejection-code sets, sizing guards
- `event-driven-data.md` -- listener contracts, logger routing, decoder-drop channel
- `reconnection-resilience.md` -- verdicts and state after reconnects
