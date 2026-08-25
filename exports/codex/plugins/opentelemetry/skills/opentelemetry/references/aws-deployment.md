# AWS Deployment

ADOT (AWS Distro for OpenTelemetry), X-Ray ID generator + propagator, ECS sidecar Collector pattern, Lambda layer, collector-less direct export, and migration from `aws-xray-sdk`. Most surface lives in AWS docs; this file is the production gotchas + the ECS YAML worth keeping local.

## When to use

Deploying an OTel-instrumented Python service on EC2/ECS/EKS/Lambda, or migrating off `aws-xray-sdk`. For the actual instrumentation patterns the AWS-side wraps, see `instrumentation-patterns.md`.

## ADOT in one sentence

`aws-opentelemetry-distro` is **upstream OTel + AWS-bundled components** (`awsxray` + `awsemf` exporters, X-Ray propagator + ID generator, AWS resource detectors, X-Ray remote sampling). It's not a fork.

```bash
pip install aws-opentelemetry-distro opentelemetry-propagator-aws-xray
```

## Gotchas

- **`memory_limiter` MUST be the first processor in every Collector pipeline** -- prevents OOM under load by dropping data when memory pressure spikes. After-the-fact ordering OOMs the sidecar.
- **`resourcedetection: override: false`** so application-set Resource attributes win over Collector-side detection. Default is `true`, which silently overwrites your `service.name` with infrastructure metadata.
- **Lambda Collector extension needs ~hundred-ms tail to flush** after handler returns. Function timeout < 3s = truncated traces. Set timeout ≥ 3s even for fast handlers.
- **Lambda layer ARN is region-specific.** Substitute the right region or you get a generic "layer not found" error at deploy.
- **Default Lambda layer enables only `botocore`/HTTP instrumentations** to minimize cold start. Set `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=none` to enable all -- accept the cold start hit, or use provisioned concurrency.
- **X-Ray ID Generator vs standard W3C trace IDs**: X-Ray accepts W3C IDs since Oct 2023, but the X-Ray ID generator embeds a Unix timestamp in the first 32 bits, which gives you time-based filtering in the X-Ray console. Worth using if X-Ray is your primary backend.
- **`AwsXRayPropagator` reads/writes `X-Amzn-Trace-Id` (`Root=...;Parent=...;Sampled=1`).** Without it, traces broken at any AWS-native hop (ALB → Lambda, API Gateway → Lambda, etc.).
- **IAM permissions are easy to forget for the sidecar role**: `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, plus CloudWatch Logs write perms if you ship EMF metrics. Missing them = silent export failures.
- **Direct export to AWS OTLP endpoints** (`https://xray.us-east-1.amazonaws.com/v1/traces`) authenticates via the standard AWS credential chain -- no API keys. Useful for low-volume or prototyping; not for prod (no buffering/retry/tail sampling).

## Full X-Ray init pattern

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
    id_generator=AwsXRayIdGenerator(),                      # X-Ray timestamp in trace ID
    sampler=ParentBased(TraceIdRatioBased(0.1)),
)
trace.set_tracer_provider(provider)
propagate.set_global_textmap(AwsXRayPropagator())           # X-Ray header support
```

## AWS resource detectors (what each populates)

| Detector | Attributes |
|----------|-----------|
| `AwsEc2ResourceDetector` | `cloud.provider`, `cloud.region`, `cloud.availability_zone`, `cloud.account.id`, `host.id`, `host.type`, `host.name` |
| `AwsEcsResourceDetector` | `aws.ecs.cluster.arn`, `aws.ecs.task.arn`, `aws.ecs.task.family`, `aws.ecs.task.revision`, `aws.ecs.container.arn`, `cloud.region` |
| `AwsEksResourceDetector` | `k8s.cluster.name`, `cloud.provider`, `cloud.platform` |
| `AwsLambdaResourceDetector` | `cloud.provider`, `cloud.region`, `faas.name`, `faas.version`, `faas.instance` |

Since SDK 1.40.0, `OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=*` auto-loads all installed detectors via entry points -- no Python listing.

## Lambda setup (SAM)

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

Layer ARN format: `arn:aws:lambda:<region>:901920570463:layer:aws-otel-python-amd64-ver-<version>:<revision>`. Latest ARN list: https://aws-otel.github.io/docs/getting-started/lambda/lambda-python.

## ECS sidecar Collector YAML (the one worth keeping)

Run the ADOT Collector as a sidecar; the app sends to `localhost:4317` (gRPC) or `localhost:4318` (HTTP).

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  batch:           { timeout: 5s, send_batch_size: 256 }
  memory_limiter:  { check_interval: 1s, limit_mib: 400, spike_limit_mib: 100 }
  resourcedetection: { detectors: [env, ec2, ecs], timeout: 5s, override: false }

exporters:
  awsxray: { region: us-east-1, indexed_attributes: [otel.resource.service.name] }
  awsemf:  { region: us-east-1, namespace: MyApplication, log_group_name: /aws/otel/metrics }

service:
  pipelines:
    traces:
      receivers:  [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters:  [awsxray]
    metrics:
      receivers:  [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters:  [awsemf]
```

