# Order Lifecycle Contracts (Verdicts, Grades, Presets, Netted Closes)

`placeOrder` returning is the *beginning* of an order's story, not its outcome. The venue's verdict arrives asynchronously; the same error code means different things depending on order state; the terminal's own configuration can veto orders the venue would accept; and on a netted account a "close" is just an order like any other -- including a wrong one. This file is the contract layer for all of that.

The contracts below bite hardest on netted accounts, on instruments that are not reduce-only (CFDs in particular), and on any system that derives a closing side from stored state rather than from the venue's own position.

## When to use

Writing or reviewing the code that decides "did this order succeed?", routes error codes into an order lifecycle, closes positions, or debugs orders that die with no visible cause. Complements `order-execution.md` (how to place) and `venue-boundary-failure-modes.md` (how rejections arrive).

## placeOrder is a positive contract: await the verdict

`placeOrder` returns as soon as the local reqId is allocated. The venue's verdict typically lands within a second (sub-second in observed deployments) via `orderStatusEvent`; measure your own distribution before choosing a bound. Callers that report success immediately convert every later rejection into a silent divergence: the system believes an order is working that the venue killed.

Await the verdict with a bounded window and asymmetric semantics:

```python
_ORDER_ACK_TIMEOUT_S = 2.0     # verdicts are typically sub-second; 2 s bounds the wait
_ORDER_REFUSED  = {"Cancelled", "ApiCancelled"}
_ORDER_UNDECIDED = {"PendingSubmit", ""}
# "Inactive" is deliberately in NEITHER set: an Inactive order can still be
# live at the venue, and calling it a refusal would make the caller re-enter
# on top of a working order.

async def await_broker_verdict(trade):
    deadline = asyncio.get_running_loop().time() + _ORDER_ACK_TIMEOUT_S
    while asyncio.get_running_loop().time() < deadline:
        status = trade.orderStatus.status
        if status in _ORDER_REFUSED:
            return False, _refusal_reason(trade)
        if status not in _ORDER_UNDECIDED:
            return True, None          # PreSubmitted / Submitted / Filled
        await asyncio.sleep(0.02)
    return True, "verdict timeout"     # report PLACED and log the uncertainty
```

- **The asymmetry rule**: on timeout, report the order as **placed** and log the uncertainty. Claiming failure on a possibly-live order makes the caller re-enter on top of it; claiming success on a dead one is caught by reconciliation. Choose the recoverable error.
- **The refusal reason is not in `orderStatus`.** When ib_async flips a pending order to cancelled, it appends the cause as a `TradeLogEntry` with an `errorCode` on `trade.log`. Read it there; the status object alone says only "Cancelled".

## Warning-grade vs rejection-grade codes: the isDone() rule

ib_async cancels an order in response to an error **only `if not trade.isDone()`**. The same code therefore means different things by order state:

- On an order still in `PendingSubmit`: codes like **110** (tick conformance) kill it; ib_async itself emits `orderStatusEvent(Cancelled)`. This is the state in which the 110 -> 135 bracket cascade happens.
- On a **working** order (`PreSubmitted`/`Submitted`): the same **110**, a **105** (modify mismatch), or a **10349** are *warning-grade*: ib_async sets the pseudo-status `ValidationError` and the order **stays live at the venue**.

Consequence: **adding a code to your rejection-routing set is not free.** Routing a warning-grade code as a rejection emits a synthetic cancellation for an order the venue still considers working: your system believes it dead, the venue believes it live, and the order is orphaned. 105 and 110 are the codes most often wrongly added to a rejection set for exactly this reason, and the rule is worth pinning with a test named after it. The pending-state kills you would catch via the error set already arrive via `orderStatusEvent`, so you lose nothing by keeping the set narrow.

## Canonical order-state set

Handle all of these; several are commonly forgotten:

`ApiPending`, `PendingSubmit`, `PendingCancel`, `PreSubmitted`, `Submitted`, `ApiCancelled`, `Cancelled`, `Filled`, `Inactive`, plus ib_async's `ValidationError` pseudo-status (warning-grade error on a working order, see above).

IBKR's own definitions are worth reading as a ladder of *who has acknowledged what*, because that is what decides whether re-entry is safe:

