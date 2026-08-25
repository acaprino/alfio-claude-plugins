# Frameworks and Tooling

PWA delivery in 2025-2026 leans on a small set of mature framework integrations. Vite ships the most flexible standalone plugin, Next.js has migrated from the unmaintained `next-pwa` to Serwist, Angular keeps its built-in `@angular/pwa` schematic, and Nuxt has an official Vite PWA module. For teams that need a single codebase distributed to native stores, Capacitor wraps the PWA in a native WebView and exposes native plugins. This reference covers each integration plus the debugging and testing surface available in 2025-2026.

## Vite via vite-plugin-pwa

`vite-plugin-pwa` is the official Vite PWA integration. It wraps Workbox 7 and supports both `generateSW` (the plugin builds the service worker for you from your Workbox config) and `injectManifest` (you write the SW yourself and the plugin injects the precache manifest into it).

A typical configuration with `generateSW` and a NetworkFirst runtime strategy for API calls:

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'prompt',
      strategies: 'generateSW',
      manifest: { /* ... */ },
      workbox: {
        navigateFallback: '/index.html',
        runtimeCaching: [{
          urlPattern: ({ url }) => url.origin === 'https://api.acme.com',
          handler: 'NetworkFirst',
          options: { cacheName: 'api', networkTimeoutSeconds: 3 }
        }]
      }
    })
  ]
});
```

Key configuration knobs:

- `registerType: 'prompt'` exposes a registration helper that the application can call to ask the user whether to reload when a new service worker is waiting. The alternative `'autoUpdate'` calls `skipWaiting()` on every update, which is dangerous for runtime state (see the service-workers reference).
- `strategies: 'generateSW'` lets Workbox build the service worker from the plugin's config. Use `'injectManifest'` to author the SW manually and only inject the precache manifest.
- `manifest` accepts the full Web App Manifest object. The plugin writes `manifest.webmanifest` and a `<link rel="manifest">` tag automatically.
- `workbox.navigateFallback` provides the SPA shell route to fall back to for navigation requests that miss the precache.
- `workbox.runtimeCaching` is an array of routes with a URL pattern matcher and a Workbox strategy. NetworkFirst with `networkTimeoutSeconds: 3` is the standard pattern for an API that should prefer fresh data but fall back to cache after a short timeout.

### Version constraint

`vite-plugin-pwa` v1.3.0 (the latest on npm as of May 2026) requires:

- Node 20.19+ or 22.12+
- Vite 7+

Vite 7 raised the minimum Node requirement to 20.19+ after Node 18 reached end-of-life in April 2025. This is documented in the Vite 7 announcement (`vite.dev/blog/announcing-vite7`). Teams on older toolchains must either upgrade or pin to an older `vite-plugin-pwa` release that supports Vite 6.

### Registering the service worker from application code

The plugin exposes a virtual module `virtual:pwa-register` (or `virtual:pwa-register/react`, `virtual:pwa-register/vue`, etc.) that returns a registration helper. With `registerType: 'prompt'`, the application receives `needRefresh` and `offlineReady` signals and decides when to reload:

```ts
import { registerSW } from 'virtual:pwa-register';

const updateSW = registerSW({
  onNeedRefresh() {
    // Show a banner: "A new version is available. Reload?"
    if (userConfirmsReload()) {
      updateSW(true);
    }
  },
  onOfflineReady() {
    // Show a toast: "Ready to work offline."
  }
});
```

This is the recommended pattern. Calling `updateSW(true)` triggers `skipWaiting` on the waiting service worker and then reloads the page after the new SW takes control.

## Next.js via @serwist/next

The original `next-pwa` library is unmaintained since 2022. Its successor fork `@ducanh2912/next-pwa` now explicitly points users to Serwist. Serwist is a TypeScript-first rewrite of Workbox with first-class Next.js support via `@serwist/next`.

A minimal service worker file at `app/sw.ts` using the App Router:

```ts
// app/sw.ts
import { defaultCache } from '@serwist/next/worker';
import { Serwist } from 'serwist';

