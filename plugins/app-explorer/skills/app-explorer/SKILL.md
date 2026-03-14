---
name: app-explorer
description: >
  AI-driven webapp explorer using Playwright MCP tools for interactive, intelligent
  mapping of web applications. Navigates through login flows, SPAs, modals, drawers,
  and dynamic content by reading accessibility snapshots and making smart exploration
  decisions. Produces a structured JSON sitemap with per-screen screenshots, navigation
  graph, element inventory, and workflow paths. Handles authenticated apps by filling
  credentials and clicking through auth flows. Adapts in real-time to unexpected UI
  states, loading spinners, and complex navigation patterns that defeat automated crawlers.
  Triggers: /app-explorer, "explore my app", "map the webapp", "analyze app structure",
  "crawl my frontend", "mappa la webapp", "esplora l'app".
---

# app-explorer

Maps a web application interactively using Playwright MCP tools. The AI navigates, screenshots, and catalogs every screen - handling login, SPAs, modals, and dynamic content that automated crawlers cannot.

## Dependency: playwright-skill plugin

This skill requires the `playwright-skill` plugin to be installed for Playwright MCP tools (`browser_navigate`, `browser_snapshot`, `browser_click`, etc.). If Playwright MCP tools are not available, STOP and tell the user:

```
Missing required plugin: playwright-skill

The app-explorer skill requires Playwright MCP tools for browser automation.
Install it with:
  claude plugin marketplace add acaprino/anvil-toolset --plugin playwright-skill

Or install the full marketplace:
  claude plugin marketplace add acaprino/anvil-toolset
```

## Strategy: Playwright MCP (primary)

Use Playwright MCP tools directly. The AI controls the browser, reads accessibility snapshots, makes intelligent decisions about what to click/explore, and builds the sitemap incrementally.

### Why Playwright MCP over a crawler script

- **Login handling**: fill credentials, click buttons, handle MFA/captcha prompts, OAuth redirects
- **SPA intelligence**: the AI understands which navigation items lead to new screens vs. redundant views
- **Adaptive exploration**: skip loading states, wait for content, retry failed navigations
- **Interactive content**: open drawers, expand accordions, fill search fields, trigger modals
- **Real-time decisions**: prioritize unexplored areas, avoid infinite loops in dynamic lists

### Required MCP tools

| Tool | Purpose |
|---|---|
| `browser_navigate` | Go to URLs |
| `browser_snapshot` | Read accessibility tree (primary way to understand page) |
| `browser_click` | Click buttons, links, tabs, nav items |
| `browser_fill_form` | Fill login forms, search fields |
| `browser_take_screenshot` | Capture screen state to file |
| `browser_press_key` | Escape to dismiss overlays, Enter to submit |
| `browser_wait_for` | Wait for navigation, loading states |
| `browser_tabs` | Handle multi-tab scenarios |

## Exploration workflow

### Phase 1: Setup

```
1. mkdir -p .app-explorer/screenshots
2. browser_navigate to the target URL
3. browser_snapshot to understand the landing page
```

### Phase 2: Authentication (if needed)

When credentials are provided:
```
1. browser_snapshot to find login form fields
2. browser_fill_form with email/username + password
3. browser_click the login/submit button
4. browser_wait_for navigation to complete
5. browser_snapshot to confirm login succeeded
6. If login fails (still on login page), retry or ask user for help
```

When NO credentials are provided:
```
1. Tell the user: "The app requires login. Please log in manually in the browser, then tell me when ready."
2. Wait for user confirmation
3. browser_snapshot to verify authenticated state
```

### Phase 3: Systematic BFS exploration

**CRITICAL RULE: NEVER declare exploration complete until you have clicked EVERY interactive element on EVERY discovered screen.** The most common failure mode is stopping too early after exploring only primary navigation. An app with 4 nav tabs likely has 15-30+ screens when you also explore cards, buttons, modals, settings sub-pages, detail views, input flows, and contextual actions. If you have explored fewer than 10 screens for a non-trivial app, you are almost certainly not done.

Maintain mental state of:
- **Visited screens**: set of (url + content_fingerprint) already explored
- **Screen queue**: screens discovered but not yet explored
- **Navigation graph**: which screen leads to which
- **Screen counter**: incrementing ID (screen_001, screen_002, ...)
- **Pending elements per screen**: track which interactive elements have NOT been clicked yet

