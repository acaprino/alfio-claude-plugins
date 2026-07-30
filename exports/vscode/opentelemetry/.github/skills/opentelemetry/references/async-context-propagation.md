# Async Context Propagation

How OpenTelemetry context propagation works in async Python -- the critical patterns that determine whether distributed traces stay connected or silently break.

## How contextvars Works with asyncio

OpenTelemetry stores the current span and baggage in `contextvars.ContextVar` instances, managed by the `ContextVarsRuntimeContext` provider. Every call to `tracer.start_as_current_span()` creates an **immutable context snapshot** -- write operations produce a NEW context that inherits from the current one, so nested modifications never corrupt the parent context.

This copy-on-write immutability is what makes OTel safe in async code. Each coroutine or task sees a consistent view of the active span without locks or coordination.

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def outer():
    with tracer.start_as_current_span("outer") as outer_span:
        # Context now holds outer_span as current
        await inner()
        # outer_span is still current here -- inner() cannot corrupt it
        current = trace.get_current_span()
        assert current == outer_span

async def inner():
    with tracer.start_as_current_span("inner") as inner_span:
        # A NEW context was created with inner_span as current
        # The outer context is untouched
        current = trace.get_current_span()
        assert current == inner_span
```

Key internals:
- `opentelemetry.context` module wraps `contextvars` -- do not manipulate `ContextVar` directly
- `attach()` / `detach()` manage the context stack when not using `start_as_current_span`
- Each `ContextVar` is scoped per-task in asyncio -- no cross-task leakage

## asyncio.create_task -- The Copy Semantics

`asyncio.create_task()` performs a **shallow copy** of all `contextvars` at **task creation time** -- not at coroutine creation time. This distinction determines whether spawned tasks inherit the correct parent span.

```python
import asyncio
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_item(item):
    # This span's parent depends on what was current when create_task() was called
    with tracer.start_as_current_span(f"process_{item}"):
        await asyncio.sleep(0.1)

# CORRECT: tasks created INSIDE the span inherit context
async def handle_request_correct(items):
    with tracer.start_as_current_span("handle_request"):
        # create_task copies context HERE -- "handle_request" is current
        tasks = [asyncio.create_task(process_item(item)) for item in items]
        return await asyncio.gather(*tasks)
        # Result: process_item spans are children of handle_request

# WRONG: coroutines created before span, tasks miss context
async def handle_request_wrong(items):
    coros = [process_item(item) for item in items]
    with tracer.start_as_current_span("handle_request"):
        # create_task copies context HERE -- but "handle_request" IS current
        # However, the coroutines were created outside the span...
        # Actually the real issue is when create_task is called OUTSIDE the span:
        tasks = [asyncio.create_task(coro) for coro in coros]
        return await asyncio.gather(*tasks)

# ACTUALLY WRONG: create_task called OUTSIDE the span
async def handle_request_broken(items):
    tasks = [asyncio.create_task(process_item(item)) for item in items]
    with tracer.start_as_current_span("handle_request"):
        # Too late -- tasks already copied context WITHOUT "handle_request"
        return await asyncio.gather(*tasks)
        # Result: process_item spans are orphans or attached to wrong parent
```

Rule: always call `create_task()` **inside** the `with tracer.start_as_current_span()` block.

## Plain await vs create_task

When you `await` a coroutine directly (without `create_task`), **no context copy occurs**. The coroutine runs inline in the caller's context and inherits whatever span is current.

```python
async def handler():
    with tracer.start_as_current_span("handler"):
        # No copy -- fetch_data runs in handler's context
        result = await fetch_data()  # "handler" is the parent span
        return result

async def fetch_data():
    with tracer.start_as_current_span("fetch_data"):
        # Parent is "handler" -- always correct with plain await
        return await some_client.get("/data")
```

This means:
- `await some_coro()` -- always inherits current span, no special handling needed
- `asyncio.create_task(some_coro())` -- copies context at creation, ordering matters
- `asyncio.gather(coro1(), coro2())` without `create_task` -- runs coroutines sequentially in caller context (gather wraps them in tasks internally, copying context at that point)

## asyncio.TaskGroup (Python 3.11+)

`TaskGroup.create_task()` follows the same copy-at-creation semantics as `asyncio.create_task()`. Context propagates correctly as long as `create_task` is called within the span scope.

```python
import asyncio
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def child_work(name: str):
    with tracer.start_as_current_span(f"child_{name}"):
        await asyncio.sleep(0.1)

