# Operations

Production sizing, monitoring thresholds, and diagnostics for RabbitMQ 4.x beyond the `rabbitmq-expert` agent's inline first aid. Load this reference for capacity planning, alerting, or an incident that outgrows the agent's DIAGNOSTICS section.

## Production checklist numbers

Source: https://www.rabbitmq.com/docs/production-checklist

- **Memory watermark** (`vm_memory_high_watermark.relative`): default 0.6, sane range 0.4-0.7. Above 0.7 needs care. Keep 256+ MiB available regardless of the watermark.
- **Disk free limit** (`disk_free_limit.absolute`): default 50MB is development-only. Production minimum is 4G, at least matching the RAM watermark. When in doubt, overprovision.
- **File descriptors**: 50K+ for production, up to 500K is reasonable. Sizing formula: 95th-percentile concurrent connections x 2 + total queue count.
- **Hardware floor**: 4 CPU cores, 4+ GiB RAM, durable local SSD/NVMe (never NAS). Do not colocate with I/O-heavy services. Khepri, quorum queues, and streams all assume durable storage.
- **Network sizing**: message rate x message size x 110% x 8 bits. Worked example: 20K msg/s at 6 KB needs ~1.056 Gbit/s.
- One queue is bounded by roughly one CPU core: split load across queues to match core count. Never set management statistics rate mode to `detailed` in production (community, https://www.cloudamqp.com/blog/part4-rabbitmq-13-common-errors.html).

## Cluster sizing and Khepri

Minimum 3 nodes, always odd (3/5/7). Under Khepri (the only store in 4.3), a node majority must be online for the cluster to be available, and legacy partition-handling strategies are ignored. Security bootstrap items live in `security.md`.

## Quorum queue operations

Source: https://www.rabbitmq.com/docs/quorum-queues

- **WAL**: `raft.wal_max_size_bytes` defaults to 512 MiB. Node memory should be at least 3x the WAL limit, 4x for high throughput.
- **Per-message index cost**: ~32 bytes in the in-memory index regardless of message body size (~1 MB per 30,000 queued messages). Long backlogs eat memory; move 5M+ backlogs to streams.
- **Leader rebalancing**: leaders pile onto surviving nodes after rolling restarts. Run `rabbitmq-queues rebalance quorum` (supports `--queue-pattern`).
- **Membership**: never changes automatically. Use `grow` / `shrink` / `add_member` / `delete_member` when resizing. `x-quorum-initial-group-size` defaults to 3. Never spread one queue past 7 nodes.
- **Dead-lettering**: at-most-once by default. `dead-letter-strategy: at-least-once` requires `overflow: reject-publish` and costs memory and CPU.
- **Topology ceiling**: above ~5,000 quorum queues, reconsider the topology; classic queues or streams may fit better.

## Streams operations

Source: https://www.rabbitmq.com/docs/streams

Retention triggers only when a segment rolls. `x-stream-max-segment-size-bytes` defaults to 500,000,000 bytes, and at least one segment is always kept, so a low-traffic stream can hold data past its `x-max-age` (format like `7D`). Small retention targets need smaller segments to actually retire on schedule. Streams need fast disks but use less CPU and memory than quorum queues.

## Monitoring

- **Stack**: `rabbitmq_prometheus` plugin plus Grafana. Production scrape interval 30s (30-60s range; the exporter is designed for 15-30s). Source: https://www.rabbitmq.com/docs/prometheus
- **Watch**: node memory used vs limit, file descriptors used vs total, Erlang process count; cluster totals for connections, channels, queues, consumers; per-queue ready vs unacked and publish vs deliver rates; connection open/close churn rates. Source: https://www.rabbitmq.com/docs/monitoring
- **Official cluster-operator alert rules** (https://github.com/rabbitmq/cluster-operator/blob/main/observability/prometheus/rule-file.yml):
  - Memory: `rabbitmq_process_resident_memory_bytes / rabbitmq_resident_memory_limit_bytes * 100 > 90`
  - File descriptors: `rabbitmq_process_open_fds / rabbitmq_process_max_fds * 100 > 90` for 2m
  - Unroutable drops: `increase(rabbitmq_channel_messages_unroutable_dropped_total[5m]) >= 1` (catches missing bindings)
- **Standard heuristics** (community, https://samber.github.io/awesome-prometheus-alerts/rules/message-brokers/rabbitmq/): sustained queue depth over a threshold; publish rate exceeding deliver rate for a sustained window; connection churn above ~100/s.

## Health checks

Staged model, cheapest first: `rabbitmq-diagnostics ping`, then `check_running`, `check_local_alarms`, `check_port_connectivity`, up to `check_virtual_hosts`. Higher stages have more false positives; keep them out of aggressive load balancer probes (LB TCP health checks are a named cause of connection churn). `node_health_check` is a no-op since 4.0. `GET /api/aliveness-test` is a no-op since 4.1. Granular endpoints live under `/api/health/checks/*`.

## Diagnostics first aid

Inventory commands (mirrors the `rabbitmq-expert` agent's DIAGNOSTICS section):

```bash
rabbitmqctl list_queues name messages consumers memory
rabbitmqctl list_connections name state channels
rabbitmqctl list_channels name consumer_count prefetch
rabbitmqctl list_exchanges name type
rabbitmqctl list_bindings
rabbitmqctl cluster_status
rabbitmqctl environment
```

Management API:

```bash
curl -u guest:guest http://localhost:15672/api/queues/%2f/my-queue
curl -u guest:guest http://localhost:15672/api/queues?columns=name,messages,message_stats
curl -u guest:guest http://localhost:15672/api/nodes
```

Extended symptoms table:

- **Stuck messages**: consumers down, prefetch exhausted, unacked accumulation
- **High memory**: unbounded queues, quorum backlog index cost, connection count
- **Publish-rate drops**: memory or disk alarm, flow control
- **Consumer lag**: slow consumer, low prefetch, one queue per core bound
- **Unexpected dead-lettering**: delivery-limit 20 default
- **FD exhaustion**: churn storm
- **Partition symptoms under Khepri**: minority side unavailable

## Tracing

The broker itself emits no traces. The pattern is an OpenTelemetry Collector `rabbitmq` receiver for broker metrics, paired with client-side instrumentation that propagates a `traceparent` header in message headers, for end-to-end delay attribution between consumer code and broker delivery.
