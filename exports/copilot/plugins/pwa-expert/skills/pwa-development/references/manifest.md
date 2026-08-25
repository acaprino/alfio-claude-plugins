# Web App Manifest

The Web App Manifest is a JSON document that the W3C defines as follows: *"An application manifest is a JSON document that contains startup parameters and application defaults for when a web application is launched"* (W3C Web Application Manifest, governed by the Process Document of 18 August 2025). The canonical file extension is `.webmanifest` served with `Content-Type: application/manifest+json`, although `manifest.json` served with `application/json` is accepted by most browsers. The manifest is included in the HTML head with a `<link rel="manifest">` element. The `crossorigin="use-credentials"` attribute is mandatory whenever the fetch needs to send cookies, even on the same origin.

```html
<link rel="manifest" href="/manifest.webmanifest" crossorigin="use-credentials">
```

The manifest is no longer just metadata. With `file_handlers`, `protocol_handlers`, `share_target`, `launch_handler`, and `scope_extensions`, the manifest acts as an OS-level contract that defines how an installed PWA participates in the host system: which files it opens, which URL schemes route to it, which other origins are part of its identity, and how multiple launches are reconciled. Treating the manifest as a serialisation of that contract (and not as a leftover from the bookmark era) is the right mental model for 2025-2026.

### How browsers discover and refresh the manifest

On a fresh page load Chromium follows the `<link rel="manifest">` element, fetches the JSON, validates the required members, and caches the parsed result. For an already-installed PWA the browser revalidates the manifest periodically (Chromium uses a 24-hour heuristic) and on every cold launch. Changes to identity-defining members (notably `id` and `start_url`) trigger a re-install flow rather than a transparent update. Changes to display members, icons, and shortcuts propagate at the next revalidation. Adding a new `file_handlers` or `protocol_handlers` entry to a manifest that the user already installed will register the new association only after the propagation cycle has run, which is why teams ship file-association changes ahead of the user-visible launch.

Cache headers on the manifest itself matter. Serving the manifest with a long `Cache-Control: max-age` value can pin a stale copy on the user's device for days. The pragmatic header is `Cache-Control: no-cache, must-revalidate`, which lets the browser ask each time but accept a 304 when nothing changed.

## A complete modern manifest

The example below is a 2025-vintage manifest that exercises every member relevant to a Chromium-targeted production deployment. iOS will silently ignore most of the advanced members; that asymmetry is normal and expected.

```json
{
  "id": "/?source=pwa",
  "name": "Acme Productivity Suite",
  "short_name": "Acme",
  "description": "Offline-first productivity suite for distributed teams.",
  "lang": "en-US",
  "dir": "ltr",
  "start_url": "/?source=pwa",
  "scope": "/",
  "display": "standalone",
  "display_override": ["window-controls-overlay", "standalone", "minimal-ui", "browser"],
  "orientation": "any",
  "theme_color": "#0f172a",
  "background_color": "#ffffff",
  "categories": ["productivity", "business"],
  "prefer_related_applications": false,
  "related_applications": [
    { "platform": "play", "url": "https://play.google.com/store/apps/details?id=com.acme.suite", "id": "com.acme.suite" }
  ],
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable" },
    { "src": "/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" },
    { "src": "/icons/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any" }
  ],
  "screenshots": [
    { "src": "/screens/desktop.png", "sizes": "1920x1080", "type": "image/png", "form_factor": "wide", "label": "Desktop dashboard" },
    { "src": "/screens/mobile.png", "sizes": "1080x1920", "type": "image/png", "form_factor": "narrow", "label": "Mobile dashboard" }
  ],
  "shortcuts": [
    { "name": "New document", "short_name": "New", "url": "/new?source=shortcut", "icons": [{ "src": "/icons/new-96.png", "sizes": "96x96" }] },
    { "name": "Inbox", "url": "/inbox?source=shortcut" }
  ],
  "share_target": {
    "action": "/share-target/",
    "method": "POST",
    "enctype": "multipart/form-data",
    "params": {
      "title": "name",
      "text": "description",
      "url": "link",
      "files": [{ "name": "sharedFiles", "accept": ["image/*", ".pdf"] }]
    }
  },
  "protocol_handlers": [
    { "protocol": "web+acme", "url": "/open?value=%s" },
    { "protocol": "mailto",  "url": "/compose?to=%s" }
  ],
  "file_handlers": [
    {
      "action": "/open-file",
      "accept": { "text/markdown": [".md"], "application/pdf": [".pdf"] },
      "launch_type": "single-client",
      "icons": [{ "src": "/icons/file-256.png", "sizes": "256x256", "type": "image/png" }]
    }
  ],
  "launch_handler": { "client_mode": ["focus-existing", "auto"] },
  "handle_links": "preferred",
  "scope_extensions": [
    { "type": "origin", "origin": "https://help.acme.com" },
    { "type": "origin", "origin": "https://*.acme.co.uk" }
  ],
  "edge_side_panel": { "preferred_width": 480 }
}
```