Sidecar IAM (the permissions easy to forget):
- `xray:PutTraceSegments`
- `xray:PutTelemetryRecords`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` (EMF metrics)

Store custom config in SSM Parameter Store and reference via `AOT_CONFIG_CONTENT` env var, or mount as a secret.

## Collector-less direct export -- when to skip the sidecar

```bash
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf \
OTEL_EXPORTER_OTLP_TRACES_HEADERS="x-aws-xray-sampling-rule=Default" \
opentelemetry-instrument python3 app.py
```

**Use direct export when**: simple deployments, low volume (< 100 spans/sec), prototyping, dev environments.

**Don't use direct export when**: you need tail sampling, attribute enrichment, multi-backend routing, or buffering/retry under load. Those all require the Collector.

## Migration: `aws-xray-sdk` → OpenTelemetry

X-Ray SDK is in maintenance mode. AWS officially recommends migrating.

1. Install: `pip install aws-opentelemetry-distro opentelemetry-propagator-aws-xray`.
2. Replace decorators:
   - `@xray_recorder.capture("name")` → `with tracer.start_as_current_span("name"):`
3. Replace metadata:
   - `subsegment.put_annotation("k", v)` → `span.set_attribute("k", v)`
   - `subsegment.put_metadata("name", obj)` → multiple `span.set_attribute("name.field", val)` calls
4. Add X-Ray ID generator + propagator (above) for trace continuity with services still on the X-Ray SDK.
5. Test propagation across the boundary -- traces from X-Ray-instrumented callers must reach OTel-instrumented callees AND vice versa.

| Feature | aws-xray-sdk | OpenTelemetry |
|---------|--------------|---------------|
| Status | Maintenance mode | Active |
| Propagation | X-Ray header only | W3C + X-Ray + B3 + Jaeger |
| Instrumentations | X-Ray-specific | 50+ libraries |
| Export destinations | X-Ray only | Any OTLP backend |
| Sampling | X-Ray centralized | Local + remote + tail |
| Metrics | Not supported | Full pipeline |

## Official docs

- ADOT main: https://aws-otel.github.io/
- ADOT Python distro: https://aws-otel.github.io/docs/getting-started/python-sdk
- Lambda layer + ARNs: https://aws-otel.github.io/docs/getting-started/lambda/lambda-python
- ECS sidecar guide: https://aws-otel.github.io/docs/setup/ecs
- X-Ray remote sampling: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html
- X-Ray → OTel migration: https://docs.aws.amazon.com/xray/latest/devguide/migrate-xray-to-opentelemetry-python.html
- ADOT Collector contrib: https://github.com/aws-observability/aws-otel-collector
- AWS X-Ray propagator package: https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/propagator/opentelemetry-propagator-aws-xray
- AWS resource detectors: https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/sdk-extension/opentelemetry-sdk-extension-aws

## Related

- `instrumentation-patterns.md` -- the per-framework setup AWS-side wraps
- `exporters-and-backends.md` -- the multi-backend Collector pipeline pattern
- `production-checklist.md` -- shutdown, kill switch, BSP tuning
- `async-context-propagation.md` -- Lambda + asyncio context gotchas
