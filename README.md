<div align="center">

# Figs

**33 specialized plugins for Claude Code -- so you spend less time prompting and more time shipping.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat)](LICENSE)
[![Marketplace](https://img.shields.io/badge/marketplace-v2.83.0-green?style=flat)](.claude-plugin/marketplace.json)
[![Plugins](https://img.shields.io/badge/plugins-33-orange?style=flat)](#plugins)
[![Agents](https://img.shields.io/badge/agents-40-purple?style=flat)](#plugins)
[![Skills](https://img.shields.io/badge/skills-46-teal?style=flat)](#plugins)
[![Commands](https://img.shields.io/badge/commands-38-red?style=flat)](#plugins)

</div>

---

## Why Figs?

- **Domain experts, not generic prompts** -- each plugin encodes months of specialized knowledge (Python, Rust, React, security, SEO, legal...)
- **Multi-agent orchestration** -- code review fires architecture, security, and pattern analysis in parallel
- **End-to-end workflows** -- chain brainstorming, planning, implementation, review, and cleanup into single commands
- **Install only what you need** -- every plugin is independent, no runtime dependencies
- **Community-driven** -- MIT licensed, upstream-synced with projects from Anthropic, Vercel, and others

## Quick Start

```bash
# Add the marketplace
claude plugin marketplace add acaprino/figs

# Install the plugins you need
claude plugin install python-development@figs
claude plugin install senior-review@figs
claude plugin install frontend@figs
```

That's it. Plugins activate automatically when relevant -- or invoke them directly:

```bash
# Slash commands
/code-review          # Multi-agent architecture + security + pattern review
/feature-e2e          # Brainstorm -> plan -> implement -> review -> humanize
/python-scaffold      # Scaffold a production-ready Python project

# Agents
"Use the python-pro agent to implement rate limiting"
"Ask the rust-engineer to review my Tauri backend"
```

---

## Plugins

| Plugin | Description | A | S | C |
|--------|-------------|:-:|:-:|:-:|
| **[python-development](docs/plugins/python-development.md)** | TDD, refactoring, async patterns, packaging, performance, dead code detection | 1 | 8 | 2 |
| **[senior-review](docs/plugins/senior-review.md)** | 3 agents review architecture, security, and patterns in parallel | 3 | - | 4 |
| **[frontend](docs/plugins/frontend.md)** | UI polish, layout design, modern CSS, web strategy, Radix/shadcn/daisyUI | 2 | 6 | 1 |
| **[codebase-mapper](docs/plugins/codebase-mapper.md)** | Generate 10 narrative docs with Mermaid diagrams from any codebase | 10 | 1 | 4 |
| **[ai-tooling](docs/plugins/ai-tooling.md)** | Brainstorm, plan, execute, optimize prompts, Agent SDK | 1 | 5 | 1 |
| **[workflows](docs/plugins/workflows.md)** | End-to-end pipelines: feature dev, frontend redesign, mobile, Tauri, review | - | - | 7 |
| **[tauri-development](docs/plugins/tauri-development.md)** | Tauri 2 desktop + mobile, Rust backend, IPC optimization | 3 | 1 | - |
| **[digital-marketing](docs/plugins/digital-marketing.md)** | SEO audits, content strategy, brand naming, domain hunting | 2 | 2 | 3 |
| **[react-development](docs/plugins/react-development.md)** | React 19 performance, state management, bundle optimization | 1 | 1 | 1 |
| **[rag-development](docs/plugins/rag-development.md)** | RAG system design -- chunking, embeddings, vector DBs, advanced patterns | 2 | 1 | 1 |
| **[marketplace-ops](docs/plugins/marketplace-ops.md)** | Audit, scaffold, review, and manage plugins in this ecosystem | 1 | 2 | 3 |
| **[learning](docs/plugins/learning.md)** | Mind maps in MarkMind format and interactive force-graphs | - | 3 | 1 |
| **[deep-dive-analysis](docs/plugins/deep-dive-analysis.md)** | 7-phase systematic codebase analysis with pattern detection | - | 1 | 1 |
| **[git-worktrees](docs/plugins/git-worktrees.md)** | Parallel development with git worktrees -- create, pause, resume, merge | 1 | 1 | 1 |
| **[business](docs/plugins/business.md)** | Tech law, compliance, privacy docs, contracts, risk management | 2 | - | - |
| **[stripe](docs/plugins/stripe.md)** | Stripe payments, subscriptions, Connect, revenue optimization | 2 | - | - |
| **[research](docs/plugins/research.md)** | Quick search and deep multi-source investigation | 2 | - | - |
| **[project-setup](docs/plugins/project-setup.md)** | Create and maintain CLAUDE.md with ground truth verification | 1 | - | 2 |
| **[humanize](docs/plugins/humanize.md)** | Make AI-generated code look human-written | 1 | - | 1 |
| **[app-analyzer](docs/plugins/app-analyzer.md)** | Analyze Android apps via ADB and webapps via Playwright | 1 | - | - |
| **[xterm](docs/plugins/xterm.md)** | Build and debug xterm.js terminal emulators | - | 1 | 2 |
| **[obsidian-development](docs/plugins/obsidian-development.md)** | Pass ObsidianReviewBot on first try | - | 3 | - |
| **[typescript-development](docs/plugins/typescript-development.md)** | TypeScript best practices and Knip dead code detection | - | 2 | - |
| **[system-utils](docs/plugins/system-utils.md)** | Clean up messy folders, find duplicates | - | 1 | 1 |
| **[messaging](docs/plugins/messaging.md)** | RabbitMQ queue design and AMQP patterns | 1 | - | - |
| **[csp](docs/plugins/csp.md)** | Scheduling, routing, assignment with OR-Tools CP-SAT | 1 | - | - |
| **[browser-extensions](docs/plugins/browser-extensions.md)** | Firefox extensions with Manifest V2/V3 | 1 | 1 | - |
| **[playwright-skill](docs/plugins/playwright-skill.md)** | General-purpose browser automation with Playwright | - | 1 | - |
| **[cc-usage](docs/plugins/cc-usage.md)** | Token usage, costs, and billing analysis | - | 1 | 1 |
| **[prompt-improver](docs/plugins/prompt-improver.md)** | Enrich vague prompts with research-based questions | - | 1 | - |
| **[figs-hooks](docs/plugins/figs-hooks.md)** | Session hooks -- startup branding, skill awareness, security gate | - | - | - |
| **[docs](docs/plugins/docs.md)** | Craft top-tier README.md files | - | 1 | 1 |
| **[testing](docs/plugins/testing.md)** | TDD methodology and behavior-driven test generation | 1 | 1 | - |

**A** = Agents, **S** = Skills, **C** = Commands

---

<details>
<summary><b>How Plugins Work</b></summary>

| Type | What it is | How to use |
|------|-----------|------------|
| **Agent** | A specialized AI persona with domain expertise | `Use the python-pro agent to implement rate limiting` |
| **Skill** | A knowledge module Claude references automatically | Activates when the task matches its trigger keywords |
| **Command** | A slash command that kicks off a workflow | `/code-review`, `/python-scaffold`, `/feature-e2e` |

Plugins are pure Markdown with optional JS/Python helper scripts. No build step, no runtime framework.

</details>

<details>
<summary><b>Project Structure</b></summary>

```
figs/
├── .claude-plugin/
│   └── marketplace.json       # plugin registry
├── docs/plugins/              # per-plugin documentation
├── plugins/
│   ├── python-development/
│   │   ├── agents/            # .md files with YAML frontmatter
│   │   ├── skills/            # SKILL.md + optional references/
│   │   └── commands/          # slash-command .md files
│   ├── senior-review/
│   ├── frontend/
│   └── ...                    # 33 plugins total
├── LICENSE
└── README.md
```

</details>

<details>
<summary><b>Local Development Install</b></summary>

```bash
git clone https://github.com/acaprino/figs.git
claude plugin install ./figs/plugins/python-development
```

</details>

---

## Contributing

1. Fork the repository
2. Add your agent/skill/command following existing patterns
3. Register it in `marketplace.json`
4. Submit a pull request

<details>
<summary><b>Agent Template</b></summary>

```markdown
---
name: agent-name
description: When and how to use this agent
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
color: blue
---

Agent system prompt here...
```

</details>

<details>
<summary><b>Skill Template</b></summary>

```markdown
---
name: skill-name
description: When this skill activates
---

# Skill Name

Instructions, references, and domain knowledge...
```

</details>

---

<div align="center">

MIT License - [LICENSE](LICENSE)

Built by [Alfio](https://github.com/acaprino)

</div>
