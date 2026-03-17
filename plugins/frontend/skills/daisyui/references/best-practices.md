# daisyUI Best Practices and Common Pitfalls

## Best Practices

### 1. Use semantic colors, not Tailwind color utilities

```html
<!-- Bad: breaks when theme changes -->
<button class="bg-blue-500 text-white px-4 py-2 rounded">Submit</button>

<!-- Good: adapts to any theme -->
<button class="btn btn-primary">Submit</button>
```

daisyUI's semantic colors (`primary`, `secondary`, `accent`, etc.) change with themes. Using `bg-blue-500` hardcodes a color that ignores the active theme.

### 2. Always include the base class

```html
<!-- Bad: no styles applied -->
<button class="btn-primary">Submit</button>

<!-- Good: base class required -->
<button class="btn btn-primary">Submit</button>
```

Modifiers like `btn-primary` only work when the base class (`btn`) is present.

### 3. Combine daisyUI components with Tailwind utilities

daisyUI handles component styling; Tailwind handles layout, spacing, and sizing:

```html
<div class="flex flex-col gap-4 p-6 max-w-md mx-auto">
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title text-2xl">Title</h2>
      <p class="text-sm text-base-content/70">Subtitle</p>
      <div class="card-actions justify-end mt-4">
        <button class="btn btn-primary btn-sm">Action</button>
      </div>
    </div>
  </div>
</div>
```

### 4. Choose themes early

Pick or create your theme before building UI. Retrofitting themes after using hardcoded colors is painful.

```css
/* Set up early in your CSS */
@plugin "daisyui" {
  themes: corporate --default, business --prefersdark;
}
```

### 5. Use `<dialog>` for modals, not checkbox

The checkbox method is legacy. Native `<dialog>` provides:
- Built-in ESC key support
- Better focus management
- Proper accessibility semantics
- `showModal()` / `close()` API

```html
<!-- Recommended -->
<dialog id="confirm" class="modal">
  <div class="modal-box">
    <p>Are you sure?</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn btn-ghost">Cancel</button>
        <button class="btn btn-error">Delete</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>
```

### 6. Responsive drawer pattern

Standard responsive sidebar: hidden on mobile (toggle via hamburger), always visible on desktop:

```html
<div class="drawer lg:drawer-open">
  <input id="nav" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <navbar class="navbar bg-base-100 lg:hidden">
      <label for="nav" class="btn btn-ghost btn-circle">
        <svg><!-- hamburger icon --></svg>
      </label>
    </navbar>
    <!-- page content -->
  </div>
  <div class="drawer-side">
    <label for="nav" class="drawer-overlay"></label>
    <aside class="menu bg-base-200 min-h-full w-80 p-4">
      <!-- nav items -->
    </aside>
  </div>
</div>
```

### 7. Use `join` for connected elements

```html
<!-- Button group -->
<div class="join">
  <button class="btn join-item">Left</button>
  <button class="btn join-item btn-active">Center</button>
  <button class="btn join-item">Right</button>
</div>

<!-- Search with button -->
<div class="join">
  <input class="input input-bordered join-item" placeholder="Search..." />
  <button class="btn btn-primary join-item">Go</button>
</div>
```

### 8. Use `content` colors for text on colored backgrounds

When placing text on a semantic background, use the matching `-content` color:

```html
<div class="bg-primary text-primary-content p-4">
  Readable text on primary background
</div>

<div class="bg-error text-error-content p-4">
  Readable text on error background
</div>
```

### 9. Use `data-theme` for scoped theming

Nest different themes on parts of the page:

```html
<html data-theme="light">
  <body>
    <main>Light content</main>
    <footer data-theme="dark">
      Dark footer section
    </footer>
  </body>
</html>
```

### 10. Optimize bundle with include/exclude

If you only use a few components, whitelist them:

```css
@plugin "daisyui" {
  include: btn, card, modal, input, select, alert, menu, navbar, drawer;
}
```

Or exclude large components you don't need:

```css
@plugin "daisyui" {
  exclude: carousel, countdown, diff, mockup-browser, mockup-phone, mockup-code, mockup-window;
}
```

---

## Common Pitfalls

