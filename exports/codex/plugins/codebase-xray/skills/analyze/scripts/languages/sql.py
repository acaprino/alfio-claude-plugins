"""
SQL adapter (ANSI / vendor-neutral DDL/DML).

Regex-based extraction. Treats top-level DDL as the "class/function" surface:

- CREATE TABLE / VIEW / MATERIALIZED VIEW -> kind="table"|"view"
- CREATE INDEX / SEQUENCE / TYPE          -> kind="index"|"sequence"|"type"
- CREATE FUNCTION / PROCEDURE / TRIGGER    -> functions list

Imports are captured from `IMPORT FOREIGN SCHEMA`, `\\i ...` (psql include),
`@@` (SQL*Plus include) where present. Most SQL has no import equivalent.
"""

from __future__ import annotations

import re

from .base import (
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken, extract_sql_comments

__all__ = ["adapter"]

_LANGUAGE_NAME = "sql"


_CREATE_TABLE_RE = re.compile(
    r"\bCREATE\s+(?:GLOBAL\s+TEMPORARY\s+|TEMPORARY\s+|TEMP\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w.\"\[\]`]+)",
    re.IGNORECASE,
)
_CREATE_VIEW_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+(?:MATERIALIZED\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w.\"\[\]`]+)",
    re.IGNORECASE,
)
_CREATE_INDEX_RE = re.compile(
    r"\bCREATE(?:\s+UNIQUE)?\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w.\"\[\]`]+)\s+ON\s+(?P<table>[\w.\"\[\]`]+)",
    re.IGNORECASE,
)
_CREATE_SEQUENCE_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+SEQUENCE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w.\"\[\]`]+)",
    re.IGNORECASE,
)
_CREATE_TYPE_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+TYPE\s+(?P<name>[\w.\"\[\]`]+)",
    re.IGNORECASE,
)
_CREATE_SCHEMA_RE = re.compile(
    r"\bCREATE\s+SCHEMA\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w.\"\[\]`]+)",
    re.IGNORECASE,
)
_CREATE_FUNCTION_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+FUNCTION\s+(?P<name>[\w.\"\[\]`]+)\s*\((?P<params>[^)]*)\)",
    re.IGNORECASE,
)
_CREATE_PROCEDURE_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+PROCEDURE\s+(?P<name>[\w.\"\[\]`]+)\s*\((?P<params>[^)]*)\)",
    re.IGNORECASE,
)
_CREATE_TRIGGER_RE = re.compile(
    r"\bCREATE(?:\s+OR\s+REPLACE)?\s+TRIGGER\s+(?P<name>[\w.\"\[\]`]+)",
    re.IGNORECASE,
)
_IMPORT_RE = re.compile(
    r"^\s*(?:IMPORT\s+FOREIGN\s+SCHEMA\s+(?P<schema>\w+)|\\i\s+(?P<psql>\S+)|@@\s*(?P<sqlplus>\S+))",
    re.IGNORECASE | re.MULTILINE,
)


def _line_no(content: str, idx: int) -> int:
    return content[:idx].count("\n") + 1


def _parse_params(raw: str) -> list[ParameterInfo]:
    """
    Best-effort split of SQL function/procedure parameters.

    Handles "name TYPE", "name IN TYPE", "name OUT TYPE", "name IN OUT TYPE".
    Splits at top-level commas only.
    """
    params: list[ParameterInfo] = []
    if not raw or not raw.strip():
        return params
    # Split at commas not inside parens (e.g. NUMERIC(10,2)).
    depth = 0
    buf = []
    pieces: list[str] = []
    for ch in raw:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            pieces.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        pieces.append("".join(buf).strip())
    for piece in pieces:
        if not piece:
            continue
        tokens = piece.split()
        if not tokens:
            continue
        name = tokens[0]
        ann = " ".join(tokens[1:]) if len(tokens) > 1 else None
        params.append(ParameterInfo(name=name, annotation=ann))
    return params


def _scan_external_calls(content: str) -> list[ExternalCallInfo]:
    """
    SQL doesn't make typical 'external calls' - the whole file IS one.
    We still note INSERT/UPDATE/DELETE/CALL/EXEC as 'database' for consistency
    with the other adapters, and dblink/UTL_HTTP/UTL_FILE etc. when present.
    """
    out: list[ExternalCallInfo] = []
    DB_OPS = re.compile(
        r"\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|MERGE|CALL|EXEC(?:UTE)?)\b",
        re.IGNORECASE,
    )
    NET_OPS = re.compile(
        r"\b(?:dblink|UTL_HTTP|HTTPURITYPE|XMLHTTP|UTL_TCP|UTL_SMTP|UTL_INADDR)\b",
        re.IGNORECASE,
    )
    FS_OPS = re.compile(
        r"\b(?:UTL_FILE|DBMS_LOB|BFILENAME|LOAD\s+DATA|COPY\s+FROM)\b",
        re.IGNORECASE,
    )
    MSG_OPS = re.compile(
        r"\b(?:DBMS_AQ|DBMS_AQADM|UTL_MAIL|DBMS_PIPE|DBMS_ALERT)\b",
        re.IGNORECASE,
    )
    IPC_OPS = re.compile(
        r"\b(?:DBMS_SCHEDULER|DBMS_JOB|EXTPROC|DBMS_PIPE)\b",
        re.IGNORECASE,
    )
    for i, line in enumerate(content.splitlines(), start=1):
        ctx = line.strip()[:100]
        if DB_OPS.search(line):
            out.append(ExternalCallInfo("database", "sql-dml", i, ctx))
        if NET_OPS.search(line):
            out.append(ExternalCallInfo("network", "net-api", i, ctx))
        if FS_OPS.search(line):
            out.append(ExternalCallInfo("filesystem", "fs-api", i, ctx))
        if MSG_OPS.search(line):
            out.append(ExternalCallInfo("messaging", "msg-api", i, ctx))
        if IPC_OPS.search(line):
            out.append(ExternalCallInfo("ipc", "ipc-api", i, ctx))
    return out


def _parse(content: str, language: str = _LANGUAGE_NAME) -> ParseResult:
    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def add_ddl(matches, kind: str) -> None:
        for m in matches:
            name = m.group("name").strip().strip('"`[]')
            classes.append(
                ClassInfo(
                    name=name,
                    kind=kind,
                    line_number=_line_no(content, m.start()),
                )
            )
            exported.append(name)

    add_ddl(_CREATE_TABLE_RE.finditer(content), "table")
    add_ddl(_CREATE_VIEW_RE.finditer(content), "view")
    add_ddl(_CREATE_INDEX_RE.finditer(content), "index")
    add_ddl(_CREATE_SEQUENCE_RE.finditer(content), "sequence")
    add_ddl(_CREATE_TYPE_RE.finditer(content), "type")
    add_ddl(_CREATE_SCHEMA_RE.finditer(content), "schema")
    add_ddl(_CREATE_TRIGGER_RE.finditer(content), "trigger")

    for m in _CREATE_FUNCTION_RE.finditer(content):
        name = m.group("name").strip().strip('"`[]')
        params = _parse_params(m.group("params") or "")
        functions.append(
            FunctionInfo(
                name=name,
                parameters=params,
                line_number=_line_no(content, m.start()),
            )
        )
        exported.append(name)
    for m in _CREATE_PROCEDURE_RE.finditer(content):
        name = m.group("name").strip().strip('"`[]')
        params = _parse_params(m.group("params") or "")
        fn = FunctionInfo(
            name=name,
            parameters=params,
            line_number=_line_no(content, m.start()),
        )
        # Use visibility to mark as procedure for downstream reporting.
        fn.visibility = "procedure"
        functions.append(fn)
        exported.append(name)

    for m in _IMPORT_RE.finditer(content):
        if m.group("schema"):
            imports.append(
                ImportInfo(
                    module=m.group("schema"),
                    names=[m.group("schema")],
                    is_from_import=False,
                    is_internal=True,
                )
            )
        elif m.group("psql"):
            imports.append(
                ImportInfo(
                    module=m.group("psql"),
                    names=[m.group("psql")],
                    is_from_import=False,
                    is_internal=True,
                )
            )
        elif m.group("sqlplus"):
            imports.append(
                ImportInfo(
                    module=m.group("sqlplus"),
                    names=[m.group("sqlplus")],
                    is_from_import=False,
                    is_internal=True,
                )
            )

    return ParseResult(
        file_path="",
        language=language,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=_scan_external_calls(content),
        exported_symbols=list(dict.fromkeys(exported)),
        notes=["parser=regex (sql)"],
    )


class _SqlAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        result = _parse(content, self.language)
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        return len(_IMPORT_RE.findall(content))

    def strip_comments_and_blanks(self, content: str) -> int:
        no_blocks = re.sub(r"/\*[\s\S]*?\*/", "", content)
        code = 0
        for line in no_blocks.split("\n"):
            s = line.strip()
            if not s:
                continue
            if s.startswith("--"):
                continue
            code += 1
        return code

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_sql_comments(content)


adapter = _SqlAdapter()
