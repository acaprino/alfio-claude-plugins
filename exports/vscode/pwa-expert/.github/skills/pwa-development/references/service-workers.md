# Service Workers

The service worker is the background script that gives a PWA its offline-capable behavior, push handling, and update strategy. It runs in a separate JavaScript context from the page, is terminated by the browser when idle, and is restarted on demand whenever an event arrives. Treat it as a stateless event handler.

## Lifecycle

A service worker fires the following events in order across its lifetime: `install`, then `activate`, then any of `fetch`, `message`, `push`, `notificationclick`, `sync`, `periodicsync` as they occur during normal operation. The service worker runs in a context separated from the page, is terminated by the browser when idle, and restarted on demand. As a direct consequence: never store persistent state in module-level variables. Every restart starts the script from scratch.

```ts
// sw.ts
declare const self: ServiceWorkerGlobalScope;

const CACHE = 'app-shell-v7';
const PRECACHE = ['/', '/offline.html', '/styles.css', '/app.js'];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(PRECACHE);
    // Opt-in immediate activation
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        return fresh;
      } catch {
        return (await caches.match('/offline.html'))!;
      }
    })());
  }
});
```

MDN summarizes the propagation rule for activation as follows: *"After activation, the service worker will now control pages, but only those that were opened after the register() is successful […] To override this default behavior and adopt open pages, a service worker can call clients.claim()"* (MDN, *Using Service Workers*).

Key implications for design:

- The `install` handler is where the app shell is precached. Use `event.waitUntil()` so the install state does not resolve until the cache is fully populated.
- The `activate` handler is where old caches are cleaned up. A new SW version that ships with a new `CACHE` name should delete every previous version. Without this, storage grows monotonically across releases.
- The `fetch` handler intercepts every network request made by pages under scope. Calling `event.respondWith()` overrides the default network behavior with a custom response (from cache, from a synthesized stream, or anywhere else).
- `message` is used for postMessage exchanges from page to SW (for example, to trigger `skipWaiting()` after a user accepts an update banner).
- `push`, `notificationclick`, `sync`, and `periodicsync` are addressed in dedicated references (`push-notifications.md`, `background-execution.md`).

A subtle but important point about `fetch`: if the handler does not call `event.respondWith()`, the browser falls back to its default network behavior. This is the correct choice for routes the SW does not care about. Conditional handling (only intercept navigations, leave everything else alone) is the most common shape for hand-authored SWs that are not full Workbox setups.

Another subtlety: `event.respondWith()` accepts a `Promise<Response>`. The handler can compute the response asynchronously without blocking the event itself. Use `(async () => { ... })()` IIFEs inside `respondWith` to use async/await syntax cleanly without an extra function declaration.

The SW being a stateless restart-on-demand process is the single most common source of bugs for first-time SW authors. Module-scope variables get reset; any state that must persist across restarts must live in IndexedDB, in the Cache, or in some other durable store.

The lifecycle states a SW transitions through:

- **parsed**: the SW script has been fetched and parsed but no event has fired yet.
- **installing**: the `install` event is running. The SW remains here until `event.waitUntil()` resolves.
- **installed (waiting)**: install completed successfully. The SW is queued to take over but the previous SW is still controlling existing clients. Default behavior: the new SW waits here until every controlled client navigates away or closes.
- **activating**: the `activate` event is running. The SW remains here until `event.waitUntil()` resolves.
- **activated**: the SW is now the controller for clients within its scope (subject to the activation rule MDN summarizes above).
- **redundant**: a newer SW has replaced this one, or installation failed.

The `waiting` state is the safety valve. It exists so the browser does not swap a new SW under a page that was loaded against the old one. Bypassing it (with `skipWaiting()`) is the source of the version-skew bugs covered in the next section.

## skipWaiting and clients.claim

These two APIs are powerful and frequently misused. They both shortcut the default safe behavior that browsers apply to service worker transitions, and using them without understanding the consequences leads to silent corruption.

web.dev (Jake Archibald) puts the warning bluntly: *"skipWaiting() means that your new service worker is likely controlling pages that were loaded with an older version. This means some of your page's fetches will have been handled by your old service worker, but your new service worker will be handling subsequent fetches. If this might break things, don't use skipWaiting()"*.

Recommended pattern for 2025:

1. Use `skipWaiting()` only when one of two conditions holds. Either you have paired it with a coordinated reload UX (an "Update available" banner that calls `wb.messageSkipWaiting()` and then reloads the page when the SW takes control), or the delta between the previous and new SW does not break any runtime assumption (cache layout, IndexedDB schema, message protocol).
2. `clients.claim()` is mainly useful on the first install, when the SW did not previously control any client. Beyond that case, the default behavior (new SW takes control only of pages opened after registration succeeded) is the correct one.

On the second point, Archibald is again direct: *"I see a lot of people including clients.claim() as boilerplate, but I rarely do so myself."*

The common shape of the bug: a developer reflexively calls both `skipWaiting()` in `install` and `clients.claim()` in `activate` because "that is what every blog post does". The next time they ship a SW with a new IndexedDB schema, every open tab suddenly has its requests handled by code that assumes the new schema, while the tab itself was built against the old one. Errors surface as runtime crashes that do not reproduce locally because, locally, the developer always hard-refreshed between iterations.

The user-driven update flow shown later in this document is the cleanest way to ship `skipWaiting()` without these traps.

A short decision matrix:

- New SW changes nothing observable from the page (only internal logging, only updated comments): omit both `skipWaiting()` and `clients.claim()`. The default flow is correct.
- New SW changes asset cache layout but is fetch-compatible with the old one (added a new route, did not change existing routes): pair `skipWaiting()` with the user-driven banner so the page reloads against the new SW immediately.
- New SW changes IndexedDB schema or the postMessage protocol: do not call `skipWaiting()` from `install`. Use the user-driven banner that calls `wb.messageSkipWaiting()` only after the user has accepted the reload. Pair with the `controlling` listener that reloads the page automatically when the new SW takes over.
- First-ever install on a client that did not previously have a SW: `clients.claim()` is reasonable so existing tabs get the SW immediately. Beyond that case, prefer the default.

When in doubt, the safer default is to omit both. The cost is an extra page reload before the new SW takes over for the user, which is a far better outcome than a corrupted session.

## Registration and scope

Service worker registration happens from the page, typically gated on the `load` event so it does not compete with critical-path resources.

```ts
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/', type: 'module' });
    // Update polling for long-lived sessions
    setInterval(() => reg.update(), 60 * 60 * 1000);
  });
}
```

The scope of a service worker is bounded by the directory the SW file is served from. A SW served at `/scripts/sw.js` can only control pages under `/scripts/`. To control the entire origin from `/`, the SW file must sit at the root of the origin: `/sw.js`.

This is the reason most frameworks emit the SW file to the public root: it is the only path that gives full origin scope without the `Service-Worker-Allowed` HTTP header workaround.

The `update()` call on the registration is a manual trigger for the browser to re-fetch `/sw.js` and check for changes. Calling it from a long-running tab on an interval (for example every hour) is a good way to ensure long-lived sessions pick up updates without waiting for a navigation.

HTTP headers that matter:

- `Cache-Control: no-cache` on `/sw.js` is critical. The browser already caps SW caching at 24 hours by default, but a misconfigured CDN can still hold a stale SW for far longer. Setting `no-cache` (which means "revalidate every time", not "do not cache") ensures rapid propagation of updates.
- The `Content-Type` header must be a JavaScript MIME type (`application/javascript` or `text/javascript`). A wrong content type causes registration to fail silently in some browsers.
- `Service-Worker-Allowed` can be used to override scope if the SW must control a path above its own location, but this is an escape hatch and adds complexity. Prefer placing `/sw.js` at the root.

Never serve `/sw.js` from a CDN with a long TTL. The version skew between the cached SW and the deployed application is the single biggest source of "I shipped a fix but users do not see it" reports.

The `type: 'module'` option in `register()` opts into ES module syntax for the SW. With it, the SW can use `import` and `export` natively. Without it, the SW is treated as a classic script and `import` is a syntax error. Most modern bundlers emit module SWs by default; verify the build output if you are unsure.

Registering inside `window.addEventListener('load', ...)` defers SW registration until the page is fully loaded. This avoids competing with critical-path resources for bandwidth on first paint. For sites where the SW takes over almost immediately after first load (offline-first PWAs that boot from cache on revisit), this trade-off is correct: the first-visit SW download does not block first paint, and every subsequent visit is SW-controlled from the start.

## Caching strategies (Offline Cookbook)

