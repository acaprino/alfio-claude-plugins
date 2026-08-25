# Platform Constraints

PWA capabilities are not portable. The same manifest plus service worker plus push pipeline behaves very differently on iOS, Android, and the three desktop browsers. This reference is the per-platform reality check: what each platform supports, what it omits, what it added recently, and what is legally or politically contested.

Read this before promising a feature to a stakeholder. Read this before scoping a PWA project. Use it as the authoritative ceiling on what is actually shippable.

The structure mirrors source guide §10. Three sections:
1. iOS / iPadOS (WebKit mandatory).
2. Android (Chrome).
3. Desktop (Chrome / Edge, Firefox, Safari macOS).

---

## iOS / iPadOS (WebKit mandatory)

iOS is the most constrained PWA platform. Every browser on iOS is forced to use WebKit under the hood. The PWA feature set is therefore the WebKit feature set, regardless of which app the user opens. The bullets below are the ceiling, not a wishlist.

### Web Push

Web Push works on iOS only from version 16.4 (March 2023). Two conditions both apply:

1. The site must be installed from Safari to the Home Screen.
2. The web app must open in `display: standalone` (the manifest member, or the legacy `apple-mobile-web-app-capable` meta tag).

If either condition is unmet, `Notification.requestPermission()` returns `denied` without prompting. There is no way to send Web Push to a non-installed iOS PWA.

The subscription must be created in response to a user gesture (a tap on a button). This is hard-enforced by WebKit and is not configurable. Subscriptions can also be silently dropped after periods of inactivity. The recommended pattern is to call `pushManager.getSubscription()` on every startup and re-subscribe if the result is `null`.

Common failure modes to test for explicitly on iOS:

- `Notification.requestPermission()` called on page load returns `denied`. Wrap it in a click handler.
- A PWA installed on iOS 16.3 or earlier does not gain push capability when the user upgrades to 16.4. The user must remove the icon from the Home Screen and re-add it.
- Switching between cellular and Wi-Fi can desynchronize the subscription. Reconcile on `visibilitychange` and on `online`.
- A push payload larger than 4 KB is silently dropped by APNs. Keep payloads small.

See `push-notifications.md` for full code patterns and iOS-specific gotchas.

### Safari 18.4 (March 31, 2025)

Safari 18.4 added two long-awaited features for Home Screen Web Apps:

1. **Declarative Web Push.** The server can send a JSON payload conforming to the notification schema and Safari renders it without waking a service worker. Reduces battery and CPU, and closes one of the prior misuse vectors that motivated Apple's caution.
2. **Screen Wake Lock API** for Home Screen Web Apps. Before 18.4, the Wake Lock API was broken on installed iOS PWAs (the request resolved but the screen still timed out). WebKit release notes filed the fix as bug 108573133.

See `push-notifications.md` for Declarative Web Push details. See `background-execution.md` for Wake Lock examples.

### iOS 26: standalone by default

In iOS 26, every site added to the Home Screen opens as a web app by default. This is an implicit opt-in to `display: standalone`. The user no longer has to follow a multi-step installation flow before push and other standalone-only capabilities become available. Existing manifest members continue to work and override the default where the developer specifies otherwise.

The practical implication: assume more iOS users will land on the standalone path in 2026 than in any prior year. Test the standalone flow on real hardware, not just simulator.

### Background APIs not available

Three Chromium-only background APIs are not implemented on iOS at any version:

- **Background Sync** (one-shot retry of failed requests when connectivity returns).
- **Periodic Background Sync** (recurring background work, engagement-gated on Chromium).
- **Background Fetch** (long downloads that survive page close).

Plan a degraded path for these on iOS. Common patterns:

- For Background Sync: queue mutations in IndexedDB and retry from the foreground on app launch or visibility change.
- For Periodic Background Sync: rely on the user opening the app, or use a server-driven push to wake the client.
- For Background Fetch: stream the download in the foreground, persist progress in IndexedDB, and resume on next launch.

Service workers on iOS are also killed aggressively when the app is backgrounded. Do not assume a service worker stays alive long enough to complete out-of-band work after the user navigates away.

### Hardware APIs not available

