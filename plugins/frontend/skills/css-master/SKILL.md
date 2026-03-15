---
name: css-master
description: Comprehensive CSS skill covering modern CSS features, architecture methodologies (BEM, CSS Modules, Cascade Layers), SASS/preprocessors, accessibility patterns, responsive images, cross-browser compatibility, and web fonts. Trigger when writing CSS, refactoring styles, handling modern CSS features (Container Queries, View Transitions, Scroll-driven animations, Masonry), or architecting a style system.
---

<!-- Upstream source (modern CSS content): https://github.com/paulirish/dotfiles/tree/main/agents/paulirish-skills/skills/modern-css -->

# CSS Master

Comprehensive reference for writing modern, robust, maintainable, and accessible CSS - from cutting-edge native features to production architecture patterns.

---

## Layout and Responsive Design

### Flexbox Patterns (One-Dimensional Layout)

Use Flexbox for component-level alignment, distribution, and 1D layouts. Always prefer `gap` over margins for spacing.

```css
/* Cluster / Auto-wrap pattern */
.cluster {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  align-items: center;
  justify-content: space-between;
}

/* Center exactly */
.center-box {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Sidebar + Main content (Auto-grow) */
.with-sidebar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-lg);
}
.with-sidebar > .sidebar { flex: 1 1 250px; }
.with-sidebar > .main    { flex: 3 1 500px; }
```

### CSS Grid Patterns (Two-Dimensional Layout)

Use Grid for macro-layouts and structured data. Rely on fluid math to avoid Media Queries where possible.

```css
/* Fluid Auto-Grid (auto-fit + minmax) */
.auto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr));
  gap: var(--space-md);
}

/* Standard App Layout */
.app-layout {
  display: grid;
  grid-template-rows: auto 1fr auto; /* Header, Main (fluid), Footer */
  min-block-size: 100dvh;
}
```

### Container Queries

Use container queries for component-based responsive design. See `references/css-patterns.md` for detailed examples.

```css
.card { container: --my-card / inline-size; }
@container --my-card (width < 40ch) { /* component-scoped responsive */ }
```

**Container units:** `cqi`, `cqb`, `cqw`, `cqh` - size relative to container dimensions

### Media Query Range Syntax
```css
@media (width <= 1024px) { }
@media (360px < width < 1024px) { }
```

### Grid Enhancements
- **Subgrid:** Inherit parent grid lines for nested layouts
- **Masonry:** `display: grid-lanes` for Pinterest-style layouts with logical tab order

---

## Color and Theming

### Color Scheme and Light-Dark Function
```css
:root {
  color-scheme: light dark;
  --surface-1: light-dark(white, #222);
  --text-1: light-dark(#222, #fff);
}
```

### Modern Color Spaces
```css
/* OKLCH: uniform brightness, P3+ colors */
.vibrant { background: oklch(72% 75% 330); }

/* Display-P3 for HDR displays */
@media (dynamic-range: high) {
  .neon { --neon-red: color(display-p3 1 0 0); }
}

/* Better gradients */
.gradient { background: linear-gradient(to right in oklch, color(display-p3 1 0 .5), color(display-p3 0 1 1)); }
```

### Accent Color
```css
:root { accent-color: hotpink; /* Tints checkboxes, radios, range inputs */ }
```

---

## Typography

### Text Wrapping
```css
h1 { text-wrap: balance; max-inline-size: 25ch; }
p { text-wrap: pretty; max-inline-size: 50ch; }
```

### Text Box Trim
```css
h1, p, button { text-box: trim-both cap alphabetic; /* Optical vertical centering */ }
```

### Fluid Typography
```css
.heading { font-size: clamp(1rem, 1rem + 0.5vw, 2rem); }
```

### Dynamic Viewport Units
- `dvh` / `dvw` - Dynamic (accounts for mobile browser UI)
- `svh` / `svw` - Small (smallest possible viewport)
- `lvh` / `lvw` - Large (largest possible viewport)

### Variable Fonts

Prefer variable fonts to reduce HTTP requests and enable granular weight/slant control with smooth transitions.

```css
@font-face {
  font-family: 'Inter Variable';
  src: url('inter-variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}

h1 {
  font-family: 'Inter Variable', sans-serif;
  font-variation-settings: 'wght' 750, 'slnt' -10;
  transition: font-variation-settings 0.3s ease;
}
```

### Web Fonts

```css
@font-face {
  font-family: 'Inter';
  src: url('inter.woff2') format('woff2');
  font-weight: 100 900;
  font-display: swap;
}
```

**Performance tips:**
- Always use `woff2` - best compression, universal support
- Preload critical fonts: `<link rel="preload" as="font" href="font.woff2" crossorigin>`
- Use `font-display: swap` or `optional`
- Subset with `glyphhanger` or Google Fonts `text=` param

---

## Animations and Motion

### Scroll-Driven Animation
```css
.parallax { animation: slide-up linear both; animation-timeline: scroll(); }
.fade-in { animation: fade linear both; animation-timeline: view(); animation-range: cover -75cqi contain 20cqi; }
```

### View Transitions
```css
@view-transition { navigation: auto; }
nav { view-transition-name: --persist-nav; view-transition-class: --site-header; }
```

### Advanced Easing with linear()
```css
.springy {
  --spring: linear(0, 0.14 4%, 0.94 17%, 1.15 24% 30%, 1.02 43%, 0.98 51%, 1 77%, 1);
  transition: transform 1s var(--spring);
}
```

### @starting-style
```css
.dialog {
  transition: opacity .5s, scale .5s;
  @starting-style { opacity: 0; scale: 1.1; }
}
```