# CORRECT: create_task inside span scope
async def process_batch():
    with tracer.start_as_current_span("parent"):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(child_work("a"))  # inherits "parent" span
            tg.create_task(child_work("b"))  # inherits "parent" span
            tg.create_task(child_work("c"))  # inherits "parent" span
    # All child spans are children of "parent"

# ALSO CORRECT: span wraps the entire TaskGroup
async def process_batch_alt():
    async with asyncio.TaskGroup() as tg:
        with tracer.start_as_current_span("parent"):
            tg.create_task(child_work("a"))  # inherits "parent"
            tg.create_task(child_work("b"))  # inherits "parent"
```

`TaskGroup` also provides structured concurrency -- if any task raises, all siblings are cancelled. This pairs well with OTel because exception recording happens automatically via `start_as_current_span`.

## The Thread Boundary Trap

This is the **#1 production tracing failure**. `loop.run_in_executor()` does NOT propagate `contextvars` to the thread pool. Every span created inside the executor becomes an orphan trace -- silently disconnected from the parent.

```python
import asyncio
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def blocking_db_query():
    # This span has NO parent -- orphaned trace
    with tracer.start_as_current_span("db_query"):
        return run_sync_query()

async def handler():
    with tracer.start_as_current_span("handler"):
        loop = asyncio.get_event_loop()
        # BROKEN: context is NOT copied to the executor thread
        result = await loop.run_in_executor(None, blocking_db_query)
```

### Fix: TracedThreadPoolExecutor

Drop-in replacement that captures and propagates context to worker threads.

```python
import contextvars
from concurrent.futures import ThreadPoolExecutor

class TracedThreadPoolExecutor(ThreadPoolExecutor):
    """ThreadPoolExecutor that propagates OTel context to worker threads."""

    def submit(self, fn, *args, **kwargs):
        ctx = contextvars.copy_context()
        return super().submit(ctx.run, fn, *args, **kwargs)

# Usage -- set as the default executor for the event loop
executor = TracedThreadPoolExecutor(max_workers=10)
loop = asyncio.get_event_loop()
loop.set_default_executor(executor)
```

### Fix: One-off run_in_executor calls

When you cannot replace the default executor, wrap individual calls.

```python
async def handler():
    with tracer.start_as_current_span("handler"):
        ctx = contextvars.copy_context()
        loop = asyncio.get_event_loop()
        # ctx.run executes blocking_db_query inside the captured context
        result = await loop.run_in_executor(None, ctx.run, blocking_db_query)
        # "db_query" span inside blocking_db_query is now a child of "handler"
```

## Python 3.12+ asyncio.to_thread

`asyncio.to_thread()` automatically propagates `contextvars` to the spawned thread -- it is the preferred alternative to `run_in_executor` on Python 3.12+.

```python
import asyncio

async def handler():
    with tracer.start_as_current_span("handler"):
        # Context automatically propagated -- no manual copy needed
        result = await asyncio.to_thread(blocking_db_query)
        # "db_query" span is correctly parented to "handler"
```

For Python 3.9-3.11, `asyncio.to_thread()` exists but does **not** propagate `contextvars`. Use `TracedThreadPoolExecutor` or `opentelemetry-instrumentation-threading` on those versions.

## opentelemetry-instrumentation-threading

Automatic context propagation for all thread-based concurrency -- no custom wrappers needed.

```bash
pip install opentelemetry-instrumentation-threading
```

Activation options:

```python
# Option 1: Auto-instrument via CLI
# opentelemetry-instrument python app.py

