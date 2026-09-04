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
        Write a structural snapshot of a target tree.
    diff <parent_run> <target> --out <run_dir>
        Diff a parent run's snapshot against the worktree; write changes.json/changes.md.
    carry <parent_run> <run_dir>
        Copy the parent run's phase files forward, renumbering citations and marking stale claims.
    check <run_dir>
        Publication gate: fail on any surviving stale marker or undocumented added symbol.

Standard library only. Parsing reuses the adapters in ./languages/.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
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
    "MARKER_PREFIX",
    "PHASE_FILES",
    "SCHEMA",
    "blast_radius",
    "build_import_index",
    "build_manifest",
    "compare_files",
    "compare_symbols",
    "file_entry",
    "hash_text",
    "is_forbidden",
    "iter_files",
    "read_text",
    "recommend",
    "renumber_line",
    "repo_root",
    "resolve_module",
    "scan_claims",
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
        # A class carrying two methods of the same name (an overload) would
        # otherwise have the second `record()` call overwrite the first,
        # losing the earlier span entirely: an edit inside the lost overload
        # then changes no hash, and compare_symbols never reports it. Widen
        # the span to cover every occurrence instead, so any edit to any of
        # them moves the hash. That over-marks rather than under-marks: it
        # costs one extra re-derivation instead of a missed claim.
        existing = spans.get(name)
        if existing is not None:
            start = min(start, existing["start"])
            end = max(end, existing["end"])
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


def compare_files(manifest: dict, target: Path, verify: bool = False) -> dict:
    """
    Classify every path as added, removed, modified or unchanged.

    Fast path: equal size and mtime means unchanged, with no read at all. Any
    other case is hashed, because a checkout or a `touch` moves the mtime
    without changing a byte, and the hash is what decides.
    """
    target = target.resolve()
    root = repo_root(target).resolve()
    old = manifest.get("files", {})
    current: dict[str, Path] = {}
    for path in iter_files(target):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        current[relative_to_root(path, root)] = path

    added, removed, modified, unchanged = [], [], [], []
    for rel, entry in old.items():
        path = current.get(rel)
        if path is None:
            removed.append(rel)
            continue
        try:
            stat = path.stat()
        except OSError:
            removed.append(rel)
            continue
        if not verify and stat.st_size == entry.get("size") and round(stat.st_mtime, 3) == entry.get("mtime"):
            unchanged.append(rel)
            continue
        try:
            same = hash_text(read_text(path)) == entry.get("hash")
        except OSError:
            same = False
        (unchanged if same else modified).append(rel)
    for rel in current:
        if rel not in old:
            added.append(rel)

    return {
        "root": root.as_posix(),
        "added": sorted(added),
        "removed": sorted(removed),
        "modified": sorted(modified),
        "unchanged": sorted(unchanged),
        "current": current,
    }


def compare_symbols(manifest: dict, comparison: dict) -> dict:
    """
    Classify symbols inside added and modified files, and record how the lines
    of every surviving symbol moved.

    `fresh` carries the re-parsed structure of those files so the caller does
    not parse them a second time.
    """
    old_files = manifest.get("files", {})
    added, removed, changed = [], [], []
    renumber: dict[str, list[dict]] = {}
    fresh: dict[str, dict] = {}

    for rel in comparison["added"] + comparison["modified"]:
        path = comparison["current"][rel]
        try:
            entry = file_entry(path)
        except OSError:
            continue
        fresh[rel] = {"symbols": entry["symbols"], "imports": entry["imports"]}
        old_symbols = old_files.get(rel, {}).get("symbols", {})
        new_symbols = entry["symbols"]
        moved: list[dict] = []
        for name, spec in new_symbols.items():
            previous = old_symbols.get(name)
            if previous is None:
                added.append({"file": rel, "symbol": name, "kind": spec["kind"]})
            elif previous["hash"] != spec["hash"]:
                changed.append({"file": rel, "symbol": name, "kind": spec["kind"]})
            else:
                moved.append({
                    "symbol": name,
                    "start_old": previous["start"],
                    "end_old": previous["end"],
                    "start_new": spec["start"],
                })
        for name, previous in old_symbols.items():
            if name not in new_symbols:
                removed.append({"file": rel, "symbol": name, "kind": previous["kind"]})
        if moved:
            renumber[rel] = sorted(moved, key=lambda m: m["start_old"])

    for rel in comparison["removed"]:
        for name, previous in old_files.get(rel, {}).get("symbols", {}).items():
            removed.append({"file": rel, "symbol": name, "kind": previous["kind"]})

    order = lambda item: (item["file"], item["symbol"])  # noqa: E731
    return {
        "added": sorted(added, key=order),
        "removed": sorted(removed, key=order),
        "changed": sorted(changed, key=order),
        "renumber": renumber,
        "fresh": fresh,
    }


