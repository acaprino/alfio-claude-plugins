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
   - Close-path / netting logic (how the system exits positions)
   - Position sizing / volume calculation and conversion-rate lookup
   - Reconnection handling
   - Gateway launcher / auto-start scripts (IBC, PM2, Task Scheduler)
   - Terminal-side configuration the code depends on (order presets, API settings)
   - Error handling (especially async rejection routing)
   - Logging

2. **Audit each component** against best practices:

### Connection
- [ ] Using IB Gateway (not TWS) for production
- [ ] Using ib_async (not archived ib_insync or a lagging ibapi from PyPI)
- [ ] ib_async pinned with an upper bound (`<3.0.0`)
- [ ] ClientId strategy defined (separate data/orders)
- [ ] Connection timeout configured
- [ ] PACEAPI enabled (`setConnectOptions('+PACEAPI')`)
- [ ] Using offline/standalone TWS version (not auto-updating)
- [ ] No sync `IB.x()` calls inside async code (only `*Async` twins; the sync forms raise "loop already running")

### Market Data
- [ ] Subscriptions cleaned up on disconnect
- [ ] Resubscription on reconnect implemented (especially after error 1101)
- [ ] Pacing violation prevention for historical data (throttle queue, caching)
- [ ] Unused subscriptions cancelled to free market data lines
- [ ] In-memory bar/ticker lists trimmed for long-running processes
- [ ] Correct whatToShow used (MIDPOINT for forex, TRADES for stocks)
- [ ] Market-open checks are tri-state (`None` beyond `tradingHours` coverage, never a confident `False` from a blind broker) with TTL refresh keyed on last attempt

