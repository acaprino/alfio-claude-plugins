---
description: >
  "End-to-end feature pipeline -- brainstorm design, write plan, isolate in worktree, execute with platform-engineering guardrails, test verification, review changes, humanize code, and create PR" argument-hint: "<feature description> [--skip-brainstorm] [--skip-humanize] [--worktree] [--strict-mode]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Feature End-to-End Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.develop/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, test failure, missing files), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
6. **Brainstorming is interactive.** Phase 1 MUST involve back-and-forth with the user -- ask questions one at a time, propose approaches, get approval before proceeding.
7. **Respect skip flags.** If `--skip-brainstorm` is set, start at Phase 2 (user must provide a design doc or requirements). If `--skip-humanize` is set, skip Phase 6.
8. **Worktree isolation.** If `--worktree` is set, create an isolated worktree before Phase 3 execution begins. All implementation work happens in the worktree.

## Pre-flight Checks

### 0. Dependency check

This command requires agents and skills from other plugins. Before proceeding, verify the following plugins are installed by checking that their agents/skills are available:

**Required plugins:**
- `ai-tooling` -- brainstorming, writing-plans, executing-plans skills
- `senior-review` -- architect-review, security-auditor, pattern-quality-scorer agents
- `platform-engineering` -- platform-reviewer agent, platform-engineering skill
- `testing` -- test-writer agent, tdd skill, e2e-testing-patterns skill

**Optional plugins (loaded conditionally based on detected stack):**
- `humanize` -- humanize agent (skip Phase 6 if missing)
- `git-worktrees` -- worktree management (required if `--worktree` flag is set)
- `frontend` -- ui-layout-designer agent, web-designer agent, frontend skill (loaded when UI changes detected)
- `tauri-development` -- tauri-desktop agent, rust-engineer agent (loaded for Tauri projects)
- `react-development` -- react-performance-optimizer agent (loaded for React projects)
- `python-development` -- python-pro agent (loaded for Python GUI projects)

Check by looking for the agent/skill files. If a required plugin is missing, STOP and tell the user:

```
Missing required plugin(s): [list]

This workflow command depends on agents and skills from other figs plugins.
Install them with:
  claude plugin marketplace add acaprino/figtree-plugins --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/figtree-plugins
```

If only `humanize` is missing, warn but continue (treat as `--skip-humanize`).

### 1. Check for existing session

Check if `.develop/state.json` exists:

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

Create `.develop/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "skip_brainstorm": false,
    "skip_humanize": false,
    "worktree": false,
    "strict_mode": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "worktree_path": null,
  "worktree_branch": null,
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--skip-brainstorm`, `--skip-humanize`, `--worktree`, and `--strict-mode` flags.

### 3. Explore project context

Scan the current project to understand:
- Language and framework (check package.json, Cargo.toml, pyproject.toml, etc.)
- Project structure and conventions
- Existing test patterns and test runner commands
- Recent git history
- Detected platforms (SPA, PWA, Mobile, Electron, Tauri) for platform-engineering rules

**Output file:** `.develop/00-context.md`

```markdown
# Pipeline Context

## Feature
[Feature description from $ARGUMENTS]

## Project
- Language: [detected]
- Framework: [detected]
- Test framework: [detected]
- Test command: [detected]
- Build tool: [detected]

## Detected Platforms
[SPA, PWA, Mobile, Electron, Tauri -- based on package.json, manifest files, build configs]

## UI Stack (auto-detected)
- UI changes detected: [yes/no]
- UI framework: [React/Vue/Svelte/Angular/vanilla/Qt/GTK/Flutter/none]
- Backend layer: [Rust (Tauri)/Node.js (Electron)/Python (Qt/GTK)/none]

## Flags
- Skip Brainstorm: [yes/no]
- Skip Humanize: [yes/no]
- Worktree: [yes/no]
- Strict Mode: [yes/no]

## Pipeline Phases
1. Brainstorm Design
2. Write Implementation Plan
3. Execute Plan (with platform-engineering guardrails)
4. Review Changes (architecture + security + patterns + platform)
5. Test Verification
6. Humanize Code
7. Create PR
```

---

## Phase 1: Brainstorm Design

**Skip if:** `--skip-brainstorm` flag is set. If skipped, ask the user to provide a design document or requirements, then save to `.develop/01-design.md` and proceed to Phase 2.

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

