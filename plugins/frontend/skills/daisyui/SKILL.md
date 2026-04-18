---
name: daisyui
description: >
  Expert guidance for building with daisyUI -- component classes, theming system, color semantics, responsive patterns, drawer/modal architecture, and Tailwind CSS integration. Trigger when working with daisyUI components, adding daisyUI to a project, theming, or building UI with daisyUI class names. Also trigger on mentions of "daisyui", "daisy ui", "daisyUI components", "daisyUI themes", or daisyUI class patterns like "btn-primary", "card", "modal", "drawer".
  TRIGGER WHEN: working with daisyUI components, adding daisyUI to a project, theming, or building UI with daisyUI class names
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# daisyUI Expert

Guidance for building production UIs with daisyUI. Covers component usage, theming, color system, responsive patterns, and integration with Tailwind CSS.

Docs: https://daisyui.com/docs

## Core Philosophy

daisyUI is a Tailwind CSS component library that provides semantic class names for UI components. Instead of writing `flex items-center justify-center gap-2 rounded-lg bg-indigo-500 px-4 py-2 text-white`, you write `btn btn-primary`. Four pillars:

1. **Semantic classes** - meaningful names (`btn`, `card`, `modal`) instead of utility chains
2. **Theme-driven** - 35 built-in themes, unlimited custom themes via CSS variables
3. **Pure CSS** - no JS runtime, no framework lock-in, works with any stack
4. **Tailwind-native** - extends Tailwind, all utilities still available for fine-tuning

## When This Skill Activates

- Adding daisyUI to a project (`npm i -D daisyui`)
- Choosing or customizing themes
- Building layouts with daisyUI components (drawer, navbar, hero)
- Styling forms, modals, cards, tables with daisyUI classes
- Integrating daisyUI with React, Vue, Svelte, or any framework
- Questions about daisyUI class names, variants, or responsive patterns

## Synergy with Other Frontend Skills

| Need | Route to |
|------|----------|
| CSS architecture, modern CSS features, responsive images | **web-designer** |
| Page layout composition, grid systems, breakpoint strategy | **ui-layout-designer** agent |
| Animations, micro-interactions, visual polish | **web-designer** agent |
| UX flows, design tokens, component hierarchy | **web-designer** agent |
| Distinctive visual identity, avoiding generic aesthetics | **frontend** skill |
| shadcn/ui components (different library, Radix-based) | **shadcn-ui** |

**This skill** handles daisyUI-specific concerns: class names, theming, color system, component patterns, and configuration.

## Live Component Lookup

This skill contains reference patterns for the most common components. For any component's full class API -- spawn a **quick-searcher** agent to fetch the docs.

### URL patterns

| Resource | URL pattern |
|----------|-------------|
| Component docs | `https://daisyui.com/components/{name}/` |
| Theme list | `https://daisyui.com/docs/themes/` |
| Color system | `https://daisyui.com/docs/colors/` |
| Config | `https://daisyui.com/docs/config/` |
| Utilities | `https://daisyui.com/docs/utilities/` |
| Theme generator | `https://daisyui.com/theme-generator/` |

## Installation and Setup

### Install

```bash
npm i -D daisyui@latest
```

### Configure (Tailwind CSS v4+)

```css
@import "tailwindcss";
@plugin "daisyui";
```

### With theme selection

```css
@plugin "daisyui" {
  themes: light --default, dark --prefersdark, nord, dracula;
}
```

### Config options

| Option | Default | Purpose |
|--------|---------|---------|
| `themes` | `light --default, dark --prefersdark` | Themes to enable (`all`, `false`, or comma list) |
| `root` | `":root"` | CSS selector for variables (web components, shadow DOM) |
| `include` | (all) | Whitelist specific components |
| `exclude` | (empty) | Blacklist specific components |
| `prefix` | `""` | Prefix for all daisyUI classes (e.g. `d-btn`) |
| `logs` | `true` | Console output during build |

## Component Catalog

See [references/components.md](references/components.md) for the full catalog with all class names.

| Category | Components |
|----------|------------|
| Actions | Button, Dropdown, FAB/Speed Dial, Modal, Swap, Theme Controller |
| Data Display | Accordion, Avatar, Badge, Card, Carousel, Chat Bubble, Collapse, Countdown, Diff, Hover 3D Card, Hover Gallery, Kbd, List, Stat, Status, Table, Text Rotate, Timeline |
| Navigation | Breadcrumbs, Dock, Link, Menu, Navbar, Pagination, Steps, Tabs |
| Feedback | Alert, Loading, Progress, Radial Progress, Skeleton, Toast, Tooltip |
| Data Input | Calendar, Checkbox, Fieldset, File Input, Filter, Label, Radio, Range, Rating, Select, Text Input, Textarea, Toggle, Validator |
| Layout | Divider, Drawer, Footer, Hero, Indicator, Join, Mask, Stack |
| Mockup | Browser, Code, Phone, Window |

