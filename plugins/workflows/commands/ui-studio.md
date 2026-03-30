---
description: >
  "End-to-end UI development pipeline -- brainstorm product concept, design direction, layout, UX patterns, write implementation plan, execute with TDD, polish, performance review, and code review" argument-hint: "<product goal or feature description> [--skip-brainstorm] [--skip-review] [--skip-humanize] [--strict-mode] [--framework react|vue|svelte|html]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# UI Studio Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.ui-studio/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, test failure, missing files), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
6. **Brainstorming is interactive.** Phase 1 MUST involve back-and-forth with the user -- ask questions one at a time, propose approaches, get approval.
7. **Product brief is the north star.** Every agent receives the product brief. If any output contradicts it, reject and redirect.

## Pre-flight Checks

### 0. Scope check -- is this the right command?

This pipeline is for **building new UI from scratch or major redesigns**. Before starting, evaluate the user's request:

**Full pipeline IS appropriate when:**
- Building a new page, feature, or component from scratch
- Major visual redesign of an existing UI
- User explicitly wants the brainstorm -> design -> build -> review workflow

**Full pipeline is NOT appropriate when:**
- Fixing a specific layout bug (broken grid, overflow, clipping)
- Reordering or repositioning existing components
- Tweaking responsive behavior at specific breakpoints
- Small CSS or styling adjustments

**If the request is a targeted fix, do NOT run the pipeline.** Instead:
1. Tell the user this is a fix, not a build-from-scratch task, so the full pipeline would be overkill
2. Use the relevant specialized agent directly:
   - Layout/grid/responsive issues -> spawn `frontend:ui-layout-designer` to analyze and fix
   - Visual polish/animations -> spawn `frontend:web-designer`
   - UX flow/interaction issues -> spawn `frontend:web-designer`
   - React performance issues -> spawn `react-development:react-performance-optimizer`
3. If no single agent fits, handle the fix directly with code analysis and edits

Never silently skip the pipeline -- always explain to the user which path you are taking and why.

### 1. Dependency check

This command requires agents and skills from other plugins. Before proceeding, verify they are installed:

**Required plugins:**
- `ai-tooling` -- brainstorming, writing-plans, executing-plans skills (Phases 1, 6, 7)
- `frontend` -- web-designer, ui-layout-designer, web-designer agents, frontend-design and web-designer skills (Phases 2-5, 8-9)
- `react-development` -- react-performance-optimizer agent (Phase 8)

**Optional plugins:**
- `senior-review` -- code-auditor, security-auditor agents (Phase 10)
- `humanize` -- humanize agent (Phase 11)

Check by looking for the agent/skill files. If a required plugin is missing, STOP and tell the user:

```
Missing required plugin(s): [list]

This workflow command depends on agents and skills from other ACP plugins.
Install them with:
  claude plugin marketplace add acaprino/alfio-claude-plugins --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/alfio-claude-plugins
```

If only optional plugins are missing, warn but continue (skip their phases).

### 2. Check for existing session

Check if `.ui-studio/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask:
  ```
  Found an in-progress UI Studio pipeline session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```
- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 3. Initialize state

Create `.ui-studio/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "skip_brainstorm": false,
    "skip_review": false,
    "skip_humanize": false,
    "strict_mode": false,
    "framework": null
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for flags. Auto-detect framework from project if not specified.

### 4. Explore project context

Scan the current project to understand:
- Language and framework (package.json, tsconfig.json, etc.)
- Existing UI components and design system
- CSS approach (Tailwind, CSS modules, styled-components, vanilla)
- Test patterns
- Recent git history

**Output file:** `.ui-studio/00-context.md`

```markdown
# Pipeline Context

## Product Goal
[From $ARGUMENTS]

## Project
- Framework: [detected]
- CSS approach: [detected]
- Component library: [detected or none]
- Test framework: [detected]

## Flags
- Skip Brainstorm: [yes/no]
- Skip Review: [yes/no]
- Skip Humanize: [yes/no]
- Strict Mode: [yes/no]
- Framework: [specified or auto-detected]
```

---

## PART A: DISCOVERY (Phases 1-2)

---

