# Distribution

A PWA can ship to multiple app stores in addition to plain web distribution. Each store has its own wrapping technology, signing flow, and submission portal. This reference covers the four mainstream targets: Google Play (via Trusted Web Activity), Microsoft Store (via PWA Builder), Apple App Store (via Capacitor or Cordova wrapping), and Meta Quest Store (via PWA Builder).

The web origin remains the source of truth. All wrappers load the same HTTPS URL, the same manifest, and the same service worker. The wrapper exists to satisfy the store's packaging requirement, to provide a verified app identity, and in some stores to unlock native capabilities (in-app purchase, native push, OS integrations) that the open web cannot deliver.

---

## Google Play via TWA (Bubblewrap)

A Trusted Web Activity (TWA) is a Chrome Custom Tab without the URL bar. The Android shell is a thin native app that opens a Chrome instance and points it at the PWA. Bubblewrap is the official Google CLI that generates, signs, and builds the TWA from a `manifest.webmanifest`.

### Install Bubblewrap and build

```bash
npm i -g @bubblewrap/cli
bubblewrap init --manifest=https://acme.com/manifest.webmanifest
bubblewrap build
```

The `init` command fetches the manifest, prompts for package name, app version, signing key parameters, and target SDK, then writes a `twa-manifest.json` project file alongside the Android Studio project skeleton. The `build` command compiles, signs, and emits two artifacts:

- `app-release-bundle.aab`: the Android App Bundle uploaded to Google Play Console.
- `app-release-signed.apk`: a directly installable APK useful for internal testing.

### Digital Asset Links: the `assetlinks.json` requirement

A TWA is "trusted" only if the web origin proves it owns the Android package. The proof is a `Digital Asset Links` JSON file served at `/.well-known/assetlinks.json` on the same HTTPS origin as the PWA. The file links the Android package name and signing certificate SHA-256 fingerprint to the origin.

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.acme.suite",
    "sha256_cert_fingerprints": ["XX:XX:..."]
  }
}]
```

Critical: without a valid Digital Asset Links file, the TWA degrades to a Custom Tab with a visible URL bar. The app still works, but it no longer looks like a standalone application. The address bar and Chrome branding are exposed, which defeats the purpose of the TWA wrapper. This is the single most common reason a TWA submission looks broken on a tester's device.

### Verification checklist for the TWA build

- The `package_name` in `assetlinks.json` matches the `applicationId` in the generated `app/build.gradle`.
- The `sha256_cert_fingerprints` array contains the SHA-256 fingerprint of the release-signing certificate. Use the upload key fingerprint if Google Play App Signing is enabled, plus the Play-signed fingerprint from the Play Console.
- The file is served with `Content-Type: application/json` and is reachable over HTTPS without redirects.
- The `manifest.webmanifest` includes `start_url`, `scope`, a valid `display` mode, and 192 and 512 PNG icons.
- The `digitalAssetLinks` validator at `developers.google.com/digital-asset-links/tools/generator` returns a clean result for the production URL before submitting to Google Play.

### Google Play submission flow

1. Create the app entry in Google Play Console.
2. Upload the `.aab` to the production track (or to internal testing first).
3. Configure store listing: title, short description, full description, screenshots, feature graphic, content rating, privacy policy URL.
4. Enable Google Play App Signing (recommended).
5. After upload, retrieve the App Signing key SHA-256 fingerprint from Play Console and reflect it in `/.well-known/assetlinks.json`.
6. Submit for review. Review typically lands within hours to a few days.

### When to keep the user inside the TWA

The TWA shows a Custom Tab inside the same Chrome instance for any cross-origin navigation that leaves the manifest scope. Configure the manifest `scope` to cover every origin the user is expected to visit during their session. For payment redirects and OAuth flows that cross to a third-party origin and back, the user briefly sees the Custom Tab address bar; this is expected behavior, not a misconfiguration.

### Versioning the TWA

Each Google Play release requires a higher `versionCode` than the previous one. Bubblewrap stores this in `twa-manifest.json` under `appVersionCode` and `appVersionName`. Update both before every build:

- `appVersionCode`: integer, must strictly increase per release.
- `appVersionName`: human-readable semver string shown on the Play Store listing.

Rebuild with `bubblewrap update` to refresh the project against any manifest changes pulled from the web origin, then `bubblewrap build` to produce a new `.aab`. The web origin can ship updates independently; the TWA shell only needs a new release when the manifest changes, the package metadata changes, or Bubblewrap or Android SDK targets need to be bumped to satisfy Play Console policy.

### Splash screen on Android

Bubblewrap reads the manifest `background_color` and the largest `purpose: "any"` icon to generate the Android splash screen. The Android 12+ splash uses a smaller, centered icon (the system masks it inside a circle), so include a `purpose: "maskable"` 512 PNG with the design centered inside the 40 percent safe zone. Without a maskable icon, Android 12 and later crop the splash icon awkwardly.

---

## Microsoft Store

The Microsoft Store accepts PWAs through PWA Builder. The flow is browser-driven and does not require Visual Studio or a Windows toolchain.

### PWA Builder for MSIX generation

1. Open `https://pwabuilder.com`.
2. Enter the production HTTPS URL of the PWA.
3. The site audits the manifest and service worker, then generates installable packages for Windows, Android, iOS, and Meta Quest from a single source.
4. For Windows, the generated artifact is a signed MSIX bundle ready for submission.

