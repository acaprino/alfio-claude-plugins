# Debugging Mobile (Android + iOS)

The full debug surface for Tauri 2 mobile apps: WebView inspector on both platforms, Rust panic extraction from device logs, store crash log analysis, and decision trees for the symptoms that recur.

`testing.md` covers the emulator + ADB happy path; this file is what you reach for when something is actually broken.

## When to use

A device is showing a white screen, a crash without a visible stack, a deep link that does nothing, an IPC call that hangs, or a Play Console / TestFlight crash report that needs symbolication.

## WebView inspector

### Android (Chrome DevTools)

WebView is debuggable by default in Tauri **debug** builds. Release builds have it disabled. To attach:

1. Plug the device or boot the emulator, app running.
2. Chrome -> `chrome://inspect/#devices` -> wait for the WebView to appear -> click "inspect".
3. Standard Chrome DevTools panel attaches: Elements, Console, Network, Sources, Performance.

Gotchas:
- **Empty list**: the device must have USB debugging on AND the app must be a debug build. Release APKs ship with `setWebContentsDebuggingEnabled(false)`.
- **"WebView" appears but inspect fails on first click**: Chrome downloads matching DevTools shards on demand; needs network. Behind a proxy you may need `--proxy-server` flags or a Chrome restart.
- **Two WebViews listed**: if you also have Chrome Custom Tabs in the app (e.g. OAuth), both show up. Identify yours by the URL or the package name on the entry.

### iOS (Safari Web Inspector)

WKWebView is inspectable on **debug** builds and on Simulator unconditionally. Release builds (App Store) are not inspectable.

1. On the device: Settings -> Safari -> Advanced -> **Web Inspector** ON.
2. On the Mac: Safari -> Settings -> Advanced -> **Show Develop menu** ON.
3. Plug the device (or run the Simulator), app open.
4. Safari -> Develop -> `<device name>` -> the Tauri view appears in the submenu -> click it.

Gotchas:
- **Develop menu has the device but no view**: the WKWebView hasn't fully loaded yet, or the app is in release mode. Force a reload, or rebuild with `--debug`.
- **Console messages from `console.log` not appearing**: WKWebView in some iOS versions filters by log level by default; toggle the level filter at the top of the console pane.
- **"Couldn't connect to inspector"** after a code reload: Safari sometimes loses the connection on HMR. Close the inspector window and reopen from the Develop menu.

## Rust panic extraction from device

Mobile crashes from Rust code surface as native-side panics. They are not visible in the WebView console.

### Android

Tauri pipes Rust `println!` / `eprintln!` to logcat tag `RustStdout` / `RustStderr`. Panics go to stderr.

```bash
# Tail panics only
adb logcat -c && adb logcat *:S RustStderr:V

# Full backtrace requires RUST_BACKTRACE in the app process env.
# In src-tauri/src/lib.rs, before tauri::Builder:
std::env::set_var("RUST_BACKTRACE", "1");

# Then logcat will show the symbolicated backtrace if symbols are present.
```

Release builds strip symbols by default. To get readable backtraces from a release-mode bug:

```toml
# src-tauri/Cargo.toml
[profile.release]
debug = 1          # line tables only (smaller than full debug)
strip = false      # don't strip the .so
```

The .so files live under `src-tauri/gen/android/app/build/intermediates/merged_native_libs/<variant>/out/lib/<abi>/`. Use `addr2line` from the NDK to map raw addresses if a stripped backtrace shows hex offsets:

```bash
$ANDROID_HOME/ndk/<version>/toolchains/llvm/prebuilt/<host>/bin/llvm-addr2line \
  -e libapp_lib.so -f -C 0x<offset>
```

### iOS

Rust panics on iOS go through `os_log` -> Console.app. Wire them up in `lib.rs`:

```rust
#[cfg(target_os = "ios")]
{
    std::env::set_var("RUST_BACKTRACE", "1");
}
```

Then on the Mac: open **Console.app**, select the device or Simulator, filter by your bundle id. For Simulator only:

```bash
xcrun simctl spawn booted log stream --level=debug --predicate 'processImagePath CONTAINS "<your-app-name>"'
```

