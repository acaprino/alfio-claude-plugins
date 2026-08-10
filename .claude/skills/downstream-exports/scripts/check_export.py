"""Structural verification for the VS Code export catalog.

Stdlib only, no dependencies, runs from the repository root:

    python .claude/skills/downstream-exports/scripts/check_export.py

Eight passes, each independently reported. Exits non-zero if any fails.

  1. frontmatter   delimiters parse, keys are in the schema for the file's kind
  2. tool ids      every id in a `tools:` list is a real VS Code tool
  3. uniqueness    no agent / skill / prompt name collides across bundles
  4. bindings      every prompt `agent:` resolves to an agent in the same bundle
  5. allowlists    every `agents:` entry resolves somewhere in the catalog
  6. coupling      no residual Claude Code coupling outside the documented exclusions
  7. code spans    no malformed backticks, the signature of a botched bulk edit
  8. byte-copies   non-markdown assets are identical to their source in plugins/

Pass 6 has exclusions, and they are not laziness. `marketplace-ops` authors
Claude Code plugin marketplaces and `ai-tooling/agent-sdk-builder` documents the
Claude Agent SDK: their tool names and TRIGGER WHEN vocabulary are the material
being taught, so renaming them would make the content false.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("exports/vscode")

SCHEMA = {
    "skill": ({"name", "description"},
              {"user-invocable", "license", "metadata", "compatibility"}),
    "agent": ({"name", "description"},
              {"user-invocable", "tools", "agents", "hooks", "model", "argument-hint"}),
    "prompt": ({"description"},
               {"agent", "argument-hint", "tools", "model", "name"}),
}

TOOLS = {
    "read/readFile", "read/problems", "read/terminalLastCommand",
    "search/codebase", "search/fileSearch", "search/listDirectory",
    "search/textSearch", "search/usages", "search/changes",
    "edit/createFile", "edit/createDirectory", "edit/editFiles",
    "execute/runInTerminal", "execute/getTerminalOutput",
    "web/fetch", "agent/runSubagent", "vscode/askQuestions", "todos",
    "websearch",  # contributed by the Web Search for Copilot extension
}

# Bundles whose SUBJECT is Claude Code. Their vocabulary is content, not coupling.
SUBJECT_MATTER = ("marketplace-ops", "ai-tooling/.github/skills/agent-sdk-builder")

COUPLING = {
    "CLAUDE_PLUGIN_ROOT": r"CLAUDE_PLUGIN_ROOT",
    "CLAUDE_CODE_ env var": r"CLAUDE_CODE_",
    "Skill() call": r"Skill\(",
    "Teammate": r"\bTeammate\b",
    "Task tools": r"\bTask(Create|List|Update)\b",
    "subagent_type": r"subagent_type",
    "plugin namespace": r"\b(senior-review|codebase-xray|abstraction-architect"
                        r"|agent-teams|playwright-skill|superpowers):[a-z]",
    "routing labels": r"(TRIGGER WHEN|DO NOT TRIGGER WHEN)",
    "plugin install cmd": r"claude plugin |/plugin install",
}

failures = []


def report(name, problems):
    if problems:
        failures.append(name)
        print(f"FAIL  {name}: {len(problems)}")
        for p in problems[:10]:
            print("        ", p)
        if len(problems) > 10:
            print(f"         ... and {len(problems) - 10} more")
    else:
        print(f"ok    {name}")


def kind_of(path):
    if path.name == "SKILL.md":
        return "skill"
    if path.name.endswith(".agent.md"):
        return "agent"
    if path.name.endswith(".prompt.md"):
        return "prompt"
    return ""


def frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, "missing opening ---"
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], None
    return None, "missing closing ---"


def top_level(block):
    """Return (keys, tools, agents). Parses to the block terminator rather than
    grepping for a shape: `tools:` lists run past 15 entries and `todos` carries
    no namespace, both of which defeat a naive pattern."""
    keys, tools, agents, current = [], [], [], None
    for line in block:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1] not in (" ", "\t", "-"):
            current = line.split(":", 1)[0].strip()
            keys.append(current)
            continue
        if line.lstrip().startswith("- "):
            item = line.lstrip()[2:].strip()
            if current == "tools":
                tools.append(item)
            elif current == "agents":
                agents.append(item)
    return keys, tools, agents


def main():
    if not ROOT.is_dir():
        print(f"run from the repository root: {ROOT} not found")
        return 2

    docs = sorted(p for p in ROOT.rglob("*.md") if kind_of(p))
    parsed = {}

    # 1 + 2 -------------------------------------------------------------
    schema_problems, tool_problems = [], []
    for p in docs:
        rel = p.relative_to(ROOT)
        block, err = frontmatter(p.read_text(encoding="utf-8"))
        if err:
            schema_problems.append(f"{rel}: {err}")
            continue
        keys, tools, agents = top_level(block)
        parsed[p] = (keys, tools, agents)
        required, optional = SCHEMA[kind_of(p)]
        for k in keys:
            if k not in required | optional:
                schema_problems.append(f"{rel}: unexpected key '{k}'")
        for k in required - set(keys):
            schema_problems.append(f"{rel}: missing required key '{k}'")
        if len(keys) != len(set(keys)):
            schema_problems.append(f"{rel}: duplicate top-level key")
        for t in tools:
            if t not in TOOLS:
                tool_problems.append(f"{rel}: unknown tool id '{t}'")
    report(f"frontmatter schema ({len(docs)} files)", schema_problems)
    report("tool ids", tool_problems)

    # 3 -----------------------------------------------------------------
    collisions = []
    for kind, key in (("agent", lambda p: p.name[:-len(".agent.md")]),
                      ("skill", lambda p: p.parent.name),
                      ("prompt", lambda p: p.name[:-len(".prompt.md")])):
        seen = defaultdict(list)
        for p in docs:
            if kind_of(p) == kind:
                seen[key(p)].append(p.parts[2])
        for name, where in sorted(seen.items()):
            if len(where) > 1:
                collisions.append(f"{kind} '{name}' in {', '.join(where)}")
    report("name uniqueness across bundles", collisions)

    # 4 + 5 -------------------------------------------------------------
    def agent_home(name):
        return [d.name for d in ROOT.iterdir()
                if d.is_dir() and (d / ".github/agents" / f"{name}.agent.md").exists()]

    bind_problems, allow_problems = [], []
    for p in docs:
        rel, bundle = p.relative_to(ROOT), p.parts[2]
        keys, _, agents = parsed.get(p, ([], [], []))
        if kind_of(p) == "prompt" and "agent" in keys:
            block, _ = frontmatter(p.read_text(encoding="utf-8"))
            name = next(l.split(":", 1)[1].strip() for l in block if l.startswith("agent:"))
            if not (ROOT / bundle / ".github/agents" / f"{name}.agent.md").exists():
                bind_problems.append(f"{rel}: agent '{name}' not in bundle '{bundle}'")
        for name in agents:
            if not agent_home(name):
                allow_problems.append(f"{rel}: allowlisted agent '{name}' exists nowhere")
    report("prompt agent: bindings", bind_problems)
    report("agents: allowlists", allow_problems)

    # 6 -----------------------------------------------------------------
    coupling = []
    for p in sorted(ROOT.rglob("*.md")):
        rel = "/".join(p.parts[2:])
        if p.name == "README.md" or any(rel.startswith(s) for s in SUBJECT_MATTER):
            continue
        if "_pipelines" in p.parts and p.name == "README.md":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for label, pat in COUPLING.items():
            for m in re.finditer(pat, text):
                line = text[:m.start()].count("\n") + 1
                coupling.append(f"{rel}:{line}  {label}")
    report("residual Claude Code coupling", coupling)

    # 7 -----------------------------------------------------------------
    spans = []
    for p in sorted(ROOT.rglob("*.md")):
        infence = False
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").split("\n"), 1):
            if line.lstrip().startswith("```"):
                infence = not infence
                continue
            if infence or "```" in line:
                continue
            if line.count("`") % 2:
                spans.append(f"{p.relative_to(ROOT)}:{n}  odd backtick count")
    report("markdown code spans", spans)

    # 8 -----------------------------------------------------------------
    drift = []
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file() or f.suffix == ".md" or "_pipelines" in f.parts:
            continue
        rel = f.relative_to(ROOT)
        bundle, tail = rel.parts[0], str(Path(*rel.parts[1:]))
        skills = tail.split(".github/skills/", 1)
        if len(skills) != 2:
            continue
        candidates = [Path("plugins") / bundle / "skills" / skills[1]]
        # research/scripts/webfetch.py lives at the plugin root upstream.
        candidates.append(Path("plugins") / bundle / "scripts" / Path(skills[1]).name)
        if not any(c.exists() and c.read_bytes() == f.read_bytes() for c in candidates):
            drift.append(f"{rel}: no identical source under plugins/{bundle}/")
    report("byte-copy assets", drift)

    # 9 -----------------------------------------------------------------
    # Every bundle file that uses $SKILLS must also say what it resolves to.
    # Agents, prompts and skills load independently, so a file that names the
    # variable without defining it leaves the agent guessing at a path. The
    # definition is recognized by the candidate roots it enumerates, not by a
    # fixed sentence, because the wording varies across bundles.
    undefined = []
    for p in sorted(ROOT.rglob("*.md")):
        if ".github" not in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "$SKILLS" in text and ".copilot/skills/" not in text:
            undefined.append(f"{p.relative_to(ROOT)}: uses $SKILLS without defining it")
    report("$SKILLS defined where used", undefined)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
