# Agent SDK: sessions and subagents

Multi-turn sessions, resuming, forking, session metadata, introspection, subagent definitions
and behavior, and the Python `ClaudeSDKClient` runtime methods.

Method names and option shapes here are API-sensitive: resolve them against the installed SDK or
the current documentation before use, per the source-of-truth policy in `SKILL.md`.

---

## 1. Subagents -- Multi-Agent Orchestration


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
| `disallowedTools` | `string[]` | Tools to block |
| `mcpServers` | `object` | MCP servers available to subagent |
| `skills` | `string[]` | Skills the subagent can invoke |
| `memory` | `object` | Memory configuration for the subagent |
| `maxTurns` | `number` | Turn limit for this subagent |

Also documented: `initialPrompt`, `background`, `effort`, `permissionMode`.

### Subagent Behavior

- **Context isolation** -- each subagent gets a fresh conversation; only its final message returns to the parent
- **Parallel execution** -- multiple subagents run concurrently when spawned together
- **No nesting** -- subagents cannot spawn their own subagents
- **Resumable** -- subagents can be resumed by ID from tool results
- **Cost isolated** -- each subagent's token usage is tracked separately
- **Progress summaries** *(verify)* -- enable `agentProgressSummaries: true` to receive periodic AI-generated progress updates from running subagents

---

## 2. Session Management


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

// Branch instead of continuing: resume + forkSession leaves the original untouched
for await (const msg of query({
  prompt: "Try an alternative approach on a copy of this conversation",
  options: { resume: sessionId, forkSession: true },
})) { /* ... */ }
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
  tagSession, renameSession,
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

// Organize sessions with tags and renames
await tagSession(sessionId, "auth-refactor");
await renameSession(sessionId, "auth-refactor-v2");
```

```python
from claude_agent_sdk import (
    list_sessions, get_session_info, get_session_messages,
    tag_session, rename_session,
)

sessions = await list_sessions(dir="/path/to/project", limit=10)
for session in sessions:
    messages = await get_session_messages(session.session_id)

info = await get_session_info(session_id)
await tag_session(session_id, "auth-refactor")
await rename_session(session_id, "auth-refactor-v2")
```

### Session State Events

Session state change events are **opt-in** as of v0.2.83 *(verify)*. Enable with environment variable:

```bash
export CLAUDE_CODE_EMIT_SESSION_STATE_EVENTS=1
```

### Exit Reasons

The `ExitReason` type includes: `"end_turn"`, `"max_turns"`, `"budget"`, `"interrupt"`, `"resume"` *(verify)*.

---

## 3. Introspection Utilities


```typescript
import { supportedAgents } from "@anthropic-ai/claude-agent-sdk";

// Discover available subagents
const agents = await supportedAgents();
```

`getSettings()` *(verify)* appears in some SDK versions for inspecting runtime-resolved settings, but is not in the currently documented API.

---

## 4. ClaudeSDKClient Methods (Python)


The Python `ClaudeSDKClient` provides additional runtime control methods:

```python
async with ClaudeSDKClient() as client:
    # Core conversation
    await client.query("Analyze the codebase")
    async for msg in client.receive_response():
        pass

    # Runtime controls
    await client.set_permission_mode("acceptEdits")
    await client.set_model("claude-sonnet-5")

    # MCP server management
    status = await client.get_mcp_status()
    await client.toggle_mcp_server("my-server", enabled=False)

    # Interrupt current generation
    await client.interrupt()

    # Clean disconnect
    await client.disconnect()
```
