# MT5 Python API Architecture

The official `MetaTrader5` PyPI package (by MetaQuotes) talks to the MT5 terminal via **Windows named pipes** (local IPC). Synchronous request-response only, no callbacks, no streaming. Polling is the only pattern. Current version mirrors the platform build (e.g. 5.0.5640), Python 3.6-3.13.

## When to use

Building any Python algotrading system on MT5. For true event-driven (push) behavior you need an MQL5 EA that bridges to Python via ZeroMQ -- see "Alternative libraries" below.

## Hard constraints (memorize before designing)

- **Windows-only.** Named pipes IPC has no native cross-platform path. Linux options below are workarounds.
- **No exceptions, no docstrings, no logging, no context manager.** Every call returns `None` on failure -- check return value AND `mt5.last_error()` after every call.
- **One Python process = one MT5 terminal connection.** No multi-tenant model.
- **Not thread-safe.** The pipe is single -- concurrent access from threads = race conditions, crashes, or corrupted data. Serialize calls or use a single dedicated worker thread.
- **No callbacks / push events.** Pure request-response; you build your own event loop on top of polling.
- **No Strategy Tester access.** Backtesting is MQL5-only; from Python use Backtrader / Backtesting.py with historical data downloaded via the API.

## Gotchas

- **Errors are silent.** `order_send()` returning `None` is a hard failure -- but the API doesn't raise. `mt5.last_error()` returns `(code, description)`. Wrap every call in a check.
- **MQL5 EAs and Python coexist** on the same terminal. EAs run on charts; Python operates externally. The terminal option **"Disable automatic trading via external Python API"** blocks Python trading (retcode 10027) while leaving EAs active -- a common cause of "my bot stopped working" after broker config changes.
- **Strategy Tester blocks all socket functions.** Inside the tester, MQL5 EAs cannot communicate with Python via sockets. There is no way to backtest a Python strategy through the MT5 tester.
- **`pip install MetaTrader5` ships a compiled C library** -- the install is fast but it must match the platform's Python ABI. Mismatch = silent import success but `initialize()` returns False with no useful error.
- **The API exposes only 32 functions** -- if you can't see it in the docs index, it's not there. There is no `OnTick()`, no event subscription, no async variant.

## Library choice

| Library | Streaming | Async | Cross-platform | Status | Best for |
|---------|-----------|-------|----------------|--------|----------|
| **MetaTrader5** (official) | Polling | Sync | Windows | Active | Direct access, low overhead |
| **aiomql** | Async polling | asyncio | Windows | Active | Best Python-pure async framework |
| **MQL5-JSON-API** (ZMQ) | **True streaming** | Yes | Any | Moderate | True event-driven via MQL5 EA bridge |
| **metaapi-cloud-sdk** | WebSocket | Yes | Any | Active (paid) | Cross-platform, paid cloud |
| **mt5linux** / **pymt5linux** | Polling | Sync | Linux (Wine + RPyC) | Inactive / fork | Linux dev, not production |

Avoid: `pymt5adapter` (deprecated), `pymt5` (gateway-only).

## Comparison with IBKR TWS API (mental model)

| Aspect | MT5 Python | IBKR TWS API |
|--------|-----------|--------------|
| Architecture | Sync polling | Event-driven callbacks |
| Rate limits | None documented (local IPC, ~63us per call) | 50 msg/sec, pacing rules |
| Data cost | Included with account | Paid exchange subscriptions |
| Data source | Broker-dependent | Exchange-sourced |
| Cross-platform | Windows only | Windows / Linux / macOS |
| Streaming | Polling (or ZMQ bridge) | Native callbacks |

If you're coming from IBKR expecting `EWrapper` callbacks, **you build the entire event system from scratch on MT5** (see `event-system-polling.md`).

## Official docs

- Python API home: https://www.mql5.com/en/docs/python_metatrader5
- Per-function reference: `https://www.mql5.com/en/docs/python_metatrader5/mt5{functionname}_py`
- MetaEditor + Python integration: https://www.metatrader5.com/en/metaeditor/help/development/python
- Release notes: https://www.metatrader5.com/en/releasenotes
- aiomql: https://github.com/Ichinga-Samuel/aiomql
- MQL5-JSON-API (ZMQ bridge): https://github.com/khramkov/MQL5-JSON-API

## Related

- `event-system-polling.md` -- how to build an event loop on top of polling
- `data-feed-historical.md` -- the `copy_rates_*` and `copy_ticks_*` family
- `order-execution.md` -- `order_send()`, fill modes, retcode handling
- `production-resilience.md` -- Windows deployment, watchdog, weekend gate
