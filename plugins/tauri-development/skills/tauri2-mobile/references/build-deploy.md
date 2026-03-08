# Build and Deploy

## Build Commands

### Android
```bash
# Debug APK (testing/sideload)
cargo tauri android build --apk

# Release AAB (Play Store)
cargo tauri android build --aab

# Specific architectures
cargo tauri android build --aab --target aarch64 --target armv7

# Debug build
cargo tauri android build --debug
```

Output locations:
- APK: `src-tauri/gen/android/app/build/outputs/apk/`
- AAB: `src-tauri/gen/android/app/build/outputs/bundle/release/`

### iOS
```bash
# App Store build
cargo tauri ios build --export-method app-store-connect

# Ad Hoc (registered devices)
cargo tauri ios build --export-method ad-hoc

# Development
cargo tauri ios build --export-method development

# Open in Xcode
cargo tauri ios build --open
```

Output: `src-tauri/gen/apple/build/`

## Code Signing

### Android Keystore

**Create keystore:**
```bash
keytool -genkey -v -keystore upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload -storepass YOUR_PASSWORD

mv upload-keystore.jks ~/.android/
```

**Configure signing:**
Create `src-tauri/gen/android/keystore.properties`:
```properties
password=YOUR_PASSWORD
keyAlias=upload
storeFile=/Users/you/.android/upload-keystore.jks
```

**Add to .gitignore:**
```
src-tauri/gen/android/keystore.properties
*.jks
*.keystore
```

**Modify build.gradle.kts** to use signing config in release build type.

### iOS Signing

**Local development:**
1. Open `src-tauri/gen/apple/[App].xcodeproj` in Xcode
2. Select target → Signing & Capabilities
3. Enable "Automatically manage signing"
4. Select your team

**CI/CD environment variables:**
```bash
APPLE_API_ISSUER=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
APPLE_API_KEY=XXXXXXXXXX
APPLE_API_KEY_PATH=/path/to/AuthKey_XXXXXXXXXX.p8
APPLE_DEVELOPMENT_TEAM=XXXXXXXXXX
```

## Store Submission

### Google Play Store

**Prerequisites:**
- Google Play Developer account ($25 one-time)
- App signed with upload key
- Privacy policy URL
- Screenshots (phone, tablet, Chromebook)

**First release:**
1. Create app in Play Console
2. Fill store listing, content rating, pricing
3. Upload AAB manually via Play Console
4. Submit for review

**Subsequent releases:**
Can use Google Play Developer API for automation.

**16KB page size requirement (NDK < 28):**
Add to `.cargo/config.toml`:
```toml
[target.aarch64-linux-android]
rustflags = ["-C", "link-arg=-Wl,-z,max-page-size=16384"]

[target.armv7-linux-androideabi]
rustflags = ["-C", "link-arg=-Wl,-z,max-page-size=16384"]
```

### Apple App Store

**Prerequisites:**
- Apple Developer Program ($99/year)
- App signed with distribution certificate
- Provisioning profile
- Screenshots (various device sizes)

**Upload:**
```bash
xcrun altool --upload-app --type ios \
  --file "src-tauri/gen/apple/build/arm64/App.ipa" \
  --apiKey $APPLE_API_KEY_ID \
  --apiIssuer $APPLE_API_ISSUER
```

Or use Xcode → Product → Archive → Distribute App

## Release Optimization

### Cargo.toml
```toml
[profile.release]
lto = true
opt-level = "s"      # Optimize for size
codegen-units = 1
strip = true
panic = "abort"

[profile.release.package.tauri]
opt-level = 3        # Full optimization for Tauri core
```

### Tauri Config
```json
{
  "bundle": {
    "resources": [],
    "externalBin": []
  }
}
```

### Frontend
- Enable minification in bundler
- Use tree shaking
- Optimize images (WebP)
- Code split with dynamic imports

## Version Management

### tauri.conf.json
```json
{
  "version": "1.0.0"
}
```

### Android (automatic from tauri.conf.json)
Or override in `tauri.android.conf.json`:
```json
{
  "bundle": {
    "android": {
      "versionCode": 1000001
    }
  }
}
```

Version code format: `MAJOR * 1000000 + MINOR * 1000 + PATCH`

### iOS
Version managed via Xcode or `tauri.ios.conf.json`.

## Icons

Generate all icon sizes:
```bash
cargo tauri icon ./app-icon.png
```

Requires 1024x1024 PNG. Generates icons in `src-tauri/icons/`.

## Windows Build Issues

Building Android APKs on Windows has specific gotchas.

### APK Flag Syntax

Use `--apk true` (not just `--apk`):
```bash
# Correct on Windows
cargo tauri android build --apk true

# May fail on Windows
cargo tauri android build --apk
```

### Symlink Error Without Developer Mode

**Problem**: When building without Windows Developer Mode enabled, you may get errors about symlinks failing. This happens because Tauri/Gradle creates symlinks to `.so` native library files, which requires elevated privileges on Windows.

**Error example**:
```
FAILURE: Build failed with an exception.
* What went wrong:
A problem occurred configuring project ':app'.
> java.nio.file.FileSystemException: ...\libtauri_app.so: A required privilege is not held by the client
```

**Solutions**:

1. **Enable Developer Mode** (recommended):
   - Settings → For developers → Developer Mode → On
   - Restart the build

