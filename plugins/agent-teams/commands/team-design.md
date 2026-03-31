---
description: "Parallel UI design and build pipeline -- brainstorm, then run design direction + layout + UX patterns in parallel, build, polish + perf + review in parallel"
argument-hint: "<product-goal-or-feature> [--skip-brainstorm] [--skip-review] [--framework react|vue|svelte|html]"
---

# Team Design

Orchestrate the UI Studio pipeline using parallel agent teams. Phases that are independent run simultaneously, dramatically reducing total time compared to the sequential `/workflows:ui-studio`.

## Skills to Load

Before starting, invoke these skills:
- `ai-tooling:brainstorming` -- product concept exploration (Phase 1)
- `frontend:frontend` -- CSS architecture, design systems, UX patterns
- `agent-teams:parallel-feature-development` -- file ownership for build phase
- `agent-teams:team-communication-protocols` -- coordination between design agents

## Pre-flight Checks

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
2. Parse `$ARGUMENTS`:
   - `<product-goal-or-feature>`: what to design and build
   - `--skip-brainstorm`: skip interactive brainstorming, user provides brief directly
   - `--skip-review`: skip code review phase
   - `--framework`: target framework (default: auto-detect from project)

## Pipeline Overview

The sequential ui-studio pipeline has 12 phases. This team version parallelizes independent phases:

```
Phase 1: Brainstorm (sequential -- interactive with user)
         |
         v
Phase 2-4: PARALLEL DESIGN TEAM (3 agents)
  - Design Direction (web-designer)
  - Layout & Structure (ui-layout-designer)
  - UX Patterns (web-designer)
         |
         v
Phase 5: Component Architecture (synthesis -- sequential)
         |
         v
Phase 6: Write Plan (sequential)
         |
         v
Phase 7: Execute Plan (sequential, batch checkpoints)
         |
         v
Phase 8-10: PARALLEL POLISH TEAM (3 agents)
  - UI Polish (web-designer)
  - React Performance (react-performance-optimizer)
  - Code Review (code-auditor + security-auditor)
```

## Phase 1: Brainstorm (Sequential)

**Skip if** `--skip-brainstorm`. Otherwise, run interactively:

1. Explore project context (framework, CSS approach, existing components)
2. If requirements are clear from user input + codebase: synthesize brief directly
3. If vague: ask clarifying questions one at a time, propose 2-3 directions, finalize

**Output**: `.ui-studio/01-brief.md` (product brief)

**CHECKPOINT**: Present brief to user, wait for approval before continuing.

## Phase 2-4: Parallel Design Team

Spawn a design team with 3 specialists working simultaneously:

1. Use `Teammate` tool with `operation: "spawnTeam"`, team name: `design-{timestamp}`
2. Spawn 3 agents in parallel:

**Agent 1: Design Direction**
- `subagent_type`: `frontend:web-designer`
- Task: Establish aesthetic direction, typography, color palette, motion principles, spacing scale
- Input: product brief from `.ui-studio/01-brief.md`
- Output: `.ui-studio/02-design-direction.md`

**Agent 2: Layout & Structure**
- `subagent_type`: `frontend:ui-layout-designer`
- Task: Choose layout pattern, define grid system, breakpoint strategy, responsive behavior
- Input: product brief from `.ui-studio/01-brief.md`
- Output: `.ui-studio/03-layout.md`

**Agent 3: UX Patterns**
- `subagent_type`: `frontend:web-designer`
- Task: Design interaction patterns, user flows, state handling (loading/empty/error), navigation, a11y
- Input: product brief from `.ui-studio/01-brief.md`
- Output: `.ui-studio/04-ux-patterns.md`

3. Monitor `TaskList` for completion
4. After all 3 complete, verify consistency:
   - Do color/spacing tokens align between design direction and layout?
   - Do interaction patterns fit the layout grid?
   - Resolve any conflicts (design direction wins for aesthetics, layout wins for structure)

**CHECKPOINT**: Present design summary to user, wait for approval.

