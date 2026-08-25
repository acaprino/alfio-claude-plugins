# Background Execution

Progressive Web Apps run code outside the visible page lifecycle through three worker types and a small set of background-oriented APIs. Each surface has different scope, lifetime, and platform support. This reference covers the taxonomy, the four background APIs (Background Sync, Periodic Background Sync, Background Fetch, Screen Wake Lock), and a per-platform reality check that tells you which APIs you can actually rely on.

## Worker taxonomy

The web platform exposes three distinct worker types. Pick the one that matches the lifetime and scope you need.

| Type | Scope | Lifetime | Use cases |
|---|---|---|---|
| **Web Worker** | Per tab | Tab lifetime | CPU off-main-thread |
| **Shared Worker** | Same origin, multi-tab | As long as one client exists | Shared state |
| **Service Worker** | Origin scope | Event-driven, browser-controlled | Caching, push, sync |

Notes on each:

- **Web Worker**: created with `new Worker('worker.js')`. Dies when the tab closes or when the worker calls `self.close()`. Use for parsing, image processing, cryptography, anything that would otherwise block the main thread.
- **Shared Worker**: created with `new SharedWorker('shared.js')`. Survives as long as at least one tab from the same origin holds a reference. Useful for cross-tab coordination (a single WebSocket connection shared by every open tab of your app). Not supported in Safari, so design fallbacks accordingly.
- **Service Worker**: registered with `navigator.serviceWorker.register('/sw.js')`. Lives at origin scope, is event-driven, terminated by the browser when idle, and restarted on demand for any of its event types. Never store persistent state in module-level variables: the next event may run after a full restart with no in-memory state preserved.

A practical rule: if the work is CPU-bound and short, use a Web Worker. If multiple tabs need to share a single resource (a single WebSocket, a single cache invalidation channel), use a Shared Worker where supported and a `BroadcastChannel` plus per-tab Web Workers where not. If the work has to run when the page is closed (push delivery, sync replay, intercepted fetch responses), the Service Worker is the only option, because it is the only worker the browser is allowed to start without an open tab.

## Background Sync (one-shot)

Background Sync lets a page schedule a one-shot retry that runs when the device regains connectivity. The classic use case is a "send" button that queues a mutation when offline and flushes it later.

Page side:

```ts
// On the page: schedule the sync
const reg = await navigator.serviceWorker.ready;
await (reg as any).sync.register('flush-queue');
```

Service worker side:

```ts
// In sw.ts
self.addEventListener('sync', (event) => {
  if (event.tag === 'flush-queue') {
    event.waitUntil(flushPendingMutations());
  }
});
```

The browser fires the `sync` event when the device has connectivity. If the handler throws or the promise passed to `event.waitUntil()` rejects, the browser will retry with backoff. Tag your sync registrations with stable strings so retries deduplicate against new registrations of the same operation.

Typical wiring with a persistent queue:

1. The page writes the pending mutation to IndexedDB (the queue table) and calls `sync.register('flush-queue')`.
2. If the request succeeds immediately (the user is online), the page handler removes the row from the queue and the registered sync becomes a no-op when it later fires.
3. If the page is offline or the immediate request fails, the row stays in the queue.
4. When connectivity returns, the SW `sync` handler reads every queued row, replays each mutation against the server, and removes successful rows.
5. On startup, the page also flushes the queue. This second path catches users on browsers without Background Sync.

**Support**: Chromium desktop and Chromium Android. **Not supported on Safari iOS, Safari macOS, or Firefox.** Design any feature that uses Background Sync with a fallback that retries on the next page open (a queue in IndexedDB plus a startup flush) so users on unsupported browsers do not lose their pending mutations.

For convenience, `workbox-background-sync` wraps this pattern. Register a `BackgroundSyncPlugin` on a POST route inside the SW and Workbox handles the queue, retries, and replay automatically. See `service-workers.md` for the wiring.

Retry policy details worth knowing:

- The browser caps total retry duration at roughly 24 hours by default. After that the queued sync is dropped. If your mutations need indefinite retry, persist them in IndexedDB and replay on startup as well.
- The `lastChance` property on the `SyncEvent` is `true` on the final attempt. Use it to inform the user via a notification if the operation could not complete.
- Each `sync.register(tag)` call collapses into a single pending sync per tag. Registering the same tag many times produces one event firing.

Common failure modes:

- The handler returns synchronously without calling `event.waitUntil()`. The browser considers the sync complete immediately and never retries.
- The handler awaits a `fetch()` that throws on offline. Wrap with `try/catch` and re-throw to signal failure to the browser.
- The page registers the sync from inside an iframe with a different scope than the SW. The registration silently no-ops. Always register from the top-level page.

## Periodic Background Sync

Periodic Background Sync lets a service worker run a task on a recurring schedule even when the app is closed. Typical use: refresh a feed once a day so the app opens with current content.

Permission query and registration:

```ts
const status = await navigator.permissions.query({ name: 'periodic-background-sync' as PermissionName });
if (status.state === 'granted') {
  await reg.periodicSync.register('content-sync', { minInterval: 24 * 60 * 60 * 1000 });
}
```

Service worker handler:

```ts
// sw.ts
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'content-sync') event.waitUntil(syncContent());
});
```

**Support**: Chromium only. Three preconditions must hold for the event to fire:

1. The PWA is installed.
2. The origin has a sufficient site engagement score. Check the current value at `chrome://site-engagement/`.
3. The user has not denied the `periodic-background-sync` permission.

`minInterval` is a hint, not a guarantee. Chrome decides the actual cadence based on engagement, battery state, and network conditions. Treat the schedule as best-effort.

Chrome does not fire the event in Android doze mode. Periodic syncs ride the Android maintenance window, so devices in deep doze will not see syncs until the system schedules a maintenance pass. Plan content freshness around best-effort updates, not strict SLAs.

To check or unregister an existing registration:

```ts
const tags = await reg.periodicSync.getTags();
if (tags.includes('content-sync')) {
  await reg.periodicSync.unregister('content-sync');
}
```

Inspect the schedule in DevTools at Application > Background Services > Periodic Background Sync. Chrome records the last three days of events here, which is the easiest way to confirm that your handler is actually firing in the wild rather than only in your local testing.

Practical tips:

- Use `minInterval: 12 * 60 * 60 * 1000` (12 hours) as a starting point for content refresh. Going lower rarely produces more frequent firings, because Chrome's heuristics dominate.
- Treat Periodic Background Sync as a freshness optimization, never as the source of truth. The first page load after the user opens the app should still fetch fresh data: the user is engaged, the network is reachable, and the SW does not need to be involved.
- Test the unsupported path by spoofing `'periodicSync' in registration` to `false` in a development build. Make sure the app remains correct without the periodic refresh.

## Background Fetch (long downloads)

Background Fetch handles long-running downloads or uploads that should survive the page closing. Typical use: downloading a podcast episode, an offline map region, or a video for later viewing.

```ts
const reg = await navigator.serviceWorker.ready;
const bgFetch = await (reg as any).backgroundFetch.fetch('episode-42', ['/media/ep42.mp4'], {
  title: 'Download episode 42',
  icons: [{ sizes: '300x300', src: '/icon.png', type: 'image/png' }],
  downloadTotal: 60 * 1024 * 1024
});
```

The browser shows a system-level progress UI for the duration of the fetch. The `downloadTotal` field is a hint that lets the browser display accurate progress; without it the bar shows indeterminate progress.

Service worker events fired during a Background Fetch:

- `backgroundfetchsuccess`: fetch completed normally. Move responses into Cache Storage.
- `backgroundfetchfailure`: fetch failed (network error, server error, user aborted).
- `backgroundfetchabort`: user canceled the fetch via the system UI.
- `backgroundfetchclick`: user tapped the progress notification.

The `id` you pass as the first argument (`'episode-42'`) is the registration handle. Use a stable identifier per resource so you can later retrieve the same registration with `reg.backgroundFetch.get(id)`. Calling `fetch()` again with an existing `id` rejects, so deduplicate before requesting.

A typical `backgroundfetchsuccess` handler moves the downloaded responses into Cache Storage so the rest of the app can read them later:

