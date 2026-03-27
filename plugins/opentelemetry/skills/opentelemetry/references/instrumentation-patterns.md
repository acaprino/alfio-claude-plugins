# Instrumentation Patterns

Production-tested patterns for instrumenting Python services with OpenTelemetry.
Covers auto-instrumentation, framework-specific setup, async database tracing,
custom decorators, and error handling.

---

## Auto-Instrumentation Setup

Install the distro and OTLP exporter:

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
```

Scan installed packages and install matching instrumentation libraries:

```bash
opentelemetry-bootstrap -a install
```

Wrap your application at startup:

```bash
opentelemetry-instrument uvicorn main:app --host 0.0.0.0 --port 8000
```

This automatically configures a global `TracerProvider`, `MeterProvider`, and W3C
trace-context propagators. Typical overhead is <1% CPU.

### Key Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS` | Comma-separated libs to skip | `"requests,django"` |
| `OTEL_PYTHON_FASTAPI_EXCLUDED_URLS` | Regex for routes to skip | `"health,ready,metrics"` |
| `OTEL_SDK_DISABLED` | Emergency kill switch | `true` |
| `OTEL_SERVICE_NAME` | Service identity | `"order-api"` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Collector address | `"http://collector:4317"` |
| `OTEL_TRACES_SAMPLER` | Sampling strategy | `"parentbased_traceidratio"` |
| `OTEL_TRACES_SAMPLER_ARG` | Sampler parameter | `"0.1"` |

---

## FastAPI Production Setup

Full manual initialization with sampling, resource attributes, and graceful
shutdown via the lifespan protocol:

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({
    "service.name": "order-api",
    "service.version": os.getenv("APP_VERSION", "0.0.0"),
    "deployment.environment": os.getenv("ENVIRONMENT", "production"),
})

sampler = ParentBased(root=TraceIdRatioBased(0.1))
provider = TracerProvider(resource=resource, sampler=sampler)
provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://collector:4317", insecure=True),
    max_queue_size=4096,
    schedule_delay_millis=5000,
))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    provider.shutdown()


app = FastAPI(title="Order API", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(
    app,
    excluded_urls="health,ready,metrics",
)
```

### Request Hooks for Custom Attributes

Attach request-scoped metadata (correlation IDs, tenant headers) to spans:

```python
def server_request_hook(span, scope):
    if span and span.is_recording():
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode()
        if request_id:
            span.set_attribute("http.request_id", request_id)


FastAPIInstrumentor.instrument_app(app, server_request_hook=server_request_hook)
```

---

## Celery Instrumentation

Celery uses `fork()` for worker processes. OTel must be initialized after the
fork to avoid corrupted state in the child process.

**Producer side** (FastAPI app) -- safe to call at module level, no fork:

```python
from opentelemetry.instrumentation.celery import CeleryInstrumentor
CeleryInstrumentor().instrument()
```

**Consumer side** (worker) -- initialize after fork via signal:

```python
from celery import Celery
from celery.signals import worker_process_init
from opentelemetry.sdk.resources import Resource

app = Celery("tasks", broker="redis://localhost:6379/0")


@worker_process_init.connect(weak=False)
def init_worker_tracing(**kwargs):
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.celery import CeleryInstrumentor

    provider = TracerProvider(
        resource=Resource.create({"service.name": "celery-worker"})
    )
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://collector:4317", insecure=True)
    ))
    trace.set_tracer_provider(provider)
    CeleryInstrumentor().instrument()


@app.task(bind=True)
def process_order(self, order_id: str):
    span = trace.get_current_span()
    span.set_attribute("order.id", order_id)
    span.set_attribute("celery.task.retries", self.request.retries)
```

### How Context Propagation Works

1. `before_task_publish` signal -- injects trace context into message headers via `inject()`
2. `task_prerun` signal -- extracts context from headers via `extract()`, creates child span
3. Result: FastAPI -> Celery task -> downstream service appears as a single distributed trace

### Disconnected Traces -- Common Causes

- OTel not initialized inside `worker_process_init` (initialized before fork instead)
- `CeleryInstrumentor` not called on both producer and consumer sides
- Task dispatched outside an active span context (no parent to propagate)

---

## SQLAlchemy Async

```python
from sqlalchemy.ext.asyncio import create_async_engine
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