2. **Manual copy workaround** (if Developer Mode not available):

   Copy the `.so` files manually to the `jniLibs` directory:

   ```powershell
   # Create jniLibs directories
   $jniLibs = "src-tauri\gen\android\app\src\main\jniLibs"
   New-Item -ItemType Directory -Force -Path "$jniLibs\arm64-v8a"
   New-Item -ItemType Directory -Force -Path "$jniLibs\armeabi-v7a"
   New-Item -ItemType Directory -Force -Path "$jniLibs\x86"
   New-Item -ItemType Directory -Force -Path "$jniLibs\x86_64"

   # Copy .so files from build output
   $buildOut = "src-tauri\gen\android\app\build\intermediates\tauri"

   Copy-Item "$buildOut\arm64-v8a\release\libtauri_app.so" "$jniLibs\arm64-v8a\"
   Copy-Item "$buildOut\armeabi-v7a\release\libtauri_app.so" "$jniLibs\armeabi-v7a\"
   Copy-Item "$buildOut\x86\release\libtauri_app.so" "$jniLibs\x86\"
   Copy-Item "$buildOut\x86_64\release\libtauri_app.so" "$jniLibs\x86_64\"
   ```

   Then rebuild with Gradle directly:
   ```powershell
   cd src-tauri\gen\android
   .\gradlew assembleRelease
   ```

### Path Lengths

Windows has a 260 character path limit by default. Tauri Android builds can exceed this.

**Solutions**:
- Keep project in a short path (e.g., `C:\dev\myapp`)
- Enable long paths: `git config --system core.longpaths true`
- Enable LongPathsEnabled in registry (requires admin)

## Dev-Mode .so Stale Assets (Windows)

### Problem

App shows months-old frontend content when launched from Android Studio, even though Gradle rebuilds the frontend correctly.

### Root Cause

The Rust `.so` library (`libyour_app.so`) was compiled with `tauri android dev` (dev mode). In dev mode the .so is configured differently than in build mode:

| Setting | Dev mode | Build mode |
|---------|----------|------------|
| `withAssetLoader()` | `false` | `true` |
| `assetLoaderDomain()` | `"wry.assets"` | `"tauri.localhost"` |
| Asset source | Rust handler serves assets embedded in .so | Android `WebViewAssetLoader` serves APK assets |

The WebView navigates to `http://tauri.localhost/`, but with `withAssetLoader()=false` the Rust handler intercepts all requests and serves the assets that were embedded in the .so at compile time. The fresh assets built by Gradle into the APK are ignored entirely.

### Cross-Compilation Blockers on Windows

Recompiling the .so with `tauri android build --debug` hits three sequential issues:

| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | `cargo` not found | Rust toolchain not in bash PATH | Add `~/.rustup/toolchains/stable-x86_64-pc-windows-msvc/bin` to PATH |
| 2 | OpenSSL not found for Android cross-compile | `reqwest` with `native-tls` requires OpenSSL headers for `x86_64-linux-android` | No pre-built OpenSSL available; use vendored build (see #3) |
| 3 | Vendored OpenSSL build fails | `openssl-src` crate needs full Perl; Git Bash ships minimal Perl (missing `Locale::Maketext::Simple`) | Install Strawberry Perl |

### Kotlin Workaround (RustWebViewClient.kt)

If cross-compilation is blocked, patch `RustWebViewClient.kt` to force the `WebViewAssetLoader` path regardless of what the .so reports. This file is in `src-tauri/gen/android/` and is gitignored/auto-generated by Tauri, so changes are local only.

Four issues must be fixed in sequence:

| # | Problem | Symptom | Fix |
|---|---------|---------|-----|
| 1 | .so in dev mode | `withAssetLoader()=false`, Rust serves stale assets | Bypass: call `assetLoader.shouldInterceptRequest()` directly instead of delegating to Rust |
| 2 | HTTP vs HTTPS | Dev-mode WebView navigates to `http://`, but asset loader only intercepts HTTPS | Add `.setHttpAllowed(true)` to the `WebViewAssetLoader.Builder` |
| 3 | Root path `/` returns null | `AssetsPathHandler` does not serve `index.html` for bare `/` path | Rewrite URL: if path is `/`, change to `/index.html` before passing to asset loader |
| 4 | Domain mismatch | .so returns `"wry.assets"`, WebView requests `"tauri.localhost"` | Hardcode `.setDomain("tauri.localhost")` in the asset loader builder |

**Key points:**
- `RustWebViewClient.kt` is regenerated by `tauri android init` -- your changes will be lost if you re-init
- This is a temporary workaround; rebuilding the .so properly is the permanent fix

### Permanent Fix

Install [Strawberry Perl](https://strawberryperl.com/), then rebuild the .so:

```bash
npx tauri android build --debug --target x86_64
```

This recompiles the .so with `withAssetLoader()=true` and `assetLoaderDomain()="tauri.localhost"`, eliminating all Kotlin workarounds.

### Collateral Build Fixes

When rebuilding after a long gap, you may also hit these issues:

| Problem | Fix |
|---------|-----|
| NDK version mismatch (e.g., config references NDK 28 but only 27 is installed) | Update NDK path in `.cargo/config.toml` to match installed version |
| Java source/target 1.8 deprecated | Update `build.gradle.kts`: set `sourceCompatibility = JavaVersion.VERSION_11`, `targetCompatibility = JavaVersion.VERSION_11`, `jvmTarget = "11"` |
| `java {}` toolchain block in root `build.gradle.kts` | Remove it -- does not work without the `java` plugin applied |
