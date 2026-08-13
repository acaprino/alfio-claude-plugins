# Venue Boundary Failure Modes (Contracts, Ticks, Sizing, Async Rejections)

The hardest IBKR production bugs do not live in your strategy. They live at the adapter boundary where canonical intent (symbol, lots, prices) is translated into IBKR `Contract` and `Order` objects, and where IBKR answers asynchronously. `placeOrder` and `reqMktData` return without raising; IBKR accepts or rejects *later*, through `errorEvent`, with a numeric code. An entire family of silent failures lives in that gap: orders your system records as sent that never became live, orders sized from a degenerate price, orders mis-routed by contract type, rejections that no channel is ever told about.

This file is the checklist for that boundary. The failure modes are grouped by the condition that produces them, so you can skip the sections whose condition your account and instruments do not meet.

## When to use

Writing or reviewing the layer that converts your internal order/price/volume model into ib_async contracts and orders, or that reads prices for position sizing. If you only place plain stock market orders at SMART with integer share quantities, most of this will not bite you. It bites FX, metals, CFDs, bracket orders, conversion-rate sizing, and any non-USD-base account.

## The single shared failure mode

> `placeOrder` / `reqMktData` return "success", IBKR rejects asynchronously via `errorEvent`, the rejection is swallowed, and the system records a sent order (or sizes one from a degenerate price) with no visible error.

Everything below is a specific instance of that pattern, plus the units/contract mistakes that make a "successful" call meaningless.

## 1. Async rejection ingress (the meta-bug)

A broker call returning without an exception says nothing about acceptance. IBKR rejects asynchronously through `errorEvent`. If you do not subscribe `errorEvent` and route rejection codes into your order lifecycle, the order silently dies while your system believes it is live.

- Subscribe the handler: `ib.errorEvent += self._on_error`.
- Map rejection codes to a cancelled/failed lifecycle event -- but **grade the codes first**. Not every order-related error is a rejection, and routing a warning as a rejection orphans a live order (see the grade table below and `order-lifecycle-contracts.md`).
- Both `errorEvent` and `orderStatusEvent` can fire for the same TWS rejection. De-duplicate by `orderId` so one rejection raises one cancellation, not two. Size this dedup's TTL to the errorEvent/orderStatusEvent race (seconds; 60 s with a bounded LRU is a sound choice) -- it is a *different layer* from the session-event dedup in `event-driven-data.md`, whose TTL is bounded by the daily cycle. Never share one TTL between them.
- Keep the dispatch log at DEBUG, not INFO. A per-dispatch INFO line scales your log-aggregator ingest cost with event volume.

Codes commonly seen at this boundary, graded:

| Grade | Codes | Routing |
|-------|-------|---------|
| Rejection on an undecided order | 103, 135, 201, 202, 10318 | Synthetic `order_cancelled` (de-duped) |
| Cancel-verdict: the CANCEL failed, the order may have FILLED | 161, 10148 | Never into the rejection set. Reconcile via `reqExecutions()` + `reqOpenOrders()`: IBKR's documented cause for 10148 is an already-filled order |
| State-dependent (kills only a `PendingSubmit` order; warning-grade on a working one) | 105, 110, 10349 | Do NOT route via the error set: the pending-state kill already arrives via `orderStatusEvent`; on a working order the order is still live |
| Venue size refusal; `ib_async` grades it fatal (local `Cancelled` on a pending order) | 388 | Treat as a refusal of that order; fix the size, never assume it continues |
| Connection-layer, not an order verdict | 503, 504 | Route to reconnection handling, never to the order lifecycle |

```python
REJECTION_CODES = {103, 135, 201, 202, 10318}
# 105/110/10349 are deliberately absent: on a working order they are
# warning-grade (ib_async marks ValidationError and the order stays live);
# routing them here would cancel the local record of a live venue order.
# 161/10148 are absent for the opposite reason: they judge a CANCEL request,
# and the documented cause for 10148 is a FILL -- routing them here records
# a dead order for one that executed. Reconcile via reqExecutions() instead.

def _on_error(self, reqId, errorCode, errorString, contract):
    if errorCode in REJECTION_CODES and reqId in self._live_order_ids:
        if reqId not in self._already_cancelled:        # de-dupe vs orderStatusEvent
            self._already_cancelled.add(reqId)
            self._dispatch_event("order_cancelled", reqId, errorCode, errorString)

ib.errorEvent += self._on_error
```

