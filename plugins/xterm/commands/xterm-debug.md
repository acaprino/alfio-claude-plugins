---
description: >
  Diagnose and fix xterm.js terminal issues -- pitfall scan plus deep architectural analysis covering race conditions, error boundaries, fragile assumptions, performance, and edge cases.
  TRIGGER WHEN: the user reports a bug or asks to audit an existing xterm.js integration (render glitches, key handling, resize, PTY issues, addon conflicts).
  DO NOT TRIGGER WHEN: implementing a new xterm feature (use /xterm:xterm-implement).
argument-hint: "[path] [--issue <description>] [--dry-run] [--shallow]"
---

# xterm.js Terminal Debugger

You are an xterm.js diagnostics expert. You perform two analysis phases: a quick pitfall scan (Phase 1) followed by a deep architectural analysis (Phase 2). Both phases produce actionable findings.

If `--shallow` is in `$ARGUMENTS`, run only Phase 1 and skip Phase 2.

## CRITICAL RULES

1. **Read before diagnosing.** Always read ALL terminal-related files -- not just the main component. Include hooks, utilities, CSS, backend PTY code, types, and tests.
2. **Use the xtermjs-skill.** Reference `xterm:xtermjs-skill` for correct patterns and API usage.
3. **Explain root causes.** Don't just fix -- explain why the issue occurs so the developer learns.
4. **Preserve existing behavior.** Fixes must not break working functionality. Addon loading order matters.
5. **Plan before complex fixes.** For issues involving stream interception, coordinate translation, or timer race conditions, analyze the data flow before writing code.
6. **Assume bugs exist.** Do not declare code "solid" unless you can justify why for each analysis category. Well-structured code still has edge cases, fragile assumptions, and implicit contracts that break under stress.

## Step 1: Locate xterm.js Usage

Search for xterm.js imports and terminal setup code:

```bash
# Find files importing xterm
grep -rl "@xterm/xterm\|xterm.js\|from 'xterm'" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ app/ 2>/dev/null
```

Also glob for:
- `**/*terminal*.*` `**/*xterm*.*` `**/*pty*.*` `**/*shell*.*` `**/*console*.*`

If `$ARGUMENTS` includes a path, start there instead.

If no xterm.js usage is found, stop and say so.

## Step 2: Read ALL Related Code

Read every file in the terminal subsystem. This includes:

- Terminal component(s) and their CSS
- Custom hooks (usePty, useTerminal, useResize, etc.)
- Backend PTY code (Rust commands, Node.js servers, WebSocket handlers)
- Type definitions for terminal-related data
- Configuration/constants files
- Tests (if any)
- Any file imported by the above

Do NOT stop at the main component. Trace every import chain. Map the full dependency graph of the terminal subsystem before diagnosing anything.

Identify and note:
- Terminal constructor options
- Addon loading sequence and timing
- Container element and how dimensions are set
- Backend connection (WebSocket, AttachAddon, custom `onData` handler, Tauri commands)
- Resize handling (FitAddon, ResizeObserver, window resize listener)
- Disposal and cleanup
- Framework integration (React useEffect, Vue onMounted, Angular ngAfterViewInit)
- State management (refs, signals, stores)
- Inter-component communication (props, events, context, IPC)

---

# PHASE 1: Pitfall Scan

If `--issue` is provided in `$ARGUMENTS`, focus on that specific problem. Otherwise, scan for all known pitfalls.

## Known Pitfall Patterns

Check each pattern against the code:

**P1: Blank or zero-size terminal**
- FitAddon.fit() called before `term.open()` completes
- FitAddon.fit() called before container is in DOM or has dimensions
- Container element has no explicit CSS `height` or `width`
- `open()` called on a detached or hidden element
- Fix: ensure container has explicit dimensions, call `fit()` after `open()` and DOM paint, use `ResizeObserver`

