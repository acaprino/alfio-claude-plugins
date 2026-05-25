# pwa-expert Plugin Implementation Plan

> **For agentic workers:** Use subagent-driven execution (if subagents available) or ai-tooling:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `pwa-expert` marketplace plugin that turns `C:\Users\alfio\Desktop\compass_artifact_wf-4c017345-0fb2-4075-a6b4-ace5bd05278e_text_markdown.md` (Italian PWA guide, 1172 lines) into an English, auto-activating Claude Code capability with one architect agent, three commands, and a 14-file knowledge skill.

**Architecture:** Single-agent + 3 commands + knowledge-base skill (pattern of `ibkr-trading`, `mt5-trading`, `rag-development`, with extra commands modeled on `digital-marketing:seo-audit` for the live-URL audit). All content is markdown. No build step, no runtime, no tests beyond `/marketplace-ops:skills-validate` and structural grep checks.

**Tech Stack:** Markdown only. Frontmatter: YAML. Plugin registered in `.claude-plugin/marketplace.json`.

**Source spec:** `docs/plans/2026-05-25-pwa-expert-plugin-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `plugins/pwa-expert/agents/pwa-architect.md` | Expert agent — frontmatter + system-prompt body for building PWAs end-to-end |
| `plugins/pwa-expert/commands/pwa-audit.md` | Slash command — hybrid local-code / live-URL audit |
| `plugins/pwa-expert/commands/pwa-scaffold.md` | Slash command — framework-aware scaffolding of manifest + SW + iOS meta tags |
| `plugins/pwa-expert/commands/pwa-checklist.md` | Slash command — walk the production deploy checklist interactively |
| `plugins/pwa-expert/skills/pwa-development/SKILL.md` | Knowledge-base router with TRIGGER WHEN / DO NOT TRIGGER WHEN and references index |
| `plugins/pwa-expert/skills/pwa-development/references/manifest.md` | Web App Manifest deep-dive (source §1) |
| `plugins/pwa-expert/skills/pwa-development/references/service-workers.md` | Service Worker lifecycle, Workbox 7, updates (source §2, §4) |
| `plugins/pwa-expert/skills/pwa-development/references/background-execution.md` | Background Sync, Periodic, Fetch, Wake Lock (source §3) |
| `plugins/pwa-expert/skills/pwa-development/references/push-notifications.md` | Web Push, VAPID, RFCs, Declarative Push (source §6) |
| `plugins/pwa-expert/skills/pwa-development/references/install-flows.md` | beforeinstallprompt, iOS manual, WCO (source §7) |
| `plugins/pwa-expert/skills/pwa-development/references/permissions.md` | Permissions API + Permissions-Policy (source §5) |
| `plugins/pwa-expert/skills/pwa-development/references/storage-persistence.md` | IndexedDB, OPFS, quotas (source §8) |
| `plugins/pwa-expert/skills/pwa-development/references/capabilities-fugu.md` | Project Fugu API matrix + examples (source §9) |
| `plugins/pwa-expert/skills/pwa-development/references/platform-constraints.md` | iOS / Android / Desktop per-platform reality (source §10) |
| `plugins/pwa-expert/skills/pwa-development/references/performance.md` | Core Web Vitals 2025, INP < 200ms (source §11) |
| `plugins/pwa-expert/skills/pwa-development/references/security.md` | HTTPS, CSP, COOP/COEP (source §12) |
| `plugins/pwa-expert/skills/pwa-development/references/distribution.md` | Bubblewrap, PWA Builder, Capacitor, Meta Quest (source §13) |
| `plugins/pwa-expert/skills/pwa-development/references/frameworks-tooling.md` | Vite, Next.js, Angular, Nuxt + debugging (source §14, §15) |
| `plugins/pwa-expert/skills/pwa-development/references/production-checklist.md` | Full deploy checklist (source §17) |
| `.claude-plugin/marketplace.json` | Plugin registration + `metadata.version` bump |
| `CLAUDE.md` | Plugin count 43→44, add `pwa-expert` to Fast freshness-class row |

---

## Pre-flight: source-document anchor map

When a task says "use source §N", the engineer reads that section of `C:\Users\alfio\Desktop\compass_artifact_wf-4c017345-0fb2-4075-a6b4-ace5bd05278e_text_markdown.md`:

| Source section | Title (Italian) | English topic |
|---|---|---|
| §1 | Web App Manifest | Manifest |
| §2 | Service Workers | Service Worker lifecycle, caching, Workbox |
| §3 | Background Workers e Esecuzione in Background | Background execution |
| §4 | Aggiornamenti e Versioning | SW updates, version skew |
| §5 | Permissions API | Permissions |
| §6 | Notifiche Push | Web Push (RFCs, VAPID, Declarative) |
| §7 | Installazione PWA | Install flows |
| §8 | Storage e Persistenza | Storage |
| §9 | Capabilities / API moderne (Project Fugu) | Fugu APIs |
| §10 | Limiti specifici per piattaforma | Platform constraints |
| §11 | Performance e Best Practices | Core Web Vitals 2025 |
| §12 | Sicurezza | HTTPS, CSP, COOP/COEP |
| §13 | Distribuzione | Store distribution |
| §14 | Debugging e Testing | DevTools + Safari Inspector limits |
| §15 | Framework e Tooling 2025-2026 | Vite, Next.js, Angular, Nuxt |
| §16 | Tendenze 2025-2026 | Trends (folded into platform-constraints and capabilities-fugu) |
| §17 | Checklist Deploy Production-Ready | Production checklist |

Each reference file is 300-700 lines of focused English prose with code examples preserved verbatim from the source. Italian inline comments inside code blocks are translated to English. Dash-aside constructs (`X — Y — Z`, `X -- Y -- Z`, `X - Y - Z` as bracketed asides) are rewritten to separate sentences, parentheses, or colons. No emojis.

---

## Universal verification snippet

Every file-creation task ends with this verification (saves repetition):

```bash
FILE="plugins/pwa-expert/<path>"
wc -l "$FILE"
# Check for forbidden dash-aside construct (em dash, double hyphen, spaced hyphen as parenthetical)
grep -nE ' — | -- | - ' "$FILE" | grep -v '^\s*[-*]' | head -20
# Check for emojis (rough Unicode range)
grep -nP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' "$FILE" | head -5
# Verify no Italian leftovers (common giveaway words)
grep -niE '\b(che|della|dello|delle|degli|sono|essere|questo|questa|quando|perché|anche|tutto|tutta|tutti)\b' "$FILE" | head -5
```

If any of those greps return content (other than legitimate hyphenated compounds like `file-handlers`), fix the file before committing.

---

### Task 1: Create plugin skeleton and the production-checklist reference

**Why first:** the checklist is the simplest reference (no narrative prose, just structured bullets) and validates the directory layout.

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/production-checklist.md`

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p plugins/pwa-expert/agents
mkdir -p plugins/pwa-expert/commands
mkdir -p plugins/pwa-expert/skills/pwa-development/references
```

- [ ] **Step 2: Write the production checklist**

Source: §17 of the source guide.

Structure the file as:

```markdown
# Production Deployment Checklist

Field-tested checklist for shipping a PWA to production in 2025-2026. Walk this before every release. Each item has a verification step and a reference to the relevant section of the knowledge base.

## How to use this checklist

Three pass criteria:
- PASS: requirement is met and verified
- FAIL: requirement is unmet and ships a defect
- N/A: requirement does not apply to this target platform

## 1. Manifest

- [ ] `id` is explicit (not implied from `start_url`). See `manifest.md` §"id and identity".
- [ ] `name`, `short_name`, `description`, `start_url`, `scope` all present.
- [ ] `display: "standalone"` plus `display_override` including `window-controls-overlay`.
- [ ] `theme_color` and `background_color` set.
- [ ] Icons: 192 PNG `purpose: "any"`, 512 PNG `purpose: "any"`, 192 PNG `purpose: "maskable"`, 512 PNG `purpose: "maskable"`. SVG `any` optional.
- [ ] Screenshots include at least one `form_factor: "wide"` and one `form_factor: "narrow"`.
- [ ] `shortcuts` defines at least two primary actions.
- [ ] `share_target` defined if app accepts shared content.
- [ ] `lang` and `dir` set.
- [ ] Served with `Content-Type: application/manifest+json`.

## 2. iOS-specific

- [ ] `<link rel="apple-touch-icon" sizes="180x180">` (opaque PNG, no transparency).
- [ ] `<meta name="apple-mobile-web-app-capable" content="yes">`.
- [ ] `<meta name="apple-mobile-web-app-status-bar-style">` set.
- [ ] `<meta name="apple-mobile-web-app-title">` set.
- [ ] `apple-touch-startup-image` for each target device combination.
- [ ] Custom "Add to Home Screen" hint shown only when `display-mode: browser`.
- [ ] Web Push tested only after install plus user gesture (iOS 16.4+ requirement).
- [ ] `viewport-fit=cover` plus `env(safe-area-inset-*)` CSS.

## 3. Service Worker

- [ ] `/sw.js` (or framework equivalent) served from root with `Cache-Control: no-cache`.
- [ ] App-shell pre-cache with versioned cache name (`app-shell-v7` pattern).
- [ ] Distinct runtime strategies for asset, API, and navigation routes.
- [ ] Old caches cleaned up in `activate` event.
- [ ] User-driven update flow with "Update now" banner (no silent `skipWaiting`).
- [ ] Offline fallback page.

## 4. Security

- [ ] HTTPS with HSTS (`max-age=31536000; includeSubDomains; preload`).
- [ ] Restrictive CSP.
- [ ] `Permissions-Policy` header.
- [ ] CORS correctly configured on API origins.
- [ ] COOP + COEP if `SharedArrayBuffer` needed (sqlite-wasm on OPFS).