# Option 2: Manual instrumentation
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
ThreadingInstrumentor().instrument()
```

What it patches:
- `threading.Thread` -- context copied when `start()` is called
- `threading.Timer` -- context copied when `start()` is called
- `concurrent.futures.ThreadPoolExecutor` -- context copied when `submit()` is called

Patches at module level, so all thread creation in the process gets context propagation. This makes `TracedThreadPoolExecutor` unnecessary when the instrumentor is active.

## Process Boundaries (Celery, Gunicorn, multiprocessing)

`fork()` copies memory, but `BatchSpanProcessor`'s background export thread does NOT survive the fork. This causes silent span loss -- spans are created and queued but never exported.

### Celery

Init OTel AFTER fork via `worker_process_init` signal. This is the most common production failure with Celery + OTel.

```python
from celery import Celery
from celery.signals import worker_process_init
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.celery import CeleryInstrumentor

resource = Resource.create({"service.name": "my-worker"})

@worker_process_init.connect(weak=False)
def init_worker_tracing(**kwargs):
    """Initialize OTel AFTER fork -- BatchSpanProcessor thread is created fresh."""
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    CeleryInstrumentor().instrument()

app = Celery("tasks", broker="redis://localhost:6379")
```

Critical: `CeleryInstrumentor` must be active on BOTH the producer (web app publishing tasks) and the consumer (worker executing tasks). The producer injects trace context into Celery message headers; the consumer extracts it.

### Gunicorn

```python
# gunicorn.conf.py
def post_fork(server, worker):
    """Initialize OTel after Gunicorn forks worker processes."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
```

Alternative: use `--preload` flag with careful init ordering -- load app code first, init OTel in each worker.

### multiprocessing.Process

Init OTel inside the target function, never before `spawn()` or `fork()`.

```python
import multiprocessing
from opentelemetry import trace

def worker_target(task_data):
    # Init OTel HERE -- inside the child process
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    with trace.get_tracer(__name__).start_as_current_span("worker"):
        process_data(task_data)

# Parent process
p = multiprocessing.Process(target=worker_target, args=(data,))
p.start()
```

## Debugging Context Loss

When traces appear disconnected -- spans show up as separate root traces instead of a connected tree:

1. **Check span scope** -- are spans created inside or outside the active span's `with` block?
2. **Check thread boundaries** -- any `run_in_executor`, `ThreadPoolExecutor.submit`, or `threading.Thread` without context copying?
3. **Check fork boundaries** -- Celery `worker_process_init`, Gunicorn `post_fork`, or `multiprocessing` without post-fork OTel init?
4. **Check CeleryInstrumentor** -- must be active on BOTH producer and consumer sides
5. **Inspect active context** -- use `trace.get_current_span().get_span_context()` to check `trace_id` and `span_id` at any point
6. **Enable debug logging** -- `OTEL_LOG_LEVEL=debug` shows context propagation events and export activity

```python
# Diagnostic helper -- print current context at any point
from opentelemetry import trace

def debug_context(label: str):
    span = trace.get_current_span()
    ctx = span.get_span_context()
    print(f"[{label}] trace_id={ctx.trace_id:032x} span_id={ctx.span_id:016x} "
          f"is_valid={ctx.is_valid} is_remote={ctx.is_remote}")
```

## Summary Table

| Mechanism | Context propagates? | Fix if not |
|-----------|---------------------|------------|
| `await coro()` | Yes (same context) | N/A |
| `asyncio.create_task()` | Yes (copy at creation) | Call `create_task` inside span |
| `asyncio.TaskGroup.create_task()` | Yes (copy at creation) | Call `create_task` inside span |
| `loop.run_in_executor()` | **No** | `TracedThreadPoolExecutor` or `contextvars.copy_context()` |
| `asyncio.to_thread()` (3.12+) | Yes | N/A |
| `asyncio.to_thread()` (3.9-3.11) | **No** | `TracedThreadPoolExecutor` or instrumentation-threading |
| `threading.Thread` | **No** | `opentelemetry-instrumentation-threading` or manual copy |
| `concurrent.futures.ThreadPoolExecutor` | **No** | `TracedThreadPoolExecutor` or instrumentation-threading |
| `multiprocessing.Process` | **No** (fork) | Init OTel inside child process |
| Celery task | Yes (via `CeleryInstrumentor`) | `worker_process_init` + instrument both sides |
| Gunicorn workers | **No** (fork) | `post_fork` hook or `--preload` |
