#!/usr/bin/env python3
"""
Rewrite Comments CLI for Deep Dive Analysis.

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

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import click

from comment_rewriter import (
    CommentRewriter,
    CommentRewriterError,
)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Analyze and rewrite comments following antirez standards."""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--report", "-r", is_flag=True, help="Generate detailed report")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--issues-only", "-i", is_flag=True, help="Show only issues")
def analyze(file_path: str, report: bool, json_output: bool, issues_only: bool):
    """
    Analyze comments in a Python file.

    Classifies each comment according to antirez taxonomy:
    - GOOD: function, design, why, teacher, checklist, guide
    - BAD: trivial, debt, backup
    """
    rewriter = CommentRewriter()
    file_path = Path(file_path)

    try:
        analysis = rewriter.analyze_file(file_path)
    except CommentRewriterError as e:
        raise click.ClickException(str(e))

    if json_output:
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
        click.echo(json.dumps(output, indent=2))

    elif report:
        click.echo(rewriter.generate_report(analysis))

    elif issues_only:
        if analysis.issues:
            click.echo(f"Issues in {file_path.name}:")
            for issue in analysis.issues:
                click.echo(f"  - {issue}")
        else:
            click.echo(f"No issues found in {file_path.name}")

    else:
        # Summary output
        click.echo(f"File: {file_path.name}")
        click.echo(f"Lines: {analysis.total_lines}, Comments: {analysis.total_comments}")
        click.echo(f"Ratio: {analysis.comment_ratio:.1f} comments per 100 lines")
        click.echo("")

        # Classification summary
        keep = analysis.by_classification.get("keep", 0)
        enhance = analysis.by_classification.get("enhance", 0)
        rewrite = analysis.by_classification.get("rewrite", 0)
        delete = analysis.by_classification.get("delete", 0)

        click.echo(f"[OK] Keep: {keep}")
        click.echo(f"[~]  Enhance: {enhance}")
        click.echo(f"[!]  Rewrite: {rewrite}")
        click.echo(f"[X]  Delete: {delete}")

        if analysis.issues:
            click.echo("")
            click.echo(f"Found {len(analysis.issues)} issue(s). Use --report for details.")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout/in-place)")
@click.option("--apply", "-a", is_flag=True, help="Apply changes (default: dry run)")
@click.option("--backup", "-b", is_flag=True, help="Create .bak backup before modifying")
def rewrite(file_path: str, output: str | None, apply: bool, backup: bool):
    """
    Rewrite comments in a Python file.

    By default runs as dry-run showing proposed changes.
    Use --apply to actually modify the file.

    Actions taken:
    - DELETE: Remove trivial and backup comments
    - REWRITE: Add suggested improvements for debt comments
    """
    rewriter = CommentRewriter()
    file_path = Path(file_path)
    output_path = Path(output) if output else None

    if backup and apply and not output:
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
        click.echo(f"Backup created: {backup_path}")

    try:
        rewritten, changes = rewriter.rewrite_file(
            file_path=file_path,
            output_path=output_path,
            dry_run=not apply,
        )
    except CommentRewriterError as e:
        raise click.ClickException(str(e))

    if changes:
        click.echo("Changes:")
        for change in changes:
            click.echo(f"  - {change}")
    else:
        click.echo("No changes needed.")

    if not apply:
        click.echo("")
        click.echo("This was a dry run. Use --apply to make changes.")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--recursive", "-r", is_flag=True, help="Scan recursively")
@click.option("--issues-only", "-i", is_flag=True, help="Show only files with issues")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def scan(directory: str, recursive: bool, issues_only: bool, json_output: bool):
    """
    Scan a directory for comment issues.

    Analyzes all Python files and reports aggregate statistics.
    """
    rewriter = CommentRewriter()
    dir_path = Path(directory)

    pattern = "**/*.py" if recursive else "*.py"
    files = list(dir_path.glob(pattern))

    # Skip __pycache__ and .venv
    files = [
        f for f in files
        if "__pycache__" not in str(f) and ".venv" not in str(f)
    ]

    if not files:
        click.echo(f"No Python files found in {directory}")
        return

    results = []
    total_issues = 0
    total_delete = 0
    total_rewrite = 0

    with click.progressbar(files, label="Scanning", item_show_func=lambda f: f.name if f else "") as bar:
        for file_path in bar:
            try:
                analysis = rewriter.analyze_file(file_path)
                results.append(analysis)
                total_issues += len(analysis.issues)
                total_delete += analysis.by_classification.get("delete", 0)
                total_rewrite += analysis.by_classification.get("rewrite", 0)
            except CommentRewriterError as e:
                click.echo(f"\nError analyzing {file_path}: {e}", err=True)
            except (OSError, UnicodeDecodeError) as e:
                click.echo(f"\nFile error {file_path}: {e}", err=True)

    if json_output:
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
        click.echo(json.dumps(output, indent=2))

    else:
        click.echo("")
        click.echo(f"Scanned {len(results)} files in {directory}")
        click.echo(f"Total issues: {total_issues}")
        click.echo(f"  - To delete: {total_delete}")
        click.echo(f"  - To rewrite: {total_rewrite}")
        click.echo("")

        # Show files with most issues
        files_with_issues = [a for a in results if a.issues]
        files_with_issues.sort(key=lambda a: len(a.issues), reverse=True)

        if files_with_issues:
            click.echo("Files with most issues:")
            for analysis in files_with_issues[:10]:
                click.echo(f"  {len(analysis.issues):3d} issues: {analysis.file_path}")

        if issues_only and not files_with_issues:
            click.echo("No issues found!")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default="comment_health.md", help="Output file")
@click.option("--recursive", "-r", is_flag=True, default=True, help="Scan recursively")
def report(directory: str, output: str, recursive: bool):
    """
    Generate a comprehensive comment health report.

    Creates a markdown report analyzing all Python files in the directory.
    """
    rewriter = CommentRewriter()
    dir_path = Path(directory)
    output_path = Path(output)

    pattern = "**/*.py" if recursive else "*.py"
    files = list(dir_path.glob(pattern))
    files = [
        f for f in files
        if "__pycache__" not in str(f) and ".venv" not in str(f)
    ]

    if not files:
        click.echo(f"No Python files found in {directory}")
        return

    results = []
    with click.progressbar(files, label="Analyzing", item_show_func=lambda f: f.name if f else "") as bar:
        for file_path in bar:
            try:
                analysis = rewriter.analyze_file(file_path)
                results.append(analysis)
            except CommentRewriterError as e:
                click.echo(f"\nError analyzing {file_path}: {e}", err=True)
            except (OSError, UnicodeDecodeError) as e:
                click.echo(f"\nFile error {file_path}: {e}", err=True)

    # Generate report
    lines = [
        "# Comment Health Report",
        "",
        f"**Directory:** `{dir_path}`",
        f"**Files Analyzed:** {len(results)}",
        f"**Generated by:** deep-dive-analysis/rewrite_comments.py",
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
        f"| Classification | Count | Percentage |",
        f"|----------------|-------|------------|",
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
            rel_path = Path(analysis.file_path).relative_to(dir_path) if str(analysis.file_path).startswith(str(dir_path)) else analysis.file_path
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
            rel_path = Path(file_path).relative_to(dir_path) if str(file_path).startswith(str(dir_path)) else file_path
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
    click.echo(f"Report written to: {output_path}")


@cli.command()
def standards():
    """
    Display the antirez commenting standards.

    Shows the taxonomy of good vs bad comments with examples.
    """
    text = """
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
    click.echo(text)


if __name__ == "__main__":
    cli()