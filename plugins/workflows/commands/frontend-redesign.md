---
description: >
  "Full frontend redesign pipeline — UX audit, layout design, implementation, React performance optimization, UI polish, and visual HTML audit report" argument-hint: "<target path or description> [--framework react|vue|svelte] [--skip-performance] [--strict-mode]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Frontend Redesign Pipeline

**Positioning:** This command improves existing frontend code. Use `premium-web-consultant` for strategy ("what to build") or `ui-studio` for building new UI from scratch.

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.frontend-redesign/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, missing files, access issues), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
6. **Phase 6 runs 3 agents in parallel.** Fire all three agents in a single response using multiple Task tool calls.
7. **Markdown report is mandatory.** Phase 6 MUST produce `.frontend-redesign/report.md` -- an actionable checklist with scores, findings, and fix instructions.

## Pre-flight Checks

### 0. Dependency check

This command requires agents from the `frontend` plugin. Before proceeding, verify it is installed by checking that these agents are available:

**Required plugins:**
- `frontend` -- web-designer, ui-layout-designer, web-designer, web-designer agents; frontend-design skill
- `react-development` -- react-performance-optimizer agent

Check by looking for the agent/skill files. If the `frontend` plugin is missing, STOP and tell the user:

```
Missing required plugin: frontend

This workflow command depends on agents from the frontend plugin.
Install it with:
  claude plugin marketplace add acaprino/alfio-claude-plugins --plugin frontend

Or install the full marketplace:
  claude plugin marketplace add acaprino/alfio-claude-plugins
```

### 1. Check for existing session

Check if `.frontend-redesign/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask:
  ```
  Found an in-progress frontend redesign session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```
- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 2. Initialize state

Create `.frontend-redesign/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "framework": null,
    "skip_performance": false,
    "strict_mode": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--framework`, `--skip-performance`, and `--strict-mode` flags.

### 3. Discover frontend files

Scan for frontend files:

```bash
find src -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.svelte" -o -name "*.css" -o -name "*.scss" \) | head -80
```

Or use the path from `$ARGUMENTS` if provided. If no frontend files found, STOP and say so.

### 4. Detect framework

If `--framework` not specified, auto-detect from:
- `package.json` dependencies (react, vue, svelte)
- File extensions (.tsx/.jsx → React, .vue → Vue, .svelte → Svelte)

### 5. Sample key files

Read a representative cross-section:
- Entry layout files (App.tsx, Layout.tsx, _app.tsx, root.tsx)
- 3-5 core components
- Primary stylesheets (globals.css, tailwind.config)
- Design token files (tokens.ts, theme.ts, variables.css)

**Output file:** `.frontend-redesign/00-scope.md`

```markdown
# Redesign Scope

## Target
[Description of what is being redesigned]

## Framework
[Detected or specified framework]

## Frontend Files
[List of component, page, and stylesheet files]

## Key Files Sampled
[List of files read for pattern detection]

## Flags
- Framework: [name]
- Skip Performance: [yes/no]
- Strict Mode: [yes/no]