declare const self: ServiceWorkerGlobalScope;
const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: defaultCache,
  fallbacks: { entries: [{ url: '/offline', matcher: ({ request }) => request.destination === 'document' }] }
});
serwist.addEventListeners();
```

Walkthrough of each option:

- `precacheEntries: self.__SW_MANIFEST` consumes the precache manifest that Serwist injects at build time. The constant is replaced during the build with the array of assets Next.js emitted.
- `skipWaiting: true` activates the new SW immediately on install. Acceptable in this template because the runtime caching strategy revalidates aggressively, but production apps with long-lived sessions should consider the user-driven reload pattern instead.
- `clientsClaim: true` takes control of open clients on first activation. Useful for the initial install.
- `navigationPreload: true` enables HTTP/2 navigation preload, letting the browser kick off the navigation request in parallel with the service worker bootstrap.
- `runtimeCaching: defaultCache` reuses Serwist's curated default strategies (static assets CacheFirst, JSON NetworkFirst, fonts CacheFirst with long expiration, etc.).
- `fallbacks.entries` registers an offline document fallback. When a navigation request fails and is not in the cache, Serwist serves `/offline` instead.

### Web App Manifest in Next.js 14+

Next.js 14+ supports `app/manifest.ts` natively. The file exports a default function returning a manifest object, and Next.js serves it at `/manifest.webmanifest` with the correct `Content-Type`:

```ts
// app/manifest.ts
import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Acme',
    short_name: 'Acme',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#0a0a0a',
    icons: [
      { src: '/icons/192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icons/512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/icons/192-maskable.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
      { src: '/icons/512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
    ]
  };
}
```

No manual `<link rel="manifest">` tag is required; the metadata API wires it up automatically.

### Build configuration

In `next.config.js`, wrap the export with `withSerwist` and point it at the SW source and destination:

```js
// next.config.js
const withSerwist = require('@serwist/next').default({
  swSrc: 'app/sw.ts',
  swDest: 'public/sw.js'
});

module.exports = withSerwist({
  // standard Next.js config
});
```

The plugin compiles `app/sw.ts` and emits the final service worker to `public/sw.js`, which Next.js then serves at `/sw.js` with the right scope.

## Angular Service Worker

Angular ships an official PWA schematic. Run once to add manifest, service worker, default icons, and the bootstrap wiring:

```bash
ng add @angular/pwa
```

This generates:

- `src/manifest.webmanifest` with a starter manifest.
- `ngsw-config.json` controlling the service worker behavior.
- A registration call in `app.config.ts` or `app.module.ts`.
- Default icon set in `src/assets/icons/`.

Cache strategies are declared in `ngsw-config.json` using two top-level arrays:

- `assetGroups` for application assets (HTML, JS, CSS, images bundled at build time).
- `dataGroups` for runtime API data fetched from the network.

A typical `ngsw-config.json`:

```json
{
  "$schema": "./node_modules/@angular/service-worker/config/schema.json",
  "index": "/index.html",
  "assetGroups": [
    {
      "name": "app",
      "installMode": "prefetch",
      "resources": {
        "files": ["/favicon.ico", "/index.html", "/manifest.webmanifest", "/*.css", "/*.js"]
      }
    },
    {
      "name": "assets",
      "installMode": "lazy",
      "updateMode": "prefetch",
      "resources": {
        "files": ["/assets/**", "/*.(svg|cur|jpg|jpeg|png|apng|webp|avif|gif|otf|ttf|woff|woff2)"]
      }
    }
  ],
  "dataGroups": [
    {
      "name": "api-perf",
      "urls": ["/api/static/**"],
      "cacheConfig": {
        "maxSize": 200,
        "maxAge": "1d",
        "strategy": "performance"
      }
    },
    {
      "name": "api-fresh",
      "urls": ["/api/live/**"],
      "cacheConfig": {
        "maxSize": 100,
        "maxAge": "1h",
        "timeout": "3s",
        "strategy": "freshness"
      }
    }
  ]
}
```

Strategy mapping:

- `'performance'` approximates CacheFirst: serve from cache when available, fetch in the background to refresh.
- `'freshness'` approximates NetworkFirst: try the network first, fall back to cache on timeout or failure. The `timeout` field maps to the network timeout before falling back.

`installMode` and `updateMode` control whether assets are prefetched at install time or lazily fetched on first request. `prefetch` everything that the user is likely to need immediately; `lazy` everything else.

## Nuxt via @vite-pwa/nuxt

`@vite-pwa/nuxt` is the official Vite PWA module for Nuxt 3+. It is a thin layer on top of `vite-plugin-pwa` that wires the manifest and service worker registration into Nuxt's module system.

Install and add to `nuxt.config.ts`:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@vite-pwa/nuxt'],
  pwa: {
    registerType: 'prompt',
    manifest: {
      name: 'Acme',
      short_name: 'Acme',
      theme_color: '#0a0a0a'
    },
    workbox: {
      navigateFallback: '/'
    },
    devOptions: {
      enabled: true,
      type: 'module'
    }
  }
});
```

