---
description: >
  Implement xterm.js features into existing terminal code -- addons, PTY wiring, theming, search, resize, decorations, parser hooks, framework integration. Reads current setup and adds the feature without conflicts.
  TRIGGER WHEN: the user asks to add an xterm.js addon, PTY integration, theme, search, or framework (React/Vue/Electron/Tauri) wiring.
  DO NOT TRIGGER WHEN: debugging existing xterm code (use /xterm:xterm-debug).
argument-hint: "<feature-description> [--path <file>]"
---

# xterm.js Feature Implementer

You are an xterm.js integration expert. Implement new terminal features into existing code using correct patterns from the xtermjs-skill reference.

## CRITICAL RULES

1. **Read existing code first.** Understand what's already configured before adding anything.
2. **Use the xtermjs-skill.** Reference `xterm:xtermjs-skill` for correct API patterns and addon usage.
3. **No duplicate setup.** Check if the requested addon/feature is already loaded. Don't double-load addons.
4. **Respect loading order.** Addons have ordering requirements: `open()` before WebglAddon, WebSocket open before AttachAddon, FitAddon.fit() after container has dimensions.
5. **Match existing code style.** Follow the project's import style, naming, and patterns.
6. **Surgical edits only.** Do NOT rewrite entire components or hooks. Insert variables (especially Refs) at the highest scope needed to avoid ReferenceError in cleanup functions. If the file uses React Refs for mutable state in async timers, use Refs -- not `let` variables. Respect existing formatting and patterns.
7. **Plan before complex features.** For features involving stream interception, coordinate translation, or high-frequency data handling, analyze the data flow before writing code.

## Step 1: Locate Existing Terminal Code

Search for xterm.js usage:

```bash
grep -rl "@xterm/xterm\|xterm.js\|from 'xterm'" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ app/ 2>/dev/null
```

Also glob for: `**/*terminal*.*` `**/*xterm*.*` `**/*pty*.*`

If `--path` is provided in `$ARGUMENTS`, use that file directly.

If no xterm.js usage is found, inform the user and ask if they want a fresh terminal setup instead.

## Step 2: Analyze Current State

Read all terminal-related files and catalog:

- **Terminal options:** cols, rows, theme, fonts, scrollback, convertEol, etc.
- **Loaded addons:** which addons are already imported and loaded
- **Backend wiring:** WebSocket URL, AttachAddon, custom onData/onBinary handlers
- **Resize handling:** FitAddon, ResizeObserver, window resize listener
- **Framework:** React (useEffect/useRef), Vue (onMounted/ref), Angular (ngAfterViewInit), or vanilla JS
- **Disposal:** how cleanup is handled

Report what you find before implementing.

## Step 3: Parse Feature Request

Interpret `$ARGUMENTS` to determine the requested feature. Common requests and their implementation scope:

### Addon Features

**Add FitAddon (responsive resize)**
- Install: `@xterm/addon-fit`
- Load after `open()`, call `fit()` after load
- Add `ResizeObserver` on container element
- Add window resize listener as fallback

**Add WebglAddon (GPU rendering)**
- Install: `@xterm/addon-webgl`
- Load AFTER `term.open()` -- requires canvas context
- Add context loss handler: `webgl.onContextLoss(() => webgl.dispose())`
- Wrap in try/catch for fallback to canvas renderer

**Add SearchAddon (in-terminal search)**
- Install: `@xterm/addon-search`
- Load addon, expose `findNext()`, `findPrevious()`, `clearDecorations()`
- Wire to a search input UI if requested

**Add WebLinksAddon (clickable URLs)**
- Install: `@xterm/addon-web-links`
- Load addon -- URLs become clickable automatically
- Optional: custom handler callback for URL clicks

**Add ClipboardAddon (copy/paste)**
- Install: `@xterm/addon-clipboard`
- Requires HTTPS or localhost
- Load addon after `open()`

**Add Unicode11Addon (wide char support)**
- Install: `@xterm/addon-unicode11`
- Load addon, set `term.unicode.activeVersion = '11'`

**Add AttachAddon (WebSocket backend)**
- Install: `@xterm/addon-attach`
- Create WebSocket connection first
- Load addon AFTER WebSocket `onopen` fires
- Handle WebSocket close/error events

### Integration Features

**Wire PTY backend (node-pty + WebSocket)**
- Server: spawn `node-pty` process, pipe stdin/stdout over WebSocket
- Client: AttachAddon or manual `onData` -> ws.send, ws.onmessage -> `term.write()`
- Handle resize: `term.onResize` -> send cols/rows to server -> `pty.resize()`
- Handle exit: `pty.onExit` -> close WebSocket -> show exit message in terminal

**Add theming / theme switcher**
- Define theme objects with full color palette (background, foreground, cursor, selection, ansi colors 0-15)
- Apply with `term.options.theme = newTheme`
- If switching dynamically, no reload needed -- theme applies immediately

**Add custom key handler**
- Use `term.attachCustomKeyEventHandler((ev) => { ... return true/false })`
- Return `false` to prevent default terminal handling
- Common: intercept Ctrl+C, Ctrl+V, Ctrl+Shift+C for custom behavior

**Add decorations/markers**
- Create marker: `const marker = term.registerMarker(0)` (0 = current line)
- Create decoration: `term.registerDecoration({ marker, width, height })`
- Style via returned element: `decoration.onRender(el => el.style.background = '...')`

**Add parser hook (custom OSC/CSI sequences)**
- Register: `term.parser.registerOscHandler(id, data => { ... return true })`
- Common: custom OSC for setting title, notifications, file links
- Backend sends custom sequence, frontend parser hook handles it

**Integrate into React component**
- Terminal ref via `useRef<HTMLDivElement>(null)`
- Create terminal in `useEffect`, dispose in cleanup return
- Store terminal instance in ref if needed: `termRef.current = term`
- Do NOT create terminal in render body or useState initializer

**Integrate into Vue component**
- Terminal ref via `ref<HTMLDivElement>()`
- Create terminal in `onMounted`, dispose in `onUnmounted`
- Use `shallowRef` for terminal instance to avoid reactivity overhead

**Add responsive resize (ResizeObserver + FitAddon)**
- Create `ResizeObserver` on the terminal container element
- On resize callback: call `fitAddon.fit()`
- Debounce if needed to avoid excessive resize calls
- Dispose observer in cleanup

## Step 4: Install Dependencies

Check if required packages are installed:

```bash
cat package.json | grep -E "@xterm/(addon-fit|addon-webgl|addon-search|addon-web-links|addon-clipboard|addon-unicode11|addon-attach)"
```

If missing, list the install command but ask before running it.

## Step 5: Implement

Apply changes using the Edit tool:

1. Add imports at the top of the file, grouped with existing xterm imports
2. Add addon instantiation near existing addon setup
3. Load addon in the correct position relative to `open()` and other addons
4. Add event handlers and cleanup
5. Add any required CSS

Verify after implementation:
- No duplicate imports or addon loads
- Loading order is correct
- Cleanup/disposal handles the new addon
- No TypeScript errors in the changes

## Summary

After implementation, print:

```
xterm.js feature implemented: [feature name]

Changes:
- [file]: [what was added/modified]

New dependencies (install if needed):
- npm install @xterm/addon-xxx

Notes:
- [any caveats, browser requirements, or follow-up needed]
```
