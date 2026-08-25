# Mobile Plugins and Patterns

Mobile-only Tauri plugins (biometric, barcode, haptics, NFC, geolocation) plus mobile deep-link configuration and the Android safe-area workaround.

## When to use

Adding a capability that only exists on Android/iOS, or hitting one of the mobile-specific quirks below. For universal plugins (fs, http, store, sql, etc.), see `plugins-core.md`.

## Mobile-only plugin matrix

| Plugin | Platforms | Use for |
|--------|-----------|---------|
| `biometric` | Android, iOS | Fingerprint / Face ID auth |
| `barcode-scanner` | Android, iOS | QR / EAN / Code128 scanning |
| `haptics` | Android, iOS | Tap / impact / notification feedback |
| `nfc` | Android, iOS | NFC tag read/write |
| `geolocation` | Android, iOS | GPS position + watch |

Universal plugins that also work on mobile: `fs`, `http`, `notification`, `store`, `sql`, `deep-link`, `opener`, `os`.

## Gotchas

- **`#[cfg(mobile)]` on every mobile-only plugin registration.** Without the gate, `cargo tauri build` fails on desktop targets. Missing-cfg is the #1 mobile build error.
- **Android `safe-area-inset-*` does not work** out of the box on Tauri's WebView. Pure CSS `env(safe-area-inset-top)` returns 0 on Android. The fix is to detect platform once at app boot and inject explicit pixel values via CSS custom properties (snippet below).
- **iOS biometric "fallback to password" requires `allowDeviceCredential: true`** -- without it, users with no biometrics enrolled get a hard error instead of a passcode prompt.
- **`barcode-scanner` opens a full-screen camera view** that takes over the WebView; design for the disappear/reappear lifecycle. Use `windowed: true` only for prototypes -- on iOS the windowed view has known z-order bugs.
- **`geolocation` `enableHighAccuracy: true` drains battery fast** -- only enable on the active screen, never in a background subscription.
- **NFC writes are platform-different.** Android works in foreground only (no background dispatch via Tauri's plugin); iOS prompts user every read/write -- there is no "always-on" NFC.
- **Mobile capabilities live in their own file.** Create `src-tauri/capabilities/mobile.json` with `"platforms": ["iOS", "android"]` -- mixing into `default.json` makes desktop fail capability checks.

## Android safe-area workaround (the one composite pattern worth keeping local)

CSS `env(safe-area-inset-*)` works on iOS but returns 0 on Android WebView. Detect Android and inject explicit values:

```typescript
import { platform } from '@tauri-apps/plugin-os';

export async function setupMobileSafeAreas(): Promise<void> {
  if ((await platform()) === 'android') {
    document.documentElement.style.setProperty('--safe-area-top', '48px');
    document.documentElement.style.setProperty('--safe-area-bottom', '24px');
  }
}
```

```css
:root {
  --safe-area-top: env(safe-area-inset-top, 0px);     /* iOS native; Android 0 -> overridden by JS */
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
}
.header { padding-top: var(--safe-area-top); }
.bottom-nav { padding-bottom: var(--safe-area-bottom); }
```

Typical values: Android top ~48px, bottom ~24px. iOS varies 44-59px top, 0-34px bottom (home indicator).

## Mobile capabilities file

```json
// src-tauri/capabilities/mobile.json
{
  "identifier": "mobile",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    "biometric:allow-authenticate",
    "geolocation:allow-get-current-position",
    "haptics:default"
  ]
}
```

## Mobile deep-link snippets

Android `AndroidManifest.xml` Intent Filter for Universal Links:

```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="app.example.com" />
</intent-filter>
```

iOS Associated Domains (Xcode → Signing & Capabilities):
```
applinks:app.example.com
```

## Official docs

- Mobile plugins index: https://v2.tauri.app/plugin/ (each plugin page lists its mobile support)
- Biometric: https://v2.tauri.app/plugin/biometric/
- Barcode scanner: https://v2.tauri.app/plugin/barcode-scanner/
- NFC: https://v2.tauri.app/plugin/nfc/
- Haptics: https://v2.tauri.app/plugin/haptics/
- Geolocation: https://v2.tauri.app/plugin/geolocation/
- Deep links (mobile sections): https://v2.tauri.app/plugin/deep-link/

## Community plugins

- `tauri-plugin-iap` -- in-app purchases (see `iap.md`)
- `tauri-plugin-keep-screen-on`, `tauri-plugin-camera`, `tauri-plugin-share`
- Index: https://github.com/tauri-apps/awesome-tauri

## Related

- `plugins-core.md` -- universal plugins
- `iap.md` -- the IAP plugin in detail
- `setup-mobile.md` -- toolchain prerequisites
- `authentication-mobile.md` -- mobile OAuth + Apple Sign-In