A few notes on the example.

`id` is set explicitly to `/?source=pwa` so the browser does not derive the identity from `start_url`. The same string is used for `start_url`, which has the side benefit of letting analytics attribute installed-app visits via the `source` query parameter. Why explicit? When `id` is omitted, Chromium computes it from `start_url`. Changing `start_url` later would change the computed `id` and the browser would treat the updated manifest as a different application, prompting a reinstall and orphaning prior subscriptions, shortcuts, and badges. An explicit `id` decouples the identity from any future URL evolution.

`display_override` lists `window-controls-overlay` first because Chromium desktop honours it when the user installs the app there, while iOS and Android fall through to `standalone`. The chain is interpreted in order until a value the browser supports is found. If none of the listed values is supported, `display` is consulted as the final fallback.

The two `screenshots` entries (one `wide`, one `narrow`) are required to trigger the richer install UI on Chromium and to populate store listings generated by PWA Builder. Without screenshots the install prompt falls back to a compact list-item style. The `form_factor` value categorises each screenshot so the browser can pick the right one based on the device the user is installing on.

`shortcuts` is exposed in the long-press menu on Android and the right-click jump list on desktop. Each entry should point at a deep link inside the PWA. The optional `icons` member per shortcut lets the launcher show a distinctive glyph for each action.

`prefer_related_applications: false` is the recommended default. Setting it to `true` causes installable surfaces in Chrome to suggest the native app listed in `related_applications` instead of the PWA. This is the right behaviour only when the native app is materially better.

`categories` is taken from a non-binding list that includes values like `productivity`, `business`, `social`, `news`, `entertainment`, `games`, `utilities`, `education`, `finance`, `health`. PWA Builder uses these values to fill in the corresponding store-listing fields when generating MSIX or Bubblewrap output.

`lang` and `dir` set the document language and writing direction for the launcher chrome (title, shortcut labels). They are honoured on Android, Chromium desktop, and iOS 16.4+.

`orientation` is a hint, not a lock. On Android the OS may override it under battery-saver constraints. On iOS the value is largely ignored: Safari decides orientation from the device pose and from user settings. For genuinely orientation-locked experiences (games, video editors), pair the manifest declaration with `screen.orientation.lock()` at runtime, with a graceful degradation when the lock is refused.

## Manifest members reference

The table below covers the members in active production use. The official complete reference lives at the MDN *Web app manifest members reference* (`developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference`, last updated 5 May 2025) and the W3C *Web Application Manifest* specification (`w3.org/TR/appmanifest/`).

