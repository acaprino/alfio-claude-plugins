---
name: radix-ui
description: >
  Expert guidance for building with Radix UI -- Primitives (unstyled accessible components)
  and Themes (pre-styled design system). Covers composition patterns, asChild prop,
  accessibility, animation, theming, color system, and keyboard navigation.
  Trigger when working with Radix components, @radix-ui packages, or building accessible
  UI primitives. Also trigger on mentions of "radix", "radix-ui", "radix primitives",
  "radix themes", "@radix-ui/react-*", or the unified "radix-ui" package.
---

# Radix UI Expert

Guidance for building accessible, composable UIs with Radix UI. Covers both Primitives (unstyled, headless) and Themes (pre-styled design system).

Docs: https://www.radix-ui.com

## Two Products

| Product | What it is | Install | Use when |
|---------|-----------|---------|----------|
| **Primitives** | Unstyled, accessible component primitives | `npm i radix-ui` | Building custom design systems, need full style control |
| **Themes** | Pre-styled component library built on Primitives | `npm i @radix-ui/themes` | Want production-ready styled components out of the box |

**shadcn/ui** is built on top of Radix Primitives. If working with shadcn, route to the **shadcn-ui** skill instead.

## When This Skill Activates

- Installing or using `radix-ui` or `@radix-ui/react-*` packages
- Building accessible components (dialog, popover, dropdown, accordion)
- Using `asChild` prop for composition
- Animating Radix components (enter/exit transitions)
- Configuring Radix Themes (colors, radius, scaling)
- Questions about WAI-ARIA patterns, keyboard navigation, focus management

## Synergy with Other Frontend Skills

| Need | Route to |
|------|----------|
| shadcn/ui components (Radix + Tailwind, pre-composed) | **shadcn-ui** |
| CSS architecture, modern CSS features | **css-master** |
| Page layout composition, grid systems | **ui-layout-designer** agent |
| Animations, micro-interactions, visual polish | **ui-polisher** agent |
| Distinctive visual identity | **frontend-design** |
| daisyUI components (different library, class-based) | **daisyui** |

## Live Component Lookup

This skill covers architecture, composition patterns, and the most common components. For any specific component's full API -- spawn a **quick-searcher** agent.

### URL patterns

| Resource | URL pattern |
|----------|-------------|
| Primitives component | `https://www.radix-ui.com/primitives/docs/components/{name}` |
| Primitives guides | `https://www.radix-ui.com/primitives/docs/guides/{topic}` |
| Themes component | `https://www.radix-ui.com/themes/docs/components/{name}` |
| Themes overview | `https://www.radix-ui.com/themes/docs/overview/{topic}` |
| Themes theming | `https://www.radix-ui.com/themes/docs/theme/{topic}` |
| Colors reference | `https://www.radix-ui.com/colors` |

---

# Radix Primitives

## Core Philosophy

Radix Primitives are **unstyled, accessible** UI components. They handle the hard parts (WAI-ARIA compliance, keyboard navigation, focus management, screen reader support) while you own all styling. Three key principles:

1. **Unstyled** - zero CSS shipped, style with anything (Tailwind, CSS Modules, styled-components)
2. **Accessible** - WAI-ARIA design patterns, full keyboard navigation, screen reader tested
3. **Composable** - granular sub-components, `asChild` for element delegation, controlled/uncontrolled

## Installation

```bash
# Unified package (recommended, tree-shakeable)
npm install radix-ui

# Or individual packages
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
```

## Component Catalog (Primitives)

See [references/primitives-components.md](references/primitives-components.md) for detailed sub-component APIs.

| Category | Components |
|----------|------------|
| Overlay | Dialog, Alert Dialog, Popover, Hover Card, Tooltip |
| Menu | Dropdown Menu, Context Menu, Menubar |
| Navigation | Navigation Menu, Tabs |
| Form | Checkbox, Radio Group, Select, Slider, Switch, Toggle, Toggle Group, Form |
| Disclosure | Accordion, Collapsible |
| Media | Avatar, Aspect Ratio, Progress |
| Layout | Scroll Area, Separator, Toolbar |
| Utility | Label, Portal, Slot, Visually Hidden, Direction Provider |
| Deprecated | Toast (use Sonner instead) |

## Composition Model

### Sub-component architecture

Every Radix component is split into named parts that you compose:

```tsx
import * as Dialog from "radix-ui/components/dialog"

<Dialog.Root>
  <Dialog.Trigger>Open</Dialog.Trigger>
  <Dialog.Portal>
    <Dialog.Overlay className="fixed inset-0 bg-black/50" />
    <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg">
      <Dialog.Title>Edit Profile</Dialog.Title>
      <Dialog.Description>Make changes to your profile.</Dialog.Description>
      {/* form content */}
      <Dialog.Close className="absolute right-4 top-4">X</Dialog.Close>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
```

