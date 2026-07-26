---
description: >
  Audit an existing OpenTelemetry Python instrumentation for correctness, performance, and production readiness.
  TRIGGER WHEN: the user asks to review, audit, or validate OTel instrumentation - span hygiene, context propagation, exporter config, sampling, async handling, attribute budgets, or AWS X-Ray / ADOT setup.
  DO NOT TRIGGER WHEN: building new instrumentation from scratch (use otel-architect agent directly), or reviewing non-OTel observability (Datadog APM, Sentry only, etc.).
argument-hint: "[path-or-description]"
---

# OpenTelemetry Audit

Analyze an existing OpenTelemetry Python instrumentation and produce an actionable audit report.

## Instructions

1. **Identify OTel components** in the codebase:
   - SDK setup (`TracerProvider`, `MeterProvider`, `LoggerProvider`)
   - Exporters (OTLP gRPC/HTTP, X-Ray, console)
   - Propagators (W3C TraceContext, B3, X-Amzn-Trace-Id, custom)
   - Instrumentations (auto-instrumentations, manual spans)
   - Samplers (parent-based, trace-id-ratio, always-on)
   - Resource detectors (service.name, service.version, aws.ec2, k8s.pod)
   - Collector / ADOT config (if present)

2. **Audit each dimension** against best practices:

### SDK Setup
- [ ] `TracerProvider` created once at process start, not per request
- [ ] `service.name` and `service.version` resources set (required for most backends)
- [ ] Resource detectors attached (aws-ec2 / k8s / ecs / container detectors for cloud)
- [ ] Shutdown registered (`atexit` or signal handler) to flush spans on exit

### Span Hygiene
- [ ] Spans use `start_as_current_span` (context manager) not raw `start_span` where possible
- [ ] Status set to ERROR only for infrastructure errors; business-logic rejections leave status UNSET
- [ ] `record_exception` used for infrastructure errors, NOT for expected business errors
- [ ] `add_event` used for business-logic events instead of new spans
- [ ] Status is never explicitly set to OK on inner spans (leave UNSET; only the outer request handler may set OK)
- [ ] Span names are low-cardinality (no IDs or user data in the name)
- [ ] Attributes use semantic conventions (`http.request.method`, not `httpMethod`)

### Attribute Budgets
- [ ] No PII in span attributes or baggage (baggage propagates to ALL downstream services)
- [ ] No `None` values in attributes
- [ ] String attributes truncated if potentially long (> 1KB)
- [ ] Span attribute count under the per-span limit (default 128)

### Context Propagation
- [ ] Single `Propagator` chosen intentionally (W3C default, or CompositePropagator for multi-format)
- [ ] Custom transports (AMQP, ZMQ, Kafka, gRPC without auto-instrumentation) inject/extract correctly
- [ ] Propagator instances are module-level or cached (not allocated per call)
- [ ] Async context propagation tested (asyncio, Celery, threading boundaries)

### Async / Threading
- [ ] asyncio: context naturally propagates; verify tasks spawned with `create_task` carry span context
- [ ] Threading: context attached on worker thread entry via `context.attach(ctx)` + `detach(token)` in `finally`
- [ ] Celery: `opentelemetry-instrumentation-celery` installed and configured
- [ ] Batch processors flush on shutdown (not just at the batch interval)

### Exporters
- [ ] OTLP endpoint uses protocol-appropriate port (gRPC 4317 or HTTP 4318)
- [ ] `BatchSpanProcessor` used in production (not `SimpleSpanProcessor`)
- [ ] `max_queue_size` and `schedule_delay_millis` tuned for workload (default 2048 / 5000)
- [ ] TLS configured for OTLP over public networks
- [ ] Compression enabled (`gzip`) for OTLP over HTTP

### Sampling
- [ ] Sampler chosen intentionally (`ParentBasedTraceIdRatio` common default)
- [ ] Ratio appropriate for cost (1.0 in dev, 0.01-0.1 in prod typical)
- [ ] Tail sampling considered if Collector is in the path
- [ ] Error sampling carve-out (always sample error spans) via span processor or Collector

### Logs and Metrics
- [ ] Logs SDK used if log correlation matters (stabilized in v1.26+; no longer underscore-private)
- [ ] `LoggerProvider` set up alongside `TracerProvider`
- [ ] Metrics use correct instruments (Counter for monotonic, UpDownCounter for gauges, Histogram for latencies)
- [ ] View / aggregation configured for high-cardinality metrics

### AWS / ADOT (if applicable)
- [ ] `AwsXRayIdGenerator` used for X-Ray compatibility
- [ ] `AwsXRayPropagator` attached (single or composite with W3C)
- [ ] `aws-ec2` / `aws-ecs` / `aws-lambda` resource detectors enabled
- [ ] ADOT sidecar or Lambda layer configured; Collector pipeline `memory_limiter -> batch -> exporters`

### Anti-Patterns to Flag
- [ ] Per-call propagator instantiation (`TraceContextTextMapPropagator()` inside inject/extract bodies)
- [ ] Spans in hot loops without sampling guards
- [ ] Exceptions silently swallowed after `record_exception` (should still raise or handle explicitly)
- [ ] Using `SimpleSpanProcessor` in production (blocks on every span)
- [ ] Jaeger exporter (removed in v1.22; use OTLP to Jaeger backend instead)

3. **Generate report** with:
   - Current state assessment (what's instrumented, how)
   - Correctness issues (broken propagation, wrong status codes, PII leaks)
   - Performance issues (SimpleSpanProcessor in prod, hot-loop spans, unbounded queues)
   - Production-readiness gaps (shutdown, sampling, resource attributes)
   - Priority fixes ordered by severity + effort
   - Code examples for each recommendation

## Synergies

- Deep propagator / custom transport patterns -> `opentelemetry-architect` (agent)
- Async context propagation patterns -> `python-development:async-python-patterns`
- RabbitMQ propagation -> `messaging:rabbitmq-expert` + `opentelemetry:opentelemetry` reference
