"""
Comment Rewriter Module for Deep Dive Analysis.

Analyzes and rewrites code comments following antirez commenting standards:
https://antirez.com/news/124

Comment Types (antirez taxonomy):

GOOD (to keep/enhance):
  1. Function Comments - API docs at function top, treat code as black box
  2. Design Comments  - File-level, explain algorithms and design choices
  3. Why Comments     - Explain reasoning, not what the code does
  4. Teacher Comments - Educate about domain knowledge (math, protocols)
  5. Checklist Comments - Remind of coordinated changes elsewhere
  6. Guide Comments   - Lower cognitive load through rhythm and divisions

BAD (to remove/rewrite):
  7. Trivial Comments - Obvious statements (i++; // Increment i)
  8. Debt Comments    - TODO/FIXME that should be resolved or documented properly
  9. Backup Comments  - Commented-out code (use git history instead)
"""

import ast
import logging
import re
import tokenize
from dataclasses import dataclass, field
from enum import Enum
from io import StringIO
from pathlib import Path

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

# Configuration constants
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_ISSUES_IN_REPORT = 20
MAX_COMMENTS_PER_SECTION = 10


class CommentRewriterError(Exception):
    """Base exception for comment rewriter errors."""

    pass


class CommentType(Enum):
    """Classification of comment types per antirez taxonomy."""

    # Good comment types
    FUNCTION = "function"  # API documentation at function/class top
    DESIGN = "design"  # File-level design explanations
    WHY = "why"  # Explains reasoning behind code
    TEACHER = "teacher"  # Educates about domain concepts
    CHECKLIST = "checklist"  # Reminds of coordinated changes
    GUIDE = "guide"  # Section dividers, rhythm helpers

    # Bad comment types
    TRIVIAL = "trivial"  # Obvious, restates code
    DEBT = "debt"  # TODO/FIXME without action
    BACKUP = "backup"  # Commented-out code

    # Neutral
    UNKNOWN = "unknown"  # Cannot classify


class CommentClassification(Enum):
    """High-level classification for action."""

    KEEP = "keep"  # Good comment, preserve
    ENHANCE = "enhance"  # Good type but could be improved
    REWRITE = "rewrite"  # Bad type, needs rewriting
    DELETE = "delete"  # Should be removed entirely


@dataclass
class CommentInfo:
    """Information about a single comment."""

    line_number: int
    column: int
    text: str
    raw_text: str  # Original text including # or quotes
    is_docstring: bool
    is_inline: bool  # Same line as code
    comment_type: CommentType
    classification: CommentClassification
    reason: str
    suggestion: str | None = None  # Suggested rewrite


@dataclass
class CommentAnalysis:
    """Complete analysis of comments in a file."""

    file_path: str
    total_comments: int
    total_lines: int
    comment_ratio: float  # comments per 100 lines
    comments: list[CommentInfo] = field(default_factory=list)
    by_type: dict[str, int] = field(default_factory=dict)
    by_classification: dict[str, int] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


# Pre-compiled regex patterns for performance (HIGH-6 fix)
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
    re.compile(r"^[\s]*[-=]+[\s]*$"),  # Separator lines (---, ===)
    re.compile(r"^[\s]*#+ "),  # Section headers
    re.compile(r"^\s*section\s*:?\s*", re.IGNORECASE),  # Section markers
    re.compile(r"^[\s]*[/\*]+ "),  # Block comment markers
]

# Patterns indicating backup/commented-out code
_CODE_PATTERNS = [
    re.compile(r"^\s*#\s*(?:def|class|import|from|if|for|while|try|except|with|return|yield|raise)\s+", re.IGNORECASE),
    re.compile(r"^\s*#\s*\w+\s*[=\(]"),  # Variable assignment or function call
    re.compile(r"^\s*#\s*\w+\.\w+\("),  # Method call
    re.compile(r"^\s*#\s*@\w+"),  # Decorator
    re.compile(r"^\s*#\s*\w+:\s*\w+\s*[=,]"),  # Type annotation
]

