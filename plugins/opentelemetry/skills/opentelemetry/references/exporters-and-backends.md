# Exporters and Backends

How to get telemetry data out of your Python application and into observability backends -- covering transport protocols, batching, propagation, sampling, Collector configuration, and log-trace correlation.

## OTLP gRPC vs HTTP

The OpenTelemetry Protocol (OTLP) supports two transport variants. The right choice depends on your deployment topology, not raw performance.

| Factor | gRPC (port 4317) | HTTP/protobuf (port 4318) |
|--------|-------------------|---------------------------|
| Throughput | 10k-50k spans/sec | 5k-20k spans/sec |
| Load balancing | Needs gRPC-aware LB | Standard ALB/nginx works |
| Debugging | Binary, harder to inspect | curl-friendly |
| Serverless | Poor (persistent conn overhead) | Preferred (stateless) |
| Proxy/firewall | Often blocked | Generally allowed |

Guidance:

- **Use gRPC** for high-throughput internal services in Kubernetes where you control the network. gRPC multiplexes over a single TCP connection and supports bidirectional streaming, making it efficient when a persistent connection is acceptable.
- **Use HTTP/protobuf** for Lambda/serverless, anything behind an ALB, or environments with restrictive firewalls. HTTP transport creates a fresh connection per batch, avoiding the cold-start penalty of gRPC channel setup.
- The OTel spec now recommends `http/protobuf` as the default protocol. Newer SDKs default to port 4318.

```python
# gRPC exporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
exporter = OTLPSpanExporter(endpoint="http://collector:4317", insecure=True)

# HTTP/protobuf exporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
exporter = OTLPSpanExporter(endpoint="http://collector:4318/v1/traces")
```

Or configure via environment variables without code changes:

```bash
OTEL_EXPORTER_OTLP_PROTOCOL=grpc          # or http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317
```

## BatchSpanProcessor

The only production choice. `SimpleSpanProcessor` exports synchronously on every span end -- useful for debugging, catastrophic for throughput. `BatchSpanProcessor` buffers spans in a thread-safe `collections.deque` and exports via a background thread independent of the async event loop -- it does not block coroutines.

Tuning parameters with corresponding env vars:

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(
    exporter,
    max_queue_size=4096,           # OTEL_BSP_MAX_QUEUE_SIZE (default 2048)
    schedule_delay_millis=5000,    # OTEL_BSP_SCHEDULE_DELAY (default 5000)
    max_export_batch_size=512,     # OTEL_BSP_MAX_EXPORT_BATCH_SIZE (default 512)
    export_timeout_millis=30000,   # OTEL_BSP_EXPORT_TIMEOUT (default 30000)
)
```

**Critical:** when the queue fills, new spans are **silently dropped**. No error, no warning by default. You will not know you are losing data unless you actively monitor. Detect this via SDK internal metrics or set `OTEL_LOG_LEVEL=debug` to surface drop warnings.

Tuning heuristics:
- `max_queue_size` -- set to 2-4x your peak spans-per-second burst. Too small drops spans, too large consumes memory.
- `schedule_delay_millis` -- lower values reduce latency to backend but increase export frequency. 5000ms is a reasonable default.
- `max_export_batch_size` -- keep at or below 512. Larger batches increase per-export latency and risk timeouts.
- `export_timeout_millis` -- if your Collector is remote or under load, increase to 60000ms.

## Propagation Formats

Propagators serialize trace context into carrier objects (HTTP headers, message metadata) so that downstream services can reconstruct the parent span relationship.

| Format | Headers | Use when |
|--------|---------|----------|
| W3C TraceContext | `traceparent`, `tracestate` | Default for all new systems |
| W3C Baggage | `baggage` | Cross-service metadata (tenant ID, feature flags) |
| B3 | `b3` or `X-B3-TraceId` + siblings | Legacy Zipkin, older Istio/Envoy |
| AWS X-Ray | `X-Amzn-Trace-Id` | AWS-native services (ALB, API Gateway, Lambda) |

Composite propagator for environments that must support multiple formats simultaneously:

```python
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.aws import AwsXRayPropagator

