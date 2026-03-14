---
description: "End-to-end feature pipeline -- brainstorm design, write plan, execute with checkpoints, review changes, and humanize code"
argument-hint: "<feature description> [--skip-brainstorm] [--skip-humanize] [--strict-mode]"
---

# Feature End-to-End Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.feature-e2e/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, test failure, missing files), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
6. **Brainstorming is interactive.** Phase 1 MUST involve back-and-forth with the user -- ask questions one at a time, propose approaches, get approval before proceeding.
7. **Respect skip flags.** If `--skip-brainstorm` is set, start at Phase 2 (user must provide a design doc or requirements). If `--skip-humanize` is set, skip Phase 5.

## Pre-flight Checks

### 0. Dependency check

This command requires agents and skills from other plugins. Before proceeding, verify the following plugins are installed by checking that their agents/skills are available:

**Required plugins:**
- `ai-tooling` -- brainstorming, writing-plans, executing-plans skills
- `senior-review` -- architect-review, security-auditor, pattern-quality-scorer agents
- `humanize` -- humanize agent (skip Phase 5 if missing)

Check by looking for the agent/skill files. If a required plugin is missing, STOP and tell the user:

```
Missing required plugin(s): [list]

This workflow command depends on agents and skills from other anvil-toolset plugins.
Install them with:
  claude plugin marketplace add acaprino/anvil-toolset --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/anvil-toolset
```

If only `humanize` is missing, warn but continue (treat as `--skip-humanize`).

### 1. Check for existing session

Check if `.feature-e2e/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask:
  ```
  Found an in-progress feature pipeline session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```
- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 2. Initialize state

Create `.feature-e2e/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "skip_brainstorm": false,
    "skip_humanize": false,
    "strict_mode": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--skip-brainstorm`, `--skip-humanize`, and `--strict-mode` flags.

### 3. Explore project context

Scan the current project to understand:
- Language and framework (check package.json, Cargo.toml, pyproject.toml, etc.)
- Project structure and conventions
- Existing test patterns
- Recent git history

**Output file:** `.feature-e2e/00-context.md`

```markdown
# Pipeline Context

## Feature
[Feature description from $ARGUMENTS]

## Project
- Language: [detected]
- Framework: [detected]
- Test framework: [detected]
- Build tool: [detected]

## Flags
- Skip Brainstorm: [yes/no]
- Skip Humanize: [yes/no]
- Strict Mode: [yes/no]

## Pipeline Phases
1. Brainstorm Design
2. Write Implementation Plan
3. Execute Plan
4. Review Changes
5. Humanize Code
```

---

## Phase 1: Brainstorm Design

**Skip if:** `--skip-brainstorm` flag is set. If skipped, ask the user to provide a design document or requirements, then save to `.feature-e2e/01-design.md` and proceed to Phase 2.

Follow the brainstorming skill process -- this phase is **interactive**:

### Step 1A: Explore project context

Review the codebase to understand the current architecture and where this feature fits.

### Step 1B: Ask clarifying questions (one at a time)

Ask the user questions to refine the feature idea:

- What problem does this feature solve?
- Who is the primary user?
- Are there constraints (performance, compatibility, design system)?
- How should this feature interact with existing functionality?
- What does "done" look like?

Use AskUserQuestion with multiple-choice options where possible. One question per message.

### Step 1C: Propose approaches

Propose 2-3 implementation approaches with trade-offs:

- Approach A: [description, pros, cons]
- Approach B: [description, pros, cons]
- Recommended: [which and why]

### Step 1D: Present design

Present the design in sections scaled to complexity. Get user approval after each section:

- Architecture (where it fits, dependencies)
- Components/modules (what to build)
- Data flow (inputs, transformations, outputs)
- Error handling (failure modes, recovery)
- Testing strategy (what to test, how)

**Output file:** `.feature-e2e/01-design.md`

```markdown
# Phase 1: Feature Design

## Feature
[Feature name and description]

## Problem Statement
[What problem this solves]

## Selected Approach
[Chosen approach with rationale]

## Architecture
[Where this fits in the codebase]

## Components
[What to build]

## Data Flow
[Inputs, transformations, outputs]

## Error Handling
[Failure modes and recovery]

## Testing Strategy
[What to test and how]

## Design Decisions
[Key decisions made during brainstorming]
```

Update `state.json`: set `current_phase` to "checkpoint-1", add phase 1 to `completed_phases`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

```
Phase 1 complete: Feature design finalized.

Feature: [name]
Approach: [selected approach summary]
Components: [count]

Please review:
- .feature-e2e/01-design.md

1. Continue -- proceed to writing the implementation plan
2. Revise design -- adjust before planning
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 2 until the user approves.

---

## Phase 2: Write Implementation Plan

Read `.feature-e2e/01-design.md` for the approved design.