The `devOptions` block enables the service worker in `nuxt dev` for end-to-end testing without a production build. This is opt-in because a registered service worker during development can hide source changes behind aggressive caching.

## Capacitor (Ionic)

For teams that need a single codebase distributed to the App Store as well as the web, Capacitor wraps the PWA in a native WebView and exposes bridges to native plugins. This is the standard path to ship a PWA-style codebase to iOS where Apple does not accept pure PWAs (App Store Guideline 4.2.2 against web clippings).

Capacitor architecture in two lines:

- The web app runs in a `WKWebView` on iOS or a `WebView` on Android.
- JavaScript code calls Capacitor bridges that invoke native APIs and return results asynchronously.

Common native plugins:

- `@capacitor/push-notifications` for native APNs / FCM push (instead of Web Push, which is constrained on iOS).
- `@capacitor/geolocation` for native-accuracy location, including background location on Android.
- `@capacitor/biometric` for Face ID, Touch ID, and Android biometric authentication.
- `@capacitor/share` for the native share sheet.
- `@capacitor/filesystem` for direct file access outside the sandboxed web storage.

A typical setup:

```bash
npm install @capacitor/core @capacitor/cli
npx cap init "Acme" "com.acme.app" --web-dir=dist
npx cap add ios
npx cap add android
npx cap sync
npx cap open ios
```

The `web-dir` points at the built PWA output (Vite `dist/`, Next.js exported `out/`, Angular `dist/<project>/`). `npx cap sync` copies the web assets into the iOS and Android projects and updates the native dependencies.

Trade-offs compared to a pure PWA:

- Distribution: Capacitor apps can ship to the App Store and the Play Store as native apps, opening App Store-only acquisition channels.
- Capabilities: native plugins unlock APIs that the PWA cannot reach on iOS (background location, biometric, native push).
- Cost: requires Apple Developer account ($99/year) and Google Play Console fee ($25 one-time).
- Maintenance: every native plugin adds an upgrade cycle and a potential point of failure on OS updates.

For Web Push specifically, Capacitor recommends `@capacitor/push-notifications` over Web Push on iOS because native APNs is more reliable and supports the silent and provisional notification modes that Web Push does not expose.

## Debugging surface

The debugging surface for PWAs in 2025-2026 is concentrated in three browsers, each with different strengths.

### Chrome and Edge DevTools (Application panel)

Chrome and Edge DevTools share the same Application panel. The panel covers every PWA-relevant runtime aspect:

- **Manifest viewer** with Window Controls Overlay emulation. Lets the developer preview how the manifest is parsed, see the resolved icons, and test the WCO layout without installing the app.
- **Service Workers** view showing the lifecycle state (installing, waiting, active, redundant), the SW version, and buttons to update, unregister, push, sync, and trigger the offline mode.
- **Storage** summary listing every storage backend (IndexedDB, Cache Storage, Service Worker, Local Storage, Session Storage, Cookies, Web SQL) and the size each consumes.
- **Cache Storage** browser showing every named cache, the requests inside, and the cached response headers.
- **IndexedDB** browser with per-database, per-objectStore inspection and the ability to delete entries.
- **Background Services** panel recording Background Fetch and Periodic Background Sync events for up to 3 days. Critical for debugging registrations that never fire: the panel logs every registration, success, and failure.
- **Quota and estimated remaining storage** showing the per-origin quota and current usage.