### asChild prop

The `asChild` prop delegates rendering to the child element, merging Radix behavior onto your own component:

```tsx
// Default: Radix renders a <button>
<Dialog.Trigger>Open</Dialog.Trigger>

// asChild: Radix merges onto YOUR element
<Dialog.Trigger asChild>
  <Link href="/settings">Open Settings</Link>
</Dialog.Trigger>
```

Requirements for custom components with `asChild`:
1. **Spread all props** onto the DOM element
2. **Forward ref** using `React.forwardRef` (or ref prop in React 19)

```tsx
const MyButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, ...props }, ref) => (
    <button ref={ref} {...props} className="my-button">
      {children}
    </button>
  )
)

<Dialog.Trigger asChild>
  <MyButton>Open</MyButton>
</Dialog.Trigger>
```

### Composing multiple primitives

`asChild` nests to combine behaviors:

```tsx
<Tooltip.Trigger asChild>
  <Dialog.Trigger asChild>
    <MyButton>Edit</MyButton>
  </Dialog.Trigger>
</Tooltip.Trigger>
```

### Controlled vs uncontrolled

All stateful components support both patterns:

```tsx
// Uncontrolled (default) - component manages its own state
<Accordion.Root type="single" defaultValue="item-1">

// Controlled - you manage state
const [value, setValue] = useState("item-1")
<Accordion.Root type="single" value={value} onValueChange={setValue}>
```

## Data Attributes

Radix exposes state via `data-*` attributes for CSS styling:

| Attribute | Values | Used for |
|-----------|--------|----------|
| `[data-state]` | `"open"` / `"closed"` | Overlays, disclosure |
| `[data-state]` | `"checked"` / `"unchecked"` / `"indeterminate"` | Checkboxes, switches |
| `[data-state]` | `"active"` / `"inactive"` | Tabs, toggles |
| `[data-disabled]` | present/absent | Disabled elements |
| `[data-orientation]` | `"vertical"` / `"horizontal"` | Accordion, tabs, separator |
| `[data-highlighted]` | present/absent | Menu items (keyboard focus) |
| `[data-side]` | `"top"` / `"right"` / `"bottom"` / `"left"` | Positioned content |
| `[data-align]` | `"start"` / `"center"` / `"end"` | Positioned content |

### Styling with data attributes

```css
/* Tailwind */
<Accordion.Content className="data-[state=open]:animate-slideDown data-[state=closed]:animate-slideUp">

/* Plain CSS */
.AccordionContent[data-state="open"] {
  animation: slideDown 300ms ease-out;
}
.AccordionContent[data-state="closed"] {
  animation: slideUp 300ms ease-in;
}
```

## Animation Patterns

See [references/patterns.md](references/patterns.md) for detailed animation patterns.

### CSS animations (recommended)

Radix suspends unmounting during CSS animations, enabling exit animations:

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

.DialogOverlay[data-state="open"] { animation: fadeIn 200ms ease-out; }
.DialogOverlay[data-state="closed"] { animation: fadeOut 200ms ease-in; }
```

### CSS variables for dynamic sizing

Accordion and Collapsible expose size variables for smooth height animation:

```css
.AccordionContent[data-state="open"] {
  animation: slideDown 300ms ease-out;
}
@keyframes slideDown {
  from { height: 0; }
  to { height: var(--radix-accordion-content-height); }
}
```

### JavaScript animation libraries

Use `forceMount` to prevent Radix from unmounting content, letting your library control the exit:

```tsx
<Dialog.Portal forceMount>
  <AnimatePresence>
    {open && (
      <Dialog.Content forceMount asChild>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          Content
        </motion.div>
      </Dialog.Content>
    )}
  </AnimatePresence>
</Dialog.Portal>
```

## Keyboard Navigation

All Radix components implement WAI-ARIA keyboard patterns:

| Component | Keys |
|-----------|------|
| Dialog | `Esc` close, `Tab` trap focus |
| Dropdown Menu | `Arrow` navigate, `Enter`/`Space` select, `Esc` close |
| Accordion | `Arrow` navigate triggers, `Enter`/`Space` toggle, `Home`/`End` |
| Tabs | `Arrow` switch tabs, `Tab` move to panel |
| Select | `Arrow` navigate, `Enter`/`Space` select |
| Slider | `Arrow` adjust, `Home`/`End` min/max |
| Radio Group | `Arrow` navigate, `Space` select |

## Accessibility Guarantees

Radix handles automatically:
- ARIA attributes (`role`, `aria-expanded`, `aria-controls`, `aria-labelledby`)
- Focus management (trap in dialogs, restore on close)
- Screen reader announcements
- Keyboard interaction patterns per WAI-ARIA spec
- RTL support via `dir` prop / `DirectionProvider`

What you must provide:
- `Title` and `Description` for dialogs/alert dialogs (or use `VisuallyHidden`)
- `aria-label` for icon-only triggers
- Meaningful content for screen readers
- Logical tab order in your layout

---

# Radix Themes

## Overview

Pre-styled component library with built-in theming. Uses Radix Primitives internally but ships with styles, a color system, and layout primitives.

## Installation

```bash
npm install @radix-ui/themes
```

```tsx
// app/layout.tsx or main entry
import "@radix-ui/themes/styles.css"
import { Theme } from "@radix-ui/themes"

