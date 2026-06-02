<!--
Portions of this file are derived from pbakaus/impeccable
(https://github.com/pbakaus/impeccable), Apache License 2.0.
Snapshot 2026-06-02.

See plugins/frontend/NOTICE.md for the full upstream attribution chain.
-->

# Production Hardening

Designs that only work with perfect data are not production-ready. Harden the interface against the inputs, errors, languages, and network conditions that real users will throw at it. The recurring failures: very long text, empty data, RTL scripts, API errors, and slow connections.

## Stress inputs to test against

- **Text length**: very long names/titles/descriptions, and the opposite (empty, single character).
- **Special characters**: emoji, RTL text, accents, CJK.
- **Numbers**: millions and billions; locale formats (`1,000` vs `1.000`).
- **Volume**: 1000+ list items, 50+ select options.
- **Errors**: offline, slow, timeout, 400/401/403/404/429/500, validation failures, permission denials, concurrent operations.

## Text Overflow & Wrapping

```css
/* Single line with ellipsis */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Multi-line clamp */
.line-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Allow wrapping of long unbroken strings (URLs, tokens) */
.wrap {
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}
```

**The flex/grid overflow gotcha**: a flex or grid item refuses to shrink below its content size by default, which causes overflow with long text. Fix it with `min-width: 0` (and `min-height: 0` for grid):

```css
.flex-item { min-width: 0; overflow: hidden; }
.grid-item { min-width: 0; min-height: 0; }
```

For text sizing, prefer `clamp()` for fluid type, keep a minimum readable size (14px on mobile), let containers expand with their text rather than fixing widths, and confirm the layout survives 200% zoom.

## Internationalization

**Text expansion**: budget 30-40% extra space for translations (German runs ~30% longer than English). Use flexbox/grid that adapts to content; never fix the width of a text container.

```jsx
// Bad: w-24 assumes short English text and clips translations
<button className="w-24">Submit</button>

// Good: padding adapts to content length
<button className="px-4 py-2">Submit</button>
```

**RTL support**: reach for CSS logical properties so layout mirrors automatically.

```css
margin-inline-start: 1rem;   /* not margin-left */
padding-inline: 1rem;        /* not padding-left/right */
border-inline-end: 1px solid; /* not border-right */

/* Directional glyphs still need an explicit flip */
[dir="rtl"] .arrow { transform: scaleX(-1); }
```

**Character sets**: UTF-8 everywhere; test CJK and emoji (emoji are 2-4 bytes and break naive character counts).

**Formatting**: use the `Intl` API rather than hand-rolled formatting.

```javascript
new Intl.DateTimeFormat('de-DE').format(date); // 15.1.2024
new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(1234.56); // $1,234.56
```

**Pluralization**: `${count} item${count !== 1 ? 's' : ''}` only works for English. Use an i18n library's plural rules (`t('items', { count })`) for languages with more than two plural forms.

## Error Handling

**Network errors**: show a clear message, explain what happened, and offer a retry. Handle timeouts explicitly.

```jsx
{error && (
  <ErrorMessage>
    <p>Failed to load data. {error.message}</p>
    <button onClick={retry}>Try again</button>
  </ErrorMessage>
)}
```

**Form validation**: inline errors next to the field, specific messages, suggested corrections, and preserve the user's input on failure. Do not block submission for non-blocking issues.

**API status codes** map to distinct UI states:

| Code | UI response |
|------|-------------|
| 400 | Show validation errors |
| 401 | Redirect to login |
| 403 | Show permission error |
| 404 | Show not-found state |
| 429 | Show rate-limit message |
| 500 | Generic error, offer a support path |

**Graceful degradation**: core functionality works without JavaScript where feasible; images carry alt text; features detect support rather than assuming it; provide fallbacks.

## Edge Cases & Boundary Conditions

- **Empty states**: no items, no results, no notifications. Always provide a clear next action, not a blank pane.
- **Loading states**: name what is loading ("Loading your projects..."); give a time estimate for long operations.
- **Large datasets**: paginate or virtualize; never render 10,000 rows at once. Pair with search/filter.
- **Concurrent operations**: disable the submit button while a request is in flight to prevent double submission; handle race conditions; use optimistic updates with rollback.
- **Permission states**: view-denied, edit-denied, read-only. Explain *why* access is limited.
- **Browser compatibility**: feature-detect (not browser-detect); polyfill modern features; provide CSS fallbacks.

## Input Validation & Sanitization

Client-side validation (required fields, format, length, patterns) is for fast feedback only. **Server-side validation is mandatory**: never trust the client, sanitize all inputs, protect against injection, and rate-limit.

```html
<input type="text" maxlength="100" pattern="[A-Za-z0-9]+" required aria-describedby="username-hint" />
<small id="username-hint">Letters and numbers only, up to 100 characters</small>
```

## Accessibility Resilience

- **Keyboard**: every action reachable by keyboard, logical tab order, focus trapped and restored in modals, skip links for long content.
- **Screen readers**: ARIA labels, live regions to announce dynamic changes, descriptive alt text, semantic HTML.
- **Motion sensitivity**: honor the user's reduced-motion preference.

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- **High contrast**: test Windows high-contrast mode; never rely on color alone; provide an alternative visual cue.

## Performance Resilience

- **Slow connections**: progressive image loading, skeleton screens, optimistic UI, offline support via service workers.
- **Memory leaks**: clean up event listeners, cancel subscriptions, clear timers, abort pending requests on unmount.
- **Throttle and debounce** high-frequency handlers.

```javascript
const debouncedSearch = debounce(handleSearch, 300); // search input
const throttledScroll = throttle(handleScroll, 100); // scroll handler
```

## Verification checklist

Names with 100+ characters. Emoji in every text field. Arabic or Hebrew for RTL. CJK characters. Internet disabled and connection throttled to 3G. 1000+ item lists. Submit clicked ten times rapidly. Forced API errors across all states. All data removed for empty states. Keyboard-only navigation. Screen reader pass.

---

**Avoid**: Assuming perfect input. Fixed widths on text containers. Assuming English-length text. Generic error messages ("Error occurred"). Trusting client-side validation alone. Forgetting offline scenarios. Blocking the entire interface when one component errors.