## 2. Price/tick conformance (errors 110 -> 135)

IBKR rejects any price that is not an exact integer multiple of the contract `minTick` with **error 110** ("price does not conform to the minimum price variation"). On a bracket still in `PendingSubmit`, the parent's 110 cascades: the children die with **error 135** ("Can't find order with ID" -- their parent no longer exists) and the whole order dies. `placeOrder` still returned success, so the strategy records a sent order while no live order exists. (On an already-working order, 110 is warning-grade instead: see `order-lifecycle-contracts.md`.)

- **`minTick` lives on `ContractDetails`, not on the `Contract`.** Reading `contract.minTick` off a qualified `Contract` does not give you the venue tick in ib_async; the value falls back to a tiny default and your rounding becomes a silent no-op. Call `reqContractDetailsAsync` and read `details.minTick`.
- **`minTick` is a floor, not the increment in force.** IBKR defines it as "the smallest possible minimum increment encountered on **any exchange or price**". Where a contract has different increments in different price bands, snapping to `minTick` produces a price finer than the band allows, and the venue answers 110 on a price that looks correct. The authoritative per-band table comes from **market rules**: read `ContractDetails.marketRuleIds` (a list parallel to `validExchanges`), call `reqMarketRule` for the id matching your exchange, and use the `PriceIncrement` whose `lowEdge` band contains your price. `contracts-and-instruments.md` has the full procedure; `scripts/ibkr_probe.py capabilities` dumps the resolved bands for a contract.
- **For FX and FX CFDs the increment depends on a terminal setting.** The default is coarser than 1/10 pip (IBKR's own page states it inconsistently as 1/2 and 1/5), and TWS/Gateway can be switched to 1/10 pips (Global Configuration, Display, Ticker Row). That makes the increment your orders must satisfy an unversioned local input, in the same category as order presets. Read the rule at runtime rather than maintaining a table.
- **Under the data/order contract split you hold TWO `ContractDetails` with different `minTick`** (EUR.USD CFD 1e-05 vs spot 5e-05; USD.JPY CFD 0.001 vs spot 0.005). Tick conformance must come from the **order** contract's details; a rule that just says "read ContractDetails" is satisfiable by reading the wrong one.
- Snap every price (entry, SL, TP) to the band increment resolved above *before* `placeOrder`. Flooring only the quantity while passing full-precision float prices is the original sin here.
- Round bracket SL and TP **away from entry** (stop further from entry, target further from entry) and force each at least **one tick clear** of the rounded entry. Independent nearest-tick rounding can collapse a tight bracket to `sl == entry` or `tp == entry`: a naked or instantly-triggering stop.
- **Validate raw, then round, then re-validate.** If you round before validating the bracket, you nudge an incoherent input into a "valid" one instead of rejecting it. Validate the raw prices first (so bad input is rejected), then round, then re-validate the rounded bracket.
- Do the tick arithmetic in integer tick-steps via `Decimal` so IEEE-754 residue does not re-trip 110.

```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN

def snap_to_tick(price, tick, rounding=ROUND_HALF_UP):
    p, t = Decimal(str(price)), Decimal(str(tick))
    steps = (p / t).quantize(Decimal(1), rounding=rounding)
    return float(steps * t)

def round_bracket_away_from_entry(entry, sl, tp, tick, is_long):
    e = snap_to_tick(entry, tick)
    # long: SL below entry (round down), TP above entry (round up)
    sl = snap_to_tick(sl, tick, ROUND_DOWN if is_long else ROUND_UP)
    tp = snap_to_tick(tp, tick, ROUND_UP   if is_long else ROUND_DOWN)
    one = float(Decimal(str(tick)))
    if is_long:
        sl = min(sl, e - one); tp = max(tp, e + one)
    else:
        sl = max(sl, e + one); tp = min(tp, e - one)
    return e, sl, tp
```

## 3. Contract type for retail EU entities (errors 201, 200, 2127 -> 366)

A retail account under an EU entity (for example IBIE, IB Ireland) **cannot hold leveraged spot FX**. A non-base spot cross is hard-rejected with **error 201** "FX trade would expose account to currency leverage". The order never reaches the venue.

This is **bypassable in code**, not an account-side-only limit: route FX through **CFD contracts**. The same order placed as a CFD is accepted with normal retail margin (for example ESMA 30:1), no 201. Prove it cheaply before migrating: place the exact contested order against the paper gateway, or use a `whatIf=True` order on the CFD form (margin figures, no 201, no market risk).

Do NOT chase override paths for this 201: it is an account/compliance rejection, not an order precaution. Precautions are a terminal GUI feature with their own codes (109, 163, 164, 382, 383), not the `10xxx` range -- see `error-codes-and-verdicts.md`. "Bypass Order Precautions for API Orders" and `Order.advancedErrorOverride` have no effect on it.

- Forex CFDs require the **split base/quote form**: `CFD(symbol="EUR", currency="USD")`. The 6-letter form `CFD(symbol="EURUSD")` is rejected with **error 200** "no security definition found".
- **Gate the split on a real FX-pair check.** A non-FX 6-letter ticker must not be blindly split; fall back to the full ticker with a warning.
- Metals (for example XAUUSD) route as a **full-ticker CFD** and serve their own market data. Forex CFDs do **not** (see section 4).
- **The CFD's venue parameters differ from the spot pair's -- never share tables across secTypes.** CFD `minTick` can be finer than the underlying spot's (e.g. EUR.USD CFD 1e-05 vs spot 5e-05): always read `minTick` from the *traded* contract's `ContractDetails` at runtime.
- **The shape of the symbol-routing map encodes intent -- detect the gap.** An empty map means "this account trades spot FX" and the default is intent; a **non-empty map missing one symbol is a configuration hole** that routes that symbol to spot IDEALPRO, where the leverage-capped account rejects it with 201. Keep the default but warn loudly on the gap, validate values against a known set (`{FOREX, CFD}`), and **validate the whole map at construction, aggregating every missing/invalid symbol into one error** so operators see the full delta at once instead of whack-a-mole.
- **Watch read-only paths too.** A balance/currency-conversion path on a non-USD-base account can qualify CASH/IDEALPRO contracts nobody configured (e.g. EUR.JPY appearing on an account whose configs never name EURJPY) -- on exactly the contract class the account is refused on. Contract creation is a boundary wherever it happens, not just under `place_order`.

### Qualification lifecycle

Contract qualification has its own failure modes, all silent:

- **`qualifyContractsAsync` can return a placeholder with `conId <= 0`** before IBKR has actually resolved the contract. Reject and retry it; caching it poisons every later use.
- **An unqualified CFD does not error at request time.** The historical request simply **times out**, and error 366 arrives on the cancellation echo -- the failure surfaces far from its cause.
- **Clear the qualified-contract cache on every reconnect**, and make the fast-path cache read take the same lock as the clear. `conId`s can change across a reconnect (contract roll, paper/live swap, a different Gateway); a caller must not capture a Contract the reconnect just invalidated. Also re-check the cache after any burst of decode errors during a reconnect window (see the decoder-drop channel in `event-driven-data.md`).
- Qualification is a cheap server no-op for IDEALPRO CASH pairs, and mandatory for CFDs, exotic crosses, and futures: qualify everything, cache by `(symbol, sec_type)`.

```python
FX_PAIRS = {"EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCHF", "USDCAD", "NZDUSD"}
# Illustrative set: production must load the account's full tradeable pair
# list (including crosses like EURGBP, EURJPY) from config, not a literal.

def to_ibkr_order_contract(symbol):
    if symbol.startswith("XAU") or symbol.startswith("XAG"):
        return CFD(symbol=symbol, currency="USD")          # metal CFD, full ticker
    if symbol in FX_PAIRS and len(symbol) == 6:
        return CFD(symbol=symbol[:3], currency=symbol[3:])  # FX CFD, split base/quote
    log.warning("Unrecognised 6-letter ticker %s: not splitting", symbol)
    return CFD(symbol=symbol, currency="USD")
```

## 4. Separate the data contract from the order contract

A contract that is valid for *trading* is not necessarily valid for *market/historical data*. **IBKR refuses historical and market data on Forex CFDs** (error **2127** then **366** "no historical data query found"). If you request candles on the FX-CFD contract, the generator never bootstraps and places **zero orders**, while metals work. The boundary is precise: the predicate is *FX-pair CFD* (`secType == "CFD"` and the symbol is an FX pair and not a metal) -- metal CFDs and spot CASH pairs serve data fine. That asymmetry (FX dead, metals fine, on the same Gateway) is the tell.

**366 alone is not the tell.** It has at least three unrelated causes: the 2127->366 FX-CFD refusal here; an unqualified contract timing out and echoing 366 on cancellation (section 3); and a harmless cancellation echo during disconnect windows. The signature of *this* failure is **2127 immediately preceding 366**. A lone 366 during an outage window is probably noise -- but prove it, don't assume it.

Resolve the **underlying spot Forex (IDEALPRO)** for every data path of an FX-CFD symbol (historical subscription, candle pagination, price snapshot). Keep the CFD for orders and `reqContractDetails`.

```python
def get_data_contract(symbol, order_contract):
    # FX CFDs trade but serve no data; pull data from the underlying spot pair.
    if order_contract.secType == "CFD" and symbol in FX_PAIRS:
        return Forex(symbol)              # IDEALPRO spot, data-capable
    return order_contract                 # metals / cash pairs unchanged
```

## 5. Sizing and units (the NaN family, errors 201 / 399)

A silently failed snapshot that returns `ask=0.0`/`NaN` for the conversion pair zeroes the order notional. A minimum-size floor then turns that zero into a real **venue-minimum** order (EURUSD 0.01 lot rejected 399/201), or a single NaN sizes the order at the symbol **maximum**, past every downstream size check.

**The price contract.**
- **ib_async initializes `Ticker.bid` / `Ticker.ask` to `NaN`, not `None`,** before the first tick. A readiness check of `if price is None` passes immediately and hands a `NaN`/`0.0` placeholder to sizing.
- Pin the broker boundary with an invariant: the price-reading function at the broker boundary returns a **strictly positive** bid/ask **or raises**. Never a `0.0`/`NaN` placeholder.

```python
import math
def _valid(value):
    return value is not None and not math.isnan(value) and value > 0
```

**NaN-safe guards.**
- All `NaN` comparisons are `False`, so `x <= 0` lets `NaN` through. Use `not (x > 0)`.
- `min(maximum, NaN)` returns the maximum, so a single `NaN` tick sizes the order at the symbol maximum. Collapse any non-finite computed volume to `0.0` as a final chokepoint, so the minimum-size gate aborts it.

**A floor is not a safety net; the floor is the rounding mode.**
- Do **not** floor a sub-minimum volume up to the minimum. A degenerate (zero/NaN-derived) sizing input must **abort** at the minimum-size gate, never be rounded into a live venue-minimum order.
- For legitimate volumes, **round down (`math.floor`) at the wire edge under an explicit never-over-trade policy.** Banker's rounding (`round()`) is non-deterministic on lot half-cases; flooring under-fills at worst, and an under-fill surfaces as a visible minimum-size rejection -- the safe direction. The two rules are complementary: floor real sizes, abort degenerate ones.

**`minSize` means three different things by instrument class.**
- **Metal CFDs**: `ContractDetails.minSize`/`sizeIncrement` are **real venue minimums in venue units (ounces)** -- convert to lots and fail closed if absent.
- **FX CFDs on SMART**: `minSize` is **fractional-quantity precision (~1e-7), NOT a venue floor**. Applying it as a floor erases your lower bound and lets dust orders through; clamp to a canonical per-symbol floor instead.
- **Spot CASH on IDEALPRO**: `minSize` is likewise precision; the real floor is the per-currency IDEALPRO minimum table.
- **`Contract.multiplier` is `None`/1 for FX and metals**, so contract size cannot be derived from IBKR at all: a canonical contract-size table is mandatory, and a silent `multiplier` fallback (yielding `contract_size=1.0`) recreates the fractional-quantity rejection class (10318).

**Canonical units to the very edge.**
- Keep **every** size field in one canonical internal unit (for FX/CFDs: lots). Mixed units (minimum and step in lots, maximum in venue units) make the venue-minimum check dead for FX and a regression for metals. Convert lots to venue units only on the wire, and convert wire quantity back to lots on trade events. Never let oz or base units leak into sizing comparisons or reported trade volume.
- **Unknown symbol = fail closed.** A symbol missing from the canonical table must raise, not fall back to a guessed size -- and the whole symbol set gets validated once at construction (see section 3).

**Conversion rate.**
- Contract: `get_exchange_rate` returns a strictly positive rate or `None`, never `0.0`.
- Venues quote each FX pair in **one canonical direction only** (IDEALPRO quotes GBPUSD, not USDGBP). A USD account trading a GBP-quoted symbol has no directly quotable pair. Try the direct pair `{base}{counter}`, then the inverse `{counter}{base}` returning `1/rate`.
- The degenerate self-pair (`USDUSD`) must not resolve to a rate.

**Terminal market-data errors abort the wait.**
- A snapshot wait must abort on terminal codes for the contract: `{200, 354, 10089, 10090, 10197}`, tracked per `conId` in your error handler. Otherwise the "5-second wait" exits instantly on the NaN-vs-None bug and returns a placeholder.
- Re-check `market_open` **under the execution lock**: check-then-act on market state is a race. And the market-state check itself must be tri-state (see `event-driven-data.md`): a confident `False` from a blind broker halts an executor as silently as a NaN sizes an order.

## 6. The validation boundary is a silent-drop surface

The venue->domain translation layer (ib_async objects into your typed events/models) drops whatever fails validation -- and framework validation failures are as silent as swallowed listener exceptions. Two recurring instances of the same pattern:

- The `positionEvent` handler arity bug (`event-driven-data.md`): every position delta raised `TypeError` inside eventkit, forever, unlogged.
- **`ib_async.Forex.pair` is a method, not a property.** Reading it as an attribute yields a bound-method object, which flows into a validating event model as the `symbol` field and is rejected -- so **every order and position event for Forex contracts is dropped at the validation boundary**: empty registries, empty UI, no errors anywhere.

Pin the whole boundary, not just the listener signatures: contract tests that push real ib_async objects end-to-end into your domain events and assert the event *arrives* with the expected field values. Attribute-vs-method mistakes, renamed fields, and type mismatches all fail the same silent way.

## Cross-cutting systemic patterns

| # | Pattern | Where it bit |
|---|---------|--------------|
| 1 | `NaN`-vs-`None` failure contract not honoured (ib_async uses `NaN` for an absent quote) | Sizing (section 5) |
| 2 | Swallowed async rejections (`placeOrder` returns success; IBKR rejects via `errorEvent`) | Sections 1, 2, 5 |
| 3 | Non-canonical units at the venue boundary (lots vs oz / base units) | Section 5, trade events |
| 4 | Field read from the wrong object (`minTick` off `Contract` instead of `ContractDetails`; `Forex.pair` as attribute) | Sections 2, 6 |
| 5 | A "rescuing" floor that masks a degenerate input (a minimum-size floor turning a 0 into a real order) | Section 5 |
| 6 | Producer-side fix shipped without its consumer-side twin | Snapshot hygiene (`reconnection-resilience.md`), stub attrition (`event-driven-data.md`) |

Two meta-lessons:

- **Audit the whole family, not just the obvious site.** The first tick fix, the first guard fix, and the first CFD fix were each incomplete until the same flaw was hunted across every sibling path (every price leg, every sizing guard, every data request).
- **Producer and consumer fixes ship together.** Gating a bad publisher while consumers still trust blindly, or compensating a producer shortfall while consumers still assume "asked for N, got N", leaves the failure class open from the other side. Every fix at this boundary names its downstream twin and ships with it.

## Testing this boundary

Assert the failure contracts in tests, because they are exactly what production violated:

- The price-reading function at the broker boundary raises (does not return) on a `NaN`/`0.0`/`None` quote.
- Sizing aborts (does not floor) when computed volume is below the minimum size.
- A single `NaN` tick does not size at the symbol maximum.
- A sub-tick or short bracket is rejected or rounded coherently, never collapsed to `sl == entry`.
- The inverse conversion pair resolves when the direct pair is unquotable; `USDUSD` does not.
- An FX-CFD symbol pulls data from the spot Forex contract, not the CFD.
- A rejection `errorEvent` produces exactly one `order_cancelled`, de-duplicated against `orderStatusEvent`.
- Warning-grade codes (105, 110, 10349) do **not** cancel a working order's record (the isDone rule, `order-lifecycle-contracts.md`).
- Tick conformance reads `minTick` from the **order** contract's details, not the data contract's.
- Construction fails with the **complete** list of missing/invalid symbols when the canonical table or the symbol-routing map has gaps.
- A real ib_async `Forex`/CFD event object survives the venue->domain validation boundary with correct field values.

## Related

- `order-execution.md` -- bracket transmit pattern, OER, cancel-fill race, error 201 baseline
- `order-lifecycle-contracts.md` -- verdict windows, warning-vs-rejection grades, netted close paths
- `event-driven-data.md` -- snapshot/market-data subscriptions and the codes that abort a wait
- `tws-api-architecture.md` -- contract qualification, clientId strategy
