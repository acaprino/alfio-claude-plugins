---
name: ibkr-trading
description: >
  Authoritative reference for Interactive Brokers integration in Python, across every asset class,
  with tooling to verify venue behaviour against a paper Gateway instead of guessing.
  TRIGGER WHEN: building, auditing or debugging anything that talks to TWS or IB Gateway via the
  TWS API and ib_async: contracts, market data, orders, brackets, error codes, reconnection,
  deployment, or a question about how IBKR actually behaves.
  DO NOT TRIGGER WHEN: MetaTrader 5 (use mt5-trading), or the IBKR Web API with no TWS connection.
---

# Interactive Brokers Integration

Reference for building, operating and debugging systems that trade through the Interactive Brokers TWS
API with `ib_async` in Python. Covers equities, options, futures, FX, CFDs and crypto.

## The one rule this skill is organised around

**IBKR's behaviour is a property of your contract, your account entity and your terminal, not a global
constant.** Most expensive IBKR bugs are not coding errors. They are correct code built on an
assumption about the venue that nobody checked, that was never documented, and that turned out to be
false for that instrument or that account.

So the order of resort, for any question, is:

1. **Read the capability list.** `ContractDetails.orderTypes` declares what that contract accepts.
   Many questions end here, for free.
2. **Read the documentation and quote the sentence.** If you cannot locate it as a sentence on the
   page, you do not have an answer. Never accept a search-engine summary as evidence.
3. **Probe it** against a paper Gateway and keep the transcript.
4. **Record the answer with its provenance and the shapes it covers.**

`venue-questions-and-probes.md` is the doctrine. `gateway-verification.md` is the tooling.

## Quick start

1. **Connection**: IB Gateway (headless, lighter) over TWS. Ports 4002 paper, 4001 live. Offline
   standalone build in production, never the auto-updater.
2. **Library**: `pip install "ib_async<3.0.0"` (Python >= 3.10). The upper bound forces an explicit
   upgrade decision.
3. **Contracts**: qualify, reject `conId <= 0` placeholders, clear the cache on every reconnect.
4. **Prices**: snap to the increment from the **market rule band**, not to `minTick`.
5. **Orders**: value `tif` explicitly on every leg. Treat a returned `placeOrder` as submitted, never
   accepted.
6. **Errors**: subscribe `errorEvent`, `orderStatusEvent`, `openOrder`, and route the library's std
   loggers into your sink. Four channels, all of them load-bearing.
7. **Resilience**: `disconnectedEvent` plus jittered backoff, gated on an active probe rather than on
   `isConnected()`.
8. **Verify**: `scripts/ibkr_gateway.py` provisions a paper Gateway; `scripts/ibkr_probe.py` measures
   what it does.

## Reference materials

**Foundations**
- `tws-api-architecture.md` - protocol, Gateway versus TWS, ports, clientId strategy, session
  exclusivity, `ib_async` setup, pinning and measured divergences, official docs and community
  resources
- `contracts-and-instruments.md` - per-asset-class contract construction, qualification, **market rules
  and the increment actually in force**, size semantics per class, option chains, combos, `whatToShow`,
  and a matrix of which failure modes bite which class

**Orders**
- `order-types-and-attributes.md` - order types, time in force, fill modes and attributes, and how to
  resolve what a given contract accepts instead of guessing
- `bracket-orders.md` - brackets in depth: attached orders plus OCA, transmit staging, TIF per leg,
  OCA types and overfill protection, trigger methods and the stop that never fires, the six variants,
  and the two questions IBKR does not answer
- `order-execution.md` - order lifecycle mechanics, execDetails, race conditions, paper-trading caveats
- `order-lifecycle-contracts.md` - verdict windows, what `placeOrder` returning proves, terminal
  presets, netted close paths, attribution

**Diagnosis**
- `error-codes-and-verdicts.md` - the three layers that can refuse an order, **the `ib_async` grading
  step that cancels live orders locally**, what the published table is and is not, precautions, and how
  to grade a code you have never seen
