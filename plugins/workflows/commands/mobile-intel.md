---
description: >
  "Competitive mobile intelligence pipeline — analyze competitor Android app via ADB, brainstorm differentiating features, design improved UX, plan implementation, and scaffold Tauri 2 mobile app" argument-hint: "<app-package-name or description> [--device <device-id>] [--skip-scaffold]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Mobile Intelligence Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.mobile-intel/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, ADB connection, missing files), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
6. **Brainstorming is interactive.** Phase 2 MUST involve back-and-forth with the user -- ask questions one at a time, propose approaches, get approval.

## Pre-flight Checks

### 0. Dependency check

This command requires agents and skills from other plugins. Before proceeding, verify they are installed:

**Required plugins:**
- `app-analyzer` -- app-analyzer agent (Phase 1)
- `frontend` -- web-designer agent (Phase 3)
- `ai-tooling` -- brainstorming, writing-plans skills (Phases 2, 4)

**Optional plugins:**
- `tauri-development` -- tauri-mobile skill (Phase 5, skip scaffold if missing)

Check by looking for the agent/skill files. If a required plugin is missing, STOP and tell the user:

```
Missing required plugin(s): [list]

This workflow command depends on agents and skills from other ACP plugins.
Install them with:
  claude plugin marketplace add acaprino/alfio-claude-plugins --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/alfio-claude-plugins
```

If only `tauri-development` is missing, warn but continue (treat as `--skip-scaffold`).

### 1. Verify ADB connection

```bash
adb devices
```

- If no devices listed: STOP and tell the user to connect a device or start an emulator.
- If `--device <device-id>` flag is provided, verify that specific device is connected.
- If multiple devices and no `--device` flag, ask the user which device to use.

### 2. Check for existing session

Check if `.mobile-intel/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask:
  ```
  Found an in-progress mobile intelligence session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```
- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 3. Initialize state

Create `.mobile-intel/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "device": null,
    "skip_scaffold": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--device` and `--skip-scaffold` flags.

---

## Phase 1: Competitor App Analysis

Use the app-analyzer agent to analyze the target app via ADB.

### Process

1. **Launch the target app** on the connected device:
   ```bash
   adb shell monkey -p <package-name> -c android.intent.category.LAUNCHER 1
   ```

2. **Navigate key screens** — for each screen:
   - Capture screenshot: `adb exec-out screencap -p > .mobile-intel/screenshots/screen-NN.png`
   - Record the screen name, purpose, and UI elements observed
   - Note navigation patterns, gestures, transitions

3. **Document the following:**
   - App architecture (tab-based, drawer, stack navigation)
   - Key user flows (onboarding, core action, settings)
   - UX patterns (loading states, error handling, empty states)
   - Design language (colors, typography, spacing, icons)
   - Unique features and differentiators
   - Pain points and UX friction

**Output file:** `.mobile-intel/01-competitor-analysis.md`

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
[References to .mobile-intel/screenshots/]
```

Update `state.json`: set `current_phase` to "checkpoint-1", add phase 1 to `completed_phases`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

Display a summary of the competitor analysis:

```
Phase 1 complete: Competitor app analyzed.

App: [package name]
Screens documented: [count]
Screenshots captured: [count]

Key findings:
- Strengths: [top 3]
- Weaknesses: [top 3]

Please review:
- .mobile-intel/01-competitor-analysis.md
- .mobile-intel/screenshots/

1. Continue -- proceed to brainstorming differentiating features
2. Capture more screens -- I need to analyze additional app areas
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 2 until the user approves.

---

## Phase 2: Brainstorm Differentiating Features

Read `.mobile-intel/01-competitor-analysis.md` for full context.

Follow the brainstorming skill process — this phase is **interactive**:

### Step 2A: Explore context

Review the competitor analysis findings. Identify the biggest opportunities based on the competitor's weaknesses and pain points.

### Step 2B: Ask clarifying questions (one at a time)

Ask the user questions to understand their vision:

- What is the target audience for your app?
- Which of the competitor's weaknesses are most important to address?
- Are there features you definitely want to include or exclude?
- What's the app's primary differentiator?
- What's the target platform priority (Android-first, iOS-first, both)?

Use AskUserQuestion with multiple-choice options where possible. One question per message.

### Step 2C: Propose approaches

Based on the analysis and user answers, propose 2-3 differentiation strategies:

- Feature parity + UX improvements
- Niche focus with fewer but better features
- Platform-native features the competitor doesn't leverage

Lead with your recommendation and explain why.

### Step 2D: Present design

Present the brainstormed feature set organized by priority:

- Must-have features (v1)
- Nice-to-have features (v1.1)
- Future considerations (v2)

Get user approval.

**Output file:** `.mobile-intel/02-brainstorm.md`

```markdown
# Phase 2: Feature Brainstorm