iOS does not implement the hardware-access Project Fugu APIs:

- Web Bluetooth.
- WebUSB.
- WebHID.
- Web Serial.
- WebNFC.

These have been requested for years and are not on the Safari roadmap. Apps that depend on direct device access must ship as native or as a Capacitor wrapper. See `distribution.md` for the Capacitor path.

### Service worker lifetime

WebKit imposes a tight lifetime budget on service workers compared to Chromium. A service worker on iOS:

- Is terminated after roughly 30 seconds of idle time.
- Is terminated immediately when the user navigates away from the controlled scope in a browser tab.
- For installed PWAs, is terminated when the app is sent to the background (Home button, app switcher).
- Is restarted on push delivery, `notificationclick`, or fetch under the controlled scope.

Long-running operations inside a service worker must therefore be designed as resumable: state goes into IndexedDB before any `await`, and is restored on the next event. Patterns that rely on closures or module-level state across multiple events will fail intermittently on iOS even when they work on Chromium.

### Storage

iOS storage for PWAs has improved but still carries caveats:

- The installed PWA has a storage container isolated from system Safari (separate process container). Cookies, IndexedDB, and Cache API data do not leak between the standalone PWA and the browser tab.
- The nominal quota is 60% of disk per origin, matching the Chromium target from 2024 onwards.
- `navigator.storage.persist()` requires the notification permission to be effective on Safari. Without notifications granted, the call returns `true` but eviction protection is not actually enforced.
- Cache eviction bugs have been reported repeatedly. WebKit bugs 190269 and 199110 have periodically eroded the guarantee that installed-PWA data is safe across system pressure events.
- For non-installed PWAs running in a Safari tab, ITP (Intelligent Tracking Prevention) applies the 7-day cap on script-writeable storage. Installed PWAs avoid this cap most of the time but it is not a hard guarantee.

See `storage-persistence.md` for the per-browser quota and persistence matrix.

### Install path

There is no `beforeinstallprompt` on iOS. Installation is manual and undiscoverable:

1. User taps the Share button in Safari.
2. User scrolls down in the share sheet.
3. User taps "Add to Home Screen".
4. User confirms the name and taps "Add".

The recommended pattern is a CSS-gated install hint that appears only when the app is opened in a regular Safari tab (not a standalone PWA), pointing the user at the Share button with a short instruction. See `install-flows.md` for the implementation.

Chrome and Firefox on iOS cannot install PWAs at all. They use WKWebView (because of App Store guideline 2.5.6) and do not surface "Add to Home Screen" in their share sheets. Detect Chrome / Firefox on iOS and either suppress the install hint or instruct the user to switch to Safari first.

Once installed, a Home Screen PWA on iOS reads its identity from a snapshot of the manifest captured at install time. Later changes to `name`, icons, or `start_url` do not propagate to existing installs. The user must remove and re-add the icon for the new metadata to take effect. This is the opposite of the WebAPK refresh model on Android.

### App Store guideline 2.5.6

App Store guideline 2.5.6 requires every browser on iOS to use WebKit as its rendering engine. This is the source of every WebKit-mandated limitation listed above. Chrome on iOS, Firefox on iOS, Edge on iOS, DuckDuckGo Browser, Brave: all WebKit. There is no API surface diversity.

iOS 18.2 in theory introduced BrowserEngineKit for non-WebKit browsers in the EU under DMA pressure. As of early 2026 no browser has shipped a production build using it. The DMA compliance posture is contested and continues to evolve.

A consequence of the WebKit floor: feature detection must happen at runtime, not at build time. A user-agent string check that says "Chrome" tells you nothing about engine capabilities on iOS. Use `if ('serviceWorker' in navigator)` plus `if ('PushManager' in window)` style checks. If you need to differentiate WKWebView from system Safari on iOS, check for `navigator.standalone === true` (Safari-only Home Screen indicator) or the `display-mode` media query.

### DMA EU (January-March 2024)

A short timeline of the DMA episode that nearly removed PWAs from iOS in the EU:

1. **January 2024.** Apple shipped iOS 17.4 beta in the EU and removed the ability to add Home Screen Web Apps, in apparent response to DMA browser-engine-choice obligations.
2. **February 2024.** Open Web Advocacy, the European Commission, and a wide developer coalition pushed back publicly. The European Commission opened an inquiry into the removal.
3. **March 1, 2024.** Apple reversed course before iOS 17.4 final shipped. TechCrunch reported the reversal and quoted Apple:

   > "We have received requests to continue to offer support for Home Screen web apps in iOS, therefore we will continue to offer the existing Home Screen web apps capability in the EU."

Home Screen Web Apps remain available in the EU as of 2026 under the original WebKit-only constraint. The episode confirmed that the PWA path on iOS is politically fragile but currently safe to depend on.

---

## Android (Chrome)

Android with Chrome is the most fully-featured PWA platform. The bullets below describe the maximum-capability baseline.

### WebAPK

When a user installs a PWA on Android, Play Services generates a **WebAPK** on demand. The WebAPK is a real Android package signed by Google. It contains a minimal Android wrapper that boots Chrome to the PWA's `start_url` in standalone mode.

Consequences of the WebAPK model:

- The PWA appears in the launcher as a native app. The icon is the manifest's 512 PNG. There is no Chrome chrome-bar branding.
- The PWA has its own entry in **Settings → Apps**. Users can grant or revoke permissions, clear data, force-stop, and uninstall through the standard Android app management UI.
- Permissions are managed by the Android system, not by Chrome's site settings. A push permission grant on the WebAPK is a real Android notification permission.
- The PWA can receive intents (via `intent://` URLs) and acts as a share target through the Android share sheet.
- A splash screen is generated automatically from the manifest's `name`, `background_color`, and 512 PNG icon.

The WebAPK is updated periodically when the manifest changes. There is a propagation lag of a few hours to a day before changes to icons, name, or start_url take effect on existing installs.

### TWA (Trusted Web Activity)

For distribution through the Google Play Store, the PWA can be wrapped in a **Trusted Web Activity**. TWA is a Chrome Custom Tab in a mode that hides the URL bar and verifies the relationship between the Android package and the web origin through Digital Asset Links.

The standard toolchain is **Bubblewrap**. The TWA-built APK or AAB is uploaded to the Play Store under the developer's Google Play account.

Critical setup step: serve `/.well-known/assetlinks.json` on the web origin with the package name and signing certificate fingerprint. Without valid Digital Asset Links the TWA degrades to a Custom Tab with a visible URL bar (and Chrome branding), which is almost always a worse experience than the PWA itself.

If the user has both a WebAPK install of the PWA and a Play Store install of the TWA wrapping the same origin, the Play Store install takes precedence in the launcher. Use `getInstalledRelatedApps()` in the web app to detect the native counterpart and suppress duplicate install prompts. See `install-flows.md`.

See `distribution.md` for the full Bubblewrap workflow.

### All capabilities available

Android Chrome supports the full PWA capability set:

- Background Sync.
- Periodic Background Sync (engagement-gated; the user must open the PWA a few times before Chrome decides it has earned background quota).
- Background Fetch.
- Web Push (FCM transport).
- Web Bluetooth, WebUSB, WebHID, Web Serial, WebNFC.
- File System Access (via the polyfill on mobile; native on desktop).
- Web Share + Web Share Target.

Background Sync fires when connectivity returns, respecting Android Doze mode. Periodic Background Sync is scheduled on the Android maintenance window, so it does not fire in Doze.

### Other Android browsers

The above describes Chrome on Android. Other browsers vary:

- **Edge** on Android uses Chromium and inherits the WebAPK install path through Chrome's Play Services hook. Coverage is essentially identical to Chrome.
- **Samsung Internet** supports WebAPK installation through Samsung's own implementation. Coverage is close to Chrome but some Project Fugu APIs lag.
- **Firefox** on Android supports "Add to Home Screen" as a lightweight shortcut, not a WebAPK. The result is a launcher icon that opens Firefox to the URL. There is no standalone container, no separate app entry, and no system-level permission management.

If a PWA must work uniformly across Android browsers, target the WebAPK common subset (Chrome, Edge, Samsung Internet) and treat Firefox on Android as a degraded shortcut path.

