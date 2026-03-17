# Frontend Plugin

> Four agents and six skills for every layer of frontend work -- from strategic planning and creative design direction to polished production UI.
>
> **Which tool do I use?**
> | Need | Tool | What it does |
> |------|------|------|
> | "What should we build?" | `/frontend:premium-web-consultant` | Strategy and planning -- website brief, sitemap, design direction, content strategy. No code. |
> | "Build it from scratch" | `/frontend:ui-studio` | Orchestrates all frontend agents from a product brief to shipped UI. |
> | "Improve what exists" | `/frontend-redesign` | Audits and redesigns existing frontend code -- UX, layout, performance, polish. |
> | "Optimize React perf" | [react-development](react-development.md) | React 19 performance, state management, bundle optimization. Separate plugin. |

## Agents

### `ui-polisher`

Senior UI polish specialist and motion designer for premium interfaces.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Micro-interactions, animations, transitions, loading states |

**Invocation:**
```
Use the ui-polisher agent to improve [component/page]
```

---

### `ui-ux-designer`

Elite UI/UX designer for beautiful, accessible interfaces and design systems.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Design systems, user flows, wireframes, accessibility |

**Invocation:**
```
Use the ui-ux-designer agent to design [feature/system]
```

---

### `ui-layout-designer`

Spatial composition specialist for grid systems, responsive breakpoint strategy, and CSS Grid/Flexbox developer handoff.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Page structure, above-the-fold layouts, responsive strategy, layout-to-CSS specs |

**Invocation:**
```
Use the ui-layout-designer agent to design [layout/page]
```

**Philosophy:** Structure first. Proportions second. Chrome last. Uses 8px spatial system and content-priority-driven layout.

---

### `css-master`

Expert CSS developer for hands-on CSS work -- refactoring styles, migrating SASS/preprocessors to native CSS, setting up CSS architecture, adopting modern CSS features.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | CSS refactoring, SASS-to-native migration, CSS architecture, Container Queries, View Transitions, Scroll-driven animations |

**Invocation:**
```
Use the css-master agent to [refactor/migrate/architect] [styles]
```

---

## Skills

### `css-master`

CSS reference covering modern features, architecture methodologies, and production patterns.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Container Queries, View Transitions, Masonry, Scroll-driven animations, legacy CSS refactoring |

**Source:** Ported from [paulirish/dotfiles](https://github.com/paulirish/dotfiles).

---

### `premium-web-consultant`

Premium web design consultant for the strategy phase before writing any code. Conducts structured client discovery (business goals, audience, competitors, tone), produces professional deliverables, and hands off to specialist agents (seo-specialist, ui-ux-designer, ui-layout-designer, css-master, content-marketer) at defined points.

| | |
|---|---|
| **Invoke** | `/frontend:premium-web-consultant` |
| **Use for** | Planning a new website or redesign -- website brief, sitemap, design direction, content strategy |

**Deliverables:** Website brief, sitemap, design direction, content strategy, implementation roadmap. Hand off to `ui-studio` when ready to build.

> **When to use this vs other tools:** Use `premium-web-consultant` when you need to decide *what* to build. Use `ui-studio` when you have a product goal and want to build it. Use `/frontend-redesign` when you already have a frontend and want to improve it.

---

### `ui-studio`

Orchestrates full frontend development from a product goal to shipped UI. Establishes a shared product brief (goal, audience, aesthetic tone) as the north star, then coordinates frontend-design, ui-layout-designer, ui-ux-designer, ui-polisher, and react-performance-optimizer toward a coherent result.

| | |
|---|---|
| **Invoke** | `/frontend:ui-studio` |
| **Use for** | Building a new UI, page, or feature from scratch |

**Flow:** Product Brief -> Design Direction -> Layout -> UX Patterns -> Implementation -> Polish -> Performance -> Review.

> **When to use this vs other tools:** Use `ui-studio` when you have a clear product goal and want to build new UI. Use `premium-web-consultant` first if you need strategy and planning. Use `/frontend-redesign` to improve existing code.

---

### `frontend-design`

Create distinctive, production-grade frontend interfaces with bold aesthetic direction. Guides typography, color, motion, spatial composition, and visual details to avoid generic-looking output.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Web components, landing pages, UI design, production-grade interfaces |

**Source:** Ported from [anthropics/claude-code](https://github.com/anthropics/claude-code) frontend-design plugin.

---

### `shadcn-ui`

Expert guidance for building with shadcn/ui -- component composition, registry system, form patterns, data tables, sidebar navigation, theming, and Tailwind v4 migration.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | shadcn/ui components, registry authoring, complex form patterns, theming, Tailwind v4 migration |
| **Trigger** | "shadcn", "shadcn/ui", "shadcn components", "shadcn registry", "shadcn blocks" |

**Core philosophy:** shadcn/ui is NOT a component library -- you copy accessible components into your project and own them. Components build on Radix UI primitives and use Tailwind CSS for styling.

---

## Commands

### `/review-design`

Unified frontend design review. Auto-detects scope: diff mode for changed files, or full audit for the entire frontend. Covers UX patterns, CSS architecture, and React performance.

```
/review-design src/ --framework react     # full audit
/review-design --full                     # explicit full audit
/review-design                            # auto-detect: diff mode if changes exist
```

**Output:** `.design-review/report.md` -- actionable checklist with scores, grouped by category (UX, Layout, CSS).

---

**Related:** [react-development](react-development.md) (React performance optimization) | [workflows](workflows.md) (`/frontend-redesign` and `/ui-studio` orchestrate frontend agents) | [xterm](xterm.md) (terminal UI components)
