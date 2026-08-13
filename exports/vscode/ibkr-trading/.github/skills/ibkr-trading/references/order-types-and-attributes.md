# Order Types, Time in Force, and Fill Modes

Which order types, liveness settings and fill modes exist, and how to find out which of them the
contract in front of you actually accepts.

The question "does IBKR support X" is almost always the wrong question. Support is **per contract, per
exchange, per account entity**, and IBKR publishes the answer in a machine-readable field that most
integrations never read. This file covers what the vocabulary means and how to resolve it for a real
contract instead of guessing.

## The capability list is a field, not a document

`ContractDetails.orderTypes` is a **comma-separated token list of everything that contract accepts**.
`ContractDetails.validExchanges` is the parallel list of venues. Both come back from
`reqContractDetails`.

The token list mixes three vocabularies that are conceptually distinct but delivered together:

- **Order types**: `MKT`, `LMT`, `STP`, `STPLMT`, `TRAIL`, `TRAILLMT`, `TRAILLIT`, `TRAILMIT`, `MIT`,
  `LIT`, `MOC`, `LOC`, `REL`, `SCALE`, `SNAPMID`, `SNAPMKT`, `SNAPREL`, `PEGMID`, `PEGBENCH`, `MTL`
- **Time in force**: `DAY`, `GTC`, `GTD`, `GAT`, `GTT`, `IOC`, `OPG`, `AUC`, `DTC`
- **Attributes and fill modes**: `AON`, `HID`, `SWEEP`, `POSTONLY`, `RTH`, `ACTIVETIM`, `DIS`, `OCA`,
  `COND`, `ALGO`, `WHATIF`, `CASHQTY`, `SIZECHK`, `PRICECHK`