Jake Archibald's Offline Cookbook defines a small set of canonical caching strategies. Pick the strategy per route type, not per SW.

| Strategy | When to use | Example asset |
|---|---|---|
| **Cache First** | Versioned, immutable assets | Hashed JS / CSS, fonts, static images |
| **Network First** | Fresh content with offline fallback | Navigational HTML, critical JSON API |
| **Stale While Revalidate** | Speed plus eventual freshness | Avatars, low-criticality data |
| **Network Only** | Side effects, authentication | POST mutations |
| **Cache Only** | Precached assets | App shell |

Notes on strategy selection:

- Cache First is the right choice for any asset whose URL contains a content hash. Once a `/assets/app.4f3a91.js` is in cache, that exact URL never serves a different payload, so caching it forever is safe. Combine with an expiration policy (`maxEntries`) so the cache does not grow unbounded across releases.
- Network First makes sense for HTML navigation when you want to ship updates immediately but still need an offline fallback. Pair it with a small network timeout (3 seconds is a common default) so a slow network does not block the cache fallback. Without the timeout, a user on a poor connection waits for the network to fail before the cached page renders.
- Stale While Revalidate is the "best of both" for non-critical reads. The user sees the cached version immediately, the SW refreshes the cache in the background, and the next visit sees the new version. Avoid this strategy for anything where serving stale data has consequences (account balances, real-time prices, security state).
- Network Only on POST requests should be combined with Background Sync so the request is queued for retry if the user is offline at submission time. See `background-execution.md`.
- Cache Only is the strategy for app-shell HTML if you handle navigation routing in JavaScript on the client. The shell ships once, navigation happens entirely on the client, and the SW does not touch the network for shell requests.

A common composite layout: app shell on Cache First, navigation HTML on Network First with a 3-second timeout falling back to the offline page, API JSON on Stale While Revalidate, images on Cache First with an `ExpirationPlugin` capping 60 entries and 30-day TTL, POST mutations on Network Only with Background Sync.

Anti-patterns to recognize:

- Caching every response under one giant cache. Without separate named caches per content type, expiration policies become impossible to express and storage usage becomes opaque. Use one cache per role (pages, images, api, fonts) so each can have its own expiration plugin.
- Caching opaque cross-origin responses without `CacheableResponsePlugin({ statuses: [0, 200] })`. By default, Workbox refuses to cache responses with status 0 (the marker for opaque CORS responses), which means CDN-served images can silently fail to cache.
- Forgetting to deal with POST in route registration. By default, Workbox routes match GET only. The third argument to `registerRoute()` is the HTTP method; pass `'POST'` for routes that handle mutations.
- Caching authenticated API responses on Stale While Revalidate. The cached response carries the headers and body from the previous user. After logout-and-login on the same device, the cache may serve the previous user's data to the new user. Use Network First for anything tied to the current session, or invalidate the cache explicitly on logout.

Pattern for explicit invalidation on logout: have the page postMessage `{ type: 'LOGOUT' }` to the SW; in the SW message handler, call `caches.delete('api')` (or the relevant cache name) before resolving. The next request after logout misses the cache and goes to the network with the fresh auth state (or no auth at all).

Strategy interactions with `Vary` headers: a response with `Vary: Cookie` or `Vary: Authorization` should not be cached across users on the same device. The Cache API stores responses keyed by request URL only; the `Vary` header is not honored by default. Filter these out at the route level (skip caching when the response carries a session-bearing header) or use a separate cache that you can invalidate on session change.

## Workbox 7 modern pattern

Workbox is Google's library for service workers. Workbox 7 is the current modern baseline. The library encapsulates the strategies above as composable primitives with plugins for cache expiration, response filtering, broadcast updates, and Background Sync.

```ts
// sw.ts (Workbox 7+)
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { CacheFirst, NetworkFirst, StaleWhileRevalidate, NetworkOnly } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

declare const self: ServiceWorkerGlobalScope;

cleanupOutdatedCaches();
precacheAndRoute(self.__WB_MANIFEST);

registerRoute(
  new NavigationRoute(new NetworkFirst({ cacheName: 'pages', networkTimeoutSeconds: 3 }))
);

registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 30 * 24 * 60 * 60 })
    ]
  })
);

registerRoute(
  ({ url }) => url.origin === 'https://api.acme.com',
  new StaleWhileRevalidate({ cacheName: 'api' })
);
```