# Extensions an import specifier may resolve to, in preference order.
_MODULE_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".java", ".rs")
# Directory imports: `orders` resolving to the package's entry file.
_PACKAGE_FILES = ("__init__.py", "index.ts", "index.tsx", "index.js", "index.jsx", "mod.rs")


def _by_basename(paths) -> dict[str, list[str]]:
    """
    Group paths by their final segment, each group sorted.

    Sorted rather than insertion order because the caller usually passes a
    set, whose iteration order depends on Python's per-process hash
    randomization: left unsorted, an ambiguous bare-basename citation with
    several candidates could resolve to a different one on every run of the
    identical tree. The ambiguity itself is not resolved here, only made to
    pick the same candidate consistently.
    """
    index: dict[str, list[str]] = {}
    for path in paths:
        index.setdefault(path.rsplit("/", 1)[-1], []).append(path)
    for candidates in index.values():
        candidates.sort()
    return index


def _lookup(candidate: str, known: dict[str, list[str]], importer: str) -> str | None:
    """
    Resolve one candidate path against the known set.

    A candidate matches a known path when it equals it or is a suffix of it at a
    segment boundary, because an import specifier names a module, not a path
    from the repository root. When several match, the one in the importer's own
    directory wins; a tie with no local winner resolves to nothing, since
    inflating the radius on a guess costs a re-read of the wrong file.
    """
    while candidate.startswith("./"):
        candidate = candidate[2:]
    if not candidate:
        return None
    hits = [p for p in known.get(candidate.rsplit("/", 1)[-1], [])
            if p == candidate or p.endswith("/" + candidate)]
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    home = importer.rsplit("/", 1)[0] if "/" in importer else ""
    local = [p for p in hits if p.rsplit("/", 1)[0] == home]
    return local[0] if len(local) == 1 else None


def resolve_module(module: str, importer: str, known: dict[str, list[str]]) -> str | None:
    """Map an import specifier to a path in the snapshot, or None."""
    if not module:
        return None
    candidates: list[str] = []
    if module.startswith("."):
        base = importer.rsplit("/", 1)[0] if "/" in importer else ""
        joined = os.path.normpath(os.path.join(base, module)).replace(os.sep, "/")
        candidates.append(joined)
        candidates += [joined + ext for ext in _MODULE_EXTENSIONS]
        candidates += [f"{joined}/{name}" for name in _PACKAGE_FILES]
    else:
        dotted = module.replace(".", "/")
        candidates += [dotted + ext for ext in _MODULE_EXTENSIONS]
        candidates += [f"{dotted}/{name}" for name in _PACKAGE_FILES]
        # A specifier that is already path-shaped ("orders/service").
        if "/" in module:
            candidates += [module] + [module + ext for ext in _MODULE_EXTENSIONS]
    for candidate in candidates:
        hit = _lookup(candidate, known, importer)
        if hit:
            return hit
    return None


