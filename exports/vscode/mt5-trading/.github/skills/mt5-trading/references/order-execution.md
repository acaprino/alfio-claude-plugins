# Order Execution and Management

`order_send()` takes a `MqlTradeRequest`-shaped dict and returns a result with a retcode. The hard parts: **fill mode is broker- and symbol-specific** (retcode 10030 is the most common production error), hedging-mode close requires the position ticket, and broker-specific values must be queried at runtime.

## When to use

Submitting market/pending orders, modifying SL/TP, closing positions, or pre-checking with `order_check()`. For position monitoring (which is also polling), see `event-system-polling.md`.

## Action shape

| Action | Constant | Use |
|--------|----------|-----|
| Market order | `TRADE_ACTION_DEAL` | Immediate execution |
| Pending order | `TRADE_ACTION_PENDING` | Place limit/stop |
| Modify SL/TP | `TRADE_ACTION_SLTP` | Change stops on existing position |
| Modify pending | `TRADE_ACTION_MODIFY` | Change pending order params |
| Remove pending | `TRADE_ACTION_REMOVE` | Cancel pending |
| Close-by | `TRADE_ACTION_CLOSE_BY` | Close against opposite position (hedging only) |

Order types: BUY, SELL, BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP, BUY_STOP_LIMIT, SELL_STOP_LIMIT, CLOSE_BY.

## Gotchas

- **Retcode 10030 (`TRADE_RETCODE_INVALID_FILL`) is the #1 production error.** Each symbol supports specific fill modes; **never hardcode** them. Detect at runtime via `symbol_info().filling_mode` (bit flag). Snippet below.
- **Hedging-mode close requires `position` field with the ticket.** Forgetting it does NOT close - it opens a new opposite position. Check `account_info().margin_mode`: 0=netting, 2=exchange, 3=hedging. Most retail forex brokers run hedging.
- **`magic=0` is the convention for manual trades.** Always assign a non-zero magic to bot orders so you can filter `[p for p in positions if p.magic == MY_MAGIC]`. Multi-strategy: unique magic per strategy+symbol.
- **`deviation` is in points, not pips.** Only effective with **Instant Execution** - with Market Execution (most ECN/STP brokers) it's silently ignored. Recommended values: 10-20 normally, 50+ during news.
- **Always `order_check()` before `order_send()`.** Validates fields, margin, fill mode, volume **without sending to the server.** Costs you nothing and catches most issues.
- **Broker-specific values change between brokers AND between symbols.** Always query at runtime: `trade_exemode`, `trade_stops_level`, `trade_freeze_level`, `filling_mode`, `volume_min/max/step`. Hardcoding is the second most common production bug.
- **Retcode 10027 (`CLIENT_DISABLES_AT`)** = autotrading disabled in terminal. Either Ctrl+E in MT5 or "Disable automatic trading via external Python API" was toggled. Check this first when a previously-working bot suddenly stops.
- **Retcode 10024 (`TOO_MANY_REQUESTS`)** - exponential backoff, min 100-200ms.
- **Retcode 10016 (`INVALID_STOPS`)** = SL/TP too close to price. Check `symbol_info().trade_stops_level` and respect it.
- **Server-side SL/TP on every position is non-negotiable.** Local-only stops disappear if the bot dies.

## Dynamic fill mode detection

```python
import MetaTrader5 as mt5

def get_filling_type(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    fm = info.filling_mode
    if fm & 1:
        return mt5.ORDER_FILLING_FOK
    if fm & 2:
        return mt5.ORDER_FILLING_IOC
    return mt5.ORDER_FILLING_RETURN
```

Fill mode reference:
- **FOK** (Fill or Kill) - full volume or nothing. Standard for Instant Execution.
- **IOC** (Immediate or Cancel) - fill what's available, cancel rest. Can return retcode 10010 (partial fill).
- **Return** - partial fills leave residual as active order. **Prohibited in Market Execution** (most ECN/STP brokers).
- **BOC** (Book or Cancel) - passive only, cancelled if would execute immediately. Maker-only strategies.

## Hedging-mode close (the ticket gotcha)

```python
def close_position(position):
    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       position.symbol,
        "volume":       position.volume,
        "type":         mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
        "position":     position.ticket,            # CRITICAL in hedging mode
        "type_filling": get_filling_type(position.symbol),
        "magic":        position.magic,
        "comment":      "close",
    }
    return mt5.order_send(request)
```

## Complete market order (the canonical recipe)

```python
def market_buy(symbol, volume, sl_points=None, tp_points=None, magic=12345):
    mt5.symbol_select(symbol, True)         # Symbol must be in Market Watch
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    if tick is None or info is None:
        return None

    price = tick.ask
    point = info.point

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       volume,
        "type":         mt5.ORDER_TYPE_BUY,
        "price":        price,
        "sl":           round(price - sl_points * point, info.digits) if sl_points else 0.0,
        "tp":           round(price + tp_points * point, info.digits) if tp_points else 0.0,
        "deviation":    20,
        "magic":        magic,
        "comment":      "python_bot",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": get_filling_type(symbol),
    }

    check = mt5.order_check(request)
    if check is None or check.retcode != 0:
        print(f"Order check failed: {check}")
        return None

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:        # 10009
        print(f"Order failed: retcode={result.retcode} comment={result.comment}")
    return result
```

