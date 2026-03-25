---
description: >
  "End-to-end mobile app pipeline -- competitor analysis via ADB, brainstorm features, UX design, implementation plan, scaffold Tauri 2 mobile app, Rust backend review, and IPC optimization" argument-hint: "<app-package-name or description> [--device <device-id>] [--skip-scaffold] [--skip-review] [--strict-mode]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Mobile Tauri Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.mobile-tauri-pipeline/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, ADB connection, missing files), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
6. **Brainstorming is interactive.** Phase 2 MUST involve back-and-forth with the user -- ask questions one at a time, propose approaches, get approval.

## Pre-flight Checks

### 0. Dependency check

This command requires agents and skills from other plugins. Before proceeding, verify they are installed:

**Required plugins:**
- `app-analyzer` -- app-analyzer agent (Phase 1)
- `ai-tooling` -- brainstorming, writing-plans, executing-plans skills (Phases 2, 5, 6)
- `frontend` -- web-designer agent (Phase 3)

**Optional plugins:**
- `tauri-development` -- tauri-mobile skill, rust-engineer, tauri-desktop agents (Phases 4, 7, 8)
- `senior-review` -- code-auditor, security-auditor agents (Phase 9)
- `humanize` -- humanize agent (Phase 10)

Check by looking for the agent/skill files. If a required plugin is missing, STOP and tell the user:

```
Missing required plugin(s): [list]

This workflow command depends on agents and skills from other figs plugins.
Install them with:
  claude plugin marketplace add acaprino/figs --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/figs
```

If only optional plugins are missing, warn but continue (skip their phases).

### 1. Verify ADB connection

```bash
adb devices
```

- If no devices listed: STOP and tell the user to connect a device or start an emulator.
- If `--device <device-id>` flag is provided, verify that specific device is connected.
- If multiple devices and no `--device` flag, ask the user which device to use.

### 2. Check for existing session

Check if `.mobile-tauri-pipeline/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask:
  ```
  Found an in-progress mobile Tauri pipeline session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```
- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 3. Initialize state

Create `.mobile-tauri-pipeline/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "device": null,
    "skip_scaffold": false,
    "skip_review": false,
    "strict_mode": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--device`, `--skip-scaffold`, `--skip-review`, and `--strict-mode` flags.

---

## PART A: MOBILE INTELLIGENCE (Phases 1-3)

---

## Phase 1: Competitor App Analysis

Use the app-analyzer agent to analyze the target app via ADB.

### Process

1. **Launch the target app** on the connected device:
   ```bash
   adb shell monkey -p <package-name> -c android.intent.category.LAUNCHER 1
   ```

2. **Navigate key screens** -- for each screen:
   - Capture screenshot: `adb exec-out screencap -p > .mobile-tauri-pipeline/screenshots/screen-NN.png`
   - Record the screen name, purpose, and UI elements observed
   - Note navigation patterns, gestures, transitions

3. **Document the following:**
   - App architecture (tab-based, drawer, stack navigation)
   - Key user flows (onboarding, core action, settings)
   - UX patterns (loading states, error handling, empty states)
   - Design language (colors, typography, spacing, icons)
   - Unique features and differentiators
   - Pain points and UX friction

**Output file:** `.mobile-tauri-pipeline/01-competitor-analysis.md`

```markdown
# Phase 1: Competitor App Analysis

## App Overview
- Package: [package name]
- Category: [app category]
- Device: [device model]

## Screen Inventory
[List of screens with screenshot references]

## Navigation Architecture
[Tab bar / drawer / stack description]

## Key User Flows
[Step-by-step flow descriptions]

## UX Patterns
[Loading states, error handling, transitions, gestures]

## Design Language
[Colors, typography, spacing, iconography]

## Strengths
[What the app does well]

## Weaknesses & Pain Points
[UX friction, missing features, poor patterns]

## Screenshots
[References to .mobile-tauri-pipeline/screenshots/]
```

Update `state.json`: set `current_phase` to "checkpoint-1", add phase 1 to `completed_phases`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

```
Phase 1 complete: Competitor app analyzed.

App: [package name]
Screens documented: [count]
Screenshots captured: [count]

Key findings:
- Strengths: [top 3]
- Weaknesses: [top 3]

Please review:
- .mobile-tauri-pipeline/01-competitor-analysis.md
- .mobile-tauri-pipeline/screenshots/

