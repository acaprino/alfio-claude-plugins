#!/usr/bin/env python3
"""Check documentation coverage for Python code.

This script analyzes:
- Docstring coverage for modules, classes, and functions
- Type hint coverage for function parameters and returns
- Documentation quality metrics

Usage:
    python check_documentation.py <file_path> [--json]
"""

import argparse
import ast
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class FunctionDocMetrics:
    """Documentation metrics for a single function."""
    name: str
    line_number: int
    has_docstring: bool
    docstring_length: int
    has_return_type: bool
    num_params: int
    num_params_with_types: int
    is_public: bool


@dataclass
class ClassDocMetrics:
    """Documentation metrics for a class."""
    name: str
    line_number: int
    has_docstring: bool
    docstring_length: int
    num_methods: int
    num_methods_documented: int
    is_public: bool


@dataclass
class FileDocMetrics:
    """Overall documentation metrics for a file."""
    file_path: str
    has_module_docstring: bool
    module_docstring_length: int

    total_functions: int
    public_functions: int
    functions_with_docstrings: int
    public_functions_with_docstrings: int

    total_classes: int
    public_classes: int
    classes_with_docstrings: int
    public_classes_with_docstrings: int

    total_params: int
    params_with_types: int

    total_returns: int
    returns_with_types: int

    docstring_coverage_pct: float  # Public items with docstrings
    type_hint_coverage_pct: float  # Params with type hints

    functions: List[FunctionDocMetrics]
    classes: List[ClassDocMetrics]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['functions'] = [asdict(f) for f in self.functions]
        result['classes'] = [asdict(c) for c in self.classes]
        return result


def is_public(name: str) -> bool:
    """Check if a name is public (doesn't start with underscore)."""
    return not name.startswith('_')


def get_docstring_length(node: ast.AST) -> int:
    """Get length of docstring in lines, or 0 if no docstring."""
    docstring = ast.get_docstring(node)
    if docstring:
        return len(docstring.splitlines())
    return 0


def has_type_hints(node: ast.FunctionDef) -> tuple[bool, int, int]:
    """Check if function has type hints.

    Returns:
        (has_return_type, num_params_with_types, total_params)
    """
    has_return_type = node.returns is not None

    # Count parameters with type annotations
    num_params_with_types = sum(
        1 for arg in node.args.args if arg.annotation is not None
    )

    total_params = len(node.args.args)

    return has_return_type, num_params_with_types, total_params


def analyze_function(node: ast.FunctionDef) -> FunctionDocMetrics:
    """Analyze a function definition for documentation metrics."""
    has_return_type, num_params_with_types, total_params = has_type_hints(node)

    return FunctionDocMetrics(
        name=node.name,
        line_number=node.lineno,
        has_docstring=ast.get_docstring(node) is not None,
        docstring_length=get_docstring_length(node),
        has_return_type=has_return_type,
        num_params=total_params,
        num_params_with_types=num_params_with_types,
        is_public=is_public(node.name)
    )


def analyze_class(node: ast.ClassDef) -> ClassDocMetrics:
    """Analyze a class definition for documentation metrics."""
    # Count methods with docstrings
    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
    methods_documented = sum(
        1 for m in methods if ast.get_docstring(m) is not None
    )

    return ClassDocMetrics(
        name=node.name,
        line_number=node.lineno,
        has_docstring=ast.get_docstring(node) is not None,
        docstring_length=get_docstring_length(node),
        num_methods=len(methods),
        num_methods_documented=methods_documented,
        is_public=is_public(node.name)
    )