## Phase 1: Brainstorm Product Concept

**Skip if:** `--skip-brainstorm` flag is set. If skipped, ask the user to provide a product brief, then save to `.ui-studio/01-brief.md` and proceed to Phase 1B.

### Step 0: Evaluate clarity of requirements

Before brainstorming, assess whether the user's input already provides clear enough requirements to build from. Consider:

- Is the target UI/feature clearly described?
- Is the aesthetic direction stated or inferrable from context (existing codebase, project style)?
- Is the scope defined (what to build, where it fits)?

**If requirements are clear:** Skip the interactive brainstorming. Go directly to Step 1C -- explore the codebase for context, then synthesize the product brief from the user's input + project context. Fill in reasonable defaults for anything not specified (infer from codebase style, framework, existing patterns).

**If requirements are vague or ambiguous:** Run the full interactive brainstorming below (Steps 1A-1C).

The threshold: if you can write a confident product brief from what the user gave you + codebase context, skip brainstorming. If you'd be guessing on core decisions (what to build, who it's for, what aesthetic), brainstorm.

---

### (Interactive brainstorming -- only when requirements are unclear)

### Step 1A: Explore context

Review the existing codebase (if any) and understand where this UI fits.

### Step 1B: Ask clarifying questions (one at a time)

Only ask about what's genuinely unclear. Skip questions where the answer is obvious from context.

- What problem does this UI solve? Who is the primary user?
- What is the desired aesthetic tone? (refined editorial / brutalist raw / playful / corporate clean / etc.)
- What device/screen size is primary? (desktop-first / mobile-first / both)
- Are there performance budgets? (Core Web Vitals targets)
- What WCAG level? (AA / AAA / none)
- What does "done" look like?

Use AskUserQuestion with multiple-choice options where possible. One question per message.

### Step 1C: Propose approaches

Based on answers, propose 2-3 product directions:
- Direction A: [aesthetic + feature set + rationale]
- Direction B: [aesthetic + feature set + rationale]
- Recommended: [which and why]

### Step 1D: Finalize product brief

Present the complete product brief for approval:

```
PRODUCT BRIEF
---
Goal:        [one sentence]
Audience:    [who, device, tech level]
Aesthetic:   [tone + archetype]
Stack:       [framework + CSS approach]
Perf budget: [Core Web Vitals targets or "none"]
A11y:        [WCAG AA / AAA / none]
Success:     [definition of done]
---
```

**Output file:** `.ui-studio/01-brief.md`

```markdown
# Phase 1: Product Brief

## Product Brief

[The brief in the format above]

## Problem Statement
[Expanded problem description]

## Target Users
[Detailed user personas]

## Design Decisions
[Key decisions made during brainstorming]

## Feature Scope
- Must-have: [list]
- Nice-to-have: [list]
- Out of scope: [list]
```

Update `state.json`: set `current_phase` to "1b", add phase 1 to `completed_phases`.

---

## Phase 1B: Quick Concept Artifact

**Always run this phase.** Right after the brief is finalized, generate a rough visual artifact so the user has something tangible to react to before committing to the full design pipeline.

```
Task:
  subagent_type: "general-purpose"
  description: "Generate quick concept artifact from product brief"
  prompt: |
    Generate a single self-contained HTML file that visualizes the product concept as a rough mockup.
    This is a quick concept artifact -- NOT a polished design. Speed and tangibility over polish.

    ## Product Brief
    [Insert contents of .ui-studio/01-brief.md]

    ## Project Context
    [Insert contents of .ui-studio/00-context.md]

    ## Instructions

    Create `.ui-studio/concept-artifact.html` -- a single HTML file (no external dependencies) that:

    1. **Shows the overall layout** with rough blocks/sections matching the product goal
    2. **Uses colors and typography** that match the aesthetic tone from the brief
    3. **Includes realistic placeholder content** (not lorem ipsum -- domain-appropriate text)
    4. **Shows the primary user flow** or key screen described in the brief
    5. **Is responsive** with a basic mobile breakpoint
    6. **Includes inline CSS** -- everything in one file, openable directly in a browser

    Style: think wireframe with personality -- enough visual fidelity to convey the direction,
    rough enough that the user knows this is a starting point, not the final design.

    Keep it under 300 lines. Fast and tangible over comprehensive.
```

