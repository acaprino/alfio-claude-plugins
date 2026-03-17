# Playwright Skill Plugin

> General-purpose browser automation with Playwright. Auto-detects dev servers, writes clean test scripts, supports responsive testing, login flows, form filling, link checking, and any browser task.

## Skills

### `playwright-skill`

Browser automation skill that writes custom Playwright code for any task and runs it via a universal executor.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | Testing a website, automating browser tasks, taking screenshots, checking links, responsive testing, login flow testing, form filling |

**Workflow:**
1. Auto-detect dev servers (localhost testing)
2. Write Playwright script to `/tmp`
3. Execute with visible or headless browser
4. Return results

**Capabilities:**
- Test pages, fill forms, take screenshots
- Check responsive design across viewports
- Validate UX and login flows
- Check links and navigation
- Run visible (headed) or headless

**Source:** Ported from [lackeyjb/playwright-skill](https://github.com/lackeyjb/playwright-skill).

**Includes:** `SKILL.md`, `API_REFERENCE.md`, `run.js` (executor), `package.json`, `lib/helpers.js` (dev server detection).

---

**Related:** [app-explorer](app-explorer.md) (depends on this for web app exploration) | [digital-marketing](digital-marketing.md) (optional dependency for SEO audits)
