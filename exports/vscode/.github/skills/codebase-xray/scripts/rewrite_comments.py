#!/usr/bin/env python3
"""
Rewrite Comments CLI.

Analyzes and rewrites code comments following antirez commenting standards.

Usage:
    # Analyze a single file
    python rewrite_comments.py analyze src/main.py

    # Analyze with full report
    python rewrite_comments.py analyze src/main.py --report

    # Rewrite a file (dry run)
    python rewrite_comments.py rewrite src/main.py

    # Rewrite a file (apply changes)
    python rewrite_comments.py rewrite src/main.py --apply

    # Analyze entire directory
    python rewrite_comments.py scan src/ --recursive

    # Generate improvement report for codebase
    python rewrite_comments.py report src/ --output comment_health.md

Standards based on: https://antirez.com/news/124
"""

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from comment_rewriter import (
    CommentRewriter,
    CommentRewriterError,
    SUPPORTED_SUFFIXES,
)

VERSION = "1.0.0"

# Directories we never recurse into during scans.
_SKIP_DIRS = (
    "__pycache__", ".venv", "venv", ".tox",
    ".git", "node_modules",
    ".mypy_cache", ".pytest_cache",
    "target", "build", "dist", "out",
)


def _iter_supported(dir_path: Path, recursive: bool) -> list[Path]:
    """Walk a directory and yield supported source files."""
    pattern = "**/*" if recursive else "*"
    out: list[Path] = []
    for candidate in dir_path.glob(pattern):
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        # Segment match, not substring: "out" must not exclude checkout.py,
        # and "build" must not exclude a rebuild/ directory.
        if any(skip in candidate.parts for skip in _SKIP_DIRS):
            continue
        out.append(candidate)
    return out


def _existing_file(value: str) -> Path:
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file {value!r} does not exist")
    return path


def _existing_dir(value: str) -> Path:
    path = Path(value)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"directory {value!r} does not exist")
    return path


