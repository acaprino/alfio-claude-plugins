# OpenTelemetry Plugin Design

**Date:** 2026-03-27
**Status:** Draft
**Plugin name:** `opentelemetry`

## Overview

A new ACP plugin providing an expert agent and knowledge base skill for OpenTelemetry Python instrumentation. The plugin targets developers building distributed systems with async Python, custom transport propagation (AMQP, ZMQ), and AWS deployment (ADOT, X-Ray, ECS).

The design is informed by two sources:
1. A comprehensive OTel Python advanced guide (SDK v1.40.0 / 0.61b0, March 2026)
2. Real-world architecture from the Jupiter distributed trading system (Windows + AWS ECS, custom AMQP/ZMQ propagators, Rust interop)

## Plugin Structure

```
plugins/opentelemetry/
  agents/
    otel-architect.md
  skills/
    opentelemetry/
      SKILL.md
      references/
        async-context-propagation.md
        instrumentation-patterns.md
        exporters-and-backends.md
        aws-deployment.md
        production-checklist.md
```

**Components:** 1 agent, 1 skill (with 5 reference files), 0 commands.

## Agent: `otel-architect`

### Frontmatter

```yaml
name: otel-architect
description: >
  Expert in OpenTelemetry Python instrumentation, distributed tracing
  architecture, and observability pipelines. Instruments code with spans
  and propagators, audits existing OTel setups, designs context propagation
  for custom transports (AMQP, ZMQ, gRPC), configures exporters and
  Collectors, and reviews OTel code for anti-patterns.
  TRIGGER WHEN: instrumenting code with OpenTelemetry, designing distributed
  tracing, auditing observability pipelines, configuring OTLP exporters,
  or reviewing tracing code for correctness.
  DO NOT TRIGGER WHEN: general logging, application monitoring unrelated
  to OTel, or infrastructure provisioning.
tools: Read, Write, Edit, Bash, Glob, Grep
model: opus
color: cyan
```

### Capabilities

The agent covers 5 core capabilities:

1. **Instrument code** - Add spans, propagators, and metrics to existing code. Identifies trace boundaries (HTTP entry, message consumption, task dispatch), adds spans following existing naming conventions, and wires propagation at every transport boundary.

2. **Audit existing instrumentation** - Find gaps in OTel setups. Checks all TracerProvider initializations, verifies context propagation at every thread/process boundary, validates shutdown handlers exist, checks sampling consistency across services, scans for PII in span attributes.

3. **Design propagation for custom transports** - Create inject/extract implementations for non-HTTP messaging (AMQP payload keys, ZMQ event data, custom message formats). Uses TextMapPropagator interface with W3C TraceContext format.

4. **Configure exporters and Collector** - Generate OTLP gRPC/HTTP exporter configs, ADOT Collector pipelines, X-Ray integration, ECS sidecar task definitions, Lambda layer configurations. Includes BatchSpanProcessor tuning for specific throughput requirements.

5. **Review OTel code** - Catch anti-patterns: SimpleSpanProcessor in production, OTel init before fork() in prefork workers, spans in hot loops, None values in attributes, missing shutdown handlers, inconsistent sampling across services.

### Agent Body Structure (~350-400 lines)

The agent body follows the terse keyword-list style used across the marketplace:

```
# ROLE
OpenTelemetry Python instrumentation architect. SDK v1.40.0 / 0.61b0.

# CAPABILITIES
(bullet list of the 5 capabilities above)

# CORE KNOWLEDGE
Condensed rules covering:
- Context propagation mechanics (asyncio.create_task copies contextvars at creation time, run_in_executor does NOT propagate, Python 3.12+ to_thread does)
- BatchSpanProcessor always, never SimpleSpanProcessor in production
- ParentBased sampling across all services
- Celery: init AFTER fork via worker_process_init
- SQLAlchemy async: pass .sync_engine to instrumentor
- Error handling: record_exception for unexpected, add_event for business errors
- Never PII in attributes or baggage
- W3C TraceContext as default propagation format

# APPROACH
Structured methodology for each capability:
- Instrumenting: read target -> identify boundaries -> add spans -> wire propagation -> verify parent-child
- Auditing: find inits -> check boundaries -> verify shutdown -> check sampling -> scan PII -> report
- Designing propagation: understand transport -> implement inject/extract -> use W3C format -> add fallback
- Configuring: determine protocol (gRPC vs HTTP) -> set BatchSpanProcessor params -> configure Collector pipeline
- Reviewing: check against anti-pattern list -> verify operational checklist -> report with severity

# ANTI-PATTERNS
Always-flag list:
- SimpleSpanProcessor in non-debug code
- OTel init before fork() in prefork workers
- Spans in hot loops without sampling guard
- None values in span attributes
- Missing provider.shutdown() in lifespan/atexit
- Mixing ParentBased and non-ParentBased across services
- Skipping the Collector in production
- PII or secrets in span attributes or baggage

# CONSTRAINTS
- Target Python 3.9-3.14, SDK v1.40.0
- Prefer auto-instrumentation for infrastructure, manual for business logic
- Never skip the Collector in production
- Check span.is_recording() before expensive attribute computation
```

## Skill: `opentelemetry`

### SKILL.md (~200 lines)

The main skill file serves as the core knowledge base loaded when OTel work is detected. It contains actionable patterns and decision trees, with pointers to reference files for deep dives.

**Frontmatter:**
```yaml
name: opentelemetry
description: >
  OpenTelemetry Python instrumentation knowledge base covering distributed tracing,
  async context propagation, custom transport propagators, sampling strategies,
  exporter configuration, and production observability patterns. SDK v1.40.0 target.
  TRIGGER WHEN: working with OpenTelemetry, distributed tracing, span instrumentation,
  context propagation, OTLP exporters, sampling strategies, or observability pipelines.
  DO NOT TRIGGER WHEN: general logging without trace correlation, or application
  monitoring tools unrelated to OTel.
```

**Content sections:**

1. **OTel Python Architecture Overview** - TracerProvider, SpanProcessor, Exporter pipeline. How context flows through contextvars. Relationship between API and SDK packages.

2. **Auto vs Manual Instrumentation** - Decision matrix: auto for infrastructure (HTTP, DB, cache), manual for business logic. How to combine both. Environment variables for control.

3. **Framework Patterns** - FastAPI (ASGI lifecycle, lifespan shutdown, request hooks), Celery (prefork init, producer/consumer instrumentation, signal-based context injection), SQLAlchemy async (.sync_engine pattern).

4. **Custom Transport Propagation** - Rules for implementing inject/extract on non-HTTP transports. TextMapPropagator interface. Carrier design (dict-based, case-insensitive). W3C TraceContext format. Examples for AMQP payload and ZMQ event patterns.

5. **Sampling Decision Tree** - When to use head-based vs tail-based vs hybrid. ParentBased importance. Custom priority samplers. Environment variable configuration.

6. **Three Pillars Correlation** - Log-trace correlation via otelTraceID/otelSpanID injection. Structured JSON logging with trace context. Metrics integration.

7. **Error Handling** - record_exception vs add_event. Status transitions (UNSET -> OK/ERROR). HTTP status code mapping. Business errors vs system errors.

8. **References Index** - Pointers to each reference file with brief description of when to consult it.

### Reference Files

Each reference file is a focused deep dive (~200-400 lines) that the agent loads on demand.

#### `async-context-propagation.md`
- How contextvars works with asyncio (immutable snapshots, shallow copy at create_task)
- The thread boundary trap (run_in_executor does NOT propagate)
- TracedThreadPoolExecutor pattern
- Python 3.12+ asyncio.to_thread automatic propagation
- asyncio.TaskGroup context behavior
- opentelemetry-instrumentation-threading auto-patching