### Android Doze and standby buckets

Android applies battery-saving constraints to all apps in the background, including WebAPKs. The two main mechanisms:

- **Doze mode.** When the device is unplugged, stationary, and the screen is off for a sustained period, the system batches background work into maintenance windows. Background Sync events delivered during Doze fire on the next maintenance window, not immediately.
- **App standby buckets.** Each app is assigned a usage bucket (active, working set, frequent, rare, restricted). Apps in lower buckets receive fewer background jobs and less network access. A PWA that the user opens infrequently will land in a low bucket and lose effective access to Periodic Background Sync.

Periodic Background Sync uses the Android JobScheduler, which respects both Doze and standby buckets. The minimum effective interval is rarely below 12 hours on a device with normal usage patterns. Do not promise sub-hourly periodic work on Android.

---

## Desktop

Desktop coverage splits sharply by browser. Chrome and Edge are the superset. Safari macOS shipped a meaningful "Add to Dock" path in 2023. Firefox has been a moving target.

### Chrome and Edge

Chrome and Edge on desktop are the most capable PWA platforms by surface area. They are a superset of Android Chrome:

- **Window Controls Overlay.** The PWA can paint into the title bar area. Enabled by `"display_override": ["window-controls-overlay"]` plus the `env(titlebar-area-*)` CSS variables and `-webkit-app-region` for drag regions. See `install-flows.md` for the full integration.
- **File Handlers.** The PWA registers as a default app for specified MIME types or extensions. Files opened from the OS file manager arrive via `window.launchQueue.setConsumer`.
- **Protocol Handlers.** The PWA registers as a handler for `web+foo://` custom protocols (or whitelisted standard protocols like `mailto`).
- **URL Handlers via `scope_extensions` and `handle_links`.** The PWA can claim ownership of URLs outside its origin (with the cross-origin association file) and influence whether navigations open in-app or in the browser.
- **Tabbed Application Mode.** Experimental, hidden behind `chrome://flags/#enable-desktop-pwas-tab-strip`. Allows the PWA to display a Chrome-style tab strip inside its standalone window. Not production-ready as of early 2026.
- **Edge side panel.** Edge-specific. `edge_side_panel.preferred_width` in the manifest sets the default width when the PWA is opened in the Edge sidebar.

Installed PWA windows on Chrome and Edge survive after the main browser window is closed. The service worker can continue to run for push and sync events even when no PWA window is open.

Operating system integration on Chrome and Edge desktop:

- **Windows.** The PWA appears in Start Menu, Taskbar, and Settings → Apps. It can be pinned to the taskbar. Edge also offers "Apps" management at `edge://apps`.
- **macOS.** The PWA appears in `~/Applications` as a `.app` bundle generated by Chrome. It is visible in Spotlight and Launchpad. Uninstall is handled inside Chrome at `chrome://apps`, not by dragging the bundle to Trash.
- **Linux.** The PWA generates a `.desktop` file under `~/.local/share/applications/`. Standard desktop launchers pick it up automatically.

Update propagation on Chrome and Edge: the manifest is re-fetched on every navigation and at least every 24 hours. Changes to `name`, icons, and `theme_color` propagate within a day for active installs. The service worker file `/sw.js` is also checked on every navigation, subject to the `Cache-Control` of the SW response. See `service-workers.md` for the recommended `Cache-Control: no-cache` setup.

### Firefox

Firefox dropped desktop PWA support on January 27, 2021. The 9to5Google report headlined the change:

> Firefox discontinues work toward Progressive Web Apps on desktop

The Mozilla team statement quoted in the same article:

> "The signal I hope we are sending is that PWA support is not coming to desktop Firefox anytime soon."

The effective removal occurred earlier than the announcement: the SSB (Site Specific Browser) prototype was removed in **Firefox 84 (December 2020)**. From that release through Firefox 142, desktop PWA installation was not available in shipped builds.

**Firefox 143 (September 2025)** reintroduced limited PWA support on Windows. The new implementation is more conservative than the SSB prototype. It supports installation, standalone display, and a subset of the manifest members, but not Window Controls Overlay, File Handlers, or Protocol Handlers. macOS and Linux remain without PWA install support in Firefox as of early 2026.

