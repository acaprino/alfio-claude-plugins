#!/usr/bin/env python3
"""Benchmark performance changes between code versions.

This script runs performance benchmarks on before/after versions of code
to ensure refactoring doesn't introduce significant performance regression.

Usage:
    python benchmark_changes.py <before_file> <after_file> <test_module> [--threshold 10]
"""

import argparse
import importlib.util
import sys
import timeit
from pathlib import Path
from typing import Dict, Any, Callable, List
import json


def load_module_from_file(file_path: Path, module_name: str):
    """Dynamically load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def discover_benchmarkable_functions(module) -> List[tuple[str, Callable]]:
    """Discover public functions in a module that can be benchmarked.

    Returns list of (name, function) tuples.
    """
    functions = []

    for name in dir(module):
        if name.startswith('_'):
            continue

        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, '__module__') and obj.__module__ == module.__name__:
            functions.append((name, obj))

    return functions


def create_benchmark_wrapper(func: Callable, test_module) -> Callable:
    """Create a benchmark wrapper that provides test data from test module.

    The test module should define benchmark_data_<function_name> or
    benchmark_setup_<function_name> functions.
    """
    func_name = func.__name__

    # Try to get benchmark data from test module
    data_provider_name = f"benchmark_data_{func_name}"
    setup_provider_name = f"benchmark_setup_{func_name}"

    if hasattr(test_module, data_provider_name):
        data_provider = getattr(test_module, data_provider_name)
        return lambda: func(*data_provider())

    elif hasattr(test_module, setup_provider_name):
        setup_provider = getattr(test_module, setup_provider_name)
        setup_data = setup_provider()

        if isinstance(setup_data, dict):
            return lambda: func(**setup_data)
        elif isinstance(setup_data, (list, tuple)):
            return lambda: func(*setup_data)
        else:
            return lambda: func(setup_data)

    else:
        # Try calling with no arguments
        return lambda: func()


def benchmark_function(func: Callable, number: int = 1000, repeat: int = 5) -> Dict[str, float]:
    """Benchmark a function and return timing statistics.

    Args:
        func: Function to benchmark
        number: Number of executions per timing
        repeat: Number of times to repeat the timing

    Returns:
        Dict with 'min', 'max', 'mean', 'median' times in seconds
    """
    try:
        # Warm up
        func()

        # Run benchmark
        times = timeit.repeat(func, number=number, repeat=repeat)

        # Convert to per-execution times
        times = [t / number for t in times]

        return {
            'min': min(times),
            'max': max(times),
            'mean': sum(times) / len(times),
            'median': sorted(times)[len(times) // 2]
        }

    except Exception as e:
        print(f"  Error benchmarking function: {e}", file=sys.stderr)
        return None


def compare_benchmarks(
    before_results: Dict[str, float],
    after_results: Dict[str, float],
    threshold_pct: float = 10.0
) -> Dict[str, Any]:
    """Compare benchmark results and determine if there's significant regression.

    Args:
        before_results: Timing results from before version
        after_results: Timing results from after version
        threshold_pct: Acceptable performance regression threshold (%)

    Returns:
        Dict with comparison data and regression status
    """
    if before_results is None or after_results is None:
        return {
            'regression': None,
            'error': 'Benchmark failed'
        }

    # Use median time for comparison (more stable than mean)
    before_time = before_results['median']
    after_time = after_results['median']

    # Calculate percentage change
    if before_time > 0:
        pct_change = ((after_time - before_time) / before_time) * 100
    else:
        pct_change = 0.0

    # Determine if there's significant regression
    has_regression = pct_change > threshold_pct

    return {
        'before_median': before_time,
        'after_median': after_time,
        'pct_change': round(pct_change, 2),
        'threshold_pct': threshold_pct,
        'regression': has_regression,
        'faster': pct_change < 0
    }


def print_benchmark_results(
    func_name: str,
    before_results: Dict[str, float],
    after_results: Dict[str, float],
    comparison: Dict[str, Any]
):
    """Print benchmark results for a single function."""
    print(f"\n  Function: {func_name}")
    print(f"  {'─'*66}")

    if comparison.get('error'):
        print(f"  ✗ {comparison['error']}")
        return

    before_time = comparison['before_median']
    after_time = comparison['after_median']
    pct_change = comparison['pct_change']
    threshold = comparison['threshold_pct']

    # Format times nicely
    def format_time(t):
        if t < 1e-6:
            return f"{t*1e9:.2f} ns"
        elif t < 1e-3:
            return f"{t*1e6:.2f} µs"
        elif t < 1:
            return f"{t*1e3:.2f} ms"
        else:
            return f"{t:.2f} s"

    print(f"  Before: {format_time(before_time)} (median)")
    print(f"  After:  {format_time(after_time)} (median)")

    if comparison['faster']:
        print(f"  Change: {pct_change:+.1f}% ✓ FASTER")
    elif comparison['regression']:
        print(f"  Change: {pct_change:+.1f}% ✗ REGRESSION (threshold: {threshold}%)")
    else:
        print(f"  Change: {pct_change:+.1f}% ✓ Within threshold")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark performance changes between code versions"
    )
    parser.add_argument("before_file", type=Path, help="Path to file before refactoring")
    parser.add_argument("after_file", type=Path, help="Path to file after refactoring")
    parser.add_argument("test_module", type=Path, help="Path to test/benchmark data module")
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Performance regression threshold in percent (default: 10)"
    )
    parser.add_argument(
        "--number",
        type=int,
        default=1000,
        help="Number of executions per timing (default: 1000)"
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=5,
        help="Number of times to repeat timing (default: 5)"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    # Validate files
    for file_path in [args.before_file, args.after_file, args.test_module]:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        if not file_path.suffix == '.py':
            print(f"Error: File must be a Python file (.py): {file_path}", file=sys.stderr)
            sys.exit(1)

    # Load modules
    try:
        before_module = load_module_from_file(args.before_file, "before_module")
        after_module = load_module_from_file(args.after_file, "after_module")
        test_module = load_module_from_file(args.test_module, "test_module")
    except Exception as e:
        print(f"Error loading modules: {e}", file=sys.stderr)
        sys.exit(1)

    # Discover functions to benchmark
    before_functions = discover_benchmarkable_functions(before_module)
    after_functions = discover_benchmarkable_functions(after_module)

    # Find common functions
    before_names = {name for name, _ in before_functions}
    after_names = {name for name, _ in after_functions}
    common_names = before_names & after_names

    if not common_names:
        print("Error: No common functions found between before and after versions", file=sys.stderr)
        sys.exit(1)

    # Run benchmarks
    results = {}
    regressions_found = False

    if not args.json:
        print(f"\n{'='*70}")
        print(f"Performance Benchmark Comparison")
        print(f"{'='*70}")
        print(f"\nBenchmarking {len(common_names)} function(s)...")

    for func_name in sorted(common_names):
        # Get functions
        before_func = next(f for name, f in before_functions if name == func_name)
        after_func = next(f for name, f in after_functions if name == func_name)

        # Create benchmark wrappers
        try:
            before_wrapper = create_benchmark_wrapper(before_func, test_module)
            after_wrapper = create_benchmark_wrapper(after_func, test_module)
        except Exception as e:
            print(f"\n  Error creating benchmark for {func_name}: {e}", file=sys.stderr)
            continue

        # Run benchmarks
        before_results = benchmark_function(before_wrapper, args.number, args.repeat)
        after_results = benchmark_function(after_wrapper, args.number, args.repeat)

        # Compare
        comparison = compare_benchmarks(before_results, after_results, args.threshold)

        results[func_name] = {
            'before': before_results,
            'after': after_results,
            'comparison': comparison
        }

        if not args.json:
            print_benchmark_results(func_name, before_results, after_results, comparison)

        if comparison.get('regression'):
            regressions_found = True

    # Summary
    if not args.json:
        print(f"\n{'='*70}")
        print(f"Summary:")
        print(f"{'='*70}")

        total = len(results)
        faster = sum(1 for r in results.values() if r['comparison'].get('faster'))
        regressed = sum(1 for r in results.values() if r['comparison'].get('regression'))
        within_threshold = total - faster - regressed

        print(f"  Total functions: {total}")
        print(f"  Faster: {faster}")
        print(f"  Within threshold: {within_threshold}")
        print(f"  Regressions: {regressed}")

        if regressions_found:
            print(f"\n✗ Performance regressions detected!")
            sys.exit(1)
        else:
            print(f"\n✓ No significant performance regressions")

    else:
        print(json.dumps(results, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