| Status | IBKR's definition | Who has confirmed |
|---|---|---|
| `ApiPending` | "order has not yet been sent to IB server, for instance if there is a delay in receiving the security definition" | nobody |
| `PendingSubmit` | "the order was sent from TWS, but confirmation has not been received that it has been received by the destination" | nobody |
| `PendingCancel` | "a request has been sent to cancel an order but confirmation has not been received of its cancellation" | nobody |
| `PreSubmitted` | "a simulated order type has been accepted by the IB system and that this order has yet to be elected" | IBKR, not the venue |
| `Submitted` | "your order has been accepted at the order destination and is working" | the venue |
| `ApiCancelled` | the state when a client cancels "after an order has been submitted and before it has been acknowledged" | nobody |
| `Cancelled` | "the balance of your order has been confirmed cancelled by the IB system" | IBKR |

`ApiPending` is an IBKR-documented status, not a client invention. Two of the definitions carry their own warning: `Cancelled` is documented to "occur unexpectedly when IB or the destination has rejected your order", so it is not proof that *you* cancelled anything; and `Filled` is not guaranteed to arrive, because "market orders executions will not always trigger a Filled status". `Inactive` deserves special care: it means "not currently working" (rejected, a share-location delay, a TWS-side block), not "dead"; never treat it as a terminal refusal without corroboration.

## Terminal order presets are invisible input (error 10349)

TWS/Gateway **order presets** configured in the GUI apply to API orders. They live in the terminal, not in your code, your config, or your repo: an unversioned input that can veto or mutate orders. The observable form: every bracket entry cancelled a few hundred milliseconds after `PendingSubmit` with `10349 "Order TIF was set to DAY based on order preset"`, wholesale, while the code is correct.

IBKR's published error table stops at 10347, so **10349 is undocumented**: treat it as a real but unlisted code rather than something you can look up. Two documented neighbours confirm the mechanism exists: **10335** "Order presets cannot be applied as configured. Please review Settings and Rapid Order Entry Configuration for consistency" and **10233** "Defaults were inherited from CASH preset during the creation of this order". Any code in that band arriving on a correct order should send you to the terminal's preset configuration.

- **The discriminator**: pull `reqContractDetails` for the instrument and read the permitted TIF list. When the order is refused for an attribute the contract details say is permitted (GTC listed, GTC rejected), **the rejector is the terminal, not the venue**.
- **Diagnose with a reversible config test first**: change/remove the preset in the terminal and retry, before touching code. If a preset is the cause, code-side "fixes" (e.g. lowering bracket children to DAY) trade a visible failure for a silent protection downgrade; the preset must be removed instead.
- **The GTC-bracket recipe is necessary, not sufficient** (see `order-execution.md`): a preset can override child TIFs or cancel staged orders outright. Worst case if mutated children *do* transmit: GTC children resting for a position that never opened, which a reaper hooked on position-closed events cannot collect because no position ever existed. Audit the preset configuration of every terminal your bots talk to, and re-audit after terminal upgrades.

## Closing a netted position: side is data, not arithmetic

IBKR CFD/FX accounts are **netted**: one position per contract, and a "close" is an ordinary opposite-side order. Two properties make the close path the most dangerous code in the adapter:

- **A wrong-side close is not a no-op and not an error.** IBKR CFD orders are not reduce-only. Closing a short with a SELL does not fail: it **doubles the short**. The failure shape: the close side is derived from `sign(position.volume)` while the position store keeps volumes as absolute values with direction in a separate field. Every "close" then goes out on the same side, and a short doubles on each attempt, silently, with no error raised at any point.
- **Fan-out multiplies it.** Sibling executors sharing one account and one netted conId can each react to the same event with a close for the same position.

**Rules:**

- Derive the close side from the **authoritative direction field** (an explicit direction field, or the signed venue position), never from the sign of a volume you may have stored as an absolute value.
- **Refuse the close when the direction is unresolved.** The wrong side doubles the position; no order leaves it untouched. Guessing is the only losing move.
- Scope event-driven closes to the symbols the executor owns, so one account-level event does not fan out into N closes.
- **Verify the close verdict like any order** (see the verdict contract above). A close path that builds its own success result without querying the venue leaves a position open that the system believes closed. If you consciously defer fixing such a hole, record the deferral and its reason where the next auditor will find it -- an applied instance of "audit the whole family" from `venue-boundary-failure-modes.md`.

## Identity: three id families, and which one survives what