On Android, Firefox supports "Add to Home Screen" as a lightweight shortcut. No WebAPK, no standalone container, no system-level app entry. See the Android section above.

The practical rule: do not depend on Firefox for desktop PWA features. Test gracefully degrading to a regular browser tab.

Service workers, Web Push, IndexedDB, Cache API, and Notifications all work in Firefox without requiring an install path. A site can therefore deliver a full offline-capable, push-enabled web experience to Firefox users without involving the install mechanism. The features that are missing on Firefox are the platform-integration features (standalone window, OS-level app entry, splash screen, Window Controls Overlay) rather than the core PWA capability set.

### Safari macOS

Safari on macOS added meaningful PWA support in **Sonoma (macOS 14, 2023)** with "Add to Dock". The feature creates a real web app in `~/Applications`:

- The web app has its own container. Cookies, IndexedDB, and Cache API data are isolated from system Safari.
- The web app appears in `~/Applications` as a `.app` bundle. It can be launched from the Dock, Spotlight, and Launchpad. It can be removed by dragging to Trash like any native app.
- **Push notifications** work for installed web apps on macOS 13+ (Ventura introduced the cross-app notification UI, Sonoma exposed it to web apps).
- **Dock badge** via `navigator.setAppBadge(n)` is supported.

What is not supported on Safari macOS:

- **Window Controls Overlay.** The web app uses a standard window frame with no API access to the title bar area.
- **File Handlers.** The web app does not register as a default opener for file types in Finder.
- **Protocol Handlers.** The web app does not register `web+foo://` handlers.
- **Background Sync, Periodic Background Sync, Background Fetch.** Same constraint as iOS Safari.
- **Web Bluetooth, WebUSB, WebHID, Web Serial, WebNFC.** Same constraint as iOS Safari.

Safari macOS is a meaningful improvement over the pre-Sonoma state (where macOS users had no PWA path at all) but it is still well below the Chrome and Edge superset.

Practical Safari macOS gotchas:

- The "Add to Dock" command lives in the **File** menu, not the share sheet. Users frequently miss it. An in-app hint is recommended.
- Removing the icon from the Dock does **not** uninstall the web app. The user must drag the `.app` bundle from `~/Applications` to Trash, or use the Safari Settings panel.
- Push notifications require the web app to be launched from the Dock at least once before the permission prompt can be triggered. The user must also have macOS notifications enabled for the web app in System Settings.
- The Safari macOS web app uses the same WebKit engine as iOS Safari, so the Background API constraints carry over. Do not assume that a "desktop" web app on macOS has the Chrome desktop capability set.

---

## Per-platform troubleshooting matrix

A few classes of bugs reproduce only on one platform. Knowing the platform helps narrow the search.

### Symptom: notifications never arrive

| Platform | Most likely causes |
|---|---|
| iOS Safari (installed PWA) | PWA opened in browser tab, not standalone. Manifest missing `display: standalone`. Subscription was created before install. iOS notifications disabled at the system level. APNs payload over 4 KB. |
| iOS Safari (browser tab) | Push is not supported in browser tabs. Confirm the PWA is on the Home Screen. |
| Android Chrome | FCM registration token expired. WebAPK uninstalled and reinstalled (new token). Android notifications disabled at the system level for the WebAPK. Doze mode delaying delivery to next maintenance window. |
| Chrome / Edge desktop | OS-level Focus Assist or Do Not Disturb suppressing notifications. The PWA is not running and the SW has not been registered for push at the OS layer. |
| Safari macOS (installed) | PWA never launched from the Dock. macOS notifications disabled for the web app in System Settings. |

### Symptom: install hint never appears

