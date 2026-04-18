---
description: >
  Audit an existing Interactive Brokers trading system for reliability, error handling, and production readiness.
  TRIGGER WHEN: the user asks to review, audit, or validate an IB/TWS trading bot (reconnection, bracket orders, pacing, error codes, IBC automation).
  DO NOT TRIGGER WHEN: building a new IB system from scratch (use the ibkr-architect agent directly), or auditing non-IB trading systems (use /mt5-trading:mt5-audit for MT5).
argument-hint: "[path-or-description]"
---

# IB Trading System Audit

Analyze an existing IB trading system and produce an actionable audit report.

## Instructions

1. **Identify IB components** in the codebase:
   - Connection setup (TWS/Gateway, port, clientId)
   - Contract definitions and qualification
   - Market data subscriptions
   - Order execution logic
   - Reconnection handling
   - Error handling
   - Logging

2. **Audit each component** against best practices:

### Connection
- [ ] Using IB Gateway (not TWS) for production
- [ ] Using ib_async (not deprecated ib_insync or outdated ibapi from PyPI)
- [ ] ClientId strategy defined (separate data/orders)
- [ ] Connection timeout configured
- [ ] PACEAPI enabled (`setConnectOptions('+PACEAPI')`)
- [ ] Using offline/standalone TWS version (not auto-updating)

### Market Data
- [ ] Subscriptions cleaned up on disconnect
- [ ] Resubscription on reconnect implemented (especially after error 1101)
- [ ] Pacing violation prevention for historical data (throttle queue, caching)
- [ ] Unused subscriptions cancelled to free market data lines
- [ ] In-memory bar/ticker lists trimmed for long-running processes
- [ ] Correct whatToShow used (MIDPOINT for forex, TRADES for stocks)

### Orders
- [ ] Bracket orders used for risk management
- [ ] transmit=False pattern for bracket submission
- [ ] All order states handled (including Inactive)
- [ ] execDetails monitored as authoritative fill source (not just orderStatus)
- [ ] Partial fill logic implemented
- [ ] Order ID management is collision-free (nextValidId or getReqId)
- [ ] Cancel-fill race condition handled (never assume cancel succeeded)
- [ ] Order efficiency ratio monitored (<=20:1)

### Error Handling
- [ ] errorEvent handler registered
- [ ] Connectivity codes handled (1100, 1101, 1102)
- [ ] Data codes handled (162 pacing, 200, 354)
- [ ] Order codes handled (103 duplicate ID, 201 rejected, 202 cancelled)
- [ ] Farm status codes logged but not alarmed (2104, 2106, 2158)
- [ ] WinError 10038 handled (Windows socket close)
- [ ] Errors logged with context (orderId, contract, timestamp)

### Reconnection
- [ ] disconnectedEvent handler with reconnection logic
- [ ] Exponential backoff implemented (not fixed-interval retry)
- [ ] Post-reconnect state recovery (positions, orders, subscriptions, executions)
- [ ] Heartbeat monitoring (reqCurrentTime or setTimeout)
- [ ] Handles daily reset window (~23:45-00:45 ET)

### Production Hardening
- [ ] IBC configured for automated Gateway lifecycle
- [ ] Task Scheduler (or equivalent) for auto-restart
- [ ] Structured logging with rotation
- [ ] Firewall restricts API to localhost only
- [ ] Java memory set to 4096 MB minimum
- [ ] Antivirus exclusion for TWS directory
- [ ] Paper trading validated before live deployment

3. **Generate report** with:
   - Current state assessment (what is implemented correctly)
   - Risk areas (missing or misconfigured components)
   - Priority improvements ordered by production impact
   - Code examples for each recommendation
