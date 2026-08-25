"""
Language adapter dispatch for Deep Dive Analysis.

Maps file extensions to language adapters that implement the LanguageAdapter
protocol. Each adapter provides structural extraction (classes, functions,
imports, external calls) and comment syntax info.

Supported languages:
    Python, Java, JavaScript, TypeScript (incl. TSX/JSX), SQL, PL/SQL.

Tree-sitter is used when available via the optional `tree-sitter-language-pack`
package, with regex-based fallback per language. Python uses the stdlib `ast`
module so it works without any external dependency.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import (
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    LanguageAdapter,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken

__all__ = [
    "LanguageAdapter",
    "ParameterInfo",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "ExternalCallInfo",
    "ParseResult",
    "CommentToken",
    "Language",
    "detect_language",
    "get_adapter",
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_LANGUAGES",
]


# Canonical language identifiers used internally.
class Language:
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SQL = "sql"
    PLSQL = "plsql"
    RUST = "rust"


SUPPORTED_LANGUAGES: tuple[str, ...] = (
    Language.PYTHON,
    Language.JAVA,
    Language.JAVASCRIPT,
    Language.TYPESCRIPT,
    Language.SQL,
    Language.PLSQL,
    Language.RUST,
)


# File extension to language map. PL/SQL detection also looks at content
# (see detect_language) because .sql is ambiguous between SQL and PL/SQL.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".java": Language.JAVA,
    ".js": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".mts": Language.TYPESCRIPT,
    ".cts": Language.TYPESCRIPT,
    ".sql": Language.SQL,
    ".ddl": Language.SQL,
    ".dml": Language.SQL,
    # PL/SQL specific extensions (Oracle).
    ".pks": Language.PLSQL,  # Package spec
    ".pkb": Language.PLSQL,  # Package body
    ".plsql": Language.PLSQL,
    ".pls": Language.PLSQL,
    ".pck": Language.PLSQL,
    ".prc": Language.PLSQL,  # Procedure
    ".fnc": Language.PLSQL,  # Function
    ".trg": Language.PLSQL,  # Trigger
    # Rust.
    ".rs": Language.RUST,
}


# Oracle-specific markers. We intentionally do NOT match generic "begin",
# "exception", "create or replace function" - PostgreSQL plpgsql uses those
# too. PL/SQL is only detected when the source uses Oracle-specific syntax.
#
# `%TYPE` and `%ROWTYPE` use a word-boundary regex so a SQL `LIKE '%type%'`
# pattern (common in pg_catalog queries) does NOT false-route to PL/SQL.
_PLSQL_LITERAL_MARKERS = (
    "create or replace package",
    "create or replace type body",
    "dbms_output",
    "utl_file",
    "utl_http",
    "bfilename",
    "extproc",
    "pragma autonomous",
    "pragma serially_reusable",
    "pragma exception_init",
    "pragma restrict_references",
)
_PLSQL_ROWTYPE_RE = re.compile(r"\w%(?:rowtype|type)\b", re.IGNORECASE)


def detect_language(file_path: Path, content: str | None = None) -> str | None:
    """
    Detect the language of a file by extension. For ambiguous .sql files,
    inspect content for PL/SQL-specific markers.

    Returns the canonical language identifier or None if unsupported.
    """
    suffix = file_path.suffix.lower()
    lang = SUPPORTED_EXTENSIONS.get(suffix)

    # Disambiguate .sql vs PL/SQL by content if provided.
    if lang == Language.SQL and content is not None:
        lowered = content.lower()
        if any(marker in lowered for marker in _PLSQL_LITERAL_MARKERS):
            return Language.PLSQL
        if _PLSQL_ROWTYPE_RE.search(content):
            return Language.PLSQL

    return lang


def get_adapter(language: str) -> LanguageAdapter:
    """
    Return the adapter for a given canonical language identifier.

    The argument is case-insensitive ("Python", "PYTHON", "python" all work).

    Raises ValueError if the language is not supported. Imports are lazy so
    that missing optional dependencies (tree-sitter) only fail when actually
    needed. Adapter modules MUST NOT do fallible work at import time -- if a
    future adapter's `__init__` raises, the resulting ImportError surfaces
    here instead of the documented ValueError.
    """
    language = language.lower()
    if language == Language.PYTHON:
        from . import python as _mod
        return _mod.adapter
    if language == Language.JAVA:
        from . import java as _mod
        return _mod.adapter
    if language == Language.JAVASCRIPT:
        from . import javascript as _mod
        return _mod.adapter
    if language == Language.TYPESCRIPT:
        from . import typescript as _mod
        return _mod.adapter
    if language == Language.SQL:
        from . import sql as _mod
        return _mod.adapter
    if language == Language.PLSQL:
        from . import plsql as _mod
        return _mod.adapter
    if language == Language.RUST:
        from . import rust as _mod
        return _mod.adapter
    raise ValueError(f"Unsupported language: {language!r}")
