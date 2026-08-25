"""Native catalog rendering for the three hosts.

One catalog per host, all three naming the same plugins at the same versions.
That identity is the whole point of a universal marketplace, so a version
mismatch is rejected before serialization rather than shipped and noticed later.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from .adapter import HOSTS
from .model import PluginSpec

CATALOG_NAME = "daodan"

CATALOG_DESCRIPTION = (
    "The Daodan: agents, skills and workflows that augment a coding agent into a "
    "specialized toolkit."
)

OWNER = {"name": "Alfio Caprino"}


class CatalogError(ValueError):
    pass


def _source(host: str, name: str) -> object:
    """Return the host-native source reference for one plugin."""
    if host == "codex":
        return {"source": "local", "path": f"./exports/codex/plugins/{name}"}
    return f"./exports/{host}/plugins/{name}"


def package_components(root: Path) -> dict[str, list[str]]:
    """Declared component paths for a rendered Claude package."""
    components: dict[str, list[str]] = {}
    for kind in ("agents", "commands"):
        directory = root / kind
        if directory.is_dir():
            paths = [f"./{kind}/{item.name}" for item in sorted(directory.glob("*.md"))]
            if paths:
                components[kind] = paths
    skills = root / "skills"
    if skills.is_dir():
        paths = [
            f"./skills/{item.name}"
            for item in sorted(skills.iterdir())
            if (item / "SKILL.md").is_file()
        ]
        if paths:
            components["skills"] = paths
    return components


def catalog_document(
    host: str,
    plugins: Sequence[PluginSpec],
    version: str,
    packages: Mapping[str, Path] | None = None,
) -> Mapping[str, object]:
    if host not in HOSTS:
        raise CatalogError(f"unknown host {host!r}")

    ordered = sorted(plugins, key=lambda plugin: plugin.name)
    seen: dict[str, str] = {}
    for plugin in ordered:
        if plugin.name in seen and seen[plugin.name] != plugin.version:
            raise CatalogError(
                f"{plugin.name}: version mismatch {seen[plugin.name]} against {plugin.version}"
            )
        seen[plugin.name] = plugin.version

    entries = []
    for plugin in ordered:
        entry: dict[str, object] = {
            "name": plugin.name,
            "description": plugin.description,
            "version": plugin.version,
            "license": plugin.license,
            "author": dict(OWNER),
            "dependencies": list(plugin.required_dependencies),
        }
        # A host that needs its components declared gets them from the package
        # that was just rendered, never from a hand-maintained list.
        if packages is not None and plugin.name in packages:
            entry.update(package_components(packages[plugin.name]))
        source = _source(host, plugin.name)
        if isinstance(source, dict):
            entry.update(source)
        else:
            entry["source"] = source
        entries.append(entry)

    return {
        "name": CATALOG_NAME,
        "metadata": {"description": CATALOG_DESCRIPTION, "version": version},
        "owner": OWNER,
        "plugins": entries,
    }


def render_catalog(
    host: str,
    plugins: Sequence[PluginSpec],
    version: str,
    packages: Mapping[str, Path] | None = None,
) -> bytes:
    """Serialize one host catalog deterministically."""
    document = catalog_document(host, plugins, version, packages)
    return (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("utf-8")


def assert_cross_host_identity(catalogs: Mapping[str, Mapping[str, object]]) -> None:
    """Fail unless every host lists the same plugins at the same versions."""
    reference: dict[str, str] | None = None
    for host, catalog in sorted(catalogs.items()):
        versions = {entry["name"]: entry["version"] for entry in catalog["plugins"]}
        if reference is None:
            reference = versions
        elif versions != reference:
            raise CatalogError(f"{host}: catalog identity differs from its peers")


def merge_into_legacy(
    existing: Mapping[str, object],
    plugins: Sequence[PluginSpec],
    host: str,
    packages: Mapping[str, Path],
) -> Mapping[str, object]:
    """Fold compiled entries into a catalog that still carries hand-written ones.

    Migration keeps the live Claude marketplace installable while plugins move to
    neutral kernels one at a time, so a compiled plugin replaces its own entry
    and nothing else in the catalog moves.
    """
    merged = json.loads(json.dumps(existing))
    compiled = {plugin.name: plugin for plugin in plugins}
    entries = []
    for entry in merged.get("plugins", []):
        plugin = compiled.pop(entry["name"], None)
        if plugin is not None:
            entry = dict(entry)
            entry["version"] = plugin.version
            entry["description"] = plugin.description
            entry["license"] = plugin.license
            source = _source(host, plugin.name)
            if isinstance(source, dict):
                entry.update(source)
            else:
                entry["source"] = source
            for kind in ("agents", "skills", "commands"):
                entry.pop(kind, None)
            entry.update(package_components(packages[plugin.name]))
        entries.append(entry)
    for name in sorted(compiled):
        plugin = compiled[name]
        entry = {
            "name": plugin.name,
            "description": plugin.description,
            "version": plugin.version,
            "license": plugin.license,
            "dependencies": list(plugin.required_dependencies),
        }
        source = _source(host, plugin.name)
        if isinstance(source, dict):
            entry.update(source)
        else:
            entry["source"] = source
        entry.update(package_components(packages[plugin.name]))
        entries.append(entry)
    merged["plugins"] = entries
    return merged
