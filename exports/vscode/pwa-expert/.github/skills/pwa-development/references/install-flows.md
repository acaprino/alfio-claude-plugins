# Install Flows

How a PWA gets onto a device varies by platform. Chromium browsers expose a programmable install prompt and a set of automated installability checks. Apple platforms have no install API at all and require the user to invoke Share then Add to Home Screen manually. Desktop Chromium adds a Window Controls Overlay surface for installed PWAs that want to repaint the titlebar area. This reference covers each surface in turn, with the snippets needed to wire it up correctly.

## Chromium installability criteria

Before Chrome, Edge, or another Chromium-based browser will fire the install prompt, the page must satisfy a fixed checklist documented on web.dev under "What does it take to be installable?". The checklist is:

- Page served over HTTPS (localhost is exempt as a development convenience).
- A valid Web App Manifest is reachable and parses, with these members present:
  - `name` or `short_name`.
  - `start_url`.
  - `icons` including at least a 192x192 and a 512x512 PNG.
  - `display` set to something other than `browser`. Valid choices are `standalone`, `fullscreen`, or `minimal-ui`.
- A service worker is registered for the page's scope and has a `fetch` event handler. The handler can be empty, but it must exist; Chromium uses its presence as a proxy for offline support.

In addition to the manifest and service worker requirements, Chromium gates the install prompt on a user-engagement bar. The web.dev rule is reproduced verbatim:

> The user needs to have clicked or tapped on the page at least once, at any time, even during a previous page load. The user needs to have spent at least 30 seconds viewing the page, at any time.

The 30-second engagement is cumulative across sessions, not a per-visit threshold. The bar exists to keep low-effort sites from showing install prompts on first paint. Source: `https://web.dev/articles/install-criteria`.

If any criterion is missing, `beforeinstallprompt` will never fire. Verify the manifest with the DevTools Application panel Manifest view, which lists each missing requirement with a direct link to the offending member.

### Common reasons the prompt does not appear

In order of frequency:

1. **Manifest icon set incomplete.** The 192 and 512 PNG icons are both required. Many projects ship only one size, or ship SVG icons. Chromium will refuse to prompt.
2. **`display: browser`.** A manifest that leaves the default `display` value still loads, but installability is denied. Set it to `standalone`, `fullscreen`, or `minimal-ui`.
3. **Empty service worker.** A registered service worker with no `fetch` handler does not count. Add the handler even if it just falls back to `fetch(event.request)`.
4. **Engagement bar not yet met.** During first development, Chrome's `chrome://flags` exposes a Bypass user engagement checks flag that fires the prompt immediately for testing. Never ship that workaround.
5. **Manifest 404 or wrong MIME type.** The manifest must be served with `Content-Type: application/manifest+json`. A misconfigured server returning `text/plain` or `application/octet-stream` is a silent failure.
6. **Manifest already installed.** If the user has already installed this PWA on this profile, `beforeinstallprompt` will not fire again unless they uninstall and revisit.

DevTools Application panel runs all the same checks the install pipeline does. Open Application then Manifest, scroll to the Installability section, and act on any red item.

## beforeinstallprompt (Chromium only)

When the criteria above are all met, Chromium dispatches a `beforeinstallprompt` event on `window`. The default behavior is to show a mini-infobar at the bottom of the viewport on mobile (a small banner inviting installation). On desktop the default surface is an icon in the address bar. To replace the default with a custom UI tied to a button in the app, capture the event, suppress the default, and store it for later. When the user taps the in-app install button, call `prompt()` on the stored event.

```ts
let deferred: BeforeInstallPromptEvent | null = null;

window.addEventListener('beforeinstallprompt', (e: any) => {
  e.preventDefault();
  deferred = e;
  document.querySelector('#install')!.removeAttribute('hidden');
});

document.querySelector('#install')!.addEventListener('click', async () => {
  if (!deferred) return;
  const { outcome } = await deferred.prompt();
  console.log('outcome:', outcome);
  deferred = null;
});

window.addEventListener('appinstalled', () => {
  // Analytics
});
```

Three event handlers cover the full install lifecycle:

1. `beforeinstallprompt` captures the deferred event and reveals the in-app install button. Calling `e.preventDefault()` is what suppresses Chromium's default UI, so always call it before storing the event.
2. The click handler on the install button calls `deferred.prompt()` to show the native install dialog. The returned `outcome` is either `'accepted'` or `'dismissed'`. The event can only be prompted once; after that, set `deferred = null`.
3. `appinstalled` fires after a successful install. Use it to record an analytics event, hide any remaining install UI, and reset state. This event also fires when the user installs via the address-bar icon or the browser menu, so it is the most reliable signal of an actual install.

The `BeforeInstallPromptEvent` type is not in the standard DOM lib. Most projects declare a minimal interface or cast through `any` as in the example above. A minimal type declaration:

```ts
interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
  prompt(): Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

declare global {
  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
  }
}
```

Browser support: Chrome, Edge, Opera, Samsung Internet, and other Chromium derivatives. Not supported on Firefox or any Safari.

### Patterns for showing the install button

The install button should not be a permanent header element. Reveal it only after `beforeinstallprompt` fires, hide it after `appinstalled`, and hide it if the user dismissed the prompt in the current session. A robust handler also persists the dismissed state for a cool-off period (a week is common) to avoid re-pestering on every reload:

```ts
const COOLOFF_DAYS = 7;
const dismissedAt = Number(localStorage.getItem('install-dismissed-at') || 0);
const inCooloff = dismissedAt && (Date.now() - dismissedAt) < COOLOFF_DAYS * 86400_000;

window.addEventListener('beforeinstallprompt', (e: any) => {
  e.preventDefault();
  deferred = e;
  if (!inCooloff) {
    document.querySelector('#install')!.removeAttribute('hidden');
  }
});

document.querySelector('#install')!.addEventListener('click', async () => {
  if (!deferred) return;
  const { outcome } = await deferred.prompt();
  if (outcome === 'dismissed') {
    localStorage.setItem('install-dismissed-at', String(Date.now()));
  }
  document.querySelector('#install')!.setAttribute('hidden', '');
  deferred = null;
});
```

The `appinstalled` event also fires for installs triggered through the browser address-bar icon or three-dot menu, not just through `prompt()`. Always treat it as the canonical install signal in analytics.

## iOS manual install

Apple platforms expose no install API. There is no `beforeinstallprompt` equivalent on Safari for iOS, iPadOS, or macOS. The user must open the Share menu and tap Add to Home Screen. The app must therefore detect that it is currently running in a regular browser tab and surface a custom hint pointing at the Share button.

The detection is done in CSS using the `display-mode` media query. When the user has not yet installed the PWA, the page runs with `display-mode: browser`. After installation, the page launches with the manifest's chosen `display` mode (for example `standalone`). Gating the hint on the browser display mode ensures it disappears the moment the user installs.

```css
@media (display-mode: browser) {
  #ios-install-hint { display: block; }
}
```

The hint should match Apple's UI vocabulary. A typical instruction reads: 'Tap the Share icon then "Add to Home Screen"'. Render an animated icon pointing at the Share button position. On iPhone the Share button sits in the bottom toolbar; on iPad it is in the top-right.

User-agent sniffing is required to limit the hint to iOS Safari. Chrome for iOS, Firefox for iOS, and every other third-party browser on Apple platforms are forced to use WKWebView under App Store guideline 2.5.6, and none of them can create a Home Screen web app. Showing an install hint inside Chrome for iOS would tell the user to use a feature their browser does not have. A reasonable check:

```ts
function isIosSafari(): boolean {
  const ua = navigator.userAgent;
  const isIos = /iPad|iPhone|iPod/.test(ua);
  const isWebkit = /WebKit/.test(ua);
  const isChromeOrFirefox = /CriOS|FxiOS|EdgiOS|OPiOS/.test(ua);
  return isIos && isWebkit && !isChromeOrFirefox;
}

if (isIosSafari() && window.matchMedia('(display-mode: browser)').matches) {
  document.querySelector('#ios-install-hint')!.removeAttribute('hidden');
}
```

The hint is one-shot. Once the user dismisses it or installs the app, store the choice in `localStorage` and do not re-display. Pestering users with install hints on every visit is a known anti-pattern.

