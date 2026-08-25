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
import time
import tomllib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .adapter import HostAdapter, resolve_support, select_coordination
from .catalogs import OWNER
from .model import PluginSpec
from .overrides import OverrideSpec
from .provenance import ADAPTER_VERSION, write_provenance
from .templates import render_path, render_template

TEXT_SUFFIXES: frozenset[str] = frozenset({".md", ".toml", ".json", ".txt", ".yaml", ".yml"})

#: Build artifacts are never content. A kernel that has been run from carries
#: them, and copying them would publish a local machine's state.
IGNORED_DIRECTORIES: frozenset[str] = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache"})
IGNORED_SUFFIXES: frozenset[str] = frozenset({".pyc", ".pyo", ".orig", ".rej"})


def _is_artifact(relative: Path) -> bool:
    return (
        any(part in IGNORED_DIRECTORIES for part in relative.parts)
        or relative.suffix in IGNORED_SUFFIXES
    )

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
        (
            path
            for path in plugin.root.rglob("*")
            if path.is_file() and not _is_artifact(path.relative_to(plugin.root))
        ),
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


#: Neutral role tools, mapped onto one host's vocabulary. The kernel never names
#: a host tool, so this table is where a Claude-shaped agent body becomes a
#: Copilot-shaped one.
COPILOT_TOOLS = {
    "Read": "search",
    "Glob": "search",
    "Grep": "search",
    "Write": "edit",
    "Edit": "edit",
    "NotebookEdit": "edit",
    "Bash": "runCommands",
    "WebFetch": "fetch",
    "WebSearch": "fetch",
    "Agent": "agent",
    "Task": "agent",
}


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a Markdown body from its frontmatter, flattening multiline scalars."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return {}, normalized
    end = normalized.find("\n---\n", 4)
    if end == -1:
        return {}, normalized
    block = normalized[4:end]
    body = normalized[end + 5 :]

    meta: dict[str, str] = {}
    key: str | None = None
    for line in block.split("\n"):
        if line[:1] not in {" ", "\t"} and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            meta[key] = value.strip()
        elif key is not None and line.strip():
            meta[key] = f"{meta[key]} {line.strip()}".strip()
    for name, value in meta.items():
        if value.startswith(">") or value.startswith("|"):
            meta[name] = value[1:].strip()
    return meta, body


def _one_line(value: str) -> str:
    """Frontmatter scalars are rendered inline, so they may not carry breaks or quotes."""
    return " ".join(value.replace("'", "").split())


def _copilot_tools(value: str) -> str:
    declared = [item.strip() for item in value.strip("[] ").split(",") if item.strip()]
    mapped = []
    for item in declared:
        target = COPILOT_TOOLS.get(item)
        if target and target not in mapped:
            mapped.append(target)
    if not mapped:
        mapped = ["search"]
    return ", ".join(f"'{item}'" for item in mapped)


def _template(adapters_root: Path | None, host: str, name: str | None) -> str | None:
    if adapters_root is None or not name:
        return None
    candidate = Path(adapters_root) / host / "templates" / name
    return candidate.read_text(encoding="utf-8") if candidate.is_file() else None


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
        "author": OWNER["name"],
    }

    replacements = {spec.source: spec for spec in overrides}
    applied: list[str] = []

    manifest = render_template(_manifest_template(adapter, adapters_root), context)
    manifest_path = render_path(adapter.layout["plugin_manifest"], context)
    _write_text(staging_root / manifest_path, manifest)

    for skill in plugin.components.skills:
        source_directory = plugin.root / "skills" / skill
        target = staging_root / render_path(adapter.layout["skills"], {**context, "skill": skill})
        for path in sorted(source_directory.rglob("*"), key=lambda item: item.as_posix()):
            if not path.is_file():
                continue
            relative = path.relative_to(source_directory)
            if _is_artifact(relative):
                continue
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
            source = plugin.root / "roles" / f"{role}.md"
            role_template = _template(
                adapters_root, adapter.host, adapter.layout.get("role_template")
            )
            if role_template is None:
                _copy(source, target)
            else:
                meta, body = _frontmatter(source.read_text(encoding="utf-8"))
                _write_text(
                    target,
                    render_template(
                        role_template,
                        {
                            **context,
                            "name": meta.get("name", role),
                            "description": _one_line(meta.get("description", "")),
                            "tools": _copilot_tools(meta.get("tools", "")),
                            "body": body.strip() + "\n",
                        },
                    ),
                )

    for policy in plugin.components.policies:
        _copy(
            plugin.root / "policies" / f"{policy}.toml",
            staging_root / "policies" / f"{policy}.toml",
        )
        # A policy is declared neutrally and enforced per host. Where this host
        # ships an implementation of it, that implementation travels with the
        # package: the policy TOML says what must hold, the adapter file is how
        # this host makes it hold.
        if adapters_root is not None:
            implementation = _policy_implementation(adapters_root, adapter.host, policy)
            if implementation is not None:
                for item in sorted(implementation.rglob("*"), key=lambda x: x.as_posix()):
                    if item.is_file() and not _is_artifact(item.relative_to(implementation)):
                        _copy(
                            item,
                            staging_root / "policies" / policy / item.relative_to(implementation),
                        )

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
        fans_out = any(phase.fanout or phase.fanout_from for phase in workflow.phases)
        source = plugin.root / workflow.entrypoint
        if override is not None:
            _copy(override.root / override.replacement, target)
            applied.append(override.source)
        elif fans_out:
            harness = _harness_context(plugin, workflow, strategy, source, context)
            team_template = _template(
                adapters_root, adapter.host, adapter.layout.get("team_workflow_template")
            )
            if team_template is not None:
                _write_text(target, render_template(team_template, harness))
            else:
                _copy(source, target)
            coordinator_template = _template(
                adapters_root, adapter.host, adapter.layout.get("coordinator_template")
            )
            if coordinator_template is not None:
                coordinator = staging_root / render_path(
                    adapter.layout["coordinators"], {**context, "workflow": workflow.name}
                )
                _write_text(coordinator, render_template(coordinator_template, harness))
        else:
            _copy(source, target)
        for schema in workflow.contract.schemas:
            _copy(plugin.root / schema, staging_root / schema)
        # The sidecar travels with the package: a harness needs the declared
        # isolation, join and phase order at runtime, and a reader needs to be
        # able to check the contract without the kernel in hand.
        _copy(
            plugin.root / "workflows" / f"{workflow.name}.toml",
            staging_root / "contracts" / f"{workflow.name}.workflow.toml",
        )

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


