"""The Daodan compiler entry point.

    python scripts/daodan_build.py            # publish all three hosts
    python scripts/daodan_build.py --check    # fail on drift, write nothing

Exit codes: 0 clean, 1 drift or validation failure, 2 invocation error.

Publication always builds Claude, Copilot and Codex together: a marketplace that
ships one host ahead of the others is exactly the drift this compiler exists to
prevent. Selecting a subset is a development affordance, and only under
``--check``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support  # noqa: E402
from scripts.daodan.catalogs import (  # noqa: E402
    assert_cross_host_identity,
    catalog_document,
    merge_into_legacy,
    render_catalog,
)
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError, PluginSpec  # noqa: E402
from scripts.daodan.overrides import load_overrides, validate_override  # noqa: E402
from scripts.daodan.render import RenderError, publish_plugin, render_plugin, tree_digest  # noqa: E402
from scripts.daodan.report import BuildReport  # noqa: E402
from scripts.daodan.trust import scan_trust  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY, ValidationIssue, validate_plugins  # noqa: E402

LEGACY_CLAUDE_CATALOG = Path(".claude-plugin/marketplace.json")


def discover_plugins(root: Path) -> list[PluginSpec]:
    """Load every content kernel under ``plugins/``, in name order."""
    plugins_root = Path(root) / "plugins"
    if not plugins_root.is_dir():
        return []
    kernels = sorted(plugins_root.glob("*/plugin.toml"), key=lambda item: item.as_posix())
    return [load_plugin(kernel.parent) for kernel in kernels]


def marketplace_version(root: Path) -> str:
    """The single marketplace version every host catalog carries.

    It stays where it has always lived, `metadata.version` in the Claude
    catalog, so the existing bump workflow keeps working through the migration.
    """
    catalog = Path(root) / LEGACY_CLAUDE_CATALOG
    if catalog.is_file():
        document = json.loads(catalog.read_text(encoding="utf-8"))
        version = document.get("metadata", {}).get("version")
        if isinstance(version, str):
            return version
    return "0.0.0"


def _overrides_for(root: Path, host: str, plugin: PluginSpec):
    directory = Path(root) / "adapters" / host / "overrides" / plugin.name
    if not directory.is_dir():
        return ()
    return load_overrides(directory)


def build_repository(root: Path, hosts: tuple[str, ...], check: bool) -> BuildReport:
    """Validate every kernel and render, or verify, every host package."""
    root = Path(root)
    issues: list[ValidationIssue] = []
    drift: list[Path] = []
    support = []

    try:
        plugins = discover_plugins(root)
    except ModelError as error:
        return BuildReport(issues=(ValidationIssue("model-error", error.path, error.message),))

    issues.extend(validate_plugins(plugins, CAPABILITY_REGISTRY))
    for scanned in ("plugins", "adapters"):
        directory = root / scanned
        if directory.is_dir():
            issues.extend(scan_trust(directory, frozenset()))

    catalogs = {}
    version = marketplace_version(root)

    for host in hosts:
        adapter = load_adapter(root / "adapters", host)
        packages = {
            plugin.name: root / adapter.layout["root"] / "plugins" / plugin.name
            for plugin in plugins
        }
        catalogs[host] = catalog_document(host, plugins, version, packages)
        for plugin in plugins:
            overrides = _overrides_for(root, host, plugin)
            declared = frozenset(plugin.capabilities.required) | frozenset(
                plugin.capabilities.optional
            )
            for override in overrides:
                issues.extend(validate_override(override, declared, repository_root=root))

            report = resolve_support(plugin, adapter)
            support.append(report)
            if report.state == "unsupported":
                issues.append(
                    ValidationIssue(
                        "unsupported-required-plugin",
                        plugin.root,
                        f"{host}: {', '.join(report.missing_capabilities) or 'no coordination strategy'}",
                    )
                )
                continue

            live = root / adapter.layout["root"] / "plugins" / plugin.name
            if check:
                if _package_drifted(plugin, adapter, live, overrides, root):
                    drift.append(live)
            elif not issues:
                publish_plugin(plugin, adapter, live, overrides, root / "adapters")

        catalog_path = root / adapter.layout["marketplace"]
        rendered = _render_host_catalog(root, adapter, host, plugins, version, catalog_path)
        if check:
            if not catalog_path.is_file() or catalog_path.read_bytes() != rendered:
                drift.append(catalog_path)
        elif not issues:
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            catalog_path.write_bytes(rendered)

    if len(catalogs) == len(HOSTS):
        assert_cross_host_identity(catalogs)

    return BuildReport(issues=tuple(issues), drift=tuple(drift), support=tuple(support))


def _render_host_catalog(root, adapter, host, plugins, version, catalog_path: Path) -> bytes:
    """Serialize one host catalog, folding into a legacy one while migration runs.

    Until every plugin is a neutral kernel, the live Claude catalog still carries
    hand-written entries for the plugins that have not moved yet. Overwriting it
    with the compiled catalog would uninstall them, so compiled entries are
    merged into it instead and the generated catalog is written whole only once
    nothing legacy is left.
    """
    packages = {
        plugin.name: root / adapter.layout["root"] / "plugins" / plugin.name
        for plugin in plugins
    }
    compiled = {plugin.name for plugin in plugins}
    if catalog_path.is_file():
        existing = json.loads(catalog_path.read_text(encoding="utf-8"))
        legacy = [
            entry for entry in existing.get("plugins", []) if entry["name"] not in compiled
        ]
        if legacy:
            document = merge_into_legacy(existing, plugins, host, packages)
            return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return render_catalog(host, plugins, version, packages)


def _package_drifted(plugin, adapter, live: Path, overrides, root: Path) -> bool:
    if not live.is_dir():
        return True
    holder = Path(tempfile.mkdtemp())
    try:
        staging = holder / live.name
        try:
            render_plugin(plugin, adapter, staging, overrides, root / "adapters")
        except RenderError:
            return True
        return tree_digest(staging) != tree_digest(live)
    finally:
        shutil.rmtree(holder, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", action="append", choices=HOSTS)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--support", action="store_true", help="print the per-host support table")
    arguments = parser.parse_args(argv)

    hosts = tuple(arguments.host or HOSTS)
    if not arguments.check and set(hosts) != set(HOSTS):
        parser.print_usage(sys.stderr)
        sys.stderr.write("publication always builds claude, copilot and codex together\n")
        return 2

    report = build_repository(arguments.root, hosts, arguments.check)
    report.write(sys.stdout)
    if arguments.support:
        report.write_support(sys.stdout)
    return 1 if report.has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
