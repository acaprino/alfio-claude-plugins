# Agent SDK: permissions, hooks, and security

Permission modes, the evaluation order, the `canUseTool` fallback, the hook events and their
matchers, and the security practices that follow from all three.

The one rule to carry out of this file: coarse policy is `allowedTools` / `disallowedTools` /
`permissionMode`, always-on enforcement is a `PreToolUse` hook, and `canUseTool` is only the
interactive fallback for calls nothing earlier resolved.

---

## 1. Permissions


Control what the agent can do at runtime.

### Permission Modes

| Mode | Behavior |
|---|---|
| `"default"` | Unmatched tools trigger `canUseTool` callback or user prompt |
| `"dontAsk"` | Deny anything not pre-approved |
| `"acceptEdits"` | Auto-accept file mutations (Edit, Write, mkdir, touch, rm, mv, cp) |
| `"bypassPermissions"` | All tools run without prompts (use with caution) |
| `"plan"` | No execution -- planning/analysis only |

### Permission Evaluation Order

1. Hooks (`PreToolUse`) -- always run, for every matching tool call
2. Deny rules (`disallowedTools`) -- **overrides everything, including `bypassPermissions`**
3. Ask rules
4. Permission mode
5. Allow rules (`allowedTools`) -- does NOT constrain `bypassPermissions`
6. `canUseTool` callback -- reached only when none of the steps above resolved the call

**Important**: `disallowedTools` is the only hard block. Even `bypassPermissions` cannot override it. Use it for safety-critical restrictions.

### Runtime Permission Callback

`canUseTool` is the interactive fallback at the END of the evaluation order: it fires only for calls that no hook, rule, or mode has already resolved. A tool listed in `allowedTools` never reaches it. Validation that must run on every invocation belongs in a `PreToolUse` hook, not here.

```typescript
for await (const msg of query({
  prompt: "Deploy the application",
  options: {
    allowedTools: ["Read"],  // Bash is NOT pre-approved, so Bash calls reach the callback
    canUseTool: async (toolName, input) => {
      // Decide unresolved requests programmatically instead of prompting a user
      if (toolName === "Bash" && input.command?.includes("rm -rf")) {
        return { behavior: "deny", message: "Destructive commands not allowed" };
      }
      return { behavior: "allow" };
    },
  },
})) { /* ... */ }
```

Callback return values:
- `{ behavior: "allow" }` -- approve the tool call
- `{ behavior: "deny", message: "reason" }` -- reject with explanation
- `{ behavior: "ask" }` -- fall through to user prompt (default mode)

---

## 2. Hooks -- Lifecycle Events


Hooks intercept agent lifecycle events for logging, validation, or control flow.

### Available Hook Events

| Hook | When | Can modify? |
|---|---|---|
| `PreToolUse` | Before a tool executes | Yes -- allow, deny, or modify input |
| `PostToolUse` | After a tool completes | Yes -- modify output |
| `PostToolUseFailure` | After a tool fails | Log errors |
| `UserPromptSubmit` | When user sends a prompt | Modify prompt text |
| `Stop` | Agent is about to stop | Force continue or modify |
| `SubagentStart` | Subagent is starting | Modify subagent config |
| `SubagentStop` | Subagent completed | Process results |
| `PreCompact` | Before context compaction | Log or modify |
| `Notification` | Agent sends a notification | Display or forward |
| `PermissionRequest` | Tool needs permission | Auto-approve or deny |
| `TaskCompleted` | A task has been completed | Process results |
| `ConfigChange` | Configuration changed at runtime | Security auditing |
| `SessionStart` | Session initialized | Setup actions |
| `SessionEnd` | Session completed | Cleanup actions |

### Hook Matchers

Matchers are regex pattern STRINGS tested against the tool name (never RegExp literals). Hooks also support async (fire-and-forget) mode; Python spells the flag `async_` to avoid the reserved word:

```typescript
hooks: {
  PreToolUse: [
    // Matcher targets specific tools by regex on tool name
    {
      matcher: "^(Write|Edit)$",
      hooks: [async (input) => {
        if (input.tool_input?.file_path?.includes(".env")) {
          return {
            hookSpecificOutput: {
              hookEventName: "PreToolUse",
              permissionDecision: "deny",
              permissionDecisionReason: "Cannot modify .env files",
            },
          };
        }
        return {};   // say nothing and the call proceeds to normal permission resolution
      }],
      timeout: 30,  // seconds, default 60
    },
    // Async hook -- fire-and-forget logging (does not block)
    {
      matcher: ".*",
      hooks: [{ async: true, asyncTimeout: 5, handler: async (input) => {
        await fetch("https://logs.example.com/webhook", {
          method: "POST",
          body: JSON.stringify({ tool: input.tool_name, time: Date.now() }),
        });
      }}],
    },
  ],
}
```

