# IBKR Trading Plugin

> Interactive Brokers algotrading - TWS API architecture, ib_async event-driven programming, market data subscriptions, order execution with bracket orders, order lifecycle verdict contracts, historical data pacing rules, contract/tick/sizing venue-boundary failure modes, reconnection resilience, Gateway automation with IBC, and Windows production deployment. Heavily production-derived: netted close paths, terminal order presets, zombie connections, stub bars and forming bars, silent-failure diagnosis.

## Agents

### `ibkr-architect`

Expert in Interactive Brokers algotrading system design, implementation, and debugging.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch` |
| **Use for** | Building IB trading bots, connecting to TWS/IB Gateway, implementing market data subscriptions, designing order execution logic, handling IB reconnection, diagnosing silent order/close failures (wrong-side closes, preset cancellations, swallowed rejections), deploying IB trading systems on Windows |

**Invocation:**
```
Use the ibkr-architect agent to [design/implement/debug] [trading component]
```

---

## Skills

### `ibkr-trading`

Comprehensive knowledge base for building production-grade algorithmic trading systems with Interactive Brokers TWS API and ib_async in Python.

| | |
|---|---|
| **Trigger** | Building, optimizing, or debugging IB trading systems with Python |

**Reference documents:** tws-api-architecture, event-driven-data, order-execution, order-lifecycle-contracts, reconnection-resilience, gateway-automation, venue-boundary-failure-modes.

---

## Commands

### `/ibkr-audit`

Audit an existing Interactive Brokers trading system for reliability, error handling, and production readiness. Covers connection, market data, orders, close path and netting, terminal preset config, error handling, venue boundary, reconnection, historical data integrity, and production hardening.

```
/ibkr-audit [path-or-description]
```

---

**Related:** [mt5-trading](mt5-trading.md) (MetaTrader 5 alternative) | [python-development](python-development.md) (Python best practices for trading code)
