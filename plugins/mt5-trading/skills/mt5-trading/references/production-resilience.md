# Production Resilience and Windows Deployment

## The API Does Not Handle Disconnections

No automatic reconnection mechanism exists. If the IPC pipe breaks, API calls return `None`. The developer must implement all recovery logic.

**Positions persist server-side** even when the terminal disconnects -- server-side SL/TP continue to function. But any Python logic (trailing stops, dynamic risk management) **ceases to function** until reconnection.

## Disconnection Detection

### Primary Signals

- `terminal_info().connected`: boolean, primary signal
- `account_info()` returns `None` if not connected
- `last_error()` for specific IPC errors:

| Code | Meaning |
|------|---------|
| -10001 | IPC send failed |
| -10002 | IPC recv failed |
| -10003 | Pipe server not responding |
| -10005 | Internal timeout |

## Reconnection Pattern

```python
import MetaTrader5 as mt5
import time
import logging

log = logging.getLogger(__name__)

MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
LOGIN = 12345678
SERVER = "BrokerServer-Live"
PASSWORD = "***"

def connect_mt5(retries=5):
    for attempt in range(retries):
        ensure_mt5_process_running()
        if mt5.initialize(
            path=MT5_PATH, login=LOGIN,
            server=SERVER, password=PASSWORD, timeout=30000
        ):
            info = mt5.terminal_info()
            if info and info.connected:
                log.info("MT5 connected successfully")
                return True
        mt5.shutdown()
        delay = min(10 * (2 ** attempt), 120)
        log.warning(f"Attempt {attempt+1} failed. Retry in {delay}s")
        time.sleep(delay)

    # Nuclear option: kill and restart
    log.error("All attempts failed. Killing MT5 process...")
    kill_mt5_process()
    time.sleep(10)
    return connect_mt5(retries=2)
```

### Process Monitoring with psutil

```python
import psutil
import subprocess

def ensure_mt5_process_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'terminal64.exe':
            return True
    log.warning("MT5 not running. Starting...")
    subprocess.Popen([MT5_PATH, "/portable"])
    time.sleep(15)  # Wait for terminal to initialize
    return True

def kill_mt5_process():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'terminal64.exe':
            proc.kill()
            log.info("MT5 process killed")
```

The `/portable` flag avoids permission issues with `C:\Program Files`. **Disable MT5 auto-updates** during trading hours -- an update can restart the terminal without warning.

## Health Check Loop

```python
def health_check(interval=30):
    """Run in main loop every 30-60 seconds."""
    info = mt5.terminal_info()
    if info is None or not info.connected:
        log.error("MT5 disconnected! Reconnecting...")
        mt5.shutdown()
        return connect_mt5()

    # Check for stale data during market hours
    tick = mt5.symbol_info_tick("EURUSD")
    if tick:
        age_seconds = time.time() - tick.time
        if age_seconds > 60:
            log.warning(f"Tick data stale by {age_seconds:.0f}s")
    return True
```

## Weekend Handling

Friday after ~22:00 UTC the forex market closes. The terminal stays connected but no quotes arrive -- `symbol_info_tick()` returns stale data. The `connected` field in `terminal_info()` may remain `True`.

```python
from datetime import datetime, timezone

def is_market_open():
    now = datetime.now(timezone.utc)
    # Forex: Sunday 22:00 UTC to Friday 22:00 UTC
    if now.weekday() == 5:  # Saturday
        return False
    if now.weekday() == 6 and now.hour < 22:  # Sunday before open
        return False
    if now.weekday() == 4 and now.hour >= 22:  # Friday after close
        return False
    return True
```

Implement datetime-based sleep mode during weekends and validate connection state before trading on Monday.

## initialize() and shutdown() Details

`initialize()` accepts: `path` (exe path), `login`, `password`, `server`, `timeout` (default 60000ms), `portable` (boolean). If the terminal is not running, it attempts to start it. Returns `True`/`False`.

