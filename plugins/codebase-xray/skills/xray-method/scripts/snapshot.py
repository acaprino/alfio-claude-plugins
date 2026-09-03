#!/usr/bin/env python3
"""
Structural snapshots and incremental change sets for the X-ray.

A run records the tree it analyzed as `snapshot/manifest.json`: every file with
its size, mtime and content hash, and every symbol with its line span and a hash
of its body. A later run diffs that manifest against the current worktree and
learns, without spending a model token, which files and symbols changed, which
files import them, and which claims in the earlier run's phase files cite any of
it.

Subcommands:
    write <target> --out <manifest.json>

Standard library only. Parsing reuses the adapters in ./languages/.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ast_parser import parse_file  # noqa: E402
from languages import SUPPORTED_EXTENSIONS  # noqa: E402

__all__ = [
    "SCHEMA",
    "build_manifest",
    "file_entry",
    "hash_text",
    "is_forbidden",
    "iter_files",
    "read_text",
    "repo_root",
    "symbol_spans",
]

SCHEMA = 1

# Hashed but never parsed above this size; recorded with no symbols.
MAX_PARSE_BYTES = 2_000_000
# Not recorded at all above this size: a file this large is not what a claim cites.
MAX_FILE_BYTES = 20_000_000

# Pruned during the walk, so a large dependency tree is never descended into.
EXCLUDED_DIRS = frozenset({
    ".deep-dive", ".git", ".idea", ".mypy_cache", ".next", ".pytest_cache",
    ".tox", ".venv", ".vscode", "__pycache__", "build", "dist", "node_modules",
    "target", "vendor", "venv",
})

# Non-source files a phase file legitimately cites.
DOC_EXTENSIONS = frozenset({
    ".cfg", ".ini", ".json", ".md", ".ps1", ".rst", ".sh", ".toml", ".txt",
    ".xml", ".yaml", ".yml",
})

# The X-ray's forbidden list. These never enter the manifest, not even as a hash.
FORBIDDEN_GLOBS = (
    ".env", ".env.*", "credentials.*", "secrets.*", "*secret*", "*credential*",
    "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
    ".npmrc", ".pypirc", ".netrc",
)


def is_forbidden(name: str) -> bool:
    """True for a file the X-ray must never read. Case-insensitive."""
    lowered = name.lower()
    return any(fnmatch.fnmatchcase(lowered, glob) for glob in FORBIDDEN_GLOBS)


def iter_files(target: Path) -> Iterator[Path]:
    """Every file in the target the snapshot records, in a stable order."""
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        for name in sorted(filenames):
            if is_forbidden(name):
                continue
            path = Path(dirpath) / name
            suffix = path.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS and suffix not in DOC_EXTENSIONS:
                continue
            yield path


def read_text(path: Path) -> str:
    """File content with newlines normalized, so a line-ending change is not an edit."""
    data = path.read_bytes()
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def hash_text(text: str) -> str:
    """Short content hash. 16 hex characters: readable in a manifest, ample here."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def repo_root(target: Path) -> Path:
    """
    The base every manifest path is relative to: the git top level when the
    target is inside a repository, otherwise the target itself.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return target
    if proc.returncode != 0 or not proc.stdout.strip():
        return target
    return Path(proc.stdout.strip())


def git_info(root: Path) -> dict | None:
    """Commit, branch and dirtiness, as metadata. Nothing in the diff depends on it."""
    def run(*args: str) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return proc.stdout.strip() if proc.returncode == 0 else None

    commit = run("rev-parse", "HEAD")
    if not commit:
        return None
    return {
        "commit": commit[:12],
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(run("status", "--porcelain")),
    }


def symbol_spans(result, lines: list[str]) -> dict[str, dict]:
    """
    Every symbol in a parse result, qualified, with its line span and body hash.

    Top-level symbols (classes and free functions) are spanned first: an exact
    end line where the adapter has one, otherwise the line before the next
    top-level symbol. Methods are spanned inside their class, so a class span
    always encloses its methods and editing a method moves both hashes.
    """
    total = len(lines)
    top: list[dict] = []
    for cls in result.classes:
        if cls.line_number > 0:
            top.append({
                "name": cls.name, "kind": cls.kind, "start": cls.line_number,
                "end": getattr(cls, "end_line", None), "methods": list(cls.methods),
            })
    for func in result.functions:
        if func.line_number > 0:
            top.append({
                "name": func.name, "kind": "function", "start": func.line_number,
                "end": getattr(func, "end_line", None), "methods": [],
            })
    top.sort(key=lambda item: (item["start"], item["name"]))

    for index, item in enumerate(top):
        if not item["end"]:
            following = top[index + 1]["start"] - 1 if index + 1 < len(top) else total
            item["end"] = following
        item["end"] = max(item["end"], item["start"])

    spans: dict[str, dict] = {}

    def record(name: str, kind: str, start: int, end: int) -> None:
        start = max(1, min(start, total))
        end = max(start, min(end, total))
        spans[name] = {
            "kind": kind,
            "start": start,
            "end": end,
            "hash": hash_text("\n".join(lines[start - 1:end])),
        }

    for item in top:
        record(item["name"], item["kind"], item["start"], item["end"])
        methods = sorted(
            (m for m in item["methods"] if m.line_number > 0),
            key=lambda m: m.line_number,
        )
        for index, method in enumerate(methods):
            end = getattr(method, "end_line", None)
            if not end:
                end = methods[index + 1].line_number - 1 if index + 1 < len(methods) else item["end"]
            record(f"{item['name']}.{method.name}", "method", method.line_number, end)
    return spans


def file_entry(path: Path) -> dict:
    """One manifest row: identity, then structure when the file is parseable."""
    stat = path.stat()
    text = read_text(path)
    lines = text.split("\n")
    entry = {
        "size": stat.st_size,
        "mtime": round(stat.st_mtime, 3),
        "hash": hash_text(text),
        "language": None,
        "lines": len(lines),
        "symbols": {},
        "imports": [],
    }
    if SUPPORTED_EXTENSIONS.get(path.suffix.lower()) and stat.st_size <= MAX_PARSE_BYTES:
        try:
            result = parse_file(path)
        except Exception:  # a parser failure degrades to a file-level entry
            return entry
        entry["language"] = result.language
        entry["symbols"] = symbol_spans(result, lines)
        entry["imports"] = sorted({i.module for i in result.imports if i.is_internal and i.module})
    return entry


def relative_to_root(path: Path, root: Path) -> str:
    """POSIX path relative to the manifest root, or absolute when outside it."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_manifest(target: Path) -> dict:
    """The structural record of the tree a run analyzed."""
    target = target.resolve()
    root = repo_root(target).resolve()
    files: dict[str, dict] = {}
    for path in iter_files(target):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            files[relative_to_root(path, root)] = file_entry(path)
        except OSError:
            continue
    from datetime import datetime, timezone
    return {
        "schema": SCHEMA,
        "target": relative_to_root(target, root) or ".",
        "root": root.as_posix(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": git_info(root),
        "files": files,
    }


def cmd_write(args: argparse.Namespace) -> int:
    manifest = build_manifest(Path(args.target))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"snapshot: {len(manifest['files'])} files -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="X-ray structural snapshots and change sets.")
    sub = parser.add_subparsers(dest="command", required=True)

    write_parser = sub.add_parser("write", help="write a manifest for a target tree")
    write_parser.add_argument("target")
    write_parser.add_argument("--out", required=True)
    write_parser.set_defaults(func=cmd_write)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
