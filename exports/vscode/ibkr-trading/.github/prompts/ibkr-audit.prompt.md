---
description: Report reliability and production-readiness defects, plus the venue assumptions nobody checked. Use when the user asks to review, audit, or validate an IB or TWS trading system: contracts, orders, brackets, pacing, error handling, reconnection, deployment. Not for building from scratch, which the ibkr-architect agent covers, a single behaviour question, which /ibkr-verify covers, or MetaTrader 5, which /mt5-audit in the `mt5-trading` bundle covers.
argument-hint: [path-or-description]
---

<!-- Vendored from plugins/ibkr-trading/commands/ibkr-audit.md in acaprino/claude-code-daodan, MIT. -->

# IB Trading System Audit

Analyse an existing IB trading system and produce an actionable audit report.

Load the `ibkr-trading` skill first ($SKILLS/ibkr-trading; `$SKILLS` is the installed skills directory: the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists).

## Scoping

**Establish the asset classes and account entity before auditing anything.** Most checks below are
conditional: size semantics, contract routing, trigger-method compatibility and data availability all
differ between equities, options, futures, FX and CFDs. Applying an FX rule to an equities system
produces false findings, and skipping an FX rule on an FX system produces silence where it matters.

Determine, and state in the report:

- which `secType`s the system actually trades
- the account entity, where it changes contract routing
- whether positions are netted, and whether the instruments are reduce-only
- whether the system holds positions across sessions

`contracts-and-instruments.md` carries a matrix of which failure modes bite which class. Use it to
select the sections that apply, and say which you skipped and why.

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
   - Gateway launcher / auto-start scripts (IBC, process managers, Task Scheduler, systemd, Docker)
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
- [ ] Fills stored append-only keyed by the FULL `execId`, with correction families grouped by the
      portion before the final period (a correction re-delivers the execution changing only the digits
      after it, so summing every callback double-counts)
- [ ] Long-lived order state keyed on `permId`, not `orderId`: only `permId` is documented to identify
      an order uniquely in an account and to survive across clients and bindings
- [ ] Recovery distinguishes visibility from control: `reqAllOpenOrders` does not bind, and an unbound
      manual order arrives with API order id 0, which cannot be modified or cancelled
- [ ] Fill history across a day boundary comes from a durable local ledger or Flex, never from
      `reqExecutions` alone (documented: current day only)
- [ ] Modifications restricted to price, size and TIF; other changes go through cancel-and-replace
- [ ] Order ID management is collision-free (nextValidId or getReqId), and a persisted high-water mark
      is never lowered because a `nextValidId` callback returned something smaller
- [ ] Cancel-fill race condition handled (never assume cancel succeeded)
- [ ] Order efficiency ratio monitored (<=20:1)
- [ ] `tif` valued explicitly on **every** leg of every order; no leg relies on the empty-string default
      (which is `DAY`). IBKR's own published bracket sample sets no TIF at all, so code copied from it
      ships DAY children
- [ ] Bracket children (SL/TP) are `tif='GTC'` whenever the position can outlive the session (DAY children leave positions naked overnight; DAY is defensible only for strictly intraday systems that guarantee flattening). Parent TIF valued deliberately -- DAY for session-scoped entries, GTC for structural levels (`bracket-orders.md`)
- [ ] `triggerMethod` on stop legs is compatible with the instrument's `secType`; an incompatible pair
      is documented to mean the order **may never trigger**, with no error. Last-driven methods (2, 3)
      are not available for `CASH`, `CMDTY` or index CFDs
- [ ] `ocaType` chosen deliberately, with block (1 or 2) unless there is a reason not to, since block
      is what provides overfill protection; no single OCA group mixes types
- [ ] Bracket construction does not use preset-driven attachment (`ptOrderType`/`slOrderType='PRESET'`),
      which sources protection levels from terminal GUI configuration
- [ ] Residual bracket children reaped when the position closes (no live SL/TP resting on a flat contract)
- [ ] Transient `Cancelled` during staged bracket transmit not treated as a real cancellation (confirm via reqOpenOrders)
- [ ] Compliance 201s treated as non-retryable (no bypass-precautions / advancedErrorOverride attempts -- `advancedErrorOverride` is a string fed from `advancedOrderRejectJson`, not a flag, and precautions are a terminal GUI feature with codes 109/163/164/382/383, not the `10xxx` range)
- [ ] Placement verdict awaited with a bounded window; on timeout the order is reported PLACED with logged uncertainty (never failure on a possibly-live order); refusal reason read from `trade.log`
- [ ] Warning-grade codes (105, 110, 10349 on working orders) NOT routed as rejections -- the `isDone()` discrimination is respected
- [ ] Order attribution map written BEFORE `placeOrder` (with rollback), and an order snapshot cached so synthetic events carry real fields

