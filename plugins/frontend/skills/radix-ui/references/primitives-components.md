# Radix Primitives - Component Reference

Detailed sub-component APIs for all Radix Primitives. Each component lists its parts, key props, data attributes, and keyboard interactions.

Docs: https://www.radix-ui.com/primitives/docs/components/

## Common patterns across all components

- **`asChild`** (boolean) - available on every part; renders as child element instead of default
- **`forceMount`** (boolean) - available on content/overlay parts; prevents unmount for JS animations
- **Data attributes** - `[data-state]`, `[data-disabled]`, `[data-orientation]` on relevant parts
- **Controlled/Uncontrolled** - `value`/`onValueChange` (controlled) or `defaultValue` (uncontrolled)

---

## Overlay Components

### Dialog

Sub-components: `Root`, `Trigger`, `Portal`, `Overlay`, `Content`, `Close`, `Title`, `Description`

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `defaultOpen` | boolean | Initial open state |
| `open` | boolean | Controlled open state |
| `onOpenChange` | `(open: boolean) => void` | State change callback |
| `modal` | boolean (default: true) | Modal vs non-modal |

| Prop (Content) | Type | Description |
|----------------|------|-------------|
| `onOpenAutoFocus` | event handler | Focus behavior on open |
| `onCloseAutoFocus` | event handler | Focus behavior on close |
| `onEscapeKeyDown` | event handler | ESC key behavior |
| `onPointerDownOutside` | event handler | Click outside behavior |
| `onInteractOutside` | event handler | Any interaction outside |

Keyboard: `Esc` closes, `Tab` trapped inside content.

**Accessibility:** Must include `Title` (or `VisuallyHidden` wrapping it). `Description` recommended.

### Alert Dialog

Same architecture as Dialog but for destructive confirmations. No close-on-click-outside. Forces user to make a choice.

Sub-components: `Root`, `Trigger`, `Portal`, `Overlay`, `Content`, `Cancel`, `Action`, `Title`, `Description`

Keyboard: `Esc` triggers Cancel, `Tab` between Cancel and Action.

### Popover

Sub-components: `Root`, `Trigger`, `Anchor`, `Portal`, `Content`, `Arrow`, `Close`

| Prop (Content) | Type | Description |
|----------------|------|-------------|
| `side` | `"top" \| "right" \| "bottom" \| "left"` | Preferred side |
| `sideOffset` | number | Gap from anchor |
| `align` | `"start" \| "center" \| "end"` | Alignment |
| `alignOffset` | number | Alignment offset |
| `avoidCollisions` | boolean | Collision detection |
| `collisionBoundary` | Element \| Element[] | Collision boundary |
| `collisionPadding` | number \| Padding | Boundary padding |
| `sticky` | `"partial" \| "always"` | Sticky behavior |

Data attrs on Content: `[data-state]`, `[data-side]`, `[data-align]`

CSS variables: `--radix-popover-content-transform-origin`, `--radix-popover-content-available-width`, `--radix-popover-content-available-height`, `--radix-popover-trigger-width`, `--radix-popover-trigger-height`

### Hover Card

Same positioning API as Popover. Opens on hover with configurable delays.

Sub-components: `Root`, `Trigger`, `Portal`, `Content`, `Arrow`

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `openDelay` | number (default: 700) | ms before open |
| `closeDelay` | number (default: 300) | ms before close |

### Tooltip

Sub-components: `Provider`, `Root`, `Trigger`, `Portal`, `Content`, `Arrow`

Wrap app with `Tooltip.Provider` for shared delay behavior.

| Prop (Provider) | Type | Description |
|-----------------|------|-------------|
| `delayDuration` | number (default: 700) | Global open delay |
| `skipDelayDuration` | number (default: 300) | Skip delay between tooltips |
| `disableHoverableContent` | boolean | Prevent hovering content |

---

## Menu Components

### Dropdown Menu