For symbolication of release crashes you need the `.dSYM` from `src-tauri/gen/apple/build/...` -- keep it with every build, App Store Connect requires it for crash reports.

## Store crash logs

### Play Console (Android)

`Quality -> Android vitals -> Crashes & ANRs` shows aggregated stack traces. Two preconditions for them to be readable:

1. **Upload the R8 / ProGuard mapping file** for each release build. Tauri release builds don't enable R8 by default, but if you turned it on, the file is at `src-tauri/gen/android/app/build/outputs/mapping/<variant>/mapping.txt`. Upload via Play Console -> the release -> "Upload" under "Native debug symbols and ReTrace mapping".
2. **Upload native debug symbols** (the unstripped `.so`) under the same panel. Without them, native frames show only library + offset.

Common symptoms in Play Console:
- `SIGSEGV` in `libapp_lib.so` -- almost always a Rust UB or a panic that aborted; check the line under symbol `rust_panic` if symbols uploaded.
- `ANR in WebView` -- main thread blocked by a sync IPC call; switch the command to `async fn` or move work to a thread.

### TestFlight / App Store Connect (iOS)

`Xcode -> Window -> Organizer -> Crashes` pulls crash logs from devices that opted in. Symbolication is automatic if the `.dSYM` is in your archive.

If a crash log shows only hex addresses for your binary:

```bash
# Inside the .xcarchive
xcrun atos -arch arm64 -o YourApp.app/YourApp -l 0x<load-address> 0x<crash-address>
```

The `.dSYM` for the Rust static lib is generated by Xcode when "Debug Information Format" is "DWARF with dSYM File". Confirm in `gen/apple/<scheme>.xcodeproj` build settings.

## Network inspection on mobile

WebView and Rust HTTP traffic both go through the device's network stack, so a system-level proxy intercepts both.

### Android

```bash
# Set proxy on emulator to host machine (mitmproxy / Charles default port 8080)
adb shell settings put global http_proxy 192.168.x.x:8080
# Clear when done
adb shell settings put global http_proxy :0
```

**TLS pinning blocker (Android 7+)**: the system trust store does not honour user-installed CAs by default. To accept the proxy CA in your debug build, add `network_security_config.xml`:

```xml
<!-- src-tauri/gen/android/app/src/main/res/xml/network_security_config.xml -->
<network-security-config>
  <debug-overrides>
    <trust-anchors>
      <certificates src="user" />
      <certificates src="system" />
    </trust-anchors>
  </debug-overrides>
</network-security-config>
```

Reference it in `AndroidManifest.xml` -> `<application android:networkSecurityConfig="@xml/network_security_config">`. The `<debug-overrides>` block applies only to debuggable builds, so it doesn't ship to production.

### iOS

Set the proxy under Settings -> Wi-Fi -> the network -> HTTP Proxy -> Manual. Trust the proxy CA via Settings -> General -> About -> Certificate Trust Settings (iOS hides this until a CA is installed via profile). Simulator: `xcrun simctl keychain booted add-root-cert <cert.pem>`.

App Transport Security blocks plaintext by default; if you need to talk to a non-HTTPS dev backend through the proxy, add an exception in `Info.plist` (debug builds only).

## Troubleshooting decision trees

### "White screen on launch"