PWA Builder injects a small native shim that registers protocol handlers, file handlers, and share target intents at the Windows level, and bridges them back into the manifest declarations. The runtime is the Edge WebView2 component already installed on Windows 10 and 11.

### Microsoft Partner Center submission

1. Create or sign in to a Microsoft Partner Center account. Individual PWA submissions are free as of 2025 and 2026.
2. Reserve the app name in Partner Center.
3. Upload the MSIX produced by PWA Builder to a new submission.
4. Fill in the store listing, age rating, market availability, and pricing (free is supported).
5. Submit for certification. Certification typically completes within a couple of business days.

### Verification before submitting

- The MSIX is signed with a trusted certificate (PWA Builder handles this when using a Partner Center account).
- The manifest `name`, `short_name`, and icon set match the Partner Center store listing.
- The PWA loads over HTTPS without mixed content warnings.
- A privacy policy URL is reachable from inside the PWA.

### What runs inside the MSIX

The packaged app launches Edge WebView2, the Chromium-based runtime bundled with Windows 10 and 11. The PWA loads from the production HTTPS origin and the service worker registers normally. Capabilities that are gated on the web platform (Web Push, Background Sync, install prompts) behave the same as inside the Edge browser. Additional Windows-only surfaces unlocked by PWA Builder's shim:

- Start menu entry with the manifest icon.
- Pinning to taskbar with a clean app identity.
- Protocol handler registration so `web+acme://` URLs from other apps open the PWA.
- File handler registration so double-clicking a `.foo` file from File Explorer can open it inside the PWA via `window.launchQueue`.

### Updating the Store listing

The web origin can ship updates independently. The MSIX needs a new submission only when the manifest changes, the icon set changes, or capability declarations (protocol handlers, file handlers, share targets) change. For pure UI or feature work behind the same manifest, no Store resubmission is required.

---

## Apple App Store

Apple does not accept pure PWAs. App Store Review Guideline 4.2.2 explicitly rejects "web clippings" and apps that are simply repackaged websites. A PWA submitted as a thin WebView wrapper without meaningful native functionality is rejected on the first review pass.

### The workable path: Capacitor or Cordova

To ship a PWA to the App Store, wrap it with a hybrid runtime that adds native plugins and platform integrations:

- **Capacitor** (Ionic): the modern recommendation. Native iOS project generated from the web build, Swift or Objective-C bridges to native plugins (push, in-app purchase, biometrics, native sharing, camera with native quality).
- **Cordova** (legacy): older, still functional, but with a slower plugin ecosystem and a less ergonomic CLI.

### Why this passes review

The hybrid wrapper is not a thin web view. It exposes native APIs that the web cannot:

- Native push notifications via APNs, which on the App Store side count as a first-class integration. Even though iOS 16.4+ supports Web Push for installed PWAs from Safari, App Store reviewers expect native APNs registration for a packaged iOS app.
- In-app purchase (IAP) through StoreKit, mandatory for digital goods sold inside the app.
- Native biometrics (Face ID, Touch ID) via the LocalAuthentication framework.
- Camera, microphone, and file pickers with iOS-native UI.
- HealthKit, ARKit, CoreNFC, and other capabilities outside the web platform.

The hybrid build typically loads the production PWA URL inside `WKWebView` and delegates a defined set of operations to native plugins. The same web origin and service worker continue to power the experience. Native plugins are invoked through a JavaScript bridge.

### Submission checklist

- Apple Developer Program membership (USD 99 per year for the Individual program).
- App Store Connect entry for the app.
- A Capacitor or Cordova iOS project that builds and runs on a physical device without warnings.
- At least two non-trivial native plugin integrations exposed in the UI (native push, IAP, biometrics, etc.).
- App Privacy details filled in for data collection, tracking, and third-party SDKs.
- Sign-In with Apple offered if any other third-party sign-in method is offered (Guideline 4.8).
- Screenshots for every required device class.

### When wrapping with Capacitor is not worth it

For an internal, B2B, or invitation-only PWA where iOS install via the Safari Share menu is acceptable, skip the App Store. iOS 16.4+ supports installation to Home Screen, manifest standalone display, and Web Push from Safari, which is enough for many internal tools. The App Store is the right target only when discovery, IAP, or native integration is a business requirement.

### Capacitor project structure at a glance

A typical Capacitor wrapper sits next to the web project:

```
my-pwa/
  package.json
  dist/                     # web build output (Vite, Next export, etc.)
  capacitor.config.ts       # Capacitor app id, name, web dir, server config
  ios/                      # generated native iOS project (Xcode)
  android/                  # generated native Android project (optional)
```

`capacitor.config.ts` typically points `webDir` at the web build output and may set `server.url` to load the production HTTPS origin instead of bundling the web assets. Loading from the production URL keeps the service worker, push, and dynamic updates on the same lifecycle as the open web; bundling locally is the recommended path for App Store submission because reviewers expect the binary to function offline at first launch.

