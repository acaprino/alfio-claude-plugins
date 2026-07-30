# Testing with Emulator and ADB

Practical recipes for testing Tauri 2 mobile apps on an Android emulator. iOS simulator is mostly Xcode-driven and doesn't need a separate guide.

## When to use

Iterating on Android in `tauri android dev`, debugging WebView issues, scripting install/log/screenshot/restart cycles, or tracking down "works on the emulator, breaks on a real device" issues.

## Emulator + ADB sanity checklist

1. AVD created in Android Studio (Pixel 7 Pro, API 34, x86_64 + Google Play, 4GB RAM is the safe default).
2. `adb devices -l` lists it.
3. `cargo tauri android dev` finds it without `--device`.
4. If not: `adb kill-server && adb start-server` and retry.

## Gotchas

- **`--force-ip-prompt` and pick the LAN IP, not 127.0.0.1.** Tauri offers a list of network interfaces; selecting localhost makes the emulator reach itself, not your dev server, and the WebView shows blank. The LAN IP (`192.168.x.x`) is what you want even on the emulator.
- **Vite must print `Network: http://192.168.x.x:5173/`.** If you only see `Local`, you forgot to honour `TAURI_DEV_HOST` in `vite.config.ts` (see `setup-mobile.md`). The emulator can't reach `localhost`.
- **HMR not working on the device?** `adb reverse tcp:5174 tcp:5174` exposes the WebSocket port back. If still broken, full restart: emulator → Vite → `adb kill-server` → start emulator → `cargo tauri android dev`.
- **Logcat is noisy.** Tauri-relevant filter: `adb logcat | grep -iE "(tauri|RustStdout|WebView)"`. Just Rust prints: `adb logcat | grep "RustStdout"`. With timestamps: `-v time`.
- **`adb install` after a previous install fails with `INSTALL_FAILED_ALREADY_EXISTS`.** Use `-r -d` (reinstall, allow downgrade) or `adb uninstall com.your.app.identifier` first.
- **IAP doesn't work on emulators without Google Play.** The "Google APIs" image is not enough -- pick "Google Play" explicitly when creating the AVD. Verify with `adb shell pm list packages | grep vending`.
- **Hardware virtualization missing = 5x slower.** Linux: `egrep -c '(vmx|svm)' /proc/cpuinfo` must be > 0, install `qemu-kvm`. Windows: enable Hyper-V or HAXM in BIOS.
- **Slow Rust builds**: `cargo tauri android build --target aarch64` skips the x86 / armv7 builds; combine with `sccache` for ~50% speedup on incremental rebuilds.
- **WebView DevTools**: open Chrome → `chrome://inspect/#devices` → click "inspect" on your app's WebView. The standard Chrome inspector attaches.

## The five commands worth aliasing

```bash
# Start dev cycle
cargo tauri android dev

# Tail Tauri-only logs
adb logcat -c && adb logcat | grep -iE "(tauri|RustStdout)"

# Reinstall debug APK without uninstalling
adb install -r src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk

# Force restart the app (faster than reinstall)
adb shell am force-stop com.your.app.identifier && \
  adb shell am start -n com.your.app.identifier/.MainActivity

# Test deep link
adb shell am start -W -a android.intent.action.VIEW -d "myapp://open/screen" com.your.app.identifier
```

## Permissions during dev

```bash
adb shell pm grant com.your.app.identifier android.permission.CAMERA
adb shell pm revoke com.your.app.identifier android.permission.CAMERA   # to test request flow
```

## Official docs

- Android emulator CLI: https://developer.android.com/studio/run/emulator-commandline
- ADB reference: https://developer.android.com/tools/adb
- WebView debugging in Chrome DevTools: https://developer.chrome.com/docs/devtools/remote-debugging/webviews
- pidcat (better logcat with colors): https://github.com/JakeWharton/pidcat
- Tauri Android dev guide: https://v2.tauri.app/develop/#android

## Related

- `setup-mobile.md` -- the toolchain underneath this
- `build-deploy-mobile.md` -- moving from emulator to real device + signing
- `plugins-mobile.md` -- the plugins you're testing on the emulator