### iOS install state transitions

After the user installs, the launch context changes in two observable ways. The `navigator.standalone` boolean (a non-standard Apple property) is `true` when the page runs from a Home Screen icon, and the `display-mode` media query reports `standalone` instead of `browser`. Both signals are reliable starting with iOS 16.4. Use them at startup to skip onboarding, request push subscription, or unhide standalone-only UI.

```ts
const isInstalled =
  window.matchMedia('(display-mode: standalone)').matches ||
  (navigator as any).standalone === true;
```

There is no `beforeinstallprompt` and no `appinstalled` event on iOS. To detect a fresh install for analytics, compare the current `isInstalled` state against a stored prior state on every load. The first load where `isInstalled` flips from `false` to `true` is the install event.

### iOS meta tag dependencies

The install hint is moot if the launched app then renders inside a browser-chrome window. Make sure the manifest has `display: standalone` (or stronger) and the HTML head includes the legacy Apple meta tags, which iOS Safari still consults preferentially:

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
```

The `apple-touch-icon` is also what iOS uses for the Home Screen icon if no maskable manifest icon is supplied. Source the icon as an opaque PNG with no transparency; iOS will render the alpha channel as black.

## getInstalledRelatedApps()

A PWA that has a native counterpart (an Android app on Google Play or a Windows app from the Microsoft Store) should suppress its own install banner when the native version is already installed. The `getInstalledRelatedApps()` API returns the list of related native apps that the platform recognizes as belonging to the same publisher.

```ts
const apps = await (navigator as any).getInstalledRelatedApps();
if (apps.find(a => a.id === 'com.acme.suite')) hideInstallBanner();
```

The API requires the manifest to declare the relationship via `related_applications`:

```json
{
  "related_applications": [
    { "platform": "play", "id": "com.acme.suite" },
    { "platform": "windows", "id": "AcmeSuite_8wekyb3d8bbwe!App" }
  ],
  "prefer_related_applications": false
}
```

Set `prefer_related_applications` to `false` so Chrome does not push the native app over the PWA on Android. The API is Chromium only and currently lists native apps on Android (Google Play) and Windows (Microsoft Store). Calls on other platforms resolve to an empty array. The matching is on app id only; the API does not currently support cross-checking that the same user is signed in across both apps.

Use this signal to hide the in-app install button, hide the iOS install hint, and skip any tutorial dialog that assumes a first-touch install. If the native counterpart is preferred for some flows (a deep link into a feature only the native app implements), deep-link out to it.

Wrap the call in a feature check, since the API is not universally available:

```ts
async function getInstalledNative(): Promise<string[]> {
  if (!('getInstalledRelatedApps' in navigator)) return [];
  const apps = await (navigator as any).getInstalledRelatedApps();
  return apps.map((a: any) => a.id);
}

