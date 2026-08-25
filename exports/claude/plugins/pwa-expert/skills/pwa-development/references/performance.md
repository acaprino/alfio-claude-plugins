# Performance

Performance is a first-class concern for PWAs. Users compare them against native apps, and Google ranks pages on the Core Web Vitals thresholds. This reference covers the 2025 metric definitions, the techniques that move the numbers, and the audit tooling for verifying them.

## Core Web Vitals 2025

The three Core Web Vitals are the user-experience metrics Google has standardized as ranking signals. From Google Search Central:

> "Largest Contentful Paint (LCP): [...] strive to have LCP occur within the first 2.5 seconds [...] Interaction To Next Paint (INP): [...] strive to have an INP of less than 200 milliseconds. Cumulative Layout Shift (CLS): [...] strive to have a CLS score of less than 0.1."

INP replaced First Input Delay (FID) on March 12, 2024. Where FID only measured the delay until the first interaction was processed, INP measures the worst-case interaction latency across the whole session, capturing the user-perceived sluggishness of taps, clicks, and key presses that FID missed.

Measurement happens at the 75th percentile (p75) in the Chrome User Experience Report (CrUX). A site passes a metric when at least 75 percent of page loads stay under the threshold. The CrUX dataset is collected from real Chrome users who opted in to anonymous telemetry, so it reflects field performance rather than lab synthetics.

The three thresholds, in summary:

| Metric | Good (p75) | What it measures |
|---|---|---|
| LCP | under 2.5 seconds | Time until the largest content element in the viewport renders |
| INP | under 200 milliseconds | Worst-case latency between user input and visual feedback across the session |
| CLS | under 0.1 | Sum of unexpected layout shifts during the page lifetime, weighted by impact area and distance |

A page reports a Core Web Vitals pass only when all three metrics are good at p75. A single failing metric drops the page out of the passing bucket.

## Techniques

### App Shell

The App Shell pattern serves a minimal HTML document plus the UI skeleton (header, navigation, layout placeholders) from a CacheFirst route in the service worker. Data is fetched separately, either by a Network request or by Stale-While-Revalidate (SWR). The shell is precached at install time, so subsequent navigations render the chrome instantly while the data layer fills in.

The shell is typically 5 to 20 KB of HTML, CSS, and bootstrap JS. Everything not strictly required for first paint is loaded on demand.

```javascript
// In the service worker
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';

precacheAndRoute(self.__WB_MANIFEST);

// App shell as the navigation fallback
registerRoute(
  new NavigationRoute(
    new CacheFirst({ cacheName: 'app-shell-v1' })
  )
);

// Data layer via SWR
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new StaleWhileRevalidate({ cacheName: 'api-cache-v1' })
);
```

### Preload critical resources

The browser's preload scanner finds resources declared with `<link rel="preload">` before the main parser reaches them, kicking off requests in parallel. For the LCP image specifically, combine `rel="preload"` with `fetchpriority="high"` so the network layer prioritizes it over below-the-fold assets.

```html
<link
  rel="preload"
  as="image"
  href="/hero.webp"
  fetchpriority="high"
  imagesrcset="/hero-480.webp 480w, /hero-960.webp 960w"
  imagesizes="100vw"
/>
```

Preload sparingly. Over-preloading floods the network with low-priority work and starves the actual critical path. Restrict preload to the LCP image, key fonts, and the first JS chunk.

### Route-based code splitting

Modern bundlers (Vite, Next.js, Nuxt) automatically split bundles per route. The entry chunk loads the framework runtime and the current route. Other routes are downloaded only when the user navigates to them, via dynamic `import()` calls the bundler rewrites into separate chunks.

In Vite, dynamic imports create their own chunks automatically:

```javascript
// router.js
const Dashboard = () => import('./views/Dashboard.vue');
const Settings = () => import('./views/Settings.vue');

const routes = [
  { path: '/dashboard', component: Dashboard },
  { path: '/settings', component: Settings },
];
```

In Next.js, `next/dynamic` provides the same affordance for component-level splitting, with an optional `loading` placeholder:

```javascript
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('../components/HeavyChart'), {
  loading: () => <p>Loading chart...</p>,
  ssr: false,
});
```

In Nuxt, pages under `pages/` are split automatically, and `defineAsyncComponent` (Vue 3) splits components.

Target the critical JS bundle at under 170 KB compressed. Anything larger pushes LCP past 2.5 seconds on mid-range mobile devices, which dominate CrUX measurements.