# Trivial comment indicators (pre-compiled)
_TRIVIAL_INDICATORS = [
    (re.compile(r"#\s*increment\b", re.IGNORECASE), re.compile(r"\+\+|\+=\s*1")),
    (re.compile(r"#\s*decrement\b", re.IGNORECASE), re.compile(r"--|-=\s*1")),
    (re.compile(r"#\s*return\b", re.IGNORECASE), re.compile(r"\breturn\b")),
    (re.compile(r"#\s*loop\b", re.IGNORECASE), re.compile(r"\bfor\b|\bwhile\b")),
    (re.compile(r"#\s*import\b", re.IGNORECASE), re.compile(r"\bimport\b")),
    (re.compile(r"#\s*set\s+\w+", re.IGNORECASE), re.compile(r"=")),
    (re.compile(r"#\s*call\s+\w+", re.IGNORECASE), re.compile(r"\(")),
    (re.compile(r"#\s*if\s+\w+", re.IGNORECASE), re.compile(r"\bif\b")),
]

# Debt pattern for removal in suggestions
_DEBT_REMOVAL_PATTERN = re.compile(r"\b(?:TODO|FIXME|XXX|HACK|BUG|WORKAROUND|TEMP|TEMPORARY)\b:?\s*", re.IGNORECASE)


def _validate_python_file(file_path: Path) -> None:
    """
    Validate that a file is a valid Python file for analysis.

    Args:
        file_path: Path to validate

    Raises:
        CommentRewriterError: If file is invalid
    """
    if not file_path.exists():
        raise CommentRewriterError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise CommentRewriterError(f"Path is not a file: {file_path}")

    if file_path.suffix != ".py":
        raise CommentRewriterError(f"File must be a Python file (.py), got: {file_path.suffix}")

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise CommentRewriterError(
            f"File too large: {file_size:,} bytes (max {MAX_FILE_SIZE_BYTES:,} bytes)"
        )


def _validate_output_path(output_path: Path, source_path: Path) -> Path:
    """
    Validate and resolve output path for file writing.

    Args:
        output_path: Requested output path
        source_path: Original source file path

    Returns:
        Validated and resolved output path

    Raises:
        CommentRewriterError: If output path is invalid
    """
    resolved = output_path.resolve()

    # Prevent overwriting non-files
    if resolved.exists() and not resolved.is_file():
        raise CommentRewriterError(f"Output path exists but is not a file: {resolved}")

    # Ensure parent directory exists
    if not resolved.parent.exists():
        raise CommentRewriterError(f"Output directory does not exist: {resolved.parent}")

    return resolved


def extract_comments(source: str) -> list[tuple[int, int, str, str, bool]]:
    """
    Extract all comments from Python source code.

    Args:
        source: Python source code string

    Returns:
        List of (line_number, column, text, raw_text, is_inline)

    Raises:
        CommentRewriterError: If tokenization fails
    """
    comments = []

    try:
        tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    except tokenize.TokenError as e:
        raise CommentRewriterError(f"Failed to tokenize source: {e}") from e

    lines = source.splitlines()

    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            line_num = tok.start[0]
            col = tok.start[1]
            raw = tok.string
            text = raw.lstrip("#").strip()

            # Check if inline (code before comment on same line)
            is_inline = col > 0 and lines[line_num - 1][:col].strip() != ""

            comments.append((line_num, col, text, raw, is_inline))

    return comments


def extract_docstrings(source: str) -> list[tuple[int, str]]:
    """
    Extract all docstrings from Python source code.

    Args:
        source: Python source code string

    Returns:
        List of (line_number, docstring_text)

    Raises:
        CommentRewriterError: If AST parsing fails
    """
    docstrings = []

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise CommentRewriterError(f"Failed to parse source for docstrings: {e}") from e

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)
            if docstring:
                line_num = node.lineno if hasattr(node, "lineno") else 1
                docstrings.append((line_num, docstring))

    return docstrings