export default function Layout({ children }) {
  return (
    <Theme accentColor="indigo" grayColor="slate" radius="medium" scaling="100%">
      {children}
    </Theme>
  )
}
```

## Theme Configuration

```tsx
<Theme
  accentColor="crimson"       // brand color (24 options)
  grayColor="sand"            // neutral tones (6 options)
  radius="large"              // border radius (none | small | medium | large | full)
  scaling="95%"               // global size scale
  appearance="dark"           // light | dark | inherit
  panelBackground="translucent" // solid | translucent
>
```

### ThemePanel (development)

```tsx
import { ThemePanel } from "@radix-ui/themes"
<ThemePanel />  // interactive UI for previewing theme changes
```

## Color System

See [references/themes-colors.md](references/themes-colors.md) for the full color reference.

### 12-step scales

Each color has 12 steps from subtle backgrounds to high-contrast text:

| Steps | Purpose | Example variable |
|-------|---------|-----------------|
| 1-2 | Backgrounds | `var(--accent-1)`, `var(--accent-2)` |
| 3-5 | Interactive states | `var(--accent-3)` hover, `var(--accent-4)` active |
| 6-8 | Borders | `var(--accent-6)` subtle, `var(--accent-8)` strong |
| 9-10 | Solid fills | `var(--accent-9)` primary, `var(--accent-10)` hover |
| 11-12 | Text | `var(--accent-11)` low contrast, `var(--accent-12)` high |

### Accent colors (24)

Gray, Gold, Bronze, Brown, Yellow, Amber, Orange, Tomato, Red, Ruby, Crimson, Pink, Plum, Purple, Violet, Iris, Indigo, Blue, Cyan, Teal, Jade, Green, Grass, Lime, Mint, Sky.

### Gray colors (6)

Gray, Mauve, Slate, Sage, Olive, Sand. Auto-paired with accent but overridable.

### Special tokens

- `var(--accent-surface)` - translucent accent for surface backgrounds
- `var(--accent-indicator)` - for selection indicators
- `var(--accent-track)` - for slider/progress tracks
- `var(--accent-contrast)` - guaranteed readable text on accent-9
- `var(--color-background)` - page background
- `var(--color-overlay)` - overlay/backdrop

### Per-component color override

```tsx
<Button color="red">Delete</Button>  // overrides theme accent for this button
<Badge color="green" highContrast>Active</Badge>
```

## Themes Component Catalog

| Category | Components |
|----------|------------|
| Layout | Box, Flex, Grid, Section, Container |
| Typography | Text, Heading, Code, Quote, Em, Strong, Kbd |
| Form | Button, IconButton, TextField, TextArea, Select, Checkbox, Radio Group, Switch, Slider, SegmentedControl |
| Overlay | Dialog, Alert Dialog, Popover, Hover Card, Tooltip, Context Menu, Dropdown Menu |
| Data Display | Table, Avatar, Badge, Callout, Card, Data List, Inset, Separator, Skeleton |
| Feedback | Progress, Spinner |
| Navigation | Tabs, Tab Nav, Link |

### Common props pattern

Most Themes components share:

```tsx
<Button
  size="1" | "2" | "3" | "4"           // numeric scale
  variant="solid" | "soft" | "outline" | "ghost" | "surface"
  color="indigo"                         // override accent
  highContrast={true}                    // enhanced visibility
  radius="full"                          // override theme radius
  loading={true}                         // loading state
  asChild                                // compose onto child
/>
```

## Best Practices

See [references/patterns.md](references/patterns.md) for detailed patterns.

1. **Always include Title + Description** in Dialog/AlertDialog (use `VisuallyHidden` if not visible)
2. **Use `asChild` for routing** -- compose Trigger onto `<Link>` or router components
3. **Prefer CSS animations** over JS libraries for Radix transitions (simpler, no `forceMount` needed)
4. **Use data attributes for styling** -- `[data-state]`, `[data-highlighted]` are stable API
5. **Don't skip sub-components** -- `Dialog.Overlay`, `Dialog.Portal` exist for a reason
6. **Controlled only when needed** -- uncontrolled (default) reduces boilerplate
7. **Forward refs** in custom components used with `asChild`
8. **Use Portal** for overlays -- prevents z-index and overflow issues
9. **Test keyboard navigation** -- Radix handles it, but verify in your layout context
10. **Use Themes for rapid prototyping**, Primitives for custom design systems
