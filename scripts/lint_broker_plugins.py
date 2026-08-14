"""Broker-plugin contract linter for the plugin marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_broker_plugins.py

`.claude/skills/broker-plugin-contract/` states what a broker-integration
plugin (category `algotrading`) must contain to reach contract level `base`
or `verified`. This linter covers the half of that contract that is a
question about a directory listing, a marketplace entry, or a
regular-expression match: the three declaration lines exist and name a real
level, one or more real archetypes (comma-separated), and a real scope, a
`multi-broker-platform` plugin carries a section naming what varies per
broker, the required agent and command exist and are registered rather than
merely present on disk, the skill's `references/` directory exists and
holds at least one file, the four required sections exist under
case-insensitive headings, the listed references and the references on
disk agree, and (at `verified`) a registered verify command, a probe
script, and an open-questions register all exist.

The rest of the contract is a question about meaning, and is not checked
here:

  - whether the declared scope or archetype is the true one: a plugin can
    declare either token correctly formed and still be describing the
    wrong subject, and nothing mechanical can tell
  - whether an order-state name is really the reference model's own, or a
    vendor mapping is both present and correct (Level base item 5)
  - whether a `MEASURED` fact is honestly dated and attributed to the full
    shape `evidence-and-probes.md` names (Level verified item 3), and on a
    `multi-broker-platform` plugin whether it also names the broker it was
    measured against, or on a `single-broker` plugin the account entity
    when that matters
  - whether an open question is genuinely paired with the experiment that
    would settle it, rather than a heading with an empty list under it
    (Level verified item 2)
  - whether a `multi-broker-platform` plugin's per-broker-variation section
    genuinely names what varies, rather than a heading with nothing under
    it (Level base item 6)
  - whether probe tooling refuses production structurally rather than by a
    flag that defaults to safe (Level verified item 4)
  - where exactly the three declaration lines sit in the file: the contract
    states a placement convention for readers, but LEVEL_RE, ARCHETYPE_RE
    and SCOPE_RE match anywhere, on purpose, so position is never a failure

One more limit reads like a gap and is not: whether the skill directory
itself is registered in the plugin's `skills` array in
`.claude-plugin/marketplace.json` is not cross-checked here, because this
script finds `SKILL.md` files by walking the plugin's directory on disk, not
by reading the manifest. That declaration is still checked, by
`scripts/lint_plugin_registration.py`, which validates every plugin's
`agents`, `skills` and `commands` arrays against what is actually on disk,
in both directions, for every plugin in the marketplace. Repeating it here
would give one fact two places to drift apart.

The roster this linter checks is not a fixed list. It is every plugin
registered under category `algotrading` in `.claude-plugin/marketplace.json`,
except `trading-broker-connectivity` itself, which is the shared vocabulary
rather than an integration and carries no declaration. That is the category
cross-check: a plugin cannot leave the category and keep silent about the
contract, and a plugin cannot declare a level without having opted into the
category that means "this is a broker integration."

A failure is fixed by changing the plugin it names, never by adding an entry
to ALLOWLIST. That constant exists for heuristic misreads in this script's
own detection, not for a broker plugin that is correctly reported as
non-conformant.
"""
import json
import re
import sys
from pathlib import Path

GENERIC_PLUGIN = "trading-broker-connectivity"
BROKER_CATEGORY = "algotrading"

ARCHETYPES = {"direct-api", "local-terminal", "vendor-gateway", "bridge", "in-platform"}
LEVELS = {"base", "verified"}
SCOPES = {"single-broker", "multi-broker-platform"}

REQUIRED_SECTIONS = ("quick start", "key decision points",
                     "symptoms to entry points", "reference materials")

OPEN_QUESTION_HEADINGS = ("open questions", "questions the documentation does not answer")

PER_BROKER_HEADINGS = ("what varies per broker", "per-broker variation",
                       "what changes between brokers")

LEVEL_RE = re.compile(r"^\*\*Contract level:\*\*\s*(\S+)\s*$", re.MULTILINE)
ARCHETYPE_RE = re.compile(r"^\*\*Archetype:\*\*\s*(.+?)\s*$", re.MULTILINE)
SCOPE_RE = re.compile(r"^\*\*Scope:\*\*\s*(\S+)\s*$", re.MULTILINE)
HEADING_RE = re.compile(r"^#{2,3}\s+(.+?)\s*$", re.MULTILINE)
LISTED_REF_RE = re.compile(r"^[-*]\s+`([^`]+\.md)`", re.MULTILINE)

# Heuristic misreads only, each with a reason. Never add an entry to make a
# real conformance failure go away: fix the plugin instead.
ALLOWLIST = {}


def broker_token(plugin_name):
    """`ibkr-trading` -> `ibkr`. A plugin not ending in -trading keeps its name."""
    suffix = "-trading"
    return plugin_name[:-len(suffix)] if plugin_name.endswith(suffix) else plugin_name


def load_marketplace(root):
    data = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    return {p["name"]: p for p in data["plugins"]}


def skill_files(root, plugin_name):
    return sorted((root / "plugins" / plugin_name).glob("skills/*/SKILL.md"))


def check(root):
    failures = []
    entries = load_marketplace(root)

    for name, entry in sorted(entries.items()):
        if name == GENERIC_PLUGIN:
            continue
        skills = skill_files(root, name)
        declared = [s for s in skills if LEVEL_RE.search(s.read_text(encoding="utf-8"))]

        if not declared:
            if entry.get("category") == BROKER_CATEGORY:
                failures.append(
                    f"{name}: category is {BROKER_CATEGORY} but no SKILL.md carries a "
                    f"**Contract level:** line. Declare base or verified.")
            continue

        for skill in declared:
            failures.extend(check_plugin(root, name, entry, skill))

    return failures