set_global_textmap(CompositePropagator([
    TraceContextTextMapPropagator(),
    W3CBaggagePropagator(),
    AwsXRayPropagator(),
]))
```

Or configure entirely via environment variable:

```bash
OTEL_PROPAGATORS="tracecontext,baggage,xray"
```

The composite propagator tries each propagator in order on extract. On inject, all propagators write their headers -- this means outgoing requests carry all formats, and incoming requests are understood regardless of which format the caller used.

## Custom Transport Inject/Extract

For non-HTTP transports (message queues, gRPC metadata, Kafka headers), you must manually inject and extract context. The `inject` and `extract` functions work with any dict-like carrier.

```python
from opentelemetry.propagate import inject, extract
from opentelemetry import context, trace

tracer = trace.get_tracer(__name__)

# Producer: inject context into message headers
headers = {}
inject(headers)
send_message(payload, headers=headers)

# Consumer: extract and activate context
ctx = extract(carrier=incoming_headers)
token = context.attach(ctx)
try:
    with tracer.start_as_current_span("process_message"):
        handle(payload)
finally:
    context.detach(token)
```

For dict-based payloads (AMQP, ZMQ) where headers are not a separate field:
- Store under a dedicated key: `message.payload["_trace_context"] = headers`
- Consumer extracts: `ctx = extract(carrier=message.payload.get("_trace_context", {}))`
- Never mix trace context with business data -- use a namespaced key to avoid collisions

For Kafka specifically, use `opentelemetry-instrumentation-kafka-python` which handles inject/extract automatically. Manual propagation is only needed for transports without auto-instrumentation support.

## Custom SpanProcessors

The `SpanProcessor` interface has two hooks: `on_start` (called synchronously at span creation) and `on_end` (called synchronously at span completion). Custom processors sit between the tracer and the exporter, enabling filtering, enrichment, and routing.

Filtering and enrichment pattern -- drops health-check noise and adds deployment metadata:

```python
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan

class FilteringEnrichmentProcessor(SpanProcessor):
    """Drops health-check spans and enriches all others."""
    def __init__(self, next_processor: SpanProcessor, drop_names: set[str]):
        self._next = next_processor
        self._drop_names = drop_names

    def on_start(self, span, parent_context=None):
        span.set_attribute("deployment.region", "us-east-1")
        self._next.on_start(span, parent_context)

    def on_end(self, span: ReadableSpan):
        if span.name in self._drop_names:
            return  # silently drop
        if span.attributes and span.attributes.get("http.target") in ("/healthz", "/ready"):
            return
        self._next.on_end(span)

    def shutdown(self, timeout_millis=30000):
        self._next.shutdown(timeout_millis)

    def force_flush(self, timeout_millis=30000):
        self._next.force_flush(timeout_millis)

# Wire it up
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

batch = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://collector:4317"))
filtering = FilteringEnrichmentProcessor(batch, drop_names={"health-check", "readiness"})
provider.add_span_processor(filtering)
```

Processors chain: the order you add them to the provider matters. Each processor's `on_end` runs sequentially. If your filtering processor drops a span, downstream processors (including the batch exporter) never see it -- this is how you reduce export volume without changing sampling.

## Sampling Strategies

### Head-Based Sampling

Decided at span creation time in the SDK. Lightweight, no infrastructure overhead, but cannot make decisions based on the complete trace (you do not know yet if the trace will contain errors or high latency).

```python
from opentelemetry.sdk.trace.sampling import (
    ParentBased, TraceIdRatioBased, ALWAYS_ON, ALWAYS_OFF
)

sampler = ParentBased(
    root=TraceIdRatioBased(0.1),          # 10% of new traces
    remote_parent_sampled=ALWAYS_ON,       # follow sampled parent
    remote_parent_not_sampled=ALWAYS_OFF,  # follow unsampled parent
)
```

`ParentBased` is essential for consistent sampling across services. Without it, service A might sample a trace but service B drops its portion -- producing a broken trace.

Custom priority sampler that always keeps critical and error spans:

```python
from opentelemetry.sdk.trace.sampling import Sampler, SamplingResult, Decision

