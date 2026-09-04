"""
JavaScript adapter. Tree-sitter when available, regex fallback otherwise.

Covers: classes, functions (declarations, expressions, arrow), imports (ES6,
CommonJS require), exported symbols, common external API calls (fetch, fs.*,
http.*, mysql/pg/mongoose/sequelize, kafkajs/amqplib/redis, child_process).
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
from .comments import CommentToken, extract_c_style_comments

__all__ = ["adapter"]

_LANGUAGE_NAME = "javascript"


_RELATIVE_IMPORT_PREFIXES = ("./", "../", "/")


def _is_internal_module(module: str) -> bool:
    """
    Classify a JS/TS import specifier as internal-to-the-project or external.

    Internal: relative path imports (`./foo`, `../bar`, `/baz`).
    External: `node:` builtins, scoped npm packages (`@scope/name`), and bare
    npm specifiers (`react`, `lodash/get`). Bare specifiers default to
    external because they're almost always npm packages -- a workspace
    setup that aliases them internally is rare enough that we accept the
    occasional misclassification.
    """
    if not module:
        return False
    if module.startswith(_RELATIVE_IMPORT_PREFIXES):
        return True
    return False


_DB_RE = re.compile(
    r"\b(?:mysql|pg|pg-promise|mongoose|sequelize|prisma|knex|typeorm|"
    r"mongodb|MongoClient|createConnection|createPool|\.query\(|\.execute\(|"
    r"\.findOne\(|\.findMany\(|\.findAll\(|\.insertOne\(|\.updateOne\(|\.deleteOne\(|"
    r"\.save\(|\.aggregate\()"
)
_NET_RE = re.compile(
    r"\b(?:fetch\(|axios|got\(|node-fetch|http\.(?:get|request)\(|https\.(?:get|request)\(|"
    r"new\s+XMLHttpRequest|new\s+WebSocket|new\s+EventSource|grpc)\b"
)
_FS_RE = re.compile(
    r"\bfs\.(?:readFile|readFileSync|writeFile|writeFileSync|appendFile|unlink|mkdir|rmdir|stat|"
    r"createReadStream|createWriteStream|promises\.)\b"
)
_MSG_RE = re.compile(
    r"\b(?:kafkajs|amqplib|redis|ioredis|bull|bullmq|nats|mqtt|socket\.io|"
    r"\.publish\(|\.subscribe\(|\.consume\(|\.sendMessage\()"
)
_IPC_RE = re.compile(
    r"\b(?:child_process|spawn\(|exec\(|fork\(|cluster\.|worker_threads|"
    r"process\.send\()"
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


# ---------------------------------------------------------------------------
# Tree-sitter path.
# ---------------------------------------------------------------------------


_TS_ERROR_HOLDER: dict[str, str] = {}


def _ts_parse(content: str, language: str = _LANGUAGE_NAME) -> ParseResult | None:
    pair = get_parser(language)
    if pair is None:
        return None
    parser, _lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as e:
        # Tree-sitter MAY raise on extreme input. Signal caller via None.
        _TS_ERROR_HOLDER["last"] = f"{type(e).__name__}: {e}"
        return None

    def text(n: Any) -> str:
        return node_text(n, src)

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def parse_params(node: Any) -> list[ParameterInfo]:
        out: list[ParameterInfo] = []
        if node is None:
            return out
        for child in node.children:
            if child.type in ("identifier", "required_parameter", "optional_parameter"):
                # JS typically uses identifier; TS uses required/optional_parameter.
                name_node = child if child.type == "identifier" else child.child_by_field_name("pattern") or child.children[0]
                ann_node = child.child_by_field_name("type") if child.type != "identifier" else None
                default_node = child.child_by_field_name("value") if child.type != "identifier" else None
                out.append(
                    ParameterInfo(
                        name=text(name_node).lstrip(":?"),
                        annotation=text(ann_node).lstrip(":").strip() if ann_node else None,
                        default=text(default_node) if default_node else None,
                    )
                )
            elif child.type == "rest_pattern":
                out.append(ParameterInfo(name="..." + text(child.children[-1])))
            elif child.type == "assignment_pattern":
                left = child.child_by_field_name("left")
                right = child.child_by_field_name("right")
                out.append(
                    ParameterInfo(
                        name=text(left) if left else "?",
                        default=text(right) if right else None,
                    )
                )
            elif child.type == "object_pattern":
                out.append(ParameterInfo(name="{...}"))
            elif child.type == "array_pattern":
                out.append(ParameterInfo(name="[...]"))
        return out

    def parse_function_like(node: Any, kind: str, default_name: str | None = None) -> FunctionInfo:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        is_async = any(c.type == "async" for c in node.children) or any(
            text(c).strip() == "async" for c in node.children if c.type == "keyword"
        )
        ret_ann = node.child_by_field_name("return_type")
        return FunctionInfo(
            name=text(name_node) if name_node else (default_name or "(anonymous)"),
            parameters=parse_params(params_node),
            return_annotation=text(ret_ann).lstrip(":").strip() if ret_ann else None,
            is_async=is_async,
            line_number=node.start_point[0] + 1,
        )

    def parse_class(node: Any) -> ClassInfo:
        name_node = node.child_by_field_name("name")
        bases: list[str] = []
        heritage = node.child_by_field_name("heritage") or None
        if heritage is None:
            # In some grammars heritage clauses are children, not a named field.
            for c in node.children:
                if c.type in ("class_heritage", "extends_clause"):
                    heritage = c
                    break
        if heritage is not None:
            for c in heritage.children:
                if c.type in ("extends_clause", "implements_clause"):
                    for sub in c.children:
                        if sub.type not in ("extends", "implements", ",", "extends_keyword"):
                            t = text(sub).strip()
                            if t and t not in ("extends", "implements"):
                                bases.append(t)
                elif c.type not in ("extends", "implements", ",", "class_heritage"):
                    t = text(c).strip()
                    if t and t not in ("extends", "implements"):
                        bases.append(t)
        body = node.child_by_field_name("body")
        methods: list[FunctionInfo] = []
        class_vars: list[str] = []
        if body is not None:
            for child in body.children:
                if child.type in ("method_definition", "method_signature"):
                    methods.append(parse_function_like(child, "method"))
                elif child.type in ("field_definition", "public_field_definition", "property_definition"):
                    n = child.child_by_field_name("name") or (child.children[0] if child.children else None)
                    value = child.child_by_field_name("value")
                    if value is not None and value.type in ("arrow_function", "function_expression", "function"):
                        # `handler = (x) => {...}` is a method in everything but syntax.
                        method = parse_function_like(value, "method", default_name=text(n) if n else None)
                        method.line_number = child.start_point[0] + 1
                        methods.append(method)
                    elif n is not None:
                        class_vars.append(text(n))
        return ClassInfo(
            name=text(name_node) if name_node else "?",
            bases=bases,
            methods=methods,
            class_variables=class_vars,
            kind="class",
            line_number=node.start_point[0] + 1,
        )

    def walk_for_decls(node: Any, depth: int = 0, in_export: bool = False) -> None:
        for child in node.children:
            t = child.type
            if t == "import_statement":
                source_node = child.child_by_field_name("source")
                if source_node is not None:
                    raw = text(source_node).strip().strip("'\"`")
                    # Collect bound names.
                    names: list[str] = []
                    for c in child.children:
                        if c.type == "import_clause":
                            for sub in c.children:
                                if sub.type == "identifier":
                                    names.append(text(sub))
                                elif sub.type == "named_imports":
                                    for spec in sub.children:
                                        if spec.type == "import_specifier":
                                            id_node = spec.child_by_field_name("name") or spec.children[0]
                                            names.append(text(id_node))
                                elif sub.type == "namespace_import":
                                    id_node = sub.children[-1]
                                    names.append("*" + " as " + text(id_node))
                    imports.append(
                        ImportInfo(
                            module=raw,
                            names=names,
                            is_from_import=True,
                            is_internal=_is_internal_module(raw),
                        )
                    )
            elif t == "lexical_declaration" or t == "variable_declaration":
                # Detect CommonJS require: const X = require('mod').
                for sub in child.children:
                    if sub.type == "variable_declarator":
                        val = sub.child_by_field_name("value")
                        if val is not None and val.type == "call_expression":
                            callee = val.child_by_field_name("function")
                            if callee is not None and text(callee) == "require":
                                args = val.child_by_field_name("arguments")
                                if args is not None and len(args.children) >= 2:
                                    arg = args.children[1]
                                    if arg.type == "string":
                                        raw = text(arg).strip("'\"`")
                                        n = sub.child_by_field_name("name")
                                        names_list = [text(n)] if n else []
                                        imports.append(
                                            ImportInfo(
                                                module=raw,
                                                names=names_list,
                                                is_from_import=False,
                                                is_internal=_is_internal_module(raw),
                                            )
                                        )
                # Top-level lexical decls produce constants if UPPER_CASE, and
                # functions when their value is a function: `const f = () => ...`
                # is how most module-level functions are written now.
                if depth == 0 or in_export:
                    for sub in child.children:
                        if sub.type == "variable_declarator":
                            n = sub.child_by_field_name("name")
                            if n is None:
                                continue
                            name = text(n)
                            val = sub.child_by_field_name("value")
                            if val is not None and val.type in ("arrow_function", "function_expression", "function"):
                                fn = parse_function_like(val, "function", default_name=name)
                                fn.line_number = sub.start_point[0] + 1
                                functions.append(fn)
                            elif depth == 0 and name.isidentifier() and name.isupper():
                                constants.append(name)
            elif t == "class_declaration":
                cls = parse_class(child)
                classes.append(cls)
                if depth == 0 or in_export:
                    exported.append(cls.name)
            elif t == "function_declaration":
                fn = parse_function_like(child, "function")
                functions.append(fn)
                if depth == 0 or in_export:
                    exported.append(fn.name)
            elif t == "export_statement":
                # Exported variable names are only visible here; classes and
                # functions are collected by the recursion below (collecting
                # them here as well would double-count every exported decl).
                for sub in child.children:
                    if sub.type in ("lexical_declaration", "variable_declaration"):
                        for d in sub.children:
                            if d.type == "variable_declarator":
                                n = d.child_by_field_name("name")
                                if n is not None:
                                    exported.append(text(n))
                walk_for_decls(child, depth + 1, in_export=True)
                continue
            # Recurse into program-level structures to find functions inside.
            if t == "statement_block":
                walk_for_decls(child, depth + 1, in_export=in_export)

    walk_for_decls(tree.root_node, depth=0)

    return ParseResult(
        file_path="",
        language=language,
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


_IMPORT_RE = re.compile(
    r"""import\s+(?:(?P<default>\w+)\s*,?\s*)?(?:\{\s*(?P<named>[^}]+)\}\s*)?(?:\*\s*as\s*(?P<ns>\w+)\s*)?(?:from\s+)?['"`](?P<source>[^'"`]+)['"`]""",
    re.MULTILINE | re.DOTALL,
)
_REQUIRE_RE = re.compile(
    r"""(?:const|let|var)\s+(?P<binding>\{[^}]+\}|\w+)\s*=\s*require\(['"`](?P<source>[^'"`]+)['"`]\)""",
    re.MULTILINE,
)
_CLASS_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:abstract\s+)?class\s+(?P<name>\w+)(?:\s+extends\s+(?P<ext>[\w.<>]+))?(?:\s+implements\s+(?P<impl>[\w.,\s<>]+))?\s*\{",
    re.MULTILINE,
)
_FUNC_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?P<async>async\s+)?function\s*\*?\s*(?P<name>\w+)\s*\(",
    re.MULTILINE,
)
_ARROW_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(?P<name>\w+)\s*=\s*(?P<async>async\s+)?\([^)]*\)\s*=>",
    re.MULTILINE,
)
_CONSTANT_RE = re.compile(
    r"^\s*(?:export\s+)?const\s+(?P<name>[A-Z][A-Z0-9_]*)\s*=",
    re.MULTILINE,
)
# Class members. Two forms: the shorthand method `name(args) {`, with the
# modifiers and TypeScript annotations one may carry, and the arrow property
# `name = (args) =>`. Indentation is required, which is what keeps a top-level
# call or statement out: a class member is never at column 0 in either form.
_METHOD_RE = re.compile(
    r"^[ \t]+(?:(?:public|private|protected)\s+)?"
    r"(?:(?:static|readonly|abstract|override|async|declare|get|set)\s+|\*\s*)*"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*"
    r"(?:"
    r"(?:<[^>(]*>)?\((?P<params>[^)]*)\)\s*(?::[^{;=]+)?\{"
    r"|=\s*(?:async\s+)?\((?P<aparams>[^)]*)\)\s*(?::[^=]+)?=>"
    r")",
    re.MULTILINE,
)
# Words that reach _METHOD_RE's shape without being a member: `if (x) {` and its
# relatives read as a call followed by a block.
_NOT_A_METHOD = frozenset({
    "if", "for", "while", "switch", "catch", "do", "else", "try", "finally",
    "with", "return", "function", "typeof", "instanceof", "new", "delete",
    "void", "await", "yield", "case", "throw", "class", "import", "export",
})
_EXPORT_RE = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(?P<name>\w+)",
    re.MULTILINE,
)