## Class Name Pattern

All daisyUI components follow a consistent naming convention:

```
{component}                  -- base class (required)
{component}-{variant}        -- style variant
{component}-{color}          -- semantic color
{component}-{size}           -- size modifier (xs, sm, md, lg, xl)
{component}-{state}          -- state modifier (active, disabled, open)
```

Example with Button:
```html
<button class="btn">Default</button>
<button class="btn btn-primary">Primary color</button>
<button class="btn btn-outline btn-sm">Small outline</button>
<button class="btn btn-primary btn-soft btn-lg">Large soft primary</button>
```

Style variants available on most components: `{component}-outline`, `{component}-ghost`, `{component}-soft`, `{component}-dash`.

## Color System

daisyUI uses **semantic color names** -- not fixed hex values. Colors change with themes automatically.

| Color | Purpose | Content pair |
|-------|---------|-------------|
| `primary` | Main brand actions | `primary-content` |
| `secondary` | Supporting actions | `secondary-content` |
| `accent` | Highlights, accents | `accent-content` |
| `neutral` | Unsaturated UI elements | `neutral-content` |
| `base-100` | Page background | `base-content` |
| `base-200` | Slightly elevated surface | -- |
| `base-300` | Most elevated surface | -- |
| `info` | Informational | `info-content` |
| `success` | Positive feedback | `success-content` |
| `warning` | Caution | `warning-content` |
| `error` | Destructive/error | `error-content` |

Colors work with all Tailwind utilities: `bg-primary`, `text-primary-content`, `border-accent`, `ring-error`, `from-primary/50`.

## Theming

### Built-in themes (35)

light, dark, cupcake, bumblebee, emerald, corporate, synthwave, retro, cyberpunk, valentine, halloween, garden, forest, aqua, lofi, pastel, fantasy, wireframe, black, luxury, dracula, cmyk, autumn, business, acid, lemonade, night, coffee, winter, dim, nord, sunset, caramellatte, abyss, silk.

### Apply themes

```html
<!-- Page-level -->
<html data-theme="nord">

<!-- Element-level (nested themes supported) -->
<div data-theme="dark">
  <div data-theme="light"><!-- light inside dark --></div>
</div>
```

### Custom theme

```css
@plugin "daisyui/theme" {
  name: "mytheme";
  default: true;
  color-scheme: light;
  --color-base-100: oklch(98% 0.02 240);
  --color-base-200: oklch(95% 0.02 240);
  --color-base-300: oklch(90% 0.02 240);
  --color-base-content: oklch(20% 0.02 240);
  --color-primary: oklch(55% 0.3 260);
  --color-primary-content: oklch(98% 0.01 260);
  --color-secondary: oklch(65% 0.15 330);
  --color-secondary-content: oklch(98% 0.01 330);
  --color-accent: oklch(70% 0.2 180);
  --color-accent-content: oklch(15% 0.02 180);
  --color-neutral: oklch(40% 0.02 240);
  --color-neutral-content: oklch(95% 0.01 240);
  --color-info: oklch(65% 0.2 250);
  --color-success: oklch(65% 0.2 150);
  --color-warning: oklch(75% 0.15 80);
  --color-error: oklch(60% 0.25 25);
  --radius-selector: 1rem;
  --radius-field: 0.5rem;
  --radius-box: 1rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

### Theme CSS variables

| Variable | Controls | Example |
|----------|----------|---------|
| `--color-{name}` | All semantic colors | `--color-primary` |
| `--radius-box` | Large containers (card, modal, alert) | `1rem` |
| `--radius-field` | Medium elements (button, input, tab) | `0.5rem` |
| `--radius-selector` | Small elements (checkbox, toggle, badge) | `1rem` |
| `--size-selector` | Scale of small elements | `0.25rem` |
| `--size-field` | Scale of medium elements | `0.25rem` |
| `--border` | Default border width | `1px` |
| `--depth` | Shadow/depth intensity (0 or 1) | `1` |
| `--noise` | Noise texture overlay (0 or 1) | `0` |

### Border radius utilities

| Class | Variable | Use for |
|-------|----------|---------|
| `rounded-box` | `--radius-box` | Cards, modals, alerts |
| `rounded-field` | `--radius-field` | Buttons, inputs, tabs |
| `rounded-selector` | `--radius-selector` | Checkboxes, toggles, badges |

## Key Patterns

### Modal (dialog element -- recommended)

```html
<button class="btn" onclick="my_modal.showModal()">Open</button>
<dialog id="my_modal" class="modal">
  <div class="modal-box">
    <h3 class="text-lg font-bold">Title</h3>
    <p class="py-4">Content here</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn">Close</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

