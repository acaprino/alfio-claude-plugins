"""Fingerprinted semantic overrides.

Every semantic divergence between hosts lives in an override under
``adapters/<host>/overrides/``, never as a quiet edit inside a rendered package.
An override carries the digest of the neutral source it was reviewed against, so
when that source moves the override is reported stale rather than silently
serving a superseded meaning.

An override can select a different declared mechanism. It can never add a tool,
MCP server, LSP server, hook or capability the kernel did not declare.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, Iterable, Mapping

from .validate import ValidationIssue

OVERRIDE_MANIFEST = "override.toml"

REQUIRED_KEYS = (
    "source",
    "source_paths",
    "reason",
    "strategy",
    "reviewed_against",
    "contracts_preserved",
    "capabilities_affected",
    "replacement",
)


@dataclass(frozen=True)
class OverrideSpec:
    root: Path
    source: str
    source_paths: tuple[Path, ...]
    reason: str
    strategy: str
    reviewed_against: str
    contracts_preserved: tuple[str, ...]
    capabilities_affected: tuple[str, ...]
    replacement: Path


class OverrideError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def source_digest(paths: Iterable[Path]) -> str:
    """Digest a set of neutral source files, path and content, order-independently."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _strings(path: Path, table: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = table[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise OverrideError(path, f"{key} must be an array of strings")
    return tuple(value)


def load_override(manifest: Path) -> OverrideSpec:
    with manifest.open("rb") as handle:
        try:
            table = tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            raise OverrideError(manifest, f"invalid TOML: {error}") from error

    for key in REQUIRED_KEYS:
        if key not in table:
            raise OverrideError(manifest, f"override requires {key!r}")
    unknown = sorted(set(table) - set(REQUIRED_KEYS))
    if unknown:
        raise OverrideError(manifest, f"unknown override key(s): {', '.join(unknown)}")

    for key in ("source", "reason", "strategy", "reviewed_against", "replacement"):
        if not isinstance(table[key], str):
            raise OverrideError(manifest, f"{key} must be a string")

    return OverrideSpec(
        root=manifest.parent,
        source=table["source"],
        source_paths=tuple(Path(item) for item in _strings(manifest, table, "source_paths")),
        reason=table["reason"],
        strategy=table["strategy"],
        reviewed_against=table["reviewed_against"],
        contracts_preserved=_strings(manifest, table, "contracts_preserved"),
        capabilities_affected=_strings(manifest, table, "capabilities_affected"),
        replacement=Path(table["replacement"]),
    )


def load_overrides(path: Path) -> tuple[OverrideSpec, ...]:
    """Load every override manifest at or under ``path``, in path order."""
    root = Path(path)
    if (root / OVERRIDE_MANIFEST).is_file():
        return (load_override(root / OVERRIDE_MANIFEST),)
    manifests = sorted(root.rglob(OVERRIDE_MANIFEST), key=lambda item: item.as_posix())
    return tuple(load_override(manifest) for manifest in manifests)


def validate_override(
    spec: OverrideSpec,
    declared_capabilities: AbstractSet[str],
    declared_contracts: AbstractSet[str] | None = None,
    repository_root: Path | None = None,
) -> list[ValidationIssue]:
    """Report every reason this override may not be applied."""
    issues: list[ValidationIssue] = []
    manifest = spec.root / OVERRIDE_MANIFEST
    base = Path(repository_root) if repository_root is not None else Path.cwd()

    replacement = spec.replacement
    if replacement.is_absolute() or ".." in replacement.parts:
        issues.append(
            ValidationIssue("override-escapes-directory", manifest, replacement.as_posix())
        )
    elif not (spec.root / replacement).is_file():
        issues.append(
            ValidationIssue("override-missing-replacement", manifest, replacement.as_posix())
        )

    missing_sources = [path for path in spec.source_paths if not (base / path).is_file()]
    if missing_sources:
        for path in missing_sources:
            issues.append(ValidationIssue("override-missing-source", manifest, path.as_posix()))
    else:
        current = source_digest([base / path for path in spec.source_paths])
        if current != spec.reviewed_against:
            issues.append(ValidationIssue("stale-override", manifest, spec.source))

    escalated = [
        capability
        for capability in spec.capabilities_affected
        if capability not in declared_capabilities
    ]
    for capability in escalated:
        issues.append(ValidationIssue("override-capability-escalation", manifest, capability))

    if declared_contracts is not None:
        for contract in spec.contracts_preserved:
            if contract not in declared_contracts:
                issues.append(ValidationIssue("override-drops-contract", manifest, contract))

    return issues
