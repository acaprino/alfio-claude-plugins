---
description: >
  "End-to-end Tauri 2 desktop app pipeline — Rust backend review, Tauri IPC optimization, React performance, layout composition, and UI polish" argument-hint: "<target path or description> [--rust-only] [--frontend-only] [--strict-mode]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Tauri Desktop Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.tauri-pipeline/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, missing files, access issues), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
6. **Respect scope flags.** If `--rust-only` is set, run only Phases 1-2 then skip to completion. If `--frontend-only` is set, skip Phases 1-2 and start at Phase 3.

## Pre-flight Checks

### 0. Dependency check

This command requires agents from other plugins. Before proceeding, verify they are installed:

**Required plugins:**
- `tauri-development` -- rust-engineer, tauri-desktop agents (Phases 1-2)
- `frontend` -- ui-layout-designer, web-designer agents (Phases 4-5)
- `react-development` -- react-performance-optimizer agent (Phase 3)

Check by looking for the agent/skill files. If a required plugin is missing:

- If `tauri-development` is missing and `--frontend-only` is NOT set, STOP and tell the user.
- If `frontend` is missing and `--rust-only` is NOT set, STOP and tell the user.
- If the missing plugin's phases would be skipped by flags, warn but continue.

```
Missing required plugin(s): [list]

This workflow command depends on agents from other ACP plugins.
Install them with:
  claude plugin marketplace add acaprino/alfio-claude-plugins --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/alfio-claude-plugins
```

### 1. Verify Tauri project structure

Check that `src-tauri/` directory and `src-tauri/tauri.conf.json` (or `tauri.conf.json` at root) exist:

```bash
ls src-tauri/tauri.conf.json 2>/dev/null || ls tauri.conf.json 2>/dev/null
```

If neither exists, STOP and tell the user this command requires a Tauri 2 project.

### 2. Check for existing session

Check if `.tauri-pipeline/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask:
  ```
  Found an in-progress pipeline session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```
- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 3. Initialize state

Create `.tauri-pipeline/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "rust_only": false,
    "frontend_only": false,
    "strict_mode": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--rust-only`, `--frontend-only`, and `--strict-mode` flags.

### 4. Identify target scope

Determine what to review from `$ARGUMENTS`:

- If a path is given, verify it exists
- If no path, default to the entire project
- Scan for Rust files (`src-tauri/src/`), frontend files (`src/`), and config files

**Output file:** `.tauri-pipeline/00-scope.md`

```markdown
# Pipeline Scope

## Target
[Description of what is being reviewed]

## Rust Backend Files
[List of .rs files in src-tauri/]

## Frontend Files
[List of .tsx/.jsx/.css files in src/]

## Config Files
[tauri.conf.json, Cargo.toml, package.json]

## Flags
- Rust Only: [yes/no]
- Frontend Only: [yes/no]
- Strict Mode: [yes/no]

## Pipeline Phases
1. Rust Backend Review
2. Tauri IPC & Optimization
3. React Frontend Performance
4. Layout Composition
5. UI Polish & Animations
```

---

## Phase 1: Rust Backend Review

**Skip if:** `--frontend-only` flag is set.

```
Task:
  subagent_type: "rust-engineer"
  description: "Rust backend review for Tauri app"
  prompt: |
    Review the Rust backend of this Tauri 2 desktop application.

    ## Scope
    [Insert contents of .tauri-pipeline/00-scope.md — Rust Backend Files section]

    ## Instructions
    Analyze the Rust code for:
    1. **Ownership & borrowing**: Unnecessary clones, lifetime issues, borrow checker workarounds
    2. **Error handling**: Proper use of Result/Option, error propagation, custom error types
    3. **Command handlers**: Tauri command signatures, async commands, state management
    4. **Memory safety**: Unsafe blocks, FFI boundaries, resource cleanup
    5. **Performance**: Hot paths, allocation patterns, unnecessary copies
    6. **Idiomatic Rust**: Modern patterns, clippy warnings, API design
    7. **Concurrency**: Tokio usage, channel patterns, mutex contention

    For each finding: severity (Critical/High/Medium/Low), file + line, concrete fix.
    Note what's done well.

    Write your findings as a structured markdown document.
```

Write output to `.tauri-pipeline/01-rust-review.md`:

```markdown
# Phase 1: Rust Backend Review

## Findings
[Organized by severity]

## What's Done Well
[Positive observations]