For each screen:
```
1. browser_snapshot to read full accessibility tree
2. browser_take_screenshot to save visual state to .app-explorer/screenshots/screen_NNN_<name>.png
3. Catalog ALL interactive elements from the snapshot:
   - Navigation items (bottom nav, sidebar, tab bars)
   - Buttons, links, tabs, menu items
   - Form fields (inputs, textareas, dropdowns, checkboxes, toggles)
   - Expandables (accordions, collapsibles)
   - Cards, chips, list items that appear clickable
   - Modal/drawer/dialog triggers
   - Icon buttons (edit, delete, settings, info, share, etc.)
   - FABs (floating action buttons)
4. Record element inventory in the screen's data
5. Click EVERY interactive element that could lead to a new screen or overlay:
   a. browser_click the element
   b. browser_snapshot to see if screen changed
   c. If new screen: record it, take screenshot, add to queue
   d. If overlay/modal: screenshot it, explore ALL its contents (tabs, buttons, sub-sections), then dismiss with Escape or close button
   e. browser_navigate back or click back-nav to return to current screen
   f. Mark element as explored
6. Do NOT move to the next screen until all elements on the current screen have been explored
```

### Exhaustive exploration rules

These rules are mandatory. Violating them produces incomplete sitemaps.

1. **Click every card/list item**: If a screen shows a list of items (meals, recipes, history entries, settings rows), click at least the first item of each distinct type to discover detail views
2. **Explore every modal/bottom sheet fully**: When a modal opens, it often contains tabs, sub-sections, or additional buttons. Explore ALL of them before dismissing
3. **Follow every settings row**: Settings/profile pages often have 5-15 sub-pages (account, notifications, goals, subscriptions, about, etc.). Click every single row
4. **Test every input method**: If the app offers multiple ways to do something (e.g., add via photo/text/voice/gallery), explore each input method's flow as a separate screen
5. **Explore date/calendar navigation**: Click forward/back on date selectors to see if different dates reveal different screen states
6. **Open every FAB/action menu**: Floating action buttons and "+" buttons often reveal multi-option menus. Explore each option
7. **Check empty vs. populated states**: If navigating to a section shows "no data" but another date/filter shows data, both are distinct screens worth capturing
8. **Never skip icon buttons**: Small icon buttons (gear, pencil, trash, info circle, share) frequently lead to important sub-screens or modals

### Exploration priorities

