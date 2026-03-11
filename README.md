# Alfio Claude Plugins

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/marketplace-v1.56.0-green.svg)](.claude-plugin/marketplace.json)
[![Plugins](https://img.shields.io/badge/plugins-22-orange.svg)](#plugins)

22 ready-to-install plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) -- an AI coding CLI by Anthropic. Specialized agents, skills, and commands for Python, code review, frontend, Tauri/Rust, AI tooling, Obsidian, and more -- so you spend less time prompting and more time shipping.

**22 plugins | 19 agents | 25 skills | 18 commands** -- install only what you need.

---

## Why Use These Plugins?

- **Specialized agents outperform generic prompts** -- each plugin encodes domain expertise that took months to develop
- **Multi-agent orchestration** -- code review runs architecture, security, and pattern analysis in parallel
- **Cross-plugin workflows** -- chain brainstorming, planning, implementation, review, and cleanup into single commands
- **Install only what you need** -- each plugin is independent with no runtime dependencies
- **Community-driven and open source** -- MIT licensed, contributions welcome

| Type | What it is | How to use |
|------|-----------|------------|
| **Agent** | A specialized AI persona with domain expertise | `Use the python-pro agent to implement rate limiting` |
| **Skill** | A knowledge module that enhances Claude's capabilities | Referenced automatically when relevant |
| **Command** | A slash command that triggers a specific workflow | `/code-review`, `/python-scaffold`, `/feature-e2e` |

---

## Installation

### From GitHub (Recommended)

**Step 1:** Add the marketplace
```bash
claude plugin marketplace add acaprino/alfio-claude-plugins
```

**Step 2:** Install the plugins you need
```bash
# Install individual plugins (pick what you need)
claude plugin install python-development@alfio-claude-plugins
claude plugin install code-review@alfio-claude-plugins
claude plugin install frontend@alfio-claude-plugins
# ... see Plugins table below for all 22 available plugins
```

### From Local Path (Development)

```bash
git clone https://github.com/acaprino/alfio-claude-plugins.git
claude plugin install ./alfio-claude-plugins/plugins/python-development
```

---

## Plugins

| Plugin | Description | Agents | Skills | Commands | Docs |
|--------|-------------|:------:|:------:|:--------:|:----:|
| **python-development** | Modern Python development ecosystem with testing, packaging, async patterns, and code refactoring tools | 1 | 8 | 2 | [docs](docs/plugins/python-development.md) |
| **humanize** | Make AI-generated code look human-written -- fixes names, removes boilerplate | 1 | - | 1 | [docs](docs/plugins/humanize.md) |
| **deep-dive-analysis** | Understand any codebase in minutes with 7-phase systematic analysis | - | 1 | 1 | [docs](docs/plugins/deep-dive-analysis.md) |
| **code-review** | Catch bugs before they ship -- 3 agents review architecture, security, and patterns in parallel | 3 | - | 3 | [docs](docs/plugins/code-review.md) |
| **tauri-development** | Build cross-platform desktop and mobile apps with Tauri 2 and Rust | 2 | 1 | - | [docs](docs/plugins/tauri-development.md) |
| **frontend** | Optimize React performance, polish UI, design layouts, and master modern CSS | 5 | 4 | 1 | [docs](docs/plugins/frontend.md) |
| **ai-tooling** | Brainstorm, plan, and execute with structured AI-assisted workflows | 1 | 3 | 1 | [docs](docs/plugins/ai-tooling.md) |
| **stripe** | Integrate Stripe payments without reading 500 pages of docs | - | 2 | - | [docs](docs/plugins/stripe.md) |
| **utilities** | Clean up messy folders, find duplicates, and remove dead code | - | 1 | 2 | [docs](docs/plugins/utilities.md) |
| **business** | Navigate tech law, compliance, contracts, and risk management | - | 1 | - | [docs](docs/plugins/business.md) |
| **project-setup** | Create and maintain accurate CLAUDE.md files with ground truth verification | 1 | - | 2 | [docs](docs/plugins/project-setup.md) |
| **code-documentation** | Generate accurate docs by analyzing your code first, not guessing | 1 | - | 2 | [docs](docs/plugins/code-documentation.md) |
| **csp** | Solve scheduling, routing, and assignment problems with OR-Tools CP-SAT | 1 | - | - | [docs](docs/plugins/csp.md) |
| **digital-marketing** | Run SEO audits, content strategy, and conversion optimization | 2 | - | 2 | [docs](docs/plugins/digital-marketing.md) |
| **messaging** | Design and optimize RabbitMQ messaging with expert AMQP patterns | 1 | - | - | [docs](docs/plugins/messaging.md) |
| **research** | Find precise answers fast with advanced multi-source search strategies | 1 | - | - | [docs](docs/plugins/research.md) |
| **mobile-development** | Analyze competitor Android apps via ADB with automated screenshots | - | 1 | - | [docs](docs/plugins/mobile-development.md) |
| **typescript-development** | Write clean TypeScript with coding standards and Knip dead code detection | - | 2 | - | [docs](docs/plugins/typescript-development.md) |
| **workflows** | Run entire dev workflows with one command -- brainstorm to review to cleanup | - | - | 4 | [docs](docs/plugins/workflows.md) |
| **app-explorer** | Map any webapp's screens and navigation with Playwright crawling | - | 1 | - | [docs](docs/plugins/app-explorer.md) |
| **browser-extensions** | Build Firefox extensions with expert Manifest V2/V3 and AMO publishing guidance | - | 1 | - | [docs](docs/plugins/browser-extensions.md) |
| **obsidian-development** | Pass ObsidianReviewBot on first submission with compliant scaffolding and checks | - | 3 | - | [docs](docs/plugins/obsidian-development.md) |

See [Quick Start Workflows](docs/workflows.md) for end-to-end pipelines like `/feature-e2e`, `/code-review`, `/frontend-redesign`, and more.

---

<details>
<summary><h2>Project Structure</h2></summary>

```
alfio-claude-plugins/
├── .claude-plugin/
│   └── marketplace.json
├── docs/
│   ├── workflows.md
│   └── plugins/
│       └── <plugin-name>.md      # one file per plugin
├── plugins/
│   ├── python-development/
│   │   ├── agents/
│   │   ├── skills/
│   │   └── commands/
│   ├── code-review/
│   │   ├── agents/
│   │   └── commands/
│   ├── frontend/
│   │   ├── agents/
│   │   ├── skills/
│   │   └── commands/
│   └── ...                       # 22 plugins total
├── LICENSE
└── README.md
```

</details>

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your agent/skill following the existing structure
4. Update `marketplace.json` with your additions
5. Submit a pull request

### Agent Template

```markdown
---
name: agent-name
description: Brief description of the agent's purpose
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
color: blue
---

Agent instructions and expertise...
```

### Skill Template

```markdown
---
name: skill-name
description: Brief description of the skill's purpose
---

# Skill Name

## Overview
...

## When to Use
...

## How to Use
...
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

Created and maintained by [Alfio](https://github.com/acaprino).