| Platform | Most likely causes |
|---|---|
| Chromium desktop | Manifest invalid (missing `name`, `short_name`, `start_url`, or 192 + 512 PNG icons). SW not registered, or registered without a `fetch` handler. Engagement threshold not yet reached (user has not interacted plus 30 seconds on page). Previous `beforeinstallprompt` event already consumed. |
| Chromium Android | Same as desktop plus the Play Services WebAPK minter is rate-limited. |
| iOS Safari | App is already in standalone mode. CSS-gated hint is hidden by `display-mode: standalone` media query. Browser is Chrome iOS or Firefox iOS (cannot install at all). |
| Safari macOS | Same as iOS but for the "Add to Dock" hint. App is already in `~/Applications`. |
| Firefox desktop | Firefox 142 or earlier on Windows. Any version on macOS or Linux. No install path exists. |

### Symptom: service worker not updating

| Platform | Most likely causes |
|---|---|
| All Chromium | `/sw.js` cached with long TTL at the CDN. SW byte-for-byte identical (no version-string change). Active SW holds clients via `clients.claim()` but never calls `skipWaiting()`. |
| iOS Safari (installed PWA) | App not opened recently. iOS aggressively kills background SWs. User must open the PWA and trigger a fresh navigation. |
| Safari macOS (installed) | Same as iOS. May require quit and relaunch of the Dock app. |
| Firefox | SW only checked at page load. Long-lived tab needs explicit reload. |

## Cross-platform decision quick-reference

| Capability | Chrome / Edge desktop | Chrome Android | Safari macOS | Safari iOS / iPadOS | Firefox desktop | Firefox Android |
|---|---|---|---|---|---|---|
| Manifest install | Yes (beforeinstallprompt) | Yes (WebAPK) | Yes (Add to Dock) | Yes (Add to Home Screen, manual) | Yes (Win, F143+) | Shortcut only |
| Standalone display mode | Yes | Yes | Yes | Yes (iOS 16.4+) | Limited | No |
| Web Push | Yes | Yes (FCM) | Yes (macOS 13+) | Yes (iOS 16.4+, installed only) | Yes | No |
| Declarative Web Push | No | No | Yes (Safari 18.4+) | Yes (Safari 18.4+) | No | No |
| Background Sync | Yes | Yes | No | No | No | No |
| Periodic Background Sync | Yes (engagement-gated) | Yes (engagement-gated) | No | No | No | No |
| Background Fetch | Yes | Yes | No | No | No | No |
| Screen Wake Lock | Yes | Yes | Yes | Yes (iOS 18.4+ for HSWA) | Yes | Yes |
| Web Bluetooth / USB / HID / Serial | Yes | Yes | No | No | No | No |
| WebNFC | No | Yes (Chrome only) | No | No | No | No |
| Window Controls Overlay | Yes | N/A | No | N/A | No | N/A |
| File Handlers | Yes | N/A | No | N/A | No | N/A |
| Protocol Handlers | Yes | Yes (limited) | No | No | Limited | Limited |
| OPFS | Yes | Yes | Yes (17+) | Yes (17+) | Yes | Yes |
| Persistent Storage | Yes (engagement-gated) | Yes (engagement-gated) | Notification-gated | Notification-gated | Prompt | Prompt |
| Badge API | Yes | Yes (WebAPK) | Yes (Dock) | Yes (iOS 16.4+) | No | No |

Cross-reference the columns above with the planning matrix in `production-checklist.md` when scoping a release.

---

## Recommended planning posture

A few defaults that fall out of the matrix:

1. **Build for the WebKit floor, enhance for Chromium.** Treat iOS as the lowest common denominator. Every degraded path required there will probably be useful as a fallback on other platforms too.
2. **Push always needs an installed PWA on iOS.** Do not promote push to iOS users until the install hint has been followed.
3. **Background work must have a foreground fallback.** Anything that uses Background Sync or Periodic Background Sync must also work when triggered from the foreground on iOS or Safari macOS.
4. **Hardware-access PWAs cannot ship to iOS as web only.** If the product depends on Web Bluetooth, WebUSB, WebHID, Web Serial, or WebNFC, plan a Capacitor wrap for the App Store from day one. See `distribution.md`.
5. **Test on real hardware.** Simulators and emulators miss the most important Safari and WebKit bugs. Real iPhone, real Mac, real Android device.
6. **Watch the DMA file.** Apple's posture on PWAs in the EU has changed twice already and may change again. Re-read this section quarterly.
7. **Pick a primary platform.** A PWA optimized for "all platforms at once" tends to satisfy none well. Pick the platform that drives the most revenue or engagement, build the experience to delight there, and let the others degrade gracefully.
8. **Document the degradation.** When a feature is degraded on a platform, document the user-visible behavior in the product spec. Engineers do not invent it on the fly: the design team chooses the fallback in advance.

