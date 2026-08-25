# Agent SDK: core API

Installation, the `query()` entry point, the full options table, built-in tools, streaming,
structured output, cost tracking, and the migration from `claude-code-sdk`.

Option shapes and tool names in this file are API-sensitive. Resolve them against the project's
installed SDK or https://code.claude.com/docs/en/agent-sdk/ before emitting code, per the
source-of-truth policy in `SKILL.md`. Entries marked *(verify)* failed documentation resolution
at the last refresh and are unconfirmed.

---

## 1. Installation & Auth


```bash
# TypeScript
npm install @anthropic-ai/claude-agent-sdk

# Python
pip install claude-agent-sdk
# or with uv
uv add claude-agent-sdk
```

Authentication via environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Alternative providers:
- **Amazon Bedrock**: `CLAUDE_CODE_USE_BEDROCK=1` + AWS credentials
- **Google Vertex AI**: `CLAUDE_CODE_USE_VERTEX=1` + GCP credentials
- **Microsoft Azure**: `CLAUDE_CODE_USE_FOUNDRY=1` + Azure credentials

---

## 2. Core API -- `query()`


Both SDKs expose `query()` as the primary entry point. It returns an async iterator streaming `SDKMessage` objects. Claude handles the entire tool loop autonomously -- you do NOT implement tool execution.

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Find and fix the bug in auth.py",
  options: {
    allowedTools: ["Read", "Edit", "Bash"],
    maxTurns: 10,
  },
})) {
  if (message.type === "assistant" && message.content) {
    for (const block of message.content) {
      if (block.type === "text") process.stdout.write(block.text);
    }
  }
  if ("result" in message) {
    console.log("\nFinal:", message.result);
    console.log("Cost:", message.total_cost_usd);
  }
}
```

### Python

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Bash"],
        max_turns=10,
    )
    async for message in query(prompt="Find and fix the bug in auth.py", options=options):
        if hasattr(message, "result"):
            print(f"Final: {message.result}")
            print(f"Cost: ${message.total_cost_usd:.4f}")

asyncio.run(main())
```

---

## 3. Configuration Options


### Full Options Reference

| Option (TS / Py) | Type | Description |
|---|---|---|
| `allowedTools` / `allowed_tools` | `string[]` | Tools to auto-approve without user confirmation |
| `disallowedTools` / `disallowed_tools` | `string[]` | Tools to always deny |
| `permissionMode` / `permission_mode` | `string` | Permission strategy (see Permissions section) |
| `systemPrompt` / `system_prompt` | `string \| object` | Custom system prompt string, or the Claude Code preset as `{ type: "preset", preset: "claude_code" }` (a bare `"claude_code"` string is not valid) |
| `model` | `string` | Model ID (e.g., `"claude-fable-5"`, `"claude-opus-5"`, `"claude-sonnet-5"`) -- short aliases resolve to the latest date-slugged release (e.g., `"claude-haiku-4-5"` resolves to `"claude-haiku-4-5-20251001"`); pin a full slug for reproducibility |
| `maxTurns` / `max_turns` | `number` | Maximum agentic loop iterations |
| `maxBudgetUsd` / `max_budget_usd` | `number` | Spending cap in USD |
| `effort` | `string` | `"low"`, `"medium"`, `"high"`, `"xhigh"`, `"max"` |
| `cwd` | `string` | Working directory for file operations |
| `mcpServers` / `mcp_servers` | `object` | MCP server configurations |
| `hooks` | `object` | Lifecycle hook callbacks |
| `agents` | `object` | Subagent definitions |
| `resume` | `string` | Session ID to resume |
| `continue` / `continue_conversation` | `boolean` | Continue most recent session |
| `forkSession` / `fork_session` | `boolean` | With `resume`: branch a new session off the resumed one instead of continuing it |
| `settingSources` / `setting_sources` | `string[]` | Which filesystem settings to load (`"user"`, `"project"`, `"local"`); pass it explicitly rather than relying on version-dependent defaults (see Migration) |
| `plugins` | `SdkPluginConfig[]` | Plugins to load, e.g. `[{ type: "local", path: "/path/to/plugin" }]` |
| `sandbox` | `object` | Sandbox/isolation settings |
| `thinking` | `object` | Extended thinking: `{ type: "adaptive" }`, `{ type: "enabled", budget_tokens: N }`, `{ type: "disabled" }` |
| `outputFormat` / `output_format` | `object` | JSON schema for structured output |
| `env` | `object` | Environment variables passed to agent |
| `canUseTool` / `can_use_tool` | `function` | Runtime permission callback |
| `includePartialMessages` / `include_partial_messages` | `boolean` | Enable token-level streaming |
| `spawnClaudeCodeProcess` *(verify)* | `function` | Custom process spawner (VMs, containers, remote) |
| `agentProgressSummaries` *(verify)* | `boolean` | Enable periodic AI-generated progress summaries for running subagents |
| `debug` / `debug` | `boolean` | Enable programmatic debug logging |
| `debugFile` / `debug_file` | `string` | File path for debug log output |

