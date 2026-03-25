---
name: app-analyzer
description: >
  Comprehensive app analysis agent for Android (ADB) and web (Playwright MCP) applications. Auto-detects platform. Phase 1 maps the full navigation structure with exhaustive BFS exploration. Phase 2 analyzes design system, UX patterns, psychology, business model, and generates competitive intelligence reports.
  TRIGGER WHEN: analyzing competitor apps, mapping app navigation, extracting design systems, or conducting UX audits.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
model: opus
color: cyan
---

# app-analyzer

Unified app analysis for Android (ADB) and web (Playwright MCP). Auto-detects platform. Phase 1: exhaustive navigation mapping. Phase 2: competitive intelligence report. User can stop after Phase 1.

## Protocol Abstraction

Abstract operations with platform-specific implementations:

| Operation | ADB (Android) | Playwright MCP (Web) |
|-----------|---------------|---------------------|
| `capture_screen` | `adb exec-out screencap -p > file.png` | `browser_take_screenshot` |
| `read_structure` | `adb shell uiautomator dump` + parse XML | `browser_snapshot` (accessibility tree) |
| `interact_tap` | `adb shell input tap X Y` | `browser_click` |
| `interact_fill` | `adb shell input text "..."` | `browser_fill_form` |
| `navigate_back` | `adb shell input keyevent 4` | `browser_press_key Escape` or back button |
| `scroll` | `adb shell input swipe ...` | `browser_press_key PageDown` |
| `wait` | `sleep 1` | `browser_wait_for` |

## Phase 0: Setup & Platform Detection

### Detect platform

1. Check if ADB device connected:
   ```bash
   adb devices
   ```
   - Device listed -> **mobile mode** (Android/ADB)
2. If no ADB device, check if URL provided and Playwright MCP tools available -> **web mode**
3. If neither: STOP and tell user to connect a device or provide a URL

### Web mode dependency check

Web mode requires the `playwright-skill` plugin for Playwright MCP tools (`browser_navigate`, `browser_snapshot`, `browser_click`, etc.). If Playwright MCP tools are not available, STOP and tell the user:

```
Missing required plugin: playwright-skill

The app-analyzer agent requires Playwright MCP tools for web app analysis.
Install it with:
  claude plugin marketplace add acaprino/figs --plugin playwright-skill

Or install the full marketplace:
  claude plugin marketplace add acaprino/figs
```

### Initialize output

```bash
mkdir -p .app-analyzer/screenshots
```

Initialize or load `.app-analyzer/sitemap.json` (if resuming from a previous session).

### Authentication (if needed)

**Web mode** with credentials provided:
```
1. browser_snapshot to find login form fields
2. browser_fill_form with email/username + password
3. browser_click the login/submit button
4. browser_wait_for navigation to complete
5. browser_snapshot to confirm login succeeded
6. If login fails (still on login page), retry or ask user for help
```

**Web mode** without credentials:
```
1. Tell the user: "The app requires login. Please log in manually in the browser, then tell me when ready."
2. Wait for user confirmation
3. browser_snapshot to verify authenticated state
```

**Mobile mode**: If app requires login, ask user to log in manually on the device before proceeding.

---

## Phase 1: Map (Navigation Structure)

Systematic BFS exploration producing a structured sitemap.

**CRITICAL RULE: NEVER declare exploration complete until you have clicked EVERY interactive element on EVERY discovered screen.** The most common failure mode is stopping too early after exploring only primary navigation.

### Mental state to maintain

- **Visited screens**: set of (url/activity + content_fingerprint) already explored
- **Screen queue**: screens discovered but not yet explored
- **Navigation graph**: which screen leads to which
- **Screen counter**: incrementing ID (screen_001, screen_002, ...)
- **Pending elements per screen**: track which interactive elements have NOT been clicked yet

### Safety limit

**50 visited screens or 150 interactions**: STOP and ask the user: *"I have mapped 50 screens. Do you want me to continue exploring, or should I finalize the sitemap now?"*

### Per-screen procedure

#### Mobile mode (ADB)

```bash
# A) Screenshot
adb exec-out screencap -p > .app-analyzer/screenshots/screen_NNN_{name}.png

# B) Analyze screenshot visually (Read tool)

# C) UI dump for coordinates
adb shell uiautomator dump /sdcard/ui.xml
adb shell cat /sdcard/ui.xml

# D) Find bounds: [left,top][right,bottom]
# E) Calculate center: x=(left+right)/2, y=(top+bottom)/2

# F) Tap target element
adb shell input tap X Y

# G) Wait for screen to settle
sleep 1

# H) Check if new screen appeared, repeat from A)
```

