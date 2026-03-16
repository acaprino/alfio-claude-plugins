# Mobile Development Plugin

> Know your competition inside out. Automated Android app analysis via ADB -- navigate, screenshot, and document UX/UI patterns into comprehensive competitive reports.

## Skills

### `analyze-mobile-app`

Mobile app competitive analyzer with automated ADB-based navigation, screenshot capture, and report generation.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | Competitor app analysis, mobile UX review, Android app documentation |

**Workflow:**
1. **Setup** - Verify ADB connection, get device info, identify current app
2. **Main loop** - For each screen: screenshot, analyze visually, dump UI hierarchy, document patterns
3. **Report** - Generate structured analysis with screenshots

**Output files:**
- `docs/{APP}_ANALYSIS.md` - Detailed analysis
- `docs/{APP}_REPORT.html` - Visual HTML report
- `docs/{APP}_USER_FLOWS.md` - User flow documentation
- `img/*.png` - Captured screenshots

**Prerequisites:** ADB installed and an Android device/emulator connected.

---

**Related:** [workflows](workflows.md) (`/mobile-intel` and `/mobile-tauri-pipeline` use this skill) | [tauri-development](tauri-development.md) (scaffolds Tauri 2 mobile apps from analysis output)