class PrioritySampler(Sampler):
    def __init__(self, default_rate=0.1):
        self._default = TraceIdRatioBased(default_rate)

    def should_sample(self, parent_context, trace_id, name,
                      kind=None, attributes=None, links=None, trace_state=None):
        if attributes and attributes.get("priority") == "critical":
            return SamplingResult(Decision.RECORD_AND_SAMPLE)
        return self._default.should_sample(
            parent_context, trace_id, name, kind, attributes, links, trace_state)

    def get_description(self):
        return "PrioritySampler(0.1)"
```

### Tail-Based Sampling

Decided after the complete trace is assembled, at the Collector level. Requires the `tail_sampling` processor from `opentelemetry-collector-contrib`. This approach can keep 100% of errors and slow traces while sampling routine traffic aggressively.

Constraint: all spans for a given trace must hit the same Collector instance. Use the `loadbalancing` exporter in a first-tier Collector to route by trace ID.

```yaml
processors:
  tail_sampling:
    decision_wait: 30s
    num_traces: 100000
    policies:
      - name: errors-always
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-traces
        type: latency
        latency: { threshold_ms: 5000 }
      - name: baseline-5pct
        type: probabilistic
        probabilistic: { sampling_percentage: 5 }
```

### Hybrid Approach

Recommended at scale: head-sample 10-20% in the SDK to reduce raw volume, then tail-sample at the Collector for 100% error/slow retention. This gives you manageable data volume with zero gaps in error visibility.

## Collector Pipeline Configuration

Full production config with multi-backend routing -- traces to X-Ray and Jaeger, metrics to CloudWatch EMF:

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  batch: { timeout: 5s, send_batch_size: 256 }
  memory_limiter: { check_interval: 1s, limit_mib: 400, spike_limit_mib: 100 }
  resourcedetection: { detectors: [env, ec2, ecs], timeout: 5s, override: false }

exporters:
  awsxray:
    region: us-east-1
    indexed_attributes: [otel.resource.service.name]
  awsemf:
    region: us-east-1
    namespace: MyApplication
    log_group_name: /aws/otel/metrics
  otlp/jaeger:
    endpoint: jaeger:4317
    tls: { insecure: true }

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [awsxray]
    traces/jaeger:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [awsemf]
```

Key points:
- `memory_limiter` MUST be the first processor in every pipeline -- it prevents OOM by dropping data when memory pressure is high
- Multiple pipelines enable multi-backend routing from a single receiver
- Named exporters (`otlp/jaeger`) disambiguate when you have multiple instances of the same exporter type
- `resourcedetection` adds cloud metadata (instance ID, region, cluster name) automatically -- set `override: false` so application-set resource attributes take precedence

## Three Pillars Correlation

Connecting traces, logs, and metrics so you can jump from a log line to the trace that produced it.

### Log-Trace Correlation

The logging instrumentor injects trace context into every Python `logging` record:

```python
from opentelemetry.instrumentation.logging import LoggingInstrumentor
LoggingInstrumentor().instrument(set_logging_format=True)
```

Or enable via environment variable without code changes:

```bash
OTEL_PYTHON_LOG_CORRELATION=true
```

This injects `otelTraceID`, `otelSpanID`, and `otelServiceName` into every log record, making them available in format strings and structured log output.

### Structured JSON Logging

For custom logging setups where you need full control over the trace context format:

```python
import logging
from opentelemetry import trace

class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        record.trace_id = format(ctx.trace_id, '032x') if ctx.trace_id else "0" * 32
        record.span_id = format(ctx.span_id, '016x') if ctx.span_id else "0" * 16
        return True

handler = logging.StreamHandler()
handler.addFilter(TraceContextFilter())
formatter = logging.Formatter(
    '{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s",'
    '"trace_id":"%(trace_id)s","span_id":"%(span_id)s"}'
)
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)
```

### Logs via OTLP

The Logs SDK is still experimental (the `_logs` namespace prefix signals this). Use it to ship logs directly to the Collector alongside traces and metrics:

```python
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter(endpoint="http://collector:4317"))
)
```

Note: the Logs SDK remains experimental as of SDK v1.40.0. For production today, use the `LoggingInstrumentor` bridge for correlation and ship logs via your existing log pipeline (CloudWatch, ELK, etc.). Adopt OTLP log export when the API stabilizes.
