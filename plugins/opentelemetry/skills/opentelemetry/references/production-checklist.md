# Production Checklist

OpenTelemetry Python production readiness reference. Covers critical configuration,
common mistakes, resource detection, SDK maturity, package versions, and breaking changes.

---

## Do These

1. **Always set `service.name`** -- without it, every span appears as `unknown_service`
   in your backend, making traces impossible to filter or route. Set it via
   `Resource.create({"service.name": "my-service"})` or the
   `OTEL_SERVICE_NAME` environment variable (env var takes precedence).

2. **Use `BatchSpanProcessor` exclusively** -- `SimpleSpanProcessor` calls the exporter
   synchronously on every `span.end()`, adding network latency to every operation.
   `BatchSpanProcessor` buffers spans and exports them on a background thread.

3. **Use `ParentBased` sampling across all services** -- if Service A uses `ParentBased`
   and Service B uses `TraceIdRatioBased` directly, B will re-roll the sampling decision
   for incoming traces, producing partial traces with missing spans. `ParentBased` respects
   the upstream decision and only applies its delegate sampler to root spans.

4. **Register shutdown handlers** -- without explicit shutdown, the last batch of spans
   in the `BatchSpanProcessor` queue is lost on every deployment or restart.

   ```python
   import atexit
   import signal

   atexit.register(provider.shutdown)
   signal.signal(signal.SIGTERM, lambda *_: provider.shutdown())
   ```

5. **Set `OTEL_SDK_DISABLED=true` as a feature flag** -- deploy the ability to kill all
   telemetry instantly without a code change. When set, the SDK returns no-op
   implementations for all signals. Pair with a feature flag system for instant rollback.

6. **Check `span.is_recording()` before computing expensive attributes** -- the API
   guarantees no-throw behavior on non-recording spans, but expensive computation
   (serialization, deep inspection) still wastes CPU on unsampled spans.

   ```python
   if span.is_recording():
       span.set_attribute("order.items", json.dumps(serialize_items(order)))
   ```

7. **Configure `OTEL_BSP_MAX_QUEUE_SIZE`** higher than default (2048) for spiky workloads
   -- dropped spans are silent by default. Set `OTEL_BSP_MAX_QUEUE_SIZE=8192` or higher.
   Monitor `otel.bsp.spans.dropped` metrics if available in your SDK version.

---

## Don't Do These

1. **Don't initialize OTel before `fork()`** in Celery/Gunicorn prefork workers --
   `BatchSpanProcessor` threads don't survive `fork()`, so export silently fails.
   Initialize in the `post_fork` / `worker_process_init` hook instead.

   ```python
   # gunicorn.conf.py
   def post_fork(server, worker):
       from myapp.telemetry import init_otel
       init_otel()
   ```

2. **Don't create spans in hot loops** without sampling -- even at 1us per span,
   1M iterations adds 1 second of overhead. Use sampling or move the span outside
   the loop and record iteration count as an attribute.

3. **Don't put PII or secrets in span attributes or baggage** -- baggage propagates
   to every downstream service automatically. Attributes are stored in your tracing
   backend, often with broad read access. Scrub or hash sensitive values.

4. **Don't set attributes with `None` values** -- behavior is undefined in the SDK.
   Some exporters silently drop the attribute, others raise. Guard with a conditional.

5. **Don't use `SimpleSpanProcessor` "just for testing in staging"** -- staging should
   mirror production config. Use `OTEL_LOG_LEVEL=debug` or
   `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4317` to diagnose locally.

6. **Don't skip the Collector** in production -- the Collector provides buffering, retry
   with backoff, attribute enrichment, tail sampling, and protocol translation that the
   SDK alone cannot offer. SDK-direct-to-backend is acceptable only for development.

---

## Resource Detection

Run once at startup. Resource attributes enrich every span, metric, and log record
with infrastructure metadata.

```python
from opentelemetry.sdk.resources import (
    Resource,
    get_aggregated_resources,
    ProcessResourceDetector,
    OTELResourceDetector,
)
from opentelemetry.sdk.extension.aws.resource.ec2 import AwsEc2ResourceDetector
from opentelemetry.sdk.extension.aws.resource.ecs import AwsEcsResourceDetector

resource = get_aggregated_resources(
    detectors=[
        OTELResourceDetector(),       # reads OTEL_RESOURCE_ATTRIBUTES env var
        ProcessResourceDetector(),     # process.pid, process.runtime.*
        AwsEc2ResourceDetector(),      # cloud.provider, cloud.region, host.id
        AwsEcsResourceDetector(),      # aws.ecs.cluster.arn, aws.ecs.task.arn
    ],
    initial_resource=Resource.create({
        "service.name": "order-service",
        "service.version": "2.1.0",
    }),
    timeout=5,
)
```