def _regex_parse(content: str, language: str = _LANGUAGE_NAME) -> ParseResult:
    imports: list[ImportInfo] = []
    for m in _IMPORT_RE.finditer(content):
        source = m.group("source")
        names: list[str] = []
        if m.group("default"):
            names.append(m.group("default"))
        if m.group("named"):
            names.extend(n.strip().split(" as ")[0].strip() for n in m.group("named").split(",") if n.strip())
        if m.group("ns"):
            names.append("* as " + m.group("ns"))
        imports.append(
            ImportInfo(
                module=source,
                names=names,
                is_from_import=True,
                is_internal=_is_internal_module(source),
            )
        )
    for m in _REQUIRE_RE.finditer(content):
        source = m.group("source")
        binding = m.group("binding")
        names: list[str] = []
        if binding.startswith("{"):
            names = [n.strip().split(":")[0].strip() for n in binding.strip("{}").split(",") if n.strip()]
        else:
            names = [binding]
        imports.append(
            ImportInfo(
                module=source,
                names=names,
                is_from_import=False,
                is_internal=_is_internal_module(source),
            )
        )

    classes: list[ClassInfo] = []
    for m in _CLASS_RE.finditer(content):
        bases: list[str] = []
        if m.group("ext"):
            bases.append(m.group("ext"))
        if m.group("impl"):
            bases.extend(b.strip() for b in m.group("impl").split(",") if b.strip())
        classes.append(
            ClassInfo(
                name=m.group("name"),
                bases=bases,
                kind="class",
                line_number=content[: m.start()].count("\n") + 1,
            )
        )

    functions: list[FunctionInfo] = []
    for m in _FUNC_RE.finditer(content):
        functions.append(
            FunctionInfo(
                name=m.group("name"),
                is_async=bool(m.group("async")),
                line_number=content[: m.start()].count("\n") + 1,
            )
        )
    for m in _ARROW_RE.finditer(content):
        functions.append(
            FunctionInfo(
                name=m.group("name"),
                is_async=bool(m.group("async")),
                line_number=content[: m.start()].count("\n") + 1,
            )
        )

    # Methods, associated to the nearest preceding class: the same rough
    # association the Java adapter makes. Without this pass a class parsed by
    # the fallback carries no members at all, so snapshot.py records one span
    # for the whole class and an edit to a single method is indistinguishable
    # from an edit to any other.
    if classes:
        by_line = sorted(classes, key=lambda c: c.line_number)
        for m in _METHOD_RE.finditer(content):
            name = m.group("name")
            if name in _NOT_A_METHOD:
                continue
            line_no = content[: m.start()].count("\n") + 1
            owner = None
            for cls in by_line:
                if cls.line_number <= line_no:
                    owner = cls
                else:
                    break
            if owner is None:
                continue
            params_raw = m.group("params")
            if params_raw is None:
                params_raw = m.group("aparams") or ""
            params = [
                ParameterInfo(name=piece.strip().split(":")[0].strip().lstrip("."))
                for piece in params_raw.split(",")
                if piece.strip()
            ]
            owner.methods.append(
                FunctionInfo(
                    name=name,
                    parameters=params,
                    is_async=re.search(r"\basync\b", m.group(0)) is not None,
                    line_number=line_no,
                )
            )

    constants = list({m.group("name") for m in _CONSTANT_RE.finditer(content)})
    exported = list({m.group("name") for m in _EXPORT_RE.finditer(content)})

    return ParseResult(
        file_path="",
        language=language,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=_scan_external_calls(content),
        exported_symbols=exported,
        notes=["parser=regex-fallback"],
    )


# ---------------------------------------------------------------------------


class _JavaScriptAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        _TS_ERROR_HOLDER.pop("last", None)
        result = _ts_parse(content, self.language)
        if result is None:
            result = _regex_parse(content, self.language)
            err = _TS_ERROR_HOLDER.pop("last", None)
            if err is not None:
                result.notes.append(f"tree-sitter raised: {err}")
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        return len(_IMPORT_RE.findall(content)) + len(_REQUIRE_RE.findall(content))

    def strip_comments_and_blanks(self, content: str) -> int:
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
        return extract_c_style_comments(content)


adapter = _JavaScriptAdapter()
