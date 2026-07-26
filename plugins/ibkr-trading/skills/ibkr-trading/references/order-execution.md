# Order Execution and Management

Placing orders, brackets, monitoring fills, reconciling positions. The principle is "anything you can do in TWS you can do via API"; the gotchas around state, races, and message rates are what make production hard.

## When to use

Submitting, modifying, cancelling, or reconciling orders. For market data subscriptions (which use the same event pattern), see `event-driven-data.md`.

## Order shapes (just the most useful ones)

| Type | Code | Use |
|------|------|-----|
| Market | `MKT` | Immediate, accepts slippage |
| Limit | `LMT` | Price control, may not fill |
| Stop | `STP` | Trigger on breach |
| Stop-Limit | `STP LMT` | Stop + price protection |
| Trailing Stop | `TRAIL` | Dynamic |
| MOC / LOC | `MOC` / `LOC` | Market / Limit on close |
| Pegged-to-NBBO | `REL` | Relative to top of book |
| Midprice | `MIDPRICE` | Pegged to midpoint |

IB algos available too: Adaptive (Urgent/Normal/Patient), TWAP, VWAP, ArrivalPx, DarkIce, Accumulate/Distribute, PctVol.

## Gotchas

- **`orderStatus` is NOT guaranteed for every state change.** Market orders that fill instantly may never callback. **Always monitor `execDetails` as the authoritative fill source** -- not `orderStatus`. `orderStatus` messages are also sometimes duplicated (echoed from TWS, server, exchange) -- de-dupe in code.
- **Bracket order transmit pattern is positional.** Set `transmit=False` on parent and on every child *except the last*; only the last child has `transmit=True`. Submitting parent with `transmit=True` before the children = unprotected position. This is the #1 bracket-order bug.
- **Order ID management**: `nextValidId` arrives on connect; IDs must be unique positive ints, always greater than the last used. In multi-client setups, your IDs must exceed all open order IDs across clients. Error **103 (Duplicate order ID)** is one of the most common production errors. `ib.client.getReqId()` auto-increments safely.
- **Cancel-fill race.** Between `cancelOrder()` and confirmation, a fill can happen. Sequence may be: cancel sent → execDetails (fill) → orderStatus(Cancelled for the residual). Never assume cancel succeeded until you've seen `Cancelled` or `Filled` in `orderStatus`.
- **Order Efficiency Ratio: <= 20:1** (submissions+modifications+cancellations vs executions). Exceeding generates warnings, then restrictions. Avoid rapid-fire modifications.
- **Message rate: 50 msg/sec to IB.** Exceeding causes disconnect (error 100). **Enable `+PACEAPI`** so TWS throttles instead of disconnecting:
  ```python
  ib.client.setConnectOptions('+PACEAPI')
  ```
- **`placeOrder()` with the same orderId = modify** -- not a new order. Cannot modify already-filled portions; cancellation may fail mid-fill.
- **Error 201 ("Order rejected") -- never auto-retry.** Always investigate. Common causes: price check failure, margin, exchange-specific rules, and (on retail EU entities) FX currency-leverage on a leveraged spot cross. Blind retry generates more 201s and burns through OER budget. The FX currency-leverage case is fixable by routing through CFDs: see `venue-boundary-failure-modes.md`.
- **Compliance 201s are NOT order precautions -- no override exists.** Precautions are the 10xxx series; account/compliance rejections like FX currency-leverage are hard rejections. Neither "Bypass Order Precautions for API Orders" in the Gateway config nor `Order.advancedErrorOverride` will let them through. Do not burn time on override paths: fix the contract type (spot -> CFD) or the account, treat the code as permanently non-retryable.
- **Bracket children (SL/TP) must be `tif='GTC'`; only the parent entry is `DAY`.** Two symmetric failure modes otherwise: DAY children expire at session end and leave an open position **naked overnight**; and children that survive the position (closed by an opposing fill or manually) rest as live orders on a flat contract, ready to open an unintended position. The invariant is *protections live exactly as long as the position*: GTC children for the position's lifetime, plus a **residual-child reaper** -- on a position-closed event for a contract now flat, cancel any bracket children still open on that contract.
- **Phantom `Cancelled` during staged bracket transmit.** With the `transmit=False` staging pattern, children can report a *transient* `Cancelled` status before flipping to `PreSubmitted` once the last child transmits. Do not emit a real cancellation event (or notify anyone) on that transient -- confirm against `reqOpenOrders()`/broker state before treating a staged child's `Cancelled` as real.
- **`whatIf=True` orders are free empirical probes.** A whatIf submission returns margin impact and commission **without placing**, and surfaces hard rejections (like a compliance 201) with zero market risk. Use whatIf against the paper gateway to *prove* an account capability or a contract-type migration before writing code around an assumption; pair with read-only `reqContractDetailsAsync` to prove a contract form resolves at all.
- **A successful `placeOrder` is "submitted", not "accepted".** IBKR accepts or rejects asynchronously via `errorEvent`. If you do not subscribe `errorEvent` and route rejection codes into your order lifecycle, a rejected order silently dies while your system thinks it is live. De-duplicate the rejection against `orderStatusEvent`. See `venue-boundary-failure-modes.md`.
- **Error 110 ("price does not conform to minimum price variation") -> 135 on bracket children.** Snap every price to the contract `minTick` (read from `ContractDetails`, not the `Contract`) before placing, and round bracket SL/TP *away* from entry. Covered in `venue-boundary-failure-modes.md`.
- **Partial fills** populate `trade.fills` (each individual execution) and increment cumulative quantity -- adjust bracket child quantities if a parent partially fills before children become live.