Key Workbox 7 modules:

- `workbox-precaching`: declarative precaching of build artifacts. `self.__WB_MANIFEST` is injected by the build (Vite plugin, Webpack plugin, or CLI) and contains the list of files plus their content hashes.
- `workbox-routing`: route registration. Routes match by URL pattern, request destination, request method, or custom predicate. `NavigationRoute` is the special wrapper for navigation requests (HTML).
- `workbox-strategies`: the strategy primitives (`CacheFirst`, `NetworkFirst`, `StaleWhileRevalidate`, `NetworkOnly`, `CacheOnly`).
- `workbox-expiration`: the `ExpirationPlugin` enforces `maxEntries` (LRU cap) and `maxAgeSeconds` (TTL) on a cache.
- `workbox-background-sync`: the `BackgroundSyncPlugin` queues failed requests for retry when connectivity returns.
- `workbox-broadcast-update`: the `BroadcastUpdatePlugin` emits a message on a `BroadcastChannel` whenever a cached response is updated. Useful for "new content available" prompts.
- `workbox-window`: the client-side counterpart that wraps SW registration with a clean API for update flows.

Less commonly used but useful when needed:

- `workbox-cacheable-response`: the `CacheableResponsePlugin` (already in the example) filters which responses are cacheable by status or by header. Essential for opaque cross-origin responses (`status === 0`).
- `workbox-range-requests`: serves partial content (HTTP `Range` requests) from cache for audio and video. Without it, ranged requests to cached media fail because the cache only knows about full-body responses.
- `workbox-google-analytics`: queues GA hits offline and replays them when connectivity returns. Less relevant in 2025-2026 because GA4 already buffers hits client-side, but kept for legacy analytics endpoints.
- `workbox-navigation-preload`: enables the navigation preload feature, where the browser starts the network request for the navigation in parallel with the SW boot. Reduces the cold-start penalty for the SW on the first navigation after a tab opens.

Official documentation: `developer.chrome.com/docs/workbox`.

What the example above does, route by route:

1. `cleanupOutdatedCaches()` removes precache entries from previous Workbox versions on every activation. Prevents storage growth across deploys.
2. `precacheAndRoute(self.__WB_MANIFEST)` registers the build-time list of files (HTML, JS, CSS, fonts, anything emitted by the build) for Cache First serving with revision-keyed invalidation. Workbox handles the URL-to-revision mapping so the cache stays consistent without manual versioning.
3. The `NavigationRoute` with `NetworkFirst` matches every navigation request (HTML). The 3-second `networkTimeoutSeconds` means a slow network falls back to the cached navigation response after 3 seconds instead of hanging indefinitely.
4. The image route matches every `request.destination === 'image'` and uses Cache First. `CacheableResponsePlugin({ statuses: [0, 200] })` allows caching of opaque cross-origin responses (status 0) in addition to normal 200s. `ExpirationPlugin` caps the cache at 60 entries and 30 days.
5. The API route matches any request to `https://api.acme.com` and uses Stale While Revalidate. The user always sees the cached response immediately; the SW updates the cache from the network in the background.

The `__WB_MANIFEST` placeholder is the bridge between the build system and the SW. The build (Vite plugin, Webpack plugin, or the `workbox-cli` tool) scans the output directory, computes a hash for every emitted file, and injects an array like `[{ url: '/assets/app.4f3a91.js', revision: null }, ...]` in place of the placeholder. Files with hashed names use `revision: null` because the hash in the URL is already the version key. Files without hashed names (the entry HTML, the manifest) use an explicit revision string.

Without the build-time injection, `precacheAndRoute(self.__WB_MANIFEST)` evaluates to `precacheAndRoute(undefined)` and throws at install time. The build step is mandatory; do not hand-author the SW with that line as a literal.

## Background Sync via workbox-background-sync

Background Sync queues failed network requests and replays them when connectivity is restored. With Workbox, this is one plugin attached to a `NetworkOnly` route.

```ts
import { BackgroundSyncPlugin } from 'workbox-background-sync';

const bgSync = new BackgroundSyncPlugin('mutations-queue', {
  maxRetentionTime: 24 * 60, // minutes
});

registerRoute(
  ({ url, request }) => url.pathname.startsWith('/api/') && request.method === 'POST',
  new NetworkOnly({ plugins: [bgSync] }),
  'POST'
);
```

