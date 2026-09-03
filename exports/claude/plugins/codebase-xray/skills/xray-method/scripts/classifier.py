"""
File Classification Module.

Classifies source files based on:
- Lines of code (computed by the language adapter, so comment/docstring
  syntax is respected per language)
- Number of dependencies (imports, also via the adapter)
- Critical patterns (security, authentication, sensitive data) - keyword
  patterns are language-agnostic
- Complexity indicators (state machines, async patterns, concurrency
  primitives) - extended with multi-language keywords

Supported languages: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust.

Known limitation: the critical and complexity patterns are matched against raw
file content, so hits inside comments and string literals count the same as
hits in code. A file that only *documents* authentication still classifies as
CRITICAL. This is deliberate. The classification decides how much scrutiny a
file gets, where over-flagging is cheap and under-flagging is not, and
per-language lexing to strip comments and strings would cost far more than the
false positives are worth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from languages import detect_language, get_adapter

__all__ = [
    "Classification",
    "ClassificationResult",
    "classify_file",
    "classify_from_content",
]

# Classification thresholds (tunable). The dependency threshold used to be 5,
# which is fewer imports than an ordinary module carries: it flagged a third of
# a small stdlib tool as high-complexity on import count alone. A file earns
# the label for what it does, not for how many names it pulls in.
HIGH_LOC_THRESHOLD: int = 300
HIGH_DEPS_THRESHOLD: int = 12
HIGH_COMPLEXITY_PATTERN_THRESHOLD: int = 3
UTILITY_LOC_MAX: int = 100
UTILITY_DEPS_MAX: int = 3
CRITICAL_PATTERN_MIN: int = 3


class Classification(Enum):
    CRITICAL = "critical"
    HIGH_COMPLEXITY = "high-complexity"
    STANDARD = "standard"
    UTILITY = "utility"


@dataclass
class ClassificationResult:
    classification: Classification
    lines_of_code: int
    num_dependencies: int
    critical_patterns_found: list[str]
    complexity_indicators: list[str]
    verification_required: bool
    reasoning: str
    language: str | None = None


# Critical patterns (security, authentication, sensitive data). These are
# keyword-based and language-agnostic.
#
# The second element marks a pattern as "primary": strong enough on its own to
# classify the file as CRITICAL, where non-primary patterns only do so once
# CRITICAL_PATTERN_MIN of them match together. Both lists are derived from this
# one spec because classify_from_content tests membership by comparing the
# regex strings, so a second hand-written copy of a primary pattern would stop
# matching the moment either copy was edited.
_CRITICAL_PATTERN_SPEC: tuple[tuple[str, bool], ...] = (
    # auth, authentication, authorize, authenticate. The negative lookahead
    # keeps "author" out: with a bare \bauth, every module with an author
    # line or an "authored_by" field classified as security-critical, which
    # made the triage flag most of a build tool.
    (r"\bauth(?!or)", True),
    (r"\btoken\b", False),
    (r"\bjwt\b", False),
    (r"\bsecret\b", True),
    (r"\bcredential", True),
    (r"\bpassword\b", False),
    (r"\bpermission", False),
    (r"\baccess.?control", False),
    (r"\bencrypt", True),
    (r"\bdecrypt", False),
    (r"\bprivate.?key", False),
    (r"\bapi.?key", False),
    (r"\bsession\b", False),
    (r"\boauth", False),
    (r"\bsecurity", False),
    # SQL injection / sensitive SQL
    (r"\bsql.?injection\b", False),
    (r"\bgrant\s+(?:all|select|insert|update|delete|execute)\b", True),
    (r"\brevoke\s+(?:all|select|insert|update|delete|execute)\b", True),
    (r"\bcreate\s+user\b", True),
    (r"\balter\s+user\b", True),
    (r"\bidentified\s+by\b", True),
)

CRITICAL_PATTERNS: list[str] = [pattern for pattern, _ in _CRITICAL_PATTERN_SPEC]

PRIMARY_CRITICAL_PATTERNS: frozenset[str] = frozenset(
    pattern for pattern, is_primary in _CRITICAL_PATTERN_SPEC if is_primary
)

# Complexity indicators. Common across languages, plus per-language extras.
COMPLEXITY_PATTERNS_BASE: list[str] = [
    r"\basync\b",
    r"\bawait\b",
    r"\bstate\b.*\bmachine\b",
    r"\bfsm\b",
    r"\btransition\b",
    r"\bcircuit.?breaker\b",
    r"\bretry\b",
    r"\bbackoff\b",
    r"\block\b",
    r"\bsemaphore\b",
    r"\bmutex\b",
    r"\bthread\b",
    r"\bqueue\b",
    r"\bcallback\b",
    r"\bevent.?loop\b",
    r"\bprocess\b",
]

# Per-language complexity additions.
COMPLEXITY_PATTERNS_PER_LANG: dict[str, list[str]] = {
    "python": [
        r"\basync\s+def\b",
        r"\basyncio\b",
        r"\bcoroutine\b",
        r"\bthreading\.",
        r"\bmultiprocessing\.",
    ],
    "java": [
        r"\bsynchronized\b",
        r"\bvolatile\b",
        r"\bExecutorService\b",
        r"\bCompletableFuture\b",
        r"\bAtomicReference\b",
        r"\bReentrantLock\b",
        r"\bForkJoinPool\b",
        r"\bThreadLocal\b",
    ],
    "javascript": [
        r"\bPromise\.(?:all|race|allSettled|any)\b",
        r"\bWorker\b",
        r"\bworker_threads\b",
        r"\bMutationObserver\b",
        r"\bAbortController\b",
    ],
    "typescript": [
        r"\bPromise\.(?:all|race|allSettled|any)\b",
        r"\bWorker\b",
        r"\bworker_threads\b",
        r"\bAbortController\b",
        r"\bdiscriminated\s+union\b",
    ],
    "sql": [
        r"\bMERGE\s+INTO\b",
        r"\bWINDOW\s+\w+\s+AS\b",
        r"\bRECURSIVE\b",
        r"\bWITH\s+\w+\s+AS\s+\(",  # CTE
        r"\bOVER\s*\(",
        r"\bSAVEPOINT\b",
        r"\bTRANSACTION\b",
        r"\bDEADLOCK\b",
    ],
    "plsql": [
        r"\bPRAGMA\s+AUTONOMOUS\b",
        r"\bPRAGMA\s+SERIALLY_REUSABLE\b",
        r"\bDBMS_SCHEDULER\b",
        r"\bDBMS_JOB\b",
        r"\bDBMS_LOCK\b",
        r"\bDBMS_PIPE\b",
        r"\bFORALL\b",
        r"\bBULK\s+COLLECT\b",
        r"\bAUTHID\s+CURRENT_USER\b",
    ],
    "rust": [
        r"\basync\s+fn\b",
        r"\bawait\b",
        r"\bunsafe\b",
        r"\bArc<",
        r"\bMutex<",
        r"\bRwLock<",
        r"\bRefCell<",
        r"\bCell<",
        r"\btokio::spawn\b",
        r"\bstd::thread::spawn\b",
        r"\bmpsc::channel\b",
        r"\boneshot::channel\b",
        r"\bbroadcast::channel\b",
        r"\bBox<dyn\s+Future",
        r"\bPin<",
        r"\bSend\s*\+\s*Sync\b",
    ],
}


def find_patterns(content: str, patterns: list[str]) -> list[str]:
    """Return the regex patterns that match in the content."""
    found: list[str] = []
    for pat in patterns:
        if re.search(pat, content, re.IGNORECASE):
            found.append(pat)
    return found


def _complexity_patterns_for(language: str | None) -> list[str]:
    base = list(COMPLEXITY_PATTERNS_BASE)
    if language and language in COMPLEXITY_PATTERNS_PER_LANG:
        base.extend(COMPLEXITY_PATTERNS_PER_LANG[language])
    return base


def classify_file(file_path: Path) -> ClassificationResult:
    """Classify a source file (Python/Java/JS/TS/SQL/PL-SQL)."""
    content = file_path.read_text(encoding="utf-8")
    return classify_from_content(content, str(file_path))


def classify_from_content(content: str, file_name: str = "") -> ClassificationResult:
    """
    Classify based on a content string. The file name's extension is used to
    pick a language adapter; falls back to a Python-like accounting if the
    extension isn't recognized.
    """
    language = detect_language(Path(file_name), content) if file_name else None
    if language is not None:
        adapter = get_adapter(language)
        loc = adapter.strip_comments_and_blanks(content)
        num_deps = adapter.count_imports(content)
    else:
        # Generic fallback: count non-empty lines, no import detection.
        loc = sum(1 for line in content.splitlines() if line.strip())
        num_deps = 0

    critical_found = find_patterns(content, CRITICAL_PATTERNS)
    complexity_found = find_patterns(content, _complexity_patterns_for(language))

    reasoning: list[str] = []

    if critical_found:
        has_primary = any(p in PRIMARY_CRITICAL_PATTERNS for p in critical_found)
        if len(critical_found) >= CRITICAL_PATTERN_MIN or has_primary:
            classification = Classification.CRITICAL
            reasoning.append(f"Critical patterns found: {len(critical_found)} matches")
        else:
            classification = Classification.HIGH_COMPLEXITY
            reasoning.append(f"Some critical patterns: {len(critical_found)}")
    elif (
        loc > HIGH_LOC_THRESHOLD
        or num_deps > HIGH_DEPS_THRESHOLD
        or len(complexity_found) >= HIGH_COMPLEXITY_PATTERN_THRESHOLD
    ):
        classification = Classification.HIGH_COMPLEXITY
        if loc > HIGH_LOC_THRESHOLD:
            reasoning.append(f"High LOC: {loc}")
        if num_deps > HIGH_DEPS_THRESHOLD:
            reasoning.append(f"Many dependencies: {num_deps}")
        if len(complexity_found) >= HIGH_COMPLEXITY_PATTERN_THRESHOLD:
            reasoning.append(f"Complexity patterns: {len(complexity_found)}")
    elif loc < UTILITY_LOC_MAX and num_deps <= UTILITY_DEPS_MAX and not complexity_found:
        classification = Classification.UTILITY
        reasoning.append("Small file with few dependencies")
    else:
        classification = Classification.STANDARD
        reasoning.append("Standard business logic")

    verification_required = classification in (
        Classification.CRITICAL,
        Classification.HIGH_COMPLEXITY,
    )

    return ClassificationResult(
        classification=classification,
        lines_of_code=loc,
        num_dependencies=num_deps,
        critical_patterns_found=critical_found,
        complexity_indicators=complexity_found,
        verification_required=verification_required,
        reasoning="; ".join(reasoning),
        language=language,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python classifier.py <file_path>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"File not found: {target}")
        sys.exit(2)

    result = classify_file(target)
    print(f"File: {target}")
    print(f"Language: {result.language or 'unknown'}")
    print(f"Classification: {result.classification.value}")
    print(f"LOC: {result.lines_of_code}")
    print(f"Dependencies: {result.num_dependencies}")
    print(f"Critical patterns: {len(result.critical_patterns_found)}")
    print(f"Complexity indicators: {len(result.complexity_indicators)}")
    print(f"Verification required: {result.verification_required}")
    print(f"Reasoning: {result.reasoning}")
