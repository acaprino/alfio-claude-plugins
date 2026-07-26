# OpenTelemetry Plugin

> OpenTelemetry Python instrumentation -- distributed tracing, async context propagation, custom transport propagators (AMQP, ZMQ, gRPC), OTLP exporters, AWS ADOT/X-Ray integration, and production observability. Targets SDK v1.42.1.

## Agents

### `otel-architect`

OpenTelemetry Python instrumentation architect.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch` |
| **Use for** | Instrumenting code with OpenTelemetry, designing distributed tracing, auditing observability pipelines, configuring OTLP exporters, reviewing tracing code for correctness |

**Invocation:**
```
Use the otel-architect agent to [instrument/audit/design] [component or pipeline]
```

---

## Skills

### `opentelemetry`

Knowledge base for instrumenting Python services with OpenTelemetry -- distributed tracing, metrics, and log correlation.

| | |
|---|---|
| **Trigger** | Working with OpenTelemetry, distributed tracing, span instrumentation, context propagation, OTLP exporters, sampling strategies, or observability pipelines |

**References:**
| File | Content |
|------|---------|
| async-context-propagation.md | Context propagation across asyncio, AMQP, ZMQ, gRPC transports |
| instrumentation-patterns.md | Span hygiene, attribute budgets, semantic conventions |
| exporters-and-backends.md | OTLP exporter config, Jaeger / Tempo / Honeycomb / Datadog tradeoffs |
| aws-deployment.md | AWS X-Ray + ADOT integration, Lambda quirks |
| production-checklist.md | Pre-launch readiness gates for production OTel pipelines |

---

## Commands

### `/otel-audit`

Audit an existing OpenTelemetry Python instrumentation for correctness, performance, and production readiness. Delegates to the `otel-architect` agent with a structured 10-dimension checklist.

```
/otel-audit src/
/otel-audit src/worker/           # audit a single module
```

**Audit dimensions:**
- SDK setup (TracerProvider lifecycle, resource detectors, graceful shutdown)
- Span hygiene (context manager use, status codes, attribute budgets, semantic conventions)
- Attribute safety (no PII in spans or baggage, no None values, string truncation)
- Context propagation (propagator instances at module scope, custom transports correct)
- Async / threading (asyncio, Celery, threading boundaries)
- Exporters (OTLP port choice, BatchSpanProcessor in prod, TLS, compression)
- Sampling (parent-based ratio, tail sampling via Collector, error carve-out)
- Logs + metrics (Logs SDK stabilized in v1.26+, correct instruments per signal)
- AWS / ADOT (X-Ray ID generator + propagator, ECS / Lambda resource detectors)
- Anti-patterns (per-call propagator allocation, SimpleSpanProcessor in prod, Jaeger exporter removed in v1.22)

**Output:** Prioritized findings grouped by severity with concrete fix code per item.

---

**Related:** [python-development](python-development.md) (Python best practices) | [platform-engineering](platform-engineering.md) (infrastructure and observability patterns)
