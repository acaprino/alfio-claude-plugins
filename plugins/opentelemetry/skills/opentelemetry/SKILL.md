---
name: opentelemetry
description: >
  OpenTelemetry Python instrumentation knowledge base covering distributed tracing,
  async context propagation, custom transport propagators, sampling strategies,
  exporter configuration, and production observability patterns. SDK v1.40.0 target.
  TRIGGER WHEN: working with OpenTelemetry, distributed tracing, span instrumentation,
  context propagation, OTLP exporters, sampling strategies, or observability pipelines.
  DO NOT TRIGGER WHEN: general logging without trace correlation, or application
  monitoring tools unrelated to OTel.
---

# OpenTelemetry Python

Knowledge base for instrumenting Python services with OpenTelemetry -- distributed tracing, metrics, and log correlation.

## When to Use

- Instrumenting a new Python service with distributed tracing
- Adding OTel to FastAPI, Celery, or async Python applications
- Designing context propagation for custom transports (AMQP, ZMQ, Kafka)
- Configuring OTLP exporters, Collectors, or AWS ADOT
- Auditing existing instrumentation for gaps or anti-patterns
- Setting up log-trace correlation
- Choosing sampling strategies for production

## Quick Start Recommendation

For most Python services, start with:
1. **Init**: `opentelemetry-bootstrap -a install` + `opentelemetry-instrument` wrapper
2. **Resource**: Set `service.name`, `service.version`, `deployment.environment`
3. **Sampler**: `ParentBased(TraceIdRatioBased(0.1))` -- 10% head sampling
4. **Exporter**: OTLP gRPC to Collector at `localhost:4317`
5. **Processor**: `BatchSpanProcessor` with default tuning
6. **Shutdown**: Register `provider.shutdown()` in lifespan/atexit

Then upgrade incrementally based on needs:
- Custom business spans -> add manual `tracer.start_as_current_span()` calls
- Non-HTTP transport -> implement custom propagator (see section below)
- AWS deployment -> add ADOT distro + X-Ray ID generator
- High throughput -> tune BatchSpanProcessor queue size + export timeout
- Error visibility -> add tail sampling at Collector level

## Architecture Overview

```
Pipeline:
  TracerProvider -> SpanProcessor (batch/simple) -> Exporter (OTLP gRPC/HTTP)

Context:
  contextvars.ContextVar stores current span + baggage per async task / thread

Signal flow:
  API (opentelemetry.trace) -> SDK (TracerProvider impl) -> Processor -> Exporter -> Collector -> Backend
```

- **API vs SDK**: API is the stable interface (`opentelemetry-api`). SDK is the implementation (`opentelemetry-sdk`). Libraries depend on API only.
- **Auto-instrumentation**: monkey-patches 50+ libraries via `sitecustomize.py` entry point
- Key env vars: `OTEL_SERVICE_NAME`, `OTEL_TRACES_SAMPLER`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SDK_DISABLED`
- **Resource**: identity attributes attached to every span -- `service.name` is required, always set explicitly
- **Propagator**: serializes context across process boundaries. Default: W3C TraceContext + Baggage

## Auto vs Manual Instrumentation

| Layer | Approach | Examples |
|-------|----------|----------|
| HTTP frameworks | Auto | FastAPI, Django, Flask |
| Database clients | Auto | SQLAlchemy, psycopg2, asyncpg |
| HTTP clients | Auto | httpx, requests, aiohttp |
| Message queues | Auto | Celery, Kafka |
| Cache | Auto | redis, memcached |
| Business logic | **Manual** | Order processing, payment flows |
| Custom transport | **Manual** | AMQP payload, ZMQ events |

Combined pattern: `opentelemetry-instrument` wraps app for auto. Manual spans added inside routes/handlers for business logic.

## Framework Patterns

**FastAPI:**
- `FastAPIInstrumentor.instrument_app(app, excluded_urls="health,ready,metrics")`
- Lifespan for shutdown: call `provider.shutdown()` in `async with` cleanup block
- Request hooks for custom attributes: `request_id`, `tenant_id`, `user_id`

**Celery:**
- CRITICAL: Init OTel AFTER fork via `@worker_process_init.connect`
- `BatchSpanProcessor` threads do not survive `fork()` -- re-init required
- `CeleryInstrumentor` injects context into message headers automatically

**SQLAlchemy async:**
- Pass `.sync_engine` to instrumentor, not the async engine
- `enable_commenter=True` for SQL comment injection with trace context

**Django:**
- `DjangoInstrumentor().instrument()` in `manage.py` or WSGI entrypoint
- Middleware auto-creates spans for each request; pairs with auto-instrumented DB calls

## Custom Transport Propagation

Rules for non-HTTP transports (AMQP, ZMQ, custom sockets):
- Implement `inject()` on producer side -- serialize trace context into message headers/payload
- Implement `extract()` on consumer side -- deserialize and attach to current context
- Use W3C TraceContext format (`traceparent` + `tracestate` keys)
- Carrier: dict-based, case-insensitive keys for HTTP compat

```python
# Producer
from opentelemetry.context import attach
from opentelemetry.propagate import inject, extract

