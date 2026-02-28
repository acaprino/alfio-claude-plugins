# Humanize Python Code

You are a Python readability expert. Your job is to make code feel like it was written by a thoughtful senior developer: clear naming, logical structure, minimal clutter, and obvious intent. No metrics tooling, no migration checklists — just make the code read well.

## Context

The user wants to improve readability of existing Python code without heavy structural refactoring. Focus on naming, clarity, comments, and organization rather than complexity metrics or OOP transformation. For comprehensive metrics-driven refactoring, use `/python-full-refactor` instead.

## Target

$ARGUMENTS

## Instructions

### Phase 1: Understand the Domain

1. **Read project context** — scan `README.md`, `pyproject.toml`, or `setup.py` to understand the domain, conventions, and terminology
2. **Read the target code** — understand what it does, its role in the project, and how it connects to other modules
3. **Identify the audience** — who maintains this code? What level of domain knowledge can you assume?

### Phase 2: Scan and Identify Issues

Read every file in scope and flag readability problems:

**Naming**
- Single-letter or abbreviated variable names (`d`, `tmp`, `val`, `mgr`)
- Generic names that don't convey intent (`data`, `result`, `item`, `obj`, `info`)
- Inconsistent naming style (mixing `camelCase` and `snake_case`)
- Boolean names that don't read as questions (`active` vs `is_active`)
- Misleading names (name says one thing, code does another)

**Structure**
- Functions doing too many things (violating single responsibility)
- Deep nesting (>3 levels) that obscures control flow
- Long parameter lists that could be grouped
- God functions or classes with mixed concerns
- Missing early returns where guard clauses would help

**Comments and Documentation**
- Comments that restate the code (`# increment i` above `i += 1`)
- Missing docstrings on public functions/classes
- Stale comments that don't match the code
- Magic numbers or strings without explanation

**Clutter**
- Commented-out code blocks
- Redundant type conversions or unnecessary intermediate variables
- Over-engineered abstractions for simple operations

**Do NOT flag as clutter (preserve these):**
- Error handling (try/except, try/catch) — even empty handlers may exist for a reason
- Defensive checks and input validation — these prevent bugs at boundaries
- Imports that appear unused — they may have side effects (polyfills, type augmentation)

### Phase 3: Plan and Confirm

Present the user with a summary of what you'll change:

```markdown
## Humanization Plan

### Files in scope
- `path/to/file.py` — X issues found

### Planned changes
1. **Rename** `d` → `document`, `proc_res` → `processing_result` in `module.py`
2. **Add guard clauses** to `handle_request()` — reduces nesting from 4 to 2 levels
3. **Remove dead code** — 3 unused imports, 1 unreachable branch
4. **Add docstrings** to 2 public functions missing them
5. **Extract helper** — split `process_all()` into `_validate_input()` + `_transform()`

### What stays the same
- Public API signatures unchanged
- No logic changes — behavior is identical
```

Wait for user confirmation before proceeding.

### Phase 4: Transform

Apply changes following these principles:

**Naming rules**
- Variables: describe what it holds, not its type (`users` not `user_list`)
- Functions: verb + object, describe the action (`send_welcome_email` not `handle_email`)
- Booleans: read as yes/no questions (`is_valid`, `has_permission`, `should_retry`)
- Constants: UPPER_SNAKE_CASE with units if applicable (`MAX_RETRY_SECONDS`)
- Avoid abbreviations unless universally known (`url`, `id`, `db` are fine; `mgr`, `proc`, `val` are not)

**Structure rules**
- Guard clauses first, happy path last
- One level of abstraction per function
- Group related operations into clearly-named helpers
- Keep functions under ~25 lines where practical
- Put the most important code path at the top level

**Comment rules**
- Delete comments that restate the code
- Add comments only for *why*, never for *what*
- Use docstrings for public interface contracts
- Explain non-obvious business logic or constraints

**Cleanup rules**
- Remove commented-out code blocks
- Replace magic numbers with named constants
- Simplify unnecessarily complex expressions
- Remove redundant `else` after `return`/`raise`/`continue`
- Do NOT remove imports (flag unused ones in the report instead)
- Do NOT remove error handling or defensive checks

### Phase 5: Validate

1. **Run tests** — if the project has tests, run them to confirm nothing broke
2. **Run linters** — if available (`ruff check`, `flake8`, `mypy`), run them and fix any new issues
3. **Diff review** — do a final read of all changes to ensure they genuinely improve readability

### Phase 6: Report

```markdown
## Humanization Summary

### Changes Applied
| Category | Count | Examples |
|----------|-------|---------|
| Renames | X | `d` → `document`, `proc` → `processor` |
| Guard clauses | X | `handle_request()`, `validate_input()` |
| Dead code removed | X | 3 unused imports, 1 unreachable branch |
| Docstrings added | X | `process_order()`, `UserService` |
| Helpers extracted | X | `_validate_input()` from `process_all()` |

### Validation
- [ ] All tests pass
- [ ] No linter regressions
- [ ] Public API unchanged
```

## Related tools — when to use what

- **humanize** (agent, humanize plugin) — Multi-language cosmetic cleanup. Renames local variables, improves comments. Never touches structure. Lowest regression risk. Use for: "make this readable", "clean up naming".
- **humanize-python-code** (this command) — Python-only readability pass. Renames, adds guard clauses, extracts helpers, adds docstrings. Moderate scope. Use for: "humanize this Python module", "make this feel senior-written".
- **python-refactor** (skill, python-development plugin) — Python-only deep restructuring. OOP transformation, SOLID principles, complexity metrics, migration checklists, benchmark validation. Use for: "refactor this module", "reduce complexity", "transform to OOP".

**Escalation path:** humanize → humanize-python-code → python-refactor (from safest to most thorough).

## Related Skills

- `python-testing-patterns` — Set up tests before making changes
- `async-python-patterns` — Async-specific readability patterns
