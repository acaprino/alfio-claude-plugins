# Error Codes and Order Verdicts

Who refused, what the refusal means, and what your client library does about it before you get a say.

The single most expensive mistake in an IBKR integration is treating `error(reqId, code, msg)` as one
channel carrying one kind of event. It is three layers of refusal multiplexed onto one callback, plus a
client-side grading step that can kill an order your venue still considers working. This file separates
them.

Ships with `assets/tws-message-codes.tsv`: all 458 codes from IBKR's published table, each tagged with
the grade `ib_async` assigns it. Search it before inventing a classification.

## The three layers that can refuse an order

An order can be stopped in three different places. They are indistinguishable by looking at the error
callback alone, and the remedy is different for each.

| Layer | Who decides | Where it is configured | Can your code change it? |
|---|---|---|---|
| **Venue / IB servers** | The exchange or IBKR's risk and compliance systems | Nowhere you control | No. Change the order or the account |
| **TWS / IB Gateway terminal** | The running terminal's own precaution and preset settings | GUI: Presets, API Precautions, Messages | Not from the API. It is local, unversioned config |
| **Client library** | `ib_async` grading the code before you see the consequence | Your process | Yes, and you must |

The terminal layer is the one that surprises people, because it is invisible from the repository. A
correct order, correct contract, correct price, refused by a checkbox on the machine running the
Gateway. Treat every terminal your bots connect to as an unversioned input to your system, audit it, and
re-audit after terminal upgrades.

## The client-side layer: `ib_async` grades before you do

This is a mechanism, not a policy, and it is the highest-value fact in this file.

```python
# ib_async/wrapper.py
warningCodes = frozenset({105, 110, 165, 321, 329, 399, 404, 434, 492, 10167})

isWarning = errorCode in warningCodes or 2100 <= errorCode < 2200
if errorCode == 110 and isRequest:
    isWarning = False
if errorCode == 110 and trade and trade.orderStatus.status == OrderStatus.PendingSubmit:
    isWarning = False
...
if not trade.isDone():
    status = trade.orderStatus.status = OrderStatus.Cancelled
    trade.log.append(TradeLogEntry(self.lastTime, status, msg, errorCode))
    self.ib.orderStatusEvent.emit(trade)
    trade.statusEvent.emit(trade)
    trade.cancelledEvent.emit(trade)
```

Read what that does:

- **Any code outside that frozenset and outside `[2100, 2200)` is fatal.** Of the 458 codes in IBKR's
  published table, **430 are graded fatal**. There is no whitelist of "codes that matter"; there is a
  tiny allowlist of codes that do not.
- **For a trade that is not `isDone()`, the status is set to `Cancelled` locally.** Nothing is sent to
  the venue. No cancel request is issued. Your system now believes the order is dead. The venue may
  still consider it working, and it can still fill.
- **`cancelledEvent` fires**, so any lifecycle code hooked there emits a cancellation for an order that
  was never cancelled.
- **110 has two carve-outs that make it fatal again**: when the error is request-scoped, and when the
  trade is still `PendingSubmit`. So 110 is warning-grade only on an already-working order. This is why
  a `110` on a staged bracket kills the parent and produces `135 "Can't find order with ID"` on the
  children a moment later *(the cascade is observed behaviour; IBKR's published note for 135 documents
  failed cancels)*.

Two of the ten codes in `warningCodes` (**492** and **10167**) do not appear in IBKR's published table
at all. The frozenset is not a transcription of IBKR's classification; it is a hand-maintained list, and
it is demonstrably incomplete in both directions.

**Consequence for every integration**: an undocumented code you have never seen arrives, `ib_async`
grades it fatal, and a live order silently leaves your books. You cannot enumerate the codes in advance.
Design for the default instead: reconcile order state against `reqOpenOrders()` / `reqExecutions()`
rather than trusting a locally-synthesized `Cancelled`.

## What IBKR's published table actually is