| Property | Function | Support notes |
|---|---|---|
| `id` | Stable identity of the app. Explicit value recommended; default is `start_url`. | Supported including iOS 16.4+. |
| `name` / `short_name` | Full name and abbreviated name in the launcher. | Universal. |
| `start_url` | URL opened at launch. | Universal. |
| `scope` | "In-app" path prefix. | Universal. Off-scope navigation surfaces the browser UI. |
| `display` | One of `standalone`, `fullscreen`, `minimal-ui`, `browser`. | iOS recognises only `standalone`, `fullscreen`, and `browser`. `standalone` is the precondition for Web Push on iOS. |
| `display_override` | Ordered list that bypasses the `display` fallback chain. Includes `window-controls-overlay`. | Chromium desktop only. |
| `theme_color`, `background_color` | Status-bar colour and splash placeholder colour. | iOS ignores `background_color` for splash purposes (see "Splash screen" below). |
| `orientation` | `portrait`, `landscape`, `any`, and related values. | Android and Chrome support is solid. iOS is limited. |
| `categories` | Hint for stores. Non-binding. | (no platform asymmetry) |
| `screenshots` with `form_factor: "wide"` or `"narrow"` | Trigger the richer install UI on Chromium and enable store-listing generation (PWA Builder). | Chromium. |
| `shortcuts` | Long-press context menu on mobile, right-click on desktop. | Android WebAPK and desktop. |
| `prefer_related_applications` plus `related_applications` | Suggest a native app instead of the PWA. | (no platform asymmetry) |

## Modern members (2024-2025)

### share_target

MDN defines this member as follows: *"The share_target manifest member allows installed Progressive Web Apps (PWAs) to be registered as a share target in the system's share dialog"*. The handler can be configured as `GET` (data arrives in the query string) or `POST` (data arrives in the request body). For file uploads, `POST` is mandatory and `enctype` must be set to `"multipart/form-data"`. The receiving endpoint should parse the form fields named by the `params` mapping. Documentation: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/share_target`.

The `params` object maps logical field names from the share dialog (`title`, `text`, `url`, `files`) to the names used by the receiving form. With the manifest shown above, a POST to `/share-target/` will arrive with form fields named `name`, `description`, `link`, and `sharedFiles`. The server (or a service-worker `fetch` handler intercepting the POST) should read those fields and route the user into the appropriate import flow. On Android the share target shows up in the system share sheet alongside native apps. On Chromium desktop the share target shows up only when the PWA is installed and the host operating system exposes a system share sheet. iOS does not support `share_target`.

A service-worker handler that intercepts the share POST and routes the user to a final destination looks like this:

```js
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.pathname === '/share-target/' && event.request.method === 'POST') {
    event.respondWith((async () => {
      const formData = await event.request.formData();
      const title = formData.get('name');
      const description = formData.get('description');
      const link = formData.get('link');
      const files = formData.getAll('sharedFiles');
      const cache = await caches.open('shared-payload');
      await cache.put('/shared-latest', new Response(JSON.stringify({
        title, description, link, fileCount: files.length,
      })));
      return Response.redirect('/import?from=share', 303);
    })());
  }
});
```

The redirect to a GET URL preserves browser history hygiene. The original POST is consumed by the SW and the page that opens has a normal navigation entry. File payloads, when present, must be staged via the Cache API or IndexedDB; the page that opens cannot read the original POST body directly.

### protocol_handlers

Custom protocol schemes must be prefixed with `web+`. The handler URL must contain a `%s` placeholder where the protocol string will be substituted at navigation time. MDN summarises the purpose as: *"Protocol handlers register the application in an OS's application preferences"*. Standard schemes such as `mailto`, `tel`, and `sms` can also be registered without the `web+` prefix.

With the example manifest, a click on a `web+acme://some/value` link anywhere on the operating system can route to the installed PWA, which receives the navigation at `/open?value=web+acme://some/value`. The PWA is expected to parse the placeholder substitution and dispatch internally. This works on Chromium desktop and Android. The user is prompted the first time a protocol-handled link is opened so the OS can confirm the association.

### file_handlers

MDN definition: *"The file_handlers member specifies an array of objects representing the types of files an installed progressive web app (PWA) can handle [...] used to associate the application with a given set of file types at the operating system level"*. At runtime the opened files are delivered via the Launch Queue API:

```js
if ('launchQueue' in window) {
  window.launchQueue.setConsumer(({ files }) => {
    for (const handle of files) {
      // handle is a FileSystemFileHandle; call handle.getFile() to read.
    }
  });
}
```

The `launch_type` member controls whether multiple files open a single client (`single-client`) or one client per file (`multiple-clients`). Chromium desktop only.

