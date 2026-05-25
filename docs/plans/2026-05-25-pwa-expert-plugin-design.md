# pwa-expert plugin design

**Date:** 2026-05-25
**Status:** Approved (brainstorming phase complete, ready for implementation plan)
**Source material:** `C:\Users\alfio\Desktop\compass_artifact_wf-4c017345-0fb2-4075-a6b4-ace5bd05278e_text_markdown.md` (1172-line PWA implementation guide for 2025-2026, in Italian)

## Goal

Add a new marketplace plugin `pwa-expert` that turns the source guide into a production-ready, auto-activating Claude Code capability. The plugin must let a developer go from "I want to ship a PWA" to a working manifest, service worker, push pipeline, and store distribution package without leaving the Claude session, while also auditing existing PWAs against the 2025-2026 best-practice surface.

## Scope

Covered:

1. Web App Manifest including the modern members (`id`, `display_override`, `scope_extensions`, `handle_links`, `launch_handler`, `file_handlers`, `protocol_handlers`, `share_target`, `edge_side_panel`)
2. Service Workers (lifecycle, caching strategies via the Offline Cookbook taxonomy, Workbox 7, Serwist for Next.js, `skipWaiting` / `clients.claim` pitfalls)
3. Background execution (Background Sync, Periodic Background Sync, Background Fetch, Screen Wake Lock) and the iOS gaps
4. Web Push end-to-end (VAPID, RFC 8030 / 8291 / 8292 / 8188, subscription lifecycle, Declarative Web Push in Safari 18.4, Badge API)
5. Install flows (`beforeinstallprompt`, iOS manual install hint, Window Controls Overlay, `getInstalledRelatedApps`)
6. Storage (IndexedDB, OPFS, Cache API, quota and eviction across browsers, `navigator.storage.persist()`)
7. Project Fugu capability matrix (File System Access, Web Share, Web Bluetooth/USB/HID/Serial/NFC, WebAuthn, etc.)
8. Platform constraints (iOS WebKit, Android WebAPK + TWA, Desktop Chrome/Edge/Safari/Firefox)
9. Core Web Vitals 2025 (INP < 200 ms replacement of FID since March 2024)
10. Security (HTTPS, CSP, COOP/COEP, Permissions-Policy)
11. Distribution (Bubblewrap to Google Play, PWA Builder to Microsoft Store, Capacitor to App Store, PWA Builder to Meta Quest)
12. Framework integration (Vite via `vite-plugin-pwa`, Next.js via `@serwist/next`, Angular via `@angular/pwa`, Nuxt via `@vite-pwa/nuxt`)
13. Debugging and observability (Chrome DevTools, Safari Web Inspector limitations on standalone PWAs, in-app diagnostics fallback)

Not covered (intentional, route elsewhere):

- Generic React performance work (route to `react-development:review-react`)
- Generic frontend styling and design systems (route to `frontend`)
- Cross-platform security review beyond PWA specifics (route to `platform-engineering`)
- Tauri or Electron desktop wrappers (route to `tauri-development`)
- GA4 / analytics implementation (route to `digital-marketing:ga4-implementation-expert`)

## Approved decisions (from brainstorming questions)

| Dimension | Decision |
|---|---|
| Plugin shape | Full pipeline: architect agent + audit command + scaffold command + checklist command + knowledge skill |
| Language | English for all plugin-facing strings, frontmatter, trigger keywords, agent prompts, SKILL.md prose. Source Italian prose translated to English in references; technical terms and code samples preserved verbatim. |
| Audit scope | Hybrid: local code analysis when arg is a path, live URL via Playwright when arg is a URL |
| Agent count | 1 architect agent (`pwa-architect`) covering the full domain |
| Scaffold scope | Manifest + service worker + iOS meta tags + framework wiring with auto-detection of Vite, Next.js, Angular, Nuxt, or vanilla |

## Plugin layout

```
plugins/pwa-expert/
  agents/
    pwa-architect.md
  commands/
    pwa-audit.md
    pwa-scaffold.md
    pwa-checklist.md
  skills/
    pwa-development/
      SKILL.md
      references/
        manifest.md
        service-workers.md
        background-execution.md
        push-notifications.md
        install-flows.md
        permissions.md
        storage-persistence.md
        capabilities-fugu.md
        platform-constraints.md
        performance.md
        security.md
        distribution.md
        frameworks-tooling.md
        production-checklist.md
```

14 files in the skill folder (SKILL.md + 13 references). One agent, three commands. Total new files: 18.

