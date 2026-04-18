---
name: shadcn-ui
description: >
  Expert guidance for building with shadcn/ui -- component composition, registry system, form patterns, data tables, sidebar navigation, theming, and Tailwind v4 migration. Trigger when working with shadcn/ui components, adding shadcn to a project, composing complex UI from shadcn primitives, or customizing shadcn themes. Also trigger on mentions of "shadcn", "shadcn/ui", "shadcn components", "shadcn registry", or "shadcn blocks".
  TRIGGER WHEN: working with shadcn/ui components, adding shadcn to a project, composing complex UI from shadcn primitives, or customizing shadcn themes
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# shadcn/ui Expert

Guidance for building production UIs with shadcn/ui. Covers component composition, advanced patterns, registry authoring, theming, and integration with the broader frontend ecosystem.

Docs: https://ui.shadcn.com/docs

## Core Philosophy

shadcn/ui is NOT a component library -- it is a collection of beautifully designed, accessible components you copy into your project and own. Five pillars:

1. **Open Code** - components live in your codebase, fully editable
2. **Composition** - small primitives combine into complex UI
3. **Distribution** - registry system for sharing component sets
4. **Beautiful Defaults** - production-ready out of the box
5. **AI-Ready** - `data-slot` attributes and structured props for LLM tooling

## When This Skill Activates

- Adding shadcn/ui to a project (`npx shadcn@latest init`)
- Installing or customizing individual components (`npx shadcn@latest add`)
- Building complex patterns: data tables, forms with validation, sidebar navigation
- Theming, color system customization, dark mode
- Creating or consuming a custom registry
- Migrating from Tailwind v3 to v4 with shadcn

## Synergy with Other Frontend Skills

This skill works alongside the other frontend skills. Route to them when appropriate:

| Need | Route to |
|------|----------|
| CSS architecture, modern CSS features, responsive patterns | **web-designer** |
| Page layout composition, grid systems, breakpoint strategy | **ui-layout-designer** agent |
| Animations, micro-interactions, visual polish | **web-designer** agent |
| UX flows, design tokens, component hierarchy | **web-designer** agent |
| Distinctive visual identity, avoiding generic AI aesthetics | **frontend** skill |
| React 19 patterns, Server Components, performance | **react-performance-optimizer** agent |

**This skill** handles shadcn-specific concerns: which components to use, how to compose them, registry patterns, form/table/sidebar architecture, and shadcn theming.

## Live Component Lookup

This skill contains reference patterns for the most complex components (Data Table, Form, Sidebar, Dialog). For any other component's API, props, or usage -- spawn a **quick-searcher** agent to fetch the docs in real time.

### URL patterns

All component docs follow a predictable URL scheme:

| Resource | URL pattern |
|----------|-------------|
| Component docs | `https://ui.shadcn.com/docs/components/{name}` |
| Form integrations | `https://ui.shadcn.com/docs/forms/{library}` |
| Blocks | `https://ui.shadcn.com/blocks` |
| Registry | `https://ui.shadcn.com/docs/registry` |
| Themes | `https://ui.shadcn.com/themes` |
| CLI reference | `https://ui.shadcn.com/docs/cli` |
| Tailwind v4 | `https://ui.shadcn.com/docs/tailwind-v4` |
| Changelog | `https://ui.shadcn.com/docs/changelog` |

### How to look up a component

When you need API details for a specific component (e.g., Combobox, Toast, Sheet):

1. Spawn a **research:quick-searcher** agent with this prompt template:
   ```
   Fetch https://ui.shadcn.com/docs/components/{component-name} and extract:
   - Sub-components and their props
   - Required accessibility attributes
   - Install command
   - Key usage patterns and code examples
   Return structured findings.
   ```

2. For Radix primitive API details (inherited by shadcn), fetch:
   `https://www.radix-ui.com/primitives/docs/components/{component-name}`

3. For TanStack Table API (used by Data Table), fetch:
   `https://tanstack.com/table/latest/docs/introduction`

### Component catalog (by category)

For quick reference when choosing components:

| Category | Components |
|----------|------------|
| Layout | Sidebar, Resizable, Collapsible, Separator, Aspect Ratio |
| Overlay | Dialog, Sheet, Drawer, Alert Dialog, Popover, Tooltip, Hover Card |
| Form | Input, Textarea, Select, Checkbox, Radio Group, Switch, Slider, Toggle, Toggle Group, Date Picker, Combobox |
| Data Display | Table, Data Table, Card, Badge, Avatar, Calendar |
| Feedback | Alert, Toast (Sonner), Progress, Skeleton |
| Navigation | Navigation Menu, Breadcrumb, Pagination, Tabs, Command, Menubar, Dropdown Menu, Context Menu |
| Typography | Label, Separator |

## Installation and Setup

### New project

```bash
npx shadcn@latest init
# Choose: New York style (default, "default" style is deprecated)
# Choose: Tailwind v4 + React 19 (current default)
```

### Add components