## Bracket order skeleton (the pattern)

```python
def create_bracket(ib, contract, action, qty, entry, tp, sl):
    parent = LimitOrder(action, qty, entry)
    parent.orderId = ib.client.getReqId()
    parent.tif = 'DAY'          # entry may expire with the session
    parent.transmit = False

    opp = 'SELL' if action == 'BUY' else 'BUY'
    take_profit = LimitOrder(opp, qty, tp)
    take_profit.orderId = ib.client.getReqId()
    take_profit.parentId = parent.orderId
    take_profit.tif = 'GTC'     # protections must survive the session
    take_profit.transmit = False

    stop_loss = StopOrder(opp, qty, sl)
    stop_loss.orderId = ib.client.getReqId()
    stop_loss.parentId = parent.orderId
    stop_loss.tif = 'GTC'       # protections must survive the session
    stop_loss.transmit = True   # only the last child triggers transmission

    for o in (parent, take_profit, stop_loss):
        ib.placeOrder(contract, o)
    return parent.orderId
```

## Cancel-with-fill-race-awareness (composite local pattern)

```python
async def safe_cancel(ib, trade):
    ib.cancelOrder(trade.order)
    while trade.orderStatus.status not in ('Cancelled', 'Filled'):
        await asyncio.sleep(0.1)
    if trade.orderStatus.status == 'Filled':
        log.warning(f"Order {trade.order.orderId} filled during cancel attempt")
    return trade.orderStatus.status
```

## Position reconciliation (run on startup + periodically)

Positions are **account-level**; open-order visibility is **per-clientId**. With several clients on one account, differing order counts across clients are visibility, not divergence -- and never let multiple clients publish full account snapshots with replace semantics (see "Multi-Client State Hygiene" in `reconnection-resilience.md`). Real-time position deltas arrive via `positionEvent` -- whose handler signature must be contract-tested or it can silently never fire (see "Event Listener Contracts" in `event-driven-data.md`).

```python
async def reconcile_positions(ib, expected_positions):
    actual = await ib.reqPositionsAsync()
    for pos in actual:
        key = (pos.contract.symbol, pos.contract.secType)
        expected = expected_positions.get(key, 0)
        if pos.position != expected:
            log.error(f"POSITION MISMATCH: {key} expected={expected} actual={pos.position}")
    fills = await ib.reqExecutionsAsync()  # also catches fills during disconnect
    for fill in fills:
        log.info(f"Reconciled fill: {fill.execution.orderId} {fill.execution.shares}@{fill.execution.avgPrice}")
```

## Authoritative fill listener

```python
def on_exec_details(trade, fill):
    log.info(f"FILL: {fill.contract.symbol} {fill.execution.side} "
             f"qty={fill.execution.shares} price={fill.execution.avgPrice} "
             f"orderId={fill.execution.orderId}")

ib.execDetailsEvent += on_exec_details
```

## Official docs

- Order types reference: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-ref/#order-types
- Bracket orders: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#bracket-orders
- Order status flow: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#order-status
- Error codes: https://www.interactivebrokers.com/campus/ibkr-api-page/tws-api-error-codes/
- Order Efficiency Ratio: https://www.interactivebrokers.com/en/general/education/order-efficiency-ratio.php

## Related

- `venue-boundary-failure-modes.md` -- async rejection ingress, tick conformance, FX-as-CFD routing, NaN-safe sizing
- `event-driven-data.md` -- the same event pattern for market data
- `reconnection-resilience.md` -- handling disconnect during open orders
- `tws-api-architecture.md` -- clientId strategy and PACEAPI option
