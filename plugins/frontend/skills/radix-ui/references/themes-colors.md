# Radix Themes - Color Reference

Complete color system reference for Radix Themes.

Docs: https://www.radix-ui.com/themes/docs/theme/color

## 12-Step Color Scale

Every color in Radix Themes follows a 12-step scale designed for specific UI purposes:

| Step | Purpose | Use for |
|------|---------|---------|
| 1 | App background | Page backgrounds |
| 2 | Subtle background | Card backgrounds, striped table rows |
| 3 | UI element background | Buttons, checkboxes at rest |
| 4 | Hovered UI element | Buttons, checkboxes on hover |
| 5 | Active/selected UI element | Pressed state, selected option |
| 6 | Subtle borders | Separators, subtle outlines |
| 7 | UI element borders | Input borders, checkbox borders |
| 8 | Hovered borders | Focused inputs, hovered borders |
| 9 | Solid backgrounds | Primary buttons, badges, tags |
| 10 | Hovered solid | Primary button hover |
| 11 | Low-contrast text | Secondary text, descriptions |
| 12 | High-contrast text | Primary text, headings |

## Accent Colors (24)

| Color | Recommended for |
|-------|----------------|
| Gray | Neutral, minimal |
| Gold | Premium, luxury |
| Bronze | Warm, earthy |
| Brown | Organic, natural |
| Yellow | Attention, highlight |
| Amber | Warm accent |
| Orange | Energy, action |
| Tomato | Warm red alternative |
| Red | Error, danger, destructive |
| Ruby | Rich red |
| Crimson | Bold, dramatic |
| Pink | Playful, creative |
| Plum | Rich purple |
| Purple | Premium, creative |
| Violet | Subtle purple |
| Iris | Cool purple |
| Indigo | Professional, trust |
| Blue | Information, links |
| Cyan | Fresh, tech |
| Teal | Calm, balanced |
| Jade | Natural, growth |
| Green | Success, positive |
| Grass | Vibrant green |
| Lime | Fresh, energetic |
| Mint | Cool, clean |
| Sky | Open, light |

## Gray Colors (6)

| Gray | Undertone | Auto-paired with |
|------|-----------|------------------|
| Gray | Pure neutral | Gray accent |
| Mauve | Slight purple | Tomato, Red, Ruby, Crimson, Pink, Plum, Purple, Violet |
| Slate | Slight blue | Iris, Indigo, Blue, Sky, Cyan |
| Sage | Slight green | Mint, Teal, Jade, Green, Grass |
| Olive | Slight yellow-green | Lime |
| Sand | Slight yellow | Yellow, Amber, Orange, Brown, Gold, Bronze |

## CSS Variable Patterns

### Accent scale

```css
var(--accent-1)   /* lightest background */
var(--accent-2)   /* subtle background */
var(--accent-3)   /* UI background */
var(--accent-4)   /* hovered UI */
var(--accent-5)   /* active UI */
var(--accent-6)   /* subtle border */
var(--accent-7)   /* UI border */
var(--accent-8)   /* hovered border */
var(--accent-9)   /* solid background */
var(--accent-10)  /* hovered solid */
var(--accent-11)  /* low-contrast text */
var(--accent-12)  /* high-contrast text */
```

### Alpha variants (translucent)

```css
var(--accent-a1) through var(--accent-a12)
```

Alpha colors are designed to look consistent when overlaid on any background.

### Gray scale

```css
var(--gray-1) through var(--gray-12)
var(--gray-a1) through var(--gray-a12)  /* alpha */
```

### Individual color scales

Access any color directly, regardless of theme accent:

```css
var(--red-1) through var(--red-12)
var(--blue-1) through var(--blue-12)
var(--green-1) through var(--green-12)
/* etc. for all 24 colors */
```

### Functional tokens

```css
/* Accent functional */
var(--accent-surface)     /* translucent accent for surfaces */
var(--accent-indicator)   /* selection indicators */
var(--accent-track)       /* slider/progress tracks */
var(--accent-contrast)    /* guaranteed readable on accent-9 */

/* Focus */
var(--focus-1) through var(--focus-12)
var(--focus-a1) through var(--focus-a12)

/* Page-level */
var(--color-background)        /* page background */
var(--color-panel-solid)       /* opaque panel */
var(--color-panel-translucent) /* translucent panel */
var(--color-surface)           /* elevated surface */
var(--color-overlay)           /* modal overlay */
```

## Usage Examples

### Custom styled component

```css
.custom-card {
  background: var(--accent-2);
  border: 1px solid var(--accent-6);
  color: var(--accent-12);
}

.custom-card:hover {
  background: var(--accent-3);
  border-color: var(--accent-7);
}
```

### Status colors outside Radix components

```css
.status-badge {
  background: var(--green-3);
  color: var(--green-11);
  border: 1px solid var(--green-6);
}

.error-message {
  color: var(--red-11);
  background: var(--red-2);
}
```

### Dark mode

Radix Themes handles dark mode automatically via the `appearance` prop on `<Theme>`. All 12-step scales adjust for dark backgrounds. No manual dark mode classes needed.

```tsx
<Theme appearance="dark">   {/* force dark */}
<Theme appearance="light">  {/* force light */}
<Theme appearance="inherit"> {/* follow system preference */}
```

## Customization

### Override accent with CSS

```css
.radix-themes {
  --accent-1: oklch(99% 0.005 250);
  --accent-2: oklch(97% 0.01 250);
  /* ... all 12 steps */
  --accent-9: oklch(55% 0.25 250);
  --accent-10: oklch(50% 0.25 250);
  --accent-11: oklch(40% 0.15 250);
  --accent-12: oklch(20% 0.05 250);
}
```

### Per-component color

```tsx
<Button color="red">Delete</Button>
<Badge color="green" highContrast>Active</Badge>
<Avatar color="purple" fallback="A" />
```

### Reduce bundle with individual imports

```css
/* Instead of importing all colors */
@import "@radix-ui/themes/styles.css";

/* Import only what you need */
@import "@radix-ui/themes/tokens/base.css";
@import "@radix-ui/themes/tokens/colors/indigo.css";
@import "@radix-ui/themes/tokens/colors/red.css";
@import "@radix-ui/themes/tokens/colors/green.css";
```