**Output file:** `.ui-studio/concept-artifact.html`

After generating, tell the user how to preview it:

```
Quick concept artifact generated: .ui-studio/concept-artifact.html
Open it directly in your browser to see a rough visual preview of the product direction.

This is intentionally rough -- it's meant to validate the direction before we invest in detailed design.
```

Update `state.json`: set `current_phase` to "checkpoint-1", add phase "1b" to `completed_phases`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

```
Phase 1 complete: Product brief finalized + concept artifact generated.

Goal: [one sentence]
Aesthetic: [tone]
Audience: [who]
Preview: .ui-studio/concept-artifact.html

Please review:
- .ui-studio/01-brief.md (product brief)
- .ui-studio/concept-artifact.html (open in browser for visual preview)

1. Continue -- proceed to detailed design
2. Revise direction -- adjust brief or visual direction before designing
3. Pause -- save progress and stop here
```

Do NOT proceed until the user approves.

---

## Phase 2: Design Direction

Use the **frontend-design** skill.

Pass the full product brief from `.ui-studio/01-brief.md`.

```
Task:
  subagent_type: "general-purpose"
  description: "Establish design direction using frontend-design skill"
  prompt: |
    You are using the frontend-design skill. Establish a bold design direction for this product.

    ## Product Brief
    [Insert contents of .ui-studio/01-brief.md]

    ## Instructions
    - Commit to an aesthetic direction aligned with the tone from the brief
    - Define typography system (font families, scale, weights)
    - Define color palette (primary, secondary, accent, semantic colors as CSS custom properties)
    - Define motion principles (speed, easing, what animates)
    - Define spacing scale (consistent tokens)
    - Produce a reference component establishing the visual language

    This is the visual contract for all subsequent phases.

    Write your design direction as a structured markdown document with CSS custom property definitions.
```

**Output file:** `.ui-studio/02-design-direction.md`

```markdown
# Phase 2: Design Direction

## Aesthetic Definition
[Tone, archetype, visual language]

## Typography System
[Font families, scale, weights, line heights]

## Color Palette
[CSS custom properties for all colors]

## Spacing Scale
[Spacing tokens]

## Motion Principles
[Speed, easing, what animates vs what doesn't]

## Reference Component
[Code for a reference component showing the visual language]
```

Update `state.json`: set `current_phase` to 3, add phase 2 to `completed_phases`.

---

## PART B: DESIGN (Phases 3-5)

---

## Phase 3: Layout & Structure

Agent: **ui-layout-designer**

```
Task:
  subagent_type: "frontend:ui-layout-designer"
  description: "Layout composition for UI"
  prompt: |
    Design the layout system for this product.

    ## Product Brief
    [Insert brief from .ui-studio/01-brief.md]

    ## Design Direction
    [Insert contents of .ui-studio/02-design-direction.md -- font scale, spacing, color tokens]

    ## Instructions
    1. Choose layout pattern fitting the content model and audience (bento, holy grail, editorial, dashboard, etc.)
    2. Define spacing system aligned with Phase 2 tokens
    3. Define breakpoint strategy (mobile-first or desktop-first per brief)
    4. Produce CSS Grid/Flexbox scaffold with named areas
    5. Define responsive pivots and column behavior
    6. Handle content overflow: scroll behavior, truncation, virtualization needs

    Layout must serve the audience's mental model from the brief.

    Write as structured markdown with CSS code snippets.
```

**Output file:** `.ui-studio/03-layout.md`

Update `state.json`: set `current_phase` to 4, add phase 3 to `completed_phases`.

---

## Phase 4: UX Patterns

Agent: **web-designer**

