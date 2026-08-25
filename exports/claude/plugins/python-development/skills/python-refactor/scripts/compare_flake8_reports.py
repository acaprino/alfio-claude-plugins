#!/usr/bin/env python3
"""Compare flake8 reports before and after refactoring.

This script compares two flake8 analysis reports (JSON format) to show
improvements or regressions in code quality.

Usage:
    python compare_flake8_reports.py before.json after.json [--html output.html]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any


def load_report(file_path: Path) -> Dict[str, Any]:
    """Load flake8 report from JSON file.

    Args:
        file_path: Path to JSON report file

    Returns:
        Parsed report dictionary
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading report {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def compare_reports(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two flake8 reports and calculate improvements.

    Args:
        before: Report from before refactoring
        after: Report from after refactoring

    Returns:
        Comparison results with improvements/regressions
    """
    # Overall metrics
    total_before = before['total_issues']
    total_after = after['total_issues']
    total_change = total_after - total_before
    total_pct = ((total_before - total_after) / total_before * 100) if total_before > 0 else 0

    # By severity
    severity_comparison = {}
    for severity in ['high', 'medium', 'low']:
        before_count = before['by_severity'].get(severity, 0)
        after_count = after['by_severity'].get(severity, 0)
        change = after_count - before_count
        pct = ((before_count - after_count) / before_count * 100) if before_count > 0 else 0

        severity_comparison[severity] = {
            'before': before_count,
            'after': after_count,
            'change': change,
            'pct_improvement': pct,
            'improved': change <= 0
        }

    # By category
    all_categories = set(before['by_category'].keys()) | set(after['by_category'].keys())
    category_comparison = {}

    for category in all_categories:
        before_count = before['by_category'].get(category, 0)
        after_count = after['by_category'].get(category, 0)
        change = after_count - before_count
        pct = ((before_count - after_count) / before_count * 100) if before_count > 0 else 0

        category_comparison[category] = {
            'before': before_count,
            'after': after_count,
            'change': change,
            'pct_improvement': pct,
            'improved': change <= 0
        }

    # By error code
    all_codes = set(before['statistics'].keys()) | set(after['statistics'].keys())
    code_comparison = {}

    for code in all_codes:
        before_count = before['statistics'].get(code, 0)
        after_count = after['statistics'].get(code, 0)
        change = after_count - before_count
        pct = ((before_count - after_count) / before_count * 100) if before_count > 0 else 0

        code_comparison[code] = {
            'before': before_count,
            'after': after_count,
            'change': change,
            'pct_improvement': pct,
            'improved': change <= 0
        }

    # Issues fixed vs new issues
    fixed_issues = []
    new_issues = []

    # Create signature for each issue
    before_sigs = {
        f"{i['file']}:{i['line']}:{i['code']}"
        for i in before.get('issues', [])
    }
    after_sigs = {
        f"{i['file']}:{i['line']}:{i['code']}"
        for i in after.get('issues', [])
    }

    # Find fixed issues
    for issue in before.get('issues', []):
        sig = f"{issue['file']}:{issue['line']}:{issue['code']}"
        if sig not in after_sigs:
            fixed_issues.append(issue)

    # Find new issues
    for issue in after.get('issues', []):
        sig = f"{issue['file']}:{issue['line']}:{issue['code']}"
        if sig not in before_sigs:
            new_issues.append(issue)

    # Status assessment
    passed_before = before.get('passed', False)
    passed_after = after.get('passed', False)

    if not passed_before and passed_after:
        status = 'IMPROVED - Now Passing'
    elif passed_before and not passed_after:
        status = 'REGRESSED - Now Failing'
    elif passed_after:
        status = 'PASSING - Maintained'
    else:
        status = 'FAILING - Needs Work'

    return {
        'status': status,
        'passed_before': passed_before,
        'passed_after': passed_after,
        'overall': {
            'before': total_before,
            'after': total_after,
            'change': total_change,
            'pct_improvement': total_pct,
            'improved': total_change <= 0
        },
        'by_severity': severity_comparison,
        'by_category': category_comparison,
        'by_code': code_comparison,
        'fixed_issues': fixed_issues,
        'new_issues': new_issues,
        'fixed_count': len(fixed_issues),
        'new_count': len(new_issues),
        'net_improvement': len(fixed_issues) - len(new_issues)
    }


def generate_text_report(comparison: Dict[str, Any]) -> str:
    """Generate human-readable comparison report.

    Args:
        comparison: Comparison results

    Returns:
        Formatted text report
    """
    lines = []

    lines.append("=" * 70)
    lines.append("Flake8 Comparison Report: Before vs After Refactoring")
    lines.append("=" * 70)
    lines.append("")

    # Overall status
    lines.append(f"Status: {comparison['status']}")
    lines.append("")

    # Overall metrics
    overall = comparison['overall']
    symbol = "✓" if overall['improved'] else "✗"
    lines.append("Overall Metrics:")
    lines.append("-" * 70)
    lines.append(f"  Total Issues Before: {overall['before']}")
    lines.append(f"  Total Issues After:  {overall['after']}")
    lines.append(f"  Change: {overall['change']:+d} ({overall['pct_improvement']:+.1f}%) {symbol}")
    lines.append("")

    # Issues fixed vs new
    lines.append("Issue Changes:")
    lines.append("-" * 70)
    lines.append(f"  Issues Fixed: {comparison['fixed_count']}")
    lines.append(f"  New Issues:   {comparison['new_count']}")
    lines.append(f"  Net Improvement: {comparison['net_improvement']:+d}")
    lines.append("")

    # By severity
    lines.append("Issues by Severity:")
    lines.append("-" * 70)
    for severity in ['high', 'medium', 'low']:
        data = comparison['by_severity'][severity]
        symbol = "✓" if data['improved'] else "✗"
        lines.append(
            f"  {severity.upper()}: {data['before']} → {data['after']} "
            f"({data['change']:+d}, {data['pct_improvement']:+.1f}%) {symbol}"
        )
    lines.append("")

    # By category (show biggest improvements/regressions)
    lines.append("Biggest Improvements by Category:")
    lines.append("-" * 70)

    improvements = [
        (cat, data)
        for cat, data in comparison['by_category'].items()
        if data['improved'] and data['change'] < 0
    ]
    improvements.sort(key=lambda x: x[1]['pct_improvement'], reverse=True)

    if improvements:
        for category, data in improvements[:10]:
            lines.append(
                f"  {category}: {data['before']} → {data['after']} "
                f"({data['pct_improvement']:+.1f}% improvement) ✓"
            )
    else:
        lines.append("  No improvements")
    lines.append("")

    # Regressions
    regressions = [
        (cat, data)
        for cat, data in comparison['by_category'].items()
        if not data['improved']
    ]
    regressions.sort(key=lambda x: x[1]['change'], reverse=True)

    if regressions:
        lines.append("Regressions by Category:")
        lines.append("-" * 70)
        for category, data in regressions:
            lines.append(
                f"  {category}: {data['before']} → {data['after']} "
                f"({data['change']:+d}) ✗"
            )
        lines.append("")

    # Top code improvements
    lines.append("Top Error Code Improvements:")
    lines.append("-" * 70)

    code_improvements = [
        (code, data)
        for code, data in comparison['by_code'].items()
        if data['improved'] and data['change'] < 0
    ]
    code_improvements.sort(key=lambda x: abs(x[1]['change']), reverse=True)

    if code_improvements:
        for code, data in code_improvements[:10]:
            lines.append(
                f"  {code}: {data['before']} → {data['after']} "
                f"({data['change']:+d}) ✓"
            )
    else:
        lines.append("  No improvements")
    lines.append("")

    # Sample fixed issues
    if comparison['fixed_issues']:
        lines.append("Sample Fixed Issues:")
        lines.append("-" * 70)
        for issue in comparison['fixed_issues'][:10]:
            lines.append(
                f"  ✓ {issue['file']}:{issue['line']} {issue['code']} "
                f"[{issue['severity']}] - {issue['message']}"
            )
        if len(comparison['fixed_issues']) > 10:
            lines.append(f"  ... and {len(comparison['fixed_issues']) - 10} more")
        lines.append("")

    # New issues (warnings)
    if comparison['new_issues']:
        lines.append("New Issues Introduced:")
        lines.append("-" * 70)
        for issue in comparison['new_issues'][:10]:
            lines.append(
                f"  ✗ {issue['file']}:{issue['line']} {issue['code']} "
                f"[{issue['severity']}] - {issue['message']}"
            )
        if len(comparison['new_issues']) > 10:
            lines.append(f"  ... and {len(comparison['new_issues']) - 10} more")
        lines.append("")

    # Summary
    lines.append("=" * 70)
    lines.append("Summary:")
    lines.append("-" * 70)

    if comparison['net_improvement'] > 0:
        lines.append(f"✓ Net improvement of {comparison['net_improvement']} issues")
    elif comparison['net_improvement'] < 0:
        lines.append(f"✗ Net regression of {abs(comparison['net_improvement'])} issues")
    else:
        lines.append("= No net change in issue count")

    if comparison['overall']['improved']:
        lines.append(f"✓ Total issues reduced by {comparison['overall']['pct_improvement']:.1f}%")
    else:
        lines.append("✗ Total issues increased")

    lines.append("")
    lines.append("=" * 70)

    return '\n'.join(lines)


def generate_html_report(comparison: Dict[str, Any]) -> str:
    """Generate HTML comparison report.

    Args:
        comparison: Comparison results

    Returns:
        HTML report string
    """
    improved_color = '#27ae60'
    regressed_color = '#e74c3c'
    neutral_color = '#95a5a6'

    overall = comparison['overall']
    status_color = improved_color if overall['improved'] else regressed_color

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Flake8 Comparison Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .status {{
            font-size: 24px;
            font-weight: bold;
            color: {status_color};
            margin: 20px 0;
            padding: 20px;
            background: #ecf0f1;
            border-radius: 6px;
            text-align: center;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            padding: 20px;
            border-radius: 6px;
            background: #ecf0f1;
            border-left: 4px solid {neutral_color};
        }}
        .metric-card.improved {{ border-left-color: {improved_color}; }}
        .metric-card.regressed {{ border-left-color: {regressed_color}; }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #7f8c8d;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-change {{
            margin-top: 5px;
            font-size: 16px;
        }}
        .metric-change.positive {{ color: {improved_color}; }}
        .metric-change.negative {{ color: {regressed_color}; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background: #34495e;
            color: white;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .improved-row {{ background: #d5f4e6; }}
        .regressed-row {{ background: #fadbd8; }}
        .issue-list {{
            margin: 20px 0;
        }}
        .issue {{
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #bdc3c7;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 14px;
        }}
        .issue.fixed {{ border-left-color: {improved_color}; }}
        .issue.new {{ border-left-color: {regressed_color}; }}
        .severity-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            color: white;
            margin-left: 5px;
        }}
        .severity-high {{ background: #e74c3c; }}
        .severity-medium {{ background: #f39c12; }}
        .severity-low {{ background: #3498db; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Flake8 Comparison: Before vs After Refactoring</h1>

        <div class="status">{comparison['status']}</div>

        <div class="metrics">
            <div class="metric-card {'improved' if overall['improved'] else 'regressed'}">
                <h3>Total Issues</h3>
                <div class="metric-value">{overall['before']} → {overall['after']}</div>
                <div class="metric-change {'positive' if overall['improved'] else 'negative'}">
                    {overall['change']:+d} ({overall['pct_improvement']:+.1f}%)
                </div>
            </div>

            <div class="metric-card {'improved' if comparison['net_improvement'] > 0 else 'regressed' if comparison['net_improvement'] < 0 else ''}">
                <h3>Net Improvement</h3>
                <div class="metric-value">{comparison['net_improvement']:+d}</div>
                <div style="margin-top: 5px; font-size: 14px;">
                    Fixed: {comparison['fixed_count']} | New: {comparison['new_count']}
                </div>
            </div>
        </div>

        <h2>Issues by Severity</h2>
        <table>
            <tr>
                <th>Severity</th>
                <th>Before</th>
                <th>After</th>
                <th>Change</th>
                <th>Improvement</th>
            </tr>
"""

    for severity in ['high', 'medium', 'low']:
        data = comparison['by_severity'][severity]
        row_class = 'improved-row' if data['improved'] else 'regressed-row' if data['change'] > 0 else ''
        symbol = '✓' if data['improved'] else '✗'
        html += f"""
            <tr class="{row_class}">
                <td><span class="severity-badge severity-{severity}">{severity.upper()}</span></td>
                <td>{data['before']}</td>
                <td>{data['after']}</td>
                <td>{data['change']:+d}</td>
                <td>{data['pct_improvement']:+.1f}% {symbol}</td>
            </tr>
"""

    html += "</table>"

    # Category improvements
    improvements = [(cat, data) for cat, data in comparison['by_category'].items() if data['improved'] and data['change'] < 0]
    improvements.sort(key=lambda x: abs(x[1]['change']), reverse=True)

    if improvements:
        html += "<h2>Top Category Improvements</h2><table>"
        html += "<tr><th>Category</th><th>Before</th><th>After</th><th>Change</th><th>Improvement</th></tr>"
        for category, data in improvements[:10]:
            html += f"""
                <tr class="improved-row">
                    <td>{category}</td>
                    <td>{data['before']}</td>
                    <td>{data['after']}</td>
                    <td>{data['change']:+d}</td>
                    <td>{data['pct_improvement']:+.1f}% ✓</td>
                </tr>
            """
        html += "</table>"

    # Fixed issues
    if comparison['fixed_issues']:
        html += f"<h2>Fixed Issues ({len(comparison['fixed_issues'])})</h2>"
        html += '<div class="issue-list">'
        for issue in comparison['fixed_issues'][:30]:
            html += f"""
                <div class="issue fixed">
                    ✓ <strong>{issue['code']}</strong>
                    <span class="severity-badge severity-{issue['severity']}">{issue['severity']}</span>
                    {issue['file']}:{issue['line']} - {issue['message']}
                </div>
            """
        if len(comparison['fixed_issues']) > 30:
            html += f'<p>... and {len(comparison["fixed_issues"]) - 30} more fixed issues</p>'
        html += '</div>'

    # New issues
    if comparison['new_issues']:
        html += f"<h2>New Issues ({len(comparison['new_issues'])})</h2>"
        html += '<div class="issue-list">'
        for issue in comparison['new_issues'][:30]:
            html += f"""
                <div class="issue new">
                    ✗ <strong>{issue['code']}</strong>
                    <span class="severity-badge severity-{issue['severity']}">{issue['severity']}</span>
                    {issue['file']}:{issue['line']} - {issue['message']}
                </div>
            """
        if len(comparison['new_issues']) > 30:
            html += f'<p>... and {len(comparison["new_issues"]) - 30} more new issues</p>'
        html += '</div>'

    html += """
    </div>
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Compare flake8 reports before and after refactoring"
    )
    parser.add_argument(
        "before_report",
        type=Path,
        help="JSON report from before refactoring"
    )
    parser.add_argument(
        "after_report",
        type=Path,
        help="JSON report from after refactoring"
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="Output HTML comparison report"
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Output JSON comparison data"
    )

    args = parser.parse_args()

    # Load reports
    before = load_report(args.before_report)
    after = load_report(args.after_report)

    # Compare
    comparison = compare_reports(before, after)

    # Generate text report
    text_report = generate_text_report(comparison)
    print(text_report)

    # Save HTML if requested
    if args.html:
        html_report = generate_html_report(comparison)
        with open(args.html, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"\nHTML report saved to: {args.html}")

    # Save JSON if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"JSON comparison saved to: {args.json}")

    # Exit code based on whether we improved
    sys.exit(0 if comparison['overall']['improved'] else 1)


if __name__ == "__main__":
    main()
