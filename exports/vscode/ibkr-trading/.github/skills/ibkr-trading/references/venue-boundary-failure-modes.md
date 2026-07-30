# Venue Boundary Failure Modes (Contracts, Ticks, Sizing, Async Rejections)

The hardest IBKR production bugs do not live in your strategy. They live at the adapter boundary where canonical intent (symbol, lots, prices) is translated into IBKR `Contract` and `Order` objects, and where IBKR answers asynchronously. `placeOrder` and `reqMktData` return without raising; IBKR accepts or rejects *later*, through `errorEvent`, with a numeric code. An entire family of silent failures lives in that gap: orders that reach FIRED with no live order, orders sized from a degenerate price, orders mis-routed by contract type, rejections that no channel is ever told about.

This file is the checklist for that boundary. It is distilled from a real multi-cluster remediation campaign on a retail EU (IBIE) account trading FX and metals.

## When to use

Writing or reviewing the layer that converts your internal order/price/volume model into ib_async contracts and orders, or that reads prices for position sizing. If you only place plain stock market orders at SMART with integer share quantities, most of this will not bite you. It bites FX, metals, CFDs, bracket orders, conversion-rate sizing, and any non-USD-base account.

## The single shared failure mode

> `placeOrder` / `reqMktData` return "success", IBKR rejects asynchronously via `errorEvent`, the rejection is swallowed, and the signal reaches FIRED (or the order is sized from a degenerate price) with no visible error.

Everything below is a specific instance of that pattern, plus the units/contract mistakes that make a "successful" call meaningless.

## 1. Async rejection ingress (the meta-bug)

A broker call returning without an exception says nothing about acceptance. IBKR rejects asynchronously through `errorEvent`. If you do not subscribe `errorEvent` and route rejection codes into your order lifecycle, the order silently dies while your system believes it is live.

- Subscribe the handler: `ib.errorEvent += self._on_error`.
- Map rejection codes to a cancelled/failed lifecycle event. Rejection codes seen in production: `{103, 105, 110, 135, 161, 201, 202, 388, 478, 503, 504, 10148, 10318}`.
- Both `errorEvent` and `orderStatusEvent` can fire for the same TWS rejection. De-duplicate by `orderId` so one rejection raises one cancellation, not two.
- Keep the dispatch log at DEBUG, not INFO. A per-dispatch INFO line scales your CloudWatch (or equivalent) ingest cost with event volume.

```python
REJECTION_CODES = {103, 105, 110, 135, 161, 201, 202, 388, 478, 503, 504, 10148, 10318}

def _on_error(self, reqId, errorCode, errorString, contract):
    if errorCode in REJECTION_CODES and reqId in self._live_order_ids:
        if reqId not in self._already_cancelled:        # de-dupe vs orderStatusEvent
            self._already_cancelled.add(reqId)
            self._dispatch_event("order_cancelled", reqId, errorCode, errorString)

ib.errorEvent += self._on_error
```

## 2. Price/tick conformance (errors 110 -> 135)

IBKR rejects any price that is not an exact integer multiple of the contract `minTick` with **error 110** ("price does not conform to the minimum price variation"). On a bracket the parent's 110 cascades to **error 135** on the children and the whole order dies. `place_order` still returned success, so the signal reaches FIRED with no live order.

- **`minTick` lives on `ContractDetails`, not on the `Contract`.** Reading `contract.minTick` off a qualified `Contract` does not give you the venue tick in ib_async; the value falls back to a tiny default and your rounding becomes a silent no-op. Call `reqContractDetailsAsync` and read `details.minTick`.
- Snap every price (entry, SL, TP) to `minTick` *before* `placeOrder`. Flooring only the quantity while passing full-precision float prices is the original sin here.
- Round bracket SL and TP **away from entry** (stop further from entry, target further from entry) and force each at least **one tick clear** of the rounded entry. Independent nearest-tick rounding can collapse a tight bracket to `sl == entry` or `tp == entry`: a naked or instantly-triggering stop.
- **Validate raw, then round, then re-validate.** If you round before `validate_bracket()`, you nudge an incoherent input into a "valid" one instead of rejecting it. Validate the raw prices first (so bad input is rejected), then round, then re-validate the rounded bracket.
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