---

## Custom Properties and Advanced Features

### @property
```css
@property --gradient-angle {
  syntax: "<angle>"; inherits: false; initial-value: 0deg;
}
.animate { transition: --gradient-angle 1s ease; &:hover { --gradient-angle: 360deg; } }
```

### calc-size()
```css
.accordion-item.open .accordion-content { height: calc-size(auto); }
```

### Tree Counting Functions (Coming Soon)
```css
.staggered { animation-delay: calc(sibling-index() * .1s); }
```

### Conditional CSS with if() (Coming Soon)
```css
.dynamic { color: if(style(--theme: dark), white, black); }
```

---

## Architecture and Organization

### Cascade Layers
```css
@layer reset, design-system, components, utilities;
@import "open-props/colors" layer(design-system);
@layer components.nav.primary { nav { position: sticky; inset-block-start: 0; } }
```

Benefits: import third-party CSS with lower specificity, organize by concern not selector weight, nested layers for clear hierarchies.

### Architecture Patterns

See `references/css-patterns.md` for detailed BEM, CSS Modules, and SASS patterns.

- **BEM**: Plain HTML projects, design systems shipped as CSS, no build step
- **CSS Modules**: React/Vue/Svelte component projects - automatic scoping
- **Tailwind**: Utility-first, rapid iteration; use `@apply` sparingly
- **SASS**: Use only when you need maps/iteration or mixins; native CSS covers most use cases now

---

## Logical Properties

Always use Logical Properties instead of directional (physical) properties to support internationalization (RTL/LTR) natively.

- **Width/Height** -- `inline-size` / `block-size`
- **Margin/Padding Top & Bottom** -- `margin-block` / `padding-block`
- **Margin/Padding Left & Right** -- `margin-inline` / `padding-inline`
- **Top/Right/Bottom/Left** -- `inset-block-start` / `inset-inline-end` / `inset-block-end` / `inset-inline-start`

```css
/* Physical (avoid) */
.box { width: 100%; margin-top: 1rem; padding-left: 2rem; }

/* Logical (prefer) */
.box { inline-size: 100%; margin-block-start: 1rem; padding-inline-start: 2rem; }
```

---

## Interactive Components

### Dialog
```html
<dialog id="modal"><form method="dialog"><button value="confirm">OK</button></form></dialog>
<button commandfor="modal" command="showModal">Open</button>
```

### Popover
```html
<button popovertarget="menu">Show Menu</button>
<div popover id="menu">...</div>
```

`popover=hint` for ephemeral tooltips that don't dismiss other popovers.

### Anchor Positioning
```css
.tooltip-anchor { anchor-name: --tooltip; }
.tooltip[popover] { position-anchor: --tooltip; position-area: block-start; position-try-fallbacks: flip-block; }
```

### Exclusive Accordion
```html
<details name="accordion">...</details>
<details name="accordion">...</details>
```

### Customizable Select
```css
select { appearance: base-select; }
```

---

## Form Enhancements

### Field Sizing
```css
textarea, select, input { field-sizing: content; }
textarea { min-block-size: 3lh; max-block-size: 80dvh; }
```

### Validation Pseudo-Classes
```css
:user-invalid { outline-color: red; }
:user-valid { outline-color: green; }
label:has(+ input:user-invalid) { text-decoration: underline wavy red; }
```

---

## Visual Effects

### Scrollbar Styling
```css
.custom-scrollbar { scrollbar-color: hotpink transparent; scrollbar-width: thin; }
```

### Corner Shapes
```css
.fancy-corners { corner-shape: squircle; }
```

---

## Accessible Styles

See `references/css-patterns.md` for complete accessibility patterns including skip links, forced colors, and visually hidden utilities.

Key rules:
- Use `:focus-visible` for keyboard-only focus rings
- Never convey information by color alone
- WCAG contrast: 4.5:1 normal text (AA), 3:1 large text (AA), 3:1 UI components
- Use `oklch()` - uniform lightness makes contrast estimation intuitive
- Respect `prefers-reduced-motion`, `prefers-color-scheme`, `prefers-contrast`

---

## Checking Browser Support: Baseline

- **Widely Available:** Supported in last 2.5 years of all major browsers
- **Newly Available:** Available in all major browsers
- **Limited Availability:** Not yet in all browsers

**How to check:** Fetch https://web-platform-dx.github.io/web-features-explorer/groups/, [caniuse.com](https://caniuse.com), MDN compatibility tables.

---

## Canonical Resources

- [CSS Wrapped 2025](https://chrome.dev/css-wrapped-2025/)
- [The Coyier CSS Starter](https://frontendmasters.com/blog/the-coyier-css-starter/)
- [Adam Argyle's CascadiaJS 2025 Deck](https://cascadiajs-2025.netlify.app/) - (markdownified locally in ./references/argyle-cacadia-2025-deck.md)
- [Modern CSS in Real Life](https://chriscoyier.net/2023/06/06/modern-css-in-real-life/)

## Usage Guidelines

1. **Prioritize Stability:** Recommend Newly Available or Widely Available features for production. Use Limited Availability with `@supports` or progressive enhancement.
2. **Use the web platform:** Prefer standard CSS over JavaScript libraries for layout, animation, and interaction.
3. **Code Style:** Use modern color spaces (`oklch`) for new palettes.

---

## References

- `references/css-patterns.md` - Container Query examples, BEM/CSS Modules/SASS patterns, accessibility tables, cross-browser compatibility, responsive images, real-world component example
- `references/argyle-cacadia-2025-deck.md` - Adam Argyle's CascadiaJS 2025 presentation notes