## Component specifications

### Agent: `pwa-architect`

- **Frontmatter:** `name: pwa-architect`, multiline `description: >` with TRIGGER WHEN / DO NOT TRIGGER WHEN, `model: opus`, `color: cyan`, `tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch`.
- **TRIGGER WHEN:** building, implementing, designing, coding, or creating PWAs (manifest, service worker, Workbox / Serwist, Web Push with VAPID, Background Sync, install flow, OPFS storage, framework integration via Vite / Next.js / Angular / Nuxt, distribution via Bubblewrap / PWA Builder / Capacitor).
- **DO NOT TRIGGER WHEN:** generic frontend styling or design systems (use `frontend`), generic React performance (use `react-development:review-react`), cross-platform security review beyond PWA specifics (use `platform-engineering`), Tauri or Electron desktop wrappers (use `tauri-development`), GA4 / analytics work (use `digital-marketing:ga4-implementation-expert`).
- **Body structure:**
  - `# pwa-architect`
  - `## Role` (one short paragraph stating expertise: PWA architecture 2025-2026)
  - `## Core Knowledge` (terse keyword list of domain areas)
  - `## References Library` (lists every reference file in the skill with a one-line topic description; explicit instruction to read on-demand, not preload)
  - `## Workflow` (numbered steps: assess target browsers, design manifest, choose SW strategy, plan push, plan distribution)
  - `## Output Standards` (what a good deliverable looks like: complete manifest with `id` + `display_override` + `icons` 192/512 any+maskable, SW with versioned cache name, iOS meta tag block, registration code wired to entry point)
  - `## Routing` (when to delegate: frontend, react-development, platform-engineering, tauri-development)
- **Target length:** approximately 200 to 250 lines (in the band of `ibkr-architect` and `rag-architect`).

### Skill: `pwa-development`

SKILL.md frontmatter: `name: pwa-development`, multiline description with TRIGGER WHEN / DO NOT TRIGGER WHEN routing.

SKILL.md body (router):

- Short purpose paragraph
- "When to use this skill" with TRIGGER WHEN / DO NOT TRIGGER WHEN that mirrors the agent
- `## References Library` table indexing every reference file with a one-line topic summary
- `## How to use this skill` paragraph stating that references are read on-demand based on the active task, never preloaded all upfront

Reference files (13), each a focused document of approximately 300 to 700 lines:

1. **`manifest.md`** — every manifest member, the modern 2024-2025 members (`scope_extensions`, `handle_links`, `launch_handler`, `file_handlers`, `protocol_handlers`, `share_target`, `edge_side_panel`), icon strategy (192 + 512 PNG `any` and `maskable` as separate assets, the 40 percent safe-zone rule, iOS `apple-touch-icon` precedence), splash screen across Android and iOS, the iOS meta tag block. Includes the complete worked example from source section 1.2.
2. **`service-workers.md`** — lifecycle events, registration with scope rules, the five Offline Cookbook strategies in a decision table, Workbox 7 worked example, update flow with `workbox-window`, cache busting and breaking changes, propagation timing per browser, `skipWaiting` / `clients.claim` pitfalls per Jake Archibald.
3. **`background-execution.md`** — taxonomy of Web Worker vs Shared Worker vs Service Worker, Background Sync one-shot, Periodic Background Sync with engagement-score caveat, Background Fetch for long downloads, Screen Wake Lock with the iOS 18.4 fix for Home Screen Web Apps.
4. **`push-notifications.md`** — full Web Push pipeline: VAPID key generation, client subscription with `userVisibleOnly: true`, Node server with `web-push`, SW handler with actions and badges, Declarative Web Push in Safari 18.4 (no SW required), iOS-specific gotchas (install required, user gesture required, silent subscription loss), Badge API, full RFC reading order (8030 then Push API then 8292 then 8291 + 8188).
5. **`install-flows.md`** — Chromium install criteria including the 30-second engagement bar, `beforeinstallprompt` deferred-prompt pattern, `appinstalled` event, iOS manual install banner gated on `@media (display-mode: browser)`, `getInstalledRelatedApps()`, Window Controls Overlay manifest + CSS env vars + `geometrychange` event.
6. **`permissions.md`** — Permissions API query pattern, full list of permission names, best practices (never ask at page load, always provide rationale UI, gesture-required prompts on iOS), Permissions-Policy header, platform differences in availability.
7. **`storage-persistence.md`** — endpoint table (`localStorage`, `sessionStorage`, cookies, IndexedDB, Cache API, OPFS), IndexedDB with `idb` plus Dexie alternative, OPFS sync-access in worker, quota and eviction per browser (Chromium 60 percent disk, Firefox 10 percent best-effort and 50 percent persistent, Safari 60 percent disk on 17+ with notification-permission gate), Safari ITP 7-day cap on non-installed PWAs, `navigator.storage.persist()`.
8. **`capabilities-fugu.md`** — full Project Fugu API matrix as a cross-browser table, worked examples for Web Share / Web Share Target / Contact Picker, WebAuthn passkey creation, File System Access (`showOpenFilePicker`), Web Bluetooth / USB / HID / Serial / NFC platform notes, links to Fugu API Tracker and Chrome Capabilities status.
9. **`platform-constraints.md`** — per-platform reality check: iOS / iPadOS (WebKit obligated, install only manual, no Background Sync / Periodic Background Sync / Background Fetch / Web Bluetooth / USB / HID / Serial / NFC, Web Push only for installed standalone apps from iOS 16.4, Safari 18.4 brought Declarative Push and Wake Lock fix, DMA UE reversal context), Android Chrome (WebAPK, TWA, all capabilities), Desktop Chrome / Edge / Safari macOS / Firefox (and the 2020-2025 Firefox PWA history).
10. **`performance.md`** — Core Web Vitals 2025 thresholds (LCP < 2.5s, INP < 200ms, CLS < 0.1 at p75), INP replaced FID on March 12 2024, techniques (App Shell, `<link rel="preload">`, route-based code splitting, `fetchpriority="high"` on LCP image, `content-visibility: auto`, `scheduler.yield()` for INP), audit tooling (Lighthouse 12.0.0 removed the PWA category in Chrome 126, PWA Builder, WebPageTest, CrUX).
11. **`security.md`** — HTTPS as a hard requirement for service workers (localhost excepted), restrictive CSP example tuned for service workers and WebAssembly, COOP / COEP for `SharedArrayBuffer` (needed for sqlite-wasm on OPFS), secure context list per API, Permissions-Policy.
12. **`distribution.md`** — Bubblewrap to Google Play (with `/.well-known/assetlinks.json` requirement, otherwise the TWA degrades to a Custom Tab with visible URL bar), PWA Builder to Microsoft Store via MSIX, Apple App Store via Capacitor wrapper (Apple Guideline 4.2.2 blocks pure web clippings), PWA Builder to Meta Quest.
13. **`frameworks-tooling.md`** — Vite `vite-plugin-pwa` v1.3.0 with Node 20.19+ / Vite 7+ requirement, Next.js `@serwist/next` (and the abandonment of `next-pwa`), Angular `@angular/pwa` schematic, Nuxt `@vite-pwa/nuxt`, Capacitor wrapping, plus the debugging surface (Chrome DevTools Application panel, Background Services up-to-3-days recording, the Safari Web Inspector limitation on standalone PWAs and the Eruda / hidden-tap diagnostic fallback).
14. **`production-checklist.md`** — the full deploy checklist from source section 17 (Manifest, iOS, Service Worker, Security, Performance, Push, Storage, Testing, Distribution, Monitoring) with each box as an actionable verification step. Distinct from the audit command in that this is a static reference; the command walks the checklist interactively.

### Command: `/pwa-expert:pwa-audit`

- **`argument-hint:`** `[path | URL]`
- **Behavior:** auto-detect mode from the argument.
  - If the argument starts with `http://` or `https://`, run live mode via the `playwright-skill` tools. Fetch the manifest, parse it, test install criteria (manifest valid + service worker registered with `fetch` handler + HTTPS + the icons rule), check meta tags, measure Core Web Vitals on the landing page, and test offline behavior by going offline mid-navigation.
  - Otherwise, run local mode. Find the manifest file (`manifest.webmanifest` or `manifest.json`), find the service worker source, find the registration call, find the iOS meta tag block, find the security headers if available (`next.config.*`, `vite.config.*`, `.htaccess`, `nginx.conf` snippets when present). Parse and check.
- **Output:** prioritized markdown report with three severity buckets (Critical, Important, Nice-to-have), each finding paired with a code citation (`file:line` for local mode, URL fragment for live mode) and a concrete fix.
- **Approach:** the command file is a prompt for `pwa-architect` to follow. Includes a structured checklist of what to verify in each mode, and explicit guidance to load the relevant reference files on-demand (not all upfront).

### Command: `/pwa-expert:pwa-scaffold`

