#!/usr/bin/env python3
"""Compare code metrics before and after refactoring.

This script compares complexity and documentation metrics between two
versions of a file to quantify refactoring improvements.

Usage:
    python compare_metrics.py <before_file> <after_file> [--json]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Import our other metric scripts
import measure_complexity
import check_documentation


def calculate_percentage_change(before: float, after: float) -> float:
    """Calculate percentage change (positive = improvement for metrics we want to decrease)."""
    if before == 0:
        return 0.0
    # For metrics we want to decrease (complexity, length), negative change is good
    return round(((before - after) / before) * 100, 1)


def calculate_percentage_increase(before: float, after: float) -> float:
    """Calculate percentage increase (positive = improvement for metrics we want to increase)."""
    if before == 0:
        if after > 0:
            return 100.0
        return 0.0
    # For metrics we want to increase (coverage), positive change is good
    return round(((after - before) / before) * 100, 1)


def compare_complexity(before_file: Path, after_file: Path) -> Dict[str, Any]:
    """Compare complexity metrics between two files."""
    before_metrics = measure_complexity.analyze_file(before_file)
    after_metrics = measure_complexity.analyze_file(after_file)

    comparison = {
        'avg_complexity': {
            'before': before_metrics.avg_complexity,
            'after': after_metrics.avg_complexity,
            'change': calculate_percentage_change(
                before_metrics.avg_complexity,
                after_metrics.avg_complexity
            ),
            'improved': after_metrics.avg_complexity <= before_metrics.avg_complexity
        },
        'max_complexity': {
            'before': before_metrics.max_complexity,
            'after': after_metrics.max_complexity,
            'change': calculate_percentage_change(
                before_metrics.max_complexity,
                after_metrics.max_complexity
            ),
            'improved': after_metrics.max_complexity <= before_metrics.max_complexity
        },
        'avg_length': {
            'before': before_metrics.avg_length,
            'after': after_metrics.avg_length,
            'change': calculate_percentage_change(
                before_metrics.avg_length,
                after_metrics.avg_length
            ),
            'improved': after_metrics.avg_length <= before_metrics.avg_length
        },
        'max_length': {
            'before': before_metrics.max_length,
            'after': after_metrics.max_length,
            'change': calculate_percentage_change(
                before_metrics.max_length,
                after_metrics.max_length
            ),
            'improved': after_metrics.max_length <= before_metrics.max_length
        },
        'avg_nesting': {
            'before': before_metrics.avg_nesting,
            'after': after_metrics.avg_nesting,
            'change': calculate_percentage_change(
                before_metrics.avg_nesting,
                after_metrics.avg_nesting
            ),
            'improved': after_metrics.avg_nesting <= before_metrics.avg_nesting
        },
        'max_nesting': {
            'before': before_metrics.max_nesting,
            'after': after_metrics.max_nesting,
            'change': calculate_percentage_change(
                before_metrics.max_nesting,
                after_metrics.max_nesting
            ),
            'improved': after_metrics.max_nesting <= before_metrics.max_nesting
        }
    }

    return comparison


def compare_documentation(before_file: Path, after_file: Path) -> Dict[str, Any]:
    """Compare documentation metrics between two files."""
    before_metrics = check_documentation.analyze_file(before_file)
    after_metrics = check_documentation.analyze_file(after_file)

    comparison = {
        'module_docstring': {
            'before': before_metrics.has_module_docstring,
            'after': after_metrics.has_module_docstring,
            'improved': after_metrics.has_module_docstring and not before_metrics.has_module_docstring
        },
        'docstring_coverage': {
            'before': before_metrics.docstring_coverage_pct,
            'after': after_metrics.docstring_coverage_pct,
            'change': calculate_percentage_increase(
                before_metrics.docstring_coverage_pct,
                after_metrics.docstring_coverage_pct
            ),
            'improved': after_metrics.docstring_coverage_pct >= before_metrics.docstring_coverage_pct
        },
        'type_hint_coverage': {
            'before': before_metrics.type_hint_coverage_pct,
            'after': after_metrics.type_hint_coverage_pct,
            'change': calculate_percentage_increase(
                before_metrics.type_hint_coverage_pct,
                after_metrics.type_hint_coverage_pct
            ),
            'improved': after_metrics.type_hint_coverage_pct >= before_metrics.type_hint_coverage_pct
        }
    }

    return comparison


def print_comparison(complexity: Dict[str, Any], documentation: Dict[str, Any]):
    """Print comparison results in human-readable format."""
    print(f"\n{'='*70}")
    print(f"Refactoring Metrics Comparison")
    print(f"{'='*70}\n")

    print("Complexity Metrics:")
    print(f"{'─'*70}")

    for metric_name, data in complexity.items():
        metric_label = metric_name.replace('_', ' ').title()
        before = data['before']
        after = data['after']
        change = data['change']
        improved = data['improved']

        symbol = '✓' if improved else '✗'
        change_str = f"{change:+.1f}%" if change != 0 else "no change"

        print(f"  {metric_label}:")
        print(f"    Before: {before}, After: {after}, Change: {change_str} {symbol}")

    print(f"\nDocumentation Metrics:")
    print(f"{'─'*70}")

    # Module docstring
    mod_doc = documentation['module_docstring']
    if mod_doc['after'] and not mod_doc['before']:
        print(f"  Module Docstring: Added ✓")
    elif mod_doc['after']:
        print(f"  Module Docstring: Present ✓")
    else:
        print(f"  Module Docstring: Missing ✗")

    # Coverage metrics
    for metric_name, data in documentation.items():
        if metric_name == 'module_docstring':
            continue

        metric_label = metric_name.replace('_', ' ').title()
        before = data['before']
        after = data['after']
        change = data['change']
        improved = data['improved']

        symbol = '✓' if improved else '✗'
        change_str = f"{change:+.1f}%" if change != 0 else "no change"

        print(f"  {metric_label}:")
        print(f"    Before: {before}%, After: {after}%, Change: {change_str} {symbol}")

    # Overall assessment
    print(f"\nOverall Assessment:")
    print(f"{'─'*70}")

    complexity_improvements = sum(1 for data in complexity.values() if data['improved'])
    complexity_total = len(complexity)

    doc_improvements = sum(1 for data in documentation.values() if data['improved'])
    doc_total = len(documentation)

    print(f"  Complexity: {complexity_improvements}/{complexity_total} metrics improved")
    print(f"  Documentation: {doc_improvements}/{doc_total} metrics improved")

    if complexity_improvements == complexity_total and doc_improvements == doc_total:
        print(f"\n✓ All metrics improved or maintained!")
    elif complexity_improvements + doc_improvements > 0:
        print(f"\n⚠ Some metrics improved")
    else:
        print(f"\n✗ No improvements detected")


def main():
    parser = argparse.ArgumentParser(
        description="Compare code metrics before and after refactoring"
    )
    parser.add_argument("before_file", type=Path, help="Path to file before refactoring")
    parser.add_argument("after_file", type=Path, help="Path to file after refactoring")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    # Validate files
    for file_path in [args.before_file, args.after_file]:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        if not file_path.suffix == '.py':
            print(f"Error: File must be a Python file (.py): {file_path}", file=sys.stderr)
            sys.exit(1)

    # Compare metrics
    complexity_comparison = compare_complexity(args.before_file, args.after_file)
    documentation_comparison = compare_documentation(args.before_file, args.after_file)

    if args.json:
        output = {
            'complexity': complexity_comparison,
            'documentation': documentation_comparison
        }
        print(json.dumps(output, indent=2))
    else:
        print_comparison(complexity_comparison, documentation_comparison)


if __name__ == "__main__":
    main()