```bash
npx shadcn@latest add button dialog form sidebar data-table
# Or add a block:
npx shadcn@latest add dashboard-01
```

### CLI v4 features (March 2026+)

```bash
shadcn add --dry-run dialog    # preview changes without writing
shadcn add --diff dialog       # show diff of what would change
shadcn info                    # show installed components, framework, CSS vars
shadcn docs dialog             # fetch component docs from CLI
shadcn init --template next    # scaffold with framework template
```

## Component Composition

shadcn components are composable primitives. Build complex UI by nesting them.

### Pattern: Sub-component composition

```tsx
<Dialog>
  <DialogTrigger asChild>
    <Button variant="outline">Edit Profile</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Edit Profile</DialogTitle>
      <DialogDescription>Update your information.</DialogDescription>
    </DialogHeader>
    {/* your content */}
  </DialogContent>
</Dialog>
```

### Pattern: Slot/asChild delegation

Use `asChild` to delegate rendering to a child element -- avoids extra DOM nodes and lets you use router Links, custom buttons, etc.

```tsx
<DialogTrigger asChild>
  <Link href="/settings">Open Settings</Link>
</DialogTrigger>
```

### Pattern: cn() utility for conditional classes

```tsx
import { cn } from "@/lib/utils"

<div className={cn(
  "rounded-lg border p-4",
  isActive && "border-primary bg-primary/5",
  className
)} />
```

### Pattern: CVA variants for custom components

```tsx
import { cva, type VariantProps } from "class-variance-authority"

const badgeVariants = cva("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs", {
  variants: {
    variant: {
      default: "bg-primary text-primary-foreground",
      destructive: "bg-destructive text-destructive-foreground",
      outline: "border text-foreground",
    },
  },
  defaultVariants: { variant: "default" },
})
```

## Key Patterns

### Data Table

3-file architecture with TanStack Table. See [references/advanced-patterns.md](references/advanced-patterns.md) for full column definition, sorting, filtering, pagination, and row selection patterns.

- `columns.tsx` - column definitions (`ColumnDef<TData>[]`)
- `data-table.tsx` - table wrapper with `useReactTable`
- `page.tsx` - server component for data fetching

### Form + Zod Validation

React Hook Form + Zod resolver. See [references/advanced-patterns.md](references/advanced-patterns.md) for field patterns, dynamic arrays, and validation modes.

```tsx
const form = useForm<z.infer<typeof schema>>({
  resolver: zodResolver(schema),
  defaultValues: { title: "" }
})
```

### Sidebar Navigation

Provider-based with `SidebarProvider`. Supports `collapsible="icon"` and `collapsible="offcanvas"`. See [references/advanced-patterns.md](references/advanced-patterns.md) for nested navigation, mobile responsive, and `useSidebar()` hook.

## Theming

### Color system (Tailwind v4 / OKLCH)

New projects use OKLCH for perceptual color uniformity. Colors defined as CSS variables in `globals.css`:

```css
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  /* ... */
}
```

### Dark mode

Toggle via class on `<html>`. All shadcn components respect `dark:` variants automatically.

### Customization approach

1. Edit CSS variables in `globals.css` for global theme changes
2. Use `cn()` for per-instance overrides
3. Edit the component source directly for structural changes (you own the code)
4. Use `data-slot` attributes for targeted CSS overrides without class specificity fights

## Tailwind v4 Migration

See [references/migration-guide.md](references/migration-guide.md) for the step-by-step migration from Tailwind v3 to v4, including:

- `npx @tailwindcss/upgrade@next` codemod
- Animation library swap (`tailwindcss-animate` to `tw-animate-css`)
- CSS variable restructuring with `@theme inline`
- `forwardRef` removal for React 19
- `data-slot` adoption

## Registry System

Build and distribute your own component sets. See [references/registry-guide.md](references/registry-guide.md) for:

- `registry.json` schema and item types
- Directory structure conventions
- Build and publish workflow
- `registry:base` for full design systems

## Common Pitfalls

See [references/pitfalls.md](references/pitfalls.md) for detailed problems and fixes:

- Tailwind class collisions with custom config
- SSR hydration errors (Accordion, etc.)
- Bundle bloat from wildcard imports
- No auto-updates -- manual `shadcn add` to refresh components
- `forwardRef` breakage in React 19
- Accessibility regressions from missing ARIA attributes

## Community Resources

- **Blocks**: https://ui.shadcn.com/blocks -- official composable page sections
- **shadcnblocks.com** -- 1100+ community blocks and templates
- **registry.directory** -- third-party registry explorer
- **shadcn-admin** (GitHub, 6k+ stars) -- full admin dashboard starter
- **next-forge** (GitHub, 6.9k+ stars) -- Turborepo monorepo with payments, analytics, i18n

## Server vs Client Components

- Data-fetching pages: Server Components (default in Next.js App Router)
- Interactive components (Dialog, Form, DataTable): `"use client"`
- Column definitions: `"use client"` (they reference React components)
- Prefer Server Components for layout shells, route segments
- Use `"use client"` boundary as low in the tree as possible