```ts
self.addEventListener('backgroundfetchsuccess', (event) => {
  const bgFetch = event.registration;
  event.waitUntil((async () => {
    const cache = await caches.open(`media-${bgFetch.id}`);
    const records = await bgFetch.matchAll();
    await Promise.all(records.map(async (record) => {
      const response = await record.responseReady;
      await cache.put(record.request, response);
    }));
    await event.updateUI({ title: 'Episode 42 ready offline' });
  })());
});
```

**Support**: Chromium only. Not available on Safari or Firefox. For non-Chromium browsers, fall back to a streaming download inside the page (with the limitation that closing the tab cancels the download).

## Screen Wake Lock

Screen Wake Lock prevents the device from dimming or sleeping the screen while a task is in progress. Typical use: a recipe app open in the kitchen, a navigation app, a barcode scanner, or a video player.

```ts
let lock: WakeLockSentinel | null = null;
try { lock = await navigator.wakeLock.request('screen'); } catch (e) { /* low battery, denied, ... */ }
document.addEventListener('visibilitychange', async () => {
  if (lock !== null && document.visibilityState === 'visible') {
    lock = await navigator.wakeLock.request('screen');
  }
});
```

Two important behaviors:

1. The browser automatically releases the wake lock when the tab is hidden or backgrounded. The `visibilitychange` listener above re-acquires the lock when the tab becomes visible again.
2. The request can fail. Common reasons include low battery, the user denying the permission, or the browser policy disallowing wake locks in the current context. Always wrap the call in `try/catch`.

When the task that justified the wake lock is over, release it explicitly:

```ts
if (lock !== null) {
  await lock.release();
  lock = null;
}
```