def _fail(message: str) -> None:
    """Report a fatal error on stderr and exit 1."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def _progress(items: list[Path], label: str) -> Iterator[Path]:
    """
    Yield items while drawing a one-line progress indicator on stderr.

    Silent when stderr is not a terminal so that piped output and CI logs stay
    clean.
    """
    interactive = sys.stderr.isatty()
    total = len(items)
    for index, item in enumerate(items, start=1):
        if interactive:
            print(
                f"\r{label} [{index}/{total}] {item.name[:48]:<48}",
                end="",
                file=sys.stderr,
                flush=True,
            )
        yield item
    if interactive:
        print("\r" + " " * (len(label) + 62) + "\r", end="", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Commands.
# ---------------------------------------------------------------------------


def cmd_analyze(args: argparse.Namespace) -> None:
    """Analyze comments in a source file."""
    rewriter = CommentRewriter()
    file_path = args.file_path

    try:
        analysis = rewriter.analyze_file(file_path)
    except CommentRewriterError as e:
        _fail(str(e))

    if args.json_output:
        output = {
            "file": analysis.file_path,
            "total_lines": analysis.total_lines,
            "total_comments": analysis.total_comments,
            "comment_ratio": round(analysis.comment_ratio, 2),
            "by_type": analysis.by_type,
            "by_classification": analysis.by_classification,
            "issues": analysis.issues,
            "comments": [
                {
                    "line": c.line_number,
                    "type": c.comment_type.value,
                    "classification": c.classification.value,
                    "text": c.text[:100],
                    "reason": c.reason,
                }
                for c in analysis.comments
            ],
        }
        print(json.dumps(output, indent=2))

    elif args.report:
        print(rewriter.generate_report(analysis))

    elif args.issues_only:
        if analysis.issues:
            print(f"Issues in {file_path.name}:")
            for issue in analysis.issues:
                print(f"  - {issue}")
        else:
            print(f"No issues found in {file_path.name}")

    else:
        # Summary output
        print(f"File: {file_path.name}")
        print(f"Lines: {analysis.total_lines}, Comments: {analysis.total_comments}")
        print(f"Ratio: {analysis.comment_ratio:.1f} comments per 100 lines")
        print("")

        # Classification summary
        keep = analysis.by_classification.get("keep", 0)
        enhance = analysis.by_classification.get("enhance", 0)
        rewrite = analysis.by_classification.get("rewrite", 0)
        delete = analysis.by_classification.get("delete", 0)

        print(f"[OK] Keep: {keep}")
        print(f"[~]  Enhance: {enhance}")
        print(f"[!]  Rewrite: {rewrite}")
        print(f"[X]  Delete: {delete}")

        if analysis.issues:
            print("")
            print(f"Found {len(analysis.issues)} issue(s). Use --report for details.")


def cmd_rewrite(args: argparse.Namespace) -> None:
    """Rewrite comments in a source file."""
    rewriter = CommentRewriter()
    file_path = args.file_path
    output_path = Path(args.output) if args.output else None

    if args.backup and args.apply and not args.output:
        # Create backup. Copy bytes so the original line endings survive.
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        backup_path.write_bytes(file_path.read_bytes())
        print(f"Backup created: {backup_path}")

    try:
        rewritten, changes = rewriter.rewrite_file(
            file_path=file_path,
            output_path=output_path,
            dry_run=not args.apply,
        )
    except CommentRewriterError as e:
        _fail(str(e))

    if changes:
        print("Changes:")
        for change in changes:
            print(f"  - {change}")
    else:
        print("No changes needed.")

    if not args.apply:
        print("")
        print("This was a dry run. Use --apply to make changes.")


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan a directory for comment issues."""
    rewriter = CommentRewriter()
    dir_path = args.directory
    files = _iter_supported(dir_path, args.recursive)

    if not files:
        print(f"No supported source files found in {dir_path}")
        return

    results = []
    total_issues = 0
    total_delete = 0
    total_rewrite = 0

    for file_path in _progress(files, "Scanning"):
        try:
            analysis = rewriter.analyze_file(file_path)
            results.append(analysis)
            total_issues += len(analysis.issues)
            total_delete += analysis.by_classification.get("delete", 0)
            total_rewrite += analysis.by_classification.get("rewrite", 0)
        except CommentRewriterError as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
        except (OSError, UnicodeDecodeError) as e:
            print(f"File error {file_path}: {e}", file=sys.stderr)

    if args.json_output:
        output = {
            "directory": str(dir_path),
            "files_scanned": len(results),
            "total_issues": total_issues,
            "total_delete": total_delete,
            "total_rewrite": total_rewrite,
            "files": [
                {
                    "file": a.file_path,
                    "issues": len(a.issues),
                    "by_classification": a.by_classification,
                }
                for a in results
            ],
        }
        print(json.dumps(output, indent=2))

    else:
        print("")
        print(f"Scanned {len(results)} files in {dir_path}")
        print(f"Total issues: {total_issues}")
        print(f"  - To delete: {total_delete}")
        print(f"  - To rewrite: {total_rewrite}")
        print("")

        # Show files with most issues
        files_with_issues = [a for a in results if a.issues]
        files_with_issues.sort(key=lambda a: len(a.issues), reverse=True)

        if files_with_issues:
            print("Files with most issues:")
            for analysis in files_with_issues[:10]:
                print(f"  {len(analysis.issues):3d} issues: {analysis.file_path}")

        if args.issues_only and not files_with_issues:
            print("No issues found!")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate a comprehensive comment health report."""
    rewriter = CommentRewriter()
    dir_path = args.directory
    output_path = Path(args.output)
    files = _iter_supported(dir_path, args.recursive)

    if not files:
        print(f"No supported source files found in {dir_path}")
        return

    results = []
    for file_path in _progress(files, "Analyzing"):
        try:
            analysis = rewriter.analyze_file(file_path)
            results.append(analysis)
        except CommentRewriterError as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
        except (OSError, UnicodeDecodeError) as e:
            print(f"File error {file_path}: {e}", file=sys.stderr)

    # Generate report
    lines = [
        "# Comment Health Report",
        "",
        f"**Directory:** `{dir_path}`",
        f"**Files Analyzed:** {len(results)}",
        "**Generated by:** codebase-xray/rewrite_comments.py",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
    ]

    # Aggregate stats
    total_comments = sum(a.total_comments for a in results)
    total_lines = sum(a.total_lines for a in results)
    total_by_type: dict[str, int] = {}
    total_by_class: dict[str, int] = {}
    all_issues = []

    for analysis in results:
        for type_name, count in analysis.by_type.items():
            total_by_type[type_name] = total_by_type.get(type_name, 0) + count
        for class_name, count in analysis.by_classification.items():
            total_by_class[class_name] = total_by_class.get(class_name, 0) + count
        for issue in analysis.issues:
            all_issues.append((analysis.file_path, issue))

    avg_ratio = (total_comments / total_lines * 100) if total_lines > 0 else 0

    lines.extend([
        f"- **Total Lines of Code:** {total_lines:,}",
        f"- **Total Comments:** {total_comments:,}",
        f"- **Comment Ratio:** {avg_ratio:.1f} per 100 lines",
        f"- **Total Issues:** {len(all_issues)}",
        "",
    ])

    # Classification breakdown
    keep = total_by_class.get("keep", 0)
    enhance = total_by_class.get("enhance", 0)
    rewrite_count = total_by_class.get("rewrite", 0)
    delete_count = total_by_class.get("delete", 0)

    lines.extend([
        "### Comment Quality",
        "",
        "| Classification | Count | Percentage |",
        "|----------------|-------|------------|",
        f"| Keep (good) | {keep} | {keep / max(total_comments, 1) * 100:.1f}% |",
        f"| Enhance (improvable) | {enhance} | {enhance / max(total_comments, 1) * 100:.1f}% |",
        f"| Rewrite (problematic) | {rewrite_count} | {rewrite_count / max(total_comments, 1) * 100:.1f}% |",
        f"| Delete (bad) | {delete_count} | {delete_count / max(total_comments, 1) * 100:.1f}% |",
        "",
    ])

    # Type breakdown
    lines.extend([
        "### Comment Types",
        "",
        "| Type | Count | Description |",
        "|------|-------|-------------|",
    ])

    type_descriptions = {
        "function": "API documentation (docstrings)",
        "design": "Algorithm/architecture explanations",
        "why": "Reasoning behind code",
        "teacher": "Domain knowledge education",
        "checklist": "Coordination reminders",
        "guide": "Section dividers/structure",
        "trivial": "Obvious statements (BAD)",
        "debt": "TODO/FIXME markers (BAD)",
        "backup": "Commented-out code (BAD)",
        "unknown": "Needs human review",
    }

    for type_name in ["function", "design", "why", "teacher", "checklist", "guide", "trivial", "debt", "backup", "unknown"]:
        count = total_by_type.get(type_name, 0)
        desc = type_descriptions.get(type_name, "")
        lines.append(f"| {type_name} | {count} | {desc} |")

    lines.append("")

    # Files needing attention
    files_with_issues = [(a, len(a.issues)) for a in results if a.issues]
    files_with_issues.sort(key=lambda x: x[1], reverse=True)

    if files_with_issues:
        lines.extend([
            "---",
            "",
            "## Files Needing Attention",
            "",
            "| File | Issues | Delete | Rewrite |",
            "|------|--------|--------|---------|",
        ])

        for analysis, issue_count in files_with_issues[:20]:
            rel_path = _display_path(analysis.file_path, dir_path)
            delete_count = analysis.by_classification.get("delete", 0)
            rewrite_count = analysis.by_classification.get("rewrite", 0)
            lines.append(f"| `{rel_path}` | {issue_count} | {delete_count} | {rewrite_count} |")

        if len(files_with_issues) > 20:
            lines.append(f"| ... | {len(files_with_issues) - 20} more files | | |")

        lines.append("")

    # Sample issues
    if all_issues:
        lines.extend([
            "---",
            "",
            "## Sample Issues",
            "",
        ])

        for file_path, issue in all_issues[:30]:
            rel_path = _display_path(file_path, dir_path)
            lines.append(f"- `{rel_path}`: {issue}")

        if len(all_issues) > 30:
            lines.append(f"- ... and {len(all_issues) - 30} more")

        lines.append("")

    # Recommendations
    lines.extend([
        "---",
        "",
        "## Recommendations",
        "",
    ])

    if delete_count > 0:
        lines.append(f"1. **Delete {delete_count} backup/trivial comments** - These add noise without value")

    if rewrite_count > 0:
        lines.append(f"2. **Address {rewrite_count} debt comments** - Convert TODO/FIXME to proper design docs or issues")

    if total_by_type.get("function", 0) < len(results):
        lines.append("3. **Add docstrings** - Many files lack function/class documentation")

    if total_by_type.get("why", 0) < total_by_type.get("trivial", 0):
        lines.append("4. **More 'why' comments** - Explain reasoning instead of restating code")

    lines.extend([
        "",
        "---",
        "",
        "_Report generated following [antirez commenting standards](https://antirez.com/news/124)_",
    ])

    # Write report
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to: {output_path}")


def _display_path(file_path: str, dir_path: Path) -> str:
    """Path relative to the scanned directory when it is inside it."""
    try:
        return str(Path(file_path).relative_to(Path(dir_path).resolve()))
    except ValueError:
        return str(file_path)


STANDARDS_TEXT = """
# Antirez Commenting Standards

