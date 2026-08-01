"""Dependency-graph linter for the plugin marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_dependency_graph.py

Cross-plugin references inside plugin bodies are contracts. Until now they were
enforced only by prose in CLAUDE.md; this linter makes them mechanical. Five
passes, each independently reported. Exits non-zero if any fails.

  1. declarations   every dependencies/optionalDependencies entry resolves:
                    bare names must exist in this marketplace (a bare external
                    name fails the whole plugin load at install time, the bug
                    that silently broke ai-tooling until marketplace 12.0.2);
                    qualified names must be name@marketplace with both halves
                    non-empty, and must not shadow a local plugin
  2. runtime refs   every runtime cross-plugin reference (agent spawn or skill
                    load) is declared in the owning plugin's dependencies or
                    optionalDependencies
  3. forbidden edge nothing in codebase-xray references a senior-review
                    component at runtime. Prose next-steps suggestions are
                    fine; a spawn or skill load is the edge the old dependency
                    cycle was made of (see CLAUDE.md, marketplace 16.0.0)
  4. degrade notes  every spawn of an agent from an optionalDependencies
                    plugin carries a nearby skip note ("not installed" /
                    "skip"), so a missing optional plugin degrades a dimension
                    instead of failing the pipeline
  5. self edges     no plugin declares itself as a dependency

What counts as a runtime reference:

  - a `subagent_type:` line naming plugin:agent (an Agent spawn)
  - a spawn/dispatch instruction naming plugin:component on the same line
  - a skill-load instruction (load/invoke/use + "skill") naming plugin:skill

Slash-command mentions (/plugin:command) are user-facing suggestions, not
runtime edges, and are deliberately not extracted. TRIGGER WHEN / DO NOT
TRIGGER WHEN lines are routing descriptions, never runtime. Tokens whose
prefix is not a known namespace (local plugin or the base name of a qualified
external dependency) are ignored.

    python scripts/lint_dependency_graph.py --refs

prints the extracted runtime edges instead of linting, for maintenance.
"""
import json
import re
import sys
from pathlib import Path

MARKETPLACE = Path(".claude-plugin/marketplace.json")
PLUGINS = Path("plugins")

# Runtime edges that must never exist, regardless of declarations.
# (source plugin, target namespace, reason)
FORBIDDEN_EDGES = [
    ("codebase-xray", "senior-review",
     "reintroduces the dependency cycle removed in marketplace 16.0.0"),
]

# Suppressions for pass 2, keyed (relative posix path, namespace). Add an
# entry only for a reference the linter misreads, with a reason.
ALLOWLIST = {
}

failures = []


def report(name, problems):
    if problems:
        failures.append(name)
        print(f"FAIL  {name}: {len(problems)}")
        for p in problems[:15]:
            print("        ", p)
        if len(problems) > 15:
            print(f"         ... and {len(problems) - 15} more")
    else:
        print(f"ok    {name}")


def load_marketplace():
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    plugins = {}
    for entry in data["plugins"]:
        plugins[entry["name"]] = {
            "dependencies": entry.get("dependencies", []),
            "optionalDependencies": entry.get("optionalDependencies", []),
        }
    return plugins


def dep_base(entry):
    """codebase-xray -> codebase-xray, agent-teams@claude-code-workflows -> agent-teams."""
    return entry.split("@", 1)[0]


TOKEN = re.compile(r"(?<![\w@/.$-])([a-z0-9]+(?:-[a-z0-9]+)*):([a-z0-9]+(?:-[a-z0-9]+)*)")
SPAWN_LINE = re.compile(r"subagent_type|\bspawn|\bdispatch", re.IGNORECASE)
SKILL_LINE = re.compile(r"\bskill", re.IGNORECASE)
SKILL_VERB = re.compile(r"\b(load|invoke|use|run)\b", re.IGNORECASE)
ROUTING_LINE = re.compile(r"TRIGGER WHEN", re.IGNORECASE)
DEGRADE_NOTE = re.compile(r"not installed|\bskip|\boptional", re.IGNORECASE)


