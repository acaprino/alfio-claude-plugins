# Production Checklist

The do/don't rules and operational defaults for shipping OTel Python in production. Most of the version-specific detail (package versions, breaking changes per release) lives upstream and changes every minor release -- check the links below.

## When to use

Auditing a service for production-readiness, or before a first prod deploy. For instrumentation patterns (FastAPI, Celery, SQLAlchemy), see `instrumentation-patterns.md`.

## Do these (the non-negotiables)

1. **Always set `service.name`** -- without it everything appears as `unknown_service`. Set via `Resource.create({"service.name": "..."})` or `OTEL_SERVICE_NAME` env var (env wins).
2. **`BatchSpanProcessor` exclusively in production.** `SimpleSpanProcessor` exports synchronously per `span.end()` -- catastrophic for throughput.
3. **`ParentBased` sampling everywhere.** Mixing `ParentBased` in service A with raw `TraceIdRatioBased` in service B re-rolls sampling per-hop and produces partial traces. `ParentBased` only applies its delegate to root spans.
4. **Register shutdown handlers.** Without `provider.shutdown()` on `atexit`/`SIGTERM`, the last batch in `BatchSpanProcessor` is lost on every restart.
5. **`OTEL_SDK_DISABLED=true` as a kill switch.** Deploys with this env var return no-op for all signals -- instant rollback without code change.
6. **`span.is_recording()` before expensive attribute computation.** API guarantees no-throw on non-recording spans, but JSON-serializing a 50KB object still wastes CPU.
7. **Tune `OTEL_BSP_MAX_QUEUE_SIZE` for spiky workloads.** Default 2048; bump to 8192+ for bursts. Dropped spans are silent by default -- monitor `otel.bsp.spans.dropped` if available.

## Don't do these

1. **Don't init OTel before `fork()`** in Celery / Gunicorn prefork. `BatchSpanProcessor` threads don't survive fork. Init in `worker_process_init` (Celery) or `post_fork` (Gunicorn). See `instrumentation-patterns.md` for full Celery recipe.
2. **Don't create spans in hot loops without sampling.** Even 1µs/span × 1M iter = 1s of overhead. Move outside the loop and record iteration count as an attribute.
3. **Don't put PII or secrets in span attributes or baggage.** Baggage propagates to every downstream service. Attributes land in your tracing backend with broad read access. Scrub or hash.
4. **Don't set attributes with `None` values.** Behavior is undefined -- some exporters drop, others raise. Guard with `if value is not None`.
5. **Don't use `SimpleSpanProcessor` "just for staging."** Staging mirrors prod. Use `OTEL_LOG_LEVEL=debug` to diagnose locally.
6. **Don't skip the Collector in production.** Buffering, retry-with-backoff, attribute enrichment, tail sampling, protocol translation -- all Collector-only. SDK-direct-to-backend is dev-only.

## Resource detection (boilerplate worth pasting)

Run once at startup. Resource attributes enrich every span/metric/log.

```python
from opentelemetry.sdk.resources import (
    Resource, get_aggregated_resources,
    ProcessResourceDetector, OTELResourceDetector,
)
from opentelemetry.sdk.extension.aws.resource.ec2 import AwsEc2ResourceDetector
from opentelemetry.sdk.extension.aws.resource.ecs import AwsEcsResourceDetector

resource = get_aggregated_resources(
    detectors=[
        OTELResourceDetector(),         # OTEL_RESOURCE_ATTRIBUTES env var
        ProcessResourceDetector(),       # process.pid, process.runtime.*
        AwsEc2ResourceDetector(),        # cloud.provider, cloud.region, host.id
        AwsEcsResourceDetector(),        # aws.ecs.cluster.arn, aws.ecs.task.arn
    ],
    initial_resource=Resource.create({
        "service.name": "order-service",
        "service.version": "2.1.0",
    }),
    timeout=5,
)
```

Since SDK 1.40.0: `OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=*` auto-loads all installed detectors via entry points -- no Python listing needed.

## Signal maturity (sanity check before adoption)

| Signal | Status | Production ready? |
|--------|--------|-------------------|
| Traces | Stable | **Yes** |
| Metrics | Stable | **Yes** |
| Logs | Experimental (`opentelemetry._logs`) | Use bridge instrumentation, not direct SDK |
| Baggage | Stable | **Yes** |

For log-trace correlation in production today, use `opentelemetry-instrumentation-logging` to inject `trace_id`/`span_id` into stdlib log records and ship through your existing log pipeline (CloudWatch, ELK, etc.). Adopt OTLP log export when the API stabilizes.

## Pinning policy

- **Stable** (`opentelemetry-api`, `opentelemetry-sdk`, exporters): pin to **exact version** (e.g. `==1.40.0`).
- **Instrumentation packages** (e.g. `opentelemetry-instrumentation-fastapi==0.61b0`): pin with `~=` to allow patch updates.
- Track upstream release notes -- minor versions occasionally break instrumentation when the underlying library changes its internals.

## Official docs

- Python SDK GitHub: https://github.com/open-telemetry/opentelemetry-python
- Python contrib (instrumentations): https://github.com/open-telemetry/opentelemetry-python-contrib
- Python SDK readthedocs: https://opentelemetry-python.readthedocs.io/
- Spec: https://opentelemetry.io/docs/specs/otel/
- Collector contrib: https://github.com/open-telemetry/opentelemetry-collector-contrib
- AWS ADOT: https://aws-otel.github.io/
- X-Ray → OTel migration: https://docs.aws.amazon.com/xray/latest/devguide/migrate-xray-to-opentelemetry-python.html
- Release notes (check before any upgrade): https://github.com/open-telemetry/opentelemetry-python/releases

## Related

- `instrumentation-patterns.md` -- per-framework setup, decorators, error handling
- `exporters-and-backends.md` -- BSP tuning details, propagation formats, custom processors
- `aws-deployment.md` -- ADOT, X-Ray, ECS sidecar, collector-less direct export
- `async-context-propagation.md` -- the crown jewel: thread/fork/asyncio context traps
