"""
Rust adapter. Tree-sitter when available, regex fallback otherwise.

Covers: top-level `fn` declarations, `struct`/`enum`/`trait`/`impl`/`mod`/
`union`/`type` items, `use` declarations (with crate/super/self -> internal
heuristic), common external API calls (std::fs, tokio::*, reqwest, sqlx,
diesel, etc.), constants/statics, and async/unsafe complexity markers.

Methods defined inside `impl Foo {}` blocks are attached as
`ClassInfo.methods` on a synthetic `ClassInfo(name="Foo", kind="impl")`.
For trait impls (`impl TraitName for Foo {}`) the synthetic name is
`"TraitName for Foo"`.

Comment doc-block detection (`///`, `//!`, `/*!`) is handled by
`languages.comments.extract_rust_comments` -- not by this adapter.
"""

from __future__ import annotations

import re
from typing import Any

from ._treesitter import get_parser, node_text
from .base import (
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken, extract_rust_comments

__all__ = ["adapter"]

_LANGUAGE_NAME = "rust"


# Rust internal-vs-external import rule:
# `use crate::*`, `use super::*`, `use self::*` are internal to the current
# crate. Everything else (`std`, `core`, `alloc`, crates.io packages) is
# external from the project's perspective.
_INTERNAL_USE_PREFIXES = ("crate::", "super::", "self::", "crate", "super", "self")


def _is_internal_use(path: str) -> bool:
    if not path:
        return False
    stripped = path.lstrip()
    return stripped.startswith(_INTERNAL_USE_PREFIXES)


# External call categories. Receivers are matched as path prefixes on the
# full `path::expr` text.
_DB_RE = re.compile(
    r"\b(?:sqlx|diesel|tokio_postgres|tokio_mysql|redis|mongodb|rusqlite|sea_orm|sqlite)\b|"
    r"\.(?:execute|query|query_as|query_one|query_all|fetch|fetch_one|fetch_all|insert|update|delete)\("
)
_NET_RE = re.compile(
    r"\b(?:reqwest|hyper|isahc|surf|ureq|actix_web|axum|warp|rocket|tonic)\b|"
    r"std::net::\w+|tokio::net::\w+"
)
_FS_RE = re.compile(
    r"std::fs::\w+|tokio::fs::\w+|std::path::Path|std::fs::File|tokio::fs::File"
)
_MSG_RE = re.compile(
    r"tokio::sync::(?:mpsc|broadcast|watch|oneshot)|crossbeam(?:::channel|_channel)|"
    r"\blapin\b|\brdkafka\b|\bnats\b|async_channel::"
)
_IPC_RE = re.compile(
    r"std::process::\w+|tokio::process::\w+|std::sync::mpsc|std::thread::\w+"
)


def _scan_external_calls(content: str) -> list[ExternalCallInfo]:
    out: list[ExternalCallInfo] = []
    for i, line in enumerate(content.splitlines(), start=1):
        ctx = line.strip()[:100]
        if _DB_RE.search(line):
            out.append(ExternalCallInfo("database", "db-api", i, ctx))
        if _NET_RE.search(line):
            out.append(ExternalCallInfo("network", "net-api", i, ctx))
        if _FS_RE.search(line):
            out.append(ExternalCallInfo("filesystem", "fs-api", i, ctx))
        if _MSG_RE.search(line):
            out.append(ExternalCallInfo("messaging", "msg-api", i, ctx))
        if _IPC_RE.search(line):
            out.append(ExternalCallInfo("ipc", "ipc-api", i, ctx))
    return out


def _vis_from_modifier(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    if s == "pub":
        return "public"
    if s.startswith("pub("):
        # pub(crate), pub(super), pub(in path::to), pub(self)
        return "protected"
    return None


# ---------------------------------------------------------------------------
# Tree-sitter path.
# ---------------------------------------------------------------------------


_TS_ERROR_HOLDER: dict[str, str] = {}


def _ts_parse(content: str) -> ParseResult | None:
    pair = get_parser("rust")
    if pair is None:
        return None
    parser, _lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as e:
        _TS_ERROR_HOLDER["last"] = f"{type(e).__name__}: {e}"
        return None

    def text(n: Any) -> str:
        return node_text(n, src)

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def parse_vis(node: Any) -> str | None:
        for c in node.children:
            if c.type == "visibility_modifier":
                return _vis_from_modifier(text(c))
        return None

    def parse_params(params_node: Any) -> list[ParameterInfo]:
        out: list[ParameterInfo] = []
        if params_node is None:
            return out
        for child in params_node.children:
            if child.type == "parameter":
                name_node = child.child_by_field_name("pattern")
                ann_node = child.child_by_field_name("type")
                out.append(
                    ParameterInfo(
                        name=text(name_node) if name_node else "?",
                        annotation=text(ann_node) if ann_node else None,
                    )
                )
            elif child.type == "self_parameter":
                out.append(ParameterInfo(name=text(child)))
        return out

    def is_async(node: Any) -> bool:
        for c in node.children:
            if c.type == "function_modifiers":
                if "async" in text(c):
                    return True
        return False

    def parse_function(node: Any) -> FunctionInfo:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        ret_node = node.child_by_field_name("return_type")
        return FunctionInfo(
            name=text(name_node) if name_node else "?",
            parameters=parse_params(params_node),
            return_annotation=text(ret_node) if ret_node else None,
            is_async=is_async(node),
            visibility=parse_vis(node),
            line_number=node.start_point[0] + 1,
        )

    def parse_impl_name(node: Any) -> str:
        # `impl Trait for Type` or `impl Type` -- name = "Trait for Type" or "Type"
        type_node = node.child_by_field_name("type")
        trait_node = node.child_by_field_name("trait")
        if trait_node is not None and type_node is not None:
            return f"{text(trait_node)} for {text(type_node)}"
        if type_node is not None:
            return text(type_node)
        return "?"

    def parse_impl(node: Any) -> ClassInfo:
        name = parse_impl_name(node)
        methods: list[FunctionInfo] = []
        body = node.child_by_field_name("body")
        if body is not None:
            for child in body.children:
                if child.type == "function_item":
                    methods.append(parse_function(child))
        return ClassInfo(
            name=name,
            methods=methods,
            kind="impl",
            line_number=node.start_point[0] + 1,
        )

    def parse_struct_like(node: Any, kind: str) -> ClassInfo:
        name_node = node.child_by_field_name("name")
        bases: list[str] = []
        # Field names go into class_variables for struct/union.
        class_vars: list[str] = []
        body = node.child_by_field_name("body")
        if body is not None:
            for child in body.children:
                if child.type in ("field_declaration", "named_field_declaration"):
                    n = child.child_by_field_name("name") or (child.children[0] if child.children else None)
                    if n is not None:
                        class_vars.append(text(n))
        return ClassInfo(
            name=text(name_node) if name_node else "?",
            bases=bases,
            class_variables=class_vars,
            kind=kind,
            visibility=parse_vis(node),
            line_number=node.start_point[0] + 1,
        )

    def parse_trait(node: Any) -> ClassInfo:
        name_node = node.child_by_field_name("name")
        methods: list[FunctionInfo] = []
        body = node.child_by_field_name("body")
        if body is not None:
            for child in body.children:
                if child.type == "function_item":
                    methods.append(parse_function(child))
                elif child.type == "function_signature_item":
                    name_n = child.child_by_field_name("name")
                    params_n = child.child_by_field_name("parameters")
                    ret_n = child.child_by_field_name("return_type")
                    methods.append(
                        FunctionInfo(
                            name=text(name_n) if name_n else "?",
                            parameters=parse_params(params_n),
                            return_annotation=text(ret_n) if ret_n else None,
                            line_number=child.start_point[0] + 1,
                        )
                    )
        return ClassInfo(
            name=text(name_node) if name_node else "?",
            methods=methods,
            kind="trait",
            visibility=parse_vis(node),
            line_number=node.start_point[0] + 1,
        )

    def parse_mod(node: Any) -> ClassInfo:
        name_node = node.child_by_field_name("name")
        return ClassInfo(
            name=text(name_node) if name_node else "?",
            kind="mod",
            visibility=parse_vis(node),
            line_number=node.start_point[0] + 1,
        )

    def parse_use(node: Any) -> None:
        # use foo::bar::baz; use foo::{a, b}; use foo::*;
        # We capture the full path text as `module` and best-effort split the
        # final segment into `names`.
        argument = node.child_by_field_name("argument") or (node.children[1] if len(node.children) > 1 else None)
        raw = text(argument).strip().rstrip(";").strip() if argument is not None else ""
        is_internal = _is_internal_use(raw)
        # Split out names from `use foo::{a, b}` form.
        names: list[str] = []
        m = re.match(r"^(?P<base>[\w:]+)::\{(?P<list>[^}]+)\}$", raw)
        if m:
            base = m.group("base")
            for n in m.group("list").split(","):
                names.append(n.strip())
            imports.append(
                ImportInfo(
                    module=base,
                    names=names,
                    is_from_import=True,
                    is_internal=_is_internal_use(base),
                )
            )
        else:
            imports.append(
                ImportInfo(
                    module=raw,
                    names=[raw.rsplit("::", 1)[-1]] if "::" in raw else [raw],
                    is_from_import=False,
                    is_internal=is_internal,
                )
            )

    # Walk top-level children.
    root = tree.root_node
    for child in root.children:
        t = child.type
        if t == "function_item":
            fn = parse_function(child)
            functions.append(fn)
            if fn.visibility == "public":
                exported.append(fn.name)
        elif t == "struct_item":
            ci = parse_struct_like(child, "struct")
            classes.append(ci)
            if ci.visibility == "public":
                exported.append(ci.name)
        elif t == "enum_item":
            ci = parse_struct_like(child, "enum")
            classes.append(ci)
            if ci.visibility == "public":
                exported.append(ci.name)
        elif t == "union_item":
            ci = parse_struct_like(child, "union")
            classes.append(ci)
            if ci.visibility == "public":
                exported.append(ci.name)
        elif t == "trait_item":
            ci = parse_trait(child)
            classes.append(ci)
            if ci.visibility == "public":
                exported.append(ci.name)
        elif t == "impl_item":
            ci = parse_impl(child)
            classes.append(ci)
        elif t == "mod_item":
            ci = parse_mod(child)
            classes.append(ci)
            if ci.visibility == "public":
                exported.append(ci.name)
        elif t == "type_item":
            name_node = child.child_by_field_name("name")
            ci = ClassInfo(
                name=text(name_node) if name_node else "?",
                kind="type-alias",
                visibility=parse_vis(child),
                line_number=child.start_point[0] + 1,
            )
            classes.append(ci)
            if ci.visibility == "public":
                exported.append(ci.name)
        elif t == "use_declaration":
            parse_use(child)
        elif t in ("const_item", "static_item"):
            name_node = child.child_by_field_name("name")
            if name_node is not None:
                name = text(name_node)
                if re.fullmatch(r"[A-Z_][A-Z0-9_]*", name):
                    constants.append(name)
                if parse_vis(child) == "public":
                    exported.append(name)

    return ParseResult(
        file_path="",
        language=_LANGUAGE_NAME,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=_scan_external_calls(content),
        exported_symbols=list(dict.fromkeys(exported)),
        notes=["parser=tree-sitter"],
    )


# ---------------------------------------------------------------------------
# Regex fallback.
# ---------------------------------------------------------------------------


_FN_RE = re.compile(
    r"^\s*(?P<vis>pub(?:\([^)]*\))?\s+)?"
    r"(?P<mods>(?:async\s+|const\s+|unsafe\s+|extern\s+(?:\"[^\"]*\"\s+)?)*)"
    r"fn\s+(?P<name>\w+)\s*(?:<[^>]*>)?\s*\((?P<params>[^)]*)\)"
    r"(?:\s*->\s*(?P<ret>[^\{;]+))?",
    re.MULTILINE,
)
_STRUCT_LIKE_RE = re.compile(
    r"^\s*(?P<vis>pub(?:\([^)]*\))?\s+)?(?P<kind>struct|enum|trait|union|mod)\s+(?P<name>\w+)",
    re.MULTILINE,
)
_IMPL_RE = re.compile(
    r"^\s*impl(?:<[^>]*>)?\s+(?P<lhs>[\w:<>, ]+?)(?:\s+for\s+(?P<rhs>[\w:<>, ]+?))?\s*\{",
    re.MULTILINE,
)
_TYPE_ALIAS_RE = re.compile(
    r"^\s*(?P<vis>pub(?:\([^)]*\))?\s+)?type\s+(?P<name>\w+)(?:<[^>]*>)?\s*=",
    re.MULTILINE,
)
_USE_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+(?P<path>[\w:\*{},\s]+?)\s*;",
    re.MULTILINE,
)
_CONST_RE = re.compile(
    r"^\s*(?P<vis>pub(?:\([^)]*\))?\s+)?(?:const|static)\s+(?P<name>[A-Z_][A-Z0-9_]*)\s*:",
    re.MULTILINE,
)


def _regex_parse(content: str) -> ParseResult:
    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def line_no(idx: int) -> int:
        return content[:idx].count("\n") + 1

    def parse_params(raw: str) -> list[ParameterInfo]:
        params: list[ParameterInfo] = []
        if not raw or not raw.strip():
            return params
        depth = 0
        buf = []
        pieces: list[str] = []
        for ch in raw:
            if ch in "(<":
                depth += 1
                buf.append(ch)
            elif ch in ")>":
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
            piece = piece.strip()
            if not piece:
                continue
            if piece in ("self", "&self", "&mut self", "mut self"):
                params.append(ParameterInfo(name=piece))
                continue
            if ":" in piece:
                name, _, ann = piece.partition(":")
                params.append(ParameterInfo(name=name.strip(), annotation=ann.strip()))
            else:
                params.append(ParameterInfo(name=piece))
        return params

    # Functions (top-level only -- impl-block methods are caught by _IMPL_RE).
    seen_fn_positions: set[int] = set()
    for m in _FN_RE.finditer(content):
        # Track positions so we can later skip these when checking impl-block methods.
        seen_fn_positions.add(m.start())
        vis = _vis_from_modifier((m.group("vis") or "").strip())
        mods = m.group("mods") or ""
        is_async_fn = "async" in mods
        params = parse_params(m.group("params") or "")
        ret = (m.group("ret") or "").strip() or None
        fn = FunctionInfo(
            name=m.group("name"),
            parameters=params,
            return_annotation=ret,
            is_async=is_async_fn,
            visibility=vis,
            line_number=line_no(m.start()),
        )
        functions.append(fn)
        if vis == "public":
            exported.append(fn.name)

    # Struct/enum/trait/union/mod.
    for m in _STRUCT_LIKE_RE.finditer(content):
        vis = _vis_from_modifier((m.group("vis") or "").strip())
        kind_raw = m.group("kind")
        kind = "type-alias" if kind_raw == "type" else kind_raw
        ci = ClassInfo(
            name=m.group("name"),
            kind=kind,
            visibility=vis,
            line_number=line_no(m.start()),
        )
        classes.append(ci)
        if vis == "public":
            exported.append(ci.name)

    # impl blocks.
    for m in _IMPL_RE.finditer(content):
        lhs = m.group("lhs").strip()
        rhs = m.group("rhs")
        if rhs is not None:
            name = f"{lhs} for {rhs.strip()}"
        else:
            name = lhs
        classes.append(
            ClassInfo(
                name=name,
                kind="impl",
                line_number=line_no(m.start()),
            )
        )

    # type aliases.
    for m in _TYPE_ALIAS_RE.finditer(content):
        vis = _vis_from_modifier((m.group("vis") or "").strip())
        ci = ClassInfo(
            name=m.group("name"),
            kind="type-alias",
            visibility=vis,
            line_number=line_no(m.start()),
        )
        classes.append(ci)
        if vis == "public":
            exported.append(ci.name)

    # use declarations.
    for m in _USE_RE.finditer(content):
        path = m.group("path").strip()
        is_internal = _is_internal_use(path)
        names: list[str] = []
        sub = re.match(r"^(?P<base>[\w:]+)::\{(?P<list>[^}]+)\}$", path)
        if sub:
            base = sub.group("base")
            names = [n.strip() for n in sub.group("list").split(",") if n.strip()]
            imports.append(
                ImportInfo(
                    module=base,
                    names=names,
                    is_from_import=True,
                    is_internal=_is_internal_use(base),
                )
            )
        else:
            imports.append(
                ImportInfo(
                    module=path,
                    names=[path.rsplit("::", 1)[-1]] if "::" in path else [path],
                    is_from_import=False,
                    is_internal=is_internal,
                )
            )

    # Constants and statics (UPPER_CASE only).
    for m in _CONST_RE.finditer(content):
        name = m.group("name")
        constants.append(name)
        if _vis_from_modifier((m.group("vis") or "").strip()) == "public":
            exported.append(name)

    return ParseResult(
        file_path="",
        language=_LANGUAGE_NAME,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=list(dict.fromkeys(constants)),
        external_calls=_scan_external_calls(content),
        exported_symbols=list(dict.fromkeys(exported)),
        notes=["parser=regex-fallback"],
    )


# ---------------------------------------------------------------------------


class _RustAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        _TS_ERROR_HOLDER.pop("last", None)
        result = _ts_parse(content)
        if result is None:
            result = _regex_parse(content)
            err = _TS_ERROR_HOLDER.pop("last", None)
            if err is not None:
                result.notes.append(f"tree-sitter raised: {err}")
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        return len(_USE_RE.findall(content))

    def strip_comments_and_blanks(self, content: str) -> int:
        # Strip /* ... */ blocks, then count non-empty, non-// lines.
        no_blocks = re.sub(r"/\*[\s\S]*?\*/", "", content)
        code = 0
        for line in no_blocks.split("\n"):
            s = line.strip()
            if not s:
                continue
            if s.startswith("//"):
                continue
            code += 1
        return code

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_rust_comments(content)


adapter = _RustAdapter()