1. Continue -- proceed to brainstorming differentiating features
2. Capture more screens -- analyze additional app areas
3. Pause -- save progress and stop here
```

Do NOT proceed until the user approves.

---

## Phase 2: Brainstorm Differentiating Features

Read `.mobile-tauri-pipeline/01-competitor-analysis.md` for context.

Follow the brainstorming skill process -- this phase is **interactive**:

### Step 2A: Explore context

Review the competitor analysis. Identify biggest opportunities from the competitor's weaknesses.

### Step 2B: Ask clarifying questions (one at a time)

- What is the target audience?
- Which competitor weaknesses matter most?
- Features to include or exclude?
- Primary differentiator?
- Target platform priority (Android-first, iOS-first, both)?

Use AskUserQuestion with multiple-choice options. One question per message.

### Step 2C: Propose approaches

Propose 2-3 differentiation strategies:
- Feature parity + UX improvements
- Niche focus with fewer but better features
- Platform-native features the competitor doesn't leverage

### Step 2D: Present design

Present features organized by priority: Must-have (v1), Nice-to-have (v1.1), Future (v2). Get user approval.

**Output file:** `.mobile-tauri-pipeline/02-brainstorm.md`

Update `state.json`: set `current_phase` to 3, add phase 2 to `completed_phases`.

---

## Phase 3: UX Design

Read `.mobile-tauri-pipeline/01-competitor-analysis.md` and `.mobile-tauri-pipeline/02-brainstorm.md`.

```
Task:
  subagent_type: "web-designer"
  description: "Design improved UX for mobile app"
  prompt: |
    Design the UX for a new mobile app that improves on a competitor's weaknesses.

    ## Competitor Analysis
    [Insert contents of .mobile-tauri-pipeline/01-competitor-analysis.md]

    ## Feature Set
    [Insert contents of .mobile-tauri-pipeline/02-brainstorm.md]

    ## Instructions
    Design:
    1. **Information architecture**: Screen hierarchy, navigation patterns
    2. **User flows**: Primary flow, onboarding, error recovery
    3. **Component system**: Reusable components, design tokens
    4. **Interaction patterns**: Gestures, transitions, micro-interactions
    5. **Accessibility**: Touch targets, contrast, screen reader support
    6. **Platform conventions**: Material Design 3 / iOS HIG compliance
    7. **Improvements**: Specific UX improvements addressing competitor weaknesses

    For each screen: purpose, layout, key interactions, how it improves on competitor.
    Write as structured markdown.
```

**Output file:** `.mobile-tauri-pipeline/03-ux-design.md`

Update `state.json`: set `current_phase` to "checkpoint-2", add phase 3 to `completed_phases`.

---

## PHASE CHECKPOINT 2 -- User Approval Required

```
Phase 3 complete: UX design done.

Screens designed: [count]
User flows mapped: [count]
Components defined: [count]

Please review:
- .mobile-tauri-pipeline/03-ux-design.md

1. Continue -- proceed to scaffold and implementation
2. Revise design -- adjust UX before building
3. Pause -- save progress and stop here
```

Do NOT proceed until the user approves.

---

## PART B: BUILD (Phases 4-6)

---

## Phase 4: Scaffold Tauri 2 Mobile App

**Skip if:** `--skip-scaffold` flag is set or `tauri-development` plugin is missing.

Read all prior phase files for context.

### Step 4A: Initialize Tauri 2 project

- Create project with `npm create tauri-app@latest` or equivalent
- Configure for mobile targets (Android and/or iOS)
- Set up project structure from UX design

### Step 4B: Configure mobile capabilities

- Android manifest permissions
- Tauri capabilities for mobile plugins
- Required Tauri plugins (biometric, geolocation, notifications, etc.)

### Step 4C: Create base architecture

- Frontend framework (React + TypeScript)
- Navigation structure from UX design
- State management foundation
- IPC command stubs

**Output file:** `.mobile-tauri-pipeline/04-scaffold-log.md`

```markdown
# Phase 4: Scaffold Log

## Project Created
- Location: [path]
- Framework: [React/Vue/etc.]
- Targets: [Android/iOS/both]

## Files Created
[List of files]

## Configured Plugins
[List of Tauri plugins]

## Architecture
[Base architecture decisions]
```

Update `state.json`: set `current_phase` to 5, add phase 4 to `completed_phases`.

---

## Phase 5: Write Implementation Plan

Read all prior phase files for context.

Follow the writing-plans skill process:

```
Task:
  subagent_type: "general-purpose"
  description: "Write implementation plan for mobile app"
  prompt: |
    You are using the writing-plans skill. Write a comprehensive, bite-sized implementation plan.

    ## Context
    [Insert summaries from all prior phases: competitor analysis, brainstorm, UX design, scaffold]

    ## Instructions
    Create a plan with bite-sized tasks following TDD principles:

    1. **Core architecture**: State management, navigation, IPC layer
    2. **Feature tasks**: One task per must-have feature, ordered by dependency
    3. **Rust backend**: Tauri commands, state management, plugin integration
    4. **Testing strategy**: Unit tests, integration tests, device testing
    5. **Polish tasks**: Animations, transitions, accessibility

    Each task: exact file paths, test-first steps, verification commands, commit messages.
    Order by dependency. Each task should be 2-5 minutes of work.

    Write as structured markdown following the writing-plans format.