Sub-components: `Root`, `Trigger`, `Portal`, `Content`, `Arrow`, `Item`, `Group`, `Label`, `CheckboxItem`, `RadioGroup`, `RadioItem`, `ItemIndicator`, `Separator`, `Sub`, `SubTrigger`, `SubContent`

Keyboard: `Arrow` navigate, `Enter`/`Space` select, `Esc` close, type to search.

Data attrs on Item: `[data-disabled]`, `[data-highlighted]`
Data attrs on CheckboxItem: `[data-state]` = `"checked"` / `"unchecked"`

### Context Menu

Same API as Dropdown Menu but triggered by right-click. No `Trigger` -- wraps target element.

Sub-components: `Root`, `Trigger`, `Portal`, `Content`, `Arrow`, `Item`, `Group`, `Label`, `CheckboxItem`, `RadioGroup`, `RadioItem`, `ItemIndicator`, `Separator`, `Sub`, `SubTrigger`, `SubContent`

### Menubar

Horizontal menu bar with dropdown menus (like OS menu bars).

Sub-components: `Root`, `Menu`, `Trigger`, `Portal`, `Content`, `Item`, `Group`, `Label`, `CheckboxItem`, `RadioGroup`, `RadioItem`, `ItemIndicator`, `Separator`, `Sub`, `SubTrigger`, `SubContent`

---

## Navigation Components

### Navigation Menu

Sub-components: `Root`, `List`, `Item`, `Trigger`, `Content`, `Link`, `Indicator`, `Viewport`

Implements WAI-ARIA Navigation pattern with arrow key support and managed viewport for animated content.

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `orientation` | `"horizontal" \| "vertical"` | Layout direction |
| `delayDuration` | number (default: 200) | Hover open delay |
| `skipDelayDuration` | number (default: 300) | Skip delay |

### Tabs

Sub-components: `Root`, `List`, `Trigger`, `Content`

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `defaultValue` | string | Initial active tab |
| `value` | string | Controlled active tab |
| `onValueChange` | function | Tab change callback |
| `orientation` | `"horizontal" \| "vertical"` | Arrow key direction |
| `activationMode` | `"automatic" \| "manual"` | Focus vs click activation |

Keyboard: `Arrow` switch tabs, `Home`/`End` first/last, `Tab` to panel content.

---

## Form Components

### Checkbox

Sub-components: `Root`, `Indicator`

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `defaultChecked` | boolean | Initial state |
| `checked` | boolean \| "indeterminate" | Controlled state |
| `onCheckedChange` | function | State change callback |
| `disabled` | boolean | Disabled state |
| `required` | boolean | Form required |
| `name` | string | Form field name |
| `value` | string | Form field value |

Data attrs: `[data-state]` = `"checked"` / `"unchecked"` / `"indeterminate"`, `[data-disabled]`

### Radio Group

Sub-components: `Root`, `Item`, `Indicator`

Keyboard: `Arrow` navigate, `Space` select.

### Select

Sub-components: `Root`, `Trigger`, `Value`, `Icon`, `Portal`, `Content`, `Viewport`, `Item`, `ItemText`, `ItemIndicator`, `Group`, `Label`, `Separator`, `ScrollUpButton`, `ScrollDownButton`, `Arrow`

Supports typeahead, grouping, custom scroll buttons.

### Slider

Sub-components: `Root`, `Track`, `Range`, `Thumb`

Supports multiple thumbs for range selection. Keyboard: `Arrow` adjust by step, `Home`/`End` min/max.

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `defaultValue` | number[] | Initial value(s) |
| `value` | number[] | Controlled value(s) |
| `min` | number (default: 0) | Minimum |
| `max` | number (default: 100) | Maximum |
| `step` | number (default: 1) | Step size |
| `minStepsBetweenThumbs` | number (default: 0) | Min gap between thumbs |
| `orientation` | string | Horizontal/vertical |
| `inverted` | boolean | Reverse direction |

### Switch

