---
description: >
  Frontend design review -- auto-detects scope: diff mode for changed frontend files, or full audit for entire frontend. UX patterns, component hierarchy, spacing, typography, accessibility, CSS architecture, and visual polish -- outputs an actionable markdown report.
  TRIGGER WHEN: the user asks for a design review, UX audit, CSS review, or frontend code review for design quality.
  DO NOT TRIGGER WHEN: the review is strictly about React performance (use /react-development:review-react) or backend code.
argument-hint: "[src-path] [--full] [--framework react|vue|svelte] [--strict-mode]"
---

# Frontend Design & Performance Review

You are a senior frontend design auditor. Review frontend code for design quality, layout, CSS architecture, and performance. Auto-detects scope based on git state.

## CRITICAL RULES

1. **Auto-detect scope.** Check git diff for frontend file changes first. If found, review only changed files (diff mode, 4 agents). If no diff or `--full` flag, audit the entire frontend (full mode, 5 agents).
2. **Design + CSS + Visual Polish.** Ignore backend files, API routes, build config. Focus on components, stylesheets, layout files. For React-specific performance review, use `/react-development:review-react`.
3. **Run all agents in parallel.** Fire all in a single response.
4. **Write markdown report.** Output is `.design-review/report.md` -- an actionable checklist with scores, findings, and fix instructions.
5. **Never enter plan mode.** Execute immediately.

## Step 1: Detect Scope

### Check for changed frontend files

```bash
git diff HEAD --name-only | grep -E '\.(tsx|jsx|vue|svelte|css|scss|sass|less|html)$' || true
git diff --name-only | grep -E '\.(tsx|jsx|vue|svelte|css|scss|sass|less|html)$' || true
git diff --cached --name-only | grep -E '\.(tsx|jsx|vue|svelte|css|scss|sass|less|html)$' || true
```

### Decision tree

**Diff mode** (changed frontend files exist AND `--full` is NOT set):
- Review only the changed frontend files
- Get the diff: `git diff HEAD -- <frontend files>`
- Run 3 agents: UX & Components, Layout & Spatial Design, Visual Polish & Motion
- This is the default when uncommitted frontend changes exist

**Full mode** (no frontend changes in diff, OR `--full` flag set):
- Scan entire frontend: `src/`, `app/`, `components/`, `pages/`, `styles/` -- or path from `$ARGUMENTS`
- Run 4 agents: UX & Components, Layout & Spatial Design, CSS Architecture, Visual Polish & Motion

### Discover frontend files (full mode only)

```bash
find src -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.svelte" -o -name "*.css" -o -name "*.scss" -o -name "*.sass" \) | head -80
```

Or use the path from `$ARGUMENTS` if provided. List what you find -- components, pages, and stylesheet files.

If no frontend files are found, stop and say so.

## Step 1.5: Run Deterministic Linters (if available)

Before sampling files, run any available linting tools and capture their output. These provide ground truth that agents can interpret and explain rather than re-discovering manually:

```bash
# CSS linting (if stylelint is configured)
npx stylelint "**/*.css" --formatter json 2>/dev/null || true

# Accessibility audit (if axe-core CLI is available)
npx @axe-core/cli --format json 2>/dev/null || true
```

If any of these commands produce output, pass the relevant results to the corresponding agent:
- Stylelint output to Agent C1 (CSS Architecture)
- Axe output to Agent A (UX Patterns)

This reduces hallucinations and lets agents focus on explaining WHY issues exist and HOW to fix them, rather than counting brackets.

## Step 2: Sample Key Files & Gather Context

Read a representative cross-section:
- Entry layout files (e.g., `App.tsx`, `Layout.tsx`, `_app.tsx`, `root.tsx`)
- 3-5 core components
- Primary stylesheet(s) or `globals.css` / `tailwind.config`
- Design token files (`tokens.ts`, `theme.ts`, `variables.css`)

