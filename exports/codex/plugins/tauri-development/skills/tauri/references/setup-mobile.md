# Mobile Environment Setup

Android SDK + iOS Xcode tooling on top of the base prerequisites in `setup.md`.

## When to use

Adding Android or iOS targets to an existing Tauri 2 project, or setting up a new dev machine for mobile builds. Pure desktop projects can skip this entirely.

## Rust targets (the one thing easy to forget)

```bash
# Android
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android

# iOS (macOS only)
rustup target add aarch64-apple-ios x86_64-apple-ios aarch64-apple-ios-sim
```

`tauri android init` / `tauri ios init` won't add these for you -- the build will fail late with cryptic linker errors if they're missing.

## Gotchas

- **Strawberry Perl on Windows.** If your Rust deps include `reqwest` with `native-tls`, cross-compiling for Android pulls in the vendored `openssl-src` crate, which needs a full Perl install. Git Bash's bundled Perl is **not** sufficient. Install [Strawberry Perl](https://strawberryperl.com/) and put it on PATH before `tauri android build`. The error message ("Could not find Perl") doesn't make this obvious.
- **`TAURI_DEV_HOST` is set automatically** by `tauri android dev` / `tauri ios dev` -- your `vite.config.ts` should read it and bind `server.host` + HMR to it. If you hardcode `localhost`, the device can't reach the dev server.
- **Vite build target.** Mobile WebViews lag desktop -- target `chrome105` for Android WebView (matches Tauri 2's WebView2 floor) and `safari14` for iOS WKWebView. `esnext` will silently produce code the device WebView can't parse.
- **iOS needs the full Xcode**, not just CLI tools. CocoaPods via `brew install cocoapods` -- the gem version drifts.
- **Android NDK version**: install **NDK 28+** if you can. NDK 28 produces 16-KB-aligned shared libraries by default, which Google Play requires (deadline extended to 2026-05-31). NDK 27 is the LTS line and works fine, but you must add the `-Wl,-z,max-page-size=16384` rustflag (see `build-deploy-mobile.md`). Set `NDK_HOME` dynamically (e.g. `$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk | tail -1)`); pinning a specific version path breaks across machines.

## Toolchain versions pinned by `tauri android init` (May 2026)

The current Tauri 2.x template (verified against `dev` branch on 2026-05-08, shipped in tauri-cli 2.11.1) generates an Android project pinned to:

| Component | Version | Source |
|---|---|---|
| `tauri` / `tauri-cli` / `tauri-build` | 2.11.1 / 2.11.1 / 2.6.1 | crates.io, released 2026-05-06 |
| Android Gradle Plugin (AGP) | 8.11.0 | `build.gradle.kts` template |
| Gradle wrapper | 8.14.3 | `gradle-wrapper.properties` template |
| Kotlin | 1.9.25 | `build.gradle.kts` template |
| `compileSdk` / `targetSdk` | 36 / 36 | `app/build.gradle.kts` template |
| `jvmTarget` (deprecated form) | `"1.8"` | `app/build.gradle.kts` template |

`targetSdk = 36` is forward-compatible with the Google Play API requirement (currently API 35 since 2025-08-31; no API 36 deadline announced as of May 2026).

### Gradle 9.0 readiness

Builds on the shipped template emit "Deprecated Gradle features were used in this build, making it incompatible with Gradle 9.0." The known-deprecated bits in the Tauri Android template:

- `kotlinOptions { jvmTarget = "1.8" }` is deprecated in favour of the `jvmToolchain { ... }` block in modern AGP/Kotlin.
- A few other AGP 8.x diagnostics that get loud when you run with Gradle 8.13+.

Tracking issue: [tauri-apps/tauri#13858](https://github.com/tauri-apps/tauri/issues/13858). PR [#14984](https://github.com/tauri-apps/tauri/pull/14984) proposed bumping the template to AGP 9.0.1 / Gradle 9.3.1 / Kotlin 2.3.10 / JVM 24 but was closed without merging as of 2026-05-08, so the warnings remain in shipped projects. Builds still succeed on Gradle 8.14.3; treat the warnings as a future-compat heads-up, not a blocker. If you want to silence them locally, you can override the toolchain with a `jvmToolchain(17)` block in `app/build.gradle.kts` and bump the wrapper, but that is a manual maintenance burden until the upstream template moves.

## Vite config snippet (the parts that matter)

```typescript
export default defineConfig({
  server: {
    host: process.env.TAURI_DEV_HOST || 'localhost',
    port: 5173,
    strictPort: true,
    hmr: process.env.TAURI_DEV_HOST
      ? { protocol: 'ws', host: process.env.TAURI_DEV_HOST, port: 5174 }
      : undefined,
  },
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    target: process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari14',
  },
});
```

## Official docs

- Mobile prerequisites: https://v2.tauri.app/start/prerequisites/#mobile-targets
- Android setup: https://v2.tauri.app/develop/#android
- iOS setup: https://v2.tauri.app/develop/#ios
- Android permissions reference: https://developer.android.com/reference/android/Manifest.permission
- iOS Info.plist usage descriptions: https://developer.apple.com/documentation/bundleresources/information_property_list

## Related

- `setup.md` -- base prerequisites
- `build-deploy-mobile.md` -- store builds, signing, the full Android/iOS gotcha trail
- `mobile-stale-builds.md` -- the Cargo `rerun-if-changed` gap that produces stale APKs (read before debugging "frontend changes don't appear")
- `testing.md` -- emulator + ADB + WebView debugging
- `ci-cd-mobile.md` -- CI build matrix for mobile