Follow the writing-plans skill process:

```
Task:
  subagent_type: "general-purpose"
  description: "Write implementation plan for feature"
  prompt: |
    You are using the writing-plans skill. Write a comprehensive, bite-sized implementation plan.

    ## Design
    [Insert contents of .feature-e2e/01-design.md]

    ## Project Context
    [Insert contents of .feature-e2e/00-context.md]

    ## Instructions
    Create a plan with bite-sized tasks following TDD principles:

    Plan header:
    - Goal: one sentence
    - Architecture: 2-3 sentences
    - Tech stack: key technologies

    For each task:
    - Exact file paths (create/modify/test)
    - Step 1: Write the failing test (complete test code)
    - Step 2: Run test to verify it fails (exact command + expected output)
    - Step 3: Write minimal implementation (complete code)
    - Step 4: Run test to verify it passes (exact command + expected output)
    - Step 5: Commit (exact git command)

    Order tasks by dependency. Each task should be 2-5 minutes of work.

    Write the plan as a structured markdown document.
```

**Output file:** `.feature-e2e/02-plan.md`

Update `state.json`: set `current_phase` to "checkpoint-2", add phase 2 to `completed_phases`.

---

## PHASE CHECKPOINT 2 -- User Approval Required

```
Phase 2 complete: Implementation plan written.

Plan summary:
- Total tasks: [count]
- Files to create: [count]
- Files to modify: [count]
- Tests to write: [count]

Please review:
- .feature-e2e/02-plan.md

1. Continue -- execute the plan with batch checkpoints
2. Revise plan -- adjust tasks before executing
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 3: Execute Plan

Read `.feature-e2e/02-plan.md` for the implementation plan.

Follow the executing-plans skill process with batch execution:

### Execution Loop

Execute tasks in batches of 3:

1. **For each task in the batch:**
   - Mark as in_progress
   - Follow each step exactly (test first, then implement)
   - Run all verification commands
   - If a test fails: STOP the batch, report the failure, ask the user how to proceed
   - Mark as completed

2. **After each batch:**
   - Show what was implemented
   - Show verification output (test results)
   - Ask: "Ready for feedback on this batch?"

3. **Wait for user feedback** before starting the next batch:
   - Apply any requested changes
   - Continue to next batch

4. **Repeat** until all tasks are complete.

Log each task's execution to `.feature-e2e/03-execution-log.md`:

```markdown
# Phase 3: Execution Log

## Task 1: [name]
- Status: completed
- Files changed: [list]
- Tests: [pass/fail]
- Commit: [hash]

## Task 2: [name]
...

## Execution Summary
- Tasks completed: [X/Y]
- Tests passing: [count]
- Commits made: [count]
```

Update `state.json`: set `current_phase` to "checkpoint-3", add phase 3 to `completed_phases`.

---

## PHASE CHECKPOINT 3 -- User Approval Required

```
Phase 3 complete: Implementation executed.

Execution summary:
- Tasks completed: [X/Y]
- Tests passing: [count]
- Commits made: [count]

Please review:
- .feature-e2e/03-execution-log.md
- Run the test suite to verify: [test command]

1. Continue -- review the changes with architecture, security, and pattern analysis
2. Fix issues -- address problems before review
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 4 until the user approves.

---

## Phase 4: Review Changes

Run the senior-review process -- fire all 3 review agents **in parallel**:

First, get the diff of all changes made during execution:

```bash
git diff HEAD~[number-of-commits-from-phase-3] --name-only
git diff HEAD~[number-of-commits-from-phase-3] -- [code files only]
```

### Agent A: Architecture & Code Quality

```
Task:
  subagent_type: "architect-review"
  description: "Architecture review of feature implementation"
  prompt: |
    Review the code changes made during feature implementation.
    Focus on code quality and architectural concerns. Skip documentation.

    ## Feature Context
    [Insert summary from .feature-e2e/01-design.md]

    ## Changed Files
    [list of changed code files]

    ## Diff
    [git diff output]

    ## Instructions
    Analyze for:
    1. Design concerns -- are changes architecturally sound?
    2. Code quality -- naming, complexity, duplication
    3. Error handling -- missing or incorrect
    4. Consistency -- do changes follow existing patterns?
    5. Scope -- is the solution appropriately scoped?

    For each finding: severity (Critical/High/Medium/Low), file + line, concrete fix.
    Note what was done well.
```

### Agent B: Security Assessment

```
Task:
  subagent_type: "security-auditor"
  description: "Security review of feature implementation"
  prompt: |
    Review the code changes for security issues. Skip documentation.

    ## Changed Files
    [list of changed code files]

    ## Diff
    [git diff output]

    ## Instructions
    Check for:
    1. Injection risks -- SQL, command, XSS in new code
    2. Input validation -- missing validation of user input
    3. Auth/authorization -- flawed logic, missing checks
    4. Secrets exposure -- hardcoded credentials or tokens
    5. Insecure defaults -- debug mode, verbose errors
    6. Dependency risks -- new packages trustworthy and current?

    For each finding: severity, CWE if applicable, file + line, concrete fix.
```