Sub-components: `Root`, `Thumb`

Same controlled/uncontrolled pattern as Checkbox. Data attrs: `[data-state]` = `"checked"` / `"unchecked"`

### Toggle

Single sub-component: `Root`

| Prop | Type | Description |
|------|------|-------------|
| `defaultPressed` | boolean | Initial state |
| `pressed` | boolean | Controlled state |
| `onPressedChange` | function | State callback |

Data attrs: `[data-state]` = `"on"` / `"off"`

### Toggle Group

Sub-components: `Root`, `Item`

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `type` | `"single" \| "multiple"` | Selection mode |

### Form

Sub-components: `Root`, `Field`, `Label`, `Control`, `Message`, `ValidityState`, `Submit`

Built-in validation with custom messages:

```tsx
<Form.Field name="email">
  <Form.Label>Email</Form.Label>
  <Form.Control asChild>
    <input type="email" required />
  </Form.Control>
  <Form.Message match="valueMissing">Please enter email</Form.Message>
  <Form.Message match="typeMismatch">Please enter valid email</Form.Message>
</Form.Field>
```

---

## Disclosure Components

### Accordion

Sub-components: `Root`, `Item`, `Header`, `Trigger`, `Content`

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `type` | `"single" \| "multiple"` | **Required.** One or many open |
| `collapsible` | boolean | Allow closing all (single mode) |
| `defaultValue` | string \| string[] | Initial open items |
| `value` | string \| string[] | Controlled open items |
| `orientation` | string | Arrow key direction |

CSS variables on Content: `--radix-accordion-content-width`, `--radix-accordion-content-height`

Keyboard: `Arrow` navigate triggers, `Enter`/`Space` toggle, `Home`/`End`.

### Collapsible

Sub-components: `Root`, `Trigger`, `Content`

CSS variables on Content: `--radix-collapsible-content-width`, `--radix-collapsible-content-height`

---

## Media Components

### Avatar

Sub-components: `Root`, `Image`, `Fallback`

| Prop (Fallback) | Type | Description |
|-----------------|------|-------------|
| `delayMs` | number | Delay before showing fallback |

### Aspect Ratio

Single component wrapping content in a fixed ratio container.

| Prop | Type | Description |
|------|------|-------------|
| `ratio` | number (default: 1) | Width/height ratio (e.g. 16/9) |

### Progress

Sub-components: `Root`, `Indicator`

| Prop (Root) | Type | Description |
|-------------|------|-------------|
| `value` | number \| null | Current value (null = indeterminate) |
| `max` | number (default: 100) | Maximum value |

---

## Layout Components

### Scroll Area

Sub-components: `Root`, `Viewport`, `Scrollbar`, `Thumb`, `Corner`

Custom scrollbar styling while maintaining native scroll behavior.

| Prop (Scrollbar) | Type | Description |
|------------------|------|-------------|
| `orientation` | `"horizontal" \| "vertical"` | Scrollbar direction |
| `forceMount` | boolean | Always show scrollbar |

### Separator

| Prop | Type | Description |
|------|------|-------------|
| `orientation` | `"horizontal" \| "vertical"` | Direction |
| `decorative` | boolean | If true, `role="none"` |

### Toolbar

Sub-components: `Root`, `Button`, `Separator`, `Link`, `ToggleGroup`, `ToggleItem`

Groups buttons and toggles with proper `role="toolbar"` and arrow key navigation.

---

## Utility Components

### Label

Associates with form controls via `htmlFor` or wrapping. Handles click-to-focus on the associated control.

### Portal

Renders children into `document.body` (or custom container).

| Prop | Type | Description |
|------|------|-------------|
| `container` | HTMLElement | Target container |

### Visually Hidden

Hides content visually while keeping it accessible to screen readers.

### Direction Provider

Wraps app to provide RTL/LTR direction for all Radix components.

```tsx
<DirectionProvider dir="rtl">
  <App />
</DirectionProvider>
```
