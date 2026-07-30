---
name: pwa-development
description: >
  Progressive Web App knowledge base for 2025-2026: Web App Manifest, Service Workers (Workbox 7,
  Serwist), Web Push (VAPID, RFC 8030/8291/8292, Declarative Push for Safari 18.4+), install flows
  (beforeinstallprompt, Window Controls Overlay), OPFS storage, Project Fugu, Core Web Vitals (INP
  < 200ms), security (HTTPS, CSP, COOP/COEP), and distribution (Bubblewrap, PWA Builder MSIX,
  Capacitor). Use when building, auditing, or debugging PWAs, including manifest, service worker,
  Web Push, install flow, OPFS, Background Sync, Wake Lock, vite-plugin-pwa, Next.js Serwist,
  @angular/pwa, @vite-pwa/nuxt, Bubblewrap, TWA, PWA Builder, or Capacitor wrapping. Not for generic
  frontend styling, React performance, cross-platform security unrelated to PWAs, Tauri or Electron
  wrappers, or GA4 and analytics: sibling bundles in the same catalog cover those.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: pwa-expert
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