### Step 1E: Layout Planning (conditional)

After the design is approved in Step 1D, detect whether the feature involves UI/layout changes.

**Auto-detection signals:**

1. **Keywords in feature description:** `button`, `page`, `modal`, `dialog`, `form`, `section`, `sidebar`, `navbar`, `header`, `footer`, `layout`, `dashboard`, `panel`, `tab`, `menu`, `dropdown`, `tooltip`, `card`, `table`, `grid`, `responsive`, `component`, `view`, `screen`, `widget`, `input`, `list`
2. **Files in scope:** `.tsx`, `.jsx`, `.vue`, `.svelte`, `.css`, `.scss`, `.html`, `.qml`, `.ui`, `.dart`
3. **UI framework detected in project:** React, Vue, Svelte, Angular, Qt, GTK, Flutter (from `package.json`, `pubspec.yaml`, CMakeLists.txt, etc.)

If 1+ signal detected, ask the user:

```
Detected UI/layout changes in this feature.

1. Include spatial layout planning with UI Layout Designer (recommended)
2. Skip layout planning -- proceed without
```

**If confirmed**, dispatch the layout designer:

```
Agent tool call:
  - description: "Layout planning for feature UI"
  - subagent_type: "frontend:ui-layout-designer"
  - prompt: |
    Plan the spatial layout for a UI feature being added to an existing project.

    ## Feature Design
    [Insert design from Step 1D -- architecture, components, data flow]

    ## Project Context
    [Insert from .develop/00-context.md -- framework, existing component patterns]

    ## Instructions
    Produce a layout specification covering:
    1. Spatial composition -- grid/flex strategy, component placement
    2. Responsive breakpoint strategy -- how the layout adapts
    3. Component hierarchy -- nesting, containment relationships
    4. Spacing and sizing -- consistent spacing scale, key dimensions
    5. Developer handoff notes -- CSS approach, class naming, framework-specific patterns

    Keep it practical and implementation-ready. Reference existing patterns in the project where applicable.
    Write your specification as a structured markdown document.
```

Append the layout designer's output as a "## Layout Specification" section in the design document.

**Output file:** `.develop/01-design.md`

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

## Layout Specification (if UI feature)
[Spatial composition, responsive strategy, component hierarchy, spacing, developer handoff -- from ui-layout-designer]

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
- .develop/01-design.md

1. Continue -- proceed to writing the implementation plan
2. Revise design -- adjust before planning
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 2 until the user approves.

---

## Phase 2: Write Implementation Plan

Read `.develop/01-design.md` for the approved design.

Follow the writing-plans skill process:

```
Task:
  subagent_type: "general-purpose"
  description: "Write implementation plan for feature"
  prompt: |
    You are using the writing-plans skill. Write a comprehensive, bite-sized implementation plan.

    ## Design
    [Insert contents of .develop/01-design.md]

    ## Project Context
    [Insert contents of .develop/00-context.md]

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

**Output file:** `.develop/02-plan.md`

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
- .develop/02-plan.md

1. Continue -- execute the plan
2. Revise plan -- adjust tasks before executing
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 2.5: Worktree Isolation (if --worktree)

**Skip if:** `--worktree` flag is NOT set.

Create an isolated git worktree for the implementation work:

1. Create a feature branch name from the target: `feature/e2e-[slugified-target]`
2. Create the worktree:
   ```bash
   git worktree add ../.worktrees/develop-[slug] -b feature/e2e-[slug]
   ```
3. Copy `.develop/` state directory to the worktree
4. Update `state.json` with `worktree_path` and `worktree_branch`
5. All subsequent phases (3-7) execute inside the worktree directory

Tell the user:
```
Worktree created at: [path]
Branch: feature/e2e-[slug]
All implementation work will happen in the isolated worktree.
```

---

## Phase 3: Execute Plan

Read `.develop/02-plan.md` for the implementation plan.

### Platform-Engineering Guardrails

Before executing, load the platform-engineering skill context based on detected platforms from `.develop/00-context.md`:

- **All projects**: Keep `server-validation` and `secrets-management` rules active
- **Web (SPA/PWA)**: Also load `auth-tokens`, `xss-csp`, `api-security`
- **Mobile**: Also load `platform-security` (mobile section), `auth-tokens`
- **Electron**: Also load `platform-security` (Electron section), `xss-csp`
- **Tauri**: Also load `platform-security` (Tauri section)

During execution, check each implementation step against loaded rules. If a MUST rule would be violated, STOP and flag it before writing the code.

### Stack-Aware UI Agent Loading

If Step 1E produced a Layout Specification, load the appropriate agents/skills based on the detected stack from `.develop/00-context.md`:

| Detected Stack | UI Layer (agents/skills) | Backend Layer (agents) |
|---------------|--------------------------|------------------------|
| **Web** (React, Vue, Svelte, vanilla) | `frontend:web-designer` + `frontend:frontend` skill | -- |
| **Tauri** | `frontend:web-designer` + `frontend:frontend` skill | `tauri-development:tauri-desktop` + `tauri-development:rust-engineer` |
| **Electron** | `frontend:web-designer` + `frontend:frontend` skill | general-purpose (Node.js) |
| **React Native** | `frontend:frontend` skill (adapted for mobile) | general-purpose |
| **Python GUI** (Qt/GTK) | general-purpose | `python-development:python-pro` |
| **Flutter** | general-purpose | general-purpose (Dart) |

During execution:
- For UI implementation tasks (HTML, CSS, components), consult the loaded UI layer agents for styling, animations, and responsive patterns
- For backend-of-frontend tasks (Tauri commands, IPC, state management), consult the loaded backend layer agents
- Both layers remain available throughout Phase 3 -- the executing agent should reference them when implementing UI-related plan tasks

### Execution Loop

Follow the executing-plans skill process with batch execution.

Execute tasks in batches of 3:

1. **For each task in the batch:**
   - Mark as in_progress
   - Follow each step exactly (test first, then implement)
   - Run all verification commands
   - Check implementation against platform-engineering MUST rules
   - If a test fails: STOP the batch, report the failure, ask the user how to proceed
   - If a platform-engineering MUST rule is violated: STOP, report the violation with rule reference and fix suggestion
   - Mark as completed

2. **After each batch:**
   - Show what was implemented
   - Show verification output (test results)
   - Ask: "Ready for feedback on this batch?"

3. **Wait for user feedback** before starting the next batch:
   - Apply any requested changes
   - Continue to next batch

4. **Repeat** until all tasks are complete.

Log each task's execution to `.develop/03-execution-log.md`:

```markdown
# Phase 3: Execution Log

## Task 1: [name]
- Status: completed
- Files changed: [list]
- Tests: [pass/fail]
- Platform-engineering checks: [pass/violations]
- Commit: [hash]

## Task 2: [name]
...

## Execution Summary
- Tasks completed: [X/Y]
- Tests passing: [count]
- Commits made: [count]
- Platform-engineering violations caught: [count]
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
- Platform violations caught and fixed: [count]

Please review:
- .develop/03-execution-log.md
- Run the test suite to verify: [test command]

1. Continue -- review the changes with architecture, security, platform, and pattern analysis
2. Fix issues -- address problems before review
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 4 until the user approves.

---

## Phase 4: Review Changes

Run the review process -- fire all 4 review agents **in parallel**:

First, get the diff of all changes made during execution:

```bash
git diff HEAD~[number-of-commits-from-phase-3] --name-only
git diff HEAD~[number-of-commits-from-phase-3] -- [code files only]
```

### Agent A: Architecture & Code Quality

```
Task:
  subagent_type: "senior-review:architect-review"
  description: "Architecture audit of feature implementation"
  prompt: |
    Review the code changes made during feature implementation.
    Focus on code quality and architectural concerns. Skip documentation.

    ## Feature Context
    [Insert summary from .develop/01-design.md]

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
  subagent_type: "senior-review:security-auditor"
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
  subagent_type: "senior-review:pattern-quality-scorer"
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

### Agent D: Platform Engineering Compliance

```
Task:
  subagent_type: "platform-engineering:platform-reviewer"
  description: "Platform engineering compliance review"
  prompt: |
    Review the code changes against the cross-platform development rulebook.

    ## Detected Platforms
    [from .develop/00-context.md]

    ## Changed Files
    [list of changed code files]

    ## Diff
    [git diff output]

    ## Instructions
    Audit against the platform-engineering rulebook for detected platforms.
    Focus on MUST rule violations (Critical) and DO/DON'T rules (Warnings).
    Cover all three pillars: Security, Architecture, Performance.

    Output format: standard platform-reviewer report with severity, file + line, rule reference, and fix.
