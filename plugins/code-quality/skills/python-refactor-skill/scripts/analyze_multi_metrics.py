#!/usr/bin/env python3
"""Analyze code using multiple complexity metrics.

This script combines cognitive complexity (via complexipy), cyclomatic complexity 
(via radon), and maintainability index for comprehensive code quality assessment.

Usage:
    python analyze_multi_metrics.py <file_or_directory> [--json] [--threshold-file FILE]
    
Requirements:
    pip install complexipy radon

Note: For linting, use Ruff separately: ruff check <path>
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class FunctionMetrics:
    """Combined metrics for a single function."""
    name: str
    file: str
    line_start: int
    line_end: int
    cyclomatic: int
    cognitive: int
    
    @property
    def risk_level(self) -> str:
        """Assess risk based on combined metrics."""
        if self.cyclomatic > 15 or self.cognitive > 20:
            return "HIGH"
        elif self.cyclomatic > 10 or self.cognitive > 15:
            return "MEDIUM"
        return "LOW"


@dataclass
class FileMetrics:
    """Combined metrics for a file."""
    file_path: str
    maintainability_index: float
    total_cognitive: int
    avg_cyclomatic: float
    max_cyclomatic: int
    max_cognitive: int
    total_functions: int
    functions: List[FunctionMetrics]
    
    @property
    def health_grade(self) -> str:
        """Overall health grade based on maintainability index."""
        if self.maintainability_index >= 80:
            return "A"
        elif self.maintainability_index >= 65:
            return "B"
        elif self.maintainability_index >= 50:
            return "C"
        elif self.maintainability_index >= 35:
            return "D"
        return "F"


@dataclass 
class Thresholds:
    """Configurable thresholds for metrics."""
    cyclomatic_warning: int = 10
    cyclomatic_error: int = 15
    cognitive_warning: int = 15
    cognitive_error: int = 25
    mi_warning: float = 65.0
    mi_error: float = 50.0
    
    @classmethod
    def from_file(cls, path: Path) -> 'Thresholds':
        """Load thresholds from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def progressive_legacy(cls) -> 'Thresholds':
        """Lenient thresholds for legacy code."""
        return cls(
            cyclomatic_warning=15,
            cyclomatic_error=25,
            cognitive_warning=20,
            cognitive_error=30,
            mi_warning=50.0,
            mi_error=35.0
        )


def get_cognitive_complexity_complexipy(path: Path) -> dict:
    """Get cognitive complexity using complexipy (Rust-based, fast!)."""
    try:
        from complexipy import file_complexity
        
        results = {}
        
        if path.is_file():
            files = [path]
        else:
            files = list(path.rglob('*.py'))
        
        for py_file in files:
            # Skip common excludes
            if any(part.startswith('.') or part in ('venv', 'env', '__pycache__', 'node_modules', 'migrations') 
                   for part in py_file.parts):
                continue
            
            try:
                result = file_complexity(str(py_file))
                file_functions = {}
                for func in result.functions:
                    key = f"{func.name}:{func.line_start}"
                    file_functions[key] = {
                        'complexity': func.complexity,
                        'line_start': func.line_start,
                        'line_end': func.line_end,
                    }
                results[str(py_file)] = {
                    'total': result.complexity,
                    'functions': file_functions
                }
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}", file=sys.stderr)
        
        return results
        
    except ImportError:
        print("Error: complexipy not installed. Install with: pip install complexipy", file=sys.stderr)
        print("Falling back to subprocess call...", file=sys.stderr)
        return get_cognitive_via_cli(path)


