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
- **Error 201 ("Order rejected") -- never auto-retry.** Always investigate. Common causes: price check failure, margin, exchange-specific rules. Blind retry generates more 201s and burns through OER budget.
- **Partial fills** populate `trade.fills` (each individual execution) and increment cumulative quantity -- adjust bracket child quantities if a parent partially fills before children become live.

## Bracket order skeleton (the pattern)

```python
def create_bracket(ib, contract, action, qty, entry, tp, sl):
    parent = LimitOrder(action, qty, entry)
    parent.orderId = ib.client.getReqId()
    parent.transmit = False

    opp = 'SELL' if action == 'BUY' else 'BUY'
    take_profit = LimitOrder(opp, qty, tp)
    take_profit.orderId = ib.client.getReqId()
    take_profit.parentId = parent.orderId
    take_profit.transmit = False

    stop_loss = StopOrder(opp, qty, sl)
    stop_loss.orderId = ib.client.getReqId()
    stop_loss.parentId = parent.orderId
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

- `event-driven-data.md` -- the same event pattern for market data
- `reconnection-resilience.md` -- handling disconnect during open orders
- `tws-api-architecture.md` -- clientId strategy and PACEAPI option