## 5. Performance

- [ ] LCP < 2.5s at p75.
- [ ] INP < 200ms at p75.
- [ ] CLS < 0.1 at p75.
- [ ] Critical JS bundle < 170 KB compressed.
- [ ] `fetchpriority="high"` on the LCP image.
- [ ] Route-based code splitting.
- [ ] HTTP/2 or HTTP/3 with Brotli or Zstd.

## 6. Push

- [ ] VAPID keys generated and stored in a secret manager.
- [ ] Subscription endpoint with automatic cleanup (HTTP 410 → delete row).
- [ ] `userVisibleOnly: true` in subscription.
- [ ] `notificationclick` handler with focus-existing or open-window logic.
- [ ] Tested on installed iOS PWA, Android Chrome, Desktop Chrome / Edge.

## 7. Storage

- [ ] `navigator.storage.estimate()` monitored.
- [ ] `navigator.storage.persist()` requested after a meaningful engagement event.
- [ ] IndexedDB cleanup logic for quota pressure.
- [ ] Fallback strategy for Safari ITP 7-day cap on non-installed PWAs.

## 8. Testing

- [ ] Lighthouse individual PWA audits in CI (the PWA category itself was removed in Lighthouse 12.0.0).
- [ ] PWA Builder score >= 80.
- [ ] Real offline test (DevTools "Offline" plus full reload).
- [ ] Tested on physical iPhone (Safari Web Inspector is unavailable for standalone Home Screen PWAs; prepare an in-app diagnostic fallback).
- [ ] Install tested on Android (WebAPK), Desktop Chrome / Edge.
- [ ] Update flow tested end-to-end.

## 9. Distribution

- [ ] Bubblewrap → Google Play with valid `assetlinks.json` (otherwise the TWA degrades to a Custom Tab with visible URL bar).
- [ ] PWA Builder → Microsoft Store.
- [ ] Capacitor wrapper for the App Store if web-only distribution is not acceptable.

## 10. Monitoring

- [ ] `appinstalled` event sent to analytics.
- [ ] CrUX / RUM tracking Core Web Vitals.
- [ ] Sentry or equivalent error tracking inside the service worker.
- [ ] Heartbeat handler for `pushsubscriptionchange`.
```

- [ ] **Step 3: Verify**

Run the universal verification snippet from the Pre-flight section. Confirm: no dash-aside, no emojis, no Italian giveaway words, line count ~110-130.

- [ ] **Step 4: Stage but do not commit yet**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/production-checklist.md
```

The single final commit at Task 23 will register everything in marketplace.json simultaneously.

---

### Task 2: Write the manifest reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/manifest.md`

- [ ] **Step 1: Translate and structure source §1**

Outline:

```
# Web App Manifest

(1-paragraph intro: what the manifest is, MIME type, .webmanifest extension, crossorigin="use-credentials" rule from source §1.1)

## A complete modern manifest

(Reproduce verbatim the JSON example from source §1.2 — lines 36-102. Add English explanatory comments after the JSON block, not inside it.)

## Manifest members reference

(Convert source §1.3 table to English. Keep all rows. Add the source's "Reference: MDN and W3C" footer with the canonical URLs.)

## Modern members (2024-2025)

### share_target
(Source §1.4. Quote the MDN definition. GET vs POST. File upload requires POST + multipart/form-data.)

### protocol_handlers
(Source §1.4. "web+" prefix rule. "%s" placeholder requirement.)

### file_handlers
(Source §1.4. Runtime delivery via window.launchQueue.setConsumer. Chromium-desktop only.)

### launch_handler
(Source §1.4. client_mode values: auto, navigate-new, navigate-existing, focus-existing. Array means fallback order.)

### handle_links
(Source §1.4. auto, preferred, not-preferred. Replaces url_handlers.)

### scope_extensions
(Source §1.4. Each extended origin must serve /.well-known/web-app-origin-association keyed by the manifest id. Currently origin-trial in some Chrome versions; verify on chromestatus.com before deploying.)

### edge_side_panel.preferred_width
(Source §1.4. Default minimum 376 px in Edge.)

## Icons

(Source §1.5. 192 + 512 PNG minimum for Chromium installability. Maskable safe-zone rule: 40 percent radius from center. Best practice: separate "any" and "maskable" assets, not combined. SVG "any" works on Chromium and Firefox, not iOS home screen. iOS uses apple-touch-icon 180×180 opaque PNG; from iOS 16.4 it also reads icons from manifest but apple-touch-icon wins when both are present.)

## Splash screen

(Source §1.6. Android generates automatically. iOS does not use the manifest; requires per-device apple-touch-startup-image. Recommend pwa-asset-generator tool. Document the landscape bug: Safari often ignores landscape startup images and stretches portrait.)

## iOS meta tag block

(Source §1.7. Reproduce the full HTML block. Note that apple-mobile-web-app-capable is still the de facto trigger for standalone mode and Web Push eligibility on iOS, even though display: standalone in the manifest is equivalent from iOS 16.4+.)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 400-550.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/manifest.md
```

---

### Task 3: Write the service-workers reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/service-workers.md`

- [ ] **Step 1: Translate and structure source §2 plus §4**

Outline:

```
# Service Workers

## Lifecycle

(Source §2.1. install → activate → fetch / message / push / notificationclick / sync / periodicsync. SW runs in a separate context, terminated when idle, restarted on demand. Never store persistent state in module-level variables. Reproduce the full TypeScript SW example from source §2.1 verbatim. Include the MDN quote on activation and clients.claim.)

## skipWaiting and clients.claim

(Source §2.2. Quote Jake Archibald's warning verbatim. State the 2025 recommended pattern: skipWaiting only when paired with a coordinated reload UX, or when the delta is runtime-safe. clients.claim is mainly useful on first install. Include the Archibald quote on rarely using clients.claim as boilerplate.)

## Registration and scope

(Source §2.3. Reproduce the registration code block. Explain the path/scope relationship: scope is bounded by the SW file's directory. /sw.js must be at root for scope "/". Headers: Cache-Control: no-cache on /sw.js.)

## Caching strategies (Offline Cookbook)

(Source §2.4. Reproduce the 5-row decision table. Each row: strategy name, when to use, example asset type.)

## Workbox 7 modern pattern

(Source §2.5. Reproduce the full Workbox 7 example with NavigationRoute + CacheFirst + StaleWhileRevalidate. List the key modules: workbox-precaching, workbox-routing, workbox-strategies, workbox-expiration, workbox-background-sync, workbox-broadcast-update, workbox-window.)

## Background Sync via workbox-background-sync

(Source §2.6. Reproduce the BackgroundSyncPlugin + NetworkOnly POST route example. State Chromium-only support.)

## Debugging

(Source §2.7. Chrome / Edge DevTools Application panel features. Safari Web Inspector unavailable for installed Home Screen PWAs — recommend Eruda or hidden tap sequence. Firefox about:debugging.)

## Updates and versioning

(From source §4. Subsections:)

### Update flow: user-driven reload pattern
(Source §4.1. Reproduce the workbox-window banner + SKIP_WAITING message exchange.)

### Cache busting
(Source §4.2. Asset hashing for Cache First. HTML with no-cache or max-age=0. /sw.js served with no-cache, never via CDN with long TTL.)

### Breaking changes in the SW
(Source §4.3. Bump CACHE name. IndexedDB migrations via onupgradeneeded. clients.matchAll() with postMessage RELOAD_REQUIRED for hard reloads.)

### Update propagation timing per browser
(Source §4.4. Chromium: every navigation plus every 24h plus on-demand. Safari iOS: less frequent, often needs close/reopen. Firefox: on page load.)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 450-600.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/service-workers.md
```

---

### Task 4: Write the background-execution reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/background-execution.md`

- [ ] **Step 1: Translate and structure source §3**

Outline:

```
# Background Execution

## Worker taxonomy
(Source §3.1. Reproduce the 3-row table: Web Worker (per-tab), Shared Worker (cross-tab same origin), Service Worker (origin scope, event-driven).)

## Background Sync (one-shot)
(Source §3.2. Reproduce the page-side sync.register and SW-side sync handler. State support: Chromium desktop + Android. NOT supported on Safari iOS / macOS or Firefox.)

## Periodic Background Sync
(Source §3.3. Reproduce the permission query + register + periodicsync handler. Chromium only. Requires PWA installed AND sufficient engagement score visible at chrome://site-engagement/. Chrome does not fire in doze mode; uses the Android maintenance window.)

## Background Fetch (long downloads)
(Source §3.4. Reproduce the backgroundFetch.fetch example with downloadTotal hint. Chromium only.)

## Screen Wake Lock
(Source §3.5. Reproduce the wakeLock.request example with visibilitychange re-acquisition. State the iOS 18.4 fix: WebKit release notes "Fixed Screen Wake Lock API for Home Screen Web Apps. (108573133)".)

## Platform reality check
(Source §3.6. Per-platform summary:
- iOS Safari: none of Background Sync, Periodic, Fetch. SW killed aggressively when app backgrounded. Installed PWA has storage isolated from system Safari (separate process container).
- Android Chrome: all APIs work. Doze mode respected.
- Desktop: installed PWA windows survive main browser close. SW can run in background for push / sync.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 300-400.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/background-execution.md
```

---

### Task 5: Write the push-notifications reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/push-notifications.md`

- [ ] **Step 1: Translate and structure source §6**

This is the largest reference (Push has the most pieces). Outline:

```
# Push Notifications

## Standards stack
(Source §6.1. List RFC 8030, RFC 8291, RFC 8292, plus W3C Push API. One sentence per standard.)

## VAPID key generation
(Source §6.2. Code block: npx web-push generate-vapid-keys. Output is EC P-256 keypair, base64url-encoded.)

## Client subscription
(Source §6.3. Reproduce the urlBase64ToUint8Array helper and the subscribe function. Highlight userVisibleOnly: true as the Chromium requirement.)

## Server (Node + web-push)
(Source §6.4. Reproduce the webpush.setVapidDetails and sendNotification example with TTL and urgency.)

## Service worker handlers
(Source §6.5. Reproduce both:
- self.addEventListener('push', ...) with full showNotification options (icon, badge, image, tag, renotify, actions, data).
- self.addEventListener('notificationclick', ...) with focus-existing client logic via matchAll.
)

## Declarative Web Push (Safari 18.4+)
(Source §6.6. Quote the WebKit team statement verbatim. Explain: server sends a JSON payload conforming to the notification schema, Safari displays it without waking a service worker. Reduces battery + CPU and closes a misuse vector.)

## iOS-specific gotchas
(Source §6.7.
- Works only if the user added the PWA to Home Screen AND it opens in display: standalone.
- Permission prompt requires user gesture (tap on button). Mandatory.
- Subscriptions can silently disappear after periods of inactivity. Pattern: re-check pushManager.getSubscription() on every startup; re-subscribe if null.
- Safari iOS is NOT inspectable for Home Screen PWAs.
)

## Badge API
(Source §6.8. Reproduce the setAppBadge / clearAppBadge example. Supported iOS 16.4+, Android Chrome WebAPK, Desktop Chrome / Edge.)

## Official sources on the Web Push protocol
(Source §6.9. Convert to English, preserve all URLs. Sections:
- IETF RFCs (8030, 8291, 8292, 8188, 7515, 7519)
- W3C / WHATWG specs (Push API, Notifications, Service Workers)
- Reference docs (MDN, web.dev, Chrome for Developers)
- Push service implementers (Mozilla autopush, Chrome FCM, Apple)
- WebKit implementation and Declarative Web Push (3 blog/WWDC links)
- Server libraries (web-push Node, pywebpush, webpush-go, webpush-java)
- Recommended reading order (5 numbered steps)
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 550-700.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/push-notifications.md
```

---

### Task 6: Write the install-flows reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/install-flows.md`

- [ ] **Step 1: Translate and structure source §7**

Outline:

```
# Install Flows

## Chromium installability criteria
(Source §7.1. List from web.dev: HTTPS, valid manifest (name/short_name, start_url, 192+512 PNG icons, display != browser), SW registered with fetch handler. Plus the 30-second engagement bar: quote the web.dev rule verbatim ("user clicked or tapped on the page at least once... spent at least 30 seconds viewing the page").)

## beforeinstallprompt (Chromium only)
(Source §7.2. Reproduce the deferred-prompt pattern with three event handlers: beforeinstallprompt to capture, click handler to call deferred.prompt(), appinstalled to record analytics.)

## iOS manual install
(Source §7.3. No API. Show CSS-gated hint:
@media (display-mode: browser) { #ios-install-hint { display: block; } }
Recognize iOS Safari (exclude Chrome iOS which uses WKWebView and cannot install). Show animated icon pointing at Share button. Instruction text: "Tap Share then Add to Home Screen".)

## getInstalledRelatedApps()
(Source §7.4. Reproduce the example. Use to hide install banner when the native counterpart is already installed.)

## Window Controls Overlay (desktop)
(Source §7.5.
- Manifest: "display_override": ["window-controls-overlay"].
- CSS using env(titlebar-area-x), env(titlebar-area-width), env(titlebar-area-height), -webkit-app-region: drag / no-drag.
- JS: navigator.windowControlsOverlay.addEventListener('geometrychange', ...) to react to titlebar reflow.
- Chrome / Edge desktop only. Edge default since version 105.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 300-400.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/install-flows.md
```

---

### Task 7: Write the permissions reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/permissions.md`

- [ ] **Step 1: Translate and structure source §5**

Outline:

```
# Permissions

## Query pattern
(Source §5.1. Reproduce the ensure(name, onGranted) helper with try/catch for unsupported names. Show the granted/prompt/denied state transitions and the change event.)

## Permission names
(Source §5.1. List all permission names from the MDN reference quoted in source: accelerometer, accessibility-events, ambient-light-sensor, background-sync, camera, clipboard-read, clipboard-write, geolocation, gyroscope, local-fonts, magnetometer, microphone, midi, notifications, payment-handler, persistent-storage, push, screen-wake-lock, storage-access, top-level-storage-access, window-management.)

## Best practices
(Source §5.2.
1. Never ask at page load. Ask at the moment of the action requiring it.
2. Always show a rationale UI before the native prompt.
3. push / notifications: the prompt must be preceded by a user gesture. On iOS this is binding.
4. Handle denied with an alternative UI. Do not re-prompt.
)

## Permissions-Policy header
(Source §5.3. Reproduce the example header value disabling third-party iframe access to camera/microphone/geolocation.)

## Platform differences in availability
(Source §5.4.
- iOS: no background-sync, no periodic-background-sync, no Bluetooth/USB/HID/Serial/NFC. clipboard-read needs gesture. notifications only on installed PWAs.
- Android Chrome: all available (with prompts).
- Desktop: superset of Android + Web Serial / USB / HID / Bluetooth.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 250-350.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/permissions.md
```

---

### Task 8: Write the storage-persistence reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/storage-persistence.md`

- [ ] **Step 1: Translate and structure source §8**

Outline:

```
# Storage and Persistence

## Storage endpoints
(Source §8.1. Reproduce the 6-row table: localStorage, sessionStorage, cookies, IndexedDB, Cache API, OPFS. Columns: type, async, worker-accessible, notes.)

## IndexedDB with idb
(Source §8.2. Reproduce the openDB example with three-version upgrade callback. Mention Dexie.js as a typed alternative with sync addon.)

## OPFS
(Source §8.3. Reproduce both the async navigator.storage.getDirectory() example and the sync FileSystemSyncAccessHandle example. Quote the web.dev definition of OPFS. Browser support: Chromium, Safari 17+, Firefox.)

## Quota and eviction
(Source §8.4. Per-browser breakdown:
- Chromium: up to 60% of total disk per origin, 80% global. Quote the MDN line.
- Firefox: 10% of disk (max 10 GiB) best-effort, up to 50% (cap 8 TiB) with persistent.
- Safari macOS / iOS 17+: increased to 60% disk per origin (80% global). Persistent Storage requires notification permission to be effective.
- Safari iOS (non-installed PWA): ITP applies the 7-day cap on script-writeable storage. Installed PWAs (Home Screen) have a separate container that historically avoids this cap, but WebKit bugs 190269 and 199110 have periodically eroded the guarantee.
)

## Persistent Storage
(Source §8.5. Reproduce the ensurePersistent helper using navigator.storage.persist() and estimate(). Per-browser policy:
- Chromium grants based on engagement / install state.
- Firefox shows a prompt.
- Safari requires notification permission granted to enable persistence.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 350-450.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/storage-persistence.md
```

---

### Task 9: Write the capabilities-fugu reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/capabilities-fugu.md`

- [ ] **Step 1: Translate and structure source §9 plus §16**

Outline:

```
# Project Fugu Capabilities

## API matrix
(Source §9. Reproduce the 14-row API table: File System Access, Web Share, Web Share Target, Contact Picker, Web Bluetooth, Web USB / Serial / HID, WebNFC, WebRTC, Payment Request, WebAuthn / Passkeys, Geolocation, Screen Capture, Web Speech (recognition), File Handlers. Columns: Chrome/Edge, Firefox, Safari. State Project Fugu shipped exactly 55 APIs per Thomas Steiner's "Is Project Fugu done?".)

## Web Share
(Source §9.1. Reproduce the navigator.share example with files. Mention navigator.canShare(data) for feature detection.)

## WebAuthn / Passkeys
(Source §9.2. Reproduce the navigator.credentials.create example with publicKey options: challenge, rp, user, pubKeyCredParams ES256 + RS256, authenticatorSelection residentKey: 'required'.)

## References to track
(One-line entry each:
- Fugu API Tracker: fugu-tracker.web.app
- Chrome Capabilities status: developer.chrome.com/docs/capabilities/status
)

## 2025-2026 trends folded in
(Source §16.
- iOS 18.4 (March 31, 2025): Declarative Web Push, Wake Lock fix for Home Screen PWAs, webkitdirectory, Image Capture API. WebKit shipped 84 new features.
- iOS 26: every Add-to-Home-Screen opens as a web app by default (implicit opt-in to standalone).
- DMA UE: Apple kept PWAs in the EU after the March 2024 reversal. iOS 18.2 in theory allows BrowserEngineKit for non-WebKit browsers, but as of early 2026 no browser has shipped one.
- Project Fugu: 55 APIs shipped. navigator.storage.getDirectory() (OPFS) growing fast. New forget() / permission-revoke methods for HID / USB / Serial.
- Baseline web feature (web.dev/baseline): interoperability badge for "widely available" APIs across all major browsers. Useful for production gating.
- INP 200ms threshold confirmed as a ranking signal.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 300-400.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/capabilities-fugu.md
```

---

### Task 10: Write the platform-constraints reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/platform-constraints.md`

- [ ] **Step 1: Translate and structure source §10**

Outline:

```
# Platform Constraints

## iOS / iPadOS (WebKit mandatory)
(Source §10.1. Comprehensive list:
- Web Push only from iOS 16.4 (March 2023) and only for PWAs installed from Safari to Home Screen.
- Safari 18.4 (March 31, 2025): Declarative Web Push + Screen Wake Lock for Home Screen PWAs.
- iOS 26: every site added to Home Screen opens as a web app by default.
- No Background Sync, Periodic Background Sync, Background Fetch.
- No Web Bluetooth / USB / HID / Serial / NFC.
- Storage: isolated container; known cache eviction bugs; nominal 60% disk per origin but persist() requires notification permission.
- Install: manual only via Share → Add to Home Screen.
- Chrome / Firefox on iOS are forced to use WebKit (App Store guideline 2.5.6).
- DMA UE (January-March 2024): Apple initially planned to remove Home Screen Web Apps in iOS 17.4 beta in the EU. After pressure from EC and Open Web Advocacy: reversal. Quote the Apple TechCrunch statement: "We have received requests to continue to offer support for Home Screen web apps in iOS, therefore we will continue to offer the existing Home Screen web apps capability in the EU."
)

## Android (Chrome)
(Source §10.2.
- WebAPK generated by Play Services at install. PWA appears as a native app in the launcher, has its own entry in Settings → Apps, permissions managed by the system.
- TWA (Trusted Web Activity) for Play Store distribution via Bubblewrap.
- All capabilities available. Background Sync works.
- intent:// linking. Native share target. Automatic splash screen.
)

## Desktop
(Source §10.3.
- Chrome / Edge: superset of features. Window Controls Overlay, File Handlers, Protocol Handlers, URL Handlers via scope_extensions / handle_links. Tabbed Application Mode experimental behind flag.
- Firefox: dropped PWA support January 27 2021 (9to5Google quote). Effective removal in Firefox 84 (December 2020). Firefox 143 (September 2025) reintroduced limited PWA support on Windows. On Android, Firefox supports "Add to Home Screen" as a lightweight shortcut.
- Safari macOS: from Sonoma (14, 2023) supports "Add to Dock" creating a real web app in ~/Applications with its own container, push notifications (macOS 13+), and Dock badge. No Window Controls Overlay, File Handlers, or Protocol Handlers.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 400-500.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/platform-constraints.md
```

---

### Task 11: Write the performance reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/performance.md`

- [ ] **Step 1: Translate and structure source §11**

Outline:

```
# Performance

## Core Web Vitals 2025
(Source §11.1. Quote the Google Search Central thresholds verbatim: LCP < 2.5s, INP < 200ms, CLS < 0.1. State that INP replaced FID on March 12, 2024. Measurement: 75th percentile in the Chrome User Experience Report (CrUX).)

## Techniques
(Source §11.2.
- App Shell: minimal HTML + UI skeleton precached (CacheFirst), data via Network or SWR.
- Preload critical resources: <link rel="preload" as="image" fetchpriority="high">.
- Route-based code splitting (Vite, Next, Nuxt) plus dynamic import.
- fetchpriority="high" on the LCP image, loading="lazy" for below-the-fold.
- CSS containment: content-visibility: auto for long lists.
- INP: break up long tasks (scheduler.yield(), requestIdleCallback). Avoid main-thread blocking >50ms.
)

## Audit tooling
(Source §11.3.
- Lighthouse: the PWA category was removed in Lighthouse 12.0.0 (Chrome 126, May 2024). Quote: "The Lighthouse panel now runs Lighthouse 12.0.0. This update brings a number of changes, including PWA category removal." Individual checks (manifest, installability, splash) remain in the DevTools Application panel.
- PWA Builder (pwabuilder.com): cross-platform score, store-package generation.
- WebPageTest. CrUX dashboard.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 250-350.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/performance.md
```

---

### Task 12: Write the security reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/security.md`

- [ ] **Step 1: Translate and structure source §12**

Outline:

```
# Security

## HTTPS requirement
(Source §12. Required for service workers (localhost excepted as the development convenience).)

## CSP for PWAs
(Source §12. Recommended CSP header, paying attention to 'strict-dynamic' and to not breaking the SW. Reproduce the recommended header verbatim with default-src 'self', script-src 'self' 'wasm-unsafe-eval', worker-src 'self', connect-src 'self' plus the API origin, img-src 'self' data: https:, object-src 'none', base-uri 'self', frame-ancestors 'none'.)

## COOP and COEP
(Source §12. Cross-Origin-Embedder-Policy: require-corp plus Cross-Origin-Opener-Policy: same-origin if SharedArrayBuffer is needed. SharedArrayBuffer is required for sqlite-wasm on OPFS.)

## Secure context requirements
(Source §12. List of APIs that require a secure context: Service Worker, Push, Geolocation, Camera, Mic, Clipboard, OPFS, WebAuthn, Bluetooth, etc.)

## Permissions-Policy
(Source §12. Used to limit capabilities on iframes. Cross-reference to permissions.md.)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 200-300.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/security.md
```

---

### Task 13: Write the distribution reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/distribution.md`

- [ ] **Step 1: Translate and structure source §13**

Outline:

```
# Distribution

## Google Play via TWA (Bubblewrap)
(Source §13.1. Reproduce the bubblewrap CLI commands:
npm i -g @bubblewrap/cli
bubblewrap init --manifest=https://acme.com/manifest.webmanifest
bubblewrap build

Outputs: app-release-bundle.aab and app-release-signed.apk.

Then the /.well-known/assetlinks.json setup with relation delegate_permission/common.handle_all_urls, target namespace android_app, package_name, sha256_cert_fingerprints. CRITICAL: without valid Digital Asset Links, the TWA degrades to a Custom Tab with visible URL bar.)

## Microsoft Store
(Source §13.2. PWA Builder generates a signed MSIX. Free submission on Partner Center for PWA packages.)

## Apple App Store
(Source §13.3. Apple does not accept pure PWAs (Guideline 4.2.2 against web clippings). Workable path: wrap with Capacitor or Cordova adding native plugins to pass review (native push, IAP).)

## Meta Quest Store
(Source §13.4. PWA Builder supports packaging for Meta Quest. Sideload via adb and official store for curated apps.)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 250-350.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/distribution.md
```

---

### Task 14: Write the frameworks-tooling reference

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/references/frameworks-tooling.md`

- [ ] **Step 1: Translate and structure source §15 plus §14**

Outline:

```
# Frameworks and Tooling

## Vite via vite-plugin-pwa
(Source §15.1. Reproduce the vite.config.ts example with VitePWA including registerType, strategies: 'generateSW', manifest, and workbox.runtimeCaching. State the version constraint: vite-plugin-pwa v1.3.0 requires Node 20.19+ or 22.12+ and Vite 7+. Vite 7 raised the requirement to Node 20.19+ after Node 18 EOL in April 2025.)

## Next.js via @serwist/next
(Source §15.2. State next-pwa original is unmaintained since 2022. The fork @ducanh2912/next-pwa now points to Serwist. Reproduce the app/sw.ts example using Serwist with precacheEntries, skipWaiting, clientsClaim, navigationPreload, runtimeCaching: defaultCache, and the offline fallback. Note: Next.js 14+ supports app/manifest.ts natively.)

## Angular Service Worker
(Source §15.3. ng add @angular/pwa schematic. Configured via ngsw-config.json with assetGroups and dataGroups. Strategies: 'performance' approximates CacheFirst, 'freshness' approximates NetworkFirst.)

## Nuxt via @vite-pwa/nuxt
(Source §15.4. Official Vite PWA module for Nuxt 3+.)

## Capacitor (Ionic)
(Source §15.5. For a single codebase distributed to the App Store too, Capacitor wraps the PWA in a native WebView exposing bridges to native plugins (Push, native-accuracy Geolocation, Biometric, etc.).)

## Debugging surface
(Source §14.
- Chrome / Edge DevTools Application panel: Manifest viewer (with WCO emulation), Service Workers, Storage, Cache, IndexedDB, Background Services panel (Background Fetch + Periodic Background Sync recording up to 3 days), Quota and estimated remaining storage.
- Safari Web Inspector remote: only the Safari tab on iOS. NOT standalone PWAs. This is the historical limit.
- PWA Builder Validator + Lighthouse PWA checks (individual, not the removed category).
- DevTools throttling: Slow 3G, offline, CPU 4x slowdown.
- WebPageTest for field-like measurements.
)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 400-500.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/references/frameworks-tooling.md
```

---

### Task 15: Write SKILL.md (the router)

**Files:**
- Create: `plugins/pwa-expert/skills/pwa-development/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Content:

```markdown
---
name: pwa-development
description: >
  Progressive Web App knowledge base covering Web App Manifest (id, display_override,
  scope_extensions, handle_links, file_handlers, share_target), Service Workers
  (Workbox 7, Serwist), Web Push (VAPID, RFC 8030/8291/8292, Declarative Push for
  Safari 18.4+), install flows (beforeinstallprompt, Window Controls Overlay), OPFS
  storage, Project Fugu capabilities, Core Web Vitals 2025 (INP < 200ms), security
  (HTTPS, CSP, COOP/COEP), and distribution (Bubblewrap to Google Play, PWA Builder
  to Microsoft Store, Capacitor to App Store). 2025-2026 baseline.
  TRIGGER WHEN: building, implementing, auditing, or debugging PWAs - manifest, service
  worker, Web Push, install flow, OPFS, Background Sync, Wake Lock, Vite vite-plugin-pwa,
  Next.js Serwist, Angular ng add @angular/pwa, Nuxt @vite-pwa/nuxt, Bubblewrap, TWA,
  PWA Builder, Capacitor wrapping.
  DO NOT TRIGGER WHEN: the task is generic frontend styling (use frontend), generic
  React performance (use react-development:review-react), cross-platform security
  review unrelated to PWA (use platform-engineering), Tauri or Electron desktop wrappers
  (use tauri-development), or GA4 / analytics work (use digital-marketing).
---

# Progressive Web App Development

Knowledge base for building, auditing, and shipping Progressive Web Apps in 2025-2026. Covers manifest, service workers, Web Push, install flows, storage, Project Fugu capabilities, platform constraints, performance (Core Web Vitals), security, and distribution to Google Play, Microsoft Store, App Store (via Capacitor), and Meta Quest.

## When to use this skill

Use this skill whenever the active task involves any of:
- A `manifest.webmanifest` or `manifest.json`, manifest members, icons, splash screens, iOS meta tags.
- A service worker file, registration, caching strategy, update flow, Workbox 7, Serwist.
- Web Push: VAPID keys, subscription, server-side delivery, Declarative Web Push.
- PWA install flow on Chromium (`beforeinstallprompt`), iOS (manual), or Window Controls Overlay on desktop.
- Background execution: Background Sync, Periodic Background Sync, Background Fetch, Screen Wake Lock.
- Storage: IndexedDB, OPFS, quotas, `navigator.storage.persist()`.
- Project Fugu APIs: File System Access, Web Share, Web Bluetooth / USB / HID / Serial / NFC, WebAuthn, etc.
- Performance for PWAs: Core Web Vitals 2025, INP < 200ms, app shell, code splitting.
- Security headers for PWAs: HTTPS, CSP tuned for SW, COOP / COEP for `SharedArrayBuffer`.
- Distribution: Bubblewrap to Google Play (TWA + `assetlinks.json`), PWA Builder to Microsoft Store (MSIX), Capacitor to App Store, PWA Builder to Meta Quest.
- Framework integration: Vite (`vite-plugin-pwa`), Next.js (`@serwist/next`), Angular (`ng add @angular/pwa`), Nuxt (`@vite-pwa/nuxt`).

Skip this skill if the task is generic frontend styling, generic React performance, cross-platform security unrelated to PWA mechanics, Tauri or Electron wrappers, or GA4 / analytics.

## References Library

Read the relevant reference on-demand for the active task. Do NOT preload all references at once; pick the one that matches the question.

| Reference | Topic |
|---|---|
| `references/manifest.md` | Web App Manifest: members, icons, splash, iOS meta tags |
| `references/service-workers.md` | SW lifecycle, caching strategies, Workbox 7, updates, debugging |
| `references/background-execution.md` | Background Sync, Periodic Sync, Background Fetch, Wake Lock |
| `references/push-notifications.md` | Web Push end-to-end: VAPID, RFCs, Declarative Push, Badge API |
| `references/install-flows.md` | beforeinstallprompt, iOS manual install, Window Controls Overlay |
| `references/permissions.md` | Permissions API, Permissions-Policy header, platform availability |
| `references/storage-persistence.md` | IndexedDB, OPFS, quotas, persistent storage |
| `references/capabilities-fugu.md` | Project Fugu API matrix and worked examples |
| `references/platform-constraints.md` | iOS / Android / Desktop per-platform reality check |
| `references/performance.md` | Core Web Vitals 2025, INP < 200ms, audit tooling |
| `references/security.md` | HTTPS, CSP for SW, COOP / COEP, secure contexts |
| `references/distribution.md` | Bubblewrap / TWA, PWA Builder MSIX, Capacitor, Meta Quest |
| `references/frameworks-tooling.md` | Vite, Next.js, Angular, Nuxt + debugging surface |
| `references/production-checklist.md` | Full deploy checklist for going to production |

## Decision quick-reference

| Question | Answer |
|---|---|
| Which SW caching strategy for hashed JS / CSS? | CacheFirst |
| Which for HTML navigation? | NetworkFirst with networkTimeoutSeconds: 3 |
| Which for avatars / low-criticality data? | StaleWhileRevalidate |
| Which for POST mutations? | NetworkOnly + BackgroundSyncPlugin |
| Should `skipWaiting()` be called by default? | No. Pair with a coordinated reload UX, or omit. |
| Minimum icon sizes for Chromium install? | 192 PNG + 512 PNG, both `purpose: "any"`. Add separate maskable assets. |
| Combine `"any maskable"` on one icon? | No. web.dev explicitly discourages it. |
| iOS Web Push: requirements? | iOS 16.4+, PWA installed to Home Screen, `display: standalone`, user-gesture-triggered subscribe. |
| Periodic Background Sync on iOS? | Not supported. Plan a degraded path. |
| Lighthouse PWA category? | Removed in Lighthouse 12.0.0 (Chrome 126, May 2024). Use individual Application-panel checks. |
| Next.js PWA library in 2026? | `@serwist/next` (not the unmaintained original `next-pwa`). |
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 90-120. Confirm the SKILL.md description is under 1024 characters (Anthropic Skills Guide limit). The description above is approximately 950 characters with the `description: >` multiline form.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/skills/pwa-development/SKILL.md
```

---

### Task 16: Write the pwa-architect agent

**Files:**
- Create: `plugins/pwa-expert/agents/pwa-architect.md`

- [ ] **Step 1: Write the agent file**

Skeleton:

```markdown
---
name: pwa-architect
description: >
  Expert architect for Progressive Web App design and implementation, 2025-2026 baseline.
  Covers Web App Manifest (id, display_override, scope_extensions, handle_links,
  file_handlers, share_target), Service Workers (Workbox 7, Serwist), Web Push (VAPID,
  RFC 8030/8291/8292, Declarative Push for Safari 18.4+), install flows
  (beforeinstallprompt, Window Controls Overlay), OPFS storage, Project Fugu APIs,
  Core Web Vitals 2025 (INP < 200ms), framework integration (Vite, Next.js, Angular,
  Nuxt), and distribution (Bubblewrap to Google Play, PWA Builder to Microsoft Store,
  Capacitor to App Store, PWA Builder to Meta Quest). TRIGGER WHEN: building,
  implementing, designing, coding, or creating PWAs, manifests, service workers, push
  pipelines, install flows, OPFS storage, framework-specific PWA integration, or store
  distribution. DO NOT TRIGGER WHEN: generic frontend styling (use frontend), generic
  React performance (use react-development:review-react), cross-platform security
  unrelated to PWAs (use platform-engineering), Tauri or Electron desktop wrappers
  (use tauri-development), or GA4 / analytics (use digital-marketing).
model: opus
color: cyan
tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch
---

# pwa-architect

## Role

Expert in Progressive Web App architecture for 2025-2026. Designs and implements complete PWAs end-to-end: manifest, service worker, Web Push, install flow, storage, framework integration, and store distribution. Reasons about platform asymmetry (Chromium full, iOS WebKit constrained, Firefox partial) and applies progressive enhancement.

## Core Knowledge

- Web App Manifest: id, name, short_name, start_url, scope, display, display_override (window-controls-overlay), theme_color, background_color, icons (192/512 PNG any + maskable as separate assets), screenshots (wide + narrow), shortcuts, share_target, protocol_handlers, file_handlers, launch_handler, handle_links, scope_extensions, edge_side_panel.
- Service Workers: lifecycle (install, activate, fetch, message, push, notificationclick, sync, periodicsync). Five Offline Cookbook strategies. Workbox 7 modules (precaching, routing, strategies, expiration, background-sync, broadcast-update, window). Serwist for Next.js. Update flow: user-driven reload, skipWaiting + clients.claim caveats per Jake Archibald.
- Web Push: VAPID (RFC 8292), RFC 8030 transport, RFC 8291 + RFC 8188 encryption. Client subscription (userVisibleOnly: true). Node server with web-push. SW push and notificationclick handlers. Declarative Web Push from Safari 18.4 (no SW required). iOS gotchas: install required, user gesture required, silent subscription loss.
- Install flows: beforeinstallprompt deferred-prompt on Chromium. iOS manual install hint gated on display-mode: browser. Window Controls Overlay on Chrome / Edge desktop. getInstalledRelatedApps.
- Background execution: Background Sync (Chromium), Periodic Background Sync (Chromium, engagement-gated), Background Fetch (Chromium), Screen Wake Lock (iOS 18.4 fix for Home Screen PWAs).
- Storage: IndexedDB (idb, Dexie), OPFS sync access in workers, Cache API. Per-browser quota and eviction. Safari ITP 7-day cap on non-installed PWAs. navigator.storage.persist().
- Project Fugu: 55 shipped APIs. File System Access, Web Share, Web Bluetooth / USB / HID / Serial / NFC, WebAuthn / Passkeys, WebRTC, Payment Request, Screen Capture.
- Platform constraints: iOS WebKit-only, no Background Sync / Fetch, no Bluetooth / USB / HID / Serial / NFC, install manual, Web Push only for installed standalone PWAs from iOS 16.4. Android: WebAPK + TWA via Bubblewrap. Desktop: Chrome / Edge full, Safari macOS Add-to-Dock, Firefox 143 limited reintroduction.
- Performance: Core Web Vitals 2025 (LCP < 2.5s, INP < 200ms, CLS < 0.1 at p75). INP replaced FID March 12, 2024. App Shell, fetchpriority on LCP image, scheduler.yield() for INP.
- Security: HTTPS required for SW (localhost excepted). Restrictive CSP including worker-src. COOP + COEP if SharedArrayBuffer needed.
- Distribution: Bubblewrap to Google Play (TWA + assetlinks.json mandatory). PWA Builder MSIX to Microsoft Store. Capacitor wrap for App Store (Guideline 4.2.2 blocks pure web clippings). PWA Builder for Meta Quest.
- Frameworks: vite-plugin-pwa v1.3.0 (Node 20.19+, Vite 7+). @serwist/next for Next.js. ng add @angular/pwa schematic. @vite-pwa/nuxt for Nuxt 3+.

## References Library

Always read the relevant reference on-demand. NEVER preload them all upfront.

| Need | Reference |
|---|---|
| Manifest design or audit | `pwa-development/references/manifest.md` |
| Service worker design or audit | `pwa-development/references/service-workers.md` |
| Background Sync / Periodic / Fetch / Wake Lock | `pwa-development/references/background-execution.md` |
| Web Push end-to-end | `pwa-development/references/push-notifications.md` |
| Install flow | `pwa-development/references/install-flows.md` |
| Permissions API | `pwa-development/references/permissions.md` |
| Storage and persistence | `pwa-development/references/storage-persistence.md` |
| Fugu capabilities | `pwa-development/references/capabilities-fugu.md` |
| Platform constraints (iOS / Android / Desktop) | `pwa-development/references/platform-constraints.md` |
| Core Web Vitals and perf | `pwa-development/references/performance.md` |
| HTTPS, CSP, COOP / COEP | `pwa-development/references/security.md` |
| Store distribution | `pwa-development/references/distribution.md` |
| Framework wiring + debugging | `pwa-development/references/frameworks-tooling.md` |
| Production checklist | `pwa-development/references/production-checklist.md` |

## Workflow

For every PWA design or build task, follow this sequence:

1. **Target platforms.** Which of Chromium-desktop, Android Chrome, iOS Safari, Desktop Safari, Firefox does the user need? Note the constraints (iOS lacks Background Sync; Firefox dropped then partially reintroduced PWAs).
2. **Manifest design.** Start with `id`, `name`, `short_name`, `start_url`, `scope`, `display: "standalone"`. Add `display_override` if targeting Chrome / Edge desktop. Define icons (192 + 512 PNG `any` AND `maskable` as separate assets). Add screenshots wide + narrow. Add shortcuts for top-2 actions. Read `manifest.md`.
3. **Service worker strategy.** Pick a strategy per route type using the Offline Cookbook table (`service-workers.md`). For new projects, default to Workbox 7 (or Serwist for Next.js). For Angular, prefer the `ng add @angular/pwa` schematic.
4. **Push plan if applicable.** Plan Web Push only if it produces user-visible notifications matching `userVisibleOnly: true`. On iOS, gate the subscribe button behind install-detected + user gesture. Consider Declarative Web Push on Safari 18.4+. Read `push-notifications.md`.
5. **Install UX.** Chromium: `beforeinstallprompt` deferred prompt triggered by a high-value action, not at page load. iOS: CSS-gated manual hint, exclude Chrome iOS. Read `install-flows.md`.
6. **Storage design.** Choose IndexedDB (via `idb`) for structured data, OPFS via worker for large binaries, Cache API only inside the SW. Request `navigator.storage.persist()` after a meaningful engagement event. Read `storage-persistence.md`.
7. **Distribution plan.** Bubblewrap → Google Play (with `assetlinks.json`). PWA Builder → Microsoft Store. Capacitor wrap → App Store if web-only is not acceptable. Read `distribution.md`.
8. **Production gate.** Walk the production checklist (`production-checklist.md`) before shipping.

## Output Standards

A complete PWA deliverable from this agent includes:

- `manifest.webmanifest` with `id`, `display_override` including `window-controls-overlay` when desktop is a target, full icon set (192/512 PNG `any` plus 192/512 PNG `maskable` as separate assets), `screenshots` wide + narrow, at least two `shortcuts`, `lang`, `dir`, and modern members (`share_target`, `protocol_handlers`, `file_handlers`, `launch_handler`, `handle_links`) where they add value.
- Service worker with a versioned cache name (e.g. `app-shell-v7`), pre-cache of the app shell, distinct runtime strategies per route type, old-cache cleanup in `activate`, offline fallback page, user-driven update flow.
- iOS meta tag block: `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, `apple-mobile-web-app-title`, `apple-touch-icon` 180x180, `theme-color`, `viewport-fit=cover`.
- Service worker registration code wired into the framework's entry point.
- Recommended headers list: HSTS, CSP, Permissions-Policy, COOP, COEP, `Cache-Control: no-cache` for `/sw.js`.