As of v1.40.0: set `OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=*` to auto-load all installed
detectors without listing them explicitly.

Collector-side alternative: use the `resourcedetection` processor with
`detectors: [env, system, docker, ec2, ecs, eks, gcp, azure]` to enrich spans at the
Collector rather than in the SDK.

---

## SDK Signal Maturity (March 2026)

| Signal  | API                | SDK                | Production ready? |
|---------|--------------------|--------------------|-------------------|
| Traces  | Stable (v1.40.0)   | Stable (v1.40.0)   | Yes               |
| Metrics | Stable (v1.40.0)   | Stable (v1.40.0)   | Yes               |
| Logs    | Experimental       | Experimental (`_logs`) | Use with caution  |
| Baggage | Stable             | N/A                | Yes               |

Logs remain under the `opentelemetry._logs` namespace (leading underscore) to signal
experimental status. Expect API changes between minor versions. For production log
correlation, use `opentelemetry-instrumentation-logging` to inject `trace_id` and
`span_id` into stdlib log records rather than the full OTel Logs SDK pipeline.

---

## Key Packages and Versions

| Package | Version | Purpose |
|---------|---------|---------|
| `opentelemetry-api` | 1.40.0 | Core API (traces, metrics, context) |
| `opentelemetry-sdk` | 1.40.0 | SDK implementation |
| `opentelemetry-exporter-otlp-proto-grpc` | 1.40.0 | gRPC OTLP exporter |
| `opentelemetry-exporter-otlp-proto-http` | 1.40.0 | HTTP OTLP exporter |
| `opentelemetry-instrumentation-fastapi` | 0.61b0 | FastAPI auto-instrumentation |
| `opentelemetry-instrumentation-celery` | 0.61b0 | Celery auto-instrumentation |
| `opentelemetry-instrumentation-sqlalchemy` | 0.61b0 | SQLAlchemy (sync + async) |
| `opentelemetry-instrumentation-httpx` | 0.61b0 | httpx client |
| `opentelemetry-instrumentation-logging` | 0.61b0 | Log-trace correlation |
| `opentelemetry-instrumentation-threading` | 0.61b0 | Thread pool context propagation |
| `opentelemetry-propagator-aws-xray` | 1.0.2 | X-Ray propagator |
| `opentelemetry-sdk-extension-aws` | latest | X-Ray ID gen + AWS resource detectors |
| `aws-opentelemetry-distro` | 0.16.0 | Full AWS auto-instrumentation distro |

Pin stable packages (`opentelemetry-api`, `opentelemetry-sdk`, exporters) to exact
versions. Pin instrumentation packages (`0.61b0`) with `~=` to allow patch updates.

---

## Recent Breaking Changes

### v1.40.0 (March 2026)

- `LoggingHandler` deprecated -- use `opentelemetry-instrumentation-logging` combined
  with `BatchLogRecordProcessor` for structured log export.
- `ConcurrentMultiSpanProcessor` made fork-safe -- internal locks are re-initialized
  after `os.fork()`. Previous versions required manual re-initialization.
- Python 3.14 support added. Python 3.8 support dropped.

### v1.39.0

- `LogData` class removed -- use `ReadableLogRecord` for exporters and
  `ReadWriteLogRecord` for processors. Direct migration: replace
  `log_data.log_record` access with the record object itself.

### v1.22.0 (earlier)

- Jaeger exporter removed entirely -- use OTLP exporters instead. Jaeger backend
  accepts OTLP natively since Jaeger v1.35. No protocol translation needed.

---

## Essential References

- opentelemetry-python (core SDK): `github.com/open-telemetry/opentelemetry-python`
- opentelemetry-python-contrib (instrumentations): `github.com/open-telemetry/opentelemetry-python-contrib`
- Python SDK docs: `opentelemetry-python.readthedocs.io`
- AWS ADOT docs: `aws-otel.github.io`
- OTel Collector contrib: `github.com/open-telemetry/opentelemetry-collector-contrib`
- OTel specification: `opentelemetry.io/docs/specs/otel/`
- X-Ray migration: `docs.aws.amazon.com/xray/latest/devguide/migrate-xray-to-opentelemetry-python.html`
