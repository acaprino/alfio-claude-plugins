---
description: >
  React performance and optimization review -- state management audit, bundle analysis, re-render detection, React 19 API adoption, and Vercel best practices checklist -- outputs an actionable markdown report.
  TRIGGER WHEN: the user asks to review React code for performance, re-renders, bundle size, or React 19 API adoption.
  DO NOT TRIGGER WHEN: reviewing CSS/design (use /frontend:review-design) or non-React frontend code.
argument-hint: "[src-path] [--strict-mode]"
---

# React Performance Review

You are a senior React performance auditor. Review React code for performance, state management, bundle optimization, and modern API adoption.

## CRITICAL RULES

1. **React-only scope.** Ignore CSS, layout, visual polish. Focus on components, state management, bundle, and React patterns.
2. **Run the agent.** Fire the react-performance-optimizer agent with the full context.
3. **Write markdown report.** Output is `.react-review/report.md` -- an actionable checklist with scores, findings, and fix instructions.
4. **Never enter plan mode.** Execute immediately.

## Step 1: Detect Scope

### Check for React files

```bash
# Check for changed React files in git diff
git diff HEAD --name-only | grep -E '\.(tsx|jsx)$' || true
git diff --name-only | grep -E '\.(tsx|jsx)$' || true
git diff --cached --name-only | grep -E '\.(tsx|jsx)$' || true
```

### Decision tree

**Diff mode** (changed React files exist AND `--full` is NOT set):
- Review only the changed React files
- Get the diff: `git diff HEAD -- <react files>`

**Full mode** (no React changes in diff, OR `--full` flag set):
- Scan entire frontend: `src/`, `app/`, `components/`, `pages/` -- or path from `$ARGUMENTS`

### Discover React files (full mode only)

```bash
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) | head -80
```

Or use the path from `$ARGUMENTS` if provided.

If no React files are found, stop and say so.

## Step 1.5: Run Deterministic Linters (if available)

```bash
# React/JS linting (if eslint is configured)
npx eslint --format json "src/**/*.{tsx,jsx}" 2>/dev/null || true
```

Pass ESLint output to the agent for ground truth.

## Step 2: Sample Key Files & Gather Context

Read a representative cross-section:
- Entry layout files (e.g., `App.tsx`, `Layout.tsx`, `_app.tsx`, `root.tsx`)
- 3-5 core components
- State management files (stores, contexts, atoms)
- Config files (vite.config, next.config, tsconfig)

## Step 3: Run Review Agent