The plugin intercepts every failed POST under `/api/`, stores it in an IndexedDB queue named `mutations-queue`, and retries the request when the browser fires the `sync` event after connectivity returns. `maxRetentionTime` is the maximum age (in minutes) a queued request will be retained before being discarded.

Support is Chromium-only. Background Sync is not available on Safari (iOS or macOS) or on Firefox. Plan a degraded path: detect support and fall back to in-page retry logic with explicit user feedback when the API is missing. See `background-execution.md` for the full Background Sync model and `platform-constraints.md` for the per-platform support matrix.

The flow at runtime:

1. The user submits a form. The page issues a POST to `/api/...`.
2. The fetch handler matches the route and tries the network.
3. If the network succeeds, the response is returned as normal.
4. If the network fails (offline, server unreachable, timeout), `BackgroundSyncPlugin` intercepts the failure, serializes the request (URL, method, headers, body), and writes it to the named IndexedDB queue.
5. The browser fires a `sync` event when connectivity returns. The plugin replays each queued request in order.
6. Requests older than `maxRetentionTime` (24 hours in this example) are discarded silently.

The page does not get notified by default that a request was queued. For visible UX (a toast saying "Will send when online"), pair the plugin with a postMessage from the SW back to the client, or check `navigator.onLine` from the page before submission.

## Debugging

Service worker debugging is uneven across browsers. The right tool depends on the target.

**Chrome and Edge DevTools**: the Application panel is the primary surface.
- Service Workers section: see registered SWs, force "update on reload", check "bypass for network" to disable the SW temporarily, send test push messages, trigger sync events on demand.
- Cache Storage: inspect every named cache, see entries, delete individual entries or whole caches.
- IndexedDB: browse databases and stores.
- Manifest: see the parsed manifest, validate installability, preview WCO.
- Storage: see total quota and per-type breakdown.
- Background Services panel: record Periodic Background Sync and Background Fetch events for up to 3 days, even when DevTools is closed.

**Safari Web Inspector**: limited.
- For Safari tabs on iOS: Develop menu, select the device, select the tab. Full SW debugging available.
- For Home Screen Web Apps on iOS: not inspectable directly. This is a major operational limitation. Workarounds: ship a hidden tap-sequence in the UI that toggles a debug overlay exposing `console.log` lines, or bundle a tool like Eruda that provides an in-page DevTools console accessible without an external connection.

**Firefox**: navigate to `about:debugging#/runtime/this-firefox` to see registered service workers. Click "Inspect" on a SW to open a dedicated DevTools console for it. Cache and IndexedDB inspection is in the Storage panel of the page DevTools.

Cross-cutting tip: keep a small `?sw_debug=1` query-string flag in the registration code that, when present, registers the SW with extra console logging and shorter cache TTLs. Strip it before production. The flag is invaluable for reproducing issues on real devices where attaching DevTools is awkward (Android Chrome over USB still works, but flag-driven verbose logging often catches the issue first).

When a bug only reproduces on a production deployment, the first three checks to run, in order:

1. Is the active SW the one you expect? Compare the URL in the Application panel's Service Workers section to the deployed build hash.
2. Is the cache layout correct? Open Cache Storage and confirm the named caches exist and contain the expected entries.
3. Is the page actually controlled by the SW? Run `navigator.serviceWorker.controller` in the console. A `null` result means the page is not controlled (the SW exists but the page was loaded before the SW activated; a reload will fix it).

In all browsers, two diagnostic habits help. First, always check that the SW you are debugging is the active SW, not a waiting or installing one. The Application panel shows the state explicitly. Second, when reproducing a bug, use a fresh incognito or private window so leftover SW state from previous sessions does not contaminate the repro.

A few patterns worth knowing when chasing SW bugs:

- "Update on reload" in the Application panel forces the SW to update on every page reload during development. Turn it on while iterating; turn it off to test the real production update flow.
- "Bypass for network" disables the SW for the current tab without unregistering it. Useful to confirm that a bug is in the SW versus in the page or server.
- The Network panel marks SW-served responses with "(ServiceWorker)" in the Size column. If a response is not marked, the SW did not intercept it.
- Calling `caches.delete('cache-name')` from the DevTools console is the fastest way to wipe a specific cache without unregistering the SW.
- For Home Screen Web Apps on iOS where the inspector is unreachable, an Eruda bundle plus a hidden activation gesture (for example, 5 taps in the top-left corner) is the standard escape hatch. Eruda gives a full DevTools-like console inside the page itself.