Retrieved 2026-08-12 from `https://ibkrcampus.com/docs/tws-api/doc/error-handling/error-codes.md`.
(Append `.md` to any IBKR docs URL for clean Markdown; the HTML site is a JS app that returns 403 to
naive fetchers. The full index is `https://ibkrcampus.com/docs/llms.txt`.)

- **458 codes**, ranging 100 to 10347.
- **It has holes.** Within 10000-10347 alone, dozens of numbers are unlisted, including the entire
  block **10255-10267**. The table jumps 10254 to 10268.
- **Codes that exist in the wild are absent from it.** `10256` ("The 'Minimum Quantity' order
  attribute may not be specified for this order"), `10257` ("The 'All or None' order attribute may
  not be specified for this order") and `10349` ("Order TIF was set to DAY based on order preset")
  are all real, all observed, and none is in the table. The first two differ only in the attribute
  named: the 10255-10267 hole looks like a per-attribute rejection family, with two members
  observed so far.

**Absence from the published table is not evidence that a code does not exist**, and it is not evidence
about the code's grade. It means you must classify it by observation. See
`venue-questions-and-probes.md` for how.

## Order precautions: what they actually are

A widespread and wrong inference is that the `10xxx` range is "the precaution layer" and therefore
overridable. It is not. The `10xxx` range is a grab-bag: fractional shares, Wall Street Horizon event
data, financial-advisor allocation, news feeds, unsupported order attributes.

Precautions are a **terminal GUI feature** with its own documented surface:

- **Global Configuration, Presets**, per instrument, "Precautionary Settings". Numeric limits on price
  percentage, ticks, size. Setting a value to `0` disables that precaution.
- **Global Configuration, API, Precautions.** Nine checkboxes, the broad one being
  **"Bypass Order Precautions for API orders"**, plus specific ones for bonds, negative yield to worst,
  called bonds, same-action pair trades, price-based volatility risk, US stocks market data in shares,
  redirect orders for stock, and no-overfill protection.
- **Global Configuration, Messages.** Per-message disable checkboxes, e.g. the 2137 Cross Side Warning.

The codes IBKR's own documentation ties to precautionary settings are **109, 163, 164, 382 and 383**,
all in the low ranges, none in `10xxx`:

| Code | Meaning |
|---|---|
| 109 | Price is out of the range defined by the Percentage setting at order defaults frame |
| 163 | The price specified would violate the percentage constraint specified in the default order settings |
| 164 | No market data to check price percent violations |
| 382 | The price specified violates the number of ticks constraint specified in the default order settings |
| 383 | The size specified violates the size constraint specified in the default order settings |

**There is no documented per-order API field that bypasses precautions.** `Order.advancedErrorOverride`
exists in the API and in `ib_async`, but it is typed `advancedErrorOverride: str = ""`, not a boolean,
and IBKR documents its value: it "accepts a string with parameters obtained from
`advancedOrderRejectJson`", the payload delivered alongside an advanced rejection (`ib_async` exposes
it as `trade.advancedError`). It is a targeted acknowledge-and-resubmit token for specific advanced
rejections, not a general bypass, and assigning `True` to it sends a nonsense string.

The reliable bypass surface is therefore terminal-side, which is precisely the unversioned local
configuration a serious deployment should refuse to depend on. If a refusal only goes away when a
checkbox is ticked on one machine, you have not fixed anything you can ship.

## Rejection, cancellation, warning: the distinctions that matter

**201 is a rejection.** "Order rejected - Reason:". The IB servers refused it. Documented causes include
large-size (LGSZ) rejects, margin, and price checks. Compliance rejections in this family have no
override: no precaution setting, no API field. Fix the order, the contract type, or the account.

**202 is a cancellation.** "Order cancelled - Reason:". An order that was active on the IB server was
cancelled. Price-check cancellations arrive here, paired with an `orderStatus` of `Cancelled`.

**Warnings arrive on a channel that is not `error` at all.** Price-capping warnings are delivered as
text on **`openOrder`**, and the capped price appears as **`mktCapPrice`** in `orderStatus`. A system
that only subscribes `errorEvent` and `orderStatusEvent` never sees the warning that its order was
capped.