Explore in this order to maximize coverage efficiently:
1. **Primary navigation** - bottom nav tabs, sidebar menu items, top nav links
2. **Page-level actions** - prominent buttons ("View plan", "Add", "Settings")
3. **List items / cards** - tappable cards that lead to detail views
4. **Expandables** - accordions, collapsible sections
5. **Modal triggers** - buttons that open overlays, dialogs, bottom sheets
6. **Contextual actions** - icon buttons, kebab menus, swipe actions
7. **Pagination / date navigation** - week selectors, page controls (sample 1-2)
8. **Form interactions** - dropdowns to see options (don't submit forms)

### Overlay / modal handling

When clicking an element opens an overlay:
```
1. browser_snapshot to detect overlay content
2. browser_take_screenshot (viewport only, not full page)
3. Catalog overlay elements
4. If overlay has tabs/navigation, explore each tab
5. Dismiss: browser_press_key "Escape", or click close button
6. browser_snapshot to confirm overlay dismissed
```

### SPA fingerprinting

Many SPAs change content without changing URL. Distinguish screens by:
- URL path + query params
- Page heading text (h1, h2)
- Active navigation state (which tab/nav item is selected)
- Presence of overlays/modals
- Key content identifiers (list titles, section headers)

If URL + headings + active nav match a visited screen, skip it.

### Phase 4: Completeness check (mandatory before building sitemap)

Before declaring exploration complete, you MUST perform this self-audit:

```
1. List every screen you discovered
2. For each screen, list every interactive element you cataloged
3. For each interactive element, confirm it was clicked/explored
4. If ANY element was not explored, go back and explore it NOW
5. Check: did you explore sub-pages behind settings/profile rows?
6. Check: did you open every modal/bottom sheet trigger?
7. Check: did you click at least one item in every list/card grid?
8. Check: did you try every distinct input method or action type?
```

Only proceed to Phase 5 when ALL elements on ALL screens have been explored or explicitly skipped (with a documented reason, e.g., "destructive action", "external link", "logout").

### Phase 5: Build sitemap

After exploration is complete, create `.app-explorer/sitemap.json`:

```json
{
  "meta": {
    "app_url": "https://example.com",
    "explored_at": "2026-03-14T20:00:00Z",
    "exploration_method": "playwright-mcp",
    "total_screens": 12,
    "total_actions": 87,
    "avg_clicks_to_reach_any_screen": 1.8,
    "max_clicks_to_reach_any_screen": 4,
    "deepest_screen": { "id": "screen_009", "title": "Subscription Details", "min_clicks": 4 }
  },
  "screens": {
    "screen_001": {
      "id": "screen_001",
      "url": "/",
      "title": "Home",
      "screenshot": "screenshots/screen_001_home.png",
      "depth": 0,
      "min_clicks_from_root": 0,
      "path_from_root": [],
      "reached_via": "root",
      "elements": [
        { "type": "nav_item", "label": "Home", "leads_to": "screen_001" },
        { "type": "nav_item", "label": "Diary", "leads_to": "screen_002" },
        { "type": "button", "label": "Add meal", "leads_to": "screen_005" }
      ],
      "element_summary": {
        "total_interactive": 24,
        "buttons": 8,
        "links": 3,
        "nav_items": 4,
        "form_fields": 0,
        "cards": 5,
        "toggles": 0
      }
    }
  },
  "navigation_graph": {
    "screen_001": ["screen_002", "screen_003", "screen_004", "screen_005"],
    "screen_002": ["screen_001", "screen_006"]
  },
  "workflows": [
    {
      "id": "wf_001",
      "destination_screen": "screen_009",
      "destination_title": "Subscription Details",
      "destination_url": "/settings/subscription",
      "min_clicks": 4,
      "steps": [
        { "step": 1, "screen": "screen_001", "title": "Home", "action": "click 'Profile' nav" },
        { "step": 2, "screen": "screen_004", "title": "Profile", "action": "click 'Subscription'" },
        { "step": 3, "screen": "screen_009", "title": "Subscription Details", "action": "arrived" }
      ]
    }
  ]
}
```

### Phase 6: Summary report

After writing sitemap.json, present to the user:
- Total screens discovered
- Navigation structure overview (which main sections exist)
- Deepest/most hidden screens
- Notable UX observations (dead ends, excessive depth, missing back navigation)

## Element types to catalog

### Navigation elements
| type | what to look for in snapshot |
|---|---|
| `nav_item` | Buttons inside `navigation` landmarks, bottom tab bars |
| `link` | `<a>` elements with internal hrefs |
| `tab` | `[role=tab]` elements |
| `menu_item` | `[role=menuitem]` elements |
| `breadcrumb` | Navigation breadcrumbs |

### Action elements
| type | what to look for |
|---|---|
| `button` | `<button>` with visible text or aria-label |
| `icon_button` | Buttons with only icons (no text) |
| `fab` | Floating action buttons (typically centered bottom) |
| `chip` | Clickable chips, tags, filter pills |
| `card` | Clickable cards, list items with actions |

### Form elements
| type | what to look for |
|---|---|
| `input` | Text inputs, search fields, date pickers |
| `textarea` | Multiline text fields |
| `dropdown` | `<select>`, `[role=combobox]` |
| `checkbox` | Checkboxes, `[role=checkbox]` |
| `toggle` | Switches, `[role=switch]` |
| `radio` | Radio buttons, `[role=radio]` |
| `slider` | Range inputs, `[role=slider]` |
| `file_upload` | File input buttons |

### Expandable elements
| type | what to look for |
|---|---|
| `accordion` | `<details>`, `[aria-expanded]` sections |
| `expandable` | Collapsible sections, show/hide toggles |
| `drawer_trigger` | Hamburger menus, sidebar openers |
| `modal_trigger` | Buttons that open overlays/dialogs |

### Informational elements (catalog but don't click)
| type | what to look for |
|---|---|
| `progress` | Progress bars, circular progress |
| `badge` | Notification badges, status indicators |
| `chart` | Data visualizations |

## Tips for effective exploration

- **Read the snapshot first, click second**: the accessibility snapshot tells you everything about the page structure. Use it to plan your clicks.
- **Track active states**: note which nav item is "active" or "pressed" - this tells you where you are.
- **Don't click destructive actions**: skip "Delete", "Log out", "Cancel subscription" etc. But DO document them as elements.
- **Sample repetitive content**: if there are 50 list items of the same type, click 2-3 to see the detail view, then move on. But always click at least 2.
- **Handle loading**: if snapshot shows a spinner or empty content, use `browser_wait_for` with a selector or just wait 2-3 seconds and re-snapshot.
- **Stay within the app domain**: don't follow external links.
- **Take viewport screenshots for overlays**: use `fullPage: false` for modals/drawers so the overlay is properly visible.
- **Take full-page screenshots for regular pages**: use `fullPage: true` for main screens to capture all content.
- **When in doubt, click it**: if you're unsure whether an element leads to a new screen, click it. The cost of an extra click is much lower than the cost of missing a screen.
- **Never stop early**: finding 5-7 screens for a feature-rich app is a sign you haven't explored deeply enough. Keep going until you've exhausted all interactive paths.

## Fallback: Python crawler (optional)

For simple apps without login requirements or complex SPA behavior, the Python crawler script can be used as a fast automated alternative:

```bash
python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url <URL> \
  --output .app-explorer \
  --max-depth 5 \
  --max-screens 200
```

The crawler opens a headed browser, waits for manual login, then runs automated BFS. Use it only when:
- The app is a simple multi-page site (not an SPA)
- No programmatic login is needed
- Basic coverage is sufficient

For anything else, use the Playwright MCP approach above.

## Post-exploration: Visual analysis

After building the sitemap, use it as a navigation map for follow-up work:
- Read `workflows` to find paths to any destination
- Use Playwright MCP tools to revisit specific screens for detailed inspection
- Answer UX questions: "what's the most hidden feature?", "how deep is the delete flow?"
- Compare screen layouts, identify inconsistencies, audit accessibility
