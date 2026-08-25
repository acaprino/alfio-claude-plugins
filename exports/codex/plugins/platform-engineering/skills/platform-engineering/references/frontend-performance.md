# Frontend Performance: Bundles, Images, and Core Web Vitals

## Bundle Size

The JavaScript you ship directly determines how fast your application becomes usable. **Pinterest reduced JavaScript from 2.5MB to <200KB and dropped Time to Interactive from 23 seconds to 5.6 seconds.** On slow 3G, a 2MB bundle takes ~7 seconds to download alone -- before a single line executes.

### MUST

- **Use ES modules for tree shaking.** Named imports (`import { fn } from 'lib'`) are tree-shakeable; CommonJS (`require`) is not. Mark `sideEffects: false` in package.json.
- **Implement route-based code splitting** -- without it, users download the entire application upfront. Use `React.lazy()`, Vue `defineAsyncComponent`, or Angular lazy-loaded modules.
- **Set performance budgets in CI/CD** using webpack `performance.hints: 'error'`, bundlesize, or Lighthouse CI to catch regressions before deploy.
- Target **<170KB compressed** for critical-path JavaScript on mobile.

### DO

- Replace heavy libraries with lighter alternatives: lodash to lodash-es or native methods; moment.js to dayjs or date-fns (saves ~200KB+).
- Use dynamic imports for heavy features loaded on demand.
- Use Brotli compression over gzip (15-25% smaller).
- Analyze bundles regularly with webpack-bundle-analyzer.

### DON'T

- Import entire libraries -- `import _ from 'lodash'` pulls ~70KB gzipped when you might need one function.
- Skip differential bundling -- ship modern ES2020+ to capable browsers and polyfilled bundles only to legacy browsers.
- Ignore CSS-in-JS bundle costs (some add 15-30KB+ runtime).

### Native Targets

- Mobile: target <20MB APK/IPA for lightweight apps. Enable R8/ProGuard (Android).
- Electron bundles Chromium at 80-150MB baseline regardless of app size.
- Tauri apps are <10MB total.

## Images

Images account for ~42% of LCP elements and over 60% of total page weight. Modern formats reduce payload by 50-80%.

### MUST

- **Serve images in modern formats** -- WebP minimum, AVIF with WebP fallback via `<picture>`. Browser support: WebP ~96%, AVIF ~90%+.
- **Set explicit width/height or aspect-ratio on all images** to prevent Cumulative Layout Shift.
- **Use responsive images with srcset/sizes** -- serving a 2400px image to a 375px phone wastes ~80% of downloaded bytes.
- **Never lazy-load the hero/LCP image** -- use `loading="eager"` and `fetchpriority="high"`. Preload it: `<link rel="preload" as="image" href="hero.webp" fetchpriority="high">`.

### DO

- Use `loading="lazy"` on all below-the-fold images.
- Use image CDNs (Cloudinary, imgix) for automatic format conversion, resizing, and compression.
- Compress to quality sweet spots: JPEG 75-85, WebP 75-80, AVIF 60-70.

### DON'T

- Serve unoptimized images -- a single 5MB hero image adds 3+ seconds to LCP on 4G.
- Use GIFs for animations -- replace with WebM/MP4 video for 90%+ size reduction.

### Mobile

Images are the #1 memory consumer on mobile. Downsample to display size, use LRU memory caches, recycle bitmaps, and decode off the main thread.

## Core Web Vitals

Google's Core Web Vitals measure real-world user experience and directly influence search rankings. Only ~48% of mobile pages currently pass all three metrics.

### Thresholds (75th percentile)

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | <=2.5s | 2.5-4s | >4s |
| **INP** (Interaction to Next Paint) | <=200ms | 200-500ms | >500ms |
| **CLS** (Cumulative Layout Shift) | <=0.1 | 0.1-0.25 | >0.25 |

### Business Impact

- **Vodafone:** improved LCP by 31%, saw 8% sales increase.
- **Renault:** improved LCP by 1 second, achieved 14% bounce rate reduction and 13% conversion increase.
- **Yahoo! JAPAN:** fixed CLS issues, gained 15.1% more page views per session.
- 53% of mobile users abandon sites taking more than 3 seconds to load.

### MUST (LCP)

- Preload the LCP image with `fetchpriority="high"`.
- Optimize server response time (TTFB <800ms).
- Never lazy-load the LCP element.

### MUST (INP)

- Break up long tasks (>50ms) on the main thread using `scheduler.yield()`, `requestIdleCallback`, or `setTimeout(0)`.
- Move heavy computation to Web Workers.

### MUST (CLS)

- Set explicit dimensions on all media elements.
- Use `font-display: swap` or `optional`.
- Reserve space for dynamic content with CSS `min-height`.

### DO

- Monitor with CrUX (real user data) + Lighthouse (lab data) continuously in CI. Field data from CrUX is what Google uses for ranking.

### Native Equivalents

- Cold start time (<2 seconds target), frame rendering latency (<16ms for 60fps), and layout stability during data loading.
- Desktop: track window render time, UI thread responsiveness, and resize stability.

## Official docs

- Core Web Vitals + thresholds: https://web.dev/articles/vitals
- LCP optimization guide: https://web.dev/articles/optimize-lcp
- INP optimization guide: https://web.dev/articles/optimize-inp
- CLS optimization guide: https://web.dev/articles/optimize-cls
- web.dev image optimization: https://web.dev/learn/images
- WebP / AVIF browser support (caniuse): https://caniuse.com/webp
- MDN responsive images (`srcset`/`sizes`): https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images
- MDN `font-display`: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display
- webpack-bundle-analyzer: https://github.com/webpack-contrib/webpack-bundle-analyzer
- Lighthouse CI: https://github.com/GoogleChrome/lighthouse-ci
- CrUX (Chrome User Experience Report): https://developer.chrome.com/docs/crux
- Brotli compression (RFC 7932): https://www.rfc-editor.org/rfc/rfc7932
- Pinterest case study: https://medium.com/pinterest-engineering/a-one-year-pwa-retrospective-f4a2f4129e05