This is **bypassable in code**, not an account-side-only limit: route FX through **CFD contracts**. The same order placed as a CFD is accepted with normal retail margin (for example ESMA 30:1), no 201. Prove it cheaply before migrating: a `whatIf=True` order on the CFD form returns margin figures with no 201 and no market risk.

Do NOT chase override paths for this 201: it is an account/compliance rejection, not an order precaution (precautions are the 10xxx series). "Bypass Order Precautions for API Orders" and `Order.advancedErrorOverride` have no effect on it.

- Forex CFDs require the **split base/quote form**: `CFD(symbol="EUR", currency="USD")`. The 6-letter form `CFD(symbol="EURUSD")` is rejected with **error 200** "no security definition found".
- **Gate the split on a real FX-pair check.** A non-FX 6-letter ticker must not be blindly split; fall back to the full ticker with a warning.
- Metals (for example XAUUSD) route as a **full-ticker CFD** and serve their own market data. Forex CFDs do **not** (see section 4).
- Qualify every contract before use and cache it by `(symbol, sec_type)`; reset the cache on reconnect.
- Validate your `symbol_types` config at construction (values in a known set such as `{FOREX, CFD}`). A malformed map that silently defaults to spot reintroduces the 201.
- **The CFD's venue parameters differ from the spot pair's -- never share tables across secTypes.** CFD `minTick` can be finer than the underlying spot's (e.g. EUR.USD CFD 1e-05 vs spot 5e-05): always read `minTick` from the *traded* contract's `ContractDetails` at runtime. And CFD `ContractDetails.minSize` is a display/precision value, NOT the venue order minimum -- do not apply spot (IDEALPRO) per-currency minimum-size tables to CFDs; CFD minimums are far smaller and must be derived separately.

```python
FX_PAIRS = {"EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCHF", "USDCAD", "NZDUSD"}

def to_ibkr_order_contract(symbol):
    if symbol.startswith("XAU") or symbol.startswith("XAG"):
        return CFD(symbol=symbol, currency="USD")          # metal CFD, full ticker
    if symbol in FX_PAIRS and len(symbol) == 6:
        return CFD(symbol=symbol[:3], currency=symbol[3:])  # FX CFD, split base/quote
    log.warning("Unrecognised 6-letter ticker %s: not splitting", symbol)
    return CFD(symbol=symbol, currency="USD")
```

## 4. Separate the data contract from the order contract

A contract that is valid for *trading* is not necessarily valid for *market/historical data*. **IBKR refuses historical and market data on Forex CFDs** (error **2127** then **366** "no historical data query found"). If you request candles on the FX-CFD contract, the generator never bootstraps and places **zero orders**, while metals work because metal CFDs serve their own data. That asymmetry (FX dead, metals fine) is the tell.

Resolve the **underlying spot Forex (IDEALPRO)** for every data path of an FX-CFD symbol (historical subscription, candle pagination, price snapshot). Keep the CFD for orders and `reqContractDetails`.

```python
def get_data_contract(symbol, order_contract):
    # FX CFDs trade but serve no data; pull data from the underlying spot pair.
    if order_contract.secType == "CFD" and symbol in FX_PAIRS:
        return Forex(symbol)              # IDEALPRO spot, data-capable
    return order_contract                 # metals / cash pairs unchanged
```

## 5. Sizing and units (the NaN family, errors 201 / 399)

A silently failed snapshot that returns `ask=0.0`/`NaN` for the conversion pair zeroes the order notional. A `volume_min` floor then turns that zero into a real **venue-minimum** order (EURUSD 0.01 lot rejected 399/201), or a single NaN sizes the order at the symbol **maximum** (an un-sized 100 oz XAUUSD order placed past the risk model).

