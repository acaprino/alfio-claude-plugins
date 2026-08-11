---
name: agent-sdk-builder
description: >
  Run the Claude Agent SDK (formerly Claude Code SDK) loop inside your own program: tool integration, subagent orchestration, prompt caching, and model migration. Not the `anthropic` client SDK for chat completions.
  TRIGGER WHEN: code references claude-agent-sdk, user says "agent sdk", "build an agent", "programmatic claude", "claude code sdk", "sidecar", "run claude programmatically".
---

# Claude Agent SDK

Build applications that run the Claude Code agent loop programmatically: agents that read files,
write code, run commands, search the web, and delegate to subagents from inside your own program.

**Key distinction**: the Agent SDK (`claude-agent-sdk`) runs the full agent loop with built-in
tools. The Anthropic Client SDK (`anthropic`) makes raw API calls. Use the Agent SDK when you want
an autonomous tool-using agent, not a chat completion.

| | TypeScript | Python |
|---|---|---|
| **Package** | `@anthropic-ai/claude-agent-sdk` | `claude-agent-sdk` |
| **Install** | `npm install @anthropic-ai/claude-agent-sdk` | `pip install claude-agent-sdk` |
| **Auth** | `ANTHROPIC_API_KEY` env var | `ANTHROPIC_API_KEY` env var |
| **Entry point** | `query()` | `query()` |
| **Source** | `anthropics/claude-agent-sdk-typescript` | `anthropics/claude-agent-sdk-python` |

The CLI package `@anthropic-ai/claude-code` ships inside the SDK. No separate install.

---

## Source of truth

This SDK changes faster than any bundled document. Option shapes, tool names, defaults, and whole
features move between releases: `fork_session` changed type, `plugins` changed from paths to config
objects, and the TypeScript V2 preview was removed outright. Treat this skill's knowledge as
orientation, never as the authority.

Three tiers. Stop at the first one that answers the question:

1. **The project's installed SDK.** TypeScript: the type definitions under
   `node_modules/@anthropic-ai/claude-agent-sdk/` and the version in its `package.json`. Python:
   the installed package under `site-packages/claude_agent_sdk/`, or `inspect.signature()` on the
   symbol. This tier wins over everything else, because it is what the user's code will run
   against.
2. **Current official documentation**, https://code.claude.com/docs/en/agent-sdk/. Use it when
   nothing is installed yet, or when the question is about behavior rather than a signature.
3. **The references in this skill.** Worked examples and orientation. Never the last word on a
   signature, an option shape, a default, or whether a feature still exists.

Classify a claim before you rely on it:

| Class | Example | Resolve with |
|---|---|---|
| STABLE | "Restrict `allowedTools` to what the task needs." | This skill |
| API-SENSITIVE | "`forkSession` is a boolean used with `resume`." | Tier 1, then tier 2 |
| MODEL-SENSITIVE | "This model id and effort level exist." | Tier 2 |

Never emit API-sensitive code from memory when tier 1 or tier 2 can settle it. Items marked
*(verify)* in the references are the ones that failed tier-2 resolution at the last refresh: they
are unconfirmed rather than confirmed-absent, and checking them is cheap.

---

## Step 1: Detect the environment

Do this before writing a line of code, and state what you found.

- **Language.** A `package.json` naming `@anthropic-ai/claude-agent-sdk` means TypeScript. A
  `pyproject.toml`, `requirements.txt`, or `uv.lock` naming `claude-agent-sdk` means Python.
- **Installed version.** `npm ls @anthropic-ai/claude-agent-sdk` or `pip show claude-agent-sdk`.
  Record it: every API-sensitive answer you give is relative to that version.
- **Nothing installed.** Say so, install the current release, and resolve signatures from tier 2.
- **Version pinned below current.** Honor the pin. Resolve against the installed types, and if the
  user asks for a feature that release does not have, say which version added it instead of
  emitting code that cannot run.

## Step 2: Pick the shape

