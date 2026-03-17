# daisyUI Component Reference

Complete class name reference for all 65 daisyUI components. Each entry lists the base class, sub-parts, modifiers, and color/size variants.

Docs: https://daisyui.com/components/

## Class name conventions

```
{component}                     base class (always required)
{component}-{part}              sub-element within the component
{component}-{variant}           style variant (outline, ghost, soft, dash)
{component}-{color}             semantic color (primary, secondary, accent, neutral, info, success, warning, error)
{component}-{size}              size (xs, sm, md, lg, xl)
{component}-{modifier}          state or layout modifier (active, disabled, open, vertical, horizontal)
```

---

## Actions

### Button
| Class | Type | Description |
|-------|------|-------------|
| `btn` | base | Button element |
| `btn-neutral` | color | Neutral color |
| `btn-primary` | color | Primary color |
| `btn-secondary` | color | Secondary color |
| `btn-accent` | color | Accent color |
| `btn-info` | color | Info color |
| `btn-success` | color | Success color |
| `btn-warning` | color | Warning color |
| `btn-error` | color | Error color |
| `btn-outline` | variant | Outline style |
| `btn-ghost` | variant | Ghost/transparent style |
| `btn-soft` | variant | Soft/muted background |
| `btn-dash` | variant | Dashed border |
| `btn-link` | variant | Styled as link |
| `btn-xs` | size | Extra small |
| `btn-sm` | size | Small |
| `btn-md` | size | Medium (default) |
| `btn-lg` | size | Large |
| `btn-xl` | size | Extra large |
| `btn-wide` | modifier | Extra horizontal padding |
| `btn-block` | modifier | Full width |
| `btn-circle` | modifier | Circular (1:1 + rounded) |
| `btn-square` | modifier | Square (1:1) |
| `btn-active` | state | Active/pressed appearance |
| `btn-disabled` | state | Disabled state |

### Dropdown
| Class | Type | Description |
|-------|------|-------------|
| `dropdown` | base | Container |
| `dropdown-content` | part | Dropdown menu/body |
| `dropdown-end` | modifier | Align to end |
| `dropdown-top` | modifier | Open upward |
| `dropdown-bottom` | modifier | Open downward |
| `dropdown-left` | modifier | Open to left |
| `dropdown-right` | modifier | Open to right |
| `dropdown-hover` | modifier | Open on hover |
| `dropdown-open` | modifier | Force open |

### Modal
| Class | Type | Description |
|-------|------|-------------|
| `modal` | base | Container (use with `<dialog>`) |
| `modal-box` | part | Content wrapper |
| `modal-action` | part | Footer actions area |
| `modal-backdrop` | part | Clickable close overlay |
| `modal-toggle` | part | Hidden checkbox (legacy) |
| `modal-open` | modifier | Force visible |
| `modal-top` | modifier | Top position |
| `modal-middle` | modifier | Center position |
| `modal-bottom` | modifier | Bottom position |
| `modal-start` | modifier | Left alignment |
| `modal-end` | modifier | Right alignment |

### Swap
| Class | Type | Description |
|-------|------|-------------|
| `swap` | base | Toggle container |
| `swap-on` | part | Visible when active |
| `swap-off` | part | Visible when inactive |
| `swap-indeterminate` | part | Visible in indeterminate state |
| `swap-active` | modifier | Force active state |
| `swap-rotate` | modifier | Rotate animation |
| `swap-flip` | modifier | Flip animation |

### Theme Controller
| Class | Type | Description |
|-------|------|-------------|
| `theme-controller` | base | Checkbox/radio that switches `data-theme` |

---

## Data Display

### Accordion
| Class | Type | Description |
|-------|------|-------------|
| `collapse` | base | Collapsible container |
| `collapse-title` | part | Clickable title |
| `collapse-content` | part | Hidden content |
| `collapse-arrow` | modifier | Arrow indicator |
| `collapse-plus` | modifier | Plus/minus indicator |
| `collapse-open` | modifier | Force open |
| `collapse-close` | modifier | Force closed |

