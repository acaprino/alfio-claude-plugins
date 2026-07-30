#!/usr/bin/env python3
"""Measure code complexity metrics for refactoring validation.

This script analyzes source code files to measure:
- Cyclomatic complexity per function
- Function length (lines of code)
- Nesting depth
- Overall file statistics

Usage:
    python measure_complexity.py <file_path> [--json]
"""

import argparse
import ast
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    line_number: int
    complexity: int
    length: int  # lines of code
    max_nesting: int
    num_parameters: int


@dataclass
class FileMetrics:
    """Overall metrics for a file."""
    file_path: str
    total_functions: int
    avg_complexity: float
    max_complexity: int
    avg_length: float
    max_length: int
    avg_nesting: float
    max_nesting: int
    functions: List[FunctionMetrics]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['functions'] = [asdict(f) for f in self.functions]
        return result


class ComplexityAnalyzer(ast.NodeVisitor):
    """AST visitor to calculate cyclomatic complexity."""

    def __init__(self):
        self.complexity = 1  # Base complexity is 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds a decision point
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        if node.ifs:
            self.complexity += len(node.ifs)
        self.generic_visit(node)


class NestingAnalyzer(ast.NodeVisitor):
    """AST visitor to calculate maximum nesting depth."""

    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0

    def _visit_nested(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    visit_If = _visit_nested
    visit_While = _visit_nested
    visit_For = _visit_nested
    visit_With = _visit_nested
    visit_Try = _visit_nested


def calculate_complexity(func_node: ast.FunctionDef) -> int:
    """Calculate cyclomatic complexity for a function."""
    analyzer = ComplexityAnalyzer()
    analyzer.visit(func_node)
    return analyzer.complexity


def calculate_max_nesting(func_node: ast.FunctionDef) -> int:
    """Calculate maximum nesting depth for a function."""
    analyzer = NestingAnalyzer()
    analyzer.visit(func_node)
    return analyzer.max_depth


def calculate_function_length(func_node: ast.FunctionDef) -> int:
    """Calculate lines of code for a function (excluding docstring)."""
    # Get total lines
    if hasattr(func_node, 'end_lineno') and func_node.end_lineno:
        total_lines = func_node.end_lineno - func_node.lineno + 1
    else:
        # Fallback for older Python versions
        total_lines = 1

    # Subtract docstring lines if present
    if (ast.get_docstring(func_node) and
        func_node.body and
        isinstance(func_node.body[0], ast.Expr) and
        isinstance(func_node.body[0].value, (ast.Str, ast.Constant))):
        docstring_node = func_node.body[0]
        if hasattr(docstring_node, 'end_lineno'):
            docstring_lines = docstring_node.end_lineno - docstring_node.lineno + 1
            total_lines -= docstring_lines

    return max(1, total_lines)


def analyze_file(file_path: Path) -> FileMetrics:
    """Analyze a Python file and return metrics."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    functions: List[FunctionMetrics] = []

    # Find all function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            metrics = FunctionMetrics(
                name=node.name,
                line_number=node.lineno,
                complexity=calculate_complexity(node),
                length=calculate_function_length(node),
                max_nesting=calculate_max_nesting(node),
                num_parameters=len(node.args.args)
            )
            functions.append(metrics)

    # Calculate overall statistics
    if functions:
        avg_complexity = sum(f.complexity for f in functions) / len(functions)
        max_complexity = max(f.complexity for f in functions)
        avg_length = sum(f.length for f in functions) / len(functions)
        max_length = max(f.length for f in functions)
        avg_nesting = sum(f.max_nesting for f in functions) / len(functions)
        max_nesting = max(f.max_nesting for f in functions)
    else:
        avg_complexity = max_complexity = 0
        avg_length = max_length = 0
        avg_nesting = max_nesting = 0

    return FileMetrics(
        file_path=str(file_path),
        total_functions=len(functions),
        avg_complexity=round(avg_complexity, 2),
        max_complexity=max_complexity,
        avg_length=round(avg_length, 2),
        max_length=max_length,
        avg_nesting=round(avg_nesting, 2),
        max_nesting=max_nesting,
        functions=functions
    )


def print_metrics(metrics: FileMetrics, verbose: bool = True):
    """Print metrics in human-readable format."""
    print(f"\n{'='*70}")
    print(f"Complexity Metrics: {metrics.file_path}")
    print(f"{'='*70}\n")

    print(f"Overall Statistics:")
    print(f"  Total Functions: {metrics.total_functions}")
    print(f"  Avg Complexity: {metrics.avg_complexity} (target: <10, warning: 15+)")
    print(f"  Max Complexity: {metrics.max_complexity}")
    print(f"  Avg Length: {metrics.avg_length} lines (target: <30, warning: 50+)")
    print(f"  Max Length: {metrics.max_length} lines")
    print(f"  Avg Nesting: {metrics.avg_nesting} levels (target: ≤3)")
    print(f"  Max Nesting: {metrics.max_nesting} levels")

    # Flag problematic metrics
    issues = []
    if metrics.avg_complexity > 10:
        issues.append(f"  ⚠ Average complexity is {metrics.avg_complexity} (target: <10)")
    if metrics.max_complexity > 15:
        issues.append(f"  ⚠ Maximum complexity is {metrics.max_complexity} (warning: 15+)")
    if metrics.avg_length > 30:
        issues.append(f"  ⚠ Average function length is {metrics.avg_length} lines (target: <30)")
    if metrics.max_nesting > 3:
        issues.append(f"  ⚠ Maximum nesting is {metrics.max_nesting} levels (target: ≤3)")

    if issues:
        print(f"\nIssues Found:")
        for issue in issues:
            print(issue)
    else:
        print(f"\n✓ All metrics within target ranges")

    if verbose and metrics.functions:
        print(f"\nPer-Function Breakdown:")
        print(f"{'─'*70}")

        # Sort by complexity (descending) to show worst offenders first
        sorted_funcs = sorted(metrics.functions, key=lambda f: f.complexity, reverse=True)

        for func in sorted_funcs[:10]:  # Show top 10 most complex
            warnings = []
            if func.complexity > 15:
                warnings.append("HIGH COMPLEXITY")
            elif func.complexity > 10:
                warnings.append("complexity warning")
            if func.length > 50:
                warnings.append("VERY LONG")
            elif func.length > 30:
                warnings.append("long")
            if func.max_nesting > 3:
                warnings.append(f"nesting: {func.max_nesting}")

            warning_str = f" [{', '.join(warnings)}]" if warnings else ""

            print(f"  {func.name}:{func.line_number}")
            print(f"    Complexity: {func.complexity}, Length: {func.length} lines, "
                  f"Nesting: {func.max_nesting}, Params: {func.num_parameters}{warning_str}")

        if len(sorted_funcs) > 10:
            print(f"  ... and {len(sorted_funcs) - 10} more functions")


def main():
    parser = argparse.ArgumentParser(
        description="Measure code complexity metrics for refactoring validation"
    )
    parser.add_argument("file_path", type=Path, help="Path to Python file to analyze")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    if not args.file_path.exists():
        print(f"Error: File not found: {args.file_path}", file=sys.stderr)
        sys.exit(1)

    if not args.file_path.suffix == '.py':
        print(f"Error: File must be a Python file (.py)", file=sys.stderr)
        sys.exit(1)

    metrics = analyze_file(args.file_path)

    if args.json:
        print(json.dumps(metrics.to_dict(), indent=2))
    else:
        print_metrics(metrics, verbose=not args.quiet)


if __name__ == "__main__":
    main()
