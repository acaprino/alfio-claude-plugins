# Obsidian TypeScript API - Quick Reference

The Obsidian API surface is fully typed in `node_modules/obsidian/obsidian.d.ts`. The official reference lives at https://docs.obsidian.md/Reference/TypeScript+API. This file is just the navigation index plus the few quirks worth knowing locally.

## When to use

Looking up a class, method, or event signature while writing a plugin. For deeper API behavior (lifecycle, threading, when each event fires), the `.d.ts` source is authoritative -- read it.

## The classes you'll touch in 95% of plugins

- `Plugin` (extends `Component`) -- `onload()`, `onunload()`, `addCommand()`, `addSettingTab()`, `addRibbonIcon()`, `registerView()`, `registerMarkdownPostProcessor()`, `loadData()`/`saveData()`, plus `app: App` and `manifest: PluginManifest`
- `App` -- the root: `vault`, `workspace`, `metadataCache`, `fileManager`, `keymap`, `scope`, `isDarkMode()`
- `Vault` (extends `Events`) -- file operations: `read()`/`cachedRead()`, `create()`, `modify()`, `process()` (the safer modify), `delete()`/`trash()`, plus events `create`/`delete`/`rename`/`modify`
- `Workspace` (extends `Events`) -- panes/leaves: `getLeaf()`, `getActiveFile()`, `openLinkText()`, `onLayoutReady()`, plus events `active-leaf-change`, `file-open`, `layout-change`
- `MetadataCache` -- `getFileCache()`, `resolvedLinks`, `unresolvedLinks`, plus events `changed`, `resolve`, `resolved`
- `Component` -- the lifecycle base: `addChild()`, `register()`, `registerEvent()`, `registerDomEvent()`, `registerInterval()`
- `View` / `ItemView` -- custom panes
- `Modal` / `SuggestModal<T>` / `AbstractInputSuggest<T>` -- dialogs and pickers
- `Setting` -- the settings tab builder (`addToggle`, `addText`, `addDropdown`, `addSlider`, `addColorPicker`, `addProgressBar`, `then`, ...)
- `Menu` / `MenuItem` -- context menus
- `Notice` -- toast messages

## File types

- `TAbstractFile` -- base (path, name, parent)
- `TFile` -- adds `stat: { ctime, mtime, size }`, `basename`, `extension`
- `TFolder` -- adds `children: TAbstractFile[]`, `isRoot()`

## Helper functions worth knowing

- `requestUrl(...)` -- HTTP client that bypasses CORS (the right way to fetch from a plugin)
- `sanitizeHTMLToDom(html)` -- safe HTML insertion
- `normalizePath(path)` -- normalize cross-platform paths
- `requireApiVersion('1.4.0')` -- gate features by Obsidian version
- `addIcon(id, svg)` / `getIcon(id)` -- custom icon registration
- `moment` -- the global moment.js instance (use this, don't bundle your own)

## HTMLElement extensions (Obsidian augments DOM)

Obsidian adds methods to `HTMLElement.prototype`. Use these instead of vanilla DOM where they exist:
- `createEl()`, `createDiv()`, `createSpan()`, `createSvg()` -- typed element creation with `DomElementInfo` shorthand (`cls`, `text`, `attr`, `parent`)
- `setText()`, `getText()` -- text content
- `addClass()` / `removeClass()` / `toggleClass()` / `hasClass()` -- class manipulation
- `setAttr()` / `setAttrs()` / `getAttr()` -- attribute manipulation
- `show()` / `hide()` / `toggle()` -- visibility
- `setCssStyles()` / `setCssProps()` / `getCssPropertyValue()` -- CSS

## Platform detection

Static `Platform` namespace: `isDesktop`, `isMobile`, `isDesktopApp`, `isMobileApp`, `isIosApp`, `isAndroidApp`, `isPhone`, `isTablet`, `isMacOS`, `isWin`, `isLinux`, `isSafari`. Useful for gating `addStatusBarItem()` (desktop-only) and similar.

## Gotchas (the few worth memorizing)

- **`vault.read()` always re-reads from disk; `vault.cachedRead()` reads from Obsidian's cache.** For UI/preview/quick lookups use `cachedRead()`; only use `read()` when you need bytes-on-disk freshness (e.g. before editing).
- **`vault.process()` is safer than `read()` + `modify()`** -- it's atomic and prevents lost-write races when multiple plugins edit the same file.
- **`vault.trash(file, system)` honors the user's "Files and links → Deleted files" setting** when `system: false`. Use it instead of `delete()` for user-initiated deletions.
- **Use `Component`'s `register*` methods** (`registerEvent`, `registerDomEvent`, `registerInterval`) -- they auto-cleanup on `unload`. Manual `addEventListener` without registering = leak.
- **`onLayoutReady(callback)`** is the right place for code that needs the workspace populated -- not `onload()`. Vault iteration in `onload()` will miss files until layout is ready.
- **`requestUrl()`, NOT `fetch()`**, for HTTP from a plugin -- `fetch` is subject to web CORS, `requestUrl` is the desktop/mobile API that bypasses it.
- **`addStatusBarItem()` is desktop-only** -- gate with `Platform.isDesktopApp`.
- **`processFrontMatter(file, fn)`** is the right way to edit YAML frontmatter -- don't regex-edit the file content.

## Official docs

- TypeScript API reference: https://docs.obsidian.md/Reference/TypeScript+API
- Plugin developer docs: https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin
- Sample plugin (the canonical starter): https://github.com/obsidianmd/obsidian-sample-plugin
- API source (.d.ts): https://github.com/obsidianmd/obsidian-api/blob/master/obsidian.d.ts
- Plugin guidelines (review checklist): https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines
- Releasing a plugin: https://docs.obsidian.md/Plugins/Releasing/Submit+your+plugin
- Community hub (submission dashboard, replaces the PR workflow since May 2026): https://community.obsidian.md
- Workflow change announcement: https://obsidian.md/blog/future-of-plugins/

## Related

- The plugin's main `SKILL.md` -- automated review rules consolidated as a checklist with bad/good code examples
