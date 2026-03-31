# Frontend Plugin

> Two agents and seven skills for every layer of frontend work -- from CSS architecture to premium polish.

## Quick Reference

| Need | Tool | What it does |
|------|------|------|
| "What should we build?" | `/frontend:premium-web-consultant` | Strategy and planning |
| "Build it from scratch" | `/agent-teams:team-design` | Orchestrates frontend agents |
| "Improve what exists" | `/agent-teams:team-design` | Audits and redesigns existing code |
| "Optimize React perf" | [react-development](react-development.md) | React 19 performance |

## Agents

### `web-designer`

Web-specific frontend expert: CSS architecture, animations, design systems, UX psychology, accessibility, and visual polish.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | CSS refactoring, SASS migration, modern CSS adoption, micro-interactions, motion narrative, page transitions, design tokens, color systems, typography, UX psychology, accessibility, visual polish |

**Invocation:**
```
Use the web-designer agent to [improve/review/implement] [component/page/design system]
```

---

### `ui-layout-designer`

Universal layout specialist for spatial composition across web, desktop, and mobile.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Page structure, above-the-fold layouts, grid systems, responsive breakpoint strategy, CSS Grid/Flexbox handoff, spacing systems |

**Invocation:**
```
Use the ui-layout-designer agent to design [layout/page]
```

**Philosophy:** Structure first. Proportions second. Chrome last. Uses 8px spatial system and content-priority-driven layout.

---

## Skills

### `frontend`

Unified web frontend knowledge base -- CSS, UX, UI patterns, layouts, and flows.

| | |
|---|---|
| **Use for** | CSS architecture reference, UX pattern decisions, UI component selection, layout patterns, flow/onboarding patterns |

**References:**
| File | Content |
|------|---------|
| css-patterns.md | Container Queries, View Transitions, Scroll-driven Animations, architecture patterns |
| argyle-cacadia-2025-deck.md | Modern CSS talk notes (Cascadia 2025, upstream-synced from paulirish/dotfiles) |
| ux-patterns.md | Onboarding, trust/social proof, persuasion/conversion, cognitive load patterns |
| ui-pattern-guide.md | Cards vs list vs table, navigation, pagination, page archetypes |
| layout-patterns.md | Holy Grail, Full-Bleed, Split Screen, Bento Grid, Masonry, and more |
| flow-patterns.md | Step indicators, quiz layouts, coachmarks, paywalls, completeness meters |

---

### `frontend-design`

Create distinctive, production-grade frontend interfaces. Upstream-synced from anthropics/claude-code.

| | |
|---|---|
| **Use for** | Building web components, pages, or applications with high design quality |

---

### `premium-web-consultant`

Premium web design consultant for the strategy phase before writing any code. Conducts structured client discovery, produces professional deliverables (website brief, sitemap, design direction, content strategy), and hands off to specialist agents.

| | |
|---|---|
| **Invoke** | `/frontend:premium-web-consultant` |
| **Use for** | Planning a new website or redesign -- website brief, sitemap, design direction, content strategy |

---

### `shadcn-ui`

Expert guidance for building with shadcn/ui.

| | |
|---|---|
| **Use for** | Component composition, registry system, form patterns, data tables, sidebar nav, theming, Tailwind v4 migration |
| **Trigger** | "shadcn", "shadcn/ui", "shadcn components", "shadcn registry", "shadcn blocks" |

---

### `daisyui`

Expert guidance for building with daisyUI.

| | |
|---|---|
| **Use for** | Component classes, theming system, color semantics, responsive patterns, drawer/modal architecture |
| **Trigger** | "daisyui", "daisy ui", "daisyUI components", "btn-primary", "card", "modal" |

---

### `radix-ui`

Expert guidance for building with Radix UI Primitives and Themes.

| | |
|---|---|
| **Use for** | Composition patterns, asChild prop, accessibility, animation, theming, color system, keyboard navigation |
| **Trigger** | "radix", "radix-ui", "@radix-ui/react-*", "radix primitives", "radix themes" |

---

## Commands

### `/review-design`

Frontend design review -- auto-detects scope: diff mode for changed frontend files, or full audit for entire frontend. UX patterns, component hierarchy, spacing, typography, accessibility, CSS architecture, and visual polish.

---

**Related:** [agent-teams](agent-teams.md) (`/team-design` orchestrates frontend agents) | [react-development](react-development.md) (React performance) | [tauri-development](tauri-development.md) (Tauri desktop/mobile apps)
