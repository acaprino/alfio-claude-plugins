#!/usr/bin/env python3
"""Regenerate the contributed agent and prompt lists in the VS Code extension manifest.

Run from the repository root:

    python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py

Agents and prompts are single files, so they ship as `chatAgents` and `chatPromptFiles`
contribution points. Skills are not contributed: 45 of the 66 carry supporting files under
references/, scripts/ and assets/, and microsoft/vscode#304721 (open) means a contributed
skill loads only its SKILL.md. extension.js copies whole skill directories into
~/.copilot/skills/ instead.

Hand-authored fields in package.json are preserved. Only contributes.chatAgents and
contributes.chatPromptFiles are rewritten.

With --check, nothing is written: the contribution lists are recomputed and compared
against the manifest on disk, exiting 1 on drift. CI runs this mode.
"""

import json
import sys
from pathlib import Path

ROOT = Path("exports/vscode")

BASE = {
    "name": "claude-code-daodan",
    "displayName": "Claude Code Daodan",
    "description": "81 agents, 66 skills and 47 prompts for GitHub Copilot: code review, "
                   "documentation, testing, research, frontend, trading, observability and more.",
    "version": "16.2.0",
    "publisher": "acaprino",
    "license": "MIT",
    "engines": {"vscode": "^1.109.0"},
    "categories": ["AI", "Chat", "Programming Languages", "Other"],
    "keywords": ["copilot", "agents", "skills", "prompts", "code-review", "documentation"],
    "repository": {
        "type": "git",
        "url": "https://github.com/acaprino/claude-code-daodan.git",
    },
    "main": "./extension.js",
    "activationEvents": ["onStartupFinished"],
    "scripts": {"vscode:uninstall": "node ./uninstall.js"},
    "contributes": {},
}


def bundles():
    return sorted(p.name for p in ROOT.iterdir() if p.is_dir())


def collect(kind, suffix):
    out = []
    for bundle in bundles():
        directory = ROOT / bundle / ".github" / kind
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob(f"*{suffix}")):
            out.append({"path": "./" + path.relative_to(ROOT).as_posix()})
    return out


def main():
    if not ROOT.is_dir():
        sys.exit("run from the repository root: exports/vscode not found")

    check_only = "--check" in sys.argv[1:]

    manifest_path = ROOT / "package.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = dict(BASE)

    agents = collect("agents", ".agent.md")
    prompts = collect("prompts", ".prompt.md")

    if check_only:
        contributes = manifest.get("contributes", {})
        stale = []
        if contributes.get("chatAgents") != agents:
            stale.append("chatAgents")
        if contributes.get("chatPromptFiles") != prompts:
            stale.append("chatPromptFiles")
        if stale:
            sys.exit(
                f"{manifest_path} is stale ({', '.join(stale)}): regenerate with "
                "python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py"
            )
        print(f"{manifest_path}: manifest is fresh "
              f"({len(agents)} agents, {len(prompts)} prompts)")
        return

    manifest.setdefault("contributes", {})
    manifest["contributes"]["chatAgents"] = agents
    manifest["contributes"]["chatPromptFiles"] = prompts

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    skills = sum(
        1
        for bundle in bundles()
        for skill in (ROOT / bundle / ".github" / "skills").glob("*/SKILL.md")
    )
    print(f"{manifest_path}: {len(agents)} agents, {len(prompts)} prompts contributed")
    print(f"{skills} skills copied at runtime by extension.js, not contributed")


if __name__ == "__main__":
    main()
