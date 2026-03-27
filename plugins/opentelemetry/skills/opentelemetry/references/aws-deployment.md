# AWS Deployment

Deploying OpenTelemetry Python applications on AWS using the AWS Distro for
OpenTelemetry (ADOT). Covers X-Ray integration, resource detectors, Lambda layers,
ECS sidecar patterns, collector-less direct export, and migration from the legacy
aws-xray-sdk.

---

## ADOT Overview

AWS Distro for OpenTelemetry (ADOT) is NOT a fork -- it bundles the upstream OTel
Collector with AWS-specific components for traces, metrics, and logs.

Bundled components:
- **Exporters**: `awsxray` (traces to X-Ray), `awsemf` (metrics to CloudWatch EMF)
- **Receivers**: `awsxray` (UDP segment receiver), `awsecscontainermetrics`
- **Resource detectors**: EC2, ECS, EKS, Lambda -- auto-populate cloud metadata
- **Python SDK distro**: `aws-opentelemetry-distro` v0.16.0 (March 2026)

What ADOT adds out of the box:
- X-Ray propagation via `X-Amzn-Trace-Id` header
- X-Ray remote sampling (centralized sampling rules from X-Ray console)
- AWS resource detection (region, account, instance ID, task ARN, etc.)

AWS officially recommends migrating from `aws-xray-sdk` to OpenTelemetry. The X-Ray
SDK is in maintenance mode -- no new features, only critical patches.

```bash
pip install aws-opentelemetry-distro
```

---

## X-Ray Integration

Two key components bridge OpenTelemetry and X-Ray:

1. **X-Ray ID Generator** -- embeds a Unix timestamp in the first 32 bits of the
   trace ID. This was historically required for X-Ray compatibility, though standard
   W3C trace IDs have been accepted since October 2023. Using the generator still
   provides the best experience in the X-Ray console (time-based trace filtering).

2. **X-Ray Propagator** -- reads and writes the `X-Amzn-Trace-Id` header format
   (`Root=1-xxx;Parent=yyy;Sampled=1`), enabling trace continuity with other AWS
   services that use native X-Ray propagation.

Full initialization pattern:

```python
from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
from opentelemetry.sdk.extension.aws.resource.ecs import AwsEcsResourceDetector
from opentelemetry.sdk.extension.aws.resource.ec2 import AwsEc2ResourceDetector
from opentelemetry.sdk.resources import get_aggregated_resources, Resource
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry import propagate, trace

resource = get_aggregated_resources(
    detectors=[AwsEc2ResourceDetector(), AwsEcsResourceDetector()],
    initial_resource=Resource.create({"service.name": "my-service"}),
    timeout=5,
)

provider = TracerProvider(
    resource=resource,
    id_generator=AwsXRayIdGenerator(),
    sampler=ParentBased(TraceIdRatioBased(0.1)),
)
trace.set_tracer_provider(provider)

# Enable X-Ray propagation alongside W3C tracecontext
propagate.set_global_textmap(AwsXRayPropagator())
```

Install the required packages:

```bash
pip install opentelemetry-sdk-extension-aws opentelemetry-propagator-aws-xray
```

---

## AWS Resource Detectors

Resource detectors run once at startup -- results are cached and attached to every
span, metric, and log record for the lifetime of the process. They enrich telemetry
with infrastructure metadata without manual configuration.

```python
from opentelemetry.sdk.resources import (
    Resource, get_aggregated_resources,
    ProcessResourceDetector, OTELResourceDetector,
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

Attributes populated by each detector:

| Detector | Attributes |
|----------|-----------|
| `AwsEc2ResourceDetector` | `cloud.provider`, `cloud.platform`, `cloud.region`, `cloud.availability_zone`, `cloud.account.id`, `host.id`, `host.type`, `host.name` |
| `AwsEcsResourceDetector` | `aws.ecs.cluster.arn`, `aws.ecs.task.arn`, `aws.ecs.task.family`, `aws.ecs.task.revision`, `aws.ecs.container.arn`, `cloud.region` |
| `AwsEksResourceDetector` | `k8s.cluster.name`, `cloud.provider`, `cloud.platform` |
| `AwsLambdaResourceDetector` | `cloud.provider`, `cloud.region`, `faas.name`, `faas.version`, `faas.instance` |

As of SDK v1.40.0, setting `OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=*` auto-loads all
installed detectors via entry points -- no explicit Python code needed.

Collector-side detection is also available via the `resourcedetection` processor:
`detectors: [env, system, docker, ec2, ecs, eks, gcp, azure]`. Use both app-side
and collector-side detection when you want process-level and infrastructure-level
attributes combined.

---

## Lambda Setup

ADOT provides a Lambda Layer that bundles the Python SDK and a lightweight Collector
extension. The layer auto-instruments your handler -- no code changes required.

SAM template:

```yaml
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: lambda_function.handler
      Runtime: python3.12
      Layers:
        - arn:aws:lambda:us-east-1:901920570463:layer:aws-otel-python-amd64-ver-1-32-0:1
      Environment:
        Variables:
          AWS_LAMBDA_EXEC_WRAPPER: /opt/otel-instrument
          OTEL_SERVICE_NAME: my-function
          OTEL_PROPAGATORS: tracecontext,xray
      Policies:
        - Statement:
          - Effect: Allow
            Action: [xray:PutTraceSegments, xray:PutTelemetryRecords]
            Resource: "*"