### 1. Hardcoded colors break theming

**Problem:** Using `bg-blue-500` or `text-gray-800` instead of semantic colors makes components ignore theme changes.

**Fix:** Replace Tailwind color utilities with daisyUI semantic colors:
- `bg-blue-500` -> `bg-primary`
- `text-gray-800` -> `text-base-content`
- `border-red-500` -> `border-error`
- `bg-gray-100` -> `bg-base-200`

### 2. Missing base class

**Problem:** Adding `btn-primary` without `btn` produces no styling.

**Fix:** Always include the base class first: `class="btn btn-primary"`.

### 3. Themes not enabled

**Problem:** Only `light` and `dark` themes work; other themes via `data-theme` show wrong colors.

**Fix:** Enable themes in config:
```css
@plugin "daisyui" {
  themes: all;  /* or list specific themes */
}
```

### 4. Modal conflicts with framework portals

**Problem:** React/Vue portal-based modals conflict with daisyUI's CSS modal positioning.

**Fix:** Either use native `<dialog>` with `showModal()` (works with daisyUI classes), or use the framework's modal with custom styling instead of daisyUI modal classes.

### 5. Using `dark:` instead of `data-theme`

**Problem:** Tailwind `dark:` variants only toggle between light/dark. daisyUI has 35 themes.

**Fix:** Use `data-theme` for theme switching. If you need Tailwind `dark:` to work alongside daisyUI themes, configure a custom variant:
```css
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));
```

### 6. Forgetting responsive prefixes

**Problem:** Fixed sizes that don't adapt to screen size.

**Fix:** Use Tailwind responsive prefixes with daisyUI size classes:
```html
<button class="btn btn-sm md:btn-md lg:btn-lg">Responsive</button>
```

### 7. Accordion items all open simultaneously

**Problem:** Multiple collapse items can open at the same time.

**Fix:** For single-open accordion behavior, use radio inputs with the same `name`:
```html
<div class="collapse collapse-arrow bg-base-100">
  <input type="radio" name="faq" checked />
  <div class="collapse-title">Question 1</div>
  <div class="collapse-content">Answer 1</div>
</div>
<div class="collapse collapse-arrow bg-base-100">
  <input type="radio" name="faq" />
  <div class="collapse-title">Question 2</div>
  <div class="collapse-content">Answer 2</div>
</div>
```

### 8. Toast positioning issues

**Problem:** Toast appears behind other elements or is clipped.

**Fix:** Place the `toast` element at the root level of the body, not nested inside positioned containers. Use fixed positioning via Tailwind if needed:
```html
<div class="toast toast-end toast-top z-50">
  <div class="alert alert-success">Saved!</div>
</div>
```

### 9. Overriding component styles incorrectly

**Problem:** Custom CSS for daisyUI components gets overridden or conflicts.

**Fix:** Use the `@utility` directive for project-wide overrides:
```css
@utility btn {
  @apply rounded-full shadow-md;
}
```

For one-off changes, add Tailwind utilities directly to the element.

### 10. Not using glass effect correctly

**Problem:** `glass` class looks wrong without a background image or gradient behind it.

**Fix:** `glass` is a frosted-glass effect -- it needs a visible background to blur. Place it over an image, gradient, or colored section:
```html
<div class="relative bg-cover bg-center" style="background-image: url(bg.jpg)">
  <div class="glass p-6 rounded-box">
    Content with frosted glass effect
  </div>
</div>
```

---

## Accessibility Checklist

- Use `<button>` for buttons, `<a>` for navigation links -- daisyUI styles both
- Add `aria-label` to icon-only buttons (`btn-square`, `btn-circle`)
- Use `<dialog>` for modals -- provides native focus trap and ESC handling
- Include `role="dialog"` if using checkbox modal method
- Use semantic HTML: `<nav>` with `navbar`, `<footer>` with `footer`, `<aside>` with drawer sidebar
- Test keyboard navigation: Tab through menus, Enter/Space for buttons, ESC for modals
- Ensure sufficient color contrast -- verify custom themes with contrast checker tools
- Add `tabindex="-1"` and `role="button"` with `btn-disabled` (disabled attribute alone works on `<button>`)
