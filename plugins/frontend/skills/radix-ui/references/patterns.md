# Radix UI Patterns and Best Practices

## Composition Patterns

### 1. Custom trigger with asChild

Route Radix behavior onto your design system button:

```tsx
import * as Dialog from "radix-ui/components/dialog"
import { Button } from "@/components/ui/button"

<Dialog.Trigger asChild>
  <Button variant="primary">Edit Profile</Button>
</Dialog.Trigger>
```

**Requirements for custom components:**

```tsx
// Must spread props AND forward ref
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, variant, ...props }, ref) => (
    <button ref={ref} {...props} className={`btn btn-${variant}`}>
      {children}
    </button>
  )
)
Button.displayName = "Button"
```

### 2. Composing multiple primitives

Combine tooltip + dialog on a single button:

```tsx
<Tooltip.Root>
  <Tooltip.Trigger asChild>
    <Dialog.Trigger asChild>
      <IconButton aria-label="Edit user">
        <PencilIcon />
      </IconButton>
    </Dialog.Trigger>
  </Tooltip.Trigger>
  <Tooltip.Portal>
    <Tooltip.Content>Edit user</Tooltip.Content>
  </Tooltip.Portal>
</Tooltip.Root>
```

### 3. Nested color override (Themes)

```tsx
<Card>
  <Heading>Account</Heading>
  <Button color="red">
    <AlertDialog.Trigger>Delete Account</AlertDialog.Trigger>
  </Button>
  {/* Nested components inherit red accent */}
</Card>
```

---

## Animation Patterns

### CSS animation (recommended)

```css
/* Enter animation */
.DialogOverlay[data-state="open"] {
  animation: overlayShow 150ms cubic-bezier(0.16, 1, 0.3, 1);
}
.DialogContent[data-state="open"] {
  animation: contentShow 150ms cubic-bezier(0.16, 1, 0.3, 1);
}

/* Exit animation - Radix waits for this to finish before unmounting */
.DialogOverlay[data-state="closed"] {
  animation: overlayHide 100ms ease-in;
}
.DialogContent[data-state="closed"] {
  animation: contentHide 100ms ease-in;
}

@keyframes overlayShow {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes overlayHide {
  from { opacity: 1; }
  to { opacity: 0; }
}
@keyframes contentShow {
  from {
    opacity: 0;
    transform: translate(-50%, -48%) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}
@keyframes contentHide {
  from {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -48%) scale(0.96);
  }
}
```

### Tailwind animation with data attributes

```tsx
<Dialog.Overlay className="
  fixed inset-0 bg-black/50
  data-[state=open]:animate-in data-[state=open]:fade-in-0
  data-[state=closed]:animate-out data-[state=closed]:fade-out-0
" />

<Dialog.Content className="
  fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2
  data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95
  data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95
" />
```

### Accordion height animation

```css
.AccordionContent {
  overflow: hidden;
}
.AccordionContent[data-state="open"] {
  animation: slideDown 300ms ease-out;
}
.AccordionContent[data-state="closed"] {
  animation: slideUp 300ms ease-in;
}

@keyframes slideDown {
  from { height: 0; }
  to { height: var(--radix-accordion-content-height); }
}
@keyframes slideUp {
  from { height: var(--radix-accordion-content-height); }
  to { height: 0; }
}
```

### Framer Motion integration

```tsx
import { AnimatePresence, motion } from "framer-motion"

function AnimatedDialog({ open, onOpenChange, children }) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <AnimatePresence>
        {open && (
          <Dialog.Portal forceMount>
            <Dialog.Overlay asChild forceMount>
              <motion.div
                className="fixed inset-0 bg-black/50"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              />
            </Dialog.Overlay>
            <Dialog.Content asChild forceMount>
              <motion.div
                className="dialog-content"
                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 10 }}
                transition={{ duration: 0.2 }}
              >
                {children}
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  )
}
```

---

## Common Patterns

### Responsive dialog (dialog on desktop, drawer on mobile)

```tsx
function ResponsiveDialog({ children, ...props }) {
  const isMobile = useMediaQuery("(max-width: 768px)")

  if (isMobile) {
    return (
      <Drawer.Root {...props}>
        <Drawer.Portal>
          <Drawer.Overlay className="fixed inset-0 bg-black/40" />
          <Drawer.Content className="fixed bottom-0 left-0 right-0 rounded-t-xl bg-white p-4">
            {children}
          </Drawer.Content>
        </Drawer.Portal>
      </Drawer.Root>
    )
  }

  return (
    <Dialog.Root {...props}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="dialog-center bg-white rounded-lg p-6 max-w-md">
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

### Command menu (cmdk + Dialog)

```tsx
import { Command } from "cmdk"