## Retcode quick reference (the ones you'll see)

| Code | Constant | Meaning |
|------|----------|---------|
| 10004 | REQUOTE | Price moved - re-fetch and retry |
| 10009 | DONE | Success |
| 10010 | DONE_PARTIAL | Partial fill (IOC) |
| 10013 | INVALID | Malformed request - check fields |
| 10016 | INVALID_STOPS | SL/TP inside `stops_level` |
| 10019 | NO_MONEY | Insufficient margin |
| 10024 | TOO_MANY_REQUESTS | Backoff (100-200ms) |
| 10027 | CLIENT_DISABLES_AT | Autotrading disabled in terminal |
| 10029 | FROZEN | In freeze zone, can't modify |
| 10030 | INVALID_FILL | Wrong fill mode - use dynamic detection |

## Mapping onto the reference order-lifecycle model

MetaTrader's own vocabulary for this table comes from two places: the retcode quick reference above,
already this plugin's text, and MetaTrader's `ENUM_ORDER_STATE` and `TRADE_RETCODE_*` documentation for
the handful of values that table does not list (the order `state` field, and retcodes 10006 `REJECT`,
10007 `CANCEL` and 10008 `PLACED`), each cited by name so a reader can tell which source backs which
row. This table adds no new evidence about MetaTrader, only a correspondence. `trading-broker-connectivity`'s
order-lifecycle reference model gives the same acknowledgement levels in vendor-neutral terms, so a
reader who knows one system can cross into the other. That correspondence between a MetaTrader value and
a model state is this plugin's own reading, not something MetaQuotes documents: MetaQuotes has never
heard of that vocabulary, so every row below is a conclusion this plugin draws, never a fact MetaTrader
states. The table covers every order value this file uses, plus the reverse direction: where the model
has a state MetaTrader never surfaces a value for.

A row's correspondence rests on one of four kinds of argument, and every row below names or shows which.
**Lexical self-evidence**: the MetaTrader token is an ordinary word (`REJECT`, `CANCELED`) whose meaning
is not in dispute, so reading the quote already answers the row. **Cross-reference**: the correspondence
follows from a rule stated elsewhere, in this plugin's own text or in the reference model's own FIX
bridge. **Analogy**: a value's documented meaning sits at the same acknowledgement level as an
already-placed row, without a quote of its own to read. **Inference from absence**: MetaTrader documents
no value at all for a concept the model names, and the row states that absence as the finding. A row
marked **Assumed mapping** rests on one of the last three; an unmarked row rests on lexical
self-evidence, a quote that already says what the row claims.