def get_cognitive_via_cli(path: Path) -> dict:
    """Fallback: get cognitive complexity via complexipy CLI."""
    try:
        result = subprocess.run(
            ["complexipy", str(path), "--output-json", "--quiet"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            # Parse JSON output
            data = json.loads(result.stdout)
            # Transform to our format
            results = {}
            for file_data in data.get('files', []):
                file_functions = {}
                for func in file_data.get('functions', []):
                    key = f"{func['name']}:{func['line_start']}"
                    file_functions[key] = {
                        'complexity': func['complexity'],
                        'line_start': func['line_start'],
                        'line_end': func.get('line_end', func['line_start']),
                    }
                results[file_data['path']] = {
                    'total': file_data.get('complexity', 0),
                    'functions': file_functions
                }
            return results
    except Exception as e:
        print(f"Warning: complexipy CLI failed: {e}", file=sys.stderr)
    
    return {}


def get_cyclomatic_complexity(file_path: Path) -> dict:
    """Get cyclomatic complexity using radon."""
    try:
        result = subprocess.run(
            ["radon", "cc", str(file_path), "-j"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        
        complexities = {}
        for filepath, file_data in data.items():
            for item in file_data:
                name = item.get("name", "unknown")
                complexity = item.get("complexity", 0)
                lineno = item.get("lineno", 0)
                key = f"{name}:{lineno}"
                complexities[key] = complexity
        
        return complexities
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: radon cc failed: {e}", file=sys.stderr)
        return {}


def get_maintainability_index(file_path: Path) -> float:
    """Get maintainability index using radon."""
    try:
        result = subprocess.run(
            ["radon", "mi", str(file_path), "-j"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        
        for file_data in data.values():
            return file_data.get("mi", 0.0)
        
        return 0.0
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: radon mi failed: {e}", file=sys.stderr)
        return 0.0


def analyze_file(file_path: Path, cognitive_data: dict) -> Optional[FileMetrics]:
    """Analyze a single file with all metrics."""
    if not file_path.suffix == '.py':
        return None
    
    cyclomatic = get_cyclomatic_complexity(file_path)
    mi = get_maintainability_index(file_path)
    
    # Get cognitive data for this file
    file_cognitive = cognitive_data.get(str(file_path), {})
    cognitive_functions = file_cognitive.get('functions', {})
    total_cognitive = file_cognitive.get('total', 0)
    
    # Combine metrics per function
    all_keys = set(cyclomatic.keys()) | set(cognitive_functions.keys())
    
    functions = []
    for key in all_keys:
        parts = key.rsplit(':', 1)
        name = parts[0] if parts else key
        lineno = int(parts[1]) if len(parts) > 1 else 0
        
        cog_data = cognitive_functions.get(key, {})
        
        functions.append(FunctionMetrics(
            name=name,
            file=str(file_path),
            line_start=cog_data.get('line_start', lineno),
            line_end=cog_data.get('line_end', lineno),
            cyclomatic=cyclomatic.get(key, 0),
            cognitive=cog_data.get('complexity', 0),
        ))
    
    if not functions:
        return FileMetrics(
            file_path=str(file_path),
            maintainability_index=round(mi, 2),
            total_cognitive=total_cognitive,
            avg_cyclomatic=0,
            max_cyclomatic=0,
            max_cognitive=0,
            total_functions=0,
            functions=[]
        )
    
    cyc_values = [f.cyclomatic for f in functions if f.cyclomatic > 0]
    cog_values = [f.cognitive for f in functions if f.cognitive > 0]
    
    return FileMetrics(
        file_path=str(file_path),
        maintainability_index=round(mi, 2),
        total_cognitive=total_cognitive,
        avg_cyclomatic=round(sum(cyc_values) / len(cyc_values), 2) if cyc_values else 0,
        max_cyclomatic=max(cyc_values) if cyc_values else 0,
        max_cognitive=max(cog_values) if cog_values else 0,
        total_functions=len(functions),
        functions=sorted(functions, key=lambda f: f.cognitive, reverse=True)
    )


def analyze_path(target_path: Path) -> List[FileMetrics]:
    """Analyze all Python files in path."""
    
    # Get cognitive complexity for all files at once (more efficient)
    print("Analyzing cognitive complexity with complexipy...", file=sys.stderr)
    cognitive_data = get_cognitive_complexity_complexipy(target_path)
    
    results = []
    
    if target_path.is_file():
        files = [target_path]
    else:
        files = list(target_path.rglob('*.py'))
    
    print(f"Analyzing {len(files)} Python files...", file=sys.stderr)
    
    for py_file in files:
        # Skip common excludes
        if any(part.startswith('.') or part in ('venv', 'env', '__pycache__', 'node_modules') 
               for part in py_file.parts):
            continue
        
        metrics = analyze_file(py_file, cognitive_data)
        if metrics:
            results.append(metrics)
    
    return results


def print_report(results: List[FileMetrics], thresholds: Thresholds) -> int:
    """Print human-readable report."""
    print(f"\n{'='*80}")
    print(f"MULTI-METRIC CODE ANALYSIS REPORT")
    print(f"Stack: Ruff (linting) + Complexipy (cognitive) + Radon (cyclomatic/MI)")
    print(f"{'='*80}\n")
    
    # Summary
    total_functions = sum(r.total_functions for r in results)
    high_risk = sum(1 for r in results for f in r.functions if f.risk_level == "HIGH")
    medium_risk = sum(1 for r in results for f in r.functions if f.risk_level == "MEDIUM")
    
    print(f"Summary:")
    print(f"  Files analyzed: {len(results)}")
    print(f"  Total functions: {total_functions}")
    print(f"  High risk functions: {high_risk}")
    print(f"  Medium risk functions: {medium_risk}")
    
    # Health grades
    grades = {}
    for r in results:
        grade = r.health_grade
        grades[grade] = grades.get(grade, 0) + 1
    
    print(f"\nHealth Grades (Maintainability Index):")
    for grade in ['A', 'B', 'C', 'D', 'F']:
        count = grades.get(grade, 0)
        bar = '█' * count
        print(f"  {grade}: {bar} ({count} files)")
    
    # Worst offenders
    all_functions = [(f, r.file_path) for r in results for f in r.functions]
    worst_cognitive = sorted(all_functions, key=lambda x: x[0].cognitive, reverse=True)[:10]
    worst_cyclomatic = sorted(all_functions, key=lambda x: x[0].cyclomatic, reverse=True)[:10]
    
    print(f"\nTop 10 Highest Cognitive Complexity:")
    print(f"{'─'*80}")
    for func, filepath in worst_cognitive:
        if func.cognitive > 0:
            status = "⚠️ " if func.cognitive > thresholds.cognitive_warning else "✓ "
            if func.cognitive > thresholds.cognitive_error:
                status = "❌"
            print(f"  {status} {func.name} ({filepath}:{func.line_start})")
            print(f"      Cognitive: {func.cognitive}, Cyclomatic: {func.cyclomatic}")
    
    print(f"\nTop 10 Highest Cyclomatic Complexity:")
    print(f"{'─'*80}")
    for func, filepath in worst_cyclomatic:
        if func.cyclomatic > 0:
            status = "⚠️ " if func.cyclomatic > thresholds.cyclomatic_warning else "✓ "
            if func.cyclomatic > thresholds.cyclomatic_error:
                status = "❌"
            print(f"  {status} {func.name} ({filepath}:{func.line_start})")
            print(f"      Cyclomatic: {func.cyclomatic}, Cognitive: {func.cognitive}")
    
    # Files needing attention
    problem_files = [r for r in results if r.maintainability_index < thresholds.mi_warning]
    if problem_files:
        print(f"\nFiles Needing Attention (MI < {thresholds.mi_warning}):")
        print(f"{'─'*80}")
        for r in sorted(problem_files, key=lambda x: x.maintainability_index):
            grade = r.health_grade
            print(f"  [{grade}] {r.file_path}")
            print(f"      MI: {r.maintainability_index}, Max CC: {r.max_cyclomatic}, Max CoC: {r.max_cognitive}")
    
    # Threshold violations summary
    violations = {
        'cognitive_error': sum(1 for f, _ in all_functions if f.cognitive > thresholds.cognitive_error),
        'cognitive_warning': sum(1 for f, _ in all_functions if thresholds.cognitive_warning < f.cognitive <= thresholds.cognitive_error),
        'cyclomatic_error': sum(1 for f, _ in all_functions if f.cyclomatic > thresholds.cyclomatic_error),
        'cyclomatic_warning': sum(1 for f, _ in all_functions if thresholds.cyclomatic_warning < f.cyclomatic <= thresholds.cyclomatic_error),
    }
    
    print(f"\nThreshold Violations:")
    print(f"{'─'*80}")
    print(f"  Cognitive > {thresholds.cognitive_error} (ERROR):   {violations['cognitive_error']}")
    print(f"  Cognitive > {thresholds.cognitive_warning} (WARNING): {violations['cognitive_warning']}")
    print(f"  Cyclomatic > {thresholds.cyclomatic_error} (ERROR):  {violations['cyclomatic_error']}")
    print(f"  Cyclomatic > {thresholds.cyclomatic_warning} (WARNING): {violations['cyclomatic_warning']}")
    
    # Final verdict
    print(f"\n{'='*80}")
    if violations['cognitive_error'] > 0 or violations['cyclomatic_error'] > 0:
        print("❌ QUALITY GATE: FAILED - Critical complexity violations found")
        return 1
    elif violations['cognitive_warning'] > 0 or violations['cyclomatic_warning'] > 0:
        print("⚠️  QUALITY GATE: WARNING - Some functions need attention")
        return 0
    else:
        print("✅ QUALITY GATE: PASSED - Code complexity within acceptable limits")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Analyze code using multiple complexity metrics (Ruff + Complexipy + Radon)"
    )
    parser.add_argument("path", type=Path, help="File or directory to analyze")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--threshold-file", type=Path, help="JSON file with custom thresholds")
    parser.add_argument("--legacy", action="store_true", help="Use lenient legacy thresholds")
    parser.add_argument("--output", type=Path, help="Output file for JSON results")
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)
    
    # Check dependencies
    try:
        import complexipy
    except ImportError:
        print("Error: complexipy not installed. Run: pip install complexipy", file=sys.stderr)
        sys.exit(1)
    
    # Load thresholds
    if args.threshold_file:
        thresholds = Thresholds.from_file(args.threshold_file)
    elif args.legacy:
        thresholds = Thresholds.progressive_legacy()
    else:
        thresholds = Thresholds()
    
    # Analyze
    results = analyze_path(args.path)
    
    if not results:
        print("No Python files found to analyze", file=sys.stderr)
        sys.exit(1)
    
    # Output
    if args.json or args.output:
        output_data = {
            'thresholds': asdict(thresholds),
            'files': [asdict(r) for r in results],
            'summary': {
                'total_files': len(results),
                'total_functions': sum(r.total_functions for r in results),
                'avg_maintainability': round(sum(r.maintainability_index for r in results) / len(results), 2)
            }
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(output_data, indent=2, default=str))
    else:
        exit_code = print_report(results, thresholds)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
