---
description: >
  Audit an existing Interactive Brokers trading system for reliability, error handling, and production readiness.
  TRIGGER WHEN: the user asks to review, audit, or validate an IB/TWS trading bot (reconnection, bracket orders, pacing, error codes, IBC automation).
  DO NOT TRIGGER WHEN: building a new IB system from scratch (use the ibkr-architect agent directly), or auditing non-IB trading systems (use /mt5-trading:mt5-audit for MT5).
argument-hint: "[path-or-description]"
---

# IB Trading System Audit

Analyze an existing IB trading system and produce an actionable audit report.

## Instructions

1. **Identify IB components** in the codebase:
   - Connection setup (TWS/Gateway, port, clientId)
   - Contract definitions and qualification (and contract *type* per account entity: spot vs CFD)
   - The adapter boundary that translates internal prices/volumes into `Contract`/`Order` objects
   - Market data subscriptions and price-snapshot reads used for sizing
   - Order execution logic (including price/tick snapping and bracket rounding)
   - Position sizing / volume calculation and conversion-rate lookup
   - Reconnection handling
   - Error handling (especially async rejection routing)
   - Logging

2. **Audit each component** against best practices:

### Connection
- [ ] Using IB Gateway (not TWS) for production
- [ ] Using ib_async (not deprecated ib_insync or outdated ibapi from PyPI)
- [ ] ClientId strategy defined (separate data/orders)
- [ ] Connection timeout configured
- [ ] PACEAPI enabled (`setConnectOptions('+PACEAPI')`)
- [ ] Using offline/standalone TWS version (not auto-updating)

### Market Data
- [ ] Subscriptions cleaned up on disconnect
- [ ] Resubscription on reconnect implemented (especially after error 1101)
- [ ] Pacing violation prevention for historical data (throttle queue, caching)
- [ ] Unused subscriptions cancelled to free market data lines
- [ ] In-memory bar/ticker lists trimmed for long-running processes
- [ ] Correct whatToShow used (MIDPOINT for forex, TRADES for stocks)

### Orders
- [ ] Bracket orders used for risk management
- [ ] transmit=False pattern for bracket submission
- [ ] All order states handled (including Inactive)
- [ ] execDetails monitored as authoritative fill source (not just orderStatus)
- [ ] Partial fill logic implemented
- [ ] Order ID management is collision-free (nextValidId or getReqId)
- [ ] Cancel-fill race condition handled (never assume cancel succeeded)
- [ ] Order efficiency ratio monitored (<=20:1)
- [ ] Bracket children (SL/TP) are `tif='GTC'` (parent DAY) -- DAY children leave positions naked overnight
- [ ] Residual bracket children reaped when the position closes (no live SL/TP resting on a flat contract)
- [ ] Transient `Cancelled` during staged bracket transmit not treated as a real cancellation (confirm via reqOpenOrders)
- [ ] Compliance 201s treated as non-retryable (no bypass-precautions / advancedErrorOverride attempts -- those only cover 10xxx precautions)

### Error Handling
- [ ] errorEvent handler registered
- [ ] Async rejection codes routed into the order lifecycle (a successful `placeOrder` is "submitted", not "accepted")
- [ ] Rejection codes mapped to a cancelled/failed event ({103, 105, 110, 135, 161, 201, 202, 388, 478, 503, 504, 10148, 10318})
- [ ] Rejection events de-duplicated against orderStatusEvent (both fire for one TWS rejection)
- [ ] Connectivity codes handled (1100, 1101, 1102)
- [ ] Data codes handled (162 pacing, 200 no security, 354 not subscribed, 2127->366 no data on Forex CFD)
- [ ] Order codes handled (103 duplicate ID, 110 tick conformance, 135 bracket child, 201 rejected, 202 cancelled, 399 sizing)
- [ ] Farm status codes logged but not alarmed (2104, 2106, 2158)
- [ ] WinError 10038 handled (Windows socket close)
- [ ] Errors logged with context (orderId, contract, timestamp)
- [ ] Per-dispatch logging kept at DEBUG, not INFO (INFO scales ingest cost with event volume)

