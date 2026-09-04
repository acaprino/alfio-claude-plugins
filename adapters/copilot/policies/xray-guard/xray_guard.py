#!/usr/bin/env python3
"""PreToolUse guard for the codebase-xray agents.

Reads a VS Code agent-hook JSON payload on stdin and prints a permission
decision on stdout. Two independent rules:

  1. Secret protection (always on). Deny any tool call that targets a file
     matching the forbidden-files list: .env, credentials, private keys, and
     the auth-token dotfiles.

  2. Write confinement (opt-in via --confine <prefix>). Deny any file-creating
     or file-editing tool call whose target lies outside the given prefix. The
     worker agents pass `--confine .codebase-xray` so an off-contract write to
     source code fails at the tool layer instead of silently corrupting a
     sibling partition.

Usage in an .agent.md frontmatter, added by hand (nothing generated wires it):

    hooks:
      PreToolUse:
        - type: command
          command: "python policies/write-confinement/xray_guard.py --confine .codebase-xray"

It ships under policies/write-confinement/ of the Copilot package as an opt-in.
It is deliberately not a plugin hook: a plugin-level hook is session-global and
would confine every write in every session, and Copilot CLI does not run plugin
hooks at all (github/copilot-cli#2540).

Fail-open by design. A payload this script cannot parse, an unrecognized tool
name, or an unexpected key layout all resolve to "allow", so a schema change in
VS Code degrades the pipeline to prompt-level enforcement rather than blocking
every tool call. The prompts and the per-agent `tools:` allowlists remain the
primary contract; this hook is defense in depth.

Requires the `chat.useCustomAgentHooks` setting. Python >= 3.10, stdlib only.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import posixpath
import sys

# Path segments that must never be read. This is the precise subset of the
# "Forbidden Files" list in SKILL.md: patterns that cannot plausibly match a
# source file worth analyzing. The broader heuristics from that list
# (`*secret*`, `*credential*`) stay prompt-level on purpose, because a module
# named `secrets_manager.py` is exactly the kind of file the analysis should
# read and document.
FORBIDDEN_GLOBS = (
    ".env",
    ".env.*",
    "*.env",
    "credentials.*",
    "secrets.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    ".npmrc",
    ".pypirc",
    ".netrc",
)

# Directory names that hold secrets by convention. Matched as whole segments.
FORBIDDEN_DIRS = ("secrets", "credentials", ".secrets", ".credentials")

# Tool names that create or modify files. Matched case-insensitively as
# substrings, so both bare ids ("createFile") and namespaced ids
# ("edit/createFile") hit. Deliberately explicit: a tool name that is not on
# this list is treated as non-mutating and skips the confinement check.
WRITE_TOOL_MARKERS = (
    "createfile",
    "createdirectory",
    "editfile",
    "editnotebook",
    "applypatch",
    "inserteditintofile",
    "replacestringinfile",
    "newfile",
    "writefile",
)

# Keys whose values are file paths. Only these are inspected, so free-text
# fields such as "explanation" never trigger a false denial.
PATH_KEYS = (
    "file",
    "filepath",
    "filepaths",
    "files",
    "path",
    "paths",
    "uri",
    "uris",
    "dirpath",
    "directorypath",
    "notebookuri",
    "target",
    "targetfile",
)


def normalize(raw: str) -> str:
    """Return a workspace-relative POSIX path, or "" if raw is not a path."""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    text = raw.strip().replace("\\", "/")
    for scheme in ("file://", "vscode-file://"):
        if text.startswith(scheme):
            text = text[len(scheme):]
    # Windows drive letters arrive as /C:/... after stripping the scheme.
    if len(text) > 2 and text[0] == "/" and text[2] == ":":
        text = text[1:]
    if os.path.isabs(text) or (len(text) > 1 and text[1] == ":"):
        try:
            rel = os.path.relpath(text, os.getcwd()).replace("\\", "/")
        except ValueError:
            # Different drive on Windows. Keep the absolute form; it is
            # outside the workspace by definition.
            return posixpath.normpath(text)
        text = rel
    return posixpath.normpath(text) if text else ""


def collect_paths(node: object, inside_path_key: bool = False) -> list[str]:
    """Walk tool_input and return every value found under a known path key."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            is_path_key = str(key).lower() in PATH_KEYS
            found.extend(collect_paths(value, inside_path_key or is_path_key))
    elif isinstance(node, list):
        for item in node:
            found.extend(collect_paths(item, inside_path_key))
    elif inside_path_key and isinstance(node, str):
        normalized = normalize(node)
        if normalized and normalized != ".":
            found.append(normalized)
    return found


def is_forbidden(path: str) -> bool:
    """True if any path segment names a secret file or a secrets directory."""
    for segment in path.split("/"):
        lowered = segment.lower()
        if lowered in FORBIDDEN_DIRS:
            return True
        for pattern in FORBIDDEN_GLOBS:
            if fnmatch.fnmatch(lowered, pattern):
                return True
    return False


def command_text(tool_input: object) -> str:
    """Extract the shell command from a terminal tool payload."""
    if not isinstance(tool_input, dict):
        return ""
    for key in ("command", "commandLine", "input", "script"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def outside(path: str, prefix: str) -> bool:
    """True if path escapes prefix."""
    if path.startswith("../") or path == "..":
        return True
    return not (path == prefix or path.startswith(prefix + "/"))


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    sys.exit(0)


def allow() -> None:
    json.dump({"continue": True}, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--confine", default="")
    args, _unknown = parser.parse_known_args()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        allow()

    if not isinstance(payload, dict):
        allow()

    event = payload.get("hook_event_name", "PreToolUse")
    if event != "PreToolUse":
        allow()

    tool_name = str(payload.get("tool_name", "")).lower()
    tool_input = payload.get("tool_input", {})
    paths = collect_paths(tool_input)

    # Rule 1: secret protection, every tool, every agent.
    for path in paths:
        if is_forbidden(path):
            deny(
                f"codebase-xray: '{path}' matches the forbidden-files list. "
                "Note the file's existence only; never read or quote its contents."
            )

    command = command_text(tool_input)
    if command:
        for token in command.replace("'", " ").replace('"', " ").split():
            candidate = normalize(token)
            if candidate and candidate != "." and is_forbidden(candidate):
                deny(
                    f"codebase-xray: the command references '{candidate}', which "
                    "matches the forbidden-files list."
                )

    # Rule 2: write confinement, opt-in, file-mutating tools only.
    prefix = args.confine.strip().replace("\\", "/").strip("/")
    if prefix and any(marker in tool_name for marker in WRITE_TOOL_MARKERS):
        for path in paths:
            if outside(path, prefix):
                deny(
                    f"codebase-xray: this agent may only write under '{prefix}/'. "
                    f"Refused a write to '{path}'. Phase output belongs in the "
                    "assigned output directory; source files are the orchestrator's."
                )

    allow()


if __name__ == "__main__":
    main()