def extract_references(plugins):
    """Yield (owner, path, line_no, namespace, kind, lines) for runtime refs.

    kind is "spawn" or "skill-load". Prose mentions are dropped here.
    """
    namespaces = set(plugins)
    for meta in plugins.values():
        for entry in meta["dependencies"] + meta["optionalDependencies"]:
            if "@" in entry:
                namespaces.add(dep_base(entry))

    refs = []
    for md in sorted(PLUGINS.glob("*/**/*.md")):
        owner = md.relative_to(PLUGINS).parts[0]
        lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, start=1):
            if ROUTING_LINE.search(line):
                continue  # TRIGGER WHEN routing labels are prose
            for m in TOKEN.finditer(line):
                ns = m.group(1)
                if ns not in namespaces or ns == owner:
                    continue
                if SPAWN_LINE.search(line):
                    kind = "spawn"
                elif SKILL_LINE.search(line) and SKILL_VERB.search(line):
                    kind = "skill-load"
                else:
                    continue  # prose mention, not enforced
                refs.append((owner, md, i, ns, kind, lines))
    return refs


def check_declarations(plugins):
    problems = []
    for name, meta in plugins.items():
        for field in ("dependencies", "optionalDependencies"):
            for entry in meta[field]:
                if "@" in entry:
                    base, _, marketplace = entry.partition("@")
                    if not base or not marketplace:
                        problems.append(f"{name}: malformed qualified entry '{entry}'")
                    elif base in plugins:
                        problems.append(
                            f"{name}: '{entry}' qualifies a plugin that exists locally; "
                            f"local dependencies use the bare name")
                elif entry not in plugins:
                    problems.append(
                        f"{name}: bare dependency '{entry}' is not in this marketplace; "
                        f"cross-marketplace dependencies must use name@marketplace "
                        f"(a bare external name fails the whole plugin load)")
    return problems


def check_runtime_refs(plugins, refs):
    problems = []
    for owner, path, line_no, ns, kind, _lines in refs:
        rel = path.as_posix()
        if (rel, ns) in ALLOWLIST:
            continue
        declared = {dep_base(e) for e in plugins[owner]["dependencies"]}
        declared |= {dep_base(e) for e in plugins[owner]["optionalDependencies"]}
        if ns not in declared:
            problems.append(
                f"{rel}:{line_no} {kind} of '{ns}:*' but '{ns}' is not in "
                f"{owner}'s dependencies or optionalDependencies")
    return problems


def check_forbidden_edges(refs):
    problems = []
    for owner, path, line_no, ns, kind, _lines in refs:
        for src, dst, reason in FORBIDDEN_EDGES:
            if owner == src and ns == dst:
                problems.append(
                    f"{path.as_posix()}:{line_no} {kind} of '{ns}:*' from "
                    f"'{src}': {reason}")
    return problems


def check_degrade_notes(plugins, refs):
    problems = []
    for owner, path, line_no, ns, kind, lines in refs:
        if kind != "spawn":
            continue
        optional = {dep_base(e) for e in plugins[owner]["optionalDependencies"]}
        if ns not in optional:
            continue
        window = lines[max(0, line_no - 13):line_no + 12]
        if not any(DEGRADE_NOTE.search(l) for l in window):
            problems.append(
                f"{path.as_posix()}:{line_no} spawns optional '{ns}:*' without a "
                f"nearby skip note; optional dependencies must degrade, never fail")
    return problems


def check_self_edges(plugins):
    problems = []
    for name, meta in plugins.items():
        for field in ("dependencies", "optionalDependencies"):
            for entry in meta[field]:
                if dep_base(entry) == name:
                    problems.append(f"{name}: declares itself in {field}")
    return problems


def main():
    if not MARKETPLACE.is_file() or not PLUGINS.is_dir():
        sys.exit("run from the repository root: .claude-plugin/marketplace.json not found")

    plugins = load_marketplace()
    refs = extract_references(plugins)

    if "--refs" in sys.argv[1:]:
        for owner, path, line_no, ns, kind, _lines in refs:
            print(f"{owner} -> {ns}  ({kind})  {path.as_posix()}:{line_no}")
        return

    spawns = sum(1 for r in refs if r[4] == "spawn")
    print(f"{len(plugins)} plugins, {len(refs)} runtime cross-plugin references "
          f"({spawns} spawns, {len(refs) - spawns} skill loads)\n")

    report("declarations", check_declarations(plugins))
    report("runtime refs", check_runtime_refs(plugins, refs))
    report("forbidden edge", check_forbidden_edges(refs))
    report("degrade notes", check_degrade_notes(plugins, refs))
    report("self edges", check_self_edges(plugins))

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