- **`orderId`** is client-managed, documented as strictly increasing, and **scoped to the clientId that placed the order**. It is the id you act with (modify, cancel) and the one that cannot be reused "except to modify an existing order".
- **`permId`** is assigned by TWS and documented as the id that "can be used to identify an order in an account uniquely". It is the only identity that survives across clients and bindings, so it is the correct key for reconciliation and for any store that outlives a session. The binding case proves why: API order-id assignment on binding is independent per TWS user, so **the same order can carry different `orderId`s for different users** while its `permId` stays put.
- **`execId`** identifies an execution, one per partial fill, in a documented 4-segment form (5 for combo legs). Corrections arrive as **another `execDetails` callback with every parameter identical except the execId**, which "will differ only in the digits after the final period".

The consequence for the fill ledger is a design rule, not a detail: store executions **append-only, keyed by the full `execId`**, group a correction family by the portion before the final period, and derive economics from the latest member of each family. Summing every `execDetails` you receive double-counts every corrected fill.

## Attribution traps (why a correct rejection handler still loses events)

- **Pre-placement rejections have no order snapshot to look up.** The symbol must be recovered from the raw contract, and `contract.symbol` on a Forex contract is the **base currency alone** (`"EUR"`, not `"EURUSD"`). An event keyed on that fails every downstream subscription filter and the rejection silently vanishes. Reconstruct pair symbols from `symbol + currency`.
- **reqId and orderId share one counter.** An `Error 300, reqId 111` arriving 25 ms before `orderId=113` looks order-correlated; it is a market-data subscription error. Triage by id *type*, not proximity.
- **IBKR exposes no per-order broker timestamp** via `openTrades()`. Stamp detection time yourself, on the same clock convention as your snapshot path. And beware present-but-null keys: `payload.get("broker_timestamp", 0.0)` returns `None` when the key exists with a null value, and one `None` reaching a staleness comparison inside a catch-all handler will freeze your position state at its last good value, silently.

## Write the attribution map before placeOrder

A synthetic rejection event is only as good as its enrichment. A cancellation event carrying an unset correlation id routes to no subscriber and dies **while looking wired**. Two ordering rules:

- **Write the correlation map (`orderId`/`conId` -> strategy, symbol) *before* calling `placeOrder`**, in both single-leg and bracket paths, with rollback on placement exception. `errorEvent` can fire before a post-placement map write completes.
- **Cache an order snapshot at placement** (kind, action, quantity, price) so a synthetic lifecycle event carries real fields instead of zeros. Consumers silently drop empty events.

## Reconciling after a gap: what the requests actually reach

Two documented scopes decide what a reconnect can and cannot rediscover, and both are narrower than they look:

- **`reqOpenOrders` returns the orders of the exact clientId that asks**, and `reqAllOpenOrders` returns orders across clients **without binding them**. Visibility and modifiability are different things: only `reqOpenOrders` (and `reqAutoOpenOrders` for future orders) binds a manual TWS order to clientId 0, and an unbound manual order arrives with **API order id 0**, which IBKR documents as unmodifiable and uncancellable from the API. A recovery path that lists an order it cannot act on has not recovered it.
- **`reqExecutions` reaches the current day only** ("Only the current day's executions can be retrieved"). A reconnect that spans the day boundary therefore cannot rebuild its fill history from the API at all: the durable ledger must be yours, with Flex or statements as the audit source for anything older.

Neither request replays what happened while you were gone as events; they return present state. An order submitted just before a socket drop is in an **unknown** state, not a failed one, until it appears in one of those two answers or in your own persisted evidence.

## When the venue fails quietly: the incident-spec method

The failure modes in this file were diagnosed with a document shape worth stealing. For any incident on a venue that fails silently, write the analysis spec *before* proposing fixes:

1. **Proven facts**, each with a timestamp and source (venue log, app log, order record).
2. **Unproven inferences**, explicitly labelled as such.
3. **Open questions**, each with the method that would close it.
4. **Competing hypotheses**, each with the *discriminating prediction* that separates it from the others.
5. **Closure criteria**: every open question ends with an explicit benign/not-benign verdict. **"Assumed benign" is not a verdict.**
6. **Out-of-scope**, stated, so deferrals are decisions rather than omissions.

## Related

- `order-execution.md` -- placing orders, brackets, fills, paper-gateway probing
- `venue-boundary-failure-modes.md` -- async rejection ingress, rejection-code sets, sizing guards
- `event-driven-data.md` -- listener contracts, logger routing, decoder-drop channel
- `reconnection-resilience.md` -- verdicts and state after reconnects