## Browser-engine choice in the EU

The Digital Markets Act, in force since March 2024, designates Apple's iOS as a "gatekeeper" platform and requires Apple to allow alternative browser engines. As of early 2026 the practical state is:

- iOS 17.4+ in the EU exposes a one-time "default browser" prompt and the `BrowserEngineKit` framework for non-WebKit browsers.
- No major browser vendor has shipped a non-WebKit production build for iOS as of this writing. Chrome iOS, Firefox iOS, and Edge iOS remain WebKit-only.
- The economics of shipping a separate Blink or Gecko build for the EU-only market have so far not justified the engineering investment.
- Apple's stated terms for `BrowserEngineKit` include audit and approval requirements that the browser vendors have contested in public.

The net effect for PWA developers: assume WebKit on iOS for the foreseeable future, even in the EU. Re-evaluate annually.

## Version-floor recommendations

Recommended minimum OS / browser versions to target a modern PWA in 2026:

| Platform | Minimum recommended | Rationale |
|---|---|---|
| iOS / iPadOS | 16.4+ | Web Push, Badge API, manifest-driven standalone. |
| iOS / iPadOS for advanced features | 18.4+ | Declarative Web Push, fixed Wake Lock for installed PWAs. |
| Android | Chrome 100+ | WebAPK generation stable, modern manifest member parsing. |
| Chrome desktop | 126+ | Lighthouse 12 audit toolchain, WCO defaults, scope_extensions. |
| Edge desktop | 126+ | Tracks Chrome closely. Side panel features at this floor. |
| Safari macOS | 14 (Sonoma)+ | Add to Dock, Push, Badge. |
| Safari macOS for advanced features | 18.4 (Sequoia)+ | Declarative Push parity with iOS. |
| Firefox desktop | 143+ on Windows only | Reintroduced PWA support. Earlier versions and other OSes do not install. |

Targeting an older floor is possible but the matrix above is the documented sweet spot. Anything older requires explicit user-segment justification.

---

## Sources

- Apple WebKit release notes for Safari 18.4: <https://webkit.org/blog/16574/webkit-features-in-safari-18-4/>.
- TechCrunch on Apple reversing the EU PWA removal (March 1, 2024): <https://techcrunch.com/2024/03/01/apple-reverses-course-and-will-keep-home-screen-web-apps-on-iphone-in-the-eu/>.
- 9to5Google on Firefox dropping desktop PWA support (January 27, 2021): <https://9to5google.com/2021/01/27/firefox-discontinues-progressive-web-apps-desktop-pwa/>.
- Wikipedia, "Progressive web app", for the Firefox 143 timeline.
- Mobiloud, iOS 26 PWA changes guide (2026).
- Open Web Advocacy on the EU DMA episode: <https://open-web-advocacy.org/>.
- App Store Review Guidelines, section 2.5.6: <https://developer.apple.com/app-store/review/guidelines/#software-requirements>.

For implementation patterns rather than platform inventory, see the topical references in this skill: `manifest.md`, `service-workers.md`, `push-notifications.md`, `background-execution.md`, `install-flows.md`, `storage-persistence.md`, `capabilities-fugu.md`, `distribution.md`.

## Update cadence for this reference

Platform support is a moving target. The bullets in this file reflect the early-2026 baseline. Re-read this section against current sources whenever:

- A new major iOS, macOS, Android, Chrome, Edge, Safari, or Firefox version ships.
- Apple or Google announces a policy change for App Store or Play Store distribution.
- The European Commission opens or closes an investigation into iOS browser-engine choice.
- A new Project Fugu capability moves from origin trial to stable.

The Mobiloud annual PWA guide, the WebKit feature blog at `webkit.org/blog`, the Chrome Status site at `chromestatus.com`, and the Open Web Advocacy news feed are the four sources to monitor.
