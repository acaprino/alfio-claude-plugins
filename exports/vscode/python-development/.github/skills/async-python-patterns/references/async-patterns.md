# Async Python Patterns

Reference for the asyncio patterns you actually use in production: context managers, generators, queues, gather/TaskGroup, cancellation, semaphores, locks, timeouts. Most surface lives in docs.python.org; this file is the gotchas + the decision points.

## When to use

Designing or auditing async Python code. For the architectural opinions (when to use gather vs TaskGroup, when threading wins over asyncio, structured concurrency philosophy), see the SKILL.md.

## Patterns at a glance

| Pattern | Use case | Key construct |
|---------|----------|---------------|
| Async context manager | Resource lifecycle (connection, transaction) | `__aenter__` / `__aexit__` + `async with` |
| Async generator / iterator | Streaming results, paginated APIs | `async def` + `yield` + `async for` |
| Producer-consumer | Decouple ingress from processing | `asyncio.Queue` |
| Fan-out / parallel | N independent tasks, all results | `asyncio.gather` (or TaskGroup, Py 3.11+) |
| Concurrency limit | Throttle parallel work | `asyncio.Semaphore` |
| Race / first-completed | First-to-finish wins | `asyncio.wait(..., return_when=FIRST_COMPLETED)` |
| Timeout | Bound a call's wall time | `async with asyncio.timeout(s)` (Py 3.11+) |
| Backpressure | Producer slows when consumer falls behind | `Queue(maxsize=N)` |

## Gotchas

- **`asyncio.gather` swallows exceptions if `return_exceptions=True`** -- they become elements of the result list. Without that flag, the first exception cancels siblings and re-raises. Pick consciously; the wrong choice means errors disappear into a list.
- **`asyncio.TaskGroup` (Python 3.11+) is the modern replacement for gather** for structured concurrency. It guarantees all spawned tasks finish before exiting the `async with` block, propagates the first exception, and cancels siblings cleanly. Prefer TaskGroup over gather for new code.
- **Don't `asyncio.run()` inside an already-running loop.** That's a `RuntimeError`. From a Jupyter cell or a sync framework with its own loop, use `asyncio.get_event_loop().run_until_complete(...)` or restructure to `await` directly.
- **`asyncio.create_task` returns a Task you must hold a reference to.** The runtime keeps only weak refs -- if you don't store the Task, it can be garbage-collected mid-flight. The fix is `task = asyncio.create_task(...)` (assign).
- **Cancellation propagates through `await` points, not over CPU work.** A coroutine doing pure CPU work for 10 seconds cannot be cancelled until it next awaits. Move CPU work to `loop.run_in_executor()` or yield with `asyncio.sleep(0)`.
- **`asyncio.Queue` is NOT thread-safe.** Use `queue.Queue` (sync) or `janus.Queue` (sync↔async bridge) when crossing thread boundaries.
- **Async generators must be closed explicitly** (`await gen.aclose()`) if you stop iterating early -- otherwise the cleanup `finally` blocks may not run.
- **`asyncio.sleep(0)` yields control without sleeping** -- useful for cooperative scheduling inside CPU-bound loops.
- **`Semaphore` and `Lock` count differently**: `Semaphore(N)` allows N concurrent holders; `Lock` is `Semaphore(1)`. For "at most N parallel HTTP requests", use Semaphore.

## Async context manager (the canonical shape)

```python
class AsyncDatabaseConnection:
    def __init__(self, dsn: str): self.dsn = dsn; self.conn = None
    async def __aenter__(self):
        self.conn = await connect(self.dsn)
        return self.conn
    async def __aexit__(self, *exc):
        await self.conn.close()

async with AsyncDatabaseConnection(dsn) as conn: ...
```

For one-shot wrappers, `contextlib.asynccontextmanager` is shorter:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def db_connection(dsn):
    conn = await connect(dsn)
    try: yield conn
    finally: await conn.close()
```

## Producer-consumer with backpressure

```python
import asyncio

async def producer(q, n):
    for i in range(n):
        await q.put(f"item-{i}")        # blocks if maxsize reached -> backpressure
    await q.put(None)                    # sentinel for shutdown

async def consumer(q):
    while True:
        item = await q.get()
        if item is None:
            q.task_done()
            break
        await process(item)
        q.task_done()

async def main():
    q = asyncio.Queue(maxsize=10)        # bounded -> producer blocks under pressure
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q, 100))
        for _ in range(3):
            tg.create_task(consumer(q))
    await q.join()
```

## Concurrency limit (Semaphore)

```python
sem = asyncio.Semaphore(10)              # at most 10 concurrent

async def fetch(url):
    async with sem:
        return await http.get(url)

results = await asyncio.gather(*[fetch(u) for u in urls])
```

## Timeout (Python 3.11+)

```python
async with asyncio.timeout(5):           # raises TimeoutError after 5s
    result = await slow_api()

# Per-task: asyncio.wait_for(coro, timeout=5)
```

## Cancellation hygiene

```python
task = asyncio.create_task(work())
try:
    result = await asyncio.wait_for(task, timeout=2)
except asyncio.TimeoutError:
    task.cancel()
    try: await task
    except asyncio.CancelledError: pass   # absorb
```

`asyncio.CancelledError` derives from `BaseException` (NOT `Exception`) -- a bare `except Exception` will NOT catch it. This is intentional.

## CPU-bound work (don't block the loop)

```python
loop = asyncio.get_running_loop()
result = await loop.run_in_executor(None, cpu_intensive_function, arg)
```

For `to_thread` (Python 3.9+, simpler):
```python
result = await asyncio.to_thread(cpu_intensive_function, arg)
```

`asyncio.to_thread` runs in the default ThreadPoolExecutor -- fine for I/O-blocking calls (legacy sync libraries) and small CPU work. For true CPU-bound, use `ProcessPoolExecutor`.

## Async iteration

```python
async def async_range(start, end, delay=0.1):
    for i in range(start, end):
        await asyncio.sleep(delay)
        yield i

async for n in async_range(1, 5): ...
```

## Race / first-completed

```python
done, pending = await asyncio.wait(
    [asyncio.create_task(slow_a()), asyncio.create_task(slow_b())],
    return_when=asyncio.FIRST_COMPLETED,
)
for t in pending: t.cancel()             # cancel losers
result = next(iter(done)).result()
```

## Official docs

- asyncio module: https://docs.python.org/3/library/asyncio.html
- `asyncio.TaskGroup` (Py 3.11+): https://docs.python.org/3/library/asyncio-task.html#task-groups
- `asyncio.timeout` (Py 3.11+): https://docs.python.org/3/library/asyncio-task.html#asyncio.timeout
- `asyncio.to_thread`: https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
- Cancellation semantics: https://docs.python.org/3/library/asyncio-task.html#task-cancellation
- Async iterators / generators (PEP 525): https://peps.python.org/pep-0525/
- `contextlib.asynccontextmanager`: https://docs.python.org/3/library/contextlib.html#contextlib.asynccontextmanager
- Structured concurrency in Python (Trio's influence): https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/

## Related

- `async-python-patterns/SKILL.md` -- the architectural opinions (TaskGroup over gather, when threading wins, structured concurrency)
- `python-tdd/references/framework-config.md` -- pytest-asyncio configuration
- `python-performance-optimization` skill -- profiling async code
