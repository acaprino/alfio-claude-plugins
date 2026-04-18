---
description: >
  Metrics-driven Python refactoring -- analyze complexity, plan improvements, execute with test validation, and produce before/after comparison report.
  TRIGGER WHEN: the user asks to refactor Python code, reduce cyclomatic complexity, or restructure modules with measured before/after metrics.
  DO NOT TRIGGER WHEN: just renaming/simplifying for readability (use /clean-code:clean-code) or removing dead code (use /senior-review:cleanup-dead-code).
argument-hint: "<target file or directory> [--strict-mode]"
---

# Python Refactoring

## CRITICAL RULES

1. **Execute phases in order.** Analysis -> Planning -> Approval -> Execution -> Validation.
2. **Write output files.** Each phase writes to `.python-refactor/` for persistence and context.
3. **Stop at checkpoint.** Get user approval of the refactoring plan BEFORE making any code changes.
4. **Run tests after every change.** Never proceed if tests fail.
5. **Never enter plan mode.** Execute immediately.
6. **One pattern at a time.** Don't combine multiple refactorings in a single edit.

## Pre-flight

### 1. Check for existing session

Check if `.python-refactor/state.json` exists:
- If in progress: offer to resume or start fresh
- If complete: offer to archive and start fresh

### 2. Initialize state

Create `.python-refactor/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "strict_mode": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP"
}
```

## Phase 1: Analysis

1. **Read the target code** to understand current structure
2. **Run complexity metrics** (if available):
   ```bash
   uv run python plugins/python-development/skills/python-refactor/scripts/measure_complexity.py $ARGUMENTS 2>/dev/null
   uv run python plugins/python-development/skills/python-refactor/scripts/analyze_with_flake8.py $ARGUMENTS 2>/dev/null
   ```
   If scripts aren't available, analyze manually by reading the code.

3. **Identify issues** against thresholds:
   - Cyclomatic complexity: >10 per function (high priority)
   - Cognitive complexity: >15 per function (high priority)
   - Function length: >30 lines (medium priority)
   - Nesting depth: >3 levels (medium priority)

4. **Establish test baseline**:
   ```bash
   pytest [test files] -v 2>/dev/null || python -m pytest -v 2>/dev/null
   ```
   Record which tests exist and their pass/fail status.

**Output file:** `.python-refactor/01-analysis.md`

```markdown
# Phase 1: Analysis

## Target
[file/directory path]

## Current Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Cyclomatic Complexity (avg) | X | <10 | PASS/FAIL |
| Cognitive Complexity (max) | X | <15 | PASS/FAIL |
| Max Function Length | X lines | <30 | PASS/FAIL |
| Max Nesting Depth | X | <=3 | PASS/FAIL |

## Issues Found
[Ordered by severity: HIGH, MEDIUM, LOW]

## Test Baseline
- Tests found: [count]
- Passing: [count]
- Failing: [count]
```

## Phase 2: Planning

Read `.python-refactor/01-analysis.md` for context.

1. **Prioritize issues** by impact
2. **Select refactoring patterns** for each issue:
   - Guard clauses for nested conditionals
   - Extract method for long functions
   - Replace magic numbers with named constants
   - Rename for clarity
   - Decompose god functions
3. **Assess risk** for each change (Low / Medium / High)
4. **Create ordered plan** with atomic steps

**Output file:** `.python-refactor/02-plan.md`

```markdown
# Phase 2: Refactoring Plan

## Refactoring Steps (ordered)

### Step 1: [pattern] on [target]
- Risk: [Low/Medium/High]
- File: [path:line]
- What: [description of change]
- Why: [rationale]

### Step 2: ...
[Continue for all planned changes]

## Estimated Impact
- Complexity reduction: ~X%
- Functions affected: [count]
- Risk level: [overall Low/Medium/High]
```

---

## PHASE CHECKPOINT -- User Approval Required

```
Analysis and planning complete.

Issues found: [count] ([X high, Y medium, Z low])
Refactoring steps planned: [count]
Overall risk: [Low/Medium/High]
Test baseline: [X] tests passing

Please review:
- .python-refactor/01-analysis.md
- .python-refactor/02-plan.md

1. Execute the plan -- apply all refactorings with test validation
2. Execute partial -- I'll tell you which steps to apply
3. Revise plan -- adjust before executing
4. Cancel -- stop here with the analysis only
```

If `--strict-mode` is set and there are High risk changes, recommend option 2 (partial execution).

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 3: Execution

Read `.python-refactor/02-plan.md` for the approved plan.

For each refactoring step:

1. Apply the single refactoring pattern
2. Run tests immediately:
   ```bash
   pytest [test files] -v
   ```
3. If tests pass: commit the change and continue
4. If tests fail: REVERT the change, report the failure, ask the user how to proceed

Log each step to `.python-refactor/03-execution.md`:

```markdown
# Phase 3: Execution Log

## Step 1: [pattern]
- Status: [completed/failed/reverted]
- File: [path]
- Tests: [all passing / X failures]
- Commit: [hash]

## Step 2: ...
```

## Phase 4: Validation

After all steps executed:

1. **Run full test suite** -- zero failures required
2. **Compare metrics** (if scripts available):
   ```bash
   uv run python plugins/python-development/skills/python-refactor/scripts/compare_metrics.py [before] [after] 2>/dev/null
   ```
3. **Manual comparison** -- re-read the code and compare complexity

**Output file:** `.python-refactor/04-validation.md`

```markdown
# Phase 4: Validation

## Metrics Comparison
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Cyclomatic Complexity (avg) | X | Y | -Z% |
| Cognitive Complexity (max) | X | Y | -Z% |
| Max Function Length | X | Y | -Z lines |
| Max Nesting Depth | X | Y | -Z |

## Test Results
- Tests run: [count]
- Passing: [count]
- Failing: [count]

## Refactoring Summary
- Steps executed: [X/Y]
- Steps reverted: [count]
- Files changed: [count]
- Commits: [count]
```

---

## Completion

```
Python refactoring complete for: $ARGUMENTS

Output Files:
- Analysis: .python-refactor/01-analysis.md
- Plan: .python-refactor/02-plan.md
- Execution Log: .python-refactor/03-execution.md
- Validation: .python-refactor/04-validation.md

Summary:
- Refactorings applied: [X/Y]
- Tests: [all passing / X failures]
- Complexity reduction: ~[Z]%

Next steps:
1. Review changes with /senior-review
2. Run the full test suite to confirm
3. Commit remaining changes if needed
```

## Related Skills

- `python-tdd` -- Set up tests before refactoring
- `python-performance-optimization` -- Profile if performance-critical
- `async-python-patterns` -- For async code refactoring
