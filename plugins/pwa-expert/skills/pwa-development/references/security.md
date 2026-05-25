# Security

Security posture for a Progressive Web App in 2025-2026. The PWA threat model is narrower than a generic web app on paper (HTTPS-only by spec, secure-context-only APIs, sandboxed origin) and wider in practice (long-lived service worker, persistent storage, push subscription endpoints, install surface). This reference covers the headers, transport, and platform requirements that a production PWA must satisfy.

## HTTPS requirement

Service workers are gated behind a secure context. The browser will refuse to register `/sw.js` over plain HTTP, and `navigator.serviceWorker` is undefined on insecure origins.

Consequences for a PWA deployment:

- All resources the service worker controls must be served over HTTPS.
- Mixed content (HTTP subresources on an HTTPS page) is blocked by the user agent for active content and downgraded for passive content. A single blocked script reference can break the install handler.
- Certificate problems (expired, self-signed without local trust, hostname mismatch) prevent registration. The error surface is the DevTools Application panel rather than the page console.
- The manifest URL, the start URL, every icon URL, and every URL the service worker fetches must resolve to HTTPS origins. A `manifest.webmanifest` served over HTTPS that references an HTTP icon will fail Chromium installability checks.

Localhost is the documented exception. Origins resolving to `127.0.0.1`, `::1`, or `localhost` are treated as secure contexts during development so the service worker can register without a TLS certificate.

Boundaries of the exemption:

- Does not extend to `*.local` hostnames or LAN IPs reached from another device.
- Does not extend to staging environments accessed over a private VPN by hostname.
- For testing on a physical device against a local dev server, either configure a proper TLS certificate (mkcert is the conventional tool) or use a tunneling service such as ngrok or Cloudflare Tunnel which provides an HTTPS endpoint.

In production, pair HTTPS with HSTS:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

The one-year `max-age`, `includeSubDomains`, and `preload` token together qualify the origin for the Chromium HSTS preload list. Preload-list submission is a one-way door: once accepted, removal takes months. Confirm subdomain coverage before submitting.

## CSP for PWAs

A restrictive Content-Security-Policy is recommended. The PWA-specific concerns are that the policy must permit the service worker file, dedicated workers, and any WebAssembly module the application loads. A policy authored for a traditional page that omits `worker-src` will block service worker registration silently.

Recommended baseline header:

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; connect-src 'self' https://api.acme.com; img-src 'self' data: https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
```

Why each directive matters for a PWA:

- `default-src 'self'`: deny-by-default fallback for any resource type not explicitly listed. Future-proofs against new fetch types.
- `script-src 'self' 'wasm-unsafe-eval'`: scripts only from same origin. The `'wasm-unsafe-eval'` token authorises WebAssembly compilation and instantiation. Required for sqlite-wasm, any WASM image codec, ONNX Runtime Web, or other compiled modules. Without it, `WebAssembly.compile()` and `WebAssembly.instantiate()` throw with a CSP violation.
- `worker-src 'self'`: required for service workers AND dedicated workers. The browser fetches the worker script under this directive, not under `script-src`. Omitting `worker-src` while having a restrictive `default-src` is the most common cause of "service worker registration failed" in policy-hardened deployments. The violation report points at the SW URL, which makes diagnosis quick once the report is read.
- `connect-src 'self' https://api.acme.com`: same-origin XHR / fetch / WebSocket / EventSource, plus the explicit API origin. The service worker's `fetch` handler issues requests under this directive too. A forgotten API origin produces opaque errors inside the SW with no helpful console message because the SW console is separate from the page console.
- `img-src 'self' data: https:`: same origin, inline data URIs (used by some manifest icon flows and by canvas-encoded thumbnails), and any HTTPS image. Tighten to specific CDN origins if the application does not render user-supplied imagery from arbitrary origins.
- `object-src 'none'`: deny `<object>`, `<embed>`, `<applet>`. Closes a long-standing XSS vector. No legitimate PWA needs plugin content.
- `base-uri 'self'`: prevents an injected `<base>` tag from rewriting relative URLs to an attacker origin. Important because service worker scope is interpreted relative to the document URL, and a hijacked base URL can shift that scope unexpectedly.
- `frame-ancestors 'none'`: deny framing. Equivalent in spirit to `X-Frame-Options: DENY` but enforced at the CSP layer. A PWA window that requires standalone or window-controls-overlay display modes has no use case for being framed.

Notes on the directives intentionally omitted from the baseline:

- `'strict-dynamic'`: a useful token for SPA bundles that load chunks via trusted loader scripts. The trade-off is that `'strict-dynamic'` disables host-source allowlists for transitively loaded scripts. If a service worker uses `importScripts()` to pull a Workbox runtime from a CDN, that import is governed by `script-src` rather than `worker-src`, and `'strict-dynamic'` interaction must be tested before relying on the token. The safer default is to bundle all worker scripts at build time and avoid `importScripts()` from third-party origins.
- `'unsafe-inline'`: must remain absent. Most modern frameworks have moved away from inline script and style; a CSP that requires `'unsafe-inline'` indicates a build configuration to revisit.
- `'unsafe-eval'`: must remain absent. The narrower `'wasm-unsafe-eval'` token authorises WebAssembly without re-opening dynamic JavaScript evaluation.