Source: https://antirez.com/news/124

## GOOD Comment Types (Keep/Enhance)

### 1. Function Comments
API documentation at function/class top. Lets readers treat code as black box.

```python
def calculate_position_size(capital: float, risk_percent: float, stop_distance: float) -> float:
    \"\"\"Calculate position size based on fixed-percentage risk model.

    Uses the formula: position_size = (capital * risk_percent) / stop_distance

    Args:
        capital: Total account capital
        risk_percent: Percentage of capital to risk (0.01 = 1%)
        stop_distance: Distance to stop loss in price units

    Returns:
        Number of units to trade

    Example:
        >>> calculate_position_size(10000, 0.02, 50)
        4.0  # Risk $200 with 50-point stop = 4 units
    \"\"\"
```

### 2. Design Comments
At file start, explain algorithms and design choices.

```python
\"\"\"
Order Matching Engine

This module implements a price-time priority matching algorithm.
We chose this over pro-rata matching because:
1. Simpler implementation with predictable behavior
2. Better suited for low-volume markets
3. Matches industry standard (NYSE, NASDAQ)

Alternative considered: Pro-rata matching (CME style)
Rejected because: Our tick sizes don't warrant partial fills
\"\"\"
```

### 3. Why Comments
Explain reasoning, not what code does.

