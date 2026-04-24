# Stripe Agent Toolkit and MCP Server

Stripe's first-party tooling for LLM tool-calling against the Stripe API.

## Two products, same security model

- **Agent Toolkit** (`stripe-agent-toolkit` / `@stripe/agent-toolkit`) -- a library that exposes Stripe actions as tools for OpenAI Agents SDK, Vercel AI SDK, LangChain, and CrewAI.
- **Stripe MCP Server** -- an MCP-compliant server at `https://mcp.stripe.com` (OAuth) or `npx -y @stripe/mcp --api-key=...` (local stdio).

Use Agent Toolkit when you're building a product where an LLM calls Stripe in-request. Use MCP when an MCP-aware client (Claude Code, Claude Desktop, Cursor) needs ad-hoc Stripe access.

## When NOT to use either

- Writing deterministic backend integrations (cron jobs, webhook handlers, checkout flows) -- use the raw SDK. Faster, cheaper, no LLM error rate.
- Actions requiring atomicity across multiple Stripe calls. LLMs may stop partway or retry incorrectly. Script it.

Rule of thumb: toolkit when a human is in the loop and the action depends on natural-language input; raw SDK otherwise.

## Gotchas

- **Never pass a full `sk_...` secret key to an LLM.** Create a Restricted API Key (RAK) at Dashboard -> Developers -> API keys, scoped to only the actions the agent needs. Out-of-scope calls return 403 -- that's the blast-radius containment you want.
- **RAKs per-use-case, not per-user.** Rotate quarterly.
- **Connect platforms:** pass `configuration.context.account` (Python) / `stripeAccount` equivalent (TS) to operate on a connected account. Equivalent to `Stripe-Account` header on raw SDK.
- **Observability is load-bearing.** Log the Stripe `request_id` from every tool call, tie it to your trace store. Without this, "agent refunded the wrong customer" is unrecoverable.
- **Tool availability is controlled by the RAK**, not by toolkit configuration. Revoking a permission in Dashboard immediately tightens the agent.

## Official docs

- Repo (canonical code samples for all 4 frameworks): https://github.com/stripe/agent-toolkit
- Stripe agents overview: https://docs.stripe.com/agents
- "Adding payments to your agentic workflows" blog: https://stripe.dev/blog/adding-payments-to-your-agentic-workflows
- MCP server docs: https://docs.stripe.com/agents (see MCP section)
- Restricted API Keys: https://docs.stripe.com/keys#create-restricted-api-secret-key

## Related

- `stripe.md` -- core API patterns the toolkit calls under the hood
- `webhooks-production.md` -- production readiness for any Stripe integration
