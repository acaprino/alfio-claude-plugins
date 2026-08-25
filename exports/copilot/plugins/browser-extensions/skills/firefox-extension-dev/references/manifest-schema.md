# manifest.json Schema Reference

Full key reference lives on MDN. This file is the gotchas (especially MV2 vs MV3 shape changes) and the Firefox-specific keys that don't exist in Chrome.

## When to use

Writing or auditing a `manifest.json`, especially when migrating MV2 → MV3 or adding Firefox-specific behavior.

## The 3 mandatory keys

```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0"
}
```

`version` format: numbers separated by up to 3 dots, max 9 digits each (e.g. `1.0.0` or `1.0.0.1`).

## Firefox-specific keys (no Chrome equivalent)

| Key | Use |
|-----|-----|
| `browser_specific_settings.gecko` | Set extension `id` (`...@example.org` format) and `strict_min_version` |
| `sidebar_action` | Sidebar panel (Chrome has its own side-panel API with different shape) |
| `protocol_handlers` | Register custom protocol handlers |
| `theme_experiment` | Experimental theme features |

The `browser_specific_settings.gecko.id` is **mandatory for AMO-listed extensions** -- without it, signing fails.

## MV2 → MV3 manifest changes (the load-bearing differences)

| Field | MV2 | MV3 |
|-------|-----|-----|
| `browser_action` (toolbar button) | Used | **Removed → use `action`** |
| `background.persistent` | `true`/`false` | **Removed** -- background is event-page (Firefox) or service_worker (Chrome) |
| `background.service_worker` | n/a | Chrome uses this, Firefox uses `background.scripts` |
| `host_permissions` | Inside `permissions` array | **Separate top-level key** |
| `optional_host_permissions` | n/a | New top-level key |
| `content_security_policy` | String | **Object** with `extension_pages` key |
| `web_accessible_resources` | Array of strings | **Array of objects** with `resources`+`matches`+`extension_ids` |
| `user_scripts` | Manifest key | **Removed** -- use `userScripts` API (optional permission only) |
| `page_action` | Used | Removed in Chrome; **Firefox keeps it in MV3** |

## Gotchas

- **`browser_specific_settings.gecko.id` MUST match across versions.** Changing it = AMO treats it as a new extension; users lose data.
- **`strict_min_version` blocks installation on older Firefox.** Use to require API features added in a specific Firefox release. Don't set it lower than you've tested.
- **MV3 `host_permissions` is NOT optional in the `permissions` array** like in MV2 -- promoting hosts from `permissions` (where MV2 put them) to `host_permissions` (where MV3 requires them) is the #1 manifest-migration error.
- **Empty `host_permissions: []` triggers `activeTab`-style "click to grant"** on Firefox MV3 if combined with `<all_urls>` content script matches. If you want no host access at startup, leave the key out entirely.
- **`background.scripts` works in Firefox MV3** as event pages; do NOT use `background.service_worker` as the primary key -- Firefox doesn't support service workers as background. Cross-browser pattern: include both keys, document the runtime split.
- **Manifest `version` is NOT semver.** Max 9 digits per dot-component, no pre-release tags (no `1.0.0-beta`). AMO rejects non-numeric versions.
- **`web_accessible_resources` MV3 needs `matches` constraints** -- exposing without constraints (`"matches": ["<all_urls>"]`) defeats the security model and triggers AMO manual review.
- **Icons: declare `"48"` and `"96"` at minimum.** Firefox uses 48 in the add-ons manager and 96 for HiDPI; missing them = blurry rendering. Sizes 16, 32, 48, 96, 128 are all supported.
- **`default_locale` is required if `_locales/` exists.** Otherwise the extension fails to load with a confusing error.
- **`incognito: "split"` is Firefox-only**; Chrome supports `"spanning"` (default) and `"not_allowed"`. If you need cross-browser private-mode behavior, leave the key out.

## MV3 minimal example (Firefox)

```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0",
  "browser_specific_settings": {
    "gecko": { "id": "my-extension@example.org", "strict_min_version": "109.0" }
  },
  "permissions": ["storage", "alarms"],
  "host_permissions": ["*://*.example.com/*"],
  "background": { "scripts": ["background.js"] },
  "action": {
    "default_icon": { "16": "icons/icon-16.png", "32": "icons/icon-32.png" },
    "default_popup": "popup/popup.html"
  },
  "content_scripts": [{
    "matches": ["*://*.example.com/*"],
    "js": ["content.js"],
    "run_at": "document_idle"
  }],
  "icons": { "48": "icons/icon-48.png", "96": "icons/icon-96.png" },
  "web_accessible_resources": [{
    "resources": ["images/*"],
    "matches": ["*://*.example.com/*"]
  }],
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

## Access manifest at runtime

```javascript
const manifest = browser.runtime.getManifest();
console.log(manifest.version);
```

## Official docs

- Full key reference: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json
- `browser_specific_settings`: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/browser_specific_settings
- MV3 migration guide: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Manifest_V3_migration_guide
- CSP for extensions: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_Security_Policy
- `web_accessible_resources` MV3 shape: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/web_accessible_resources

## Related

- `browser-api-reference.md` -- which manifest key enables which API
- `amo-publishing.md` -- which manifest patterns trigger AMO rejection
- `best-practices.md` -- background-script lifecycle (event page vs service worker) gotchas
