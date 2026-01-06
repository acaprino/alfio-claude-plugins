# Rust Patterns for Tauri Mobile

## Mobile Entry Point

All code goes in `lib.rs` (not `main.rs`) for mobile compatibility:

```rust
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            fetch_data,
            get_platform_info
        ])
        .setup(|app| {
            #[cfg(debug_assertions)]
            if let Some(window) = app.get_webview_window("main") {
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Commands

### Sync Command
```rust
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}
```

### Async Command
```rust
#[tauri::command]
async fn fetch_data(url: String) -> Result<String, String> {
    reqwest::get(&url)
        .await
        .map_err(|e| e.to_string())?
        .text()
        .await
        .map_err(|e| e.to_string())
}
```

### Platform Detection
```rust
#[tauri::command]
fn get_platform_info() -> serde_json::Value {
    serde_json::json!({
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "is_mobile": cfg!(mobile)
    })
}
```

## State Management

```rust
use std::sync::Mutex;
use tauri::State;

struct AppState {
    counter: Mutex<i32>,
    user_token: Mutex<Option<String>>,
}

#[tauri::command]
fn increment(state: State<AppState>) -> i32 {
    let mut counter = state.counter.lock().unwrap();
    *counter += 1;
    *counter
}

#[tauri::command]
fn set_token(state: State<AppState>, token: String) {
    *state.user_token.lock().unwrap() = Some(token);
}

// In run():
.manage(AppState {
    counter: Mutex::new(0),
    user_token: Mutex::new(None),
})
```

## Channels (Streaming Data)

```rust
use tauri::ipc::Channel;

#[derive(Clone, serde::Serialize)]
struct Progress {
    downloaded: u64,
    total: u64,
    percentage: u8,
}

#[tauri::command]
async fn download_with_progress(
    url: String,
    on_progress: Channel<Progress>,
) -> Result<Vec<u8>, String> {
    let response = reqwest::get(&url).await.map_err(|e| e.to_string())?;
    let total = response.content_length().unwrap_or(0);
    let mut downloaded: u64 = 0;
    let mut data = Vec::new();
    
    let mut stream = response.bytes_stream();
    while let Some(chunk) = stream.next().await {
        let chunk = chunk.map_err(|e| e.to_string())?;
        downloaded += chunk.len() as u64;
        data.extend_from_slice(&chunk);
        
        on_progress.send(Progress {
            downloaded,
            total,
            percentage: (downloaded as f64 / total as f64 * 100.0) as u8,
        }).ok();
    }
    
    Ok(data)
}
```

## Events (Backend to Frontend)

```rust
use tauri::Emitter;

#[tauri::command]
async fn start_background_task(app: tauri::AppHandle) {
    tauri::async_runtime::spawn(async move {
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(5)).await;
            app.emit("background-tick", serde_json::json!({
                "timestamp": chrono::Utc::now().to_rfc3339()
            })).ok();
        }
    });
}
```

## Conditional Compilation

```rust
// Mobile-only code
#[cfg(mobile)]
.plugin(tauri_plugin_biometric::init())

// Desktop-only code
#[cfg(desktop)]
.plugin(tauri_plugin_global_shortcut::init())

// Platform-specific
#[cfg(target_os = "android")]
fn android_specific() { }

#[cfg(target_os = "ios")]
fn ios_specific() { }
```

## Error Handling

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
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: serde::Serializer {
        serializer.serialize_str(&self.to_string())
    }
}

#[tauri::command]
async fn risky_operation() -> Result<String, AppError> {
    // Errors automatically serialize to frontend
    Ok("success".into())
}
```

## Cargo.toml Dependencies

```toml
[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.11", features = ["json", "stream"] }
thiserror = "1"
log = "0.4"

[profile.release]
lto = true
opt-level = "s"
codegen-units = 1
strip = true
```
