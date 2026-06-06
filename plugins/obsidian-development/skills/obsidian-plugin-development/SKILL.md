---
name: obsidian-plugin-development
description: >
  Ensures compliance with Obsidian's automated plugin review (community.obsidian.md), eslint-plugin-obsidianmd rules, and official Obsidian plugin guidelines.
  TRIGGER WHEN: writing, reviewing, or fixing Obsidian community plugin code
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Obsidian Plugin Development

## Overview

Write Obsidian plugin code that passes Obsidian's automated plugin review on first submission. Since May 2026, plugins are submitted and reviewed through the Community hub at community.obsidian.md (the old PR workflow to `obsidianmd/obsidian-releases`, gated by ObsidianReviewBot, is retired); every GitHub release is scanned automatically. All rules below are enforced via `eslint-plugin-obsidianmd` and `@typescript-eslint`. Violations labeled "Required" block approval, and a failing version of an already-listed plugin is removed from directory search within 24 hours.

## When to Use

- Writing or editing TypeScript in an Obsidian plugin
- Preparing a plugin submission on the community.obsidian.md dashboard
- Fixing automated review violations
- Adding UI text, commands, settings tabs, or DOM manipulation

## Quick Reference: Required Rules

### 1. Sentence Case for All UI Text

Every user-visible string: sentence case only.

```typescript
// NO
'Block Settings'
'Add Block'
'Recent Files'

// YES
'Block settings'
'Add block'
'Recent files'
```

Applies to: `Setting.setName()`, `Setting.setDesc()`, `createEl()` text, button labels, modal titles, notices, menu items, tooltips. Proper nouns and acronyms (e.g. "API", "GitHub", "Obsidian") keep their casing.

### 2. No Inline Styles

Never assign `element.style.*` directly. Use CSS classes.

```typescript
// NO
el.style.display = 'flex';
el.style.transform = 'scale(0.9)';
el.style.opacity = '0';

// YES -- use CSS classes
el.addClass('hp-flex-container');
el.toggleClass('hp-scaled', true);
el.toggleClass('hp-hidden', true);

// For dynamic CSS custom properties, use setCssProps or setCssStyles:
el.setCssStyles({ '--my-var': value });
```

Flagged properties include: `display`, `transform`, `opacity`, `width`, `height`, `margin`, `padding`, `cursor`, `fontSize`, `fontFamily`, `flexDirection`, `alignItems`, `flexShrink`, `borderRadius`, `backdropFilter`, `background`, `borderWidth`, `borderStyle`, `transition`, `gridTemplateRows`, `transformOrigin`, and all others.

### 3. No Unnecessary Type Assertions

Don't `as Type` when it doesn't change the type.

```typescript
// NO -- assertion is redundant with ?? fallback
draft.url as string ?? ''
draft.showDate as boolean ?? true

// YES
String(draft.url ?? '')
Boolean(draft.showDate ?? true)
// or just
(draft.url ?? '') as string   // assertion AFTER coalescing
```

### 4. Promises Must Be Handled

Every Promise must be: `await`ed, `.catch()`ed, `.then()` with rejection handler, or `void`ed.

```typescript
// NO
someAsyncFn();
this.app.vault.read(file).then(text => { ... });

// YES
await someAsyncFn();
void someAsyncFn();
this.app.vault.read(file).then(text => { ... }, err => console.error(err));
this.app.vault.read(file).then(text => { ... }).catch(console.error);
```

### 5. No Async Without Await

Remove `async` from methods that don't use `await`.

```typescript
// NO
async onOpen() { this.render(); }

// YES
onOpen() { this.render(); }
```

### 6. No Promise Where Void Expected

Don't return a Promise in callbacks expecting `void`.

```typescript
// NO -- event callback expects void
this.registerEvent(this.app.vault.on('modify', async (file) => {
  await this.reload();
}));

// YES
this.registerEvent(this.app.vault.on('modify', (file) => {
  void this.reload();
}));
```

### 7. No Object Stringification

Ensure values won't stringify as `[object Object]`.

