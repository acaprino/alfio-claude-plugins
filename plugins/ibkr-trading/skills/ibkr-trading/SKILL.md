---
name: ibkr-trading
description: >
  Knowledge base for production trading automation in Python.
  TRIGGER WHEN: building, optimizing, or debugging Interactive Brokers systems with the TWS API
  and ib_async.
  DO NOT TRIGGER WHEN: MetaTrader 5 (use mt5-trading), or IBKR Web API with no TWS connection.
---

# Interactive Brokers Algotrading

Knowledge base for building production-grade algorithmic trading systems with Interactive Brokers TWS API and ib_async in Python.

## When to Use

- Connecting to TWS or IB Gateway with ib_async
- Implementing real-time market data subscriptions
- Designing order execution logic (bracket orders, order lifecycle)
- Handling pacing violations for historical data requests
- Building reconnection resilience for 24/7 production bots
- Deploying IB trading systems on Windows with IBC + Task Scheduler
- Debugging TWS API error codes (110, 135, 162, 200, 201, 354, 366, 1100-1102, 10349)
- Translating FX/metals symbols into the right contract type (spot vs CFD) for the account's entity
- Sizing orders from prices without the `NaN`/`0.0`/unit/tick traps that silently mis-size or reject
- Diagnosing a bot that looks connected but is dead (zombie `isConnected()`, reconnect supervisor silently stopped)
- Event handlers that "never fire" (eventkit swallows listener exceptions; wrong handler arity)
- Bracket TIF design: GTC children, positions left naked overnight, orphaned SL/TP on flat contracts
- Historical FX bars off the bar grid (session-reopen stub bars) corrupting replays/bootstraps
- Daily market open/close events swallowed by a dedup layer (TTL resonance)
- A position that DOUBLED after a "close" (wrong-side close on a netted account)
- Orders cancelled moments after submission by a terminal-side order preset (error 10349)
- Deciding what `placeOrder` returning actually proves (verdict windows, warning-grade vs rejection-grade codes)
- An executor silently halted on a market-closed reading that is actually expired `tradingHours` coverage
- Historical requests coming back empty with no error (duration caps, cross-process pacing, past-retention)
- Auto-starting one Gateway under several bot processes (launcher locks, PM2 restart loops)
- Events vanishing at the venue-to-domain validation boundary (bound-method symbols, Pydantic drops)

## Quick Start

For 80% of use cases, start with:
1. **Connection**: IB Gateway (headless, lower resources) + IBC (automated lifecycle)
2. **Library**: `pip install ib_async` (asyncio-native successor to ib_insync); pin `<3.0.0`
3. **Data**: `reqRealTimeBars` for live 5-sec bars with local aggregation
4. **Orders**: Bracket orders with `transmit=False` pattern
5. **Resilience**: `disconnectedEvent` + jittered-backoff async reconnection
6. **Deployment**: IBC + Windows Task Scheduler for auto-restart

Then harden incrementally:
- Missing fills on reconnect -- add `reqExecutions()` reconciliation
- Pacing violations -- add asyncio.Semaphore throttled request queue
- Overnight crashes -- add IBC auto-restart + heartbeat monitoring
- State drift -- add periodic position/order reconciliation via `reqPositions()`
- Orders FIRED but never live, mis-sized, or rejected with no error -- read `venue-boundary-failure-modes.md` (async rejection ingress, tick conformance, FX-as-CFD routing, `NaN`-safe sizing)
- Connected-looking but dead for hours -- replace `isConnected()` gates with active probes (`reqCurrentTimeAsync` + timeout), defensive `disconnect()` after failed attempts, escalation on supervisor silence (`reconnection-resilience.md`)
- Handlers that never fire / invisible listener crashes -- contract-test handler signatures, route `eventkit`/`ib_async` std loggers to your sink (`event-driven-data.md`)
- Positions naked overnight or orphaned SL/TP -- GTC bracket children + residual-child reaper on position-closed (`order-execution.md`)
- Replay/bootstrap corrupted by bars live never saw -- drop off-grid session stub bars AND the forming last bar, chronology-guard state transitions (`event-driven-data.md`)
- "Closed" positions that doubled, orders killed by invisible terminal config, uncertain placement verdicts -- read `order-lifecycle-contracts.md` (netted close paths, error 10349 presets, verdict windows, the isDone rule)
- Gateway start collisions across processes, PM2 restart loops, outage-window surprises -- read `gateway-automation.md` (single-flight launcher, port-probe verification, scheduled resets)

