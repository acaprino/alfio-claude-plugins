---
name: python-performance-optimization
description: >
  Measure first with cProfile, line_profiler, memory_profiler or py-spy, then fix what the numbers show.
  TRIGGER WHEN: debugging slow Python code, optimizing bottlenecks, cutting memory usage, or improving application performance.
---

# Python Performance Optimization

Profile, analyze, and optimize Python code for better performance - CPU profiling, memory optimization, and implementation best practices.

## When to Invoke

- User reports slow Python code or asks to speed up execution
- Profiling or benchmarking Python applications
- Reducing CPU time, memory consumption, or I/O wait
- Optimizing database queries or data processing pipelines
- Debugging memory leaks or excessive memory usage
- Choosing between parallelization strategies (threading, multiprocessing, async)
- Evaluating algorithmic vs implementation-level improvements

## Core Concepts

### Profiling Types
- **CPU Profiling**: Identify time-consuming functions (cProfile, py-spy)
- **Memory Profiling**: Track memory allocation and leaks (tracemalloc, memory_profiler)
- **Line Profiling**: Profile at line-by-line granularity (line_profiler)
- **Call Graph**: Visualize function call relationships

### Performance Metrics
- **Execution Time**: How long operations take
- **Memory Usage**: Peak and average memory consumption
- **CPU Utilization**: Processor usage patterns
- **I/O Wait**: Time spent on I/O operations

### Optimization Strategies
- **Algorithmic**: Better algorithms and data structures
- **Implementation**: More efficient code patterns
- **Parallelization**: Multi-threading/processing
- **Caching**: Avoid redundant computation
- **Native Extensions**: C/Rust for critical paths

## Quick Start

```python
import time
import timeit

# Simple timing
start = time.time()
result = sum(range(1000000))
print(f"Execution time: {time.time() - start:.4f} seconds")

# Accurate benchmarking with timeit
execution_time = timeit.timeit("sum(range(1000000))", number=100)
print(f"Average time: {execution_time/100:.6f} seconds")
```

## Profiling Tools Summary

### cProfile - CPU Profiling
```bash
python -m cProfile -o output.prof script.py
python -m pstats output.prof
```

### line_profiler - Line-by-Line
```bash
uv add --dev line-profiler    # or: uv tool install line-profiler
kernprof -l -v script.py
```

### memory_profiler - Memory Usage
```bash
uv add --dev memory-profiler
python -m memory_profiler script.py
```

### py-spy - Production Profiling
```bash
uv tool install py-spy
py-spy record -o profile.svg -- python script.py
py-spy top --pid 12345
```

## Key Optimization Patterns

### Data Structure Selection
- **Dict/Set for lookups**: O(1) vs O(n) for list search
- **Generators for large datasets**: Constant memory vs full list
- **__slots__ on classes**: Reduces per-instance memory

### Code-Level Optimizations
- List comprehensions over loops (faster C implementation)
- `str.join()` over `+=` concatenation
- Local variables over global access in hot loops
- Inline simple operations in tight loops
- Built-in functions (implemented in C)

### Caching
- `functools.lru_cache` for expensive pure functions
- `weakref.WeakValueDictionary` for GC-friendly caches

### Parallelization
- **multiprocessing**: CPU-bound tasks, true parallelism
- **threading**: I/O-bound tasks with shared memory
- **asyncio**: I/O-bound tasks with many concurrent operations

### Memory Optimization
- `tracemalloc` for detecting memory leaks (snapshot comparison)
- Iterators over lists for file/stream processing
- `weakref` caches to allow garbage collection

### Database Optimization
- Batch operations with `executemany()` and single commit
- Index frequently queried columns
- Select only needed columns (avoid `SELECT *`)
- Use `EXPLAIN QUERY PLAN` for analysis

## Benchmarking

```python
from functools import wraps
import time

def benchmark(func):
    """Decorator to benchmark function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.6f} seconds")
        return result
    return wrapper
```

For pytest-based benchmarking: `pip install pytest-benchmark`

## Best Practices

1. **Profile before optimizing** - measure to find real bottlenecks
2. **Focus on hot paths** - optimize code that runs most frequently
3. **Use appropriate data structures** - dict for lookups, set for membership
4. **Avoid premature optimization** - clarity first, then optimize
5. **Use built-in functions** - they are implemented in C
6. **Cache expensive computations** - use lru_cache
7. **Batch I/O operations** - reduce system calls
8. **Use generators** for large datasets
9. **Consider NumPy** for numerical operations
10. **Profile production code** - use py-spy for live systems

## Common Pitfalls

- Optimizing without profiling
- Using global variables unnecessarily
- Not using appropriate data structures
- Creating unnecessary copies of data
- Not using connection pooling for databases
- Ignoring algorithmic complexity
- Over-optimizing rare code paths
- Not considering memory usage

## Performance Checklist

- [ ] Profiled code to identify bottlenecks
- [ ] Used appropriate data structures
- [ ] Implemented caching where beneficial
- [ ] Optimized database queries
- [ ] Used generators for large datasets
- [ ] Considered multiprocessing for CPU-bound tasks
- [ ] Used async I/O for I/O-bound tasks
- [ ] Minimized function call overhead in hot loops
- [ ] Checked for memory leaks
- [ ] Benchmarked before and after optimization

## References

- `references/optimization-patterns.md` - detailed code examples for all profiling tools, optimization patterns (list comprehensions, generators, string concat, dict lookups, local vars, function call overhead), advanced optimization (NumPy, lru_cache, __slots__, multiprocessing, async I/O), database optimization, memory leak detection, and benchmarking tools

## Resources

- **cProfile**: Built-in CPU profiler
- **memory_profiler**: Memory usage profiling
- **line_profiler**: Line-by-line profiling
- **py-spy**: Sampling profiler for production
- **NumPy**: High-performance numerical computing
- **Cython**: Compile Python to C
- **PyPy**: Alternative Python interpreter with JIT
