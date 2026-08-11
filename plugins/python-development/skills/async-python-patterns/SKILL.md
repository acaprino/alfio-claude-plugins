---
name: async-python-patterns
description: >
  Structure asyncio code: task management, cancellation, rate limiting, blocking calls kept off the event loop.
  TRIGGER WHEN: building async APIs, concurrent or I/O-bound systems needing non-blocking operations, or choosing between asyncio, threading and multiprocessing.
---

# Async Python Patterns

Implement asynchronous Python applications using asyncio, concurrent programming patterns, and async/await for building high-performance, non-blocking systems.

## When to Invoke

- Building async web APIs (FastAPI, aiohttp, Sanic)
- Implementing concurrent I/O operations (database, file, network)
- Creating web scrapers with concurrent requests
- Developing real-time applications (WebSocket servers, chat systems)
- Processing multiple independent tasks simultaneously
- Building microservices with async communication
- Optimizing I/O-bound workloads
- Implementing async background tasks and queues
- Deciding between threading, multiprocessing, and asyncio

## Core Concepts

### Event Loop
- Single-threaded cooperative multitasking
- Schedules coroutines for execution
- Handles I/O operations without blocking
- Manages callbacks and futures

### Coroutines
Functions defined with `async def` that can be paused and resumed.

```python
async def my_coroutine():
    result = await some_async_operation()
    return result
```

### Tasks
Scheduled coroutines that run concurrently on the event loop.

### Futures
Low-level objects representing eventual results of async operations.

### Async Context Managers
Resources that support `async with` for proper cleanup.

### Async Iterators
Objects that support `async for` for iterating over async data sources.

## Quick Start

```python
import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

asyncio.run(main())
```

## Fundamental Patterns

### Basic Async/Await

```python
import asyncio

async def fetch_data(url: str) -> dict:
    await asyncio.sleep(1)  # Simulate I/O
    return {"url": url, "data": "result"}

async def main():
    result = await fetch_data("https://api.example.com")
    print(result)

asyncio.run(main())
```

### Concurrent Execution with gather()

```python
import asyncio
from typing import List

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.5)
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_all_users(user_ids: List[int]) -> List[dict]:
    tasks = [fetch_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)

asyncio.run(fetch_all_users([1, 2, 3, 4, 5]))
```

### Task Creation and Management

```python
import asyncio

async def background_task(name: str, delay: int):
    await asyncio.sleep(delay)
    return f"Result from {name}"

async def main():
    task1 = asyncio.create_task(background_task("Task 1", 2))
    task2 = asyncio.create_task(background_task("Task 2", 1))

    # Do other work while tasks run
    await asyncio.sleep(0.5)

    result1 = await task1
    result2 = await task2
    print(f"Results: {result1}, {result2}")

asyncio.run(main())
```

### Error Handling

```python
import asyncio
from typing import Optional

async def safe_operation(item_id: int) -> Optional[dict]:
    try:
        return await risky_operation(item_id)
    except ValueError as e:
        print(f"Error: {e}")
        return None

async def process_items(item_ids):
    tasks = [safe_operation(iid) for iid in item_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = [r for r in results if r is not None and not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    return successful
```

### Timeout Handling

```python
import asyncio

async def with_timeout():
    try:
        result = await asyncio.wait_for(slow_operation(5), timeout=2.0)
    except asyncio.TimeoutError:
        print("Operation timed out")
```

### Semaphore for Rate Limiting

```python
import asyncio
from typing import List

async def api_call(url: str, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        await asyncio.sleep(0.5)  # Simulate API call
        return {"url": url, "status": 200}

async def rate_limited_requests(urls: List[str], max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [api_call(url, semaphore) for url in urls]
    return await asyncio.gather(*tasks)
```

## Decision Framework

### When to Use asyncio
- I/O-bound tasks (network, database, file)
- Many concurrent connections
- Web servers and API clients
- WebSocket applications

### When to Use threading
- I/O-bound tasks with existing sync libraries
- Simple parallelism needs
- Interfacing with C extensions that release GIL

### When to Use multiprocessing
- CPU-bound tasks (computation, data processing)
- Need true parallelism (bypasses GIL)
- Tasks that don't need shared memory

## Common Pitfalls

### Forgetting await
```python
# Wrong - returns coroutine object
result = async_function()

# Correct
result = await async_function()
```

### Blocking the Event Loop
```python
# Wrong - blocks event loop
import time
async def bad():
    time.sleep(1)  # Blocks!

# Correct
async def good():
    await asyncio.sleep(1)  # Non-blocking
```

### Not Handling Cancellation
```python
async def cancelable_task():
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Perform cleanup
        raise  # Re-raise to propagate
```

### Mixing Sync and Async Code
```python
# Wrong
def sync_function():
    result = await async_function()  # SyntaxError!

# Correct
def sync_function():
    result = asyncio.run(async_function())
```

## Testing Async Code

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await fetch_data("https://api.example.com")
    assert result is not None

@pytest.mark.asyncio
async def test_with_timeout():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_operation(5), timeout=1.0)
```

## Best Practices

1. **Use asyncio.run()** for entry point (Python 3.7+)
2. **Always await coroutines** to execute them
3. **Use gather() for concurrent execution** of multiple tasks
4. **Implement proper error handling** with try/except
5. **Use timeouts** to prevent hanging operations
6. **Pool connections** for better performance
7. **Avoid blocking operations** in async code - use run_in_executor
8. **Use semaphores** for rate limiting
9. **Handle task cancellation** properly
10. **Test async code** with pytest-asyncio

## References

- `references/async-patterns.md` - async context managers, async iterators/generators, producer-consumer pattern, async locks and synchronization, web scraping with aiohttp, async database operations, WebSocket server implementation, connection pools, batch operations, running blocking operations in executors

## Resources

- **Python asyncio documentation**: https://docs.python.org/3/library/asyncio.html
- **aiohttp**: Async HTTP client/server
- **FastAPI**: Modern async web framework
- **asyncpg**: Async PostgreSQL driver
- **motor**: Async MongoDB driver
