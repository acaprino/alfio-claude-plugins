# Mobile Stale Builds (Android)

The single most expensive bug in Tauri 2 mobile Android development: the APK ships an old frontend bundle even though `vite build` regenerated `dist/` and Gradle reports a successful build. Hours get burned debugging "phantom" UI bugs that are just stale assets baked into a stale `.so`.

## When to use

You changed the frontend, ran `tauri android dev` or `tauri android build --debug`, the build finished green, but the device shows old UI. The Gradle log says `:app:rustBuildArm64Debug SKIPPED` (or similar). Or you suspect any "the change didn't reach the device" symptom.

For the Windows-host cross-compilation chain (Strawberry Perl, OpenSSL, RustWebViewClient.kt patch), see `build-deploy-mobile.md`. That trail is a different problem domain (the `.so` was never produced fresh because cross-compile failed); this file covers the case where cross-compile succeeded but Cargo reused a cached `.so`.

## The bug architecture

`tauri::generate_context!()` expands `include_dir!` / `include_bytes!` macros at compile time, embedding the files referenced by `build.frontendDist` into `libapp_lib.so`. Cargo only rebuilds the crate when it sees a change to a tracked dependency. The chain has two known weaknesses.

**Weakness 1: tauri-build only watches the directory path, not file contents.**
PR [tauri-apps/tauri#8756](https://github.com/tauri-apps/tauri/pull/8756) (merged 2024-02-04, present in all 2.x releases) added one line to `tauri-build/src/lib.rs`:
```rust
if dist_path.exists() {
    println!("cargo:rerun-if-changed={}", dist_path.display());
}
```
This emits `rerun-if-changed` for the `dist/` directory itself, not for the files inside it.

**Weakness 2: Cargo's directory watch misses file modifications.**
Per the [Cargo book](https://doc.rust-lang.org/cargo/reference/build-scripts.html#change-detection) and [cargo#2599](https://github.com/rust-lang/cargo/issues/2599): when `rerun-if-changed` points to a directory, Cargo checks only the directory's own mtime. The directory mtime updates when entries are added or deleted, not when the contents of an existing file change. So `vite build` overwriting `dist/index.html` and `dist/assets/index-XXX.js` produces no mtime change on `dist/` itself, Cargo decides nothing changed, and the cached `.so` from the previous run is reused.

**No upstream API exists** to register a watch directory. The `tauri_build::Attributes` struct has methods for capabilities, codegen, plugins, and the app manifest, but nothing for `frontendDist` watching. The `capabilities_path_pattern()` docs explicitly note: "You must emit rerun-if-changed instructions for your capabilities directory." The pattern is delegated to user `build.rs`.

The result: touching `lib.rs` (or any other `.rs` file) is the only thing that reliably invalidates Cargo's cache, but that is a manual workaround, not a fix. The clean fix lives in `build.rs`.

## Tier 1: build.rs walk pattern (the correct fix)

Add a recursive walk of the frontend dist directory in `src-tauri/build.rs`. Emit two kinds of `rerun-if-changed` directive:

- The directory itself: catches `add` / `delete` of files (covers new chunks from `vite build`'s content-hashed filenames).
- Each file inside the directory: catches modifications to existing files (covers `index.html` rewrites and any non-content-hashed asset).

Both are needed. The directory form alone misses content edits; the per-file form alone misses additions. Cargo deduplicates internally, so the cost is just the walk.

```rust
// src-tauri/build.rs
use std::path::Path;

fn main() {
    // Frontend dist directory relative to this crate (src-tauri/).
    // Match build.frontendDist in tauri.conf.json.
    let frontend_dist = Path::new("..").join("dist");

    // Watch the directory itself: detects file ADD / DELETE.
    println!("cargo:rerun-if-changed={}", frontend_dist.display());

    // Walk recursively and emit per-file: detects MODIFICATIONS.
    if frontend_dist.exists() {
        emit_rerun_recursive(&frontend_dist);
    }

    tauri_build::build();
}

fn emit_rerun_recursive(dir: &Path) {
    let Ok(entries) = std::fs::read_dir(dir) else { return };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            emit_rerun_recursive(&path);
        } else {
            println!("cargo:rerun-if-changed={}", path.display());
        }
    }
}
```

Use `std::fs::read_dir` (zero deps) or pull in `walkdir = "2"` if your `build.rs` already uses it. Either works.

**Adjust the path** to match `tauri.conf.json`'s `build.frontendDist`. Common values:
- `../dist` (Vite default with the project at repo root)
- `../public-react` (custom output dir)
- `../../web/dist` (monorepo with `apps/web` and `apps/desktop/src-tauri`)

**Verify the fix worked.** After the next `vite build` + `tauri android build --debug`, the Gradle log should show `:app:rustBuildArm64Debug` actually executing instead of `SKIPPED`, and the cargo subprocess should print compilation lines for the Tauri crate.

## Tier 2: touch lib.rs (fallback only)

If you cannot edit `build.rs` for some reason (vendored crate, CI constraint), bumping the mtime of any `.rs` file in the crate forces Cargo to consider the crate changed:

```bash
# PowerShell
(Get-Item src-tauri\src\lib.rs).LastWriteTime = Get-Date

# Bash
touch src-tauri/src/lib.rs
```

This is a manual hack, not a workflow. It does not scale (you forget, you ship stale builds, hours lost). Use it once to confirm the diagnosis, then add the Tier 1 fix.

## Tier 3: Gradle safety net (verifyEmbeddedAssets)

Even with Tier 1 in place, a Gradle-level safety net is worth adding for two reasons: first, defense in depth catches regressions if someone accidentally touches `build.rs`; second, it surfaces the bug at build time with a readable error instead of silently producing a stale APK.

The safety net is a custom Gradle task that:
1. Reads the just-built `libapp_lib.so` from `jniLibs/<abi>/`.
2. Looks for a known reference into the embedded bundle (e.g., the content-hashed entry script name from `dist/index.html`, like `index-abc123.js`).
3. Fails the build if the reference is not found in the `.so`'s bytes.

Add to `src-tauri/gen/android/app/build.gradle.kts` (or a separate `frontend.build.gradle.kts` applied from it):

```kotlin
import java.io.File

tasks.register("verifyEmbeddedAssets") {
    description = "Fails if libapp_lib.so does not contain the current dist/ entry script."
    group = "verification"

    doLast {
        val distDir = rootProject.projectDir.parentFile.parentFile.resolve("dist")
        val indexHtml = distDir.resolve("index.html")
        if (!indexHtml.exists()) {
            error("[verifyEmbeddedAssets] $indexHtml missing. Run `npm run build` first.")
        }

        // Extract the entry script name from index.html (vite emits /assets/index-<hash>.js).
        val entry = Regex("""/assets/(index-[A-Za-z0-9_-]+\.js)""")
            .find(indexHtml.readText())
            ?.groupValues?.get(1)
            ?: error("[verifyEmbeddedAssets] No /assets/index-*.js reference in dist/index.html.")

        val jniLibs = layout.buildDirectory.dir("intermediates/merged_native_libs").get().asFile
        val sos = jniLibs.walkTopDown().filter { it.name == "libapp_lib.so" }.toList()
        if (sos.isEmpty()) error("[verifyEmbeddedAssets] No libapp_lib.so found under $jniLibs.")

        sos.forEach { so ->
            if (!containsBytes(so, entry.toByteArray(Charsets.UTF_8))) {
                error(
                    """
                    [verifyEmbeddedAssets] $so does not contain '$entry'.
                    The .so was built from an older dist/ snapshot. Cargo did not rebuild because its
                    rerun-if-changed tracking missed the frontend changes. Confirm src-tauri/build.rs
                    walks the frontend dist directory and emits rerun-if-changed for each file.
                    See the mobile stale-builds reference.
                    """.trimIndent()
                )
            }
        }
    }
}

// Byte-level substring scan: Kotlin's String.contains operates on charsets, not raw bytes.
fun containsBytes(file: File, needle: ByteArray): Boolean {
    file.inputStream().buffered().use { input ->
        val window = ByteArray(needle.size)
        var filled = 0
        var b = input.read()
        while (b != -1) {
            if (filled < needle.size) {
                window[filled++] = b.toByte()
            } else {
                System.arraycopy(window, 1, window, 0, needle.size - 1)
                window[needle.size - 1] = b.toByte()
            }
            if (filled == needle.size && window.contentEquals(needle)) return true
            b = input.read()
        }
    }
    return false
}
```

### Wire the task into the build

The task must run AFTER the `.so` is produced and BEFORE the APK is assembled. Tauri's Gradle plugin (in `src-tauri/gen/android/buildSrc/src/main/kotlin/RustPlugin.kt`) generates one `rustBuild<Arch><Profile>` task per architecture, plus a `rustBuildUniversal<Profile>` aggregate. Use `mustRunAfter` against those.

```kotlin
afterEvaluate {
    tasks.matching { it.name == "verifyEmbeddedAssets" }.configureEach {
        mustRunAfter(tasks.matching {
            it.name.startsWith("rustBuild") || it.name.startsWith("buildCargoNdk")
        })
    }

    // Hook into the merge step so verification runs before APK packaging.
    tasks.matching { it.name.startsWith("merge") && it.name.endsWith("JniLibFolders") }
        .configureEach {
            finalizedBy("verifyEmbeddedAssets")
        }
}
```

**Task name stability**: `rustBuild<Arch><Profile>` is generated programmatically in `RustPlugin.kt` and has been stable since Tauri 2.0 GA. The `<Arch>` segment comes from the `archList` template variable. The aggregate `rustBuildUniversal<Profile>` is the safest dependency target if you do not want to enumerate architectures.

**Caveat**: `ensureNativeLibs` and `syncFrontendAssets` are not Tauri-emitted tasks. If you see them in your `build.gradle.kts`, they are local additions from your project (or copied from a template) and their semantics depend on what your team wrote.

## Cache reset playbook

When the stale-build symptom hits and you need to break out of it, use the smallest hammer first:

| Symptom | Reset to apply |
|---|---|
| Frontend changes ignored, `rustBuild* SKIPPED` | Add Tier 1 to `build.rs`. As a one-shot bypass: `touch src-tauri/src/lib.rs`. |
| Tier 1 in place, still stale | `cargo clean` inside `src-tauri/`. Forces a full Rust recompile. Slow but surgical. |
| Cargo clean did not help | `cd src-tauri/gen/android && ./gradlew clean`. Wipes Gradle's intermediates including `merged_native_libs`. |
| Both clean commands did not help | `rm -rf src-tauri/gen/android/app/build/`. Nuclear: removes all Gradle output for the Android subproject. |
| Multi-arch APK shipping wrong arch's frontend | Ensure all `rustBuild<Arch>Debug` tasks ran. Check the Gradle log for SKIPPED on any arch. |
| Even nuclear did not help | Check `tauri.conf.json` for the `build.frontendDist` value. If you renamed the dir without updating the config, every build embeds an empty bundle. |

`adb install -r` (re-install) does not help with this bug: the APK content is already wrong before install. The fix is upstream of install.

## Dev mode (`tauri android dev`) versus build mode (`--debug`)

`tauri android dev` builds the `.so` in dev mode, where the Rust handler serves embedded assets from the `.so` rather than the WebView's `WebViewAssetLoader`. This makes the stale-asset symptom worse, because:

- In dev mode the `.so` IS the asset source. A stale `.so` directly shows stale UI.
- In build mode (`--debug` / `--apk` / `--aab`), the WebView's asset loader serves files from the APK, which Gradle does refresh. A stale `.so` may still cause issues (e.g., wrong `assetLoaderDomain`), but the assets the user sees come from the APK, not the `.so`.

Neither case is acceptable. Tier 1 fixes both. The Windows-only cross-compilation chain in `build-deploy-mobile.md` is a different (independent) failure mode where the dev-mode `.so` simply cannot be produced fresh on the host.

## References

- [PR tauri-apps/tauri#8756](https://github.com/tauri-apps/tauri/pull/8756): the upstream change adding directory-level `rerun-if-changed` for `frontendDist` (merged 2024-02-04, scope: directory only).
- [Cargo issue #2599](https://github.com/rust-lang/cargo/issues/2599): definitive proof that directory-form `rerun-if-changed` does not detect file content modifications.
- [Cargo book: Build Scripts / Change Detection](https://doc.rust-lang.org/cargo/reference/build-scripts.html#change-detection): canonical semantics.
- [tauri_build::Attributes](https://docs.rs/tauri-build/latest/tauri_build/struct.Attributes.html): confirms no public API for watch-dir registration.
- [RustPlugin.kt (Tauri dev branch)](https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-cli/templates/mobile/android/buildSrc/src/main/kotlin/RustPlugin.kt): source of the `rustBuild<Arch><Profile>` task naming convention.

## Related

- `build-deploy-mobile.md`: Windows-host cross-compile chain, RustWebViewClient.kt patch, signing, 16KB page size.
- `setup-mobile.md`: toolchain prerequisites, Vite config, NDK version selection.
- `debugging-mobile.md`: white-screen and "frontend not updating" decision trees that point back here.
