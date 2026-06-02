# Layout Patterns Library

CSS layout patterns for common page structures. Used by `frontend-layout` agent.

## Holy Grail

Full-page chrome: header / (sidebar + main + aside) / footer.
```css
.holy-grail {
  display: grid;
  grid-template:
    "header header header" auto
    "sidebar main aside" 1fr
    "footer footer footer" auto
    / 240px 1fr 200px;
  min-height: 100dvh;
}
```

## Full-Bleed with Content Column

Content constrained to max-width; some sections break out to full viewport width.
```css
.page {
  display: grid;
  grid-template-columns:
    [full-start] minmax(1.5rem, 1fr)
    [content-start] min(100% - 3rem, 1200px)
    [content-end] minmax(1.5rem, 1fr)
    [full-end];
}
.full-bleed { grid-column: full; }
.content    { grid-column: content; }
```

## Split Screen

Two panes -- equal or weighted (60/40, 70/30).
```css
.split {
  display: grid;
  grid-template-columns: 1fr 1fr; /* or 3fr 2fr for weighted */
  min-height: 100dvh;
}
```

## Organic / Anti-Grid

Fluid, natural compositions that break rigid structure -- magazine-style editorial feel.
Deliberately asymmetrical placement, overlapping elements, varied whitespace, free-form content flow.
Use when: portfolio, creative agency, brand storytelling, editorial, fashion, art.
Avoid when: data-heavy, e-commerce catalog, enterprise dashboards.
```css
.organic {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: clamp(1rem, 3vw, 2.5rem);
}
/* Deliberately irregular placement */
.organic__hero   { grid-column: 1 / 8; grid-row: 1 / 3; }
.organic__aside  { grid-column: 9 / 13; grid-row: 1; align-self: end; }
.organic__pull   { grid-column: 3 / 11; margin-top: -4rem; position: relative; z-index: 1; }
.organic__offset { grid-column: 2 / 7; transform: rotate(-1deg); }
```
Key principles:
- Guide the eye through visual weight and flow, not grid lines
- Intentional overlap creates depth and editorial quality
- Vary element sizes dramatically -- one dominant, rest subordinate
- Negative space is the structure -- let content breathe unevenly
- Combine with motion narrative for scroll-driven journey feel

## Editorial Asymmetry

3-column base grid; content spans 2+1 or 1+2 for unequal rhythm.
```css
.editorial {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}
.lead   { grid-column: span 2; }
.aside  { grid-column: span 1; }
```

## Bento Grid

Asymmetric card tiles with varied row/col spans -- dashboard, features, portfolio.
```css
.bento {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 200px;
  gap: 1rem;
}
.bento-lg   { grid-column: span 2; grid-row: span 2; }
.bento-wide { grid-column: span 3; }
```

## Sidebar + Main

Classic two-column: fixed sidebar, fluid content area.
```css
.layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 2rem;
}
@media (max-width: 768px) {
  .layout { grid-template-columns: 1fr; }
}
.aside {
  position: sticky;
  top: var(--header-height, 4rem);
  max-height: calc(100dvh - var(--header-height, 4rem));
  overflow-y: auto;
}
```

## Masonry

Variable-height cards packed into the shortest lane. CSS-native via `display: grid-lanes` (Safari 26; behind a flag in Chrome and Firefox) with a `columns` fallback.
```css
/* Native masonry / grid-lanes (progressive enhancement) */
@supports (display: grid-lanes) {
  .masonry {
    display: grid-lanes;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
  }
}
/* Fallback */
.masonry-fallback {
  columns: 3;
  column-gap: 1.5rem;
}
```

## Centered Narrow (Reading Layout)

Max-width content column, generous margins -- articles, docs, forms.
```css
.narrow {
  max-width: 65ch; /* ~680px at 16px base */
  margin-inline: auto;
  padding-inline: clamp(1rem, 5vw, 2rem);
}
```

## Stacked Sections

Full-width alternating content rows -- marketing landing pages.
```css
.section { padding-block: clamp(4rem, 10vw, 8rem); }
.section:nth-child(even) { background: var(--surface-alt); }
.section__inner {
  max-width: 1200px;
  margin-inline: auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}
.section:nth-child(even) .section__inner { direction: rtl; }
.section:nth-child(even) .section__inner > * { direction: ltr; }
```

## Card Grid with Subgrid Alignment

Auto-fill cards; subgrid aligns internals (title, body, CTA) across rows.
```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}
.card {
  display: grid;
  grid-row: span 3;
  grid-template-rows: subgrid;
}
/* card children: .card__header, .card__body, .card__footer */
```

