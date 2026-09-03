"""
PL/SQL adapter (Oracle).

Builds on the SQL adapter for DDL and adds PL/SQL-specific extraction:

- PACKAGE / PACKAGE BODY      -> classes (kind="package" / "package-body")
- TYPE BODY                    -> classes (kind="type-body")
- TRIGGER                      -> classes (kind="trigger")
- Standalone PROCEDURE / FUNCTION (within package or top-level)
- Cursor declarations         -> class_variables on the enclosing package
- Exception declarations      -> class_variables on the enclosing package

PL/SQL has no real "imports", but `%TYPE` and `%ROWTYPE` references identify
implicit type dependencies; we surface them as imports for the dependency
counter to work.
"""

from __future__ import annotations

import re

from .base import (
    ClassInfo,
    FunctionInfo,
    ImportInfo,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken, extract_sql_comments
from . import sql as _sql

__all__ = ["adapter"]

_LANGUAGE_NAME = "plsql"


_PACKAGE_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+(?:EDITIONABLE\s+|NONEDITIONABLE\s+)?PACKAGE(?:\s+BODY)?\s+(?P<schema>\w+\.)?(?P<name>\w+)\b",
    re.IGNORECASE,
)
_TYPE_BODY_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+TYPE\s+BODY\s+(?P<name>\w+)",
    re.IGNORECASE,
)
_INNER_PROCEDURE_RE = re.compile(
    r"^\s*PROCEDURE\s+(?P<name>\w+)\s*(?:\((?P<params>[^)]*)\))?",
    re.IGNORECASE | re.MULTILINE,
)
_INNER_FUNCTION_RE = re.compile(
    r"^\s*FUNCTION\s+(?P<name>\w+)\s*(?:\((?P<params>[^)]*)\))?\s+RETURN\s+(?P<ret>[\w%.]+)",
    re.IGNORECASE | re.MULTILINE,
)
_CURSOR_RE = re.compile(
    r"^\s*CURSOR\s+(?P<name>\w+)\s+(?:\([^)]*\)\s+)?IS\b",
    re.IGNORECASE | re.MULTILINE,
)
_EXCEPTION_RE = re.compile(
    r"^\s*(?P<name>\w+)\s+EXCEPTION\s*;",
    re.IGNORECASE | re.MULTILINE,
)
_ROWTYPE_RE = re.compile(
    r"\b(?P<schema>\w+\.)?(?P<obj>\w+)%(?:ROWTYPE|TYPE)\b",
    re.IGNORECASE,
)
_CONSTANT_RE = re.compile(
    r"^\s*(?P<name>[A-Z][A-Z0-9_]*)\s+CONSTANT\s+",
    re.MULTILINE,
)


def _line_no(content: str, idx: int) -> int:
    return content[:idx].count("\n") + 1


def _parse_params(raw: str) -> list[ParameterInfo]:
    """Same shape as SQL parameter parsing; PL/SQL adds IN/OUT/IN OUT modes."""
    return _sql._parse_params(raw)


def _parse(content: str) -> ParseResult:
    # Start with SQL extraction so tables/views/sequences are captured too.
    result = _sql._parse(content, language=_LANGUAGE_NAME)
    result.notes = ["parser=regex (plsql)"]

    # Packages and package bodies.
    seen_packages: dict[str, ClassInfo] = {}
    for m in _PACKAGE_RE.finditer(content):
        is_body = bool(re.search(r"PACKAGE\s+BODY", m.group(0), re.IGNORECASE))
        name = m.group("name")
        cls = ClassInfo(
            name=name,
            kind="package-body" if is_body else "package",
            line_number=_line_no(content, m.start()),
        )
        result.classes.append(cls)
        if name not in seen_packages:
            seen_packages[name] = cls
        result.exported_symbols.append(name)

    # Type bodies.
    for m in _TYPE_BODY_RE.finditer(content):
        name = m.group("name")
        result.classes.append(
            ClassInfo(
                name=name,
                kind="type-body",
                line_number=_line_no(content, m.start()),
            )
        )
        result.exported_symbols.append(name)

    # Inner procedures and functions (top-level scan; we don't track exact
    # owning package boundaries - that would require a real parser).
    for m in _INNER_PROCEDURE_RE.finditer(content):
        # Skip if this line is part of a CREATE OR REPLACE PROCEDURE - those
        # are already captured by the SQL adapter.
        line_start = content.rfind("\n", 0, m.start()) + 1
        prefix = content[line_start : m.start()].lstrip()
        if prefix.upper().startswith(("CREATE", "DECLARE")):
            continue
        fn = FunctionInfo(
            name=m.group("name"),
            parameters=_parse_params(m.group("params") or ""),
            visibility="procedure",
            line_number=_line_no(content, m.start()),
        )
        result.functions.append(fn)
        result.exported_symbols.append(m.group("name"))
    for m in _INNER_FUNCTION_RE.finditer(content):
        fn = FunctionInfo(
            name=m.group("name"),
            parameters=_parse_params(m.group("params") or ""),
            return_annotation=m.group("ret"),
            line_number=_line_no(content, m.start()),
        )
        result.functions.append(fn)
        result.exported_symbols.append(m.group("name"))

    # Cursor and exception declarations - attach as class_variables to the
    # last package seen (best-effort grouping).
    last_package = next(iter(seen_packages.values())) if seen_packages else None
    if last_package is not None:
        for m in _CURSOR_RE.finditer(content):
            last_package.class_variables.append(f"CURSOR {m.group('name')}")
        for m in _EXCEPTION_RE.finditer(content):
            last_package.class_variables.append(f"EXCEPTION {m.group('name')}")

    # Constants.
    for m in _CONSTANT_RE.finditer(content):
        result.constants.append(m.group("name"))

    # Implicit type imports (%TYPE / %ROWTYPE references).
    seen_imports: set[str] = {imp.module for imp in result.imports}
    for m in _ROWTYPE_RE.finditer(content):
        schema = m.group("schema") or ""
        obj = m.group("obj")
        module = f"{schema}{obj}".strip(".")
        if module and module not in seen_imports:
            seen_imports.add(module)
            result.imports.append(
                ImportInfo(
                    module=module,
                    names=[obj],
                    is_from_import=False,
                    is_internal=True,
                )
            )

    result.exported_symbols = list(dict.fromkeys(result.exported_symbols))
    return result


class _PlSqlAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        result = _parse(content)
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        # Distinct %TYPE/%ROWTYPE references plus any standard SQL imports.
        # Dedup the rowtype matches so 6 cursors all referencing `users%ROWTYPE`
        # count as 1, not 6 -- otherwise the classifier crosses HIGH_DEPS_THRESHOLD
        # spuriously for small PL/SQL packages.
        unique_rowtypes = {m.group(0).lower() for m in _ROWTYPE_RE.finditer(content)}
        return len(unique_rowtypes) + _sql.adapter.count_imports(content)

    def strip_comments_and_blanks(self, content: str) -> int:
        return _sql.adapter.strip_comments_and_blanks(content)

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_sql_comments(content)


adapter = _PlSqlAdapter()
