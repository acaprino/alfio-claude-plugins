"""Fail if the harness-independent protocol layer leaks harness, vendor, or
transport vocabulary. Stdlib only, runnable from the repo root."""
import re
import sys
from pathlib import Path

PROTOCOL_DIR = Path("plugins/peer-review/protocol")

# Case-insensitive: vendors, models, transports. Case-sensitive: tool names that
# are ordinary words in lowercase. "Read" is deliberately absent: too ambiguous
# for a mechanical check, covered by review instead.
INSENSITIVE = [
    r"\bclaude\b", r"\banthropic\b", r"\bopenai\b", r"\bgpt-?[0-9o]*\b",
    r"\bgemini\b", r"\bcopilot\b", r"\bcodex\b", r"\bmcp\b",
    r"\bchat/completions\b", r"CLAUDE_PLUGIN_ROOT",
]
SENSITIVE = [r"\bBash\b", r"\bGrep\b", r"\bGlob\b", r"\bWebFetch\b", r"\bWebSearch\b"]

def main() -> int:
    failures = []
    for path in sorted(PROTOCOL_DIR.glob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern in INSENSITIVE:
                if re.search(pattern, line, re.IGNORECASE):
                    failures.append(f"{path}:{number}: {pattern}: {line.strip()}")
            for pattern in SENSITIVE:
                if re.search(pattern, line):
                    failures.append(f"{path}:{number}: {pattern}: {line.strip()}")
    if failures:
        print("ontology leak in the protocol layer:")
        print("\n".join(failures))
        return 1
    print(f"protocol layer clean ({len(list(PROTOCOL_DIR.glob('*.md')))} files)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