```
Task:
  subagent_type: "frontend:web-designer"
  description: "UX patterns and interaction design"
  prompt: |
    Design UX patterns and interactions for this product.

    ## Product Brief
    [Insert brief from .ui-studio/01-brief.md]

    ## Layout Structure
    [Insert contents of .ui-studio/03-layout.md]

    ## Instructions
    1. Design interaction patterns aligned with the user goal from the brief
    2. Handle all three states everywhere needed: loading, empty, error
    3. Validate information hierarchy -- primary action must dominate
    4. Design user flows for key tasks (from feature scope in brief)
    5. Flag accessibility requirements for the WCAG level in the brief
    6. Define form patterns, validation feedback, and error recovery
    7. Design navigation and wayfinding patterns

    Every UX decision must serve the stated goal and audience from the brief.

    Write as structured markdown.
```

**Output file:** `.ui-studio/04-ux-patterns.md`

Update `state.json`: set `current_phase` to 5, add phase 4 to `completed_phases`.

---

## Phase 5: Component Architecture

Read all design phases (02, 03, 04) and synthesize a component plan.

```
Task:
  subagent_type: "general-purpose"
  description: "Component architecture from design specs"
  prompt: |
    Synthesize the design direction, layout, and UX patterns into a concrete component architecture.

    ## Product Brief
    [Insert brief from .ui-studio/01-brief.md]

    ## Design Direction
    [Insert .ui-studio/02-design-direction.md]

    ## Layout
    [Insert .ui-studio/03-layout.md]

    ## UX Patterns
    [Insert .ui-studio/04-ux-patterns.md]

    ## Instructions
    Define:
    1. **Component tree**: Hierarchy of components from layout to atoms
    2. **Props and state**: What data each component needs, where state lives
    3. **CSS architecture**: How design tokens flow (CSS custom properties, theme context)
    4. **Responsive behavior**: How each component adapts per breakpoint strategy
    5. **Accessibility requirements**: ARIA roles, keyboard navigation, focus management
    6. **File structure**: Where each component file goes

    This becomes the blueprint for the implementation plan.

    Write as structured markdown.
```

**Output file:** `.ui-studio/05-component-architecture.md`

Update `state.json`: set `current_phase` to 6, add phase 5 to `completed_phases`.

---

## Phase 6: Interactive Mockup Preview

Generate a self-contained React mockup that renders the entire design as a static demo. This gives the user a tangible visual preview before committing to full implementation.

```
Task:
  subagent_type: "general-purpose"
  description: "Generate React mockup preview from design specs"
  prompt: |
    Generate a self-contained React mockup file that renders the full UI design as a static preview.
    This is a rough prototype for visual validation -- NOT production code.

    ## Product Brief
    [Insert brief from .ui-studio/01-brief.md]

    ## Design Direction
    [Insert .ui-studio/02-design-direction.md -- typography, colors, spacing, motion]

    ## Layout
    [Insert .ui-studio/03-layout.md -- grid, breakpoints]

    ## UX Patterns
    [Insert .ui-studio/04-ux-patterns.md -- interactions, states]

    ## Component Architecture
    [Insert .ui-studio/05-component-architecture.md -- component tree]

    ## Instructions

    Create a single React file `.ui-studio/mockup/MockupPreview.tsx` that:

    1. **Embeds all design tokens** as CSS custom properties in a `<style>` block or inline styles
    2. **Renders the full layout** with placeholder content matching the grid structure
    3. **Shows all key components** from the component tree with realistic placeholder data
    4. **Demonstrates responsive behavior** using CSS media queries from the layout spec
    5. **Shows key states**: default view, with loading skeletons, empty states, and error states
       rendered as separate sections so the user can scroll through and see all states
    6. **Applies typography and color** exactly as defined in the design direction
    7. **Includes navigation** structure showing all screens/routes as tabs or sections

    The mockup should:
    - Be runnable with a simple `npx vite` or similar dev server
    - Use inline styles or a `<style>` tag -- no external CSS dependencies
    - Use placeholder images from `https://placehold.co/WIDTHxHEIGHT`
    - Include realistic text content (not "lorem ipsum" -- use content matching the product domain)
    - Be visually representative of the final product, even if rough

    Also create `.ui-studio/mockup/index.html` that loads the component if the project
    doesn't already have a React setup. Use a CDN-based React setup (esm.sh or unpkg)
    so it runs without npm install.

    Write both files.