def classify_comment(
    text: str,
    raw_text: str,
    is_inline: bool,
    is_docstring: bool,
    line_content: str | None = None,
) -> tuple[CommentType, CommentClassification, str]:
    """
    Classify a comment according to antirez taxonomy.

    Uses pre-compiled regex patterns for performance.

    Args:
        text: Comment text without # prefix
        raw_text: Original comment text including #
        is_inline: Whether comment is on same line as code
        is_docstring: Whether this is a docstring
        line_content: Full line content for context

    Returns:
        Tuple of (CommentType, CommentClassification, reason)
    """
    text_lower = text.lower()

    # Docstrings are always function comments
    if is_docstring:
        if len(text) < 10:
            return (
                CommentType.FUNCTION,
                CommentClassification.ENHANCE,
                "Docstring too brief - needs more detail",
            )
        return (
            CommentType.FUNCTION,
            CommentClassification.KEEP,
            "Docstring provides API documentation",
        )

    # Check for backup (commented-out code)
    for pattern in _CODE_PATTERNS:
        if pattern.match(raw_text):
            return (
                CommentType.BACKUP,
                CommentClassification.DELETE,
                "Commented-out code should be removed (use git history)",
            )

    # Check for debt comments (TODO/FIXME)
    for pattern in _DEBT_PATTERNS:
        if pattern.search(text):
            return (
                CommentType.DEBT,
                CommentClassification.REWRITE,
                "Debt marker found - resolve or document in design comments",
            )

    # Check for trivial comments (restates code)
    if line_content and is_inline:
        for comment_pattern, code_pattern in _TRIVIAL_INDICATORS:
            if comment_pattern.search(raw_text):
                if code_pattern.search(line_content):
                    return (
                        CommentType.TRIVIAL,
                        CommentClassification.DELETE,
                        "Comment restates what code already says",
                    )

    # Check for checklist comments
    for pattern in _CHECKLIST_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.CHECKLIST,
                CommentClassification.KEEP,
                "Checklist comment - reminds of coordinated changes",
            )

    # Check for why comments
    for pattern in _WHY_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.WHY,
                CommentClassification.KEEP,
                "Why comment - explains reasoning behind code",
            )

    # Check for teacher comments
    for pattern in _TEACHER_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.TEACHER,
                CommentClassification.KEEP,
                "Teacher comment - educates about domain concepts",
            )

    # Check for guide comments (section dividers)
    for pattern in _GUIDE_PATTERNS:
        if pattern.match(text):
            return (
                CommentType.GUIDE,
                CommentClassification.KEEP,
                "Guide comment - provides structure and rhythm",
            )

    # Short inline comments are often trivial
    if is_inline and len(text) < 20:
        return (
            CommentType.TRIVIAL,
            CommentClassification.ENHANCE,
            "Short inline comment - consider expanding or removing",
        )

    # Default to unknown - needs human review
    return (
        CommentType.UNKNOWN,
        CommentClassification.ENHANCE,
        "Cannot classify automatically - human review needed",
    )