def _policy_implementation(adapters_root: Path, host: str, policy: str) -> Path | None:
    """Find this host's implementation of a neutral policy, if it ships one.

    The mapping lives on the adapter side (`policy.toml`, `implements = ...`) so
    that the kernel never has to name a host mechanism to get one.
    """
    root = Path(adapters_root) / host / "policies"
    if not root.is_dir():
        return None
    for candidate in sorted(root.iterdir(), key=lambda item: item.name):
        manifest = candidate / "policy.toml"
        if not manifest.is_file():
            continue
        with manifest.open("rb") as handle:
            declared = tomllib.load(handle)
        if declared.get("implements") == policy:
            return candidate
    return None


def _harness_context(plugin, workflow, strategy, source: Path, context: dict) -> dict:
    """Everything a host harness template may substitute, and nothing else."""
    roles = []
    for phase in workflow.phases:
        for reference in phase.fanout:
            roles.append(reference.partition(":")[2] or reference)
        if phase.role:
            roles.append(phase.role)
    if any(phase.fanout_from for phase in workflow.phases):
        # Dynamic selection: which roles run is decided at runtime, so the
        # harness must be allowed to reach every role this plugin declares.
        roles.extend(plugin.components.roles)
    if not roles:
        roles = list(plugin.components.roles)
    ordered = sorted(set(roles))
    fanout_phase = next(
        (phase for phase in workflow.phases if phase.fanout or phase.fanout_from),
        workflow.phases[0],
    )
    meta, body = _frontmatter(source.read_text(encoding="utf-8"))
    return {
        **context,
        "workflow": workflow.name,
        "description": _one_line(meta.get("description", plugin.description)),
        "strategy": strategy.name,
        "role_delivery": strategy.role_delivery,
        "isolation": fanout_phase.isolation,
        "join": fanout_phase.join or "all-delivered",
        "roles": ", ".join(f"`{item}`" for item in ordered),
        "agents": ", ".join(f"'{item}'" for item in ordered),
        "body": body.strip() + "\n",
    }


def _rename_with_retry(source: Path, destination: Path, attempts: int = 10) -> None:
    """Rename a tree, retrying a transient sharing violation.

    On Windows a directory rename fails with access denied while any process
    still holds a handle inside it, and an indexer or scanner routinely holds one
    for a moment after a package is written. That is transient by nature, so it
    must not abort a publication that is otherwise correct.
    """
    for attempt in range(attempts):
        try:
            source.rename(destination)
            return
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.1 * (attempt + 1))


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
            _rename_with_retry(live, previous)
        try:
            _rename_with_retry(staging, live)
        except OSError as error:
            if had_live:
                _rename_with_retry(previous, live)
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
    staging = live.parent / f".{live.name}.{uuid.uuid4().hex}.staging"
    staging.mkdir()
    try:
        result = render_plugin(plugin, adapter, staging, overrides, adapters_root)
        replace_tree(staging, live)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
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
