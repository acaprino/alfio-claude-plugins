# Frontend Patterns for Tauri Mobile

## Invoking Rust Commands

```typescript
import { invoke } from '@tauri-apps/api/core';

// Simple invoke
const result = await invoke<string>('greet', { name: 'World' });

// Type-safe wrapper
export async function greet(name: string): Promise<string> {
  return invoke('greet', { name });
}

export async function fetchData(url: string): Promise<string> {
  return invoke('fetch_data', { url });
}
```

## Channels (Streaming)

```typescript
import { invoke, Channel } from '@tauri-apps/api/core';

interface Progress {
  downloaded: number;
  total: number;
  percentage: number;
}

export async function downloadWithProgress(
  url: string,
  onProgress: (progress: Progress) => void
): Promise<Uint8Array> {
  const channel = new Channel<Progress>();
  channel.onmessage = onProgress;
  
  return invoke('download_with_progress', {
    url,
    onProgress: channel,
  });
}

// Usage
await downloadWithProgress('https://example.com/file.zip', (p) => {
  console.log(`${p.percentage}% complete`);
});
```

## Event Listeners

```typescript
import { listen, emit } from '@tauri-apps/api/event';

// Listen for events from Rust
const unlisten = await listen<{ timestamp: string }>('background-tick', (event) => {
  console.log('Tick:', event.payload.timestamp);
});

// Cleanup
unlisten();

// Emit event to Rust
await emit('user-action', { action: 'clicked' });
```

## Platform Detection

```typescript
import { platform, arch } from '@tauri-apps/plugin-os';

export async function getPlatform() {
  const p = await platform();
  return {
    isAndroid: p === 'android',
    isIOS: p === 'ios',
    isMobile: p === 'android' || p === 'ios',
    isDesktop: !['android', 'ios'].includes(p),
    arch: await arch(),
  };
}
```

## Plugin Usage Examples

### Biometric Authentication
```typescript
import { authenticate } from '@tauri-apps/plugin-biometric';

async function biometricLogin(): Promise<boolean> {
  try {
    await authenticate('Confirm your identity', {
      allowDeviceCredential: true,
      cancelTitle: 'Cancel',
      fallbackTitle: 'Use password',
    });
    return true;
  } catch (e) {
    console.error('Biometric failed:', e);
    return false;
  }
}
```

### Geolocation
```typescript
import { getCurrentPosition, watchPosition } from '@tauri-apps/plugin-geolocation';

async function getLocation() {
  const position = await getCurrentPosition({
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 0,
  });
  return {
    lat: position.coords.latitude,
    lng: position.coords.longitude,
    accuracy: position.coords.accuracy,
  };
}

// Watch position changes
const watchId = await watchPosition(
  { enableHighAccuracy: true },
  (position) => console.log('New position:', position)
);
```

### Haptics
```typescript
import { vibrate, impactFeedback, notificationFeedback } from '@tauri-apps/plugin-haptics';

async function buttonTap() {
  await impactFeedback('light'); // light, medium, heavy
}

async function success() {
  await notificationFeedback('success'); // success, warning, error
}
```

### Notifications
```typescript
import { sendNotification, requestPermission } from '@tauri-apps/plugin-notification';

async function notify(title: string, body: string) {
  const permission = await requestPermission();
  if (permission === 'granted') {
    await sendNotification({ title, body });
  }
}
```

### Deep Links
```typescript
import { onOpenUrl, getCurrent } from '@tauri-apps/plugin-deep-link';

async function setupDeepLinks(handler: (url: string) => void) {
  // Check if opened via deep link
  const urls = await getCurrent();
  if (urls?.length) {
    handler(urls[0]);
  }
  
  // Listen for future deep links
  await onOpenUrl((urls) => handler(urls[0]));
}
```

