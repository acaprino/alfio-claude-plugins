---
name: app-explorer
description: >
  Automated webapp explorer that exhaustively crawls a local web application using Playwright
  BFS, mapping all screens, interactive elements, navigation flows, and user workflows into
  a structured JSON sitemap with per-screen screenshots. Captures 20+ element types including
  form fields, toggles, accordions, sliders, chips, cards, and generic clickables. Recursively
  explores modals, dialogs, drawers, and hamburger menus. Computes UX metrics: min clicks per
  destination, average depth, deepest screens, per-screen element summaries. Supports
  authenticated SPAs with session persistence and mobile viewport. Use when: analyzing webapp
  structure, documenting UI flows, preparing for visual analysis, mapping user workflows,
  auditing navigation complexity.
  Triggers: /app-explorer, "explore my app", "map the webapp", "analyze app structure",
  "crawl my frontend", "mappa la webapp", "esplora l'app".
---

# app-explorer

Crawls a local webapp and produces `.app-explorer/sitemap.json` + screenshots.

## Usage

```bash
# Step 1: ensure .app-explorer/ exists
mkdir -p .app-explorer/screenshots

# Step 2: run the crawler (browser will open - ask user to login if needed)
python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url <URL> \
  --output .app-explorer \
  --max-depth 5 \
  --max-screens 200

# Mobile viewport (default: on, 390x844)
python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url <URL> --output .app-explorer

# Custom viewport
python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url <URL> --output .app-explorer --width 1280 --height 800 --no-mobile

# Reuse auth from previous crawl (skip login)
python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url <URL> --output .app-explorer --auth .app-explorer/auth.json
```

Replace `{SKILL_BASE_DIR}` with the base directory shown at the top of this skill context.

### CLI flags

| Flag | Default | Description |
|---|---|---|
| `--url` | required | Starting URL |
| `--output` | `.app-explorer` | Output directory |
| `--max-depth` | `5` | Max BFS depth |
| `--max-screens` | `200` | Max screens to explore |
| `--mobile` | on | Mobile viewport with touch (390x844) |
| `--no-mobile` | - | Disable mobile viewport |
| `--width` | `390` | Viewport width |
| `--height` | `844` | Viewport height |
| `--auth` | none | Path to `auth.json` from previous crawl to skip login |
| `--thorough` | on | Exhaustive exploration: captures all 20+ element types, recursively explores modals/dialogs/drawers, detects generic clickables |
| `--no-thorough` | - | Fall back to basic detection (buttons, links, dropdowns, tabs, menu items, nav items only) |

## Workflow

1. Create `.app-explorer/` in the current working directory if it doesn't exist.
2. Run crawler.py with the target URL. The script:
   - Opens a **headed** (visible) browser with mobile viewport (390x844)
   - Navigates to the URL
   - Prints: `"Browser aperto. Effettua il login se necessario, poi premi Invio per avviare il crawl..."`
   - Waits for user to press Enter
   - Validates login succeeded (re-prompts if still on login page)
   - Saves auth state to `auth.json` for future reuse
   - Runs BFS crawl using the **post-login page** as root (preserves auth session)
   - Explores all pages, buttons, menus, modals, tabs, bottom navigation
   - With `--thorough` (default): captures 20+ element types, recursively explores overlays (up to depth 3), auto-detects hamburger/drawer menus with dedicated screenshots
   - Uses multi-signal fingerprinting (includes visible modals/dialogs/drawers) to distinguish SPA states with same URL
   - Saves a screenshot for every unique screen
   - Writes `.app-explorer/sitemap.json`
3. Confirm to user: `"Crawl completato. N schermate trovate. Sitemap in .app-explorer/sitemap.json"`
4. Read `sitemap.json` for downstream visual analysis or to answer structure/UX questions.

## SPA support