The `accept` mapping pairs MIME types with file extensions. The PWA can choose either side as the source of truth: list the MIME type and let the extension follow, or list both for resilience against operating systems that infer MIME types differently. The optional `icons` array lets the operating system display the PWA's file icon next to the registered file types in the file manager. A note on registration: the file association is created when the user installs the PWA and the manifest is parsed for the first time. Adding a `file_handlers` entry to an already-installed PWA propagates after the next manifest update cycle, which can take up to 24 hours on Chromium.

A receiver page paired with the example manifest looks like this:

```html
<!DOCTYPE html>
<html>
<head><title>Acme: open file</title></head>
<body>
<script>
  if ('launchQueue' in window) {
    launchQueue.setConsumer(async ({ files }) => {
      for (const handle of files) {
        const file = await handle.getFile();
        const text = await file.text();
        // Hand the file off to the editor.
      }
    });
  }
</script>
</body>
</html>
```

If the user opens multiple files at once and the manifest declares `launch_type: "single-client"`, the consumer callback fires once with an array of all the file handles. With `launch_type: "multiple-clients"`, the browser opens one PWA window per file and each consumer receives a single-element array. The single-client mode is correct for batch editors (a tab-bar editor that opens multiple documents in one window). The multiple-clients mode is correct for monolithic editors (one document per window, like a word processor).

### launch_handler

MDN definition: *"The launch_handler member defines values that control the launch of a web application. Currently it can only contain a single value, client_mode"*. The accepted values for `client_mode` are `auto`, `navigate-new`, `navigate-existing`, and `focus-existing`. When an array is supplied, the values are interpreted as a fallback order, with the first supported value taking effect. The `focus-existing` mode is the right choice for document-style apps where reusing an open window is more useful than opening a fresh tab.

The difference between `navigate-existing` and `focus-existing` is subtle but important. With `navigate-existing` the existing window is navigated to the launch URL, replacing whatever the user had on screen. With `focus-existing` the existing window is brought to the foreground at whatever URL it was already showing, and the launch URL is delivered to the page via the Launch Queue (`window.launchQueue.setConsumer`). For apps that maintain editable state (a draft, a partially filled form), `focus-existing` is mandatory: `navigate-existing` would silently discard the in-progress work.

### handle_links

Accepts `auto`, `preferred`, or `not-preferred`. Expresses the PWA's preference for capturing in-scope links opened from outside the app. This member is part of the WICG work that replaced the older `url_handlers` proposal. Browser behaviour is heuristic: even with `preferred`, the system decides whether to route the link to the installed PWA or to the browser.

The three values map to three reasonable user-experience outcomes. `preferred` is the right setting for app-style PWAs where the user almost always wants their installed app to handle their own links. `not-preferred` is appropriate for content-style PWAs (a magazine, a blog) where browser-tab handling is the better default and the PWA window is reserved for explicit launches. `auto` lets the browser pick, which today tends to favour the browser-tab behaviour unless the user has expressed a preference via the operating system's default-app settings.

### scope_extensions

Extends the effective scope of the app across multiple origins. Each origin listed in the manifest must publish a `/.well-known/web-app-origin-association` document whose top-level key matches the manifest `id`. The intended use is multi-domain products where the marketing site, help centre, and app share a single PWA identity. Track the stability of this member at `chrome://flags` and at chromestatus.com before relying on it in production. Some Chrome versions ship it behind an origin trial.

A minimal `web-app-origin-association` document on `https://help.acme.com` paired with the example manifest looks like this:

```json
{
  "https://acme.com/?source=pwa": {
    "scope": "/"
  }
}
```

The top-level key is the manifest `id` of the requesting PWA. The `scope` field constrains how much of the secondary origin the PWA can swallow. Without the well-known document, Chromium ignores the entry silently; there is no visible error in DevTools and the install proceeds as if `scope_extensions` were not declared. Wildcard origins of the form `https://*.acme.co.uk` match any subdomain, but each matched subdomain still has to serve its own association document.

### display_override

