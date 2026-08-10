# Agent SDK: deployment and worked patterns

Ephemeral versus long-running session hosting, custom process spawning, sandbox isolation, and
three end-to-end patterns: a CI/CD review agent, a multi-agent research pipeline, and an
interactive chat loop.

---

## 1. Hosting & Deployment Patterns


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

### Custom Process Spawning *(verify)*

Run agents in VMs, containers, or remote environments. `spawnClaudeCodeProcess` ships in some SDK versions but is not in the currently documented API; confirm before building on it:

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

The `sandbox` option enables sandboxed execution for agent tool calls. Anthropic also publishes a standalone sandboxing runtime (`@anthropic-ai/sandbox-runtime`) for isolating the whole agent process; its API surface changes faster than this file, so take exact usage from that package's README rather than from memory.

---

## 2. Common Patterns


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