Reporting:

```http
Content-Security-Policy-Report-Only: <same policy>; report-to csp-endpoint
Reporting-Endpoints: csp-endpoint="https://api.acme.com/csp-report"
```

Run a `Report-Only` policy for at least one release cycle before promoting to enforcement. Service-worker-related violations are particularly easy to miss because the SW runs after the document has been delivered and any CSP violation it triggers reports against the worker script URL rather than the document URL.

Common PWA-specific CSP traps:

- Build pipelines that inject inline `<style>` blocks for critical CSS will fail under `style-src 'self'`. Either use a hash (`style-src 'self' 'sha256-...'`) generated by the build, or move critical CSS out of inline blocks.
- Workbox in dev mode loads diagnostic scripts from `unpkg.com`. The dev policy must allow that origin or use `vite-plugin-pwa`'s built-in dev SW mode that bundles everything locally.
- Some analytics vendors load scripts dynamically by injecting `<script>` tags after page load. `'strict-dynamic'` is needed in that case, but it disables host allowlisting so the entire script-src strategy must be reconsidered.
- Browser extensions that inject content into the page can trigger CSP violations attributed to the page origin. Violation reports from `chrome-extension://`, `moz-extension://`, or `safari-web-extension://` schemes can usually be filtered server-side.

## COOP and COEP

Cross-Origin-Opener-Policy and Cross-Origin-Embedder-Policy gate cross-origin isolation. A document is cross-origin isolated when it serves both:

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Cross-origin isolation unlocks a set of high-power capabilities:

- `SharedArrayBuffer` and the `Atomics.wait` / `Atomics.notify` primitives.
- High-resolution `performance.now()` timers (microsecond precision rather than the post-Spectre downgraded 100 microsecond floor).
- `performance.measureUserAgentSpecificMemory()` for memory profiling.
- Multithreaded WebAssembly modules that rely on shared linear memory.

For a PWA the most common reason to enable isolation is `SharedArrayBuffer`, which is required by sqlite-wasm running against the OPFS (Origin Private File System) sync access handle. Without isolation, sqlite-wasm falls back to the slower OPFS asynchronous path or to IndexedDB-backed VFS, with measurable performance loss on write-heavy workloads.

Practical impact of enabling COEP `require-corp`:

- Every cross-origin subresource (image, script, stylesheet, font, fetch response) must either declare `Cross-Origin-Resource-Policy: cross-origin` (or `same-site`) or be requested with the `crossorigin` attribute and respond with the appropriate CORS headers.
- Third-party embeds that do not ship CORP headers will break. Examples that have historically caused friction: legacy CDN images, analytics pixel tags, some embedded video players, ad iframes.
- The migration path is to inventory cross-origin subresources first, confirm CORP / CORS coverage, then enable enforcement. The intermediate step is the Report-Only variant:

  ```http
  Cross-Origin-Embedder-Policy-Report-Only: require-corp
  Cross-Origin-Opener-Policy-Report-Only: same-origin
  ```

- Service worker fetches inherit the document's isolation state. A SW running in an isolated document cannot proxy a cross-origin response that lacks CORP unless it strips or rewrites the response in a way that preserves the security invariant. The cleaner solution is to ensure the origin server emits CORP.
- Popup windows opened from an isolated document inherit isolation only if the popup origin also serves the required headers. The `window.open()` reference is severed when isolation states differ, which can break OAuth popup flows that expected to call back into the opener.
- `document.domain` is no longer writable in cross-origin-isolated documents. Legacy multi-subdomain coordination via `document.domain` setters must be migrated to `postMessage` before enabling isolation.

Decision matrix:

- No `SharedArrayBuffer` requirement: omit COEP and ship COOP `same-origin-allow-popups` or `same-origin`. This still protects against cross-window references (window opener attacks, tab-napping) without the cross-origin embedding cost.
- `SharedArrayBuffer` required: enable both COOP `same-origin` and COEP `require-corp`. Audit every cross-origin subresource first.
- Mixed: serve the cross-origin-isolated experience only on the routes that need it. Browsers re-evaluate isolation per top-level navigation, so a non-isolated landing page can hand off to an isolated `/editor` route that loads the sqlite-wasm bundle.

## Secure context requirements

A "secure context" is a Window or Worker whose top-level browsing context was loaded over HTTPS (or one of the local exemptions: `localhost`, `127.0.0.1`, `::1`, or a `file://` URL with appropriate browser flags). Many modern web platform APIs are gated on this condition and are simply undefined or throw `SecurityError` on insecure origins.

PWA-relevant APIs that require a secure context:

- Service Worker (`navigator.serviceWorker`)
- Push API and the Notifications API in service worker scope
- Geolocation (`navigator.geolocation`)
- Camera and Microphone (`getUserMedia`)
- Clipboard read and write (`navigator.clipboard`)
- Origin Private File System (`navigator.storage.getDirectory()`)
- Web Authentication / Passkeys (`navigator.credentials`)
- Web Bluetooth (`navigator.bluetooth`)
- WebUSB (`navigator.usb`)
- WebHID (`navigator.hid`)
- Web Serial (`navigator.serial`)
- Persistent storage requests (`navigator.storage.persist()`)
- Background Sync, Periodic Background Sync, Background Fetch
- Screen Wake Lock (`navigator.wakeLock`)
- Web Share with files
- Encrypted Media Extensions (`navigator.requestMediaKeySystemAccess`)
- Web Crypto's `crypto.subtle` surface

Inheritance rules:

- A secure top-level document propagates its secure context to same-origin iframes it embeds.
- A non-secure ancestor poisons descendants. An HTTPS iframe inside an HTTP parent is not a secure context.
- Workers inherit from the document that created them. Service workers inherit from their registering page.

Feature detection should test the API surface directly rather than the `isSecureContext` boolean. A graceful-degradation path that renders a static install hint when the SW is unavailable produces a better user experience than a hard failure. The audit pattern:

```javascript
if (!window.isSecureContext) {
  // Render a banner explaining HTTPS requirement, useful only during development.
  return;
}
if (!('serviceWorker' in navigator)) {
  // Browser does not support service workers at all; fall back to a static experience.
  return;
}
```

Pair feature detection with capability detection where the API exists but the platform restricts it. For example, the Push API surface is defined on iOS Safari, but `pushManager.subscribe()` only resolves after Add to Home Screen. Code that gates on `'PushManager' in window` alone will show a misleading "permission denied" state to in-browser visitors.

## Permissions-Policy

The `Permissions-Policy` response header (formerly `Feature-Policy`) restricts which web platform features the document and any nested browsing contexts may use. For a PWA the primary use case is to deny access to powerful APIs from third-party iframes the application embeds, and to make the document's own capability surface explicit.

A restrictive baseline that denies third-party iframes the most sensitive capabilities:

```http
Permissions-Policy: camera=(self), microphone=(self), geolocation=(self), payment=(self), usb=(), bluetooth=(), serial=(), hid=()
```

Token meanings:

- `(self)`: allow the feature in the top-level document and in same-origin iframes.
- `()`: deny the feature everywhere, including the top-level document. Useful for hardening a capability the PWA never uses.
- `*`: allow everywhere, including cross-origin iframes. Avoid for any sensitive capability.
- `(self "https://embed.example.com")`: allow same origin plus the named cross-origin embed.

Hardening defaults to consider adding when the PWA does not use the capability at all: `accelerometer=()`, `gyroscope=()`, `magnetometer=()`, `ambient-light-sensor=()`, `local-fonts=()`, `idle-detection=()`, `screen-wake-lock=(self)`, `display-capture=()`.

Cross-reference: see `permissions.md` for the full header syntax, the complete list of policy-controlled features, and the per-platform availability matrix covering iOS, Android, and Desktop. The Permissions-Policy header and the Permissions API are complementary: Permissions-Policy gates which origins may request a capability at all, while the Permissions API tracks the user's grant state for capabilities the origin is allowed to request. A capability denied by Permissions-Policy will surface as `denied` from `navigator.permissions.query()` without ever prompting the user.

## Additional production hardening

Headers that are not strictly PWA-specific but should accompany the policies above:

- `Referrer-Policy: strict-origin-when-cross-origin`: leak only the origin (not the full path) on cross-origin requests, and nothing at all on HTTPS to HTTP downgrades.
- `X-Content-Type-Options: nosniff`: prevent MIME-type sniffing on responses. Important for the service worker file: a `/sw.js` served as `text/html` by a misconfigured server will be rejected by the browser.
- `Cross-Origin-Resource-Policy: same-origin`: declare that origin-owned resources should not be embeddable cross-origin. Pair with COEP enforcement on the consuming side.

Cookie posture for the API origin the PWA calls:

- `Secure`: required on HTTPS, forbidden on HTTP.
- `HttpOnly`: cookies the JS does not need to read.
- `SameSite=Lax` for session cookies; `SameSite=None; Secure` only when cross-site embedding is intentional.
- `__Host-` prefix on session cookies to bind them to the origin and path `/`.

Subresource Integrity (SRI) for any third-party script the PWA does load via `<script src>`. The integrity hash protects against CDN compromise. Note that SRI does not apply to service-worker `importScripts()`; for that path the only safe option is to bundle dependencies at build time.

Service worker as an attack surface:

- A compromised SW persists across navigations and survives until explicitly unregistered. Treat its source like deploy-critical infrastructure.
- Code review should confirm the SW does not blindly cache or replay authenticated responses (avoid caching `Authorization`-bearing requests under CacheFirst).
- The SW should validate that registration targets the expected scope. A scope wider than necessary increases blast radius.
- Plan for emergency unregister: ship a "kill switch" endpoint or version flag that the active SW can detect and self-unregister via `self.registration.unregister()`.