## Key Issues for Phase 2 Context
[Findings that affect Tauri IPC layer]
```

Update `state.json`: set `current_phase` to 2, add phase 1 to `completed_phases`.

---

## Phase 2: Tauri IPC & Optimization

**Skip if:** `--frontend-only` flag is set.

Read `.tauri-pipeline/01-rust-review.md` for context.

```
Task:
  subagent_type: "tauri-desktop"
  description: "Tauri IPC architecture and optimization review"
  prompt: |
    Review the Tauri 2 IPC architecture, plugin usage, and optimization opportunities.

    ## Scope
    [Insert contents of .tauri-pipeline/00-scope.md]

    ## Phase 1 Context
    [Insert contents of .tauri-pipeline/01-rust-review.md — Key Issues section]

    ## Instructions
    Analyze for:
    1. **IPC architecture**: Command design, payload serialization, batch operations
    2. **State management**: Tauri state containers, shared state between commands
    3. **Plugin usage**: Are plugins configured correctly? Missing capabilities?
    4. **Security**: CSP configuration, allowed origins, command permissions
    5. **Window management**: Multi-window IPC, WebView configuration
    6. **Build optimization**: Bundle size, feature flags, Cargo profile settings
    7. **Event system**: Custom events, event listeners, cleanup patterns

    For each finding: severity, file, issue, concrete fix recommendation.
    Note what's done well.

    Write your findings as a structured markdown document.
```

Write output to `.tauri-pipeline/02-tauri-optimization.md`:

```markdown
# Phase 2: Tauri IPC & Optimization

## Findings
[Organized by severity]

## What's Done Well
[Positive observations]

## Key Issues for Frontend Context
[Findings that affect the frontend layer]
```

Update `state.json`: set `current_phase` to "checkpoint-1", add phase 2 to `completed_phases`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

Display a summary of findings from Phases 1-2 and ask:

```
Phases 1-2 complete: Rust backend and Tauri IPC reviews done.

Summary:
- Rust Backend: [X critical, Y high, Z medium findings]
- Tauri IPC: [X critical, Y high, Z medium findings]

Please review:
- .tauri-pipeline/01-rust-review.md
- .tauri-pipeline/02-tauri-optimization.md

1. Continue -- proceed to React frontend performance review
2. Fix critical issues first -- I'll address backend findings before continuing
3. Pause -- save progress and stop here
```

If `--strict-mode` flag is set and there are Critical findings, recommend option 2.

If `--rust-only` flag is set, skip to **Completion** after this checkpoint.

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 3: React Frontend Performance

**Skip if:** `--rust-only` flag is set.

Read `.tauri-pipeline/02-tauri-optimization.md` for IPC context.

```
Task:
  subagent_type: "react-performance-optimizer"
  description: "React frontend performance review for Tauri app"
  prompt: |
    Analyze the React frontend of this Tauri 2 desktop application for performance.

    ## Scope
    [Insert contents of .tauri-pipeline/00-scope.md — Frontend Files section]

    ## Tauri Context
    [Insert .tauri-pipeline/02-tauri-optimization.md — Key Issues for Frontend section]

    ## Instructions
    Analyze for:
    1. **Re-render optimization**: Unnecessary re-renders, missing memoization, expensive computations in render
    2. **State management**: Global vs local state, state update batching, context overhead
    3. **IPC integration**: Are Tauri invoke calls debounced? Loading states? Error boundaries?
    4. **Bundle optimization**: Code splitting, lazy loading, tree shaking effectiveness
    5. **React patterns**: Hook dependencies, effect cleanup, key usage in lists
    6. **Desktop-specific**: Window resize handling, system tray integration, native menu sync
    7. **Data fetching**: Caching strategy for Tauri commands, stale data handling

    For each finding: severity, file, issue, concrete fix.
    Note what's done well.

    Write your findings as a structured markdown document.
```

Write output to `.tauri-pipeline/03-react-performance.md`.

Update `state.json`: set `current_phase` to 4, add phase 3 to `completed_phases`.

---

## Phase 4: Layout Composition

Read `.tauri-pipeline/03-react-performance.md` for context.

```
Task:
  subagent_type: "ui-layout-designer"
  description: "Layout composition review for Tauri desktop app"
  prompt: |
    Review the layout system and spatial design of this Tauri 2 desktop application.

    ## Scope
    [Insert contents of .tauri-pipeline/00-scope.md — Frontend Files section]

    ## Instructions
    Analyze for:
    1. **Desktop layout patterns**: Sidebar + content, panel splits, resizable panes
    2. **Grid system**: Consistent layout grid, CSS Grid/Flexbox usage
    3. **Spacing scale**: Consistent spacing tokens or arbitrary values
    4. **Window resizing**: Layout behavior on window resize, minimum sizes
    5. **Typography system**: Font scale, readability at different DPIs
    6. **Content overflow**: Scroll behavior, truncation, virtualized lists
    7. **Desktop conventions**: Native-feeling chrome, toolbar layout, status bar

    For each finding: severity, file, issue, concrete fix.
    Note what's done well.

    Write your findings as a structured markdown document.
