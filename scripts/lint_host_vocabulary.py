"""Host-vocabulary linter for the neutral plugin kernels.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_host_vocabulary.py

Every kernel under plugins/ is compiled into three host packages, and the
compiler copies role and workflow bodies as they are. The moment a body names
one host's team API or dispatch primitive, that host's vocabulary has become
every host's contract: a worker on Codex told to "call TaskUpdate" has no such
tool, and the instruction is either refused or silently improvised. The rule
lives in the `downstream-exports` skill: never name a host tool, team API or
dispatch primitive in neutral content. The mechanism belongs in each host's
harness template, and a kernel expresses only the obligation (deliver your owned
files, report delivered or failed, hold the barrier).

What is flagged: the Claude Code Agent Teams and Agent-tool vocabulary listed in
TOKENS, anywhere in a shipped plugin body, fenced blocks included, because the
worker prompts that carry the damage live inside them.

What is deliberately NOT flagged:

  - `marketplace-ops` and `ai-tooling`'s `agent-sdk-builder` skill, whose
    subject matter IS the agent tooling (CLAUDE.md: never de-brand them)
  - `project-setup/examples/`, which ships example CLAUDE.md files about the
    Claude Code host by design
  - generic words such as "spawn", "dispatch", "worker" and "orchestrator",
    which name the obligation rather than a host's implementation of it

GRANDFATHERED holds the per-file occurrence count observed when this linter
landed (marketplace 26.1.0). Each entry is real debt, not a heuristic misread:
neutralize the file and delete its entry rather than raising a count. A count
that grows, and a file that is not listed, fail.
"""
import re
import sys
from pathlib import Path

PLUGINS = Path("plugins")

#: Claude Code Agent Teams and Agent-tool primitives. `teammate` is the team
#: layer's own word for a worker, and the one that reads most naturally in prose,
#: which is exactly why it leaks.
TOKENS = re.compile(
    r"\b(TaskUpdate|TaskList|TaskCreate|TaskGet|TeamCreate|TeamDelete|SendMessage"
    r"|shutdown_request|subagent_type|teammates?)\b"
)

# Bodies whose subject matter is the host tooling itself.
SUBJECT_MATTER = (
    "plugins/marketplace-ops/",
    "plugins/ai-tooling/skills/agent-sdk-builder/",
    "plugins/project-setup/examples/",
)

# File -> occurrence count when the linter landed. Fix a file, delete its entry.
# Never raise a count to make a build pass.
GRANDFATHERED: dict[str, int] = {
    "plugins/ai-tooling/workflows/prompt-optimize.md": 1,
    "plugins/business/roles/business-planner.md": 1,
    "plugins/clean-code/workflows/clean-code.md": 1,
    "plugins/codebase-mapper/workflows/docs-create.md": 2,
    "plugins/codebase-mapper/workflows/humanize-docs.md": 2,
    "plugins/codebase-mapper/workflows/team-codebase-map.md": 18,
    "plugins/digital-marketing/workflows/content-strategy.md": 3,
    "plugins/frontend-review/workflows/review-frontend.md": 4,
    "plugins/peer-review/workflows/review.md": 3,
    "plugins/react-development/workflows/review-react.md": 1,
    "plugins/senior-review/skills/review-quality-gates/SKILL.md": 4,
    "plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md": 16,
    "plugins/senior-review/skills/review-quality-gates/references/code-review-fix-loop.md": 1,
    "plugins/senior-review/workflows/code-review.md": 3,
    "plugins/senior-review/workflows/pr-review.md": 2,
    "plugins/senior-review/workflows/team-review.md": 20,
    "plugins/text-humanizer/workflows/humanize-text.md": 1,
    "plugins/typescript-development/workflows/review-typescript.md": 1,
}


def body_files():
    for path in sorted(PLUGINS.rglob("*.md")):
        posix = path.as_posix()
        if any(posix.startswith(prefix) for prefix in SUBJECT_MATTER):
            continue
        yield path


def scan():
    """Yield (path, line_no, token, line) per hit."""
    for path in body_files():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in TOKENS.finditer(line):
                yield path, line_no, match.group(1), line.strip()


def check(hits):
    counts: dict[str, int] = {}
    lines: dict[str, list[tuple[int, str, str]]] = {}
    for path, line_no, token, line in hits:
        key = path.as_posix()
        counts[key] = counts.get(key, 0) + 1
        lines.setdefault(key, []).append((line_no, token, line))

    problems = []
    grandfathered = 0
    for key, count in sorted(counts.items()):
        allowed = GRANDFATHERED.get(key, 0)
        if count <= allowed:
            grandfathered += count
            continue
        problems.append((key, count, allowed, lines[key]))
    stale = sorted(key for key in GRANDFATHERED if key not in counts)
    return problems, grandfathered, stale


def main():
    if not PLUGINS.is_dir():
        sys.exit("run from the repository root: plugins/ not found")

    hits = list(scan())
    problems, grandfathered, stale = check(hits)
    scanned = len(list(body_files()))
    print(f"{scanned} plugin body files scanned, {len(hits)} host-vocabulary hit(s) found")
    if grandfathered:
        print(f"{grandfathered} hit(s) in {len(GRANDFATHERED)} file(s) grandfathered\n")
    else:
        print()

    failed = False
    if stale:
        failed = True
        print(f"FAIL  stale baseline ({len(stale)}): these files are clean, delete their entries")
        for key in stale:
            print(f"         {key}")
    if problems:
        failed = True
        print(f"FAIL  host vocabulary in neutral content ({len(problems)} file(s)):")
        for key, count, allowed, entries in problems:
            print(f"         {key}: {count} hit(s), {allowed} grandfathered")
            for line_no, token, line in entries:
                print(f"           :{line_no}  {token}  {line[:100]}")
        print(
            "         fix: state the obligation (deliver owned files, report delivered or "
            "failed, hold the barrier) and leave the mechanism to the host harness template"
        )
    else:
        print("ok    host vocabulary")

    if failed:
        sys.exit("\nhost vocabulary check failed")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