### Close Path & Netting *(netted accounts and non-reduce-only instruments: CFDs, FX, futures)*
- [ ] Close side derived from the authoritative direction field (an explicit direction field, or the signed venue position), never from the sign of an abs-stored volume -- a wrong-side close on a netted account doubles the position
- [ ] Close refused (not guessed) when direction is unresolved; event-driven closes scoped to owned symbols so account-level events don't fan out
- [ ] Close verdicts verified against the venue (no self-reported success); any consciously deferred hole is recorded with its reason
- [ ] Broker events without a venue timestamp stamped at detection time; no `None` timestamps reaching staleness comparisons (present-but-null keys defeat `.get(key, default)`)

### Terminal & Preset Config
- [ ] Order presets of every terminal the bots talk to audited (a GUI preset can cancel or mutate API orders with error 10349, even when contract details permit the attribute); re-audited after terminal upgrades
- [ ] Bracket TIF recipe validated against presets, including the orphaned-GTC-children-on-never-opened-position case (which a position-closed reaper cannot collect)

### Capability Assumptions and Their Provenance
Audits whether the system's beliefs about the venue were ever checked. See `venue-questions-and-probes.md`.
- [ ] Capability decisions ("IBKR does not support X", "this attribute is refused") trace to
      `ContractDetails.orderTypes` or to a probe transcript, not to a forum post or a search summary
- [ ] Order-type, TIF and attribute support resolved per contract rather than assumed globally
- [ ] Venue-behaviour claims in comments, docs and ADRs carry a provenance tag (measured, documented,
      assumed), and the assumed ones are tracked rather than silently load-bearing
- [ ] Behaviour on partial parent fills (child activation and sizing) is either measured for this
      account or explicitly recorded as unmeasured, with the decisions that depend on it named
- [ ] No design depends on a terminal GUI setting (order presets, precaution bypasses, the FX pip
      granularity toggle); any that does is flagged as unversioned and unshippable

### Error Handling
- [ ] The client library's own grading is understood and defended against: `ib_async` treats every code
      outside `warningCodes` and `[2100, 2200)` as fatal (430 of 458 published codes) and sets a
      non-done trade to `Cancelled` **locally**, emitting `cancelledEvent`, without telling the venue.
      Order state is therefore reconciled against `reqOpenOrders()`/`reqExecutions()`, not trusted from
      a synthesised cancellation
- [ ] `openOrder` subscribed as a distinct channel: price-capping warnings arrive there as free text
      with no code, and `mktCapPrice` arrives on `orderStatus`
