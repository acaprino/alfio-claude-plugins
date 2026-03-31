# App Analyzer Plugin

> Comprehensive app analysis for Android (ADB) and web (Playwright MCP). Auto-detects platform. Phase 1 maps the full navigation structure with exhaustive BFS exploration. Phase 2 analyzes design system, UX patterns, psychology, business model, and generates competitive intelligence reports.

## Agents

### `app-analyzer`

Unified app analysis agent that auto-detects platform and runs a two-phase analysis pipeline.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Competitor app analysis, navigation mapping, design system extraction, UX audits |

**Invocation:**
```
Use the app-analyzer agent to analyze [app name or URL]
```

**Phase 1: Navigation Mapping**
- Exhaustive BFS exploration of all screens
- Platform-specific operations (ADB for Android, Playwright MCP for web)
- Screenshots, UI hierarchy dumps, and navigation flow documentation
- User can stop after Phase 1

**Phase 2: Competitive Intelligence**
- Design system extraction (colors, typography, spacing, components)
- UX pattern analysis and psychology
- Business model intelligence
- Structured report generation

**Supported platforms:**

| Operation | ADB (Android) | Playwright MCP (Web) |
|-----------|---------------|---------------------|
| Screenshots | `adb exec-out screencap` | `playwright_screenshot` |
| Navigation | `adb shell input tap` | `playwright_click` |
| UI hierarchy | `adb shell uiautomator dump` | DOM inspection |

---

**Related:** [playwright-skill](playwright-skill.md) (optional dependency for web app exploration) | [agent-teams](agent-teams.md) (`/team-spawn app-analysis` uses this plugin) | [tauri-development](tauri-development.md) (scaffolds Tauri 2 mobile apps from analysis output)