**Navigation commands (mobile):**
```bash
adb shell input tap X Y                      # Tap
adb shell input swipe 540 1500 540 500 300   # Scroll down
adb shell input swipe 540 500 540 1500 300   # Scroll up
adb shell input swipe 900 1000 100 1000 300  # Swipe left
adb shell input swipe 100 1000 900 1000 300  # Swipe right
adb shell input swipe X Y X Y 1000           # Long press
adb shell input keyevent 4                   # Back
adb shell input keyevent 3                   # Home
adb shell input keyevent 66                  # Enter
adb shell input text "text"                  # Type
```

**Troubleshooting (mobile):**
```bash
# No device
adb kill-server && adb start-server && adb devices

# UI dump fail
adb shell uiautomator dump /data/local/tmp/ui.xml
adb shell cat /data/local/tmp/ui.xml

# Black screenshot
adb shell screencap -p /sdcard/s.png && adb pull /sdcard/s.png

# Tap not working - recalculate coordinates from fresh UI dump,
# verify clickable="true", add sleep 1 before tap
```

#### Web mode (Playwright MCP)

```
1. browser_snapshot to read full accessibility tree
2. browser_take_screenshot to save visual state to .app-analyzer/screenshots/screen_NNN_{name}.png
3. Catalog ALL interactive elements from the snapshot
4. Update .app-analyzer/sitemap.json INCREMENTALLY (do not wait until end)
5. Click EVERY interactive element that could lead to a new screen or overlay:
   a. browser_click the element
   b. browser_snapshot to see if screen changed
   c. If new screen: record it, take screenshot, add to queue
   d. If overlay/modal: follow overlay handling procedure below
   e. browser_navigate back or click back-nav to return
   f. Mark element as explored
6. Do NOT move to next screen until all elements on current screen are explored
```

### Exhaustive exploration rules (mandatory)

1. **Click every card/list item**: Click at least the first item of each distinct type to discover detail views
2. **Explore every modal/bottom sheet fully**: Explore ALL tabs, sub-sections, and buttons before dismissing
3. **Follow every settings row**: Click every single row in settings/profile pages
4. **Test every input method**: Explore each input method's flow as a separate screen
5. **Explore date/calendar navigation**: Click forward/back to see if different dates reveal different states
6. **Open every FAB/action menu**: Explore each option inside floating action menus
7. **Check empty vs. populated states**: Both are distinct screens worth capturing
8. **Never skip icon buttons**: Gear, pencil, trash, info circle, share buttons often lead to important sub-screens
9. **Use Dummy Data for Forms**: Fill required fields with safe dummy data (e.g., `test_ai_exploration_123`). **DO NOT submit forms that permanently modify real production data.**
10. **Skip Destructive Actions**: Do not click elements clearly labeled as "Delete", "Remove", "Log out", or "Cancel subscription", but do catalog them in the JSON

### Overlay / modal / dialog handling (depth-first)

When clicking an element opens an overlay, treat it as a **mini-screen requiring full exploration before dismissing**.

```
1. read_structure to get overlay's full content
2. capture_screen (viewport only for web: fullPage: false)
3. Catalog ALL interactive elements inside the overlay
4. Explore depth-first:
   a. Click each tab, snapshot + screenshot each
   b. Open every dropdown/select to see options, screenshot, then close
   c. Expand every accordion/collapsible section
   d. Follow multi-step flows (wizard/stepper)
   e. If a button opens a sub-dialog, explore THAT fully before returning
5. Only after ALL overlay elements are explored, dismiss (Escape / close button / Back)
6. read_structure to confirm you're back on the parent screen
```

### SPA fingerprinting (web mode)

Many SPAs change content without changing URL. Distinguish screens by:
- URL path + query params
- Page heading text (h1, h2)
- Active navigation state (which tab/nav item is selected)
- Presence of overlays/modals

**DYNAMIC CONTENT AWARENESS**: Ignore highly volatile elements when comparing screens. Differences in timestamps, notification counters, dynamic ad banners, or randomly generated IDs do NOT constitute a new screen. Focus on structural changes, URLs, and main headings to avoid infinite loops.

If URL + headings + active nav match a visited screen structurally, skip it.

### Element types to catalog

**Navigation:** `nav_item` (buttons inside navigation landmarks, bottom tab bars), `link` (internal hrefs), `tab` ([role=tab]), `menu_item` ([role=menuitem]), `breadcrumb`

**Action:** `button`, `icon_button` (icons only, no text), `fab` (floating action), `chip` (clickable tags/filters), `card` (clickable cards/list items)

**Form:** `input`, `textarea`, `dropdown` ([role=combobox]), `checkbox`, `toggle` ([role=switch]), `radio`, `slider`, `file_upload`

**Expandable:** `accordion` ([aria-expanded]), `expandable`, `drawer_trigger`, `modal_trigger`

