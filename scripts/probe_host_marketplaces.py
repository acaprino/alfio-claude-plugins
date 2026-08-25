"""Validate the disposable native-host protocol probe fixtures.

The fixtures under ``tests/host-probes/`` are three throwaway single-plugin
marketplaces, one per host, used to establish what each native harness actually
supports before any adapter binding encodes an assumption. This module checks
their structure; the behavioural evidence table is filled in by hand after
running the probes in real host sessions (see ``tests/host-probes/README.md``).

Standard library only. Run directly for a report:

    python scripts/probe_host_marketplaces.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_ROOT = REPO_ROOT / "tests" / "host-probes"

HOSTS = ("claude", "copilot", "codex")

MARKETPLACE_PATH = {
    "claude": Path(".claude-plugin/marketplace.json"),
    "copilot": Path(".github/plugin/marketplace.json"),
    "codex": Path(".agents/plugins/marketplace.json"),
}

PLUGIN_MANIFEST_PATH = {
    "claude": Path(".claude-plugin/plugin.json"),
    "copilot": Path("plugin.json"),
    "codex": Path(".codex-plugin/plugin.json"),
}

REQUIRED_FILES = {
    "claude": (
        Path("plugins/probe/skills/probe/SKILL.md"),
        Path("plugins/probe/agents/probe-worker.md"),
        Path("plugins/probe/commands/probe-team.md"),
    ),
    "copilot": (
        Path("plugins/probe/skills/probe/SKILL.md"),
        Path("plugins/probe/agents/probe-coordinator.agent.md"),
        Path("plugins/probe/agents/probe-worker.agent.md"),
    ),
    "codex": (
        Path("plugins/probe/skills/probe/SKILL.md"),
        Path("plugins/probe/hooks/hooks.json"),
        Path("plugins/probe/.codex/agents/probe.toml"),
    ),
}

PROBE_NAME = "daodan-probe"
PROBE_VERSION = "0.0.1"
PROBE_SOURCE = "./plugins/probe"
SINGLE_WORKER_CONTRACT = "Return exactly DAODAN_PROBE_OK."


def validate_fixture(root: Path, host: str) -> list[str]:
    """Return one message per structural defect in a probe fixture."""
    if host not in MARKETPLACE_PATH:
        return [f"{host}: unknown host"]

    errors: list[str] = []
    marketplace = root / MARKETPLACE_PATH[host]
    if not marketplace.is_file():
        return [f"{host}: missing {MARKETPLACE_PATH[host].as_posix()}"]

    try:
        catalog = json.loads(marketplace.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"{host}: {MARKETPLACE_PATH[host].as_posix()} is not valid JSON: {error}"]

    plugins = catalog.get("plugins", [])
    if len(plugins) != 1:
        errors.append(f"{host}: expected one probe plugin")
    else:
        entry = plugins[0]
        if entry.get("name") != PROBE_NAME:
            errors.append(f"{host}: plugin name is {entry.get('name')!r}, expected {PROBE_NAME!r}")
        if entry.get("version") != PROBE_VERSION:
            errors.append(f"{host}: plugin version is {entry.get('version')!r}, expected {PROBE_VERSION!r}")
        source = entry.get("source")
        if source != PROBE_SOURCE:
            errors.append(f"{host}: source is {source!r}, expected the repository-relative {PROBE_SOURCE!r}")

    manifest = root / "plugins/probe" / PLUGIN_MANIFEST_PATH[host]
    if not manifest.is_file():
        errors.append(f"{host}: missing plugins/probe/{PLUGIN_MANIFEST_PATH[host].as_posix()}")
    else:
        try:
            declared = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{host}: plugin manifest is not valid JSON: {error}")
        else:
            if declared.get("name") != PROBE_NAME:
                errors.append(f"{host}: plugin manifest name is {declared.get('name')!r}")
            if declared.get("version") != PROBE_VERSION:
                errors.append(f"{host}: plugin manifest version is {declared.get('version')!r}")

    for relative in REQUIRED_FILES[host]:
        if not (root / relative).is_file():
            errors.append(f"{host}: missing {relative.as_posix()}")

    skill = root / "plugins/probe/skills/probe/SKILL.md"
    if skill.is_file() and SINGLE_WORKER_CONTRACT not in skill.read_text(encoding="utf-8"):
        errors.append(f"{host}: probe skill does not state the single-worker output contract")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROBE_ROOT, help="probe fixture root")
    arguments = parser.parse_args(argv)

    failures = 0
    for host in HOSTS:
        errors = validate_fixture(arguments.root / host, host)
        failures += len(errors)
        if errors:
            for message in errors:
                print(message)
        else:
            print(f"{host}: ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