**Read it before probing anything.** If `AON` is absent from the list for your contract, an All-or-None
refusal is the venue declining an unsupported attribute, not a precaution to bypass. If it is present
and the order is still refused, the refusal is about the *shape* (order type, TIF, size, or the
terminal's own settings) and probing is warranted.

Two cautions:

- The list is **per contract and per exchange**. The same symbol routed `SMART` versus routed to a
  specific venue can differ. The `orderTypes` you get back corresponds to the contract you asked about.
- **Presence in the list is not a guarantee of acceptance.** It is the venue's declaration of the
  vocabulary it understands. Combinations remain constrained, and the terminal layer can still veto.
  Presence rules things *out* reliably; it rules things *in* provisionally.

This is the first step of every capability question. The probe is the second, and
`venue-questions-and-probes.md` covers when it is warranted.

## Time in force: how long the order stays alive

| TIF | Meaning | Notes that bite |
|---|---|---|
| `DAY` | Dies at the end of the regular session | The default when the field is left empty. Leaving `tif` unset is not "no opinion"; it is a choice of DAY |
| `GTC` | Good til cancelled | Not universally native. See the simulation note below |
| `GTD` | Good til a date | Requires `goodTillDate`, and its time zone handling is a common source of surprise |
| `GAT` | Good after time | Requires `goodAfterTime`. The order is inert until then |
| `GTT` | Good til time | |
| `IOC` | Immediate or cancel | Fills what it can now, cancels the rest. Partial fills are expected, not exceptional |
| `FOK` | Fill or kill | A documented `Order.tif` value in its own right ("if the entire order does not execute as soon as it becomes available, the entire order is canceled"). It rarely appears as a capability token in `orderTypes`, so verify it by probe rather than by token; `IOC` + `allOrNone` approximates it only where AON is itself supported (10236/10237 constraints apply) |
| `OPG` | At the open | Routed for the opening auction only |
| `AUC` | Auction | Venue-specific |
| `DTC` | Day til cancelled | Deactivated at session end rather than cancelled, and re-armed |

**The GTC simulation caveat is the one that produces silent surprises.** On venues where GTC is not
native, IB simulates it: the order is deactivated at session close and re-armed at the next open,
described as transparent to the client. What that order reports as *while deactivated*, and whether a
reconciliation snapshot taken in that window classifies it as working, is not documented. If your system
reconciles open orders on a timer across a session boundary, this is a measurement you owe yourself.
See `venue-questions-and-probes.md`.

**Leaving `tif` empty is a decision.** Value it explicitly on every leg of every order. A default that
differs from your intent is indistinguishable in the code from an intent you never had.

## Fill modes and execution attributes

| Attribute | Type | Effect | Where it bites |
|---|---|---|---|
| `allOrNone` | bool | Do not fill unless the whole quantity can fill | Support is per contract and per order type. `10236`: a child must be AON if the parent is AON. `10237`: an AON ticket can route entire unfilled size only |
| `minQty` | int | Minimum acceptable fill size | Unset by default (`UNSET_INTEGER`), not zero |
| `sweepToFill` | bool | Prioritise speed over price across venues | Equities-oriented |
| `blockOrder` | bool | Large-size block handling | Instrument-restricted |
| `hidden` | bool | Not displayed in the book | Venue-restricted; some venues reject outright |
| `notHeld` | bool | Releases the venue from price/time obligation | Meaningful for `REL` and discretionary routing |
| `outsideRth` | bool | Eligible outside regular trading hours | If the order type or destination cannot honour it, TWS **ignores it and warns with 2109** rather than rejecting |
| `discretionaryAmt` | float | Hidden price discretion beyond the limit | Equities |
| `percentOffset` | float | Offset for relative order types | Only meaningful for the types that define it |
| `ocaGroup` / `ocaType` | str / int | One-cancels-all membership and reduction behaviour | See the OCA note below |

**`ocaType` values 2 and 3 mean "proportionately reduced in size" for OCA siblings when one of them
fills.** They act between members of the same OCA group. They are not a parent-to-child mechanism, and
the OCA documentation never mentions `parentId`. Do not reach for `ocaType` to solve a bracket sizing
problem; it does not address it.

**`advancedErrorOverride` is a string, not a flag.** Its declared type is `str = ""`, and IBKR
documents the accepted value: parameters obtained from `advancedOrderRejectJson`, the payload that
arrives with an advanced rejection (`trade.advancedError` in `ib_async`). Assigning a boolean sends a
nonsense string and proves nothing about whether an override was applied.

## Order types worth knowing precisely

- **`MKT`**: no price, immediate. On illiquid instruments this is how you discover the width of the
  book the expensive way.
- **`LMT`**: the workhorse. Price must satisfy the contract's minimum increment at your price band, not
  just `minTick`. See `contracts-and-instruments.md`.
- **`STP`**: becomes a market order when the trigger is touched. The trigger method itself is
  configurable and venue-dependent.
- **`STPLMT`**: becomes a limit order at the trigger. Safer on gaps, and can fail to fill entirely,
  which is the trade being made.
- **`TRAIL` and `TRAILLMT`**: trailing by amount or percent. The trail is maintained by IB, so the
  order's behaviour depends on IB's server-side state, not on your process being alive.
- **`REL` (Relative / Pegged-to-Primary)**: pegs to the NBBO with an offset. Commonly paired with
  `notHeld`.
- **`MIDPRICE`**: attempts to fill between bid and ask. US and SMART only.
- **`MOC` / `LOC`**: auction-only, with venue cutoff times that are not the session close.
- **Algos** (`Adaptive`, `TWAP`, `VWAP`, `ArrivalPx`, `DarkIce`, `Accumulate/Distribute`): delivered
  through `algoStrategy` and `algoParams`, gated by the `ALGO` token in `orderTypes`.

**Trigger methods matter for stops.** The price event that fires a stop (last, bid/ask, double bid/ask,
midpoint) is configurable per order and defaults differently per instrument class. Two systems with the
same stop price can trigger at different moments. Set it explicitly when it matters.

## How order type, TIF and attribute interact

There is no single global compatibility table, because the answer is a three-way function of order
type, venue and instrument, and IBKR does not publish it as a matrix. What exists is:

1. **`ContractDetails.orderTypes`** for the vocabulary that contract accepts.
2. **Refusal codes** that name the incompatibility when a combination is rejected, e.g. 2109 for an
   ignored `outsideRth`, 10236/10237 for AON constraints, 10268-10270 for retired attributes.
3. **`whatIf=True`** to test a specific combination without market risk.

The practical procedure, in order, for any "can I do X on Y" question:

1. Qualify the contract and read `orderTypes` and `validExchanges`.
2. If the token is absent, stop. The answer is no, for that contract on that exchange.
3. If present, build the exact order and submit it with `whatIf=True`. Respect the documented budget:
   at most one what-if per minute, roughly one per ten real submissions, and cancel it afterwards.
4. If the what-if passes but the real order is refused, suspect the terminal layer: presets,
   precautions, and messages. Discriminate with a reversible config change, and do not ship a
   dependency on it.
5. Record the result with the shape it was measured on. An answer measured on a `STP` parent says
   nothing about a `LMT` parent.

**Retired attributes are a real category.** `EtradeOnly` (10268), `firmQuoteOnly` (10269) and
`nbboPriceCap` (10270) are no longer supported and will refuse orders that still set them. Library
defaults have historically carried these; check what your library sends rather than what your code sets.

## Related

- `bracket-orders.md` - the bracket in depth: variants, TIF interactions, the documented silences
- `contracts-and-instruments.md` - `orderTypes` lives on `ContractDetails`, alongside the increment rules
- `error-codes-and-verdicts.md` - what a refusal code means, and what your library does with it
- `venue-questions-and-probes.md` - when to probe, and what counts as an answer
- `gateway-verification.md` - the prober that dumps this matrix for your own contracts
