# Trading Broker Integration Plugin

> Broker integration for algorithmic trading in Python: Interactive Brokers via the TWS API and ib_async across equities, options, futures, FX, CFDs and crypto (contracts and market rules, order types and TIF/fill-mode capability resolution, brackets, a classified catalog of all 458 published TWS message codes, venue-behaviour verification tooling, reconnection resilience, deployment on Windows, Linux, macOS and Docker), MetaTrader 5 via the official synchronous API (polling-based event systems, order execution with fill modes, historical data, the aiomql async framework, a ZeroMQ bridge, Windows production deployment), and the vendor-neutral vocabulary shared between them: five access archetypes, the single-broker/multi-broker-platform axis, a reference order-lifecycle state machine, session and recovery patterns, and a six-rank evidence ladder with provenance tags.

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

### `mt5-architect`

Expert in MetaTrader 5 Python algotrading system design, implementation, and debugging.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch` |
| **Use for** | Building MT5 trading bots, connecting to MT5 terminal via Python, implementing polling event loops, executing orders with correct fill modes, handling MT5 disconnections, deploying MT5 bots on Windows |

**Invocation:**
```
Use the mt5-architect agent to [design/implement/debug] [trading component]
```

---

## Skills

### `broker-vocabulary`

The vocabulary that is the same for every broker: what kind of access path a system has, how to model an order's life without borrowing one vendor's words for it, and what a claim about a venue is actually worth.

| | |
|---|---|
| **Trigger** | Comparing brokers or integration paths, starting an integration against a broker with no dedicated coverage in this skill, or naming what kind of access path a system uses |

**Reference documents:** access-archetypes, order-lifecycle-reference-model, session-and-recovery, evidence-and-probes.

---

### `ibkr`

Authoritative reference for Interactive Brokers integration in Python, across every asset class, with tooling to verify venue behaviour against a paper Gateway instead of guessing.

| | |
|---|---|
| **Trigger** | Building, auditing or debugging anything that talks to TWS or IB Gateway via the TWS API and ib_async: contracts, market data, orders, brackets, error codes, reconnection, deployment, or a question about how IBKR actually behaves |

**Reference documents:** tws-api-architecture, contracts-and-instruments, event-driven-data, order-execution, order-types-and-attributes, bracket-orders, order-lifecycle-contracts, error-codes-and-verdicts, account-state-and-pnl, venue-boundary-failure-modes, venue-questions-and-probes, reconnection-resilience, gateway-automation, gateway-verification.

---

### `mt5`

Knowledge base for the official MetaTrader 5 API, its polling model, and Windows-side production concerns.

| | |
|---|---|
| **Trigger** | Building, implementing, optimizing, or debugging MT5 trading systems with Python, including the aiomql and ZeroMQ bridge alternatives |

**Reference documents:** api-architecture, event-system-polling, order-execution, data-feed-historical, production-resilience.

---

## Commands

### `/trading-broker-integration:ibkr-audit`

Audit an existing Interactive Brokers trading system for reliability, error handling, and production readiness. Covers connection, market data, orders, close path and netting, terminal preset config, error handling, venue boundary, reconnection, historical data integrity, and production hardening.

```
/trading-broker-integration:ibkr-audit [path-or-description]
```

---

### `/trading-broker-integration:ibkr-verify`

Answer a question about IBKR behaviour with evidence instead of a guess: whether IBKR supports something, why an order was refused, what a code means, or a claim about venue behaviour verified against a real gateway. Walks a fixed evidence ladder (capability list, documentation, probe against a paper Gateway) and reports which rung produced the answer.

```
/trading-broker-integration:ibkr-verify [question, code, or contract]
```

---

### `/trading-broker-integration:mt5-audit`

Audit an existing MetaTrader 5 trading system for reliability, error handling, and production readiness. Covers connection setup, event/polling loop structure, order execution, data fetching, error handling, reconnection, and logging.

```
/trading-broker-integration:mt5-audit [path-or-description]
```

---

**Related:** [python-development](python-development.md) (Python best practices for trading code)
