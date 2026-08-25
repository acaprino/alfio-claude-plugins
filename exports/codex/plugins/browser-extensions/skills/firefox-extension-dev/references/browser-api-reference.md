# WebExtension JavaScript APIs

The full API surface lives on MDN -- this file is the navigation index plus the Firefox-only APIs and MV2/MV3 differences worth memorizing. For per-method deep-links, see `mdn-api-urls.md`.

## When to use

Picking which API to use, knowing whether it's Firefox-only, and knowing what permission to declare. For per-API method/event listings, hit MDN directly.

## API namespace pattern

All APIs accessed via `browser.*` (Firefox returns Promises for all async methods; Chrome's `chrome.*` uses callbacks unless polyfilled). For cross-browser code, use the `webextension-polyfill` package and continue calling `browser.*`.

## Firefox-only APIs (don't write code expecting Chrome to support these)

- `browserSettings` -- global browser settings
- `captivePortal` -- detect captive portal
- `contextualIdentities` -- container tabs (also requires `cookies` permission)
- `dns` -- DNS resolution
- `find` -- find text in pages
- `pkcs11` -- security modules
- `sidebarAction` -- sidebar panel (Chrome has its own side-panel API, different shape)
- `tabHide` -- experimental, Firefox-only
- `webRequestFilterResponse` -- response body filtering

Plus: Firefox keeps **blocking `webRequest` in MV3** (Chrome dropped it), and supports both `declarativeNetRequest` AND blocking `webRequest` simultaneously -- this is the headline reason ad-blockers prefer Firefox MV3.

## MV2 → MV3 API renames (the gotchas)

| MV2 | MV3 |
|-----|-----|
| `browserAction` (manifest `browser_action`) | `action` (manifest `action`) |
| `tabs.executeScript` / `tabs.insertCSS` / `tabs.removeCSS` | `scripting.executeScript` / `scripting.insertCSS` / `scripting.removeCSS` |
| `contentScripts` API | `scripting.registerContentScripts` |
| `user_scripts` (manifest) | `userScripts` API (MV3 needs optional permission) |
| `background.scripts` + `persistent` | `background.scripts` (event page in Firefox) / `service_worker` (Chrome) |
| `web_accessible_resources` (string array) | `web_accessible_resources` (object array with `resources`+`matches`+`extension_ids`) |

Firefox keeps `pageAction` in MV3; Chrome dropped it.

## Storage areas (the only API where Firefox-vs-Chrome differs in limits)

| Area | Limit | Persistence |
|------|-------|-------------|
| `storage.local` | 10 MB | On disk |
| `storage.sync` | 100 KB | Synced across devices (requires sign-in) |
| `storage.session` | 10 MB | In-memory only, lost on restart |
| `storage.managed` | Read-only | Set by domain admin |

**Never use `window.localStorage` in extensions** -- Firefox clears it during privacy cleanup. Use `browser.storage.local` instead.

## Permission cheat sheet (the most common ones)

| Permission | Use |
|------------|-----|
| `activeTab` | Temporary access to active tab on user action -- prefer over `<all_urls>` |
| `tabs` | Read URL/title/favIconUrl on Tab objects (different from access) |
| `storage` | `browser.storage` API |
| `cookies` | Cookie management (+ host perms required) |
| `webRequest` | Listen to HTTP requests |
| `webRequestBlocking` | Modify/block HTTP requests (Firefox keeps this in MV3) |
| `scripting` | MV3 script/CSS injection |
| `declarativeNetRequest` | Declarative network filtering |
| `notifications` | OS notifications |
| `clipboardWrite` / `clipboardRead` | System clipboard |
| `unlimitedStorage` | Skip the 10 MB `storage.local` limit |
| `nativeMessaging` | `runtime.connectNative()` / `sendNativeMessage()` |

## Gotchas

- **Firefox returns Promises for everything.** Chrome's older callback API still works in Chrome MV3 alongside Promises. Cross-browser code: use `webextension-polyfill`.
- **`browser.tabs.executeScript` is MV2-only.** In MV3 use `browser.scripting.executeScript({ target: { tabId }, func: () => {...} })`.
- **`chrome.action` exists in Chrome MV3, but `browser.action` may need polyfill** for older Firefox versions -- check `strict_min_version` in `browser_specific_settings`.
- **`runtime.onInstalled` fires for both `install` and `update`** -- check `reason` to differentiate. The `reason` value `browser_update` and `chrome_update` differ between browsers.
- **`runtime.setUninstallURL`** is the cleanest way to drive a feedback survey -- works in both MV2/MV3.

## Quick API recipes (the few worth keeping local)

```javascript
// Active tab (the safe pattern)
const [tab] = await browser.tabs.query({ active: true, currentWindow: true });

// Storage with default fallback
const { settings } = await browser.storage.local.get({
  settings: { theme: "light", fontSize: 14 }
});

// Listen for storage changes across pages
browser.storage.onChanged.addListener((changes, areaName) => {
  for (const [key, { oldValue, newValue }] of Object.entries(changes)) {
    console.log(`${areaName}.${key}: ${oldValue} -> ${newValue}`);
  }
});

// Install vs update branch
browser.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === "install") initializeDefaults();
  if (reason === "update") migrateData();
});
```

## Official docs

- WebExtension API index (MDN): https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API
- Browser compatibility per API: each MDN page has a "Browser compatibility" table
- Permissions reference: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/permissions
- Firefox vs Chrome incompatibilities: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Chrome_incompatibilities
- MV2 → MV3 migration guide: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Manifest_V3_migration_guide
- `webextension-polyfill`: https://github.com/mozilla/webextension-polyfill

## Related

- `mdn-api-urls.md` -- direct deep-links per API method/event
- `manifest-schema.md` -- which manifest key enables which API
- `amo-publishing.md` -- which permissions trigger AMO manual review
- `best-practices.md` -- the MV3 footgun catalog (must-read for production extensions)
