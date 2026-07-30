---
name: ibkr-trading
description: >
  Comprehensive Interactive Brokers algotrading knowledge base covering TWS API 10.45
  architecture, ib_async event-driven programming, market data subscriptions, order execution with
  bracket orders, historical data with pacing rules, reconnection resilience, IBC automation, and
  Windows production deployment. Use when building, implementing, writing, coding, creating,
  optimizing, or debugging IB trading systems with Python.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: ibkr-trading
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
- Debugging TWS API error codes (110, 135, 162, 200, 201, 354, 366, 1100-1102)
- Translating FX/metals symbols into the right contract type (spot vs CFD) for the account's entity
- Sizing orders from prices without the `NaN`/`0.0`/unit/tick traps that silently mis-size or reject
- Diagnosing a bot that looks connected but is dead (zombie `isConnected()`, reconnect supervisor silently stopped)
- Event handlers that "never fire" (eventkit swallows listener exceptions; wrong handler arity)
- Bracket TIF design: GTC children, positions left naked overnight, orphaned SL/TP on flat contracts
- Historical FX bars off the bar grid (session-reopen stub bars) corrupting replays/bootstraps
- Daily market open/close events swallowed by a dedup layer (TTL resonance)

## Quick Start

For 80% of use cases, start with:
1. **Connection**: IB Gateway (headless, lower resources) + IBC (automated lifecycle)
2. **Library**: `pip install ib_async` (asyncio-native successor to ib_insync)
3. **Data**: `reqRealTimeBars` for live 5-sec bars with local aggregation
4. **Orders**: Bracket orders with `transmit=False` pattern
5. **Resilience**: `disconnectedEvent` + exponential backoff reconnection
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
- Replay/bootstrap corrupted by bars live never saw -- drop off-grid session stub bars, chronology-guard state transitions (`event-driven-data.md`)

## Reference Materials

- `tws-api-architecture.md` -- TWS API 10.45, Gateway vs TWS, Client Portal, ib_async setup, clientId strategy, official docs
- `event-driven-data.md` -- reqMktData, reqRealTimeBars, reqTickByTickData, keepUpToDate, OHLCV construction, pacing violations, historical data, session-reopen stub bars (off-grid drop + top-up, replay chronology guards), eventkit listener contracts (swallowed exceptions, handler arity, std-logger routing), dedup TTL resonance with daily market events
- `order-execution.md` -- order types, bracket orders (GTC children + residual-child reaper, phantom transient Cancelled), lifecycle states, execDetails monitoring, race conditions, error codes, compliance-201 non-overridability, whatIf probing, per-clientId order visibility
- `reconnection-resilience.md` -- daily reset, IBC automation, reconnect patterns, the `isConnected()` zombie blind spot (active liveness probes, defensive disconnect, decorrelated recovery layers), Gateway-log forensics, multi-client snapshot hygiene, the silent-failure review signature, heartbeat, Windows deployment, community resources
- `venue-boundary-failure-modes.md` -- the silent-failure layer: async rejection ingress (`errorEvent` -> lifecycle), price/tick conformance (110/135, `minTick` from `ContractDetails`), FX-as-CFD routing for retail EU entities (201/200/2127/366), CFD venue params vs spot (minTick, minSize-is-precision), data-contract vs order-contract split, and `NaN`-safe sizing with canonical lot units and conversion-rate fallback

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Connection target | IB Gateway | Need visual debugging -- TWS |
| Python library | ib_async | Need same-day new features -- ibapi |
| Live data | reqRealTimeBars (5s bars) | Need tick precision -- reqTickByTickData (max 3) |
| Chart data | keepUpToDate | Network-sensitive env -- reqRealTimeBars + aggregation |
| Historical data | reqHistoricalData + throttle | Bulk backfill -- chunked requests with Semaphore |
| Order type | Bracket (parent+TP+SL) | Need trailing: TRAIL. Need algo: Adaptive |
| Lifecycle mgmt | IBC + Task Scheduler | Docker available -- gnzsnz/ib-gateway-docker |
| whatToShow | TRADES | Forex: MIDPOINT. Backtesting: ADJUSTED_LAST |
