#!/usr/bin/env python3
"""Comprehensive code analysis using flake8 with plugins.

This script runs flake8 with recommended plugins to perform thorough
code quality analysis before and after refactoring.

Recommended flake8 plugins:
- flake8-bugbear: Finds likely bugs and design problems
- flake8-comprehensions: Checks for unnecessary comprehensions
- flake8-docstrings: Checks docstring conventions (pydocstyle)
- flake8-simplify: Suggests code simplifications
- flake8-cognitive-complexity: Measures cognitive complexity
- flake8-expression-complexity: Checks expression complexity
- flake8-annotations: Validates type annotations
- flake8-broken-line: Checks line breaks
- pep8-naming: Checks PEP 8 naming conventions

Usage:
    python analyze_with_flake8.py <file_or_directory> [--output report.json] [--html]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


# Recommended flake8 plugins organized by priority for human-readable code
ESSENTIAL_PLUGINS = {
    'flake8-bugbear': 'Finds likely bugs and design problems (B codes)',
    'flake8-simplify': 'Suggests simpler, clearer code (SIM codes)',
    'flake8-cognitive-complexity': 'Measures cognitive load (CCR codes)',
    'pep8-naming': 'Enforces clear naming conventions (N codes)',
    'flake8-docstrings': 'Ensures documentation (D codes)',
}

RECOMMENDED_PLUGINS = {
    **ESSENTIAL_PLUGINS,
    'flake8-comprehensions': 'Cleaner comprehensions (C4 codes)',
    'flake8-expression-complexity': 'Prevents complex expressions (ECE codes)',
    'flake8-functions': 'Simpler function signatures (CFQ codes)',
    'flake8-variables-names': 'Better variable naming (VNE codes)',
    'tryceratops': 'Clean exception handling (TC codes)',
}

OPTIONAL_PLUGINS = {
    'flake8-builtins': 'Prevents shadowing built-ins (A codes)',
    'flake8-eradicate': 'Finds commented-out code (E800 codes)',
    'flake8-unused-arguments': 'Flags unused parameters (U codes)',
    'flake8-annotations': 'Validates type hints (ANN codes)',
    'pydoclint': 'Complete docstrings (DOC codes)',
    'flake8-spellcheck': 'Catches typos (SC codes)',
}

ALL_PLUGINS = {**RECOMMENDED_PLUGINS, **OPTIONAL_PLUGINS}


def check_flake8_installed() -> bool:
    """Check if flake8 is installed."""
    try:
        result = subprocess.run(
            ['flake8', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_plugins_installed() -> Dict[str, bool]:
    """Check which recommended plugins are installed.

    Returns:
        Dictionary mapping plugin name to installation status
    """
    installed = {}

    try:
        result = subprocess.run(
            ['flake8', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        version_output = result.stdout.lower()

        for plugin in ALL_PLUGINS:
            # Check if plugin name appears in version output
            plugin_name = plugin.replace('flake8-', '').replace('-', '')
            installed[plugin] = plugin_name in version_output

    except (subprocess.TimeoutExpired, FileNotFoundError):
        installed = {plugin: False for plugin in ALL_PLUGINS}

    return installed


def run_flake8_analysis(
    target_path: Path,
    max_complexity: int = 10,
    max_cognitive_complexity: int = 10,
    max_expression_complexity: int = 7,
    ignore_codes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Run flake8 analysis on target path.

    Args:
        target_path: File or directory to analyze
        max_complexity: Maximum cyclomatic complexity threshold
        max_cognitive_complexity: Maximum cognitive complexity threshold
        max_expression_complexity: Maximum expression complexity threshold
        ignore_codes: List of error codes to ignore

    Returns:
        Dictionary with analysis results
    """
    if not check_flake8_installed():
        return {
            'error': 'flake8 is not installed',
            'install_command': 'pip install flake8'
        }

    # Build flake8 command
    cmd = [
        'flake8',
        str(target_path),
        '--max-complexity', str(max_complexity),
        '--statistics',
        '--count',
        '--show-source',
        '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s'
    ]

    # Add cognitive complexity if plugin installed
    installed_plugins = check_plugins_installed()
    if installed_plugins.get('flake8-cognitive-complexity'):
        cmd.extend(['--max-cognitive-complexity', str(max_cognitive_complexity)])

    # Add expression complexity if plugin installed
    if installed_plugins.get('flake8-expression-complexity'):
        cmd.extend(['--max-expression-complexity', str(max_expression_complexity)])

    # Add ignore codes if specified
    if ignore_codes:
        cmd.extend(['--ignore', ','.join(ignore_codes)])

    # Run flake8
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        return parse_flake8_output(
            result.stdout,
            result.stderr,
            result.returncode,
            target_path,
            installed_plugins
        )

    except subprocess.TimeoutExpired:
        return {
            'error': 'flake8 analysis timed out (>5 minutes)',
            'target': str(target_path)
        }
    except Exception as e:
        return {
            'error': f'Failed to run flake8: {e}',
            'target': str(target_path)
        }