## Phase 5: Component Architecture (Sequential)

Synthesize all 3 design outputs into a component plan:

1. Read `.ui-studio/02-design-direction.md`, `03-layout.md`, `04-ux-patterns.md`
2. Define: component tree, props/state, CSS architecture, responsive behavior, a11y requirements, file structure
3. Output: `.ui-studio/05-component-architecture.md`

## Phase 6: Write Implementation Plan (Sequential)

Use `ai-tooling:writing-plans` skill:

1. Read all design phase files + component architecture
2. Create bite-sized tasks with TDD (test first, then implement)
3. Order: foundation -> layout scaffold -> base components -> composites -> pages -> interactions -> a11y -> responsive polish
4. Output: `.ui-studio/07-plan.md`

**CHECKPOINT**: Present plan to user, wait for approval.

## Phase 7: Execute Plan (Sequential with Batches)

Use `ai-tooling:executing-plans` skill:

1. Execute tasks in batches of 3
2. For each task: write failing test -> implement -> verify passing
3. After each batch: show progress, wait for user feedback
4. Spawn specialized implementers based on task type:
   - React components: `frontend:frontend-architect`
   - CSS/styling: `frontend:web-designer`
   - Tests: `testing:test-writer`
5. Output: `.ui-studio/08-execution-log.md`

## Phase 8-10: Parallel Polish Team

Spawn a polish/review team with 3 specialists working simultaneously:

1. Use `Teammate` tool with `operation: "spawnTeam"`, team name: `polish-{timestamp}`
2. Spawn 3 agents in parallel:

**Agent 1: UI Polish**
- `subagent_type`: `frontend:web-designer`
- Task: Add micro-interactions, hover/focus states, loading skeletons, respect prefers-reduced-motion
- Input: product brief + implemented component files
- Output: `.ui-studio/09-polish-log.md`

**Agent 2: Performance Review** (React projects only)
- `subagent_type`: `react-development:react-performance-optimizer`
- Task: Re-render optimization, bundle analysis, Core Web Vitals, state management audit
- Input: implemented component files
- Output: `.ui-studio/10-performance-log.md`

**Agent 3: Code Review**
- `subagent_type`: `senior-review:code-auditor`
- Task: Architecture review, pattern consistency, quality scoring
- Input: component architecture plan + implemented files
- Load: `senior-review:defect-taxonomy` skill
- Output: `.ui-studio/11-review.md`

**Optional Agent 4: Security Audit** (if not `--skip-review`)
- `subagent_type`: `senior-review:security-auditor`
- Task: XSS vectors, CSRF, input validation, CSP compatibility
- Input: implemented component files
- Output: appended to `.ui-studio/11-review.md`

3. Monitor `TaskList` for completion
4. Consolidate review findings into a unified report with scores

## Phase 11: Completion

1. Send `shutdown_request` to all remaining teammates
2. Call `Teammate` cleanup
3. Present final summary:

```
UI Studio (Team Mode) complete for: {product goal}

## Parallel Execution Summary
- Design team: 3 agents ran in parallel (saved ~60% design time)
- Polish team: 3-4 agents ran in parallel (saved ~70% review time)

## Output Files
- Product Brief: .ui-studio/01-brief.md
- Design Direction: .ui-studio/02-design-direction.md
- Layout System: .ui-studio/03-layout.md
- UX Patterns: .ui-studio/04-ux-patterns.md
- Component Architecture: .ui-studio/05-component-architecture.md
- Implementation Plan: .ui-studio/07-plan.md
- Execution Log: .ui-studio/08-execution-log.md
- Polish Log: .ui-studio/09-polish-log.md
- Performance Log: .ui-studio/10-performance-log.md
- Code Review: .ui-studio/11-review.md

## Scores
| Category | Score |
|----------|-------|
| Code Quality | X/10 |
| CSS Quality | X/10 |
| Accessibility | X/10 |
| Security | X/10 |
| Performance | X/10 |
| **Overall** | **X/10** |
```
