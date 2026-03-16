# Anvil Hooks Plugin

> Session lifecycle hooks for the anvil-toolset ecosystem -- startup branding, skill awareness, security enforcement, and automatic context management.

**Note:** This plugin uses `plugin.json` for hook configuration instead of marketplace registration. Hooks run automatically -- no manual invocation needed.

## Hooks

### SessionStart hooks

These run automatically when a Claude Code session starts:

| Handler | Purpose |
|---------|---------|
| `anvil-logo.js` | Displays ASCII logo on session startup |
| `skill-awareness.js` | Injects skill awareness so Claude knows which skills are available |
| `cleanup-builtins.js` | Removes duplicate built-in plugins that conflict with anvil-toolset |

### PostToolUse hooks

These run after specific tool invocations:

| Handler | Trigger | Purpose |
|---------|---------|---------|
| `security-gate.js` | After `Write` or `Edit` | Scans written/edited files for hardcoded secrets (API keys, tokens, passwords) and blocks commits |
| `autocompact.js` | After any tool use | Monitors context usage and triggers automatic compaction when context is high |

## Configuration

Hooks are defined in `plugins/anvil-hooks/hooks/hooks.json`. Handler scripts live in `plugins/anvil-hooks/hooks/handlers/`.

**Optional dependency:** `ai-tooling` (for skill awareness injection).

---

**Related:** [marketplace-ops](marketplace-ops.md) (plugin management) | [ai-tooling](ai-tooling.md) (anvil-forge skill awareness)
