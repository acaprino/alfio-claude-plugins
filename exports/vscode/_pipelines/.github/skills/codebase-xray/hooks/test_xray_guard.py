#!/usr/bin/env python3
"""Test suite for xray_guard.py.

Run it after any change to the guard, to the forbidden-files list, or to the
`--confine` values in the agent frontmatter:

    python .github/skills/codebase-xray/hooks/test_xray_guard.py

Exits 0 when every case passes, 1 otherwise. Stdlib only, no test runner.

The guard resolves paths relative to the working directory, so every case runs
with cwd set to a throwaway temp directory. That keeps the results identical
whether you run this from the repo root, from the bundle, or from CI.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xray_guard.py")
WORKSPACE = tempfile.mkdtemp(prefix="xray-guard-test-")


def run(payload, confine=None):
    cmd = [sys.executable, GUARD]
    if confine:
        cmd += ["--confine", confine]
    body = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(cmd, input=body, capture_output=True, text=True, cwd=WORKSPACE)
    if proc.returncode != 0:
        return "ERROR(rc=%d) %s" % (proc.returncode, proc.stderr.strip()[:160])
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return "BADJSON %r" % proc.stdout[:160]
    hso = out.get("hookSpecificOutput")
    if hso:
        return hso["permissionDecision"]
    return "allow" if out.get("continue") else "?"


def pre(tool, tool_input):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
        "cwd": WORKSPACE,
    }


CASES = [
    # --- X-ray workers: confined to .deep-dive ---
    ("worker writes owned phase file",
     pre("edit/createFile", {"filePath": ".deep-dive/runs/r1/partitions/api/01-structure.md"}),
     ".deep-dive", "allow"),
    ("worker creates run subdir",
     pre("edit/createDirectory", {"dirPath": ".deep-dive/runs/r1/partitions/web"}),
     ".deep-dive", "allow"),
    ("worker writes source file",
     pre("edit/createFile", {"filePath": "src/main.py"}), ".deep-dive", "deny"),
    ("worker edits source file",
     pre("edit/editFiles", {"filePath": "src/auth/login.ts", "explanation": "fix"}),
     ".deep-dive", "deny"),
    ("worker reads source file",
     pre("read/readFile", {"filePath": "src/main.py"}), ".deep-dive", "allow"),

    # --- secret protection ---
    ("reads .env", pre("read/readFile", {"filePath": "src/.env"}), ".deep-dive", "deny"),
    ("reads .env.production",
     pre("read/readFile", {"filePath": ".env.production"}), ".deep-dive", "deny"),
    ("reads a private key",
     pre("read/readFile", {"filePath": "deploy/certs/server.pem"}), ".deep-dive", "deny"),
    ("reads id_rsa",
     pre("read/readFile", {"filePath": "infra/keys/id_rsa"}), ".deep-dive", "deny"),
    ("reads .netrc", pre("read/readFile", {"filePath": ".netrc"}), ".deep-dive", "deny"),
    ("reads a file inside a secrets dir",
     pre("read/readFile", {"filePath": "config/secrets/db.yaml"}), ".deep-dive", "deny"),
    ("reads secrets.yaml",
     pre("read/readFile", {"filePath": "config/secrets.yaml"}), ".deep-dive", "deny"),
    ("reads a source module named secrets_manager.py",
     pre("read/readFile", {"filePath": "src/auth/secrets_manager.py"}), ".deep-dive", "allow"),
    ("reads a source module named credential_store.ts",
     pre("read/readFile", {"filePath": "src/credential_store.ts"}), ".deep-dive", "allow"),
    ("reads keyboard.py, not a *.key match",
     pre("read/readFile", {"filePath": "src/ui/keyboard.py"}), ".deep-dive", "allow"),

    # --- orchestrators: no confine, secrets still denied ---
    ("orchestrator writes a source file",
     pre("edit/editFiles", {"filePath": "src/main.py"}), None, "allow"),
    ("orchestrator reads .env", pre("read/readFile", {"filePath": ".env"}), None, "deny"),

    # --- terminal commands ---
    ("terminal runs an analysis script on source",
     pre("execute/runInTerminal",
         {"command": 'python ".github/skills/codebase-xray/scripts/ast_parser.py" src/main.py'}),
     ".deep-dive", "allow"),
    ("terminal cats .env",
     pre("execute/runInTerminal", {"command": "cat ./.env"}), ".deep-dive", "deny"),

    # --- path edge cases ---
    ("path traversal out of the confine",
     pre("edit/createFile", {"filePath": ".deep-dive/../src/evil.py"}), ".deep-dive", "deny"),
    ("absolute path inside the confine",
     pre("edit/createFile",
         {"filePath": os.path.join(WORKSPACE, ".deep-dive", "runs", "r1", "state.json")}),
     ".deep-dive", "allow"),
    ("absolute path outside the workspace",
     pre("edit/createFile", {"filePath": os.path.join(WORKSPACE, "..", "elsewhere.md")}),
     ".deep-dive", "deny"),
    ("multi-file payload with one bad target",
     pre("edit/editFiles",
         {"filePaths": [".deep-dive/runs/r1/07-final-report.md", "README.md"]}),
     ".deep-dive", "deny"),
    ("free-text field naming a source path is not a target",
     pre("edit/createFile",
         {"filePath": ".deep-dive/runs/r1/05-risks.md",
          "explanation": "documents src/auth/login.py and .env handling"}),
     ".deep-dive", "allow"),
    ("non-mutating search tool outside the confine",
     pre("search/textSearch", {"query": "TODO", "path": "src/"}), ".deep-dive", "allow"),

    # --- review pipeline: confined to .team-review ---
    ("reviewer writes its findings file",
     pre("edit/createFile", {"filePath": ".team-review/findings-security.md"}),
     ".team-review", "allow"),
    ("reviewer writes into .deep-dive, not its session",
     pre("edit/createFile", {"filePath": ".deep-dive/runs/r1/01-structure.md"}),
     ".team-review", "deny"),
    ("reviewer patches the source it is reviewing",
     pre("edit/editFiles", {"filePath": "src/auth/login.py"}), ".team-review", "deny"),
    ("reviewer reads the interconnect map",
     pre("read/readFile", {"filePath": ".team-review/02-interconnect.md"}),
     ".team-review", "allow"),
    ("reviewer reads the X-ray run output",
     pre("read/readFile", {"filePath": ".deep-dive/runs/r1/05-risks.md"}),
     ".team-review", "allow"),
    ("verification lens reads freely",
     pre("read/readFile", {"filePath": "src/payments/refund.ts"}), None, "allow"),
    ("verification lens still cannot read .env",
     pre("read/readFile", {"filePath": "services/api/.env"}), None, "deny"),

    # --- fail-open behavior ---
    ("malformed json fails open", "{not json", ".deep-dive", "allow"),
    ("empty payload fails open", "{}", ".deep-dive", "allow"),
    ("non-PreToolUse event passes through",
     {"hook_event_name": "PostToolUse", "tool_name": "edit/createFile",
      "tool_input": {"filePath": "src/main.py"}}, ".deep-dive", "allow"),
    ("unknown mutating tool name fails open",
     pre("some/futureWriteTool", {"filePath": "src/main.py"}), ".deep-dive", "allow"),
]


def main() -> int:
    failures = 0
    for label, payload, confine, expected in CASES:
        got = run(payload, confine)
        ok = got == expected
        if not ok:
            failures += 1
        print("%-4s %-52s expected=%-5s got=%s"
              % ("PASS" if ok else "FAIL", label, expected, got))
    print("\n%d/%d passed" % (len(CASES) - failures, len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
