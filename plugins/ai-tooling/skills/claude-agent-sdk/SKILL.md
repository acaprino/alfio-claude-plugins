---
name: claude-agent-sdk
description: >
  Build apps with the Claude Agent SDK (formerly Claude Code SDK). DO NOT.
  TRIGGER WHEN: code references claude-agent-sdk, user says "agent sdk", "build an agent", "programmatic claude", "claude code sdk", "sidecar", "run claude programmatically".
  DO NOT TRIGGER WHEN: user is using the Claude API client SDK (`anthropic`/`@anthropic-ai/sdk`) for direct chat completions, or doing general programming unrelated to agent orchestration.
---

# Claude Agent SDK

The Claude Agent SDK lets you run Claude Code programmatically -- build AI agents that read files, write code, execute commands, search the web, and orchestrate subagents, all from your application code.

**Key distinction**: The Agent SDK (`claude-agent-sdk`) runs the full Claude Code agent loop with built-in tools. The Anthropic Client SDK (`anthropic`) is for raw API calls. Use the Agent SDK when you need autonomous tool-using agents.

## Quick Reference

| | TypeScript | Python |
|---|---|---|
| **Package** | `@anthropic-ai/claude-agent-sdk` | `claude-agent-sdk` |
| **Install** | `npm install @anthropic-ai/claude-agent-sdk` | `pip install claude-agent-sdk` |
| **Auth** | `ANTHROPIC_API_KEY` env var | `ANTHROPIC_API_KEY` env var |
| **Core function** | `query()` | `query()` |
| **GitHub** | `anthropics/claude-agent-sdk-typescript` | `anthropics/claude-agent-sdk-python` |

The CLI package `@anthropic-ai/claude-code` is bundled inside the SDK -- no separate install needed.

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
| `systemPrompt` / `system_prompt` | `string` | Custom system prompt or `"claude_code"` for default |
| `model` | `string` | Model ID (e.g., `"claude-sonnet-4-6"`) |
| `maxTurns` / `max_turns` | `number` | Maximum agentic loop iterations |
| `maxBudgetUsd` / `max_budget_usd` | `number` | Spending cap in USD |
| `effort` | `string` | `"low"`, `"medium"`, `"high"`, `"max"` |
| `cwd` | `string` | Working directory for file operations |
| `mcpServers` / `mcp_servers` | `object` | MCP server configurations |
| `hooks` | `object` | Lifecycle hook callbacks |
| `agents` | `object` | Subagent definitions |
| `resume` | `string` | Session ID to resume |
| `continue` / `continue_conversation` | `boolean` | Continue most recent session |
| `forkSession` / `fork_session` | `string` | Fork from an existing session |
| `settingSources` / `setting_sources` | `string[]` | Load settings from `["user", "project", "local"]` |
| `plugins` | `string[]` | Local plugin directory paths |
| `sandbox` | `object` | Sandbox/isolation settings |
| `thinking` | `object` | Extended thinking: `"adaptive"`, `{type: "enabled", budget: N}`, `"disabled"` |
| `outputFormat` / `output_format` | `object` | JSON schema for structured output |
| `env` | `object` | Environment variables passed to agent |
| `canUseTool` / `can_use_tool` | `function` | Runtime permission callback |
| `includePartialMessages` / `include_partial_messages` | `boolean` | Enable token-level streaming |
| `spawnClaudeCodeProcess` | `function` | Custom process spawner (VMs, containers, remote) |
| `agentProgressSummaries` | `boolean` | Enable periodic AI-generated progress summaries for running subagents |
| `debug` / `debug` | `boolean` | Enable programmatic debug logging |
| `debugFile` / `debug_file` | `string` | File path for debug log output |