```typescript
// NO -- if draft is Record<string,unknown>, draft.mode could be an object
`Value: ${draft.mode ?? 'default'}`

// YES
`Value: ${String(draft.mode ?? 'default')}`
```

### 8. Settings Headings: Use Setting API

Don't create HTML headings. Use `Setting.setHeading()`.

```typescript
// NO
contentEl.createEl('h2', { text: 'My settings' });

// YES
new Setting(contentEl).setName('My settings').setHeading();
```

### 9. No Detach Leaves in onunload

Obsidian handles leaf cleanup. Detaching resets user's layout.

```typescript
// NO
onunload() {
  this.app.workspace.detachLeavesOfType(VIEW_TYPE);
}

// YES
onunload() {
  // Obsidian cleans up leaves automatically
}
```

### 10. No TFile/TFolder Cast

Use `instanceof` instead of type casting.

```typescript
// NO
const file = abstractFile as TFile;

// YES
if (abstractFile instanceof TFile) { ... }
```

### 11. No Forbidden DOM Elements

Don't create `<style>` or `<link>` elements dynamically.

### 12. No Plugin as Component

Don't pass `this` (plugin) to `MarkdownRenderer.render()`. Use a `Component` instance.

```typescript
// NO
MarkdownRenderer.render(this.app, md, el, '', this);

// YES -- use a Component subclass or this view/block
MarkdownRenderer.render(this.app, md, el, '', this.component);
```

### 13. No View References in Plugin

Don't store view references in plugin properties (memory leak).

### 14. Use Vault.configDir

Don't hardcode `.obsidian`. Use `this.app.vault.configDir`.

### 15. Platform Detection

Use `Platform` API, not `navigator.userAgent`.

```typescript
// NO
if (navigator.userAgent.includes('Mac')) { ... }

// YES
import { Platform } from 'obsidian';
if (Platform.isMacOS) { ... }
```

### 16. No Regex Lookbehind

Lookbehinds break on some iOS versions. Avoid unless `isDesktopOnly: true`.

### 17. Commands

- No word "command" in command ID or name
- No plugin ID in command ID
- No plugin name in command name
- No default hotkeys

### 18. File Operations

- Use `FileManager.trashFile()` instead of `Vault.trash()`/`Vault.delete()`
- Don't iterate all files to find by path -- use `getAbstractFileByPath()`
- Use `normalizePath()` for user-provided paths

### 19. No Sample/Template Code

Remove `MyPlugin`, `SampleModal`, template code from obsidian-sample-plugin.

### 20. Object.assign

Don't use `Object.assign(this.settings, data)` to mutate defaults.

### 21. Manifest & License

- `manifest.json` must have valid structure
- `LICENSE` must have correct copyright holder and current year
- Plugin ID: alphanumeric + dashes, no "obsidian", no "plugin" suffix
- Description: no "Obsidian", no "This plugin", must end with `. ? ! )`

### 22. Popout Window Compatibility

Use the popout-safe globals. Bare `document` and global timers target the main window only and break in popout windows.

```typescript
// NO
document.body.appendChild(el);
const t = setTimeout(cb, 500);
clearTimeout(t);
globalThis.myFlag = true;

// YES
activeDocument.body.appendChild(el);
const t = activeWindow.setTimeout(cb, 500);
activeWindow.clearTimeout(t);
```

Rules: `obsidianmd/prefer-active-doc` (warn), `obsidianmd/prefer-window-timers` (error, also covers `setInterval` and `requestAnimationFrame`), `obsidianmd/no-global-this` (error).

### 23. API Availability vs minAppVersion

Every API the code calls must exist in the Obsidian version declared as `minAppVersion`. `obsidianmd/no-unsupported-api` cross-checks usage against the manifest.

```typescript
// NO -- revealLeaf needs v1.7.2 but manifest says minAppVersion 1.5.0
await this.app.workspace.revealLeaf(leaf);

// YES -- raise minAppVersion to 1.7.2, or gate the call behind a version check
```

### 24. Use createEl Helpers