```python
# We retry 3 times because MT5 occasionally returns stale prices
# during high volatility. This was observed during NFP releases
# where first 1-2 requests returned cached data.
for attempt in range(3):
    price = get_current_price()
```

### 4. Teacher Comments
Educate about domain knowledge.

```python
# Sharpe Ratio measures risk-adjusted returns.
# Formula: (portfolio_return - risk_free_rate) / portfolio_std_dev
# Values > 1.0 indicate good risk-adjusted performance.
# See: https://www.investopedia.com/terms/s/sharperatio.asp
sharpe = (returns.mean() - risk_free) / returns.std()
```

### 5. Checklist Comments
Remind of coordinated changes.

```python
# WARNING: If you modify this enum, also update:
# - frontend/src/types/state.ts
# - docs/api/states.md
# - The state machine diagram in ARCHITECTURE.md
class WorkerState(Enum):
    IDLE = "idle"
    RUNNING = "running"
```

### 6. Guide Comments
Lower cognitive load through rhythm.

```python
# === Price Calculation ===

def calculate_entry_price():
    ...

def calculate_exit_price():
    ...

# === Volume Calculation ===

def calculate_position_volume():
    ...
```

---

## BAD Comment Types (Delete/Rewrite)

### 7. Trivial Comments
Restates what code already says.

```python
# BAD - Delete these:
i += 1  # Increment i
return result  # Return the result
for item in items:  # Loop through items

# GOOD - These add value:
i += 1  # Move to next page (API uses 1-based indexing)
return result  # Caller expects list, not generator
```

### 8. Debt Comments
TODO/FIXME without action plan.

```python
# BAD:
# TODO: fix this later
# FIXME: doesn't work sometimes
# XXX: hack

# GOOD - Convert to design comment or issue:
# DESIGN DECISION: Using polling instead of websockets.
# Context: Legacy API doesn't support push notifications. When
# upgrading to v2, evaluate switching to push model.
# Tracking: PROJECT-1234
```

### 9. Backup Comments
Commented-out code.