The crawler handles single-page applications with:
- **Auth session persistence**: saves browser storage state after login, uses current page as BFS root (no re-navigation that would lose auth)
- **Multi-signal fingerprinting**: combines URL + interactive labels + DOM headings + active tab state to distinguish pages with the same URL
- **Bottom navigation detection**: finds nav buttons, tab bars, and bottom nav components common in mobile SPAs
- **Recursive overlay exploration**: clicks elements inside modals, dialogs, and drawers to discover nested screens (depth up to 3); explores tabs, nav items, accordions inside overlays - not just buttons/links
- **Hamburger/drawer auto-detection**: identifies hamburger menu buttons and sidebar triggers, opens them, takes a dedicated viewport screenshot of the open drawer, then explores hidden navigation items
- **Viewport-aware screenshots**: uses viewport-only screenshots for overlays/dialogs/drawers (preserving mobile framing), full-page for regular screens
- **Button-opened pages queued for BFS**: when clicking a button navigates to a new URL (not just opening an overlay), that URL is enqueued for full BFS exploration of its own links and buttons
- **Overlay dismiss**: tries Escape, close button, then backdrop click to dismiss modals/sheets before continuing
- **Enhanced fingerprinting**: considers visible modals, dialogs, and drawers as part of the screen identity
- **Auth reuse**: `--auth auth.json` flag to skip login on subsequent crawls

## sitemap.json structure

```json
{
  "meta": { "app_url", "explored_at", "total_screens", "total_actions",
            "avg_clicks_to_reach_any_screen", "max_clicks_to_reach_any_screen",
            "deepest_screen": { "id", "title", "min_clicks" } },
  "screens": {
    "screen_001": {
      "id", "url", "title", "screenshot", "depth", "min_clicks_from_root",
      "path_from_root": [ { "step", "from_screen", "action", "label" } ],
      "reached_via",
      "elements": [ { "type", "label", "selector"/"href", "leads_to" } ],
      "element_summary": {
        "total_interactive": 42,
        "buttons": 8,
        "links": 12,
        "form_fields": 6,
        "toggles": 2,
        "accordions": 3,
        "..."
      }
    }
  },
  "navigation_graph": { "screen_id": ["screen_id", ...] },
  "workflows": [
    { "id", "destination_screen", "destination_title", "destination_url",
      "min_clicks", "steps": [ { "step", "screen", "title", "action" } ] }
  ]
}
```

## Element types captured

### Interactive elements (always detected)

| type | description |
|---|---|
| `button` | `<button>` with text/aria-label |
| `link` | Internal `<a href>` |
| `dropdown` | `<select>`, `[role=combobox]` with options |
| `tab` | `[role=tab]` |
| `menu_item` | `[role=menuitem]` |
| `nav_item` | Bottom nav / tab bar buttons |
| `modal_trigger` | Elements that open an overlay/modal |

### Thorough-mode element types (requires `--thorough`, default: on)

| type | description |
|---|---|
| `input` | Text, email, password, number, search, date, time, color, file inputs |
| `textarea` | Multiline text fields |
| `toggle` | Switches, checkboxes styled as toggles (`[role=switch]`) |
| `checkbox` | `input[type=checkbox]`, `[role=checkbox]` |
| `radio` | `input[type=radio]`, `[role=radio]` |
| `accordion` | Semantic accordions (`<details>`, `.accordion`, `[data-accordion]`) |
| `expandable` | Buttons with `[aria-expanded]` (non-accordion expandables) |
| `slider` | Range inputs, `[role=slider]` |
| `icon_button` | Buttons with only icons (no text), FABs |
| `chip` | Clickable chips, tags, badges |
| `card` | Clickable cards and list items |
| `drawer_trigger` | Hamburger menu buttons, sidebar triggers |
| `dialog_trigger` | Elements with `[aria-haspopup=dialog]` |
| `context_menu_trigger` | Elements with `[aria-haspopup=menu]` |
| `tree_item` | `[role=treeitem]` |
| `toolbar_button` | Buttons inside `[role=toolbar]` |
| `pagination` | Pagination links and steppers |
| `generic_clickable` | Any element with click handler or `cursor:pointer` not captured above |

## Phase 2: Visual analysis

After crawl, use `sitemap.json` as navigation map:
- Read `workflows` to find paths to any destination
- Use MCP Playwright tools to navigate to specific screens for visual inspection
- Answer UX questions: "what's the most hidden feature?", "how deep is the delete flow?"
