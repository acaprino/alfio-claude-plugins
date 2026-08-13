# Venue Questions and Probes

What to do when IBKR's documentation does not answer the question your design depends on.

This is the most common failure mode in a mature IBKR integration, and it does not look like a bug. It
looks like a decision: someone needed to know how the venue behaves, the documentation was silent or
ambiguous, a plausible answer was adopted, and the system was built on it. The answer was never wrong in
a way anyone could see, because nothing ever tested it. It surfaces later as an incident, or as a
mitigation built for a hazard that could not occur, or as a mitigation removed for a hazard that could.

The remedy is not more reading. It is a discipline about what counts as an answer.

## The evidence ladder

Rank every claim about venue behaviour by how it was obtained. Record the rank next to the claim.

| Rank | Source | Admissible as? |
|---|---|---|
| 1 | **Your own probe against a live or paper gateway**, with the transcript kept | Proof, for the shapes you probed |
| 2 | **A direct read of an IBKR documentation page**, quoted verbatim with its URL | Proof, if the sentence actually says it |
| 3 | **IBKR support or a ticket response**, in writing | Strong, but support contradicts itself across tickets |
| 4 | **The client library's source code** | Proof about the *library*, never about the venue |
| 5 | **Community claims**: forum posts, Stack Overflow, blogs | Hypothesis. Never a basis for a design decision |
| 6 | **A search-engine summary or an AI answer** | **Not evidence at any strength.** See below |

**Rank 6 is a trap with a specific failure mode**, and it has burned real integrations: a search result
summarises a page as containing a claim, the page is opened, and the claim is not there. The summary
synthesised it from surrounding context. A claim that cannot be located as a quoted sentence on the page
it is attributed to **does not exist**. Open the page. If the sentence is not in it, the question is
still open.

**Silence is a finding.** "The official bracket-order documentation says nothing about partial parent
fills" is a measured result worth recording, not a failed search. Record it with the date and the URL
checked, so the next person does not repeat the search and reach a different conclusion by luck.

## Provenance tags

Tag every venue-behaviour claim in your own repository. Three tags are enough:

- **`MEASURED`**: a probe transcript exists. Note which shapes were probed; a result measured on a STP
  order says nothing about a LMT order.
- **`DOCUMENTED`**: a verbatim quote and URL exist.
- **`ASSUMED`**: neither. This is not a defect; unmeasured assumptions are unavoidable. Hiding them is
  the defect. Every `ASSUMED` tag on a path that can move money is a queue item.

A decision record that cites an `ASSUMED` claim as its justification is a decision record that expires
the moment anyone measures.

## The probe instruments

### `whatIf=True`: the venue's verdict with no market risk

Setting `Order.whatIf = True` sends the order for a credit check instead of to a destination. The
estimated post-trade margin comes back on the `OrderState` in the `openOrder` callback. Equivalent to
TWS's "Preview" and its Margin Impact panel. In `ib_async`, use `whatIfOrderAsync(contract, order)`:
it registers the response future and returns the `OrderState`, whereas on the plain `placeOrder` path
the library discards the what-if response entirely and the `Trade` never sees a verdict.

It is also the fastest way to learn whether the venue will accept an order *shape*: attributes, contract
type, TIF combinations, price conformance. A refusal comes back as an error code without anything ever
resting on the book.

**IBKR publishes a courtesy budget for it, and it is tight.** Verbatim from the documentation:

- "keep the ratio: 10 order submissions: 1 what-if request"
- "do not overuse the what-if request (> 1 what-if request per minute)"
- "cancel the what-if order after margin review"

A probe harness that fires dozens of shapes in a loop violates all three. Space them, cache the results,
and treat the transcript as an artifact worth keeping so nobody re-probes what is already known.

Two limits to know before trusting a `whatIf` result:

- **A `whatIf` pass is not a guarantee of acceptance.** It is a credit check. Rejections that depend on
  the state of the book, on the terminal's own presets, or on timing can still refuse the real order.
- **A `whatIf` refusal is a real refusal of that shape**, and that is the direction of inference you
  can rely on.

### A paper order placed and cancelled

The used-in-anger path. Some behaviours only exist on a real submission: terminal preset interference,
staged bracket transmission, the transient states, the actual verdict window. Use a limit price far
from the market so nothing fills, place, read every channel, cancel, and confirm the cancel landed.

This is the only instrument that answers questions about *lifecycle*, as opposed to *acceptance*.

### `reqContractDetails` and `reqMarketRule`

Read-only, cheap, and the answer to every "what does this instrument actually allow" question:
permitted order types, permitted TIFs, valid exchanges, minimum increments per price band. Run it
before assuming an attribute is unsupported. If the contract details permit what your order was refused
for, the rejector is not the venue.

### A reversible terminal config change

The discriminator between "the venue refuses this" and "this terminal refuses this". Change one setting,
re-probe, change it back. Record the result. **Do not ship a dependency on the changed setting**: a
behaviour that only works with a checkbox ticked on one machine is not a property of your system.

## Writing an open question

Keep a register. One entry per unknown, deleted when answered rather than annotated, with the answer
moving into the durable reference. Each entry states three things:

1. **What is unknown**, precisely enough that a probe could settle it.
2. **What breaks while it stays unknown.** If nothing does, it is curiosity; deprioritise it honestly.
3. **The cheapest experiment that settles it**, named concretely.

The third item is what makes the register useful. An unknown without a proposed measurement is a
complaint.

Two rules keep the register honest:

- **A question answered for one shape is not answered.** "Refused on STP orders, CFD and spot alike" is
  a measured result about STP orders. Whether a LMT parent behaves the same is a separate entry until
  separately measured.
- **A decision already shipped on an unmeasured premise is a defect in the register, not just in the
  code.** Record which decisions depend on the entry, so the answer propagates when it arrives.

## Questions the documentation does not answer

These recur in every non-trivial IBKR integration. As of 2026-08-13 the reference documentation
settles none of them; the first now has a support-stated answer, recorded below. Each is listed with
the measurement that settles it, so you can answer it for your account and instruments rather than
inheriting someone's guess.

**Do bracket children activate on a partial parent fill?**
The bracket and API reference pages say nothing; checked directly, and that silence is real. The
answer now has documentation-grade support from outside the reference: an IBKR staff reply on the
Campus "Placing Complex Orders" lesson (2023-10-11) states children are held "until its parent fills"
and activate "once the parent order is completely filled". Grade it DOCUMENTED (support-stated) rather
than settled: verify for your account by logging `filled`/`remaining` on every fill event and reading
the children's state against the next real partial.

**Does TWS resize bracket children to the parent's cumulative fill?**
Same silence, same measurement. Note that `ocaType` values 2 and 3 ("proportionately reduced in size")
are **not** this mechanism: they act on OCA siblings when one of them fills, and the OCA documentation
never mentions `parentId`. If TWS does not resize, the client must, on the fill path, with a race
between the fill and the correction.

**What does `cancelOrder` guarantee?**
It is a socket write with no acknowledgement; the usual client-side transition is `PendingCancel`
(ib_async marks a staged `transmit=False` leg `Cancelled` directly instead). Unknown: what TWS does
with a cancel received while disconnected or mid-fill, and whether `PendingCancel` can persist without
reaching a terminal state. Settle it by killing the gateway mid-cancel on paper and reading the order's
state on reconnect. Note two documented constraints: the EClient API's `cancelOrder` takes an
`OrderCancel` object (ib_async wraps it: `cancelOrder(order)`), and **an API client cannot cancel an
order placed by a different client ID**; only `reqGlobalCancel` reaches those, and it cancels
everything.

**Which order modifications amend in place, and which cost queue priority?**
IBKR documents *what* to modify (price, size, TIF) but never says, field by field, whether the venue
sees an amend or a cancel-and-replace. For a strategy that reprices while queued, that difference is
the strategy. Settle it by placing a displayed limit order in the book, modifying one field at a time
against an untouched control order, and comparing status sequences, exchange-side identity where it is
exposed, and fill priority. Modifying a **partially filled** order is a separate entry: IBKR's
modification page carries no warning about it, which is not the same as it being safe.

**Is callback ordering guaranteed across `openOrder`, `orderStatus`, `execDetails` and
`commissionReport`?**
IBKR documents that duplicate `orderStatus` messages are common and that a market order's execution may
not produce a `Filled` status at all, but publishes no ordering or completeness guarantee across the
four channels. Anything that reduces them into state must therefore be idempotent and key-based rather
than order-dependent. Settle the actual behaviour for your account by stamping arrival sequence and
time on all four during partial-fill bursts, cancel-versus-fill races and reconnects.

**Is there an order-rate limit distinct from the 50-requests-per-second message rate?**
The documented pacing page counts *requests for data*; no retrieved IBKR source states an
orders-per-second cap, a duplicate-order guard, or the semantics of a "potential duplicate order"
warning. Settle it by isolating order placement, modification and cancellation bursts from data
requests and recording where acknowledgement latency, warnings or a session termination appear. Note
the documented cost of getting it wrong in reject mode: three pacing breaches end the API session.

**Does a terminal-simulated stop survive its terminal?**
Simulated order types are held by TWS/Gateway or IBKR rather than resting at the venue. Undocumented:
whether a simulated stop re-arms after a hard terminal crash, or simply does not exist until the
process returns. Settle it on paper: place a simulated stop and, where the venue offers one, a native
stop, kill the terminal, drive the price through the trigger, restart, and read both orders' states.
While unmeasured, treat a dead Gateway holding simulated stops as an unprotected position
(`reconnection-resilience.md`).

**What does GTC do at a session boundary?**
On venues where GTC is simulated, IB deactivates the order at session close and re-arms it at the next
open, described as transparent to the client. Unobserved: what the order reports as while deactivated,
and whether a reconciliation snapshot taken in that window sees it as working. Settle it by leaving a
far-from-market GTC order on paper across a session close and reading its status either side.

**Is an order attribute refused universally or only for certain shapes?**
Attribute refusals are frequently order-type-specific and contract-specific. The wording "may not be
specified for **this** order" is a hint that the refusal is scoped. Probe the attribute against each
order type you actually use before concluding it is unavailable. Note that IBKR's published table does
document AON constraints (10236 "Child has to be AON if parent order is AON", 10237 "All or None ticket
can route entire unfilled size only"), which is evidence the attribute exists on brackets under
conditions, and that a refusal is about the shape rather than about support.

**What is the real minimum increment at my price level?**
`ContractDetails.minTick` is documented as "the smallest possible minimum increment encountered on any
exchange or price". It is a floor across everything, not the increment in force for your contract on
your exchange at your price. See `contracts-and-instruments.md`.

## Related

- `error-codes-and-verdicts.md` - grading a code you have never seen
- `contracts-and-instruments.md` - market rules, increments, per-class contract construction
- `gateway-verification.md` - the tooling that runs these probes against a disposable paper gateway
- `order-lifecycle-contracts.md` - the verdict window, and what `placeOrder` returning proves