- `venue-questions-and-probes.md` - the evidence ladder, provenance tags, probe instruments, and the
  standing register of questions the documentation does not answer
- `venue-boundary-failure-modes.md` - the adapter layer: async rejection ingress, tick conformance,
  entity-dependent contract routing, qualification lifecycle, `NaN`-safe sizing, the venue-to-domain
  validation boundary

**Data**
- `event-driven-data.md` - subscriptions, bar construction, pacing, historical silence triage,
  session-reopen stub bars, eventkit listener contracts

**Operations**
- `reconnection-resilience.md` - reconnect patterns, the `isConnected()` zombie, half-open connects,
  supervisor self-death, what the terminal preserves, Gateway-log forensics
- `gateway-automation.md` - scheduled outage windows, IBC, multi-process launcher locks, deployment on
  Windows, Linux, macOS and Docker
- `gateway-verification.md` - provisioning a disposable paper Gateway and using it to answer questions

**Data assets**
- `assets/tws-message-codes.tsv` - all 458 published TWS message codes, each tagged with the grade
  `ib_async` assigns it. Search this before inventing a classification.

## Tooling

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/ibkr-trading/scripts

python $S/ibkr_gateway.py doctor              # what is installed, which ports are open
python $S/ibkr_gateway.py install             # download and install Gateway + IBC, unattended
python $S/ibkr_gateway.py configure --user U  # config pinned to paper
python $S/ibkr_gateway.py start               # headless, verified by port probe

python $S/ibkr_probe.py capabilities --stock AAPL       # what this contract really permits
python $S/ibkr_probe.py shape --stock AAPL --type STP --tif GTC --attr allOrNone
python $S/ibkr_probe.py matrix --stock AAPL --types LMT,STP --tifs DAY,GTC,IOC
python $S/ibkr_probe.py bracket --stock AAPL --qty 1    # lifecycle, TIF read-back, preset detection
python $S/ibkr_probe.py codes 10256 10257 10349         # no gateway needed
```

Paper only, enforced twice: live ports are refused, and every managed account must look like a paper
account after connecting.

## Symptoms to entry points

| Symptom | Read |
|---|---|
| Order refused with a code you cannot classify | `error-codes-and-verdicts.md` |
| An order vanished from your books but may be live at the venue | `error-codes-and-verdicts.md`, the grading section |
| Error 110 on a price that looks correct | `contracts-and-instruments.md`, market rules |
| Protective legs expired overnight, or orphaned on a flat position | `bracket-orders.md` |
| A stop that never triggered, with no error | `bracket-orders.md`, trigger methods |
| "Does IBKR support attribute X" | `order-types-and-attributes.md` |
| A position doubled after a close | `order-lifecycle-contracts.md` |
| Orders cancelled moments after submission, code correct | `order-lifecycle-contracts.md`, terminal presets |
| Handlers that never fire, events that vanish | `event-driven-data.md` |
| Historical bars empty, or corrupting a replay | `event-driven-data.md` |
| Connected-looking but dead for hours | `reconnection-resilience.md` |
| Gateway start collisions, restart loops, outage windows | `gateway-automation.md` |
| A design decision resting on an unverified assumption | `venue-questions-and-probes.md` |

## Key decision points

| Decision | Default | Change when |
|---|---|---|
| Connection target | IB Gateway | Visual debugging wanted: TWS |
| Python library | `ib_async` | Same-day new API features: `ibapi` |
| Live data | `reqRealTimeBars` (5s) | Tick precision: `reqTickByTickData`, capped at 5% of data lines |
| Historical | `reqHistoricalData` + throttle | Bulk backfill: chunked with a semaphore |
| Order price source | Market rule band increment | Never `minTick` alone |
| Bracket children TIF | `GTC` | Strictly intraday systems that guarantee flattening |
| Reconnect backoff | Equal-jitter exponential | Single client on a dedicated Gateway: plain exponential |
| Lifecycle management | IBC + scheduler | Docker available: `gnzsnz/ib-gateway-docker` |
| Capability question | Read `orderTypes` | Token present but still refused: probe with `whatIf` |
