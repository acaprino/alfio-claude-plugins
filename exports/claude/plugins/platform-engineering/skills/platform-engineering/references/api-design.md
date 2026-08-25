# API Design and State Management

## API Versioning and Error Handling

### MUST

- **Version your APIs from day one** -- breaking changes without versioning strand old mobile clients that can't force-update like web. Use URL path versioning (`/v1/resource`) for public APIs.
- **Implement pagination** on all list endpoints -- unbounded result sets crash mobile clients and overload servers.
- **Use standardized error responses** (RFC 7807/RFC 9457 Problem Details) with `type`, `title`, `status`, `detail`, and `instance` fields.

## REST vs GraphQL

### DO

- **Choose REST for simple CRUD, public APIs, and when HTTP caching matters.** REST's URL-based caching works natively with CDNs, proxies, and browser HTTP caches.
- **Choose GraphQL for complex nested data needs and multi-platform backends.** Research shows 66% performance improvement for mobile apps migrating from REST to GraphQL by eliminating redundant network calls. Facebook invented GraphQL in 2012 specifically because REST was too inflexible for mobile.
- **Use cursor-based pagination** for real-time or large datasets (avoids the shifting-window problem); offset-based for fixed-page navigation.

### DON'T

- Use GraphQL for simple CRUD or when HTTP caching is critical -- GraphQL's POST-to-single-endpoint pattern breaks standard CDN caching.
- Expose GraphQL introspection or allow unbounded query depth in production.

### Platform Recommendations

| Platform | Recommendation |
|----------|---------------|
| **SPA** | REST or GraphQL both work well |
| **PWA** | REST preferred -- URL-based caching integrates cleanly with service workers |
| **Mobile** | GraphQL shines -- reduces round-trips on cellular networks; use persisted queries |
| **Desktop** | REST usually sufficient; aggregate multiple calls server-side |

## State Management by Platform

### SPA

- Separate server state from UI state. Use TanStack Query or SWR for server data.
- Client state: Zustand (~3KB, ideal for small-to-medium React apps), Redux Toolkit (~45KB, enterprise-grade), or Pinia (Vue 3 standard).
- Start with built-in state (useState, ref) and graduate to external libraries when state is shared across many components.
- DON'T use React Context as a global state manager -- it triggers unnecessary re-renders of all consumers on any state change.

### PWA

- Use IndexedDB (via Dexie.js or localForage) for structured offline data -- localStorage is limited to ~5MB and is synchronous/blocking.
- Use the Cache API with service workers for asset and API response caching.
- Implement Background Sync for queuing failed writes.

### Mobile

- Use platform-standard persistence (Room on Android, CoreData/SwiftData on iOS).
- Follow unidirectional data flow: UI to Action to State to UI.
- Android: ViewModel + StateFlow. iOS: SwiftUI + ObservableObject.
- Use WorkManager (Android) and BGTaskScheduler (iOS) for background sync.

### Desktop

- **Never share mutable state directly between main and renderer processes.**
- Electron: use `ipcMain.handle`/`ipcRenderer.invoke` with preload scripts and context isolation.
- Tauri: use the `invoke` command system -- the Rust core process manages global state (settings, DB connections).
- Keep shared state between frontend and backend minimal and well-structured.

## Official docs

- RFC 7807 / 9457 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457.html
- GraphQL spec: https://spec.graphql.org/
- REST API design (Microsoft guidance): https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design
- Google API design guide: https://cloud.google.com/apis/design
- TanStack Query: https://tanstack.com/query
- SWR: https://swr.vercel.app/
- Zustand: https://zustand-demo.pmnd.rs/
- Redux Toolkit: https://redux-toolkit.js.org/
- Pinia: https://pinia.vuejs.org/
- Dexie.js (IndexedDB wrapper): https://dexie.org/
- Android Room: https://developer.android.com/training/data-storage/room
- iOS SwiftData: https://developer.apple.com/documentation/swiftdata
- Tauri IPC: https://v2.tauri.app/develop/calling-rust/
- Electron context isolation: https://www.electronjs.org/docs/latest/tutorial/context-isolation