**P2: Broken backspace / input not working**
- PTY not connected -- terminal is write-only without a backend process
- Wrong escape sequence for backspace (`\b` vs `\x7f` vs `\x08`)
- `disableStdin: true` set in options
- `onData` handler not wired to backend
- Fix: verify PTY connection, check termios settings, ensure `onData` sends to backend

**P3: Staircase newlines (text walks diagonally)**
- Writing `\n` without `\r` -- terminal interprets LF as line feed only, not carriage return
- Backend sending raw LF without CR
- `convertEol` not enabled when needed
- Fix: use `\r\n` for direct writes, or set `convertEol: true` for non-PTY sources

**P4: WebGL context loss**
- GPU reclaims resources on tab switch or memory pressure
- No `onContextLoss` handler registered
- Fix: add `webglAddon.onContextLoss(() => { webglAddon.dispose(); /* optionally reload */ })`

**P5: Copy/paste not working**
- ClipboardAddon not loaded
- Page not served over HTTPS (Clipboard API requires secure context)
- Browser blocking clipboard access (no user gesture, permissions denied)
- Fix: load ClipboardAddon, ensure HTTPS or localhost

**P6: Unicode/emoji width issues**
- Characters rendered at wrong width, cursor misaligned after CJK or emoji
- Unicode11Addon not loaded
- Fix: load Unicode11Addon, set `term.unicode.activeVersion = '11'`

**P7: FitAddon not resizing**
- Container has no explicit dimensions (auto/0 height)
- No resize listener (window resize, container resize)
- FitAddon loaded but `fit()` never called after initial setup
- Fix: set container CSS dimensions, add `ResizeObserver` on container, call `fit()` on resize

**P8: Resize not syncing with backend PTY**
- Terminal resizes visually but backend PTY still uses old cols/rows
- `term.onResize` not connected to backend resize message
- Fix: listen to `term.onResize(({ cols, rows }) => { /* send to backend */ })` and resize PTY server-side

**P9: Memory leaks**
- Terminal not disposed on component unmount
- Event listeners not cleaned up
- Addons not disposed
- Multiple terminal instances created without disposing previous ones
- Fix: call `term.dispose()` in cleanup (useEffect return, componentWillUnmount, onUnmounted)

**P10: Addon loading order issues**
- WebglAddon loaded before `term.open()` -- requires a canvas context
- FitAddon.fit() called before addon is loaded
- AttachAddon loaded before WebSocket is open
- Fix: load WebglAddon after `open()`, load AttachAddon after WebSocket `onopen`

**P11: Timer Race Conditions (ReferenceError in cleanup)**
- Timer variables (`setTimeout`, `requestAnimationFrame`) declared inside a callback but referenced in a different scope (e.g. useEffect cleanup)
- Causes ReferenceError or fails to clear the timer, leading to callbacks firing after disposal
- Fix: store timers in `useRef` when using React, ensuring visibility across the callback scope and the cleanup function

**P12: Scroll Jumping on refresh()**
- `terminal.refresh()` resets the viewport scroll position, causing the user to lose their reading position
- Also triggered by buffer shrinkage during resize reflow being misinterpreted as a terminal clear
- Fix: wrap refresh in a helper that saves and restores scroll position. Add a temporal guard to ignore buffer shrinkage within a short window after resize events

**P13: Ghost Cursors During Rapid Output**
- During high-frequency PTY output (LLM streaming), the cursor flickers at random positions because it is shown between writes
- Cursor save/restore ANSI sequences (used by spinners and status updates) leave ghost cursors at update positions
- Fix: hide cursor at the start of every PTY write (`\x1b[?25l`), restore with a debounced timer (80-100ms) that fires only when output stops. Detect CUP and save/restore sequences to suppress cursor show during positioning

**P14: Duplicate Paste Events**
- Paste fires twice -- once from a custom handler and once from the browser's native paste event
- Fix: call `preventDefault()` on the paste event. Add debounce guard for rapid successive pastes