Use `<input type="radio" name="accordion">` for single-open accordion behavior.

### Avatar
| Class | Type | Description |
|-------|------|-------------|
| `avatar` | base | Container |
| `avatar-group` | base | Group multiple avatars |
| `online` | modifier | Green online indicator |
| `offline` | modifier | Gray offline indicator |
| `placeholder` | modifier | Text placeholder style |

### Badge
| Class | Type | Description |
|-------|------|-------------|
| `badge` | base | Inline badge |
| `badge-{color}` | color | All semantic colors |
| `badge-outline` | variant | Outline style |
| `badge-soft` | variant | Soft background |
| `badge-dash` | variant | Dashed border |
| `badge-ghost` | variant | Ghost style |
| `badge-xs/sm/md/lg/xl` | size | Size variants |

### Card
| Class | Type | Description |
|-------|------|-------------|
| `card` | base | Card container |
| `card-body` | part | Content area with padding |
| `card-title` | part | Title text |
| `card-actions` | part | Action buttons area |
| `card-bordered` | modifier | Add border |
| `card-dash` | modifier | Dashed border |
| `card-compact` | modifier | Reduced padding |
| `card-side` | modifier | Horizontal layout |
| `image-full` | modifier | Full-bleed image background |

### Carousel
| Class | Type | Description |
|-------|------|-------------|
| `carousel` | base | Scrollable container |
| `carousel-item` | part | Each slide |
| `carousel-center` | modifier | Center active item |
| `carousel-end` | modifier | Snap to end |
| `carousel-vertical` | modifier | Vertical scroll |

### Chat Bubble
| Class | Type | Description |
|-------|------|-------------|
| `chat` | base | Chat line container |
| `chat-image` | part | Author avatar |
| `chat-header` | part | Author name/metadata |
| `chat-bubble` | part | Message bubble |
| `chat-footer` | part | Status text |
| `chat-start` | modifier | Left-aligned (incoming) |
| `chat-end` | modifier | Right-aligned (outgoing) |
| `chat-bubble-{color}` | color | Bubble color |

### Countdown
| Class | Type | Description |
|-------|------|-------------|
| `countdown` | base | Number transition container |

Set value via CSS `--value` custom property (0-999).

### Diff
| Class | Type | Description |
|-------|------|-------------|
| `diff` | base | Side-by-side comparison |
| `diff-item-1` | part | First item |
| `diff-item-2` | part | Second item |
| `diff-resizer` | part | Drag handle |

### Kbd
| Class | Type | Description |
|-------|------|-------------|
| `kbd` | base | Keyboard key display |
| `kbd-xs/sm/md/lg/xl` | size | Size variants |

### List
| Class | Type | Description |
|-------|------|-------------|
| `list` | base | Vertical list container |
| `list-row` | part | Row item |

### Stat
| Class | Type | Description |
|-------|------|-------------|
| `stats` | base | Stats container |
| `stat` | part | Individual stat block |
| `stat-title` | part | Label text |
| `stat-value` | part | Main number |
| `stat-desc` | part | Description text |
| `stat-figure` | part | Icon/image area |
| `stat-actions` | part | Action buttons |
| `stats-horizontal` | modifier | Horizontal layout |
| `stats-vertical` | modifier | Vertical layout |

### Table
| Class | Type | Description |
|-------|------|-------------|
| `table` | base | Table element |
| `table-zebra` | modifier | Alternating row colors |
| `table-pin-rows` | modifier | Sticky header |
| `table-pin-cols` | modifier | Sticky first column |
| `table-xs/sm/md/lg` | size | Size variants |
| `active` | state | Highlight row |
| `hover` | state | Highlight on hover |

### Timeline
| Class | Type | Description |
|-------|------|-------------|
| `timeline` | base | Timeline container |
| `timeline-start` | part | Content before marker |
| `timeline-middle` | part | Marker area |
| `timeline-end` | part | Content after marker |
| `timeline-snap-icon` | modifier | Snap alignment |
| `timeline-compact` | modifier | Single-side layout |
| `timeline-vertical` | modifier | Vertical orientation |
| `timeline-horizontal` | modifier | Horizontal orientation |