### Example -- Full Configuration

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const msg of query({
  prompt: "Refactor the auth module to use JWT tokens",
  options: {
    model: "claude-sonnet-4-6",
    allowedTools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    disallowedTools: ["WebSearch", "WebFetch"],
    permissionMode: "bypassPermissions",
    maxTurns: 25,
    maxBudgetUsd: 1.0,
    effort: "high",
    cwd: "/home/user/project",
    systemPrompt: "You are a senior backend engineer. Follow the project's coding standards.",
    thinking: "adaptive",
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
| `Agent` | Spawn subagents (required for multi-agent) |
| `Skill` | Invoke skills from plugins |
| `AskUserQuestion` | Request user input |
| `TodoWrite` | Manage task lists |
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

## 5. Custom Tools via MCP

Create custom tools using the SDK's MCP server helpers. Tools are defined with schemas and handlers, then exposed as in-process MCP servers.

### TypeScript

```typescript
import { tool, createSdkMcpServer, query } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// Define tools
const getWeather = tool(
  "get_weather",
  "Get current weather for a city",
  { city: z.string(), units: z.enum(["celsius", "fahrenheit"]).default("celsius") },
  async ({ city, units }) => ({
    content: [{ type: "text", text: JSON.stringify({ city, temp: 22, units }) }],
  })
);

const searchDatabase = tool(
  "search_db",
  "Search the application database",
  { query: z.string(), limit: z.number().default(10) },
  async ({ query: q, limit }) => {
    const results = await db.search(q, limit);
    return { content: [{ type: "text", text: JSON.stringify(results) }] };
  }
);

// Create MCP server
const server = createSdkMcpServer({
  name: "app-tools",
  tools: [getWeather, searchDatabase],
});

// Use in query
for await (const msg of query({
  prompt: "What's the weather in Rome and find related travel posts?",
  options: {
    mcpServers: { app: server },
    allowedTools: ["mcp__app__get_weather", "mcp__app__search_db"],
  },
})) {
  // Custom tools are called automatically by the agent
}
```

### Python

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions

@tool("get_weather", "Get current weather for a city", {"city": str, "units": str})
async def get_weather(args):
    return {"content": [{"type": "text", "text": f"Weather in {args['city']}: 22C"}]}

@tool("search_db", "Search the database", {"query": str, "limit": int})
async def search_db(args):
    results = await db.search(args["query"], args["limit"])
    return {"content": [{"type": "text", "text": str(results)}]}

server = create_sdk_mcp_server(name="app-tools", tools=[get_weather, search_db])

options = ClaudeAgentOptions(
    mcp_servers={"app": server},
    allowed_tools=["mcp__app__get_weather", "mcp__app__search_db"],
)

async for msg in query(prompt="Weather in Rome?", options=options):
    pass
```

### MCP Tool Naming Convention

Custom tools follow the pattern: `mcp__<server-name>__<tool-name>`

Example: server named `"mytools"` with tool `"search"` becomes `mcp__mytools__search`

### External MCP Servers

Connect to external MCP servers via stdio or HTTP:

```typescript
options: {
  mcpServers: {
    // stdio transport (local process)
    localServer: {
      command: "node",
      args: ["./mcp-server.js"],
    },
    // HTTP/SSE transport (remote)
    remoteServer: {
      url: "https://mcp.example.com/sse",
      headers: { Authorization: "Bearer token" },
    },
  },
}
```

---

## 6. Subagents -- Multi-Agent Orchestration

Subagents let you define specialized agents that the main agent can spawn for parallel or delegated work.

### Defining Subagents

```typescript
for await (const msg of query({
  prompt: "Review the codebase for quality and security issues",
  options: {
    allowedTools: ["Read", "Grep", "Glob", "Agent"],  // Agent tool required
    agents: {
      "security-reviewer": {
        description: "Security expert. Use for vulnerability scanning, auth review, injection detection.",
        prompt: "You are a security auditor. Find vulnerabilities, auth issues, and injection vectors.",
        tools: ["Read", "Glob", "Grep"],
        model: "opus",
      },
      "code-quality": {
        description: "Code quality reviewer. Use for style, patterns, complexity, dead code.",
        prompt: "Review code quality: naming, complexity, patterns, duplication.",
        tools: ["Read", "Glob", "Grep"],
        model: "sonnet",
      },
      "test-runner": {
        description: "Runs tests and reports results.",
        prompt: "Execute test suites and analyze failures.",
        tools: ["Bash", "Read", "Grep"],
        model: "haiku",
      },
    },
  },
})) {
  // Claude automatically decides when to spawn subagents
  // based on their descriptions
}
```

### Subagent Properties

| Property | Type | Description |
|---|---|---|
| `description` | `string` | **Required.** When to use this agent (Claude decides based on this) |
| `prompt` | `string` | **Required.** System prompt for the subagent |
| `tools` | `string[]` | Restricted tool set |
| `model` | `string` | `"sonnet"`, `"opus"`, `"haiku"`, or `"inherit"` |
| `disallowedTools` | `string[]` | Tools to block (TS only) |
| `mcpServers` | `object` | MCP servers available to subagent |
| `skills` | `string[]` | Skills the subagent can invoke |
| `memory` | `object` | Memory configuration for the subagent |
| `maxTurns` | `number` | Turn limit for this subagent (TS only) |

### Subagent Behavior

- **Context isolation** -- each subagent gets a fresh conversation; only its final message returns to the parent
- **Parallel execution** -- multiple subagents run concurrently when spawned together
- **No nesting** -- subagents cannot spawn their own subagents
- **Resumable** -- subagents can be resumed by ID from tool results
- **Cost isolated** -- each subagent's token usage is tracked separately
- **Progress summaries** -- enable `agentProgressSummaries: true` to receive periodic AI-generated progress updates from running subagents

---

## 7. Session Management

Sessions persist conversation history to disk, enabling multi-turn workflows.

### Resume a Session (TypeScript)

```typescript
let sessionId: string | undefined;

// First query -- capture session ID
for await (const msg of query({
  prompt: "Read the authentication module",
  options: { allowedTools: ["Read", "Glob"] },
})) {
  if (msg.type === "system" && msg.subtype === "init") {
    sessionId = msg.session_id;
  }
}

// Second query -- resume with full context
for await (const msg of query({
  prompt: "Now refactor it to use JWT",
  options: { resume: sessionId },
})) {
  if ("result" in msg) console.log(msg.result);
}
```

### Continue Most Recent Session

```typescript
// TypeScript
for await (const msg of query({
  prompt: "Continue where we left off",
  options: { continue: true },
})) { /* ... */ }
```

```python
# Python
options = ClaudeAgentOptions(continue_conversation=True)
async for msg in query(prompt="Continue where we left off", options=options):
    pass
```

### Session Client (Python)

Python provides `ClaudeSDKClient` for managed multi-turn conversations:

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    # First turn
    await client.query("What's the project structure?")
    async for msg in client.receive_response():
        pass  # process

    # Second turn -- context retained automatically
    await client.query("Now find all API endpoints")
    async for msg in client.receive_response():
        pass  # process

    # Interrupt current generation
    await client.interrupt()
```

### List, Inspect, and Manage Sessions

```typescript
import {
  listSessions, getSessionInfo, getSessionMessages,
  forkSession, tagSession, renameSession,
} from "@anthropic-ai/claude-agent-sdk";

// List sessions
const sessions = await listSessions({ dir: "/path/to/project", limit: 10 });
for (const session of sessions) {
  console.log(session.sessionId, session.createdAt, session.tag);
}

// Single-session metadata lookup
const info = await getSessionInfo(sessionId);
console.log(info.tag, info.createdAt);

// Read conversation history (includes parallel tool results)
const messages = await getSessionMessages(sessionId);

// Branch a conversation from a specific point
const forked = await forkSession(sessionId);

// Organize sessions with tags and renames
await tagSession(sessionId, "auth-refactor");
await renameSession(sessionId, "auth-refactor-v2");
```

```python
from claude_agent_sdk import (
    list_sessions, get_session_info, get_session_messages,
    fork_session, tag_session, rename_session,
)

sessions = await list_sessions(dir="/path/to/project", limit=10)
for session in sessions:
    messages = await get_session_messages(session.session_id)

info = await get_session_info(session_id)
await tag_session(session_id, "auth-refactor")
await rename_session(session_id, "auth-refactor-v2")
```

### Session State Events

Session state change events are **opt-in** as of v0.2.83. Enable with environment variable:

```bash
export CLAUDE_CODE_EMIT_SESSION_STATE_EVENTS=1
```

### Exit Reasons

The `ExitReason` type includes: `"end_turn"`, `"max_turns"`, `"budget"`, `"interrupt"`, `"resume"`.

---

## 8. Introspection Utilities

```typescript
import { supportedAgents, getSettings } from "@anthropic-ai/claude-agent-sdk";

// Discover available subagents
const agents = await supportedAgents();

// Inspect runtime-resolved settings (includes applied model and effort)
const settings = await getSettings();
console.log(settings.applied.model, settings.applied.effort);
```

---

## 9. Permissions

Control what the agent can do at runtime.

### Permission Modes

| Mode | Behavior |
|---|---|
| `"default"` | Unmatched tools trigger `canUseTool` callback or user prompt |
| `"dontAsk"` | Deny anything not pre-approved (TypeScript only) |
| `"acceptEdits"` | Auto-accept file mutations (Edit, Write, mkdir, touch, rm, mv, cp) |
| `"bypassPermissions"` | All tools run without prompts (use with caution) |
| `"plan"` | No execution -- planning/analysis only |

### Permission Evaluation Order

1. Hooks (`PreToolUse`)
2. Deny rules (`disallowedTools`) -- **overrides everything, including `bypassPermissions`**
3. Permission mode
4. Allow rules (`allowedTools`) -- does NOT constrain `bypassPermissions`
5. `canUseTool` callback

**Important**: `disallowedTools` is the only hard block. Even `bypassPermissions` cannot override it. Use it for safety-critical restrictions.

### Runtime Permission Callback

```typescript
for await (const msg of query({
  prompt: "Deploy the application",
  options: {
    allowedTools: ["Read", "Bash"],
    canUseTool: async (toolName, input) => {
      // Block destructive commands
      if (toolName === "Bash" && input.command?.includes("rm -rf")) {
        return { behavior: "deny", message: "Destructive commands not allowed" };
      }
      // Allow everything else
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

## 10. Hooks -- Lifecycle Events

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
| `TeammateIdle` | A teammate agent is idle | Reassign or notify |
| `ConfigChange` | Configuration changed at runtime | Security auditing |
| `SessionStart` (TS) | Session initialized | Setup actions |
| `SessionEnd` (TS) | Session completed | Cleanup actions |

### Hook Matchers

Hooks can use regex matchers to target specific tools, and support async (fire-and-forget) mode:

```typescript
hooks: {
  PreToolUse: [
    // Matcher targets specific tools by regex on tool name
    {
      matcher: /^(Write|Edit)$/,
      hooks: [async (event) => {
        if (event.input.file_path?.includes(".env")) {
          return { behavior: "deny", message: "Cannot modify .env files" };
        }
        return { behavior: "allow" };
      }],
      timeout: 30,  // seconds, default 60
    },
    // Async hook -- fire-and-forget logging (does not block)
    {
      matcher: /.*/,
      hooks: [{ async: true, asyncTimeout: 5, handler: async (event) => {
        await fetch("https://logs.example.com/webhook", {
          method: "POST",
          body: JSON.stringify({ tool: event.toolName, time: Date.now() }),
        });
      }}],
    },
  ],
}
```

### Hook Return Values

Hook outputs can include:
- `behavior`: `"allow"`, `"deny"`, or `"ask"` (deny > ask > allow when multiple hooks conflict)
- `systemMessage`: inject a system message into conversation
- `continue`: force the agent to continue (for Stop hooks)
- `hookSpecificOutput`: event-specific modifications

### Hook Example

```typescript
for await (const msg of query({
  prompt: "Analyze the codebase",
  options: {
    hooks: {
      PreToolUse: async (event) => {
        console.log(`Tool: ${event.toolName}, Input: ${JSON.stringify(event.input)}`);
        // Block writes to production config
        if (event.toolName === "Write" && event.input.file_path?.includes("production")) {
          return { behavior: "deny", message: "Cannot modify production files" };
        }
        return { behavior: "allow" };
      },
      PostToolUse: async (event) => {
        console.log(`Tool ${event.toolName} completed in ${event.duration_ms}ms`);
      },
      Stop: async (event) => {
        console.log(`Agent stopping. Result: ${event.result}`);
      },
    },
  },
})) { /* ... */ }
```

---

## 11. Streaming

### Message Types

Messages streamed from `query()` include:

| Type | Description |
|---|---|
| `system` (subtype: `init`) | Session initialized -- contains `session_id` |
| `system` (subtype: `api_retry`) | API retry info -- attempt count, max retries, delay, error status |
| `assistant` | Claude's response with `content` blocks (text, tool_use) |
| `result` | Final result with `result` text, `total_cost_usd`, `usage` |
| `task_progress` | Real-time usage metrics for running agents |
| `rate_limit` | Rate limit event with retry timing (Python: `RateLimitEvent`) |
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

## 12. Structured Output

Force the agent to return JSON conforming to a schema:

```typescript
for await (const msg of query({
  prompt: "Analyze this codebase and list all API endpoints",
  options: {
    outputFormat: {
      type: "json_schema",
      json_schema: {
        name: "api_analysis",
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
  },
})) {
  if ("result" in msg) {
    const analysis = JSON.parse(msg.result);
    console.log(analysis.endpoints);
  }
}
```

---

## 13. Plugins and Skills

Load local plugins to give the agent access to custom skills, agents, and commands:

```typescript
for await (const msg of query({
  prompt: "Review the frontend code",
  options: {
    plugins: ["/path/to/my-plugin"],
    allowedTools: ["Read", "Glob", "Grep", "Skill"],
  },
})) { /* agent can now invoke skills from the plugin */ }
```

Load filesystem settings (CLAUDE.md, .claude/ configs):

```typescript
options: {
  settingSources: ["user", "project", "local"],
}
```

---

## 14. Cost Tracking

```typescript
for await (const msg of query({ prompt: "Analyze auth.py", options: {} })) {
  if ("result" in msg) {
    console.log(`Total cost: $${msg.total_cost_usd}`);
    console.log(`Input tokens: ${msg.usage?.input_tokens}`);
    console.log(`Output tokens: ${msg.usage?.output_tokens}`);
    // Per-model breakdown (TypeScript)
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

## 15. Hosting & Deployment Patterns

### Ephemeral Sessions

New container per task, destroy on completion. Best for CI/CD, one-shot tasks.

```typescript
// In a serverless function or CI step
const result = [];
for await (const msg of query({
  prompt: taskDescription,
  options: {
    maxTurns: 15,
    maxBudgetUsd: 0.25,
    permissionMode: "bypassPermissions",
    cwd: "/workspace",
  },
})) {
  if ("result" in msg) result.push(msg);
}
```

### Long-Running Sessions

Persistent containers with multiple agent interactions. Best for interactive applications.

```typescript
// Resume across container restarts
const sessionId = await loadSessionId();
for await (const msg of query({
  prompt: userInput,
  options: { resume: sessionId },
})) { /* ... */ }
```

### Custom Process Spawning

Run agents in VMs, containers, or remote environments:

```typescript
for await (const msg of query({
  prompt: "Analyze the repo",
  options: {
    spawnClaudeCodeProcess: async (options) => {
      // Spawn in a Docker container, VM, or remote server
      const container = await docker.createContainer({
        Image: "node:20",
        Cmd: ["npx", "@anthropic-ai/claude-code", ...options.args],
      });
      await container.start();
      return container.stream;
    },
  },
})) { /* ... */ }
```

### Sandbox Isolation

Use Anthropic's sandbox runtime for secure execution:

```typescript
import { createSandbox } from "@anthropic-ai/sandbox-runtime";

const sandbox = await createSandbox({ image: "node:20" });
for await (const msg of query({
  prompt: "Run the test suite",
  options: { sandbox },
})) { /* ... */ }
```

---

## 16. Security Best Practices

1. **Always set `allowedTools`** -- restrict to minimum necessary tools
2. **Use `maxBudgetUsd`** -- prevent runaway costs
3. **Use `maxTurns`** -- prevent infinite loops
4. **Use `canUseTool` callbacks** -- validate dangerous operations at runtime
5. **Sandbox untrusted code** -- use container isolation for user-submitted tasks
6. **Never pass secrets in prompts** -- use `env` option or MCP tools for credential access
7. **Use `disallowedTools`** -- explicitly block tools you never want used
8. **Proxy credentials** -- use a proxy pattern for API keys the agent needs

```typescript
// Secure configuration example
options: {
  allowedTools: ["Read", "Glob", "Grep"],     // read-only
  disallowedTools: ["Bash", "Write", "Edit"],  // no execution or mutation
  maxTurns: 10,
  maxBudgetUsd: 0.25,
  permissionMode: "dontAsk",                   // deny anything not listed
  canUseTool: async (tool, input) => {
    // Additional runtime validation
    if (input.file_path?.includes("..")) {
      return { behavior: "deny", message: "Path traversal blocked" };
    }
    return { behavior: "allow" };
  },
}
```

---

## 17. Common Patterns

### CI/CD Code Review Agent

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function reviewPR(diff: string): Promise<string> {
  let review = "";
  for await (const msg of query({
    prompt: `Review this PR diff for bugs, security issues, and style:\n\n${diff}`,
    options: {
      allowedTools: ["Read", "Glob", "Grep"],
      maxTurns: 15,
      maxBudgetUsd: 0.50,
      outputFormat: {
        type: "json_schema",
        json_schema: {
          name: "pr_review",
          schema: {
            type: "object",
            properties: {
              issues: { type: "array", items: { type: "object", properties: {
                severity: { type: "string" }, file: { type: "string" },
                line: { type: "number" }, description: { type: "string" },
              }}},
              summary: { type: "string" },
              approved: { type: "boolean" },
            },
            required: ["issues", "summary", "approved"],
          },
        },
      },
    },
  })) {
    if ("result" in msg) review = msg.result;
  }
  return review;
}
```

### Multi-Agent Research Pipeline

```typescript
for await (const msg of query({
  prompt: "Research best practices for rate limiting in Node.js APIs",
  options: {
    allowedTools: ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Agent"],
    agents: {
      "codebase-analyst": {
        description: "Analyzes the local codebase for existing patterns.",
        prompt: "Search the codebase for rate limiting implementations and patterns.",
        tools: ["Read", "Glob", "Grep"],
        model: "sonnet",
      },
      "web-researcher": {
        description: "Researches best practices and documentation online.",
        prompt: "Search for current best practices, libraries, and patterns.",
        tools: ["WebSearch", "WebFetch"],
        model: "sonnet",
      },
    },
  },
})) { /* ... */ }
```

### Interactive Chat Application

```python
from claude_agent_sdk import ClaudeSDKClient

async def chat_loop():
    async with ClaudeSDKClient() as client:
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break
            await client.query(user_input)
            async for msg in client.receive_response():
                if hasattr(msg, "content"):
                    for block in msg.content:
                        if block.get("type") == "text":
                            print(f"Agent: {block['text']}")
```

---

## 18. Migration from claude-code-sdk

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

2. **Settings sources no longer loaded by default** -- CLAUDE.md, .claude/ configs, and user settings are NOT loaded unless you opt in:
   ```typescript
   settingSources: ["user", "project", "local"]
   ```

To fully restore old `claude-code-sdk` behavior, use both options together.

---

## 19. TypeScript V2 Preview

A simplified session-based API is available as a preview:

```typescript
import {
  unstable_v2_createSession,
  unstable_v2_resumeSession,
  unstable_v2_prompt,
} from "@anthropic-ai/claude-agent-sdk";

// Create a session
await using session = await unstable_v2_createSession({
  model: "claude-sonnet-4-6",
  allowedTools: ["Read", "Edit", "Bash"],
});

// Send a prompt and stream response
const response = session.send("Find bugs in auth.py");
for await (const event of response) {
  // process streaming events
}

// Or use stream() for full message objects
const stream = session.stream("Now fix them");
for await (const msg of stream) {
  // process messages
}

// Resume a previous session
const resumed = await unstable_v2_resumeSession(sessionId);

// One-shot helper (no session management)
for await (const msg of unstable_v2_prompt("Quick question", { model: "claude-haiku-4-5" })) {
  // process
}
```

`await using` (TypeScript 5.2+) automatically closes the session when the scope exits. The V2 API does not yet support session forking.

---

## 20. ClaudeSDKClient Methods (Python)

The Python `ClaudeSDKClient` provides additional runtime control methods:

```python
async with ClaudeSDKClient() as client:
    # Core conversation
    await client.query("Analyze the codebase")
    async for msg in client.receive_response():
        pass

    # Runtime controls
    await client.set_permission_mode("bypassPermissions")
    await client.set_model("claude-sonnet-4-6")

    # File management
    await client.rewind_files()  # undo file changes made by agent

    # MCP server management
    status = await client.get_mcp_status()
    await client.add_mcp_server("new-server", {"command": "node", "args": ["server.js"]})
    await client.remove_mcp_server("old-server")
    info = await client.get_server_info()

    # Interrupt current generation
    await client.interrupt()

    # Clean disconnect
    await client.disconnect()
```

---

## Official Resources

- [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [TypeScript Reference](https://platform.claude.com/docs/en/agent-sdk/typescript)
- [Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [Subagents Guide](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Permissions Guide](https://platform.claude.com/docs/en/agent-sdk/permissions)
- [Hooks Guide](https://platform.claude.com/docs/en/agent-sdk/hooks)
- [Custom Tools / MCP](https://platform.claude.com/docs/en/agent-sdk/custom-tools)
- [Sessions](https://platform.claude.com/docs/en/agent-sdk/sessions)
- [Hosting](https://platform.claude.com/docs/en/agent-sdk/hosting)
- [Secure Deployment](https://platform.claude.com/docs/en/agent-sdk/secure-deployment)
- [Migration Guide](https://platform.claude.com/docs/en/agent-sdk/migration-guide)
- [V2 Preview (TypeScript)](https://platform.claude.com/docs/en/agent-sdk/typescript-v2-preview)
- [Structured Output](https://platform.claude.com/docs/en/agent-sdk/structured-outputs)
- [Cost Tracking](https://platform.claude.com/docs/en/agent-sdk/cost-tracking)
- [Demo Apps](https://github.com/anthropics/claude-agent-sdk-demos)