def build_import_index(manifest: dict, comparison: dict, symbols: dict) -> dict[str, list[str]]:
    """
    Reverse import edges over the CURRENT view of the tree: the manifest's
    imports for unchanged files, the fresh parse for added and modified ones.
    Removed files contribute no outgoing edges of their own, since a deleted
    file no longer imports anything.

    They still have to be resolvable AS TARGETS, though: a surviving,
    unchanged importer's own import list still names the module that used to
    point at the removed file, and that edge is exactly what a removed file's
    blast radius depends on. So the known set for resolution is the current
    tree plus every removed file's last-known path, while the set actually
    walked for outgoing edges stays the current tree only.
    """
    old_files = manifest.get("files", {})
    fresh = symbols.get("fresh", {})
    current_imports: dict[str, list[str]] = {}
    for rel in comparison["unchanged"]:
        current_imports[rel] = list(old_files.get(rel, {}).get("imports", []))
    for rel, entry in fresh.items():
        current_imports[rel] = list(entry.get("imports", []))

    resolvable = list(current_imports) + [rel for rel in comparison["removed"] if rel not in current_imports]
    known = _by_basename(resolvable)
    index: dict[str, list[str]] = {}
    for importer, modules in current_imports.items():
        for module in modules:
            imported = resolve_module(module, importer, known)
            if imported and imported != importer:
                index.setdefault(imported, [])
                if importer not in index[imported]:
                    index[imported].append(importer)
    return {key: sorted(value) for key, value in index.items()}


def blast_radius(index: dict[str, list[str]], comparison: dict, symbols: dict) -> list[dict]:
    """
    Files importing something that changed. One hop, never the transitive
    closure: on most codebases the closure is the whole tree, which is a full
    run wearing a different name.

    A modified file whose symbols all survived unchanged (lines shifted, a
    comment rewritten) puts nobody in the radius: an importer depends on what a
    module offers, not on where its lines sit. A removed file, and a modified
    file with no symbols at all, always do.
    """
    moved: set[str] = set()
    for state in ("added", "removed", "changed"):
        moved.update(item["file"] for item in symbols[state])
    structureless = {
        rel for rel in comparison["modified"]
        if not symbols.get("fresh", {}).get(rel, {}).get("symbols")
    }
    touched = (set(comparison["modified"]) & (moved | structureless)) | set(comparison["removed"])
    reverse: dict[str, list[str]] = {}
    for imported in touched:
        for importer in index.get(imported, []):
            if importer in touched:
                continue
            reverse.setdefault(importer, []).append(imported)
    return [{"file": key, "imports": sorted(value)} for key, value in sorted(reverse.items())]


PHASE_FILES = (
    "01-structure.md", "02-interfaces.md", "03-flows.md", "04-semantics.md",
    "05-risks.md", "06-documentation.md", "07-final-report.md",
    "08-interconnect-map.md",
)

# `src/app/service.py::Class.method`
CITE_SYMBOL = re.compile(r"([\w./\\-]+\.[A-Za-z0-9_]+)::([A-Za-z_][\w.]*)")
# `src/app/service.py:42`
CITE_LINE = re.compile(r"([\w./\\-]+\.[A-Za-z0-9_]+):(\d+)\b")
# A bare path inside backticks or a table cell.
CITE_PATH = re.compile(r"[`|\s(\[]([\w./\\-]+\.[A-Za-z0-9_]+)[`|\s),\]]")


def _path_index(paths) -> dict[str, list[str]]:
    return _by_basename(paths)


def _match_cited_path(cited: str, index: dict[str, list[str]]) -> str | None:
    """A phase file cites a path as the model wrote it; match at a segment boundary."""
    normalized = cited.replace("\\", "/").lstrip("./")
    if not normalized:
        return None
    for candidate in index.get(normalized.rsplit("/", 1)[-1], []):
        if candidate == normalized or candidate.endswith("/" + normalized) or normalized.endswith("/" + candidate):
            return candidate
    return None


