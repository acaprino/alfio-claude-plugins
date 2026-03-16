# React Development Plugin

> React 19 performance optimization, state management auditing, bundle analysis, re-render detection, and Vercel best practices enforcement.

## Agents

### `react-performance-optimizer`

Senior React performance engineer specializing in React 19 optimization, bundle reduction, and modern web/desktop performance.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Bundle analysis, re-render optimization, state management audit, virtualization, React Compiler readiness |

**Invocation:**
```
Use the react-performance-optimizer agent to analyze [component/app]
```

**Core philosophy:** Measure first, optimize second. External store subscriptions are the #1 re-render source -- React Compiler cannot fix them. Surgical selectors over broad subscriptions.

**Key areas:**
- React Compiler (React Forget) configuration and limitations
- External store selector optimization (Zustand, Jotai, Redux)
- React 19 APIs (`use()`, `useOptimistic()`, `useDeferredValue()`)
- Server Components and streaming (web only)
- Bundle splitting, tree shaking, and preloading
- TanStack Virtual for large datasets
- `useEffect` cleanup patterns

**Performance targets:**
| Metric | Web | Desktop |
|--------|-----|---------|
| Bundle (initial) | < 200KB | < 3MB |
| Frame rate | 60 FPS | 60 FPS |
| Render time | < 16ms | < 16ms |
| Memory baseline | N/A | < 100MB |

**Agent delegation:** Defers CSS issues to `css-master`, layout to `ui-layout-designer`, animation jank to `ui-polisher`, and Tauri IPC/Rust to `tauri-optimizer`.

---

## Skills

### `react-best-practices`

62 performance optimization rules from Vercel Engineering across 8 categories, prioritized by impact.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Writing, reviewing, or refactoring React/Next.js code for optimal performance patterns |

**Source:** Ported from [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills).

**Rule categories (by priority):**

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Eliminating Waterfalls | CRITICAL |
| 2 | Bundle Size Optimization | CRITICAL |
| 3 | Server-Side Performance | HIGH |
| 4 | Client-Side Data Fetching | MEDIUM-HIGH |
| 5 | Re-render Optimization | MEDIUM |
| 6 | Rendering Performance | MEDIUM |
| 7 | JavaScript Performance | LOW-MEDIUM |
| 8 | Advanced Patterns | LOW |

Includes `references.md` with all 62 rules expanded and a `rules/` directory with individual rule files containing code examples.

---

## Commands

### `/review-react`

React performance and optimization review -- state management audit, bundle analysis, re-render detection, React 19 API adoption, and Vercel best practices checklist.

```
/review-react src/ --strict-mode
```

**Scope detection:**
- **Diff mode** (default): Reviews only changed `.tsx`/`.jsx` files from `git diff`
- **Full mode**: Scans entire frontend when no React changes exist or `--full` is set

**Pipeline:** Detect scope -> Run ESLint (if available) -> Sample key files -> Fire `react-performance-optimizer` agent with Vercel checklist -> Generate markdown report

**Output:** `.react-review/report.md` -- actionable checklist with scores per category (re-render control, state management, bundle, React 19 adoption) and prioritized findings.

---

**Related:** [frontend](frontend.md) (UI design, layout, CSS) | [workflows](workflows.md) (`/frontend-redesign` and `/ui-studio` use this agent)
