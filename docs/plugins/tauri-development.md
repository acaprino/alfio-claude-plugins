# Tauri Development Plugin

> Build fast, secure cross-platform apps. Expert Rust engineering plus Tauri 2 optimization for desktop and mobile -- with concrete performance targets for startup time, memory, and IPC latency.

## Agents

### `tauri-optimizer`

Expert in Tauri v2 + React optimization for trading and high-frequency data scenarios.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | IPC optimization, state management, memory leaks, WebView tuning |

**Invocation:**
```
Use the tauri-optimizer agent to analyze [project/file]
```

**Performance targets:**
| Metric | Target | Critical |
|--------|--------|----------|
| Startup time | < 1s | < 2s |
| Memory baseline | < 100MB | < 150MB |
| IPC latency | < 0.5ms | < 1ms |
| Frame rate | 60 FPS | > 30 FPS |

---

### `rust-engineer`

Expert Rust developer specializing in systems programming and memory safety.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Ownership patterns, async tokio, FFI, performance optimization |

**Invocation:**
```
Use the rust-engineer agent to implement [feature]
```

**Checklist enforced:**
- Zero unsafe code outside core abstractions
- clippy::pedantic compliance
- Complete documentation with examples
- MIRI verification for unsafe blocks

---

## Skills

### `tauri2-mobile`

Expert guidance for Tauri 2 mobile app development (Android/iOS).

| | |
|---|---|
| **Invoke** | `/tauri2-mobile` |
| **Use for** | Mobile setup, plugins, testing, store deployment |

**Quick commands:**
| Task | Command |
|------|---------|
| Init Android | `npm run tauri android init` |
| Dev Android | `npm run tauri android dev` |
| Build APK | `npm run tauri android build --apk` |
| Build iOS | `npm run tauri ios build` |

---

**Related:** [workflows](workflows.md) (`/tauri-pipeline` and `/mobile-tauri-pipeline` orchestrate these agents) | [frontend](frontend.md) (UI polish and layout for Tauri webviews) | [react-development](react-development.md) (React performance in Tauri)
