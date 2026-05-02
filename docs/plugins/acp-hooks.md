# ACP Hooks Plugin

> Session lifecycle hooks for the ACP ecosystem: skill awareness, security enforcement, automatic context management, brainstorm gating, code review gating, documentation gating, and team spawn suggestions.

**Note:** This plugin uses `plugin.json` for hook configuration instead of marketplace registration. Hooks run automatically; no manual invocation needed.

## Hooks

### SessionStart hooks

These run automatically when a Claude Code session starts:

| Handler | Purpose |
|---------|---------|
| `skill-awareness.js` | Injects skill awareness so Claude knows which skills are available |
| `cleanup-builtins.js` | Removes duplicate built-in plugins that conflict with ACP |

### UserPromptSubmit hooks

These run before Claude processes a user prompt:

| Handler | Purpose |
|---------|---------|
| `brainstorm-gate.js` | Detects creative/building intent (add, create, build, implement, etc.) and reminds Claude to invoke brainstorming + worktree-manager skills before jumping into code |
| `team-spawn-gate.js` | Detects team-worthy requests and suggests the matching agent team preset (review, security, debug, feature, fullstack, deep-search, research, migration, docs, app-analysis, tauri, ui-studio). Advisory only -- asks user before spawning |

**Bypass conditions (brainstorm-gate):** slash commands, questions (ending with `?`), single-word prompts, bug fix/debug prompts, prompts starting with `*` (explicit bypass).

**Bypass conditions (team-spawn-gate):** slash commands, questions (ending with `?`), single-word prompts, `#` or `*` prefix, `--no-team` flag. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var.

### PreToolUse hooks

These run before specific tool invocations:

| Handler | Matcher | Purpose |
|---------|---------|---------|
| `review-gate.js` | `Bash` | Blocks `gh pr create` and `git merge` targeting main/master until `/code-review` is run |
| `docs-gate.js` | `Bash` | Blocks PR/merge when documentation may need auditing -- detects changes to plugin files and reminds to update docs |

**Bypass conditions:**
- Set `reviewGate` to `false` in `~/.claude/acp-config.json`
- Add `--no-review` flag to the command
- Merging FROM main/master into a feature branch (pulling in upstream changes is fine)

### PostToolUse hooks

These run after specific tool invocations:

| Handler | Trigger | Purpose |
|---------|---------|---------|
| `security-gate.js` | After `Write` or `Edit` | Scans written/edited files for hardcoded secrets (API keys, tokens, passwords) and blocks commits |
| `autocompact.js` | After any tool use | Monitors context usage and triggers automatic compaction when context is high |

## Configuration

`plugins/acp-hooks/hooks/hooks.json` defines the hooks. Handler scripts live in `plugins/acp-hooks/hooks/handlers/`.

**Disablable hooks** (via `~/.claude/acp-config.json`):
- `securityGate: false` - disable secret scanning
- `reviewGate: false` - disable PR/merge review gating
- `teamSpawnGate: false` - disable team preset suggestions

**Optional dependencies:** `ai-tooling` (skill awareness injection), `git-worktrees` (brainstorm-gate worktree awareness), `senior-review` (review-gate `/code-review` command), `agent-teams` (team-spawn-gate presets).

---

**Related:** [marketplace-ops](marketplace-ops.md) (plugin management) | [ai-tooling](ai-tooling.md) (acp-loader skill awareness) | [senior-review](senior-review.md) (code review commands)
