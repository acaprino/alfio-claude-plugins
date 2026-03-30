---
description: >
  "Rewrite source code to be more readable and human-friendly -- improves naming, removes AI boilerplate, simplifies structure, adds clarity comments -- without changing behavior" argument-hint: "<file or directory> [--dry-run] [--strict] [--yes] [--force]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Clean Code

Use the `clean-code-agent` to rewrite source code for readability without changing behavior.

## Rules

1. **Validate before and after.** Establish a baseline with type checker + tests + linter, then verify no regressions.
2. **If `--dry-run`, preview only.** Show proposed changes without modifying files.
3. **Revert on failure.** If any validation fails after a change, revert with `git restore <file>` immediately.
4. **Ask for confirmation** at Steps 2 and 3, unless `--yes` flag is provided.
5. **Block without validation tools.** If no tests AND no type checker exist, require `--force` to proceed.

## Step 1: Identify Target

From `$ARGUMENTS`, determine files to clean:
- If a file path: clean that file
- If a directory: clean all source files in it
- Filter out test files (unless they reference renamed symbols)

List the files to be cleaned and their language.

## Step 2: Establish Validation Baseline

Detect available validation tools by inspecting project files:

| Tool | How to detect | Command |
|------|--------------|---------|
| **Type checker** | `tsconfig.json` | `tsc --noEmit` |
| | `mypy.ini`, `pyrightconfig.json`, or mypy/pyright in `pyproject.toml` | `mypy .` or `pyright` |
| | `Cargo.toml` | `cargo check` |
| | `go.mod` | `go vet ./...` |
| **Test runner** | `package.json` | `npm test` |
| | `pyproject.toml` or `setup.py` | `pytest` |
| | `Cargo.toml` | `cargo test` |
| | `go.mod` | `go test ./...` |
| | `Makefile` with test target | `make test` |
| **Linter** | `ruff.toml` or ruff config in `pyproject.toml` | `ruff check` |
| | `.eslintrc*` or `eslint.config.*` | `eslint` |
| | `Cargo.toml` | `cargo clippy` |

Run all detected tools and capture both stdout and stderr. Record the baseline.

**Hard gate:** if NO tests AND NO type checker are found, stop and tell the user:

```
No tests or type checker found. Cannot validate that changes are safe.

1. Cancel -- set up tests or type checking first (recommended)
2. Proceed with --force -- I'll be careful but regressions may go undetected
```

`--yes` alone does NOT bypass this gate. Only `--force` does.

## Step 3: Preview Changes (always for --dry-run, ask otherwise)

If `--dry-run` flag is set, or if the target is a directory with >3 files, show a preview first.
If `--yes` flag is provided, apply all changes after showing the preview without asking.

For each file, analyze and propose:
- Variable/function renames (vague -> domain-meaningful)
- Boilerplate comments to remove (paraphrase comments, empty docstrings)
- Why-comments to add (non-obvious business logic)
- Structural simplifications (flatten nesting, remove redundant abstractions, consolidate logic)

Present the preview:

```
Clean Code preview for: [target]

[file1]:
- Rename `data` -> `user_profile` (line 23)
- Rename `proc` -> `process_payment` (line 45)
- Remove boilerplate docstring (line 12-15)
- Flatten nested if/else chain (line 30-50)
- Add comment explaining retry logic (line 67)

[file2]:
- ...

Total changes: [count] across [file count] files

1. Apply all changes
2. Apply to specific files only
3. Cancel
```

If `--dry-run`, stop after the preview.

## Step 4: Apply Changes

Spawn the `clean-code-agent` with the file list and approved changes from the preview. The agent has its own safety rules and transformation guidelines -- do not repeat them here. Just pass the target:

```
Task:
  subagent_type: "clean-code-agent"
  description: "Clean [target] for readability"
  prompt: |
    Improve the readability of this code. Zero behavior changes.

    Files: [list of files]
    Approved changes: [from preview, if applicable]
    Flags: [--strict if present in $ARGUMENTS]
```

## Step 5: Validate & Report

Re-run ALL validation tools detected in Step 2, in this order:

1. **Type checker** -- if it fails on a file that passed in baseline, revert that file
2. **Tests** -- if any previously-passing test now fails, revert the responsible file
3. **Linter** -- if new errors appear, fix or revert
4. **Non-code grep** -- for every renamed symbol, search `.json`, `.yaml`, `.yml`, `.toml`, `.env`, `.cfg`, `.ini`, `.xml`, `.html`, `.md` for the OLD name. Report matches as warnings.

Present summary:

```
Clean Code complete for: [target]

Files modified: [count]
Changes made:
- Renames: [count]
- Comments removed: [count]
- Comments added: [count]
- Structural simplifications: [count]

Validation:
  Type check: [passed / N errors -- reverted] or [not available]
  Tests: [all passing / X failures -- reverted] or [not available]
  Linter: [passed / N new warnings] or [not available]

Stale references found in non-code files:
  - [config.json:12] -- still references old name `data`
  - [README.md:45] -- documents old function name `proc`

Review the changes with: git diff
```

If `--strict` flag is set, also flag any remaining readability concerns that weren't auto-fixable.

## What It Does / Does NOT Do

**Does:** rename vague local variables, remove paraphrase comments, add why-comments, simplify structure (flatten nesting, remove redundant abstractions, consolidate logic).

**Does not:** reorder code, extract functions, change APIs, remove error handling/validations/imports, modify test files, over-simplify. See the agent's safety rules for the full list.

For deeper restructuring, use `/python-refactor`.

Clean the following:

$ARGUMENTS