```typescript
// NO
document.createElement('iframe');
document.createDocumentFragment();
el.createEl('span', { text: file.path });

// YES
createEl('iframe');
createFragment();
el.createSpan({ text: file.path });
```

Rule `obsidianmd/prefer-create-el`. The review platform enforces it, but the rule is not yet in the npm release, so local ESLint misses it: check these patterns manually.

### 25. ESLint Directive Comments

Every `eslint-disable` directive needs a description, and some rules cannot be disabled at all (`obsidianmd/no-static-styles-assignment`, `obsidianmd/ui/sentence-case`).

```typescript
// NO
// eslint-disable-next-line obsidianmd/prefer-active-doc

// YES
// eslint-disable-next-line obsidianmd/prefer-active-doc -- main-window-only startup code
```

Enforced platform-side via `@eslint-community/eslint-comments/require-description` and `no-restricted-disable`; add the same plugin locally to catch them before release.

## Optional (Non-blocking)

- Remove unused variables and imports
- Use `AbstractInputSuggest` instead of copied `TextInputSuggest`
- Don't persist data in `localStorage` or `sessionStorage`. Use `Plugin.loadData()`/`saveData()` for plugin data (stored in the plugin's `data.json`, synced with the vault). For device-specific per-vault values (window positions, device caches), use `App.loadLocalStorage()`/`App.saveLocalStorage()`, which scope keys to the current vault. Raw `localStorage` is shared across all vaults on the device and never synced; `sessionStorage` does not survive a restart.

## Additional Best Practices

| Practice | Details |
|----------|---------|
| No `innerHTML`/`outerHTML` | Use `createEl`, `setText`, `sanitizeHTMLToDom` |
| Use `requestUrl()` | Instead of `fetch()` for network requests |
| CSS variables for theming | `--background-secondary`, `--text-muted`, etc. |
| Scope CSS | All plugin CSS scoped to plugin containers |
| Accessibility | `aria-label` on icon buttons, keyboard nav, focus indicators |
| Touch targets | Min 44x44px on mobile |
| Auto-cleanup | `registerEvent()`, `registerInterval()`, `register()` |
| No production logging | No `console.log` in `onload()`/`onunload()` |

## API Reference

See `references/obsidian-api-reference.md` in this skill directory for a condensed TypeScript API reference covering all key classes: Plugin, App, Vault, Workspace, MetadataCache, FileManager, Component, View, Modal, Setting, Menu, MarkdownRenderer, Platform, DOM helpers, and more.

For the full type definitions, read `node_modules/obsidian/obsidian.d.ts` in the project.

## Running Checks Locally

```bash
npm install --save-dev eslint-plugin-obsidianmd @eslint-community/eslint-plugin-eslint-comments
```

Configure ESLint with the obsidianmd recommended config plus the eslint-comments rules (`require-description`, `no-restricted-disable`). Lint `src/` AND `package.json` (the dependency rules only fire when `package.json` is linted). Run before publishing a release: the platform scans every GitHub release automatically.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Title Case in UI text | Sentence case everything |
| `el.style.display = 'none'` | `el.addClass('hp-hidden')` |
| `as string ?? ''` | `String(x ?? '')` |
| `createEl('h2', ...)` in modal | `new Setting(el).setName(...).setHeading()` |
| Async onOpen without await | Remove `async` keyword |
| Unhandled promise | Add `void`, `await`, or `.catch()` |
| `detachLeavesOfType` in onunload | Remove -- Obsidian handles it |
| `abstractFile as TFile` | `if (x instanceof TFile)` |
| `setTimeout(cb, ms)` | `activeWindow.setTimeout(cb, ms)` |
| `document.body` | `activeDocument.body` |
| `el.createEl('span', {...})` | `el.createSpan({...})` |
| Bare `// eslint-disable-next-line` | Append ` -- reason` description |
| New API with old `minAppVersion` | Raise `minAppVersion` to the API's version |
| `localStorage.setItem('key', v)` | `this.app.saveLocalStorage('key', v)` or `this.saveData(...)` |
