# Testing with Emulator and ADB

## Emulator Setup

### Create Optimized Emulator
Android Studio → Device Manager → Create Device

**Recommended configuration:**
```
Device: Pixel 7 Pro
System Image: API 34 (Android 14) x86_64 with Google Play
RAM: 4096 MB
VM Heap: 512 MB
Internal Storage: 8 GB
```

### Verify Hardware Virtualization
```bash
# Linux (KVM)
egrep -c '(vmx|svm)' /proc/cpuinfo  # must be > 0
sudo apt install qemu-kvm
kvm-ok

# macOS Intel: HAXM included with Android Studio
# macOS Apple Silicon: native ARM64 emulation
# Windows: enable Hyper-V or HAXM in BIOS
```

### Start Emulator from CLI
```bash
# List available emulators
emulator -list-avds

# Start with GPU acceleration
emulator -avd Pixel_7_Pro_API_34 -gpu host

# Headless for CI
emulator -avd Pixel_7_Pro_API_34 -no-window -no-audio

# Optimized network
emulator -avd Pixel_7_Pro_API_34 -gpu host -netdelay none -netspeed full
```

## ADB Connection

```bash
# List connected devices
adb devices -l

# If emulator not detected, restart ADB
adb kill-server
adb start-server
adb devices
```

## Development Commands

```bash
# Dev on emulator (auto-detect)
cargo tauri android dev

# Select specific device
cargo tauri android dev --device emulator-5554

# Force IP selection prompt
cargo tauri android dev --force-ip-prompt
```

**Important:** When prompted for IP, select your LAN address (e.g., `192.168.1.x`), NOT `127.0.0.1`.

## ADB Commands

### APK Installation
```bash
# Build debug APK
cargo tauri android build --debug

# Install (replace existing)
adb install -r src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk

# Force reinstall
adb install -r -d app-universal-debug.apk

# Uninstall
adb uninstall com.your.app.identifier

# Clear app data
adb shell pm clear com.your.app.identifier
```

### Logcat (View Logs)
```bash
# Tauri filtered logs
adb logcat | grep -iE "(tauri|RustStdout|WebView)"

# Rust logs only
adb logcat | grep "RustStdout"

# Clear and start fresh
adb logcat -c && adb logcat | grep -i tauri

# With timestamp
adb logcat -v time | grep -i tauri

# Save to file
adb logcat -v time > debug_$(date +%Y%m%d_%H%M%S).log

# Errors/warnings only
adb logcat "*:W" | grep -i tauri

# Better tool with colors
pip install pidcat
pidcat com.your.app.identifier
```

### App Management
```bash
# Force stop
adb shell am force-stop com.your.app.identifier

# Start app
adb shell am start -n com.your.app.identifier/.MainActivity

# Restart
adb shell am force-stop com.your.app.identifier && \
adb shell am start -n com.your.app.identifier/.MainActivity
```

### Shell & File System
```bash
# Interactive shell
adb shell

# Access app data (debug builds only)
adb shell run-as com.your.app.identifier ls /data/data/com.your.app.identifier/

# Copy files
adb pull /sdcard/Download/file.txt ./
adb push ./config.json /sdcard/Download/

# Screenshot
adb shell screencap /sdcard/screenshot.png && adb pull /sdcard/screenshot.png ./

# Screen recording (max 3 min)
adb shell screenrecord /sdcard/recording.mp4
# Ctrl+C to stop
adb pull /sdcard/recording.mp4 ./
```

### Network & Ports
```bash
# Forward PC port to device
adb forward tcp:8080 tcp:8080

# Reverse (device to PC, useful for local APIs)
adb reverse tcp:3000 tcp:3000

# List forwards
adb forward --list

# Remove all
adb forward --remove-all
```

## Chrome DevTools for WebView

1. Start app on emulator
2. Open Chrome on PC → `chrome://inspect/#devices`
3. Find device, click "inspect" on WebView

## Testing Specific Features

### Permissions
```bash
# Grant permission
adb shell pm grant com.your.app.identifier android.permission.CAMERA

# Revoke (to test request flow)
adb shell pm revoke com.your.app.identifier android.permission.CAMERA

# List app permissions
adb shell dumpsys package com.your.app.identifier | grep permission
```

### Deep Links
```bash
# Custom scheme
adb shell am start -W -a android.intent.action.VIEW \
  -d "myapp://open/screen" com.your.app.identifier

# Universal link
adb shell am start -W -a android.intent.action.VIEW \
  -d "https://app.example.com/open"
```

### IAP on Emulator
Requirements:
1. Emulator with Google Play (not just "Google APIs")
2. Google account configured as license tester
3. App published in internal testing track

```bash
# Verify Google Play present
adb shell pm list packages | grep vending

# Clear Play Store cache if issues
adb shell pm clear com.android.vending
```

## Troubleshooting

### "No available Android Emulator detected"
```bash
adb devices                    # Verify emulator running
echo $ANDROID_HOME            # Check env vars
adb kill-server && adb start-server
emulator -avd YOUR_AVD_NAME & # Start manually
sleep 15
cargo tauri android dev
```

### "INSTALL_FAILED_ALREADY_EXISTS"
```bash
adb uninstall com.your.app.identifier
# or
adb install -r -d app-universal-debug.apk
```

### Frontend not loading / Connection timeout
```bash
# Check your IP
ip addr | grep "inet "        # Linux
ipconfig | findstr IPv4       # Windows

# Open firewall
sudo ufw allow 5173
sudo ufw allow 5174

# Test from device
adb shell curl http://192.168.1.100:5173

# Vite must show: Network: http://192.168.x.x:5173/
```

### HMR not working
```bash
# Reverse WebSocket port
adb reverse tcp:5174 tcp:5174

# Full restart:
# 1. Close emulator
# 2. Close Vite
# 3. adb kill-server
# 4. Start emulator
# 5. cargo tauri android dev
```

### Slow builds
```bash
# Use specific target
cargo tauri android build --target aarch64

# Enable incremental in Cargo.toml
[profile.dev]
incremental = true

# Use sccache
cargo install sccache
export RUSTC_WRAPPER=sccache
```

## Automation Script (Justfile)

```makefile
emu:
    emulator -avd Pixel_7_Pro_API_34 -gpu host &

dev:
    cargo tauri android dev

debug:
    cargo tauri android build --debug
    adb install -r src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk

log:
    adb logcat -c && adb logcat | grep -iE "(tauri|RustStdout)"

shot:
    @mkdir -p screenshots
    adb shell screencap /sdcard/shot.png
    adb pull /sdcard/shot.png ./screenshots/$(shell date +%s).png

restart:
    adb shell am force-stop com.your.app.identifier
    adb shell am start -n com.your.app.identifier/.MainActivity

clean:
    rm -rf src-tauri/gen/android
    cargo tauri android init
```
