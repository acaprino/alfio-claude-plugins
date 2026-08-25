"""
Usage Finder Module.

Finds where symbols are used across the codebase. Multi-language:
- Source file types: .py, .java, .js/.mjs/.cjs/.jsx, .ts/.tsx, .rs,
  .sql/.ddl/.dml, PL/SQL extensions (.pks, .pkb, .plsql, .pls, .pck, .prc,
  .fnc, .trg).
- Import patterns are language-aware (Python `import`/`from`, Java `import`,
  JS/TS `import`/`require`; Rust and SQL/PL-SQL have no import pattern, so
  only raw usages are reported for them).
- Inheritance / call detection uses language-agnostic heuristics that work
  reasonably across the targeted set.

Uses ripgrep when available, then grep, then a pure-Python rglob fallback.
"""

from __future__ import annotations

import functools
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "UsageLocation",
    "UsageResult",
    "find_usages_with_grep",
    "find_importing_modules",
    "find_all_usages",
    "is_excluded",
    "SOURCE_EXTENSIONS",
]

# Constants
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
SUBPROCESS_TIMEOUT_SECONDS: int = 30

logger = logging.getLogger(__name__)


# Single source of truth for the languages package; no longer maintained
# separately here. Re-exported so callers that imported it from this module
# keep working.
from languages import SUPPORTED_EXTENSIONS as _SUPPORTED_EXTENSIONS_MAP

SOURCE_EXTENSIONS: tuple[str, ...] = tuple(_SUPPORTED_EXTENSIONS_MAP.keys())

DEFAULT_EXCLUDES = (
    "__pycache__",
    ".venv", "venv", ".tox",
    ".git",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "target", "build", "dist", "out",
    "*.pyc", "*.class",
)

# `C:\...` / `c:/...`. Used to keep a Windows drive letter attached to its path
# when splitting `path:line:content` output from grep and ripgrep.
_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:[\\/]")


def is_excluded(path: Path, patterns: tuple[str, ...] | list[str]) -> bool:
    """
    Match exclude patterns against whole path segments, not substrings.

    A bare pattern ("out", "build") excludes a path only when it is one of the
    directory or file names, so `src/checkout.py`, `app/layout.ts`, and
    `docs/about/` survive. A leading-`*` pattern ("*.pyc") matches the file
    name's suffix.
    """
    parts = path.parts
    for pattern in patterns:
        if pattern.startswith("*"):
            if path.name.endswith(pattern[1:]):
                return True
        elif pattern in parts:
            return True
    return False


def validate_symbol(symbol: str) -> str:
    """
    Accept identifiers that are valid across the supported languages.

    Python/Java/JS/TS identifiers are `[A-Za-z_][A-Za-z0-9_]*` with optional
    dotted qualifiers; SQL allows dotted (schema.table) and quoted names but
    we restrict here to unquoted identifiers for safety.
    """
    if not re.match(r"^[A-Za-z_$][A-Za-z0-9_.$]*$", symbol):
        raise ValueError(
            f"Invalid symbol name: {symbol!r}. Must be a valid identifier."
        )
    return symbol


@dataclass
class UsageLocation:
    file_path: str
    line_number: int
    line_content: str
    usage_type: str  # "import", "call", "inheritance", "reference"


@dataclass
class UsageResult:
    symbol: str
    source_file: str
    usages: list[UsageLocation]
    importing_modules: list[str]


def _classify_usage(line: str, symbol: str) -> str:
    stripped = line.strip()
    # Imports (Python, Java, JS/TS).
    if stripped.startswith(("from ", "import ", "@import ")) or " import " in stripped[:20]:
        return "import"
    if re.match(r"^\s*(?:const|let|var)\s+\w[\w{}\s,]*=\s*require\(", stripped):
        return "import"
    # Inheritance: class X extends Y, class X(Y), interface I extends J.
    if re.search(
        rf"\b(?:class|interface)\s+\w+(?:\s*<[^>]*>)?\s*"
        rf"(?:extends|implements|\()\s*[^{{(]*{re.escape(symbol)}",
        stripped,
    ):
        return "inheritance"
    # Function call: SYMBOL(.
    if re.search(rf"\b{re.escape(symbol)}\s*\(", stripped):
        return "call"
    return "reference"