def _symbol_verdict(path: str, symbol: str, changed: set, removed: set, added_files: set,
                    removed_files: set) -> str | None:
    """
    A claim about a symbol is affected by what happened to THAT symbol, matched
    exactly. Never by what happened to its enclosing class: a class span
    encloses its methods, so editing any one method moves the class hash, and
    walking up to the class would mark every claim about every sibling method.
    A claim about the class as a whole cites the class, and is caught by the
    exact match on it.
    """
    if path in removed_files:
        return "file-removed"
    if path in added_files:
        return "file-added"
    if (path, symbol) in removed:
        return "symbol-removed"
    if (path, symbol) in changed:
        return "symbol-changed"
    return None


def scan_claims(parent_dir: Path, comparison: dict, symbols: dict, importers: list[dict]) -> list[dict]:
    """
    Every line in the parent's phase files that cites something the change set
    touched, with the reason it is affected. Excludes 07-final-report.md:
    Phase 7 is regenerated on every run, never carried, so a claim living only
    there is not a work item, and counting it would inflate claims_affected
    and the per-phase breakdown the checkpoint prints.
    """
    modified = set(comparison["modified"])
    added_files = set(comparison["added"])
    removed_files = set(comparison["removed"])
    importer_files = {entry["file"] for entry in importers}
    changed = {(item["file"], item["symbol"]) for item in symbols["changed"]}
    removed = {(item["file"], item["symbol"]) for item in symbols["removed"]}
    spans = {
        rel: {entry["symbol"]: entry for entry in entries}
        for rel, entries in symbols["renumber"].items()
    }
    index = _path_index(
        set(comparison["unchanged"]) | modified | added_files | removed_files | importer_files
    )

    claims: list[dict] = []
    for name in PHASE_FILES:
        if name == "07-final-report.md":
            continue  # Phase 7 is regenerated, never carried; see docstring.
        phase_path = parent_dir / name
        if not phase_path.exists():
            continue
        section = ""
        for number, line in enumerate(read_text(phase_path).split("\n"), start=1):
            if line.startswith("#"):
                section = line.strip()
                continue
            cites: list[str] = []
            reason: str | None = None

            for path_text, symbol in CITE_SYMBOL.findall(line):
                path = _match_cited_path(path_text, index)
                if not path:
                    continue
                cites.append(f"{path}::{symbol}")
                verdict = _symbol_verdict(path, symbol, changed, removed, added_files, removed_files)
                reason = reason or verdict
                if verdict is None and path in importer_files:
                    reason = reason or "importer"

            for path_text, line_text in CITE_LINE.findall(line):
                path = _match_cited_path(path_text, index)
                if not path:
                    continue
                cites.append(f"{path}:{line_text}")
                if path in removed_files:
                    reason = reason or "file-removed"
                elif path in added_files:
                    reason = reason or "file-added"
                elif path in modified:
                    inside = any(
                        entry["start_old"] <= int(line_text) <= entry["end_old"]
                        for entry in spans.get(path, {}).values()
                    )
                    if not inside:
                        reason = reason or "line-outside-known-symbol"
                elif path in importer_files:
                    reason = reason or "importer"

            # The bare-path fallback runs ONLY when the line carried no precise
            # citation. A line that named a symbol or a line number has already
            # been judged at that precision, and re-judging it by its file would
            # mark every claim about every unchanged symbol in a modified file:
            # the symbol-level granularity, thrown away at the last step.
            if reason is None and not cites:
                for path_text in CITE_PATH.findall(line):
                    path = _match_cited_path(path_text, index)
                    if not path:
                        continue
                    if path in removed_files:
                        reason = "file-removed"
                    elif path in added_files:
                        reason = "file-added"
                    elif path in modified:
                        reason = "file-modified"
                    elif path in importer_files:
                        reason = "importer"
                    if reason:
                        cites.append(path)
                        break

            if reason:
                claims.append({
                    "phase_file": name,
                    "line": number,
                    "section": section,
                    "cites": sorted(set(cites)),
                    "reason": reason,
                })
    return claims


