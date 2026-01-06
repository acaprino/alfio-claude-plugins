# Environment Setup

## Prerequisites

### All Platforms
- Rust (latest stable): `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Node.js LTS
- Tauri CLI: `npm install -D @tauri-apps/cli`

### Android Development

**Install Android Studio** with SDK Manager components:
- Android SDK Platform (API 34+)
- Android SDK Platform-Tools
- Android SDK Build-Tools
- NDK (Side by side)
- Android SDK Command-line Tools

**Environment Variables:**
```bash
# macOS
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export ANDROID_HOME="$HOME/Library/Android/sdk"
export NDK_HOME="$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk)"

# Linux
export JAVA_HOME=/opt/android-studio/jbr
export ANDROID_HOME="$HOME/Android/Sdk"
export NDK_HOME="$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk)"

# Windows (PowerShell)
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:NDK_HOME = "$env:ANDROID_HOME\ndk\<version>"
```

**Rust targets:**
```bash
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
```

### iOS Development (macOS only)

- Xcode from Mac App Store (full install, not just CLI tools)
- Command Line Tools: `xcode-select --install`
- CocoaPods: `brew install cocoapods`
- Apple Developer account configured in Xcode

**Rust targets:**
```bash
rustup target add aarch64-apple-ios x86_64-apple-ios aarch64-apple-ios-sim
```

## Project Initialization

```bash
# New project with mobile
npm create tauri-app@latest
# Select mobile targets during setup

# Add mobile to existing project
npm run tauri android init
npm run tauri ios init

# Verify setup
cargo tauri info
```

## Vite Configuration for Mobile

```typescript
// vite.config.ts
import { defineConfig } from 'vite';

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
    minify: !process.env.TAURI_ENV_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
  },
});
```

## Platform-Specific Configuration

### Android Permissions (AndroidManifest.xml)
Location: `src-tauri/gen/android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.CAMERA"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.USE_BIOMETRIC"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    <uses-permission android:name="android.permission.VIBRATE"/>
</manifest>
```

### iOS Permissions (Info.plist)
Location: `src-tauri/Info.ios.plist`

```xml
<plist version="1.0">
<dict>
    <key>NSCameraUsageDescription</key>
    <string>Camera access for scanning</string>
    <key>NSLocationWhenInUseUsageDescription</key>
    <string>Location for local features</string>
    <key>NSFaceIDUsageDescription</key>
    <string>Face ID for authentication</string>
</dict>
</plist>
```