def suggest_rewrite(
    comment: CommentInfo,
    context_before: list[str] | None = None,
    context_after: list[str] | None = None,
) -> str | None:
    """
    Suggest a rewrite for a comment based on its classification.

    Args:
        comment: The comment to suggest a rewrite for
        context_before: Lines before the comment (optional)
        context_after: Lines after the comment (optional)

    Returns:
        Suggested rewrite text or None if no suggestion
    """
    if comment.classification == CommentClassification.DELETE:
        return None  # Just delete, no rewrite

    if comment.comment_type == CommentType.DEBT:
        # Suggest converting to design comment or issue
        task_text = _DEBT_REMOVAL_PATTERN.sub("", comment.text)
        return (
            f"# DESIGN DECISION: {task_text.strip()}\n"
            f"# Context: [Add why this is deferred and conditions for completion]"
        )

    if comment.comment_type == CommentType.TRIVIAL:
        # Suggest converting to why comment
        return "# WHY: [Explain the reasoning behind this code, not what it does]"

    if comment.comment_type == CommentType.FUNCTION and comment.classification == CommentClassification.ENHANCE:
        # Suggest expanding docstring
        return (
            '"""[Brief description of what this does]\n\n'
            "Args:\n    [parameter]: [description]\n\n"
            "Returns:\n    [description of return value]\n\n"
            'Raises:\n    [Exception]: [when it is raised]\n"""'
        )

    return None