A minimal Eruda gate looks like:

```html
<script src="https://cdn.jsdelivr.net/npm/eruda"></script>
<script>
  let taps = 0;
  document.body.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1 && e.touches[0].clientY < 40 && e.touches[0].clientX < 40) {
      taps += 1;
      if (taps >= 5) {
        eruda.init();
        taps = 0;
      }
      setTimeout(() => { taps = 0; }, 1500);
    }
  });
</script>
```

Ship the gate behind a runtime flag in production builds, or strip it entirely from the public bundle and only include it in a separate diagnostic build delivered to internal users.

## Updates and versioning

Service worker updates are asynchronous and can interact badly with long-running sessions. The patterns below are the production-tested approach for shipping new SW versions without breaking users mid-session.

### Update flow: user-driven reload pattern

The recommended flow uses `workbox-window` on the client to detect that a new SW is waiting, prompt the user, and orchestrate the SW takeover plus the page reload.

```ts
// client.ts (with workbox-window)
import { Workbox } from 'workbox-window';
const wb = new Workbox('/sw.js');

wb.addEventListener('waiting', () => {
  showUpdateBanner({
    onAccept: () => {
      wb.addEventListener('controlling', () => window.location.reload());
      wb.messageSkipWaiting();
    }
  });
});

wb.register();
```

```ts
// sw.ts
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});
```

Flow narrative:

1. `wb.register()` registers `/sw.js`.
2. When the browser detects a new SW and it enters the `waiting` state, the `waiting` event fires.
3. The page shows an "Update available, reload?" banner.
4. When the user accepts, the page subscribes to the `controlling` event (which fires when the new SW takes control of this client) and posts `SKIP_WAITING` to the waiting SW.
5. The waiting SW receives the message and calls `self.skipWaiting()`, which moves it from `waiting` to `active`.
6. The browser fires `controlling` on the client, and the page reloads to start clean against the new SW version.

This pattern keeps `skipWaiting()` paired with an immediate reload, which is the only situation where `skipWaiting()` is safe to use without risk of version skew.

The banner UI is a product decision. A few patterns that work well in practice:

- Non-blocking toast in the corner with an explicit "Reload now" button. The user can dismiss for later. The toast re-appears on the next navigation if the SW is still waiting.
- Full-width banner at the top of the page when the new SW has critical fixes. The page is still usable, but the prompt is more prominent.
- Modal dialog only when the new SW is incompatible with the current client (RELOAD_REQUIRED case). Used rarely, but unmissable.

Avoid silent auto-reload triggered by the SW `waiting` event with no user interaction. It loses unsaved input and is a surprising user experience.

### Cache busting

Three rules cover the cache busting question for PWAs.

- Versioned assets (JS, CSS, images served from `/assets/app.4f3a91.js`-style URLs) can be served with long TTL and safely cached under Cache First. The hash in the filename is the version key.
- HTML must be served with `Cache-Control: no-cache` or `max-age=0, must-revalidate`. The HTML is the entry point that references the hashed asset URLs, and serving a stale HTML means users load old asset references.
- `/sw.js` must be served with `Cache-Control: no-cache`. Never serve it from a CDN with a long TTL. The browser already enforces a 24-hour cap on SW caching by default, but CDN misconfiguration is a recurring source of update-propagation bugs.

If the deployment goes through Cloudflare, Fastly, or another CDN, verify these three rules at the edge configuration level, not only in the origin server. CDNs default to caching aggressively; a missing surrogate-control rule for `/sw.js` will let the old SW persist at the edge for hours even when the origin is updated.

### Breaking changes in the SW

When the new SW version is incompatible with the previous one (different cache layout, different IndexedDB schema, different message protocol), a clean transition needs more than `skipWaiting()` plus reload.

Patterns:

- Bump the `CACHE` constant (`app-shell-v7` becomes `app-shell-v8`). The `activate` handler that deletes any cache whose name does not match the current `CACHE` will purge the old one.
- IndexedDB migrations: bump the database version by +1 in `indexedDB.open()` and handle the `onupgradeneeded` event. Inside the handler, transform old object stores to the new schema. Never assume the previous version was N-1; the user may be coming from any earlier version.
- Hard reload broadcast: use `self.clients.matchAll()` to enumerate every open client, then `client.postMessage({ type: 'RELOAD_REQUIRED' })` on each. The page handles the message by showing a modal or calling `location.reload()` directly. Use this when the SW payload requires a fresh page even after activation.