`display_override` is the modern replacement for relying solely on `display`. It is an ordered array of display modes the browser tries in sequence until one is supported. The richest mode in the array, `window-controls-overlay`, is only honoured on Chromium desktop and lets the PWA render its own custom title bar where the operating-system window controls (close, minimise, maximise) are still drawn by the browser, but the rest of the title-bar area is given to the app. The CSS environment variables `env(titlebar-area-x)`, `env(titlebar-area-y)`, `env(titlebar-area-width)`, and `env(titlebar-area-height)` describe the available region.

A typical chain is `["window-controls-overlay", "standalone", "minimal-ui", "browser"]`. On Chromium desktop the app gets the overlay mode. On Android the overlay value is unsupported, so the browser falls through to `standalone`. On iOS the fall-through continues through `minimal-ui` (also unsupported on iOS) and lands on `browser` only as a safety net; in practice iOS interprets the fallback from `display: "standalone"` directly.

`display_override` also accepts a `"tabbed"` value, which is experimental at the time of writing. It lets a PWA host multiple "tabs" inside a single standalone window, with the tab strip drawn by the browser. The feature is behind a flag in Chrome (`chrome://flags/#enable-desktop-pwas-tab-strip`) and is not yet a production-ready signal.

### edge_side_panel.preferred_width

Sets the preferred width in CSS pixels when the PWA runs inside the Microsoft Edge side panel. Microsoft Learn explains the default: *"If your app's layout can't support the 376 pixels minimum width, you can define your preferred width by using the preferred_width property in your web app manifest"*. Below 376 pixels Edge does not render the app in the side panel.

The side panel is a long, narrow column docked to the side of the Edge window. Apps that fit there are typically utilities (a calculator, a clipboard manager, a chat client). The `preferred_width` value is a hint, not a hard constraint. Edge will respect it when sufficient screen real estate is available and will collapse to a smaller width when not. PWAs targeting the side panel should adopt a narrow-first layout with container queries so the same UI degrades gracefully across the panel width range.

## Icons

A few rules are non-negotiable for installability across platforms. For Chromium, the two minimum icons are a 192x192 PNG and a 512x512 PNG. Both should be declared with `purpose: "any"`. Below that bar the install prompt will not appear.

Maskable icons follow a separate rule. The safe zone is the inner 80% of the icon diameter, equivalent to a circular region of 40% radius centred on the icon. The web.dev guidance is explicit: *"The important parts of your icon, such as your logo, must be within a circular area in the center of the icon with a radius equal to 40% of the icon width. The outer 10% edge might be cropped on some platforms"* (`web.dev/articles/maskable-icon`). Anything outside that zone may be cropped by the platform mask. The best practice is to publish two distinct assets: one with `purpose: "any"` for use in unmasked contexts (legacy icon trays, store listings) and one with `purpose: "maskable"` for adaptive launchers. web.dev explicitly discourages combining both purposes on a single image with `purpose: "any maskable"`, because the centred maskable composition looks badly framed in any context.

SVG icons declared with `sizes: "any"` work on Chromium and Firefox but not on iOS Safari for the home screen. If a single vector icon is desired, ship it as an additional entry alongside the PNG raster pair so that platforms without SVG support fall back to PNG.

iOS handles icons through a separate channel. The home-screen icon is sourced from `<link rel="apple-touch-icon" href="/apple-touch-icon.png">`, expected to be an opaque 180x180 PNG (no transparency, no mask; Apple adds the rounded corners automatically). Starting with iOS 16.4 Safari can also read the `icons` array from the manifest, but when both sources are present `apple-touch-icon` takes precedence (per the WebKit blog post on Web Push for Web Apps on iOS).

A practical authoring workflow that satisfies every platform:

1. Author the source icon as a 1024x1024 PNG with a square colour fill behind the logo. The fill must extend to the edge so that masking does not reveal background.
2. Generate the 192x192 and 512x512 `purpose: "any"` PNGs by downscaling.
3. Generate the 192x192 and 512x512 `purpose: "maskable"` PNGs by adding internal padding so the logo sits inside the 40% safe radius.
4. Generate the 180x180 opaque PNG for `apple-touch-icon`.
5. Optionally add an SVG declared with `sizes: "any"` for vector-aware platforms.

