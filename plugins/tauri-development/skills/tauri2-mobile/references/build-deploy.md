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
