---
name: ibkr-trading
description: >
  Comprehensive Interactive Brokers algotrading knowledge base covering TWS API 10.45 architecture,
  ib_async event-driven programming, market data subscriptions, order execution with bracket orders,
  historical data with pacing rules, reconnection resilience, IBC automation, and Windows production deployment.
  TRIGGER WHEN: building, implementing, writing, coding, creating, optimizing, or debugging IB trading systems with Python.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
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
- Debugging TWS API error codes (162, 200, 201, 354, 1100-1102)

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

## Reference Materials

- `tws-api-architecture.md` -- TWS API 10.45, Gateway vs TWS, Client Portal, ib_async setup, clientId strategy, official docs
- `event-driven-data.md` -- reqMktData, reqRealTimeBars, reqTickByTickData, keepUpToDate, OHLCV construction, pacing violations, historical data
- `order-execution.md` -- order types, bracket orders, lifecycle states, execDetails monitoring, race conditions, error codes
- `reconnection-resilience.md` -- daily reset, IBC automation, reconnect patterns, heartbeat, Windows deployment, community resources

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