def check_plugin(root, name, entry, skill_path):
    out = []
    text = skill_path.read_text(encoding="utf-8")
    plugin_dir = root / "plugins" / name
    token = broker_token(name)

    level = LEVEL_RE.search(text).group(1)
    if level not in LEVELS:
        out.append(f"{name}: contract level {level!r} is not one of {sorted(LEVELS)}")
        return out

    archetype_match = ARCHETYPE_RE.search(text)
    if not archetype_match:
        out.append(f"{name}: no **Archetype:** line")
    else:
        tokens = [t.strip() for t in archetype_match.group(1).split(",")]
        bad = [t for t in tokens if t not in ARCHETYPES]
        if bad:
            out.append(f"{name}: archetype {', '.join(bad)!r} is not one of "
                       f"{sorted(ARCHETYPES)}")

    out.extend(check_scope(name, text, skill_path))

    description = text.split("---")[1] if text.startswith("---") else ""
    for clause in ("TRIGGER WHEN:", "DO NOT TRIGGER WHEN:"):
        if clause not in description:
            out.append(f"{name}: skill description is missing {clause}")

    headings = {h.strip().lower() for h in HEADING_RE.findall(text)}
    for section in REQUIRED_SECTIONS:
        if section not in headings:
            out.append(f"{name}: SKILL.md has no '{section}' section")

    out.extend(check_references(name, skill_path, text))
    out.extend(check_structure(name, entry, plugin_dir, token))
    if level == "verified":
        out.extend(check_verified(name, entry, plugin_dir, skill_path, token))
    return out


def check_references(name, skill_path, text):
    out = []
    ref_dir = skill_path.parent / "references"
    on_disk = {p.name for p in ref_dir.glob("*.md")} if ref_dir.is_dir() else set()
    if not on_disk:
        out.append(f"{name}: level base requires a references/ directory with at least "
                   f"one .md file")
    listed = {Path(r).name for r in LISTED_REF_RE.findall(text) if r.endswith(".md")}
    for missing in sorted(on_disk - listed):
        out.append(f"{name}: references/{missing} exists but is not listed in SKILL.md")
    for ghost in sorted(listed - on_disk):
        out.append(f"{name}: SKILL.md lists {ghost} but references/ has no such file")
    return out


def check_scope(name, text, skill_path):
    out = []
    scope_match = SCOPE_RE.search(text)
    if not scope_match:
        out.append(f"{name}: no **Scope:** line")
        return out

    scope = scope_match.group(1)
    if scope not in SCOPES:
        out.append(f"{name}: scope {scope!r} is not one of {sorted(SCOPES)}")
        return out

    if scope != "multi-broker-platform":
        return out

    headings = {h.strip().lower() for h in HEADING_RE.findall(text)}
    found = bool(headings & set(PER_BROKER_HEADINGS))
    if not found:
        ref_dir = skill_path.parent / "references"
        for ref in sorted(ref_dir.glob("*.md")) if ref_dir.is_dir() else []:
            ref_headings = {h.strip().lower()
                            for h in HEADING_RE.findall(ref.read_text(encoding="utf-8"))}
            if ref_headings & set(PER_BROKER_HEADINGS):
                found = True
                break
    if not found:
        out.append(f"{name}: scope multi-broker-platform requires a section naming what "
                   f"varies per broker (SKILL.md or references/)")
    return out


def check_structure(name, entry, plugin_dir, token):
    out = []
    wanted = [
        (plugin_dir / "agents" / f"{token}-architect.md", entry.get("agents", []),
         f"./agents/{token}-architect.md"),
        (plugin_dir / "commands" / f"{token}-audit.md", entry.get("commands", []),
         f"./commands/{token}-audit.md"),
    ]
    for path, registered, rel in wanted:
        if not path.is_file():
            out.append(f"{name}: base level requires {path.relative_to(plugin_dir.parent.parent)}")
        elif rel not in registered:
            out.append(f"{name}: {rel} exists on disk but is not registered in marketplace.json")
    return out


def check_verified(name, entry, plugin_dir, skill_path, token):
    out = []
    verify = plugin_dir / "commands" / f"{token}-verify.md"
    rel = f"./commands/{token}-verify.md"
    if not verify.is_file():
        out.append(f"{name}: level verified requires commands/{token}-verify.md")
    elif rel not in entry.get("commands", []):
        out.append(f"{name}: {rel} exists on disk but is not registered in marketplace.json")

    scripts = skill_path.parent / "scripts"
    if not (scripts.is_dir() and any(scripts.glob("*probe*.py"))):
        out.append(f"{name}: level verified requires a probe script under skills/*/scripts/")

    ref_dir = skill_path.parent / "references"
    found = False
    for ref in sorted(ref_dir.glob("*.md")) if ref_dir.is_dir() else []:
        headings = {h.strip().lower() for h in HEADING_RE.findall(ref.read_text(encoding="utf-8"))}
        if headings & set(OPEN_QUESTION_HEADINGS):
            found = True
            break
    if not found:
        out.append(f"{name}: level verified requires an open-questions register in references/")
    return out


def main():
    root = Path.cwd()
    failures = [f for f in check(root) if f not in ALLOWLIST]

    if failures:
        print(f"{len(failures)} contract violation(s):\n")
        for failure in failures:
            print(f"  {failure}")
        sys.exit("\nfix the plugin, not the linter; see .claude/skills/broker-plugin-contract/")
    print("all broker plugins conform to the contract")


if __name__ == "__main__":
    main()
