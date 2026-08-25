# Frontend Patterns for Tauri

How the JS/TS side talks to Rust: invoke, channels, events, and the convention of typing them at the boundary.

## When to use

Designing the frontend layer of a Tauri app -- TypeScript wrappers around Rust commands, streaming progress channels, event listeners, plugin usage. Most code lives upstream; this file calls out the conventions that make the boundary maintainable.

## When NOT to use

Pure Rust code (commands, state, channels on the Rust side) -- see `rust-patterns.md`.

## Gotchas

- **Always wrap `invoke()` in a typed function**, never call `invoke` from React/Vue components directly. The string `'greet'` is a magic identifier; if it changes in Rust, you want one TS file to update, not 30 components.
- **`Channel<T>` is one-shot.** Construct a fresh `new Channel()` per call, set `.onmessage` *before* passing it to `invoke`, otherwise you race with the first emission.
- **`listen()` returns a Promise of an unlisten function**, not the function directly. The React-hook footgun:
  ```typescript
  // wrong: cleanup never runs
  useEffect(() => { listen('event', h); }, []);
  // right
  useEffect(() => {
    const p = listen('event', h);
    return () => { p.then(fn => fn()); };
  }, []);
  ```
- **`@tauri-apps/plugin-fs` `BaseDirectory.AppData`** is the only safe write target on iOS sandboxing -- writing to absolute paths fails silently in release builds.
- **Capabilities are explicit.** Adding a plugin in Rust does NOT grant the JS side permission. You must list `"<plugin>:default"` (or specific allow-rules) in `src-tauri/capabilities/default.json` or invocation throws "permission denied" only at runtime, not at build.
- **Platform detection is async.** `platform()` from `@tauri-apps/plugin-os` returns a Promise; do not call it inside a render path -- cache it once at app boot.

## Capabilities snippet (the file you forget exists)

```json
// src-tauri/capabilities/default.json
{
  "$schema": "https://schemas.tauri.app/config/2/Capability",
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "fs:default",
    "http:default",
    "notification:default",
    "clipboard-manager:default",
    "opener:default"
  ]
}
```

## Official docs

- JS API `invoke` / `Channel`: https://v2.tauri.app/develop/calling-rust/
- Event API (`listen`, `emit`): https://v2.tauri.app/develop/calling-frontend/
- Capabilities + permissions: https://v2.tauri.app/security/capabilities/
- All `@tauri-apps/plugin-*` JS APIs: https://v2.tauri.app/plugin/
- `@tauri-apps/plugin-os`: https://v2.tauri.app/plugin/os/

## Related

- `rust-patterns.md` -- the Rust side of every example here
- `ipc-streaming.md` -- when Channels aren't enough (HFT/streaming)
- `plugins-core.md` -- per-plugin permission keys
