#!/usr/bin/env python3
"""
Check Progress CLI for Deep Dive Analysis.

View and filter analysis progress from analysis_progress.json.

Usage:
    python check_progress.py                    # Show overall stats
    python check_progress.py --phase 1          # Show Phase 1 files
    python check_progress.py --status pending   # Show pending files
    python check_progress.py --verification-needed  # Show files needing verification
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from progress_tracker import ProgressTracker, FileEntry

# Valid phase numbers
VALID_PHASES = list(range(1, 8))  # Phases 1-7


def format_stats(stats: dict) -> str:
    """Format statistics for display."""
    lines = [
        "=" * 60,
        "DEEP DIVE ANALYSIS PROGRESS",
        "=" * 60,
        "",
        f"Total Files: {stats['total_files']}",
        f"Progress: {stats['progress_percentage']}%",
        f"Current Phase: {stats['current_phase']}",
        "",
        "By Status:",
        f"  Done:      {stats['status']['done']:>4}",
        f"  Analyzing: {stats['status']['analyzing']:>4}",
        f"  Pending:   {stats['status']['pending']:>4}",
        f"  Blocked:   {stats['status']['blocked']:>4}",
        "",
        "By Classification:",
        f"  Critical:        {stats['classification']['critical']:>4}",
        f"  High-Complexity: {stats['classification']['high_complexity']:>4}",
        f"  Standard:        {stats['classification']['standard']:>4}",
        f"  Utility:         {stats['classification']['utility']:>4}",
        f"  Unclassified:    {stats['classification']['unclassified']:>4}",
        "",
        "Verification:",
        f"  Required:  {stats['verification']['required']:>4}",
        f"  Completed: {stats['verification']['completed']:>4}",
        f"  Pending:   {stats['verification']['pending']:>4}",
        "",
        "=" * 60,
    ]
    return "\n".join(lines)


def format_file_list(files: list[FileEntry], title: str = "Files") -> str:
    """Format a list of files for display."""
    if not files:
        return f"{title}: None found"

    lines = [
        f"{title}: {len(files)} files",
        "-" * 60,
    ]

    # Group by phase
    by_phase: dict[int, list[FileEntry]] = {}
    for f in files:
        if f.phase not in by_phase:
            by_phase[f.phase] = []
        by_phase[f.phase].append(f)

    for phase in sorted(by_phase.keys()):
        phase_files = by_phase[phase]
        lines.append(f"\nPhase {phase}:")

        for entry in phase_files:
            status_icon = {
                "done": "[x]",
                "analyzing": "[~]",
                "pending": "[ ]",
                "blocked": "[!]",
            }.get(entry.status, "[?]")

            cls_short = {
                "critical": "CRIT",
                "high-complexity": "HIGH",
                "standard": "STD",
                "utility": "UTIL",
            }.get(entry.classification or "", "????")

            ver = "*" if entry.verification_required and not entry.verification_done else " "

            # Normalize path separators for consistent display
            display_path = entry.path.replace("\\", "/")
            lines.append(f"  {status_icon} [{cls_short}]{ver} {display_path}")

            if entry.notes:
                lines.append(f"       Note: {entry.notes}")

    lines.append("")
    lines.append("Legend: [x]=done [~]=analyzing [ ]=pending [!]=blocked *=needs verification")

    return "\n".join(lines)


def format_phase_summary(tracker: ProgressTracker) -> str:
    """Format phase-by-phase summary."""
    lines = [
        "Phase Summary:",
        "-" * 40,
    ]

    for phase_num, phase_info in sorted(tracker.data.phases.items()):
        status_icon = {
            "completed": "[DONE]",
            "in_progress": "[>>>>]",
            "pending": "[----]",
        }.get(phase_info.status, "[????]")

        lines.append(f"  Phase {phase_num}: {status_icon} {phase_info.progress:>7} - {phase_info.name}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check deep dive analysis progress"
    )

    parser.add_argument(
        "-p", "--phase",
        type=int,
        choices=VALID_PHASES,
        metavar="N",
        help="Filter by phase number (1-7)",
    )
    parser.add_argument(
        "-s", "--status",
        choices=["pending", "analyzing", "done", "blocked"],
        help="Filter by status",
    )
    parser.add_argument(
        "-c", "--classification",
        choices=["critical", "high-complexity", "standard", "utility"],
        help="Filter by classification",
    )
    parser.add_argument(
        "--verification-needed",
        action="store_true",
        help="Show only files needing verification",
    )
    parser.add_argument(
        "--next",
        action="store_true",
        help="Show next file to analyze",
    )
    parser.add_argument(
        "--phases",
        action="store_true",
        help="Show phase summary only",
    )
    parser.add_argument(
        "--progress-file",
        type=Path,
        default=Path("analysis_progress.json"),
        help="Path to progress file",
    )

    args = parser.parse_args()

    # Load tracker
    try:
        tracker = ProgressTracker(args.progress_file)
        tracker.load()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Handle special commands
    if args.phases:
        print(format_phase_summary(tracker))
        return

    if args.next:
        next_file = tracker.get_next_pending(phase=args.phase)
        if next_file:
            print(f"Next file to analyze:")
            print(f"  Path: {next_file.path}")
            print(f"  Phase: {next_file.phase}")
            print(f"  Classification: {next_file.classification or 'unclassified'}")
            print(f"  Verification required: {next_file.verification_required}")
            print()
            print("To analyze:")
            print(f"  python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \\")
            print(f"    --file {next_file.path} --output-format markdown --update-progress")
        else:
            phase_msg = f" in phase {args.phase}" if args.phase else ""
            print(f"No pending files{phase_msg}!")
        return

    # Apply filters
    files = tracker.data.files

    if args.verification_needed:
        files = tracker.get_files_needing_verification()
        title = "Files Needing Verification"
    elif args.phase is not None:
        files = tracker.get_files_by_phase(args.phase)
        title = f"Phase {args.phase} Files"
    elif args.status:
        files = tracker.get_files_by_status(args.status)
        title = f"{args.status.title()} Files"
    elif args.classification:
        files = tracker.get_files_by_classification(args.classification)
        title = f"{args.classification.title()} Files"
    else:
        # Show overall stats
        stats = tracker.get_statistics()
        print(format_stats(stats))
        print()
        print(format_phase_summary(tracker))
        return

    # Apply additional filters
    if args.phase is not None and not args.verification_needed:
        # Phase filter already applied
        pass
    elif args.phase is not None:
        files = [f for f in files if f.phase == args.phase]

    if args.status and args.phase is None and not args.verification_needed:
        # Status filter already applied
        pass
    elif args.status:
        files = [f for f in files if f.status == args.status]

    if args.classification and args.phase is None and args.status is None:
        # Classification filter already applied
        pass
    elif args.classification:
        files = [f for f in files if f.classification == args.classification]

    print(format_file_list(files, title))


if __name__ == "__main__":
    main()
