---
description: Scaffold a new Firefox WebExtension project with manifest.json (V3 default), directory layout, content/background scripts, web-ext config, and a working "Hello World" popup. Follows AMO publishing requirements from day one. Use when the user asks to create, bootstrap, start, or scaffold a new Firefox extension / WebExtension / browser add-on. Not for adding features to an existing extension (use firefox-extension-dev agent), or targeting Chrome-only (different APIs and review process).
argument-hint: <extension-name> [--mv V2|V3] [--sidebar] [--content-script] [--options-page]
---

# Firefox Extension Scaffold

Scaffold a production-ready Firefox WebExtension with Manifest V3 defaults, `web-ext` CLI integration, and AMO-compatible structure.

## CRITICAL RULES

1. **Default to Manifest V3**. Firefox MV3 supports both `background.scripts` (event pages with DOM access, unlike Chrome) and `declarativeNetRequest`. Only use V2 when the user has an explicit reason (ESR Firefox target, specific APIs not in V3).
2. **Generate a working "Hello World"** the user can load immediately via `web-ext run`. No `TODO` placeholders as the only content of any file.
3. **Match AMO submission requirements** from day one: no binary blobs without source, no obfuscated code, valid semver, unique `id` in `browser_specific_settings`.
4. **Never hardcode user identity**. If the user does not specify `--author` or `--id`, prompt them.

## Procedure

### 1. Parse arguments

- `extension-name`: required, kebab-case (becomes directory name + manifest `name` slugified)
- `--mv V2 | V3`: manifest version (default V3)
- `--sidebar`: include sidebar_action
- `--content-script`: include content script template (default: include)
- `--options-page`: include options UI template

If extension `id` not provided, ask the user for their preferred format (`{extension-name}@example.com` or email-style) -- AMO requires a unique ID.

### 2. Directory layout

```
<extension-name>/
  manifest.json
  src/
    background.js            (or background.ts if --ts)
    content.js               (if --content-script)
    popup/
      index.html
      popup.js
      popup.css
    options/                 (if --options-page)
      index.html
      options.js
    sidebar/                 (if --sidebar)
      index.html
      sidebar.js
  icons/
    icon-48.png
    icon-96.png
  web-ext-config.js
  .web-ext-artifacts/        (gitignored, build output)
  .gitignore
  package.json
  README.md
```

### 3. Write manifest.json (MV3)

```json
{
  "manifest_version": 3,
  "name": "{{Extension Name}}",
  "version": "0.1.0",
  "description": "{{One-line description}}",
  "author": "{{Author from prompt}}",
  "icons": {
    "48": "icons/icon-48.png",
    "96": "icons/icon-96.png"
  },
  "browser_specific_settings": {
    "gecko": {
      "id": "{{extension-id from prompt}}",
      "strict_min_version": "128.0"
    }
  },
  "permissions": [],
  "host_permissions": [],
  "background": {
    "scripts": ["src/background.js"]
  },
  "action": {
    "default_popup": "src/popup/index.html",
    "default_title": "{{Extension Name}}"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["src/content.js"]
    }
  ]
}
```

If `--sidebar`, add:
```json
"sidebar_action": {
  "default_title": "{{Extension Name}}",
  "default_panel": "src/sidebar/index.html",
  "default_icon": "icons/icon-48.png"
}
```

If `--options-page`, add:
```json
"options_ui": {
  "page": "src/options/index.html",
  "open_in_tab": false
}
```

Always start with empty `permissions` / `host_permissions` arrays -- users add only what they need. AMO reviewers reject extensions requesting permissions they don't use.

### 4. Write web-ext-config.js

```javascript
module.exports = {
  verbose: false,
  sourceDir: './',
  artifactsDir: './.web-ext-artifacts',
  ignoreFiles: [
    'package-lock.json',
    'yarn.lock',
    'README.md',
    'web-ext-config.js',
    '.git',
    'node_modules',
    '.web-ext-artifacts',
  ],
  run: {
    startUrl: ['about:debugging#/runtime/this-firefox'],
    firefox: process.env.FIREFOX_BIN || 'firefox',
    browserConsole: true,
  },
  lint: {
    pretty: true,
    warningsAsErrors: false,
  },
  build: {
    overwriteDest: true,
  },
};
```

### 5. Write package.json

```json
{
  "name": "{{extension-name}}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "start": "web-ext run",
    "build": "web-ext build",
    "lint": "web-ext lint",
    "sign": "web-ext sign --api-key=$WEB_EXT_API_KEY --api-secret=$WEB_EXT_API_SECRET"
  },
  "devDependencies": {
    "web-ext": "^8.0.0"
  }
}
```

### 6. Seed background.js with a working event

```javascript
// src/background.js
browser.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === 'install') {
    console.log('{{Extension Name}} installed');
  }
});

browser.action.onClicked.addListener((tab) => {
  console.log('Action clicked on tab', tab.id, tab.url);
});
```

### 7. Seed popup with working HTML + JS

Popup renders "{{Extension Name}} -- click to greet", wires a button that calls `browser.tabs.query` and displays the active tab's URL. User sees something real in under 60 seconds.

### 8. Seed content.js (if --content-script) as a no-op that proves injection

```javascript
// src/content.js
console.log('{{Extension Name}} content script loaded on', window.location.href);
```

### 9. Write README with first-run instructions

```markdown
# {{Extension Name}}

## Develop

    npm install
    npm start    # launches Firefox with the extension loaded

## Lint

    npm run lint

## Build

    npm run build    # output: .web-ext-artifacts/{{name}}-{{version}}.zip

## Publish to AMO

1. Get API credentials from https://addons.mozilla.org/en-US/developers/addon/api/key/
2. Export `WEB_EXT_API_KEY` and `WEB_EXT_API_SECRET`
3. Run `npm run sign`
```

### 10. Report

Show created files, tell the user to run:
```
cd <extension-name>
npm install
npm start
```
and to replace placeholder icons (48x48 and 96x96 PNG) before publishing.

## Synergies

- Full API / manifest / AMO docs -> `firefox-extension-dev` agent or `firefox-extension-dev` skill
- Pre-publish lint -> `/firefox-lint`
- Publishing flow -> `/firefox-publish`
