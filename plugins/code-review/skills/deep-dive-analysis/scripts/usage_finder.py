"""
Usage Finder Module for Deep Dive Analysis.

Finds where symbols are used across the codebase:
- Import statements that reference the symbol
- Direct usages in code
- Inheritance relationships
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "UsageLocation",
    "UsageResult",
    "find_usages_with_grep",
    "find_importing_modules",
    "find_all_usages",
]

# Constants
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB limit for file reading
SUBPROCESS_TIMEOUT_SECONDS: int = 30

logger = logging.getLogger(__name__)


def validate_symbol(symbol: str) -> str:
    """
    Validate that symbol is a safe Python identifier.

    Args:
        symbol: The symbol name to validate

    Returns:
        The validated symbol

    Raises:
        ValueError: If symbol contains unsafe characters
    """
    # Allow valid Python identifiers and dotted names (module.Class)
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_.]*$', symbol):
        raise ValueError(f"Invalid symbol name: {symbol!r}. Must be a valid Python identifier.")
    return symbol


@dataclass
class UsageLocation:
    """A location where a symbol is used."""

    file_path: str
    line_number: int
    line_content: str
    usage_type: str  # "import", "call", "inheritance", "reference"


@dataclass
class UsageResult:
    """Result of searching for symbol usages."""

    symbol: str
    source_file: str
    usages: list[UsageLocation]
    importing_modules: list[str]


def find_usages_with_grep(
    symbol: str,
    search_paths: list[Path],
    exclude_patterns: list[str] | None = None,
) -> list[UsageLocation]:
    """
    Find usages of a symbol using grep/ripgrep.

    Args:
        symbol: The symbol to search for
        search_paths: Paths to search in
        exclude_patterns: Patterns to exclude (e.g., __pycache__, .venv)

    Returns:
        List of UsageLocation objects

    Raises:
        ValueError: If symbol contains invalid characters
    """
    # Validate symbol to prevent command injection
    symbol = validate_symbol(symbol)

    usages = []

    exclude_patterns = exclude_patterns or [
        "__pycache__",
        ".venv",
        "venv",
        ".git",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        "*.pyc",
    ]

    for search_path in search_paths:
        if not search_path.exists():
            continue

        # Build grep command
        # Use ripgrep if available, fall back to grep
        try:
            # Try ripgrep first
            cmd = ["rg", "-n", "--type", "py", symbol, str(search_path)]

            # Add excludes
            for pattern in exclude_patterns:
                cmd.extend(["--glob", f"!{pattern}"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )

            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        # ripgrep format: path:line:content
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            file_path = parts[0]
                            try:
                                line_num = int(parts[1])
                            except ValueError:
                                continue
                            content = parts[2].strip()

                            # Determine usage type
                            usage_type = _classify_usage(content, symbol)

                            usages.append(
                                UsageLocation(
                                    file_path=file_path,
                                    line_number=line_num,
                                    line_content=content,
                                    usage_type=usage_type,
                                )
                            )

        except FileNotFoundError:
            # ripgrep not available, try with grep
            try:
                cmd = [
                    "grep",
                    "-rn",
                    "--include=*.py",
                    symbol,
                    str(search_path),
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT_SECONDS,
                )

                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                file_path = parts[0]
                                try:
                                    line_num = int(parts[1])
                                except ValueError:
                                    continue
                                content = parts[2].strip()

                                usage_type = _classify_usage(content, symbol)

                                usages.append(
                                    UsageLocation(
                                        file_path=file_path,
                                        line_number=line_num,
                                        line_content=content,
                                        usage_type=usage_type,
                                    )
                                )

            except (FileNotFoundError, subprocess.TimeoutExpired):
                # Fallback to Python-based search
                usages.extend(_python_based_search(symbol, search_path, exclude_patterns))

        except subprocess.TimeoutExpired:
            continue

    return usages


def _classify_usage(line: str, symbol: str) -> str:
    """
    Classify the type of usage from the line content.

    Args:
        line: The source code line containing the symbol
        symbol: The symbol being searched for

    Returns:
        Usage type: "import", "inheritance", "call", or "reference"
    """
    stripped = line.strip()

    # Check for import
    if stripped.startswith("from ") or stripped.startswith("import "):
        return "import"

    # Check for inheritance
    if re.search(rf"class\s+\w+\([^)]*{re.escape(symbol)}[^)]*\)", stripped):
        return "inheritance"

    # Check for function call
    if re.search(rf"{re.escape(symbol)}\s*\(", stripped):
        return "call"

    # Default to reference
    return "reference"


def _python_based_search(
    symbol: str,
    search_path: Path,
    exclude_patterns: list[str],
) -> list[UsageLocation]:
    """
    Fallback Python-based file search when grep/ripgrep unavailable.

    Args:
        symbol: The symbol to search for
        search_path: Directory to search in
        exclude_patterns: Patterns to exclude from search

    Returns:
        List of UsageLocation objects found
    """
    usages = []

    def should_exclude(path: Path) -> bool:
        path_str = str(path)
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True
        return False

    for py_file in search_path.rglob("*.py"):
        if should_exclude(py_file):
            continue

        try:
            # Skip files that are too large to prevent memory issues
            if py_file.stat().st_size > MAX_FILE_SIZE_BYTES:
                logger.debug(f"Skipping large file: {py_file}")
                continue

            content = py_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, start=1):
                if symbol in line:
                    usage_type = _classify_usage(line, symbol)
                    usages.append(
                        UsageLocation(
                            file_path=str(py_file),
                            line_number=line_num,
                            line_content=line.strip(),
                            usage_type=usage_type,
                        )
                    )
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Error reading {py_file}: {e}")
            continue

    return usages


def find_importing_modules(
    symbol: str,
    source_module: str,
    search_paths: list[Path],
) -> list[str]:
    """
    Find modules that import a specific symbol.

    Args:
        symbol: The symbol to search for
        source_module: The module where the symbol is defined
        search_paths: Paths to search in

    Returns:
        List of module paths that import the symbol
    """
    importing = []

    # Patterns to match imports
    patterns = [
        rf"from\s+{re.escape(source_module)}\s+import\s+.*\b{re.escape(symbol)}\b",
        rf"from\s+{re.escape(source_module)}\s+import\s+\*",
        rf"import\s+{re.escape(source_module)}",
    ]

    for search_path in search_paths:
        if not search_path.exists():
            continue

        for py_file in search_path.rglob("*.py"):
            # Skip unwanted files
            path_str = str(py_file)
            if any(
                x in path_str
                for x in ["__pycache__", ".venv", "venv", ".git", "node_modules"]
            ):
                continue

            try:
                # Skip large files
                if py_file.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue

                content = py_file.read_text(encoding="utf-8")

                for pattern in patterns:
                    if re.search(pattern, content):
                        # Convert file path to module path
                        rel_path = str(py_file.relative_to(search_path.parent))
                        module_path = rel_path.replace("\\", "/").replace("/", ".")[:-3]
                        if module_path not in importing:
                            importing.append(module_path)
                        break
            except (OSError, UnicodeDecodeError, ValueError) as e:
                logger.debug(f"Error processing {py_file}: {e}")
                continue

    return importing


def find_all_usages(
    symbol: str,
    source_file: Path,
    project_root: Path | None = None,
) -> UsageResult:
    """
    Find all usages of a symbol from a source file.

    Args:
        symbol: The symbol to search for
        source_file: Path to the file where the symbol is defined
        project_root: Root of the project to search (defaults to source_file parent)

    Returns:
        UsageResult with all found usages
    """
    if project_root is None:
        # Try to find project root by looking for common markers
        current = source_file.parent
        while current != current.parent:
            if (current / "pyproject.toml").exists() or (current / ".git").exists():
                project_root = current
                break
            current = current.parent

        if project_root is None:
            project_root = source_file.parent

    # Determine search paths based on project structure
    search_paths = []

    # Common project directories (check for typical layouts)
    for dir_name in [
        "src",
        "lib",
        "app",
        "packages",
        "modules",
        "core",
        "common",
    ]:
        dir_path = project_root / dir_name
        if dir_path.exists():
            search_paths.append(dir_path)

    # If no standard dirs found, search from project root
    if not search_paths:
        search_paths = [project_root]

    # Find usages
    usages = find_usages_with_grep(symbol, search_paths)

    # Filter out the source file itself
    source_str = str(source_file)
    usages = [u for u in usages if not u.file_path.endswith(source_str.split("/")[-1])]

    # Calculate source module for import searching
    try:
        rel_path = source_file.relative_to(project_root)
        source_module = str(rel_path).replace("\\", ".").replace("/", ".")[:-3]
    except ValueError:
        source_module = source_file.stem

    importing = find_importing_modules(symbol, source_module, search_paths)

    return UsageResult(
        symbol=symbol,
        source_file=str(source_file),
        usages=usages,
        importing_modules=importing,
    )


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python usage_finder.py <symbol> [source_file]")
        sys.exit(1)

    symbol = sys.argv[1]
    source_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    project_root = Path(".")

    result = find_all_usages(symbol, source_file, project_root)

    output = {
        "symbol": result.symbol,
        "source_file": result.source_file,
        "usage_count": len(result.usages),
        "usages": [
            {
                "file": u.file_path,
                "line": u.line_number,
                "type": u.usage_type,
                "content": u.line_content[:100],
            }
            for u in result.usages[:20]  # Limit output
        ],
        "importing_modules": result.importing_modules,
    }

    print(json.dumps(output, indent=2))