engine = create_async_engine("postgresql+asyncpg://user:pass@db/orders")
SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)  # NOTE: .sync_engine
```

Important details:
- Pass `.sync_engine` -- the instrumentation patches the synchronous interface that asyncpg wraps internally
- Set `enable_commenter=True` to append trace context as SQL comments, enabling DB log correlation:

```python
SQLAlchemyInstrumentor().instrument(
    engine=engine.sync_engine,
    enable_commenter=True,
)
# Generated SQL: SELECT * FROM orders /* traceparent='00-abc...' */
```

---

## HTTP Client Instrumentation

Instrument outgoing HTTP calls to propagate trace context across service boundaries:

```python
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
HTTPXClientInstrumentor().instrument()  # patches all httpx clients globally
```

Alternative libraries:
- `opentelemetry-instrumentation-requests` -- for `requests` library
- `opentelemetry-instrumentation-aiohttp-client` -- for `aiohttp.ClientSession`

All HTTP client instrumentations automatically inject the `traceparent` header into
outgoing requests, enabling downstream services to continue the trace.

---

## Custom Decorators

### @traced_async with Argument Extraction

Automatically creates spans for async functions and optionally captures function
arguments as span attributes:

```python
import inspect
import functools
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


def traced_async(name, extract_args=None):
    """Decorator that wraps an async function in a span.

    Args:
        name: Span name (e.g. "evaluate_signal").
        extract_args: List of argument names to capture as span attributes.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(func.__module__)
            with tracer.start_as_current_span(name) as span:
                if extract_args and span.is_recording():
                    sig = inspect.signature(func)
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                    for arg_name in extract_args:
                        value = bound.arguments.get(arg_name)
                        if value is not None:
                            span.set_attribute(
                                f"app.{arg_name}",
                                str(value),
                            )
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator


# Usage:
@traced_async("evaluate_signal", extract_args=["symbol", "timeframe"])
async def evaluate_signal(symbol: str, timeframe: str, tick: dict):
    ...
```

### TracedClass Mixin

Automatically wraps all public async methods of a class in traced spans using
`__init_subclass__`:

```python
class TracedClass:
    """Mixin that auto-instruments all public async methods."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, method in inspect.getmembers(
            cls, predicate=inspect.iscoroutinefunction
        ):
            if not name.startswith("_"):
                setattr(
                    cls,
                    name,
                    traced_async(f"{cls.__name__}.{name}")(method),
                )

    def _get_tracer_name(self) -> str:
        return self.__class__.__module__
```

### Sensitive Argument Redaction

Prevent credentials and secrets from leaking into trace backends:

```python
SENSITIVE_KEYS = {"password", "token", "api_key", "secret", "credential"}


def redact_value(key: str, value) -> str:
    """Return '[REDACTED]' if key matches a sensitive pattern."""
    if any(s in key.lower() for s in SENSITIVE_KEYS):
        return "[REDACTED]"
    return str(value)
```

Integrate with `traced_async` by replacing the `str(value)` call with
`redact_value(arg_name, value)` in the argument extraction loop.

---

## Error Handling in Spans

### Distinguishing Infrastructure Errors from Business Logic

```python
from opentelemetry.trace import Status, StatusCode

with tracer.start_as_current_span("process_payment") as span:
    span.set_attribute("payment.amount", payment.amount)
    try:
        result = await gateway.charge(payment)
        span.set_attribute("payment.tx_id", result.tx_id)
        span.set_status(Status(StatusCode.OK))
        return result
    except GatewayTimeoutError as e:
        # Infrastructure error -- record as exception, mark ERROR
        span.record_exception(e, attributes={
            "error.category": "gateway_timeout",
            "payment.gateway": payment.gateway_name,
        })
        span.set_status(Status(StatusCode.ERROR, f"Gateway timeout: {e}"))
        raise HTTPException(status_code=504)
    except InsufficientFundsError as e:
        # Business error -- expected outcome, NOT an error status
        span.add_event("payment_declined", attributes={"reason": str(e)})
        span.set_status(Status(StatusCode.OK))
        return {"status": "declined", "reason": str(e)}
```

### Key Rules

- `record_exception(e)` creates a span event named "exception" with attributes for
  type, message, and stacktrace
- Status transitions: `UNSET` -> `OK` or `UNSET` -> `ERROR`. Once set, status
  never transitions back
- Only 5xx responses should use `StatusCode.ERROR` for HTTP spans. 4xx responses
  are client errors, not server errors
- `start_as_current_span()` defaults: `record_exception=True` and
  `set_status_on_exception=True` -- exceptions are captured automatically unless
  you handle them explicitly
- Business-logic rejections (declined payments, validation failures) should use
  `add_event()` with `StatusCode.OK`, not `record_exception()` with `StatusCode.ERROR`
