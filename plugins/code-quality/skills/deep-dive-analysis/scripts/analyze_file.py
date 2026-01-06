#!/usr/bin/env python3
"""
Analyze File CLI for Deep Dive Analysis.

Main entry point for analyzing Python files following DEEP_DIVE_PLAN methodology.

Usage:
    python analyze_file.py --file <path> [options]
    python analyze_file.py --symbol <name> --file <path>
    python analyze_file.py --phase <num>
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from classifier import classify_file
from ast_parser import parse_file
from progress_tracker import ProgressTracker
from usage_finder import find_all_usages

__all__ = ["analyze_single_file", "format_as_markdown", "format_as_summary"]

logger = logging.getLogger(__name__)


def analyze_single_file(
    file_path: Path,
    find_usages: bool = False,
    update_progress: bool = False,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """
    Perform complete analysis of a single file.

    Args:
        file_path: Path to the Python file
        find_usages: Whether to find usages of exported symbols
        update_progress: Whether to update analysis_progress.json
        project_root: Root of the project (for usage finding)

    Returns:
        Dict with complete analysis results
    """
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    if not file_path.suffix == ".py":
        return {"error": f"Not a Python file: {file_path}"}

    # Step 1: Classify
    classification = classify_file(file_path)

    # Step 2: Parse structure
    try:
        structure = parse_file(file_path)
    except SyntaxError as e:
        return {
            "error": f"Syntax error in file: {e}",
            "classification": classification.classification.value,
        }

    # Step 3: Find usages (if requested)
    usages = {}
    if find_usages and structure.exported_symbols:
        for symbol in structure.exported_symbols[:5]:  # Limit to first 5 symbols
            usage_result = find_all_usages(symbol, file_path, project_root)
            usages[symbol] = {
                "count": len(usage_result.usages),
                "importing_modules": usage_result.importing_modules,
                "sample_usages": [
                    {
                        "file": u.file_path,
                        "line": u.line_number,
                        "type": u.usage_type,
                    }
                    for u in usage_result.usages[:5]
                ],
            }

    # Step 4: Update progress (if requested)
    progress_warning = None
    if update_progress:
        try:
            tracker = ProgressTracker(project_root / "analysis_progress.json" if project_root else Path("analysis_progress.json"))
            tracker.load()

            # Calculate relative path
            if project_root:
                rel_path = str(file_path.relative_to(project_root))
            else:
                rel_path = str(file_path)

            tracker.update_file(
                rel_path,
                status="done",
                classification=classification.classification.value,
                verification_required=classification.verification_required,
            )
            tracker.save()
        except FileNotFoundError as e:
            progress_warning = f"Progress file not found: {e}"
            logger.warning(progress_warning)
        except (OSError, json.JSONDecodeError) as e:
            progress_warning = f"Failed to update progress: {e}"
            logger.warning(progress_warning)

    # Build result
    result = {
        "file": str(file_path),
        "classification": {
            "level": classification.classification.value,
            "lines_of_code": classification.lines_of_code,
            "num_dependencies": classification.num_dependencies,
            "verification_required": classification.verification_required,
            "reasoning": classification.reasoning,
            "critical_patterns": len(classification.critical_patterns_found),
            "complexity_indicators": len(classification.complexity_indicators),
        },
        "structure": {
            "classes": [
                {
                    "name": c.name,
                    "bases": c.bases,
                    "methods": [
                        {
                            "name": m.name,
                            "is_async": m.is_async,
                            "params": [p.name for p in m.parameters],
                        }
                        for m in c.methods
                    ],
                    "class_variables": c.class_variables,
                    "line": c.line_number,
                    "docstring": c.docstring[:100] if c.docstring else None,
                }
                for c in structure.classes
            ],
            "functions": [
                {
                    "name": f.name,
                    "is_async": f.is_async,
                    "params": [p.name for p in f.parameters],
                    "return_type": f.return_annotation,
                    "line": f.line_number,
                }
                for f in structure.functions
            ],
            "constants": structure.constants,
            "exported_symbols": structure.exported_symbols,
        },
        "dependencies": {
            "internal": list(
                set(i.module for i in structure.imports if i.is_internal)
            ),
            "external": list(
                set(i.module for i in structure.imports if not i.is_internal and i.module)
            ),
        },
        "external_calls": {
            call_type: [
                {"pattern": c.pattern, "line": c.line_number}
                for c in structure.external_calls
                if c.call_type == call_type
            ]
            for call_type in ["database", "network", "filesystem", "amqp", "zmq"]
            if any(c.call_type == call_type for c in structure.external_calls)
        },
    }

    if usages:
        result["usages"] = usages

    if progress_warning:
        result["warning"] = progress_warning

    return result


def format_as_markdown(analysis: dict[str, Any]) -> str:
    """Format analysis result as Markdown."""
    if "error" in analysis:
        return f"## Error\n\n{analysis['error']}"

    lines = []

    # Header
    file_name = Path(analysis["file"]).name
    lines.append(f"# Analysis: {file_name}")
    lines.append("")

    # Classification
    cls = analysis["classification"]
    lines.append("## Classification")
    lines.append("")
    lines.append(f"- **Level:** {cls['level'].upper()}")
    lines.append(f"- **Lines of Code:** {cls['lines_of_code']}")
    lines.append(f"- **Dependencies:** {cls['num_dependencies']}")
    lines.append(f"- **Verification Required:** {'Yes' if cls['verification_required'] else 'No'}")
    lines.append(f"- **Reasoning:** {cls['reasoning']}")
    lines.append("")

    # Structure - Classes
    if analysis["structure"]["classes"]:
        lines.append("## Classes")
        lines.append("")
        for cls_info in analysis["structure"]["classes"]:
            bases = f"({', '.join(cls_info['bases'])})" if cls_info['bases'] else ""
            lines.append(f"### `{cls_info['name']}{bases}`")
            lines.append("")
            if cls_info.get("docstring"):
                lines.append(f"> {cls_info['docstring']}")
                lines.append("")
            lines.append(f"*Line {cls_info['line']}*")
            lines.append("")

            if cls_info["class_variables"]:
                lines.append("**Class Variables:**")
                for var in cls_info["class_variables"]:
                    lines.append(f"- `{var}`")
                lines.append("")

            if cls_info["methods"]:
                lines.append("**Methods:**")
                for method in cls_info["methods"]:
                    async_prefix = "async " if method["is_async"] else ""
                    params = ", ".join(method["params"])
                    lines.append(f"- `{async_prefix}{method['name']}({params})`")
                lines.append("")

    # Structure - Functions
    if analysis["structure"]["functions"]:
        lines.append("## Functions")
        lines.append("")
        for func in analysis["structure"]["functions"]:
            async_prefix = "async " if func["is_async"] else ""
            params = ", ".join(func["params"])
            ret = f" -> {func['return_type']}" if func.get("return_type") else ""
            lines.append(f"- `{async_prefix}{func['name']}({params}){ret}` (line {func['line']})")
        lines.append("")

    # Dependencies
    lines.append("## Dependencies")
    lines.append("")
    deps = analysis["dependencies"]
    if deps["internal"]:
        lines.append("**Internal (Jupiter):**")
        for dep in sorted(deps["internal"]):
            lines.append(f"- `{dep}`")
        lines.append("")
    if deps["external"]:
        lines.append("**External (Third-Party):**")
        for dep in sorted(deps["external"]):
            lines.append(f"- `{dep}`")
        lines.append("")

    # External Calls
    if analysis.get("external_calls"):
        lines.append("## External System Calls")
        lines.append("")
        for call_type, calls in analysis["external_calls"].items():
            lines.append(f"**{call_type.upper()}:**")
            for call in calls[:5]:  # Limit display
                lines.append(f"- `{call['pattern']}` (line {call['line']})")
            lines.append("")

    # Usages
    if analysis.get("usages"):
        lines.append("## Symbol Usages")
        lines.append("")
        for symbol, usage_data in analysis["usages"].items():
            lines.append(f"### `{symbol}` ({usage_data['count']} usages)")
            lines.append("")
            if usage_data["importing_modules"]:
                lines.append("**Imported by:**")
                for mod in usage_data["importing_modules"][:5]:
                    lines.append(f"- `{mod}`")
                lines.append("")

    return "\n".join(lines)


def format_as_summary(analysis: dict[str, Any]) -> str:
    """Format analysis result as a brief summary."""
    if "error" in analysis:
        return f"Error: {analysis['error']}"

    cls = analysis["classification"]
    struct = analysis["structure"]

    lines = [
        f"File: {analysis['file']}",
        f"Classification: {cls['level'].upper()} ({cls['reasoning']})",
        f"LOC: {cls['lines_of_code']} | Dependencies: {cls['num_dependencies']}",
        f"Classes: {len(struct['classes'])} | Functions: {len(struct['functions'])}",
        f"Exported: {', '.join(struct['exported_symbols'][:5])}{'...' if len(struct['exported_symbols']) > 5 else ''}",
        f"Internal deps: {len(analysis['dependencies']['internal'])} | External deps: {len(analysis['dependencies']['external'])}",
    ]

    if cls["verification_required"]:
        lines.append("*** VERIFICATION REQUIRED ***")

    if analysis.get("warning"):
        lines.append(f"Warning: {analysis['warning']}")

    return "\n".join(lines)


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Analyze Python files following DEEP_DIVE_PLAN methodology"
    )

    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="Path to Python file to analyze",
    )
    parser.add_argument(
        "-s", "--symbol",
        type=str,
        help="Find usages of a specific symbol",
    )
    parser.add_argument(
        "-o", "--output-format",
        choices=["json", "markdown", "summary"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument(
        "-u", "--find-usages",
        action="store_true",
        help="Find usages of exported symbols",
    )
    parser.add_argument(
        "-p", "--update-progress",
        action="store_true",
        help="Update analysis_progress.json",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root directory",
    )

    args = parser.parse_args()

    if not args.file:
        parser.error("--file is required")

    # Resolve paths
    file_path = args.file
    if not file_path.is_absolute():
        file_path = args.project_root / file_path

    # Run analysis
    result = analyze_single_file(
        file_path,
        find_usages=args.find_usages or args.symbol is not None,
        update_progress=args.update_progress,
        project_root=args.project_root,
    )

    # Format output
    if args.output_format == "json":
        print(json.dumps(result, indent=2, default=str))
    elif args.output_format == "markdown":
        print(format_as_markdown(result))
    else:  # summary
        print(format_as_summary(result))


if __name__ == "__main__":
    main()
