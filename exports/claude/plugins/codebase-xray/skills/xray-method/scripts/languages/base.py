"""
Shared dataclasses and the LanguageAdapter protocol.

The dataclasses are the stable contract returned by every language adapter,
so analyze_file.py and downstream consumers do not branch on language. Some
fields are language-specific (decorators apply to Python/JS/TS, annotations
to Python/Java/TS); they remain optional strings so the shape stays uniform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Literal, Protocol, runtime_checkable

__all__ = [
    "ParameterInfo",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "ExternalCallInfo",
    "ParseResult",
    "LanguageAdapter",
    "CallType",
    "Visibility",
    "Kind",
]


# Categories of external system calls. The "other" entry is a future-proofing
# fallback; no adapter currently emits it.
CallType = Literal["database", "network", "filesystem", "messaging", "ipc", "other"]

# Function/class visibility modifiers across the supported languages, plus the
# SQL/PL-SQL marker that distinguishes a stored procedure from a function.
Visibility = Literal["public", "private", "protected", "procedure"]

# All ClassInfo.kind values emitted across the supported languages. Includes
# OO kinds (class/interface/enum/record/annotation), TS-only "type-alias",
# SQL DDL kinds (table/view/index/sequence/type/schema/trigger), and PL/SQL
# container kinds (package/package-body/type-body).
Kind = Literal[
    "class",
    "interface",
    "enum",
    "record",
    "annotation",
    "type-alias",
    "table",
    "view",
    "index",
    "sequence",
    "type",
    "schema",
    "trigger",
    "package",
    "package-body",
    "type-body",
    # Rust-specific kinds:
    "struct",
    "trait",
    "impl",
    "mod",
    "union",
]


@dataclass
class ParameterInfo:
    name: str
    annotation: str | None = None
    default: str | None = None


@dataclass
class FunctionInfo:
    name: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_annotation: str | None = None
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    # Visibility hint, populated by adapters that know (Java public/private,
    # JS/TS export, SQL CREATE vs CREATE OR REPLACE). "procedure" is the
    # SQL/PL-SQL marker for a stored procedure (vs a function).
    visibility: Visibility | None = None
    docstring: str | None = None
    line_number: int = 0


@dataclass
class ClassInfo:
    name: str
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionInfo] = field(default_factory=list)
    class_variables: list[str] = field(default_factory=list)
    # Distinguish class / interface / enum / record / type-alias / DDL kinds.
    # See `Kind` for the full enumeration.
    kind: Kind = "class"
    visibility: Visibility | None = None
    docstring: str | None = None
    line_number: int = 0


@dataclass
class ImportInfo:
    module: str
    names: list[str] = field(default_factory=list)
    is_from_import: bool = False
    is_internal: bool = False


@dataclass
class ExternalCallInfo:
    call_type: CallType
    pattern: str
    line_number: int
    context: str


@dataclass
class ParseResult:
    """
    Convention for `functions` vs `classes[*].methods`:

    - `functions` contains TOP-LEVEL callables (Python top-level def, JS top-level
      function/arrow declarations, SQL CREATE FUNCTION/PROCEDURE, PL/SQL inner
      PROCEDURE/FUNCTION declarations).
    - Methods of a class/interface/etc. live inside `classes[*].methods` and
      are NOT duplicated into `functions`.
    - Java has no top-level functions, so `functions` is always empty for
      Java files; all callables are class methods.

    Consumers enumerating "every callable in the file" must visit both lists:
    `functions + [m for c in classes for m in c.methods]`.

    Convention for `notes`:

    - `notes[0]` starts with `parser=<source>` where source is one of:
      `stdlib-ast` (Python), `tree-sitter` (Java/JS), `tree-sitter (ts)` (TS),
      `regex-fallback` (Java/JS), `regex-fallback (ts)` (TS),
      `regex (sql)` (SQL), `regex (plsql)` (PL/SQL).
    - Additional notes may be appended for syntax errors, tree-sitter
      exceptions, lossy encoding, etc.
    """

    file_path: str
    language: str = "unknown"
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    external_calls: list[ExternalCallInfo] = field(default_factory=list)
    exported_symbols: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@runtime_checkable
class LanguageAdapter(Protocol):
    """
    Each language module exposes a module-level `adapter` matching this.

    `language` is a class-level constant (each adapter sets it on the class,
    not the instance) and must equal one of the canonical identifiers in
    `languages.Language`.
    """

    language: ClassVar[str]

    def parse(self, content: str, file_path: str) -> ParseResult:
        ...

    def count_imports(self, content: str) -> int:
        ...

    def strip_comments_and_blanks(self, content: str) -> int:
        """Return number of non-empty, non-comment lines."""
        ...

    def extract_comments(
        self, content: str
    ) -> list["CommentToken"]:
        """
        Return all comments in the file with their token info.

        See comments.CommentToken for the shape.
        """
        ...


# Forward import declared here so adapters can import the type from base.
from .comments import CommentToken  # noqa: E402  (placed after Protocol on purpose)

__all__.append("CommentToken")