### Agent C: Pattern Consistency & Scoring

```
Task:
  subagent_type: "pattern-quality-scorer"
  description: "Pattern analysis and quality scoring of feature implementation"
  prompt: |
    Analyze the code changes for pattern consistency and quality score.

    ## Changed Files
    [list of changed code files]

    ## Diff
    [git diff output]

    ## Instructions
    Pattern Consistency:
    - Identify dominant patterns in changed files
    - Flag deviations introduced by these changes
    - Check for anti-patterns

    Mental Models (all six):
    - Security Engineer, Performance Engineer, Team Lead, Systems Architect, SRE, Pattern Detective

    Quality Score:
    | Category     | Score |
    |--------------|-------|
    | Code Quality | X/10  |
    | Security     | X/10  |
    | Consistency  | X/10  |
    | **Overall**  | **X/10** |
```

After all agents complete, consolidate into `.feature-e2e/04-review.md`:

```markdown
# Phase 4: Code Review

## Overall Score: X/10

## Critical & High Issues
[Merged from all agents, deduplicated]

## Medium & Low Issues
[Merged from all agents]

## What Was Done Well
[Positive observations]

## Recommended Actions
1. [highest priority fix]
2. [second priority]
3. [third priority]
```

Update `state.json`: set `current_phase` to "checkpoint-4", add phase 4 to `completed_phases`.

---

## PHASE CHECKPOINT 4 -- User Approval Required

```
Phase 4 complete: Code review finished.

Overall Score: X/10
Critical: [X] | High: [Y] | Medium: [Z] | Low: [W]

Top issues:
1. [critical/high issue]
2. [critical/high issue]
3. [critical/high issue]

Please review:
- .feature-e2e/04-review.md

1. Continue -- humanize the code (improve readability)
2. Fix review issues first -- address findings before humanizing
3. Skip humanize -- finish without humanizing (same as --skip-humanize)
4. Pause -- save progress and stop here
```

If `--strict-mode` is set and there are Critical findings, recommend option 2.

Do NOT proceed to Phase 5 until the user approves.

---

## Phase 5: Humanize Code

**Skip if:** `--skip-humanize` flag is set or user chose option 3 at checkpoint.

Read `.feature-e2e/04-review.md` to understand which files were changed.

```
Task:
  subagent_type: "humanize"
  description: "Humanize feature implementation code"
  prompt: |
    Improve the readability and human-friendliness of recently implemented code.
    Do NOT change behavior -- only improve naming, comments, and code clarity.

    ## Changed Files
    [list of code files modified during Phase 3 execution]

    ## Review Context
    [Insert consistency findings from .feature-e2e/04-review.md]

    ## Instructions
    For each changed file:
    1. Improve variable/function names to be more descriptive
    2. Add brief comments where logic isn't self-evident
    3. Improve code structure for readability (extract functions if needed)
    4. Ensure consistent style with the rest of the codebase
    5. Remove any AI-generated boilerplate or unnecessary comments

    Do NOT:
    - Change any behavior or logic
    - Add error handling or features
    - Refactor architecture
    - Add type annotations to unchanged code

    Run tests after changes to verify behavior is preserved.
```

Log changes to `.feature-e2e/05-humanize-log.md`:

```markdown
# Phase 5: Humanize Log

## Files Modified
[List of files with changes made]

## Changes Made
- [file]: Renamed X to Y, added comment explaining Z
- [file]: Extracted helper function for clarity

## Tests
- All tests still passing: [yes/no]
```

Update `state.json`: set `status` to `"complete"`, `last_updated` to current timestamp.

---

## Completion

Present the final summary:

```
Feature end-to-end pipeline complete for: $ARGUMENTS

## Output Files
- Project Context: .feature-e2e/00-context.md
- Design: .feature-e2e/01-design.md
- Implementation Plan: .feature-e2e/02-plan.md
- Execution Log: .feature-e2e/03-execution-log.md
- Code Review: .feature-e2e/04-review.md
- Humanize Log: .feature-e2e/05-humanize-log.md [if not skipped]

## Summary
- Feature: [name]
- Tasks executed: [count]
- Tests passing: [count]
- Code Quality Score: [X/10]
- Files changed: [count]

## Next Steps
1. Review the final code review at .feature-e2e/04-review.md
2. Run the full test suite to confirm: [test command]
3. Commit any remaining changes and push
```

If `--strict-mode` is set and there were Critical review findings that weren't addressed:
```
STRICT MODE: Unresolved critical issues remain. Review .feature-e2e/04-review.md before merging.
```
