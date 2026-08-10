# Messaging Plugin Deepening Design

Date: 2026-08-10
Status: approved, pending implementation plan

## Goal

Deepen the `messaging` plugin (today a single 218-line `rabbitmq-expert` agent) with the best practices, patterns, real-world mistakes, anti-patterns, and version updates surfaced by an August 2026 re-research pass. The plugin stays RabbitMQ-only. The current content claims "RabbitMQ 4.x coverage" but contains facts that are now wrong, not merely stale: the current stable series is 4.3 (4.3.4), and 4.2/4.1 community support has already ended.

## Decisions taken during brainstorming

1. **Scope: RabbitMQ only.** The trigger keeps excluding Kafka, NATS, Redis Streams, and other brokers. No broker-selection guide.
2. **Code examples become client-neutral pseudocode plus AMQP properties.** The existing Node.js (amqplib) blocks are converted. No client-specific pattern examples.
3. **Shape: lean agent plus production skill with references** (approach B of 3). A single enriched agent (approach A) was rejected because the research yielded too much high-value operational detail (thresholds, alert rules, upgrade gates) to fit a single file without cuts. Adding an `/messaging:mq-audit` command (approach C) was deferred as a possible follow-up, not part of this design.
4. **No upstream delegation.** A marketplace scan found no installable upstream covering RabbitMQ. The closest external content (martinholovsky/claude-skills-generator `rabbitmq-expert`, MIT, 1555 lines) is less current than our agent (no 4.x facts, calls mirrored queues "deprecated" when they were removed in 4.0, contains template-assembly artifacts). It is used only as a research pointer for two gaps we do have (security bootstrapping, connection resilience), with every fact verified against official RabbitMQ docs. Nothing is copied, per the standing no-vendored-copies policy.
5. **RabbitMQ's current version is stated in exactly one file** (the skill's SKILL.md), so future refreshes touch one anchor. Lesson taken from the 2026-08 ibkr-trading refresh.

## Components

### 1. Agent: `plugins/messaging/agents/rabbitmq-expert.md` (rewritten, ~300 lines)

Stays the decision-maker: decision frameworks, essential knowledge, anti-patterns, diagnostics entry points. Detail moves to the skill references, which the agent points to explicitly.

Corrections to currently wrong facts:

- Khepri timeline: fully supported but opt-in through 4.1, default metadata store for new clusters in 4.2, the only store in 4.3 (Mnesia removed). The current "default in 4.1+" claim is wrong.
- Lazy queues: removed. In 4.3 declaring a queue with `x-queue-mode` (any value) or `x-queue-version: 1` fails; CQv2 is the only classic-queue implementation.
- `rabbitmq-diagnostics node_health_check` is a no-op since 4.0 and `GET /api/aliveness-test` since 4.1; replaced in the diagnostics section by targeted checks (`check_running`, `check_local_alarms`, `check_port_connectivity`) and `/api/health/checks/*`.
- Quorum queues have a default `delivery-limit` of 20 since 4.0; messages are dropped after 20 failed deliveries unless a DLX is configured. In 4.3 client-initiated requeues no longer count toward the limit (acquired-count split).
- Global QoS (`basic.qos` with `global=true`) and transient non-exclusive classic queues are denied by default in 4.3.
- AMQP 1.0 messages without an explicit durable header are non-durable since 4.2 (`delivery_mode: 2` remains correct for AMQP 0-9-1 only).
- Priority workloads: quorum queues support 32 strict priority levels in 4.3, flipping the recommendation away from classic `x-max-priority` queues.
- Partition handling: `pause_minority` and friends are ignored under Khepri (accepted but unused in 4.3); Khepri majority semantics apply.

Updated decision frameworks: classic vs quorum vs stream selection including the official "when NOT to use quorum queues" criteria (transient or exclusive queues, declaration churn, lowest-latency needs, no confirms/acks, 5M+ backlogs, high fan-out) and the ~5,000 quorum-queue topology ceiling.

New and extended anti-patterns (kept terse in the agent, elaborated in references):

- The delayed-message-exchange plugin: archived April 2026, unmaintained, single-node Mnesia storage, killed by Mnesia removal in 4.3. Never introduce it in new designs; use fixed-TTL tier queues or an external scheduler.
- Per-message TTL for retry delays: broken by design (expired messages are only discarded at the queue head, so a long-TTL message blocks shorter ones behind it). Retry tiers must use per-queue TTL.
- Sharing one connection for publishing and consuming: a memory alarm blocks all publishing connections cluster-wide, and on a shared connection the block also stalls consumer acks, deadlocking the drain.
- Unlimited prefetch: one consumer grabs the whole backlog, risks OOM and mass redelivery.
- The eight existing anti-patterns stay (unbounded queues, missing confirms, single-node production, queue-per-message, auto-ack for critical messages, connection or channel churn, mirrored queues, basic.get polling), with the mirrored-queues entry reframed from "deprecated" to "removed in 4.0, upgrade gate".

