# Messaging Plugin Deepening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the `rabbitmq-expert` agent as a lean decision-maker corrected for RabbitMQ 4.3 and add a `rabbitmq-production` skill with four reference files carrying the production numbers, patterns, upgrade paths, and security guidance from the 2026-08-10 research pass.

**Architecture:** Single plugin (`plugins/messaging/`), no new cross-plugin dependencies. The agent keeps decision frameworks and anti-patterns; deep detail lives in skill references loaded on demand. The export bundle at `exports/vscode/messaging/` is re-mirrored in the same change.

**Tech Stack:** Markdown plugin content only; stdlib Python verification scripts; git.

**Spec:** `docs/superpowers/specs/2026-08-10-messaging-plugin-deepening-design.md` (read it before starting any task).

## Global Constraints

- All content in English, terse keyword-list style with markdown headers, matching existing agents in this repo.
- **No dash-asides anywhere** (no `—`, no ` -- `, no spaced ` - ` used to wrap a parenthetical clause). List markers `- ` at line start and hyphenated compounds (`delivery-limit`) are fine. Verify each authored file with: `grep -nE '—|\S --? \S' <file>` and read every hit in context (list items and CLI flags like `--queue-pattern` are false positives; rewrite only true asides).
- **Client-neutral pseudocode only** in pattern examples. Convention used everywhere:

  ```
  publish(exchange="orders", routing_key="order.created", body, properties={delivery_mode: 2})
  queue.declare("work", durable=true, args={"x-dead-letter-exchange": "retry"})
  consume("work", prefetch=30, on_message=handler)   # manual ack inside handler
  ```

  No `pika.`, `amqplib`, `channel.basicPublish`, or any client API names in examples.
- **The precise current RabbitMQ version (4.3.4) appears in exactly one file**: `plugins/messaging/skills/rabbitmq-production/SKILL.md`. Series-level wording ("4.3") is allowed in the agent description and the marketplace description.
- **One final commit** carrying plugin files, `marketplace.json`, docs, and `exports/` together, then push to master (house marketplace workflow). Tasks 1-9 leave the tree dirty on purpose; only Task 10 commits.
- Plugin version goes 1.4.2 to **2.0.0**; `metadata.version` in `marketplace.json` gets a **minor** bump; `exports/vscode/package.json` `version` is set equal to the new `metadata.version`.
- No new cross-plugin runtime references: the OpenTelemetry mention in operations.md stays prose-only (never "load the opentelemetry skill").
- Every factual claim added must come from this plan's embedded fact lists (researched 2026-08-10, official-source tagged). Do not add facts from memory.

---

### Task 1: Rewrite the agent `plugins/messaging/agents/rabbitmq-expert.md`

**Files:**
- Modify: `plugins/messaging/agents/rabbitmq-expert.md` (full rewrite, target 260-320 lines)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: the agent references the skill by the exact name `rabbitmq-production` and the four reference filenames `versions-and-upgrades.md`, `patterns.md`, `operations.md`, `security.md` (created in Tasks 2-6). Tasks 2-6 must keep those names.

- [ ] **Step 1: Read the current agent** at `plugins/messaging/agents/rabbitmq-expert.md` (218 lines) to preserve its voice, header structure, and the content explicitly kept below.