```python
# BAD - Delete (use git history):
# def old_implementation():
#     return calculate_slow_way()

# GOOD - Explain if keeping temporarily:
# DEPRECATED: Remove after v2.1 release (Jan 2025)
# Kept for rollback safety during migration
# def old_implementation():
```

---

## Quick Reference

| Type | Keep? | Action |
|------|-------|--------|
| Function (docstrings) | YES | Expand if too brief |
| Design (file-level) | YES | Add if missing |
| Why (reasoning) | YES | These are valuable |
| Teacher (domain) | YES | Link to sources |
| Checklist (sync) | YES | Keep updated |
| Guide (structure) | YES | Don't overdo |
| Trivial | NO | Delete |
| Debt | NO | Convert to issue/design |
| Backup | NO | Delete, use git |
"""


def cmd_standards(args: argparse.Namespace) -> None:
    """Display the antirez commenting standards."""
    print(STANDARDS_TEXT)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rewrite_comments.py",
        description="Analyze and rewrite comments following antirez standards.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"rewrite_comments.py, version {VERSION}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # analyze
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze comments in a source file",
        description=(
            "Analyze comments in a source file "
            "(Python/Java/JS/TS/SQL/PL-SQL/Rust).\n\n"
            "Classifies each comment according to antirez taxonomy:\n"
            "- GOOD: function, design, why, teacher, checklist, guide\n"
            "- BAD: trivial, debt, backup"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    analyze_parser.add_argument("file_path", metavar="FILE_PATH", type=_existing_file)
    analyze_parser.add_argument("--report", "-r", action="store_true", help="Generate detailed report")
    analyze_parser.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    analyze_parser.add_argument("--issues-only", "-i", action="store_true", help="Show only issues")
    analyze_parser.set_defaults(func=cmd_analyze)

    # rewrite
    rewrite_parser = subparsers.add_parser(
        "rewrite",
        help="Rewrite comments in a source file",
        description=(
            "Rewrite comments in a source file "
            "(Python/Java/JS/TS/SQL/PL-SQL/Rust).\n\n"
            "By default runs as dry-run showing proposed changes.\n"
            "Use --apply to actually modify the file.\n\n"
            "Actions taken:\n"
            "- DELETE: Remove trivial and backup comments\n"
            "- REWRITE: Add suggested improvements for debt comments"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    rewrite_parser.add_argument("file_path", metavar="FILE_PATH", type=_existing_file)
    rewrite_parser.add_argument("--output", "-o", help="Output file (default: stdout/in-place)")
    rewrite_parser.add_argument("--apply", "-a", action="store_true", help="Apply changes (default: dry run)")
    rewrite_parser.add_argument("--backup", "-b", action="store_true", help="Create .bak backup before modifying")
    rewrite_parser.set_defaults(func=cmd_rewrite)

    # scan
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a directory for comment issues",
        description=(
            "Scan a directory for comment issues across supported languages.\n\n"
            "Analyzes all supported source files "
            "(Python/Java/JS/TS/SQL/PL-SQL/Rust) and reports aggregate "
            "statistics."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    scan_parser.add_argument("directory", metavar="DIRECTORY", type=_existing_dir)
    scan_parser.add_argument("--recursive", "-r", action="store_true", help="Scan recursively")
    scan_parser.add_argument("--issues-only", "-i", action="store_true", help="Show only files with issues")
    scan_parser.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    scan_parser.set_defaults(func=cmd_scan)

    # report
    report_parser = subparsers.add_parser(
        "report",
        help="Generate a comment health report",
        description=(
            "Generate a comprehensive comment health report.\n\n"
            "Creates a markdown report analyzing all supported source files "
            "(Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust) in the "
            "directory."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    report_parser.add_argument("directory", metavar="DIRECTORY", type=_existing_dir)
    report_parser.add_argument("--output", "-o", default="comment_health.md", help="Output file")
    report_parser.add_argument("--recursive", "-r", action="store_true", default=True, help="Scan recursively")
    report_parser.set_defaults(func=cmd_report)

    # standards
    standards_parser = subparsers.add_parser(
        "standards",
        help="Display the antirez commenting standards",
        description=(
            "Display the antirez commenting standards.\n\n"
            "Shows the taxonomy of good vs bad comments with examples."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    standards_parser.set_defaults(func=cmd_standards)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