Frontmatter unchanged in shape (`model: inherit`, `color: blue`, YAML `>` description with TRIGGER WHEN / DO NOT TRIGGER WHEN). The description gains "4.3" instead of "4.x" wording only where it does not duplicate the version anchor rule (the description may say "RabbitMQ 4.x" generically; the precise current version lives in SKILL.md).

### 2. Skill: `plugins/messaging/skills/rabbitmq-production/`

`SKILL.md`: quick reference (queue-type decision table, key production thresholds) plus an index of the references and when to load each. Frontmatter with TRIGGER WHEN / DO NOT TRIGGER WHEN in house style. States the current RabbitMQ series (4.3, latest patch 4.3.4) as the single version anchor for the plugin.

`references/versions-and-upgrades.md`:

- Series timeline with dates and community-support windows: 4.0 (Aug 2024), 4.1.0 (15 Apr 2025, EOL 31 Jan 2026), 4.2.0 (28 Oct 2025, EOL 31 Jul 2026), 4.3.0 (23 Apr 2026, supported until 30 Nov 2026).
- Headline features per series: 4.1 (quorum-queue log read offloading, initial AMQP 1.0 stream filters, rabbitmqadmin v2), 4.2 (Khepri default for new clusters, AMQP 1.0 SQL filter expressions, Direct Reply-To for AMQP 1.0, message interceptors, local shovels, blue-green migration commands), 4.3 (Khepri-only, 32 quorum priority levels, native delayed retries with backoff on requeue, acquired-count vs delivery-count split, consumer timeout handling per queue type, halved per-message memory overhead up to 32 KiB).
- Breaking changes and denials: 4.3 upgrade only from 4.2.x with six feature flags enabled first (`rabbitmq_4.2.0`, `rabbitmq_4.1.0`, `rabbitmq_4.0.0`, `khepri_db`, `quorum_queue_non_voters`, `message_containers_deaths_v2`); CQv1 and lazy-mode declaration failures; transient non-exclusive queues and global QoS denied by default; partition-handling config ignored; AMQP 1.0 durable default flip in 4.2; MQTT max packet size 256 MiB to 16 MiB in 4.1; `max_message_size` default 16 MiB since 4.0 (hard cap 512 MiB).
- Erlang baseline: 27.0 minimum for 4.3 and for 4.2.9+; Erlang 28 supported for brand-new clusters only; 29 unsupported.
- Client ecosystem: the official AMQP 1.0 client family (Java, .NET, Go, Python 1.0.0 GA Jul 2026) with topology recovery; .NET client v7 async rewrite (`IModel` renamed `IChannel`); amqplib 2.x (Node 18+; `^0.10` pins are stale); pika 1.4.x still AMQP 0-9-1 only; Java amqp-client 5.34.
- Kubernetes cluster-operator: v2.22 line, HTTP startup probe requires RabbitMQ 4.2.4+/4.3.0+, cert-manager required since 2.20, default image 4.2.6+, pause reconciliation before operator upgrades.

`references/patterns.md` (all pseudocode plus AMQP properties and queue arguments):

- Publisher confirms: synchronous vs asynchronous tradeoff, retransmit-on-reconnect rule (accepting duplicates), `mandatory` flag or alternate exchange for unroutable capture, and the unroutable-drop alert that pairs with it.
- Consumer acknowledgment: manual ack after processing, nack/requeue semantics, poison quarantine for free via the default delivery-limit 20 plus DLX, alert on DLX queue depth.
- Retry with exponential backoff: fixed-TTL tier queues (for example retry.5s, retry.30s, retry.5m) each with per-queue `x-message-ttl` and DLX routing back to the work queue, attempt count via `x-death`; why per-message TTL cannot work; note that 4.3 native delayed retries replace many hand-built topologies.
- Idempotent consumer: exactly-once is impossible; official prescription is idempotency over deduplication, with the `redelivered`-flag optimization when dedup is expensive.
- Transactional outbox: message plus business change in one DB transaction, relay publishes with confirms, still at-least-once.
- Claim check: payload in object storage or DB, reference in the message; pairs with the 16 MiB default cap.
- RPC: `reply_to` plus `correlation_id`, exclusive auto-delete callback queue; Direct Reply-To including the 4.2 AMQP 1.0 form.
- Connection management: one long-lived connection per process, separate connections for publishing and consuming (memory-alarm deadlock rationale), one channel per thread, reconnect with exponential backoff, connection pooling sketch, heartbeat floor (~5s minimum, ~11 minutes to detect a dead TCP peer without heartbeats).
- Streams: single active consumer with offset resume on takeover (the restart-from-zero bug), offset storage every few thousand messages rather than per message, Bloom-filter filtering is probabilistic so clients must re-check filter values, streams have no TTL/priority/DLX, per-consumer prefetch only.
- Topic routing and priority: existing topic wildcard table kept; priority guidance rewritten around quorum 32 strict levels with classic `x-max-priority` as the legacy fallback (~5 levels max advisory).

`references/operations.md`:

- Production checklist numbers: `vm_memory_high_watermark.relative` default 0.6, sane range 0.4 to 0.7; `disk_free_limit.absolute` minimum 4G (50MB default is dev-only); 50K+ file descriptors with the sizing formula (95th-percentile connections x 2 + queue count); hardware floor (4 cores, 4+ GiB RAM, local SSD/NVMe); network sizing formula (rate x size x 110% x 8 bits).
- Cluster sizing: 3/5/7 odd node counts, Khepri majority-online requirement, security bootstrap pointers to security.md.
- Quorum-queue operations: WAL `raft.wal_max_size_bytes` default 512 MiB with node memory at 3x to 4x the WAL limit; ~32 bytes in-memory metadata per message (roughly 1 MB per 30,000 queued messages); leader rebalancing after rolling restarts (`rabbitmq-queues rebalance quorum`); membership grows or shrinks only explicitly; `x-quorum-initial-group-size` 3, never spread one queue past 7 nodes; at-most-once dead-lettering by default, `at-least-once` requires `overflow: reject-publish`.
- Streams operations: retention triggers per segment roll (`x-stream-max-segment-size-bytes` default 500 MB, at least one segment always kept), so low-traffic streams outlive `x-max-age`; segment size must shrink for small retention targets.
- Monitoring: `rabbitmq_prometheus` plus Grafana, 30s production scrape interval; official cluster-operator alert rules with thresholds (memory > 90% of limit, FDs > 90% for 2m, any unroutable dropped message); publish rate exceeding deliver rate as the standard backlog alert heuristic; connection churn above ~100/s as a client-bug signal; never set management statistics rate mode to `detailed` in production.
- Health checks: staged model from `rabbitmq-diagnostics ping` up to `check_virtual_hosts`; keep expensive stages out of aggressive LB probes (a named cause of churn); the removed no-op checks listed as such.
- Diagnostics: updated `rabbitmqctl` command list (node_health_check removed), Management API curl examples kept, common symptoms-to-causes table extended with the 4.x incident shapes (unexpected dead-lettering after the delivery-limit default, memory alarms blocking publishers, FD exhaustion from churn storms).
- Tracing: no broker-side trace emission; OTel Collector `rabbitmq` receiver for broker metrics plus client-side `traceparent` propagation in message headers. Prose mention only, no cross-plugin reference to the opentelemetry plugin.
- One queue is bounded by roughly one CPU core; split load across queues to match cores.

`references/security.md` (facts verified against official RabbitMQ docs; the external skill served only as a gap pointer):

- Bootstrap: delete the `guest` user, `anonymous_login_user = none`, per-app users with least-privilege permissions.
- Virtual-host isolation and the permission model; topic permissions to restrict publish/consume by routing-key pattern.
- TLS: on all public listeners, client-side certificate and hostname verification, evaluate with testssl.sh.
- Secrets: keep credentials out of config files checked into VCS; environment or secret-store injection.

### 3. Explicitly out of scope

- No `/messaging:mq-audit` command (possible follow-up, not designed here).
- No Kafka/NATS/other-broker content and no broker-comparison guide.
- No client-library-specific examples.
- No new cross-plugin dependencies: the OTel mention stays prose-only, and no python/typescript plugin pointers are added.

## Repo contracts

- `marketplace.json`: messaging entry gains `"skills": ["./skills/rabbitmq-production"]`, description updated to name the 4.3 series, plugin version 1.4.2 to 2.0.0 (restructure: new skill plus rewritten agent), `metadata.version` bumped in the same commit.
- `docs/plugins/messaging.md`: rewritten to describe the agent plus skill shape; the stale "mirrored queues" expertise line goes away.
- Downstream export: load the `downstream-exports` skill during implementation; mirror the agent update and the new skill directory into `exports/vscode/messaging/`, run `check_export.py`. No agent or prompt is added, renamed, or removed, so the extension manifest should not change; verify with `gen_extension_manifest.py --check`.
- Dependency graph: no new runtime cross-plugin references, so `lint_dependency_graph.py` stays clean.
- Single commit carrying plugin files, marketplace.json, docs, and exports; then push to master. Commit message in house imperative style, tagged as a refresh per the custom-plugin-refresh protocol.

## Verification

Run the four CI checks locally before committing: `python scripts/lint_dependency_graph.py`, `python .claude/skills/downstream-exports/scripts/check_export.py`, `python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check`, `python scripts/check_version_bumps.py <base> <head>` over the commit range. Additionally grep the final content for the banned dash-aside construct and for leftover client-specific API calls in pattern examples.

## Sources

Primary: rabbitmq.com docs (production-checklist, quorum-queues, streams, reliability, alarms, monitoring, prometheus, upgrade, which-erlang, release-information, metadata-store, local-random-exchange, http-api-reference), rabbitmq-server release notes for 4.1.0/4.2.0/4.2.9/4.3.0, RabbitMQ blog (4.3 release, Khepri default, quorum-queue migration), rabbitmq/cluster-operator observability rule file, rabbitmq client-libraries pages and release pages, rabbitmq-delayed-message-exchange archive notice. Secondary (community, cross-checked): CloudAMQP best-practice series, samber/awesome-prometheus-alerts, exponential-backoff and outbox pattern write-ups. Research reports gathered 2026-08-10 by three parallel agents (authoritative/recency sweep, community best-practices sweep, marketplace comparison scan).