### Hook Return Values

**A hook does not return the `canUseTool` shape.** `{ behavior: "deny", message }` is
`PermissionResult`, which belongs to the `canUseTool` callback alone. A hook that returns it
matches no part of the hook output type, so it is ignored: the guard looks installed and allows
everything. This is the single most dangerous confusion in this file, because it fails silently
and in the safe-looking direction.

A hook returns `HookJSONOutput`. The fields that matter:

- `hookSpecificOutput`: the event-specific decision. For `PreToolUse` its fields are
  `hookEventName`, `permissionDecision`, `permissionDecisionReason`, `updatedInput` and
  `additionalContext`, where `permissionDecision` is `"allow"`, `"deny"`, `"ask"` or `"defer"`
- `systemMessage`: inject a system message into the conversation
- `continue`: keep the agent going (for `Stop` hooks)
- `suppressOutput`, `stopReason`, `reason`: presentation and control

Returning `{}` decides nothing and lets the call fall through to normal permission resolution,
which is what a logging-only hook should do. Verify these names against the type definitions in
your installed SDK before relying on them: this is API-sensitive.

### Hook Example

```typescript
for await (const msg of query({
  prompt: "Analyze the codebase",
  options: {
    hooks: {
      PreToolUse: [{
        matcher: ".*",
        hooks: [async (input) => {
          console.log(`Tool: ${input.tool_name}, Input: ${JSON.stringify(input.tool_input)}`);
          // Block writes to production config
          if (input.tool_name === "Write" && input.tool_input?.file_path?.includes("production")) {
            return {
              hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason: "Cannot modify production files",
              },
            };
          }
          return {};   // decide nothing: fall through to normal permission resolution
        }],
      }],
      PostToolUse: [{
        matcher: ".*",
        hooks: [async (input) => {
          console.log(`Tool ${input.tool_name} completed`);
        }],
      }],
      Stop: [{
        hooks: [async () => {
          console.log("Agent stopping");
        }],
      }],
    },
  },
})) { /* ... */ }
```

---

## 3. Security Best Practices


1. **Always set `allowedTools`** -- restrict to minimum necessary tools
2. **Use `maxBudgetUsd`** -- prevent runaway costs
3. **Use `maxTurns`** -- prevent infinite loops
4. **Enforce runtime invariants with `PreToolUse` hooks** -- never with `canUseTool` (see below)
5. **Sandbox untrusted code** -- use container isolation for user-submitted tasks
6. **Never pass secrets in prompts** -- use `env` option or MCP tools for credential access
7. **Use `disallowedTools`** -- explicitly block tools you never want used
8. **Proxy credentials** -- use a proxy pattern for API keys the agent needs

Three mechanisms, three distinct jobs. Do not substitute one for another:

| Mechanism | Job |
|---|---|
| `allowedTools` / `disallowedTools` / `permissionMode` | Coarse permission policy |
| `PreToolUse` hook | Always-on enforcement: runs for every matching tool call, before permission resolution |
| `canUseTool` | Interactive fallback: runs only for calls no rule, mode, or hook has already resolved |

**Do not use `canUseTool` as an always-on security interceptor.** Calls already approved by allow rules or the permission mode never reach it, so a security check placed there silently stops running the moment you allow-list the tool. Validation that must hold for every invocation belongs in a `PreToolUse` hook.

```typescript
// Secure configuration example
options: {
  allowedTools: ["Read", "Glob", "Grep"],     // read-only
  disallowedTools: ["Bash", "Write", "Edit"],  // no execution or mutation
  maxTurns: 10,
  maxBudgetUsd: 0.25,
  permissionMode: "dontAsk",                   // deny anything not listed
  hooks: {
    PreToolUse: [{
      matcher: "Read|Glob|Grep",
      hooks: [async (input) => {
        // Always-on invariant: runs even for allow-listed tools
        if (input.tool_input?.file_path?.includes("..")) {
          return {
            hookSpecificOutput: {
              hookEventName: "PreToolUse",
              permissionDecision: "deny",
              permissionDecisionReason: "Path traversal blocked",
            },
          };
        }
        return {};
      }],
    }],
  },
}
```