---

## Navigation

### Breadcrumbs
| Class | Type | Description |
|-------|------|-------------|
| `breadcrumbs` | base | Container (use with `<ul>`) |

### Dock
| Class | Type | Description |
|-------|------|-------------|
| `dock` | base | Bottom navigation bar |
| `dock-label` | part | Label text |
| `dock-active` | state | Active item |
| `dock-xs/sm/md/lg/xl` | size | Size variants |

### Link
| Class | Type | Description |
|-------|------|-------------|
| `link` | base | Underlined link |
| `link-{color}` | color | All semantic colors |
| `link-hover` | modifier | Underline only on hover |

### Menu
| Class | Type | Description |
|-------|------|-------------|
| `menu` | base | Menu container |
| `menu-title` | part | Section title |
| `menu-dropdown` | part | Submenu container |
| `menu-dropdown-toggle` | part | Submenu trigger |
| `menu-xs/sm/md/lg/xl` | size | Size variants |
| `menu-horizontal` | modifier | Horizontal layout |
| `menu-vertical` | modifier | Vertical layout (default) |
| `active` | state | Active menu item |
| `disabled` | state | Disabled item |
| `focus` | state | Focused item |

### Navbar
| Class | Type | Description |
|-------|------|-------------|
| `navbar` | base | Top navigation bar |
| `navbar-start` | part | Left section |
| `navbar-center` | part | Center section |
| `navbar-end` | part | Right section |

### Pagination
| Class | Type | Description |
|-------|------|-------------|
| `join` | base | Button group container |
| `join-item` | part | Each page button |

### Steps
| Class | Type | Description |
|-------|------|-------------|
| `steps` | base | Step container |
| `step` | part | Individual step |
| `step-{color}` | color | Step color |
| `steps-horizontal` | modifier | Horizontal layout |
| `steps-vertical` | modifier | Vertical layout |

### Tabs
| Class | Type | Description |
|-------|------|-------------|
| `tabs` | base | Tab container |
| `tab` | part | Individual tab |
| `tab-content` | part | Tab panel content |
| `tab-active` | state | Active tab |
| `tab-disabled` | state | Disabled tab |
| `tabs-box` | modifier | Boxed style |
| `tabs-border` | modifier | Bottom border style |
| `tabs-lift` | modifier | Lifted/raised style |
| `tabs-xs/sm/md/lg/xl` | size | Size variants |

---

## Feedback

### Alert
| Class | Type | Description |
|-------|------|-------------|
| `alert` | base | Alert container |
| `alert-info` | color | Info style |
| `alert-success` | color | Success style |
| `alert-warning` | color | Warning style |
| `alert-error` | color | Error style |
| `alert-outline` | variant | Outline style |
| `alert-soft` | variant | Soft background |
| `alert-dash` | variant | Dashed border |

### Loading
| Class | Type | Description |
|-------|------|-------------|
| `loading` | base | Loading spinner |
| `loading-spinner` | modifier | Spinner animation |
| `loading-dots` | modifier | Dots animation |
| `loading-ring` | modifier | Ring animation |
| `loading-ball` | modifier | Bouncing ball |
| `loading-bars` | modifier | Bars animation |
| `loading-infinity` | modifier | Infinity animation |
| `loading-xs/sm/md/lg/xl` | size | Size variants |

### Progress
| Class | Type | Description |
|-------|------|-------------|
| `progress` | base | Progress bar |
| `progress-{color}` | color | All semantic colors |

### Radial Progress
| Class | Type | Description |
|-------|------|-------------|
| `radial-progress` | base | Circular progress |

Set value via `--value` CSS variable (0-100) and `--size`/`--thickness`.

### Skeleton
| Class | Type | Description |
|-------|------|-------------|
| `skeleton` | base | Loading placeholder |

### Toast
| Class | Type | Description |
|-------|------|-------------|
| `toast` | base | Positioned container |
| `toast-start` | modifier | Left |
| `toast-center` | modifier | Center |
| `toast-end` | modifier | Right |
| `toast-top` | modifier | Top |
| `toast-middle` | modifier | Middle |
| `toast-bottom` | modifier | Bottom |