The `pwa-asset-generator` tool can perform steps 2-5 automatically from a single source PNG or SVG, including the iOS startup images discussed below.

## Splash screen

On Android and Chromium the splash screen is generated automatically from `name`, `background_color`, `theme_color`, and the 512x512 icon. No per-device assets are required.

On iOS the manifest is not consulted for the splash screen. Each device width, height, pixel-density ratio, and orientation needs its own `<link rel="apple-touch-startup-image">` entry, matched via the `media` attribute. A representative entry looks like this:

```html
<link rel="apple-touch-startup-image"
      media="(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3)"
      href="/splash/iphone-14-pro.png">
```

The canonical tool for generating the full asset set and the matching `<link>` tags is `pwa-asset-generator` (`github.com/onderceylan/pwa-asset-generator`). Progressier is a hosted alternative for teams that prefer not to run a generator script in CI. A known iOS bug: in landscape orientation Safari frequently ignores the landscape startup image and stretches the portrait one. The pragmatic workaround is to ship the portrait asset with a centred composition so the stretching is less jarring.

A complete iOS startup-image set covers the active iPhone and iPad device matrix at 2x and 3x device pixel ratios, in both portrait and landscape. That can run to 40+ entries. Most teams use a generator rather than hand-authoring the list. The matching `media` queries are precise: they reference both `device-width` and `device-height` (not just the viewport), and pixel-density ratios via `-webkit-device-pixel-ratio`. A single missing combination causes Safari to show a blank white screen during the launch animation on the affected device.

The Android and Chromium splash screen has no equivalent issue because the browser composites the screen at runtime from the manifest values. As long as `name`, `background_color`, and the 512x512 icon are present, the splash works.

## iOS meta tag block

The block below is what every PWA targeting iOS should put in the document head. The five lines work together: the first three drive standalone-mode behaviour, the fourth provides the home-screen icon, and the last two configure the visual chrome.

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Acme">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<meta name="theme-color" content="#0f172a">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

A practical note on `apple-mobile-web-app-capable`. This meta tag remains the de facto trigger for the PWA to open in standalone mode on iOS, which is the precondition for receiving Web Push. From iOS 16.4 onward, `display: "standalone"` in the manifest is equivalent in principle. In practice the meta tag is still recommended for compatibility, because older iOS releases that some users have not updated rely on it exclusively, and because the cost of including it is zero.

The `apple-mobile-web-app-status-bar-style` value controls the appearance of the iOS status bar when the PWA is launched from the home screen. The accepted values are `default`, `black`, and `black-translucent`. The `black-translucent` value lets the content draw under the status bar, which is what most modern designs expect when paired with `viewport-fit=cover` and `env(safe-area-inset-*)` in CSS.

The `apple-mobile-web-app-title` value is the short label that appears under the home-screen icon. It should match `short_name` in the manifest. If it is omitted, iOS falls back to the document `<title>`, which is usually too long for the home-screen slot and gets truncated.

The `viewport-fit=cover` parameter on the viewport meta tag is what enables the safe-area inset environment variables in CSS. Without it, the safe-area insets resolve to zero and any layout that depends on `env(safe-area-inset-top)` or `env(safe-area-inset-bottom)` will render incorrectly on notched devices.

## Validating the manifest

Three places to validate a manifest before shipping:

1. **Chrome DevTools, Application panel, Manifest section.** Shows the parsed manifest, the resolved icon set with previews, the computed identity, and any installability warnings. The "Preview install dialog" affordance renders the install prompt with the manifest's data so you can review the user-visible result without triggering an install.
2. **PWA Builder validator at `pwabuilder.com`.** Cross-platform scoring with concrete remediation suggestions. Includes checks for properties relevant to Microsoft Store packaging that DevTools does not surface.
3. **Lighthouse PWA-focused audits (manifest, installability, splash).** The umbrella PWA category was removed in Lighthouse 12.0.0 (Chrome 126, May 2024), but the individual checks remain available under the DevTools Application panel and via the Lighthouse CLI with the `--only-audits` flag.

