---
description: >
  Checks manifest, install criteria, offline behavior, security headers and performance, locally or against a live URL, citing file and line.
  TRIGGER WHEN: auditing a PWA, or verifying one is installable and production-ready.
argument-hint: "[path | URL]"
---

# /pwa-expert:pwa-audit

Adversarial PWA audit. Two modes, auto-detected from `$ARGUMENTS`:

- **Live URL mode:** if the argument starts with `http://` or `https://`, fetch the page with Playwright, parse the manifest, test install criteria, check security headers, test offline behavior, and measure Core Web Vitals on the landing page.
- **Local code mode:** otherwise, treat the argument as a path (default: current working directory). Locate the manifest file, service worker source, registration call, iOS meta tag block, and security-header configuration in the codebase. Parse and check.

## Setup

Delegate this audit to the `pwa-architect` agent. The agent must read the relevant references from the `pwa-development` skill on-demand (not all upfront), targeting each section of the audit.

Reference reading order, as audit sections are reached:

- Manifest checks: `references/manifest.md`, `references/production-checklist.md` §1.
- Install criteria and prompts: `references/install-flows.md`.
- Service worker logic: `references/service-workers.md`.
- Security headers: `references/security.md`.
- Offline behavior: `references/service-workers.md` and `references/storage-persistence.md`.
- Performance metrics: `references/performance.md`.
- Push notifications: `references/push-notifications.md`.
- Framework-specific files: `references/frameworks-tooling.md`.

## Mode A: Live URL

If `$ARGUMENTS` is a URL, use the `playwright-skill` tools:

1. Launch a browser and navigate to the URL.
2. Fetch `/manifest.webmanifest` (and fall back to `/manifest.json`). Validate as JSON. Run the manifest checklist from `production-checklist.md` §1.
3. Check the service worker registration: look for a `<script>` registering `navigator.serviceWorker.register(...)`, or for an existing controller via `navigator.serviceWorker.controller`.
4. Check the install criteria from `install-flows.md`: manifest valid, `display` not `browser`, SW registered with `fetch` handler, HTTPS, 192+512 PNG icons present.
5. Check meta tags: `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, `apple-mobile-web-app-title`, `apple-touch-icon`, `theme-color`, `viewport`.
6. Check security headers via response headers: HTTPS plus HSTS, CSP presence (warn if `'unsafe-eval'` is allowed), `Cross-Origin-Opener-Policy`, `Cross-Origin-Embedder-Policy`.
7. Test offline behavior: route the page through `page.context().setOffline(true)`, reload, and confirm a non-broken response (offline page or cached navigation).
8. Measure Core Web Vitals on the landing page (LCP, CLS at least; INP requires interaction). Compare against `performance.md` thresholds.

If `playwright-skill` is unavailable, tell the user to install it from its upstream marketplace (`claude plugin marketplace add lackeyjb/playwright-skill`, then `claude plugin install playwright-skill@playwright-skill`), and meanwhile fall back to suggesting manual checks and explain what each would verify. In that fallback path, the audit should still produce a structured report with explicit "could not verify" markers for any item that required browser automation.

Live-mode auth note: if the target URL is behind authentication, ask the user via `AskUserQuestion` whether to run the audit against a public route only, or whether the user can provide login steps. Never attempt to bypass auth.

## Mode B: Local code

If `$ARGUMENTS` is a path or omitted, search the codebase:

1. Find the manifest: `Glob` for `manifest.webmanifest`, `manifest.json`, `app/manifest.ts` (Next.js 14+), `src/manifest.ts`. Parse and verify against `production-checklist.md` §1.
2. Find the SW source: `Glob` for `sw.js`, `sw.ts`, `service-worker.js`, `service-worker.ts`, `app/sw.ts` (Serwist), `ngsw-config.json` (Angular). Read and audit caching strategies, `skipWaiting` / `clients.claim` use, cleanup in `activate`, offline fallback.
3. Find the SW registration: `Grep` for `serviceWorker.register`, `workbox-window`, `Workbox(`, `Serwist(`, or Next.js implicit registration via `@serwist/next`.
4. Find iOS meta tags: `Grep` for `apple-mobile-web-app-capable`. Confirm the full block from `manifest.md` §"iOS meta tag block".
5. Find security headers: read `next.config.*` (Next.js headers function), `vite.config.*` plus any `server` plugin, `nginx.conf` / `.htaccess` if present, `firebase.json` `hosting.headers`, `vercel.json` `headers`. Check HSTS, CSP, COOP, COEP, Permissions-Policy.
6. Find Web Push: `Grep` for `pushManager.subscribe`, `setVapidDetails`, `web-push`. If found, audit the subscription flow and server-side delivery against `push-notifications.md`.
7. Find storage usage: `Grep` for `localStorage.`, `IDBDatabase`, `openDB(`, `navigator.storage`. Flag anti-patterns from `storage-persistence.md` (for example, `localStorage` used for large data).
8. Detect framework via `package.json` and configs. Apply framework-specific checks from `frameworks-tooling.md` (Vite vite-plugin-pwa config, Serwist app/sw.ts, Angular ngsw-config.json structure).

If the codebase contains a build artifact directory (`dist/`, `.next/`, `build/`), do not audit the generated SW from there. Always work from source. Generated SW files are derivative and may be stale relative to config.

## Common defects to look for

Patterns the audit should treat as Critical until proven otherwise:

- A service worker that calls `self.skipWaiting()` without a coordinated client reload. Causes mid-session resource version mismatches and broken navigations.
- A `cache.addAll([...])` precache list with no version suffix or hash strategy. Caches go stale forever after first install.
- An offline fallback page that itself fetches uncached subresources. The fallback fails open in network outages.
- A manifest with `display: "standalone"` but no maskable icon at 192 and 512. Android adaptive launchers fall back to a generated badge.
- A CSP that includes `'unsafe-inline'` for `script-src` in production. Treat as Critical unless paired with a nonce or hash strategy.
- Web Push subscriptions persisted without `expirationTime` handling or a server-side resubscribe path. Silent delivery failures accumulate.

Patterns to flag as Important:

- A service worker fetch handler that calls `event.respondWith(fetch(event.request))` unconditionally. Adds latency for zero caching benefit.
- A manifest `start_url` lacking a tracking parameter (for example `?source=pwa`). Analytics cannot distinguish installed-app sessions.
- An `apple-touch-icon` smaller than 180×180 or with transparency. iOS renders a black background on the Home Screen.

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

Numbering convention: `C1, C2, ...` for Critical, `I1, I2, ...` for Important, `N1, N2, ...` for Nice-to-have. Stable IDs let the user reference findings in follow-up prompts.

Fix guidance must be concrete. Prefer a code snippet or an exact path-and-value change over a vague "consider improving this". If the fix is large, link to the relevant reference section and summarize the first concrete step.

## iOS caveat

If the target is iOS-focused, prepend the report with a clear note that Safari Web Inspector cannot inspect installed Home Screen PWAs. Live-mode audit therefore covers only the in-browser experience, not the post-install standalone state.

Concrete consequence: behaviors that only manifest once the app is added to the Home Screen (standalone display, status bar styling, safe-area insets, splash screens, Web Push permission in iOS 16.4+) cannot be observed remotely. Recommend that the user run a manual install-and-launch pass on a real iOS device, ideally on the lowest supported iOS version in their target matrix.

If the user has access to a Mac plus a wired iOS device, recommend the desktop Safari "Develop" menu attached to the in-Safari tab. This is the closest available approximation to inspecting the installed app but still does not reach the installed standalone surface.
