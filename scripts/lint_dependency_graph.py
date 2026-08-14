"""Dependency-graph linter for the plugin marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_dependency_graph.py

Cross-plugin references inside plugin bodies are contracts. Until now they were
enforced only by prose in CLAUDE.md; this linter makes them mechanical. Eight
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
                    instead of failing the pipeline. Since pass 6 forbids
                    optional LOCAL dependencies, this pass now only ever fires
                    on cross-marketplace ones
  5. self edges     no plugin declares itself as a dependency
  6. internal deps  a dependency on a plugin inside this marketplace is always
     mandatory      hard. Bare names in optionalDependencies are rejected: they
                    buy silent degradation ("Skipped: not installed" on a whole
                    review dimension) and protect against nothing, since local
                    plugins install together. See CLAUDE.md, "Dependency
                    policy: every internal dependency is mandatory"
  7. no local       the other half of pass 6, over prose instead of
     degrade prose  declarations. A hard local dependency is always present, so
                    text making something conditional on its install, or naming
                    a stand-in for it, can only produce a silently reduced
                    result. Added after the 21.x policy pass deleted every such
                    branch by hand and still left one behind, with all six other
                    checks green
  8. deps are used  the reverse of pass 2: every hard local dependency is
                    backed by a runtime reference, or by an entry in
                    ARTIFACT_DEPENDENCIES naming the artifact that carries the
                    contract. A declaration nothing uses is a prose pointer with
                    an install cost. This is also the only check that notices a
                    dependency silently reintroduced by a concurrent writer

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
    # trading-broker-connectivity is read by broker plugins that do not know
    # about each other; an edge back into one vendor would put every broker
    # plugin's install at risk of pulling in every other one through the
    # single thing they all share. A future broker plugin needs its own
    # entry here too.
    ("trading-broker-connectivity", "ibkr-trading",
     "the generic plugin must never dispatch into a broker plugin"),
    ("trading-broker-connectivity", "mt5-trading",
     "the generic plugin must never dispatch into a broker plugin"),
]

# Suppressions for pass 2, keyed (relative posix path, namespace). Add an
# entry only for a reference the linter misreads, with a reason.
ALLOWLIST = {
}

# Suppressions for pass 7, keyed (relative posix path, line number). Add an
# entry only for a line the linter misreads, with a reason. A line that really
# does make a dimension conditional on a hard local dependency gets fixed, never
# suppressed: that is the defect the pass exists to catch.
DEGRADE_PROSE_ALLOWLIST = {
}

# Real dependencies pass 8 cannot see, because the edge is an artifact contract
# rather than a spawn or a skill load. (owner, dependency): the artifact.
ARTIFACT_DEPENDENCIES = {
    ("abstraction-architect", "codebase-xray"):
        "reads the .deep-dive/ run output; deep_dive_path is required in global mode",
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
    unregistered = set()
    for owner, path, line_no, ns, kind, _lines in refs:
        rel = path.as_posix()
        if (rel, ns) in ALLOWLIST:
            continue
        if owner not in plugins:
            # Files on disk under plugins/<owner>/ with no marketplace.json
            # entry. Nothing here can be judged, since the declarations to
            # check against do not exist yet. Report it once and keep going:
            # crashing would abort the scan and hide every later undeclared
            # reference. lint_plugin_registration.py owns this condition.
            unregistered.add(owner)
            continue
        declared = {dep_base(e) for e in plugins[owner]["dependencies"]}
        declared |= {dep_base(e) for e in plugins[owner]["optionalDependencies"]}
        if ns not in declared:
            problems.append(
                f"{rel}:{line_no} {kind} of '{ns}:*' but '{ns}' is not in "
                f"{owner}'s dependencies or optionalDependencies")
    for owner in sorted(unregistered):
        problems.append(
            f"plugins/{owner}: has runtime references but no entry in "
            f".claude-plugin/marketplace.json; its declarations cannot be "
            f"checked until it is registered (see lint_plugin_registration.py)")
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


def check_internal_deps_mandatory(plugins):
    """Standing rule since marketplace 21.3.0: a dependency on a plugin inside
    this marketplace is always hard.

    An optional local dependency protects against nothing (local plugins install
    together from the same marketplace) and buys silent degradation: a review
    prints "Skipped: not installed" for a whole dimension and hands back a report
    that reads as complete. Cross-marketplace entries are unaffected; they stay
    optional-capable because the user installs them by hand.
    """
    problems = []
    for name, meta in plugins.items():
        for entry in meta["optionalDependencies"]:
            # Membership, not just the absence of "@": a bare name that is NOT a local
            # plugin is pass 1's business (a typo, or an external name missing its
            # marketplace). Claiming it belongs in dependencies would send a maintainer
            # to break the whole plugin load.
            if "@" not in entry and entry in plugins:
                problems.append(
                    f"{name}: '{entry}' is a plugin in this marketplace and must be "
                    f"declared in dependencies, not optionalDependencies "
                    f"(see CLAUDE.md, 'Dependency policy: every internal "
                    f"dependency is mandatory')")
    return problems


INSTALL_CONDITIONAL = re.compile(
    r"not installed|\bis installed\b|\bfalls? back\b|\bfallback\b", re.IGNORECASE)

# A line asserting the plugin is always there, or that no fallback exists, states
# the policy rather than breaching it. Without this the pass fires on its own
# remedy: "There is no generic fallback variant" trips a bare /fallback/.
POLICY_AFFIRMATION = re.compile(
    r"always available|always present|is a hard dependency|are hard dependencies|"
    r"\bno (generic )?fallback\b|broken install", re.IGNORECASE)


def check_no_local_degrade_prose(plugins):
    """The inverse of pass 4, and the half of the policy pass 6 cannot reach.

    Pass 6 governs declarations. This governs the prose those declarations are
    supposed to bind. A hard local dependency is always present, so text that
    makes a dimension conditional on its install, or that names a stand-in for
    it, can only produce a silently reduced result: the review reports the
    dimension as run while a generic agent did the work, or drops it with a note
    nobody reads.

    This pass exists because prose drifts where declarations do not. The 21.x
    policy pass deleted every such branch by hand and still left one behind
    (`team-review.md`, the testing-dimension addendum), with all six other
    checks green. Two independent reviewers found it; no linter did.

    Deliberately narrow. The bare word "skip" is legitimate everywhere in this
    repo ("Skip the dimension only when its signal did not match"), so a match
    needs an install-conditional phrase AND a hard local dependency named on the
    same line.
    """
    problems = []
    for md in sorted(PLUGINS.glob("*/**/*.md")):
        owner = md.relative_to(PLUGINS).parts[0]
        if owner not in plugins:
            continue  # unregistered; pass 2 and lint_plugin_registration.py own it
        hard_local = {e for e in plugins[owner]["dependencies"]
                      if "@" not in e and e in plugins}
        if not hard_local:
            continue
        lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, start=1):
            if (md.as_posix(), i) in DEGRADE_PROSE_ALLOWLIST:
                continue
            if not INSTALL_CONDITIONAL.search(line):
                continue
            if POLICY_AFFIRMATION.search(line):
                continue  # states the rule, does not breach it
            for ns in sorted(hard_local):
                if re.search(rf"(?<![\w-]){re.escape(ns)}(?![\w-])", line):
                    problems.append(
                        f"{md.as_posix()}:{i} makes something conditional on "
                        f"'{ns}' being installed (or names a fallback for it), "
                        f"but '{ns}' is a hard dependency of {owner} and is "
                        f"always present; a dimension is skipped only when its "
                        f"signal did not match")
    return problems


def check_deps_are_used(plugins, refs):
    """The reverse direction of pass 2, and the one nothing checked before.

    Pass 2 asks whether every runtime reference is declared. Nobody asked the
    opposite: whether every declaration is used. A hard local dependency that
    nothing spawns, loads or reads is not a dependency, it is a prose pointer
    with an install cost. CLAUDE.md already draws that line for runtime edges
    ("prose next-steps suggestions are fine; a spawn or Skill invocation is
    not"); this pass applies it to declarations.

    Two defects found on 2026-08-11 both live here. `senior-review` required
    `python-development`, the heaviest plugin in the set at 501 KB, to back one
    "see also" line in one agent. And a concurrent session silently restored
    `research -> codebase-mapper` after it was removed, with every other check
    green, because a declared-but-unused dependency was an error for nobody.

    ARTIFACT_DEPENDENCIES is for the real dependencies this cannot see: an edge
    expressed by reading files another plugin produces, rather than by spawning
    it. Those are legitimate and must be declared, so name them here with the
    artifact that carries the contract.
    """
    used = {(owner, ns) for owner, _p, _l, ns, _k, _lines in refs}
    problems = []
    for name, meta in plugins.items():
        for dep in meta["dependencies"]:
            if "@" in dep or dep not in plugins:
                continue  # cross-marketplace; pass 1 owns those
            if (name, dep) in used or (name, dep) in ARTIFACT_DEPENDENCIES:
                continue
            problems.append(
                f"{name}: declares '{dep}' but never spawns it, loads a skill "
                f"from it, or declares an artifact contract with it. A prose "
                f"pointer is not a dependency: drop the declaration, or add it "
                f"to ARTIFACT_DEPENDENCIES with the artifact that carries the "
                f"contract")
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
    report("internal deps mandatory", check_internal_deps_mandatory(plugins))
    report("no local degrade prose", check_no_local_degrade_prose(plugins))
    report("deps are used", check_deps_are_used(plugins, refs))

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