```

**Output files:**
- `.ui-studio/mockup/MockupPreview.tsx`
- `.ui-studio/mockup/index.html`

After generating, tell the user how to preview the mockup:

```
Phase 6 complete: React mockup generated.

Preview the mockup:
  Option A (if project has React): Import MockupPreview from .ui-studio/mockup/MockupPreview.tsx
  Option B (standalone): Open .ui-studio/mockup/index.html in a browser

The mockup shows:
- Full layout with grid structure
- All key components with placeholder data
- Typography, colors, and spacing from the design direction
- Responsive behavior at defined breakpoints
- Loading, empty, and error states
```

Update `state.json`: set `current_phase` to "checkpoint-2", add phase 6 to `completed_phases`.

---

## PHASE CHECKPOINT 2 -- User Approval Required

```
Phases 2-6 complete: Design system specified and mockup generated.

Design summary:
- Aesthetic: [tone]
- Layout: [pattern]
- Components: [count]
- UX flows: [count]
- Mockup: .ui-studio/mockup/

Please review:
- .ui-studio/02-design-direction.md (visual language)
- .ui-studio/03-layout.md (layout system)
- .ui-studio/04-ux-patterns.md (interactions)
- .ui-studio/05-component-architecture.md (component tree)
- .ui-studio/mockup/ (visual preview)

