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

Index for OTel Python -- traces, metrics, log-trace correlation, distributed propagation. References hold the gotchas; canonical reference lives at https://opentelemetry-python.readthedocs.io and https://opentelemetry.io/docs/.

## When to use

- New Python service that needs distributed tracing
- Adding OTel to FastAPI / Celery / async Python
- Custom transports (AMQP, ZMQ, Kafka) needing propagator wiring
- OTLP exporter / Collector / AWS ADOT configuration
- Auditing existing instrumentation for gaps or anti-patterns
- Log-trace correlation
- Sampling strategy choice for production

## Quick-start production recipe

For most Python services, start with this and iterate:

1. **Init**: `opentelemetry-bootstrap -a install` + `opentelemetry-instrument` wrapper
2. **Resource**: set `service.name`, `service.version`, `deployment.environment`
3. **Sampler**: `ParentBased(TraceIdRatioBased(0.1))` -- 10% head sampling
4. **Exporter**: OTLP gRPC to a local Collector at `localhost:4317`
5. **Processor**: `BatchSpanProcessor` with default tuning (raise `OTEL_BSP_MAX_QUEUE_SIZE=8192` if bursty)
6. **Shutdown**: register `provider.shutdown()` in lifespan / `atexit` / `SIGTERM`

Then escalate based on what you actually need:
- Custom business spans → manual `tracer.start_as_current_span()`
- Non-HTTP transport → custom propagator (skeleton in `exporters-and-backends.md`)
- AWS deployment → ADOT distro + X-Ray ID generator (`aws-deployment.md`)
- High throughput → tune BSP queue size + export timeout
- Error-only retention → tail sampling at the Collector

## Auto vs manual instrumentation (the matrix)

| Layer | Approach | Examples |
|-------|----------|----------|
| HTTP frameworks | **Auto** | FastAPI, Django, Flask |
| Database clients | **Auto** | SQLAlchemy, psycopg2, asyncpg |
| HTTP clients | **Auto** | httpx, requests, aiohttp |
| Message queues | **Auto** | Celery, Kafka |
| Cache | **Auto** | redis, memcached |
| Business logic | **Manual** | Order processing, payment flows |
| Custom transport | **Manual** | AMQP payload, ZMQ events |

Combined pattern: `opentelemetry-instrument` wraps the app for auto; manual spans inside routes/handlers for business logic. See `instrumentation-patterns.md` for per-framework details.

## Critical framework gotchas (worth memorizing)

- **Celery**: init OTel **after fork** via `@worker_process_init.connect`. `BatchSpanProcessor` threads don't survive `fork()` -- export silently fails otherwise. Recipe in `instrumentation-patterns.md`.
- **SQLAlchemy async**: pass `engine.sync_engine` to the instrumentor, NOT the async engine.
- **FastAPI**: register `provider.shutdown()` in `lifespan` cleanup, otherwise last span batch is lost on every restart.
- **HTTP status / Span Status**: only 5xx → `StatusCode.ERROR`. 4xx are client errors, leave UNSET. Business rejections (declined payment) use `add_event`, not ERROR.

## Custom transport propagation (skeleton)

For AMQP, ZMQ, custom sockets -- inject on producer, extract on consumer, use W3C TraceContext format.

```python
# Producer
from opentelemetry.propagate import inject
headers = {}; inject(headers)
message.payload["_trace_context"] = headers

# Consumer
from opentelemetry.propagate import extract
from opentelemetry import context, trace
ctx = extract(carrier=message.payload.get("_trace_context", {}))
token = context.attach(ctx)
try:
    with trace.get_tracer(__name__).start_as_current_span("process"):
        handle(message)
finally:
    context.detach(token)
```

Full discussion + custom SpanProcessor patterns: `exporters-and-backends.md`.

## Sampling -- the decision tree

- **`ParentBased(TraceIdRatioBased(rate))`** -- the right default. Respects upstream decision; only applies the delegate to root spans. Without ParentBased, downstream services re-roll → broken traces.
- **Tail sampling at the Collector** -- when you need to keep 100% of errors/slow traces while sampling routine traffic. Requires trace-ID affinity (loadbalancing exporter in front).
- **Hybrid** at scale: head-sample 10-20% in SDK + tail-sample at Collector for error/slow retention.

Env shortcut: `OTEL_TRACES_SAMPLER=parentbased_traceidratio`, `OTEL_TRACES_SAMPLER_ARG=0.1`.

## Reference index

- `async-context-propagation.md` -- contextvars mechanics, asyncio task propagation, **thread boundary trap, TracedThreadPoolExecutor, fork+BSP loss, Python 3.12+ improvements** (the crown jewel of this skill -- read first when debugging missing/broken context)
- `instrumentation-patterns.md` -- auto-instrument setup, FastAPI/Celery/SQLAlchemy patterns, `traced_async` decorator, `TracedClass` mixin, sensitive-arg redaction, error handling
- `exporters-and-backends.md` -- OTLP gRPC vs HTTP, BSP tuning, propagation formats, custom SpanProcessors, multi-backend Collector YAML
- `aws-deployment.md` -- ADOT distro, X-Ray ID generator + propagator, ECS sidecar with memory_limiter ordering, IAM list, Lambda layer, collector-less when/when-not, X-Ray SDK migration
- `production-checklist.md` -- do/don't operational rules, resource detection boilerplate, signal maturity, version pinning policy

## Three pillars correlation (one-liner)

```python
# Inject trace_id / span_id / service_name into every stdlib log record
from opentelemetry.instrumentation.logging import LoggingInstrumentor
LoggingInstrumentor().instrument(set_logging_format=True)
# OR env: OTEL_PYTHON_LOG_CORRELATION=true
```

For metrics: `MeterProvider` + `Counter`/`Histogram`/`UpDownCounter`/`ObservableGauge`. Shares `Resource` with `TracerProvider` so service identity is consistent.

For OTLP log export: the Logs SDK (`opentelemetry._logs`, leading underscore = experimental) -- in production today, use the `LoggingInstrumentor` bridge and ship via your existing log pipeline.

## Official docs

- Python SDK: https://opentelemetry-python.readthedocs.io/
- Specification: https://opentelemetry.io/docs/specs/otel/
- All instrumentations index: https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation
- Collector contrib: https://github.com/open-telemetry/opentelemetry-collector-contrib
- Release notes (always check before upgrade): https://github.com/open-telemetry/opentelemetry-python/releases
