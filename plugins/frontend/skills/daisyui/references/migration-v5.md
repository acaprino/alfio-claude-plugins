# daisyUI v4 to v5 Migration Guide

## Requirements

- Tailwind CSS 4 (required)
- daisyUI v5 configures via CSS `@plugin`, not `tailwind.config.js`

## Migration Steps

1. Remove daisyUI from `tailwind.config.js` (delete the `plugins: [require("daisyui")]` line)
2. Run `npx @tailwindcss/upgrade` to migrate Tailwind to v4
3. Install latest: `npm i -D daisyui@latest`
4. Add to CSS:
   ```css
   @import "tailwindcss";
   @plugin "daisyui";
   ```
5. Apply class renames and behavioral changes below

## Renamed Classes

| v4 | v5 |
|----|-----|
| `card-bordered` | `card-border` |
| `card-compact` | `card-sm` |
| `tabs-bordered` | `tabs-border` |
| `tabs-lifted` | `tabs-lift` |
| `tabs-boxed` | `tabs-box` |
| `online` (avatar) | `avatar-online` |
| `offline` (avatar) | `avatar-offline` |
| `placeholder` (avatar) | `avatar-placeholder` |
| `disabled` (menu) | `menu-disabled` |
| `active` (menu) | `menu-active` |
| `focus` (menu) | `menu-focus` |
| `btm-nav` | `dock` |

## Removed Classes

| Removed | Replacement |
|---------|-------------|
| `form-control` | `fieldset` + `legend` |
| `label-text`, `label-text-alt` | `fieldset-legend` or `label` |
| `btn-group` | `join` |
| `input-group` | `join` |
| `artboard` | Tailwind `w-*` / `h-*` utilities |
| `-bordered` on inputs | Border is now default; use `-ghost` to remove |
| `hover` on table | Use `hover:bg-base-300` |

## Removed CSS Variables

| Removed | Notes |
|---------|-------|
| `--animation-btn` | Removed; use Tailwind animations |
| `--animation-input` | Removed |
| `--btn-focus-scale` | Removed |
| `--p`, `--b1`, etc. | Abbreviated names replaced with full names (`--color-primary`, `--color-base-100`) |

## Behavioral Changes

- **Footer**: vertical by default -- add `footer-horizontal` for horizontal layout
- **Inputs/selects**: have border by default and default `width: 20rem`
- **btn-ghost**: hover now transitions from ghost to visible (was always slightly visible)
- **Stat**: background is transparent -- add `bg-base-100` if needed
- **Menu**: not full width by default -- add `w-full` if needed
- **Content colors**: no longer auto-calculated from background -- must be specified in custom themes

## New in v5

### New components
- `list` / `list-row` - vertical information rows
- `status` - small status icon
- `fieldset` / `fieldset-legend` - semantic form grouping
- `label` - floating label support
- `filter` / `filter-reset` - radio button group with reset
- `calendar` - styles for calendar libraries
- `validator` / `validator-hint` - validation-driven styling
- `dock` / `dock-label` - bottom navigation (replaces `btm-nav`)
- Hover 3D Card, Hover Gallery, Text Rotate, FAB/Speed Dial

### New modifiers
- `xl` size on all components
- `soft` style (muted background) on buttons, badges, alerts
- `dash` style (dashed border) on buttons, badges, alerts, cards
- Responsive modifier support on all component classes

### New theme variables
- `--depth` (0 or 1) - subtle shadow/depth
- `--noise` (0 or 1) - texture overlay

### New features
- `include` / `exclude` config for selective bundling
- Popover API support for dropdowns
- 3 new themes: caramellatte, abyss, silk

## Package Changes

- Zero npm dependencies (was ~100)
- 61% smaller npm package (4.7MB to 1.8MB)
- 75% smaller CDN (137kB to 34kB)
- ESM compatible, native CSS nesting