- [ ] **Step 2: Write the new agent.** Keep the frontmatter shape exactly (`name: rabbitmq-expert`, `model: inherit`, `color: blue`, `tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch`). Description (YAML `>` form): update "RabbitMQ 4.x" to "RabbitMQ 4.3"; keep TRIGGER WHEN / DO NOT TRIGGER WHEN clauses as they are. Body sections and required content:

  **# ROLE**: keep the current one-paragraph role, append: "Load the `rabbitmq-production` skill references for production thresholds, upgrade paths, full pattern write-ups, and security hardening."

  **# KNOWLEDGE MAP** (new): four-row table naming each reference file and when to load it (versions-and-upgrades.md: upgrades, breaking changes, client/library choices; patterns.md: implementing any delivery pattern; operations.md: sizing, monitoring, diagnostics beyond first aid; security.md: hardening, TLS, multi-tenancy).

  **# CAPABILITIES**, updated per sub-section:
  - Exchange Types: keep direct/topic/fanout/headers/consistent-hash; add `local-random` (introduced in 4.0, low-latency RPC to local queues, source https://www.rabbitmq.com/docs/local-random-exchange) and `x-modulus-hash` (moved into core in 4.3, was in the sharding plugin).
  - Queue Design: classic queues are CQv2 only, non-replicated, transient non-exclusive classic queues denied by default in 4.3; **remove the lazy-queues bullet entirely** (declaring `x-queue-mode` with any value fails in 4.3); quorum queues are the production default with default `delivery-limit` 20 since 4.0, 32 strict priority levels and native delayed retries (increasing/linear backoff on requeue) in 4.3; streams and super streams kept as today plus: no TTL/priority/DLX on streams, per-consumer prefetch only.
  - Binding Patterns: keep unchanged.
  - Clustering and HA: correct the Khepri line to "opt-in through 4.1, default for NEW clusters in 4.2, the only metadata store in 4.3 (Mnesia removed)"; add "partition-handling config (`pause_minority`, `autoheal`, `pause_if_all_down`) accepted but IGNORED in 4.3; Khepri needs a node majority online"; keep federation/shovel and add "local shovels (4.2+): intra-cluster shovel protocol, cheaper than AMQP shovels".
  - Protocols: keep the five, add to AMQP 1.0: "since 4.2 messages without an explicit durable header are NON-durable" and "SQL filter expressions for stream consumers (4.2+)"; add to MQTT: "max packet size default 16 MiB since 4.1".
  - Message Properties: keep, with corrections: `delivery_mode: 2` applies to AMQP 0-9-1 (AMQP 1.0 sets the durable header explicitly); per-message TTL (`expiration`) carries the warning "expired messages are discarded only at the queue head; never use per-message TTL for retry delays"; DLX gains "dead-lettering is at-most-once by default; `dead-letter-strategy: at-least-once` requires `overflow: reject-publish`".
  - Flow Control: keep, with "global QoS (`basic.qos` global=true) denied by default in 4.3; per-consumer prefetch is the only supported form".

  **# DECISION FRAMEWORK**, updated:
  - Exchange Type Selection: keep, add "lowest-latency RPC to node-local queues -> local-random".
  - Queue Type Selection (replaces Queue Durability): decision list for classic vs quorum vs stream. Quorum by default for durable replicated work. Do NOT use quorum queues for: transient or exclusive queues, high declaration/deletion churn, lowest-possible-latency needs, workloads that never use confirms/acks, backlogs of 5M+ messages (use streams), high fan-out (use streams). Above ~5,000 quorum queues, rethink the topology. Source: https://www.rabbitmq.com/docs/quorum-queues
  - Message Persistence Tradeoffs: keep, add the AMQP 1.0 durable-header caveat.
  - Prefetch Tuning: keep the bands, replace the "global vs per-consumer" line with "global QoS is denied by default in 4.3", add the formula "prefetch ~= round-trip time / per-message processing time" for few fast consumers.
  - Priority Workloads (new): quorum queues offer 32 strict priority levels in 4.3 (higher priority delivered strictly first) and are the default recommendation; classic `x-max-priority` is legacy, cap at ~5 levels.

  **# COMMON PATTERNS**: convert every example to the pseudocode convention from Global Constraints. Keep, in compressed form (3-8 lines each): publisher confirms, consumer acknowledgment, retry via DLX (rewritten as FIXED-TTL TIER queues with per-queue `x-message-ttl`, with the explicit note "per-message TTL cannot implement backoff"), RPC (`reply_to` + `correlation_id`; mention Direct Reply-To works over AMQP 1.0 since 4.2), topic routing wildcard table (keep as-is). Drop the priority-queue setup block (now covered by the decision framework). End with "Full pattern catalog incl. outbox, idempotent consumer, claim check, reconnection: load `rabbitmq-production` reference patterns.md".

  **# ANTI-PATTERNS**: keep the existing eight with two rewrites, and add four. Rewrites: "Classic mirrored queues" becomes "removed in 4.0 (deprecated 3.13); their presence blocks any 4.x upgrade; migrate to quorum queues before upgrading"; "Unbounded queues" keeps its fix line and adds "keep queues short; a message published to an empty queue goes straight to the consumer". New entries:
  - **Delayed-message-exchange plugin** (dead): archived April 2026, unmaintained, single-node Mnesia storage (node loss = message loss; disabling the plugin loses all undelivered delayed messages), incompatible with 4.3 (Mnesia removed). Fix: fixed-TTL tier queues, 4.3 native delayed retries, or an external scheduler. Source: https://github.com/rabbitmq/rabbitmq-delayed-message-exchange
  - **Per-message TTL for retry delays**: broken by design, expired messages are only discarded at the queue head (a 5-minute-TTL message blocks a 1-second-TTL message behind it). Fix: per-queue TTL tier queues. Source: https://www.rabbitmq.com/docs/ttl
  - **One shared connection for publish and consume**: a memory alarm blocks all publishing connections cluster-wide; on a shared connection the block also stalls consumer acks and deadlocks the drain. Fix: separate connections. Source: https://www.rabbitmq.com/docs/alarms
  - **Unlimited prefetch**: one consumer buffers the whole backlog, risking client OOM and mass redelivery on crash. Fix: bounded per-consumer prefetch.

  **# DIAGNOSTICS**:
  - `rabbitmqctl` list: keep `list_queues`/`list_connections`/`list_channels`/`list_exchanges`/`list_bindings`/`cluster_status`/`environment`; **delete `node_health_check`** (no-op since 4.0).
  - Add staged health checks: `rabbitmq-diagnostics ping` (stage 1), `check_running`, `check_local_alarms`, `check_port_connectivity`, `/api/health/checks/*`; note `GET /api/aliveness-test` is a no-op since 4.1 and expensive stages must stay out of aggressive LB probes.
  - Management API curl examples: keep.
  - Common Symptoms and Causes: keep all six rows, add two: "Messages dead-lettered or dropped unexpectedly -> quorum queue default delivery-limit 20 reached (4.0+)"; "File descriptor exhaustion -> connection churn storm (rates above ~100/s indicate client bugs or LB health checks opening AMQP connections)".

  **# OUTPUT FORMAT**: keep as-is, change the last bullet to "Always specify the RabbitMQ series (4.x) compatibility for features used; current-series specifics live in the `rabbitmq-production` skill".

- [ ] **Step 3: Verify corrections landed.** Run and check expectations:

  ```bash
  grep -n "node_health_check" plugins/messaging/agents/rabbitmq-expert.md   # expect: no output
  grep -n "lazy" plugins/messaging/agents/rabbitmq-expert.md               # expect: no output
  grep -n "default in 4.1" plugins/messaging/agents/rabbitmq-expert.md     # expect: no output
  grep -cn "delivery-limit" plugins/messaging/agents/rabbitmq-expert.md    # expect: >= 1
  grep -n "delayed-message" plugins/messaging/agents/rabbitmq-expert.md    # expect: hits only in ANTI-PATTERNS
  grep -nE '—|\S --? \S' plugins/messaging/agents/rabbitmq-expert.md       # read hits; no true dash-asides
  grep -nEi 'pika|amqplib|createConfirmChannel|ch\.' plugins/messaging/agents/rabbitmq-expert.md  # expect: no output
  ```

- [ ] **Step 4: Verify size**: `wc -l plugins/messaging/agents/rabbitmq-expert.md` expected 260-320. If far outside, trim detail into the (upcoming) references rather than cutting corrections.

---

### Task 2: Create `plugins/messaging/skills/rabbitmq-production/SKILL.md`

**Files:**
- Create: `plugins/messaging/skills/rabbitmq-production/SKILL.md` (target 90-130 lines)

**Interfaces:**
- Consumes: reference filenames fixed in Task 1.
- Produces: the skill name `rabbitmq-production` used by marketplace.json (Task 8) and the export (Task 9). This file is the ONLY place stating the precise current version 4.3.4.

- [ ] **Step 1: Write SKILL.md** with this exact frontmatter shape (house style; compare `plugins/opentelemetry/skills/opentelemetry/SKILL.md`):

  ```yaml
  ---
  name: rabbitmq-production
  description: >
    Production knowledge base for RabbitMQ 4.x: version timeline and upgrade gates,
    delivery patterns in client-neutral pseudocode, production sizing and monitoring
    thresholds, and security hardening.
    TRIGGER WHEN: designing, operating, upgrading, monitoring, or securing RabbitMQ
    in production, or implementing delivery patterns (retry, outbox, idempotency, RPC).
    DO NOT TRIGGER WHEN: the broker is Kafka, NATS, Redis Streams, or another
    non-AMQP system, or the task is a quick conceptual question the rabbitmq-expert
    agent answers without production detail.
  ---
  ```

  Body sections:
  - **Current state** (the single version anchor): "Current stable series: RabbitMQ 4.3 (latest patch 4.3.4). Community support for 4.1 ended 2026-01-31, for 4.2 ended 2026-07-31; 4.3 is supported until 2026-11-30. Minimum Erlang 27.0. Source: https://www.rabbitmq.com/release-information (checked 2026-08-10)."
  - **Queue type quick table**: rows classic (CQv2, non-replicated, transient denied by default in 4.3), quorum (default for durable work; delivery-limit 20 default; 32 priorities and delayed retries in 4.3), stream (5M+ backlogs, fan-out, replay; no TTL/priority/DLX).
  - **Key thresholds quick table**: memory watermark 0.4-0.7 (default 0.6), disk free minimum 4G, file descriptors 50K+, connection churn alarm at >100/s, default max message size 16 MiB, quorum topology ceiling ~5,000 queues, Prometheus scrape 30s.
  - **Reference index**: one row per reference file with load condition (same four rows as the agent's KNOWLEDGE MAP).

- [ ] **Step 2: Verify**: dash-aside grep (as in Task 1); `grep -c "4.3.4" plugins/messaging/skills/rabbitmq-production/SKILL.md` expect exactly 1; confirm frontmatter parses as YAML (visual check that `description: >` block is indented consistently).

---

### Task 3: Create `references/versions-and-upgrades.md`

**Files:**
- Create: `plugins/messaging/skills/rabbitmq-production/references/versions-and-upgrades.md` (target 130-190 lines)

**Interfaces:**
- Consumes: filename fixed by Tasks 1-2. Must NOT restate "4.3.4" (the anchor lives in SKILL.md; this file says "the 4.3 series").
- Produces: nothing downstream.

- [ ] **Step 1: Write the file** with these sections and facts (every fact below is official-source, researched 2026-08-10; keep the URLs inline as sources):

  **Series timeline** (source https://www.rabbitmq.com/release-information): 4.0 GA Aug 2024; 4.1.0 on 2025-04-15, community EOL 2026-01-31; 4.2.0 on 2025-10-28, community EOL 2026-07-31; 4.3.0 on 2026-04-23, community-supported until 2026-11-30; extended commercial support runs later per series.

  **What each series added.**
  - 4.1 (https://www.rabbitmq.com/blog/2025/04/15/rabbitmq-4.1.0-is-released): quorum-queue log reads offloaded to channels/sessions (better consumer throughput); initial AMQP 1.0 filter expressions on streams (`properties` / `application-properties`); `rabbitmqadmin` v2; required feature flags auto-enable at node boot; AMQP 0-9-1 initial max frame 4096 to 8192 bytes; MQTT Maximum Packet Size default 256 MiB to 16 MiB.
  - 4.2 (https://github.com/rabbitmq/rabbitmq-server/blob/main/release-notes/4.2.0.md): Khepri default metadata store for NEW deployments; AMQP 1.0 SQL filter expressions for stream consumers (comparison/logical/arithmetic, `LIKE`, `IN`, `IS NULL`; superset of the 4.1 property filters); Direct Reply-To for AMQP 1.0 (cross-protocol); incoming and outgoing broker message interceptors (built-ins: timestamping, MQTT client ID injection); local shovels (intra-cluster protocol, higher throughput than AMQP shovels); new `rabbitmqctl` commands for blue-green migration and message-size distribution analysis. 4.2.9: minimum Erlang raised to 27.0; super stream partitions capped at 1,000 by default (https://github.com/rabbitmq/rabbitmq-server/blob/main/release-notes/4.2.9.md).
  - 4.3 (https://github.com/rabbitmq/rabbitmq-server/blob/main/release-notes/4.3.0.md and https://www.rabbitmq.com/blog/2026/04/23/rabbitmq-4.3-release): Khepri is the only metadata store, Mnesia removed entirely; quorum queues gain 32 strict priority levels (strictly higher first, per-priority message counts, priority-aware expiration), native delayed retries (increasing or linear backoff on requeue, per-message override via AMQP 1.0 `x-opt-delivery-time` annotation), and an `acquired-count` split from `delivery-count` so client-initiated requeues no longer count toward the poison delivery limit; consumer timeout handling moved into quorum queues with graceful AMQP 1.0 `released` disposition (classic queues and streams never evaluate consumer timeouts); per-message memory overhead halved for messages up to 32 KiB; recovery snapshots for faster startup; Ra upgraded to 3.x; `x-modulus-hash` exchange moved into core.

  **Breaking changes and denials, by series.**
  - Since 4.0: classic mirrored queues removed (migrate to quorum BEFORE upgrading; blue-green recommended for complex topologies, https://www.rabbitmq.com/docs/3.13/migrate-mcq-to-qq); quorum `delivery-limit` defaults to 20 (dropped or dead-lettered after 20 failed deliveries; `x-delivery-limit: -1` restores old behavior but is not recommended; configure DLX on all quorum queues); `max_message_size` default 16 MiB (was 128 MiB in 3.x), hard server cap 512 MiB; `rabbitmq-diagnostics node_health_check` is a no-op.
  - Since 4.1: `GET /api/aliveness-test` is a no-op; replacements are targeted `rabbitmq-diagnostics` checks (`check_running`, `check_local_alarms`, `check_port_connectivity`) and granular `/api/health/checks/*` endpoints (https://www.rabbitmq.com/docs/http-api-reference).
  - Since 4.2: AMQP 1.0 messages without an explicit durable header default to NON-durable (spec compliance; silent change for publishers); `rabbitmq_raft`-prefixed Prometheus metrics renamed and restructured (update Grafana dashboards); ineffective `*.cacerts` settings removed.
  - In 4.3: upgrade accepted only from 4.2.x, with six feature flags enabled first (`rabbitmq_4.2.0`, `rabbitmq_4.1.0`, `rabbitmq_4.0.0`, `khepri_db`, `quorum_queue_non_voters`, `message_containers_deaths_v2`); general rule: enable all stable feature flags before any major-series upgrade (https://www.rabbitmq.com/docs/upgrade). CQv1 removed: declaring `x-queue-mode` (any value) or `x-queue-version: 1` fails. Transient non-durable non-exclusive classic queues denied by default (escape hatch `deprecated_features.permit.transient_nonexcl_queues = true` on all nodes before upgrading). Global QoS (`basic.qos` with `global=true`) denied by default. Partition-handling keys (`pause_minority`, `autoheal`, `pause_if_all_down`) accepted but IGNORED; Khepri majority semantics apply. `rabbitmqadmin` v1 HTTP endpoint removed.
  - Deprecated ecosystem: the `rabbitmq-delayed-message-exchange` plugin was archived April 2026 and is incompatible with 4.3 (Mnesia removal); a "message scheduler" replacement exists only in commercial Tanzu RabbitMQ.

  **Erlang/OTP baseline** (https://www.rabbitmq.com/docs/which-erlang): 4.3 requires 27.0 minimum; 27.x fully supported; 28.x supported for brand-new clusters only (known rolling-upgrade issue moving Khepri clusters from 27 to 28); 29 unsupported.

  **Client ecosystem** (https://www.rabbitmq.com/client-libraries/amqp-client-libraries): new official "RabbitMQ AMQP 1.0 clients" family designed for 4.x with topology management and connection/topology recovery: Java `rabbitmq-amqp-java-client` (Java 11+, 21 recommended), .NET `rabbitmq-amqp-dotnet-client`, Go `rabbitmq-amqp-go-client`, Python `rabbitmq-amqp-python-client` (1.0.0 GA 2026-07-20, Python 3.10-3.14). AMQP 0-9-1 clients: Java `com.rabbitmq:amqp-client` 5.34.x maintenance line; .NET client v7 (fully async, `IModel` renamed `IChannel`, `CreateBasicProperties()` removed, migration guide https://github.com/rabbitmq/rabbitmq-dotnet-client/blob/main/v7-MIGRATION.md); pika 1.4.x (still AMQP 0-9-1 only); amqplib for Node is 2.x requiring Node 18+ (`^0.10` pins are stale).

  **Kubernetes cluster operator** (https://github.com/rabbitmq/cluster-operator/releases and https://www.rabbitmq.com/kubernetes/operator/install-operator): v2.22 line current (v2.22.3, Jul 2026); v2.22.0 switched the startup probe to HTTP, requiring RabbitMQ 4.2.4+ or 4.3.0+ (older images need annotation `rabbitmq.com/legacy-startup-probe: "true"`, unsupported); cert-manager required since operator 2.20; default deployed image 4.2.6+ since v2.21; tested on Kubernetes 1.29-1.32; operator upgrades trigger rolling restarts, pause reconciliation first.

- [ ] **Step 2: Verify**: dash-aside grep; `grep -c "4.3.4" <file>` expect 0; `grep -c "khepri_db" <file>` expect >= 1.

---

### Task 4: Create `references/patterns.md`

**Files:**
- Create: `plugins/messaging/skills/rabbitmq-production/references/patterns.md` (target 200-280 lines)

**Interfaces:**
- Consumes: pseudocode convention from Global Constraints; filename fixed by Tasks 1-2.
- Produces: nothing downstream.

- [ ] **Step 1: Write the file.** One `##` section per pattern. Every pattern gets: when to use (1-2 lines), pseudocode block, failure modes / caveats bullets, source URL. Patterns and their required facts:

  1. **Publisher confirms**: synchronous (await per publish or batch, simple, slower) vs asynchronous (confirm callback tracking outstanding ids, fast, complex); rule: after a connection or channel failure, retransmit everything unconfirmed and accept the duplicates (idempotent consumer downstream); use the `mandatory` flag or an alternate exchange to catch unroutable messages, and alert on the unroutable-dropped counter. Source: https://www.rabbitmq.com/docs/reliability
  2. **Consumer acknowledgment**: manual ack after processing completes; nack without requeue routes to DLX; on quorum queues the default `delivery-limit` of 20 plus a DLX gives poison-message quarantine for free, so alert on DLX queue depth instead of building custom quarantine. In 4.3 client-initiated requeues no longer consume the delivery limit (acquired-count split). Source: https://www.rabbitmq.com/docs/quorum-queues
  3. **Retry with exponential backoff (TTL tier queues)**: fixed tiers (example: `retry.5s`, `retry.30s`, `retry.5m`), each declared with per-QUEUE `x-message-ttl` and a DLX pointing back at the work exchange; attempt count read from `x-death`; after max attempts route to a parking queue. State explicitly why per-message TTL cannot work (head-of-queue discard: a long-TTL message blocks shorter-TTL messages behind it, https://www.rabbitmq.com/docs/ttl). Note: RabbitMQ 4.3 quorum queues have native delayed retries (increasing/linear backoff on requeue) that replace many hand-built tiers. Never use the delayed-message-exchange plugin (archived April 2026, single-node Mnesia storage, dead on 4.3).
  4. **Idempotent consumer**: exactly-once delivery is impossible; official guidance is idempotent processing rather than explicit deduplication; if dedup is expensive, only dedup messages carrying the `redelivered` flag. Dedup key: business id or message id persisted with the side effect. Source: https://www.rabbitmq.com/docs/reliability
  5. **Transactional outbox**: business change and outgoing message written in ONE database transaction; a relay reads the outbox and publishes with confirms; delivery remains at-least-once, so pattern 4 stays mandatory; costs are relay polling latency and load.
  6. **Claim check**: payloads beyond the KB range go to object storage or a DB, the message carries the reference; pairs with the 16 MiB default `max_message_size` (hard cap 512 MiB); set `content_type` accordingly.
  7. **RPC**: request published with `reply_to` (exclusive auto-delete callback queue) and `correlation_id`; server replies to `reply_to` echoing `correlation_id`; Direct Reply-To avoids the queue round-trip and works for AMQP 1.0 cross-protocol since 4.2; `local-random` exchange (4.0+) for lowest-latency RPC to node-local queues.
  8. **Connection management**: one long-lived connection per process; SEPARATE connections for publishing and consuming (memory alarms block all publishing connections cluster-wide; on a shared connection the block stalls consumer acks and deadlocks draining, https://www.rabbitmq.com/docs/alarms); one channel per thread, never shared; reconnect loop with exponential backoff and jitter (pseudocode: retry sleep `base * 2^attempt` capped, reset on success); optional connection pool sketch for high-churn publishers; heartbeats: do not set below ~5s (false positives), and without heartbeats a dead TCP peer takes ~11 minutes to detect on default Linux (https://www.rabbitmq.com/docs/reliability). Each connection costs ~100 KB broker RAM, more with TLS; connection churn above ~100/s is a client bug signal (https://www.rabbitmq.com/docs/connections).
  9. **Streams**: single active consumer with offset resume on takeover (the classic bug: the new active consumer restarts from the beginning instead of the stored offset; resume via the consumer-update callback); store offsets every few thousand messages, never per message (offset writes persist into the stream and grow disk); Bloom-filter stream filtering (3.13+) is probabilistic, clients MUST re-check filter values client-side; SAC per partition plus super streams gives ordered processing with scale-out; streams have no TTL, no priority, no DLX; per-consumer prefetch only. Sources: https://www.rabbitmq.com/docs/streams and https://www.rabbitmq.com/blog/2021/09/13/rabbitmq-streams-offset-tracking
  10. **Topic routing**: keep the wildcard table from the old agent (`logs.*`, `logs.#`, `*.error`, `#`) with one pseudocode binding example.

- [ ] **Step 2: Verify**: dash-aside grep; client-API grep from Task 1 Step 3 (expect no output); `grep -c '^## ' <file>` expect 10.

---

### Task 5: Create `references/operations.md`

**Files:**
- Create: `plugins/messaging/skills/rabbitmq-production/references/operations.md` (target 170-230 lines)

**Interfaces:**
- Consumes: filename fixed by Tasks 1-2.
- Produces: nothing downstream.

- [ ] **Step 1: Write the file** with these sections and facts (sources inline):

  **Production checklist numbers** (https://www.rabbitmq.com/docs/production-checklist):
  - `vm_memory_high_watermark.relative`: default 0.6, sane range 0.4-0.7, above 0.7 with care, keep 256+ MiB always available.
  - `disk_free_limit.absolute`: default 50MB is development-only; production minimum 4G, at least matching the RAM watermark; when in doubt overprovision.
  - File descriptors: 50K+ for production, up to 500K reasonable; sizing formula: 95th-percentile concurrent connections x 2 + total queue count.
  - Hardware floor: 4 CPU cores, 4+ GiB RAM, durable local SSD/NVMe (never NAS); do not colocate with I/O-heavy services; Khepri, quorum queues, and streams all assume durable storage.
  - Network sizing: message rate x message size x 110% x 8 bits (worked example: 20K msg/s at 6 KB needs ~1.056 Gbit/s).
  - One queue is bounded by roughly one CPU core: split load across queues to match cores. Never set management statistics rate mode to `detailed` in production (https://www.cloudamqp.com/blog/part4-rabbitmq-13-common-errors.html, community).

  **Cluster sizing and Khepri**: minimum 3 nodes, always odd (3/5/7); under Khepri (only store in 4.3) a node MAJORITY must be online for the cluster to be available, and legacy partition-handling strategies are ignored; security bootstrap items live in security.md.

  **Quorum queue operations** (https://www.rabbitmq.com/docs/quorum-queues):
  - WAL: `raft.wal_max_size_bytes` default 512 MiB; node memory at least 3x the WAL limit, 4x for high throughput.
  - Per-message in-memory index cost ~32 bytes regardless of body size (~1 MB per 30,000 queued messages): long backlogs eat memory, move 5M+ backlogs to streams.
  - Leaders pile onto surviving nodes after rolling restarts: `rabbitmq-queues rebalance quorum` (supports `--queue-pattern`).
  - Membership never changes automatically: `grow` / `shrink` / `add_member` / `delete_member` when resizing; `x-quorum-initial-group-size` default 3; never spread one queue past 7 nodes.
  - Dead-lettering is at-most-once by default; `dead-letter-strategy: at-least-once` requires `overflow: reject-publish` and costs memory/CPU.
  - Topology ceiling: above ~5,000 quorum queues, reconsider (classic or streams may fit better).

  **Streams operations** (https://www.rabbitmq.com/docs/streams): retention triggers only when a segment rolls; `x-stream-max-segment-size-bytes` default 500,000,000 bytes and at least one segment is always kept, so low-traffic streams hold data past `x-max-age` (format like `7D`); small retention targets need smaller segments; streams need fast disks but use less CPU/memory than quorum queues.

  **Monitoring** (https://www.rabbitmq.com/docs/prometheus and https://www.rabbitmq.com/docs/monitoring):
  - Stack: `rabbitmq_prometheus` plugin + Grafana; production scrape interval 30s (30-60s range; the exporter is designed for 15-30s).
  - Watch: node memory used vs limit, FDs used vs total, Erlang processes; cluster totals for connections/channels/queues/consumers; per-queue ready vs unacked and publish vs deliver rates; connection open/close churn rates.
  - Official cluster-operator alert rules (https://github.com/rabbitmq/cluster-operator/blob/main/observability/prometheus/rule-file.yml): memory `rabbitmq_process_resident_memory_bytes / rabbitmq_resident_memory_limit_bytes * 100 > 90`; file descriptors `rabbitmq_process_open_fds / rabbitmq_process_max_fds * 100 > 90` for 2m; unroutable drops `increase(rabbitmq_channel_messages_unroutable_dropped_total[5m]) >= 1` (catches missing bindings).
  - Standard heuristics (community, https://samber.github.io/awesome-prometheus-alerts/rules/message-brokers/rabbitmq/): sustained queue depth over threshold; publish rate exceeding deliver rate for a sustained window; connection churn above ~100/s.

  **Health checks**: staged model from cheap to expensive: `rabbitmq-diagnostics ping`, then `check_running`, `check_local_alarms`, `check_port_connectivity`, up to `check_virtual_hosts`; higher stages have more false positives, keep them out of aggressive LB probes (LB TCP health checks are a named churn cause); `node_health_check` is a no-op since 4.0 and `GET /api/aliveness-test` since 4.1; granular endpoints under `/api/health/checks/*`.

  **Diagnostics first aid**: the `rabbitmqctl` inventory commands and Management API curl examples (mirror the agent's DIAGNOSTICS section), plus the extended symptoms table: stuck messages (consumers down, prefetch exhausted, unacked accumulation), high memory (unbounded queues, quorum backlog index cost, connection count), publish-rate drops (memory/disk alarm, flow control), consumer lag (slow consumer, low prefetch, one queue per core bound), unexpected dead-lettering (delivery-limit 20 default), FD exhaustion (churn storm), partition symptoms under Khepri (minority side unavailable).

  **Tracing**: the broker emits no traces; pattern is OTel Collector `rabbitmq` receiver for broker metrics plus client-side instrumentation propagating `traceparent` in message headers for end-to-end delay attribution (consumer code vs broker delivery). Prose only, no skill loads.

- [ ] **Step 2: Verify**: dash-aside grep; `grep -c "node_health_check" <file>` expect exactly 1 (the no-op warning); `grep -c "> 90" <file>` expect 2.

---

### Task 6: Create `references/security.md`

**Files:**
- Create: `plugins/messaging/skills/rabbitmq-production/references/security.md` (target 80-120 lines)

**Interfaces:**
- Consumes: filename fixed by Tasks 1-2.
- Produces: nothing downstream.

- [ ] **Step 1: Write the file.** Facts (verify wording against https://www.rabbitmq.com/docs/production-checklist and https://www.rabbitmq.com/docs/access-control while writing; the external skill that pointed at this gap is NOT a source):

  - **Bootstrap hardening**: delete the default `guest` user (it can only connect from localhost anyway, remove it outright); set `anonymous_login_user = none`; create one least-privilege user per application; never reuse credentials across apps.
  - **Virtual hosts**: one vhost per application or environment for isolation; permissions are granted per vhost as three regexes (configure / write / read) via `rabbitmqctl set_permissions -p <vhost> <user> <conf> <write> <read>`; pseudo-example rows for a publisher-only and a consumer-only user.
  - **Topic permissions**: restrict publish/consume by routing-key pattern on topic exchanges via `rabbitmqctl set_topic_permissions`; use for multi-tenant topic exchanges.
  - **TLS**: enable on all listeners crossing a public or shared network; client side must verify the server certificate AND hostname; evaluate the deployed config with testssl.sh; disable plain AMQP listener where TLS is mandated.
  - **Secrets**: credentials never in files tracked by VCS; inject via environment or a secret store (Kubernetes `Secret`, Vault); rotate on compromise; the management UI and API share the same credentials, so scope monitoring users with the `monitoring` tag instead of `administrator`.

- [ ] **Step 2: Verify**: dash-aside grep; `grep -c "set_topic_permissions" <file>` expect >= 1.

---

### Task 7: Update `docs/plugins/messaging.md`

**Files:**
- Modify: `docs/plugins/messaging.md` (full rewrite of the 33-line file)

**Interfaces:**
- Consumes: final agent and skill shapes from Tasks 1-6.
- Produces: nothing downstream.

- [ ] **Step 1: Rewrite the doc**: keep the header blockquote style; document the `rabbitmq-expert` agent (updated expertise list: exchange types, queue-type selection incl. quorum/streams, clustering with Khepri, protocols, diagnostics; the "mirrored queues" line goes away) and add a `## Skills` section for `rabbitmq-production` with its four references and one-line load conditions. Keep the `**Related:**` footer line pointing at python-development. State "RabbitMQ 4.3 series" once, without the patch version.

- [ ] **Step 2: Verify**: `grep -n "mirrored" docs/plugins/messaging.md` expect no output; dash-aside grep.

---

### Task 8: Update `.claude-plugin/marketplace.json`

**Files:**
- Modify: `.claude-plugin/marketplace.json` (messaging entry around line 313, and `metadata.version`)

**Interfaces:**
- Consumes: skill directory from Task 2.
- Produces: the new `metadata.version` value that Task 9 copies into `exports/vscode/package.json`.

- [ ] **Step 1: Edit the messaging entry**: set `"version": "2.0.0"`; replace the description with:

  ```
  RabbitMQ and AMQP messaging - queue configuration, exchange routing, clustering, high availability, and event-driven architecture optimization (RabbitMQ 4.3 coverage: Khepri-only metadata store, quorum queue priorities and delayed retries, streams, MQTT 5, AMQP 1.0 SQL filters) plus a production knowledge base skill
  ```

  and add after the `"agents"` array:

  ```json
  "skills": [
    "./skills/rabbitmq-production"
  ]
  ```

- [ ] **Step 2: Bump `metadata.version`** (top of the file): read the current value and increment the MINOR component (e.g. `18.3.x` becomes `18.4.0`). Record the new value for Task 9.

- [ ] **Step 3: Verify**: `python -c "import json; json.load(open('.claude-plugin/marketplace.json', encoding='utf-8'))"` expect silence; `python scripts/lint_dependency_graph.py` expect exit 0.

---

### Task 9: Mirror into `exports/vscode/messaging/`

**Files:**
- Modify: `exports/vscode/messaging/.github/agents/rabbitmq-expert.agent.md`
- Create: `exports/vscode/messaging/.github/skills/rabbitmq-production/SKILL.md`
- Create: `exports/vscode/messaging/.github/skills/rabbitmq-production/references/` (copy of all four reference files)
- Modify: `exports/vscode/package.json` (version only)

**Interfaces:**
- Consumes: all files from Tasks 1-6; the new `metadata.version` from Task 8.
- Produces: nothing downstream.

- [ ] **Step 1: Re-mirror the agent.** Replace the body of `exports/vscode/messaging/.github/agents/rabbitmq-expert.agent.md` with the new agent body from Task 1, keeping: the existing VS Code frontmatter block (update only the description text: "4.x" to "4.3", and convert `TRIGGER WHEN: x` to `Use when x`, `DO NOT TRIGGER WHEN: y` to `Not for y` with correct grammar) and the `<!-- Vendored from ... -->` attribution comment. In the body, references to loading "the `rabbitmq-production` skill" stay as-is (skills are copied to `~/.copilot/skills/`, the name resolves).

- [ ] **Step 2: Mirror the skill.** Copy `plugins/messaging/skills/rabbitmq-production/` to `exports/vscode/messaging/.github/skills/rabbitmq-production/`. The four `references/*.md` are byte-copies (they name no Claude Code tool or agent). Adapt ONLY `SKILL.md` frontmatter to the house export shape (compare `exports/vscode/opentelemetry/.github/skills/opentelemetry/SKILL.md`): convert TRIGGER WHEN/DO NOT TRIGGER WHEN to `Use when ... Not for ...` prose inside the description, then add:

  ```yaml
  user-invocable: true
  license: MIT
  metadata:
    author: Alfio Caprino
    source: acaprino/claude-code-daodan
    upstream-plugin: messaging
  ```

- [ ] **Step 3: Bump `exports/vscode/package.json` `version`** to the exact new `metadata.version` from Task 8 (the extension re-copies skills when this changes; without the bump the new skill never reaches `~/.copilot/skills/`).

- [ ] **Step 4: Verify the export**:

  ```bash
  python .claude/skills/downstream-exports/scripts/check_export.py                     # expect exit 0
  python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check   # expect exit 0 (no agent/prompt added or renamed)
  grep -rn "TRIGGER WHEN" exports/vscode/messaging/                                    # expect no output
  grep -rn "Not for the task is" exports/vscode/messaging/                             # expect no output (grammar trap)
  ```

---

### Task 10: Final verification, single commit, push

**Files:**
- No new files; commits everything from Tasks 1-9.

**Interfaces:**
- Consumes: all prior tasks complete, working tree contains only the intended changes.

- [ ] **Step 1: Full verification sweep** from the repo root:

  ```bash
  python scripts/lint_dependency_graph.py
  python .claude/skills/downstream-exports/scripts/check_export.py
  python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
  grep -rnE '—' plugins/messaging/ docs/plugins/messaging.md   # expect no output
  git status --short                                            # expect ONLY the files named in Tasks 1-9
  ```

- [ ] **Step 2: Version-bump check over the pending change**: `git stash` is NOT needed; instead run `python scripts/check_version_bumps.py HEAD` after committing in Step 3 (the script takes a base rev; `HEAD~1` after the commit). If it fails, fix versions and amend nothing: make a follow-up edit and include it before pushing.

- [ ] **Step 3: Commit everything in one commit**:

  ```bash
  git add plugins/messaging .claude-plugin/marketplace.json docs/plugins/messaging.md exports/vscode
  git commit -m "Deepen messaging for RabbitMQ 4.3: rewrite rabbitmq-expert, add the rabbitmq-production skill (messaging 2.0.0)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

- [ ] **Step 4: Run the range check**: `python scripts/check_version_bumps.py HEAD~1 HEAD` expect exit 0.

- [ ] **Step 5: Push**: `git push` and confirm the consistency CI passes on `master` (check `gh run list --limit 1` after a minute if `gh` is available; otherwise report the push and note CI is pending).

---

## Self-Review Notes

- Spec coverage: agent rewrite (Task 1), SKILL.md and four references (Tasks 2-6), docs (Task 7), marketplace contracts (Task 8), export mirror (Task 9), verification and single-commit rule (Task 10). Out-of-scope items from the spec (mq-audit command, other brokers, client-specific examples) have no tasks, correctly.
- The version anchor rule is enforced twice: Task 2 Step 2 (`4.3.4` exactly once in SKILL.md) and Task 3 Step 2 (`4.3.4` absent from versions-and-upgrades.md).
- All facts embedded here were researched 2026-08-10 from official sources; implementers must not supplement from memory.