---

<!-- Section below derived from pbakaus/impeccable (Apache-2.0), snapshot 2026-06-02. -->

# Spatial Design Principles

The patterns above are recipes; the principles below explain how to combine spacing, grid, and hierarchy into a coherent system.

## Spacing Systems

### Use 4pt Base, Not 8pt

8pt systems are too coarse; you'll frequently need 12px (between 8 and 16). Use 4pt for granularity: 4, 8, 12, 16, 24, 32, 48, 64, 96px.

### Name Tokens Semantically

Name by relationship (`--space-sm`, `--space-lg`), not value (`--spacing-8`). Use `gap` instead of margins for sibling spacing; it eliminates margin collapse and cleanup hacks.

### Rhythm Through Contrast

Equal spacing everywhere reads as no rhythm. Group related elements tightly (8-12px between siblings) and separate distinct sections generously (48-96px). Vary spacing within a section rather than repeating one gap. Apply `clamp()` for fluid spacing that breathes on larger screens.

## Grid Systems

### Flexbox for 1D, Grid for 2D

Use Flexbox for one-dimensional layouts: nav bars, button groups, card internals, most component interiors. Use Grid for two-dimensional structure: page layouts, dashboards, and anything where rows *and* columns need coordinated control.

### The Self-Adjusting Grid

Use `repeat(auto-fit, minmax(280px, 1fr))` for responsive grids without breakpoints. Columns are at least 280px, as many as fit per row, leftovers stretch. For complex layouts, use named grid areas (`grid-template-areas`) and redefine them at breakpoints.

## Visual Hierarchy

### The Squint Test

Blur your eyes (or screenshot and blur). Can you still identify:
- The most important element?
- The second most important?
- Clear groupings?

If everything looks the same weight blurred, you have a hierarchy problem.

### Hierarchy Through Multiple Dimensions

Don't rely on size alone. Combine:

| Tool | Strong Hierarchy | Weak Hierarchy |
|------|------------------|----------------|
| **Size** | 3:1 ratio or more | <2:1 ratio |
| **Weight** | Bold vs Regular | Medium vs Regular |
| **Color** | High contrast | Similar tones |
| **Position** | Top/left (primary) | Bottom/right |
| **Space** | Surrounded by white space | Crowded |

**The best hierarchy uses 2-3 dimensions at once**: A heading that's larger, bolder, AND has more space above it.

### Cards Are Not Required

Cards are overused. Spacing and alignment create visual grouping naturally. Use cards only when content is truly distinct and actionable, items need visual comparison in a grid, or content needs clear interaction boundaries. **Never nest cards inside cards.** Use spacing, typography, and subtle dividers for hierarchy within a card.

## Container Queries

Viewport queries are for page layouts. **Container queries are for components**:

```css
.card-container {
  container-type: inline-size;
}

.card {
  display: grid;
  gap: var(--space-md);
}

/* Card layout changes based on its container, not viewport */
@container (min-width: 400px) {
  .card {
    grid-template-columns: 120px 1fr;
  }
}
```

**Why this matters**: A card in a narrow sidebar stays compact, while the same card in a main content area expands automatically, without viewport hacks.

## Optical Adjustments

Text at `margin-left: 0` looks indented due to letterform whitespace; use negative margin (`-0.05em`) to optically align. Geometrically centered icons often look off-center; play icons need to shift right, arrows shift toward their direction.

### Touch Targets vs Visual Size

Buttons can look small but need large touch targets (44px minimum). Use padding or pseudo-elements:

```css
.icon-button {
  width: 24px;  /* Visual size */
  height: 24px;
  position: relative;
}

.icon-button::before {
  content: '';
  position: absolute;
  inset: -10px;  /* Expand tap target to 44px */
}
```

## Depth & Elevation

Create semantic z-index scales (dropdown → sticky → modal-backdrop → modal → toast → tooltip) instead of arbitrary numbers. For shadows, create a consistent elevation scale (sm → md → lg → xl). **Key insight**: Shadows should be subtle. If you can clearly see it, it's probably too strong.

---

**Avoid**: Arbitrary spacing values outside your scale. Making all spacing equal (variety creates hierarchy). Creating hierarchy through size alone; combine size, weight, color, and space. Defaulting to the hero-metric template (big number, small label, stat row, gradient) when there is no real data behind it; a prominent metric only works when it shows actual data.