const installed = await getInstalledNative();
if (installed.includes('com.acme.suite')) {
  document.querySelector('#install')?.setAttribute('hidden', '');
  document.querySelector('#ios-install-hint')?.setAttribute('hidden', '');
}
```

The native id formats vary by platform: `play` uses the Android package name, `windows` uses the Microsoft Store family name with `!App` suffix, `chrome_web_store` uses the extension id. The exact id values must match what the published native app declares to its store.

## Window Controls Overlay (desktop)

Window Controls Overlay (WCO) lets an installed desktop PWA paint its own content into the titlebar area, alongside the minimize, maximize, and close buttons. The default standalone window has a generic titlebar with the app name; WCO removes that titlebar and gives the app the full window canvas, with reserved space for the system controls on the right (or left, depending on locale).

Opt in via the manifest:

```json
{
  "display_override": ["window-controls-overlay", "standalone"],
  "display": "standalone"
}
```

`display_override` is an ordered fallback list. Browsers that understand `window-controls-overlay` use it; older browsers fall back to `standalone`. The `display` member is still required as the ultimate fallback.

The titlebar area is exposed to CSS via four environment variables: `titlebar-area-x`, `titlebar-area-y`, `titlebar-area-width`, and `titlebar-area-height`. Each takes a fallback value used when the page is not running in WCO mode. The `-webkit-app-region` property controls whether a region is draggable (acts as the titlebar grab) or not.

```css
.titlebar {
  position: fixed; top: 0; left: env(titlebar-area-x, 0);
  width: env(titlebar-area-width, 100%);
  height: env(titlebar-area-height, 33px);
  -webkit-app-region: drag;
}
.titlebar button { -webkit-app-region: no-drag; }
```

Set the parent strip to `drag` so the user can grab anywhere except over interactive controls. Set every interactive child (buttons, menus, inputs) to `no-drag` so clicks reach them instead of triggering a window move.

To react to titlebar geometry changes (the user resizes the window, changes the system locale, toggles the maximize state), listen on `navigator.windowControlsOverlay`:

```ts
if ('windowControlsOverlay' in navigator) {
  navigator.windowControlsOverlay.addEventListener('geometrychange', e => {
    const { width } = (e as any).titlebarAreaRect;
    document.body.classList.toggle('narrow', width < 250);
  });
}
```

The `geometrychange` event fires whenever the reserved control area moves or resizes. Use it to hide secondary titlebar widgets when space is tight or to reposition app controls if the system controls flipped sides (Windows on the right, GNOME by default on the right, but right-to-left locales reverse this).

Window Controls Overlay is Chrome and Edge desktop only. It does not apply on mobile (where the OS handles all chrome) and it does not work on Safari macOS Add-to-Dock PWAs. Microsoft Edge made WCO the default for installed PWAs in September 2022. From the Edge blog: "We're now releasing the Window Controls Overlay feature as a default experience for all to use in Microsoft Edge 105". On Chrome the manifest opt-in is still required.

Best practice is to put non-essential branding in the overlay area (logo, app title, lightweight nav) and keep critical interactive controls out of the reserved system-controls zone. The system controls cover a fixed region on each platform; reading `titlebarAreaRect` gives the precise rectangle, which is the only safe way to know what space is yours.

### Detecting WCO at runtime

Some app flows want to know whether WCO is currently active (the user might have it disabled via OS settings, or the window might be in a state where it does not apply). The `visible` property on `navigator.windowControlsOverlay` is the live indicator:

```ts
function isWcoActive(): boolean {
  return 'windowControlsOverlay' in navigator
    && (navigator as any).windowControlsOverlay.visible;
}
```

Toggle a body class accordingly so CSS can switch between a traditional titlebar layout and a WCO-aware layout:

```ts
function applyWcoClass() {
  document.body.classList.toggle('wco', isWcoActive());
}
applyWcoClass();
if ('windowControlsOverlay' in navigator) {
  (navigator as any).windowControlsOverlay.addEventListener('geometrychange', applyWcoClass);
}
```

### Accessibility in WCO

The draggable titlebar competes with text selection and pointer events. Any control inside the titlebar strip must explicitly set `-webkit-app-region: no-drag` or it will swallow clicks into a window-move gesture. Keyboard users get nothing from the drag affordance, so duplicate any window-management actions (close, minimize, maximize) through the system menu rather than relying on the overlay for them.

Test WCO in three states: the default standalone window with WCO disabled (older Chrome), WCO with the system controls on the right (Windows, GNOME default), and WCO with controls on the left (macOS, right-to-left locales). The `titlebarAreaRect` event payload tells you which side the controls are on by inspecting `x` and `width` against the viewport width.

### Browser support summary

| Surface | Chrome | Edge | Safari iOS | Safari macOS | Firefox |
|---|---|---|---|---|---|
| `beforeinstallprompt` | Yes | Yes | No | No | No |
| `appinstalled` | Yes | Yes | No | No (Add to Dock has no event) | No |
| iOS Share install | n/a | n/a | Yes (Safari only) | n/a | n/a |
| Add to Dock | n/a | n/a | n/a | macOS 14 Sonoma+ | n/a |
| `getInstalledRelatedApps` | Yes (Android, Windows) | Yes (Windows) | No | No | No |
| Window Controls Overlay | Yes (desktop) | Yes (default since 105) | No | No | No |

For coverage across all four browser families, plan three install paths: programmatic prompt on Chromium, manual hint on iOS Safari, and a passive no-op on Firefox (display the manifest and let the user invoke install through the browser menu where available).