**Size and precision refusals are their own family**: 388 (order size below the minimum requirement,
notice-grade), 110 (price not a multiple of the minimum increment), 10250 (size does not conform to
the minimum variation).

## The four channels an adverse verdict can arrive on

Subscribe all four or you have a blind spot by construction.

1. **`errorEvent`**: numeric codes, the layer this file is mostly about.
2. **`orderStatusEvent`**: the state machine, plus `mktCapPrice`. Both this and `errorEvent` fire for a
   single venue rejection, so de-duplicate on a seconds-scale window.
3. **`openOrder`**: free-text warnings with no code, including price capping.
4. **The library's own std loggers**: `ib_async` message-decode failures ("Error handling fields:")
   never reach `errorEvent`, carry no reqId and no contract. Route `ib_async`, `ib_insync` and
   `eventkit` loggers into your application sink or these are invisible.

## Grading a code you have never seen

A code arrives that is not in your rejection set. The procedure, in order:

1. **Look it up in `assets/tws-message-codes.tsv`.** If present, you have IBKR's own text and the grade
   `ib_async` will apply.
2. **If absent, do not infer a grade from its numeric range.** The ranges do not mean what they look
   like they mean. Record it as unclassified.
3. **Determine what actually happened to the order**, which is the only thing that decides the grade.
   Query `reqOpenOrders()` and `reqExecutions()` after the event, not your own cached state, because
   your cached state may have been written by the client-side grading step described above. An order
   still listed as working was not rejected, whatever your library did to its status.
4. **Discriminate venue from terminal.** If `reqContractDetails` shows the venue permits the attribute
   the order was refused for, the rejector is the terminal, not the venue. Test that with a reversible
   config change before touching code.
5. **Record the classification with its evidence**, and add a test that pins it. Adding a code to a
   rejection set is never free: routing a warning-grade code as a rejection emits a synthetic
   cancellation for a live order, and now your books and the venue disagree in the dangerous direction.

## The rejection set, and why it stays small

Codes that reliably mean "this order is dead at the venue", suitable for routing into an order
lifecycle: `{103, 135, 201, 202, 10318}`.

**Cancel-verdict codes are their own family and never belong in a rejection set: `161` and `10148`.**
Both report on a *cancel request*, not on the order. IBKR's own note for 10148 ("OrderId that needs to
be cancelled can not be cancelled, state:") names the documented cause: **the order had already
filled**. 161 ("not in a cancellable state") spans filled, already-cancelled and not-yet-active.
Routing either as a rejection records a dead order for one that may have **executed**: your books say
flat while the account holds a position, which is the divergence above with the sign flipped. On
receiving them, reconcile against `reqExecutions()` and `reqOpenOrders()` instead.

Codes that are **state-dependent** and must not be routed via the error set: `105`, `110`, `10349`.
Their meaning depends on whether the order was already working. `orderStatusEvent` already delivers the
pending-state kills, so a narrow rejection set loses you nothing.

**`388` needs both halves stated.** At the venue it is a size verdict ("Order size is smaller than the
minimum requirement"), but `ib_async` grades it **fatal** (it is not in `warningCodes`), so on a
not-yet-working order the library synthesises a local `Cancelled`. Treat it as a refusal of that order
and fix the size; never assume "the order continues" on the strength of its polite wording.

Connection-layer, route to reconnection rather than the order lifecycle: `503`, `504`, `1100`, `1101`,
`1102`, `2110`.

Everything else is unclassified until observed. That is the honest state, and it is safer than a
confident guess.

## Related

- `venue-questions-and-probes.md` - how to settle a behaviour question the documentation does not answer
- `order-lifecycle-contracts.md` - verdict windows, what `placeOrder` returning actually proves
- `venue-boundary-failure-modes.md` - the adapter layer where these codes are produced
- `contracts-and-instruments.md` - minimum increments, market rules, and the 110 family