Worked example of a hard-reload broadcast inside the `activate` handler:

```ts
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    // Standard cleanup of caches no longer in use
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));

    // Notify every client that a hard reload is required for this version
    const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of clients) {
      client.postMessage({ type: 'RELOAD_REQUIRED', cacheVersion: CACHE });
    }
  })());
});
```

The page handles `RELOAD_REQUIRED` with a banner ("A critical update was installed. Reload to continue.") rather than an unannounced `location.reload()`. The user keeps control and does not lose unsaved input.

### Update propagation timing per browser

Browsers differ in how aggressively they check for SW updates.

- **Chromium** (Chrome, Edge, Opera, Brave): the browser checks for updates on every navigation, plus every 24 hours if the page stays open continuously, plus on-demand whenever the page calls `registration.update()`.
- **Safari iOS**: update checks are less frequent. In practice, getting a new SW picked up often requires closing and reopening the Home Screen Web App. This is one more reason the user-driven reload pattern is important: it gives the user a deliberate moment to commit to the new version rather than relying on browser-driven polling.
- **Firefox desktop**: update check happens at page load. Long-running tabs do not see new SW versions until they navigate or refresh.

The general principle: do not assume any given browser will pick up an SW update on a tight schedule. Build the update mechanism around explicit triggers (the user-driven banner above, the once-an-hour `registration.update()` poll, manual reload) rather than counting on the browser to converge on its own. Background convergence is best-effort across all engines and worst on Safari iOS Home Screen PWAs.

The on-demand `registration.update()` call from the registration code earlier in this document is the workaround for long-lived sessions on every browser: polling once an hour ensures the update is fetched even on browsers that do not poll aggressively on their own.

Operational rule of thumb: a release that goes out at 14:00 should expect to reach most Chromium users by their next navigation (within minutes for active tabs that hit the once-an-hour `update()` call, or by the next page load otherwise). Safari iOS Home Screen PWAs may take a day or more to converge, with some users only picking up the update after they close and reopen the app. Plan release rollouts and metrics accordingly: do not assume a release is universally deployed within an hour of the SW build going live.

For breaking server changes that must be coordinated with a SW update (a new API shape, a renamed endpoint), the safe pattern is:

1. Deploy the server change behind a feature flag or with backward compatibility for the previous API shape.
2. Deploy the new SW that uses the new API.
3. Let the SW propagate to users over the next few days.
4. Once telemetry shows >99% of active SWs have updated, remove the backward-compatibility shim on the server.

Trying to flip the server in lockstep with the SW deployment is the recipe for hours of broken sessions on devices that have not yet picked up the new SW.

The flip side: if a hotfix must reach users immediately (security fix, payment-system bug), the user-driven banner is the fastest reliable channel. The banner appears on the next page load for users with the new SW waiting, and the explicit reload commits the fix. Background convergence by itself cannot meet a "fix shipped in 30 minutes" objective; pair every release with the visible update prompt so users have a way to accept the new version on their own.

A final note on cache versioning: keep the `CACHE` constant tied to a build identifier (commit SHA prefix, package version, build timestamp) so a single look at the running SW tells you which build is active. Hand-edited integers (`v1`, `v2`, `v3`) drift out of sync with the actual deployment and lose their diagnostic value within a few releases.

Cross-reference summary for this document:

- For Background Sync, Periodic Background Sync, Background Fetch, and Wake Lock, see `background-execution.md`.
- For Web Push, VAPID, RFCs, Declarative Web Push, and the Badge API, see `push-notifications.md`.
- For storage quotas, eviction policies, Persistent Storage, and OPFS, see `storage-persistence.md`.
- For platform-specific support matrices (which APIs are missing on iOS, Firefox, or Safari macOS), see `platform-constraints.md`.
- For SW debugging within DevTools, including the Application panel surface, see this document plus `frameworks-tooling.md` for framework-specific debugging notes.
- For the production deployment checklist that gates a PWA release, see `production-checklist.md` Section 3 (Service Worker).
