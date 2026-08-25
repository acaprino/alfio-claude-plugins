---
name: pwa-development
description: >
  Knowledge base for the app layer of the web platform, and the gaps between engines.
  TRIGGER WHEN: building or auditing a PWA: Web App Manifest, service workers, Workbox, Serwist, vite-plugin-pwa, @angular/pwa, @vite-pwa/nuxt, Web Push, VAPID, Declarative Push, beforeinstallprompt, Window Controls Overlay, OPFS, Background Sync, Wake Lock, Project Fugu, Bubblewrap, TWA, PWA Builder, Capacitor.
  DO NOT TRIGGER WHEN: React performance (use react-development:review-react), non-PWA platform security (use platform-engineering), or Tauri and Electron shells (use tauri-development).
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
