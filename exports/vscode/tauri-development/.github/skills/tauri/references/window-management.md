# Window Management

Multi-window, frameless, system tray, native menus, and global shortcuts. All standard Tauri API -- this file calls out the gotchas, not the surface.

## When to use

Adding a second window (settings, splash, overlay), system tray icon, native menu bar, or system-wide hotkey to a desktop app.

## When NOT to use

Mobile -- multi-window, tray, menus, and global shortcuts are desktop-only. Mobile apps have a single root window.

## Gotchas

- **Always check existence before creating.** `WebviewWindowBuilder::new(app, "settings", ...)` with a label that already exists throws -- you want `app.get_webview_window("settings").map(|w| w.set_focus())` first.
- **Frameless drag region is CSS, not config.** `-webkit-app-region: drag` on a div makes it the title bar; `no-drag` on buttons inside it lets clicks through. Forgetting `no-drag` makes minimize/close unusable.
- **Tray icon needs an explicit icon source.** `app.default_window_icon().unwrap().clone()` works; passing a path that doesn't exist gives no error and a blank tray slot.
- **Close-to-tray needs `api.prevent_close()` AND `window.hide()`.** Just preventing close leaves the window invisible-but-existing; the user can't bring it back without the tray menu.
- **Menu accelerators: `CmdOrCtrl`, not `Ctrl`.** Using `Ctrl` directly on macOS shows the wrong glyph and binds the wrong modifier. Always `CmdOrCtrl+S` for cross-platform.
- **`CheckMenuItem` state is *not* persisted** -- toggle handler must store + restore from your app state.
- **Global shortcuts can collide silently.** `register()` returns `Result` but a successful register on top of an existing OS-level binding may "win" in unpredictable ways. Document required hotkeys and let users override.
- **`onCloseRequested` fires per-window**, not for the whole app. If you want "quit on last window closed," check `app.webview_windows().len()` in the handler.
- **Window labels must be unique strings** that you'll hardcode across both Rust and JS -- there's no shared enum. A typo gives you `None` from `get_webview_window`.

## The check-then-create pattern (Rust)

```rust
if let Some(win) = app.get_webview_window("settings") {
    win.set_focus().map_err(|e| e.to_string())?;
    return Ok(());
}
WebviewWindowBuilder::new(&app, "settings", WebviewUrl::App("/settings".into()))
    .title("Settings").inner_size(600.0, 400.0).center().build()?;
```

## Capabilities for global-shortcut

```json
"permissions": [
  "core:default",
  "global-shortcut:allow-register",
  "global-shortcut:allow-unregister"
]
```

## Inter-window comm options

- Tauri events (`emit` / `listen`) -- broadcast or per-window with `get_webview_window("x").emit(...)`.
- Shared `tauri::State<T>` -- both windows read/write through commands. Better for large state; events are better for notifications.

## Official docs

- WebviewWindow API (Rust): https://docs.rs/tauri/latest/tauri/webview/struct.WebviewWindowBuilder.html
- WebviewWindow API (JS): https://v2.tauri.app/reference/javascript/api/namespacewebviewwindow/
- Tray icon: https://v2.tauri.app/learn/system-tray/
- Menu API: https://v2.tauri.app/learn/window-menu/
- Global shortcut plugin: https://v2.tauri.app/plugin/global-shortcut/
- Window events: https://v2.tauri.app/develop/calling-frontend/#window-events

## Related

- `frontend-patterns.md` -- `getCurrentWebviewWindow()` and event listening
- `rust-patterns.md` -- state management and command shape
- `plugins-core.md` -- the global-shortcut plugin alongside core plugins