### Tooltip
| Class | Type | Description |
|-------|------|-------------|
| `tooltip` | base | Tooltip wrapper |
| `tooltip-{color}` | color | All semantic colors |
| `tooltip-open` | modifier | Force visible |
| `tooltip-top` | modifier | Position top |
| `tooltip-bottom` | modifier | Position bottom |
| `tooltip-left` | modifier | Position left |
| `tooltip-right` | modifier | Position right |

Set text via `data-tip="text"` attribute.

---

## Data Input

### Checkbox
| Class | Type | Description |
|-------|------|-------------|
| `checkbox` | base | Checkbox input |
| `checkbox-{color}` | color | All semantic colors |
| `checkbox-xs/sm/md/lg/xl` | size | Size variants |

### Fieldset
| Class | Type | Description |
|-------|------|-------------|
| `fieldset` | base | Form group container |
| `fieldset-legend` | part | Legend/title |

### File Input
| Class | Type | Description |
|-------|------|-------------|
| `file-input` | base | File upload input |
| `file-input-{color}` | color | All semantic colors |
| `file-input-bordered` | modifier | Add border |
| `file-input-ghost` | variant | Ghost style |
| `file-input-xs/sm/md/lg/xl` | size | Size variants |

### Filter
| Class | Type | Description |
|-------|------|-------------|
| `filter` | base | Radio group with reset |
| `filter-reset` | part | Reset button |

### Label
| Class | Type | Description |
|-------|------|-------------|
| `label` | base | Form label |

### Radio
| Class | Type | Description |
|-------|------|-------------|
| `radio` | base | Radio button |
| `radio-{color}` | color | All semantic colors |
| `radio-xs/sm/md/lg/xl` | size | Size variants |

### Range (Slider)
| Class | Type | Description |
|-------|------|-------------|
| `range` | base | Range slider |
| `range-{color}` | color | All semantic colors |
| `range-xs/sm/md/lg/xl` | size | Size variants |

### Rating
| Class | Type | Description |
|-------|------|-------------|
| `rating` | base | Star rating container |
| `rating-half` | modifier | Half-star support |
| `rating-hidden` | modifier | Hidden reset input |
| `rating-xs/sm/md/lg/xl` | size | Size variants |

### Select
| Class | Type | Description |
|-------|------|-------------|
| `select` | base | Select dropdown |
| `select-{color}` | color | All semantic colors |
| `select-bordered` | modifier | Add border |
| `select-ghost` | variant | Ghost style |
| `select-xs/sm/md/lg/xl` | size | Size variants |

### Text Input
| Class | Type | Description |
|-------|------|-------------|
| `input` | base | Text input |
| `input-{color}` | color | All semantic colors |
| `input-bordered` | modifier | Add border |
| `input-ghost` | variant | Ghost style |
| `input-xs/sm/md/lg/xl` | size | Size variants |

### Textarea
| Class | Type | Description |
|-------|------|-------------|
| `textarea` | base | Multi-line input |
| `textarea-{color}` | color | All semantic colors |
| `textarea-bordered` | modifier | Add border |
| `textarea-ghost` | variant | Ghost style |
| `textarea-xs/sm/md/lg/xl` | size | Size variants |

### Toggle
| Class | Type | Description |
|-------|------|-------------|
| `toggle` | base | Switch toggle |
| `toggle-{color}` | color | All semantic colors |
| `toggle-xs/sm/md/lg/xl` | size | Size variants |

### Validator
| Class | Type | Description |
|-------|------|-------------|
| `validator` | base | Form validation styling |

---

## Layout

### Divider
| Class | Type | Description |
|-------|------|-------------|
| `divider` | base | Content separator |
| `divider-{color}` | color | All semantic colors |
| `divider-horizontal` | modifier | Horizontal (in flex row) |
| `divider-vertical` | modifier | Vertical |
| `divider-start` | modifier | Text aligned to start |
| `divider-end` | modifier | Text aligned to end |

