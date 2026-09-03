"""
Structural parser.

This module is a thin dispatcher over per-language adapters in ./languages/.

Supported languages:
    Python, Java, JavaScript, TypeScript (incl. TSX), SQL, PL/SQL, Rust.

Tree-sitter is used when the optional `tree-sitter-language-pack` package is
installed; otherwise a regex-based fallback is used. Python always uses the
stdlib `ast` module.
"""

from __future__ import annotations

from pathlib import Path

from languages import (
    SUPPORTED_EXTENSIONS,
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    ParameterInfo,
    ParseResult,
    detect_language,
    get_adapter,
)

__all__ = [
    "ParameterInfo",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "ExternalCallInfo",
    "ParseResult",
    "parse_file",
]


def parse_file(file_path: Path) -> ParseResult:
    """
    Parse a source file and return its structure.

    Language is detected from the file extension; .sql files are
    disambiguated against PL/SQL by inspecting content.

    Raises ValueError if the file extension is not recognized.
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding="utf-8")
    language = detect_language(file_path, content)
    if language is None:
        raise ValueError(
            f"Unsupported file extension {file_path.suffix!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )
    adapter = get_adapter(language)
    return adapter.parse(content, str(file_path))


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ast_parser.py <file_path>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"File not found: {target}")
        sys.exit(2)

    result = parse_file(target)
    output = {
        "file_path": result.file_path,
        "language": result.language,
        "notes": result.notes,
        "classes": [
            {
                "name": c.name,
                "kind": c.kind,
                "visibility": c.visibility,
                "bases": c.bases,
                "methods": [m.name for m in c.methods],
                "class_variables": c.class_variables,
                "line_number": c.line_number,
            }
            for c in result.classes
        ],
        "functions": [
            {
                "name": f.name,
                "is_async": f.is_async,
                "visibility": f.visibility,
                "parameters": [p.name for p in f.parameters],
                "line_number": f.line_number,
            }
            for f in result.functions
        ],
        "imports": {
            "internal": [i.module for i in result.imports if i.is_internal],
            "external": [i.module for i in result.imports if not i.is_internal],
        },
        "constants": result.constants,
        "external_calls": [
            {"type": c.call_type, "pattern": c.pattern, "line": c.line_number}
            for c in result.external_calls[:10]
        ],
        "exported_symbols": result.exported_symbols,
    }
    print(json.dumps(output, indent=2))