def recommend(ratio: float, threshold: float, affected: int, reasons: list[str]) -> str:
    if reasons:
        return "full"
    if affected == 0:
        return "none"
    if ratio > threshold:
        reasons.append(f"ratio {ratio:.2f} over threshold {threshold:.2f}")
        return "full"
    return "incremental"


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _changes_markdown(changes: dict) -> str:
    files = changes["files"]
    lines = ["# X-Ray Change Set", ""]
    parent = changes.get("parent_run") or "none"
    git = changes.get("git") or {}
    head = f"Parent run: {parent}."
    if git.get("commit"):
        head += f" Worktree at {git['commit']}" + (" (dirty)." if git.get("dirty") else ".")
    lines += [head, "", "## Code changes", ""]
    lines.append(
        f"{len(files['modified'])} modified, {len(files['added'])} added, "
        f"{len(files['removed'])} removed, of {changes['totals']['files_in_snapshot']} in the snapshot."
    )
    lines.append("")
    for label, key in (("Modified", "modified"), ("Added", "added"), ("Removed", "removed")):
        if files[key]:
            lines.append(f"**{label}:**")
            lines += [f"- `{path}`" for path in files[key]]
            lines.append("")
    if any(changes["symbols"].values()):
        lines += ["| Symbol | File | Kind | Change |", "|---|---|---|---|"]
        for state in ("changed", "added", "removed"):
            for item in changes["symbols"][state]:
                lines.append(f"| `{item['symbol']}` | `{item['file']}` | {item['kind']} | {state} |")
        lines.append("")
    lines += ["## Blast radius", ""]
    if changes["importers"]:
        lines += ["| Importer | Imports |", "|---|---|"]
        lines += [
            f"| `{entry['file']}` | {', '.join('`' + i + '`' for i in entry['imports'])} |"
            for entry in changes["importers"]
        ]
    else:
        lines.append("No file imports anything that changed.")
    lines += ["", "## Affected claims", ""]
    if changes["claims"]:
        lines += ["| Phase file | Line | Section | Cites | Reason |", "|---|---|---|---|---|"]
        lines += [
            f"| {c['phase_file']} | {c['line']} | {c['section']} | "
            f"{', '.join('`' + x + '`' for x in c['cites'])} | {c['reason']} |"
            for c in changes["claims"]
        ]
    else:
        lines.append("No claim in the parent run cites anything that changed.")
    lines.append("")
    return "\n".join(lines)