def _ripgrep_globs() -> list[str]:
    globs: list[str] = []
    for ext in SOURCE_EXTENSIONS:
        globs.extend(["--glob", f"*{ext}"])
    for pattern in DEFAULT_EXCLUDES:
        globs.extend(["--glob", f"!{pattern}"])
    return globs


def _grep_includes() -> list[str]:
    return [f"--include=*{ext}" for ext in SOURCE_EXTENSIONS]


def find_usages_with_grep(
    symbol: str,
    search_paths: list[Path],
    exclude_patterns: list[str] | None = None,
) -> list[UsageLocation]:
    """
    Find usages of a symbol using ripgrep, falling back to grep, then to a
    pure-Python search.
    """
    symbol = validate_symbol(symbol)
    excludes = list(exclude_patterns or DEFAULT_EXCLUDES)
    usages: list[UsageLocation] = []

    for search_path in search_paths:
        if not search_path.exists():
            continue

        # 1. ripgrep.
        try:
            cmd = ["rg", "-n", "--hidden", "--no-ignore-vcs"]
            cmd.extend(_ripgrep_globs())
            for pat in excludes:
                cmd.extend(["--glob", f"!{pat}"])
            cmd.append(symbol)
            cmd.append(str(search_path))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )
            if result.returncode in (0, 1):  # 1 = no match, not an error
                _absorb_grep_lines(result.stdout, usages, symbol)
                continue
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 2. grep.
        try:
            cmd = ["grep", "-rn"] + _grep_includes() + [symbol, str(search_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )
            if result.returncode in (0, 1):
                _absorb_grep_lines(result.stdout, usages, symbol)
                continue
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 3. Pure-Python fallback.
        usages.extend(_python_based_search(symbol, search_path, excludes))

    return usages


def _split_grep_line(line: str) -> tuple[str, str, str] | None:
    """
    Split one `path:line:content` record from grep/ripgrep output.

    A Windows absolute path starts with its own colon (`C:\\src\\a.py`), so the
    drive prefix is held back before splitting; otherwise every absolute-path
    search parses the drive letter as the file name and the rest as a line
    number, and silently yields zero results.
    """
    drive = ""
    if _DRIVE_PREFIX_RE.match(line):
        drive, line = line[:2], line[2:]
    parts = line.split(":", 2)
    if len(parts) < 3:
        return None
    return drive + parts[0], parts[1], parts[2]


def _absorb_grep_lines(stdout: str, sink: list[UsageLocation], symbol: str) -> None:
    if not stdout:
        return
    for line in stdout.strip().split("\n"):
        if not line:
            continue
        parsed = _split_grep_line(line.rstrip("\r"))
        if parsed is None:
            continue
        file_path, line_no, raw_content = parsed
        try:
            line_num = int(line_no)
        except ValueError:
            continue
        content = raw_content.strip()
        sink.append(
            UsageLocation(
                file_path=file_path,
                line_number=line_num,
                line_content=content,
                usage_type=_classify_usage(content, symbol),
            )
        )


def _python_based_search(
    symbol: str,
    search_path: Path,
    exclude_patterns: list[str],
) -> list[UsageLocation]:
    out: list[UsageLocation] = []

    for src in search_path.rglob("*"):
        if not src.is_file():
            continue
        if src.suffix not in SOURCE_EXTENSIONS:
            continue
        if is_excluded(src, exclude_patterns):
            continue
        try:
            if src.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
            content = src.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_num, line in enumerate(content.split("\n"), start=1):
            if symbol in line:
                out.append(
                    UsageLocation(
                        file_path=str(src),
                        line_number=line_num,
                        line_content=line.strip(),
                        usage_type=_classify_usage(line, symbol),
                    )
                )
    return out


def find_importing_modules(
    symbol: str,
    source_module: str,
    search_paths: list[Path],
) -> list[str]:
    """
    Find files that import a specific symbol. Recognizes:

    - Python:     `from <mod> import ... <symbol> ...`, `import <mod>`
    - Java:       `import <mod>.<symbol>`, `import static <mod>.<symbol>`
    - JS / TS:    `import { <symbol> } from '<mod>'`, `import <symbol> from '<mod>'`,
                  `const { <symbol> } = require('<mod>')`
    """
    importing: list[str] = []
    seen: set[str] = set()

    py_patterns = [
        rf"from\s+{re.escape(source_module)}\s+import\s+.*\b{re.escape(symbol)}\b",
        rf"from\s+{re.escape(source_module)}\s+import\s+\*",
        rf"\bimport\s+{re.escape(source_module)}\b",
    ]
    java_patterns = [
        rf"\bimport\s+(?:static\s+)?{re.escape(source_module)}\.{re.escape(symbol)}\b",
        rf"\bimport\s+(?:static\s+)?{re.escape(source_module)}\.\*",
    ]
    js_patterns = [
        rf"\bimport\b[^;]*\b{re.escape(symbol)}\b[^;]*from\s+['\"]{re.escape(source_module)}['\"]",
        rf"\brequire\(['\"]{re.escape(source_module)}['\"]\)",
    ]
    all_patterns = py_patterns + java_patterns + js_patterns

    for search_path in search_paths:
        if not search_path.exists():
            continue
        for src in search_path.rglob("*"):
            if not src.is_file() or src.suffix not in SOURCE_EXTENSIONS:
                continue
            path_str = str(src)
            if is_excluded(src, DEFAULT_EXCLUDES):
                continue
            try:
                if src.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue
                content = src.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern in all_patterns:
                if re.search(pattern, content):
                    rel = str(src.relative_to(search_path.parent)) if search_path.parent else path_str
                    module = rel.replace("\\", "/")
                    if module not in seen:
                        seen.add(module)
                        importing.append(module)
                    break
    return importing


@functools.lru_cache(maxsize=4096)
def _resolved(path_str: str) -> str:
    """Resolved, case-normalized path string. Cached: called per usage hit."""
    try:
        resolved = Path(path_str).resolve()
    except OSError:
        resolved = Path(path_str).absolute()
    return os.path.normcase(str(resolved))


def _is_same_file(candidate: str, source_file: Path) -> bool:
    return _resolved(candidate) == _resolved(str(source_file))


def find_all_usages(
    symbol: str,
    source_file: Path,
    project_root: Path | None = None,
) -> UsageResult:
    """Find all usages of a symbol from a source file in the project."""
    if project_root is None:
        current = source_file.parent
        while current != current.parent:
            if (
                (current / "pyproject.toml").exists()
                or (current / "package.json").exists()
                or (current / "pom.xml").exists()
                or (current / "build.gradle").exists()
                or (current / "build.gradle.kts").exists()
                or (current / ".git").exists()
            ):
                project_root = current
                break
            current = current.parent
        if project_root is None:
            project_root = source_file.parent

    search_paths: list[Path] = []
    for dir_name in ("src", "lib", "app", "packages", "modules", "core", "common"):
        candidate = project_root / dir_name
        if candidate.exists():
            search_paths.append(candidate)
    if not search_paths:
        search_paths = [project_root]

    usages = find_usages_with_grep(symbol, search_paths)

    # Filter out the source file itself. Compare resolved paths: a basename
    # match would drop every other file sharing the name (all __init__.py,
    # every index.ts) from the results.
    usages = [u for u in usages if not _is_same_file(u.file_path, source_file)]

    # Compute source module for import searching.
    try:
        rel_path = source_file.relative_to(project_root)
        # Python style: a.b.c (no extension).
        source_module = str(rel_path).replace("\\", ".").replace("/", ".")
        if "." in source_file.name:
            source_module = source_module[: source_module.rfind(".")]
    except ValueError:
        source_module = source_file.stem

    importing = find_importing_modules(symbol, source_module, search_paths)

    return UsageResult(
        symbol=symbol,
        source_file=str(source_file),
        usages=usages,
        importing_modules=importing,
    )


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python usage_finder.py <symbol> [source_file]")
        sys.exit(1)

    symbol = sys.argv[1]
    source_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    project_root = Path(".")
    result = find_all_usages(symbol, source_file, project_root)

    output = {
        "symbol": result.symbol,
        "source_file": result.source_file,
        "usage_count": len(result.usages),
        "usages": [
            {
                "file": u.file_path,
                "line": u.line_number,
                "type": u.usage_type,
                "content": u.line_content[:100],
            }
            for u in result.usages[:20]
        ],
        "importing_modules": result.importing_modules,
    }
    print(json.dumps(output, indent=2))
