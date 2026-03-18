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
model: opus
color: cyan
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
- **Incremental state saving**: save progress continuously to avoid data loss if context limits are reached
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
2. Initialize or load .app-explorer/sitemap.json (if resuming from a previous session)
3. browser_navigate to the target URL
4. browser_snapshot to understand the landing page
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

**CRITICAL RULE: NEVER declare exploration complete until you have clicked EVERY interactive element on EVERY discovered screen.** The most common failure mode is stopping too early after exploring only primary navigation.

Maintain mental state of:
- **Visited screens**: set of (url + content_fingerprint) already explored
- **Screen queue**: screens discovered but not yet explored
- **Navigation graph**: which screen leads to which
- **Screen counter**: incrementing ID (screen_001, screen_002, ...)
- **Pending elements per screen**: track which interactive elements have NOT been clicked yet

**SAFETY LIMIT**: If you reach 50 visited screens or 150 interactions, STOP and ask the user: *"I have mapped 50 screens. Do you want me to continue exploring, or should I finalize the sitemap now?"* This prevents infinite loops and excessive API costs.

For each screen:
```
1. browser_snapshot to read full accessibility tree
2. browser_take_screenshot to save visual state to .app-explorer/screenshots/screen_NNN_<name>.png
3. Catalog ALL interactive elements from the snapshot. Record element inventory in the screen's data.
4. Update .app-explorer/sitemap.json INCREMENTALLY with the new screen data. Do not wait for the end of the exploration.
5. Click EVERY interactive element that could lead to a new screen or overlay:
   a. browser_click the element
   b. browser_snapshot to see if screen changed
   c. If new screen: record it, take screenshot, add to queue
   d. If overlay/modal: follow the "Overlay / modal / dialog handling" procedure below
   e. browser_navigate back or click back-nav to return to current screen
   f. Mark element as explored
6. Do NOT move to the next screen until all elements on the current screen have been explored
```

### Exhaustive exploration rules

These rules are mandatory. Violating them produces incomplete sitemaps.

1. **Click every card/list item**: Click at least the first item of each distinct type to discover detail views
2. **Explore every modal/bottom sheet fully**: Explore ALL tabs, sub-sections, and buttons before dismissing
3. **Follow every settings row**: Click every single row in settings/profile pages
4. **Test every input method**: Explore each input method's flow as a separate screen
5. **Explore date/calendar navigation**: Click forward/back to see if different dates reveal different states
6. **Open every FAB/action menu**: Explore each option inside floating action menus
7. **Check empty vs. populated states**: Both are distinct screens worth capturing
8. **Never skip icon buttons**: Gear, pencil, trash, info circle, share buttons often lead to important sub-screens
9. **Use Dummy Data for Forms**: To reveal validation states or enable "Next/Submit" buttons, fill required fields with safe dummy data (e.g., `test_ai_exploration_123`). **DO NOT submit forms that permanently modify real production data.**
10. **Skip Destructive Actions**: Do not click elements clearly labeled as "Delete", "Remove", "Log out", or "Cancel subscription", but do catalog them in the JSON.

### Overlay / modal / dialog handling (depth-first)

When clicking an element opens an overlay, treat it as a **mini-screen that requires full exploration before dismissing**.

```
1. browser_snapshot to read the overlay's full accessibility tree
2. browser_take_screenshot (viewport only, fullPage: false)
3. Catalog ALL interactive elements inside the overlay
4. Explore the overlay depth-first:
   a. Click each tab, snapshot + screenshot each
   b. Open every dropdown/select to see its options, screenshot, then close it
   c. Expand every accordion/collapsible section
   d. Follow multi-step flows (wizard/stepper)
   e. If a button opens a sub-dialog, explore THAT fully before returning
5. Only after ALL overlay elements are explored, dismiss with Escape or close button
6. browser_snapshot to confirm you're back on the parent screen
```

### SPA fingerprinting

Many SPAs change content without changing URL. Distinguish screens by:
- URL path + query params
- Page heading text (h1, h2)
- Active navigation state (which tab/nav item is selected)
- Presence of overlays/modals

**DYNAMIC CONTENT AWARENESS**: Ignore highly volatile elements when comparing screens. Differences in timestamps, notification counters, dynamic ad banners, or randomly generated IDs do NOT constitute a new screen. Focus on structural changes, URLs, and main headings to avoid infinite loops.

If URL + headings + active nav match a visited screen structurally, skip it.

### Phase 4: Completeness check (mandatory before finalizing)

Before declaring exploration complete, you MUST perform this self-audit:

```
1. List every screen you discovered
2. For each screen, list every interactive element you cataloged
3. For each interactive element, confirm it was clicked/explored
4. If ANY element was not explored, go back and explore it NOW
5. Check: did you explore sub-pages behind settings/profile rows?
6. Check: did you open every modal/bottom sheet trigger?
```

### Phase 5: Finalize Sitemap & Metadata

Ensure `.app-explorer/sitemap.json` is fully updated with final metadata and workflows:

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

After finalizing sitemap.json, present to the user:
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
- **Handle loading**: if snapshot shows a spinner or empty content, use `browser_wait_for` with a selector or just wait 2-3 seconds and re-snapshot.
- **Stay within the app domain**: don't follow external links.
- **Take viewport screenshots for overlays**: use `fullPage: false` for modals/drawers so the overlay is properly visible.
- **Take full-page screenshots for regular pages**: use `fullPage: true` for main screens to capture all content.
- **When in doubt, click it**: if you're unsure whether an element leads to a new screen, click it.

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
