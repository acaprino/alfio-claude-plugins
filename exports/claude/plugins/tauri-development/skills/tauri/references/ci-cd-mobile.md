# Mobile CI/CD

Mobile-specific signing, store upload, and gotchas on top of the base pipeline patterns in `ci-cd.md`.

## When to use

CI that produces signed `.aab`/`.apk` for Google Play or `.ipa` for the App Store. Internal/test builds can skip most of this.

## Required runner OS

- **Android**: Linux (cheapest, fastest). Java 17+, Android SDK + NDK, Rust targets `aarch64-linux-android` and `armv7-linux-androideabi`.
- **iOS**: macOS only -- Apple toolchains do not run elsewhere. Full Xcode (not CLI tools), Rust targets `aarch64-apple-ios` and `aarch64-apple-ios-sim`.

Run them in parallel jobs.

## Gotchas

- **16KB page size for Google Play.** Builds with NDK < 28 may fail Play Console's page-size check. Either upgrade NDK or add `RUSTFLAGS="-C link-arg=-Wl,-z,max-page-size=16384"` for affected `.so` libs. Symptom: store upload rejected with "App is not 16 KB aligned."
- **Android keystore as base64.** Generate with `base64 -i upload-keystore.jks | tr -d '\n'` and store as `ANDROID_KEYSTORE_BASE64`. Decode at build time:
  ```bash
  echo "$ANDROID_KEYSTORE_BASE64" | base64 -d > /tmp/keystore.jks
  ```
  Then write `keystore.properties` with alias/password/path. Required secrets: `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`, `ANDROID_KEYSTORE_BASE64`.
- **iOS: App Store Connect API key, not Apple ID.** Headless CI cannot do interactive 2FA. Generate a `.p8` key in App Store Connect and store as `APPLE_API_KEY_CONTENT` (raw .p8 contents) plus `APPLE_API_ISSUER`, `APPLE_API_KEY` (the key ID), `APPLE_TEAM_ID`.
- **Cache Gradle and CocoaPods.** Without it, Android builds add 5-10 min and iOS adds 3-5 min.
  - Gradle: `~/.gradle/caches/` keyed on `gradle-wrapper.properties` hash
  - CocoaPods: `Pods/` and `~/Library/Caches/CocoaPods/` keyed on `Podfile.lock`
- **Dev builds vs store builds use different artifact paths.** AABs land in `src-tauri/gen/android/app/build/outputs/bundle/`, APKs in `.../apk/`. iOS `.ipa` ends up under `src-tauri/gen/apple/build/`.

## Store upload

- **Google Play**: Fastlane or the Play Developer API. Tracks: `internal`, `alpha`, `beta`, `production`. Requires a service account JSON with the `Release Manager` role.
- **App Store**: `xcrun altool --upload-app` or Fastlane `pilot`/`deliver`. Uses the same App Store Connect API key as signing.

## Official docs

- Tauri Android distribution: https://v2.tauri.app/distribute/google-play/
- Tauri iOS distribution: https://v2.tauri.app/distribute/app-store/
- App Store Connect API keys: https://developer.apple.com/documentation/appstoreconnectapi/creating_api_keys_for_app_store_connect_api
- 16KB page size requirement: https://developer.android.com/guide/practices/page-sizes
- Fastlane: https://docs.fastlane.tools/

## Related

- `ci-cd.md` -- base pipeline patterns, caching, OS matrix
- `build-deploy-mobile.md` -- the mobile bundle gotchas (NDK, symlinks, RustWebViewClient) that CI inherits
- `setup-mobile.md` -- the toolchain CI mirrors
