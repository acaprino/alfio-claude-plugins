# CI/CD for Tauri Applications

Provider-agnostic notes on what makes a Tauri pipeline different from a generic Node app build.

## When to use

Designing or auditing a CI pipeline that produces Tauri installers/bundles. For mobile-specific CI (signing, store upload, 16KB page size), continue to `ci-cd-mobile.md`.

## OS matrix (cannot be flattened)

| Target | Runner OS | Notes |
|--------|-----------|-------|
| Windows (.msi/.nsis) | Windows | WebView2 bundled or bootstrapped at install |
| macOS (.dmg/.app) | macOS | codesign + notarization required for distribution |
| Linux (.AppImage/.deb) | Ubuntu | needs `libwebkit2gtk-4.1-dev` |
| Android (.apk/.aab) | Ubuntu | Android SDK + NDK; can build on Linux |
| iOS (.ipa) | macOS | Xcode required, no Linux/Windows alternative |

Always run platforms in parallel jobs -- a serial matrix wastes hours.

## Gotchas

- **Don't ship debug builds by accident.** Without an explicit release profile, binaries are 10-50x larger and noticeably slower. Set in `Cargo.toml`:
  ```toml
  [profile.release]
  lto = true
  opt-level = "s"      # "3" if you optimize for speed over size
  codegen-units = 1
  strip = true
  panic = "abort"
  ```
- **Cache `src-tauri/target/` aggressively.** Key on `Cargo.lock` hash + Rust toolchain version + OS. Cache size 500MB-2GB; Rust rebuilds without it take 20+ minutes.
- **Signing secrets as base64.** Store keystores, .p12, .p8 as base64-encoded CI secrets (`base64 -i file | tr -d '\n'`) and decode at build time to a temp path. Never commit credentials.
- **`tauri-apps/tauri-action`** is the path of least resistance on GitHub Actions for desktop builds (auto-uploads to a draft release). On other CIs you call `tauri build` directly and upload `src-tauri/target/release/bundle/*` yourself.
- **Updater signing key.** `TAURI_SIGNING_PRIVATE_KEY` + `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` are required if you ship the updater plugin -- builds without them succeed but produce unsigned `.json` manifests that the updater will refuse.

## Artifact paths cheat sheet

| Platform | Bundle output |
|----------|---------------|
| Windows / macOS / Linux | `src-tauri/target/release/bundle/` |
| Android | `src-tauri/gen/android/app/build/outputs/` |
| iOS | `src-tauri/gen/apple/build/` |

## Official docs

- Tauri CI/CD guide: https://v2.tauri.app/distribute/pipelines/
- `tauri-action`: https://github.com/tauri-apps/tauri-action
- Code signing per platform: https://v2.tauri.app/distribute/sign/
- Auto-updater + key generation: https://v2.tauri.app/plugin/updater/

## Related

- `ci-cd-mobile.md` -- Android keystore, App Store Connect API, store upload, 16KB page size
- `build-deploy-desktop.md` -- desktop signing/notarization details
- `build-deploy-mobile.md` -- Android/iOS bundle gotchas the CI inherits