**The price contract.**
- **ib_async initializes `Ticker.bid` / `Ticker.ask` to `NaN`, not `None`,** before the first tick. A readiness check of `if price is None` passes immediately and hands a `NaN`/`0.0` placeholder to sizing.
- Pin the broker boundary with an invariant: `get_symbol_price` returns a **strictly positive** bid/ask **or raises**. Never a `0.0`/`NaN` placeholder.

```python
import math
def _valid(value):
    return value is not None and not math.isnan(value) and value > 0
```

**NaN-safe guards.**
- All `NaN` comparisons are `False`, so `x <= 0` lets `NaN` through. Use `not (x > 0)`.
- `min(volume_max, NaN)` returns `volume_max`, so one `NaN` tick sizes the order at the symbol maximum. Collapse any non-finite computed volume to `0.0` as a final chokepoint, so the `volume_min` gate aborts it.

**A floor is not a safety net.**
- Do **not** floor a sub-minimum volume up to `volume_min`. A degenerate (zero/NaN-derived) sizing input must **abort** at the `volume < volume_min` gate, never be rounded into a live venue-minimum order.

**Canonical units to the very edge.**
- Keep **all** `volume_*` fields in one unit (lots). Mixed units (`volume_min`/`step` in lots, `volume_max` in venue units) make the venue-minimum check dead for FX and a regression for metals. Convert lots to venue units only on the wire, and convert wire quantity back to lots on trade events. Never let oz or base units leak into sizing comparisons or reported trade volume.

**Conversion rate.**
- Contract: `get_exchange_rate` returns a strictly positive rate or `None`, never `0.0`.
- Venues quote each FX pair in **one canonical direction only** (IDEALPRO quotes GBPUSD, not USDGBP). A USD account trading a GBP-quoted symbol has no directly quotable pair. Try the direct pair `{base}{counter}`, then the inverse `{counter}{base}` returning `1/rate`.
- The degenerate self-pair (`USDUSD`) must not resolve to a rate.

**Terminal market-data errors abort the wait.**
- A snapshot wait must abort on terminal codes for the contract: `{200, 354, 10089, 10090, 10197}`, tracked per `conId` in your error handler. Otherwise the "5-second wait" exits instantly on the NaN-vs-None bug and returns a placeholder.
- Re-check `market_open` **under the execution lock**: check-then-act on market state is a race.

## Cross-cutting systemic patterns

| # | Pattern | Where it bit |
|---|---------|--------------|
| 1 | `NaN`-vs-`None` failure contract not honoured (ib_async uses `NaN` for an absent quote) | Sizing (section 5) |
| 2 | Swallowed async rejections (`placeOrder` returns success; IBKR rejects via `errorEvent`) | Sections 1, 2, 5 |
| 3 | Non-canonical units at the venue boundary (lots vs oz / base units) | Section 5, trade events |
| 4 | Field read from the wrong object (`minTick` off `Contract` instead of `ContractDetails`) | Section 2 |
| 5 | A "rescuing" floor that masks a degenerate input (`volume_min` turning a 0 into a real order) | Section 5 |

The meta-lesson: **audit the whole family, not just the obvious site.** The first tick fix, the first guard fix, and the first CFD fix were each incomplete until the same flaw was hunted across every sibling path (every price leg, every sizing guard, every data request).

## Testing this boundary

Assert the failure contracts in tests, because they are exactly what production violated:

- `get_symbol_price` raises (does not return) on a `NaN`/`0.0`/`None` quote.
- Sizing aborts (does not floor) when computed volume is below `volume_min`.
- A single `NaN` tick does not size at `volume_max`.
- A sub-tick or short bracket is rejected or rounded coherently, never collapsed to `sl == entry`.
- The inverse conversion pair resolves when the direct pair is unquotable; `USDUSD` does not.
- An FX-CFD symbol pulls data from the spot Forex contract, not the CFD.
- A rejection `errorEvent` produces exactly one `order_cancelled`, de-duplicated against `orderStatusEvent`.

## Related

- `order-execution.md` -- bracket transmit pattern, OER, cancel-fill race, error 201 baseline
- `event-driven-data.md` -- snapshot/market-data subscriptions and the codes that abort a wait
- `tws-api-architecture.md` -- contract qualification, clientId strategy