| Need | Shape | Reference |
|---|---|---|
| One task, run to completion | `query()` | `references/sdk-api.md` |
| Multi-turn with retained context | `ClaudeSDKClient` (Python), or `query()` with `resume` | `references/sessions-subagents.md` |
| Branch a conversation without mutating it | `resume` plus `forkSession` | `references/sessions-subagents.md` |
| Delegate specialized work | `agents` plus the `Agent` tool | `references/sessions-subagents.md` |
| Give the agent your own functions | in-process MCP server | `references/mcp-plugins-skills.md` |
| Reuse existing Claude Code plugins | `plugins` and `settingSources` | `references/mcp-plugins-skills.md` |
| A machine-readable result | `outputFormat` with a JSON schema | `references/sdk-api.md` |
| Coarse "what may it use at all" | `allowedTools` / `disallowedTools` / `permissionMode` | `references/permissions-hooks-security.md` |
| A rule that must hold on every call | `PreToolUse` hook | `references/permissions-hooks-security.md` |
| Decide unresolved requests in code | `canUseTool` | `references/permissions-hooks-security.md` |
| Run untrusted work | sandbox and container isolation | `references/deployment.md` |
| Ship it somewhere | ephemeral or long-running hosting | `references/deployment.md` |

Load only the reference the chosen row names. Loading all five defeats the point.

## Step 3: Security model

Three mechanisms, three jobs. Substituting one for another is the most common way an SDK
application ends up with security that does not run:

| Mechanism | Job |
|---|---|
| `allowedTools` / `disallowedTools` / `permissionMode` | Coarse policy: what the agent may use at all |
| `PreToolUse` hook | Always-on enforcement: runs for every matching call, before permission resolution |
| `canUseTool` | Interactive fallback: runs only for calls no rule, mode, or hook already resolved |

**A validation rule that must always hold belongs in a `PreToolUse` hook.** Anything you allow-list
never reaches `canUseTool`, so a check placed there stops running the moment the tool is approved,
silently. `disallowedTools` is the only hard block and outranks even `bypassPermissions`. Details
and worked examples: `references/permissions-hooks-security.md`.

Also standing: set `maxTurns` and `maxBudgetUsd` on anything autonomous, keep secrets out of
prompts (use `env` or an MCP tool instead), and isolate untrusted work in a container.

## Step 4: Build and validate

1. Write the smallest program that does the job. Resist adding options you have not verified.
2. Resolve every API-sensitive detail against tier 1, then tier 2.
3. Type-check where the project supports it (`tsc --noEmit`, or the project's type checker).
4. Run it once on a cheap prompt with `maxTurns` and `maxBudgetUsd` set low, before running it for
   real.
5. Report which facts came from the installed SDK, which from the documentation, and name anything
   you could not verify. A named gap is useful; a confident guess is not.

---

## References

| File | Holds |
|---|---|
| `references/sdk-api.md` | Install, `query()`, full options table, built-in tools, streaming, structured output, cost tracking, migration from `claude-code-sdk` |
| `references/sessions-subagents.md` | Sessions, resume, fork, session metadata, introspection, subagent definitions, Python client methods |
| `references/permissions-hooks-security.md` | Permission modes and evaluation order, `canUseTool`, hook events and matchers, security practices |
| `references/mcp-plugins-skills.md` | Custom tools as in-process MCP servers, external MCP servers, loading plugins and settings |
| `references/deployment.md` | Hosting shapes, sandbox isolation, CI/CD review agent, research pipeline, chat loop |

`references/reasoning-patterns.md` in this directory belongs to the `prompt-engineer` agent, not to
the SDK. It sits here because the VS Code export mirrors plugin-root references into the consuming
skill directory.

## Official documentation

- [Overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [TypeScript reference](https://code.claude.com/docs/en/agent-sdk/typescript)
- [Python reference](https://code.claude.com/docs/en/agent-sdk/python)
- [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)
- [Hooks](https://code.claude.com/docs/en/agent-sdk/hooks)
- [Sessions](https://code.claude.com/docs/en/agent-sdk/sessions)
- [Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)
- [Custom tools and MCP](https://code.claude.com/docs/en/agent-sdk/custom-tools)
- [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- [Migration guide](https://code.claude.com/docs/en/agent-sdk/migration-guide)
- [Demo apps](https://github.com/anthropics/claude-agent-sdk-demos)