```

After all agents complete, consolidate into `.develop/04-review.md`:

```markdown
# Phase 4: Code Review

## Overall Score: X/10

## Critical & High Issues
[Merged from all 4 agents, deduplicated]

## Platform Engineering Violations
[MUST rule violations from Agent D]

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
Platform violations: [count]

Top issues:
1. [critical/high issue]
2. [critical/high issue]
3. [critical/high issue]

Please review:
- .develop/04-review.md

1. Continue -- proceed to test verification
2. Fix review issues first -- address findings before continuing
3. Pause -- save progress and stop here
```

If `--strict-mode` is set and there are Critical findings, recommend option 2.

Do NOT proceed to Phase 5 until the user approves.

---

## Phase 5: Test Verification

Run a comprehensive test verification to ensure quality and coverage:

### Step 5A: Run full test suite

```bash
[test command from 00-context.md]
```

If any test fails, STOP and report. Ask the user whether to fix or continue.

### Step 5B: Coverage analysis

If the project has a coverage tool configured (detected from package.json scripts, pytest.ini, etc.), run it:

```bash
[coverage command -- e.g., pytest --cov, npx vitest --coverage, etc.]
```

### Step 5C: Gap analysis

Dispatch the test-writer agent to identify untested paths:

```
Task:
  subagent_type: "testing:test-writer"
  description: "Test gap analysis for feature implementation"
  prompt: |
    Analyze the code changes from this feature implementation and identify untested paths.

    ## Changed Files
    [list of changed code files from .develop/03-execution-log.md]

    ## Existing Tests
    [list of test files created/modified during Phase 3]

    ## Instructions
    DO NOT write tests yet. Only analyze and report:

    1. List every public function/method/endpoint added or modified
    2. For each, check if a test exists that covers:
       - Happy path
       - Error/edge cases
       - Boundary values
    3. Flag any untested or under-tested code paths
    4. Rate overall test coverage confidence: Strong / Adequate / Weak / Insufficient

    Output a structured report of gaps found.
```

If gaps are found and confidence is Weak or Insufficient:
- Generate the missing tests using the test-writer agent
- Run the full suite again to verify new tests pass

### Step 5D: E2E test verification (conditional)

**Trigger when:** UI changes were detected in Phase 1 (Step 1E) AND the project has Playwright or Cypress configured (detected from `package.json` dependencies, `playwright.config.ts`, or `cypress.config.ts`).

**Skip if:** No UI changes or no E2E framework configured.

Use the `testing:e2e-testing-patterns` skill as guidance for writing and reviewing E2E tests:

1. Check if E2E tests already cover the new feature's critical user journeys
2. If not, generate E2E tests following skill patterns (Page Object Model, proper waiting strategies, data-testid selectors)
3. Run the E2E suite:
   ```bash
   npx playwright test  # or npx cypress run
   ```
4. Report results in the test verification output

If E2E tests need to be created, follow the skill's guidance on:
- Page Object Model for reusable page interactions
- Fixtures for test data setup/teardown
- Auto-waiting assertions instead of fixed timeouts
- Network mocking for third-party services

**Output file:** `.develop/05-test-verification.md`

```markdown
# Phase 5: Test Verification

## Test Suite Results
- Total tests: [count]
- Passing: [count]
- Failing: [count]
- Skipped: [count]

## Coverage
- Line coverage: [X%] (if available)
- Branch coverage: [X%] (if available)

## Gap Analysis
- Functions/endpoints analyzed: [count]
- Fully tested: [count]
- Partially tested: [count]
- Untested: [count]
- Coverage confidence: [Strong/Adequate/Weak/Insufficient]

## Tests Added
[List of tests generated to fill gaps, if any]

## E2E Tests (if applicable)
- E2E framework: [Playwright/Cypress/none]
- E2E tests covering feature: [count]
- E2E tests added: [count]
- E2E suite passing: [yes/no/skipped]

## Verification
- All tests passing after gap fill: [yes/no]
```

Update `state.json`: set `current_phase` to "checkpoint-5", add phase 5 to `completed_phases`.

---

## PHASE CHECKPOINT 5 -- User Approval Required

```
Phase 5 complete: Test verification done.

