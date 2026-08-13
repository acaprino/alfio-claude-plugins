# Order Lifecycle Reference Model

A vendor-neutral state machine, the three layers that can refuse an order, and the identifiers that
survive. Use it as the model your adapter converts *into*, so that a vendor's vocabulary is translated
once, deliberately, at the boundary, instead of leaking its assumptions through the whole system.

The model is not a claim that every broker works this way. It is a fixed set of questions, so that
"what does this vendor call an accepted order" has somewhere to be answered and recorded.

## The reference state machine

Every state is defined by **who has acknowledged what**, because that is what decides whether acting
again is safe. Names are secondary; the acknowledgement column is the model.

| State | Meaning | Who has acknowledged |
|---|---|---|
| `CREATED` | The order exists in your process and nowhere else | nobody |
| `SENT` | Handed to the transport. No acknowledgement of any kind yet | nobody |
| `VALIDATED` | The broker has checked it against the account and holds it | the broker |
| `WORKING` | Resting at the venue and eligible to trade | the venue |
| `PARTIALLY_FILLED` | One or more executions have happened, quantity remains | the venue |
| `FILLED` | Fully executed | the venue |
| `CANCEL_REQUESTED` | A cancel was sent, nothing has confirmed it | nobody |
| `CANCELLED` | Confirmed dead, with no quantity still eligible to trade | the broker or the venue |
| `REJECTED` | Refused by one of the three layers below | whichever layer refused |
| `UNKNOWN` | The state is not established, typically after a gap | nobody |

Six rules govern the transitions, and each one is a bug class when violated:

- **`UNKNOWN` is a state, not an error.** After a disconnect, a restart or a missed event, an order
  that was in flight is `UNKNOWN` until the broker says otherwise. Systems that lack this state
  silently pick `REJECTED` or `WORKING` instead, and both guesses lose money in a different way.
- **Only `FILLED`, `CANCELLED` and `REJECTED` are terminal.** Everything else means the venue may still
  act, including states whose names sound final. Never treat a not-currently-working state as death
  without corroboration from the broker.
- **`REJECTED` and `CANCELLED` must not be collapsed.** They differ in remedy: a rejection means the
  order as shaped will never work and something must change, a cancellation means the order was fine
  and is now gone. A system that reports one status for both cannot tell a retry from a re-shape.
- **Any pre-`WORKING` state can go to `REJECTED` asynchronously**, arbitrarily later than the call that
  created it, including after your process has moved on.
- **A cancel is not a rollback.** `PARTIALLY_FILLED` to `CANCELLED` leaves the executions that already
  happened. The position, the exposure and the ledger all survive the cancel.
- **A fill can arrive after a cancel request.** `CANCEL_REQUESTED` is not a pause, and the race between
  a cancel in flight and a fill in flight is won by the venue. Treat the cancel as decided only when
  the broker confirms the remaining quantity.

## The three layers that can refuse

An order can be stopped in three places. They are frequently indistinguishable from the shape of the
error alone, and the remedy is different for each.

| Layer | What it means | Typical remedy |
|---|---|---|
| **Transport acceptance** | The message was handed over and structurally taken: a socket write completed, an HTTP call returned 200, a local component accepted the call | Retry, reconnect, fix the encoding or the field types |
| **Broker validation acceptance** | The broker checked the order against your account, entitlements, margin, instrument permissions and its own risk rules, and holds it | Change the order, the account, the entitlement or the size. Nothing about the venue is implicated |
| **Venue acceptance** | The exchange or matching engine took the order and it is working | Change the order to something the venue permits, or accept that this shape is unavailable on this instrument |

Two properties of this stack are the whole point of naming it:

- **A synchronous success at one layer says nothing about the next.** A returned call, a 200, an
  allocated identifier: all of these are transport acceptance and only transport acceptance. Reporting
  them as success is the most common structural bug in a broker integration, because it converts every
  later refusal into a silent divergence between what you believe and what is true.
- **Asynchronous refusal after a synchronous success is the normal case, not an anomaly.** Design the
  ingress for it first. Subscribe to the asynchronous channel *before* placing, because the refusal can
  arrive before the placing call returns, and a handler registered afterwards misses it.

Under `local-terminal` and `bridge`, the transport is a program with opinions rather than a pipe, so it
can refuse on its own configuration. That configuration lives outside your repository and outside the
broker, which makes it invisible in code review and unversioned in deployment. When an order is refused
for an attribute the broker's own capability data says is permitted, the rejector is the local
component and no amount of code change will fix it.

