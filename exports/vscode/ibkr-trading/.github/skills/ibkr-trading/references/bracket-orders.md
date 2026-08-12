# Bracket Orders

The logic, the variants, the configuration surface, and the places the documentation stops.

A bracket looks like the simplest complex order in the API and is the one that produces the most
production incidents. The reason is that its behaviour is decided in four different places: your order
objects, the attached-order mechanism, the OCA relationship between the children, and the terminal's own
presets. Three of those four are invisible in your code.

## What a bracket actually is

Verbatim from IBKR: bracket orders "make use of the TWS API's **Attaching Orders** mechanism". A bracket
is not a distinct order type. It is:

- a **parent** order, plus
- **child** orders carrying `parentId = parent.orderId`, which the venue holds until the parent's
  condition is met, plus
- an **OCA relationship between the children**, so that one executing removes the other.

Everything else is configuration. Understanding it as "attached orders plus OCA" is what makes the
exceptions predictable instead of surprising.

The canonical structure: a BUY parent is bracketed by a high-side SELL limit (take profit) and a
low-side SELL stop (stop loss). A SELL parent by a low-side BUY limit and a high-side BUY stop.

## The transmit staging protocol

Three orders are sent as three separate `placeOrder` calls, which creates a window where the parent
could fill before its protections exist. IBKR's answer is `Order.transmit`:

- Parent and all children except the last: `transmit = False`. TWS receives them and holds them.
- **Last child**: `transmit = True`. TWS transmits it *and* all its predecessors.

Consequences that are not obvious:

- **The order of `placeOrder` calls matters.** The parent must be sent before children referencing it.
- **A failure mid-stage leaves untransmitted orders parked in TWS.** They are not live and not visible
  as working, but they exist. Reconcile with `reqOpenOrders()` rather than assuming a failed sequence
  left nothing behind.
- **A staged child shows a transient `Cancelled` before `PreSubmitted`.** This is an artifact of
  staging, not a venue cancellation. Emitting a real cancellation event on it corrupts your lifecycle.
  Confirm against `reqOpenOrders()` before believing it.