This gives you the design language, patterns, and architecture to evaluate against.

**Context segmentation:** Do NOT pass all files to all agents. Each agent should receive only the files relevant to its domain:
- **Agent A (UX):** Components, layout files, brief
- **Agent B (Layout):** Layout files, stylesheets, design tokens, brief
- **Agent C1 (CSS):** Stylesheets, config files, design tokens
- **Agent C2 (Visual Polish):** Stylesheets, animated components

This avoids context duplication and keeps each agent focused.

**UI Studio brief check:** Look for a product brief file (`brief.md`, `product-brief.md`, or similar) in the project root or docs directory. If found, use it as the north star for evaluating design coherence -- every UX, layout, and aesthetic decision should align with the stated goal, audience, and aesthetic tone from the brief. Pass the brief content to all agents as evaluation context.

## Step 3: Run Parallel Review Agents

Fire all agents **in parallel** in a single response (3 in diff mode, 4 in full mode):

### Agent A: UX Patterns & Component Architecture

```
Task:
  subagent_type: "web-designer"
  description: "Full UX and component architecture design audit"
  prompt: |
    Perform a full UX and component architecture audit of this frontend codebase.

    ## Scope
    [list of key files sampled]

    ## File Contents
    [paste sampled component and layout file contents -- NOT stylesheets, those go to CSS agents]

    ## Product Brief (if available)
    [paste brief content or "No product brief found -- evaluate against general UX best practices"]

    ## Linter Output (if available)
    [paste axe-core accessibility report if captured in Step 1.5, or "No linter output available"]

    ## Instructions
    Evaluate:
    1. **Component responsibility**: God components, missing abstractions, component prop explosion
    2. **UX patterns**: Consistency of interaction patterns (forms, modals, navigation, data loading)
    3. **Empty/loading/error states**: Are all three states handled everywhere they're needed?
    4. **Information hierarchy**: Is visual hierarchy consistent? Do primary/secondary/tertiary actions follow a system?
    5. **User flows**: Are there obvious dead ends, missing feedback, or confusing navigation?
    6. **Design system adherence**: Are colors, spacing, and typography from a token system, or are they scattered arbitrary values?
    7. **Accessibility audit**: Semantic HTML, ARIA roles, keyboard navigation, focus management, color contrast awareness
    8. **Brief alignment** (if brief provided): Does the UX serve the stated goal and audience? Are interaction patterns appropriate for the target user?
    9. **Laws of UX audit**: Evaluate against core UX laws:
       - Fitts's Law: Are click/tap targets appropriately sized and positioned? Are primary actions easy to reach?
       - Hick's Law: Are users overwhelmed by too many choices? Are complex decisions broken into steps?
       - Jakob's Law: Do interaction patterns follow familiar conventions users expect from similar products?
       - Miller's Law: Is information chunked into digestible groups (7 +/- 2)?
       - Doherty Threshold: Do interactions feel responsive (< 400ms feedback)?
       - Peak-End Rule: Are the peak moments and final interactions memorable and positive?
       - Aesthetic-Usability Effect: Does visual polish compensate for minor usability issues?
    10. **Senior production details**:
        - 5-second glance test: Can a new user understand the page purpose in 5 seconds?
        - Letter spacing on large headlines (> 32px should have tighter tracking)
        - Nested rounded corners: inner radius = outer radius - gap (not matching radii)
        - HSB color tinting for hover/active states (not opacity)
        - Card design: do cards use visual hierarchy instead of labels?
        - Kill lines/use space: is content tight or is there unnecessary padding/decoration?
        - Action-benefit button copy: do CTAs describe the benefit, not just the action?
        - Authentic photos vs stock photos
    11. **Visual style consistency**: Identify which aesthetic the project uses (glassmorphism 2.0, bento grid, gradient revival, dark-first, motion-rich, brutalism, minimalism, typographic-first, archival index) and whether it's applied consistently across all pages and components
    12. **UX pattern correctness**: Evaluate onboarding patterns (coachmarks, guided tour, blank slate, lazy registration, completeness meter), trust/social proof patterns, and cognitive load patterns
    13. **Compliance-driven UX**: European Accessibility Act readiness, WCAG 2.2 new criteria (focus appearance 2.4.11, target size 2.5.8), AI transparency requirements
    14. **Digital wellbeing**: Natural pause points, addictive pattern detection (dark patterns, infinite scroll without purpose), attention budget
    15. **Sustainable UX**: Energy-efficient patterns (dark mode, reduced animations option, lazy loading), resource-heavy anti-patterns (autoplay video, excessive polling)

    For each finding: severity (Critical/High/Medium/Low), file, issue, specific fix recommendation.
    Note what's working well.

    Return structured JSON at the end:
    ```json
    {
      "findings": [
        { "severity": "High", "category": "Accessibility", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "ux_consistency": 7, "accessibility": 5, "component_design": 8, "overall": 7 }
    }
    ```
```

### Agent B: Layout System & Spatial Design

```
Task:
  subagent_type: "ui-layout-designer"
  description: "Layout system, grid, and spatial design audit"
  prompt: |
    Audit the layout system, grid, spacing, and spatial design of this frontend codebase.

    ## Scope
    [list of key files sampled]

    ## File Contents
    [paste sampled layout files, stylesheets, and design token files]

    ## Product Brief (if available)
    [paste brief content or "No product brief found -- evaluate against general layout best practices"]

    ## Instructions
    Evaluate:
    1. **Layout pattern identification**: Identify which layout pattern is used (holy grail, full-bleed, split screen, organic/anti-grid, editorial asymmetry, bento grid, sidebar+main, masonry, centered narrow, stacked sections, card grid with subgrid) and whether it's the right choice for the content type
    2. **UI pattern selection audit**: Are the right display patterns chosen? Cards vs list vs table vs gallery vs carousel for data display. Navigation pattern correctness (tabs, accordion, breadcrumbs, fat footer). Content loading pattern (pagination vs continuous scroll vs load more)
    3. **Page archetype audit**: Does the layout follow best practices for its archetype (dashboard, product page, pricing table, wizard, FAQ, settings panel)?
    4. **Flow & onboarding layout**: Step indicators, single-step layouts, coachmark positioning, notification positioning, paywall layout, completeness meter layout, lazy registration gate
    5. **Spacing scale**: Is spacing derived from a consistent scale (4px/8px/rem)? Or arbitrary pixel values scattered everywhere?
    6. **Responsive strategy**: Are breakpoints consistent? Mobile-first vs desktop-first? Are there layout shifts on resize?
    7. **Typography system**: Font scale, line-height, letter-spacing -- are they tokens or raw values?
    8. **Spatial composition**: Visual weight distribution, proportion rules (rule of thirds, golden ratio), optical vs mathematical alignment, negative space usage, Z-axis depth
    9. **Above-the-fold engineering**: Viewport height strategy, LCP optimization, the three instant questions (what is this, why should I care, what do I do next)
    10. **Alignment & rhythm**: Do elements align to a clear baseline? Is vertical rhythm maintained?
    11. **Container strategy**: Max-widths, centering, content containers -- are they consistent?
    12. **Brief alignment** (if brief provided): Does the layout serve the stated audience and aesthetic tone? Is the spatial hierarchy appropriate?

    For each finding: severity (Critical/High/Medium/Low), file, issue, specific fix.
    Note what's done well.

    Return structured JSON at the end:
    ```json
    {
      "findings": [
        { "severity": "Medium", "category": "Spacing", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "layout_system": 7, "responsive": 8, "typography": 6, "overall": 7 }
    }
    ```
```

### Agent C1: CSS Architecture (full mode only)

Skip this agent in diff mode. Only run in full mode.

```
Task:
  subagent_type: "web-designer"
  description: "CSS architecture and modern feature adoption audit"
  prompt: |
    Audit the CSS architecture, modern feature adoption, and stylesheet quality of this frontend codebase.

    ## Scope
    [list of key files sampled]

    ## File Contents
    [paste sampled stylesheets, config files, and design tokens only -- NOT component logic]

    ## Product Brief (if available)
    [paste brief content or "No product brief found -- evaluate against CSS architecture best practices"]

    ## Linter Output (if available)
    [paste stylelint JSON report if captured in Step 1.5, or "No linter output available"]

    ## Instructions
    Evaluate:
    1. **Modern CSS feature adoption**: Are these features used where beneficial?
       - Container Queries for component-level responsiveness
       - Native CSS nesting instead of preprocessor nesting
       - `@scope` for component style isolation
       - Cascade Layers (`@layer`) for specificity management
       - `oklch()` / `color-mix()` for color systems
       - `clamp()` for fluid typography and spacing
       - Logical properties (`inline`, `block`) for internationalization
       - `dvh` / `svh` / `lvh` for viewport units
       - Anchor positioning for tooltips and popovers
    2. **Architecture quality**:
       - Layer structure: does the project organize styles into layers (reset/tokens/base/components/utilities/overrides)?
       - Selector depth and specificity management -- are selectors shallow and predictable?
       - `!important` abuse -- count and categorize all `!important` usage
       - Dead CSS: unused selectors, legacy overrides, commented-out blocks
    3. **Preprocessor migration readiness** (if SASS/Less is used):
       - SASS variables vs CSS custom properties -- which is used, should it migrate?
       - SASS nesting vs native nesting -- can the preprocessor be dropped?
       - SASS mixins vs modern CSS alternatives (Container Queries, `clamp()`, logical properties)
    4. **CSS performance**:
       - `content-visibility` for off-screen content
       - `will-change` discipline (set before animation, remove after)
       - Layout thrashing -- styles that force reflow in animation loops
       - Font loading strategies (`font-display`, preload, subsetting)
    5. **Accessibility CSS**:
       - `prefers-reduced-motion` -- is it respected for all animations?
       - `prefers-color-scheme` -- does dark mode use it?
       - `forced-colors` -- does high contrast mode work?
       - `focus-visible` patterns -- are focus styles clear and consistent?
    6. **Component isolation**: CSS Modules, `@scope`, naming conventions (BEM, utility-first) -- are styles scoped or leaking across components?
    7. **Brief alignment** (if brief provided): Does the CSS architecture support the project's scale and team needs?

    For each finding: severity (Critical/High/Medium/Low), file, issue, specific fix.
    Note what's done well.

    Return structured JSON at the end:
    ```json
    {
      "findings": [
        { "severity": "Medium", "category": "CSS Architecture", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "modern_css": 6, "architecture": 7, "performance": 8, "accessibility_css": 7, "overall": 7 }
    }
    ```
```

### Agent C2: Visual Polish & Motion

```
Task:
  subagent_type: "web-designer"
  description: "Visual polish and motion design audit"
  prompt: |
    Audit the visual polish, animation quality, and motion design of this frontend codebase.

    ## Scope
    [list of key files sampled]

    ## File Contents
    [paste sampled stylesheets and animated/interactive component files only]

    ## Product Brief (if available)
    [paste brief content or "No product brief found -- evaluate against general visual polish best practices"]

    ## Instructions
    Evaluate:
    1. **Visual consistency**: Border-radius, shadow elevation, color palette -- are they consistent or scattered?
    2. **Dark mode**: Is dark mode supported? Are colors properly adapted or just inverted?
    3. **Motion narrative**: Are scroll-triggered sequences telling a brand story? Is there cinematic page transition flow? Choreographed element entrances that build meaning? Pacing and rhythm variation?
    4. **Native browser animation audit**:
       - View Transitions API usage for page/route transitions
       - `@starting-style` for DOM entry animations
       - `transition-behavior: allow-discrete` for display/visibility changes
       - CSS `animation-timeline` for scroll-driven animations
       - AutoAnimate for list reordering
    5. **Glassmorphism 2.0 assessment**: If frosted glass effects are used, are they subtle and tactile (mature) or heavy-handed? Proper `backdrop-filter` layering?
    6. **Micro-interaction completeness**:
       - Hover and press states on all interactive elements
       - Input focus animations (not just outline)
       - Toggle spring physics and checkbox satisfaction
       - Form validation animations (shake, highlight, inline error entrance)
       - Loading state transitions (skeleton to content)
    7. **Animation technical quality**:
       - Easing curves: ease-out for enters, ease-in for exits, spring for interactions
       - GPU-accelerated properties only (`transform`, `opacity`) -- no animating `width`, `height`, `top`, `left`
       - `prefers-reduced-motion` respected for all animations
       - Consistent timing constants (not random durations)
       - No janky animations (layout-triggering properties in animation loops)
    8. **CSS performance**: Unnecessary repaints, oversized background images, unoptimized filters
    9. **Brief alignment** (if brief provided): Does the visual polish match the stated aesthetic tone? Is motion appropriate for the audience?

    For each finding: severity (Critical/High/Medium/Low), file, issue, specific fix.
    Note what's done well.

    Return structured JSON at the end:
    ```json
    {
      "findings": [
        { "severity": "Low", "category": "Visual Polish", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "visual_polish": 7, "motion_design": 6, "micro_interactions": 8, "overall": 7 }
    }
    ```
```

## Step 4: Generate Markdown Report

After all agents complete, create `.design-review/` directory and write `report.md`.

Merge and deduplicate overlapping findings from all agents. Order by severity, then file name. Group findings by category (UX, Layout, CSS Architecture, Visual Polish & Motion, Performance).

**Output file:** `.design-review/report.md`

```markdown
# Design & Performance Review -- [date]

Full frontend audit - [N] components - [M] stylesheets

## Product Brief Context

[If a product brief was found, summarize goal, audience, aesthetic tone, and performance budget. If not, note "No product brief found -- reviewed against general best practices."]

## Scores

| Category | Score |
|----------|-------|
| UX Quality | X/10 |
| Layout System | X/10 |
| CSS Architecture | X/10 |
| Visual Polish & Motion | X/10 |
| Accessibility | X/10 |
| Typography | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `Component.tsx`, `Layout.tsx`, `globals.css`, ...

---

## Critical & High Issues

### UX & Components

#### `Button.tsx` -- [issue title]
- **Severity**: Critical
- **Issue**: [description]
- **Fix**: [concrete fix instruction]
- [ ] Fixed

### Layout & Spacing

#### `Layout.tsx` -- [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

### CSS Architecture

#### `globals.css` -- [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

### Visual Polish & Motion

#### `AnimatedCard.tsx` -- [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

---

## Medium & Low Issues

### UX & Components
[Same format as above]

### Layout & Spacing
[Same format]

### CSS Architecture
[Same format]

### Visual Polish & Motion
[Same format]

---

## What's Working Well

- [positive observation from agents]
- [another positive]

---

## Action Plan

1. [ ] [top priority fix -- from critical findings]
2. [ ] [second priority]
3. [ ] [third priority]
4. [ ] [fourth priority]
5. [ ] [fifth priority]
```

**Print a short summary** in the conversation:

```
Design & performance review complete.

Report: .design-review/report.md

Overall Score: X/10
UX: X/10 | Layout: X/10 | CSS: X/10 | Polish: X/10 | Accessibility: X/10

Critical: X | High: X | Medium: X | Low: X

Top 3 issues:
1. [critical issue summary]
2. [high issue summary]
3. [high issue summary]
```

If `--strict-mode` is set and Critical findings exist:
```
STRICT MODE: X critical design issues found. Recommend addressing before shipping.
```