**Do not call `initialize()` multiple times without `shutdown()`** -- causes known issues. One Python process can connect to **one terminal only**. For multi-terminal: separate processes, each with an MT5 installation in a different directory in `/portable` mode.

## The 10 Critical Production Caveats

1. **Server-side SL/TP always**: never rely solely on Python for risk management. If Python crashes, positions remain open without protection.
2. **`initialize()`/`shutdown()` not in loops**: calling repeatedly degrades performance drastically. Initialize once at startup, shut down once at end.
3. **Thread safety**: all MT5 calls on a single thread. Use `asyncio` for concurrency, not multiple threads.
4. **Dynamic fill mode**: query `symbol_info().filling_mode` before every order. Supported fill modes can change.
5. **UTC everywhere**: never use naive datetime. All MT5 times are UTC.
6. **Silent errors**: every function can return `None` without exception. Always check return values and `last_error()`.
7. **Demo is not live**: demo has instant fills, tight spreads, no requotes. Live: frequent requotes (10004), variable spreads, real slippage.
8. **`symbol_select()` required**: the symbol must be in Market Watch before any trading or data request.
9. **One process per terminal**: multiple Python processes on the same MT5 instance cause errors and degradation.
10. **Terminal auto-update**: can restart MT5 during trading. Disable in Tools -> Options -> General.

## Recommended Production Architecture

```
[Python Process - Single Thread]
    |-- Health Check (every 30-60s) -> reconnect if needed
    |-- Per symbol (round-robin):
    |   |-- Fetch data (copy_rates, symbol_info_tick)
    |   |-- Signal calculation
    |   |-- order_check() -> order_send()
    |   |-- Position reconciliation
    |-- State reconciliation on restart
    |-- Circuit breaker (stop after N consecutive errors)
    |-- Kill switch (flatten and halt)
    |-- Structured logging + alerting

[MT5 Terminal] <-> [Broker Server]
    |-- Named pipe IPC
```

## Comparison: MT5 vs IBKR Resilience

| Aspect | MT5 | IBKR |
|--------|-----|------|
| Auto-reconnect (terminal) | Terminal reconnects to broker automatically | Gateway auto-restarts weekly |
| API reconnect | None, must implement fully | None (ib_async), must implement |
| Daily reset | None (but weekend closure) | Mandatory ~23:45-00:45 ET daily |
| Positions during disconnect | Persist server-side, SL/TP active | Native exchange orders continue |
| Resource usage | ~200-400MB (terminal) | Gateway ~300-500MB, TWS ~1-2GB |
| Process monitoring | psutil + subprocess | IBC + Task Scheduler |

## Community Resources

### GitHub Repositories

- **aiomql** (https://github.com/Ichinga-Samuel/aiomql, ~109 stars) -- best architectural reference for async MT5 bots
- **gym-mtsim** (https://github.com/AminHP/gym-mtsim, ~422 stars) -- OpenAI Gym environment for MT5 trading, reinforcement learning
- **MQL5-JSON-API** (https://github.com/khramkov/MQL5-JSON-API) -- ZeroMQ bridge with real-time streaming
- **jimtin/algorithmic_trading_bot** (https://github.com/jimtin/algorithmic_trading_bot, ~137 stars) -- MT5 + Binance bot with video series
- **mt5linux** (https://github.com/lucas-campagna/mt5linux, ~116 stars) -- Linux bridge via Wine/RPyC

### Communities

- **Reddit r/algotrading** (~500K+ members): active for MT5 + Python discussions
- **MQL5.com Forum**: threads on Python integration, error -10003, multi-terminal management
- **Discord FXGears** (https://discord.com/invite/wEDAse9, ~20K members)
- **Quantreo Discord** (https://discord.gg/wXjNPAc5BH): accompanies Udemy MT5 Python course

### Guides

- TheForexGeek MT5 Python guide: https://theforexgeek.com/mt5-python-integration/
- Jim Tin's Medium series: "How to Build a MetaTrader 5 Python Trading Bot"