def analyze_file(file_path: Path) -> FileDocMetrics:
    """Analyze a Python file for documentation coverage."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Module-level docstring
    module_docstring = ast.get_docstring(tree)
    has_module_docstring = module_docstring is not None
    module_docstring_length = len(module_docstring.splitlines()) if module_docstring else 0

    # Analyze top-level functions and classes
    functions: List[FunctionDocMetrics] = []
    classes: List[ClassDocMetrics] = []

    total_params = 0
    params_with_types = 0
    total_returns = 0
    returns_with_types = 0

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func_metrics = analyze_function(node)
            functions.append(func_metrics)

            total_params += func_metrics.num_params
            params_with_types += func_metrics.num_params_with_types
            total_returns += 1
            if func_metrics.has_return_type:
                returns_with_types += 1

        elif isinstance(node, ast.ClassDef):
            class_metrics = analyze_class(node)
            classes.append(class_metrics)

            # Also analyze class methods
            for method_node in node.body:
                if isinstance(method_node, ast.FunctionDef):
                    method_metrics = analyze_function(method_node)
                    functions.append(method_metrics)

                    total_params += method_metrics.num_params
                    params_with_types += method_metrics.num_params_with_types
                    total_returns += 1
                    if method_metrics.has_return_type:
                        returns_with_types += 1

    # Calculate statistics
    total_functions = len(functions)
    public_functions = sum(1 for f in functions if f.is_public)
    functions_with_docstrings = sum(1 for f in functions if f.has_docstring)
    public_functions_with_docstrings = sum(
        1 for f in functions if f.is_public and f.has_docstring
    )

    total_classes = len(classes)
    public_classes = sum(1 for c in classes if c.is_public)
    classes_with_docstrings = sum(1 for c in classes if c.has_docstring)
    public_classes_with_docstrings = sum(
        1 for c in classes if c.is_public and c.has_docstring
    )

    # Calculate coverage percentages
    public_items = public_functions + public_classes
    documented_public_items = public_functions_with_docstrings + public_classes_with_docstrings

    if public_items > 0:
        docstring_coverage_pct = round((documented_public_items / public_items) * 100, 1)
    else:
        docstring_coverage_pct = 0.0

    if total_params > 0:
        type_hint_coverage_pct = round((params_with_types / total_params) * 100, 1)
    else:
        type_hint_coverage_pct = 0.0

    return FileDocMetrics(
        file_path=str(file_path),
        has_module_docstring=has_module_docstring,
        module_docstring_length=module_docstring_length,
        total_functions=total_functions,
        public_functions=public_functions,
        functions_with_docstrings=functions_with_docstrings,
        public_functions_with_docstrings=public_functions_with_docstrings,
        total_classes=total_classes,
        public_classes=public_classes,
        classes_with_docstrings=classes_with_docstrings,
        public_classes_with_docstrings=public_classes_with_docstrings,
        total_params=total_params,
        params_with_types=params_with_types,
        total_returns=total_returns,
        returns_with_types=returns_with_types,
        docstring_coverage_pct=docstring_coverage_pct,
        type_hint_coverage_pct=type_hint_coverage_pct,
        functions=functions,
        classes=classes
    )


def print_metrics(metrics: FileDocMetrics, verbose: bool = True):
    """Print documentation metrics in human-readable format."""
    print(f"\n{'='*70}")
    print(f"Documentation Coverage: {metrics.file_path}")
    print(f"{'='*70}\n")

    # Module-level documentation
    if metrics.has_module_docstring:
        print(f"✓ Module docstring present ({metrics.module_docstring_length} lines)")
    else:
        print(f"✗ Module docstring missing")

    print(f"\nOverall Statistics:")
    print(f"  Public Functions: {metrics.public_functions}")
    print(f"  Functions with Docstrings: {metrics.public_functions_with_docstrings}/{metrics.public_functions}")
    print(f"  Public Classes: {metrics.public_classes}")
    print(f"  Classes with Docstrings: {metrics.public_classes_with_docstrings}/{metrics.public_classes}")
    print(f"\n  Docstring Coverage: {metrics.docstring_coverage_pct}% (target: >80%)")
    print(f"  Type Hint Coverage: {metrics.type_hint_coverage_pct}% (target: >90%)")

    # Flag issues
    issues = []
    if not metrics.has_module_docstring:
        issues.append("  ⚠ Module docstring is missing")
    if metrics.docstring_coverage_pct < 80:
        issues.append(f"  ⚠ Docstring coverage is {metrics.docstring_coverage_pct}% (target: >80%)")
    if metrics.type_hint_coverage_pct < 90:
        issues.append(f"  ⚠ Type hint coverage is {metrics.type_hint_coverage_pct}% (target: >90%)")

    if issues:
        print(f"\nIssues Found:")
        for issue in issues:
            print(issue)
    else:
        print(f"\n✓ All documentation targets met")

    if verbose:
        # Show undocumented public items
        undocumented_funcs = [
            f for f in metrics.functions
            if f.is_public and not f.has_docstring
        ]
        undocumented_classes = [
            c for c in metrics.classes
            if c.is_public and not c.has_docstring
        ]

        if undocumented_funcs:
            print(f"\nUndocumented Public Functions:")
            for func in undocumented_funcs[:10]:  # Show first 10
                print(f"  {func.name}:{func.line_number} - Missing docstring")
            if len(undocumented_funcs) > 10:
                print(f"  ... and {len(undocumented_funcs) - 10} more")

        if undocumented_classes:
            print(f"\nUndocumented Public Classes:")
            for cls in undocumented_classes:
                print(f"  {cls.name}:{cls.line_number} - Missing docstring")

        # Show functions with missing type hints
        missing_types = [
            f for f in metrics.functions
            if f.is_public and (
                not f.has_return_type or
                f.num_params_with_types < f.num_params
            )
        ]

        if missing_types:
            print(f"\nPublic Functions with Missing Type Hints:")
            for func in missing_types[:10]:  # Show first 10
                hints = []
                if not func.has_return_type:
                    hints.append("missing return type")
                if func.num_params_with_types < func.num_params:
                    hints.append(f"{func.num_params - func.num_params_with_types} params without types")
                print(f"  {func.name}:{func.line_number} - {', '.join(hints)}")
            if len(missing_types) > 10:
                print(f"  ... and {len(missing_types) - 10} more")


def main():
    parser = argparse.ArgumentParser(
        description="Check documentation coverage for Python code"
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