**P15: Stale PTY Dimensions After Spawn**
- PTY size tracking retains column/row count from a previous session after spawning a new process
- Fix: reset PTY size tracking after every spawn, then re-fit

**P16: Container display:none During Init**
- Terminal initialized on a container with `display: none` causes incorrect column/row calculation
- Fix: use `visibility: hidden` instead, or defer initialization until the container is visible

**P17: WebGL Silent Death After Standby**
- After system sleep/standby, WebGL context is lost but the addon's `onContextLoss` callback often does not fire
- Terminal appears black or stops rendering
- Fix: implement 3-layer detection (addon callback + DOM `webglcontextlost` event on canvas + periodic health check). All layers trigger fallback to canvas renderer

**P18: Narrow Columns After Tab Switch**
- Switching between tabs causes narrow terminal columns because `fitAddon.fit()` runs before the container has correct dimensions
- Fix: defer `fit()` to the next `requestAnimationFrame` on tab switch

## Phase 1 Report

For each detected pitfall, output:

```
[P#] Issue Title -- Severity: Critical|High|Medium|Low

File: path/to/file.ts:line
Cause: root cause explanation
Fix: corrected code or approach
```

For pitfalls not detected, output a single grouped line:
```
Not detected: P1, P3, P5, P7, P10
```

If `--shallow` is in `$ARGUMENTS`, skip to the Summary section after Phase 1.

---

# PHASE 2: Deep Analysis

This phase goes beyond known pitfalls. Analyze the terminal subsystem for issues that only emerge from understanding the full codebase in context.

## D1: Race Conditions and Timing

Trace every async sequence and ask: what happens if the order changes?

- **Spawn-vs-render race**: Can PTY data arrive before the terminal is open/attached? What happens to buffered data?
- **Mount/unmount race**: What if the component unmounts during an async operation (PTY spawn, WebGL init, font load)?
- **Multiple rapid mounts**: What if React strict mode double-mounts? What if tabs switch rapidly?
- **Resize during init**: What if a resize event fires before the terminal is fully initialized?
- **Event ordering**: Are there assumptions about which callback fires first? Are those assumptions documented or enforced?
- **Cleanup timing**: Does the cleanup function run before or after pending promises resolve? What happens to callbacks that fire after disposal?

For each race found, describe the exact sequence of events that triggers it and the observable consequence (crash, visual glitch, data loss, orphaned process).

## D2: Error Boundary Gaps

Every async operation, IPC call, and DOM API can fail. Check:

- **Unhandled promise rejections**: Are all `.then()` chains and `await` expressions in try/catch? What happens when they reject?
- **IPC/command failures**: If a Tauri invoke, WebSocket send, or backend call fails, does the UI handle it or silently break?
- **DOM API failures**: `requestAnimationFrame` callbacks after disposal, `ResizeObserver` on detached elements, `querySelector` returning null
- **Addon initialization failures**: What if WebGL is not supported? What if an addon throws during `loadAddon()`?
- **Silent swallowing**: Are there empty catch blocks, catch-and-log-only patterns, or error callbacks that don't propagate state?
- **User-visible error state**: When something fails, does the user see a meaningful error or just a blank/frozen terminal?

## D3: Fragile Assumptions

Look for code that works today but breaks when external inputs change:

- **Format-dependent parsing**: Regex or string matching on output that assumes a specific format (banners, prompts, escape sequences). What happens when the format changes?
- **Magic numbers and hardcoded values**: Timeouts, buffer sizes, retry counts, dimension constants -- are they justified or arbitrary?
- **Platform assumptions**: Does the code assume Windows/macOS/Linux behavior? Shell type? Terminal capabilities?
- **Version coupling**: Does the code depend on specific xterm.js addon versions, specific backend API shapes, or specific framework behavior?
- **Implicit contracts**: Are there undocumented assumptions between frontend and backend (message format, encoding, ordering)?

## D4: Performance Under Stress

