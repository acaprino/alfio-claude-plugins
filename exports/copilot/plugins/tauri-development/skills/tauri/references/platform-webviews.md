# Platform WebViews

Tauri uses three different web engines on desktop: WebView2 (Chromium) on Windows, WKWebView (Safari) on macOS, WebKitGTK (Safari-engine) on Linux. The version-matrix and UA strings live upstream -- this file is the strategy + the gotchas.

## When to use

Choosing CSS/JS features (Container Queries, View Transitions, OffscreenCanvas, etc.) and worrying about cross-engine compatibility, or debugging "works on my Windows machine but breaks on macOS/Linux."

## Engine baseline (worth memorizing)

| Platform | Engine | Updates with | Floor |
|----------|--------|--------------|-------|
| Windows | WebView2 (Chromium) | Edge runtime, evergreen | Win 10 1803+ |
| macOS | WKWebView (Safari) | macOS releases, NOT auto | macOS 10.15 |
| Linux | WebKitGTK | distro package | distro-dependent |

WebView2 is the most forgiving; WKWebView is tied to macOS version (a user on macOS 12 has Safari 15 features and nothing newer); WebKitGTK varies wildly by distro and is the realistic compatibility floor.

## Gotchas

- **`SharedArrayBuffer` is effectively absent on macOS/Linux.** Chromium-only. Don't design around it for cross-platform Tauri apps.
- **`OffscreenCanvas` 2D context is macOS 14+.** Windows works, Linux partial. Build a fallback path or restrict to Windows + recent macOS.
- **`structuredClone` only since Safari 15.4 (macOS 15)** -- on older macOS it silently doesn't exist. Polyfill or feature-detect.
- **CSS `env(safe-area-inset-*)` works natively only on WKWebView.** Android WebView and Linux ignore it (see `plugins-mobile.md` for the workaround).
- **Backdrop filter needs `-webkit-backdrop-filter` fallback** on WKWebView and older WebKitGTK.
- **`window.open()` blocked without user gesture** on WKWebView -- if you trigger it from a `setTimeout` or a fetch resolution, it silently fails.
- **WebView2 ignores system proxy** on some corporate networks -- traffic bypasses pac scripts. Surfaces as "works at home, breaks at customer site."
- **WebKitGTK on Wayland**: window operations (position, always-on-top) may not work; drag-and-drop may need `gtk-layer-shell`. X11 is more reliable.
- **`MediaRecorder` not on macOS until 14.5** -- if you're recording in-app, gate the feature.
- **DevTools differ wildly.**
  - Windows: `F12` or `window.open_devtools()` from Rust.
  - macOS: enable Safari → Settings → Advanced → "Show features for web developers", then Safari → Develop → [machine] → [app window]. There is no programmatic devtools toggle in release.
  - Linux: `WEBKIT_INSPECTOR_SERVER=127.0.0.1:9222` env var, then any browser at that URL.

## Cross-engine feature detection (the lazy-but-correct pattern)

```css
/* Container Queries */
@supports (container-type: inline-size) { .sidebar { container-type: inline-size; } }

/* View Transitions */
@supports (view-transition-name: any) { ::view-transition-old(root) { animation: fade-out .3s; } }

/* Backdrop filter fallback */
@supports not (backdrop-filter: blur(10px)) { .overlay { background: rgba(0,0,0,.8); } }
```

```typescript
// Engine detection -- WKWebView and WebKitGTK both report "WebKit"
const isChromium = /Chrome|Edg/.test(navigator.userAgent);
const hasOffscreen = typeof OffscreenCanvas !== 'undefined';
const hasSAB = typeof SharedArrayBuffer !== 'undefined';

// Reliable platform detection
import { platform } from '@tauri-apps/plugin-os';
const os = await platform(); // 'windows' | 'macos' | 'linux'
```

## Linux package dependency (in tauri.conf.json)

```json
"bundle": {
  "linux": {
    "deb": { "depends": ["libwebkit2gtk-4.1-0 (>= 2.40)"] },
    "rpm": { "depends": ["webkit2gtk4.1 >= 2.40"] }
  }
}
```

Without this, your `.deb` installs but the app refuses to launch with a missing-library error.

## Testing strategy

1. Develop on whatever you have (usually WebView2/Windows -- most lenient).
2. Smoke-test on macOS for WKWebView Safari-version surprises.
3. Compatibility floor on WebKitGTK (Ubuntu LTS = oldest WebKit you'll realistically hit).
4. CI matrix all three (see `ci-cd.md`).

## Official docs

- WebView2 release notes / feature tracking: https://learn.microsoft.com/en-us/microsoft-edge/webview2/release-notes
- WebKit feature support per Safari version: https://webkit.org/blog/category/web-inspector/ (and https://caniuse.com filtered by Safari)
- WebKitGTK release notes: https://webkitgtk.org/2.46.x/api-docs.html (replace version)
- MDN compatibility tables: https://developer.mozilla.org/en-US/docs/Web (each API page has a Browser compat section)
- caniuse: https://caniuse.com/

## Related

- `plugins-mobile.md` -- Android WebView safe-area workaround
- `ci-cd.md` -- the cross-platform matrix that catches engine-specific breakage
- `high-frequency-ui.md` -- engine-specific perf notes for trading UIs
