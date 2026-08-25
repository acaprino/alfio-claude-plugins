# Tauri 2 Core Plugins

Universal plugins (work on desktop AND mobile). For mobile-only plugins (biometric, haptics, nfc, barcode-scanner), see `plugins-mobile.md`.

## When to use

Choosing which plugin to add for a capability you need (filesystem, HTTP, store, SQL, deep links, dialogs, etc.) and registering it correctly.

## Universal plugin matrix

| Plugin | Desktop | Mobile | Use for |
|--------|---------|--------|---------|
| `fs` | yes | yes | File read/write (use `BaseDirectory.AppData` for cross-platform) |
| `http` | yes | yes | HTTP client that bypasses CORS (vs browser fetch) |
| `notification` | yes | yes | OS notifications |
| `clipboard-manager` | yes | yes | Clipboard read/write |
| `dialog` | yes | yes | Native open/save/message dialogs |
| `opener` | yes | yes | Open URL in system browser (preferred for OAuth) |
| `store` | yes | yes | Persistent key-value (JSON file under app data) |
| `sql` | yes | yes | SQLite |
| `log` | yes | yes | Structured logging to stdout/file/webview |
| `os` | yes | yes | Platform/arch detection |
| `deep-link` | yes | yes | Custom URL scheme handling |

Add via `npm run tauri add <name>` -- it patches Cargo.toml, package.json, and capabilities in one shot.

## Gotchas

- **Adding the plugin in `lib.rs` is half the job.** You also need the JS package (`npm i @tauri-apps/plugin-<name>`) AND the permission entry in `capabilities/default.json`. `tauri add` does all three; manual installs forget #3 every time.
- **`opener` vs `shell` for OAuth.** Use `opener::openUrl` for OAuth/external links -- it invokes the OS default browser. The `shell` plugin's `open` works on desktop but is more permissive than necessary and adds attack surface. Google specifically blocks OAuth in WebViews (see `authentication.md`).
- **`tauri-plugin-store` is async-by-default.** `await store.save()` is required after `set` to actually flush to disk -- without it the app exits and writes are lost.
- **`tauri-plugin-log` colors break on Windows terminals** that don't support ANSI codes -- gate `with_colors` behind `cfg!(debug_assertions)` if you ship CLI users.
- **`tauri-plugin-sql` migrations live in a `migrations` Vec** at builder time, not in app code. Adding migrations after launch requires a release.

## Minimal lib.rs registration shape

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_log::Builder::new().build())
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("error");
}
```

## Deep-link config (desktop)

```json
// tauri.conf.json
"plugins": {
  "deep-link": { "desktop": { "schemes": ["myapp"] } }
}
```

For mobile deep-link config (Android Intent Filters, iOS Associated Domains), see `plugins-mobile.md`.

## Official docs

- Plugin index: https://v2.tauri.app/plugin/
- Per-plugin permission reference: each page has a "Permissions" section, e.g. https://v2.tauri.app/plugin/file-system/#permissions
- `tauri add` CLI: https://v2.tauri.app/reference/cli/#add
- Awesome Tauri (community plugins): https://github.com/tauri-apps/awesome-tauri

## Related

- `plugins-mobile.md` -- biometric, barcode, haptics, nfc, geolocation
- `frontend-patterns.md` -- JS-side usage examples for these plugins
- `authentication.md` -- why `opener` matters for OAuth
- `shell-plugin.md` -- when to reach for `shell` instead of `opener`