## Redesign Phases
1. UX Audit & User Flow Design
2. Layout Composition & Grid System
3. Implement Designs
4. React Performance Optimization
5. UI Polish & Micro-interactions
6. Final Design Audit (HTML Report)
```

---

## Phase 1: UX Audit & User Flow Design

```
Task:
  subagent_type: "web-designer"
  description: "UX audit and user flow redesign"
  prompt: |
    Perform a comprehensive UX audit of this frontend application and design improved user flows.

    ## Scope
    [Insert contents of .frontend-redesign/00-scope.md]

    ## Sampled File Contents
    [Paste contents of key layout and component files]

    ## Instructions
    Audit and redesign:
    1. **Current UX assessment**: Evaluate existing patterns, identify pain points
    2. **Component responsibility audit**: God components, missing abstractions, prop explosion
    3. **User flow analysis**: Navigation paths, dead ends, missing feedback
    4. **Information hierarchy**: Visual hierarchy consistency, primary/secondary/tertiary actions
    5. **State handling**: Empty states, loading states, error states — are all three handled?
    6. **Accessibility**: Semantic HTML, ARIA, keyboard navigation, focus management, contrast
    7. **Design system adherence**: Colors, spacing, typography from tokens or scattered values?

    For each finding:
    - Current state (what's wrong)
    - Redesigned state (what it should be)
    - Priority: Critical/High/Medium/Low
    - Specific implementation guidance

    Organize findings as: issues to fix, patterns to establish, components to refactor.

    Write your findings as a structured markdown document.
```

**Output file:** `.frontend-redesign/01-ux-audit.md`

```markdown
# Phase 1: UX Audit & User Flow Design

## Current State Assessment
[Overall UX health]

## Critical UX Issues
[Must-fix problems]

## User Flow Redesign
[Improved navigation and interaction patterns]

## Component Refactoring Plan
[Components that need restructuring]

## Design System Recommendations
[Token system, component library suggestions]

## Accessibility Gaps
[A11y issues and fixes]

## Key Findings for Phase 2 Context
[Layout and spacing issues that inform the layout phase]
```

Update `state.json`: set `current_phase` to 2, add phase 1 to `completed_phases`.

---

## Phase 2: Layout Composition & Grid System

Read `.frontend-redesign/01-ux-audit.md` for context.

```
Task:
  subagent_type: "ui-layout-designer"
  description: "Layout system design and grid composition"
  prompt: |
    Design a comprehensive layout system and grid composition for this frontend redesign.

    ## Scope
    [Insert contents of .frontend-redesign/00-scope.md]

    ## UX Audit Context
    [Insert contents of .frontend-redesign/01-ux-audit.md — especially layout/spacing findings]

    ## Sampled File Contents
    [Paste contents of layout and stylesheet files]

    ## Instructions
    Design and specify:
    1. **Grid system**: Define the layout grid (CSS Grid/Flexbox), column structure, gutters
    2. **Spacing scale**: Design a consistent spacing system (4px/8px base) with named tokens
    3. **Responsive strategy**: Breakpoints, mobile-first vs desktop-first, layout shifts
    4. **Typography scale**: Font sizes, line heights, letter spacing as tokens
    5. **Container strategy**: Max-widths, centering, content containers
    6. **Page templates**: Common page layouts (sidebar+content, full-width, split)
    7. **Component sizing**: Consistent sizing system for buttons, inputs, cards

    For each specification, provide:
    - Design token values (CSS custom properties)
    - Example CSS code
    - Migration notes from current patterns

    Write your specifications as a structured markdown document.
```

**Output file:** `.frontend-redesign/02-layout-spec.md`

Update `state.json`: set `current_phase` to "checkpoint-1", add phase 2 to `completed_phases`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

Display a summary of the UX audit and layout specifications:

```
Phases 1-2 complete: UX audit and layout system designed.

UX Audit:
- Critical issues: [count]
- Components to refactor: [count]
- Accessibility gaps: [count]

Layout System:
- Grid: [type]
- Spacing scale: [base unit]
- Breakpoints: [count]

Please review:
- .frontend-redesign/01-ux-audit.md
- .frontend-redesign/02-layout-spec.md

1. Continue -- implement the designs
2. Revise -- adjust UX or layout decisions before implementing
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 3: Implement Designs

Read `.frontend-redesign/01-ux-audit.md` and `.frontend-redesign/02-layout-spec.md` for the approved designs.

Use the frontend-design skill process to implement:

### Step 3A: Design tokens & foundation

- Create or update design token files (CSS custom properties or theme config)
- Implement spacing scale, typography scale, color tokens
- Set up layout grid utilities

### Step 3B: Component refactoring

Working through the UX audit's component refactoring plan:
- Refactor god components into focused components
- Implement missing abstractions
- Add proper state handling (empty, loading, error)
- Fix accessibility issues (semantic HTML, ARIA, keyboard nav)

### Step 3C: Layout implementation

Following the layout spec:
- Apply grid system to page templates
- Implement responsive breakpoints
- Apply consistent spacing tokens
- Fix typography scale

### Step 3D: User flow improvements

From the UX audit:
- Fix navigation dead ends
- Add missing feedback (loading indicators, success/error states)
- Improve information hierarchy

Log all changes to `.frontend-redesign/03-implementation-log.md`:

```markdown
# Phase 3: Implementation Log

## Design Tokens Created/Updated
[List of token files and values]

## Components Refactored
[List of components with changes made]

## Layout Changes
[Grid, spacing, responsive changes]

## User Flow Improvements
[Navigation, feedback, hierarchy changes]

## Files Modified
[Complete list of modified files]
```

Update `state.json`: set `current_phase` to 4, add phase 3 to `completed_phases`.

---

## Phase 4: React Performance Optimization

**Skip if:** `--skip-performance` flag is set. If skipped, proceed to Phase 5.

Read `.frontend-redesign/03-implementation-log.md` for context on what changed.

```
Task:
  subagent_type: "react-performance-optimizer"
  description: "React performance optimization after redesign"
  prompt: |
    Optimize the React performance of this frontend after a major redesign.

    ## Scope
    [Insert contents of .frontend-redesign/00-scope.md]

    ## Implementation Context
    [Insert summary of changes from .frontend-redesign/03-implementation-log.md]

    ## Instructions
    Analyze and optimize:
    1. **Re-render audit**: Identify components that re-render unnecessarily after the redesign
    2. **Memoization**: Add React.memo, useMemo, useCallback where needed
    3. **Code splitting**: Verify lazy loading is in place for new/refactored components
    4. **State management**: Check for unnecessary context re-renders from new token system
    5. **Bundle impact**: Did the redesign increase bundle size? Optimize if so
    6. **CSS performance**: New animations GPU-accelerated? Layout-triggering properties?
    7. **Hydration**: If SSR, check hydration mismatch risks from new components

    For each optimization:
    - What was the problem
    - What you changed
    - Expected performance impact

    Apply the optimizations directly to the code. Run tests to verify nothing breaks.

    Write your findings and changes as a structured markdown document.
```

**Output file:** `.frontend-redesign/04-performance.md`

Update `state.json`: set `current_phase` to 5, add phase 4 to `completed_phases`.

---

## Phase 5: UI Polish & Micro-interactions

Read `.frontend-redesign/03-implementation-log.md` and `.frontend-redesign/04-performance.md` (if exists) for context.

```
Task:
  subagent_type: "web-designer"
  description: "UI polish and micro-interactions for redesigned frontend"
  prompt: |
    Add visual polish and micro-interactions to this redesigned frontend.

    ## Scope
    [Insert contents of .frontend-redesign/00-scope.md]

    ## Implementation Context
    [Insert summary from .frontend-redesign/03-implementation-log.md]

    ## Performance Context
    [Insert summary from .frontend-redesign/04-performance.md if exists, noting any animation constraints]

    ## Instructions
    Polish and enhance:
    1. **Transitions**: Smooth page transitions, component mount/unmount animations
    2. **Hover & focus states**: Consistent interactive feedback on all clickable elements
    3. **Loading animations**: Skeleton screens, spinners, progress bars where needed
    4. **Micro-interactions**: Button press feedback, form validation animations, success states
    5. **Motion system**: Consistent easing curves, duration scale, spring parameters
    6. **Dark mode**: If supported, verify all new components adapt properly
    7. **Reduced motion**: Respect prefers-reduced-motion for all animations
    8. **Empty states**: Beautiful empty state illustrations/messages where needed
    9. **Error states**: Friendly error messages with recovery actions

    Apply changes directly. Use GPU-accelerated properties (transform, opacity) for animations.
    Run tests to verify nothing breaks.

    Write your changes as a structured markdown document.
```

**Output file:** `.frontend-redesign/05-polish-log.md`

Update `state.json`: set `current_phase` to "checkpoint-2", add phase 5 to `completed_phases`.

---

## PHASE CHECKPOINT 2 -- User Approval Required

```
Phases 3-5 complete: Implementation, performance, and polish done.

Summary:
- Components refactored: [count]
- Layout changes: [count]
- Performance optimizations: [count]
- Polish additions: [count]

Please review:
- .frontend-redesign/03-implementation-log.md
- .frontend-redesign/04-performance.md
- .frontend-redesign/05-polish-log.md

1. Continue -- run the final design audit and generate HTML report
2. Adjust -- make changes before the audit
3. Pause -- save progress and stop here
```

Do NOT proceed to Phase 6 until the user approves.

---

## Phase 6: Final Design Audit & HTML Report

Read all `.frontend-redesign/*.md` files for full context.

Re-read the modified frontend files to assess the final state.

Run all three audit agents **in parallel** in a single response:

### Agent A: UX Patterns & Component Architecture

```
Task:
  subagent_type: "web-designer"
  description: "Final UX audit of redesigned frontend"
  prompt: |
    Perform a final UX audit of the redesigned frontend.

    ## Scope
    [List of key files after redesign]

    ## File Contents
    [Paste sampled component and layout file contents — the CURRENT state after all changes]

    ## Instructions
    Evaluate the redesigned frontend:
    1. Component responsibility — are god components resolved?
    2. UX patterns — consistent interaction patterns?
    3. Empty/loading/error states — all three handled everywhere?
    4. Information hierarchy — visual hierarchy consistent?
    5. User flows — dead ends fixed? Feedback present?
    6. Design system adherence — tokens used consistently?
    7. Accessibility — semantic HTML, ARIA, keyboard nav, contrast?

    For each finding: severity (Critical/High/Medium/Low), file, issue, specific fix.
    Note what's working well.

    Return structured JSON:
    ```json
    {
      "findings": [
        { "severity": "...", "category": "...", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "ux_consistency": N, "accessibility": N, "component_design": N, "overall": N }
    }
    ```
```

### Agent B: Layout System & Spatial Design

```
Task:
  subagent_type: "ui-layout-designer"
  description: "Final layout audit of redesigned frontend"
  prompt: |
    Audit the layout system of the redesigned frontend.

    ## Scope
    [List of key files after redesign]

    ## File Contents
    [Paste sampled layout and stylesheet file contents — CURRENT state]

    ## Instructions
    Evaluate:
    1. Layout system — consistent grid/layout pattern?
    2. Spacing scale — derived from consistent scale?
    3. Responsive strategy — breakpoints consistent? No layout shifts?
    4. Typography system — font scale as tokens?
    5. Alignment & rhythm — baseline alignment, vertical rhythm?
    6. Container strategy — max-widths, centering consistent?

    For each finding: severity, file, issue, specific fix.
    Note what's done well.

    Return structured JSON:
    ```json
    {
      "findings": [
        { "severity": "...", "category": "...", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "layout_system": N, "responsive": N, "typography": N, "overall": N }
    }
    ```
```

### Agent C: CSS Architecture & Visual Polish

```
Task:
  subagent_type: "web-designer"
  description: "Final CSS and polish audit of redesigned frontend"
  prompt: |
    Audit the CSS architecture and visual polish of the redesigned frontend.

    ## Scope
    [List of key files after redesign]

    ## File Contents
    [Paste sampled stylesheet and component file contents — CURRENT state]

    ## Instructions
    Evaluate:
    1. CSS architecture — global pollution, specificity, !important abuse?
    2. Modern CSS — custom properties, container queries, logical properties?
    3. Animation quality — smooth transitions, GPU-accelerated, reduced-motion respected?
    4. Visual consistency — border-radius, shadows, colors consistent?
    5. Dark mode — properly adapted?
    6. CSS performance — unnecessary repaints, layout-triggering animations?
    7. Dead CSS — unused selectors, legacy overrides?
    8. Component isolation — styles scoped properly?

    For each finding: severity, file, issue, specific fix.
    Note what's done well.

    Return structured JSON:
    ```json
    {
      "findings": [
        { "severity": "...", "category": "...", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "css_architecture": N, "visual_polish": N, "animations": N, "overall": N }
    }
    ```
```

### Generate Markdown Report

After all agents complete, create `.frontend-redesign/report.md` — an actionable checklist.

Merge and deduplicate overlapping findings. Group by category (UX, Layout, CSS). Order by severity.

**Output file:** `.frontend-redesign/report.md`

```markdown
# Frontend Redesign Audit — [date]

Full redesign pipeline audit · [N] components · [M] stylesheets

## Scores

| Category | Score |
|----------|-------|
| UX Quality | X/10 |
| Layout System | X/10 |
| CSS Architecture | X/10 |
| Accessibility | X/10 |
| Typography | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Before vs After Redesign

| Metric | Before (Phase 1) | After (Phase 6) |
|--------|-------------------|------------------|
| UX Score | X/10 | Y/10 |
| Layout Score | X/10 | Y/10 |
| CSS Score | X/10 | Y/10 |
| Critical Issues | X | Y |

## Remaining Critical & High Issues

### UX & Components

#### `Component.tsx` — [issue title]
- **Severity**: Critical
- **Issue**: [description]
- **Fix**: [concrete fix instruction]
- [ ] Fixed

### Layout & Spacing

#### `Layout.tsx` — [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

### CSS Architecture

#### `styles.css` — [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

## Medium & Low Issues
[Same format, grouped by category]

## What's Working Well
- [positive observations from all agents]

## Remaining Action Items
1. [ ] [top priority remaining fix]
2. [ ] [second priority]
3. [ ] [third priority]
4. [ ] [fourth priority]
5. [ ] [fifth priority]
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

Print a short summary:

```
Frontend redesign pipeline complete for: $ARGUMENTS

## Output Files
- Scope: .frontend-redesign/00-scope.md
- UX Audit: .frontend-redesign/01-ux-audit.md
- Layout Spec: .frontend-redesign/02-layout-spec.md
- Implementation Log: .frontend-redesign/03-implementation-log.md
- Performance: .frontend-redesign/04-performance.md
- Polish Log: .frontend-redesign/05-polish-log.md
- Audit Report: .frontend-redesign/report.md

## Summary
Overall Score: X/10
UX: X/10 | Layout: X/10 | CSS: X/10 | Accessibility: X/10

Critical: X | High: X | Medium: X | Low: X

Top 3 remaining issues:
1. [issue summary]
2. [issue summary]
3. [issue summary]
```

If `--strict-mode` is set and Critical findings exist:
```
STRICT MODE: Critical design issues remain after redesign. Recommend addressing before shipping.
```
