# Backend and Platform Performance

## API and Database Performance

### MUST

- **Implement pagination on all list endpoints.** Cursor-based pagination maintains consistent performance regardless of dataset size -- offset pagination with `LIMIT 20 OFFSET 20000` still internally processes 20,000 rows.
- **Enable response compression** -- Brotli or gzip reduces JSON payloads by 70-90%.
- **Create indexes on frequently queried columns and foreign keys.** Without indexes, every query becomes a full table scan. 1M rows: indexed lookup ~1ms vs full scan ~1000ms+.
- **Use EXPLAIN/EXPLAIN ANALYZE on all slow queries.** Watch for `type=ALL` (full table scan), missing indexes, and unexpected row counts.
- **Implement connection pooling** -- documented improvement: 150ms to 12ms average response time, CPU from 80% to 15%.

### DO

- Migrate to HTTP/2+ for multiplexed requests and header compression. HTTP/3 (QUIC) adds 0-RTT connection establishment, particularly beneficial for mobile with frequent network switching.
- Use GraphQL field selection or REST sparse fieldsets to avoid transferring unnecessary data -- one optimization replacing `SELECT *` with specific columns on a 5-table join improved query time from 45 seconds to 2 seconds.
- Use read replicas for read-heavy workloads.

### DON'T

- Wrap indexed columns in functions -- `WHERE YEAR(created_at) = 2025` makes the index useless. Use range comparisons instead.
- Ignore ORM-generated SQL -- ORMs frequently produce N+1 patterns and unnecessary JOINs.
- Over-index -- every index slows writes and consumes storage.

## Mobile Battery and Memory

### MUST

- **Use push notifications instead of polling** for real-time updates -- polling wakes the cellular radio repeatedly, each cycle costing significant battery.
- Batch network requests to minimize radio wake-ups.
- **Detect and fix memory leaks** using LeakCanary (Android) and Xcode Instruments (iOS). Common causes: inner class references, unclosed listeners, retained activities/fragments.
- **Respond to memory pressure callbacks** -- `onTrimMemory()` on Android, `didReceiveMemoryWarning` on iOS -- by clearing caches and releasing resources.

### DO

- Virtualize long lists using RecyclerView (Android), UICollectionView (iOS), or FlatList (React Native). Never render 1000+ items in a ScrollView.
- Flatten view hierarchies -- deep nesting causes slow layout passes.
- Profile regularly with Android Profiler, Xcode Instruments, and Firebase Performance Monitoring.
- Targets: cold start <2 seconds, frame rendering <16ms (60fps), memory <100MB during normal operations.

### DON'T

- Run background services indefinitely -- the OS kills them and they drain battery. Use WorkManager/BGTaskScheduler with appropriate constraints.
- Allocate objects in tight loops -- triggers excessive garbage collection causing visible jank.
- Use continuous GPS tracking unless essential -- GPS reduces battery by up to 33%.

### Desktop (Electron) Memory

- Each window spawns a new Chromium renderer process consuming ~50-100MB. Six windows can consume 1GB+.
- Monitor and prevent IPC listener accumulation -- each `ipcRenderer.on()` without cleanup is a memory leak.
- Never use synchronous IPC (`ipcRenderer.sendSync`) -- blocks the renderer completely.
- Tauri comparison: 30-50MB idle memory vs Electron's 200-500MB, <500ms startup vs 1-2 seconds, 2.5-10MB installer vs 80-150MB.

## SSR, SSG, and Hybrid Rendering

### MUST

- **Never use pure client-side rendering for SEO-critical pages.** CSR delivers a blank page until JavaScript downloads, parses, executes, and fetches data.
- **Account for hydration cost** in SSR applications -- the entire component tree re-executes client-side. On large apps, hydration can take 1-3 seconds during which the page appears interactive but isn't.

### Rendering Strategy Comparison

| Strategy | Best for | SEO | Performance | Server cost |
|----------|---------|-----|-------------|-------------|
| **SSG** | Blogs, docs, marketing | Excellent | Fastest (CDN-served) | Lowest |
| **ISR** | E-commerce catalogs, news | Excellent | Fast (cached + revalidated) | Low-Medium |
| **SSR** | Personalized pages, search results | Excellent | Good (hydration cost) | Higher |
| **CSR** | Dashboards, admin panels | Poor | Slow initial load | Low server |

### DO

- Use SSG/ISR wherever possible -- pre-built static pages served via CDN achieve near-zero TTFB, 10-100x faster than server-rendered pages.
- Use hybrid rendering: SSG for marketing pages, SSR for product listings with fresh data, CSR for authenticated dashboards.
- Implement **Island Architecture** (Astro) or **React Server Components** (Next.js) to hydrate only interactive components.
- Implement streaming SSR (React 18+, Next.js App Router) to progressively stream HTML.
- Cache SSR responses at the CDN edge with appropriate TTLs.

### DON'T

- Use SSR for content that rarely changes -- you pay server render cost on every request unnecessarily.
- Hydrate the entire page if only small sections need interactivity.
- Ignore serverless SSR cold starts (100-500ms+) -- pre-warm functions or use edge rendering.

## CDN Caching

### MUST

- **Use content hashing for all static assets** -- filenames like `app.a1b2c3.css`, set `Cache-Control: public, max-age=31536000, immutable`.
- **Never long-cache the SPA entry point** (`index.html`) -- use `Cache-Control: no-cache` so users always get the latest version that references current hashed assets.

### DO

- Use `stale-while-revalidate` for API and dynamic content: `Cache-Control: public, max-age=60, stale-while-revalidate=300`.
- Implement tag-based cache purging for surgical invalidation.
- Use cache shielding to reduce origin load.

### DON'T

- Cache personalized or authenticated responses at the CDN layer without `Vary` headers or private caching.
- Purge the entire cache when a single resource changes.
- Vary cache on Cookie header unless truly necessary -- it destroys hit rates.

## Official docs

- HTTP/2 spec (RFC 9113): https://www.rfc-editor.org/rfc/rfc9113
- HTTP/3 spec (RFC 9114): https://www.rfc-editor.org/rfc/rfc9114
- MDN `Cache-Control`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
- `stale-while-revalidate` (RFC 5861): https://www.rfc-editor.org/rfc/rfc5861
- Postgres EXPLAIN ANALYZE: https://www.postgresql.org/docs/current/sql-explain.html
- Postgres index types: https://www.postgresql.org/docs/current/indexes-types.html
- LeakCanary (Android): https://square.github.io/leakcanary/
- Xcode Instruments: https://developer.apple.com/tutorials/instruments
- Android WorkManager: https://developer.android.com/topic/libraries/architecture/workmanager
- iOS BGTaskScheduler: https://developer.apple.com/documentation/backgroundtasks/bgtaskscheduler
- Next.js rendering modes: https://nextjs.org/docs/app/building-your-application/rendering
- React Server Components: https://react.dev/reference/rsc/server-components
- Astro Islands: https://docs.astro.build/en/concepts/islands/
- Tauri vs Electron benchmarks (community): https://github.com/Elanis/web-to-desktop-framework-comparison