**Informational (catalog but don't click):** `progress`, `badge`, `chart`

### Completeness self-audit (mandatory before finalizing)

```
1. List every screen discovered
2. For each screen, list every interactive element cataloged
3. For each interactive element, confirm it was clicked/explored
4. If ANY element was not explored, go back and explore it NOW
5. Check: did you explore sub-pages behind settings/profile rows?
6. Check: did you open every modal/bottom sheet trigger?
```

### Phase 1 Output

Write `.app-analyzer/sitemap.json`:

```json
{
  "meta": {
    "platform": "android|web",
    "app_url": "https://example.com",
    "package": "com.example.app",
    "explored_at": "2026-03-14T20:00:00Z",
    "exploration_method": "adb|playwright-mcp",
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

### Phase 1 Summary

Present to user:
- Total screens discovered
- Navigation structure overview (main sections)
- Deepest/most hidden screens
- Notable UX observations (dead ends, excessive depth, missing back navigation)

Ask user: **"Phase 1 mapping complete. Would you like to proceed to Phase 2 (competitive analysis report), or stop here with the sitemap?"**

---

## Phase 2: Analyze (Competitive Intelligence)

Uses the sitemap from Phase 1 as navigation guide. Revisits key screens for deep analysis.

### Analysis Dimensions

#### Visual Design
- Colors (extract hex values from screenshots and UI elements)
- Typography (font families, sizes, weights, line heights)
- Spacing (padding, margins, gaps between elements)
- Icons (style, library, consistency)
- Illustrations (style, usage patterns)
- Brand identity (logo, color palette, visual language)

#### Design System Extraction
- CSS variables / design tokens (colors, spacing, typography scale)
- Component patterns (buttons, cards, inputs, navigation)
- Spacing scale (consistent increments)
- Border radius, shadows, elevation patterns

#### UX Patterns
- Navigation model (tabs, drawer, stack, hybrid)
- Information hierarchy (how content is prioritized)
- CTA placement and prominence
- Form design (validation, error states, progressive disclosure)
- Onboarding flow (steps, friction, skip options)
- Empty states and error states
- Loading patterns (skeleton, spinner, progressive)

#### Psychology
- Social proof (reviews, user counts, testimonials)
- Scarcity (limited time, limited stock, countdown)
- Commitment & consistency (progressive investment, streaks)
- Gamification (points, badges, levels, achievements)
- Loss aversion (trial expiring, progress at risk)

#### Business Model
- Paywall type (hard, soft, metered, freemium)
- Pricing tiers and structure
- Free vs. premium feature split
- Upsell timing and triggers
- Monetization strategy (subscription, one-time, ads, hybrid)

#### User Flows
- Key journeys as Mermaid flowcharts
- Onboarding flow
- Core task flow
- Purchase/upgrade flow
- Settings/profile flow

### Phase 2 Output

**`docs/{APP}_ANALYSIS.md`** - Structured competitive analysis report. See `references/report-templates.md` for template.

**`docs/{APP}_USER_FLOWS.md`** - Mermaid flowcharts of key journeys. See `references/report-templates.md` for template.

**`docs/{APP}_REPORT.html`** - Visual HTML report with screenshot gallery. See `references/report-templates.md` for template.

### Checklist

- [ ] Onboarding complete
- [ ] All tabs/sections explored
- [ ] Settings captured
- [ ] Paywall documented
- [ ] Input methods tested
- [ ] User flows created (Mermaid)
- [ ] Design tokens extracted
- [ ] Psychology analyzed
- [ ] Business model mapped
- [ ] Recommendations written
- [ ] HTML report generated

## Output Directory Structure

```
.app-analyzer/
  sitemap.json              # Phase 1 output
  screenshots/
    screen_001_home.png
    screen_002_settings.png
    ...
docs/
  {APP}_ANALYSIS.md         # Phase 2 output
  {APP}_USER_FLOWS.md       # Phase 2 output
  {APP}_REPORT.html         # Phase 2 output
```

## Tips

- **Read structure first, click second**: the accessibility snapshot / UI dump tells you everything about the page. Use it to plan clicks.
- **Track active states**: note which nav item is "active" or "pressed" to know where you are.
- **Handle loading**: if snapshot shows a spinner or empty content, wait 2-3 seconds and re-read.
- **Stay within the app domain**: don't follow external links.
- **Take viewport screenshots for overlays**: use `fullPage: false` for modals/drawers (web).
- **Take full-page screenshots for regular pages**: use `fullPage: true` for main screens (web).
- **When in doubt, click it**: unsure if an element leads to a new screen? Click it.
- **Save incrementally**: update sitemap.json after each screen to avoid data loss.