```

**Output file:** `.mobile-tauri-pipeline/05-implementation-plan.md`

Update `state.json`: set `current_phase` to "checkpoint-3", add phase 5 to `completed_phases`.

---

## PHASE CHECKPOINT 3 -- User Approval Required

```
Phase 5 complete: Implementation plan written.

Plan summary:
- Total tasks: [count]
- Features covered: [count] must-have
- Rust commands: [count]
- Tests planned: [count]

Please review:
- .mobile-tauri-pipeline/05-implementation-plan.md

1. Continue -- execute the plan
2. Revise plan -- adjust before executing
3. Pause -- save progress and stop here
```

Do NOT proceed until the user approves.

---

## Phase 6: Execute Plan

Read `.mobile-tauri-pipeline/05-implementation-plan.md` for the plan.

Follow the executing-plans skill process with batch execution:

### Execution Loop

Execute tasks in batches of 3:

1. **For each task in the batch:**
   - Mark as in_progress
   - Follow each step exactly (test first, then implement)
   - Run all verification commands
   - If a test fails: STOP the batch, report the failure, ask the user
   - Mark as completed

2. **After each batch:**
   - Show what was implemented
   - Show verification output (test results)
   - Ask: "Ready for feedback on this batch?"

3. **Wait for user feedback** before starting next batch.

4. **Repeat** until all tasks are complete.

Log to `.mobile-tauri-pipeline/06-execution-log.md`:

```markdown
# Phase 6: Execution Log

## Task 1: [name]
- Status: completed
- Files changed: [list]
- Tests: [pass/fail]
- Commit: [hash]

## Execution Summary
- Tasks completed: [X/Y]
- Tests passing: [count]
- Commits made: [count]
```

Update `state.json`: set `current_phase` to "checkpoint-4", add phase 6 to `completed_phases`.

---

## PHASE CHECKPOINT 4 -- User Approval Required

```
Phase 6 complete: Implementation executed.

Tasks completed: [X/Y]
Tests passing: [count]
Commits made: [count]

1. Continue -- proceed to Tauri backend review and optimization
2. Fix issues -- address problems before review
3. Skip review -- finish without review (same as --skip-review)
4. Pause -- save progress
```

If `--skip-review` is set, skip to Completion.

Do NOT proceed until the user approves.

---

## PART C: REVIEW & POLISH (Phases 7-10)

**Skip all of Part C if `--skip-review` flag is set.**

---

## Phase 7: Rust Backend Review

**Skip if:** `tauri-development` plugin is missing.

```
Task:
  subagent_type: "tauri-development:rust-engineer"
  description: "Rust backend review for Tauri mobile app"
  prompt: |
    Review the Rust backend of this Tauri 2 mobile application.

    ## Context
    [Insert scaffold and execution context from prior phases]

    ## Instructions
    Analyze the Rust code for:
    1. **Ownership & borrowing**: Unnecessary clones, lifetime issues
    2. **Error handling**: Result/Option usage, error propagation
    3. **Command handlers**: Tauri command signatures, async commands, state management
    4. **Memory safety**: Unsafe blocks, resource cleanup
    5. **Performance**: Hot paths, allocation patterns
    6. **Mobile-specific**: Battery impact, background processing, permissions
    7. **Concurrency**: Tokio usage, channel patterns

    For each finding: severity, file + line, concrete fix.
    Write as structured markdown.
```

**Output file:** `.mobile-tauri-pipeline/07-rust-review.md`

Update `state.json`: set `current_phase` to 8, add phase 7 to `completed_phases`.

---

## Phase 8: Tauri IPC & Mobile Optimization

**Skip if:** `tauri-development` plugin is missing.

Read `.mobile-tauri-pipeline/07-rust-review.md` for context.

```
Task:
  subagent_type: "tauri-development:tauri-desktop"
  description: "Tauri IPC and mobile optimization review"
  prompt: |
    Review the Tauri 2 IPC architecture and mobile-specific optimizations.

    ## Rust Review Context
    [Insert key findings from .mobile-tauri-pipeline/07-rust-review.md]

    ## Instructions
    Analyze:
    1. **IPC architecture**: Command design, payload serialization, batch operations
    2. **Mobile optimization**: Startup time, memory footprint, battery impact
    3. **Plugin usage**: Mobile plugins configured correctly? Missing capabilities?
    4. **Security**: CSP, allowed origins, command permissions
    5. **Build optimization**: Bundle size, feature flags, mobile-specific Cargo settings
    6. **Platform differences**: Android vs iOS behavior, platform-specific code

    For each finding: severity, file, concrete fix.
    Write as structured markdown.
