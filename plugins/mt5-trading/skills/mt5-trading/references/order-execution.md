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
- **Hedging-mode close requires `position` field with the ticket.** Forgetting it does NOT close -- it opens a new opposite position. Check `account_info().margin_mode`: 0=netting, 2=exchange, 3=hedging. Most retail forex brokers run hedging.
- **`magic=0` is the convention for manual trades.** Always assign a non-zero magic to bot orders so you can filter `[p for p in positions if p.magic == MY_MAGIC]`. Multi-strategy: unique magic per strategy+symbol.
- **`deviation` is in points, not pips.** Only effective with **Instant Execution** -- with Market Execution (most ECN/STP brokers) it's silently ignored. Recommended values: 10-20 normally, 50+ during news.
- **Always `order_check()` before `order_send()`.** Validates fields, margin, fill mode, volume **without sending to the server.** Costs you nothing and catches most issues.
- **Broker-specific values change between brokers AND between symbols.** Always query at runtime: `trade_exemode`, `trade_stops_level`, `trade_freeze_level`, `filling_mode`, `volume_min/max/step`. Hardcoding is the second most common production bug.
- **Retcode 10027 (`CLIENT_DISABLES_AT`)** = autotrading disabled in terminal. Either Ctrl+E in MT5 or "Disable automatic trading via external Python API" was toggled. Check this first when a previously-working bot suddenly stops.
- **Retcode 10024 (`TOO_MANY_REQUESTS`)** -- exponential backoff, min 100-200ms.
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
- **FOK** (Fill or Kill) -- full volume or nothing. Standard for Instant Execution.
- **IOC** (Immediate or Cancel) -- fill what's available, cancel rest. Can return retcode 10010 (partial fill).
- **Return** -- partial fills leave residual as active order. **Prohibited in Market Execution** (most ECN/STP brokers).
- **BOC** (Book or Cancel) -- passive only, cancelled if would execute immediately. Maker-only strategies.

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
| 10004 | REQUOTE | Price moved -- re-fetch and retry |
| 10009 | DONE | Success |
| 10010 | DONE_PARTIAL | Partial fill (IOC) |
| 10013 | INVALID | Malformed request -- check fields |
| 10016 | INVALID_STOPS | SL/TP inside `stops_level` |
| 10019 | NO_MONEY | Insufficient margin |
| 10024 | TOO_MANY_REQUESTS | Backoff (100-200ms) |
| 10027 | CLIENT_DISABLES_AT | Autotrading disabled in terminal |
| 10029 | FROZEN | In freeze zone, can't modify |
| 10030 | INVALID_FILL | Wrong fill mode -- use dynamic detection |

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

- `api-architecture.md` -- why errors are silent and you must check every return
- `event-system-polling.md` -- monitoring positions and trade transitions via polling
- `production-resilience.md` -- weekend gate, watchdog, /portable flag