```

Write output to `.tauri-pipeline/04-layout.md`.

Update `state.json`: set `current_phase` to 5, add phase 4 to `completed_phases`.

---

## Phase 5: UI Polish & Animations

Read `.tauri-pipeline/03-react-performance.md` and `.tauri-pipeline/04-layout.md` for context.

```
Task:
  subagent_type: "web-designer"
  description: "UI polish and animation review for Tauri desktop app"
  prompt: |
    Review the visual polish, animations, and micro-interactions of this Tauri 2 desktop app.

    ## Scope
    [Insert contents of .tauri-pipeline/00-scope.md — Frontend Files section]

    ## Layout Context
    [Insert key findings from .tauri-pipeline/04-layout.md]

    ## Instructions
    Analyze for:
    1. **Visual consistency**: Color palette, border-radius, shadows, elevation system
    2. **Animations**: Transition quality, GPU acceleration, prefers-reduced-motion
    3. **Micro-interactions**: Button feedback, hover states, focus indicators
    4. **Loading states**: Skeleton screens, progress indicators, optimistic updates
    5. **Dark mode**: Theme switching, system preference detection, color adaptation
    6. **Desktop feel**: Native-feeling interactions, drag handles, context menus
    7. **Polish details**: Empty states, error states, onboarding, first-run experience

    For each finding: severity, file, issue, concrete fix.
    Note what's done well.

    Write your findings as a structured markdown document.
```

Write output to `.tauri-pipeline/05-polish.md`.

Update `state.json`: set `current_phase` to 6, add phase 5 to `completed_phases`.

---

## Phase 6: Consolidated Report

Read all `.tauri-pipeline/*.md` files (01 through 05). Generate the final consolidated report.

**Output file:** `.tauri-pipeline/06-final-report.md`

```markdown
# Tauri Desktop Pipeline Report

## Target
[From 00-scope.md]

## Executive Summary
[2-3 sentence overview of overall app health]

## Score Summary

| Layer               | Critical | High | Medium | Low |
|---------------------|----------|------|--------|-----|
| Rust Backend        | X        | X    | X      | X   |
| Tauri IPC           | X        | X    | X      | X   |
| React Performance   | X        | X    | X      | X   |
| Layout              | X        | X    | X      | X   |
| UI Polish           | X        | X    | X      | X   |
| **Total**           | **X**    | **X**| **X**  | **X**|

## Critical & High Priority Issues
[All critical and high findings across all phases, with source phase reference]

## Medium & Low Priority Issues
[Grouped by phase]

## What's Done Well
[Positive findings from all phases]

## Recommended Action Plan
1. [Ordered list of recommended actions, starting with critical items]
2. [Group related fixes by layer]

## Pipeline Metadata
- Review date: [timestamp]
- Phases completed: [list]
- Flags applied: [list active flags]
```

Update `state.json`: set `status` to `"complete"`, `last_updated` to current timestamp.

---

## CLAUDE.md Alignment Check

After the review, check if findings suggest the project's `CLAUDE.md` is stale:

1. Read `CLAUDE.md` (if it exists)
2. Cross-reference review findings with documented conventions, structure, and workflows
3. If any documented information is outdated or missing, note it in the review output and propose updates to the user

---

## Completion

Present the final summary:

```
Tauri desktop pipeline complete for: $ARGUMENTS

## Output Files
- Scope: .tauri-pipeline/00-scope.md
- Rust Backend: .tauri-pipeline/01-rust-review.md
- Tauri IPC: .tauri-pipeline/02-tauri-optimization.md
- React Performance: .tauri-pipeline/03-react-performance.md
- Layout: .tauri-pipeline/04-layout.md
- UI Polish: .tauri-pipeline/05-polish.md
- Final Report: .tauri-pipeline/06-final-report.md

## Summary
- Total findings: [count]
- Critical: [X] | High: [Y] | Medium: [Z] | Low: [W]

## Next Steps
1. Review the full report at .tauri-pipeline/06-final-report.md
2. Address Critical issues immediately
3. Plan High priority fixes for current sprint
```

If `--strict-mode` is set and Critical findings exist:
```
STRICT MODE: Critical issues found across the pipeline. Recommend addressing before shipping.
```