| This model | MetaTrader value | Note |
|---|---|---|
| `CREATED` | none | **Assumed mapping.** Inference from absence: no order object exists anywhere in MT5 until `order_send()` is called, so there is nothing for a state or a retcode to describe. The reference model's own FIX bridge gives the identical reason for its identical `CREATED` gap |
| `SENT` | `ORDER_STATE_STARTED`, `ORDER_STATE_REQUEST_ADD` | **Assumed mapping.** "Order checked, but not yet accepted by broker" and "Order is being registered (placing to the trading system)" both describe the pre-acceptance window, and MetaTrader's own documentation draws no line between them, so this plugin folds both here rather than inventing a distinction neither description supports |
| `VALIDATED` | none | **Assumed mapping.** Inference from absence: MetaTrader documents no value between "not yet accepted" and "accepted." `order_check()` reads like a candidate by name, but the model maps to the acknowledgement, not the name, and this file already says `order_check()` validates "without sending to the server": nobody outside the local terminal has looked at the order yet, so it sits before `SENT`, not at `VALIDATED`. For most MT5 accounts the broker that accepts the order also is the venue, so the reference model's own broker-versus-venue split rarely surfaces here as two separate steps at all |
| `WORKING` | `ORDER_STATE_PLACED`, retcode 10008 `PLACED` | **Assumed mapping.** "Order accepted" is the state that follows `STARTED`; for a pending order that is the same order now resting and eligible to trade. `order.state` and `result.retcode` are two different fields that happen to share the English word "placed": read them as the same acknowledgement level, not as confirming each other |
| `PARTIALLY_FILLED` | `ORDER_STATE_PARTIAL` | "Order partially executed" states the row directly |
| `PARTIALLY_FILLED` | retcode 10010 `DONE_PARTIAL` | **Assumed mapping.** Cross-reference: this file's IOC entry above says IOC "fill[s] what's available, cancel[s] rest," so by the time this retcode arrives the order has already taken the path the reference model itself names "A cancel is not a rollback": `PARTIALLY_FILLED` to `CANCELLED` "leaves the executions that already happened," compressed here into one synchronous answer instead of two separate events. The model's own definition of `PARTIALLY_FILLED` is "quantity remains," meaning still resting and workable; that reading would be wrong for the IOC case this plugin documents, where the remainder is already dead on arrival |
| `FILLED` | `ORDER_STATE_FILLED` | "Order fully executed" states the row directly |
| `FILLED` | retcode 10009 `DONE` | **Assumed mapping.** Cross-reference: MetaTrader's own definition of `DONE` is generic, "Request completed," true of any successful action, not fill-specific. This plugin's canonical market-order recipe above checks it as the fill outcome of `TRADE_ACTION_DEAL` specifically, and that is the only use this file makes of the code, so the row is scoped to that action. What `DONE` means after `TRADE_ACTION_REMOVE` or `TRADE_ACTION_PENDING` is not resolved here: this file's text never exercises those combinations, and guessing would present a mapping as a fact it is not |
| `CANCEL_REQUESTED` | `ORDER_STATE_REQUEST_CANCEL` | Lexical self-evidence. "Order is being deleted (deleting from the trading system)" is the ordinary meaning of a cancel in flight, not yet confirmed |
| `CANCEL_REQUESTED` | `ORDER_STATE_REQUEST_MODIFY` | **Assumed mapping.** Cross-reference to the reference model's own FIX bridge, which places a modify in flight on the same row as `CANCEL_REQUESTED` ("`Pending Replace` (E) is the same shape for a modify in flight"). MetaTrader's "Order is being modified" is that same shape: sent, not yet confirmed |
| `CANCELLED` | `ORDER_STATE_CANCELED`, retcode 10007 `CANCEL` | Lexical self-evidence. "Order canceled by client" and "Request canceled by trader" both state the row directly |
| `CANCELLED` | `ORDER_STATE_EXPIRED` | **Assumed mapping.** Cross-reference to the reference model's own FIX bridge, which folds FIX's `Expired` into `CANCELLED` and says to keep the vendor's own term alongside where the difference matters. This plugin keeps MetaTrader's own `EXPIRED` for exactly that reason: a GTD pending order that timed out and an order a client explicitly cancelled are both dead with no quantity left to trade, but they are not the same event for reporting or diagnosis |
| `REJECTED` | `ORDER_STATE_REJECTED`, retcode 10006 `REJECT` | Lexical self-evidence. "Order rejected" and "Request rejected" both state the row directly |
| `REJECTED` | retcodes 10013 `INVALID`, 10016 `INVALID_STOPS`, 10019 `NO_MONEY`, 10024 `TOO_MANY_REQUESTS`, 10027 `CLIENT_DISABLES_AT`, 10029 `FROZEN`, 10030 `INVALID_FILL` | **Assumed mapping.** Analogy to the row above: each names a specific reason the request never got past validation, the same acknowledgement level as the direct `REJECT` code. Individual meanings are already in the retcode quick reference above; this row states only the shared correspondence |
| `REJECTED` | retcode 10004 `REQUOTE` | **Assumed mapping.** Analogy, with a caveat the model's own definition of `REJECTED` raises on its own: "a rejection means the order as shaped will never work and something must change." A requote is the one code here where that is not quite true. The shape was fine, only the price moved, and this file's own entry above says to re-fetch and retry the same request rather than reshape it |
| `UNKNOWN` | none | **Assumed mapping.** Inference from absence: no MetaTrader value means "I do not know." This plugin's own name for the gap after a disconnect, before `production-resilience.md`'s reconnection pattern has re-polled and confirmed what actually happened while the pipe was down |

Deals get no row above. A deal in MetaTrader's own deal-properties documentation is a historical record
of a completed execution with no status or state field of its own: `DEAL_ENTRY_IN`, `DEAL_ENTRY_OUT`,
`DEAL_ENTRY_INOUT` and `DEAL_ENTRY_OUT_BY` classify what the execution did to a position, not what state
it is in. `FILLED` and `PARTIALLY_FILLED` above already cover what a deal's existence means for the
order; the deal record itself has nothing left to transition through.

## Broker mode differences

| Aspect | ECN / STP (Market Execution) | Market Maker (Instant Execution) |
|--------|------------------------------|----------------------------------|
| Requotes | None | Possible (10004) |
| `deviation` | Ignored | Respected |
| Slippage direction | Bidirectional | Typically negative only |
| `stops_level` | Often 0 (good for scalping) | Usually > 0 |

## Official docs

- `order_send` reference: https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py
- `order_check` reference: https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py
- `MqlTradeRequest` structure: https://www.mql5.com/en/docs/constants/structures/mqltraderequest
- Trading constants (actions, types, fill modes, retcodes): https://www.mql5.com/en/docs/constants/tradingconstants
- `symbol_info` (filling_mode, stops_level, trade_exemode): https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfo_py

## Related

- `api-architecture.md` - why errors are silent and you must check every return
- `event-system-polling.md` - monitoring positions and trade transitions via polling
- `production-resilience.md` - weekend gate, watchdog, /portable flag
