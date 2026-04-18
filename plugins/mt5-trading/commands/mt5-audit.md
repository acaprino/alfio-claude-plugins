---
description: >
  Audit an existing MetaTrader 5 trading system for reliability, error handling, and production readiness.
  TRIGGER WHEN: the user asks to review, audit, or validate an MT5 Python trading bot (polling loops, fill modes, reconnection, order retcodes, Windows deployment).
  DO NOT TRIGGER WHEN: building a new MT5 system from scratch (use the mt5-architect agent), or auditing non-MT5 systems (use /ibkr-trading:ibkr-audit for IB).
argument-hint: "[path-or-description]"
---

# MT5 Trading System Audit

Analyze an existing MT5 Python trading system and produce an actionable audit report.

## Instructions

1. **Identify MT5 components** in the codebase:
   - Connection setup (initialize, login, server)
   - Event/polling loop structure
   - Order execution logic
   - Data fetching approach
   - Error handling
   - Reconnection handling
   - Logging

2. **Audit each component** against best practices:

### Connection
- [ ] initialize() called once at startup (not in loops)
- [ ] shutdown() called once at exit
- [ ] All required params: path, login, server, password, timeout
- [ ] /portable flag used if installed in Program Files
- [ ] Single process per MT5 terminal instance

### Event System
- [ ] Polling loop implemented (not missing events)
- [ ] New candle detection via time field comparison
- [ ] Position change detection via ticket set comparison
- [ ] Appropriate poll interval for strategy timeframe
- [ ] Not using time.sleep() excessively (CPU waste)

### Order Execution
- [ ] Fill mode detected dynamically per symbol (not hardcoded)
- [ ] order_check() called before every order_send()
- [ ] All retcodes handled (especially 10030 invalid fill, 10016 invalid stops)
- [ ] Position ticket specified when closing in hedging mode
- [ ] Magic number used (non-zero) for all bot orders
- [ ] Server-side SL/TP set on every position
- [ ] symbol_select() called before trading operations
- [ ] Broker-specific values queried at runtime (stops_level, filling_mode, etc.)

### Data
- [ ] UTC timezone used for all datetime objects (pytz)
- [ ] "Max bars in chart" set to Unlimited in terminal
- [ ] Data cached locally for efficiency (Parquet recommended)
- [ ] Incremental updates (not full re-download each run)

### Error Handling
- [ ] Every API call checked for None return
- [ ] last_error() called on failures for diagnostics
- [ ] IPC errors handled (-10001, -10002, -10003, -10005)
- [ ] Retcode 10004 (requote) triggers price refresh + retry
- [ ] Retcode 10024 (too many requests) triggers backoff
- [ ] Silent error pattern avoided (no unchecked returns)

### Thread Safety
- [ ] All MT5 calls on single thread
- [ ] asyncio used for concurrency (not threading)
- [ ] No concurrent access to IPC pipe
- [ ] Multi-account uses separate processes

### Reconnection
- [ ] terminal_info().connected checked periodically (health check)
- [ ] Exponential backoff reconnection implemented
- [ ] psutil used to monitor terminal64.exe process
- [ ] subprocess.Popen for terminal restart capability
- [ ] MT5 auto-updates disabled during trading hours
- [ ] Weekend handling implemented (sleep mode)

### Production Hardening
- [ ] Structured logging with rotation
- [ ] Circuit breaker (stop after N consecutive errors)
- [ ] Kill switch (flatten all positions and halt)
- [ ] Process auto-restart (Task Scheduler or watchdog)
- [ ] Demo vs live behavior differences accounted for
- [ ] State reconciliation on restart (positions, orders)

3. **Generate report** with:
   - Current state assessment (what is implemented correctly)
   - Risk areas (missing or misconfigured components)
   - Priority improvements ordered by production impact
   - Code examples for each recommendation