```

**Output file:** `.mobile-tauri-pipeline/08-tauri-optimization.md`

Update `state.json`: set `current_phase` to 9, add phase 8 to `completed_phases`.

---

## Phase 9: Senior Code Review

**Skip if:** `senior-review` plugin is missing.

Run 3 review agents in parallel:

### Agent A: Architecture Review

```
Task:
  subagent_type: "senior-review:code-auditor"
  description: "Code audit of mobile app"
  prompt: |
    Review the architecture of this Tauri 2 mobile application.

    ## Context
    [Insert key findings from phases 7 and 8]

    ## Instructions
    Focus on:
    1. Component boundaries and separation of concerns
    2. Dependency management between frontend and Rust backend
    3. API design of Tauri commands
    4. State management architecture
    5. Mobile-specific architectural decisions

    For each finding: severity, file, concrete fix.
```

### Agent B: Security Audit

```
Task:
  subagent_type: "senior-review:security-auditor"
  description: "Security audit of mobile app"
  prompt: |
    Security audit of this Tauri 2 mobile application.

    ## Context
    [Insert key findings from phases 7 and 8]

    ## Instructions
    Focus on:
    1. Mobile-specific security: data storage, biometric auth, certificate pinning
    2. IPC security: command permissions, input validation
    3. Network security: HTTPS enforcement, API key management
    4. Local data: SQLite encryption, credential storage
    5. Platform security: Android permissions, iOS entitlements

    For each finding: severity, CWE, file, attack scenario, fix.
```

### Agent C: Pattern & Quality Scoring

```
Task:
  subagent_type: "senior-review:code-auditor"
  description: "Quality scoring of mobile app"
  prompt: |
    Pattern consistency and quality scoring for this Tauri 2 mobile application.

    ## Context
    [Insert all prior review findings]

    ## Instructions
    - Pattern consistency across Rust and TypeScript code
    - Anti-pattern checklist
    - All six mental models
    - Quality score: Security, Performance, Maintainability, Architecture, Overall

    Write as structured markdown with score table.
```

After all complete, consolidate into `.mobile-tauri-pipeline/09-code-review.md`:

```markdown
# Phase 9: Senior Code Review

## Overall Score: X/10

## Architecture Findings
[From Agent A]

## Security Findings
[From Agent B]

## Quality & Pattern Findings
[From Agent C]

## Score Table

| Category        | Score |
|-----------------|-------|
| Security        | X/10  |
| Performance     | X/10  |
| Architecture    | X/10  |
| Maintainability | X/10  |
| **Overall**     | **X/10** |
```

Update `state.json`: set `current_phase` to 10, add phase 9 to `completed_phases`.

---

## Phase 10: Humanize Code

**Skip if:** `humanize` plugin is missing.

```
Task:
  subagent_type: "humanize:humanize"
  description: "Humanize mobile app code"
  prompt: |
    Improve readability of recently implemented code. Do NOT change behavior.

    ## Changed Files
    [List from execution log]

    ## Review Context
    [Pattern findings from .mobile-tauri-pipeline/09-code-review.md]

    ## Instructions
    1. Improve variable/function names
    2. Add brief comments where logic isn't self-evident
    3. Improve structure for readability
    4. Ensure consistent style
    5. Remove AI-generated boilerplate

    Run tests after changes.
```

**Output file:** `.mobile-tauri-pipeline/10-humanize-log.md`

Update `state.json`: set `status` to `"complete"`.

---

## Completion

Present the final summary:

```
Mobile Tauri pipeline complete for: $ARGUMENTS

## Output Files
### Intelligence
- Competitor Analysis: .mobile-tauri-pipeline/01-competitor-analysis.md
- Feature Brainstorm: .mobile-tauri-pipeline/02-brainstorm.md
- UX Design: .mobile-tauri-pipeline/03-ux-design.md
- Screenshots: .mobile-tauri-pipeline/screenshots/

### Build
- Scaffold Log: .mobile-tauri-pipeline/04-scaffold-log.md
- Implementation Plan: .mobile-tauri-pipeline/05-implementation-plan.md
- Execution Log: .mobile-tauri-pipeline/06-execution-log.md

### Review
- Rust Review: .mobile-tauri-pipeline/07-rust-review.md
- Tauri Optimization: .mobile-tauri-pipeline/08-tauri-optimization.md
- Code Review: .mobile-tauri-pipeline/09-code-review.md
- Humanize Log: .mobile-tauri-pipeline/10-humanize-log.md

## Summary
- Competitor screens analyzed: [count]
- Features implemented: [count]
- Tasks completed: [count]
- Code Quality Score: [X/10]

## Next Steps
1. Review .mobile-tauri-pipeline/09-code-review.md for findings
2. Test on physical device: adb install [apk path]
3. Address Critical/High issues before release
```

If `--strict-mode` and Critical findings exist:
```
STRICT MODE: Critical issues found. Review before releasing.
```