#### `instrumentation-patterns.md`
- @traced / @traced_async decorator patterns with extract_args
- TracedClass mixin using __init_subclass__
- Sensitive argument redaction
- FastAPI server_request_hook / response_hook
- SQLAlchemy async instrumentation (.sync_engine, enable_commenter)
- Celery task attribute enrichment (retries, task name)
- HTTP client instrumentation (httpx, requests)

#### `exporters-and-backends.md`
- OTLP gRPC vs HTTP comparison table (throughput, load balancing, debugging, serverless)
- BatchSpanProcessor tuning (max_queue_size, schedule_delay_millis, max_export_batch_size)
- Silent span dropping under load
- Custom SpanProcessors (filtering, enrichment, conditional routing)
- Collector pipeline configuration (receivers, processors, exporters)
- Multi-backend routing

#### `aws-deployment.md`
- ADOT distro (aws-opentelemetry-distro v0.16.0)
- X-Ray ID generator and propagator
- AWS resource detectors (EC2, ECS, Lambda)
- Lambda layer setup (SAM template, environment variables, cold start optimization)
- ECS sidecar pattern (task definition, SSM Parameter Store for config)
- Collector-less direct export to X-Ray/CloudWatch OTLP endpoints
- Migration from aws-xray-sdk to OTel

#### `production-checklist.md`
- Do list: set service.name, BatchSpanProcessor, ParentBased sampling, shutdown handlers, OTEL_SDK_DISABLED kill switch, is_recording() guard, BSP queue sizing
- Don't list: init before fork, spans in hot loops, PII in attributes/baggage, None attribute values, SimpleSpanProcessor in staging, skip Collector
- Resource detection configuration (get_aggregated_resources, detector list)
- SDK signal maturity table (Traces stable, Metrics stable, Logs experimental)
- Key packages and versions table
- Recent breaking changes (v1.40.0, v1.39.0, v1.22.0)

## Marketplace Registration

```json
{
  "name": "opentelemetry",
  "source": "./plugins/opentelemetry",
  "description": "OpenTelemetry Python instrumentation expert -- distributed tracing architecture, async context propagation, custom transport propagators (AMQP, ZMQ), OTLP exporters, AWS ADOT/X-Ray, Collector configuration, and production observability patterns",
  "version": "1.0.0",
  "author": { "name": "Alfio" },
  "license": "MIT",
  "keywords": [
    "opentelemetry",
    "otel",
    "tracing",
    "distributed-tracing",
    "observability",
    "instrumentation",
    "spans",
    "context-propagation",
    "otlp",
    "aws-xray",
    "adot",
    "celery",
    "fastapi",
    "asyncio",
    "metrics"
  ],
  "category": "development",
  "strict": false,
  "agents": ["./agents/otel-architect.md"],
  "skills": ["./skills/opentelemetry"]
}
```

## Content Source

The skill references and agent knowledge are derived from a comprehensive OTel Python guide provided by the user, covering:
- SDK v1.40.0 / 0.61b0 (March 2026)
- Python 3.9-3.14 support
- Async context propagation mechanics
- FastAPI, Celery, SQLAlchemy instrumentation
- W3C TraceContext, Baggage, B3, X-Ray propagation
- OTLP gRPC/HTTP exporters, BatchSpanProcessor tuning
- AWS ADOT, X-Ray, Lambda, ECS deployment
- Custom SpanProcessors, sampling strategies
- Three pillars correlation (logs + traces + metrics)
- Production operational checklist

The guide content is split across the skill's reference files by topic area, with the core patterns and decision trees in SKILL.md and deep dives in the references/ directory.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Plugin name | `opentelemetry` | Matches technology naming pattern (like `react-development`) |
| Agent count | 1 (`otel-architect`) | All 5 capabilities are tightly coupled; splitting would cause overlap |
| Skill organization | Single SKILL.md + 5 references | OTel content is interconnected; references allow on-demand loading |
| Commands | None | Agent handles auditing conversationally |
| Model | `opus` | Complex architectural reasoning required |
| Color | `cyan` | Architecture/design convention |
| Category | `development` | Matches peer plugins |