def parse_flake8_output(
    stdout: str,
    stderr: str,
    returncode: int,
    target_path: Path,
    installed_plugins: Dict[str, bool]
) -> Dict[str, Any]:
    """Parse flake8 output into structured format.

    Args:
        stdout: Standard output from flake8
        stderr: Standard error from flake8
        returncode: Exit code from flake8
        target_path: Path that was analyzed
        installed_plugins: Dictionary of installed plugins

    Returns:
        Structured analysis results
    """
    issues = []
    statistics = {}

    lines = stdout.strip().split('\n')

    for line in lines:
        if not line.strip():
            continue

        # Parse issue line: path:row:col: CODE message
        match = re.match(r'^(.+?):(\d+):(\d+):\s+([A-Z]+\d+)\s+(.+)$', line)
        if match:
            file_path, row, col, code, message = match.groups()
            issues.append({
                'file': file_path,
                'line': int(row),
                'column': int(col),
                'code': code,
                'message': message.strip(),
                'severity': categorize_issue_severity(code),
                'category': categorize_issue(code)
            })
        elif ':' in line and line.split(':')[0].strip().isdigit():
            # Statistics line: "123 E501 line too long"
            parts = line.split(None, 2)
            if len(parts) >= 2:
                count = parts[0]
                code = parts[1]
                if count.isdigit():
                    statistics[code] = int(count)

    # Group issues by category
    by_category = {}
    by_severity = {}
    by_file = {}

    for issue in issues:
        category = issue['category']
        severity = issue['severity']
        file_path = issue['file']

        by_category[category] = by_category.get(category, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_file[file_path] = by_file.get(file_path, 0) + 1

    return {
        'target': str(target_path),
        'timestamp': datetime.now().isoformat(),
        'total_issues': len(issues),
        'exit_code': returncode,
        'passed': returncode == 0,
        'issues': issues,
        'statistics': statistics,
        'by_category': by_category,
        'by_severity': by_severity,
        'by_file': by_file,
        'installed_plugins': installed_plugins,
        'errors': stderr if stderr else None
    }


def categorize_issue(code: str) -> str:
    """Categorize flake8 issue by code prefix.

    Args:
        code: Flake8 error/warning code (e.g., E501, W503)

    Returns:
        Category name
    """
    prefix = code[0] if code else 'U'

    categories = {
        'E': 'Style Error (PEP 8)',
        'W': 'Style Warning (PEP 8)',
        'F': 'PyFlakes Error',
        'C': 'Complexity',
        'B': 'Bugbear (Likely Bug)',
        'N': 'Naming Convention',
        'D': 'Docstring',
        'A': 'Annotations',
        'S': 'Simplification',
        'T': 'Type Checking',
    }

    return categories.get(prefix, 'Other')


def categorize_issue_severity(code: str) -> str:
    """Determine severity level of issue.

    Args:
        code: Flake8 error/warning code

    Returns:
        Severity level (high/medium/low)
    """
    # High severity: Likely bugs, security issues
    high_severity = [
        'F', 'B',  # PyFlakes errors, Bugbear
        'E9',  # Runtime errors
    ]

    # Medium severity: Complexity, bad practices
    medium_severity = [
        'C',  # Complexity
        'N',  # Naming
        'A',  # Annotations
    ]

    # Check code prefix
    for prefix in high_severity:
        if code.startswith(prefix):
            return 'high'

    for prefix in medium_severity:
        if code.startswith(prefix):
            return 'medium'

    return 'low'


def generate_summary_report(analysis: Dict[str, Any]) -> str:
    """Generate human-readable summary report.

    Args:
        analysis: Parsed analysis results

    Returns:
        Formatted text report
    """
    lines = []

    lines.append("=" * 70)
    lines.append("Flake8 Code Quality Analysis Report")
    lines.append("=" * 70)
    lines.append("")

    lines.append(f"Target: {analysis['target']}")
    lines.append(f"Timestamp: {analysis['timestamp']}")
    lines.append(f"Result: {'PASSED' if analysis['passed'] else 'FAILED'}")
    lines.append(f"Total Issues: {analysis['total_issues']}")
    lines.append("")

    # Installed plugins organized by priority
    lines.append("Installed Plugins:")
    lines.append("-" * 70)
    installed_plugins = analysis['installed_plugins']

    lines.append("ESSENTIAL (Must-Have):")
    for plugin, description in ESSENTIAL_PLUGINS.items():
        status = "✓" if installed_plugins.get(plugin) else "✗"
        lines.append(f"  {status} {plugin}: {description}")

    lines.append("\nRECOMMENDED (Strong Impact):")
    for plugin, description in RECOMMENDED_PLUGINS.items():
        if plugin not in ESSENTIAL_PLUGINS:
            status = "✓" if installed_plugins.get(plugin) else "✗"
            lines.append(f"  {status} {plugin}: {description}")

    lines.append("\nOPTIONAL (Nice to Have):")
    for plugin, description in OPTIONAL_PLUGINS.items():
        status = "✓" if installed_plugins.get(plugin) else "✗"
        lines.append(f"  {status} {plugin}: {description}")
    lines.append("")

    # Missing plugins warning
    missing_essential = [p for p in ESSENTIAL_PLUGINS if not installed_plugins.get(p)]
    missing_recommended = [p for p in RECOMMENDED_PLUGINS if p not in ESSENTIAL_PLUGINS and not installed_plugins.get(p)]
    missing_optional = [p for p in OPTIONAL_PLUGINS if not installed_plugins.get(p)]

    if missing_essential:
        lines.append("⚠ Missing ESSENTIAL Plugins (install these first):")
        for plugin in missing_essential:
            lines.append(f"  - {plugin}")
        lines.append(f"\nInstall: pip install {' '.join(missing_essential)}")
        lines.append("")

    if missing_recommended:
        lines.append("⚠ Missing RECOMMENDED Plugins:")
        for plugin in missing_recommended:
            lines.append(f"  - {plugin}")
        lines.append(f"\nInstall: pip install {' '.join(missing_recommended)}")
        lines.append("")

    # Issues by severity
    if analysis['by_severity']:
        lines.append("Issues by Severity:")
        lines.append("-" * 70)
        for severity in ['high', 'medium', 'low']:
            count = analysis['by_severity'].get(severity, 0)
            if count > 0:
                symbol = "✗" if severity == 'high' else "⚠" if severity == 'medium' else "•"
                lines.append(f"  {symbol} {severity.upper()}: {count}")
        lines.append("")

    # Issues by category
    if analysis['by_category']:
        lines.append("Issues by Category:")
        lines.append("-" * 70)
        for category, count in sorted(
            analysis['by_category'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            lines.append(f"  {category}: {count}")
        lines.append("")

    # Top issues
    if analysis['statistics']:
        lines.append("Top Issue Types:")
        lines.append("-" * 70)
        sorted_stats = sorted(
            analysis['statistics'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for code, count in sorted_stats[:10]:
            lines.append(f"  {code}: {count} occurrence(s)")
        lines.append("")

    # Files with most issues
    if analysis['by_file']:
        lines.append("Files with Most Issues:")
        lines.append("-" * 70)
        sorted_files = sorted(
            analysis['by_file'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for file_path, count in sorted_files[:10]:
            lines.append(f"  {file_path}: {count} issue(s)")
        lines.append("")

    # Detailed issues
    if analysis['issues']:
        lines.append("Detailed Issues:")
        lines.append("-" * 70)

        # Group by severity and show high severity first
        high_issues = [i for i in analysis['issues'] if i['severity'] == 'high']
        medium_issues = [i for i in analysis['issues'] if i['severity'] == 'medium']
        low_issues = [i for i in analysis['issues'] if i['severity'] == 'low']

        for severity_label, issues in [
            ('HIGH SEVERITY', high_issues),
            ('MEDIUM SEVERITY', medium_issues),
            ('LOW SEVERITY (First 20)', low_issues[:20])
        ]:
            if issues:
                lines.append(f"\n{severity_label}:")
                for issue in issues:
                    lines.append(
                        f"  {issue['file']}:{issue['line']}:{issue['column']} "
                        f"{issue['code']} {issue['message']}"
                    )

    lines.append("")
    lines.append("=" * 70)

    return '\n'.join(lines)


def generate_html_report(analysis: Dict[str, Any]) -> str:
    """Generate HTML report.

    Args:
        analysis: Parsed analysis results

    Returns:
        HTML report string
    """
    severity_colors = {
        'high': '#e74c3c',
        'medium': '#f39c12',
        'low': '#3498db'
    }

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Flake8 Analysis Report</title>
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
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            padding: 20px;
            border-radius: 6px;
            background: #ecf0f1;
        }}
        .summary-card.passed {{ background: #d5f4e6; }}
        .summary-card.failed {{ background: #fadbd8; }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #7f8c8d;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            margin-right: 5px;
        }}
        .severity-high {{ background: {severity_colors['high']}; }}
        .severity-medium {{ background: {severity_colors['medium']}; }}
        .severity-low {{ background: {severity_colors['low']}; }}
        .issue-list {{
            margin: 20px 0;
        }}
        .issue {{
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #bdc3c7;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .issue.high {{ border-left-color: {severity_colors['high']}; }}
        .issue.medium {{ border-left-color: {severity_colors['medium']}; }}
        .issue.low {{ border-left-color: {severity_colors['low']}; }}
        .issue-code {{
            font-family: monospace;
            background: #2c3e50;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }}
        .issue-location {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .plugin-list {{
            list-style: none;
            padding: 0;
        }}
        .plugin-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        .plugin-installed {{ color: #27ae60; }}
        .plugin-missing {{ color: #e74c3c; }}
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Flake8 Code Quality Analysis Report</h1>

        <div class="summary">
            <div class="summary-card {'passed' if analysis['passed'] else 'failed'}">
                <h3>Status</h3>
                <div class="value">{'PASSED' if analysis['passed'] else 'FAILED'}</div>
            </div>
            <div class="summary-card">
                <h3>Total Issues</h3>
                <div class="value">{analysis['total_issues']}</div>
            </div>
            <div class="summary-card">
                <h3>Target</h3>
                <div style="font-size: 14px; word-break: break-all;">{analysis['target']}</div>
            </div>
            <div class="summary-card">
                <h3>Timestamp</h3>
                <div style="font-size: 14px;">{analysis['timestamp']}</div>
            </div>
        </div>
"""

    # Issues by severity
    if analysis['by_severity']:
        html += "<h2>Issues by Severity</h2>"
        html += '<div style="margin: 20px 0;">'
        for severity in ['high', 'medium', 'low']:
            count = analysis['by_severity'].get(severity, 0)
            if count > 0:
                html += f'<span class="severity-badge severity-{severity}">{severity.upper()}: {count}</span>'
        html += '</div>'

    # Installed plugins organized by priority
    html += "<h2>Installed Plugins</h2>"

    html += "<h3>Essential (Must-Have)</h3>"
    html += '<ul class="plugin-list">'
    for plugin, description in ESSENTIAL_PLUGINS.items():
        installed = analysis['installed_plugins'].get(plugin, False)
        status_class = 'plugin-installed' if installed else 'plugin-missing'
        status_symbol = '✓' if installed else '✗'
        html += f'<li class="{status_class}"><strong>{status_symbol} {plugin}</strong>: {description}</li>'
    html += '</ul>'

    html += "<h3>Recommended (Strong Impact)</h3>"
    html += '<ul class="plugin-list">'
    for plugin, description in RECOMMENDED_PLUGINS.items():
        if plugin not in ESSENTIAL_PLUGINS:
            installed = analysis['installed_plugins'].get(plugin, False)
            status_class = 'plugin-installed' if installed else 'plugin-missing'
            status_symbol = '✓' if installed else '✗'
            html += f'<li class="{status_class}"><strong>{status_symbol} {plugin}</strong>: {description}</li>'
    html += '</ul>'

    html += "<h3>Optional (Nice to Have)</h3>"
    html += '<ul class="plugin-list">'
    for plugin, description in OPTIONAL_PLUGINS.items():
        installed = analysis['installed_plugins'].get(plugin, False)
        status_class = 'plugin-installed' if installed else 'plugin-missing'
        status_symbol = '✓' if installed else '✗'
        html += f'<li class="{status_class}"><strong>{status_symbol} {plugin}</strong>: {description}</li>'
    html += '</ul>'

    # Top issues table
    if analysis['statistics']:
        html += "<h2>Top Issue Types</h2>"
        html += "<table>"
        html += "<tr><th>Code</th><th>Occurrences</th><th>Category</th></tr>"
        sorted_stats = sorted(analysis['statistics'].items(), key=lambda x: x[1], reverse=True)
        for code, count in sorted_stats[:15]:
            category = categorize_issue(code)
            html += f"<tr><td><span class='issue-code'>{code}</span></td><td>{count}</td><td>{category}</td></tr>"
        html += "</table>"

    # Detailed issues
    if analysis['issues']:
        html += "<h2>Detailed Issues</h2>"

        # Group by severity
        for severity in ['high', 'medium', 'low']:
            severity_issues = [i for i in analysis['issues'] if i['severity'] == severity]
            if severity_issues:
                limit = 50 if severity == 'high' else 30 if severity == 'medium' else 20
                html += f"<h3>{severity.upper()} Severity Issues</h3>"
                html += '<div class="issue-list">'
                for issue in severity_issues[:limit]:
                    html += f'''
                    <div class="issue {severity}">
                        <div>
                            <span class="issue-code">{issue['code']}</span>
                            <span class="severity-badge severity-{severity}">{severity.upper()}</span>
                            <span class="issue-location">{issue['file']}:{issue['line']}:{issue['column']}</span>
                        </div>
                        <div style="margin-top: 8px;">{issue['message']}</div>
                        <div style="margin-top: 4px; color: #7f8c8d; font-size: 13px;">Category: {issue['category']}</div>
                    </div>
                    '''
                if len(severity_issues) > limit:
                    html += f'<div style="padding: 10px; color: #7f8c8d;">... and {len(severity_issues) - limit} more {severity} severity issues</div>'
                html += '</div>'

    html += """
    </div>
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive code analysis using flake8 with plugins"
    )
    parser.add_argument(
        "target",
        type=Path,
        help="File or directory to analyze"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for JSON report"
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="Output file for HTML report"
    )
    parser.add_argument(
        "--max-complexity",
        type=int,
        default=10,
        help="Maximum cyclomatic complexity (default: 10)"
    )
    parser.add_argument(
        "--max-cognitive-complexity",
        type=int,
        default=10,
        help="Maximum cognitive complexity (default: 10)"
    )
    parser.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated list of error codes to ignore"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal console output"
    )

    args = parser.parse_args()

    if not args.target.exists():
        print(f"Error: Target not found: {args.target}", file=sys.stderr)
        sys.exit(1)

    # Parse ignore codes
    ignore_codes = args.ignore.split(',') if args.ignore else None

    # Run analysis
    analysis = run_flake8_analysis(
        args.target,
        max_complexity=args.max_complexity,
        max_cognitive_complexity=args.max_cognitive_complexity,
        ignore_codes=ignore_codes
    )

    # Check for errors
    if 'error' in analysis:
        print(f"Error: {analysis['error']}", file=sys.stderr)
        if 'install_command' in analysis:
            print(f"Install with: {analysis['install_command']}", file=sys.stderr)
        sys.exit(1)

    # Save JSON report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2)
        if not args.quiet:
            print(f"JSON report saved to: {args.output}")

    # Save HTML report
    if args.html:
        html_content = generate_html_report(analysis)
        with open(args.html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        if not args.quiet:
            print(f"HTML report saved to: {args.html}")

    # Print summary to console
    if not args.quiet:
        summary = generate_summary_report(analysis)
        print(summary)

    # Exit with appropriate code
    sys.exit(0 if analysis['passed'] else 1)


if __name__ == "__main__":
    main()