def cmd_diff(args: argparse.Namespace) -> int:
    parent_dir = Path(args.parent_run)
    target = Path(args.target)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    reasons: list[str] = []
    manifest = _read_json(parent_dir / "snapshot" / "manifest.json")
    parent_state = _read_json(parent_dir / "state.json") or {}
    if manifest is None:
        reasons.append("parent run has no snapshot manifest")
        manifest = {"files": {}, "target": None, "created_at": None}
    if parent_state.get("status") not in (None, "complete"):
        reasons.append(f"parent run status is {parent_state.get('status')}")
    if args.flags:
        try:
            requested = json.loads(args.flags)
        except ValueError:
            requested = {}
        parent_flags = parent_state.get("flags") or {}
        differing = sorted(k for k, v in requested.items() if parent_flags.get(k) != v)
        if differing:
            reasons.append("flags differ from the parent run: " + ", ".join(differing))

    comparison = compare_files(manifest, target, verify=args.verify)
    symbols = compare_symbols(manifest, comparison)
    index = build_import_index(manifest, comparison, symbols)
    importers = blast_radius(index, comparison, symbols)
    claims = scan_claims(parent_dir, comparison, symbols, importers) if manifest.get("files") else []

    affected_files = sorted(
        set(comparison["added"]) | set(comparison["removed"]) | set(comparison["modified"])
        | {entry["file"] for entry in importers}
    )
    # With no parent manifest, this falls back to the current worktree's file
    # count: the same fallback the ratio's denominator uses just below, so the
    # two always agree. A consumer that recomputes the ratio from the stored
    # totals must never divide by a files_in_snapshot of 0.
    total = len(manifest.get("files") or {}) or len(comparison["current"]) or 1
    ratio = len(affected_files) / total
    recommendation = recommend(ratio, args.threshold, len(affected_files), reasons)

    from datetime import datetime, timezone
    changes = {
        "schema": SCHEMA,
        "parent_run": parent_state.get("run_id") or parent_dir.name,
        "base_snapshot_created_at": manifest.get("created_at"),
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": git_info(repo_root(target.resolve()).resolve()),
        "files": {
            "added": comparison["added"],
            "removed": comparison["removed"],
            "modified": comparison["modified"],
        },
        "symbols": {
            "added": symbols["added"],
            "removed": symbols["removed"],
            "changed": symbols["changed"],
        },
        "renumber": symbols["renumber"],
        "importers": importers,
        "affected_files": affected_files,
        "claims": claims,
        "totals": {
            "files_in_snapshot": total,
            "affected_files": len(affected_files),
            "ratio": round(ratio, 4),
            "claims_affected": len(claims),
        },
        "recommendation": recommendation,
        "reasons": reasons,
    }
    (out_dir / "changes.json").write_text(
        json.dumps(changes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "changes.md").write_text(_changes_markdown(changes), encoding="utf-8")
    print(
        f"change set: {recommendation}; {len(affected_files)} affected files of {total}, "
        f"{len(claims)} affected claims -> {out_dir / 'changes.json'}"
    )
    return 0


MARKER_PREFIX = "<!-- xray:stale"


def renumber_line(text: str, renumber: dict, index: dict) -> str:
    """
    Move every `path:line` citation of a modified file onto its new line, when
    the old line falls inside a symbol that survived the edit. A citation
    outside every surviving span is left alone: the diff already marked its
    claim affected, so the model rewrites it rather than trusting the number.
    """
    def replace(match: "re.Match[str]") -> str:
        cited, number = match.group(1), int(match.group(2))
        path = _match_cited_path(cited, index)
        entries = renumber.get(path or "", [])
        for entry in entries:
            if entry["start_old"] <= number <= entry["end_old"]:
                return f"{cited}:{entry['start_new'] + (number - entry['start_old'])}"
        return match.group(0)

    return CITE_LINE.sub(replace, text)


def cmd_carry(args: argparse.Namespace) -> int:
    parent_dir = Path(args.parent_run)
    run_dir = Path(args.run_dir)
    changes = _read_json(run_dir / "changes.json")
    if changes is None:
        print("carry: no changes.json in the run directory; run `diff` first", file=sys.stderr)
        return 2

    knowledge = parent_dir / "knowledge"
    if knowledge.is_dir():
        shutil.copytree(knowledge, run_dir / "knowledge", dirs_exist_ok=True)

    renumber = changes.get("renumber", {})
    index = _path_index(
        set(renumber)
        | set(changes["files"]["modified"])
        | set(changes["files"]["added"])
        | set(changes["files"]["removed"])
    )
    by_file: dict[str, dict[int, dict]] = {}
    for claim in changes.get("claims", []):
        by_file.setdefault(claim["phase_file"], {})[claim["line"]] = claim

    copied = 0
    marked = 0
    for name in PHASE_FILES:
        source = parent_dir / name
        if not source.exists() or name == "07-final-report.md":
            continue  # Phase 7 is regenerated, never carried.
        marks = by_file.get(name, {})
        out_lines: list[str] = []
        # A carried claim must survive byte for byte, so the source is read
        # raw here rather than through read_text: that helper deliberately
        # normalizes CRLF and CR to LF for the hashing and diff paths it was
        # written for, which would silently rewrite a CRLF parent phase file
        # to LF. Splitting and joining on "\n" alone, with no newline style
        # detected or re-normalized, keeps each line's own trailing "\r" (if
        # it has one) attached to it, so mixed line endings survive too.
        raw = source.read_bytes().decode("utf-8", errors="replace")
        for number, line in enumerate(raw.split("\n"), start=1):
            claim = marks.get(number)
            if claim:
                cites = " ".join(claim["cites"])
                # The inserted marker takes the same line ending as the claim
                # line it sits above, so it does not break that file's style.
                ending = "\r" if line.endswith("\r") else ""
                out_lines.append(f"{MARKER_PREFIX} reason={claim['reason']} cites={cites} -->{ending}")
                out_lines.append(line)
                marked += 1
            else:
                out_lines.append(renumber_line(line, renumber, index))
        # newline="" so Python writes "\n" literally instead of translating
        # it to the platform's line separator, the other half of preserving
        # whatever ending style each line already carries.
        with (run_dir / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join(out_lines))
        copied += 1

    added = changes.get("symbols", {}).get("added", [])
    if added:
        with (run_dir / "changes.md").open("a", encoding="utf-8") as handle:
            handle.write("\n## Added symbols\n\n")
            handle.write("No claim cites these yet. Phases 01 and 02 always; 03 to 06 at full depth.\n\n")
            handle.write("| Symbol | File | Kind |\n|---|---|---|\n")
            for item in added:
                handle.write(f"| `{item['symbol']}` | `{item['file']}` | {item['kind']} |\n")

    print(f"carry: {copied} phase files copied, {marked} claims marked stale, {len(added)} symbols added")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """
    The publication gate for an incremental run: no claim may still be marked
    stale, and every symbol the change set added must be cited somewhere.

    "Cited" means a phase file names it through the same `path::symbol` form
    every other citation in this file is matched by, on a line that is not
    itself a stale marker: a marker's own `cites=` field is written in that
    same shape, so it must be excluded before matching, or a claim's own
    unresolved marker would count as the documentation that resolves it. The
    citation must also resolve to the SAME file the symbol was added in, not
    merely carry the same bare name: two files can each define a `handler`,
    and a citation of one must never document an addition to the other. The
    path index is built from the added symbols' own files only, so a
    citation of an unrelated file never even attempts to resolve.
    """
    run_dir = Path(args.run_dir)
    changes = _read_json(run_dir / "changes.json")
    if changes is None:
        print("check: no changes.json in the run directory; run `diff` first", file=sys.stderr)
        return 2

    added = changes.get("symbols", {}).get("added", [])
    index = _path_index({item["file"] for item in added})

    problems: list[str] = []
    documented: set[tuple[str, str]] = set()
    for name in PHASE_FILES:
        path = run_dir / name
        if not path.exists():
            continue
        for number, line in enumerate(read_text(path).split("\n"), start=1):
            if line.startswith(MARKER_PREFIX):
                problems.append(f"{name}:{number}: claim still marked stale: {line.strip()}")
                continue
            for path_text, symbol in CITE_SYMBOL.findall(line):
                resolved = _match_cited_path(path_text, index)
                if resolved:
                    documented.add((resolved, symbol))

    for item in added:
        if (item["file"], item["symbol"]) not in documented:
            problems.append(
                f"added symbol never documented: {item['file']}::{item['symbol']}"
            )

    if problems:
        print("check: FAILED")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("check: clean")
    return 0


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

    diff_parser = sub.add_parser("diff", help="diff a parent run's snapshot against the worktree")
    diff_parser.add_argument("parent_run")
    diff_parser.add_argument("target")
    diff_parser.add_argument("--out", required=True)
    diff_parser.add_argument("--verify", action="store_true", help="hash every file, ignoring size and mtime")
    diff_parser.add_argument("--threshold", type=float, default=0.4)
    diff_parser.add_argument("--flags", default=None, help="this run's flags as JSON, compared with the parent's")
    diff_parser.set_defaults(func=cmd_diff)

    carry_parser = sub.add_parser("carry", help="copy a parent run's phase files and mark the stale claims")
    carry_parser.add_argument("parent_run")
    carry_parser.add_argument("run_dir")
    carry_parser.set_defaults(func=cmd_carry)

    check_parser = sub.add_parser("check", help="verify an incremental run before publishing")
    check_parser.add_argument("run_dir")
    check_parser.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