## Identifiers

Three identifiers, three different jobs. Confusing them is how an integration loses track of orders it
placed correctly.

| Identifier | Assigned by | Unique within | Survives a cancel | Survives a replace |
|---|---|---|---|---|
| **Client-assigned order ID** | You, before sending | Your client session or connection, rarely the whole account | The value is spent, never reuse it | Frequently not. Many vendors implement a replace as a cancel plus a new order with a new value |
| **Broker order ID** | The broker, on validation acceptance | The account, across sessions and across clients | Yes | Vendor-specific, and this is the question to ask explicitly |
| **Execution ID** | The broker or the venue, one per fill | Globally, and permanently | Not applicable; an execution is already history | Not applicable |

The rules that follow:

- **Key durable storage on the broker order ID.** The client-assigned value is scoped to a client
  identity you may not have after a restart, and under some vendors the same order carries a different
  client-assigned value for a different user. A store that outlives a session and is keyed on it cannot
  survive the session it outlived.
- **You still need the client-assigned value**, because it is what you act with before the broker has
  answered. Write it, and its link to the intent behind it, before sending.
- **Store executions append-only, keyed on the execution ID.** Corrections and busts arrive as new
  executions rather than as edits to old ones, so a ledger that updates in place destroys its own audit
  trail, and one that sums every execution it receives double-counts every corrected fill.
- **Ask what a replace does to identity, per vendor, and record the answer with a provenance tag.**
  Mutate-in-place and cancel-and-new are both common, they are indistinguishable from the calling side,
  and code written for one silently orphans orders under the other.

## What a successful place call proves

It proves that the transport accepted the message. That is the entire claim, and it is worth stating as
a rule because the code that gets this wrong always looks correct.

- **Report "placed", never "succeeded".** The word matters, because everything downstream inherits it.
- **Await the verdict in a bounded window**, then apply the asymmetry rule: on timeout, report the
  order as placed and log the uncertainty. Claiming failure on a possibly-live order makes the caller
  re-enter on top of it and doubles the position. Claiming success on a dead one is caught by the next
  reconciliation. When you must be wrong, be wrong in the recoverable direction.
- **Measure the verdict distribution before choosing the bound.** A timeout copied from another
  integration is a guess about a different venue.
- **A cancel call has exactly the same shape.** It proves the cancel request was accepted. Between the
  request and the confirmation the order can still fill, and code that decrements exposure on the
  request rather than on the confirmation is wrong in the direction that costs money.
- **The refusal reason often lives somewhere other than the status.** Find the channel that carries the
  cause and read it there; a status of `REJECTED` with no reason attached is a support ticket you will
  write against yourself.

## Mapping a vendor's vocabulary onto this one

This is the point of the file. The failure it prevents is silent substitution: a developer reads a
vendor status, decides it is close enough to a model state, and encodes that decision nowhere. The
next person cannot tell an established fact from a guess, and the guess is defended as if it were one.

Write the map before writing the adapter, as a table in the repository, one row per vendor term:

| This model | Vendor term | Who has acknowledged | Provenance |
|---|---|---|---|
| `WORKING` | `Submitted` | the venue | DOCUMENTED |
| `VALIDATED` | `PreSubmitted` | the broker only | DOCUMENTED |
| (no counterpart) | `Inactive` | unclear: not working, not confirmed dead | ASSUMED |

Five rules make the map worth having:

1. **Map to the acknowledgement, not to the name.** Two vendors using the same English word for
   different acknowledgement levels is the normal case. Decide each row by asking who has confirmed
   what, and never by string similarity.
2. **Record the gaps in both directions.** A vendor state with no counterpart keeps the vendor's own
   term in quotes and gets no model state at all. A model state the vendor never reports means yours is
   an inference: say so in the row, because a `WORKING` you inferred is not a `WORKING` you were told.
3. **Never substitute silently.** Writing "this vendor's `Inactive` is not `CANCELLED`, and this model
   has no state for it" is a finding. Picking the nearest state and moving on is the defect.
4. **Tag every row.** A row tagged `ASSUMED` on a path that can move money is a queue item, not a
   completed mapping.
5. **The map is a claim about a version.** Re-derive it after a vendor upgrade or a client-library
   upgrade, and date it, so the next reader knows what it was true of.

The same procedure applies to identifiers and to refusal channels, and it is worth the same table. A
vendor that multiplexes three layers of refusal onto one callback needs a row per code family stating
which layer it belongs to, because that is the mapping the remedy depends on.
