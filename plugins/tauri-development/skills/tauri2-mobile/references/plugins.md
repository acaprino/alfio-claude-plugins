# Tauri 2 Plugins for Mobile

## Adding Plugins

```bash
npm run tauri add <plugin-name>
```

This automatically:
1. Adds Rust crate to `Cargo.toml`
2. Adds npm package
3. Updates capabilities if needed

## Official Plugins with Mobile Support

| Plugin | Mobile | Description |
|--------|--------|-------------|
| `fs` | ✅ | File system access |
| `http` | ✅ | HTTP client |
| `notification` | ✅ | Push/local notifications |
| `clipboard-manager` | ✅ | Clipboard access |
| `dialog` | ✅ | Native dialogs |
| `shell` | ❌ | **Does not work on Android** for URLs |
| `opener` | ✅ | Open URLs in system browser |
| `store` | ✅ | Key-value storage |
| `sql` | ✅ | SQLite database |
| `biometric` | 📱 | Fingerprint/Face ID |
| `barcode-scanner` | 📱 | QR/barcode scanning |
| `geolocation` | ✅ | GPS location |
| `haptics` | 📱 | Vibration feedback |
| `nfc` | 📱 | NFC read/write |
| `deep-link` | ✅ | URL scheme handling |
| `log` | ✅ | Logging |
| `os` | ✅ | OS information |

📱 = Mobile only, ⚠️ = Limited functionality

## Plugin Configuration

### lib.rs Setup
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
        #[cfg(mobile)]
        .plugin(tauri_plugin_biometric::init())
        #[cfg(mobile)]
        .plugin(tauri_plugin_haptics::init())
        #[cfg(mobile)]
        .plugin(tauri_plugin_geolocation::init())
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("error");
}
```

### Permissions (capabilities/default.json)
```json
{
  "permissions": [
    "core:default",
    "opener:default",
    "deep-link:default",
    "fs:default",
    "http:default",
    "notification:default",
    "store:default",
    "geolocation:allow-get-current-position",
    "geolocation:allow-watch-position",
    "biometric:allow-authenticate",
    "biometric:allow-status",
    "haptics:default",
    "clipboard-manager:default"
  ]
}
```

## Deep Linking Configuration

### tauri.conf.json
```json
{
  "plugins": {
    "deep-link": {
      "mobile": [
        { "scheme": ["myapp"], "appLink": false },
        { 
          "scheme": ["https"], 
          "host": "app.example.com", 
          "pathPrefix": ["/open"],
          "appLink": true 
        }
      ],
      "desktop": {
        "schemes": ["myapp"]
      }
    }
  }
}
```

### Android Intent Filter
Add to `AndroidManifest.xml` for Universal Links:
```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="app.example.com" />
</intent-filter>
```

### iOS Associated Domains
Add to Xcode: Signing & Capabilities → Associated Domains:
```
applinks:app.example.com
```

## Opener Plugin (External URLs)

**Use this instead of shell plugin for opening URLs on mobile.**

The `shell` plugin's `open` command fails on Android with:
```
Scoped shell IO error: No such file or directory (os error 2)
```

### Setup
```bash
npm run tauri add opener
```

### Usage
```typescript
import { openUrl } from '@tauri-apps/plugin-opener';

// Open URL in system browser (Chrome Custom Tabs on Android)
await openUrl('https://example.com');

// Open email client
await openUrl('mailto:hello@example.com');

// Open phone dialer
await openUrl('tel:+1234567890');
```

### Permissions
```json
{
  "permissions": [
    "opener:default"
  ]
}
```

### OAuth Use Case
Critical for OAuth flows where Google blocks WebView sign-in. See [authentication.md](authentication.md) for complete OAuth implementation guide.

## Logging Plugin

```rust
// Cargo.toml
tauri-plugin-log = "2"

// lib.rs
.plugin(
    tauri_plugin_log::Builder::new()
        .level(log::LevelFilter::Debug)
        .with_colors(tauri_plugin_log::fern::colors::ColoredLevelConfig::default())
        .build()
)

// Usage
log::info!("App started");
log::debug!("Debug info: {:?}", data);
log::error!("Error: {}", error);
```

## Store Plugin (Persistent Storage)

```typescript
import { Store } from '@tauri-apps/plugin-store';

const store = new Store('settings.json');

// Save
await store.set('theme', 'dark');
await store.set('user', { id: 1, name: 'John' });
await store.save();

// Load
const theme = await store.get<string>('theme');
const user = await store.get<{ id: number; name: string }>('user');

// Delete
await store.delete('theme');
await store.clear();
```

## SQL Plugin (SQLite)

```typescript
import Database from '@tauri-apps/plugin-sql';

const db = await Database.load('sqlite:app.db');

// Create table
await db.execute(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
  )
`);

// Insert
await db.execute(
  'INSERT INTO users (name, email) VALUES (?, ?)',
  ['John', 'john@example.com']
);

// Select
const users = await db.select<{ id: number; name: string; email: string }[]>(
  'SELECT * FROM users WHERE name LIKE ?',
  ['%John%']
);
```

## Barcode Scanner

```typescript
import { scan, Format } from '@tauri-apps/plugin-barcode-scanner';

async function scanQR(): Promise<string | null> {
  try {
    const result = await scan({
      formats: [Format.QRCode, Format.EAN13],
      windowed: false,
    });
    return result.content;
  } catch (e) {
    console.error('Scan failed:', e);
    return null;
  }
}
```

## NFC Plugin

```typescript
import { scan, write } from '@tauri-apps/plugin-nfc';

// Read NFC tag
const data = await scan();
console.log('Tag ID:', data.id);
console.log('Records:', data.records);

// Write to NFC tag
await write([
  { format: 'text', value: 'Hello NFC!' }
]);
```

## Community Plugins

### In-App Purchases (tauri-plugin-iap)
See [references/iap.md](iap.md) for complete IAP guide.

```bash
npm install @choochmeque/tauri-plugin-iap-api
cargo add tauri-plugin-iap
```

### Other Notable Community Plugins
- `tauri-plugin-keep-screen-on` - Prevent screen timeout
- `tauri-plugin-camera` - Camera access
- `tauri-plugin-share` - Native share sheet

Search: https://v2.tauri.app/plugin/ or https://github.com/tauri-apps/awesome-tauri