1. **Frontend bundle reachable?** `tauri android dev` prints the dev URL -- visit it from the device's browser. If it loads, the bundle is fine and the issue is in the WebView. If not, see `setup-mobile.md` for `TAURI_DEV_HOST` / Vite host config.
2. **WebView console empty?** Open Chrome / Safari inspector. A blank console usually means JS threw before any log -- check the Errors tab. A "Refused to load" CSP error is the most common.
3. **CSP error?** `tauri.conf.json` -> `app.security.csp` -- the dev server origin must be in `connect-src` or unset (`null`) for development.
4. **Logcat shows panic at startup?** A Rust `setup` hook panicked; the WebView never gets HTML. Find the panic via `RustStderr` (see above).
5. **Stale `.so` embedding old frontend?** This is the most common Android-only "white screen" cause once the basics check out. The `.so` was rebuilt against an old `dist/` because `tauri-build` only watches the directory path, not file contents (Cargo's directory-form `rerun-if-changed` misses content modifications). One-shot bypass: `touch src-tauri/src/lib.rs` then rebuild. Real fix: walk the frontend dir in `build.rs`. Full architecture and the Gradle safety net in `mobile-stale-builds.md`.

### "Frontend changes don't appear in the app"

You changed the frontend, ran `tauri android dev` or `tauri android build --debug`, the build succeeded, but the device still shows old UI. Walk this in order:

1. **Did Gradle rebuild the Rust crate?** Inspect the build log for `:app:rustBuildArm64Debug` (or the arch you target). If it says `SKIPPED`, Cargo decided the crate had no changes. This is the canonical stale-`.so` symptom.
2. **Touch `src-tauri/src/lib.rs` and rebuild.** If the device now shows the new UI, the diagnosis is confirmed: Cargo is not tracking your frontend dir as a dependency. Apply the `build.rs` walk pattern in `mobile-stale-builds.md` (Tier 1) so this stops happening on every change.
3. **Verify `tauri.conf.json` `build.frontendDist`** points at the dir `vite build` actually writes to. If you renamed `dist/` to `public-react/` without updating the config, every build embeds an empty / stale bundle.
4. **Check for two competing build outputs.** A common multi-crate trap: two different `Cargo.toml` files referencing different `frontendDist` paths, only one of which is current. `cargo metadata` and `grep -r frontendDist src-tauri/` resolve this.
5. **Cache reset escalation** (smallest hammer first): `cargo clean` inside `src-tauri/` -> `./gradlew clean` inside `src-tauri/gen/android/` -> `rm -rf src-tauri/gen/android/app/build/`. After this, if the next build still embeds stale assets, the bug is in your `build.rs`, not the cache.
6. **Dev mode versus build mode**: `tauri android dev` serves assets directly from the `.so` (Rust handler). `--debug` / `--apk` builds serve via `WebViewAssetLoader` from APK files. Both fail if the `.so` is stale, but for different reasons. See `mobile-stale-builds.md` for the dev/build mode distinction and the `RustWebViewClient.kt` patch for Windows hosts that cannot cross-compile.

### "Deep link not firing"

1. **Manifest configured?** Check `src-tauri/gen/android/app/src/main/AndroidManifest.xml` for the `<intent-filter>` with `<data android:scheme="myapp">`. Run `npm run tauri android init` again if the plugin was added after init.
2. **Plugin permission granted?** `capabilities/default.json` must include `deep-link:default`.
3. **Listener wired?** `onOpenUrl` must be registered before the app finishes mounting; if registered late, the launching URL is lost. Register synchronously in your top-level setup.
4. **Test the intent directly**: `adb shell am start -W -a android.intent.action.VIEW -d "myapp://test/path" com.your.app.identifier`. If this fires the listener, the URL source (browser, email) is the problem.
5. **iOS universal links silent?** `apple-app-site-association` must be served at `https://<domain>/.well-known/apple-app-site-association` with `Content-Type: application/json` and the correct team-id + bundle-id. Test with: `curl -I https://<domain>/.well-known/apple-app-site-association`.

### "Build OK but install fails"

| Error | Fix |
|---|---|
| `INSTALL_FAILED_ALREADY_EXISTS` | `adb install -r -d <apk>` or `adb uninstall com.your.app.identifier` |
| `INSTALL_FAILED_VERSION_DOWNGRADE` | The installed build has a higher `versionCode`. Bump in `tauri.conf.json -> bundle.android.versionCode` or `adb uninstall` first |
| `INSTALL_FAILED_INSUFFICIENT_STORAGE` | Emulator disk full; `adb shell pm trim-caches 1G` or recreate the AVD |
| `INSTALL_FAILED_NO_MATCHING_ABIS` | Built for the wrong arch; `cargo tauri android build --target <aarch64\|x86_64>` matching the emulator |
| `Failed to finalize session: INSTALL_PARSE_FAILED_NO_CERTIFICATES` | Release APK installed without signing. Use `--debug` for local install or sign properly |

### "HMR breaks after reconnect"

WebSocket survives only as long as `adb reverse` is alive. Sequence: `adb kill-server` -> `adb start-server` -> close the app on the device -> `cargo tauri android dev` again. If it still fails, the emulator's network stack needs a cold reset (close the AVD, not just the app).

### "IPC call hangs forever"

1. **Tracing**: temporarily add `tracing_subscriber::fmt::init()` at the top of `lib.rs` and `RUST_LOG=tauri=trace,my_crate=debug` -- you'll see every command entering and exiting.
2. **Async commands blocked on `block_on`?** A common bug: an `async fn` command awaiting a Mutex held by another sync command. Switch to `tokio::sync::Mutex`.
3. **Channel never drained?** `Channel<T>` Stops emitting if the JS-side handler throws. Wrap the `onmessage` handler in try/catch.
4. **Reply too large?** Tauri's IPC has practical size limits per message; payloads above a few MB stall. Stream via `Channel<T>` instead of returning a single `Vec<u8>`.

## ANR detection (Android)

App Not Responding triggers when the main thread is blocked > 5s. Causes in Tauri:
- A synchronous Tauri command doing heavy CPU work (`#[tauri::command] fn x() -> ...`). Mark it `async` or use `tauri::async_runtime::spawn_blocking`.
- A long-running JS handler invoked from a UI event. Profile with the Performance panel in DevTools.
- File IO on the main thread; use `tokio::fs` or move to a worker.

`adb shell dumpsys cpuinfo | grep <package>` shows main-thread CPU; sustained 100% during interaction is the signal.

## Memory profiling pointers

- **Android Studio Profiler**: Run -> Profile -> select the device process. Memory tab tracks Java + native heap. Capture a heap dump while the bug is reproducible.
- **Xcode Instruments**: Product -> Profile -> Allocations / Leaks. WKWebView memory is reported under WebKit; Rust memory is part of the app process.
- Tauri-specific leaks usually trace to `AppHandle` clones held in long-lived tasks or `State<T>` containing `Vec`/`HashMap` that grow without bound.

## Logging plugin

`tauri-plugin-log` is the production-grade alternative to `println!`. Add via `npm run tauri add log`. Output goes to:
- Android: `logcat` tag matching your bundle id, plus a rotating file under the app's data dir.
- iOS: `os_log` plus a rotating file under the app's `Documents/`.

Configure level + targets in `lib.rs`:

```rust
.plugin(
    tauri_plugin_log::Builder::new()
        .level(log::LevelFilter::Info)
        .targets([
            tauri_plugin_log::Target::new(tauri_plugin_log::TargetKind::Stdout),
            tauri_plugin_log::Target::new(tauri_plugin_log::TargetKind::LogDir { file_name: None }),
        ])
        .build(),
)
```

For Sentry / Bugsnag, integrate at the JS layer first (their SDKs cover WebView crashes and unhandled promise rejections); the Rust side is harder because no first-class crate ships a Tauri integration yet -- a `panic_hook` that POSTs to your endpoint is the typical workaround.

## Official docs

- WebView debugging in Chrome DevTools: https://developer.chrome.com/docs/devtools/remote-debugging/webviews
- Safari Web Inspector: https://developer.apple.com/documentation/safari-developer-tools/inspecting-ios
- ANR diagnosis: https://developer.android.com/topic/performance/vitals/anr
- Play Console crash mapping: https://support.google.com/googleplay/android-developer/answer/9848633
- TestFlight crash logs: https://developer.apple.com/documentation/xcode/diagnosing-issues-using-crash-reports-and-device-logs
- `tauri-plugin-log`: https://v2.tauri.app/plugin/logging/

## Related

- `mobile-stale-builds.md` -- the stale-`.so` Cargo tracking gap; required reading for any "frontend change not visible" bug
- `testing.md` -- emulator + ADB recipes (the happy path)
- `setup-mobile.md` -- toolchain prerequisites
- `build-deploy-mobile.md` -- signing, store builds, R8, dSYM
- `ipc-streaming.md` -- IPC architecture, the source of most "stuck" bugs
- `plugins-mobile.md` -- mobile plugin APIs being debugged
