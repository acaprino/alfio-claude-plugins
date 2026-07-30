"""
Java language adapter. Tree-sitter is used when available; otherwise a regex
fallback extracts classes, methods, imports, and common external calls.
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


_JAVA_STDLIB_PREFIXES = (
    "java.", "javax.", "jakarta.", "sun.", "org.w3c.", "org.xml.",
)


def _is_internal_import(module: str) -> bool:
    return not module.startswith(_JAVA_STDLIB_PREFIXES) and not module.startswith("org.")


# Heuristics for external calls (work both for tree-sitter and regex paths).
_DB_HINTS = re.compile(
    r"\b(?:Connection|PreparedStatement|Statement|ResultSet|EntityManager|JdbcTemplate|MongoClient|Repository|Session|"
    r"executeQuery|executeUpdate|prepareStatement|createStatement|persist|merge|find|findAll|save|delete)\b"
)
_NET_HINTS = re.compile(
    r"\b(?:HttpClient|HttpRequest|HttpURLConnection|OkHttpClient|WebClient|RestTemplate|"
    r"RestClient|Socket|ServerSocket|URL|URI)\b"
)
_FS_HINTS = re.compile(
    r"\b(?:File|FileInputStream|FileOutputStream|FileReader|FileWriter|Files\.|Paths\.|BufferedReader|BufferedWriter)\b"
)
_MSG_HINTS = re.compile(
    r"\b(?:KafkaProducer|KafkaConsumer|JmsTemplate|RabbitTemplate|MessageProducer|MessageConsumer|"
    r"@KafkaListener|@JmsListener|@RabbitListener)\b"
)
_IPC_HINTS = re.compile(
    r"\b(?:Runtime\.getRuntime\(\)|ProcessBuilder|Process|Thread\.start|ExecutorService|ForkJoinPool)\b"
)


def _scan_external_calls(content: str) -> list[ExternalCallInfo]:
    out: list[ExternalCallInfo] = []
    for i, line in enumerate(content.splitlines(), start=1):
        ctx = line.strip()[:100]
        if _DB_HINTS.search(line):
            out.append(ExternalCallInfo("database", "db-api", i, ctx))
        if _NET_HINTS.search(line):
            out.append(ExternalCallInfo("network", "net-api", i, ctx))
        if _FS_HINTS.search(line):
            out.append(ExternalCallInfo("filesystem", "fs-api", i, ctx))
        if _MSG_HINTS.search(line):
            out.append(ExternalCallInfo("messaging", "msg-api", i, ctx))
        if _IPC_HINTS.search(line):
            out.append(ExternalCallInfo("ipc", "ipc-api", i, ctx))
    return out


# ---------------------------------------------------------------------------
# Tree-sitter extraction.
# ---------------------------------------------------------------------------


_TS_ERROR_HOLDER: dict[str, str] = {}


def _ts_parse(content: str) -> ParseResult | None:
    pair = get_parser("java")
    if pair is None:
        return None
    parser, lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as e:
        # Tree-sitter MAY raise on extreme input (deep recursion, encoding).
        # parse() is contractually non-raising; signal caller to fall back to
        # regex parsing by returning None, and record the error so _JavaAdapter
        # can annotate the result's `notes`.
        _TS_ERROR_HOLDER["last"] = f"{type(e).__name__}: {e}"
        return None

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []  # Java methods only exist inside types.
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def text(node: Any) -> str:
        return node_text(node, src)

    def parse_modifiers(method_or_field: Any) -> tuple[str | None, bool, bool, bool]:
        # Returns (visibility, is_static, is_final, is_abstract).
        visibility = None
        is_static = is_final = is_abstract = False
        mods = method_or_field.child_by_field_name("modifiers")
        if mods is None:
            for child in method_or_field.children:
                if child.type == "modifiers":
                    mods = child
                    break
        if mods is not None:
            for child in mods.children:
                t = child.type
                if t in ("public", "protected", "private"):
                    visibility = t
                elif t == "static":
                    is_static = True
                elif t == "final":
                    is_final = True
                elif t == "abstract":
                    is_abstract = True
        return visibility, is_static, is_final, is_abstract

    def parse_parameters(params_node: Any) -> list[ParameterInfo]:
        params: list[ParameterInfo] = []
        if params_node is None:
            return params
        for child in params_node.children:
            if child.type in ("formal_parameter", "spread_parameter"):
                ann_node = child.child_by_field_name("type")
                name_node = child.child_by_field_name("name")
                params.append(
                    ParameterInfo(
                        name=text(name_node) if name_node else "?",
                        annotation=text(ann_node) if ann_node else None,
                        default=None,
                    )
                )
        return params

    def parse_method(node: Any) -> FunctionInfo:
        name_node = node.child_by_field_name("name")
        ret_node = node.child_by_field_name("type")
        params_node = node.child_by_field_name("parameters")
        visibility, is_static, _is_final, _is_abstract = parse_modifiers(node)
        return FunctionInfo(
            name=text(name_node) if name_node else "?",
            parameters=parse_parameters(params_node),
            return_annotation=text(ret_node) if ret_node else None,
            is_async=False,  # Java has no async keyword - reactive code is by API.
            is_classmethod=False,
            is_staticmethod=is_static,
            is_property=False,
            visibility=visibility,
            docstring=None,
            line_number=node.start_point[0] + 1,
        )

    def parse_class_like(node: Any, kind: str) -> ClassInfo:
        name_node = node.child_by_field_name("name")
        bases: list[str] = []
        superclass = node.child_by_field_name("superclass")
        if superclass is not None:
            bases.append(text(superclass).removeprefix("extends").strip())
        interfaces = node.child_by_field_name("interfaces")
        if interfaces is not None:
            txt = text(interfaces).removeprefix("implements").strip()
            for piece in txt.split(","):
                piece = piece.strip()
                if piece:
                    bases.append(piece)
        # Methods + class variables come from the body.
        methods: list[FunctionInfo] = []
        class_vars: list[str] = []
        body = node.child_by_field_name("body")
        if body is not None:
            for child in body.children:
                if child.type == "method_declaration":
                    methods.append(parse_method(child))
                elif child.type == "constructor_declaration":
                    m = parse_method(child)
                    m.name = m.name or text(name_node)
                    methods.append(m)
                elif child.type == "field_declaration":
                    for sub in child.children:
                        if sub.type == "variable_declarator":
                            n = sub.child_by_field_name("name")
                            if n is not None:
                                fname = text(n)
                                class_vars.append(fname)
                                if fname.isupper():
                                    constants.append(fname)
        visibility, _is_static, _is_final, _is_abstract = parse_modifiers(node)
        return ClassInfo(
            name=text(name_node) if name_node else "?",
            bases=bases,
            methods=methods,
            class_variables=class_vars,
            kind=kind,
            visibility=visibility,
            docstring=None,
            line_number=node.start_point[0] + 1,
        )

    # Walk top-level only for declarations.
    root = tree.root_node
    for child in root.children:
        if child.type == "import_declaration":
            full = text(child).removeprefix("import").strip().rstrip(";").strip()
            is_static = full.startswith("static ")
            if is_static:
                full = full.removeprefix("static").strip()
            module = full.rsplit(".", 1)[0] if "." in full else full
            name = full.rsplit(".", 1)[-1]
            imports.append(
                ImportInfo(
                    module=module,
                    names=[name],
                    is_from_import=True,
                    is_internal=_is_internal_import(module),
                )
            )
        elif child.type == "class_declaration":
            c = parse_class_like(child, "class")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "interface_declaration":
            c = parse_class_like(child, "interface")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "enum_declaration":
            c = parse_class_like(child, "enum")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "record_declaration":
            c = parse_class_like(child, "record")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "annotation_type_declaration":
            c = parse_class_like(child, "annotation")
            classes.append(c)

    return ParseResult(
        file_path="",
        language="java",
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=_scan_external_calls(content),
        exported_symbols=exported,
        notes=["parser=tree-sitter"],
    )


# ---------------------------------------------------------------------------
# Regex fallback.
# ---------------------------------------------------------------------------


_IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;", re.MULTILINE)
_CLASS_RE = re.compile(
    r"^\s*(?P<vis>public\s+|protected\s+|private\s+)?"
    r"(?:abstract\s+|final\s+|static\s+|sealed\s+|non-sealed\s+)*"
    r"(?P<kind>class|interface|enum|record|@interface)\s+(?P<name>\w+)"
    r"(?:\s+extends\s+(?P<ext>[\w<>,\s.]+?))?"
    r"(?:\s+implements\s+(?P<impl>[\w<>,\s.]+?))?"
    r"\s*[\{(]",
    re.MULTILINE,
)
_METHOD_RE = re.compile(
    r"^\s*(?P<vis>public\s+|protected\s+|private\s+)?"
    r"(?P<mods>(?:static\s+|final\s+|abstract\s+|synchronized\s+|default\s+|native\s+)*)"
    r"(?P<ret>[\w<>\[\],?\s.]+?)\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)"
    r"(?:\s+throws\s+[\w,\s.]+)?\s*[\{;]",
    re.MULTILINE,
)
_CONSTANT_RE = re.compile(
    r"^\s*(?:public\s+|protected\s+|private\s+)?static\s+final\s+[\w<>\[\],?\s.]+\s+(?P<name>[A-Z_][A-Z0-9_]*)\s*[=;]",
    re.MULTILINE,
)


def _regex_parse(content: str) -> ParseResult:
    imports: list[ImportInfo] = []
    for m in _IMPORT_RE.finditer(content):
        full = m.group(1)
        module = full.rsplit(".", 1)[0] if "." in full else full
        name = full.rsplit(".", 1)[-1]
        imports.append(
            ImportInfo(
                module=module,
                names=[name],
                is_from_import=True,
                is_internal=_is_internal_import(module),
            )
        )

    classes: list[ClassInfo] = []
    exported: list[str] = []
    for m in _CLASS_RE.finditer(content):
        visibility = (m.group("vis") or "").strip() or None
        kind_raw = m.group("kind")
        kind = {"@interface": "annotation"}.get(kind_raw, kind_raw)
        name = m.group("name")
        bases: list[str] = []
        if m.group("ext"):
            bases.extend(b.strip() for b in m.group("ext").split(",") if b.strip())
        if m.group("impl"):
            bases.extend(b.strip() for b in m.group("impl").split(",") if b.strip())
        cls = ClassInfo(
            name=name,
            bases=bases,
            methods=[],
            class_variables=[],
            kind=kind,
            visibility=visibility,
            line_number=content[: m.start()].count("\n") + 1,
        )
        classes.append(cls)
        if visibility in (None, "public"):
            exported.append(name)

    # Methods (associated to the nearest preceding class - rough but useful).
    if classes:
        for m in _METHOD_RE.finditer(content):
            name = m.group("name")
            # Skip control keywords mis-matched as return-type/name pairs.
            if name in {"if", "for", "while", "switch", "catch", "return", "synchronized"}:
                continue
            visibility = (m.group("vis") or "").strip() or None
            mods = m.group("mods") or ""
            params_raw = (m.group("params") or "").strip()
            params: list[ParameterInfo] = []
            if params_raw:
                for piece in params_raw.split(","):
                    piece = piece.strip()
                    if not piece:
                        continue
                    tokens = piece.split()
                    if len(tokens) >= 2:
                        ann = " ".join(tokens[:-1])
                        pname = tokens[-1].lstrip("...")
                        params.append(ParameterInfo(name=pname, annotation=ann))
                    else:
                        params.append(ParameterInfo(name=piece))
            line_no = content[: m.start()].count("\n") + 1
            method = FunctionInfo(
                name=name,
                parameters=params,
                return_annotation=(m.group("ret") or "").strip() or None,
                is_async=False,
                is_classmethod=False,
                is_staticmethod="static" in mods,
                visibility=visibility,
                line_number=line_no,
            )
            # Attach to last class whose line_number is <= method line.
            owner = None
            for cls in classes:
                if cls.line_number <= line_no:
                    owner = cls
            if owner is not None:
                owner.methods.append(method)

    constants = list({m.group("name") for m in _CONSTANT_RE.finditer(content)})

    return ParseResult(
        file_path="",
        language="java",
        classes=classes,
        functions=[],
        imports=imports,
        constants=constants,
        external_calls=_scan_external_calls(content),
        exported_symbols=exported,
        notes=["parser=regex-fallback"],
    )


# ---------------------------------------------------------------------------


class _JavaAdapter:
    language = "java"

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
        return len(_IMPORT_RE.findall(content))

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
        return extract_c_style_comments(content)


adapter = _JavaAdapter()
