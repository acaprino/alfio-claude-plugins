---
description: >
  End-to-end Python development pipeline — Architecture design, TDD execution, and refactoring polish. Argument hint: "<task description> [--skip-tests] [--refactor-only]".
  TRIGGER WHEN: managing an end-to-end python project workflow, from design to tested and refactored code.
  DO NOT TRIGGER WHEN: the user asks for isolated edits, or the task is outside the scope of Python.
---

# Python End-to-End Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output report in `.python-pipeline/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the `ask_user` tool with clear options.
4. **Halt on failure.** If any step fails (agent error, missing files, access issues), STOP immediately. Present the error and ask the user how to proceed.
5. **Respect scope flags.** If `--skip-tests` is set, run only Phase 1 and 3. If `--refactor-only` is set, skip to Phase 3.

## Pre-flight Checks

### 0. Dependency check

This command requires the specialized Python agents. Before proceeding, verify they are available in the workspace:
- `python-architect` (Phase 1)
- `python-test-engineer` (Phase 2)
- `python-refactor-agent` (Phase 3)

### 1. Initialize state

Create a `.python-pipeline/` directory and `state.json` file to track progress.

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "current_phase": 1
}
```

Parse `$ARGUMENTS` for `--skip-tests` and `--refactor-only` flags.

---

## Phase 1: Architecture & Scaffolding (Architect)

**Goal:** Understand the requirements, design the system architecture, and write the initial scaffolding/core logic.
**Agent:** `python-architect`

1. Delegate the user's `$ARGUMENTS` to the `python-architect` agent.
2. Ask the architect to produce an architecture plan and implement the core structural code (e.g. `pyproject.toml`, main app files, data models).
3. The architect must write the summary to `.python-pipeline/01-architecture-report.md`.

### PHASE 1 CHECKPOINT 🛑

Present the generated architecture to the user.
Ask the user: "Phase 1 complete. Core architecture is designed. Proceed to Phase 2 (Testing)?" (Or Phase 3 if tests are skipped).

---

## Phase 2: Test-Driven Execution (Test Engineer)

**Goal:** Ensure correctness through rigorous pytest implementation and >90% coverage.
**Agent:** `python-test-engineer`

*Skip if `--skip-tests` or `--refactor-only` is set.*

1. Provide the Phase 1 report to the `python-test-engineer` agent.
2. Instruct the test engineer to write comprehensive unit and integration tests for the implemented code.
3. The engineer must run `pytest` (if available) to verify, and write `.python-pipeline/02-test-report.md`.

### PHASE 2 CHECKPOINT 🛑

Present the test coverage and results to the user.
Ask the user: "Phase 2 complete. Tests are green. Proceed to Phase 3 (Refactoring & Polish)?"

---

## Phase 3: Refactoring & Polish (Refactor Agent)

**Goal:** Clean up the codebase, reduce complexity, remove dead code, and ensure high-quality docstrings.
**Agent:** `python-refactor-agent`

1. Provide the codebase context to the `python-refactor-agent`.
2. Instruct the agent to run code quality tools (ruff, vulture) if available, and apply systematic refactoring.
3. Instruct the agent to add antirez-style comments and Google-style docstrings where missing.
4. The agent writes `.python-pipeline/03-refactor-report.md`.

### PHASE 3 CHECKPOINT 🛑

Present the final refactoring summary to the user.
Ask the user: "Pipeline complete! Review the changes and let me know if any further adjustments are needed."

---

## CLAUDE.md Alignment Check

Before finalizing, verify the project's `CLAUDE.md` still reflects the current state:

1. Read `CLAUDE.md` (if it exists)
2. Compare against changes made during this pipeline:
   - New or renamed files/directories
   - Changed conventions, dependencies, or tech stack
   - Updated build/test commands or workflows
3. If `CLAUDE.md` is out of date, propose specific updates to the user
4. If no `CLAUDE.md` exists and the project would benefit from one, suggest creating it

---

## Completion

Once Phase 3 is approved:
1. Update `.python-pipeline/state.json` status to `"complete"`.
2. Print a final summary of the Python End-to-End Pipeline.