### fetchpriority and lazy loading

`fetchpriority="high"` on the LCP image elevates it above other in-viewport images. `fetchpriority="low"` deprioritizes images and scripts that are not on the critical path.

`loading="lazy"` defers below-the-fold images until they approach the viewport. Combine with `width` and `height` attributes so the browser reserves the layout box and avoids contributing to CLS when the image arrives.

```html
<!-- LCP image: prioritized -->
<img
  src="/hero.webp"
  fetchpriority="high"
  width="1200"
  height="600"
  alt="Product hero"
/>

<!-- Below the fold: lazy -->
<img
  src="/testimonial-1.webp"
  loading="lazy"
  width="400"
  height="300"
  alt="Customer testimonial"
/>
```

Never set `loading="lazy"` on the LCP image. Lazy loading delays the request until layout calculations finish, which directly hurts LCP.

### CSS containment

`content-visibility: auto` tells the browser it can skip rendering work for off-screen elements. The browser still allocates a layout box (sized via `contain-intrinsic-size` to avoid CLS) but skips paint, layout, and accessibility-tree work for the contained subtree until it scrolls near the viewport.

```css
.list-item {
  content-visibility: auto;
  contain-intrinsic-size: 0 240px;
}
```

This is highly effective on long lists, infinite scrolls, and tabbed content where many sections exist in the DOM but only one is visible. Always pair with `contain-intrinsic-size` to preallocate the layout box; without it, the page jumps as items become visible and the CLS score collapses.

`contain: layout paint` is a less aggressive sibling: it isolates a subtree's layout and paint from the rest of the document but does not skip work for off-screen content.

### INP and main-thread discipline

INP is dominated by long tasks on the main thread. Any task longer than 50 milliseconds blocks input from being processed, and the worst such task during the session defines INP.

Two primitives let you yield mid-work and let the browser drain pending input:

- `scheduler.yield()` (Chromium 129+, Safari 17.4+): the modern, ergonomic primitive. Returns a promise that resolves after the browser has processed any pending high-priority work (including input).
- `requestIdleCallback`: schedules a callback to run during idle time. Useful for non-urgent work like telemetry flushing or pre-rendering.

```javascript
async function processLargeList(items) {
  for (const item of items) {
    processItem(item);
    if ('scheduler' in window && 'yield' in scheduler) {
      await scheduler.yield();
    } else {
      // Fallback: yield via a 0ms timeout
      await new Promise((r) => setTimeout(r, 0));
    }
  }
}
```

Other main-thread hygiene rules:

- Move CPU-heavy work (parsing, image decoding, encryption) into a Web Worker so the main thread stays responsive.
- Debounce input handlers on rapid events (`input`, `scroll`, `mousemove`).
- Avoid synchronous layout reads after writes (the forced reflow pattern). Batch reads, then batch writes.
- Use `transform` and `opacity` for animation, not `top`, `left`, `width`, or `height` (which trigger layout).
- Use the Performance panel's "Long Tasks" view to find the worst offenders.

A long task budget worth enforcing in CI: no single task above 200 milliseconds, p95 task duration under 50 milliseconds.

### Font loading

Web fonts are a common source of both LCP regressions (text-painting is blocked until the font arrives) and CLS regressions (text reflows when the fallback swaps to the web font). Two complementary fixes:

- Self-host fonts and preload the critical weights with `<link rel="preload" as="font" crossorigin>`. Avoid third-party font CDNs that add a separate TCP and TLS handshake.
- Apply `font-display: swap` in the `@font-face` rule so the fallback renders immediately, with the web font swapping in when ready. Combine with `size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` to match the fallback metrics to the web font, eliminating the layout shift on swap.

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2');
  font-display: swap;
  size-adjust: 107%;
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}
```

### Image format selection

Modern formats reduce LCP image transfer by 25 to 50 percent versus JPEG:

- AVIF: best compression, supported in Chromium 85+, Safari 16.4+, Firefox 93+.
- WebP: nearly universal, supported everywhere except very old browsers.
- JPEG: the safe fallback via `<picture>`.

```html
<picture>
  <source srcset="/hero.avif" type="image/avif" />
  <source srcset="/hero.webp" type="image/webp" />
  <img src="/hero.jpg" alt="Product hero" width="1200" height="600" />
