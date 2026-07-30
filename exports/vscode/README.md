# VS Code Copilot export catalog

A VS Code Copilot port of [acaprino/claude-code-daodan](https://github.com/acaprino/claude-code-daodan), packaged as **36 independently installable bundles**. Each bundle is a self-contained `.github/` directory holding skills, agents, and prompt files. Copy the ones you want into your project; ignore the rest.

The catalog is not a single install. That is the point: VS Code loads the `description` of every agent and skill present in a workspace to route requests, so a Rust project that also carries Stripe, MT5 and SEO agents pays for them on every turn. One bundle per concern keeps that cost proportional.

## Install

```bash
cp -r exports/vscode/<bundle>/.github  /path/to/your/project/
```

If the project already has a `.github/` directory, copy the three subdirectories individually:

```bash
cp -r exports/vscode/<bundle>/.github/skills/*  /path/to/your/project/.github/skills/
cp    exports/vscode/<bundle>/.github/prompts/* /path/to/your/project/.github/prompts/
cp    exports/vscode/<bundle>/.github/agents/*  /path/to/your/project/.github/agents/
```

Bundles compose: copying several merges cleanly, because every agent, skill and prompt name is unique across the whole catalog. VS Code picks them up without a restart. Verify with **Chat: Configure Agents**, and by typing `/` in the Chat view.

For a monorepo where the bundle lives at the repository root but you open a subfolder, enable `chat.useCustomizationsInParentRepositories`.

## The catalog

`_pipelines` is the flagship bundle and the only one that carries more than one upstream plugin. It holds the two multi-agent pipelines (`/xray-team-analyze`, `/team-review`) plus the vendored superpowers methodology, and it has [its own README](_pipelines/README.md).

| Bundle | Entry points | SK / AG / PR | Needs |
|---|---|---|---|
| **`_pipelines`** | `/xray-team-analyze`, `/team-review`, `superpowers` | 18 / 27 / 2 | python, playwright-mcp (optional) |
| `ai-tooling` | `/prompt-optimize` | 1 / 1 / 1 | |
| `app-analyzer` | `app-analyzer` | 0 / 1 / 0 | **playwright-mcp** |
| `browser-extensions` | `/firefox-scaffold`, `/firefox-lint`, `/firefox-publish` | 1 / 1 / 3 | |
| `business` | `business-planner`, `legal-advisor`, `privacy-doc-generator` | 1 / 3 / 0 | websearch |
| `clean-code` | `/clean-code` | 0 / 1 / 1 | |
| `codebase-cleanup` | `/deps-audit`, `/refactor-clean`, `/tech-debt` | 0 / 0 / 3 | |
| `codebase-mapper` | `/map-codebase`, `/docs-create`, `/docs-maintain`, `/humanize-docs` | 1 / 11 / 4 | |
| `csp` | `or-tools-expert` | 0 / 1 / 0 | |
| `digital-marketing` | `/seo-audit`, `/llm-seo-audit`, `/ga4-audit`, `/content-strategy`, `/brand-naming`, `/reply-to-customer-review` | 4 / 4 / 6 | websearch, **playwright-mcp**, python |
| `docker` | `multi-stage-dockerfile` | 1 / 0 / 0 | |
| `docs` | `readme-craft`, `/maintain-readme` | 1 / 0 / 1 | |
| `grabber-development` | `grabber-architect` + 3 specialists | 1 / 4 / 0 | **playwright-mcp** |
| `ibkr-trading` | `/ibkr-audit` | 1 / 1 / 1 | |
| `kotlin-development` | `kotlin-specialist` | 1 / 0 / 0 | |
| `learning` | `/export-to-markmind` | 3 / 0 / 1 | python |
| `libgdx-development` | `/libgdx-audit` | 1 / 1 / 1 | |
| `marketplace-ops` | `/marketplace-health`, `/marketplace-review`, `/marketplace-scaffold-plugin`, `/skills-validate` | 2 / 1 / 4 | python |
| `messaging` | `rabbitmq-expert` | 0 / 1 / 0 | |
| `mt5-trading` | `/mt5-audit` | 1 / 1 / 1 | |
| `obsidian-development` | `obsidian-scaffold`, `obsidian-check` | 3 / 0 / 0 | |
| `opentelemetry` | `/otel-audit` | 1 / 1 / 1 | |
| `platform-engineering` | `/platform-review` | 1 / 1 / 1 | |
| `project-setup` | `/create-claude-md`, `/maintain-claude-md` | 0 / 1 / 2 | |
| `pwa-expert` | `/pwa-audit`, `/pwa-scaffold`, `/pwa-checklist` | 1 / 1 / 3 | **playwright-mcp** for live-URL mode |
| `python-development` | `/python-scaffold`, `/python-refactor`, `/python-audit` | 9 / 3 / 3 | python |
| `rag-development` | `/rag-audit` | 1 / 2 / 1 | |
| `react-development` | `/review-react` | 1 / 1 / 1 | |
| `research` | `/team-research` | 1 / 3 / 1 | websearch, python |
| `stripe` | `/audit-webhooks` | 1 / 3 / 1 | python |
| `system-utils` | `/organize-files` | 1 / 0 / 1 | |
| `tauri-development` | `tauri-desktop`, `tauri-mobile`, `rust-engineer` | 1 / 3 / 0 | |
| `testing` | `tdd`, `e2e-testing-patterns`, `test-writer` | 2 / 1 / 0 | |
| `text-humanizer` | `/humanize-text` | 1 / 1 / 1 | |
| `typescript-development` | `typescript-engineer` | 3 / 1 / 0 | |
| `xterm` | `/xterm-debug`, `/xterm-implement` | 1 / 0 / 2 | |

SK / AG / PR counts skills, agents and prompt files. A **bold** requirement means the bundle's headline feature does not work without it.

## Optional companions

Three capabilities live outside the bundles. Nothing is vendored, and every bundle degrades explicitly rather than failing when one is missing.

| Capability | Where it comes from | Which bundles reach for it |
|---|---|---|
| **Web search** | The [Web Search for Copilot](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-websearchforcopilot) extension contributes `#websearch` (needs a Tavily or Bing API key). Copilot Chat's own Bing-backed search is an alternative, behind the "Copilot Access to Bing" policy. | `business`, `research`, `digital-marketing` |
| **Browser automation** | [playwright-mcp](https://github.com/microsoft/playwright-mcp), an MCP server. Add it under **Settings > AI > Manage MCP Servers**. | `app-analyzer`, `digital-marketing`, `grabber-development`, `pwa-expert`, `_pipelines` |
| **Python 3.10+** | Your machine. Only needed by bundles that ship helper scripts. | `_pipelines`, `python-development`, `stripe`, `marketplace-ops`, `learning`, `digital-marketing`, `research` |

Web search has no built-in VS Code tool. Agents that need it declare `websearch` in their `tools:` allowlist, which resolves once the extension is installed and is inert otherwise. Browser automation is the opposite case: an MCP server's tool ids depend on the name the user gives that server, so they cannot be allowlisted at all. The five agents that drive a browser therefore ship **without** a `tools:` field, which in VS Code grants the full available tool set. Each says so in a comment at the top of the file.

## Cross-bundle links

Bundles reference each other in prose all over the catalog ("for React performance, the `react-development` bundle covers it"). Those are pointers, not dependencies: nothing breaks if the other bundle is absent.

Exactly two references are real, both declared in an orchestrator's `agents:` allowlist, and both degrade:

| Bundle | Wants | Behavior when absent |
|---|---|---|
| `codebase-mapper` | `xray-interconnect-mapper`, from `_pipelines` | `/map-codebase` skips Phase 1b, warns once, and runs in degraded mode: writers fall back to the context brief alone |
| `research` | `codebase-explorer`, from `codebase-mapper` | `/team-research` skips the local-code angle, notes it in the report, and continues with the web angles |

## Differences from the Claude Code plugins

Catalog-wide. `_pipelines` documents its own differences separately, in [its README](_pipelines/README.md).

| Area | Claude Code | This port |
|---|---|---|
| Distribution | A marketplace you install plugins from | A directory of bundles you copy. There is no plugin system in Copilot, so a bundle is self-contained or it is nothing. |
| Commands | Plugin commands, namespaced `plugin:command` | `.github/prompts/*.prompt.md`. Namespaces are gone: `/senior-review:team-review` is `/team-review`. |
| Single-agent commands | The command body dispatches a subagent | The prompt binds the agent directly with `agent:` in frontmatter. VS Code gates dispatch behind an `agents:` allowlist that a prompt file cannot declare, and a one-hop dispatch buys nothing. |
| Multi-agent pipelines | The command body fans out from the main agent | A named orchestrator agent per pipeline, which is the only thing that can hold the `agents:` allowlist |
| Multi-agent teams | The `agent-teams` plugin plus `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | Native `#agent/runSubagent`. No flag, no plugin, nothing to tear down. |
| Barriers | `TaskList` polling on task status | File existence on disk, verified with `#search/fileSearch` |
| Script paths | `${CLAUDE_PLUGIN_ROOT}` expansion | `$SKILLS`, resolved by probing `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` |
| Skill descriptions | `TRIGGER WHEN:` / `DO NOT TRIGGER WHEN:` routing labels | Plain activation prose. The labels are a Claude Code convention; VS Code routes on the description itself. |
| Browser automation | The `playwright-skill` plugin | playwright-mcp, see above |
| `/team-codebase-map` | A parallel variant of `/map-codebase` built on `agent-teams` | Dropped. Once the team layer is deleted it is identical to `/map-codebase`, which already runs its six writers concurrently. |
| `/content-strategy` fan-out | Three concurrent dispatches of `content-marketer` | Three sequential passes. The three are lenses of one persona on one target, not independent reviewers whose independence carries information. |
| `project-setup` target file | `CLAUDE.md` | `AGENTS.md` or `.github/copilot-instructions.md`, with `CLAUDE.md` still honored when a project has one. Each file says so up front; the substance is unchanged. |

### Content that deliberately keeps Claude Code vocabulary

Two bundles have Claude Code itself as their **subject matter**, and their tool names are content rather than references:

- `marketplace-ops` authors Claude Code plugin marketplaces. Its `skills-creator` and `marketplace-audit` skills document the `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task` frontmatter vocabulary and the `TRIGGER WHEN` convention, because that is what the reader is being taught to write.
- `ai-tooling/agent-sdk-builder` documents the Claude Agent SDK, where `allowedTools: ["Read", "Grep", "Glob"]` and the `CLAUDE_CODE_*` environment variables are the real API.

Renaming those would make the material wrong. Anything that greps the export for Claude Code coupling must exclude them.

## Not exported

**`prompt-improver`** is a `UserPromptSubmit` hook: it rewrites the user's prompt before the model sees it. VS Code exposes only `PreToolUse`-style hooks on agents, with no equivalent interception point, so there is nothing faithful to port.

Everything else in the marketplace has a bundle. Three plugins have no bundle of their own because `_pipelines` already carries them whole: `codebase-xray`, `senior-review`, and `abstraction-architect`. Splitting them out would duplicate 68 files under a second set of names, and a user who installed both copies would get two variants of every reviewer competing for the same request.

Four commands stay unexported for reasons `_pipelines` already records: `/codebase-xray:analyze` (the single-partition fallback covers it), `/senior-review:code-review` and `/senior-review:pr-review` (no automated fix loop ships here), and `/abstraction-architect:audit` (the agent runs as a `/team-review` dimension).

## Conventions

Every file in every bundle follows the same shape.

- **Skills** carry `name`, `description`, `user-invocable`, `license: MIT`, and a `metadata` block naming the author, `acaprino/claude-code-daodan` as source, and the upstream plugin.
- **Agents** carry `name`, `description`, `user-invocable`, `tools` (a YAML list of VS Code tool ids), and `agents` (the dispatch allowlist, `[]` for leaf agents). Each begins with an HTML comment naming the file it was vendored from.
- **Prompts** carry `description`, an optional `agent` binding, and an optional unquoted `argument-hint`.
- Agent and skill names are unique across the entire catalog, so bundles can be combined freely.
- Export-only files, which have no upstream source, say so in a comment explaining why they exist. There are three: the two orchestrators (`map-codebase-orchestrator`, `research-orchestrator`) and the `_pipelines` support agents.

`plugins/` upstream is the source of truth and this directory is derived. Never edit a bundle and back-port: fix it upstream, then mirror.