Tests: [passing]/[total] passing
Coverage confidence: [Strong/Adequate/Weak/Insufficient]
Tests added to fill gaps: [count]

Please review:
- .develop/05-test-verification.md

1. Continue -- humanize the code
2. Skip humanize -- go straight to PR creation
3. Add more tests -- improve coverage before continuing
4. Pause -- save progress and stop here
```

Do NOT proceed to Phase 6 until the user approves.

---

## Phase 6: Humanize Code

**Skip if:** `--skip-humanize` flag is set or user chose option 2 at checkpoint.

Read `.develop/04-review.md` to understand which files were changed.

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
    [Insert consistency findings from .develop/04-review.md]

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

Log changes to `.develop/06-humanize-log.md`:

```markdown
# Phase 6: Humanize Log

## Files Modified
[List of files with changes made]

## Changes Made
- [file]: Renamed X to Y, added comment explaining Z
- [file]: Extracted helper function for clarity

## Tests
- All tests still passing: [yes/no]
```

Update `state.json`: set `current_phase` to "checkpoint-6", add phase 6 to `completed_phases`.

---

## Phase 7: Create PR

Generate a PR with full context from the pipeline:

### Step 7A: Prepare PR description

Read all pipeline output files to build a comprehensive PR:

```
Task:
  subagent_type: "general-purpose"
  description: "Generate PR description from pipeline outputs"
  prompt: |
    Generate a pull request description from the feature pipeline outputs.

    ## Design
    [Insert .develop/01-design.md]

    ## Execution Log
    [Insert .develop/03-execution-log.md]

    ## Review Results
    [Insert .develop/04-review.md]

    ## Test Verification
    [Insert .develop/05-test-verification.md]

    ## Instructions
    Write a PR description following this format:

    ## Summary
    [2-3 bullet points: what this PR does and why]

    ## Design Decisions
    [Key decisions from brainstorming with rationale]

    ## Changes
    [Grouped list of changes by component/area]

    ## Testing
    - Tests added: [count]
    - Coverage confidence: [level]
    - Test command: [command]

    ## Review Results
    - Quality Score: [X/10]
    - Critical issues resolved: [count]
    - Platform compliance: [pass/warnings]

    ## Risk Assessment
    [High/Medium/Low with explanation]

    ## Checklist
    - [ ] All tests passing
    - [ ] No critical review findings unresolved
    - [ ] Platform-engineering MUST rules satisfied
    - [ ] Code humanized for readability
```

### Step 7B: Create PR

If working in a worktree (`--worktree` was set):

```bash
# Push the feature branch
git push -u origin [worktree_branch]

# Create PR
gh pr create --title "[PR title]" --body "$(cat <<'EOF'
[generated PR description]
EOF
)"
```

If working on the main branch (no worktree):

```bash
# Create a feature branch from current state
git checkout -b feature/e2e-[slug]
git push -u origin feature/e2e-[slug]

# Create PR
gh pr create --title "[PR title]" --body "$(cat <<'EOF'
[generated PR description]
EOF
)"
```

**Output file:** `.develop/07-pr.md`

```markdown
# Phase 7: Pull Request

## PR URL
[URL from gh pr create]

## Branch
[branch name]

## Title
[PR title]

## Risk Assessment
[High/Medium/Low]
```

Update `state.json`: set `status` to `"complete"`, `last_updated` to current timestamp.

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

Present the final summary:

```
Feature end-to-end pipeline complete for: $ARGUMENTS

## Output Files
- Project Context:    .develop/00-context.md
- Design:            .develop/01-design.md
- Implementation Plan: .develop/02-plan.md
- Execution Log:     .develop/03-execution-log.md
- Code Review:       .develop/04-review.md
- Test Verification: .develop/05-test-verification.md
- Humanize Log:      .develop/06-humanize-log.md [if not skipped]
- Pull Request:      .develop/07-pr.md

## Summary
- Feature: [name]
- Tasks executed: [count]
- Tests passing: [count]
- Coverage confidence: [level]
- Code Quality Score: [X/10]
- Platform compliance: [pass/warnings]
- Files changed: [count]
- PR: [URL]

## Pipeline Duration
- Started: [timestamp]
- Completed: [timestamp]
```

If `--strict-mode` is set and there were Critical review findings that weren't addressed:
```
STRICT MODE: Unresolved critical issues remain. Review .develop/04-review.md before merging.
```