Every deliverable cites the relevant reference file so the user can verify the reasoning.

## Routing

Delegate to other agents or plugins when the task crosses out of PWA scope:

- Generic frontend styling, design systems, layout work: `frontend` plugin.
- React-specific performance, bundle size, re-render audit: `react-development:review-react`.
- Cross-platform security audit beyond PWA mechanics (mobile / Electron / Tauri rulebook): `platform-engineering:platform-review`.
- Tauri or Electron desktop wrappers: `tauri-development`.
- GA4 / analytics instrumentation, Consent Mode: `digital-marketing:ga4-implementation-expert`.
- Stripe payments inside the PWA: `stripe:stripe-integrator`.

## Notable 2025-2026 gotchas to internalize

- iOS Web Push: only installed standalone PWAs from iOS 16.4. Subscriptions can disappear silently; re-check `pushManager.getSubscription()` on every startup.
- Safari Web Inspector cannot inspect installed Home Screen PWAs. Prepare an in-app diagnostic fallback (Eruda, hidden tap sequence).
- Lighthouse PWA category was removed in Chrome 126 / Lighthouse 12.0.0 (May 2024). Use the individual Application-panel checks, not the deprecated category score.
- `scope_extensions` is still origin-trial in some Chrome versions. Verify status on `chromestatus.com` before deploying.
- `next-pwa` is unmaintained since 2022. Default to `@serwist/next` for Next.js.
- Without a valid `/.well-known/assetlinks.json`, a Bubblewrap TWA degrades to a Custom Tab showing the URL bar.
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 200-260. Confirm the description in frontmatter is under 1024 characters.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/agents/pwa-architect.md
```

---

### Task 17: Write the pwa-audit command

**Files:**
- Create: `plugins/pwa-expert/commands/pwa-audit.md`

- [ ] **Step 1: Write the command file**

```markdown
---
description: Audit a PWA implementation. Auto-detects local-code mode (path or omitted) vs live-URL mode (Playwright). Produces a prioritized markdown report with file-line citations.
argument-hint: "[path | URL]"
---

# /pwa-expert:pwa-audit

Adversarial PWA audit. Two modes, auto-detected from `$ARGUMENTS`:

- **Live URL mode:** if the argument starts with `http://` or `https://`, fetch the page with Playwright, parse the manifest, test install criteria, check security headers, test offline behavior, and measure Core Web Vitals on the landing page.
- **Local code mode:** otherwise, treat the argument as a path (default: current working directory). Locate the manifest file, service worker source, registration call, iOS meta tag block, and security-header configuration in the codebase. Parse and check.

## Setup

Delegate this audit to the `pwa-architect` agent. The agent must read the relevant references from the `pwa-development` skill on-demand (not all upfront), targeting each section of the audit.

## Mode A: Live URL

If `$ARGUMENTS` is a URL, use the `playwright-skill` tools:

1. Launch a browser and navigate to the URL.
2. Fetch `/manifest.webmanifest` (and fall back to `/manifest.json`). Validate as JSON. Run the manifest checklist from `production-checklist.md` §1.
3. Check the service worker registration: look for a `<script>` registering `navigator.serviceWorker.register(...)`, or for an existing controller via `navigator.serviceWorker.controller`.
4. Check the install criteria from `install-flows.md`: manifest valid, `display` not `browser`, SW registered with `fetch` handler, HTTPS, 192+512 PNG icons present.
5. Check meta tags: `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, `apple-mobile-web-app-title`, `apple-touch-icon`, `theme-color`, `viewport`.
6. Check security headers via response headers: HTTPS plus HSTS, CSP presence (and warn if `'unsafe-eval'` is allowed), `Cross-Origin-Opener-Policy`, `Cross-Origin-Embedder-Policy`.
7. Test offline behavior: route the page through `page.context().setOffline(true)`, reload, and confirm a non-broken response (offline page or cached navigation).
8. Measure Core Web Vitals on the landing page (LCP, CLS at least; INP requires interaction). Compare against `performance.md` thresholds.

If `playwright-skill` is unavailable, fall back to suggesting manual checks and explain what each would verify.

## Mode B: Local code

If `$ARGUMENTS` is a path or omitted, search the codebase:

1. Find the manifest: `Glob` for `manifest.webmanifest`, `manifest.json`, `app/manifest.ts` (Next.js 14+), `src/manifest.ts`. Parse and verify against `production-checklist.md` §1.
2. Find the SW source: `Glob` for `sw.js`, `sw.ts`, `service-worker.js`, `service-worker.ts`, `app/sw.ts` (Serwist), `ngsw-config.json` (Angular). Read and audit caching strategies, `skipWaiting` / `clients.claim` use, cleanup in `activate`, offline fallback.
3. Find the SW registration: `Grep` for `serviceWorker.register`, `workbox-window`, `Workbox(`, `Serwist(`, or Next.js implicit registration via `@serwist/next`.
4. Find iOS meta tags: `Grep` for `apple-mobile-web-app-capable`. Confirm the full block from `manifest.md` §"iOS meta tag block".
5. Find security headers: read `next.config.*` (Next.js headers function), `vite.config.*` plus any `server` plugin, `nginx.conf` / `.htaccess` if present, `firebase.json` `hosting.headers`, `vercel.json` `headers`. Check HSTS, CSP, COOP, COEP, Permissions-Policy.
6. Find Web Push: `Grep` for `pushManager.subscribe`, `setVapidDetails`, `web-push`. If found, audit the subscription flow and server-side delivery against `push-notifications.md`.
7. Find storage usage: `Grep` for `localStorage.`, `IDBDatabase`, `openDB(`, `navigator.storage`. Flag anti-patterns from `storage-persistence.md` (e.g. `localStorage` for large data).
8. Detect framework via `package.json` and configs. Apply framework-specific checks from `frameworks-tooling.md` (Vite vite-plugin-pwa config, Serwist app/sw.ts, Angular ngsw-config.json structure).

## Output

Write a markdown report to stdout (or a file if the user asked) with this structure:

```
# PWA Audit Report

**Target:** <path or URL>
**Mode:** <local | live>
**Date:** YYYY-MM-DD

## Summary

<one paragraph: overall posture, biggest risks>

## Critical findings

### C1: <short title>
- **Location:** <file:line> or <URL fragment>
- **Issue:** <one sentence>
- **Impact:** <one sentence>
- **Fix:** <concrete change with code if applicable>
- **Reference:** `references/<file>.md` §<heading>

## Important findings

(same format)

## Nice-to-have findings

(same format)

## Verified passes

(short list of categories where the implementation is correct)
```

Severity buckets:
- **Critical:** ships a defect (install will fail; Web Push will not deliver on iOS; SW will not update; CSP allows XSS; missing HTTPS).
- **Important:** degrades the experience (no maskable icons; `skipWaiting()` without coordinated reload; no offline fallback; INP > 200ms at p75).
- **Nice-to-have:** polish (no Window Controls Overlay; no scope_extensions; no shortcuts beyond the minimum).

For each finding, cite the file and line in local mode, or the URL plus the manifest field or DOM selector in live mode.

## iOS caveat

If the target is iOS-focused, prepend the report with a clear note that Safari Web Inspector cannot inspect installed Home Screen PWAs, so live-mode audit covers only the in-browser experience, not the post-install standalone state.
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 130-170.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/commands/pwa-audit.md
```

---

### Task 18: Write the pwa-scaffold command

**Files:**
- Create: `plugins/pwa-expert/commands/pwa-scaffold.md`

- [ ] **Step 1: Write the command file**

```markdown
---
description: Scaffold a complete PWA into the current project. Detects framework (Vite, Next.js, Angular, Nuxt, vanilla) and generates manifest, service worker, iOS meta tags, registration code, icon stubs, and recommended security headers documentation.
argument-hint: "[framework]"
---

# /pwa-expert:pwa-scaffold

Scaffold a production-ready PWA into the current project. Delegate execution to `pwa-architect`. The agent reads the relevant references (`manifest.md`, `service-workers.md`, `frameworks-tooling.md`) on-demand.

## Framework detection

1. Parse `package.json` if present.
2. Look for `vite.config.*`, `next.config.*`, `angular.json`, `nuxt.config.*` in the project root.
3. If `$ARGUMENTS` is provided, use it (one of: `vite`, `next`, `angular`, `nuxt`, `vanilla`).
4. If detection is ambiguous, ask the user via `AskUserQuestion` which framework to target.

## Inputs to collect

Before generating files, use `AskUserQuestion` to gather:

1. App name (full): used for manifest `name`. Example: "Acme Productivity Suite".
2. App name (short): used for manifest `short_name` and the iOS meta `apple-mobile-web-app-title`. Example: "Acme".
3. Description: used for manifest `description`.
4. Theme color (hex): used for manifest `theme_color` and the `<meta name="theme-color">`. Default: `#0f172a`.
5. Background color (hex): used for manifest `background_color` and Android splash. Default: `#ffffff`.
6. Two primary shortcuts (name + URL each): for manifest `shortcuts`. Defaults can be skipped if the user does not have them yet.

## Idempotency

Before writing each file, check if it exists. If it does, show a diff and ask via `AskUserQuestion` whether to overwrite, merge, or skip. Never silently overwrite an existing manifest or SW.

## Generated artifacts (per framework)

### Vite (vite-plugin-pwa)

- `public/manifest.webmanifest` with the full set of members per `manifest.md` (id, display_override, icons any+maskable, screenshots wide+narrow, shortcuts).
- `vite.config.ts` (or `.js`): add the `VitePWA` plugin from `vite-plugin-pwa` with `registerType: 'prompt'`, `strategies: 'generateSW'`, manifest reference, `workbox.runtimeCaching` with the four canonical strategies (CacheFirst for hashed assets, NetworkFirst for navigation with `networkTimeoutSeconds: 3`, StaleWhileRevalidate for low-criticality data, NetworkOnly + BackgroundSyncPlugin for POST mutations). If `vite.config.*` already exists, modify it in-place via Edit, do not overwrite.
- `index.html`: insert the iOS meta tag block plus `<link rel="manifest" href="/manifest.webmanifest" crossorigin="use-credentials">` and `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">`.
- Registration: `vite-plugin-pwa` provides `virtual:pwa-register`. Add `import { registerSW } from 'virtual:pwa-register'` and the workbox-window banner pattern (see `service-workers.md`) in `src/main.ts(x)`.
- `public/icons/README.md`: explain the icon requirements (192+512 PNG `any`, 192+512 PNG `maskable`, 180×180 opaque `apple-touch-icon.png`, optional SVG `any`). Include the 40 percent safe-zone rule for maskable icons.
- `public/icons/`: empty stub files (`icon-192.png`, `icon-512.png`, `icon-maskable-192.png`, `icon-maskable-512.png`, `apple-touch-icon.png`) as 0-byte placeholders to make the manifest valid before real icons are supplied.

### Next.js (@serwist/next)

- `app/manifest.ts` (Next.js 14+) returning a `MetadataRoute.Manifest` with the full member set.
- `app/sw.ts` using Serwist (full example from `frameworks-tooling.md` §"Next.js via @serwist/next").
- `next.config.*`: add the `@serwist/next` plugin wrapper.
- `app/layout.tsx`: add the iOS meta tag block via the `<head>` (using `<meta name="apple-mobile-web-app-capable" content="yes" />` etc.). Add `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />`.
- Registration: Serwist exposes `@serwist/next` registration helper. Wire it in `app/layout.tsx`.
- `public/icons/` stubs and README.md as above.

### Angular (ng add @angular/pwa)

- Run `ng add @angular/pwa --project <project-name>` via Bash. This schematic creates the manifest, the SW, registration, and `ngsw-config.json`.
- After the schematic completes, edit `src/manifest.webmanifest` to include the modern members (id, display_override, icons any+maskable, screenshots, shortcuts) that the schematic does not generate by default.
- Edit `src/index.html` to add the iOS meta tag block plus `apple-touch-icon`.
- Edit `ngsw-config.json` to add a `dataGroups` entry with strategy `freshness` for API origins.

### Nuxt (@vite-pwa/nuxt)

- Install `@vite-pwa/nuxt` and add it to `nuxt.config.ts` `modules`.
- Configure the module with the same manifest and workbox config as the Vite case.
- Add the iOS meta tag block via `app.head` in `nuxt.config.ts`.
- `public/icons/` stubs and README.md.

### Vanilla

- `manifest.webmanifest` in the project root.
- `sw.js` in the project root (Workbox 7 patterns hand-written, full example from `service-workers.md`).
- `index.html` updated with manifest link, iOS meta tag block, and inline registration script.
- `icons/` stubs.

## Always-emitted documentation

In addition to the framework artifacts, always create:

- `headers-recommendations.md` in the project root. Documents recommended HSTS, CSP (the example from `security.md`), Permissions-Policy, COOP, COEP, plus `Cache-Control: no-cache` for the service worker file. Each header explained with one-line rationale. NOT auto-applied to deploy config given framework / host variance.
- A short "Next steps" message in the chat: open the manifest in DevTools Application panel, replace the icon stubs with real icons, generate `apple-touch-startup-image` for the target devices (suggest `pwa-asset-generator`), run `/pwa-expert:pwa-checklist` once the app is wired up.

## What this command does NOT do

- Does not generate Capacitor or Cordova projects (out of scope; documented in `distribution.md`).
- Does not generate a push notification server (the `push-notifications.md` reference contains a full Node example; users copy it into their own backend).
- Does not auto-apply security headers to deploy config (too framework-specific and host-specific to do safely; documented in `headers-recommendations.md` instead).
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 130-170.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/commands/pwa-scaffold.md
```

---

### Task 19: Write the pwa-checklist command

**Files:**
- Create: `plugins/pwa-expert/commands/pwa-checklist.md`

- [ ] **Step 1: Write the command file**

```markdown
---
description: Walk the production deploy checklist interactively. Reports pass / fail / N/A per category against the codebase (and optional deployed URL). Distinct from /pwa-audit: this is a deterministic checklist walk, not an open-ended adversarial audit.
argument-hint: "[path or URL]"
---

# /pwa-expert:pwa-checklist

Walk the production deploy checklist from `references/production-checklist.md` interactively against the current project (or the provided URL).

Delegate to `pwa-architect`. The agent reads `production-checklist.md` upfront (this is one of the few cases where preloading a reference is correct — the command IS the checklist), then walks every item.

## Modes

- If `$ARGUMENTS` is a URL: walk the checklist against the live deployment via `playwright-skill` where applicable, plus the codebase for items that can only be verified in source.
- If `$ARGUMENTS` is a path or omitted: walk against the codebase only.

## How the walk works

For every item in every category of `production-checklist.md`:

1. State the item verbatim.
2. Verify it. Use `Read`, `Grep`, `Glob`, `Bash`, or `playwright-skill` tools as appropriate.
3. Record the result as one of: **PASS**, **FAIL**, **N/A** (with a reason for N/A).

## Output format

Produce a markdown report:

```
# Production Checklist Report

**Target:** <path or URL>
**Date:** YYYY-MM-DD

## Summary

| Category | Pass | Fail | N/A | Score |
|---|---|---|---|---|
| Manifest | X | Y | Z | X / (X+Y) |
| iOS-specific | ... |
| Service Worker | ... |
| Security | ... |
| Performance | ... |
| Push | ... |
| Storage | ... |
| Testing | ... |
| Distribution | ... |
| Monitoring | ... |
| **Overall** | ... |

## Manifest

- [PASS] id is explicit (not implied from start_url). Found in `public/manifest.webmanifest:2`.
- [FAIL] Icons: 192 PNG purpose: "maskable" missing. Add via /pwa-expert:pwa-scaffold or by hand.
- ...

(... and so on for every category, every item)

## Recommended next actions

(Numbered list of the highest-impact fails, ordered by severity.)
```

## Difference from /pwa-expert:pwa-audit

- `pwa-audit` is open-ended and adversarial. It uses domain knowledge to find defects the checklist does not enumerate.
- `pwa-checklist` is deterministic. The output maps 1:1 to the source guide's deploy checklist sections. Two runs on the same target produce structurally identical reports.

Use `pwa-checklist` for release gates and CI integration. Use `pwa-audit` for design reviews and pre-launch deep-dives.

## Output rules

- No emojis. Status indicators are text only: `[PASS]`, `[FAIL]`, `[N/A]`.
- Cite a file and line for every PASS / FAIL where possible (local mode) or a URL fragment / manifest field (live mode).
- Recommend the matching reference file from the knowledge base for every FAIL, so the user can self-serve the fix.
```

- [ ] **Step 2: Verify**

Run the universal verification snippet. Target line count: 80-110.

- [ ] **Step 3: Stage**

```bash
git add plugins/pwa-expert/commands/pwa-checklist.md
```

---

### Task 20: Register the plugin in marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read the current marketplace.json header**

```bash
head -20 .claude-plugin/marketplace.json
```

Note the current `metadata.version`.

- [ ] **Step 2: Find the end of the `plugins` array**

```bash
grep -nE '^\s*\]\s*$' .claude-plugin/marketplace.json | tail -5
```

The `plugins` array close is the right insertion point for the new entry.

- [ ] **Step 3: Insert the new plugin entry**

Use `Edit` to add this object as the last element in the `plugins` array (right before the closing `]`). Add a comma to the previous last entry's closing brace if needed.

```json
    {
      "name": "pwa-expert",
      "source": "./plugins/pwa-expert",
      "description": "Progressive Web App expert covering manifest (id, display_override, scope_extensions, handle_links, file_handlers, share_target), service workers (Workbox 7 / Serwist), Web Push (VAPID, RFC 8030/8291/8292, Declarative Push for Safari 18.4+), install flows (beforeinstallprompt, Window Controls Overlay), OPFS storage, Project Fugu capabilities, Core Web Vitals 2025 (INP < 200ms), and distribution (Bubblewrap to Google Play, PWA Builder to Microsoft Store, Capacitor to App Store, PWA Builder to Meta Quest). 2025-2026 baseline.",
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

- [ ] **Step 4: Bump metadata.version**

Edit the `metadata.version` field. The bump is **minor** (intake of a new plugin). Example: `2.10.1` → `2.11.0`. Read the actual current value first, then apply the minor bump.

- [ ] **Step 5: Validate JSON**

```bash
python -c "import json; json.load(open('.claude-plugin/marketplace.json'))" && echo "OK"
```

If `python` is not available: `node -e "JSON.parse(require('fs').readFileSync('.claude-plugin/marketplace.json'))" && echo "OK"`.

- [ ] **Step 6: Stage**

```bash
git add .claude-plugin/marketplace.json
```

---

### Task 21: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Bump the plugin count and append the name**

Find the line that starts "43 plugins:" and update to "44 plugins:", and append `, pwa-expert` to the comma-separated list (right after `kotlin-development`).

Use `Edit` with `old_string`:
```
43 plugins: clean-code, deep-dive-analysis, tauri-development, frontend, react-development, xterm, ai-tooling, python-development, stripe, system-utils, messaging, research, business, project-setup, app-analyzer, typescript-development, csp, digital-marketing, senior-review, obsidian-development, browser-extensions, learning, marketplace-ops, playwright-skill, acp-hooks, prompt-improver, cc-usage, codebase-mapper, git-worktrees, rag-development, docs, testing, platform-engineering, ibkr-trading, mt5-trading, opentelemetry, docker, grabber-development, agent-teams, reverse-engineering, codebase-cleanup, libgdx-development, kotlin-development.
```

and `new_string`:
```
44 plugins: clean-code, deep-dive-analysis, tauri-development, frontend, react-development, xterm, ai-tooling, python-development, stripe, system-utils, messaging, research, business, project-setup, app-analyzer, typescript-development, csp, digital-marketing, senior-review, obsidian-development, browser-extensions, learning, marketplace-ops, playwright-skill, acp-hooks, prompt-improver, cc-usage, codebase-mapper, git-worktrees, rag-development, docs, testing, platform-engineering, ibkr-trading, mt5-trading, opentelemetry, docker, grabber-development, agent-teams, reverse-engineering, codebase-cleanup, libgdx-development, kotlin-development, pwa-expert.
```

- [ ] **Step 2: Add pwa-expert to the "Fast" freshness-class row**

Find the row in the "Freshness risk classes" table that lists "Fast" examples. The current example list is `libgdx-development, opentelemetry, tauri-development, stripe (API additions, webhook event types), grabber-development (anti-bot vendor moves), browser-extensions`. Append `, pwa-expert (browser version churn, WebKit feature rollout, framework PWA library churn)`.

Use `Edit` with the exact `old_string` from the current CLAUDE.md table cell and the new content. Read CLAUDE.md first to get the exact current cell content (it may have evolved since this plan was written).

- [ ] **Step 3: Stage**

```bash
git add CLAUDE.md
```

---

### Task 22: Run skills validation

- [ ] **Step 1: Run /marketplace-ops:skills-validate against the new plugin**

```
Invoke: Skill tool with skill="marketplace-ops:skills-validate" and args="plugins/pwa-expert"
```

Confirm there are no Critical or Important findings. If there are, fix them inline (most likely candidates: description over 1024 chars, missing TRIGGER WHEN, body too long, no examples in agent body).

- [ ] **Step 2: Run /marketplace-ops:marketplace-health**

```
Invoke: Skill tool with skill="marketplace-ops:marketplace-health"
```

Confirm the JSON is valid, `pwa-expert` appears in the plugin count, all referenced paths exist.

- [ ] **Step 3: Final structural greps**

```bash
# Dash-aside construct check across all new files
grep -rnE ' — | -- | - ' plugins/pwa-expert/ | grep -v '^\s*[-*]' | head -20

# Emoji check
grep -rnP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' plugins/pwa-expert/ | head -5

# Italian leftover check
grep -rniE '\b(che|della|dello|delle|degli|sono|essere|questo|questa|quando|perché|anche|tutto|tutta|tutti)\b' plugins/pwa-expert/ | head -10

# Confirm each reference file is within the 250-700 line band
wc -l plugins/pwa-expert/skills/pwa-development/references/*.md
```

Fix any flagged content inline before the final commit.

- [ ] **Step 4: Confirm the staged file set**

```bash
git status --short
```

Should show every new file under `plugins/pwa-expert/`, the modified `.claude-plugin/marketplace.json`, and the modified `CLAUDE.md`.

---

### Task 23: Final commit

- [ ] **Step 1: Verify the staged set is complete**

```bash
git diff --cached --stat
```

Expected:
- 19 new files under `plugins/pwa-expert/` (1 agent + 3 commands + 1 SKILL.md + 14 references)
- 1 modified file: `.claude-plugin/marketplace.json`
- 1 modified file: `CLAUDE.md`

Total: 19 files added, 2 modified.

- [ ] **Step 2: Create the commit**

```bash
git commit -m "$(cat <<'EOF'
Add pwa-expert plugin for Progressive Web App development (v1.0.0)

New plugin covering 2025-2026 PWA baseline:
- pwa-architect agent for end-to-end PWA design and implementation
- /pwa-expert:pwa-audit (local code + live URL via Playwright)
- /pwa-expert:pwa-scaffold (manifest + SW + iOS meta + framework wiring for Vite, Next.js, Angular, Nuxt, vanilla)
- /pwa-expert:pwa-checklist (production deploy checklist walk)
- pwa-development knowledge skill with 14 references: manifest, service workers, background execution, push notifications (RFC 8030/8291/8292, Declarative Push), install flows, permissions, storage/OPFS, Fugu capabilities, platform constraints, performance (CWV 2025), security, distribution, frameworks-tooling, production checklist

Bumps marketplace metadata.version to <new>.
Updates CLAUDE.md plugin count 43→44 and adds pwa-expert to the Fast freshness-class row.
EOF
)"
```

- [ ] **Step 3: Verify the commit**

```bash
git log --oneline -1
git show --stat HEAD
```

Confirm 21 files (19 added + 2 modified). Push when ready (do NOT auto-push):

```
# Suggest to user, do not auto-execute:
# git push
```

---

## Self-review checklist

Before declaring the plan complete, the planner walks this list:

**Spec coverage:** Every section of the design doc maps to at least one task.
- [x] Goal and scope (covered by overall task set)
- [x] Approved decisions (encoded in Tasks 16-19 component specs)
- [x] Plugin layout (Tasks 1-19 create every listed file)
- [x] Agent body structure (Task 16)
- [x] SKILL.md router (Task 15)
- [x] All 14 references (Tasks 1-14, in topic order)
- [x] /pwa-audit command (Task 17)
- [x] /pwa-scaffold command (Task 18)
- [x] /pwa-checklist command (Task 19)
- [x] Marketplace registration (Task 20)
- [x] License and attribution (no action needed; documented in design)
- [x] Style and convention compliance (verification snippet runs after every file)
- [x] All 11 acceptance criteria covered

**Placeholder scan:** No "TBD", "TODO", "implement later", "add appropriate error handling", "similar to Task N" anywhere in this plan.

**Type / name consistency:**
- Agent name `pwa-architect` used consistently in Task 16, agent body, SKILL.md, and command files.
- Skill name `pwa-development` used consistently in agent References Library, SKILL.md frontmatter, and command files that reference it.
- Command names `pwa-audit`, `pwa-scaffold`, `pwa-checklist` consistent across the plan, marketplace.json, and command file headers.
- Reference file names (snake_case-free, hyphenated) consistent across SKILL.md table, agent References Library table, plan File Structure table, and individual tasks.

No discrepancies found.
