"""Bundled-path linter for the plugin marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_bundled_paths.py

A plugin body that tells the agent to read `plugins/<name>/skills/x/references/y.md`
is describing a path that exists only in a checkout of THIS repository. Claude Code
installs plugins into its own cache directory, so at runtime that path resolves to
nothing and the reference silently does not load. `${CLAUDE_PLUGIN_ROOT}` is the
substitution that survives installation, and it expands inside agent, command and
skill bodies, not only in hooks and MCP configs.

Two passes, each independently reported. Exits non-zero if any fails.

  1. self refs     a plugin referencing its OWN bundled file must go through
                   ${CLAUDE_PLUGIN_ROOT}/... (or a skill-relative references/...
                   path from inside that same skill), never plugins/<self>/...
  2. cross refs    a plugin must not reach into ANOTHER plugin's files by path at
                   all. ${CLAUDE_PLUGIN_ROOT} points at the referencing plugin, so
                   it cannot express this, and the target may not even be
                   installed. Load the other plugin's skill by name instead.

What is deliberately NOT flagged:

  - attribution and provenance comments naming an upstream file
  - marketplace.json manifest paths (`./agents/x.md`), which are relative to the
    plugin source and are how the registry is written
  - `marketplace-ops`, whose subject matter IS this repository's layout, and
    `.claude/`, `docs/`, `evals/` and `exports/`, which are not shipped plugin
    bodies
  - prose that names a directory shape without instructing a read

GRANDFATHERED holds references that predate this linter. Each entry is real debt,
not a heuristic misread: fix the reference and delete the entry rather than adding
to the list. New violations must fail.
"""
import json
import re
import sys
from pathlib import Path

MARKETPLACE = Path(".claude-plugin/marketplace.json")
PLUGINS = Path("plugins")

# Plugins whose subject matter is this repository's own layout, so a
# `plugins/<name>/...` string is content rather than a runtime path.
SUBJECT_MATTER_PLUGINS = {"marketplace-ops"}

# Lines that name a path for provenance rather than for reading.
ATTRIBUTION = re.compile(
    r"(vendored from|adapted from|ported from|upstream|source:|originally at"
    r"|renamed from|used to live|lived (in|at)|moved (from|to)|formerly)",
    re.I,
)

# plugins/<name>/<something>: the shape that breaks once installed.
PATH_REF = re.compile(r"plugins/([a-z0-9][a-z0-9-]*)/([A-Za-z0-9_][A-Za-z0-9_./-]*)")

# The two reference roots that account for most of the baseline below.
AUDIENCE = "plugins/codebase-mapper/skills/codebase-mapper/references/audience-adaptation.md"
TAXONOMY = "plugins/senior-review/skills/defect-taxonomy/references/"

# Debt recorded when a linter lands, keyed by file AND exact path string so a NEW
# broken path in an already-listed file still fails. Empty since marketplace
# 19.2.0: the 40 references this linter found on its first run (across
# business, codebase-mapper, python-development, senior-review, stripe and
# tauri-development) were all fixed in that release rather than grandfathered.
#
# Fix a reference, delete its entry. Never add one to make a build pass.
GRANDFATHERED: dict[str, set[str]] = {}

failures: list[str] = []


def load_plugin_names() -> set[str]:
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    return {p["name"] for p in data["plugins"]}


def body_files():
    """Every shipped plugin body: agents, commands, and skill markdown."""
    for path in sorted(PLUGINS.rglob("*.md")):
        parts = path.parts
        if len(parts) < 3:
            continue
        if parts[1] in SUBJECT_MATTER_PLUGINS:
            continue
        yield parts[1], path


def scan():
    """Yield (owner, path, line_no, target_plugin, matched_path, line) per hit."""
    known = load_plugin_names()
    for owner, path in body_files():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            # Fenced blocks are scanned, not skipped: in this repo the runtime
            # paths live inside them (subagent prompt blocks, `uv run` script
            # invocations), which is exactly where a broken path does damage.
            if line.lstrip().startswith("```") or ATTRIBUTION.search(line):
                continue
            for match in PATH_REF.finditer(line):
                target = match.group(1)
                if target not in known:
                    continue
                yield owner, path, line_no, target, match.group(0), line.strip()


def check(hits):
    self_refs, cross_refs, skipped = [], [], 0
    for owner, path, line_no, target, matched, line in hits:
        if matched in GRANDFATHERED.get(path.as_posix(), ()):
            skipped += 1
            continue
        entry = (path.as_posix(), line_no, target, line)
        (self_refs if target == owner else cross_refs).append(entry)
    return self_refs, cross_refs, skipped


def report(name, problems, hint):
    if problems:
        failures.append(name)
        print(f"FAIL  {name} ({len(problems)}):")
        for path, line_no, target, line in problems:
            print(f"         {path}:{line_no}  -> plugins/{target}/...")
            print(f"           {line[:110]}")
        print(f"         fix: {hint}")
    else:
        print(f"ok    {name}")


def main():
    if not MARKETPLACE.is_file() or not PLUGINS.is_dir():
        sys.exit("run from the repository root: .claude-plugin/marketplace.json not found")

    hits = list(scan())
    self_refs, cross_refs, skipped = check(hits)
    scanned = len({p for _, p in body_files()})
    print(f"{scanned} plugin body files scanned, {len(hits)} bundled-path reference(s) found")
    if skipped:
        owners = sorted({p.split("/")[1] for p in GRANDFATHERED})
        print(f"{skipped} known-broken reference(s) in {len(GRANDFATHERED)} file(s) "
              f"grandfathered: {', '.join(owners)}\n")
    else:
        print()

    report("self refs", self_refs,
           "replace plugins/<self>/ with ${CLAUDE_PLUGIN_ROOT}/, or with a "
           "skill-relative references/... path inside the same skill")
    report("cross refs", cross_refs,
           "do not read another plugin's files by path; load its skill by name, "
           "and declare the dependency in marketplace.json")

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
