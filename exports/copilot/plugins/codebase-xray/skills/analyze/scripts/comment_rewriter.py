"""
Comment Rewriter Module.

Analyzes and rewrites code comments following antirez commenting standards:
https://antirez.com/news/124

Comment Types (antirez taxonomy):

GOOD (to keep/enhance):
  1. Function Comments - API docs at function/class top (docstrings, Javadoc,
     JSDoc, SQL header blocks)
  2. Design Comments  - File-level, explain algorithms and design choices
  3. Why Comments     - Explain reasoning, not what the code does
  4. Teacher Comments - Educate about domain knowledge (math, protocols)
  5. Checklist Comments - Remind of coordinated changes elsewhere
  6. Guide Comments   - Lower cognitive load through rhythm and divisions

BAD (to remove/rewrite):
  7. Trivial Comments - Obvious statements (i++; // Increment i)
  8. Debt Comments    - TODO/FIXME that should be resolved or documented
  9. Backup Comments  - Commented-out code (use git history instead)

Multi-language: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust.
Per-language comment extraction is delegated to
languages.<lang>.adapter.extract_comments(). Classification uses regex patterns
that are largely language-agnostic.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from languages import detect_language, get_adapter
from languages.comments import CommentToken

__all__ = [
    "CommentType",
    "CommentClassification",
    "CommentInfo",
    "CommentAnalysis",
    "CommentRewriter",
    "CommentRewriterError",
    "analyze_comments",
    "rewrite_file",
]

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_ISSUES_IN_REPORT = 20
MAX_COMMENTS_PER_SECTION = 10

# Single source of truth: keep in sync with `languages.SUPPORTED_EXTENSIONS`.
from languages import SUPPORTED_EXTENSIONS as _SUPPORTED_EXTENSIONS_MAP

SUPPORTED_SUFFIXES = frozenset(_SUPPORTED_EXTENSIONS_MAP.keys())


class CommentRewriterError(Exception):
    """Base exception for comment rewriter errors."""


class CommentType(Enum):
    FUNCTION = "function"
    DESIGN = "design"
    WHY = "why"
    TEACHER = "teacher"
    CHECKLIST = "checklist"
    GUIDE = "guide"
    TRIVIAL = "trivial"
    DEBT = "debt"
    BACKUP = "backup"
    UNKNOWN = "unknown"


class CommentClassification(Enum):
    KEEP = "keep"
    ENHANCE = "enhance"
    REWRITE = "rewrite"
    DELETE = "delete"


@dataclass
class CommentInfo:
    line_number: int
    column: int
    text: str
    raw_text: str
    is_docstring: bool
    is_inline: bool
    is_block: bool
    is_doc_block: bool
    comment_type: CommentType
    classification: CommentClassification
    reason: str
    suggestion: str | None = None


@dataclass
class CommentAnalysis:
    file_path: str
    language: str
    total_comments: int
    total_lines: int
    comment_ratio: float
    comments: list[CommentInfo] = field(default_factory=list)
    by_type: dict[str, int] = field(default_factory=dict)
    by_classification: dict[str, int] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pattern bank (language-agnostic where possible, language-aware where needed).
# ---------------------------------------------------------------------------

_DEBT_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\bXXX\b", re.IGNORECASE),
    re.compile(r"\bHACK\b", re.IGNORECASE),
    re.compile(r"\bBUG\b", re.IGNORECASE),
    re.compile(r"\bWORKAROUND\b", re.IGNORECASE),
    re.compile(r"\bTEMP\b", re.IGNORECASE),
    re.compile(r"\bTEMPORARY\b", re.IGNORECASE),
]

_CHECKLIST_PATTERNS = [
    re.compile(r"\bif you (?:change|modify|update)\b", re.IGNORECASE),
    re.compile(r"\bremember to\b", re.IGNORECASE),
    re.compile(r"\bdon'?t forget\b", re.IGNORECASE),
    re.compile(r"\balso update\b", re.IGNORECASE),
    re.compile(r"\bmust be kept in sync\b", re.IGNORECASE),
    re.compile(r"\bsee also\b", re.IGNORECASE),
    re.compile(r"\bwhen changing\b", re.IGNORECASE),
]

_WHY_PATTERNS = [
    re.compile(r"\bbecause\b", re.IGNORECASE),
    re.compile(r"\bthe reason\b", re.IGNORECASE),
    re.compile(r"\bwe (?:do|use) this\b", re.IGNORECASE),
    re.compile(r"\bthis is (?:necessary|needed|required)\b", re.IGNORECASE),
    re.compile(r"\bto avoid\b", re.IGNORECASE),
    re.compile(r"\bto prevent\b", re.IGNORECASE),
    re.compile(r"\bworkaround for\b", re.IGNORECASE),
    re.compile(r"\bdue to\b", re.IGNORECASE),
    re.compile(r"\brequired by\b", re.IGNORECASE),
    re.compile(r"\bhistorically\b", re.IGNORECASE),
]

_TEACHER_PATTERNS = [
    re.compile(r"\balgorithm\b", re.IGNORECASE),
    re.compile(r"\bprotocol\b", re.IGNORECASE),
    re.compile(r"\bformula\b", re.IGNORECASE),
    re.compile(r"\bequation\b", re.IGNORECASE),
    re.compile(r"\btheorem\b", re.IGNORECASE),
    re.compile(r"\bRFC\s*\d+\b", re.IGNORECASE),
    re.compile(r"\bsee (?:http|https)://\b", re.IGNORECASE),
    re.compile(r"\brefer to\b", re.IGNORECASE),
    re.compile(r"\bexplained in\b", re.IGNORECASE),
]

_GUIDE_PATTERNS = [
    re.compile(r"^[\s]*[-=]+[\s]*$"),
    re.compile(r"^[\s]*#+ "),
    re.compile(r"^\s*section\s*:?\s*", re.IGNORECASE),
    re.compile(r"^[\s]*[/*]+ "),
]

# Per-language commented-out code patterns.
# The CommentToken.raw_text contains the original markers, so we match on the
# raw_text. Each pattern detects "this comment body looks like real code".
_CODE_PATTERNS_BY_LANG: dict[str, list[re.Pattern[str]]] = {
    "python": [
        re.compile(r"^\s*#\s*(?:def|class|import|from|if|for|while|try|except|with|return|yield|raise|async\s+def)\b", re.IGNORECASE),
        re.compile(r"^\s*#\s*\w+\s*[=(]"),
        re.compile(r"^\s*#\s*\w+(?:\.\w+)+\("),
        re.compile(r"^\s*#\s*@\w+"),
    ],
    "java": [
        re.compile(r"^\s*//\s*(?:public|private|protected|class|interface|enum|return|if|for|while|try|catch|throw|new)\b"),
        re.compile(r"^\s*//\s*\w+\s*[=(]"),
        re.compile(r"^\s*//\s*\w+(?:\.\w+)+\("),
        re.compile(r"^\s*//\s*@\w+"),
    ],
    "javascript": [
        re.compile(r"^\s*//\s*(?:const|let|var|function|class|return|if|for|while|try|catch|throw|new|async\s+function|export|import)\b"),
        re.compile(r"^\s*//\s*\w+\s*[=(]"),
        re.compile(r"^\s*//\s*\w+(?:\.\w+)+\("),
        re.compile(r"^\s*//\s*@\w+"),
    ],
    "typescript": [
        re.compile(r"^\s*//\s*(?:const|let|var|function|class|interface|enum|type|return|if|for|while|try|catch|throw|new|async\s+function|export|import)\b"),
        re.compile(r"^\s*//\s*\w+\s*[=(]"),
        re.compile(r"^\s*//\s*\w+(?:\.\w+)+\("),
        re.compile(r"^\s*//\s*@\w+"),
    ],
    "sql": [
        re.compile(r"^\s*--\s*(?:SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|GRANT|REVOKE|COMMIT|ROLLBACK|CALL)\b", re.IGNORECASE),
    ],
    "plsql": [
        re.compile(r"^\s*--\s*(?:DECLARE|BEGIN|END|EXCEPTION|PROCEDURE|FUNCTION|PACKAGE|TYPE|CURSOR|RETURN|RAISE|IF|FOR|WHILE|LOOP|CALL|EXEC|SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|GRANT|REVOKE|COMMIT|ROLLBACK)\b", re.IGNORECASE),
    ],
    "rust": [
        re.compile(r"^\s*//\s*(?:pub|fn|struct|enum|trait|impl|mod|use|let|const|static|return|if|for|while|match|loop|unsafe|async|await|extern)\b"),
        re.compile(r"^\s*//\s*\w+\s*[=(]"),
        re.compile(r"^\s*//\s*\w+(?:::\w+)+\s*[\(<]"),
        re.compile(r"^\s*//\s*#\["),  # attribute
    ],
}

# Per-language trivial comment indicators: (comment_pattern, code_pattern).
# Matches when the inline comment paraphrases what the same line of code says.
_TRIVIAL_INDICATORS_BY_LANG: dict[str, list[tuple[re.Pattern[str], re.Pattern[str]]]] = {
    "python": [
        (re.compile(r"#\s*increment\b", re.IGNORECASE), re.compile(r"\+\+|\+=\s*1")),
        (re.compile(r"#\s*decrement\b", re.IGNORECASE), re.compile(r"--|-=\s*1")),
        (re.compile(r"#\s*return\b", re.IGNORECASE), re.compile(r"\breturn\b")),
        (re.compile(r"#\s*loop\b", re.IGNORECASE), re.compile(r"\bfor\b|\bwhile\b")),
        (re.compile(r"#\s*import\b", re.IGNORECASE), re.compile(r"\bimport\b")),
        (re.compile(r"#\s*set\s+\w+", re.IGNORECASE), re.compile(r"=")),
        (re.compile(r"#\s*call\s+\w+", re.IGNORECASE), re.compile(r"\(")),
        (re.compile(r"#\s*if\s+\w+", re.IGNORECASE), re.compile(r"\bif\b")),
    ],
    "java": [
        (re.compile(r"//\s*increment\b", re.IGNORECASE), re.compile(r"\+\+|\+=\s*1")),
        (re.compile(r"//\s*decrement\b", re.IGNORECASE), re.compile(r"--|-=\s*1")),
        (re.compile(r"//\s*return\b", re.IGNORECASE), re.compile(r"\breturn\b")),
        (re.compile(r"//\s*loop\b", re.IGNORECASE), re.compile(r"\bfor\b|\bwhile\b")),
        (re.compile(r"//\s*set\s+\w+", re.IGNORECASE), re.compile(r"=")),
        (re.compile(r"//\s*new\b", re.IGNORECASE), re.compile(r"\bnew\b")),
    ],
    "javascript": [
        (re.compile(r"//\s*increment\b", re.IGNORECASE), re.compile(r"\+\+|\+=\s*1")),
        (re.compile(r"//\s*decrement\b", re.IGNORECASE), re.compile(r"--|-=\s*1")),
        (re.compile(r"//\s*return\b", re.IGNORECASE), re.compile(r"\breturn\b")),
        (re.compile(r"//\s*loop\b", re.IGNORECASE), re.compile(r"\bfor\b|\bwhile\b")),
        (re.compile(r"//\s*import\b", re.IGNORECASE), re.compile(r"\bimport\b|\brequire\(")),
    ],
    "typescript": [
        (re.compile(r"//\s*increment\b", re.IGNORECASE), re.compile(r"\+\+|\+=\s*1")),
        (re.compile(r"//\s*decrement\b", re.IGNORECASE), re.compile(r"--|-=\s*1")),
        (re.compile(r"//\s*return\b", re.IGNORECASE), re.compile(r"\breturn\b")),
        (re.compile(r"//\s*loop\b", re.IGNORECASE), re.compile(r"\bfor\b|\bwhile\b")),
        (re.compile(r"//\s*import\b", re.IGNORECASE), re.compile(r"\bimport\b|\brequire\(")),
    ],
    "sql": [
        (re.compile(r"--\s*select\b", re.IGNORECASE), re.compile(r"\bSELECT\b", re.IGNORECASE)),
        (re.compile(r"--\s*insert\b", re.IGNORECASE), re.compile(r"\bINSERT\b", re.IGNORECASE)),
        (re.compile(r"--\s*update\b", re.IGNORECASE), re.compile(r"\bUPDATE\b", re.IGNORECASE)),
        (re.compile(r"--\s*delete\b", re.IGNORECASE), re.compile(r"\bDELETE\b", re.IGNORECASE)),
    ],
    "plsql": [
        (re.compile(r"--\s*begin\b", re.IGNORECASE), re.compile(r"\bBEGIN\b", re.IGNORECASE)),
        (re.compile(r"--\s*end\b", re.IGNORECASE), re.compile(r"\bEND\b", re.IGNORECASE)),
        (re.compile(r"--\s*raise\b", re.IGNORECASE), re.compile(r"\bRAISE\b", re.IGNORECASE)),
    ],
    "rust": [
        (re.compile(r"//\s*increment\b", re.IGNORECASE), re.compile(r"\+\+|\+=\s*1")),
        (re.compile(r"//\s*decrement\b", re.IGNORECASE), re.compile(r"--|-=\s*1")),
        (re.compile(r"//\s*return\b", re.IGNORECASE), re.compile(r"\breturn\b")),
        (re.compile(r"//\s*loop\b", re.IGNORECASE), re.compile(r"\bfor\b|\bwhile\b|\bloop\b")),
        (re.compile(r"//\s*use\b", re.IGNORECASE), re.compile(r"\buse\b")),
        (re.compile(r"//\s*match\b", re.IGNORECASE), re.compile(r"\bmatch\b")),
    ],
}

_DEBT_REMOVAL_PATTERN = re.compile(
    r"\b(?:TODO|FIXME|XXX|HACK|BUG|WORKAROUND|TEMP|TEMPORARY)\b:?\s*",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Validation.
# ---------------------------------------------------------------------------


def _validate_source_file(file_path: Path) -> str:
    """Validate the file and return its detected language."""
    if not file_path.exists():
        raise CommentRewriterError(f"File does not exist: {file_path}")
    if not file_path.is_file():
        raise CommentRewriterError(f"Path is not a file: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise CommentRewriterError(
            f"Unsupported file extension {file_path.suffix!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_SUFFIXES))}"
        )
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise CommentRewriterError(
            f"File too large: {file_size:,} bytes (max {MAX_FILE_SIZE_BYTES:,} bytes)"
        )
    content_for_detect = ""
    try:
        # Read just enough to detect PL/SQL via content. Small read is cheap.
        with file_path.open("rb") as fh:
            content_for_detect = fh.read(16 * 1024).decode("utf-8", errors="ignore")
    except OSError:
        pass
    lang = detect_language(file_path, content_for_detect)
    if lang is None:
        raise CommentRewriterError(f"Could not detect language for: {file_path}")
    return lang


def _read_preserving_newlines(path: Path) -> tuple[str, str, bool]:
    """
    Read a source file without letting Python normalize its line endings.

    Returns (content, newline, ends_with_newline) where `content` uses "\\n"
    throughout (what the analysis code expects) and the other two carry the
    information needed to write the file back in its original shape. Reading
    through `read_text` would collapse CRLF to LF and lose the distinction,
    which is how a rewrite of one comment ends up re-encoding every line of a
    LF file checked out on Windows.
    """
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except UnicodeDecodeError:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            raw = fh.read()

    if "\r\n" in raw:
        newline = "\r\n"
    elif "\r" in raw:
        newline = "\r"
    else:
        newline = "\n"

    content = raw.replace("\r\n", "\n").replace("\r", "\n")
    return content, newline, raw.endswith(("\n", "\r"))


def _write_preserving_newlines(path: Path, text: str, newline: str) -> None:
    """Write `text` (LF-separated) using `newline` verbatim, no translation."""
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text if newline == "\n" else text.replace("\n", newline))


def _validate_output_path(output_path: Path, source_path: Path) -> Path:
    resolved = output_path.resolve()
    if resolved.exists() and not resolved.is_file():
        raise CommentRewriterError(f"Output path exists but is not a file: {resolved}")
    if not resolved.parent.exists():
        raise CommentRewriterError(f"Output directory does not exist: {resolved.parent}")
    return resolved


def _run_formatter(file_path: Path, language: str) -> None:
    """
    Best-effort formatter run after rewriting.

    The executable is resolved with shutil.which so that npm-installed tools
    (prettier, biome) are found through their Windows .cmd shims, which
    subprocess will not locate on its own. A missing formatter is skipped
    silently; one that runs and fails is reported, because a non-zero exit
    means the rewritten file may have been left unformatted or half-written.
    """
    candidates: list[list[str]] = []
    if language == "python":
        candidates = [["ruff", "format", str(file_path)], ["black", "-q", str(file_path)]]
    elif language == "java":
        candidates = [["google-java-format", "-i", str(file_path)]]
    elif language in ("javascript", "typescript"):
        candidates = [["prettier", "--write", str(file_path)], ["biome", "format", "--write", str(file_path)]]
    elif language in ("sql", "plsql"):
        candidates = [["sqlfluff", "fix", "--dialect", "ansi" if language == "sql" else "oracle", str(file_path)]]
    elif language == "rust":
        candidates = [["rustfmt", str(file_path)]]

    for cmd in candidates:
        executable = shutil.which(cmd[0])
        if executable is None:
            continue
        try:
            proc = subprocess.run(
                [executable, *cmd[1:]],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as e:
            logger.warning("Formatter %s could not run on %s: %s", cmd[0], file_path, e)
            return
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            reason = detail[0] if detail else f"exit code {proc.returncode}"
            logger.warning("Formatter %s failed on %s: %s", cmd[0], file_path, reason)
        return


# ---------------------------------------------------------------------------
# Classification.
# ---------------------------------------------------------------------------


def classify_comment(
    token: CommentToken,
    language: str,
    line_content: str | None = None,
) -> tuple[CommentType, CommentClassification, str]:
    """
    Classify a comment according to antirez taxonomy.

    Doc blocks (JSDoc / Javadoc) and Python docstrings are treated as
    "function" comments. SQL header blocks (/* ... */ at file start, or
    long top-level block comments) are treated as "design".
    """
    text = token.text
    raw = token.raw_text
    text_lower = text.lower()

    # Doc blocks (Javadoc /**, JSDoc /**) - treat as function docs.
    if token.is_doc_block:
        if len(text) < 10:
            return (
                CommentType.FUNCTION,
                CommentClassification.ENHANCE,
                "Doc block too brief - needs more detail",
            )
        return (
            CommentType.FUNCTION,
            CommentClassification.KEEP,
            "Doc block provides API documentation",
        )

    # Backup (commented-out code).
    code_patterns = _CODE_PATTERNS_BY_LANG.get(language, [])
    for pattern in code_patterns:
        if pattern.match(raw):
            return (
                CommentType.BACKUP,
                CommentClassification.DELETE,
                "Commented-out code should be removed (use git history)",
            )

    # Debt (TODO/FIXME).
    for pattern in _DEBT_PATTERNS:
        if pattern.search(text):
            return (
                CommentType.DEBT,
                CommentClassification.REWRITE,
                "Debt marker found - resolve or document in design comments",
            )

    # Trivial (inline, restates code).
    if line_content and token.is_inline:
        trivial = _TRIVIAL_INDICATORS_BY_LANG.get(language, [])
        for comment_pat, code_pat in trivial:
            if comment_pat.search(raw):
                if code_pat.search(line_content):
                    return (
                        CommentType.TRIVIAL,
                        CommentClassification.DELETE,
                        "Comment restates what code already says",
                    )

    # Checklist.
    for pattern in _CHECKLIST_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.CHECKLIST,
                CommentClassification.KEEP,
                "Checklist comment - reminds of coordinated changes",
            )

    # Why.
    for pattern in _WHY_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.WHY,
                CommentClassification.KEEP,
                "Why comment - explains reasoning behind code",
            )

    # Teacher.
    for pattern in _TEACHER_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.TEACHER,
                CommentClassification.KEEP,
                "Teacher comment - educates about domain concepts",
            )

    # Guide.
    for pattern in _GUIDE_PATTERNS:
        if pattern.match(text):
            return (
                CommentType.GUIDE,
                CommentClassification.KEEP,
                "Guide comment - provides structure and rhythm",
            )

    # Block comment that wasn't a doc block: candidate design comment.
    if token.is_block and len(text) > 40:
        return (
            CommentType.DESIGN,
            CommentClassification.KEEP,
            "Block comment - likely design/algorithm explanation",
        )

    # Short inline comments are often trivial.
    if token.is_inline and len(text) < 20:
        return (
            CommentType.TRIVIAL,
            CommentClassification.ENHANCE,
            "Short inline comment - consider expanding or removing",
        )

    return (
        CommentType.UNKNOWN,
        CommentClassification.ENHANCE,
        "Cannot classify automatically - human review needed",
    )


def suggest_rewrite(comment: CommentInfo) -> str | None:
    if comment.classification == CommentClassification.DELETE:
        return None
    if comment.comment_type == CommentType.DEBT:
        task_text = _DEBT_REMOVAL_PATTERN.sub("", comment.text)
        return (
            f"DESIGN DECISION: {task_text.strip()}\n"
            f"Context: [Add why this is deferred and conditions for completion]"
        )
    if comment.comment_type == CommentType.TRIVIAL:
        return "WHY: [Explain the reasoning behind this code, not what it does]"
    if comment.comment_type == CommentType.FUNCTION and comment.classification == CommentClassification.ENHANCE:
        return (
            "Brief description of what this does.\n\n"
            "Args:\n  [parameter]: [description]\n"
            "Returns:\n  [description of return value]\n"
            "Raises:\n  [Exception]: [when it is raised]"
        )
    return None


# ---------------------------------------------------------------------------
# Rewriter.
# ---------------------------------------------------------------------------


class CommentRewriter:
    """Analyzes and (optionally) rewrites comments following antirez standards."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def _analyze_impl(
        self,
        content: str,
        file_path: str,
        language: str,
        include_suggestions: bool,
    ) -> CommentAnalysis:
        adapter = get_adapter(language)
        lines = content.splitlines()

        analysis = CommentAnalysis(
            file_path=file_path,
            language=language,
            total_comments=0,
            total_lines=len(lines),
            comment_ratio=0.0,
        )

        for token in adapter.extract_comments(content):
            # Python docstrings are NOT emitted by extract_python_comments
            # (tokenize only yields `#` tokens). They are pulled separately
            # via the AST helper `_add_python_docstrings` later in this
            # method, so the per-token loop never sees docstrings.
            is_docstring = False
            line_content = (
                lines[token.line_number - 1]
                if 0 < token.line_number <= len(lines)
                else ""
            )
            comment_type, classification, reason = classify_comment(
                token=token,
                language=language,
                line_content=line_content,
            )
            info = CommentInfo(
                line_number=token.line_number,
                column=token.column,
                text=token.text,
                raw_text=token.raw_text,
                is_docstring=is_docstring,
                is_inline=token.is_inline,
                is_block=token.is_block,
                is_doc_block=token.is_doc_block,
                comment_type=comment_type,
                classification=classification,
                reason=reason,
            )
            if include_suggestions:
                info.suggestion = suggest_rewrite(info)
            analysis.comments.append(info)

        # Python-specific: pull docstrings from AST as well.
        if language == "python":
            self._add_python_docstrings(content, analysis, include_suggestions)

        analysis.comments.sort(key=lambda c: c.line_number)
        analysis.total_comments = len(analysis.comments)
        if analysis.total_lines > 0:
            analysis.comment_ratio = (analysis.total_comments / analysis.total_lines) * 100
        for c in analysis.comments:
            analysis.by_type[c.comment_type.value] = analysis.by_type.get(c.comment_type.value, 0) + 1
            analysis.by_classification[c.classification.value] = (
                analysis.by_classification.get(c.classification.value, 0) + 1
            )
        for c in analysis.comments:
            if c.classification in (CommentClassification.DELETE, CommentClassification.REWRITE):
                analysis.issues.append(
                    f"Line {c.line_number}: [{c.comment_type.value}] {c.reason}"
                )
        return analysis

    def _add_python_docstrings(
        self,
        content: str,
        analysis: CommentAnalysis,
        include_suggestions: bool,
    ) -> None:
        import ast

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    continue
                line_num = getattr(node, "lineno", 1)
                token = CommentToken(
                    line_number=line_num,
                    column=0,
                    text=docstring,
                    raw_text=f'"""{docstring}"""',
                    is_inline=False,
                    is_block=True,
                    is_doc_block=False,  # Python docstring, not /** */
                )
                # Force classification as a function/design comment.
                comment_type = CommentType.FUNCTION
                classification = (
                    CommentClassification.ENHANCE
                    if len(docstring) < 10
                    else CommentClassification.KEEP
                )
                reason = (
                    "Docstring too brief - needs more detail"
                    if len(docstring) < 10
                    else "Docstring provides API documentation"
                )
                info = CommentInfo(
                    line_number=line_num,
                    column=0,
                    text=docstring,
                    raw_text=token.raw_text,
                    is_docstring=True,
                    is_inline=False,
                    is_block=True,
                    is_doc_block=False,
                    comment_type=comment_type,
                    classification=classification,
                    reason=reason,
                )
                if include_suggestions:
                    info.suggestion = suggest_rewrite(info)
                analysis.comments.append(info)

    def analyze_file(self, file_path: Path) -> CommentAnalysis:
        file_path = Path(file_path).resolve()
        language = _validate_source_file(file_path)
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if self.verbose:
                logger.warning(f"File contains non-UTF8 characters: {file_path}")
        return self._analyze_impl(content, str(file_path), language, include_suggestions=True)

    def analyze_content(
        self,
        content: str,
        file_path: str = "<string>",
        language: str | None = None,
    ) -> CommentAnalysis:
        if language is None:
            language = detect_language(Path(file_path), content)
            if language is None:
                raise CommentRewriterError(
                    "Could not detect language. Pass language= explicitly."
                )
        return self._analyze_impl(content, file_path, language, include_suggestions=True)

    def rewrite_file(
        self,
        file_path: Path,
        output_path: Path | None = None,
        dry_run: bool = True,
    ) -> tuple[str, list[str]]:
        file_path = Path(file_path).resolve()
        language = _validate_source_file(file_path)
        if output_path is not None:
            output_path = _validate_output_path(Path(output_path), file_path)

        content, newline, ends_with_newline = _read_preserving_newlines(file_path)

        lines = content.splitlines()
        analysis = self._analyze_impl(content, str(file_path), language, include_suggestions=True)
        changes: list[str] = []

        lines_to_delete: set[int] = set()
        line_modifications: dict[int, str] = {}

        for comment in analysis.comments:
            # Don't modify docstrings or doc blocks automatically.
            if comment.is_docstring or comment.is_doc_block:
                continue
            line_idx = comment.line_number - 1
            if not (0 <= line_idx < len(lines)):
                continue
            old_line = lines[line_idx]

            if comment.classification == CommentClassification.DELETE:
                if comment.is_inline and not comment.is_block:
                    new_line = old_line[: comment.column].rstrip()
                    if new_line.strip():
                        line_modifications[line_idx] = new_line
                        changes.append(
                            f"Line {comment.line_number}: Removed inline comment: {comment.text[:50]}..."
                        )
                    else:
                        lines_to_delete.add(line_idx)
                        changes.append(
                            f"Line {comment.line_number}: Deleted line (empty after comment removal)"
                        )
                elif not comment.is_block:
                    # Stand-alone line comment.
                    lines_to_delete.add(line_idx)
                    changes.append(
                        f"Line {comment.line_number}: Deleted comment line: {comment.text[:50]}..."
                    )
                # Block comments: do not auto-delete to avoid removing
                # documentation by accident; just flag in changes.
                else:
                    changes.append(
                        f"Line {comment.line_number}: [skipped] Block comment flagged for deletion - requires manual review"
                    )

            elif comment.classification == CommentClassification.REWRITE and comment.suggestion:
                indent = len(old_line) - len(old_line.lstrip())
                indent_str = " " * indent
                marker = _line_marker_for(language)
                suggestion_lines = comment.suggestion.split("\n")
                suggestion_text = "\n".join(
                    f"{indent_str}{marker} {line}" for line in suggestion_lines
                )
                if line_idx not in line_modifications:
                    line_modifications[line_idx] = suggestion_text + "\n" + old_line
                    changes.append(
                        f"Line {comment.line_number}: Suggested rewrite for: {comment.text[:50]}..."
                    )

        for idx, new_content in line_modifications.items():
            if idx not in lines_to_delete:
                lines[idx] = new_content
        for idx in sorted(lines_to_delete, reverse=True):
            if 0 <= idx < len(lines):
                lines.pop(idx)
        rewritten = "\n".join(lines)
        if ends_with_newline:
            rewritten += "\n"

        if not dry_run:
            target = output_path or file_path
            if target.exists():
                backup_path = target.with_suffix(target.suffix + ".tmp")
                try:
                    backup_path.write_bytes(target.read_bytes())
                    _write_preserving_newlines(target, rewritten, newline)
                    backup_path.unlink()
                except Exception:
                    if backup_path.exists():
                        # replace(), not rename(): on Windows rename() onto an
                        # existing target raises FileExistsError, turning a
                        # recoverable write failure into a lost file.
                        backup_path.replace(target)
                    raise
            else:
                _write_preserving_newlines(target, rewritten, newline)
            changes.append(f"Wrote changes to: {target}")
            _run_formatter(target, language)

        return rewritten, changes

    def generate_report(self, analysis: CommentAnalysis) -> str:
        lines = [
            f"# Comment Analysis: {Path(analysis.file_path).name}",
            "",
            f"**File:** `{analysis.file_path}`",
            f"**Language:** {analysis.language}",
            f"**Total Lines:** {analysis.total_lines}",
            f"**Total Comments:** {analysis.total_comments}",
            f"**Comment Ratio:** {analysis.comment_ratio:.1f} per 100 lines",
            "",
            "---",
            "",
            "## Summary by Type",
            "",
        ]
        for type_name, count in sorted(analysis.by_type.items()):
            lines.append(f"- **{type_name}**: {count}")
        lines.extend(["", "## Summary by Classification", ""])
        for class_name, count in sorted(analysis.by_classification.items()):
            icon = {
                "keep": "[OK]",
                "enhance": "[~]",
                "rewrite": "[!]",
                "delete": "[X]",
            }.get(class_name, "[?]")
            lines.append(f"- {icon} **{class_name}**: {count}")
        if analysis.issues:
            lines.extend(["", "## Issues Found", ""])
            for issue in analysis.issues[:MAX_ISSUES_IN_REPORT]:
                lines.append(f"- {issue}")
            if len(analysis.issues) > MAX_ISSUES_IN_REPORT:
                lines.append(f"- ... and {len(analysis.issues) - MAX_ISSUES_IN_REPORT} more")
        lines.extend(["", "---", "", "## Detailed Analysis", ""])
        for classification in CommentClassification:
            class_comments = [c for c in analysis.comments if c.classification == classification]
            if not class_comments:
                continue
            lines.append(f"### {classification.value.upper()} ({len(class_comments)})")
            lines.append("")
            for comment in class_comments[:MAX_COMMENTS_PER_SECTION]:
                type_badge = f"[{comment.comment_type.value}]"
                preview = comment.text[:60] + "..." if len(comment.text) > 60 else comment.text
                lines.append(f"- **Line {comment.line_number}** {type_badge}: `{preview}`")
                lines.append(f"  - Reason: {comment.reason}")
                if comment.suggestion:
                    lines.append(f"  - Suggestion: _{comment.suggestion[:80]}..._")
            if len(class_comments) > MAX_COMMENTS_PER_SECTION:
                lines.append(f"- ... and {len(class_comments) - MAX_COMMENTS_PER_SECTION} more")
            lines.append("")
        lines.extend([
            "---",
            "",
            "_Analysis based on antirez commenting standards: https://antirez.com/news/124_",
        ])
        return "\n".join(lines)


def _line_marker_for(language: str) -> str:
    return {
        "python": "#",
        "java": "//",
        "javascript": "//",
        "typescript": "//",
        "sql": "--",
        "plsql": "--",
        "rust": "//",
    }.get(language, "#")


# ---------------------------------------------------------------------------
# Convenience functions.
# ---------------------------------------------------------------------------


def analyze_comments(file_path: Path) -> CommentAnalysis:
    return CommentRewriter().analyze_file(file_path)


def rewrite_file(
    file_path: Path,
    output_path: Path | None = None,
    dry_run: bool = True,
) -> tuple[str, list[str]]:
    return CommentRewriter().rewrite_file(file_path, output_path, dry_run)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python comment_rewriter.py <file_path>")
        print("")
        print("Analyzes file comments following antirez standards.")
        print("Supports Python, Java, JavaScript, TypeScript, SQL, PL/SQL.")
        sys.exit(1)
    test_file = Path(sys.argv[1])
    try:
        rewriter = CommentRewriter(verbose=True)
        analysis = rewriter.analyze_file(test_file)
        print(rewriter.generate_report(analysis))
    except CommentRewriterError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