```
Task:
  subagent_type: "react-development:react-performance-optimizer"
  description: "React performance and bundle optimization audit"
  prompt: |
    Audit the React performance, state management, and bundle optimization of this frontend codebase.

    ## Scope
    [list of key files sampled]

    ## File Contents
    [paste sampled components, state management files, and config -- NOT stylesheets]

    ## Product Brief (if available)
    [paste brief content -- especially performance budget and stack info -- or "No product brief found"]

    ## Linter Output (if available)
    [paste ESLint JSON report if captured in Step 1.5, or "No linter output available"]

    ## Vercel React Best Practices Checklist (62 rules -- flag violations)

    **1. Eliminating Waterfalls (CRITICAL):** async-defer-await (move await into branches), async-parallel (Promise.all for independent ops), async-dependencies (better-all for partial deps), async-api-routes (start promises early, await late), async-suspense-boundaries (stream with Suspense)
    **2. Bundle Size (CRITICAL):** bundle-barrel-imports (import directly, avoid barrels), bundle-dynamic-imports (next/dynamic for heavy components), bundle-defer-third-party (load analytics after hydration), bundle-conditional (load modules only when activated), bundle-preload (preload on hover/focus)
    **3. Server-Side (HIGH):** server-auth-actions, server-cache-react (React.cache per-request), server-cache-lru (cross-request LRU), server-dedup-props, server-hoist-static-io, server-serialization (minimize client data), server-parallel-fetching, server-after-nonblocking
    **4. Client-Side Data (MEDIUM-HIGH):** client-swr-dedup, client-event-listeners (deduplicate global), client-passive-event-listeners (passive for scroll), client-localstorage-schema (version and minimize)
    **5. Re-render Optimization (MEDIUM):** rerender-defer-reads, rerender-memo (extract expensive work), rerender-memo-with-default-value, rerender-dependencies (primitive deps), rerender-derived-state (subscribe to derived booleans), rerender-derived-state-no-effect, rerender-functional-setstate, rerender-lazy-state-init, rerender-simple-expression-in-memo, rerender-move-effect-to-event, rerender-transitions (startTransition), rerender-use-ref-transient-values, rerender-no-inline-components
    **6. Rendering (MEDIUM):** rendering-animate-svg-wrapper, rendering-content-visibility, rendering-hoist-jsx, rendering-svg-precision, rendering-hydration-no-flicker, rendering-hydration-suppress-warning, rendering-activity, rendering-conditional-render (ternary not &&), rendering-usetransition-loading, rendering-resource-hints, rendering-script-defer-async
    **7. JS Performance (LOW-MEDIUM):** js-batch-dom-css, js-index-maps (Map for lookups), js-cache-property-access, js-cache-function-results, js-cache-storage, js-combine-iterations, js-length-check-first, js-early-exit, js-hoist-regexp, js-min-max-loop, js-set-map-lookups, js-tosorted-immutable, js-flatmap-filter
    **8. Advanced (LOW):** advanced-event-handler-refs, advanced-init-once, advanced-use-latest

    ## Instructions
    Use the checklist above as your primary audit framework. Flag any violations you find in the reviewed code, citing the specific rule ID (e.g. "Violates bundle-barrel-imports").

    Evaluate (in addition to the rules above):
    1. **React Compiler readiness**: Is `babel-plugin-react-compiler` configured? Identify patterns the compiler can auto-optimize vs patterns requiring manual intervention (external store reads, non-React state mutations, dynamic property access)
    2. **External store selector audit (CRITICAL)**:
       - Selectors returning objects/arrays without `useShallow` -- causes re-renders on every store update
       - Selectors with `.filter()` / `.map()` / `.reduce()` creating new references every render
       - `useStore()` with no selector -- subscribes to entire store
       - Component receiving store-derived object as prop without memoization
    3. **React 19 API adoption**: Are newer APIs used where beneficial?
       - `use()` for conditional data fetching and context
       - `useOptimistic()` for optimistic UI updates
       - `useFormStatus()` for form submission state
       - `useActionState()` for server action results
       - `useDeferredValue()` for separating critical vs deferrable updates
    4. **State management**: Zustand/Jotai/Redux selector patterns, prop drilling, state duplication, useEffect chains
    5. **Bundle optimization**: Heavy imports, missing code splitting, lazy loading opportunities, tree-shaking blockers
    6. **Virtualization check**: Large lists/tables not using TanStack Virtual or similar, index as key in virtualized lists
    7. **Context-aware caching**: TanStack Query config appropriate for app type? CRUD apps need short stale times, real-time apps need WebSocket invalidation, static content can use long cache
    8. **useEffect/useCallback infinite loop detection (CRITICAL)**:
       - `useCallback` that updates state listed in its own dependency array, called from a `useEffect` that depends on the callback -- creates infinite re-trigger cycle
       - `useEffect` with no ref guard calling state-updating functions on mount
       - Unstable callback references (object/array deps) in `useEffect` dependency arrays causing continuous re-firing
       - Symptom: repeated identical network requests, 429 rate limit errors, CPU spike on component mount
    9. **useEffect cleanup audit**:
       - Missing `AbortController` on fetch calls
       - `Channel.onmessage` not nulled on unmount
       - WebSocket connections not closed
       - Missing `clearInterval` / `clearTimeout`
       - Missing `removeEventListener`
    10. **Stale closure detection (CRITICAL)**:
       - Variables derived from state/props captured in `useEffect(..., [])` closures without ref indirection
       - Event handlers registered at mount time reading state that changes after mount
       - Interval/timeout callbacks reading stale captured values
       - Symptom: handler uses outdated state value, decisions based on stale data, no crash or warning
    11. **Performance budget** (if brief provided): Does the current state meet the stated Core Web Vitals or performance targets?

    For each finding: severity (Critical/High/Medium/Low), file, issue, specific fix with code example.
    Note what's done well.

    Return structured JSON at the end:
    ```json
    {
      "findings": [
        { "severity": "Critical", "category": "Re-renders", "file": "...", "issue": "...", "fix": "..." }
      ],
      "positives": ["..."],
      "score": { "re_render_control": 6, "state_management": 7, "bundle": 8, "overall": 7 }
    }
    ```
```

## Step 4: Generate Markdown Report

After the agent completes, create `.react-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `.react-review/report.md`

```markdown
# React Performance Review -- [date]

Full React audit - [N] components - [M] state files

## Product Brief Context

[If a product brief was found, summarize performance budget and stack info. If not, note "No product brief found -- reviewed against general best practices."]

## Scores

| Category | Score |
|----------|-------|
| Re-render Control | X/10 |
| State Management | X/10 |
| Bundle Optimization | X/10 |
| React 19 Adoption | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `Component.tsx`, `Store.ts`, ...

---

## Critical & High Issues

### Re-render Control

#### `Store.ts` -- [issue title]
- **Severity**: Critical
- **Issue**: [description]
- **Fix**: [fix instruction with code]
- [ ] Fixed

### State Management

#### `Context.tsx` -- [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

### Bundle Optimization

#### `index.ts` -- [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

---

## Medium & Low Issues

[Same format as above]

---

## What's Working Well

- [positive observation]
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
React performance review complete.

Report: .react-review/report.md

Overall Score: X/10
Re-renders: X/10 | State: X/10 | Bundle: X/10 | React 19: X/10

Critical: X | High: X | Medium: X | Low: X

Top 3 issues:
1. [critical issue summary]
2. [high issue summary]
3. [high issue summary]
```

If `--strict-mode` is set and Critical findings exist:
```
STRICT MODE: X critical React performance issues found. Recommend addressing before shipping.
```