### Example -- Full Configuration

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const msg of query({
  prompt: "Refactor the auth module to use JWT tokens",
  options: {
    model: "claude-sonnet-5",
    allowedTools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    disallowedTools: ["WebSearch", "WebFetch"],
    permissionMode: "acceptEdits",
    maxTurns: 25,
    maxBudgetUsd: 1.0,
    effort: "high",
    cwd: "/home/user/project",
    systemPrompt: "You are a senior backend engineer. Follow the project's coding standards.",
    thinking: { type: "adaptive" },
    env: { NODE_ENV: "development" },
  },
})) {
  // process messages
}
```

---

## 4. Built-in Tools


The agent has access to these tools by default:

| Tool | Purpose |
|---|---|
| `Read` | Read files from filesystem |
| `Write` | Create new files |
| `Edit` | Precise string replacements in existing files |
| `Bash` | Execute shell commands |
| `Glob` | Find files by pattern |
| `Grep` | Search file contents with regex |
| `WebSearch` | Search the web |
| `WebFetch` | Fetch and parse web pages |
| `Agent` | Spawn subagents (required for multi-agent); older SDK versions emitted this tool under the name `Task` |
| `Skill` | Invoke skills from plugins |
| `AskUserQuestion` | Request user input |
| `ToolSearch` | Discover deferred tools |

Control which tools the agent can use:

```typescript
// Only allow read-only operations
options: {
  allowedTools: ["Read", "Glob", "Grep"],
  disallowedTools: ["Bash", "Write", "Edit"],
}
```

---

## 5. Streaming


### Message Types

Messages streamed from `query()` include:

| Type | Description |
|---|---|
| `system` (subtype: `init`) | Session initialized -- contains `session_id` |
| `system` (subtype: `api_retry`) *(verify)* | API retry info -- attempt count, max retries, delay, error status |
| `assistant` | Claude's response with `content` blocks (text, tool_use) |
| `result` | Final result with `result` text, `total_cost_usd`, `usage` |
| `rate_limit` *(verify)* | Rate limit event with retry timing (Python: `RateLimitEvent`) |
| `stream_event` | Partial token (when `includePartialMessages: true`) |

### Token-Level Streaming

```typescript
for await (const msg of query({
  prompt: "Explain the auth flow",
  options: {
    includePartialMessages: true,
    allowedTools: ["Read"],
  },
})) {
  if (msg.type === "stream_event") {
    process.stdout.write(msg.delta?.text ?? "");
  }
}
```

---

## 6. Structured Output


Force the agent to return JSON conforming to a schema:

```typescript
for await (const msg of query({
  prompt: "Analyze this codebase and list all API endpoints",
  options: {
    outputFormat: {
      type: "json_schema",
      schema: {
        type: "object",
        properties: {
          endpoints: {
            type: "array",
            items: {
              type: "object",
              properties: {
                method: { type: "string" },
                path: { type: "string" },
                handler: { type: "string" },
              },
              required: ["method", "path", "handler"],
            },
          },
        },
        required: ["endpoints"],
      },
    },
  },
})) {
  if ("result" in msg) {
    const analysis = JSON.parse(msg.result);
    console.log(analysis.endpoints);
  }
}
```

---

## 7. Cost Tracking


```typescript
for await (const msg of query({ prompt: "Analyze auth.py", options: {} })) {
  if ("result" in msg) {
    console.log(`Total cost: $${msg.total_cost_usd}`);
    console.log(`Input tokens: ${msg.usage?.input_tokens}`);
    console.log(`Output tokens: ${msg.usage?.output_tokens}`);
    // Per-model breakdown (TypeScript; verify against your installed SDK)
    if (msg.modelUsage) {
      for (const [model, usage] of Object.entries(msg.modelUsage)) {
        console.log(`${model}: $${usage.cost_usd}`);
      }
    }
  }
}
```

Use `maxBudgetUsd` to set a hard spending cap:

```typescript
options: { maxBudgetUsd: 0.50 }  // stop after $0.50
```

---

## 8. Migration from claude-code-sdk


The old `claude-code-sdk` / `@anthropic-ai/claude-code-sdk` packages are deprecated. Migration:

```bash
# TypeScript
npm uninstall @anthropic-ai/claude-code-sdk
npm install @anthropic-ai/claude-agent-sdk

# Python
pip uninstall claude-code-sdk
pip install claude-agent-sdk
```

Update imports:

```typescript
// Old
import { query } from "@anthropic-ai/claude-code-sdk";
// New
import { query } from "@anthropic-ai/claude-agent-sdk";
```

```python
# Old
from claude_code_sdk import query, ClaudeCodeOptions
# New
from claude_agent_sdk import query, ClaudeAgentOptions
```

### Breaking Changes

The API surface is mostly identical, but two critical defaults changed:

1. **System prompt no longer defaults to Claude Code's prompt** -- the new SDK uses a minimal system prompt. To restore Claude Code behavior:
   ```typescript
   systemPrompt: { type: "preset", preset: "claude_code" }
   ```

2. **Settings-source defaults are version-dependent** -- early `claude-agent-sdk` releases loaded NO filesystem settings (CLAUDE.md, .claude/ configs, user settings) by default; current releases load the `user` and `project` sources with default `query()` options. Do not rely on either default: pass `settingSources` explicitly:
   ```typescript
   settingSources: ["user", "project", "local"]
   ```

To fully restore old `claude-code-sdk` behavior, set both the system prompt preset and explicit setting sources.

---

## 9. TypeScript V2 API: removed


An experimental V2 session API (`unstable_v2_createSession()` with a `send`/`stream` pattern) previously shipped as a preview. It was **removed in TypeScript Agent SDK 0.3.142**. Do not build on it: use `query()` with `resume` (plus `forkSession` for branching) for session workflows.
