# Storage and Persistence

Storage in a PWA spans six distinct APIs with very different performance, capacity, and reliability profiles. The right choice depends on the data shape (string key/value vs. structured records vs. binary blobs), whether the access path runs on the main thread or inside a worker, and whether the data must survive eviction under storage pressure. This reference walks the six endpoints, the two primary structured-storage APIs (IndexedDB and OPFS), per-browser quotas and eviction policies, and the `navigator.storage.persist()` flow for opting into persistent storage.

## Storage endpoints

The PWA platform exposes six storage surfaces. The first three (localStorage, sessionStorage, cookies) are legacy and synchronous on the main thread, with hard size caps in the megabyte range. The latter three (IndexedDB, Cache API, OPFS) are the modern, async, worker-accessible surfaces with gigabyte-scale capacity.

| API | Type | Async | Worker | Notes |
|---|---|---|---|---|
| `localStorage` | string K/V | No | No | 5 to 10 MiB cap, synchronous, avoid |
| `sessionStorage` | string K/V | No | No | Tab lifetime |
| Cookies | string | n/a | n/a | Sent on every request |
| **IndexedDB** | Structured NoSQL | Yes | Yes | Gigabytes available |
| **Cache API** | Request / Response | Yes | Yes | For service worker caching |
| **OPFS** | Sandboxed file system | Async (main thread) and Sync (Worker only) | Yes | Performance for binary files |

### Reading the table

The five columns capture the practical differentiators that drive most storage decisions:

- **Type**: the shape of the data the API was designed for. Mismatching the shape is the most common source of pain (storing structured records in `localStorage` as JSON strings, storing binary blobs in IndexedDB as `ArrayBuffer`).
- **Async**: whether reads and writes return Promises. Synchronous APIs block the main thread and cannot be safely used during a hot path.
- **Worker**: whether the API is accessible from a Service Worker or a dedicated Web Worker. Anything that must work offline (the service worker's `fetch` handler) or off the main thread (heavy CPU tasks in a Worker) must use a worker-accessible API.
- **Notes**: the headline constraint or use case.

### Practical guidance per endpoint

- `localStorage` and `sessionStorage` block the main thread on every read and write. Both contribute to Interaction to Next Paint regressions. Use them only for tiny configuration flags that absolutely must be readable synchronously during a hot critical path. Even then, prefer migrating to IndexedDB with a one-time hydration on startup. Both storages serialize values to strings, so callers have to `JSON.stringify` and `JSON.parse` on every access, which compounds the main-thread cost.
- `sessionStorage` is scoped to the tab's lifetime: a new tab gets a fresh empty store, closing the tab clears it. It is appropriate for transient UI state (a form draft, a wizard step), never for persistent application data.
- Cookies were never designed as a storage tier for application data. They are sent on every HTTP request to the origin, inflating request size and complicating CDN caching. Reserve them for authentication tokens and similar session-bound material handled by the server. The 4 KB per-cookie size limit and 50-cookie per-origin limit make them unsuitable for anything richer.
- The Cache API is the natural fit for service worker response caching (precached app shell, runtime cache for assets and API responses). Do not abuse it as a general-purpose store: each entry is a full `Request` / `Response` pair and lookups are by URL, which is awkward for arbitrary application data. The pairing with the Service Worker `fetch` event makes it the right tool for offline HTTP, the wrong tool for offline business logic.
- IndexedDB is the default structured store for application data: objects with indexed fields, transactions, and async access from main thread and workers alike. It supports binary types (Blob, ArrayBuffer) directly without serialization, so it can hold images and other media if OPFS is not available.
- OPFS is the default for binary blobs and large files where IndexedDB's serialization overhead would be wasteful. It also unlocks synchronous file IO inside Workers, which sqlite-wasm and similar engines rely on for byte-level random access.

### Choosing between IndexedDB and OPFS

When the data is structured records with indexed queries (notes, contacts, mutations queue), IndexedDB is the right answer. When the data is binary blobs (PDFs, audio, video, sqlite database files), OPFS is the right answer. When the data is HTTP responses that the service worker should serve while offline, the Cache API is the right answer. Mixing all three in a single app is normal: shell HTML in the Cache, user records in IndexedDB, large attachments on OPFS.

### Decision matrix

| Data | Best fit | Reason |
|---|---|---|
| App shell HTML, CSS, JS | Cache API | Served by the SW `fetch` handler |
| User records (notes, contacts) | IndexedDB | Indexed queries, transactions |
| Pending mutations queue | IndexedDB | Ordered append, transactional flush |
| Large binary blobs (images, audio) | OPFS | No structured-clone tax |
| In-browser sqlite or DuckDB | OPFS (sync) | Byte-level random access |
| Small config flags | IndexedDB key/value store | Avoids `localStorage` blocking |
| Auth tokens | Cookies (HttpOnly) or memory | Server visibility, no JS exposure |
| Wizard step or form draft | `sessionStorage` | Tab lifetime is exactly the wizard's life |

## IndexedDB with `idb`

The native IndexedDB API is verbose (callbacks, request objects, version-change events) and easy to mis-handle. The `idb` library by Jake Archibald wraps it in a Promise API while staying a thin shim over the native interface (no schema layer, no DSL).

```ts
import { openDB } from 'idb';

const db = await openDB('acme', 3, {
  upgrade(db, oldVersion) {
    if (oldVersion < 1) db.createObjectStore('docs', { keyPath: 'id' });
    if (oldVersion < 2) db.createObjectStore('mutations', { autoIncrement: true });
    if (oldVersion < 3) {
      const tx = db.transaction('docs', 'readwrite');
      // migration logic for v3 schema
    }
  }
});
await db.put('docs', { id: 1, title: 'Hello' });
```

### Anatomy of the example

- The database is named (`acme`) and explicitly versioned (`3`). Bumping the version is the only way to trigger a schema migration. The version is a positive integer; calling `openDB` with a lower number than the stored version throws.
- The `upgrade` callback receives the old version. The standard pattern is a chain of `if (oldVersion < N)` blocks. Each block applies the deltas for that version. This makes the upgrade reentrant: a user opening v3 from v0 runs all three blocks in order; a user upgrading from v2 to v3 runs only the third.
- Object stores are created with `createObjectStore(name, options)`. `keyPath` extracts the key from a property of the stored object. `autoIncrement` is the alternative for log-style stores where the consumer does not provide a key.
- Migrations that touch existing data inside `upgrade` must use a transaction obtained from the `upgrade` event itself. Do not open a fresh transaction from the outer scope inside `upgrade`; it will deadlock against the version-change transaction.
- `db.put('docs', { id: 1, title: 'Hello' })` is the upsert primitive: insert if missing, replace if present. Use `add` for strict insert-or-fail semantics.

### When to consider Dexie.js

For schema-driven workflows where TypeScript types should drive the storage layer, Dexie.js is the typed alternative. It adds a fluent schema builder (`db.version(3).stores({ docs: 'id, title, *tags' })`), Promise-friendly query syntax, and an optional sync addon (Dexie Cloud) for multi-device replication. Use Dexie when the schema is non-trivial and the team values declarative migrations over per-version imperative code; use `idb` when the priority is minimal abstraction over the standard API.

### Common pitfalls

- **Transactions that span microtasks**: an IndexedDB transaction auto-commits at the end of the current microtask checkpoint. Awaiting a non-IndexedDB Promise inside a transaction body silently aborts it. Keep transactions short and avoid mixing them with `fetch`, `setTimeout`, or other async sources.
- **Schema deletion**: deleting an object store deletes its data. Removing a store in `upgrade` should be matched by an external migration that exported the data first, if it still matters.
- **Long-running queries on the main thread**: large reads (cursor over thousands of records) block the renderer if executed on the main thread. Move heavy queries to a dedicated Worker that opens its own connection to the same database.
- **Forgetting cross-tab coordination**: two tabs of the same origin share the same IndexedDB. Concurrent writes from different tabs need either a coordination layer (Web Locks API, `BroadcastChannel` for invalidation messages) or carefully scoped transactions. Without it, the last write wins silently.
- **Mixing `idb` with raw IndexedDB calls**: the `idb` wrapper attaches its Promise semantics to the request objects. Mixing it with bare `request.onsuccess` callbacks in the same transaction creates subtle ordering bugs. Pick one style per module.

### A simple mutations-queue pattern

A common offline-first pattern keeps a mutations queue in IndexedDB. The app writes locally first, queues a mutation, and a background flush job (typically driven by Background Sync) drains the queue when connectivity returns:

```ts
import { openDB } from 'idb';

const db = await openDB('acme', 3, {
  upgrade(db, oldVersion) {
    if (oldVersion < 1) db.createObjectStore('docs', { keyPath: 'id' });
    if (oldVersion < 2) db.createObjectStore('mutations', { autoIncrement: true });
  }
});

async function applyMutationLocal(mutation) {
  const tx = db.transaction(['docs', 'mutations'], 'readwrite');
  await tx.objectStore('docs').put(mutation.payload);
  await tx.objectStore('mutations').add(mutation);
  await tx.done;
}

async function flushQueue() {
  const all = await db.getAll('mutations');
  for (const m of all) {
    await fetch('/api/mutations', { method: 'POST', body: JSON.stringify(m) });
    await db.delete('mutations', m.id);
  }
}
```

Cross-reference: pair this with the Background Sync pattern in `background-execution.md` to flush the queue automatically when the network returns. Pair with the Workbox `BackgroundSyncPlugin` shown in `service-workers.md` for the simpler HTTP-only variant.

## OPFS

The Origin Private File System is a per-origin sandboxed file system exposed through `navigator.storage`. Unlike user-visible file APIs (File System Access), OPFS files are invisible to the user, cannot be exported through native file pickers, and are scoped to the origin that created them.

### Async API

The async API works on the main thread and in any worker:

```ts
const root = await navigator.storage.getDirectory();
const fh = await root.getFileHandle('blob.bin', { create: true });
```

`navigator.storage.getDirectory()` returns the root `FileSystemDirectoryHandle` for the origin. From there, `getFileHandle(name, { create: true })` returns a handle to an existing or newly created file. Writes go through `fh.createWritable()`, which returns a `FileSystemWritableFileStream`; reads go through `fh.getFile()`, which returns a `File` whose `arrayBuffer` or `stream` methods deliver the bytes.

### Sync API (Worker only)

```ts
const root = await navigator.storage.getDirectory();
const fh = await root.getFileHandle('blob.bin', { create: true });

// Sync API: Worker context only
const access = await fh.createSyncAccessHandle();
const buf = new TextEncoder().encode('payload');
access.write(buf, { at: 0 });
access.flush();
access.close();
```

The sync API returns a `FileSystemSyncAccessHandle` whose `read`, `write`, `flush`, and `close` methods are synchronous. This is the high-performance path used by sqlite-wasm and similar engines that need byte-level random access without async overhead. It is restricted to Worker contexts because synchronous blocking IO on the main thread would freeze the UI; calling `createSyncAccessHandle` from the main thread throws.

The handle holds an exclusive lock on the file for its lifetime. A second `createSyncAccessHandle` against the same file from another worker waits or throws depending on the implementation. Always call `close()` when done, including in error paths. Use `try { ... } finally { access.close(); }` as the discipline.

### What OPFS is for

From web.dev: "The origin private file system [...] allows web apps to store and manipulate files in their very own origin-specific virtual filesystem, including low-level file manipulation, byte-by-byte access, and file streaming".

Concrete use cases:

- **In-browser databases**: sqlite-wasm, DuckDB-wasm, and similar engines compile a relational store to WebAssembly and use OPFS sync access for their backing file. Performance approaches native sqlite on disk.
- **Media editing**: a video editor that holds the working file (hundreds of megabytes to gigabytes) on OPFS to avoid copying it through IndexedDB's structured-clone path.
- **Offline document caches**: a notes app that downloads attachments to OPFS once and then serves them locally on subsequent opens.
- **AI model caches**: a client-side ML feature that downloads a WebGPU or WebAssembly model file once and reuses it across sessions without re-downloading.
- **Log buffers**: a diagnostic recorder that streams session logs to OPFS during normal operation and uploads the file on error.

### Browser support

Chromium (all versions with OPFS), Safari 17+, Firefox. The sync access handle subset has the same support matrix as the async API. The sync API was a later addition to the spec; verify on a per-feature basis before relying on it in production for older browsers. Feature-detect both the directory entry point and the sync handle separately if both code paths are reachable:

```ts
const hasOpfs = !!navigator.storage?.getDirectory;
const hasOpfsSync = hasOpfs && 'createSyncAccessHandle' in FileSystemFileHandle.prototype;
```

### Working with directories

OPFS supports nested directories, which is essential for any app that needs more than a flat namespace. The directory handle exposes `getDirectoryHandle`, `getFileHandle`, `removeEntry`, and an async iterator over entries:

```ts
const root = await navigator.storage.getDirectory();
const attachments = await root.getDirectoryHandle('attachments', { create: true });
const file = await attachments.getFileHandle('img-001.png', { create: true });

// Iterate
for await (const [name, handle] of attachments.entries()) {
  // name is 'img-001.png', handle is the FileSystemFileHandle
}

// Delete a single file
await attachments.removeEntry('img-001.png');

// Delete a directory and its contents
await root.removeEntry('attachments', { recursive: true });
```

### Performance characteristics

The sync access handle path approaches native file IO speed. Benchmarks published on web.dev show sqlite-wasm on OPFS sync delivering near-disk performance for typical workloads, an order of magnitude better than sqlite-wasm on IndexedDB-backed virtual file system. The async API is slower than the sync API but still beats IndexedDB for opaque binary blobs because it skips structured clone.

For apps that handle media (a video editor working on a 500 MiB clip, an audio recorder accumulating raw PCM data), OPFS sync from a dedicated Worker is the only path that meets interactive performance budgets on commodity hardware.

## Quota and eviction

Each browser implements its own quota and eviction policy. The numbers differ widely, and the eviction triggers differ even more. The same site can have 60% of the disk available on Chrome and a 7-day cap on Safari iOS.

### Chromium

Up to 60% of total disk size per origin, with an 80% global cap across the browser. From MDN: "In browsers based on the Chromium open-source project, including Chrome and Edge, an origin can store up to 60% of the total disk size in both persistent and best-effort modes". When the global cap is hit, the browser evicts data starting from the least recently used origin. Persistent storage (see next section) protects an origin from this eviction.

The 60% per-origin number is generous in absolute terms (60 GiB on a 100 GiB disk, 600 GiB on a 1 TiB disk), but it is a maximum, not a reservation. Other origins compete for the same global pool. An origin that needs guaranteed headroom should call `persist()` early.

### Firefox

10% of disk space (capped at 10 GiB) per origin in best-effort mode. Up to 50% of disk (capped at 8 TiB) with persistent storage granted. The 10% / 10 GiB cap is generous enough for most application data, but apps that store large media should plan for persistent storage from the start. The Firefox eviction strategy is also LRU-by-origin, with persistent origins excluded.

### Safari macOS and iOS 17+

Increased to 60% disk per origin (80% global), aligning with Chromium. Persistent Storage is supported but with a critical caveat: it requires notification permission to be effective. An origin that has not been granted notification permission cannot upgrade its storage to persistent. The 7-day ITP cap (described below) does not apply once the PWA has been installed to the Home Screen and the user has launched it from there.

### Safari iOS (non-installed PWA)

Intelligent Tracking Prevention applies a 7-day cap on script-writeable storage. Sites that the user has not interacted with for 7 days have their IndexedDB, localStorage, sessionStorage, Cache API entries, and Service Worker registrations deleted. Installed PWAs (those added to the Home Screen) have a separate container that historically avoids this cap, but WebKit bugs 190269 and 199110 have periodically eroded the guarantee.

The defensive pattern is to assume eviction can happen and to design recovery flows accordingly: cache data is treated as best-effort, source-of-truth data lives on the server, and re-hydration is fast. A PWA that depends on local-only state surviving a 7-day gap is unshippable on iOS Safari without a Home Screen install gate.

### Diagnosing eviction

When data disappears, the first instinct is to assume a bug in the app's cleanup code. Often the real cause is platform eviction. The DevTools Application panel in Chromium shows the current usage and the persistent-storage state per origin; on Safari the equivalent surface is Web Inspector's Storage tab when the page is inspected. If the app's expected data is missing and the storage estimate is at zero, it is almost certainly an eviction, not a logic bug.

Signals to log for support diagnostics:

- The result of the last `persist()` call and when it was made.
- The current `estimate()` snapshot, broken down by `usageDetails` when available.
- Whether the PWA is installed (via `getInstalledRelatedApps` or the display-mode media query).
- The platform and browser version (UA-CH headers in Chromium, parsed UA string elsewhere).

With this telemetry, a support case that opens with "my data is gone" can be triaged in minutes: persistent granted, recent estimate near quota, last interaction more than 7 days ago, Safari iOS, non-installed. That is an ITP eviction, not a bug.

### Quota summary at a glance

| Browser | Best-effort cap | Persistent cap | Eviction trigger |
|---|---|---|---|
| Chromium | 60% disk per origin (80% global) | Same, with eviction protection | Global cap exceeded, LRU-by-origin |
| Firefox | 10% disk per origin (max 10 GiB) | 50% disk per origin (max 8 TiB) | Global cap exceeded, LRU-by-origin |
| Safari macOS / iOS 17+ | 60% disk per origin (80% global) | Same, requires notification permission | Global cap, plus user "Clear Website Data" |
| Safari iOS non-installed | Best-effort, 7-day ITP cap | n/a | 7 days without user interaction |
| Safari iOS installed PWA | 60% per origin (subject to WebKit bug history) | Requires notification permission | Container clear when PWA uninstalled |

### Practical implications

- An app that needs more than a few hundred megabytes on iOS Safari should require Home Screen install before unlocking the heavy storage features.
- A Firefox-targeted app that approaches 1 GiB of cached data should call `navigator.storage.persist()` early to lift the 10% cap.
- A Chromium-targeted app gets headroom by default, but should still call `persist()` to protect against quota-pressure eviction.
- Storage planning is a per-platform exercise. A "one quota" mental model fails as soon as the app ships beyond Chrome desktop.
- On Safari iOS, the install-or-bust dynamic means the install prompt is also a storage prompt. Treat them as a single onboarding decision in product design.

## Persistent Storage

The Storage Standard exposes `navigator.storage.persist()` and `navigator.storage.estimate()` to opt into persistent storage and to inspect current usage. Persistent storage means the browser commits to not evicting the origin's data under quota pressure; it can still be cleared by the user explicitly.

```ts
async function ensurePersistent() {
  if (navigator.storage?.persist) {
    const granted = await navigator.storage.persist();
    const { quota, usage } = await navigator.storage.estimate();
    console.log({ persisted: granted, quota, usage });
  }
}
```

### Usage pattern

- Feature-detect `navigator.storage` and `navigator.storage.persist` before calling. Older browsers and some embedded WebViews lack the API.
- Call `persist()` to request the upgrade. The returned Promise resolves to `true` if granted, `false` otherwise. Do not assume the call shows a UI; the policy is browser-specific (see below).
- Call `estimate()` to retrieve the current quota and usage in bytes. Use this to drive a storage-pressure UI: warn the user when usage exceeds 80% of quota, offer a "clear cache" action.

### Per-browser policy for granting persistence

- **Chromium** grants automatically based on heuristics including the site engagement score, whether the PWA is installed, and whether the user has bookmarked the site. There is no permission prompt. A high-engagement installed PWA effectively always gets `true`. Sites that have not built up engagement get `false` silently.
- **Firefox** shows a permission prompt the first time `persist()` is called. The user sees a doorhanger and can grant or deny. The decision is remembered per origin. A denied origin can be re-asked only after the user clears site permissions.
- **Safari** requires that the origin has already been granted notification permission. Without notifications, `persist()` resolves to `false` even when the user would otherwise want persistence. This is a hard requirement, not a heuristic; design the onboarding flow to request notifications before requesting persistent storage if both are needed.

### When to call `persist()`

Call `persist()` after a meaningful engagement event (the user has completed onboarding, installed the PWA, or saved their first document), not on page load. Calling on page load is wasted on Chromium (it will use its heuristic regardless), annoying on Firefox (cold prompt without context), and fruitless on Safari (notifications are not yet granted).

A reasonable trigger sequence:

1. User completes the first meaningful action in the app (created a note, started a recording, downloaded a document).
2. App displays a soft pre-prompt explaining why offline storage matters for this app.
3. App calls `Notification.requestPermission()` if notifications are part of the value proposition.
4. App calls `navigator.storage.persist()` and records the result.
5. App falls back gracefully if `false` is returned: continue working in best-effort mode, surface a passive UI hint that data could be evicted under disk pressure.

### Monitoring usage

For ongoing monitoring, wire `estimate()` into the app's telemetry and surface quota-pressure warnings before the platform takes destructive action. A common pattern is to schedule a cleanup pass when usage exceeds a configurable threshold (for example, 80% of quota): delete old cache entries, compact IndexedDB stores, drop OPFS scratch files. Cleanup is far less disruptive than waiting for the browser to evict opaque chunks of state.

The `estimate()` return shape is `{ usage: number, quota: number, usageDetails?: { ... } }`. The optional `usageDetails` (Chromium) breaks the usage down by storage type (indexedDB, caches, serviceWorkerRegistrations, fileSystem), which is useful for diagnosing which subsystem is bloating. Log this on a debug screen for support cases.

### Recovery from eviction

Even with persistent storage granted, the user can clear site data through browser settings or, on iOS, by uninstalling the PWA. The recovery contract is the same as for any cache miss: re-derive the data from the server, hydrate IndexedDB and OPFS again, resume normal operation. Test this path explicitly; sites that have never been tested with cleared storage usually have a hidden assumption that breaks on the empty state.

To run this test in DevTools:

1. Open the Application panel.
2. Storage section, "Clear site data" with all checkboxes selected.
3. Reload the page.
4. Walk the app's primary flows. The first interaction should rehydrate transparently; if any path throws or shows an empty state with no recovery, fix the path.

### Persistent storage and the "you ran out of disk" UX

When `estimate()` shows usage approaching `quota`, the app should react before the platform does. A reasonable threshold ladder:

- Below 50% of quota: no action.
- Between 50% and 80%: passive UI hint (a small storage meter in the settings page).
- Above 80%: proactive cleanup pass (delete oldest caches, prompt the user to clear non-essential offline content).
- Above 95%: hard guard rails (block new uploads, surface a modal explaining the situation).

Without this, the first sign the user gets of a full quota is an opaque write failure deep in some interaction. That experience is much worse than a clear warning two days earlier.

### Persistent does not mean permanent

A subtle trap: `persist()` returns `true` and an engineer assumes the data is now safe forever. Persistent storage protects against quota-pressure eviction. It does not protect against:

- The user manually clearing site data through browser settings.
- The user uninstalling the PWA (on platforms where install is a discrete operation, like iOS Home Screen and Android WebAPK).
- The browser uninstalling itself (rare but possible).
- A disk failure or OS reinstall.
- A user switching to a different browser profile or device.

The app's recovery path must still work from a cold empty state. Persistent storage buys consistency under storage pressure, nothing more.

## Cross-references

- Service worker caching strategies that fill the Cache API: `service-workers.md` (Offline Cookbook table, Workbox 7 pattern).
- Background Sync to flush a mutations queue: `background-execution.md` and `service-workers.md` (`BackgroundSyncPlugin`).
- COOP and COEP headers required for `SharedArrayBuffer` (used by sqlite-wasm on OPFS sync): `security.md`.
- The `persistent-storage` permission name and the broader Permissions API: `permissions.md`.
- iOS-specific storage gotchas, the 7-day ITP cap, and the Home Screen container model: `platform-constraints.md`.

## References

- MDN, Storage Standard: `https://developer.mozilla.org/en-US/docs/Web/API/Storage_API`
- MDN, IndexedDB API: `https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API`
- MDN, File System API and OPFS: `https://developer.mozilla.org/en-US/docs/Web/API/File_System_API`
- web.dev, Origin private file system: `https://web.dev/articles/origin-private-file-system`
- web.dev, Persistent Storage: `https://web.dev/articles/persistent-storage`
- `idb` library: `https://github.com/jakearchibald/idb`
- Dexie.js: `https://dexie.org/`
- WebKit Tracking Prevention Policy: `https://webkit.org/tracking-prevention-policy/`