For CI integration, the Lighthouse CLI is the most reliable option. A minimal pipeline runs `lighthouse --only-audits=installable-manifest,maskable-icon,apple-touch-icon` against a deployment preview URL and fails the build on regressions. The PWA Builder service also exposes a JSON API at `pwabuilder.com/reportcard` that can be polled from a script.

## Cross-platform support matrix at a glance

| Member | Chromium desktop | Android (Chrome WebAPK) | iOS Safari | Firefox |
|---|---|---|---|---|
| `id`, `name`, `short_name`, `start_url`, `scope` | Yes | Yes | Yes (16.4+) | Yes |
| `display: "standalone"` | Yes | Yes | Yes | Yes |
| `display_override: ["window-controls-overlay", ...]` | Yes | Falls through | Falls through | Falls through |
| `theme_color`, `background_color` | Yes | Yes | `theme_color` only | Yes |
| Icons `192/512` PNG `purpose: "any"` | Yes | Yes | Yes (16.4+, but apple-touch-icon wins) | Yes |
| Icons `purpose: "maskable"` | Yes | Yes | Ignored | Yes |
| `screenshots` rich install UI | Yes | Yes | Not applicable | No |
| `shortcuts` | Yes | Yes | No | No |
| `share_target` | Partial (where OS share sheet exists) | Yes | No | No |
| `protocol_handlers` | Yes | Yes | No | No |
| `file_handlers` | Yes | No | No | No |
| `launch_handler` | Yes | Yes | No | No |
| `handle_links` | Yes | Yes | No | No |
| `scope_extensions` | Yes (some versions origin-trial) | Yes | No | No |
| `edge_side_panel` | Edge only | No | No | No |

## Common authoring mistakes

A short list of mistakes that recur in code review of new PWA manifests:

1. **Omitting `id`.** Without an explicit `id`, the browser derives one from `start_url`. Any later change to `start_url` will be interpreted as a new app and trigger a reinstall, breaking the user's existing install.
2. **Setting `purpose: "any maskable"` on the same icon.** Combining purposes on one image produces a layout that is poorly framed in every context (centred for masking but cropped in legacy trays). Ship separate assets.
3. **Missing 512x512 PNG.** Chromium requires both 192 and 512 PNG sizes for installability. A single icon entry is not enough.
4. **Forgetting the `apple-touch-icon`.** iOS does not synthesise a fallback. Without an `apple-touch-icon` the home screen icon is the favicon at low resolution, which looks unprofessional.
5. **Missing `viewport-fit=cover`.** Modern iPhones have a notch and a home indicator that intrude into the viewport. Without `viewport-fit=cover`, content rendered with default insets will be clipped or overlapped.
6. **Hosting the manifest off-origin.** The manifest must be same-origin as the page that references it. Cross-origin hosting requires `crossorigin="use-credentials"` and a permissive CORS response, which is rarely worth the friction.
7. **Wrong `Content-Type`.** Serving the manifest as `text/html` or `text/plain` causes Chromium to reject it silently. Verify with `curl -I` that the response carries `application/manifest+json` (preferred) or `application/json`.
8. **Skipping `screenshots`.** Installability still works without them, but the install prompt is the minimal compact variant. Authors usually want the rich variant once they see both side by side.
9. **Wildcard origins in `scope_extensions` without the well-known document on each matched subdomain.** Each subdomain that is matched by the wildcard still has to serve its own `web-app-origin-association`.
10. **Hard-coding the manifest in HTML rather than serving as JSON.** Some frameworks let you inline the manifest as a data URL. This works in narrow circumstances but breaks the `crossorigin` handling and disables cache validation. Always serve the manifest as a separate, properly typed HTTP resource.

## Identity, scope, and start URL together

These three members work as a unit and confuse first-time authors. `id` is the immutable identity that the browser uses to match the manifest to an existing install. `start_url` is the URL the browser navigates to when the user opens the installed app. `scope` is the URL prefix that the browser treats as "inside" the app for navigation purposes (clicks on links inside the scope stay in the standalone window; clicks on links outside the scope open the browser).

