# Production Deployment Checklist

Field-tested checklist for shipping a Progressive Web App to production in 2025-2026. Walk this before every release. Each item has a verification step and a reference to the relevant section of the knowledge base.

## How to use this checklist

Three pass criteria:

- **PASS**: requirement is met and verified.
- **FAIL**: requirement is unmet and ships a defect.
- **N/A**: requirement does not apply to this target platform.

The `/pwa-checklist` command walks this list interactively against a codebase (and optionally a deployed URL) and produces a deterministic pass/fail dashboard. The `/pwa-audit` command runs an open-ended adversarial audit instead; use this checklist when you want a structured release gate, the audit when you want to find defects the checklist does not enumerate.

## 1. Manifest

- [ ] `id` is explicit (not implied from `start_url`). See `manifest.md`.
- [ ] `name`, `short_name`, `description`, `start_url`, `scope` all present.
- [ ] `display: "standalone"` plus `display_override` including `window-controls-overlay` when desktop is a target.
- [ ] `theme_color` and `background_color` set.
- [ ] Icons: 192 PNG `purpose: "any"`, 512 PNG `purpose: "any"`, 192 PNG `purpose: "maskable"`, 512 PNG `purpose: "maskable"`. SVG `purpose: "any"` optional.
- [ ] Screenshots include at least one `form_factor: "wide"` and one `form_factor: "narrow"`.
- [ ] `shortcuts` defines at least two primary actions.
- [ ] `share_target` defined if the app accepts shared content.
- [ ] `lang` and `dir` set.
- [ ] Served with `Content-Type: application/manifest+json`.

## 2. iOS-specific

- [ ] `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">` (opaque PNG, no transparency).
- [ ] `<meta name="apple-mobile-web-app-capable" content="yes">`.
- [ ] `<meta name="apple-mobile-web-app-status-bar-style">` set (typically `black-translucent`).
- [ ] `<meta name="apple-mobile-web-app-title">` set.
- [ ] `apple-touch-startup-image` declared for each target device combination (width, height, pixel ratio, orientation).
- [ ] Custom "Add to Home Screen" hint shown only when `display-mode: browser` matches.
- [ ] Web Push tested only after install plus an explicit user gesture (iOS 16.4+ requirement).
- [ ] `viewport-fit=cover` plus `env(safe-area-inset-*)` CSS used for layout safety.

## 3. Service Worker

- [ ] `/sw.js` (or framework equivalent) served from the root with `Cache-Control: no-cache`.
- [ ] App-shell pre-cache uses a versioned cache name (the `app-shell-v7` pattern).
- [ ] Distinct runtime strategies for asset, API, and navigation routes.
- [ ] Old caches cleaned up in the `activate` event.
- [ ] User-driven update flow with an "Update now" banner. No silent `skipWaiting()`.
- [ ] Offline fallback page exists and is precached.

## 4. Security

- [ ] HTTPS with HSTS (`max-age=31536000; includeSubDomains; preload`).
- [ ] Restrictive CSP that covers `script-src`, `worker-src`, `connect-src`, `img-src`, `object-src`, `base-uri`, `frame-ancestors`.
- [ ] `Permissions-Policy` header restricts capabilities for third-party iframes.
- [ ] CORS correctly configured on every API origin the SW or page calls.
- [ ] COOP + COEP if `SharedArrayBuffer` is needed (for example, sqlite-wasm on OPFS).

## 5. Performance

- [ ] LCP < 2.5 s at p75.
- [ ] INP < 200 ms at p75.
- [ ] CLS < 0.1 at p75.
- [ ] Critical JS bundle < 170 KB compressed.
- [ ] `fetchpriority="high"` on the LCP image.
- [ ] Route-based code splitting.
- [ ] HTTP/2 or HTTP/3 with Brotli or Zstd compression.

## 6. Push

- [ ] VAPID keys generated and stored in a secret manager.
- [ ] Subscription endpoint with automatic cleanup (HTTP 410 deletes the row).
- [ ] `userVisibleOnly: true` set in the client subscription.
- [ ] `notificationclick` handler with focus-existing or open-window logic.
- [ ] Tested on installed iOS PWA, Android Chrome, and Desktop Chrome or Edge.

## 7. Storage

- [ ] `navigator.storage.estimate()` monitored.
- [ ] `navigator.storage.persist()` requested after a meaningful engagement event (not at page load).
- [ ] IndexedDB cleanup logic exists for quota pressure.
- [ ] Fallback strategy documented for Safari ITP 7-day cap on non-installed PWAs.

## 8. Testing

- [ ] Lighthouse individual PWA audits in CI. The PWA category itself was removed in Lighthouse 12.0.0 (Chrome 126), so audit the individual checks from the Application panel.
- [ ] PWA Builder score >= 80.
- [ ] Real offline test performed (DevTools "Offline" plus a full reload of a non-cached page).
- [ ] Tested on a physical iPhone. Safari Web Inspector cannot inspect installed Home Screen PWAs, so an in-app diagnostic fallback is wired in (Eruda or a hidden tap sequence).
- [ ] Install tested on Android (WebAPK) and Desktop Chrome or Edge.
- [ ] Update flow tested end-to-end (deploy version 2, confirm the banner appears, confirm the reload picks up the new SW).

## 9. Distribution

- [ ] Bubblewrap to Google Play with a valid `/.well-known/assetlinks.json`. Without it, the TWA degrades to a Custom Tab with a visible URL bar.
- [ ] PWA Builder to Microsoft Store (MSIX package via Partner Center).
- [ ] Capacitor wrapper for the App Store if a web-only distribution is not acceptable. Apple Guideline 4.2.2 rejects pure web clippings.

## 10. Monitoring

- [ ] `appinstalled` event sent to analytics.
- [ ] CrUX or RUM tracking the three Core Web Vitals.
- [ ] Sentry or equivalent error tracking inside the service worker.
- [ ] Heartbeat handler for `pushsubscriptionchange`.
