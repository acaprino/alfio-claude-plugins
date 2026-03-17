# App Explorer Plugin

> Automated webapp explorer. Crawls a local web application with Playwright BFS, maps all screens, interactive elements, navigation flows, and user workflows, and outputs a structured JSON sitemap with per-screen screenshots.

## Skills

### `app-explorer`

Crawls local web applications via Playwright breadth-first search. Maps screens, interactive elements, and navigation flows into structured JSON with screenshots. Computes UX metrics: min clicks, average depth, deepest screens.

| | |
|---|---|
| **Trigger** | `/app-explorer`, "explore my app", "map the webapp", "crawl my frontend" |
| **Features** | Authenticated SPAs, session persistence, mobile viewport, per-screen screenshots |
| **Output** | JSON sitemap with UX metrics |

## Example: Exploring a remote authenticated SPA (mobile)

**Scenario**: Document the mobile layout of `https://app.kalo-ai.com`, a nutrition/meal-tracking PWA with email+password authentication.

### 1. Run the crawler

```bash
mkdir -p .app-explorer/screenshots

python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url https://app.kalo-ai.com \
  --output .app-explorer \
  --max-depth 5 \
  --max-screens 200
```

The crawler opens a headed mobile-viewport browser (390x844). It pauses at the login screen for the user to authenticate, then explores from the post-login page.

### 2. What the crawler found

**Kalo** is an Italian-language nutrition app with 4 main sections accessible via bottom navigation, plus a FAB-triggered dialog:

| Screen | URL | Depth | Key elements |
|---|---|---|---|
| Login | `/` | 0 | Email/password form, Google SSO, register link |
| Home | `/home` | 1 | Current meal card with ingredients/macros, daily progress ring, recent foods chips, supplements tracker |
| Diario | `/calendar` | 1 | Weekly day picker, personalized plan summary, meal list (Colazione/Pranzo/Spuntino/Cena), supplements |
| Stats | `/stats` | 1 | Streak counter, weekly overview chart, meal distribution donut, favorite foods, macro bars, activity heatmap |
| Profilo | `/settings` | 1 | User profile, plan settings (weight goal, nutritional targets, meal config, dietary preferences, supplements), app settings (theme, location), subscription management |
| Aggiungi cibo | `/home` (dialog) | 2 | Day/meal selector, input modes: Foto, Galleria, Testo, Voce |

### 3. Navigation structure

```
Login --> Home (via auth)
               |
               +-- Diario (bottom nav)
               +-- Stats (bottom nav)
               +-- Profilo (bottom nav)
               +-- Aggiungi cibo (FAB "+" button, bottom-sheet dialog)
```

All 4 main sections are reachable in 1 click from any other section via bottom navigation. The "Aggiungi cibo" dialog is 1 click from any section via the central FAB.

### 4. SPA characteristics observed

- **Horizontal swipe navigation**: sections slide horizontally (Home, Diario, Stats, Profilo render as adjacent panels)
- **Bottom-sheet dialogs**: "Aggiungi cibo" opens as a bottom sheet with blur backdrop
- **Auth-gated**: all routes redirect to `/` login if unauthenticated
- **Mobile-first**: designed for 390px viewport with touch targets, no desktop layout observed
- **Rich interactivity**: checkboxes for meal tracking, expandable meal cards, progress bars, chip-based quick-add for recent foods

### 5. Output files

```
.app-explorer/
  sitemap.json                          # Full structured sitemap
  auth.json                             # Saved auth state for reuse
  screenshots/
    01-home.png                         # Home screen (full page)
    02-diario.png                       # Diario/Calendar view
    03-stats.png                        # Statistics dashboard
    04-profilo.png                      # Profile/Settings
    05-aggiungi-cibo-dialog.png         # Add food dialog
```

### 6. Reuse auth for subsequent crawls

```bash
python "{SKILL_BASE_DIR}/scripts/crawler.py" \
  --url https://app.kalo-ai.com \
  --output .app-explorer \
  --auth .app-explorer/auth.json
```

---

**Related:** [playwright-skill](playwright-skill.md) (underlying browser automation) | [frontend](frontend.md) (UI redesign after mapping) | [workflows](workflows.md) (pipelines that use app exploration)
