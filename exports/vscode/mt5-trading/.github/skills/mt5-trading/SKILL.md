---
name: mt5-trading
description: >
  Comprehensive MetaTrader 5 Python algotrading knowledge base covering the official synchronous
  API, polling-based event systems, order execution with fill modes, historical data functions,
  reconnection resilience, and Windows production deployment. Includes aiomql and ZeroMQ bridge
  alternatives. Use when building, implementing, writing, coding, creating, optimizing, or
  debugging MT5 trading systems with Python.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: mt5-trading
---

# MetaTrader 5 Python Algotrading

Knowledge base for building production-grade algorithmic trading systems with MetaTrader 5 Python API.

## When to Use

- Connecting to MT5 terminal via the official Python API
- Building polling-based event systems (on_tick, on_new_candle, on_position)
- Executing orders with correct fill modes (FOK, IOC, Return)
- Downloading historical data (copy_rates, copy_ticks)
- Handling MT5 disconnections and terminal restarts
- Deploying MT5 bots on Windows with process monitoring
- Choosing between official API, aiomql, and ZeroMQ bridge

## Quick Start

For 80% of use cases, start with:
1. **Library**: `pip install MetaTrader5` (official) or `pip install aiomql` (async wrapper)
2. **Connection**: `mt5.initialize(path=..., login=..., server=..., password=...)`
3. **Event system**: polling loop with candle/tick/position change detection
4. **Orders**: `order_check()` before `order_send()`, always detect fill mode dynamically
5. **Risk**: server-side SL/TP on every position (non-negotiable)
6. **Resilience**: health check every 30-60s, psutil process monitoring, exponential backoff

Then harden incrementally:
- Silent errors -- wrap every API call with None check + last_error()
- Fill mode rejections (10030) -- dynamic filling_mode detection per symbol
- Terminal crashes -- psutil watchdog + subprocess restart
- Weekend handling -- datetime.weekday() sleep mode

## Reference Materials

- `api-architecture.md` -- MT5 Python API architecture, 32 functions, named pipes IPC, MQL5 EA vs Python, library comparison
- `event-system-polling.md` -- polling patterns, new candle detection, tick monitoring, position tracking, concurrency rules
- `order-execution.md` -- order_send, fill modes (FOK/IOC/Return), hedging vs netting, retcodes, risk checks, magic numbers
- `data-feed-historical.md` -- copy_rates, copy_ticks, depth, timezone caveats, caching, data quality, broker differences
- `production-resilience.md` -- disconnection handling, reconnection, weekend management, Windows deployment, community resources

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Library | Official MetaTrader5 | Need async: aiomql. Need true streaming: ZeroMQ bridge |
| Event model | Polling (1-5s interval) | Tick-sensitive: poll 100-250ms. True events: ZeroMQ EA bridge |
| Fill mode | Detect dynamically per symbol | Never hardcode -- changes between brokers/symbols |
| Account mode | Hedging (most forex brokers) | Check account_info().margin_mode at startup |
| Data caching | Parquet + Zstandard | Tick data -- partition by day/month |
| Concurrency | asyncio (single thread) | Multi-account -- separate processes per terminal |
| Backtesting | Python framework (Backtrader, Backtesting.py) | Need MT5 tester -- MQL5 EA wrapper |
| SL/TP | Server-side always | Python trailing only as supplement, never as sole protection |
