"""
File Classification Module for Deep Dive Analysis.

Classifies Python files based on:
- Lines of code
- Number of dependencies
- Critical patterns (security, authentication, sensitive operations)
- Complexity indicators (state machines, async patterns)
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re

__all__ = [
    "Classification",
    "ClassificationResult",
    "classify_file",
    "classify_from_content",
]

# Classification thresholds
HIGH_LOC_THRESHOLD: int = 300
HIGH_DEPS_THRESHOLD: int = 5
HIGH_COMPLEXITY_PATTERN_THRESHOLD: int = 3
UTILITY_LOC_MAX: int = 100
UTILITY_DEPS_MAX: int = 3
CRITICAL_PATTERN_MIN: int = 3


class Classification(Enum):
    """File classification levels."""

    CRITICAL = "critical"
    HIGH_COMPLEXITY = "high-complexity"
    STANDARD = "standard"
    UTILITY = "utility"


@dataclass
class ClassificationResult:
    """Result of file classification."""

    classification: Classification
    lines_of_code: int
    num_dependencies: int
    critical_patterns_found: list[str]
    complexity_indicators: list[str]
    verification_required: bool
    reasoning: str


# Patterns that indicate critical files (security, authentication, sensitive data)
CRITICAL_PATTERNS: list[str] = [
    r"\bauth",  # auth, authentication, authorize
    r"\btoken\b",
    r"\bjwt\b",
    r"\bsecret\b",
    r"\bcredential",
    r"\bpassword\b",
    r"\bpermission",
    r"\baccess.?control",
    r"\bencrypt",
    r"\bdecrypt",
    r"\bprivate.?key",
    r"\bapi.?key",
    r"\bsession\b",
    r"\boauth",
    r"\bsecurity",
]

# Patterns that indicate high complexity
COMPLEXITY_PATTERNS: list[str] = [
    r"\basync\s+def\b",
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
    r"\bprocess\b",
    r"\bqueue\b",
    r"\bcallback\b",
    r"\bevent.?loop\b",
]


def count_lines(content: str) -> int:
    """Count non-empty, non-comment lines of code."""
    lines = content.split("\n")
    code_lines = 0
    in_docstring = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Track docstrings
        if '"""' in stripped or "'''" in stripped:
            # Count occurrences to handle single-line docstrings
            triple_double = stripped.count('"""')
            triple_single = stripped.count("'''")

            if triple_double == 2 or triple_single == 2:
                # Single-line docstring, skip it
                continue
            elif triple_double == 1 or triple_single == 1:
                in_docstring = not in_docstring
                continue

        if in_docstring:
            continue

        # Skip single-line comments
        if stripped.startswith("#"):
            continue

        code_lines += 1

    return code_lines


def count_imports(content: str) -> int:
    """Count import statements."""
    import_pattern = r"^(?:from\s+\S+\s+)?import\s+"
    return len(re.findall(import_pattern, content, re.MULTILINE))


def find_patterns(content: str, patterns: list[str]) -> list[str]:
    """Find which patterns match in the content."""
    content_lower = content.lower()
    found = []

    for pattern in patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            found.append(pattern)

    return found


def classify_file(file_path: Path) -> ClassificationResult:
    """
    Classify a Python file based on its content.

    Args:
        file_path: Path to the Python file to classify

    Returns:
        ClassificationResult with classification and supporting data
    """
    content = file_path.read_text(encoding="utf-8")
    return classify_from_content(content, str(file_path))


def classify_from_content(content: str, file_name: str = "") -> ClassificationResult:
    """
    Classify based on content string (canonical implementation).

    Args:
        content: Python source code as string
        file_name: Optional filename for context

    Returns:
        ClassificationResult with classification and supporting data
    """
    # Gather metrics
    loc = count_lines(content)
    num_deps = count_imports(content)
    critical_found = find_patterns(content, CRITICAL_PATTERNS)
    complexity_found = find_patterns(content, COMPLEXITY_PATTERNS)

    reasoning_parts: list[str] = []

    # Primary critical patterns that always indicate critical classification
    primary_critical = [r"\bauth", r"\bsecret\b", r"\bcredential", r"\bencrypt"]

    # Classification logic
    if critical_found:
        # Files with critical patterns are always at least high-complexity
        has_primary_critical = any(p in critical_found for p in primary_critical)
        if len(critical_found) >= CRITICAL_PATTERN_MIN or has_primary_critical:
            classification = Classification.CRITICAL
            reasoning_parts.append(f"Critical patterns found: {len(critical_found)} matches")
        else:
            classification = Classification.HIGH_COMPLEXITY
            reasoning_parts.append(f"Some critical patterns: {len(critical_found)}")
    elif (
        loc > HIGH_LOC_THRESHOLD
        or num_deps > HIGH_DEPS_THRESHOLD
        or len(complexity_found) >= HIGH_COMPLEXITY_PATTERN_THRESHOLD
    ):
        classification = Classification.HIGH_COMPLEXITY
        if loc > HIGH_LOC_THRESHOLD:
            reasoning_parts.append(f"High LOC: {loc}")
        if num_deps > HIGH_DEPS_THRESHOLD:
            reasoning_parts.append(f"Many dependencies: {num_deps}")
        if len(complexity_found) >= HIGH_COMPLEXITY_PATTERN_THRESHOLD:
            reasoning_parts.append(f"Complexity patterns: {len(complexity_found)}")
    elif loc < UTILITY_LOC_MAX and num_deps <= UTILITY_DEPS_MAX and not complexity_found:
        classification = Classification.UTILITY
        reasoning_parts.append("Small file with few dependencies")
    else:
        classification = Classification.STANDARD
        reasoning_parts.append("Standard business logic")

    # Determine if verification is required
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
        reasoning="; ".join(reasoning_parts),
    )


if __name__ == "__main__":
    # Quick test with a sample file
    import sys

    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        if test_file.exists():
            result = classify_file(test_file)
            print(f"File: {test_file}")
            print(f"Classification: {result.classification.value}")
            print(f"LOC: {result.lines_of_code}")
            print(f"Dependencies: {result.num_dependencies}")
            print(f"Critical patterns: {len(result.critical_patterns_found)}")
            print(f"Complexity indicators: {len(result.complexity_indicators)}")
            print(f"Verification required: {result.verification_required}")
            print(f"Reasoning: {result.reasoning}")
        else:
            print(f"File not found: {test_file}")
    else:
        print("Usage: python classifier.py <file_path>")