- [ ] Undocumented codes handled by policy rather than by enumeration (10256, 10257 and 10349 are real
      and absent from IBKR's published table, which also omits all of 10255-10267)
- [ ] errorEvent handler registered
- [ ] Async rejection codes routed into the order lifecycle (a successful `placeOrder` is "submitted", not "accepted")
- [ ] Rejection codes GRADED before routing: rejection-grade ({103, 135, 201, 202, 10318}) mapped to a cancelled/failed event; cancel-verdict codes (161, 10148) NEVER routed as rejections (IBKR's documented cause for 10148 is an already-FILLED order; reconcile via reqExecutions instead); state-dependent codes (105, 110, 10349) excluded; 388 treated as a refusal of that order (ib_async grades it fatal, despite its polite wording); 503/504 routed to reconnection, not the order lifecycle
- [ ] Rejection events de-duplicated against orderStatusEvent (both fire for one TWS rejection; seconds-scale TTL)
- [ ] Connectivity codes handled (1100, 1101, 1102)
- [ ] Data codes handled (162 generic historical-data error, 200 no security, 354 not subscribed, 2127->366 no data on Forex CFD, 10089/10090/10186 subscription gaps, 10197 competing live/paper session)
- [ ] Delayed-feed detection reads the `marketDataType` callback, not an error code (no error code means "you are on delayed data")
- [ ] Order codes handled (103 duplicate ID, 110 tick conformance, 135 can't-find-order after a parent's death, 201 rejected, 202 cancelled, 399 sizing, 10349 preset override -- state-dependent, see the grading item above, never in the rejection set)
- [ ] Farm status codes logged but not alarmed (2104, 2106, 2158)
- [ ] WinError 10038 handled (Windows socket close)
- [ ] Errors logged with context (orderId, contract, timestamp)
- [ ] Per-dispatch logging kept at DEBUG, not INFO (INFO scales ingest cost with event volume)
- [ ] `ib_async`/`ib_insync`/`eventkit` std loggers routed to the app sink at construction, plus asyncio loop exception handler and threading.excepthook escalating to the critical logger
- [ ] Decoder-drop channel known: "Error handling fields:" decode failures never reach errorEvent; reconnect-window bursts of them trigger a qualified-contract cache re-check

### Venue Boundary: Contracts, Ticks, Sizing *(mostly FX, metals and CFDs; tick conformance applies to every class)*
Audits the silent-failure layer where canonical intent becomes IBKR contracts/orders. See `venue-boundary-failure-modes.md`.
- [ ] Order prices snapped to the increment in force before `placeOrder` (entry, SL, TP)
- [ ] The increment comes from the **market rule band** containing the price (`ContractDetails.marketRuleIds` -> `reqMarketRule` -> the `PriceIncrement` whose `lowEdge` band applies), NOT from `minTick` alone. IBKR defines `minTick` as the smallest increment on *any* exchange or price, so snapping to it can produce a price finer than the band allows and earn a 110 on a price that looks correct
- [ ] `minTick` read from `ContractDetails` (`reqContractDetailsAsync`), NOT off the `Contract` object -- and from the ORDER contract's details under the data/order split (the two differ)
- [ ] For FX and FX CFDs, the 1/2-versus-1/10 pip terminal setting (Global Configuration, Display, Ticker Row) is known and accounted for, or the market rule is read at runtime instead of tabulated
- [ ] Bracket SL/TP rounded *away* from entry and forced at least one tick clear (no `sl == entry` collapse)
- [ ] Tick rounding ordered validate-raw -> round -> re-validate (incoherent input rejected, not nudged)
- [ ] Contract type matches the account entity: retail EU (IBIE) routes leveraged FX through CFDs, not spot (else 201 currency leverage)
- [ ] FX CFDs use the split base/quote form `CFD(symbol="EUR", currency="USD")` (6-letter form fails 200)
- [ ] FX-pair split is gated on a real FX check (non-FX 6-letter ticker not blindly split)
- [ ] Data requests use a data-capable contract: underlying spot Forex for FX CFDs (FX-pair CFDs serve no data; the tell is 2127 immediately preceding 366 -- a lone 366 has other causes and gets proven, not assumed)
- [ ] Qualification lifecycle handled: conId<=0 placeholders rejected and retried (never cached); qualified-contract cache cleared on every reconnect under the same lock as the fast-path read
- [ ] The symbol-routing and canonical-size maps are validated at construction with ALL gaps aggregated into one error; partially-populated maps warn loudly (a missing symbol is a 201-shaped hole); unknown symbols fail closed
- [ ] Contract creation on read-only paths (conversion-rate lookups) guarded like order paths
- [ ] Price readiness check treats `NaN` as invalid (ib_async inits bid/ask to `NaN`, not `None`)
- [ ] The price-reading function at the broker boundary returns strictly positive or raises (no 0.0/NaN placeholder)
- [ ] Sizing guards use `not (x > 0)`, never `x <= 0` (NaN comparisons are False)
- [ ] Non-finite computed volume collapses to 0.0 and aborts at the minimum-size gate
- [ ] The minimum size is an abort threshold, NOT a floor that rounds sub-minimum input up into a live order; legitimate sizes floor DOWN at the wire edge (never-over-trade; banker's rounding is non-deterministic on half-cases)
- [ ] Every size field in one canonical internal unit (lots for FX/CFDs, shares for equities, contracts for futures/options); venue units only on the wire, converted back on trade events
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
- [ ] Handles both recurring outage windows: the published ~23:45-00:45 ET daily reset AND the operator-reported ~04:30 UTC connectivity reset (absent from IBKR's schedule; verify in your own Gateway logs)
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

### Historical Data Integrity *(FX and CFD historical feeds)*
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
- [ ] Java heap raised (4096 MB is a sound floor for heavy data volumes)
- [ ] Antivirus exclusion for TWS directory
- [ ] Paper trading validated before live deployment

3. **Generate report** with:
   - Scope: asset classes, account entity, and which check sections were skipped as inapplicable
   - Current state assessment (what is implemented correctly)
   - Risk areas (missing or misconfigured components)
   - Priority improvements ordered by production impact
   - Code examples for each recommendation
   - For silent-failure findings, an incident-spec-shaped writeup (proven facts, labelled inferences, open questions with closure criteria -- "assumed benign" is not a verdict)
   - **An unverified-assumptions register**: every belief about venue behaviour the code depends on
     that has no measurement and no quoted documentation behind it. For each, name the decision that
     rests on it and the cheapest experiment that settles it. Offer to run the applicable probes with
     `/ibkr-verify`.

A finding that the code is correct but rests on an unchecked premise is a real finding. Report it as
such rather than passing the check.
