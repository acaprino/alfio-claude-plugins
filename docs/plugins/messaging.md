# Messaging Plugin

> Design reliable messaging systems on the RabbitMQ 4.3 series. Exchange and queue topology design, clustering with Khepri, AMQP/MQTT/Stream protocol guidance, and production operations: upgrades, delivery patterns, sizing, and security hardening.

## Agents

### `rabbitmq-expert`

RabbitMQ and AMQP architecture expert. Designs queue topologies, configures exchanges and bindings, sets up clustering and high availability, diagnoses delivery issues, and tunes throughput.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch |
| **Use for** | RabbitMQ exchange and queue design, AMQP/MQTT troubleshooting, clustering and high availability, throughput tuning |

**Invocation:**
```
Use the rabbitmq-expert agent to [design/configure/optimize] [messaging system]
```

**Expertise:**
- **Exchange types** - direct, topic, fanout, headers, consistent-hash, x-modulus-hash, and local-random routing
- **Queue design** - classic, quorum, and stream queues, including strict quorum priority levels and native delayed retries; picking the right type per workload
- **Clustering and HA** - Khepri metadata store, quorum queue replication, federation, shovel, and local shovels
- **Protocols** - AMQP 0-9-1, AMQP 1.0, MQTT 5, Stream Protocol, and STOMP
- **Flow control** - prefetch tuning, publisher confirms, and consumer acknowledgment modes
- **Diagnostics** - rabbitmqctl inventory commands, staged health checks, and management API queries

---

## Skills

### `rabbitmq-production`

Production knowledge base for RabbitMQ 4.x: version timeline and upgrade gates, delivery patterns in client-neutral pseudocode, production sizing and monitoring thresholds, and security hardening.

| | |
|---|---|
| **Trigger** | Designing, operating, upgrading, monitoring, or securing RabbitMQ in production, or implementing a delivery pattern (retry, outbox, idempotency, RPC) |

**References:**
| Reference | Load when |
|---|---|
| `versions-and-upgrades.md` | Upgrades, breaking changes, client/library choices |
| `patterns.md` | Implementing any delivery pattern |
| `operations.md` | Sizing, monitoring, diagnostics beyond first aid |
| `security.md` | Hardening, TLS, multi-tenancy |

---

**Related:** [python-development](python-development.md) (Python implementation patterns for consumers/producers)
