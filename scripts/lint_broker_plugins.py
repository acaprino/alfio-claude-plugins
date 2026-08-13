"""Broker-plugin contract linter for the plugin marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_broker_plugins.py

`.claude/skills/broker-plugin-contract/` states what a broker-integration
plugin (category `algotrading`) must contain to reach contract level `base`
or `verified`. Most of that contract is a question about meaning: whether an
order-state name is really the reference model's own, whether a `MEASURED`
fact is honestly dated, whether an open question is genuinely paired with the
experiment that would settle it. None of that is checked here. This linter
covers the half of the contract that is a question about a directory
listing, a marketplace entry, or a regular-expression match: the two
declaration lines exist and name a real level and archetype, the required
agent and command exist and are registered rather than merely present on
disk, the four required sections exist under case-insensitive headings, the
listed references and the references on disk agree, and (at `verified`) a
registered verify command, a probe script, and an open-questions register
all exist.

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

REQUIRED_SECTIONS = ("quick start", "key decision points",
                     "symptoms to entry points", "reference materials")

OPEN_QUESTION_HEADINGS = ("open questions", "questions the documentation does not answer")

LEVEL_RE = re.compile(r"^\*\*Contract level:\*\*\s*(\S+)\s*$", re.MULTILINE)
ARCHETYPE_RE = re.compile(r"^\*\*Archetype:\*\*\s*(\S+)\s*$", re.MULTILINE)
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
    elif archetype_match.group(1) not in ARCHETYPES:
        out.append(f"{name}: archetype {archetype_match.group(1)!r} is not one of "
                   f"{sorted(ARCHETYPES)}")

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
    listed = {Path(r).name for r in LISTED_REF_RE.findall(text) if r.endswith(".md")}
    for missing in sorted(on_disk - listed):
        out.append(f"{name}: references/{missing} exists but is not listed in SKILL.md")
    for ghost in sorted(listed - on_disk):
        out.append(f"{name}: SKILL.md lists {ghost} but references/ has no such file")
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