- **A validation failure on the parent kills the whole stage.** The classic sequence is `110` on the
  parent (price not conforming to the minimum increment), followed by a `135` ("Can't find order
  with ID") for each child, because their parent no longer exists. Read the first error, not the
  loudest.

## IBKR's published sample is not a production recipe

The official sample sets `orderType`, `totalQuantity`, prices, `parentId` and `transmit`. It **does not
set `tif` on any leg**. An unset TIF means `DAY`.

That produces stop-loss and take-profit children that **expire at the session close**, leaving an open
position with no protections overnight. Copying the sample verbatim into a system that holds positions
across sessions is how naked overnight exposure gets shipped.

**Value the TIF explicitly on every leg.** Not because the default is wrong in every case, but because
an unvalued field is indistinguishable from an intent you never formed. The usual production shape is
`GTC` on the protective children, so the protections live exactly as long as the position can.

## TIF per leg: the decisions

| Leg | Common choice | Why, and what it costs |
|---|---|---|
| Parent | `DAY` | The entry opportunity is usually session-scoped. A `GTC` parent means an unfilled entry crosses session boundaries and can fill on a day whose thesis has expired |
| Parent | `GTC` | Chosen when the entry level is structural rather than intraday. Requires the session-boundary behaviour below to be understood |
| Children | `GTC` | Protections outlive the session. This is the safe default for anything held overnight |
| Children | `DAY` | Only correct for strictly intraday systems that flatten before the close, and only if the flattening is guaranteed |

**The GTC session-boundary caveat.** Where GTC is not native to the venue, IB simulates it: the order is
deactivated at session close and re-armed at the next open, described as transparent to the client.
What the order reports as while deactivated, and whether a periodic open-order reconciliation classifies
it as working during that window, is **not documented**. If your system reconciles on a timer and can
act on "this order is gone", measure this before trusting it. See `venue-questions-and-probes.md`.

**Terminal presets can override the TIF you set.** Error `10349` ("Order TIF was set to DAY based on
order preset") is the observable form. Related: `10233` ("Defaults were inherited from CASH preset
during the creation of this order"). The preset lives in the terminal GUI, not in your repository, and
it applies to API orders. Audit the presets of every terminal your bots connect to, and re-audit after
terminal upgrades.

## OCA: what the children actually do to each other

The children of a bracket are an OCA group. OCA semantics are documented and worth knowing exactly,
because they are frequently misapplied to problems they do not solve.

| `ocaType` | Behaviour |
|---|---|
| 1 | Cancel all remaining orders, **with block** |
| 2 | Remaining orders **proportionately reduced in size**, with block |
| 3 | Remaining orders proportionately reduced in size, **no block** |

**"With block" is overfill protection**: only one order in the group is routed at a time, removing the
possibility of an overfill. That is a real safety property and the reason to prefer types 1 or 2 over 3.
Note that the terminal's API precautions include a "Bypass No Overfill Protection precaution for
destinations where implied natively" checkbox, so this interacts with the terminal layer too.

**Multiple OCA types cannot be used in a single OCA group.** Mixing them is a configuration error.

**Partial completion re-balances the group.** Verbatim: "Completion of one piece of the group order
causes cancellation of the remaining group orders while partial completion causes the group to
re-balance."

**The trap**: this is a *sibling* mechanism. It describes what happens among members of the OCA group
when one of *them* fills. It is not a parent-to-child mechanism, and the OCA documentation never
mentions `parentId`. Reaching for `ocaType` 2 or 3 to make children track a partially filled *parent*
does not address that problem. See the documented silences below.

## Trigger methods: the stop child can be built so it never fires

`Order.triggerMethod` decides what price event fires a simulated stop. It is compatible with some
security types and not others, and IBKR states the consequence plainly: **"If an incompatible
triggerMethod and secType are used in your API order, the order may never trigger."** No error, no
rejection, a protective leg that silently does not exist.

| Value | Method |
|---|---|
| 0 | Default for the instrument |
| 1 | Double bid/ask |
| 2 | Last |
| 3 | Double last |
| 4 | Bid/ask |
| 7 | Last or bid/ask |
| 8 | Mid-point |

| secType | Bid/ask-driven (1, 4, 8) | Last-driven (2, 3) | Default |
|---|---|---|---|
| STK | yes | yes | Last (double bid/ask for OTC) |
| CFD | yes | yes | Last |
| CFD on index | yes | **n/a** | n/a |
| OPT | yes | yes | US: double bid/ask. Other: Last |
| FOP | yes | yes | Last |
| FUT | yes | yes | Last |
| COMBO | yes | yes | Last |
| CASH (spot FX) | yes | **n/a** | Bid/ask |
| CMDTY | yes | **n/a** | Last |
| IND | **n/a** | yes | Conditions only |

Read the `n/a` cells as landmines. A last-driven trigger method on a spot FX or commodity stop is an
incompatible combination, and the documented outcome is an order that may never trigger.

**These methods apply only to stops IB simulates.** Where a stop variant is handled natively by the
venue, the specified trigger method is ignored. So the same setting can matter on one instrument and be
inert on another.

## Variants of the bracket

**1. Manual three-leg (`parentId` + `transmit`).** The canonical form above. Full control, full
responsibility. Use this for automation.

**2. Preset-driven attachment (`ptOrderType` / `slOrderType` = `"PRESET"`).** IBKR supports attaching a
profit taker and a stop loss by setting `ptOrderId`/`ptOrderType` and `slOrderId`/`slOrderType` to
`"PRESET"` on a single order object, with the child parameters taken from the terminal's Presets.

```python
order.ptOrderType = "PRESET"; order.ptOrderId = 10001
order.slOrderType = "PRESET"; order.slOrderId = 10002
```

**Do not use this in an automated system.** It moves the definition of your protective legs into
unversioned terminal configuration. The protection levels of a live strategy would then depend on a GUI
setting on one machine, changeable without a commit, invisible in review, and silently different across
environments.

**3. Explicit OCA on the children.** Assign `ocaGroup` and `ocaType` to the children yourself to choose
the reduction and block behaviour, rather than accepting whatever the implicit grouping does.

**4. Attached orders generally.** `parentId` is not limited to TP and SL. Any order can be attached to
any parent, including hedging legs and additional scaling exits. The bracket is one shape of a general
mechanism.

**5. Trailing protective leg.** A `TRAIL` or `TRAILLMT` child instead of `STP`. The trail is maintained
server-side, so it survives your process dying, which is an argument for it and a reason to reconcile
its state rather than model it locally.

**6. AON brackets.** Constrained and documented: `10236` "Child has to be AON if parent order is AON",
and `10237` "All or None ticket can route entire unfilled size only". Whether AON is accepted at all is
per contract: check the `AON` token in `ContractDetails.orderTypes` before probing. See
`order-types-and-attributes.md`.

## What the documentation does not say

Two questions, both load-bearing for correctness, neither answered by IBKR's published documentation.
This was checked directly against the bracket page rather than inferred from a search result: the
silence is real.

**Do children activate on a partial parent fill?** If children become live at nominal size while the
parent is only partly filled, the protective legs can be larger than the position they protect, and an
execution on them opens a position in the opposite direction rather than closing one.

**Does TWS resize children to the parent's cumulative fill?** If it does not, the client must, on the
fill event path, accepting a race between the fill and the correction.

Both are settled by the same measurement: drive a paper bracket parent to a partial fill and read the
children's status and quantity. Partial fills are hard to provoke deliberately on paper, so the
practical route is to log `filled` and `remaining` on every fill event and read the children's state
against the next real partial fill. Until measured, treat the hazard as open and record which of your
decisions depend on the answer.

**Do not resolve this from a forum post.** Community answers on this question contradict each other,
and at least one widely repeated claim cannot be located on the page it is attributed to.

## Failure modes to design against

- **Naked overnight positions**: `DAY` children expiring at the session close while the position lives
  on. Fixed by valuing TIF explicitly.
- **Orphaned protective legs**: the position closes by some other path (manual intervention, an
  opposing signal, a partial close), and the children rest on a flat contract. Fixed by a
  **residual-child reaper**: on a position-closed event for a now-flat contract, cancel any bracket
  children still working. Protections must live exactly as long as the position.
- **Orphaned children on a position that never opened**: if a preset mutates the children and they
  transmit while the parent never fills, GTC children rest for a position that does not exist. A reaper
  hooked on position-closed cannot collect them, because no position was ever opened. Reconcile working
  orders against positions, not only against closes.
- **Netted accounts and the not-reduce-only rule**: IBKR CFD orders are not reduce-only, and positions
  net per contract at the account level. A protective leg firing on a netted account with no position
  opens a new one in the opposite direction. Never derive a closing side from the sign of an
  absolute-valued quantity.
- **Partial closes on a shared `conId`** emit a position-modified event rather than position-closed, so
  a reaper keyed only on close events does not run.
- **Price collapse between legs**: rounding a stop and an entry to the same price, or to prices less
  than one increment apart. Round protective legs *away* from the entry and force at least one
  increment of clearance.

## Bracket checklist

- [ ] TIF valued explicitly on every leg, never left to default
- [ ] Protective children `GTC` if the position can survive a session
- [ ] Every price snapped to the increment in force at that price band, from the **order** contract's
      market rule, not to `minTick` alone
- [ ] Protective legs at least one increment clear of the entry, rounded away from it
- [ ] `triggerMethod` compatible with the instrument's `secType`, or left at 0
- [ ] `AON` presence confirmed in `ContractDetails.orderTypes` before it is set
- [ ] `ocaType` chosen deliberately, with block unless there is a reason not to
- [ ] Transient `Cancelled` during staging not treated as a real cancellation
- [ ] The staging sequence reconciled against `reqOpenOrders()` after any mid-sequence failure
- [ ] Residual-child reaper on position-closed, plus a working-orders-versus-positions reconciliation
      for children whose position never opened
- [ ] Terminal presets audited for every terminal the system connects to, and after upgrades
- [ ] Behaviour on partial parent fill measured for your account, or explicitly recorded as unmeasured
      with the decisions that depend on it

## Related

- `order-types-and-attributes.md` - TIF, fill modes, and the per-contract capability list
- `order-lifecycle-contracts.md` - verdict windows, what `placeOrder` returning proves
- `error-codes-and-verdicts.md` - 110, 135, 10349, and what the library does with them
- `venue-questions-and-probes.md` - settling the silences above
- `contracts-and-instruments.md` - market rules and the increment in force at your price
