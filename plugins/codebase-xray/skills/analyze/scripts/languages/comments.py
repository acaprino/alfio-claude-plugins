"""
Per-language comment extraction.

The antirez classification in comment_rewriter.py is language-agnostic - what
varies is how comments are recognized in source. This module exposes one
function per language that returns CommentToken records, plus a tiny
CommentSyntax descriptor used by the regex-based extractor.

State-machine extraction is used (rather than regex alone) because strings and
character literals can contain comment-like sequences (`"// not a comment"`).
For Python we delegate to the stdlib `tokenize` module which already handles
this correctly; for the other languages we implement a small lexer that tracks
string state and skips comment markers inside strings.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CommentToken",
    "CommentSyntax",
    "extract_python_comments",
    "extract_c_style_comments",
    "extract_sql_comments",
    "extract_rust_comments",
]


@dataclass
class CommentToken:
    line_number: int
    column: int
    text: str  # Comment body, stripped of markers
    raw_text: str  # Original text including markers
    is_inline: bool
    # Block-style /* ... */ or Javadoc /** ... */ vs line // or # or --
    is_block: bool = False
    # JSDoc / Javadoc (/** ... */). Always implies is_block=True.
    is_doc_block: bool = False


@dataclass
class CommentSyntax:
    """Describes how comments are written in a language."""

    line_markers: tuple[str, ...]  # e.g. ('#',) or ('//',) or ('--',)
    block_open: str | None = None  # e.g. '/*'
    block_close: str | None = None  # e.g. '*/'
    doc_block_open: str | None = None  # e.g. '/**'
    # Characters that start a string literal. Comments inside strings are
    # NOT comments. Each entry is a (open, close) pair; both can be the same.
    string_delimiters: tuple[tuple[str, str], ...] = (('"', '"'), ("'", "'"))
    # Optional escape character that lets a quote be embedded in a string.
    string_escape: str | None = "\\"


# ---------------------------------------------------------------------------
# Python uses stdlib tokenize.
# ---------------------------------------------------------------------------


def extract_python_comments(source: str) -> list[CommentToken]:
    import tokenize
    from io import StringIO

    tokens_out: list[CommentToken] = []
    try:
        toks = list(tokenize.generate_tokens(StringIO(source).readline))
    except tokenize.TokenError:
        # Best effort - fall back to regex-based # extraction.
        return _extract_with_regex_python_fallback(source)

    lines = source.splitlines()
    for tok in toks:
        if tok.type == tokenize.COMMENT:
            line_num = tok.start[0]
            col = tok.start[1]
            raw = tok.string
            text = raw.lstrip("#").strip()
            line_content = lines[line_num - 1] if 0 < line_num <= len(lines) else ""
            is_inline = col > 0 and line_content[:col].strip() != ""
            tokens_out.append(
                CommentToken(
                    line_number=line_num,
                    column=col,
                    text=text,
                    raw_text=raw,
                    is_inline=is_inline,
                    is_block=False,
                )
            )
    return tokens_out


def _extract_with_regex_python_fallback(source: str) -> list[CommentToken]:
    out: list[CommentToken] = []
    for i, raw_line in enumerate(source.splitlines(), start=1):
        idx = raw_line.find("#")
        if idx >= 0:
            # Naive: ignore strings. Good enough for fallback.
            text = raw_line[idx:].lstrip("#").strip()
            out.append(
                CommentToken(
                    line_number=i,
                    column=idx,
                    text=text,
                    raw_text=raw_line[idx:],
                    is_inline=raw_line[:idx].strip() != "",
                    is_block=False,
                )
            )
    return out


# ---------------------------------------------------------------------------
# C-style (Java, JavaScript, TypeScript): // line comments + /* */ block +
# /** */ doc block, with proper string-state handling.
# ---------------------------------------------------------------------------


_C_STYLE_SYNTAX = CommentSyntax(
    line_markers=("//",),
    block_open="/*",
    block_close="*/",
    doc_block_open="/**",
    string_delimiters=(('"', '"'), ("'", "'"), ("`", "`")),
    string_escape="\\",
)


def extract_c_style_comments(source: str) -> list[CommentToken]:
    return _extract_with_syntax(source, _C_STYLE_SYNTAX)


# ---------------------------------------------------------------------------
# SQL / PL-SQL: -- line comments + /* */ block.
# ---------------------------------------------------------------------------


_SQL_SYNTAX = CommentSyntax(
    line_markers=("--",),
    block_open="/*",
    block_close="*/",
    doc_block_open=None,
    string_delimiters=(("'", "'"),),
    # Standard SQL uses doubled single quote '' for escape, not backslash.
    string_escape=None,
)


def extract_sql_comments(source: str) -> list[CommentToken]:
    return _extract_with_syntax(source, _SQL_SYNTAX)


# ---------------------------------------------------------------------------
# Rust: same C-style lexer, plus post-processing to flag doc comments.
# `///` and `//!` (line) and `/** */` and `/*! */` (block) are rustdoc.
# ---------------------------------------------------------------------------


def extract_rust_comments(source: str) -> list[CommentToken]:
    """
    Extract Rust comments using the C-style lexer, then post-process to
    flag rustdoc tokens: `///` and `//!` for line comments, `/** */` and
    `/*! */` for block comments.

    Note: `/** */` is ALREADY flagged as is_doc_block by _extract_with_syntax
    via the doc_block_open marker. We only need to handle the three
    rust-specific cases: `///`, `//!`, and `/*! */`.
    """
    tokens = _extract_with_syntax(source, _C_STYLE_SYNTAX)
    for tok in tokens:
        raw = tok.raw_text.lstrip()
        if not tok.is_block:
            # Line comment: check for /// or //! markers.
            if raw.startswith("///") or raw.startswith("//!"):
                tok.is_doc_block = True
                # Strip the extra marker char from text.
                if raw.startswith("///"):
                    tok.text = raw[3:].strip()
                else:
                    tok.text = raw[3:].strip()
        else:
            # Block comment: /*! */ is rustdoc inner-doc-block.
            if raw.startswith("/*!"):
                tok.is_doc_block = True
                # Strip /*! and trailing */
                body = raw
                if body.startswith("/*!"):
                    body = body[3:]
                if body.endswith("*/"):
                    body = body[:-2]
                tok.text = body.strip()
    return tokens


# ---------------------------------------------------------------------------
# Generic syntax-driven extractor.
# ---------------------------------------------------------------------------


def _extract_with_syntax(source: str, syntax: CommentSyntax) -> list[CommentToken]:
    """
    Scan the source one char at a time, tracking whether we're inside a
    string, a line comment, or a block comment. Emit CommentTokens when we
    leave a comment state.

    This is intentionally simple. It does NOT understand template literals
    with embedded expressions (`${...}`), heredocs, raw strings, or nested
    block comments. The aim is "good enough for documentation extraction",
    not a full lexer.
    """
    lines = source.splitlines()
    out: list[CommentToken] = []

    i = 0
    n = len(source)
    line_num = 1
    line_start = 0  # index in `source` of start-of-line

    # State flags.
    in_line_comment = False
    in_block_comment = False
    is_doc_block = False
    block_start_line = 0
    # `comment_start_col` covers two states: column of the open marker for a
    # block comment, OR column of the open marker for a line comment.
    comment_start_col = 0
    block_buf: list[str] = []
    # Index in `source` of the start of the current line comment's open marker.
    # Initialized eagerly so a future refactor that opens a line comment via
    # a non-standard path doesn't trip an UnboundLocalError.
    line_start_of_comment = 0

    in_string = False
    string_close: str = ""

    while i < n:
        ch = source[i]
        rest = source[i:]

        # Track newlines for line numbering. Always advance line counters
        # even inside states so we record positions correctly.
        if ch == "\n":
            if in_line_comment:
                # Line comment ends at newline.
                col = comment_start_col
                raw = source[line_start_of_comment:i]
                marker_len = next(
                    (len(m) for m in syntax.line_markers if raw.startswith(m)),
                    0,
                )
                text = raw[marker_len:].strip()
                line_content = lines[line_num - 1] if 0 < line_num <= len(lines) else ""
                is_inline = col > 0 and line_content[:col].strip() != ""
                out.append(
                    CommentToken(
                        line_number=line_num,
                        column=col,
                        text=text,
                        raw_text=raw,
                        is_inline=is_inline,
                        is_block=False,
                    )
                )
                in_line_comment = False
            elif in_block_comment:
                block_buf.append(ch)
            # Strings ending at newline: most languages here allow multiline
            # strings via backtick or are unaffected. Keep state.
            i += 1
            line_num += 1
            line_start = i
            continue

        if in_line_comment:
            i += 1
            continue

        if in_block_comment:
            if syntax.block_close and rest.startswith(syntax.block_close):
                # Emit the block comment. `block_buf[0]` is the open marker
                # (block_open or doc_block_open) by construction (see the
                # state-entry branches below), so block_buf_str already
                # starts with the marker -- no need for prefix gymnastics.
                block_buf_str = "".join(block_buf) + syntax.block_close
                marker_open = syntax.doc_block_open if is_doc_block else syntax.block_open
                # Strip markers from text body.
                body = block_buf_str
                if marker_open and body.startswith(marker_open):
                    body = body[len(marker_open):]
                if syntax.block_close and body.endswith(syntax.block_close):
                    body = body[: -len(syntax.block_close)]
                text = body.strip()
                line_content = (
                    lines[block_start_line - 1] if 0 < block_start_line <= len(lines) else ""
                )
                is_inline = comment_start_col > 0 and line_content[:comment_start_col].strip() != ""
                out.append(
                    CommentToken(
                        line_number=block_start_line,
                        column=comment_start_col,
                        text=text,
                        raw_text=block_buf_str,
                        is_inline=is_inline,
                        is_block=True,
                        is_doc_block=is_doc_block,
                    )
                )
                in_block_comment = False
                is_doc_block = False
                block_buf = []
                i += len(syntax.block_close)
                continue
            block_buf.append(ch)
            i += 1
            continue

        if in_string:
            # Handle escapes.
            if syntax.string_escape and ch == syntax.string_escape and i + 1 < n:
                i += 2
                continue
            if rest.startswith(string_close):
                # SQL convention: doubled-close-char escapes a literal close
                # char inside the string. `'It''s OK'` is one string, not two.
                # When no `string_escape` is set and the next char is also the
                # close, consume both and stay in the string.
                if (
                    syntax.string_escape is None
                    and i + len(string_close) < n
                    and source[i + len(string_close) : i + 2 * len(string_close)] == string_close
                ):
                    i += 2 * len(string_close)
                    continue
                in_string = False
                i += len(string_close)
                continue
            i += 1
            continue

        # Not in any state - look for starts.
        # 1. Block comment / doc block (check doc first since /** is longer).
        if syntax.doc_block_open and rest.startswith(syntax.doc_block_open):
            in_block_comment = True
            is_doc_block = True
            block_start_line = line_num
            comment_start_col = i - line_start
            block_buf = [syntax.doc_block_open]
            i += len(syntax.doc_block_open)
            continue
        if syntax.block_open and rest.startswith(syntax.block_open):
            in_block_comment = True
            is_doc_block = False
            block_start_line = line_num
            comment_start_col = i - line_start
            block_buf = [syntax.block_open]
            i += len(syntax.block_open)
            continue
        # 2. Line comment.
        matched_line_marker = None
        for marker in syntax.line_markers:
            if rest.startswith(marker):
                matched_line_marker = marker
                break
        if matched_line_marker:
            in_line_comment = True
            comment_start_col = i - line_start
            line_start_of_comment = i
            i += len(matched_line_marker)
            continue
        # 3. String start.
        matched_string = None
        for open_, close_ in syntax.string_delimiters:
            if rest.startswith(open_):
                matched_string = (open_, close_)
                break
        if matched_string:
            in_string = True
            string_close = matched_string[1]
            i += len(matched_string[0])
            continue

        i += 1

    # Handle EOF inside a line comment (file ends without newline).
    if in_line_comment:
        col = comment_start_col
        raw = source[line_start_of_comment:n]
        marker_len = next(
            (len(m) for m in syntax.line_markers if raw.startswith(m)),
            0,
        )
        text = raw[marker_len:].strip()
        line_content = lines[line_num - 1] if 0 < line_num <= len(lines) else ""
        is_inline = col > 0 and line_content[:col].strip() != ""
        out.append(
            CommentToken(
                line_number=line_num,
                column=col,
                text=text,
                raw_text=raw,
                is_inline=is_inline,
                is_block=False,
            )
        )

    return out
