"""
Python language adapter. Uses the stdlib `ast` module, so it works without
any external dependency.

This module preserves the original ast_parser.py behavior. The other adapters
provide a similar shape but with less detail (decorators, kw-only args, etc.
are Python-specific).
"""

from __future__ import annotations

import ast
import sys

from .base import (
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken, extract_python_comments

__all__ = ["adapter"]


# ---------------------------------------------------------------------------
# External call detection (preserved from ast_parser.py).
# ---------------------------------------------------------------------------

_DB_METHODS = frozenset([
    "find_one", "find_many", "insert_one", "insert_many",
    "update_one", "update_many", "delete_one", "delete_many",
    "aggregate", "execute", "executemany", "fetchone", "fetchall", "fetchmany",
    "commit", "rollback",
])
_DB_RECEIVERS = frozenset([
    "cursor", "collection", "session", "conn", "connection", "db", "database",
])
_DB_MODULES = frozenset([
    "motor", "beanie", "pymongo", "sqlalchemy", "sqlite3", "psycopg2",
    "asyncpg", "databases", "tortoise", "peewee", "mongoengine",
])
_NETWORK_MODULES = frozenset([
    "aiohttp", "httpx", "requests", "urllib", "urllib3", "grpc",
])
_NETWORK_METHODS = frozenset([
    "get", "post", "put", "delete", "patch", "head", "options", "fetch",
    "request",
])
_NETWORK_CONSTRUCTORS = frozenset([
    "ClientSession", "AsyncClient", "Session", "Client",
])
_FS_METHODS = frozenset([
    "read_text", "write_text", "read_bytes", "write_bytes",
    "mkdir", "rmdir", "unlink", "rename", "replace",
])
_FS_FUNCTIONS = frozenset(["open"])
_FS_MODULES = frozenset(["shutil", "os", "os.path"])
_MSG_METHODS = frozenset([
    "publish", "consume", "subscribe", "basic_publish", "basic_consume",
    "send_message", "receive",
])
_MSG_MODULES = frozenset([
    "kafka", "redis", "celery", "kombu", "pika", "aio_pika", "nats",
])
_IPC_MODULES = frozenset([
    "subprocess", "multiprocessing", "mmap",
])
_IPC_CONSTRUCTORS = frozenset([
    "Popen", "Process", "Pool",
])


def _build_external_prefixes() -> frozenset[str]:
    """
    Build the "treat as external" prefix set from the stdlib plus a curated
    list of common third-party packages. `sys.stdlib_module_names` is Python
    3.10+ and covers every stdlib module name exhaustively, which fixes the
    historical false-positive on `argparse`, `enum`, `sys`, etc.
    """
    stdlib = sys.stdlib_module_names
    third_party = frozenset({
        "pytest", "mock", "requests", "aiohttp", "httpx",
        "pydantic", "sqlalchemy", "django", "flask", "fastapi", "celery",
        "redis", "kafka", "boto3", "numpy", "pandas", "scipy",
    })
    return frozenset(stdlib) | third_party


_COMMON_EXTERNAL_PREFIXES = _build_external_prefixes()


def _annotation_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "?"


def _default_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "..."


def _extract_docstring(node) -> str | None:
    if (
        getattr(node, "body", None)
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value.strip()
    return None


def _decorators(node) -> tuple[bool, bool, bool]:
    is_cm = is_sm = is_prop = False
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            if d.id == "classmethod":
                is_cm = True
            elif d.id == "staticmethod":
                is_sm = True
            elif d.id == "property":
                is_prop = True
    return is_cm, is_sm, is_prop


def _parse_function(node) -> FunctionInfo:
    params: list[ParameterInfo] = []
    args = node.args
    num_defaults = len(args.defaults)
    num_args = len(args.args)
    non_default_args = num_args - num_defaults
    for i, arg in enumerate(args.args):
        default = None
        if i >= non_default_args:
            default = _default_str(args.defaults[i - non_default_args])
        params.append(
            ParameterInfo(
                name=arg.arg,
                annotation=_annotation_str(arg.annotation),
                default=default,
            )
        )
    for i, arg in enumerate(args.kwonlyargs):
        default = None
        if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
            default = _default_str(args.kw_defaults[i])
        params.append(
            ParameterInfo(
                name=arg.arg,
                annotation=_annotation_str(arg.annotation),
                default=default,
            )
        )
    is_cm, is_sm, is_prop = _decorators(node)
    return FunctionInfo(
        name=node.name,
        parameters=params,
        return_annotation=_annotation_str(node.returns),
        is_async=isinstance(node, ast.AsyncFunctionDef),
        is_classmethod=is_cm,
        is_staticmethod=is_sm,
        is_property=is_prop,
        visibility="private" if node.name.startswith("_") and not node.name.startswith("__") else "public",
        docstring=_extract_docstring(node),
        line_number=node.lineno,
    )


def _parse_class(node: ast.ClassDef) -> ClassInfo:
    bases: list[str] = []
    for base in node.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            bases.append("?")
    methods: list[FunctionInfo] = []
    class_vars: list[str] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_parse_function(item))
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            class_vars.append(item.target.id)
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    class_vars.append(target.id)
    return ClassInfo(
        name=node.name,
        bases=bases,
        methods=methods,
        class_variables=class_vars,
        kind="class",
        visibility="private" if node.name.startswith("_") else "public",
        docstring=_extract_docstring(node),
        line_number=node.lineno,
    )


def _is_likely_internal(module: str) -> bool:
    if not module:
        return False
    top = module.split(".")[0]
    if top.startswith("_"):
        return True
    if top.lower() in _COMMON_EXTERNAL_PREFIXES:
        return False
    if module.startswith("."):
        return True
    return True


def _parse_imports(tree: ast.Module) -> list[ImportInfo]:
    imports: list[ImportInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportInfo(
                        module=alias.name,
                        names=[alias.asname or alias.name],
                        is_from_import=False,
                        is_internal=_is_likely_internal(alias.name),
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            imports.append(
                ImportInfo(
                    module=module,
                    names=names,
                    is_from_import=True,
                    is_internal=_is_likely_internal(module),
                )
            )
    return imports


class _CallVisitor(ast.NodeVisitor):
    def __init__(self, lines: list[str]) -> None:
        self.calls: list[ExternalCallInfo] = []
        self.lines = lines

    def _context(self, lineno: int) -> str:
        if 0 < lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()[:100]
        return ""

    def _parts(self, node: ast.Call) -> tuple[str | None, str | None]:
        func = node.func
        if isinstance(func, ast.Attribute):
            method = func.attr
            if isinstance(func.value, ast.Name):
                return func.value.id, method
            if isinstance(func.value, ast.Attribute):
                try:
                    return ast.unparse(func.value), method
                except Exception:
                    return None, method
            return None, method
        if isinstance(func, ast.Name):
            return None, func.id
        return None, None

    def _classify(self, receiver: str | None, method: str) -> str | None:
        if method in _DB_METHODS:
            if receiver and (receiver in _DB_RECEIVERS or receiver.split(".")[0] in _DB_MODULES):
                return "database"
            if receiver is None:
                return None
            return "database" if receiver in _DB_RECEIVERS else None
        if receiver and receiver.split(".")[0] in _DB_MODULES:
            return "database"
        if receiver and receiver.split(".")[0] in _NETWORK_MODULES:
            return "network"
        if method in _NETWORK_CONSTRUCTORS:
            return "network"
        if method in _NETWORK_METHODS and receiver and receiver.split(".")[0] in _NETWORK_MODULES:
            return "network"
        if method in _FS_FUNCTIONS or method in _FS_METHODS:
            return "filesystem"
        if receiver and receiver.split(".")[0] in _FS_MODULES:
            return "filesystem"
        if method in _MSG_METHODS:
            if receiver and receiver.split(".")[0] in _MSG_MODULES:
                return "messaging"
            return (
                "messaging"
                if receiver
                and any(kw in receiver.lower() for kw in ("channel", "queue", "topic", "producer", "consumer"))
                else None
            )
        if receiver and receiver.split(".")[0] in _MSG_MODULES:
            return "messaging"
        if receiver and receiver.split(".")[0] in _IPC_MODULES:
            return "ipc"
        if method in _IPC_CONSTRUCTORS:
            return "ipc"
        return None

    def visit_Call(self, node: ast.Call) -> None:
        receiver, method = self._parts(node)
        if method is not None:
            call_type = self._classify(receiver, method)
            if call_type:
                pattern = f"{receiver}.{method}" if receiver else method
                self.calls.append(
                    ExternalCallInfo(
                        call_type=call_type,  # type: ignore[arg-type]
                        pattern=pattern,
                        line_number=node.lineno,
                        context=self._context(node.lineno),
                    )
                )
        self.generic_visit(node)


def _find_constants(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    out.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper():
                out.append(node.target.id)
    return out


def _find_exported(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            out.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                out.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    out.append(target.id)
    return out


class _PythonAdapter:
    language = "python"

    def parse(self, content: str, file_path: str) -> ParseResult:
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return ParseResult(
                file_path=file_path,
                language=self.language,
                notes=[f"syntax error: {e.msg} at line {e.lineno}"],
            )

        classes: list[ClassInfo] = []
        functions: list[FunctionInfo] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(_parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(_parse_function(node))

        visitor = _CallVisitor(content.split("\n"))
        visitor.visit(tree)

        return ParseResult(
            file_path=file_path,
            language=self.language,
            classes=classes,
            functions=functions,
            imports=_parse_imports(tree),
            constants=_find_constants(tree),
            external_calls=visitor.calls,
            exported_symbols=_find_exported(tree),
            notes=["parser=stdlib-ast"],
        )

    def count_imports(self, content: str) -> int:
        import re
        return len(re.findall(r"^(?:from\s+\S+\s+)?import\s+", content, re.MULTILINE))

    def strip_comments_and_blanks(self, content: str) -> int:
        # Mirror the original count_lines: count non-empty, non-comment lines,
        # skipping docstrings.
        lines = content.split("\n")
        code = 0
        in_doc = False
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if '"""' in line or "'''" in line:
                td = line.count('"""')
                ts = line.count("'''")
                if td == 2 or ts == 2:
                    continue
                if td == 1 or ts == 1:
                    in_doc = not in_doc
                    continue
            if in_doc:
                continue
            if line.startswith("#"):
                continue
            code += 1
        return code

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_python_comments(content)


adapter = _PythonAdapter()
