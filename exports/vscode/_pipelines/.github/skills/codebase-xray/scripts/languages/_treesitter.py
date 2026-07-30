"""
Optional tree-sitter loader.

Returns a (parser, language) pair or None if tree-sitter or the requested
grammar is unavailable. Adapters call this and fall back to regex parsing
when it returns None.

We prefer `tree-sitter-language-pack` (modern, single dependency, bundles
many grammars) and fall back to per-grammar packages
(`tree-sitter-python`, `tree-sitter-java`, etc.) if the user has installed
those directly.

## Caching

`get_parser` is `@lru_cache`-decorated. **Both success and failure are
cached** for the process lifetime. If you install tree-sitter mid-process
(e.g. from a REPL), call `get_parser.cache_clear()` to drop the negative
entries so the next `get_parser(language)` re-probes the install state.

## Thread-safety

Tree-sitter's C bindings (per all current Python wrappers) are NOT safe for
concurrent `parser.parse(src)` calls from multiple threads. The cache here
returns a SHARED parser instance per language, so callers using
ThreadPoolExecutor over many files will corrupt parse state. Either
serialize calls, or wrap the cache in a `threading.local()` if you must
parallelize. The regex-fallback adapters are already pure-Python and
GIL-safe, which is the recommended path for parallel parsing.
"""

from __future__ import annotations

import functools
from typing import Any

__all__ = ["get_parser", "node_text"]


# Aliases used by tree-sitter-language-pack.
_LANG_PACK_ALIASES = {
    "python": "python",
    "java": "java",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
    "sql": "sql",
    "rust": "rust",
}

# Per-grammar package names for the fallback strategy.
_GRAMMAR_MODULES = {
    "python": "tree_sitter_python",
    "java": "tree_sitter_java",
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "tsx": "tree_sitter_typescript",
    "sql": "tree_sitter_sql",
    "rust": "tree_sitter_rust",
}

# TypeError is included because a version mismatch between `tree-sitter` and a
# grammar package surfaces as one (e.g. `Language(capsule)` rejecting an
# incompatible capsule). Treating it as "unavailable" degrades to the regex
# fallback instead of crashing the whole analysis run.
_LOAD_ERRORS = (ImportError, AttributeError, TypeError, ValueError, LookupError)


@functools.lru_cache(maxsize=None)
def get_parser(language: str) -> tuple[Any, Any] | None:
    """
    Return (parser, language_obj) for the requested language, or None if
    tree-sitter is not installed or the grammar is unavailable.

    `language_obj` may be None when the backing package does not expose a
    usable language handle; callers only need the parser.

    Result is cached. Call `get_parser.cache_clear()` after a mid-process
    install to re-probe.
    """
    pack_name = _LANG_PACK_ALIASES.get(language)
    if pack_name is None:
        return None

    # Strategy 1: tree-sitter-language-pack (preferred).
    #
    # Only `get_parser` is used. The pack's `get_language` returns a plain
    # capsule rather than a `tree_sitter.Language` on newer releases (the
    # package dropped its tree-sitter dependency), so building our own
    # `Parser(get_language(...))` would break there. The parser the pack hands
    # back already carries its language.
    try:
        from tree_sitter_language_pack import get_parser as _pack_get_parser  # type: ignore

        parser = _pack_get_parser(pack_name)
    except _LOAD_ERRORS:
        pass
    else:
        return parser, getattr(parser, "language", None)

    # Strategy 2: individual tree-sitter-<lang> package + tree-sitter core
    # (the >= 0.23 API, where Language() takes the grammar capsule and Parser()
    # takes the Language).
    try:
        from tree_sitter import Language, Parser  # type: ignore

        import_name = _GRAMMAR_MODULES.get(pack_name)
        if import_name is None:
            return None
        mod = __import__(import_name)
        # tree-sitter-typescript exposes both language_typescript and language_tsx.
        if pack_name == "typescript":
            lang_capsule = mod.language_typescript()
        elif pack_name == "tsx":
            lang_capsule = mod.language_tsx()
        else:
            lang_capsule = mod.language()
        lang_obj = Language(lang_capsule)
        parser = Parser(lang_obj)
        return parser, lang_obj
    except _LOAD_ERRORS:
        return None


def node_text(node: Any, source_bytes: bytes) -> str:
    """
    Return the source text covered by a tree-sitter node.

    Returns "" when the node carries out-of-range or missing byte offsets
    (seen on ERROR/MISSING nodes in a partially parsed tree). Callers treat an
    empty name as "nothing extractable here" and skip the node, so an empty
    string is the intended degradation rather than a swallowed bug.
    """
    try:
        return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
    except (AttributeError, TypeError, ValueError):
        return ""
