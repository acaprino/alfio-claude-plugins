---
name: rabbitmq-production
description: >
  Knowledge base for running the broker under real load, split into references loaded on demand.
  Use when designing, operating, upgrading, monitoring, or securing RabbitMQ in production, or
  implementing delivery patterns (retry, outbox, idempotency, RPC). Not for a quick conceptual
  question the rabbitmq-expert agent answers without production detail.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: messaging
---

# RabbitMQ Production

Index for running RabbitMQ 4.x in production: version and upgrade gates, delivery patterns, sizing and monitoring thresholds, security hardening. References hold the full write-ups; canonical reference lives at https://www.rabbitmq.com/docs.

## Scope

The `rabbitmq-expert` agent covers exchange types, queue topology design, clustering and HA, protocols, and first-aid diagnostics inline. This skill supplies what the agent defers here: version-specific upgrade gates, sizing and monitoring thresholds, full delivery-pattern write-ups, and security hardening. Load the matching reference below instead of reasoning from general RabbitMQ knowledge; defaults and limits change materially between minor versions.

## When to use

- Planning or executing a RabbitMQ upgrade across major or minor versions
- Choosing a queue type for a new workload (classic, quorum, stream)
- Implementing a delivery pattern (retry, outbox, idempotency, RPC)
- Sizing a cluster or setting monitoring thresholds and alarms
- Hardening a broker for TLS or multi-tenancy
- Diagnosing an operational incident beyond first-aid `rabbitmqctl` checks

## How to use this skill

The quick tables below are for fast checks during a conversation. For anything version-sensitive or that changes broker behavior (an upgrade, a sizing decision, a security control, a delivery pattern implementation), load the matching reference file first rather than relying on the quick table alone. The quick tables summarize; the references are the source of truth within this skill.

## Current state

Current stable series: RabbitMQ 4.3 (latest patch 4.3.4). Community support for 4.1 ended 2026-01-31, for 4.2 ended 2026-07-31; 4.3 is supported until 2026-11-30. Minimum Erlang 27.0. Source: https://www.rabbitmq.com/release-information (checked 2026-08-10).

Full timeline, breaking changes per version, and client/library compatibility: load `versions-and-upgrades.md`.

## Queue type quick table

| Queue type | Notes |
|---|---|
| classic | CQv2, non-replicated; transient denied by default in 4.3 |
| quorum | default for durable work; delivery-limit 20 default; 32 priorities and delayed retries in 4.3 |
| stream | 5M+ backlogs, fan-out, replay; no TTL, no priority, no DLX |

Topology ceilings and per-type operational limits: load `operations.md`. The queue-type decision list lives in the `rabbitmq-expert` agent.

## Key thresholds quick table

| Threshold | Value |
|---|---|
| Memory watermark | 0.4 to 0.7 (default 0.6) |
| Disk free minimum | 4 GB |
| File descriptors | 50K+ |
| Connection churn alarm | above 100 connections/s |
| Default max message size | 16 MiB |
| Quorum topology ceiling | roughly 5,000 queues per cluster |
| Prometheus scrape interval | 30s |

Full sizing methodology, alarm wiring, and diagnostic playbooks: load `operations.md`.

## Delivery patterns (client-neutral)

Retry, outbox, idempotency, and RPC patterns are written in client-neutral pseudocode so they apply across AMQP client libraries. Load `patterns.md` before implementing any of them.

- Do not implement retry, outbox, idempotency, or RPC from general AMQP knowledge alone; load `patterns.md` first
- The pattern snippets in the `rabbitmq-expert` agent are quick illustrations, not the full write-up

## Reference index

| Reference | Load when |
|---|---|
| `versions-and-upgrades.md` | upgrades, breaking changes, client/library choices |
| `patterns.md` | implementing any delivery pattern |
| `operations.md` | sizing, monitoring, diagnostics beyond first aid |
| `security.md` | hardening, TLS, multi-tenancy |