**iOS 18.4 (March 31, 2025)** finally enabled Screen Wake Lock for Home Screen Web Apps after years of being unavailable on iOS PWAs (WebKit bugzilla #254545 fix). The WebKit release notes confirmed:

> "Fixed Screen Wake Lock API for Home Screen Web Apps. (108573133)"

Before iOS 18.4 the API was either absent or non-functional in standalone PWAs on iOS. From iOS 18.4 onward, an installed PWA can hold a wake lock just like Safari can. Feature-detect with `'wakeLock' in navigator` before calling.

Common pitfalls:

- Holding the lock for the entire app session drains the battery. Acquire it only for the specific task that needs it (a step in a recipe, an active scan, a video playback session) and release it as soon as the task ends.
- The wake lock does not prevent the OS from killing your tab for memory pressure. It only prevents the screen from dimming or sleeping while the tab is visible.
- The `lock.released` promise resolves when the lock is released for any reason (manual release, tab hidden, low battery). Use it to update UI that depends on the wake state.

A full pattern with cleanup:

```ts
class WakeLockGuard {
  private lock: WakeLockSentinel | null = null;
  private onVisibility = async () => {
    if (this.lock !== null && document.visibilityState === 'visible') {
      try { this.lock = await navigator.wakeLock.request('screen'); } catch {}
    }
  };
  async acquire() {
    if (!('wakeLock' in navigator)) return false;
    try {
      this.lock = await navigator.wakeLock.request('screen');
      document.addEventListener('visibilitychange', this.onVisibility);
      return true;
    } catch {
      return false;
    }
  }
  async release() {
    document.removeEventListener('visibilitychange', this.onVisibility);
    if (this.lock !== null) {
      await this.lock.release();
      this.lock = null;
    }
  }
}
```

Use one guard instance per task. Call `acquire()` when the task starts (recipe step opened, scanner active, video playing) and `release()` when the task ends (recipe step left, scanner closed, video paused). Never share a single global guard across unrelated features, because the first `release()` will drop the lock for everyone else.

## Platform reality check

Each platform exposes a different subset of the background APIs. Plan progressive enhancement around the most constrained target (usually iOS Safari).

### iOS Safari

- **No Background Sync.**
- **No Periodic Background Sync.**
- **No Background Fetch.**
- The service worker is terminated aggressively when the app goes into the background. Long-running SW work after backgrounding will not complete; design every SW task to be short and resumable.
- The installed PWA has storage isolated from system Safari. The Home Screen Web App runs in a separate process container with its own cookies, IndexedDB, Cache Storage, and OPFS. Data set in Safari is not visible inside the installed PWA and vice versa.
- Screen Wake Lock works from iOS 18.4 (March 31, 2025) for Home Screen Web Apps. Before that release, do not assume wake lock availability on iOS.

Practical consequence: if your feature design relies on Background Sync or Periodic Background Sync, your iOS users will not get it. Build a startup flush queue in IndexedDB and run it on every page load as the iOS fallback.

A second iOS-specific gotcha: a Home Screen Web App that has not been opened for a while may have its storage evicted by WebKit's intelligent tracking prevention thresholds. The installed-PWA container is supposed to be exempt, but historically WebKit bugs have eroded the exemption. Re-verify subscription state, IndexedDB rows, and Cache Storage entries on every PWA launch rather than assuming persistence.

### Android Chrome

- All four APIs are available: Background Sync, Periodic Background Sync, Background Fetch, Screen Wake Lock.
- Doze mode is respected. Periodic Sync events fire during the Android maintenance window rather than on demand; expect intervals longer than the requested `minInterval` on doze-eligible devices.
- The PWA installs as a WebAPK generated by Play Services. It appears in the launcher as a native-looking app with its own Settings entry and permission management.

### Desktop

- Installed PWA windows survive the main browser closing. A user can quit Chrome and the PWA window keeps running in its own process.
- The service worker can run in the background for push and sync even when no PWA window is open, subject to system idle and energy policies.
- Background Sync, Periodic Background Sync, and Background Fetch are available on Chromium desktop (Chrome and Edge). Not available on Safari macOS or Firefox.
- Screen Wake Lock is widely supported on desktop Chromium and Safari macOS.

### Quick decision table

| API | iOS Safari | Android Chrome | Desktop Chromium | Safari macOS | Firefox |
|---|---|---|---|---|---|
| Background Sync | No | Yes | Yes | No | No |
| Periodic Background Sync | No | Yes (engagement-gated) | Yes (engagement-gated) | No | No |
| Background Fetch | No | Yes | Yes | No | No |
| Screen Wake Lock | Yes (iOS 18.4+, installed PWA) | Yes | Yes | Yes | Partial |

When designing a feature, start from the iOS column and ask: what is the experience for a user who has none of these APIs? That answer is the floor. Then layer the Chromium-only enhancements on top with feature detection. The result is a PWA that works for everyone and uses the best available mechanism on each platform.

### Feature-detection recipe

Group the detections in one helper so the rest of the codebase can branch without repeating typeof checks:

```ts
export const bg = {
  hasSync: 'serviceWorker' in navigator && 'SyncManager' in window,
  hasPeriodicSync: 'serviceWorker' in navigator && 'PeriodicSyncManager' in window,
  hasFetch: 'serviceWorker' in navigator && 'BackgroundFetchManager' in window,
  hasWakeLock: 'wakeLock' in navigator,
};
```

Then the call sites read naturally: `if (bg.hasSync) reg.sync.register(...); else flushOnNextStartup();` and so on. Centralizing the checks also keeps the test surface small: mock the `bg` object in tests to simulate each platform combination.

### Design heuristics

A few rules of thumb that hold across platforms:

1. The page is the source of truth for user intent. The SW is the executor of intent. Background APIs let the SW finish work after the page closes; they do not let the SW invent new work.
2. Never schedule background work that the user did not implicitly request. Periodic Sync on first install is a permission abuse and may get flagged by browsers as misuse, lowering your engagement score and starving future syncs.
3. Always send a notification or update a visible UI surface when background work completes a user-facing operation. Silent success leaves the user unsure whether their data shipped.
4. Make every background path idempotent. The browser will retry, the user may also retry from the page on the next open, and a flaky network may produce partial successes. Server endpoints should accept the same mutation key twice without producing duplicate effects.
5. Log every fired event to a small ring buffer in IndexedDB so you can debug field issues. DevTools shows you the last three days locally; nothing in production gives you that visibility unless you build it.