headers = {}
inject(headers)
message.payload["_trace_context"] = headers
```

```python
# Consumer
ctx = extract(carrier=message.payload.get("_trace_context", {}))
token = attach(ctx)
try:
    with tracer.start_as_current_span("process"):
        handle(message)
finally:
    context.detach(token)
```

## Sampling Strategies

Decision tree:
- **Always**: `ParentBased` wrapper -- respects parent's sampling decision
- **Head-based** (SDK): `TraceIdRatioBased(rate)` -- cheap, consistent, blind to content
- **Tail-based** (Collector): `tail_sampling` processor -- keeps errors, slow traces. Requires all spans for a trace to hit same Collector instance.
- **Hybrid** (production at scale): head-sample at 10-20% in SDK, tail-sample at Collector to retain 100% of errors/slow

| Strategy | Where | Pros | Cons |
|----------|-------|------|------|
| AlwaysOn | SDK | Complete data | Expensive at scale |
| TraceIdRatio | SDK | Predictable cost | Drops interesting traces |
| ParentBased | SDK | Consistent per-trace | Depends on root decision |
| Tail sampling | Collector | Content-aware | Memory-heavy, needs affinity |

Env vars: `OTEL_TRACES_SAMPLER=parentbased_traceidratio`, `OTEL_TRACES_SAMPLER_ARG=0.1`

## BatchSpanProcessor Tuning

Default values work for most services. Tune only when observing dropped spans or export latency:

| Parameter | Default | Guidance |
|-----------|---------|----------|
| `max_queue_size` | 2048 | Increase for bursty workloads (4096-8192) |
| `schedule_delay_millis` | 5000 | Lower (1000-2000) for near-realtime export |
| `max_export_batch_size` | 512 | Match exporter batch limits |
| `export_timeout_millis` | 30000 | Reduce if exporter hangs block shutdown |

- Monitor `otel.bsp.spans.dropped` metric for queue overflow
- Use `SimpleSpanProcessor` only in tests -- it blocks on every span end

## Three Pillars Correlation

**Log-trace correlation:**
- `opentelemetry-instrumentation-logging` injects `otelTraceID`, `otelSpanID` into log records
- Or env var: `OTEL_PYTHON_LOG_CORRELATION=true`
- Add `TraceContextFilter` to logging handler for `trace_id`/`span_id` in JSON output

**Metrics:**
- `MeterProvider` + instruments: `Counter`, `Histogram`, `UpDownCounter`, `Gauge`
- Shares same `Resource` with `TracerProvider` for correlation
- Use `ObservableGauge` for system metrics (pool sizes, queue depth)

**Logs SDK:**
- `_logs` module is experimental -- use instrumentation bridge, not direct `LoggerProvider`

## Error Handling

- `span.record_exception(e, attributes={})` -- unexpected errors; creates span event with stacktrace
- `span.add_event("name", attributes={})` -- expected business outcomes (e.g. declined payment)
- Status: `UNSET` -> `OK` (explicit success) or `UNSET` -> `ERROR` (failures, 5xx only for HTTP)
- `start_as_current_span()` auto-records exceptions and sets ERROR status by default
- Do NOT set `OK` on every span -- `UNSET` is the correct default for successful operations
- Span attribute limits: default 128 attributes per span. Set `OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT` if needed.
- Never put high-cardinality values (user IDs, request bodies) in span names -- use attributes instead

## Reference Materials

Detailed reference documents are in the `references/` directory:

- `async-context-propagation.md` -- contextvars mechanics, asyncio task propagation, thread boundary traps, TracedThreadPoolExecutor, Python 3.12+ improvements
- `instrumentation-patterns.md` -- auto-instrumentation setup, FastAPI/Celery/SQLAlchemy patterns, custom decorators, error handling in spans
- `exporters-and-backends.md` -- OTLP gRPC vs HTTP, BatchSpanProcessor tuning, propagation formats, custom SpanProcessors, Collector pipelines
- `aws-deployment.md` -- ADOT distro, X-Ray integration, Lambda layers, ECS sidecar, collector-less direct export, migration from aws-xray-sdk
- `production-checklist.md` -- do/don't operational rules, resource detection, SDK signal maturity, package versions, breaking changes