1. Continue -- write implementation plan
2. Revise design -- adjust before planning (I'll regenerate the mockup)
3. Pause -- save progress and stop here
```

Do NOT proceed until the user approves.

---

## PART C: BUILD (Phases 7-8)

---

## Phase 7: Write Implementation Plan

Read all prior phase files for complete design context.

Follow the writing-plans skill process:

```
Task:
  subagent_type: "general-purpose"
  description: "Write implementation plan for UI"
  prompt: |
    You are using the writing-plans skill. Write a comprehensive, bite-sized implementation plan
    for building this UI from the completed design specifications.

    ## Product Brief
    [Insert .ui-studio/01-brief.md]

    ## Design Direction
    [Insert .ui-studio/02-design-direction.md]

    ## Layout
    [Insert .ui-studio/03-layout.md]

    ## UX Patterns
    [Insert .ui-studio/04-ux-patterns.md]

    ## Component Architecture
    [Insert .ui-studio/05-component-architecture.md]

    ## Project Context
    [Insert .ui-studio/00-context.md]

    ## Instructions
    Create a plan with bite-sized tasks following TDD principles:

    Task ordering:
    1. **Foundation**: CSS custom properties, design tokens, theme setup
    2. **Layout scaffold**: Grid structure, responsive container
    3. **Base components**: Buttons, inputs, typography components (bottom-up)
    4. **Composite components**: Cards, forms, navigation (composed from base)
    5. **Page sections**: Hero, content areas, sidebars (composed from composites)
    6. **Interaction wiring**: Event handlers, state management, API integration
    7. **Accessibility**: ARIA roles, keyboard navigation, focus management
    8. **Responsive polish**: Breakpoint behavior, mobile adaptations

    Each task:
    - Exact file paths (create/modify/test)
    - Step 1: Write failing test (visual regression or unit test)
    - Step 2: Run test to verify it fails
    - Step 3: Write implementation
    - Step 4: Run test to verify it passes
    - Step 5: Commit

    Include CSS code from the design specs in the implementation steps.

    Write the plan as structured markdown.
```

**Output file:** `.ui-studio/07-plan.md`

Update `state.json`: set `current_phase` to "checkpoint-3", add phase 7 to `completed_phases`.

---

## PHASE CHECKPOINT 3 -- User Approval Required

```
Phase 7 complete: Implementation plan written.

Plan summary:
- Total tasks: [count]
- Components to build: [count]
- Files to create: [count]
- Tests to write: [count]

Please review:
- .ui-studio/07-plan.md

1. Continue -- execute the plan with batch checkpoints
2. Revise plan -- adjust tasks before executing
3. Pause -- save progress and stop here
```

Do NOT proceed until the user approves.

---

## Phase 8: Execute Plan

Read `.ui-studio/07-plan.md` for the plan.

Follow the executing-plans skill process with batch execution:

### Execution Loop

Execute tasks in batches of 3:

1. **For each task in the batch:**
   - Mark as in_progress
   - Follow each step exactly (test first, then implement)
   - Run all verification commands
   - If a test fails: STOP, report, ask user
   - Mark as completed

2. **After each batch:**
   - Show what was implemented
   - Show verification output
   - Ask: "Ready for feedback on this batch?"

3. **Wait for user feedback** before next batch.

4. **Repeat** until all tasks complete.

Log to `.ui-studio/08-execution-log.md`:

```markdown
# Phase 8: Execution Log

## Task 1: [name]
- Status: completed
- Files changed: [list]
- Tests: [pass/fail]
- Commit: [hash]

...

## Execution Summary
- Tasks completed: [X/Y]
- Tests passing: [count]
- Commits made: [count]
```

Update `state.json`: set `current_phase` to "checkpoint-4", add phase 8 to `completed_phases`.

---

## PHASE CHECKPOINT 4 -- User Approval Required

```
Phase 8 complete: Implementation executed.

Tasks completed: [X/Y]
Tests passing: [count]
Commits made: [count]

1. Continue -- proceed to polish and performance
2. Fix issues -- address problems before polish
3. Skip polish -- go straight to review
4. Pause -- save progress
```

Do NOT proceed until the user approves.

---

## PART D: POLISH & REVIEW (Phases 9-12)

---

## Phase 9: UI Polish & Micro-interactions

Agent: **web-designer**

```
Task:
  subagent_type: "frontend:web-designer"
  description: "UI polish and micro-interactions"
  prompt: |
    Polish the implemented UI to match the product brief's aesthetic tone.

    ## Product Brief
    [Insert brief from .ui-studio/01-brief.md -- especially aesthetic tone]

    ## Design Direction
    [Insert motion principles from .ui-studio/02-design-direction.md]

    ## Implemented Code
    [List of implemented component files from Phase 8]

    ## Instructions
    1. Add micro-interactions matching the aesthetic tone from the brief
    2. Layer page load animations and scroll reveals appropriate to audience
    3. Polish hover/focus/active states for all interactive elements
    4. Ensure `prefers-reduced-motion` is respected
    5. Add loading skeleton screens where appropriate
    6. Polish empty and error states
    7. Verify visual consistency with the design direction tokens

    Polish must AMPLIFY the aesthetic tone, not override it.
    "Refined editorial" = restrained, purposeful motion.
    "Playful" = bouncy, expressive motion.
    The brief decides.

    Write changes and run tests to verify nothing breaks.
```

**Output file:** `.ui-studio/09-polish-log.md`

Update `state.json`: set `current_phase` to 10, add phase 9 to `completed_phases`.

---

## Phase 10: React Performance (React projects only)

**Skip if:** Framework is not React/Next.js.

Agent: **react-performance-optimizer**

```
Task:
  subagent_type: "react-development:react-performance-optimizer"
  description: "React performance optimization"
  prompt: |
    Optimize React performance against the budget from the product brief.

    ## Product Brief
    [Insert brief -- performance budget section]

    ## Implemented Code
    [List of component files]

    ## Instructions
    Analyze and fix:
    1. Re-render optimization: unnecessary renders, missing memoization
    2. State management: global vs local, context overhead
    3. Bundle optimization: code splitting, lazy loading, tree shaking
    4. React patterns: hook dependencies, effect cleanup, key usage
    5. Core Web Vitals: LCP, FID, CLS against budget from brief
    6. CSS performance: unused styles, critical CSS extraction

    For each finding: severity, file, fix. Apply fixes directly.
    Run tests after changes.
```

**Output file:** `.ui-studio/10-performance-log.md`

Update `state.json`: set `current_phase` to 11, add phase 10 to `completed_phases`.

---

## Phase 11: Code Review

**Skip if:** `--skip-review` flag is set or `senior-review` plugin is missing.

Run 3 review agents in parallel:

### Agent A: Architecture Review

```
Task:
  subagent_type: "senior-review:code-auditor"
  description: "Code audit of UI implementation"
  prompt: |
    Review the UI implementation architecture.

    ## Product Brief
    [Insert brief]

    ## Component Architecture (planned)
    [Insert .ui-studio/05-component-architecture.md]

    ## Changed Files
    [List from execution and polish logs]

    ## Instructions
    Focus on:
    1. Does the implementation match the planned component architecture?
    2. Component boundaries and prop drilling
    3. State management patterns
    4. CSS architecture and token usage
    5. Accessibility implementation quality

    For each finding: severity, file, concrete fix.
```

### Agent B: Security Audit

```
Task:
  subagent_type: "senior-review:security-auditor"
  description: "Security audit of UI implementation"
  prompt: |
    Security audit of the UI implementation.

    ## Changed Files
    [List from execution log]

    ## Instructions
    Focus on:
    1. XSS vectors in dynamic content rendering
    2. CSRF protection in forms
    3. Input validation and sanitization
    4. Secure storage of sensitive UI state
    5. CSP compatibility of inline styles/scripts

    For each finding: severity, CWE, file, fix.
```

### Agent C: Quality Scoring

```
Task:
  subagent_type: "senior-review:code-auditor"
  description: "Pattern consistency scoring of UI implementation"
  prompt: |
    Pattern consistency and quality scoring of the UI implementation.

    ## Changed Files
    [List from execution log]

    ## Instructions
    - Pattern consistency across components
    - CSS pattern consistency (naming, nesting, custom properties)
    - Anti-pattern checklist
    - All six mental models
    - Quality score: Code Quality, CSS Quality, Accessibility, Performance, Overall

    Score table with X/10 ratings.
```

After all complete, consolidate into `.ui-studio/11-review.md`:

```markdown
# Phase 11: Code Review

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
| Code Quality    | X/10  |
| CSS Quality     | X/10  |
| Accessibility   | X/10  |
| Security        | X/10  |
| Performance     | X/10  |
| **Overall**     | **X/10** |

## Recommended Fixes
1. [highest priority]
2. [second priority]
3. [third priority]
```

Update `state.json`: set `current_phase` to 12, add phase 11 to `completed_phases`.

---

## Phase 12: Humanize Code

**Skip if:** `--skip-humanize` flag or `humanize` plugin missing.

```
Task:
  subagent_type: "humanize:humanize"
  description: "Humanize UI code"
  prompt: |
    Improve readability of the implemented UI code. Do NOT change behavior.

    ## Changed Files
    [List from execution log]

    ## Review Context
    [Pattern findings from .ui-studio/11-review.md]

    ## Instructions
    1. Improve component and variable names
    2. Add brief comments where logic isn't self-evident
    3. Simplify complex JSX structures
    4. Clean up CSS: organize custom properties, group related rules
    5. Remove AI-generated boilerplate
    6. Ensure consistent naming conventions

    Run tests after changes.
```

**Output file:** `.ui-studio/12-humanize-log.md`

Update `state.json`: set `status` to `"complete"`.

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
UI Studio pipeline complete for: $ARGUMENTS

## Output Files
### Discovery
- Product Brief: .ui-studio/01-brief.md

### Design
- Design Direction: .ui-studio/02-design-direction.md
- Layout System: .ui-studio/03-layout.md
- UX Patterns: .ui-studio/04-ux-patterns.md
- Component Architecture: .ui-studio/05-component-architecture.md
- Mockup Preview: .ui-studio/mockup/

### Build
- Implementation Plan: .ui-studio/07-plan.md
- Execution Log: .ui-studio/08-execution-log.md

### Polish & Review
- Polish Log: .ui-studio/09-polish-log.md
- Performance Log: .ui-studio/10-performance-log.md [if React]
- Code Review: .ui-studio/11-review.md
- Humanize Log: .ui-studio/12-humanize-log.md

## Summary
- Components built: [count]
- Tasks completed: [count]
- Tests passing: [count]
- Code Quality Score: [X/10]

## Next Steps
1. Review .ui-studio/11-review.md for findings
2. Run the full test suite
3. Browser test at all breakpoints
4. Accessibility audit with screen reader
```

If `--strict-mode` and Critical findings exist:
```
STRICT MODE: Critical issues found. Review before shipping.
```
