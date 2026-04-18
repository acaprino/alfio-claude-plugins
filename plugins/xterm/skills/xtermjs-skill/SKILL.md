---
name: xtermjs-skill
description: >
  Expert guidance for building, configuring, and integrating xterm.js terminal emulators in web and Electron applications. Use this skill whenever the user mentions xterm, xterm.js, @xterm/xterm, terminal emulator in the browser, web terminal, WebSSH, in-browser shell, or asks about addons like FitAddon, WebglAddon, SearchAddon, AttachAddon, or integration with node-pty. Also trigger for questions about ANSI/VT sequences, terminal theming, PTY over WebSocket, custom key handlers, parser hooks, or embedding a terminal in React/Vue/Angular/Electron apps.
  TRIGGER WHEN: the user mentions xterm, xterm.js, @xterm/xterm, terminal emulator in the browser, web terminal, WebSSH, in-browser shell, or asks about addons like FitAddon, WebglAddon, SearchAddon, AttachAddon, or integration with node-pty.
  DO NOT TRIGGER WHEN: the user wants a native OS terminal (not browser-based) or a non-xterm terminal library (e.g. VT100 emulator in Python).
---

# xterm.js Development Skill

xterm.js (`@xterm/xterm`) is a full-featured terminal emulator that runs in the browser or
Electron. It is NOT a shell -- it must be connected to a backend process (e.g. via node-pty +
WebSocket) to execute commands.

---

## 1. Installation

```bash
npm install @xterm/xterm
# Required addons (install only what you need):
npm install @xterm/addon-fit @xterm/addon-attach @xterm/addon-web-links \
            @xterm/addon-search @xterm/addon-webgl @xterm/addon-clipboard \
            @xterm/addon-web-fonts @xterm/addon-unicode11
```

Always import the CSS:
```html
<link rel="stylesheet" href="node_modules/@xterm/xterm/css/xterm.css" />
```
Or in JS/TS:
```ts
import '@xterm/xterm/css/xterm.css';
```

---

## 2. Basic Setup

```ts
import { Terminal } from '@xterm/xterm';

const term = new Terminal({
  cols: 80,
  rows: 24,
  cursorBlink: true,
  scrollback: 5000,
  fontFamily: '"Cascadia Code", Menlo, monospace',
  fontSize: 14,
  theme: {
    background: '#1e1e1e',
    foreground: '#d4d4d4',
    cursor: '#d4d4d4',
  },
});

term.open(document.getElementById('terminal')!);
term.write('Hello from \x1B[1;32mxterm.js\x1B[0m\r\n$ ');
```

**Critical**: Always call `term.open(element)` AFTER the element is in the DOM.
Use `\r\n` (not just `\n`) for newlines when writing directly.

---

## 3. Official Addons

| Addon | Package | Purpose |
|---|---|---|
| FitAddon | `@xterm/addon-fit` | Resize terminal to fill its container |
| AttachAddon | `@xterm/addon-attach` | Connect to a WebSocket backend |
| SearchAddon | `@xterm/addon-search` | In-terminal text search |
| WebglAddon | `@xterm/addon-webgl` | GPU-accelerated WebGL2 renderer |
| WebLinksAddon | `@xterm/addon-web-links` | Clickable URLs |
| ClipboardAddon | `@xterm/addon-clipboard` | Browser clipboard integration |
| WebFontsAddon | `@xterm/addon-web-fonts` | Wait for web fonts before rendering |
| Unicode11Addon | `@xterm/addon-unicode11` | Unicode 11 character width support |
| LigaturesAddon | `@xterm/addon-ligatures` | Font ligature support (DEPRECATED with Canvas renderer removal; prefer WebGL + font features) |

### Loading addons

```ts
import { FitAddon } from '@xterm/addon-fit';
import { WebglAddon } from '@xterm/addon-webgl';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { SearchAddon } from '@xterm/addon-search';

const fitAddon = new FitAddon();
const searchAddon = new SearchAddon();

term.loadAddon(fitAddon);
term.loadAddon(searchAddon);
term.loadAddon(new WebLinksAddon());

term.open(document.getElementById('terminal')!);

// WebGL: load AFTER open(), handle fallback
try {
  const webgl = new WebglAddon();
  webgl.onContextLoss(() => webgl.dispose()); // fallback on context loss
  term.loadAddon(webgl);
} catch {
  console.warn('WebGL2 not available, falling back to canvas renderer');
}

fitAddon.fit();
```

---

## 4. FitAddon: Responsive Resizing

FitAddon resizes cols/rows to fit the container's pixel dimensions.