### Safari Web Inspector (remote)

Safari Web Inspector connects from a macOS Safari instance to an iOS device over USB or wireless. The limit that catches every PWA developer:

- **Safari tab on iOS is inspectable.**
- **Standalone PWAs are NOT inspectable.** Installed Home Screen Web Apps run in a separate process container that Web Inspector cannot reach. This is a historical limit that has persisted across every iOS release including iOS 26.

This forces an alternative debugging strategy for installed PWAs on iOS:

- Build an in-app diagnostic page that surfaces `console.log` output, errors, network state, and storage estimates to the screen.
- Use `Eruda` or a similar in-page console for ad-hoc inspection.
- Pipe errors to a remote error tracker (Sentry, LogRocket) so production issues are visible without device access.
- Reproduce in mobile Safari tab first when possible, then validate the install behavior separately.

### PWA Builder Validator and Lighthouse

Two complementary tooling layers:

- **PWA Builder Validator** at `pwabuilder.com` runs a manifest, service worker, and security check, scores the PWA against a cross-platform readiness rubric, and generates store packages (MSIX for Microsoft Store, APK for Google Play, etc.).
- **Lighthouse PWA checks** survive as individual audits in DevTools, even though the dedicated PWA category was removed in Lighthouse 12.0.0 (Chrome 126, May 2024). The individual checks remain available in the Application panel and can be scripted in CI via the Lighthouse Node API.

The removal of the PWA category does NOT mean PWAs are deprecated. The Lighthouse team rationale was that the category had become too fragmented to summarize as a single score; the underlying checks still exist and are still recommended.

### DevTools network and CPU throttling

DevTools exposes throttling presets that simulate constrained environments:

- **Slow 3G** for a worst-case mobile network. Useful for validating that the app shell is precached and that NetworkFirst routes have a `networkTimeoutSeconds` short enough to fall back gracefully.
- **Offline** for end-to-end offline testing. Critical for verifying the SW fetch handler covers every route the user might hit.
- **CPU 4x slowdown** for simulating low-end Android devices. Useful for validating INP under load and catching long tasks that block the main thread.

Combine these: run the app in Offline mode with CPU 4x slowdown to expose every assumption about the network and the device that the application is making.

### WebPageTest

For field-like measurements, WebPageTest (`webpagetest.org`) runs the app from real browsers on real network conditions in geographically distributed test agents. Useful for:

- Validating Core Web Vitals from a network that is closer to the median user than the developer's office connection.
- Comparing before-and-after performance impact of a deploy.
- Generating filmstrips and waterfalls that DevTools throttling cannot match for realism.
- Testing from low-end Moto G class devices that few developers own.

WebPageTest is the standard for synthetic monitoring; pair it with field RUM via the Chrome User Experience Report (CrUX) or a RUM provider for the full picture.

## Choosing between generateSW and injectManifest

Both Vite and Next.js (and any other Workbox-based tool) offer two ways to produce the service worker. The choice matters because it determines who owns the SW source.

### generateSW

The plugin writes the entire service worker for you based on declarative configuration. You specify the precache manifest, runtime caching rules, and a few global flags, and the plugin emits a complete SW file at build time.

When to pick `generateSW`:

- The app's caching policy fits the declarative model (precache + a handful of runtime routes).
- The team wants to minimize the SW surface area to maintain.
- The framework integration already handles registration and update lifecycle.

When NOT to pick `generateSW`:

- The app needs custom `push`, `notificationclick`, or `sync` event handlers.
- The team needs to integrate with non-Workbox APIs (Background Fetch, Web Periodic Background Sync, Web Locks inside the SW).
- Custom message handling between the SW and clients is required.

### injectManifest

You author the service worker yourself, including all event handlers. The plugin injects a precache manifest array into a placeholder in your SW source at build time, but the rest of the file is yours to control.

When to pick `injectManifest`:

- Push notifications with custom payload handling, focus-existing-client logic, or action buttons.
- Background Sync with custom queue logic.
- Coordinated update flow with bidirectional `postMessage` between SW and clients.
- Logic that doesn't map to Workbox routes.