<Dialog.Root>
  <Dialog.Portal>
    <Dialog.Overlay />
    <Dialog.Content>
      <Command>
        <Command.Input placeholder="Type a command..." />
        <Command.List>
          <Command.Empty>No results</Command.Empty>
          <Command.Group heading="Actions">
            <Command.Item>New File</Command.Item>
            <Command.Item>Search</Command.Item>
          </Command.Group>
        </Command.List>
      </Command>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
```

### Multi-step dialog

```tsx
function MultiStepDialog() {
  const [step, setStep] = useState(1)

  return (
    <Dialog.Root>
      <Dialog.Portal>
        <Dialog.Overlay />
        <Dialog.Content>
          <Dialog.Title>
            {step === 1 ? "Choose plan" : step === 2 ? "Payment" : "Confirm"}
          </Dialog.Title>
          {step === 1 && <PlanSelector onNext={() => setStep(2)} />}
          {step === 2 && <PaymentForm onNext={() => setStep(3)} onBack={() => setStep(1)} />}
          {step === 3 && <Confirmation onBack={() => setStep(2)} />}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

---

## Common Pitfalls

### 1. Missing Title in Dialog

**Problem:** Screen readers cannot announce the dialog purpose.

**Fix:** Always include `Dialog.Title`. Use `VisuallyHidden` if the title shouldn't be visible:

```tsx
<Dialog.Content>
  <VisuallyHidden>
    <Dialog.Title>Settings</Dialog.Title>
  </VisuallyHidden>
  {/* visible content */}
</Dialog.Content>
```

### 2. Event handler conflicts with asChild

**Problem:** Custom component's `onClick` conflicts with Radix's internal handler.

**Fix:** Radix merges handlers automatically when using `asChild`. Your handler runs alongside Radix's. If you need to prevent Radix behavior, call `event.preventDefault()`.

### 3. Portal breaks styling context

**Problem:** Portaled content loses CSS context (CSS variables, theme classes).

**Fix:** Radix portals to `document.body` by default. Ensure your theme provider/CSS variables are on `:root` or `body`. For scoped themes, pass a custom `container` to Portal.

### 4. forceMount confusion

**Problem:** Using `forceMount` without a JS animation library leaves content permanently visible.

**Fix:** Only use `forceMount` when you control visibility via a JS animation library (Framer Motion, React Spring). For CSS animations, let Radix handle mount/unmount.

### 5. Select in forms not submitting

**Problem:** Radix Select doesn't render a native `<select>` element.

**Fix:** Radix Select renders a hidden `<input>` with the selected value when `name` is provided. Ensure you pass `name` to `Select.Root`:

```tsx
<Select.Root name="country" defaultValue="us">
```

### 6. Tooltip not showing for disabled buttons

**Problem:** Disabled buttons don't fire mouse events.

**Fix:** Wrap the disabled button in a span:

```tsx
<Tooltip.Trigger asChild>
  <span tabIndex={0}>
    <Button disabled>Disabled action</Button>
  </span>
</Tooltip.Trigger>
```

### 7. z-index stacking issues

**Problem:** Overlapping dialogs, popovers, or tooltips layer incorrectly.

**Fix:** Radix handles stacking automatically within its own components. If mixing with non-Radix overlays, set `z-index` on the Portal content. Radix creates new stacking contexts properly.

### 8. SSR hydration mismatch

**Problem:** Portal renders differently on server vs client.

**Fix:** Radix portals only activate on the client. For SSR frameworks (Next.js), this is handled automatically. If you see hydration warnings, ensure you're not conditionally rendering Radix components based on server-only state.

---

## Accessibility Checklist

- [ ] `Dialog.Title` present (use `VisuallyHidden` wrapper if hidden)
- [ ] `Dialog.Description` present when applicable
- [ ] `aria-label` on icon-only buttons/triggers
- [ ] Test `Tab` key navigation through all interactive elements
- [ ] Test `Esc` key closes dialogs/menus/popovers
- [ ] Test `Arrow` keys in menus, tabs, radio groups
- [ ] Test `Enter`/`Space` activates buttons and triggers
- [ ] Test screen reader announces dialog title on open
- [ ] Focus returns to trigger after dialog closes
- [ ] Dropdown items accessible via typeahead (type first letter)
