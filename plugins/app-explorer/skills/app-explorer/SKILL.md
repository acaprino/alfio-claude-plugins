---
name: app-explorer
description: >
  Automated webapp explorer that crawls a local web application using Playwright BFS,
  mapping all screens, interactive elements, navigation flows, and user workflows into
  a structured JSON sitemap with per-screen screenshots. Computes UX metrics: min clicks
  per destination, average depth, deepest screens. Use when: analyzing webapp structure,
  documenting UI flows, preparing for visual analysis, mapping user workflows, auditing
  navigation complexity. Triggers: /app-explorer, "explore my app", "map the webapp",
  "analyze app structure", "crawl my frontend", "mappa la webapp", "esplora l'app".
---

# app-explorer

Crawls a local webapp and produces `.app-explorer/sitemap.json` + screenshots.

## Usage

```bash
# Step 1: ensure .app-explorer/ exists
mkdir -p .app-explorer/screenshots

# Step 2: run the crawler (browser will open — ask user to login if needed)
python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url <URL> \
  --output .app-explorer \
  --max-depth 5 \
  --max-screens 200
```

Replace `{SKILL_BASE_DIR}` with the base directory shown at the top of this skill context.

## Workflow

1. Create `.app-explorer/` in the current working directory if it doesn't exist.
2. Run crawler.py with the target URL. The script:
   - Opens a **headed** (visible) browser
   - Navigates to the URL
   - Prints: `"Browser aperto. Effettua il login se necessario, poi premi Invio per avviare il crawl..."`
   - Waits for user to press Enter
   - Runs BFS crawl across all pages, buttons, menus, modals, dropdowns, tabs
   - Saves a screenshot for every unique screen
   - Writes `.app-explorer/sitemap.json`
3. Confirm to user: `"Crawl completato. N schermate trovate. Sitemap in .app-explorer/sitemap.json"`
4. Read `sitemap.json` for downstream visual analysis or to answer structure/UX questions.

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
      "elements": [ { "type", "label", "selector"/"href", "leads_to" } ]
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

| type | description |
|---|---|
| `button` | `<button>` with text/aria-label |
| `link` | Internal `<a href>` |
| `dropdown` | `<select>`, `[role=combobox]` with options |
| `tab` | `[role=tab]` |
| `menu_item` | `[role=menuitem]` |
| `modal_trigger` | Elements that open an overlay/modal |

## Phase 2: Visual analysis

After crawl, use `sitemap.json` as navigation map:
- Read `workflows` to find paths to any destination
- Use MCP Playwright tools to navigate to specific screens for visual inspection
- Answer UX questions: "what's the most hidden feature?", "how deep is the delete flow?"
