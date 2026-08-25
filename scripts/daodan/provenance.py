"""Provenance for every generated plugin package.

``exports/`` is generated output, so a reader needs to be able to tell which
kernel and which harness produced a given tree without guessing. Every generated
plugin carries a ``.daodan-provenance.json`` with exactly these keys and nothing
else: an extra key would make the file drift into a second, unvalidated manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from .render import RenderResult

PROVENANCE_FILENAME = ".daodan-provenance.json"

ADAPTER_VERSION = "1.0.0"

KEYS = (
    "adapterVersion",
    "coreDigest",
    "harnessStrategies",
    "host",
    "overrides",
    "plugin",
    "version",
)


def provenance_document(result: "RenderResult", version: str) -> dict[str, object]:
    return {
        "adapterVersion": ADAPTER_VERSION,
        "coreDigest": result.core_digest,
        "harnessStrategies": {name: strategy for name, strategy in result.harness_strategies},
        "host": result.host,
        "overrides": list(result.overrides),
        "plugin": result.plugin,
        "version": version,
    }


def write_provenance(result: "RenderResult", version: str) -> Path:
    """Write the provenance file into the staged plugin tree."""
    document = provenance_document(result, version)
    if tuple(sorted(document)) != KEYS:
        raise ValueError("provenance document keys drifted from the declared contract")
    path = result.staging_root / PROVENANCE_FILENAME
    path.write_text(
        json.dumps(document, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return path
