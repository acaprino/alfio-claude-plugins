# Versions and Upgrades

Version timeline, per-series additions, breaking changes and denials, the Erlang/OTP baseline, client library choices, and the Kubernetes cluster operator for RabbitMQ 4.x. Load this reference before planning or executing an upgrade, or choosing a client library.

## Series timeline

Source: https://www.rabbitmq.com/release-information

- 4.0: GA August 2024
- 4.1.0: released 2025-04-15; community EOL 2026-01-31
- 4.2.0: released 2025-10-28; community EOL 2026-07-31
- 4.3.0: released 2026-04-23; community-supported until 2026-11-30
- Extended commercial support runs later per series

## What each series added

### 4.1

Source: https://www.rabbitmq.com/blog/2025/04/15/rabbitmq-4.1.0-is-released

- Quorum-queue log reads offloaded to channels/sessions for better consumer throughput
- Initial AMQP 1.0 filter expressions on streams (`properties` / `application-properties`)
- `rabbitmqadmin` v2
- Required feature flags auto-enable at node boot
- AMQP 0-9-1 initial max frame raised from 4096 to 8192 bytes
- MQTT Maximum Packet Size default lowered from 256 MiB to 16 MiB

### 4.2

Source: https://github.com/rabbitmq/rabbitmq-server/blob/main/release-notes/4.2.0.md

- Khepri becomes the default metadata store for NEW deployments
- AMQP 1.0 SQL filter expressions for stream consumers (comparison/logical/arithmetic, `LIKE`, `IN`, `IS NULL`); a superset of the 4.1 property filters
- Direct Reply-To for AMQP 1.0 (cross-protocol)
- Incoming and outgoing broker message interceptors (built-ins: timestamping, MQTT client ID injection)
- Local shovels: an intra-cluster protocol with higher throughput than AMQP shovels
- New `rabbitmqctl` commands for blue-green migration and message-size distribution analysis

4.2.9 (source: https://github.com/rabbitmq/rabbitmq-server/blob/main/release-notes/4.2.9.md): minimum Erlang raised to 27.0; super stream partitions capped at 1,000 by default.

### 4.3

Sources: https://github.com/rabbitmq/rabbitmq-server/blob/main/release-notes/4.3.0.md and https://www.rabbitmq.com/blog/2026/04/23/rabbitmq-4.3-release

- Khepri is the only metadata store; Mnesia removed entirely
- Quorum queues gain 32 strict priority levels (strictly higher first, per-priority message counts, priority-aware expiration)
- Native delayed retries: increasing or linear backoff on requeue, with a per-message override via the AMQP 1.0 `x-opt-delivery-time` annotation
- `acquired-count` split from `delivery-count`, so client-initiated requeues no longer count toward the poison delivery limit
- Consumer timeout handling moved into quorum queues with graceful AMQP 1.0 `released` disposition (classic queues and streams never evaluate consumer timeouts)
- Per-message memory overhead halved for messages up to 32 KiB
- Recovery snapshots for faster startup
- Ra upgraded to 3.x
- `x-modulus-hash` exchange moved into core

## Breaking changes and denials, by series

### Since 4.0

- Classic mirrored queues removed. Migrate to quorum BEFORE upgrading; blue-green recommended for complex topologies (https://www.rabbitmq.com/docs/3.13/migrate-mcq-to-qq)
- Quorum `delivery-limit` defaults to 20: messages are dropped or dead-lettered after 20 failed deliveries. `x-delivery-limit: -1` restores the old behavior but is not recommended; configure a DLX on all quorum queues
- `max_message_size` default is 16 MiB (was 128 MiB in 3.x); hard server cap 512 MiB
- `rabbitmq-diagnostics node_health_check` is a no-op

### Since 4.1

- `GET /api/aliveness-test` is a no-op. Replacements are targeted `rabbitmq-diagnostics` checks (`check_running`, `check_local_alarms`, `check_port_connectivity`) and granular `/api/health/checks/*` endpoints (https://www.rabbitmq.com/docs/http-api-reference)

### Since 4.2

- AMQP 1.0 messages without an explicit durable header default to NON-durable (spec compliance; a silent change for publishers)
- `rabbitmq_raft`-prefixed Prometheus metrics renamed and restructured; update Grafana dashboards
- Ineffective `*.cacerts` settings removed

### In 4.3

- Upgrade accepted only from 4.2.x, with six feature flags enabled first: `rabbitmq_4.2.0`, `rabbitmq_4.1.0`, `rabbitmq_4.0.0`, `khepri_db`, `quorum_queue_non_voters`, `message_containers_deaths_v2`. General rule: enable all stable feature flags before any major-series upgrade (https://www.rabbitmq.com/docs/upgrade)
- CQv1 removed: declaring `x-queue-mode` (any value) or `x-queue-version: 1` fails
- Transient non-durable non-exclusive classic queues denied by default. Escape hatch: `deprecated_features.permit.transient_nonexcl_queues = true` on all nodes before upgrading
- Global QoS (`basic.qos` with `global=true`) denied by default
- Partition-handling keys (`pause_minority`, `autoheal`, `pause_if_all_down`) are accepted but IGNORED; Khepri majority semantics apply
- `rabbitmqadmin` v1 HTTP endpoint removed

### Deprecated ecosystem

The `rabbitmq-delayed-message-exchange` plugin was archived April 2026 and is incompatible with 4.3 due to the Mnesia removal. A "message scheduler" replacement exists only in commercial Tanzu RabbitMQ.

## Erlang/OTP baseline

Source: https://www.rabbitmq.com/docs/which-erlang

- 4.3 requires 27.0 minimum
- 27.x fully supported
- 28.x supported for brand-new clusters only (known rolling-upgrade issue moving Khepri clusters from 27 to 28)
- 29 unsupported

## Client ecosystem

Source: https://www.rabbitmq.com/client-libraries/amqp-client-libraries

New official "RabbitMQ AMQP 1.0 clients" family, designed for 4.x with topology management and connection/topology recovery:

- Java: `rabbitmq-amqp-java-client` (Java 11+, 21 recommended)
- .NET: `rabbitmq-amqp-dotnet-client`
- Go: `rabbitmq-amqp-go-client`
- Python: `rabbitmq-amqp-python-client` (1.0.0 GA 2026-07-20, Python 3.10-3.14)

AMQP 0-9-1 clients:

- Java: `com.rabbitmq:amqp-client` 5.34.x maintenance line
- .NET: client v7, fully async (`IModel` renamed `IChannel`, `CreateBasicProperties()` removed; migration guide https://github.com/rabbitmq/rabbitmq-dotnet-client/blob/main/v7-MIGRATION.md)
- Python: pika 1.4.x (still AMQP 0-9-1 only)
- Node: amqplib is 2.x, requiring Node 18+ (`^0.10` pins are stale)

## Kubernetes cluster operator

Sources: https://github.com/rabbitmq/cluster-operator/releases and https://www.rabbitmq.com/kubernetes/operator/install-operator

- v2.22 line current (v2.22.3, Jul 2026)
- v2.22.0 switched the startup probe to HTTP, requiring RabbitMQ 4.2.4+ or 4.3.0+. Older images need the annotation `rabbitmq.com/legacy-startup-probe: "true"`, which is unsupported
- cert-manager required since operator 2.20
- Default deployed image is 4.2.6+ since v2.21
- Tested on Kubernetes 1.29-1.32
- Operator upgrades trigger rolling restarts; pause reconciliation first