### Drawer
| Class | Type | Description |
|-------|------|-------------|
| `drawer` | base | Grid layout container |
| `drawer-toggle` | part | Hidden checkbox |
| `drawer-content` | part | Main page content |
| `drawer-side` | part | Sidebar wrapper |
| `drawer-overlay` | part | Dark backdrop |
| `drawer-end` | modifier | Right-side drawer |
| `drawer-open` | modifier | Force open |
| `is-drawer-open:` | variant | Styles when open |
| `is-drawer-close:` | variant | Styles when closed |

### Footer
| Class | Type | Description |
|-------|------|-------------|
| `footer` | base | Footer container |
| `footer-title` | part | Section title |
| `footer-center` | modifier | Centered layout |

### Hero
| Class | Type | Description |
|-------|------|-------------|
| `hero` | base | Hero section |
| `hero-content` | part | Content area |
| `hero-overlay` | part | Image overlay |

### Indicator
| Class | Type | Description |
|-------|------|-------------|
| `indicator` | base | Position container |
| `indicator-item` | part | Corner badge |
| `indicator-start` | modifier | Left position |
| `indicator-center` | modifier | Center position |
| `indicator-end` | modifier | Right position |
| `indicator-top` | modifier | Top position |
| `indicator-middle` | modifier | Middle position |
| `indicator-bottom` | modifier | Bottom position |

### Join
| Class | Type | Description |
|-------|------|-------------|
| `join` | base | Group container |
| `join-item` | part | Grouped element |
| `join-horizontal` | modifier | Horizontal (default) |
| `join-vertical` | modifier | Vertical |

### Mask
| Class | Type | Description |
|-------|------|-------------|
| `mask` | base | Shape mask |
| `mask-squircle` | shape | Rounded square |
| `mask-heart` | shape | Heart |
| `mask-hexagon` | shape | Hexagon |
| `mask-hexagon-2` | shape | Rotated hexagon |
| `mask-decagon` | shape | Decagon |
| `mask-pentagon` | shape | Pentagon |
| `mask-diamond` | shape | Diamond |
| `mask-square` | shape | Square |
| `mask-circle` | shape | Circle |
| `mask-star` | shape | 5-point star |
| `mask-star-2` | shape | 4-point star |
| `mask-triangle` | shape | Triangle |
| `mask-triangle-2` | shape | Upside-down triangle |
| `mask-triangle-3` | shape | Left triangle |
| `mask-triangle-4` | shape | Right triangle |
| `mask-parallelogram` | shape | Parallelogram |
| `mask-parallelogram-2` | shape | Reverse parallelogram |
| `mask-half-1` | modifier | Left half |
| `mask-half-2` | modifier | Right half |

### Stack
| Class | Type | Description |
|-------|------|-------------|
| `stack` | base | Stacked elements (visual depth) |

---

## Mockup

### Browser
| Class | Type | Description |
|-------|------|-------------|
| `mockup-browser` | base | Browser chrome |
| `mockup-browser-toolbar` | part | URL bar area |

### Code
| Class | Type | Description |
|-------|------|-------------|
| `mockup-code` | base | Code editor |

Use `<pre data-prefix="$">` for line prefixes and `class="bg-warning text-warning-content"` for highlighted lines.

### Phone
| Class | Type | Description |
|-------|------|-------------|
| `mockup-phone` | base | iPhone mockup |

### Window
| Class | Type | Description |
|-------|------|-------------|
| `mockup-window` | base | OS window frame |
| `mockup-window-bordered` | modifier | Add border |

---

## Utility Classes

### Glass
| Class | Description |
|-------|-------------|
| `glass` | Frosted glass effect with blur, opacity, reflection |

### Responsive prefix support

All daisyUI modifiers support Tailwind responsive prefixes:
```html
<button class="btn btn-xs md:btn-md lg:btn-lg">Responsive</button>
<dialog class="modal modal-bottom sm:modal-middle">Responsive modal</dialog>
<div class="drawer lg:drawer-open">Responsive drawer</div>
```
