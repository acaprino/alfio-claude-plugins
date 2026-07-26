# ACP Hooks Plugin

> Session lifecycle hooks for the Claude Code Daodan ecosystem: skill awareness, security enforcement, automatic context management, code review gating, documentation gating, and team spawn suggestions.

**Note:** This plugin uses `plugin.json` for hook configuration instead of marketplace registration. Hooks run automatically; no manual invocation needed.

## Hooks

### SessionStart hooks

These run automatically when a Claude Code session starts:

| Handler | Purpose |
|---------|---------|
| `skill-awareness.js` | Injects skill awareness so Claude knows which skills are available |
| `cleanup-builtins.js` | Removes duplicate built-in plugins that conflict with Claude Code Daodan |

### UserPromptSubmit hooks

These run before Claude processes a user prompt:

| Handler | Purpose |
|---------|---------|
| `team-spawn-gate.js` | Detects team-worthy requests and suggests either a local pipeline command (`/senior-review:team-review`, `/research:team-research`) or an upstream `agent-teams` (wshobson/agents) preset (security, debug, feature, fullstack, migration). Advisory only: injects a suggestion into context, never blocks the prompt |

**Bypass conditions (team-spawn-gate):** empty or single-word prompts, `/`, `#`, or `*` prefix, `--no-team` flag, `teamSpawnGate: false` in `~/.claude/acp-config.json`, or `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` set to `0`/`false`. Enabled by default otherwise.

### PreToolUse hooks

These run before specific tool invocations:

| Handler | Matcher | Purpose |
|---------|---------|---------|
| `review-gate.js` | `Bash` | Blocks `gh pr create` and `git merge` targeting main/master until `/code-review` is run |
| `docs-gate.js` | `Bash` | Blocks PR/merge when documentation may need auditing - detects changes to plugin files and reminds to update docs |

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

**Optional dependencies:** `ai-tooling` (skill awareness injection), `senior-review` (review-gate `/code-review` command, team-spawn-gate `/senior-review:team-review` preset), `research` (team-spawn-gate `/research:team-research` preset).

---

**Related:** [marketplace-ops](marketplace-ops.md) (plugin management) | [ai-tooling](ai-tooling.md) (acp-loader skill awareness) | [senior-review](senior-review.md) (code review commands)