```ts
// Resize on window resize
const ro = new ResizeObserver(() => fitAddon.fit());
ro.observe(document.getElementById('terminal')!);

// Or with window resize event (less precise):
window.addEventListener('resize', () => fitAddon.fit());
```

**Gotcha**: Container must have explicit dimensions (CSS `width`/`height`).
FitAddon returns `undefined` if the container has zero size.

---

## 5. Backend Integration: node-pty + WebSocket

### Frontend (AttachAddon)

```ts
import { AttachAddon } from '@xterm/addon-attach';

const socket = new WebSocket('ws://localhost:3000/ws');
const attachAddon = new AttachAddon(socket);
term.loadAddon(attachAddon);

// Sync terminal resize with PTY on the server
term.onResize(({ cols, rows }) => {
  socket.send(JSON.stringify({ type: 'resize', cols, rows }));
});
```

### Backend (Node.js + node-pty)

```ts
import * as pty from 'node-pty';
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 3000 });

wss.on('connection', (ws) => {
  const shell = process.platform === 'win32' ? 'powershell.exe' : 'bash';
  const ptyProcess = pty.spawn(shell, [], {
    name: 'xterm-color',
    cols: 80,
    rows: 24,
    env: process.env,
  });

  ptyProcess.onData((data) => ws.send(data));
  ws.on('message', (msg) => {
    const parsed = JSON.parse(msg.toString());
    if (parsed.type === 'resize') {
      ptyProcess.resize(parsed.cols, parsed.rows);
    } else {
      ptyProcess.write(msg.toString());
    }
  });
  ws.on('close', () => ptyProcess.kill());
});
```

For simple bidirectional use (no resize), AttachAddon handles piping automatically;
manual `term.onData` / `pty.onData` wiring is only needed for custom protocols.

---

## 6. Manual Data Wiring (without AttachAddon)

```ts
// PTY → terminal
ptyProcess.onData((data) => term.write(data));

// Terminal → PTY (user keystrokes)
term.onData((data) => ptyProcess.write(data));

// Binary events (e.g., certain mouse reports)
term.onBinary((data) => ptyProcess.write(data));
```

---

## 7. Theming

Pass an `ITheme` object in options or use `term.options.theme = {...}` at runtime:

```ts
const darkTheme = {
  background: '#0d1117',
  foreground: '#c9d1d9',
  cursor: '#58a6ff',
  cursorAccent: '#0d1117',
  selectionBackground: '#264f78',
  black:   '#484f58', red:     '#ff7b72', green:   '#3fb950', yellow:  '#d29922',
  blue:    '#58a6ff', magenta: '#bc8cff', cyan:    '#39c5cf', white:   '#b1bac4',
  brightBlack:   '#6e7681', brightRed:   '#ffa198', brightGreen:  '#56d364',
  brightYellow:  '#e3b341', brightBlue:  '#79c0ff', brightMagenta:'#d2a8ff',
  brightCyan:    '#56d4dd', brightWhite: '#f0f6fc',
};

// Apply at construction
const term = new Terminal({ theme: darkTheme });

// Or update at runtime
term.options.theme = darkTheme;
```

---

## 8. Key Event Handling

```ts
// Intercept keys before terminal processes them
// Return false to suppress, true to allow
term.attachCustomKeyEventHandler((ev: KeyboardEvent) => {
  // Example: Ctrl+Shift+C → copy
  if (ev.ctrlKey && ev.shiftKey && ev.key === 'C') {
    // Modern clipboard API (navigator.clipboard requires HTTPS/localhost)
    const selection = term.getSelection();
    if (selection) navigator.clipboard.writeText(selection);
    return false; // don't pass to terminal
  }
  return true;
});
```

---

## 9. Search (SearchAddon)

```ts
// Find next/previous
searchAddon.findNext('search term', {
  regex: false,
  wholeWord: false,
  caseSensitive: false,
  incremental: false,       // true = highlight while typing
  decorations: {
    matchBackground: '#ffff0040',
    matchBorder: '#ffff00',
    matchOverviewRuler: '#ffff00',
    activeMatchBackground: '#ff000080',
    activeMatchBorder: '#ff0000',
    activeMatchColorOverviewRuler: '#ff0000',
  },
});
searchAddon.findPrevious('search term');
```

---

## 10. Decorations and Markers

```ts
// Add a marker on the current row
const marker = term.registerMarker(0); // 0 = current row offset

// Add a decoration (e.g. highlight a line)
const decoration = term.registerDecoration({
  marker,
  overviewRulerOptions: { color: '#ff0000' },
});

decoration?.onRender((element) => {
  element.style.backgroundColor = 'rgba(255,0,0,0.2)';
});
```

