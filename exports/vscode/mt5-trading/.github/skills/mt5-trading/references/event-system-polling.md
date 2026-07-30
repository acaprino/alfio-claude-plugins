# Event System: Building Events on a Polling API

## The Core Problem

The MT5 Python API **supports no form of callback, subscription, or streaming**. Even `market_book_add()` requires polling with `market_book_get()`. The only native approach is a `while True` loop with `time.sleep()`.

## Polling Patterns

### New Candle Detection

Compare the `time` field of the last bar from `copy_rates_from_pos(symbol, tf, 0, 1)` with the cached value. If different, new candle.

```python
import MetaTrader5 as mt5
import time

last_candle_time = {}

def check_new_candle(symbol, timeframe):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    if rates is None:
        return False
    current_time = rates[0]['time']
    if symbol not in last_candle_time:
        last_candle_time[symbol] = current_time
        return False
    if current_time != last_candle_time[symbol]:
        last_candle_time[symbol] = current_time
        return True
    return False
```

**Poll intervals by timeframe**: M1 -- poll every 1s; M5 -- every 3-5s; H1 -- every 10-30s.

**Optimization**: calculate seconds remaining until next candle close and sleep until that moment + buffer, instead of constant polling.

### Tick Detection

Compare `tick.time_msc` from `symbol_info_tick()` with the previous value:

```python
last_tick_msc = {}

def check_new_tick(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    if symbol not in last_tick_msc or tick.time_msc != last_tick_msc[symbol]:
        last_tick_msc[symbol] = tick.time_msc
        return tick
    return None
```

### Position Change Detection

Snapshot `positions_get()` and compare ticket sets between iterations:

```python
known_positions = set()

def check_position_changes():
    positions = mt5.positions_get()
    if positions is None:
        positions = ()
    current_tickets = {p.ticket for p in positions}

    opened = current_tickets - known_positions
    closed = known_positions - current_tickets

    known_positions.clear()
    known_positions.update(current_tickets)
    return opened, closed
```

For historical fills, use `history_deals_get(from_time, to_time)` with a sliding window.

## Complete Event Loop

```python
class MT5EventLoop:
    def __init__(self, symbols, timeframe, poll_interval=1.0):
        self.symbols = symbols
        self.timeframe = timeframe
        self.poll_interval = poll_interval
        self.last_candle_times = {}
        self.known_positions = set()
        self.callbacks = {
            'on_tick': [], 'on_new_candle': [],
            'on_position_opened': [], 'on_position_closed': []
        }

    def on(self, event, callback):
        self.callbacks[event].append(callback)

    def _emit(self, event, *args):
        for cb in self.callbacks.get(event, []):
            cb(*args)

    def _init_state(self):
        for s in self.symbols:
            rates = mt5.copy_rates_from_pos(s, self.timeframe, 0, 1)
            if rates is not None:
                self.last_candle_times[s] = rates[0]['time']
        positions = mt5.positions_get() or ()
        self.known_positions = {p.ticket for p in positions}

    def run(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
        for s in self.symbols:
            mt5.symbol_select(s, True)
        self._init_state()

        while True:
            for symbol in self.symbols:
                # Check ticks
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    self._emit('on_tick', symbol, tick)

                # Check candles
                rates = mt5.copy_rates_from_pos(symbol, self.timeframe, 0, 1)
                if rates is not None:
                    t = rates[0]['time']
                    if t != self.last_candle_times.get(symbol):
                        self.last_candle_times[symbol] = t
                        self._emit('on_new_candle', symbol, rates[0])

            # Check positions
            positions = mt5.positions_get() or ()
            current = {p.ticket for p in positions}
            for ticket in current - self.known_positions:
                pos = next((p for p in positions if p.ticket == ticket), None)
                if pos:
                    self._emit('on_position_opened', pos)
            for ticket in self.known_positions - current:
                self._emit('on_position_closed', ticket)
            self.known_positions = current

            time.sleep(self.poll_interval)
```

## Latency and Rate Limits

A single IPC call costs **~15-60 microseconds**. No documented rate limits on the local API -- communication is via shared memory, not network. However, excessive polling wastes CPU and can degrade terminal performance.

**Practical recommendations**:
- Strategies on M1+ bars: poll every 1-5s
- Tick-sensitive strategies: poll every 100-250ms
- Multi-symbol: round-robin across symbols
- Cache static metadata (symbol properties, account info) and refresh hourly

## Concurrency Rules

**The MT5 API is NOT thread-safe.** The IPC pipe is single -- concurrent access causes race conditions, crashes, or corrupted data.

**Golden rule: one process -> one terminal, one thread for all MT5 calls.**

If concurrency is needed:
- Use `asyncio` (not threading) -- `asyncio.to_thread()` serialized by the GIL
- Protect every call with `threading.Lock()` if threading is unavoidable
- For multi-account/multi-broker: separate processes (`multiprocessing`), each with its own terminal instance
- `aiomql` handles this internally with serialized `asyncio.to_thread()`

### asyncio Pattern

```python
import asyncio

class AsyncMT5:
    async def get_rates(self, symbol, timeframe, count):
        return await asyncio.to_thread(
            mt5.copy_rates_from_pos, symbol, timeframe, 0, count
        )

    async def send_order(self, request):
        result = await asyncio.to_thread(mt5.order_check, request)
        if result and result.retcode == 0:
            return await asyncio.to_thread(mt5.order_send, request)
        return result
```

## Async Event Loop with aiomql

aiomql provides a cleaner async pattern out of the box:

```python
from aiomql import MetaTrader, Bot, Strategy

class MyStrategy(Strategy):
    async def trade(self):
        # Called on each polling cycle
        candles = await self.mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 100)
        # Strategy logic here
```

The Bot class orchestrates multiple strategies, manages sessions, and handles reconnection automatically.