class CommentRewriter:
    """
    Analyzes and rewrites comments following antirez standards.

    The antirez commenting philosophy emphasizes:
    1. Comments should explain WHY, not WHAT
    2. Function comments serve as inline API documentation
    3. Design comments explain algorithm choices at file level
    4. Never leave commented-out code (use git history)
    5. Resolve or properly document TODO/FIXME items
    6. Avoid trivial comments that restate the code
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def _analyze_comments_impl(
        self,
        content: str,
        file_path: str,
        include_suggestions: bool = True,
    ) -> CommentAnalysis:
        """
        Internal implementation of comment analysis.

        Eliminates code duplication between analyze_file() and analyze_content().

        Args:
            content: Python source code to analyze
            file_path: Path string for reporting
            include_suggestions: Whether to generate rewrite suggestions

        Returns:
            CommentAnalysis with classified comments
        """
        lines = content.splitlines()

        analysis = CommentAnalysis(
            file_path=file_path,
            total_comments=0,
            total_lines=len(lines),
            comment_ratio=0.0,
        )

        # Extract and classify regular comments
        for line_num, col, text, raw_text, is_inline in extract_comments(content):
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            comment_type, classification, reason = classify_comment(
                text=text,
                raw_text=raw_text,
                is_inline=is_inline,
                is_docstring=False,
                line_content=line_content,
            )

            comment = CommentInfo(
                line_number=line_num,
                column=col,
                text=text,
                raw_text=raw_text,
                is_docstring=False,
                is_inline=is_inline,
                comment_type=comment_type,
                classification=classification,
                reason=reason,
            )

            # Get context for suggestion if requested
            if include_suggestions:
                context_before = lines[max(0, line_num - 3) : line_num - 1]
                context_after = lines[line_num : min(len(lines), line_num + 3)]
                comment.suggestion = suggest_rewrite(comment, context_before, context_after)

            analysis.comments.append(comment)

        # Extract and classify docstrings
        for line_num, docstring in extract_docstrings(content):
            comment_type, classification, reason = classify_comment(
                text=docstring,
                raw_text=f'"""{docstring}"""',
                is_inline=False,
                is_docstring=True,
            )

            comment = CommentInfo(
                line_number=line_num,
                column=0,
                text=docstring,
                raw_text=f'"""{docstring}"""',
                is_docstring=True,
                is_inline=False,
                comment_type=comment_type,
                classification=classification,
                reason=reason,
            )

            analysis.comments.append(comment)

        # Sort by line number
        analysis.comments.sort(key=lambda c: c.line_number)

        # Calculate statistics
        analysis.total_comments = len(analysis.comments)
        if analysis.total_lines > 0:
            analysis.comment_ratio = (analysis.total_comments / analysis.total_lines) * 100

        # Count by type and classification
        for comment in analysis.comments:
            type_name = comment.comment_type.value
            class_name = comment.classification.value

            analysis.by_type[type_name] = analysis.by_type.get(type_name, 0) + 1
            analysis.by_classification[class_name] = analysis.by_classification.get(class_name, 0) + 1

        # Generate issues list
        for comment in analysis.comments:
            if comment.classification in (CommentClassification.DELETE, CommentClassification.REWRITE):
                analysis.issues.append(
                    f"Line {comment.line_number}: [{comment.comment_type.value}] {comment.reason}"
                )

        return analysis

    def analyze_file(self, file_path: Path) -> CommentAnalysis:
        """
        Analyze all comments in a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            CommentAnalysis with classified comments

        Raises:
            CommentRewriterError: If file is invalid or cannot be parsed
        """
        file_path = Path(file_path).resolve()

        # Validate file (CRITICAL-1 fix)
        _validate_python_file(file_path)

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with replacement for non-UTF8 files
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if self.verbose:
                logger.warning(f"File contains non-UTF8 characters: {file_path}")

        return self._analyze_comments_impl(content, str(file_path), include_suggestions=True)

    def analyze_content(self, content: str, file_path: str = "<string>") -> CommentAnalysis:
        """
        Analyze comments in a string of Python code.

        Args:
            content: Python source code string
            file_path: Optional path for identification in reports

        Returns:
            CommentAnalysis with classified comments

        Raises:
            CommentRewriterError: If content cannot be parsed
        """
        return self._analyze_comments_impl(content, file_path, include_suggestions=True)

    def rewrite_file(
        self,
        file_path: Path,
        output_path: Path | None = None,
        dry_run: bool = True,
    ) -> tuple[str, list[str]]:
        """
        Rewrite a file's comments following antirez standards.

        Args:
            file_path: Path to the Python file
            output_path: Where to write result (None = modify in place)
            dry_run: If True, just return changes without writing

        Returns:
            Tuple of (rewritten_content, list_of_changes)

        Raises:
            CommentRewriterError: If file is invalid or cannot be written
        """
        file_path = Path(file_path).resolve()

        # Validate input file (CRITICAL-1 fix)
        _validate_python_file(file_path)

        # Validate output path if provided (CRITICAL-2 fix)
        if output_path is not None:
            output_path = _validate_output_path(Path(output_path), file_path)

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="replace")

        lines = content.splitlines()
        original_line_count = len(lines)

        analysis = self._analyze_comments_impl(content, str(file_path), include_suggestions=True)
        changes = []

        # Track lines to delete (as set of indices) for safer deletion
        lines_to_delete: set[int] = set()
        line_modifications: dict[int, str] = {}

        # Process comments (non-docstrings only)
        for comment in analysis.comments:
            if comment.is_docstring:
                continue

            line_idx = comment.line_number - 1
            if not (0 <= line_idx < len(lines)):
                continue

            old_line = lines[line_idx]

            if comment.classification == CommentClassification.DELETE:
                if comment.is_inline:
                    # Remove only the comment part, validate result (HIGH-5 fix)
                    new_line = old_line[: comment.column].rstrip()
                    if new_line.strip():
                        # Line still has code, keep it
                        line_modifications[line_idx] = new_line
                        changes.append(
                            f"Line {comment.line_number}: Removed inline comment: {comment.text[:50]}..."
                        )
                    else:
                        # Line becomes empty after removing comment - mark for deletion
                        lines_to_delete.add(line_idx)
                        changes.append(
                            f"Line {comment.line_number}: Deleted line (empty after comment removal)"
                        )
                else:
                    # Stand-alone comment line - mark for deletion
                    if old_line.strip().startswith("#"):
                        lines_to_delete.add(line_idx)
                        changes.append(
                            f"Line {comment.line_number}: Deleted comment line: {comment.text[:50]}..."
                        )

            elif comment.classification == CommentClassification.REWRITE and comment.suggestion:
                # Add suggestion as additional comment before original
                indent = len(old_line) - len(old_line.lstrip())
                indent_str = " " * indent
                suggestion_lines = comment.suggestion.split("\n")
                suggestion_text = "\n".join(indent_str + line for line in suggestion_lines)

                # Store for insertion (will be handled after deletions)
                if line_idx not in line_modifications:
                    line_modifications[line_idx] = suggestion_text + "\n" + old_line
                    changes.append(
                        f"Line {comment.line_number}: Suggested rewrite for: {comment.text[:50]}..."
                    )

        # Apply modifications and deletions (HIGH-5 fix - safer approach)
        # First, apply modifications
        for idx, new_content in line_modifications.items():
            if idx not in lines_to_delete:
                lines[idx] = new_content

        # Then, delete lines from bottom to top to preserve indices
        for idx in sorted(lines_to_delete, reverse=True):
            if 0 <= idx < len(lines):
                lines.pop(idx)

        rewritten = "\n".join(lines)

        # Write if not dry run (CRITICAL-2 fix - validated path)
        if not dry_run:
            target = output_path or file_path

            # Create backup before overwriting
            if target.exists():
                backup_path = target.with_suffix(target.suffix + ".tmp")
                try:
                    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
                    target.write_text(rewritten, encoding="utf-8")
                    backup_path.unlink()  # Remove backup on success
                except Exception:
                    # Restore from backup on failure
                    if backup_path.exists():
                        backup_path.rename(target)
                    raise
            else:
                target.write_text(rewritten, encoding="utf-8")

            changes.append(f"Wrote changes to: {target}")

        return rewritten, changes

    def generate_report(self, analysis: CommentAnalysis) -> str:
        """Generate a human-readable report of comment analysis."""
        lines = [
            f"# Comment Analysis: {Path(analysis.file_path).name}",
            "",
            f"**File:** `{analysis.file_path}`",
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

        lines.extend([
            "",
            "## Summary by Classification",
            "",
        ])

        for class_name, count in sorted(analysis.by_classification.items()):
            icon = {
                "keep": "[OK]",
                "enhance": "[~]",
                "rewrite": "[!]",
                "delete": "[X]",
            }.get(class_name, "[?]")
            lines.append(f"- {icon} **{class_name}**: {count}")

        if analysis.issues:
            lines.extend([
                "",
                "## Issues Found",
                "",
            ])
            for issue in analysis.issues[:MAX_ISSUES_IN_REPORT]:
                lines.append(f"- {issue}")
            if len(analysis.issues) > MAX_ISSUES_IN_REPORT:
                lines.append(f"- ... and {len(analysis.issues) - MAX_ISSUES_IN_REPORT} more")

        lines.extend([
            "",
            "---",
            "",
            "## Detailed Analysis",
            "",
        ])

        # Group by classification
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


def analyze_comments(file_path: Path) -> CommentAnalysis:
    """
    Convenience function to analyze comments in a file.

    Args:
        file_path: Path to the Python file

    Returns:
        CommentAnalysis with classified comments

    Raises:
        CommentRewriterError: If file is invalid or cannot be parsed
    """
    rewriter = CommentRewriter()
    return rewriter.analyze_file(file_path)


def rewrite_file(
    file_path: Path,
    output_path: Path | None = None,
    dry_run: bool = True,
) -> tuple[str, list[str]]:
    """
    Convenience function to rewrite comments in a file.

    Args:
        file_path: Path to the Python file
        output_path: Where to write result (None = modify in place)
        dry_run: If True, just return changes without writing

    Returns:
        Tuple of (rewritten_content, list_of_changes)

    Raises:
        CommentRewriterError: If file is invalid or cannot be written
    """
    rewriter = CommentRewriter()
    return rewriter.rewrite_file(file_path, output_path, dry_run)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        try:
            rewriter = CommentRewriter(verbose=True)
            analysis = rewriter.analyze_file(test_file)
            print(rewriter.generate_report(analysis))
        except CommentRewriterError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python comment_rewriter.py <file_path>")
        print("")
        print("Analyzes Python file comments following antirez standards.")
        print("See: https://antirez.com/news/124")