</picture>
```

Always declare `width` and `height` (or `aspect-ratio` in CSS) on every image so the browser reserves the layout box before the bytes arrive.

### Compression and transport

- Serve over HTTP/2 or HTTP/3. HTTP/3 (QUIC) eliminates head-of-line blocking and recovers faster from packet loss on mobile networks.
- Compress text assets with Brotli (better than gzip for HTML, CSS, and JS) or Zstd (faster on the server, comparable ratio).
- Set long `Cache-Control: public, max-age=31536000, immutable` on hashed asset URLs. Serve HTML with `Cache-Control: no-cache` so the service worker controls update behavior.

## Audit tooling

### Lighthouse

The PWA category was removed in Lighthouse 12.0.0 (Chrome 126, May 2024). From the Chrome DevTools release notes:

> "The Lighthouse panel now runs Lighthouse 12.0.0. This update brings a number of changes, including PWA category removal."

The category's removal does not mean PWA checks went away. The individual checks (manifest validation, installability heuristics, splash screen, theme color, viewport, service worker registration) moved to the DevTools Application panel, where they live under the Manifest and Service Workers sub-panels. Run them manually for each release.

The remaining Lighthouse categories (Performance, Accessibility, Best Practices, SEO) still apply to PWAs and should run in CI. Lighthouse CI integrates with GitHub Actions and surfaces regressions as PR comments.

For Core Web Vitals specifically, treat Lighthouse as a lab tool: it gives reproducible numbers under controlled conditions, but the official p75 thresholds are measured against CrUX field data. Use both.

### PWA Builder

PWA Builder (https://www.pwabuilder.com/) is Microsoft's cross-platform PWA scoring service. Paste a URL and it returns:

- A score (0 to 100) covering manifest correctness, service-worker presence, security headers, and accessibility heuristics.
- Generated store packages: signed MSIX for the Microsoft Store, Bubblewrap-based AAB for Google Play, Capacitor-wrapped Xcode project for the App Store, packaging for Meta Quest.
- A detailed report of missing manifest members, suggested icons, and security improvements.

Use PWA Builder as the second opinion on Lighthouse. Aim for a score of 80 or higher before shipping. The package generation alone is worth a daily run during release prep.

### WebPageTest

WebPageTest (https://www.webpagetest.org/) runs real browsers from instrumented machines across global locations. It provides:

- Filmstrip view of the visual progression, frame by frame.
- Per-request waterfall with detailed timing breakdown (DNS, TCP, TLS, TTFB, content download).
- Lab Core Web Vitals measurements (LCP, CLS, TBT as the lab INP proxy).
- Comparison runs between branches or competitors.
- Custom scripted flows (login, navigate, interact) so you can measure beyond the first page load.

For PWAs, WebPageTest is the lab tool that gets closest to real-world conditions. The "Mobile 4G" preset on a mid-range Android device is a representative baseline.

### CrUX dashboard

The CrUX dashboard (https://developer.chrome.com/docs/crux) exposes the field data Google uses to score Core Web Vitals. Two ways to consume it:

- BigQuery: the raw dataset, refreshed monthly, queryable by origin or page-level URL.
- CrUX API: a REST endpoint that returns the latest 28-day rolling p75 values for a given origin or page.
- Looker Studio template: a pre-built dashboard the team can clone and point at any origin.

CrUX is the only source of truth for Search Console's "Page Experience" report and the only data Google uses for ranking. Lab metrics from Lighthouse and WebPageTest correlate with CrUX but are not what Google actually scores. Always validate fixes against the CrUX field numbers, not the lab ones, before declaring a regression fixed.

The CrUX history API exposes month-over-month trends, which is the right view for catching slow regressions that don't show up in a single Lighthouse run.

## Putting it together

A practical performance plan for a PWA in 2025-2026:

1. Set CrUX-based budgets: LCP under 2.5s p75, INP under 200ms p75, CLS under 0.1 p75.
2. Adopt the App Shell pattern so navigations render instantly from cache.
3. Preload the LCP image with `fetchpriority="high"` and lazy-load everything below the fold.
4. Code-split per route. Keep the critical JS bundle under 170 KB compressed.
5. Apply `content-visibility: auto` plus `contain-intrinsic-size` to long lists.
6. Audit main-thread tasks in DevTools. Yield with `scheduler.yield()` in any loop that processes more than a few dozen items.
7. Run Lighthouse and PWA Builder in CI on every PR. Run WebPageTest weekly.
8. Track CrUX field data monthly via the CrUX API or BigQuery export. Alert when any metric drops out of the "good" bucket at p75.
