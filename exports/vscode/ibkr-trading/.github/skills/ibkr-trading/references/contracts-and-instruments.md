# Contracts and Instruments

Building the right `Contract` for each asset class, and reading the venue parameters that decide whether
an order is well-formed.

Most IBKR integrations are written against one asset class and quietly assume its rules are the API's
rules. They are not. Tick semantics, size semantics, the meaning of `multiplier`, which `whatToShow`
returns data, and whether qualification is even required all change per class. This file states what is
general and what is per-class, so a system written for one can be extended to another without inheriting
a false premise.

## The Contract object

The documented minimum viable structure is either:

- `conId` + `exchange`, or
- `symbol` + `secType` + `exchange` + `primaryExchange` + `currency`

Derivatives require more: `lastTradeDateOrContractMonth`, `strike`, `right`, `tradingClass`,
`multiplier`.

`primaryExchange` matters more than it looks. `SMART` alone is ambiguous for symbols listed on several
venues, and the ambiguity resolves differently over time. Pin `primaryExchange` for equities.

`tradingClass` is the discriminator between contracts that share a symbol and expiry, most visibly
weekly versus monthly options. Omitting it where it is needed returns several contracts, and
qualification will not choose for you.

## Per-class construction

`ib_async` ships convenience classes; the underlying object is always `Contract`.

| Class | Constructor | Required beyond symbol/currency | Notes |
|---|---|---|---|
| Equity | `Stock(symbol, exchange, currency)` | `primaryExchange` when SMART-routed | Fractional shares are a separate permission with their own refusal codes (most of 10243-10252) |
| Option | `Option(symbol, lastTradeDateOrContractMonth, strike, right, exchange)` | expiry, strike, right, often `tradingClass` and `multiplier` | Strike must exist. Discover, never construct, strikes |
| Future | `Future(symbol, lastTradeDateOrContractMonth, exchange)` | expiry or `localSymbol` | Expiry format is contract-month or a full date depending on the contract |
| Continuous future | `ContFuture(symbol, exchange)` | | Data only. **Not tradable.** Resolve to the front `Future` to place orders |
| Future option | `FuturesOption(...)` | as Option plus the future's parameters | |
| Spot FX | `Forex('EURUSD')` | | The API `symbol` is the base currency alone (`EUR`), with `currency` the quote |
| CFD | `CFD(symbol, currency=...)` | | For FX-pair CFDs the split form is required: `CFD('EUR', currency='USD')` |
| Crypto | `Crypto(symbol, exchange, currency)` | exchange (e.g. `PAXOS`), currency | Permissions and venue vary by region |
| Index | `Index(symbol, exchange, currency)` | | Data only, not tradable |
| Bond | `Bond(secIdType='ISIN', secId=..., exchange=...)` | an identifier | Its own details callback |
| Combo | `Contract(secType='BAG', ...)` with `comboLegs` | legs with `conId`, `ratio`, `action`, `exchange` | See below |

**Qualification is not uniform.** `qualifyContractsAsync` is a no-op for a fully specified spot FX
contract, and mandatory for options, futures, CFDs and anything ambiguous. Two rules hold everywhere:

- A returned `conId` of `0` or negative is a **placeholder, not a contract**. Reject it and retry.
  Never cache it.
- **Clear the qualified-contract cache on every reconnect**, under the same lock as the fast-path read.
  Contract data can be dropped during a reconnect burst, and a stale cache outlives the session it was
  built for.

## Minimum price increments: `minTick` is not the increment

This is the most commonly mis-implemented rule in the API, and it produces error **110** on prices that
look correct.

IBKR's own wording: `ContractDetails.minTick` "specifies the smallest possible minimum increment
encountered on **any exchange or price**". It is a floor across every venue and every price band, not
the increment in force for your contract, on your exchange, at your price.

The actual increment comes from **market rules**:

1. `reqContractDetails` returns `ContractDetails.marketRuleIds`, a list parallel to the valid-exchanges
   list. Index into it with the position of your exchange.
2. `reqMarketRule(marketRuleId)` returns, on the `marketRule` callback, an array of `PriceIncrement`
   with `lowEdge` and `increment`.
3. The increment in force is the one whose `lowEdge` band contains your price.

Snapping to `minTick` when the band's increment is coarser produces a price the venue rejects. Snapping
to the band increment is correct everywhere, including for instruments with a single band.

Three further traps:

- **Read the increment from the ORDER contract's details, not the data contract's.** Where the two
  differ (a CFD traded against a spot contract used for data), their increments differ too.
- **`minTick` is unpopulated on a `Contract`.** It lives on `ContractDetails`. Reading
  `contract.minTick` off a qualified contract yields a default, and your rounding becomes a silent
  no-op.
