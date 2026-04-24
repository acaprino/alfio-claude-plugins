# Stripe Agent Toolkit and MCP Server

Stripe ships first-party tooling to let LLM agents call Stripe APIs through function/tool-calling. Use this when you are building an AI feature that creates payment links, invoices, customers, or reports usage on behalf of a user -- not when you are writing backend integration code yourself.

Two separate products:

- **Stripe Agent Toolkit** -- a Python and TypeScript library (`stripe-agent-toolkit`, `@stripe/agent-toolkit`) that exposes Stripe actions as callable tools for OpenAI Agents SDK, Vercel AI SDK, LangChain, and CrewAI.
- **Stripe MCP Server** -- a Model Context Protocol server. Works with any MCP-aware client (Claude Desktop, Claude Code, Cursor, etc.). Available as a hosted endpoint at `https://mcp.stripe.com` and as a local `npx` process.

## When to use which

- **Agent Toolkit** -- when you're building a product feature where an LLM calls Stripe during a request (support chatbot creating a refund, agent creating invoices from parsed emails, RAG-over-Stripe-data). You control the framework and runtime.
- **MCP Server** -- when you're using an MCP-capable IDE/chat and want ad-hoc Stripe access ("create a test customer", "list my recent disputes"). You don't control the runtime; the IDE does.

Same security model underneath: a Restricted API Key (RAK) with scoped permissions.

## Security first: Restricted API Keys

Never use a full `sk_live_...` secret key with an LLM. Create a RAK at Dashboard -> Developers -> API keys -> Create restricted key. Grant only the actions the agent needs.

For a customer-support bot that issues refunds:

- `Customers`: Read
- `PaymentIntents`: Read
- `Charges`: Read
- `Refunds`: Write
- Everything else: None

If the LLM tries an action outside the scope, Stripe returns 403 and the agent sees the error in its tool-call trace. That is the whole point -- blast radius capped at the RAK.

For a billing agent that creates payment links:

- `Customers`: Write
- `Products`: Read
- `Prices`: Read
- `PaymentLinks`: Write

Keep RAKs per-use-case, not per-user. Rotate quarterly.

## Agent Toolkit: Python

### OpenAI Agents SDK

```python
from stripe_agent_toolkit.openai.toolkit import create_stripe_agent_toolkit
from agents import Agent, Runner

toolkit = await create_stripe_agent_toolkit(
    secret_key=os.environ["STRIPE_RESTRICTED_KEY"],  # rk_live_... or rk_test_...
)

stripe_agent = Agent(
    name="Billing Agent",
    instructions=(
        "You help customers manage their subscription. "
        "Use Stripe tools for anything involving billing. "
        "Confirm destructive actions (refunds, cancellations) before executing."
    ),
    tools=toolkit.get_tools(),
)

result = await Runner.run(stripe_agent, "Cancel my subscription at period end")
```

### LangChain

```python
from stripe_agent_toolkit.langchain.toolkit import StripeAgentToolkit
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

toolkit = StripeAgentToolkit(secret_key=os.environ["STRIPE_RESTRICTED_KEY"])
llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a billing assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
agent = create_tool_calling_agent(llm, toolkit.get_tools(), prompt)
executor = AgentExecutor(agent=agent, tools=toolkit.get_tools())
await executor.ainvoke({"input": "Show me this customer's last 3 invoices: cus_xxx"})
```

### CrewAI

```python
from stripe_agent_toolkit.crewai.toolkit import StripeAgentToolkit
from crewai import Agent as CrewAgent, Task, Crew

toolkit = StripeAgentToolkit(secret_key=os.environ["STRIPE_RESTRICTED_KEY"])
billing = CrewAgent(
    role="Billing Specialist",
    goal="Resolve billing inquiries",
    backstory="You are fluent in Stripe operations.",
    tools=toolkit.get_tools(),
)
```

## Agent Toolkit: TypeScript

### Vercel AI SDK

```typescript
import { StripeAgentToolkit } from '@stripe/agent-toolkit/ai-sdk';
import { openai } from '@ai-sdk/openai';
import { generateText } from 'ai';

const toolkit = new StripeAgentToolkit({
  secretKey: process.env.STRIPE_RESTRICTED_KEY!,
});

const { text } = await generateText({
  model: openai('gpt-4o'),
  tools: toolkit.getTools(),
  maxSteps: 5,
  prompt: 'Create a $20 payment link for product prod_abc and return the URL.',
});
```

### LangChain (TypeScript)

```typescript
import { createStripeAgentToolkit } from '@stripe/agent-toolkit/langchain';
import { ChatOpenAI } from '@langchain/openai';
import { AgentExecutor, createToolCallingAgent } from 'langchain/agents';

const toolkit = await createStripeAgentToolkit({
  secretKey: process.env.STRIPE_RESTRICTED_KEY!,
});
const tools = toolkit.getTools();
const agent = await createToolCallingAgent({ llm: new ChatOpenAI({ model: 'gpt-4o' }), tools, prompt });
const executor = new AgentExecutor({ agent, tools });
```

## Connect platforms

When your agent operates on behalf of a connected account (platform / marketplace), pass the `account` in configuration:

```python
toolkit = await create_stripe_agent_toolkit(
    secret_key=os.environ["STRIPE_PLATFORM_KEY"],
    configuration={"context": {"account": "acct_xxx"}},
)
```

All tool calls now execute against the connected account, equivalent to `Stripe-Account` header on raw SDK calls.

## MCP server

### Hosted (recommended)

Configure any MCP-aware client to use `https://mcp.stripe.com`. Authentication is OAuth -- the client walks the user through Stripe login, Stripe returns a scoped token, tool calls are authenticated per-session.

In Claude Code, for example, MCP servers are configured via settings; consult your client's MCP docs.

### Local (self-hosted)

```bash
npx -y @stripe/mcp --api-key=rk_live_...
```

Runs a stdio MCP server. Point your MCP client at this process.

The local variant is useful for:

- CI pipelines that need Stripe actions without OAuth
- Test-mode workflows in a sandbox account
- Air-gapped environments

Pass the RAK via `--api-key` or the `STRIPE_SECRET_KEY` env var. Same scoping rules as the toolkit.

## When NOT to use the toolkit

- You're writing a normal backend integration (checkout flow, webhook handler, invoice generation triggered by cron). Use the raw SDK -- it's faster, cheaper, and doesn't need an LLM in the loop.
- You need deterministic behavior. LLM tool-calling has nonzero error rate; a cron job does not.
- Your action requires atomicity across multiple Stripe calls. The LLM may stop partway, call the wrong action, or retry incorrectly. Script it.

Rule of thumb: toolkit if a human is in the loop and the Stripe action depends on natural-language input; raw SDK otherwise.

## Observability

Every tool call logs the Stripe request_id. Pipe those into your trace store:

```python
toolkit = await create_stripe_agent_toolkit(
    secret_key=os.environ["STRIPE_RESTRICTED_KEY"],
    configuration={
        "context": {"stripe_version": "2026-04-22.dahlia"},
    },
)
```

Pair with OpenTelemetry on your agent framework so you see:

1. User prompt
2. LLM tool-call decision
3. Stripe API request_id
4. Stripe response
5. LLM final output

Without this, debugging "agent created a refund for the wrong customer" is hard.

## Related

- `stripe.md` -- core patterns
- `stripe-patterns.md` -- Connect basics
- Agent Toolkit repo: https://github.com/stripe/agent-toolkit
- MCP docs: https://docs.stripe.com/agents
- Managing agents and payments (Stripe blog): https://stripe.dev/blog/adding-payments-to-your-agentic-workflows