## Competitor Weaknesses Targeted
[Which pain points we're addressing]

## Target Audience
[User's target audience]

## Differentiation Strategy
[Selected approach]

## Feature Set

### Must-Have (v1)
[Prioritized feature list with rationale]

### Nice-to-Have (v1.1)
[Secondary features]

### Future (v2)
[Long-term features]

## Design Decisions
[Key decisions made during brainstorming]
```

Update `state.json`: set `current_phase` to "checkpoint-2", add phase 2 to `completed_phases`.

---

## PHASE CHECKPOINT 2 -- User Approval Required

```
Phase 2 complete: Feature brainstorm finalized.

Features planned:
- Must-have: [count] features
- Nice-to-have: [count] features
- Future: [count] features

Please review:
- .mobile-intel/02-brainstorm.md

1. Continue -- proceed to UX design
2. Revise features -- adjust the feature set before designing
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 3: UX Design

Read `.mobile-intel/01-competitor-analysis.md` and `.mobile-intel/02-brainstorm.md` for context.

```
Task:
  subagent_type: "web-designer"
  description: "Design improved UX for mobile app based on competitor analysis"
  prompt: |
    Design the UX for a new mobile app that improves on a competitor's weaknesses.

    ## Competitor Analysis
    [Insert contents of .mobile-intel/01-competitor-analysis.md]

    ## Feature Set
    [Insert contents of .mobile-intel/02-brainstorm.md]

    ## Instructions
    Design:
    1. **Information architecture**: Screen hierarchy, navigation patterns
    2. **User flows**: Primary flow, onboarding, error recovery
    3. **Component system**: Reusable components, design tokens
    4. **Interaction patterns**: Gestures, transitions, micro-interactions
    5. **Accessibility**: Touch targets, contrast, screen reader support
    6. **Platform conventions**: Material Design 3 / iOS HIG compliance
    7. **Improvements over competitor**: Specific UX improvements addressing identified weaknesses

    For each screen, describe:
    - Purpose and content
    - Layout structure
    - Key interactions
    - How it improves on the competitor

    Write your findings as a structured markdown document.
```

**Output file:** `.mobile-intel/03-ux-design.md`

Update `state.json`: set `current_phase` to 4, add phase 3 to `completed_phases`.

---

## Phase 4: Implementation Plan

Read all prior phase files for full context.

Follow the writing-plans skill process:

```
Task:
  subagent_type: "general-purpose"
  description: "Write implementation plan for mobile app"
  prompt: |
    You are using the writing-plans skill. Write a comprehensive implementation plan for this mobile app.

    ## Context
    [Insert summaries from .mobile-intel/01-competitor-analysis.md, 02-brainstorm.md, 03-ux-design.md]

    ## Instructions
    Create a bite-sized implementation plan following TDD principles:

    1. **Project setup**: Tauri 2 mobile project initialization, dependencies
    2. **Core architecture**: State management, navigation, IPC layer
    3. **Feature tasks**: One task per must-have feature, ordered by dependency
    4. **Testing strategy**: Unit tests, integration tests, device testing
    5. **Polish tasks**: Animations, transitions, accessibility

    Each task should include:
    - Exact file paths
    - Complete code snippets
    - Test commands with expected output
    - Commit messages

    Save the plan following the writing-plans format with bite-sized steps.

    Write your plan as a structured markdown document.
```

**Output file:** `.mobile-intel/04-implementation-plan.md`

Update `state.json`: set `current_phase` to "checkpoint-3", add phase 4 to `completed_phases`.

---

## PHASE CHECKPOINT 3 -- User Approval Required

```
Phase 4 complete: Implementation plan written.

Plan summary:
- Total tasks: [count]
- Estimated features: [count] must-have, [count] nice-to-have
- Architecture: [brief description]

Please review:
- .mobile-intel/04-implementation-plan.md

1. Continue -- scaffold the Tauri 2 mobile app
2. Revise plan -- adjust implementation approach
3. Skip scaffold -- stop here with the plan (same as --skip-scaffold)
4. Pause -- save progress and stop here
```

Do NOT proceed to Phase 5 until the user approves.

---

## Phase 5: Scaffold Tauri 2 Mobile App

**Skip if:** `--skip-scaffold` flag is set or user chose option 3 at checkpoint.

Read `.mobile-intel/04-implementation-plan.md` for the implementation plan.

Use the tauri-mobile skill guidance to scaffold the project:

### Step 5A: Initialize Tauri 2 project

Follow the tauri-mobile skill process:
- Create project with `npm create tauri-app@latest` or equivalent
- Configure for mobile targets (Android and/or iOS)
- Set up the project structure from the implementation plan

### Step 5B: Configure mobile capabilities

- Set up Android manifest permissions
- Configure Tauri capabilities for mobile plugins
- Add required Tauri plugins (biometric, geolocation, notifications, etc.)

### Step 5C: Create base architecture

- Set up frontend framework (React + TypeScript)
- Create navigation structure from UX design
- Add state management foundation
- Create IPC command stubs matching the plan

**Output file:** `.mobile-intel/05-scaffold-log.md`

```markdown
# Phase 5: Scaffold Log

## Project Created
- Location: [path]
- Framework: [React/Vue/etc.]
- Targets: [Android/iOS/both]

## Files Created
[List of created files]

## Configured Plugins
[List of Tauri plugins added]

## Next Steps
[What to implement first from the plan]
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
Mobile intelligence pipeline complete for: $ARGUMENTS

## Output Files
- Competitor Analysis: .mobile-intel/01-competitor-analysis.md
- Feature Brainstorm: .mobile-intel/02-brainstorm.md
- UX Design: .mobile-intel/03-ux-design.md
- Implementation Plan: .mobile-intel/04-implementation-plan.md
- Scaffold Log: .mobile-intel/05-scaffold-log.md [if not skipped]
- Screenshots: .mobile-intel/screenshots/

## Summary
- Competitor screens analyzed: [count]
- Features planned: [must-have count] must-have, [nice-to-have count] nice-to-have
- Implementation tasks: [count]

## Next Steps
1. Review the implementation plan at .mobile-intel/04-implementation-plan.md
2. Use /feature-e2e to execute the plan with full review pipeline
3. Or use the executing-plans skill to implement task by task
```