---

## 11. Parser Hooks (Custom Sequences)

```ts
// Register a custom OSC sequence handler (e.g. OSC 1337)
term.parser.registerOscHandler(1337, (data: string) => {
  console.log('Custom OSC 1337 payload:', data);
  return true; // handled
});

// Register a custom CSI sequence handler
term.parser.registerCsiHandler({ final: 'z' }, (params) => {
  console.log('Custom CSI z params:', params);
  return true;
});
```

---

## 12. React Integration Pattern

```tsx
import { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

export function XTerminal() {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);

  useEffect(() => {
    const term = new Terminal({ cursorBlink: true });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current!);
    fitAddon.fit();
    termRef.current = term;

    const ro = new ResizeObserver(() => fitAddon.fit());
    ro.observe(containerRef.current!);

    return () => {
      ro.disconnect();
      term.dispose();
    };
  }, []);

  return <div ref={containerRef} style={{ width: '100%', height: '400px' }} />;
}
```

---

## 13. Common Pitfalls

| Problem | Cause | Fix |
|---|---|---|
| Terminal renders blank / wrong size | FitAddon called before DOM paint | Call `fitAddon.fit()` after `open()`, use `ResizeObserver` |
| Characters appear wrong width | Unicode handling | Load `Unicode11Addon`, call `term.unicode.activeVersion = '11'` |
| Backspace doesn't work | PTY not connected / wrong escape | Send `\x7f` or `\x08`; check PTY termios settings |
| Copy/paste broken on some browsers | Browser security | Use `ClipboardAddon` and ensure HTTPS or localhost |
| WebGL context lost after tab switch | GPU resource reclaim | `webgl.onContextLoss(() => webgl.dispose())` |
| Terminal doesn't fill container | Container has no height | Set explicit CSS `height` on container element |
| `\n` without `\r` causes staircase | Missing carriage return | Use `\r\n` or enable `convertEol: true` in options |

---

## 14. Key Terminal Options Reference

```ts
const term = new Terminal({
  cols: 80,              // initial columns
  rows: 24,              // initial rows
  cursorBlink: true,     // blinking cursor
  cursorStyle: 'block',  // 'block' | 'underline' | 'bar'
  scrollback: 10000,     // scrollback buffer lines
  tabStopWidth: 4,       // tab stop width
  convertEol: false,     // auto-add \r on \n (avoid for real PTY)
  disableStdin: false,   // read-only mode
  allowProposedApi: false, // enable experimental APIs
  allowTransparency: false, // transparent background support
  windowsPty: undefined, // pass { backend: 'conpty' | 'winpty', buildNumber } for Windows PTY (v5+; replaces deprecated windowsMode)
  macOptionIsMeta: false, // treat Option key as Meta (macOS)
  rightClickSelectsWord: false,
  fontSize: 14,
  fontFamily: 'monospace',
  fontWeight: 'normal',
  fontWeightBold: 'bold',
  lineHeight: 1.0,
  letterSpacing: 0,
  logLevel: 'info',      // 'debug' | 'info' | 'warn' | 'error' | 'off'
});
```

---

## 15. High-Performance Data Handling

When connected to high-throughput backends (LLMs, build tools, log streams), naive patterns cause UI freezes and data corruption.

### UTF-8 Boundary Handling

Multi-byte UTF-8 sequences can be split across read chunks from the PTY. The reader must maintain a remainder buffer to reassemble them before passing to `term.write()`.

### Coalescing PTY Output with React State

Do NOT synchronize React state on every PTY `onData` chunk -- hundreds per second during heavy output will freeze the UI.

- Use intermediate buffers to accumulate data
- Use `requestAnimationFrame` to extract terminal state (cursor position, buffer length, bookmarks) at most 60 times per second
- Never call `term.refresh()` during active output -- it resets scroll position. Use a debounced timer for manual refreshes

### Cursor Ghosting During Rapid Output

During fast PTY output (LLM streaming, build logs), the cursor appears and disappears at random positions creating a flickering/ghost effect.

Fix: Hide cursor during ALL PTY writes with `term.write('\x1b[?25l')`, then use a debounced timer (80-100ms) that restores the cursor only when output stabilizes. Consolidate cursor movement detection into a single regex instead of multiple sequential string scans.

### Viewport Index Calculation

To read the correct buffer line, always use `buffer.baseY + buffer.cursorY` for the absolute index. Using `cursorY` alone reads from the top of the scrollback, not the current viewport row.

### Throttling Expensive UI Updates

Components that re-render based on terminal state (minimap, bookmarks, line counters) must throttle updates:

- Throttle minimap/canvas re-renders to 150ms with a trailing render guarantee
- Cap hardware pixel dimensions for canvas elements at high DPR to avoid GPU limits
- Coalesce bookmark sync via `requestAnimationFrame` instead of per-chunk updates

---

## 16. Stream Interception & ANSI Manipulation

Before calling `term.write()`, the data stream may need preprocessing:

### ConPTY Windows Quirks

Windows ConPTY corrupts supplementary plane characters (emoji) when passed through `CreateProcessW`. Strip or replace emoji from text before passing to ConPTY to prevent lone surrogates corrupting the data stream.

When the shell resolves to a `.cmd`/`.bat` shim, cmd.exe metacharacters in arguments can cause injection. Use cmd.exe-specific quoting: `""` for embedded quotes and `%%` for percent signs.

### Paste Sanitization

Terminal control characters in pasted text can inject commands or corrupt output. Sanitize pasted text by filtering terminal output control characters. Block the native paste event with `preventDefault()` to prevent double-paste, and add a debounce guard for rapid paste events.

### Banner/Output Interception

To replace or filter backend output (e.g. replacing a startup banner with custom content):

1. Buffer initial PTY output until a known delimiter is detected
2. Replace the buffered content with custom output
3. On screen clear events (`ESC[2J`), re-activate the interception to handle redraws (e.g. on window resize)
4. During post-replacement cooldown, filter positioning sequences (CUP) that would overwrite the replacement, but preserve printable content

Prefer HTML overlay approaches (React component with CSS fade-out) over inline ANSI manipulation when possible -- inline approaches conflict with CUP offset tracking.

---

## 17. Browser Quirks & WebGL Resiliency

### Container Initialization

NEVER use `display: none` on the xterm container during initialization -- `cols`/`rows` calculation will fail. Use `visibility: hidden` instead, or mount the component only when visible.

### WebGL Context Loss After Sleep/Standby

A single `onContextLoss` callback is insufficient. After system sleep/standby, the WebGL context dies silently and the addon callback often does not fire.

Use a 3-layer detection strategy:
1. Addon callback: `webglAddon.onContextLoss(() => fallbackToCanvas())`
2. DOM event: listen for `webglcontextlost` on the canvas element generated by the addon
3. Periodic health check: timer that verifies the WebGL context is still valid

All three layers should trigger automatic fallback to the canvas renderer.

### Tab Switching

Defer `fitAddon.fit()` to the next `requestAnimationFrame` when switching tabs, to give the DOM time to update container dimensions. Fitting immediately causes narrow columns.

### Resize Throttling

Throttle terminal resize events to prevent a burst of resize messages to the backend PTY. Also reset PTY size tracking after spawning a new process to avoid stale column counts from the previous session.

---

## 18. Viewport Virtualization & Coordinate Translation

When injecting custom content (banners, status bars) that the backend PTY does not know about, absolute cursor positioning (CUP sequences) breaks because the backend's row count does not match the frontend's.

### Pattern: Coordinate Lying

1. **Lie about dimensions**: Subtract the offset of injected rows before sending dimensions to the PTY (both at spawn and on resize)
2. **Clamp values**: Always enforce a minimum (e.g. `Math.max(10, rows - OFFSET)`) to prevent backend crashes on tiny terminals
3. **Intercept and translate**: Use a stream middleware to intercept incoming CUP sequences (`\x1b[<row>;<col>H`), adding the offset back before passing to `term.write()`

```ts
// Example: frontend has 30 rows, custom banner is 12 rows
const CUP_ROW_OFFSET = 12; // derive from banner content, not magic number

// Lie to PTY on spawn and resize
term.onResize(({ cols, rows }) => {
  const virtualRows = Math.max(10, rows - CUP_ROW_OFFSET);
  socket.send(JSON.stringify({ type: 'resize', cols, rows: virtualRows }));
});
```

Derive the offset from the actual content size (e.g. `bannerLines.length`) rather than hardcoding magic numbers. When the injected content can change (resize-triggered redraw), re-derive the offset dynamically.

---

## 19. Disposal

Always dispose to prevent memory leaks:

```ts
term.dispose();         // disposes terminal and all loaded addons
fitAddon.dispose();     // or dispose individual addons
marker.dispose();       // markers and decorations
decoration.dispose();
```

---

## References

- API docs: https://xtermjs.org/docs/api/terminal/classes/terminal/
- Addon docs: https://xtermjs.org/docs/guides/using-addons/
- Parser hooks: https://xtermjs.org/docs/guides/hooks/
- GitHub: https://github.com/xtermjs/xterm.js
- node-pty: https://github.com/microsoft/node-pty