Reference setup for `injectManifest` in Vite:

```ts
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa';

export default {
  plugins: [
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts'
    })
  ]
};
```

```ts
// src/sw.ts
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { NetworkFirst } from 'workbox-strategies';

declare const self: ServiceWorkerGlobalScope;

precacheAndRoute(self.__WB_MANIFEST);

registerRoute(
  new NavigationRoute(new NetworkFirst({ cacheName: 'pages', networkTimeoutSeconds: 3 }))
);

self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {};
  event.waitUntil(self.registration.showNotification(data.title, data.options));
});
```

The `self.__WB_MANIFEST` placeholder is replaced at build time with the precache manifest.

## Framework selection cheat-sheet

| Stack | Library | Notes |
|---|---|---|
| Vite (React, Vue, Svelte, vanilla) | `vite-plugin-pwa` | Most flexible; both `generateSW` and `injectManifest`; requires Node 20.19+ and Vite 7+ |
| Next.js (App Router or Pages Router) | `@serwist/next` | The original `next-pwa` is unmaintained; the `@ducanh2912/next-pwa` fork redirects to Serwist |
| Angular | `@angular/pwa` schematic | Built-in; no Workbox; uses Angular's own SW with `ngsw-config.json` |
| Nuxt 3+ | `@vite-pwa/nuxt` | Thin Nuxt-module wrapper over `vite-plugin-pwa` |
| Ionic / Single codebase for App Store | Capacitor wrapper | Wraps the PWA in a native WebView; ships to App Store and Play Store as a native app |
| Remix | `@remix-pwa/sw` (community) | Active maintainer, smaller user base than Serwist or vite-plugin-pwa |
| SvelteKit | `vite-plugin-pwa` via the SvelteKit Vite adapter | Same plugin as plain Vite, with adapter-specific manifest hooks |
| Astro | `@vite-pwa/astro` | Maintained alongside the Nuxt module by the same team |

The pattern that has emerged in 2025-2026: pick the Vite-based ecosystem (`vite-plugin-pwa`, `@vite-pwa/nuxt`, `@vite-pwa/astro`) when on Vite, pick Serwist when on Next.js, and accept Angular's built-in SW when on Angular.

## Build-time vs runtime manifest considerations

A few cross-framework gotchas worth noting:

- **Manifest extension and MIME type:** prefer `manifest.webmanifest` served with `Content-Type: application/manifest+json`. Some CDNs default to `application/json` or even `text/plain` for unknown extensions; this breaks installability on Chromium. Configure the CDN explicitly.
- **start_url and scope mismatches across environments:** the manifest is built once but deployed to multiple origins (preview, staging, production). Avoid hardcoding the origin in `start_url`; use relative paths. The framework helper usually does this correctly by default.
- **icon path resolution:** Next.js 14+'s `app/manifest.ts` resolves icon paths against the public root automatically. Vite, Nuxt, and Angular resolve against the build output root. Verify that the deployed paths are absolute or correctly relative to the manifest URL.
- **Cache headers on the manifest:** the manifest itself should have a short cache TTL (5 minutes is reasonable). Long TTLs on the manifest mean icon and metadata changes take a long time to reach installed users.

## CI integration

For continuous integration of PWA quality checks:

- Run Lighthouse via the Node CLI in CI. The PWA category is removed, but the individual installability and best-practices audits remain. Fail the build on regression.
- Run the PWA Builder validator via its public REST API. Track the score over time.
- Run a synthetic offline reload via Playwright: register the SW, take the app offline, reload, assert the offline page renders.
- For Workbox-based projects, run `workbox-cli` in CI to validate the generated SW against the expected precache manifest and runtime routing config.

A minimal Playwright offline test:

```ts
import { test, expect } from '@playwright/test';

test('PWA serves offline page when network is down', async ({ page, context }) => {
  await page.goto('/');
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
  await context.setOffline(true);
  await page.reload();
  await expect(page.locator('body')).toContainText('You are offline');
});
```

This catches the most common regression: a deploy that breaks the offline fallback by changing the route, the precache manifest, or the SW navigation handler.

