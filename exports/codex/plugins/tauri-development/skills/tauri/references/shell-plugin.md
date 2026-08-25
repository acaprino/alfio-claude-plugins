# Shell Plugin

Spawn child processes, run sidecar binaries, stream stdout/stderr. The hard parts are scope-based permissions and a few cross-platform spawn gotchas.

## When to use

Running a CLI tool the user has installed (git, node, ffmpeg) or a binary you ship as a sidecar. For OAuth and "open URL" actions, use `opener` instead -- safer scope.

## When NOT to use

External URL handoff (browsers, mailto, tel) -- use `tauri-plugin-opener` (`openUrl`). The shell plugin's `open` is more permissive than necessary.

## Gotchas

- **Every command needs an explicit scope entry** in `capabilities/default.json`. Tauri 2 dropped the v1 "allow any cmd" mode -- you list the exact `cmd` + `args` shape (or use `{ "validator": "<regex>" }` for variable args). Forgotten scopes throw at runtime, not at build.
- **Windows: pop-up cmd.exe windows.** Spawning console binaries on Windows shows a black flash unless you set `creation_flags(0x08000000)` (CREATE_NO_WINDOW) on the Command before `.spawn()`. Affects every CLI tool spawn from a windowed app.
- **PATH is not the user's PATH.** Spawned processes inherit the app's environment, which on macOS launched-from-Finder lacks `/usr/local/bin`, `/opt/homebrew/bin`, etc. Specify full paths or set `envs([...])` explicitly when calling Homebrew/MacPorts binaries.
- **Sidecar filenames must end with the target triple** (e.g. `my-tool-aarch64-apple-darwin`). Tauri picks the right one at runtime; missing the suffix = "sidecar not found." Get your triple via `rustc -Vv | grep host`.
- **`spawn()` returns a `Receiver` you must drain.** If you don't `recv()` events, the channel buffers up and stalls the child's stdio. Run the receive loop in `tokio::spawn`.
- **`child.kill()` is best-effort on Windows** -- console children may need extra teardown. Always set a sensible timeout for your wait loop, don't rely on `kill()` to immediately reap.
- **`shell:allow-stdin-write` is a separate permission** -- omitting it makes `child.write()` fail silently in release builds.

## Permission scope shape (the part that's easy to mis-spell)

```json
{
  "identifier": "shell:allow-execute",
  "allow": [
    { "name": "git-status", "cmd": "git", "args": ["status"] },
    { "name": "run-script", "cmd": "node", "args": [{ "validator": "\\S+" }] },
    { "name": "my-tool", "sidecar": true, "args": [{ "validator": ".*" }] }
  ]
}
```

Scope keys: `name` (referenced from JS as `Command.create('name')`), `cmd` (literal binary), `args` (mix of literal strings and `{validator: regex}`), `sidecar: true` for bundled binaries.

## Sidecar config

```json
// tauri.conf.json
"bundle": {
  "externalBin": ["binaries/my-tool"]
}
```

Files on disk: `binaries/my-tool-x86_64-pc-windows-msvc.exe`, `binaries/my-tool-aarch64-apple-darwin`, etc.

## Official docs

- Shell plugin: https://v2.tauri.app/plugin/shell/
- Permission reference: https://v2.tauri.app/plugin/shell/#default-permission
- Sidecar binaries: https://v2.tauri.app/develop/sidecar/
- Rust API: https://docs.rs/tauri-plugin-shell
- JS API: https://v2.tauri.app/reference/javascript/shell/

## Related

- `plugins-core.md` -- when to use `opener` instead
- `frontend-patterns.md` -- JS Channel pattern (used for streaming spawn output)
- `rust-patterns.md` -- error handling for spawn results