### Drawer sidebar (responsive)

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <!-- Page content -->
    <label for="sidebar" class="btn btn-ghost lg:hidden">Menu</label>
  </div>
  <div class="drawer-side">
    <label for="sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 min-h-full w-80 p-4">
      <li><a>Home</a></li>
      <li><a>About</a></li>
    </ul>
  </div>
</div>
```

### Card

```html
<div class="card bg-base-100 w-96 shadow-xl">
  <figure><img src="photo.jpg" alt="Photo" /></figure>
  <div class="card-body">
    <h2 class="card-title">Title</h2>
    <p>Description text.</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Buy Now</button>
    </div>
  </div>
</div>
```

### Form with fieldset

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Account</legend>
  <label class="label">Email</label>
  <input type="email" class="input input-bordered w-full" placeholder="you@example.com" />
  <label class="label">Password</label>
  <input type="password" class="input input-bordered w-full" />
  <button class="btn btn-primary mt-4">Sign In</button>
</fieldset>
```

## Best Practices

See [references/best-practices.md](references/best-practices.md) for detailed patterns. Key points:

1. **Use semantic colors** -- `btn-primary` not `bg-blue-500`; themes change colors automatically
2. **Combine with Tailwind** -- daisyUI for components, Tailwind for layout/spacing/sizing
3. **Theme early** -- choose/create theme before building; avoid color overrides later
4. **Use `data-theme`** -- for theme switching, not Tailwind `dark:` (unless you need both)
5. **Prefer `<dialog>`** -- for modals over checkbox method; better a11y and ESC support
6. **Responsive drawer** -- `lg:drawer-open` for desktop-visible, mobile-toggleable sidebar
7. **Don't fight the classes** -- if you need deep customization, use `@utility` directive
8. **Join group** -- use `join` to visually connect related elements (button groups, input+button)

## Framework Integration

daisyUI is pure CSS -- works identically in React, Vue, Svelte, Solid, HTMX, or plain HTML. No framework-specific wrappers needed.

### React/Next.js

```tsx
export function Alert({ children, type = "info" }) {
  return (
    <div className={`alert alert-${type}`}>
      <span>{children}</span>
    </div>
  )
}
```

### Dynamic theme switching

```tsx
function ThemeSwitcher() {
  const [theme, setTheme] = useState("light")
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme)
  }, [theme])
  return (
    <select className="select select-bordered" value={theme}
      onChange={(e) => setTheme(e.target.value)}>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
      <option value="nord">Nord</option>
    </select>
  )
}
```

### With daisyUI's Theme Controller

```html
<input type="checkbox" value="dark" class="toggle theme-controller" />
```

The `theme-controller` class makes any checkbox/radio automatically toggle themes.

## Customization Approaches

1. **Tailwind utilities** -- add spacing, sizing, responsive modifiers to any daisyUI component
2. **Component variants** -- use built-in modifiers (`btn-outline`, `btn-ghost`, `btn-soft`)
3. **Theme variables** -- change colors, radii, borders globally via custom theme
4. **@utility directive** -- override component defaults project-wide:
   ```css
   @utility btn {
     @apply rounded-full;
   }
   ```
5. **include/exclude** -- only load components you need for smaller CSS output

## v4 to v5 Migration

See [references/migration-v5.md](references/migration-v5.md) for the full migration guide including:

- Class renames (`card-bordered` -> `card-border`, `btm-nav` -> `dock`, etc.)
- Removed classes (`form-control`, `input-group`, `-bordered` on inputs)
- Behavioral changes (footer vertical by default, inputs bordered by default)
- New components (list, status, fieldset, filter, validator, dock, calendar)
- New modifiers (`xl` size, `soft`, `dash` styles on all components)

## Common Pitfalls

See [references/best-practices.md](references/best-practices.md) for expanded discussion:

- Using Tailwind color classes (`bg-blue-500`) instead of semantic colors -- breaks theming
- Forgetting base class (`btn` before `btn-primary`) -- no styles applied
- Mixing daisyUI modal with framework portal -- use native `<dialog>` or framework's modal
- Not enabling themes in config -- only `light` and `dark` available by default
- Using `dark:` variants instead of `data-theme` -- themes are more than light/dark