### Orders
- [ ] Bracket orders used for risk management
- [ ] transmit=False pattern for bracket submission
- [ ] All order states handled (including Inactive, PendingCancel, ApiCancelled, and ib_async's ValidationError pseudo-status)
- [ ] execDetails monitored as authoritative fill source (not just orderStatus)
- [ ] Partial fill logic implemented
- [ ] Order ID management is collision-free (nextValidId or getReqId)
- [ ] Cancel-fill race condition handled (never assume cancel succeeded)
- [ ] Order efficiency ratio monitored (<=20:1)
- [ ] Bracket children (SL/TP) are `tif='GTC'` (parent DAY) -- DAY children leave positions naked overnight
- [ ] Residual bracket children reaped when the position closes (no live SL/TP resting on a flat contract)
- [ ] Transient `Cancelled` during staged bracket transmit not treated as a real cancellation (confirm via reqOpenOrders)
- [ ] Compliance 201s treated as non-retryable (no bypass-precautions / advancedErrorOverride attempts -- those only cover 10xxx precautions)
- [ ] Placement verdict awaited with a bounded window; on timeout the order is reported PLACED with logged uncertainty (never failure on a possibly-live order); refusal reason read from `trade.log`
- [ ] Warning-grade codes (105, 110, 10349 on working orders) NOT routed as rejections -- the `isDone()` discrimination is respected
- [ ] Order attribution map written BEFORE `placeOrder` (with rollback), and an order snapshot cached so synthetic events carry real fields

### Close Path & Netting
- [ ] Close side derived from the authoritative direction field (`position_type` / signed venue position), never from the sign of an abs-stored volume -- a wrong-side close on a netted account doubles the position
- [ ] Close refused (not guessed) when direction is unresolved; event-driven closes scoped to owned symbols so account-level events don't fan out
- [ ] Close verdicts verified against the venue (no self-reported success); any consciously deferred hole is recorded with its reason
- [ ] Broker events without a venue timestamp stamped at detection time; no `None` timestamps reaching staleness comparisons (present-but-null keys defeat `.get(key, default)`)

### Terminal & Preset Config
- [ ] Order presets of every terminal the bots talk to audited (a GUI preset can cancel or mutate API orders with error 10349, even when contract details permit the attribute); re-audited after terminal upgrades
- [ ] Bracket TIF recipe validated against presets, including the orphaned-GTC-children-on-never-opened-position case (which a position-closed reaper cannot collect)

### Error Handling
- [ ] errorEvent handler registered
- [ ] Async rejection codes routed into the order lifecycle (a successful `placeOrder` is "submitted", not "accepted")
- [ ] Rejection codes GRADED before routing: rejection-grade ({103, 135, 161, 201, 202, 10148, 10318}) mapped to a cancelled/failed event; state-dependent codes (105, 110, 10349) excluded; 388 treated as a size notice; 503/504 routed to reconnection, not the order lifecycle
- [ ] Rejection events de-duplicated against orderStatusEvent (both fire for one TWS rejection; seconds-scale TTL)
- [ ] Connectivity codes handled (1100, 1101, 1102)
- [ ] Data codes handled (162 generic historical-data error, 200 no security, 354 not subscribed, 2127->366 no data on Forex CFD, 10089/10090/10186 subscription gaps, 10197 competing live/paper session)
- [ ] Delayed-feed detection reads the `marketDataType` callback, not an error code (no error code means "you are on delayed data")
- [ ] Order codes handled (103 duplicate ID, 110 tick conformance, 135 can't-find-order after a parent's death, 201 rejected, 202 cancelled, 399 sizing, 10349 preset override)
- [ ] Farm status codes logged but not alarmed (2104, 2106, 2158)
- [ ] WinError 10038 handled (Windows socket close)
- [ ] Errors logged with context (orderId, contract, timestamp)
- [ ] Per-dispatch logging kept at DEBUG, not INFO (INFO scales ingest cost with event volume)
- [ ] `ib_async`/`ib_insync`/`eventkit` std loggers routed to the app sink at construction, plus asyncio loop exception handler and threading.excepthook escalating to the critical logger
- [ ] Decoder-drop channel known: "Error handling fields:" decode failures never reach errorEvent; reconnect-window bursts of them trigger a qualified-contract cache re-check

### Venue Boundary: Contracts, Ticks, Sizing
Audits the silent-failure layer where canonical intent becomes IBKR contracts/orders. See `venue-boundary-failure-modes.md`.
- [ ] Order prices snapped to the contract `minTick` before `placeOrder` (entry, SL, TP)
- [ ] `minTick` read from `ContractDetails` (`reqContractDetailsAsync`), NOT off the `Contract` object -- and from the ORDER contract's details under the data/order split (the two differ)
- [ ] Bracket SL/TP rounded *away* from entry and forced at least one tick clear (no `sl == entry` collapse)
- [ ] Tick rounding ordered validate-raw -> round -> re-validate (incoherent input rejected, not nudged)
- [ ] Contract type matches the account entity: retail EU (IBIE) routes leveraged FX through CFDs, not spot (else 201 currency leverage)
- [ ] FX CFDs use the split base/quote form `CFD(symbol="EUR", currency="USD")` (6-letter form fails 200)
- [ ] FX-pair split is gated on a real FX check (non-FX 6-letter ticker not blindly split)
- [ ] Data requests use a data-capable contract: underlying spot Forex for FX CFDs (FX-pair CFDs serve no data; the tell is 2127 immediately preceding 366 -- a lone 366 has other causes and gets proven, not assumed)
- [ ] Qualification lifecycle handled: conId<=0 placeholders rejected and retried (never cached); qualified-contract cache cleared on every reconnect under the same lock as the fast-path read
- [ ] `symbol_types` / canonical-size maps validated at construction with ALL gaps aggregated into one error; partially-populated maps warn loudly (a missing symbol is a 201-shaped hole); unknown symbols fail closed
- [ ] Contract creation on read-only paths (conversion-rate lookups) guarded like order paths
- [ ] Price readiness check treats `NaN` as invalid (ib_async inits bid/ask to `NaN`, not `None`)
- [ ] `get_symbol_price` returns strictly positive or raises (no 0.0/NaN placeholder)
- [ ] Sizing guards use `not (x > 0)`, never `x <= 0` (NaN comparisons are False)
- [ ] Non-finite computed volume collapses to 0.0 and aborts at the `volume < volume_min` gate
- [ ] `volume_min` is an abort threshold, NOT a floor that rounds sub-minimum input up into a live order; legitimate sizes floor DOWN at the wire edge (never-over-trade; banker's rounding is non-deterministic on half-cases)
- [ ] All `volume_*` fields in one canonical unit (lots); venue units only on the wire, converted back on trade events
- [ ] `minSize` interpreted per instrument class (metal CFD = real venue minimum; FX CFD on SMART = precision, not a floor; spot CASH = precision with IDEALPRO per-currency floors); no `Contract.multiplier` fallback for contract size
- [ ] Conversion rate tries direct `{base}{counter}` then inverse `{counter}{base}` (1/rate); rejects `USDUSD`
- [ ] Market-open re-checked under the execution lock (check-then-act is a race)
- [ ] Venue params read per traded contract at runtime: CFD `minTick` differs from spot; no spot minimum tables applied to CFDs
- [ ] The venue->domain validation boundary contract-tested end-to-end (real ib_async objects into domain events; attribute-vs-method traps like `Forex.pair` drop events silently)

### Reconnection
- [ ] disconnectedEvent handler with reconnection logic (async task, never sync connect/sleep inside the handler)
- [ ] Jittered backoff schedule (not fixed-interval, not synchronized across sibling clients sharing one Gateway)
- [ ] Post-reconnect state recovery (positions, orders, subscriptions, executions, qualified-contract cache cleared)
- [ ] Heartbeat monitoring (reqCurrentTime or setTimeout), loop not gated on `isConnected()`
- [ ] Handles both scheduled outage windows (~23:45-00:45 ET daily reset AND the ~04:30 UTC connectivity reset)
- [ ] Retry loop gated on an ACTIVE probe (`reqCurrentTimeAsync` + timeout), not on `isConnected()` (zombie flag after a failed connectAsync)
- [ ] Half-open connectAsync returns (no exception, `isConnected()` False) synthesized into retryable failures
- [ ] Defensive `disconnect()` after every failed connect attempt (resets zombie client state); half-open sockets torn down on cancellation (else error 326)
- [ ] The reconnect supervisor itself supervised: respawned by an independent loop if it dies on an escaped exception; terminal config errors stop it instead of retrying forever
- [ ] Recovery layers decorrelated (supervisor, heartbeat, polled fallback do not all trust the same boolean)
- [ ] Escalation/alert when the reconnect supervisor goes silent (no attempt logs after a disconnect)
- [ ] Account snapshots health-gated on the producer AND rejected by consumers when flagged unhealthy (no last-writer-wins replace of shared position state)

### Event Listeners
- [ ] Every ib_async event handler signature contract-tested (wrong arity = handler dies silently on every emission inside eventkit)
- [ ] `eventkit` / `ib_async` std loggers routed to the application log sink (listener exceptions are otherwise invisible)

### Historical Data Integrity
- [ ] Off-grid session-reopen stub bars dropped from intraday FX historical responses (with drop-count logging; D1+ exempt)
- [ ] The forming last bar dropped (bars whose synthesized time_close is in the future) -- IBKR returns it, MT5-style "last row = closed" assumptions corrupt indicators
- [ ] Requested bar count preserved via over-fetch + bounded top-up after dropping; the consumer independently guards against a thin/empty replay window
- [ ] Empty responses triaged by batch index (empty FIRST batch = no data; later batches = suspect the 15s identical-request pacing, which is enforced across processes) with a bounded same-request retry ladder
- [ ] `time_close` synthesized at the adapter; ib_async date-vs-datetime bar timestamps converted explicitly (unknown types raise, never fall back to now())
- [ ] Replay/bootstrap paths chronology-guard state transitions (bar closes after last state update; confirmation window not elapsed)
- [ ] Downstream dedup of market open/close events uses a TTL bounding only the real duplicate window (seconds-minutes, never >= the ~24h session cycle)

### Production Hardening
- [ ] IBC configured for automated Gateway lifecycle
- [ ] Task Scheduler (or equivalent) for auto-restart
- [ ] Gateway auto-start is single-flight across processes (host-wide lock with atomic payload, stale detection by PID + create time, LOCK_STALE >= START_TIMEOUT)
- [ ] Launcher tolerates cold IBC logins (start timeout >= 600 s) and verifies startup by API port probe, never by launcher exit code
- [ ] Structured logging with rotation
- [ ] Firewall restricts API to localhost only
- [ ] Java heap raised (4096 MB is a battle-tested floor for heavy data volumes)
- [ ] Antivirus exclusion for TWS directory
- [ ] Paper trading validated before live deployment

3. **Generate report** with:
   - Current state assessment (what is implemented correctly)
   - Risk areas (missing or misconfigured components)
   - Priority improvements ordered by production impact
   - Code examples for each recommendation
   - For silent-failure findings, an incident-spec-shaped writeup (proven facts, labelled inferences, open questions with closure criteria -- "assumed benign" is not a verdict)