- **FX and FX CFD market rules default to a coarser increment than 1/10 pip**, and the terminal can
  be switched to 1/10 pips (Global Configuration, Display, Ticker Row, "Allow Forex trading in 1/10
  pips"). IBKR's own page states the default inconsistently (1/2 pip in one bullet, 1/5 in the next),
  which is itself a reason to read the market rule rather than assert a number. The increment your
  orders must satisfy therefore depends on a GUI setting on the machine running the terminal. This is
  the same class of unversioned local input as order presets: audit it, and prefer reading the market
  rule at runtime over any table you maintain.

Round with integer tick-steps via `Decimal`, validate the raw price, round, then re-validate. Round
bracket protective legs *away* from the entry and force at least one increment of clearance, so a
stop and an entry can never collapse onto the same price.

## Size semantics differ per class

`minSize` and `sizeIncrement` on `ContractDetails` do not mean the same thing everywhere, and reading
them as a universal venue floor is how dust orders and rejected orders both get produced.

- **Equities**: whole shares unless fractional trading is permitted for the account, the instrument and
  the order type. All three must hold; the refusals are distinct codes.
- **Futures and options**: integer contracts. `multiplier` is real and load-bearing for notional.
- **FX CFDs on SMART**: the reported minimum is **quantity precision** (on the order of 1e-7), not a
  venue floor. Applying it as a floor erases your lower bound.
- **Metal CFDs**: a real venue minimum, in the instrument's unit (ounces).
- **Spot FX on IDEALPRO**: precision, with real per-currency floors that are not in that field.
- **`multiplier` is `None` or `1` for FX and metals.** A canonical contract-size table is required; a
  multiplier fallback silently mis-sizes.

Consequence for sizing code: keep one canonical unit internally, convert to venue units only at the
wire, convert back on trade events, and treat a minimum as an **abort threshold**. A minimum that
rounds a degenerate input *up* turns a sizing bug into a live order.

## Option chains

Do not construct strikes. Request them:

```python
params = await ib.reqSecDefOptParamsAsync(
    underlyingSymbol='IBM', futFopExchange='', underlyingSecType='STK', underlyingConId=8314
)
```

`futFopExchange` empty means all exchanges. The response carries expirations, strikes, `multiplier` and
`tradingClass` per exchange. Take the intersection with what you can trade, then qualify the specific
contract.

Chains are large. Subscribing market data for a whole chain will exhaust market data lines immediately;
budget the subscription, or use snapshots and accept their billing.

## Combos and spreads

A spread is a `Contract` with `secType='BAG'` and a list of `comboLegs`, each carrying the leg's
`conId`, `ratio`, `action` and `exchange`. Two documented pricing rules constrain the design:

- **Per-leg pricing** (via `OrderComboLeg.price`, assembled into `Order.orderComboLegs`) is permitted
  only with **at most 2 legs**, and only on a **NonGuaranteed** spread.
- **More than 2 legs** must be priced as an overall order (`lmtPrice`) and **must not** be
  NonGuaranteed.

Leg `conId`s must be qualified first. A combo built from unqualified legs fails in ways that do not name
the leg at fault.

## `whatToShow` per class

| Class | Default | Notes |
|---|---|---|
| Equities, futures | `TRADES` | `ADJUSTED_LAST` for backtests needing split/dividend adjustment |
| Spot FX, FX CFDs | `MIDPOINT` | `TRADES` returns nothing; there are no prints |
| Options | `TRADES`, often thin | Illiquid strikes return sparse or empty series legitimately |
| Indices | `TRADES` | |
| Any class, spread analysis | `BID_ASK` | Counts as **2 requests** toward pacing limits |

An empty historical response is not an error. Distinguish "no data for this contract and setting" from
pacing and from duration caps before retrying.

## Data contract versus order contract

For some instruments the contract you trade and the contract you can get data for are different objects.
FX-pair CFDs are the clearest case: they trade, and they serve no market or historical data. The tell is
a `2127` immediately preceding a `366` *(observed diagnostic; 2127 is absent from IBKR's published
table)*; a lone `366` has other causes and deserves proof rather than assumption.

Where the split exists, resolve the underlying data-capable contract for every data path and keep the
tradable contract for orders. Then remember the increment rule above: read venue parameters from the
contract you are actually placing.

## Applicability: which failure modes bite which class

The traps documented in `venue-boundary-failure-modes.md` are not universal. This matrix says where to
look first.

| Failure mode | Equities | Options | Futures | Spot FX | CFDs |
|---|---|---|---|---|---|
| Tick conformance (110) via price bands | Yes | Yes | Yes | Yes | Yes |
| Data contract differs from order contract | No | No | No | No | **Yes** (FX pairs) |
| Minimum is precision, not a floor | No | No | No | Yes | Yes |
| `multiplier` absent, canonical size table required | No | No | No | Yes | Yes |
| Entity-dependent contract routing | Rare | Rare | Rare | **Yes** | **Yes** |
| Netted positions, no reduce-only | Account-dependent | Account-dependent | Yes | Yes | **Yes** |
| Session-reopen stub bars in history | No | No | Venue-dependent | **Yes** | **Yes** |
| Fractional-size refusal codes | **Yes** | No | No | No | No |
| Chain size exhausts data lines | No | **Yes** | Curve-dependent | No | No |

## Related

- `error-codes-and-verdicts.md` - what a refusal code means and what your library does with it
- `venue-boundary-failure-modes.md` - the adapter layer that builds these objects, and the FX,
  metals and CFD depth that the matrix above points at
- `order-types-and-attributes.md` - the capability vocabulary and how to resolve it per contract
- `event-driven-data.md` - subscriptions, bar construction, pacing