```

Key considerations:
- The Collector extension needs a few hundred milliseconds after the handler returns
  to flush buffered spans. Set function timeout >= 3 seconds to avoid truncation.
- Only AWS SDK (`botocore`) and HTTP (`urllib3`, `requests`) instrumentations are
  enabled by default to minimize cold start impact.
- Set `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=none` to enable all installed
  instrumentations (accept the cold start cost).
- For latency-sensitive functions, use provisioned concurrency to absorb cold starts.
- Layer ARN region must match your function's region -- substitute accordingly.

---

## ECS Sidecar Pattern

Run the ADOT Collector as a sidecar container alongside your application container.
The app sends telemetry to `localhost:4317` (gRPC) or `localhost:4318` (HTTP).

Store custom Collector configuration in SSM Parameter Store and reference it via the
`AOT_CONFIG_CONTENT` environment variable or mount it as a secret.

Production Collector config for ECS:

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  batch:
    timeout: 5s
    send_batch_size: 256
  memory_limiter:
    check_interval: 1s
    limit_mib: 400
    spike_limit_mib: 100
  resourcedetection:
    detectors: [env, ec2, ecs]
    timeout: 5s
    override: false

exporters:
  awsxray:
    region: us-east-1
    indexed_attributes: [otel.resource.service.name]
  awsemf:
    region: us-east-1
    namespace: MyApplication
    log_group_name: /aws/otel/metrics

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [awsxray]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [awsemf]
```

Processor ordering matters -- `memory_limiter` must come first to prevent OOM under
load. The `resourcedetection` processor adds ECS task metadata before `batch` groups
spans for export.

IAM permissions required on the sidecar task role:
- `xray:PutTraceSegments`
- `xray:PutTelemetryRecords`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` (for EMF metrics)

---

## Collector-less Direct Export

As of ADOT Python >= 0.10.0, applications can export directly to AWS OTLP endpoints
without running a Collector process. X-Ray and CloudWatch now accept OTLP natively.

```bash
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf \
OTEL_EXPORTER_OTLP_TRACES_HEADERS="x-aws-xray-sampling-rule=Default" \
opentelemetry-instrument python3 app.py
```

Authentication uses the standard AWS credential chain (env vars, instance profile,
ECS task role). No API keys needed.

**When to use direct export:**
- Simpler deployments where Collector overhead is not justified
- Small services with low trace volume (< 100 spans/second)
- Quick prototyping and development environments

**When NOT to use direct export:**
- Need tail sampling, attribute enrichment, or multi-backend routing (requires Collector)
- High throughput services (Collector provides buffering, retry, and backpressure)
- Need to decouple app deployment from export configuration changes

---

## Migration from aws-xray-sdk

The AWS X-Ray SDK is in maintenance mode. OpenTelemetry is the recommended path for
all new and existing Python services.

| Feature | aws-xray-sdk | OpenTelemetry |
|---------|-------------|---------------|
| Status | Maintenance mode | Active development |
| Propagation | X-Ray header only | W3C + X-Ray + B3 + Jaeger |
| Instrumentation | X-Ray-specific patches | 50+ library instrumentations |
| Export destinations | X-Ray only | Any OTLP-compatible backend |
| Sampling | X-Ray centralized rules | Local + remote + tail sampling |
| Metrics | Not supported | Full metrics pipeline |
| Community | AWS internal | CNCF open-source ecosystem |

Migration steps:

1. Install the ADOT Python distro:
   ```bash
   pip install aws-opentelemetry-distro opentelemetry-propagator-aws-xray
   ```

2. Replace X-Ray SDK imports with OTel equivalents:
   ```python
   # Before
   from aws_xray_sdk.core import xray_recorder, patch_all

   # After
   from opentelemetry import trace
   tracer = trace.get_tracer(__name__)
   ```

3. Replace `@xray_recorder.capture()` with span creation:
   ```python
   # Before
   @xray_recorder.capture("process_order")
   def process_order(order_id): ...

   # After
   def process_order(order_id):
       with tracer.start_as_current_span("process_order"):
           ...
   ```

4. Replace segment/subsegment metadata with span attributes:
   ```python
   # Before
   subsegment.put_metadata("order", order_data)
   subsegment.put_annotation("order_id", order_id)

   # After
   span.set_attribute("order.id", order_id)
   span.set_attribute("order.total", order_data["total"])
   ```

5. Add X-Ray ID generator and propagator for trace continuity with existing
   X-Ray-instrumented services (see X-Ray Integration section above).

6. Test trace continuity across services -- verify that traces initiated by
   X-Ray-instrumented callers correctly propagate to OTel-instrumented callees
   and vice versa.

Reference: `docs.aws.amazon.com/xray/latest/devguide/migrate-xray-to-opentelemetry-python.html`
