"""
TypeScript adapter. Builds on the JavaScript adapter and adds:

- interface declarations (kind="interface")
- enum declarations (kind="enum")
- type alias declarations (kind="type-alias")

The tree-sitter `typescript` grammar handles `.ts`; `tsx` is a separate grammar
that also covers JSX/TSX. We detect TSX via file path suffix when called.
"""

from __future__ import annotations

import re
from typing import Any

from ._treesitter import get_parser, node_text
from .base import ClassInfo, ParseResult
from .comments import CommentToken, extract_c_style_comments

# NOTE: `javascript` is imported lazily inside the methods/helpers below so a
# TS-only user with a broken JS grammar package does not see TS parsing fail
# at module import time. The chain TS -> JS is intentional code reuse but
# should not be a load-time dependency.

__all__ = ["adapter"]

_LANGUAGE_NAME = "typescript"


_INTERFACE_RE = re.compile(
    r"^\s*(?:export\s+)?interface\s+(?P<name>\w+)(?:\s*<[^>]*>)?(?:\s+extends\s+(?P<ext>[\w.,<>\s]+))?\s*\{",
    re.MULTILINE,
)
_TYPE_ALIAS_RE = re.compile(
    r"^\s*(?:export\s+)?type\s+(?P<name>\w+)(?:\s*<[^>]*>)?\s*=",
    re.MULTILINE,
)
_ENUM_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const\s+)?enum\s+(?P<name>\w+)\s*\{",
    re.MULTILINE,
)


def _augment_with_ts_constructs(content: str, base: ParseResult) -> ParseResult:
    """Append interface/enum/type-alias entries to a JS-parsed result."""
    for m in _INTERFACE_RE.finditer(content):
        bases: list[str] = []
        if m.group("ext"):
            bases.extend(b.strip() for b in m.group("ext").split(",") if b.strip())
        base.classes.append(
            ClassInfo(
                name=m.group("name"),
                bases=bases,
                kind="interface",
                line_number=content[: m.start()].count("\n") + 1,
            )
        )
        base.exported_symbols.append(m.group("name"))
    for m in _ENUM_RE.finditer(content):
        base.classes.append(
            ClassInfo(
                name=m.group("name"),
                kind="enum",
                line_number=content[: m.start()].count("\n") + 1,
            )
        )
        base.exported_symbols.append(m.group("name"))
    for m in _TYPE_ALIAS_RE.finditer(content):
        base.classes.append(
            ClassInfo(
                name=m.group("name"),
                kind="type-alias",
                line_number=content[: m.start()].count("\n") + 1,
            )
        )
        base.exported_symbols.append(m.group("name"))
    # Deduplicate exported symbols.
    base.exported_symbols = list(dict.fromkeys(base.exported_symbols))
    return base


def _ts_parse(content: str, is_tsx: bool) -> ParseResult | None:
    from . import javascript as _js  # lazy import; see module docstring

    pair = get_parser("tsx" if is_tsx else "typescript")
    if pair is None:
        return None
    parser, _lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as e:
        # Mirror the Java/JS pattern: surface via the JS holder so the parent
        # _JavaScriptAdapter.parse / _TypeScriptAdapter.parse will annotate notes.
        _js._TS_ERROR_HOLDER["last"] = f"{type(e).__name__}: {e}"
        return None

    def text(n: Any) -> str:
        return node_text(n, src)

    # The TypeScript grammar is a superset of JS, so class_declaration,
    # function_declaration, import_statement, lexical_declaration, and
    # export_statement keep the same node names. Run the JS walker first
    # to get those, then layer the TS-only constructs. The walker must use
    # the SAME grammar as the local parse above: feeding a .tsx file to the
    # plain typescript grammar yields ERROR nodes around JSX and drops
    # declarations.
    js_result = _js._ts_parse(content, language="tsx" if is_tsx else _LANGUAGE_NAME)
    if js_result is None:
        return None

    ts_classes: list[ClassInfo] = []
    ts_exported: list[str] = []

    def collect_interface(node: Any, exported_flag: bool) -> None:
        name_node = node.child_by_field_name("name")
        bases: list[str] = []
        heritage = node.child_by_field_name("heritage")
        if heritage is None:
            for c in node.children:
                if c.type in ("extends_type_clause", "extends_clause"):
                    heritage = c
                    break
        if heritage is not None:
            for c in heritage.children:
                t2 = text(c).strip()
                if t2 and t2 not in ("extends", ","):
                    bases.append(t2)
        ci = ClassInfo(
            name=text(name_node) if name_node else "?",
            bases=bases,
            kind="interface",
            line_number=node.start_point[0] + 1,
        )
        ts_classes.append(ci)
        if exported_flag:
            ts_exported.append(ci.name)

    def collect_simple(node: Any, kind: str, exported_flag: bool) -> None:
        name_node = node.child_by_field_name("name")
        ci = ClassInfo(
            name=text(name_node) if name_node else "?",
            kind=kind,
            line_number=node.start_point[0] + 1,
        )
        ts_classes.append(ci)
        if exported_flag:
            ts_exported.append(ci.name)

    def walk(node: Any, exported_flag: bool) -> None:
        for child in node.children:
            t = child.type
            if t == "interface_declaration":
                collect_interface(child, exported_flag)
            elif t == "enum_declaration":
                collect_simple(child, "enum", exported_flag)
            elif t == "type_alias_declaration":
                collect_simple(child, "type-alias", exported_flag)
            elif t == "export_statement":
                walk(child, exported_flag=True)

    walk(tree.root_node, exported_flag=False)

    js_result.classes.extend(ts_classes)
    js_result.exported_symbols.extend(ts_exported)
    js_result.exported_symbols = list(dict.fromkeys(js_result.exported_symbols))
    js_result.language = _LANGUAGE_NAME
    # Re-tag parser provenance so downstream display shows TS, not JS.
    js_result.notes = [n.replace("=tree-sitter", "=tree-sitter (ts)") for n in js_result.notes]
    return js_result


class _TypeScriptAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        from . import javascript as _js  # lazy import

        _js._TS_ERROR_HOLDER.pop("last", None)
        is_tsx = file_path.lower().endswith(".tsx")
        result = _ts_parse(content, is_tsx=is_tsx)
        if result is None:
            # Fallback: JS regex + TS-only constructs.
            result = _js._regex_parse(content, language=self.language)
            result = _augment_with_ts_constructs(content, result)
            # Re-tag parser provenance so downstream display shows TS.
            result.notes = [n.replace("=regex-fallback", "=regex-fallback (ts)") for n in result.notes]
            err = _js._TS_ERROR_HOLDER.pop("last", None)
            if err is not None:
                result.notes.append(f"tree-sitter raised: {err}")
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        from . import javascript as _js  # lazy import

        return _js.adapter.count_imports(content)

    def strip_comments_and_blanks(self, content: str) -> int:
        from . import javascript as _js  # lazy import

        return _js.adapter.strip_comments_and_blanks(content)

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter = _TypeScriptAdapter()
