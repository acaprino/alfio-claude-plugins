# Rust Patterns for Tauri

Backend conventions: entry point, commands, state, channels, events, error handling. The lib.rs/main.rs split and `cfg(mobile)` are the only Tauri-specific bits; the rest is idiomatic Rust.

## When to use

Writing or auditing the `src-tauri/src/` code of a Tauri 2 app. For the JS side of the same boundary, see `frontend-patterns.md`.

## Gotchas

- **All code in `lib.rs`, NOT `main.rs`.** Mobile builds invoke `lib::run()` via `mobile_entry_point` and never see `main.rs`. Putting your `tauri::Builder` in `main.rs` makes desktop work and mobile silently fail to start.
- **`#[cfg_attr(mobile, tauri::mobile_entry_point)]` on `pub fn run()`** is mandatory for mobile. Missing it = the app launches and immediately closes on Android/iOS.
- **`#[cfg(mobile)]` / `#[cfg(desktop)]` for plugin registration** -- mobile-only plugins (biometric, haptics, nfc) won't compile for desktop targets. Without the cfg gate, your `cargo tauri build` fails on the wrong platform.
- **State must be `Send + Sync`.** Use `Mutex<T>` (or `tokio::sync::Mutex` for async commands) -- `RefCell` will not compile through `State<T>`. Forgetting `tokio::sync::Mutex` in async commands deadlocks the runtime under contention.
- **Custom error types need manual `serde::Serialize`.** `thiserror` gives you `Display`; Tauri's IPC needs `Serialize`. The standard pattern (in the snippet below) serializes the error via `to_string()` so the JS side just sees the message.
- **`Channel::send()` returns `Result` -- ignore it intentionally** with `.ok()`. The frontend may have torn down the channel; that's not a backend error.
- **Async commands must return `Result<T, E>` for both arms to serialize**, even if you don't expect failures. `async fn foo() -> String` works but you lose the error-propagation channel.

## The error-handling pattern (the one piece worth memorizing)

```rust
#[derive(Debug, thiserror::Error)]
enum AppError {
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Custom error: {0}")]
    Custom(String),
}

impl serde::Serialize for AppError {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(&self.to_string())
    }
}

#[tauri::command]
async fn risky() -> Result<String, AppError> { Ok("ok".into()) }
```

## Cargo.toml release profile (mirror in CI)

```toml
[profile.release]
lto = true
opt-level = "s"      # "3" for speed
codegen-units = 1
strip = true
panic = "abort"
```

## Official docs

- Commands + state + channels: https://v2.tauri.app/develop/calling-rust/
- Events from Rust: https://v2.tauri.app/develop/calling-frontend/
- Plugin authoring + builder API: https://v2.tauri.app/develop/plugins/
- Conditional compilation in Rust: https://doc.rust-lang.org/reference/conditional-compilation.html

## Related

- `frontend-patterns.md` -- the TS side of every example here
- `plugins-core.md` -- which plugins to register and their permission keys
- `ipc-streaming.md` -- composite patterns for high-throughput Rust→JS streams
