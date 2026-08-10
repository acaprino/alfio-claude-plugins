# Agent SDK: custom tools, MCP servers, plugins and skills

Defining your own tools as in-process MCP servers, connecting external MCP servers over stdio and
HTTP, the `mcp__<server>__<tool>` naming convention, and loading Claude Code plugins and
filesystem settings into an SDK run.

---

## 1. Custom Tools via MCP


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

## 2. Plugins and Skills


Load local plugins to give the agent access to custom skills, agents, and commands:

```typescript
for await (const msg of query({
  prompt: "Review the frontend code",
  options: {
    plugins: [{ type: "local", path: "/path/to/my-plugin" }],
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