A common pattern:

- `id`: `/?source=pwa` (immutable, decoupled from any future URL changes)
- `start_url`: `/?source=pwa` (the same URL as `id` initially; can diverge later)
- `scope`: `/` (the entire origin)

A more specialised pattern for an app deployed under a sub-path:

- `id`: `/app/?source=pwa`
- `start_url`: `/app/?source=pwa`
- `scope`: `/app/`

The scope here is `/app/` so that the marketing pages at `/` continue to open in the browser tab rather than in the standalone window.

## Decision quick-reference

| Question | Answer |
|---|---|
| Should I set `id` explicitly? | Yes. Always. Even if it duplicates `start_url`. |
| Two icon assets or one with `purpose: "any maskable"`? | Two. web.dev discourages the combined purpose. |
| Need a wide and narrow screenshot? | Yes. Both `form_factor: "wide"` and `form_factor: "narrow"`. |
| Cache-Control on the manifest itself? | `no-cache, must-revalidate`. Never a long max-age. |
| `display_override` first entry? | `window-controls-overlay` for Chromium desktop coverage. |
| iOS startup image set? | Generate with `pwa-asset-generator`, do not hand-author. |
| Custom protocol scheme prefix? | `web+` for non-standard schemes. Standard schemes (mailto, tel, sms) need no prefix. |
| `file_handlers` `launch_type`? | `single-client` for document apps that batch files. `multiple-clients` for one-file-per-window editors. |
| `launch_handler` `client_mode`? | `focus-existing` for apps with editable state. `navigate-existing` only when discarding state is acceptable. |
| `handle_links`? | `preferred` for app-style PWAs. `not-preferred` for content-style PWAs. |

## Reference: MDN and W3C

The authoritative sources for every member documented above are the MDN reference page and the W3C specification:

- MDN, *Web app manifest members reference*: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference` (last updated 5 May 2025).
- W3C, *Web Application Manifest*: `w3.org/TR/appmanifest/`.

Per-member MDN pages worth bookmarking:

- `share_target`: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/share_target`
- `protocol_handlers`: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/protocol_handlers`
- `file_handlers`: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/file_handlers`
- `launch_handler`: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/launch_handler`
- `handle_links`: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/handle_links`
- `scope_extensions`: `developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/scope_extensions`

Companion specifications and articles:

- web.dev, *Maskable icons*: `web.dev/articles/maskable-icon`.
- WebKit blog, *Web Push for Web Apps on iOS and iPadOS*: covers `apple-touch-icon` precedence and the iOS 16.4 install-required rule for Web Push.
- Microsoft Learn, *Edge side panel for PWAs*: documents `edge_side_panel.preferred_width` and the 376-pixel minimum.
- `github.com/onderceylan/pwa-asset-generator`: generator for the iOS startup image set, the maskable icons, and the `<link>` tags.

For cross-platform installability scoring, the PWA Builder validator at `pwabuilder.com` reads the manifest and reports the missing or weak members. The Application panel in Chrome and Edge DevTools provides a live preview that renders the manifest the same way the install prompt will.

## Final notes

The Web App Manifest is the leanest of the PWA building blocks: a single JSON file with no runtime, no asynchronous behaviour, no transport layer. The trade-off is that every member subtly affects platform behaviour and the asymmetry between Chromium and iOS is largest here. A manifest that ships clean on Chrome desktop may produce a malformed home-screen icon on iPhone, an unbranded splash screen, and no Web Push at all, all silently. The recommended habit is to validate the manifest on three surfaces during every release: Chrome DevTools Application panel, Safari on a real iPhone, and the PWA Builder report card.

The other building blocks of the PWA (Service Worker, push subscription pipeline, install flow, storage, performance) all assume a correctly authored manifest. A misconfigured `id`, a missing `apple-touch-icon`, or a wrong `Content-Type` on the manifest response cascades into install failures, push opt-in failures, and orphaned subscriptions. Treat the manifest as the foundation: it earns the careful authoring time.
