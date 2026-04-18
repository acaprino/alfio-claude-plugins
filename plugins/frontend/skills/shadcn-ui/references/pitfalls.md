# Common Pitfalls and Known Issues

Frequently encountered problems when building with shadcn/ui, with solutions.

## 1. Tailwind Class Name Collisions

**Problem**: Custom Tailwind config utilities override shadcn component styling through CSS specificity conflicts.

**Fix**: Namespace custom utilities using Tailwind's variants feature. Audit class name cascades, especially in light/dark mode. Use `cn()` to merge classes predictably.

## 2. SSR Hydration Errors

**Problem**: Components like Accordion cause DOM mismatches when client state differs from server render.

**Fix**:
```tsx
// Option A: Dynamic import with ssr disabled
const Accordion = dynamic(() => import("@/components/ui/accordion"), { ssr: false })

// Option B: Guard with window check
const [mounted, setMounted] = useState(false)
useEffect(() => setMounted(true), [])
if (!mounted) return null
```

## 3. Bundle Bloat from Unused Imports

**Problem**: Wildcard imports (`import * as AllComponents`) defeat tree-shaking.

**Fix**: Always use named imports. Audit bundle size with `@next/bundle-analyzer`:
```tsx
// Bad
import * as UI from "@/components/ui"

// Good
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent } from "@/components/ui/dialog"
```

## 4. Typography Conflicts

**Problem**: Custom `fontSize` overrides in `tailwind.config` conflict with shadcn's CSS-variable-based type scaling.

**Fix**: Set typography scale via CSS variables, not hardcoded Tailwind extend values. Use `@apply` for reusable type classes.

## 5. Accessibility Regressions

**Problem**: shadcn is WAI-ARIA compliant by default, but developers omit required accessible names, ARIA roles, and focus management.

**Fix**:
- Always include `DialogTitle` and `DialogDescription` (even if visually hidden)
- Run Lighthouse + axe-core audits after major changes
- Test keyboard navigation manually
- Verify `aria-label` on icon-only buttons

## 6. No Auto-Updates

**Problem**: Breaking changes in dependencies (e.g., `cmdk`) can break components. Because shadcn copies files into your repo, `npm update` does not fix them.

**Fix**:
- Pin dependency versions in `package.json`
- Subscribe to shadcn changelog
- Re-run `npx shadcn@latest add [component]` to pull updated versions
- Use `shadcn add --diff` (CLI v4) to preview what changes

## 7. Visual Sameness

**Problem**: Apps look identical out of the box -- same colors, same spacing, same feel.

**Fix**:
- Customize CSS variables in `globals.css` before building
- Use `shadcn/create` to choose colors, spacing, fonts, and icons upfront
- Use **frontend** skill for distinctive visual identity
- Consider a custom registry:base to define your design system

## 8. forwardRef Breakage in React 19

**Problem**: All shadcn components updated for React 19 drop `React.forwardRef`. Custom wrappers using the old pattern produce warnings or break.

**Fix**: Migrate custom wrappers to standard function components with `ref` as a prop. See migration-guide.md Step 7.

## 9. Radix UI Dependency

**Problem**: Historical maintenance gap in Radix UI raised concerns about long-term viability.

**Status**: Resolved -- WorkOS actively funds Radix development with dedicated engineers. No action needed.

## 10. "use client" Boundary Placement

**Problem**: Wrapping too much in `"use client"` defeats Server Component benefits. Wrapping too little causes runtime errors.

**Fix**:
- Place `"use client"` as low in the tree as possible
- Interactive components (Dialog, Form, DataTable) need it
- Column definitions need it (they reference React components)
- Layout shells and route segments should remain Server Components
- Data-fetching pages should remain Server Components