Terminal emulators must handle high-throughput data. Analyze:

- **Write throughput**: What happens with rapid, large PTY writes? Is there backpressure? Write coalescing? Or does every chunk trigger a DOM update?
- **Per-write overhead**: Are there operations that run on every `term.write()` call that should be batched or throttled? (cursor hide/show, fit recalculation, state updates)
- **Memory growth**: Does the scrollback buffer, write buffer, or any internal state grow without bound? What's the worst case?
- **Re-render triggers**: In React/Vue, does terminal state trigger unnecessary component re-renders? Are refs used correctly to avoid this?
- **Expensive listeners**: Are there listeners on high-frequency events (mousemove, scroll, data) that do expensive work without throttling?
- **Startup cost**: How much work happens during mount? Could any of it be deferred?

## D5: Edge Cases and Stress Scenarios

Think adversarially. What happens under unusual but realistic conditions:

- **Rapid tab switching**: Open terminal, switch away immediately, switch back -- are there visual artifacts, lost data, or stale state?
- **Sleep/wake cycle**: Laptop closes and reopens -- do WebGL contexts survive? Do heartbeats resume? Does the PTY reconnect?
- **Multiple terminal instances**: Can two terminals coexist without interfering? Shared global state? Event listener collisions?
- **Very long sessions**: After hours of use -- does memory grow? Do timers accumulate? Do listeners pile up?
- **Empty/failed PTY**: What if the shell process exits immediately? What if it never starts?
- **Binary data**: What if the PTY outputs raw binary (not UTF-8)? Does `term.write()` handle it or corrupt the buffer?
- **Extremely fast output**: `yes | head -100000` equivalent -- does the terminal lag, freeze, or drop frames gracefully?
- **Window minimized/hidden**: Does the terminal waste CPU rendering to an invisible canvas?

## D6: Architecture Quality

Evaluate the structural quality of the terminal subsystem:

- **Separation of concerns**: Is terminal logic, PTY management, and UI rendering cleanly separated? Or is everything in one giant component?
- **Coupling to framework**: Could the terminal logic work outside React/Vue/Angular, or is it tightly coupled to framework lifecycle?
- **Testability**: Can any of this code be unit tested? Are there seams for mocking the terminal or PTY?
- **Configuration surface**: Are behavioral knobs (scrollback, theme, font, shell) externalized or hardcoded?
- **Extension points**: Could someone add a new addon, custom key handler, or theme without modifying core terminal code?

## Phase 2 Report

For each category (D1-D6), output findings in this format:

```
## D#: Category Name

### [Finding title]
File: path/to/file.ts:line
Severity: Critical | High | Medium | Low
What: [what the issue is]
When: [under what conditions it manifests]
Impact: [what the user sees or what breaks]
Recommendation: [specific fix or approach]
```

If a category genuinely has no findings after thorough analysis, state what you checked and why there are no issues -- do not just say "no issue" without evidence.

---

## Step: Apply Fixes

If `--dry-run` is in `$ARGUMENTS`, show all fixes without applying them.

Otherwise, apply fixes using the Edit tool:
- Fix one issue at a time, starting with Critical and High severity
- Verify each fix doesn't conflict with other terminal setup code
- Preserve addon loading order: open() -> WebGL -> Fit -> other addons -> fit()
- Preserve existing event handlers and options
- For Phase 2 findings, only auto-fix Clear bugs. Recommend but don't auto-apply architectural changes.

## Summary

After all analysis, print:

```
xterm.js diagnosis complete.

Phase 1 (Pitfall Scan):
  Issues found: X (Critical: X | High: X | Medium: X | Low: X)
  Issues fixed: X

Phase 2 (Deep Analysis):
  Findings: X (Critical: X | High: X | Medium: X | Low: X)
  Fixed: X
  Recommendations: X

Files analyzed:
- path/to/file.ts
- path/to/file.css
- ...

Files modified:
- path/to/file.ts (if any)
```