### Venue Boundary: Contracts, Ticks, Sizing
Audits the silent-failure layer where canonical intent becomes IBKR contracts/orders. See `venue-boundary-failure-modes.md`.
- [ ] Order prices snapped to the contract `minTick` before `placeOrder` (entry, SL, TP)
- [ ] `minTick` read from `ContractDetails` (`reqContractDetailsAsync`), NOT off the `Contract` object
- [ ] Bracket SL/TP rounded *away* from entry and forced at least one tick clear (no `sl == entry` collapse)
- [ ] Tick rounding ordered validate-raw -> round -> re-validate (incoherent input rejected, not nudged)
- [ ] Contract type matches the account entity: retail EU (IBIE) routes leveraged FX through CFDs, not spot (else 201 currency leverage)
- [ ] FX CFDs use the split base/quote form `CFD(symbol="EUR", currency="USD")` (6-letter form fails 200)
- [ ] FX-pair split is gated on a real FX check (non-FX 6-letter ticker not blindly split)
- [ ] Data requests use a data-capable contract: underlying spot Forex for FX CFDs (FX CFDs serve no data; 2127->366)
- [ ] `symbol_types` config validated at startup (no silent default to spot)
- [ ] Price readiness check treats `NaN` as invalid (ib_async inits bid/ask to `NaN`, not `None`)
- [ ] `get_symbol_price` returns strictly positive or raises (no 0.0/NaN placeholder)
- [ ] Sizing guards use `not (x > 0)`, never `x <= 0` (NaN comparisons are False)
- [ ] Non-finite computed volume collapses to 0.0 and aborts at the `volume < volume_min` gate
- [ ] `volume_min` is an abort threshold, NOT a floor that rounds sub-minimum input up into a live order
- [ ] All `volume_*` fields in one canonical unit (lots); venue units only on the wire, converted back on trade events
- [ ] Conversion rate tries direct `{base}{counter}` then inverse `{counter}{base}` (1/rate); rejects `USDUSD`
- [ ] Market-open re-checked under the execution lock (check-then-act is a race)
- [ ] Venue params read per traded contract at runtime: CFD `minTick` differs from spot; CFD `minSize` is precision, not the venue minimum (no spot minimum tables applied to CFDs)

### Reconnection
- [ ] disconnectedEvent handler with reconnection logic
- [ ] Exponential backoff implemented (not fixed-interval retry)
- [ ] Post-reconnect state recovery (positions, orders, subscriptions, executions)
- [ ] Heartbeat monitoring (reqCurrentTime or setTimeout)
- [ ] Handles daily reset window (~23:45-00:45 ET)
- [ ] Retry loop gated on an ACTIVE probe (`reqCurrentTimeAsync` + timeout), not on `isConnected()` (zombie flag after a failed connectAsync)
- [ ] Defensive `disconnect()` after every failed connect attempt (resets zombie client state)
- [ ] Recovery layers decorrelated (supervisor, heartbeat, polled fallback do not all trust the same boolean)
- [ ] Escalation/alert when the reconnect supervisor goes silent (no attempt logs after a disconnect)
- [ ] Account snapshots health-gated (a disconnected client must not publish empty snapshots; no last-writer-wins replace of shared position state)

### Event Listeners
- [ ] Every ib_async event handler signature contract-tested (wrong arity = handler dies silently on every emission inside eventkit)
- [ ] `eventkit` / `ib_async` std loggers routed to the application log sink (listener exceptions are otherwise invisible)

### Historical Data Integrity
- [ ] Off-grid session-reopen stub bars dropped from intraday FX historical responses (with drop-count logging; D1+ exempt)
- [ ] Requested bar count preserved via over-fetch + bounded top-up after dropping
- [ ] Replay/bootstrap paths chronology-guard state transitions (bar closes after last state update; confirmation window not elapsed)
- [ ] Downstream dedup of market open/close events uses a TTL bounding only the real duplicate window (seconds-minutes, never >= the ~24h session cycle)

### Production Hardening
- [ ] IBC configured for automated Gateway lifecycle
- [ ] Task Scheduler (or equivalent) for auto-restart
- [ ] Structured logging with rotation
- [ ] Firewall restricts API to localhost only
- [ ] Java memory set to 4096 MB minimum
- [ ] Antivirus exclusion for TWS directory
- [ ] Paper trading validated before live deployment

3. **Generate report** with:
   - Current state assessment (what is implemented correctly)
   - Risk areas (missing or misconfigured components)
   - Priority improvements ordered by production impact
   - Code examples for each recommendation
