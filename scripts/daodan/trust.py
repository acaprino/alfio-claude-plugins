"""Trust scanning for the compiler's inputs and staged outputs.

A generated marketplace is published content, so a secret that reaches
``plugins/``, ``adapters/`` or a staged export is a secret that ships. This scan
refuses those paths outright rather than trying to judge whether a given file is
a real credential.

It never prints matched content: a diagnostic that quotes the secret it found
has published it a second time.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import AbstractSet

from .validate import ValidationIssue

SECRET_FILENAMES: frozenset[str] = frozenset(
    {
        ".env",
        ".netrc",
        "_netrc",
        ".npmrc",
        ".pypirc",
        ".htpasswd",
        "credentials",
        "credentials.json",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
    }
)

SECRET_SUFFIXES: frozenset[str] = frozenset({".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"})

SECRET_DIRECTORIES: frozenset[str] = frozenset({"secrets", "credentials"})

PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")

TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".py", ".js", ".sh", ".cfg", ".ini", ""}
)


def _is_secret_path(relative: Path) -> bool:
    name = relative.name
    if name in SECRET_FILENAMES:
        return True
    if name.startswith(".env."):
        return True
    if relative.suffix in SECRET_SUFFIXES:
        return True
    return any(part in SECRET_DIRECTORIES for part in relative.parts[:-1])


def scan_trust(root: Path, allowlisted: AbstractSet[Path]) -> list[ValidationIssue]:
    """Report secret-shaped paths and embedded private keys under ``root``.

    ``allowlisted`` holds exact repository-relative paths of synthetic test
    fixtures. Nothing else is exempt.
    """
    root = Path(root)
    allowed = {Path(item) for item in allowlisted}
    issues: list[ValidationIssue] = []

    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative in allowed:
            continue
        if ".git" in relative.parts:
            continue
        if _is_secret_path(relative):
            issues.append(
                ValidationIssue("forbidden-secret-path", path, relative.as_posix())
            )
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if PRIVATE_KEY_HEADER.search(content):
            issues.append(ValidationIssue("embedded-private-key", path, relative.as_posix()))

    return issues
