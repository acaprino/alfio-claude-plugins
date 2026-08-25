"""Deterministic rendering and transactional publication of host packages.

Two properties are load-bearing. **Equal inputs produce equal bytes**, so a
rebuild that changes nothing produces no diff and a drift check is meaningful.
And **a partial host tree is never written**: everything renders under a
temporary directory beside the live tree, every validator runs there, and only
then does one rename make it live.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .adapter import HostAdapter, resolve_support, select_coordination
from .model import PluginSpec
from .overrides import OverrideSpec
from .provenance import ADAPTER_VERSION, write_provenance
from .templates import render_path, render_template

TEXT_SUFFIXES: frozenset[str] = frozenset({".md", ".toml", ".json", ".txt", ".yaml", ".yml"})

DEFAULT_MANIFEST_TEMPLATE = """{
  "description": "${description}",
  "license": "${license}",
  "name": "${plugin}",
  "version": "${version}"
}
"""


class RenderError(RuntimeError):
    """Raised before a generated tree becomes live."""


@dataclass(frozen=True)
class RenderResult:
    plugin: str
    host: str
    staging_root: Path
    files: tuple[Path, ...]
    core_digest: str
    harness_strategies: tuple[tuple[str, str], ...]
    overrides: tuple[str, ...]


def tree_digest(root: Path) -> str:
    """Digest a whole tree by relative path and content."""
    digest = hashlib.sha256()
    for path in sorted(
        (item for item in Path(root).rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _kernel_files(plugin: PluginSpec) -> list[Path]:
    return sorted(
        (path for path in plugin.root.rglob("*") if path.is_file()),
        key=lambda item: item.as_posix(),
    )


def _kernel_digest(plugin: PluginSpec) -> str:
    digest = hashlib.sha256()
    for path in _kernel_files(plugin):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _write_text(destination: Path, content: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    destination.write_bytes(normalized.encode("utf-8"))


def _copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in TEXT_SUFFIXES:
        _write_text(destination, source.read_text(encoding="utf-8"))
    else:
        shutil.copyfile(source, destination)


def _manifest_template(adapter: HostAdapter, adapters_root: Path | None) -> str:
    if adapters_root is not None:
        candidate = Path(adapters_root) / adapter.host / "templates" / "plugin.json.tmpl"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    return DEFAULT_MANIFEST_TEMPLATE


def render_plugin(
    plugin: PluginSpec,
    adapter: HostAdapter,
    destination: Path,
    overrides: Sequence[OverrideSpec] = (),
    adapters_root: Path | None = None,
) -> RenderResult:
    """Render one neutral plugin into one host's package layout.

    ``destination`` is a staging root: this function never touches live output.
    """
    support = resolve_support(plugin, adapter)
    if support.state == "unsupported":
        raise RenderError(
            f"{adapter.host}: {plugin.name} is unsupported "
            f"(missing: {', '.join(support.missing_capabilities) or 'no viable coordination strategy'})"
        )

    staging_root = Path(destination)
    staging_root.mkdir(parents=True, exist_ok=True)

    context = {
        "plugin": plugin.name,
        "version": plugin.version,
        "description": plugin.description,
        "license": plugin.license,
        "host": adapter.host,
        "adapter_version": ADAPTER_VERSION,
    }

    replacements = {spec.source: spec for spec in overrides}
    applied: list[str] = []

    manifest = render_template(_manifest_template(adapter, adapters_root), context)
    _write_text(staging_root / "plugin.json", manifest)

    for skill in plugin.components.skills:
        source_directory = plugin.root / "skills" / skill
        target = staging_root / render_path(adapter.layout["skills"], {**context, "skill": skill})
        for path in sorted(source_directory.rglob("*"), key=lambda item: item.as_posix()):
            if not path.is_file():
                continue
            relative = path.relative_to(source_directory)
            if relative.as_posix() == "SKILL.md":
                _copy(path, target)
            else:
                _copy(path, target.parent / relative)

    for role in plugin.components.roles:
        target = staging_root / render_path(adapter.layout["roles"], {**context, "role": role})
        override = replacements.get(f"role:{role}")
        if override is not None:
            _copy(override.root / override.replacement, target)
            applied.append(override.source)
        else:
            _copy(plugin.root / "roles" / f"{role}.md", target)

    strategies: list[tuple[str, str]] = []
    for workflow in plugin.workflows:
        strategy = select_coordination(workflow, adapter)
        if strategy is None:
            raise RenderError(f"{adapter.host}: no coordination strategy for {workflow.name}")
        strategies.append((workflow.name, strategy.name))
        target = staging_root / render_path(
            adapter.layout["workflows"], {**context, "workflow": workflow.name}
        )
        override = replacements.get(f"workflow:{workflow.name}")
        if override is not None:
            _copy(override.root / override.replacement, target)
            applied.append(override.source)
        else:
            _copy(plugin.root / workflow.entrypoint, target)
        for schema in workflow.contract.schemas:
            _copy(plugin.root / schema, staging_root / schema)

    files = tuple(
        sorted(
            (path.relative_to(staging_root) for path in staging_root.rglob("*") if path.is_file()),
            key=lambda item: item.as_posix(),
        )
    )

    result = RenderResult(
        plugin=plugin.name,
        host=adapter.host,
        staging_root=staging_root,
        files=files,
        core_digest=_kernel_digest(plugin),
        harness_strategies=tuple(strategies),
        overrides=tuple(sorted(set(applied))),
    )
    write_provenance(result, plugin.version)
    return result


def replace_tree(staging: Path, live: Path) -> None:
    """Swap a fully validated staging tree into place, or leave the live tree alone.

    A sibling lock keeps two builders from swapping the same output, and a
    ``.previous`` backup is what makes the swap recoverable: the live tree is
    never edited file-by-file.
    """
    staging = Path(staging)
    live = Path(live)
    if not staging.is_dir():
        raise RenderError(f"staging tree does not exist: {staging}")

    live.parent.mkdir(parents=True, exist_ok=True)
    lock = live.parent / f".{live.name}.lock"
    previous = live.parent / f".{live.name}.previous"

    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RenderError(f"another build holds {lock}") from error
    os.close(handle)

    try:
        if previous.exists():
            shutil.rmtree(previous)
        had_live = live.exists()
        if had_live:
            live.rename(previous)
        try:
            staging.rename(live)
        except OSError as error:
            if had_live:
                previous.rename(live)
            raise RenderError(f"could not publish {live}: {error}") from error
        if had_live:
            shutil.rmtree(previous, ignore_errors=True)
    finally:
        lock.unlink(missing_ok=True)


def publish_plugin(
    plugin: PluginSpec,
    adapter: HostAdapter,
    live: Path,
    overrides: Sequence[OverrideSpec] = (),
    adapters_root: Path | None = None,
) -> RenderResult:
    """Render into a temporary sibling of ``live`` and publish it atomically."""
    live = Path(live)
    live.parent.mkdir(parents=True, exist_ok=True)
    holder = tempfile.mkdtemp(dir=live.parent)
    staging = Path(holder) / live.name
    try:
        result = render_plugin(plugin, adapter, staging, overrides, adapters_root)
        replace_tree(staging, live)
    finally:
        shutil.rmtree(holder, ignore_errors=True)
    return RenderResult(
        plugin=result.plugin,
        host=result.host,
        staging_root=live,
        files=result.files,
        core_digest=result.core_digest,
        harness_strategies=result.harness_strategies,
        overrides=result.overrides,
    )


def read_provenance(root: Path) -> dict[str, object]:
    return json.loads((Path(root) / ".daodan-provenance.json").read_text(encoding="utf-8"))
