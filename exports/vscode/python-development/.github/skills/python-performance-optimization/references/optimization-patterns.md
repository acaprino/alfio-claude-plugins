# Python Performance Optimization Patterns

The profilers, the optimization patterns, and the gotchas. Per-tool walkthroughs live in tool READMEs and `docs.python.org/3/library/profile.html`; this file is the **decision tree** + **the gotchas** + **the patterns that move the needle**.

## When to use

Diagnosing a slow Python program, picking the right profiler, or choosing between optimization patterns (caching, vectorization, C extensions). For the architectural decision tree (when to even bother optimizing), see `python-performance-optimization/SKILL.md`.

## Profiler decision tree (the only thing to memorize)

| Question | Tool |
|----------|------|
| **Where is time spent across the program?** | `cProfile` (function-level CPU time) |
| **Which line is slow inside a hot function?** | `line_profiler` (`@profile` decorator + `kernprof -l -v`) |
| **Where is memory allocated?** | `tracemalloc` (stdlib) or `memory_profiler` (`@profile` for memory) |
| **Why is GC running so often?** | `objgraph` (object reference cycles) or `gc.get_stats()` |
| **What's blocking the event loop?** | `asyncio` debug mode (`PYTHONASYNCIODEBUG=1`) |
| **Per-line micro-bench in CI** | `pytest-benchmark` (statistical, comparable across commits) |
| **Quick A/B for a snippet** | `timeit` (`python -m timeit "..."`) or `%timeit` in IPython/Jupyter |
| **Hot path in production with low overhead** | `py-spy` (sampling profiler, attaches to running process) |
| **Stack trace flame graph** | `py-spy record -o profile.svg --pid <pid>` |

## Gotchas

- **`cProfile` overhead is significant** -- a function profiled at 100ns may show 500ns. Useful for *relative* comparisons, not absolute timings.
- **`timeit` runs the code N times** in a loop; the default `-n` auto-scales until you get a meaningful measurement. Don't trust a single run; run 5+ and report min (not mean -- min eliminates noise from OS scheduling).
- **`@profile` is line_profiler's decorator** -- it does NOT exist in Python by default. The script ONLY runs under `kernprof`; running `python script.py` directly fails with `NameError: name 'profile' is not defined`. Workaround: `from line_profiler import LineProfiler` in code.
- **`memory_profiler` requires `psutil`** as a transitive dep. On macOS Apple Silicon, install with `pip install psutil --no-binary :all:` if the wheel is incompatible.
- **`tracemalloc` snapshot diff is the right way** to find memory leaks: `snapshot1 = tracemalloc.take_snapshot()`, do work, `snapshot2 = ...`, `snapshot2.compare_to(snapshot1, 'lineno')`. NOT a single snapshot.
- **GC tuning rarely helps** unless you're allocating millions of objects. `gc.set_threshold(700, 10, 10)` (defaults are higher) for write-heavy workloads. `gc.disable()` only for short-lived processes that don't need it.
- **GIL is the silent ceiling for CPU-bound threads.** `threading` does not give parallelism for pure-Python CPU work. Use `multiprocessing` or `concurrent.futures.ProcessPoolExecutor`. `asyncio` doesn't help either -- it's single-threaded.
- **`functools.lru_cache(maxsize=None)` for pure functions only.** Methods on instances will keep the instance alive forever (memory leak). For methods, use `functools.cache` per instance via descriptor pattern, or keep the instance lifetime bounded.
- **String concatenation in a loop is O(n²)** -- use `"".join(parts)` instead. Surprises people; it's the canonical case where Python's "obvious" code is wrong.
- **List comprehension > `for` + `.append()`** by ~30%. Generator expression < list comprehension when you don't need the whole result in memory.
- **`numpy` for array math, NOT `for` loops.** A vectorized `(arr1 + arr2) ** 2` is 100× faster than the equivalent Python loop. Same for pandas: `df['col'].apply(func)` is slow; use vector ops or `df.eval()`.
- **`async`/`await` doesn't make CPU work faster** -- it only helps with I/O concurrency. CPU-bound work in an async function blocks the event loop.

## Profiling recipes (the few worth memorizing)

### cProfile -- one-shot

```bash
python -m cProfile -o output.prof script.py
python -m pstats output.prof
# At the prompt:
sort cumtime
stats 20
```

In code:
```python
import cProfile, pstats
from pstats import SortKey

profiler = cProfile.Profile()
profiler.enable()
main()
profiler.disable()

stats = pstats.Stats(profiler).sort_stats(SortKey.CUMULATIVE)
stats.print_stats(20)
```

