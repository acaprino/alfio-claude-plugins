"""Registration linter: every plugin content file on disk is declared in the marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_plugin_registration.py

`.claude-plugin/marketplace.json` is what makes an agent, skill or command
loadable. A file that exists under `plugins/<name>/agents/` but is absent from
that plugin's `agents` array does not exist at runtime: `subagent_type:
<plugin>:<agent>` resolves to nothing and the spawn fails with "Agent type not
found", taking its phase down with it. Nothing else in this repository checks
that array. The VS Code side has `gen_extension_manifest.py --check`; this is
the Claude Code equivalent, added after senior-review 9.0.0 shipped
`premise-auditor.md` on disk and undeclared, which silently disabled both
mechanisms that release existed to add.

Two passes, each independently reported. Exits non-zero if either fails.

  1. undeclared    a content file exists on disk but no manifest entry points at
                   it. This is the failure above: installed, invisible.
  2. dangling      a manifest entry points at a path that does not exist. This is
                   the same defect from the other side, and it is what a rename
                   that updates the file but not the manifest produces.

All three content kinds are checked, because the invariant is not agent-specific:
an undeclared skill or command fails the same way for the same reason.

  agents      `./agents/<file>.md`      matched against plugins/<name>/agents/*.md
  skills      `./skills/<dir>`          matched against directories holding a SKILL.md
  commands    `./commands/<file>.md`    matched against plugins/<name>/commands/*.md

There is no grandfathering map on purpose: the invariant is mechanical, it holds
across every plugin today, and an exception would mean shipping something users
cannot load.
"""
import json
import sys
from pathlib import Path

MARKETPLACE = Path(".claude-plugin/marketplace.json")
PLUGINS = Path("plugins")

failures: list[str] = []


def on_disk(source: Path, kind: str) -> set[str]:
    """Declared-path strings for what `plugins/<name>/<kind>/` actually holds."""
    directory = source / kind
    if not directory.is_dir():
        return set()
    if kind == "skills":
        return {f"./skills/{d.name}" for d in sorted(directory.iterdir())
                if (d / "SKILL.md").is_file()}
    return {f"./{kind}/{f.name}" for f in sorted(directory.glob("*.md"))}


def check():
    """Yield (pass_name, plugin, declared-path) for every violation."""
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    for plugin in data["plugins"]:
        name = plugin["name"]
        source = Path(plugin["source"])
        for kind in ("agents", "skills", "commands"):
            declared = set(plugin.get(kind, []))
            present = on_disk(source, kind)
            for path in sorted(present - declared):
                yield "undeclared", name, path
            for path in sorted(declared):
                target = source / path[2:]
                exists = (target / "SKILL.md").is_file() if kind == "skills" else target.is_file()
                if not exists:
                    yield "dangling", name, path


def report(name, problems, hint):
    if problems:
        failures.append(name)
        print(f"FAIL  {name} ({len(problems)}):")
        for plugin, path in problems:
            print(f"         {plugin}: {path}")
        print(f"         fix: {hint}")
    else:
        print(f"ok    {name}")


def main():
    if not MARKETPLACE.is_file() or not PLUGINS.is_dir():
        sys.exit("run from the repository root: .claude-plugin/marketplace.json not found")

    violations = list(check())
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    counted = sum(len(p.get(k, [])) for p in data["plugins"]
                  for k in ("agents", "skills", "commands"))
    print(f"{len(data['plugins'])} plugins scanned, {counted} declared content path(s)\n")

    report("undeclared", [(p, path) for kind, p, path in violations if kind == "undeclared"],
           "add the path to that plugin's agents/skills/commands array in "
           ".claude-plugin/marketplace.json, or delete the file")
    report("dangling", [(p, path) for kind, p, path in violations if kind == "dangling"],
           "the declared path does not exist: fix the entry to match the file on "
           "disk, or remove the entry")

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
