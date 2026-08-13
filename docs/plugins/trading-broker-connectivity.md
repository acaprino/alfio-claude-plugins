# Trading Broker Connectivity Plugin

> Vendor-neutral vocabulary for programmatic broker integration: five access archetypes, a reference order state machine with the three layers that can refuse an order, session and recovery patterns, and the six-rank evidence ladder with provenance tags that decides what a claim about a venue is worth

## Skills

### `trading-broker-connectivity`

The vocabulary that is the same for every broker: what kind of access path a system has, how to model an order's life without borrowing one vendor's words for it, and what a claim about a venue is actually worth.

| | |
|---|---|
| **Trigger** | Comparing brokers or integration paths, starting an integration against a broker with no dedicated plugin, or naming what kind of access path a system uses |

**Reference documents:** access-archetypes, order-lifecycle-reference-model, session-and-recovery, evidence-and-probes.

---

**Related:** [ibkr-trading](ibkr-trading.md) (uses the `local-terminal` archetype) | [mt5-trading](mt5-trading.md) (uses the `local-terminal` archetype)