### line_profiler -- per-line breakdown

```bash
pip install line_profiler
# Annotate the function with @profile (no import; kernprof injects it)
kernprof -l -v script.py
```

### memory_profiler -- per-line memory

```bash
pip install memory_profiler psutil
# Annotate with @profile (memory variant)
python -m memory_profiler script.py
```

### tracemalloc -- find leaks

```python
import tracemalloc
tracemalloc.start()
snap1 = tracemalloc.take_snapshot()

do_work()

snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, 'lineno')[:10]:
    print(stat)
```

### py-spy -- production sampling

```bash
pip install py-spy
sudo py-spy top --pid <PID>                  # live top-like view
sudo py-spy record -o profile.svg --pid <PID> --duration 30
```

py-spy is the right tool when you can't restart the process (live prod debugging). Sub-1% overhead.

### timeit -- micro-bench

```bash
python -m timeit -n 10000 -s "import json" "json.dumps({'a': 1})"
```

In IPython/Jupyter: `%timeit json.dumps({'a': 1})` (single line) or `%%timeit` (cell).

## Optimization patterns (in order of typical ROI)

1. **Algorithmic** -- Profile first, then check Big-O. A `O(n²)` loop replaced by a `dict` lookup beats every micro-optimization.
2. **Vectorization** -- numpy / pandas for numeric work. 10-1000× speedup over Python loops.
3. **Caching** -- `functools.lru_cache` for pure functions, Redis / dict for cross-call state. Memoize expensive deterministic work.
4. **Lazy evaluation** -- generators (`yield`) instead of lists when you process one item at a time. Saves memory and often time (early exit).
5. **Concurrency** -- `asyncio` for I/O-bound, `ProcessPoolExecutor` for CPU-bound. Threading helps only if the bottleneck is in C extensions that release the GIL.
6. **Native code** -- Cython, mypyc, Numba, or PyO3 (Rust) for hot loops. 10-100× speedup but adds build complexity.
7. **JIT** -- PyPy for compute-heavy pure-Python code. Drop-in for CPython in many cases; check compatibility.

## Anti-patterns (the things that look smart but aren't)

- **`__slots__` for every class** -- saves a few KB per instance but makes inheritance + serialization harder. Use only for classes instantiated millions of times.
- **Premature `lru_cache` decoration** -- caching everything pollutes memory and complicates lifetime reasoning. Profile first.
- **Manual loop unrolling in Python** -- the interpreter doesn't benefit; readability suffers.
- **`is` for equality of small ints / strings** -- relies on CPython interning, breaks portability and is brittle.
- **Replacing `dict` with `OrderedDict`** in modern Python -- unnecessary since 3.7 (ordering is guaranteed).
- **Using `multiprocessing` for tasks that take < 1 second total** -- fork overhead dominates.

## When to reach for native code

Threshold heuristic: if profiling shows **a single function consuming > 30% of total time AND vectorization isn't an option**, consider:

| Tool | When |
|------|------|
| **Cython** | C-like syntax, gradual typing, mature ecosystem |
| **mypyc** | Compile typed Python directly; less invasive than Cython |
| **Numba** | NumPy-heavy code, GPU support via CUDA |
| **PyO3 (Rust)** | New extensions, modern toolchain, memory safety |
| **C/C++ + ctypes** | Existing C library you want to wrap |

## Official docs

- `cProfile` + `pstats`: https://docs.python.org/3/library/profile.html
- `tracemalloc`: https://docs.python.org/3/library/tracemalloc.html
- `gc` module: https://docs.python.org/3/library/gc.html
- `timeit`: https://docs.python.org/3/library/timeit.html
- `functools.lru_cache`: https://docs.python.org/3/library/functools.html#functools.lru_cache
- `concurrent.futures`: https://docs.python.org/3/library/concurrent.futures.html
- line_profiler: https://github.com/pyutils/line_profiler
- memory_profiler: https://github.com/pythonprofilers/memory_profiler
- py-spy: https://github.com/benfred/py-spy
- pytest-benchmark: https://pytest-benchmark.readthedocs.io/
- Cython: https://cython.org/
- mypyc: https://mypyc.readthedocs.io/
- Numba: https://numba.pydata.org/
- PyO3: https://pyo3.rs/

## Related

- `python-performance-optimization/SKILL.md` -- decision tree (when to optimize, when not)
- `async-python-patterns/references/async-patterns.md` -- when async genuinely helps and when it doesn't
- `python-refactor/references/cognitive_complexity_guide.md` -- complexity refactoring (often resolves perf as a side effect)
