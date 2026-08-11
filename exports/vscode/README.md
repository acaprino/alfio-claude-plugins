# Claude Code Daodan for GitHub Copilot

A VS Code Copilot port of [acaprino/claude-code-daodan](https://github.com/acaprino/claude-code-daodan): **88 agents, 68 skills and 49 prompts**, shipped as one extension. Install it once and every project you open has them. You never copy a `.github/` directory into a repository.

This directory is both the extension source and the catalog documentation. The 37 bundles below are how the content is organized on disk, not 37 separate installs.

## Install

Search for **Claude Code Daodan** in the Extensions view and click Install. Nothing else: no settings to edit, no repository to clone, no folder to copy.

On first start the extension does two things:

- **Agents and prompts** register straight from the extension through the `chatAgents` and `chatPromptFiles` contribution points. Type `/` in the Chat view to see the prompts; **Chat: Configure Agents** lists the agents.
- **Skills** are copied into `~/.copilot/skills/`, the personal skills location VS Code reads in every workspace. They cannot be contributed like the rest: 45 of the 66 carry supporting files under `references/`, `scripts/` and `assets/`, and a contributed skill loads only its `SKILL.md` ([microsoft/vscode#304721](https://github.com/microsoft/vscode/issues/304721)). Copying keeps those files together, and the `$SKILLS` probe already resolves there.

A skill directory that is already present and was not installed by the extension is never overwritten; it is reported and skipped.

| Command | What it does |
|---|---|
| **Daodan: Install or Refresh Skills** | Re-run the copy by hand, after changing the location or resolving a conflict |
| **Daodan: Remove Installed Skills** | Delete only the skills the extension installed |
| **Daodan: Reveal Skills Folder** | Open the install location in the OS file manager |

| Setting | Default | What it does |
|---|---|---|
| `daodan.autoSync` | `true` | Install and refresh skills on start and after an update |
| `daodan.skillsLocation` | `~/.copilot/skills` | Where skills are installed. Change it only for a path VS Code already scans. |

Uninstalling the extension removes the skills it installed.

### The cost of having everything everywhere

VS Code loads the `description` of every agent and skill available in order to route a request. With all 88 agents and 68 skills installed at user level, a Rust project carries the Stripe, MT5 and SEO descriptions too, on every turn. That is a real cost, accepted deliberately in exchange for one install that follows you into every project. Turn off what you do not want in the Agent Customizations editor (**Chat: Open Customizations**), or set `daodan.autoSync` to `false` and manage the skills folder yourself.

### Per-project install, without the extension

The bundles still work the old way when you want a single project to carry only what it needs:

```bash
cp -r exports/vscode/<bundle>/.github  /path/to/your/project/
```

If the project already has a `.github/` directory, copy the three subdirectories individually:

```bash
cp -r exports/vscode/<bundle>/.github/skills/*  /path/to/your/project/.github/skills/
cp    exports/vscode/<bundle>/.github/prompts/* /path/to/your/project/.github/prompts/
cp    exports/vscode/<bundle>/.github/agents/*  /path/to/your/project/.github/agents/
```

Bundles compose: copying several merges cleanly, because every agent, skill and prompt name is unique across the whole catalog. VS Code picks them up without a restart.

For a monorepo where the bundle lives at the repository root but you open a subfolder, enable `chat.useCustomizationsInParentRepositories`.

## The catalog

`_pipelines` is the flagship bundle and the only one that carries more than one upstream plugin. It holds the two multi-agent pipelines (`/xray-team-analyze`, `/team-review`) plus the vendored superpowers methodology, and it has [its own README](_pipelines/README.md).

| Bundle | Entry points | SK / AG / PR | Needs |
|---|---|---|---|
| **`_pipelines`** | `/xray-team-analyze`, `/team-review`, `superpowers` | 18 / 30 / 2 | python, playwright-mcp (optional), `testing` and `typescript-development` bundles (optional) |
| `ai-tooling` | `/prompt-optimize` | 1 / 1 / 1 | |
| `app-analyzer` | `app-analyzer` | 0 / 1 / 0 | **playwright-mcp** |
| `browser-extensions` | `/firefox-scaffold`, `/firefox-lint`, `/firefox-publish` | 1 / 1 / 3 | |
| `business` | `business-planner`, `legal-advisor`, `privacy-doc-generator` | 1 / 3 / 0 | websearch |
| `clean-code` | `/clean-code` | 0 / 1 / 1 | |
| `codebase-mapper` | `/map-codebase`, `/docs-create`, `/docs-maintain`, `/humanize-docs` | 1 / 11 / 4 | |
| `csp` | `or-tools-expert` | 0 / 1 / 0 | |
| `dependency-audit` | `/deps-audit` | 1 / 0 / 1 | |
| `digital-marketing` | `/seo-audit`, `/llm-seo-audit`, `/ga4-audit`, `/content-strategy`, `/brand-naming`, `/reply-to-customer-review` | 4 / 4 / 6 | websearch, **playwright-mcp**, python |
| `docker` | `multi-stage-dockerfile` | 1 / 0 / 0 | |
| `docs` | `readme-craft`, `/maintain-readme` | 1 / 0 / 1 | |
| `frontend-review` | `/review-frontend` | 0 / 1 / 1 | `react-development`, `typescript-development`, `pwa-expert` and `platform-engineering` bundles (optional), design skills copied by hand (optional) |
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
| `testing` | `/test-audit`, `/test-consolidate`, `test-writer`, `test-suite-auditor` | 1 / 2 / 2 | |
| `text-humanizer` | `/humanize-text` | 1 / 1 / 1 | |
| `typescript-development` | `/review-typescript`, `typescript-engineer` | 4 / 2 / 1 | |
| `xterm` | `/xterm-debug`, `/xterm-implement` | 1 / 0 / 2 | |

SK / AG / PR counts skills, agents and prompt files. A **bold** requirement means the bundle's headline feature does not work without it.

## Optional companions

Four capabilities live outside the bundles. Nothing is vendored, and every bundle degrades explicitly rather than failing when one is missing.

| Capability | Where it comes from | Which bundles reach for it |
|---|---|---|
| **Design skills** | Three repositories, copied by hand: [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (ships a Copilot-shaped `.github/skills/impeccable/`), [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (`ui-ux-pro-max` and `design-system`), and [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (`frontend-design`). Copy each skill directory whole into your skills folder. | `frontend-review` |
| **Web search** | The [Web Search for Copilot](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-websearchforcopilot) extension contributes `#websearch` (needs a Tavily or Bing API key). Copilot Chat's own Bing-backed search is an alternative, behind the "Copilot Access to Bing" policy. | `business`, `research`, `digital-marketing` |
| **Browser automation** | [playwright-mcp](https://github.com/microsoft/playwright-mcp), an MCP server. Add it under **Settings > AI > Manage MCP Servers**. | `app-analyzer`, `digital-marketing`, `grabber-development`, `pwa-expert`, `_pipelines` |
| **Python 3.10+** | Your machine. Only needed by bundles that ship helper scripts. | `_pipelines`, `python-development`, `stripe`, `marketplace-ops`, `learning`, `digital-marketing`, `research` |

Web search has no built-in VS Code tool. Agents that need it declare `websearch` in their `tools:` allowlist, which resolves once the extension is installed and is inert otherwise. Browser automation is the opposite case: an MCP server's tool ids depend on the name the user gives that server, so they cannot be allowlisted at all. The five agents that drive a browser therefore ship **without** a `tools:` field, which in VS Code grants the full available tool set. Each says so in a comment at the top of the file.

The design skills are the only companion with no install path at all: they ship as Claude Code plugins, and a skill directory copied into your skills folder is what this extension does for its own skills anyway. `/review-frontend` probes for the four directories and reviews against whichever it finds, so a partial copy is a working setup rather than a broken one.

## Cross-bundle links

Bundles reference each other in prose all over the catalog ("for React performance, the `react-development` bundle covers it"). Those are pointers, not dependencies: nothing breaks if the other bundle is absent.

Eight references are real, all declared in an orchestrator's `agents:` allowlist, and all degrade:

| Bundle | Wants | Behavior when absent |
|---|---|---|
| `codebase-mapper` | `xray-interconnect-mapper`, from `_pipelines` | `/map-codebase` skips Phase 1b, warns once, and runs in degraded mode: writers fall back to the context brief alone |
| `research` | `codebase-explorer`, from `codebase-mapper` | `/team-research` skips the local-code angle, notes it in the report, and continues with the web angles |
| `_pipelines` | `test-suite-auditor`, from `testing` | `/team-review` falls back to `review-generic-reviewer` with the testing dimension named in the prompt, and notes the fallback in the dimension plan |
| `_pipelines` | `type-safety-auditor`, from `typescript-development` | `/team-review` skips the TypeScript type-safety dimension and reports it as "not installed" under Skipped. There is no generic fallback: the 20-rule checklist it audits against lives in that bundle |
| `frontend-review` | `react-performance-optimizer`, from `react-development` | `/review-frontend` skips the React performance dimension, reports it as "bundle not installed" in the report's status table, and drops it from the weighted mean rather than scoring it zero |
| `frontend-review` | `type-safety-auditor`, from `typescript-development` | Same, for the TypeScript type-safety dimension |
| `frontend-review` | `pwa-architect`, from `pwa-expert` | Same, for the PWA architecture dimension |
| `frontend-review` | `platform-reviewer`, from `platform-engineering` | Same, for the platform compliance dimension |

## Differences from the Claude Code plugins

Catalog-wide. `_pipelines` documents its own differences separately, in [its README](_pipelines/README.md).

| Area | Claude Code | This port |
|---|---|---|
| Distribution | A marketplace you install plugins from | One VS Code extension, installed once and available in every workspace. The bundles remain copyable per project for anyone who wants a narrower install. |
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
| `/review-frontend` design dimension | A hard gate on three external plugins (`impeccable`, `ui-ux-pro-max`, `frontend-design`). Any one missing and the command stops with an install block. | Degraded instead. None of the three has a Copilot install path, so a stop-and-install gate would be a gate that can never pass. The prompt probes for their four skill directories, reviews against whichever are present, skips the dimension only when all four are absent, and names each missing source with the repository to copy its skill directory from. That also makes design a skippable dimension for scoring, which upstream it can never be. |

### Content that deliberately keeps Claude Code vocabulary

Two bundles have Claude Code itself as their **subject matter**, and their tool names are content rather than references:

- `marketplace-ops` authors Claude Code plugin marketplaces. Its `skills-creator` and `marketplace-audit` skills document the `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task` frontmatter vocabulary and the `TRIGGER WHEN` convention, because that is what the reader is being taught to write.
- `ai-tooling/agent-sdk-builder` documents the Claude Agent SDK, where `allowedTools: ["Read", "Grep", "Glob"]` and the `CLAUDE_CODE_*` environment variables are the real API.

Renaming those would make the material wrong. Anything that greps the export for Claude Code coupling must exclude them.

## Not exported

Every plugin in the marketplace has a bundle. Three plugins have no bundle of their own because `_pipelines` already carries them whole: `codebase-xray`, `senior-review`, and `abstraction-architect`. Splitting them out would duplicate 68 files under a second set of names, and a user who installed both copies would get two variants of every reviewer competing for the same request.

Four commands stay unexported for reasons `_pipelines` already records: `/codebase-xray:analyze` (the single-partition fallback covers it), `/senior-review:code-review` and `/senior-review:pr-review` (no automated fix loop ships here), and `/abstraction-architect:audit` (the agent runs as a `/team-review` dimension).

## Conventions

Every file in every bundle follows the same shape.

- **Skills** carry `name`, `description`, `user-invocable`, `license: MIT`, and a `metadata` block naming the author, `acaprino/claude-code-daodan` as source, and the upstream plugin.
- **Agents** carry `name`, `description`, `user-invocable`, `tools` (a YAML list of VS Code tool ids), and `agents` (the dispatch allowlist, `[]` for leaf agents). Each begins with an HTML comment naming the file it was vendored from.
- **Prompts** carry `description`, an optional `agent` binding, and an optional unquoted `argument-hint`.
- Agent and skill names are unique across the entire catalog, so bundles can be combined freely.
- Export-only files, which have no upstream source, say so in a comment explaining why they exist. There are four: the three orchestrators (`map-codebase-orchestrator`, `research-orchestrator`, `frontend-review-orchestrator`) and the `_pipelines` support agents.

`plugins/` upstream is the source of truth and this directory is derived. Never edit a bundle and back-port: fix it upstream, then mirror.