Add native plugins through `npm install @capacitor/push-notifications`, `@capacitor/local-notifications`, `@capacitor-community/in-app-purchases`, and so on. Each plugin exposes a JavaScript API the PWA can call from the same code that runs on the open web, with feature detection so the PWA-on-web fallback continues to work.

---

## Meta Quest Store

PWA Builder packages PWAs for the Meta Quest Store, the curated app marketplace for Meta Quest headsets running Horizon OS. The runtime on Quest is a Chromium fork, so most PWA features port cleanly.

### Two distribution channels on Quest

1. **Meta Quest Store (curated)**: official submission through the Meta Developer Hub. The store hosts the app for general discovery. Review is more involved than mobile stores, with VR-specific guidelines around comfort, locomotion, and content.
2. **Sideload via `adb`**: developer-mode headset connected by USB. Push an APK with `adb install`. Useful for internal testing, enterprise distribution, and apps that do not pass curated review.

### PWA Builder flow for Quest

1. On `pwabuilder.com`, after entering the PWA URL, select the Meta Quest package option.
2. PWA Builder generates an Android APK packaged for Quest with the correct manifest entries and immersive-web flags.
3. For sideload: `adb install path/to/app.apk` against a Quest in Developer Mode.
4. For curated submission: upload through the Meta Developer Hub and follow the Quest Store review process.

### VR-specific considerations

- The PWA should declare `display: "fullscreen"` or `display_override` including `"fullscreen"` so the headset launches it without a system browser chrome.
- Test the WebXR entry point (if the app uses WebXR) on the physical device. Quest browser hardware-acceleration paths differ from desktop Chromium.
- Audio must be inside a user-gesture promise to autoplay in some Quest configurations.
- Quest UI guidelines require comfortable input handling and a clear exit path from immersive sessions.

### Sideload workflow

For internal testing, employee distribution, or apps that are not ready for the curated store:

1. Enable Developer Mode on the Quest from the Meta Quest mobile app (requires a verified developer account).
2. Connect the headset by USB and authorize the host machine.
3. Run `adb devices` to confirm the headset is visible.
4. Push the APK with `adb install -r path/to/app.apk` (the `-r` flag replaces the previous install).
5. Launch the app from the Quest's Unknown Sources section under the Library.

This is the standard flow for kiosk deployments, on-site enterprise apps, and pre-store beta testing.

---

## Troubleshooting common submission issues

### TWA opens with a visible URL bar

The `assetlinks.json` file is missing, served with the wrong MIME type, or contains a fingerprint that does not match the actual signing key. Re-verify against the Play Console App Signing key fingerprint and confirm the file is reachable at `https://YOUR-ORIGIN/.well-known/assetlinks.json` without redirects.

### Apple review cites Guideline 4.2.2

The app reads as "a website wrapped in a WebView" to the reviewer. Surface at least two native integrations prominently: native push registration, in-app purchase, biometrics, or a native sharing flow. Update the App Store listing screenshots and description to emphasize what the app does natively, not just what the website does.

### MSIX upload rejected for missing identity

The MSIX `Identity` element must match the name reserved in Partner Center exactly. PWA Builder injects this when the user is signed in with their Partner Center account; if generating offline, edit the `AppxManifest.xml` inside the MSIX or regenerate with the correct identity.

### Service worker stops updating inside a wrapper

The wrapper caches the web origin's responses through the wrapping runtime (Chrome for TWA, WebView2 for MSIX, WKWebView for Capacitor). Confirm the service worker is registered with the correct scope, that `/sw.js` is served with `Cache-Control: no-cache`, and that the user-driven update banner from `service-workers.md` is wired into the production build.

---

## Choosing where to ship

| Surface | Wrapper | Effort | When to ship |
|---|---|---|---|
| Open web | None | Lowest | Always. The PWA URL is the foundation. |
| Google Play | Bubblewrap (TWA) | Low | Android users expect Play. Bubblewrap is one config file plus `assetlinks.json`. |
| Microsoft Store | PWA Builder (MSIX) | Low | Windows users discovering through the Store. Free submission and minimal native binding. |
| Apple App Store | Capacitor or Cordova | High | Required for IAP, native push, or App Store discovery. Adds a real native project to maintain. |
| Meta Quest Store | PWA Builder | Medium | VR-first or immersive PWAs targeting Horizon OS users. |

The recommended order for most teams: ship the open-web PWA first, then Google Play and Microsoft Store in parallel (both are low effort and unlock substantial install volume), then Apple App Store last if the business case justifies the wrapper investment. Meta Quest is a niche target unless the PWA is explicitly built around WebXR or immersive use cases.

---

## Related references

- `manifest.md`: the manifest fields consumed by Bubblewrap and PWA Builder (`name`, `short_name`, `start_url`, `scope`, `display`, `display_override`, icons).
- `service-workers.md`: the service worker that every wrapper loads at runtime.
- `platform-constraints.md`: per-platform behavior of the wrapped PWA on iOS, Android, and Desktop.
- `production-checklist.md`: the pre-submission deploy checklist.
