"""Render Codex repository instructions from their canonical Claude copies."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_SKILLS = (
    "custom-plugin-refresh",
    "downstream-exports",
    "external-repo-intake",
    "upstream-sync",
)
REPLACEMENTS = (
    (".claude/skills/", ".agents/skills/"),
    ("~/.claude/plugins/cache", "~/.codex/plugins/cache"),
    ("CLAUDE.md", "AGENTS.md"),
    ("claude plugin", "codex plugin"),
    ("hosts that are not Claude Code", "hosts that are not Codex"),
)
CLAUDE_DISTRIBUTION_COMMAND = "claude plugin marketplace add acaprino/daodan"
CLAUDE_DISTRIBUTION_SENTINEL = "__DAODAN_CLAUDE_DISTRIBUTION_COMMAND__"


def adapt_claude_instructions_for_codex(text: str) -> str:
    """Apply the complete, deliberately small Codex instruction adaptation."""
    text = text.replace(
        CLAUDE_DISTRIBUTION_COMMAND,
        CLAUDE_DISTRIBUTION_SENTINEL,
    )
    for source, target in REPLACEMENTS:
        text = text.replace(source, target)
    return text.replace(
        CLAUDE_DISTRIBUTION_SENTINEL,
        CLAUDE_DISTRIBUTION_COMMAND,
    )


def instruction_pairs() -> tuple[tuple[Path, Path], ...]:
    skills = tuple(
        (
            ROOT / ".claude" / "skills" / name / "SKILL.md",
            ROOT / ".agents" / "skills" / name / "SKILL.md",
        )
        for name in WORKFLOW_SKILLS
    )
    return ((ROOT / "CLAUDE.md", ROOT / "AGENTS.md"), *skills)


def sync(*, check: bool) -> list[Path]:
    """Write or report Codex instruction files that differ from their source."""
    drift: list[Path] = []
    for source, target in instruction_pairs():
        expected = adapt_claude_instructions_for_codex(
            source.read_text(encoding="utf-8")
        )
        actual = target.read_text(encoding="utf-8") if target.is_file() else None
        if actual == expected:
            continue
        drift.append(target)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8", newline="\n")
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    drift = sync(check=args.check)
    for path in drift:
        print(path.relative_to(ROOT).as_posix())
    return 1 if args.check and drift else 0


if __name__ == "__main__":
    sys.exit(main())