- **`argument-hint:`** `[framework]` (optional, auto-detected if omitted)
- **Behavior:** detect the framework via the presence of `vite.config.*`, `next.config.*`, `angular.json`, `nuxt.config.*`, or `package.json` deps. If none is detected, ask the user via `AskUserQuestion` which framework to target (Vite, Next.js, Angular, Nuxt, vanilla).
- **Generated artifacts:**
  - `manifest.webmanifest` with `id`, `name`, `short_name`, `description`, `start_url`, `scope`, `display`, `display_override` including `window-controls-overlay`, `theme_color`, `background_color`, icons (192 PNG `any`, 512 PNG `any`, 192 PNG `maskable`, 512 PNG `maskable`, optional SVG `any`), screenshots (one wide and one narrow stub), at least two shortcuts. Asks the user for the app name, theme color, and primary shortcuts up front via `AskUserQuestion`.
  - Service worker: Workbox 7 patterns by default. For Next.js, use Serwist via `@serwist/next` and place the SW at `app/sw.ts`. For Angular, prefer running `ng add @angular/pwa` instead of hand-writing the SW (the command instructs Claude to run the schematic).
  - iOS meta tag block: full `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, `apple-mobile-web-app-title`, `apple-touch-icon` 180x180, `theme-color`, `viewport-fit=cover`. Inserts into the framework's HTML entry point.
  - Service worker registration code wired into the framework's entry point (main.ts, app/layout.tsx, app.component.ts).
  - `headers-recommendations.md` next to the generated files: recommended HSTS, CSP, Permissions-Policy, COOP, COEP, and `Cache-Control: no-cache` for the service worker file. Not auto-applied to deploy config, given the framework variance, but documented inline.
  - Icon stubs (`/icons/icon-192.png`, `/icons/icon-512.png`, etc.) as empty placeholder files with a `README.md` in `/icons/` explaining the required dimensions and the maskable safe-zone rule. The user replaces these with real icons.
- **Idempotency:** if any artifact already exists, the command shows a diff and asks for confirmation per file before overwriting. Never silently overwrites existing manifests or service workers.

### Command: `/pwa-expert:pwa-checklist`

- **`argument-hint:`** `[path]` (optional, defaults to current working directory)
- **Behavior:** walks the production deploy checklist from the source guide's section 17 interactively. For each category (Manifest, iOS, Service Worker, Security, Performance, Push, Storage, Testing, Distribution, Monitoring), inspects the codebase (and optionally the deployed URL if provided) and reports pass / fail / not-applicable per item.
- **Difference from `pwa-audit`:** `pwa-audit` is open-ended and adversarial (finds defects). `pwa-checklist` is structured against a fixed checklist verbatim and produces a deterministic pass/fail dashboard that maps 1:1 to the source guide's checklist sections.
- **Output:** markdown report with per-category percentage and the full item list with status icons (textual only, no emojis).

## Marketplace registration

Add a single entry to `.claude-plugin/marketplace.json` under `plugins[]`:

```json
{
  "name": "pwa-expert",
  "source": "./plugins/pwa-expert",
  "description": "Progressive Web App expert covering manifest, service workers (Workbox 7 / Serwist), Web Push (VAPID, Declarative Push), install flows, OPFS storage, Project Fugu capabilities, Core Web Vitals, and distribution (Bubblewrap, PWA Builder, Capacitor). 2025-2026 baseline.",
  "version": "1.0.0",
  "author": "Alfio Caprino",
  "license": "MIT",
  "keywords": [
    "pwa", "progressive-web-app", "service-worker", "manifest",
    "web-push", "vapid", "workbox", "serwist",
    "offline", "installable", "bubblewrap", "twa", "capacitor",
    "opfs", "indexeddb", "background-sync", "wake-lock",
    "window-controls-overlay", "fugu", "ios-safari", "webapk"
  ],
  "category": "frontend",
  "strict": true,
  "agents": "./agents",
  "skills": "./skills",
  "commands": "./commands",
  "optionalDependencies": ["playwright-skill"]
}
```

Bump `metadata.version` by a minor increment (intake of a new plugin).

## License and attribution

The source markdown file is user-provided material (lives on the user's desktop, not an external public repo). It does NOT trigger the External-repository intake workflow from CLAUDE.md, so no attribution headers are required in derived files. Plugin license is MIT to match the marketplace default.

## Style and convention compliance

- All plugin-facing strings in English (matches the marketplace convention used by the other 43 plugins).
- Italian prose from the source guide is translated to English in references. Technical terms (VAPID, Service Worker, Manifest, OPFS, INP, LCP, CLS) stay in English. Code samples are preserved verbatim including comments, except that Italian inline comments are translated to English to keep the references monolingual.
- No dash-aside construct anywhere (per CLAUDE.md). The source guide uses the construct heavily; every aside is rewritten to a separate sentence, parenthesis, or colon.
- No emojis in any plugin file. The source guide has none, so this is straightforward.
- Agent frontmatter uses multiline `description: >` with explicit TRIGGER WHEN / DO NOT TRIGGER WHEN to maximize auto-activation accuracy.
- Files follow kebab-case naming.
- SKILL.md description respects the 1024-character limit (per the auto-memory rule about Anthropic Skills Guide).
- No README inside the skill folder (per the same rule).

## Risks and open considerations

1. **Source guide is in Italian.** Translation must be faithful but English-idiomatic. Risk: losing nuance on phrases like "best-effort", "PWA isolata", "engagement score". Mitigation: translate by topic, not line-by-line, and keep technical terms in their canonical English form.
2. **Source guide cites versioned facts** (Safari 18.4 dates, Firefox 143 reintroduction, Lighthouse 12.0.0 PWA-category removal in Chrome 126). These facts are stable as of the source date but will drift. Mitigation: the plugin falls under "Fast" risk class in the Custom plugin maintenance rubric (6-month refresh cadence) and is tracked accordingly. Add a row to the maintenance mental model when committing.
3. **`scope_extensions` is still origin-trial in some Chrome versions.** Mitigation: reference notes say to verify status on chromestatus.com before deploying.
4. **Live URL audit depends on Playwright.** Mitigation: declare `playwright-skill` as `optionalDependencies` in marketplace.json. The command must fail gracefully when Playwright is unavailable and fall back to suggesting manual checks.
5. **iOS PWA audits cannot use Safari Web Inspector** for standalone Home Screen Web Apps. The audit command must clearly note this limitation when the target is iOS, and suggest the Eruda or hidden-tap diagnostic pattern from the source guide's section 14.
6. **`pwa-scaffold` for Angular** runs the `ng add @angular/pwa` schematic rather than hand-writing the SW. This requires `Bash` tool access in the command's executor. Documented in the command file.

## Out of scope (deferred or rejected)

- Server-side push delivery as a generated artifact. The `push-notifications.md` reference includes a complete Node + `web-push` server example as a documentation snippet, but `pwa-scaffold` does NOT emit a server file. Users copy the example into their own backend.
- Capacitor scaffolding for App Store distribution. Capacitor is a separate ecosystem; the reference documents the option, but `pwa-scaffold` does not generate Capacitor projects (route the user to standalone Capacitor docs).
- Full Lighthouse CI integration. The audit command runs PWA-relevant checks itself; users who want CI Lighthouse should add Lighthouse CI to their pipeline directly.
- Storybook / component-library tooling. Out of PWA scope.

## Acceptance criteria

The implementation phase is complete when:

1. `plugins/pwa-expert/` exists with the file layout above (1 agent + 3 commands + 1 skill with 14 files).
2. `.claude-plugin/marketplace.json` registers `pwa-expert` and bumps `metadata.version`.
3. Agent and SKILL.md both have multiline `description: >` with TRIGGER WHEN / DO NOT TRIGGER WHEN.
4. Every reference file is between approximately 300 and 700 lines, focused on its topic, with at least one worked code example per major sub-topic.
5. No dash-aside construct anywhere in the plugin. No emojis.
6. `pwa-scaffold` correctly detects Vite, Next.js, Angular, and Nuxt, and falls back to vanilla. Generates the right SW pattern per framework.
7. `pwa-audit` correctly distinguishes path-arg from URL-arg and dispatches to local-mode or live-mode.
8. `pwa-checklist` walks the source guide's section 17 checklist verbatim and produces a per-category dashboard.
9. The CLAUDE.md "Custom plugin maintenance" section explicitly lists `pwa-expert` in the "Fast" freshness-class row of the example table (alongside `libgdx-development`, `opentelemetry`, `tauri-development`, `stripe`, `grabber-development`, `browser-extensions`), so the 6-month refresh cadence is discoverable from a single grep.
10. The plugin count in the CLAUDE.md "Project structure" paragraph is updated from 43 to 44, and `pwa-expert` is appended to the comma-separated plugin list there.
11. One commit bundles all new files, the marketplace.json update, and both CLAUDE.md edits; commit message follows the marketplace-update workflow.