### File System
```typescript
import { readTextFile, writeTextFile, BaseDirectory } from '@tauri-apps/plugin-fs';

async function saveData(filename: string, data: object) {
  await writeTextFile(filename, JSON.stringify(data), {
    baseDir: BaseDirectory.AppData,
  });
}

async function loadData<T>(filename: string): Promise<T | null> {
  try {
    const content = await readTextFile(filename, {
      baseDir: BaseDirectory.AppData,
    });
    return JSON.parse(content);
  } catch {
    return null;
  }
}
```

### HTTP Client
```typescript
import { fetch } from '@tauri-apps/plugin-http';

async function apiCall<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  return response.json();
}
```

## React Hooks Examples

```typescript
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

// Generic invoke hook
function useInvoke<T>(command: string, args?: Record<string, unknown>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    invoke<T>(command, args)
      .then(setData)
      .catch((e) => setError(e.toString()))
      .finally(() => setLoading(false));
  }, [command, JSON.stringify(args)]);

  return { data, loading, error };
}

// Event listener hook
function useEvent<T>(eventName: string, handler: (payload: T) => void) {
  useEffect(() => {
    const unlisten = listen<T>(eventName, (e) => handler(e.payload));
    return () => { unlisten.then(fn => fn()); };
  }, [eventName, handler]);
}
```

## Capabilities Configuration

Add permissions in `src-tauri/capabilities/default.json`:

```json
{
  "$schema": "https://schemas.tauri.app/config/2/Capability",
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-open",
    "fs:default",
    "http:default",
    "notification:default",
    "geolocation:allow-get-current-position",
    "biometric:allow-authenticate",
    "haptics:default",
    "clipboard-manager:default"
  ]
}
```

For mobile-specific capabilities, create `src-tauri/capabilities/mobile.json`:

```json
{
  "identifier": "mobile",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    "biometric:allow-authenticate",
    "geolocation:allow-watch-position",
    "haptics:default"
  ]
}
```

## Safe Areas on Android WebView

CSS `env(safe-area-inset-*)` does **not** work by default on Android WebView. The WebView lacks the viewport-fit=cover meta and proper inset reporting.

### The Problem

```css
/* This won't work on Android WebView */
.header {
  padding-top: env(safe-area-inset-top, 0px);
}
```

### Solution: JavaScript Fallback for Android Only

The fix: use `env()` in CSS as the default, and only override with JS on Android where it doesn't work.

```typescript
import { platform } from '@tauri-apps/plugin-os';

export async function setupMobileSafeAreas(): Promise<void> {
  const p = await platform();

  if (p === 'android') {
    // Android WebView doesn't support env(safe-area-inset-*)
    // Override with typical values: status bar ~48px, navigation ~24px
    document.documentElement.style.setProperty('--safe-area-top', '48px');
    document.documentElement.style.setProperty('--safe-area-bottom', '24px');
  }
  // iOS and desktop: don't set variables, let CSS env() fallback handle it
}
```

### CSS Usage

Use CSS custom properties with `env()` as the fallback. This way iOS gets native values, and Android uses the JS-set overrides:

```css
:root {
  /* Defaults use env() - works on iOS, ignored on Android */
  --safe-area-top: env(safe-area-inset-top, 0px);
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
}

.header {
  padding-top: var(--safe-area-top);
}

.bottom-nav {
  padding-bottom: var(--safe-area-bottom);
}

.app-container {
  min-height: calc(100vh - var(--safe-area-top) - var(--safe-area-bottom));
}
```

### Typical Values

| Area | Android | iOS (varies by device) |
|------|---------|------------------------|
| Top (status bar) | ~48px | 44px - 59px |
| Bottom (navigation) | ~24px | 0px - 34px (home indicator) |

### React Integration

```tsx
import { useEffect } from 'react';
import { setupMobileSafeAreas } from './utils/safe-areas';

function App() {
  useEffect(() => {
    setupMobileSafeAreas();
  }, []);

  return <div className="app-container">...</div>;
}
```
