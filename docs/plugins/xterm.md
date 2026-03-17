# xterm Plugin

> Build, debug, and extend xterm.js terminal emulators in web, Electron, and Tauri apps. Covers addons, PTY wiring, theming, high-performance data handling, and browser quirks -- plus two commands for debugging and implementing features.

## Skills

### `xtermjs-skill`

Expert guidance for building, configuring, and integrating xterm.js (`@xterm/xterm`) terminal emulators.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | xterm, xterm.js, `@xterm/xterm`, web terminal, WebSSH, PTY, FitAddon, WebglAddon, SearchAddon, AttachAddon, node-pty |

**Coverage:**
- Installation and basic setup (Terminal constructor, `term.open()`)
- 9 official addons: FitAddon, AttachAddon, SearchAddon, WebglAddon, WebLinksAddon, ClipboardAddon, WebFontsAddon, Unicode11Addon, LigaturesAddon
- Backend integration: node-pty + WebSocket with resize sync
- Theming (full ANSI palette) and custom key handlers
- Search, decorations, markers, and parser hooks (custom OSC/CSI)
- React/Vue integration patterns with proper cleanup
- High-performance data handling: UTF-8 boundary reassembly, write coalescing, cursor ghosting fixes
- Stream interception: ConPTY quirks, paste sanitization, banner replacement
- Browser quirks: WebGL context loss after sleep, `display:none` init, tab-switch resize
- Viewport virtualization and coordinate translation for injected content

---

## Commands

### `/xterm-debug`

Diagnose and fix xterm.js terminal issues with a two-phase analysis: quick pitfall scan (18 known patterns) followed by deep architectural analysis.

```
/xterm-debug src/ --issue "terminal renders blank after tab switch"
/xterm-debug --shallow           # pitfall scan only
/xterm-debug --dry-run            # report without applying fixes
```

**Phase 1 (Pitfall Scan)** checks 18 known patterns including: blank terminal (P1), broken backspace (P2), staircase newlines (P3), WebGL context loss (P4), copy/paste (P5), Unicode width (P6), resize sync (P7-P8), memory leaks (P9), addon loading order (P10), timer race conditions (P11), scroll jumping (P12), ghost cursors (P13), duplicate paste (P14), stale PTY dimensions (P15), `display:none` init (P16), WebGL silent death after standby (P17), narrow columns after tab switch (P18).

**Phase 2 (Deep Analysis)** covers 6 categories: race conditions and timing (D1), error boundary gaps (D2), fragile assumptions (D3), performance under stress (D4), edge cases (D5), architecture quality (D6).

---

### `/xterm-implement`

Implement xterm.js features into existing terminal code. Reads your current setup and adds the requested feature without conflicts.

```
/xterm-implement "add WebGL rendering with fallback"
/xterm-implement "add search functionality" --path src/Terminal.tsx
```

**Supported features:** FitAddon, WebglAddon, SearchAddon, WebLinksAddon, ClipboardAddon, Unicode11Addon, AttachAddon, node-pty backend wiring, theming, custom key handlers, decorations/markers, parser hooks, React/Vue integration, ResizeObserver.

**Safety:** Reads all existing terminal code first. Checks for duplicate addon loads. Respects loading order (`open()` before WebGL, WebSocket open before AttachAddon). Matches existing code style. Surgical edits only -- does not rewrite entire components.

---

**Related:** [frontend](frontend.md) (UI polish and layout) | [react-development](react-development.md) (React performance for terminal host components)
