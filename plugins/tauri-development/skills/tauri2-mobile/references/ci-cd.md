# CI/CD with GitHub Actions

## Android Build Workflow

```yaml
name: Build Android

on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Setup Android SDK
        uses: android-actions/setup-android@v3

      - name: Setup Rust
        uses: dtolnay/rust-action@stable
        with:
          targets: aarch64-linux-android,armv7-linux-androideabi

      - name: Install dependencies
        run: npm ci

      - name: Setup Android signing
        run: |
          cd src-tauri/gen/android
          echo "keyAlias=${{ secrets.ANDROID_KEY_ALIAS }}" > keystore.properties
          echo "password=${{ secrets.ANDROID_KEY_PASSWORD }}" >> keystore.properties
          base64 -d <<< "${{ secrets.ANDROID_KEYSTORE_BASE64 }}" > $RUNNER_TEMP/keystore.jks
          echo "storeFile=$RUNNER_TEMP/keystore.jks" >> keystore.properties

      - name: Build AAB
        run: npm run tauri android build -- --aab

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: android-aab
          path: src-tauri/gen/android/app/build/outputs/bundle/release/*.aab
```

## iOS Build Workflow

```yaml
name: Build iOS

on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Setup Rust
        uses: dtolnay/rust-action@stable
        with:
          targets: aarch64-apple-ios

      - name: Install dependencies
        run: npm ci

      - name: Setup iOS signing
        env:
          APPLE_API_ISSUER: ${{ secrets.APPLE_API_ISSUER }}
          APPLE_API_KEY: ${{ secrets.APPLE_API_KEY }}
          APPLE_API_KEY_PATH: ${{ runner.temp }}/AuthKey.p8
          APPLE_DEVELOPMENT_TEAM: ${{ secrets.APPLE_TEAM_ID }}
        run: |
          echo "${{ secrets.APPLE_API_KEY_CONTENT }}" > $RUNNER_TEMP/AuthKey.p8

      - name: Build iOS
        run: npm run tauri ios build -- --export-method app-store-connect

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ios-ipa
          path: src-tauri/gen/apple/build/**/*.ipa
```

## Combined Workflow

```yaml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      # ... Android steps from above

  build-ios:
    runs-on: macos-latest
    steps:
      # ... iOS steps from above

  create-release:
    needs: [build-android, build-ios]
    runs-on: ubuntu-latest
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            android-aab/*.aab
            ios-ipa/*.ipa
          draft: true
```

## Using tauri-action

Official Tauri action for simplified builds:

```yaml
- name: Build Tauri
  uses: tauri-apps/tauri-action@v0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tagName: v__VERSION__
    releaseName: 'App v__VERSION__'
    releaseBody: 'See assets for downloads.'
    releaseDraft: true
    prerelease: false

# For mobile (experimental)
- uses: tauri-apps/tauri-action@v0
  with:
    mobile: 'android'  # or 'ios' (requires macOS runner)
```

## Required Secrets

### Android
```
ANDROID_KEY_ALIAS        # Keystore alias (e.g., "upload")
ANDROID_KEY_PASSWORD     # Keystore password
ANDROID_KEYSTORE_BASE64  # base64 encoded keystore file
```

Generate base64:
```bash
base64 -i upload-keystore.jks | tr -d '\n'
```

### iOS
```
APPLE_API_ISSUER       # From App Store Connect API
APPLE_API_KEY          # Key ID
APPLE_API_KEY_CONTENT  # Content of .p8 file
APPLE_TEAM_ID          # Development team ID
```

## Caching

Speed up builds with caching:

```yaml
- name: Cache Rust
  uses: Swatinem/rust-cache@v2
  with:
    workspaces: src-tauri

- name: Cache Gradle
  uses: gradle/actions/setup-gradle@v3

- name: Cache CocoaPods
  uses: actions/cache@v4
  with:
    path: |
      src-tauri/gen/apple/Pods
      ~/Library/Caches/CocoaPods
    key: ${{ runner.os }}-pods-${{ hashFiles('**/Podfile.lock') }}
```

## Auto-publish to Stores

### Google Play (with Fastlane)
```yaml
- name: Deploy to Play Store
  uses: r0adkll/upload-google-play@v1
  with:
    serviceAccountJsonPlainText: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
    packageName: com.your.app
    releaseFiles: android-aab/*.aab
    track: internal  # or alpha, beta, production
```

### App Store (with Fastlane)
```yaml
- name: Deploy to App Store
  run: |
    fastlane deliver --ipa ios-ipa/*.ipa \
      --skip_screenshots --skip_metadata \
      --api_key_path $RUNNER_TEMP/AuthKey.p8
```