## Reference Materials

- `tws-api-architecture.md` -- TWS API version and GPL open-sourcing, Gateway vs TWS, Web API (formerly Client Portal), ib_async setup and pinning, clientId strategy, official docs, community resources
- `event-driven-data.md` -- reqMktData, reqRealTimeBars, reqTickByTickData, keepUpToDate, OHLCV construction, pacing violations, historical silence triage (duration caps, cross-process pacing), tri-state market-open, session-reopen stub bars (off-grid drop + attrition top-up, replay chronology guards), the forming bar, eventkit listener contracts (swallowed exceptions, handler arity, std-logger routing, decoder-drop channel), dedup TTL resonance with daily market events
- `order-execution.md` -- order types, bracket orders (GTC children + residual-child reaper, phantom transient Cancelled), execDetails monitoring, race conditions, error codes, compliance-201 non-overridability, paper-gateway probing and whatIf, paper trading caveats, per-clientId order visibility
- `order-lifecycle-contracts.md` -- placeOrder verdict windows and refusal reasons, warning-grade vs rejection-grade codes (the isDone rule), the canonical order-state set, terminal order presets (10349), netted close paths (wrong-side doubling), attribution traps, map-write-before-placeOrder, the incident-spec method
- `reconnection-resilience.md` -- reconnect patterns (async, jittered), the `isConnected()` zombie blind spot (active liveness probes, defensive disconnect, decorrelated recovery layers), half-open connects, supervisor self-death, Gateway-log forensics, multi-client snapshot hygiene, the silent-failure review signature, heartbeat
- `gateway-automation.md` -- scheduled outage windows (daily reset + the 04:30 UTC storm), IBC automation, N-process launcher locks and port-probe verification, Windows deployment (firewall, AV, memory, WinError 10038, Task Scheduler), Docker alternative
- `venue-boundary-failure-modes.md` -- the silent-failure layer: async rejection ingress with graded code sets (`errorEvent` -> lifecycle), price/tick conformance (110/135, `minTick` from the ORDER contract's `ContractDetails`), FX-as-CFD routing for retail EU entities (201/200/2127-before-366), qualification lifecycle (conId placeholders, cache invalidation on reconnect), minSize-by-instrument-class, symbol-map shape validation, `NaN`-safe sizing with canonical lot units and conversion-rate fallback, the venue-to-domain validation boundary

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Connection target | IB Gateway | Need visual debugging -- TWS |
| Python library | ib_async | Need same-day new features -- ibapi |
| Live data | reqRealTimeBars (5s bars) | Need tick precision -- reqTickByTickData (capped at 5% of market data lines) |
| Chart data | keepUpToDate | Network-sensitive env -- reqRealTimeBars + aggregation |
| Historical data | reqHistoricalData + throttle | Bulk backfill -- chunked requests with Semaphore |
| Order type | Bracket (parent+TP+SL) | Need trailing: TRAIL. Need algo: Adaptive |
| Reconnect backoff | Equal-jitter exponential | Single client on a dedicated Gateway -- plain exponential is acceptable |
| Lifecycle mgmt | IBC + Task Scheduler | Docker available -- gnzsnz/ib-gateway-docker |
| whatToShow | TRADES | Forex: MIDPOINT. Backtesting: ADJUSTED_LAST |
