# Figs Documentation

Custom Claude Code plugin marketplace. Agents, skills, and commands for development workflows, code quality, AI tooling, and more.

**Install:** `claude plugin marketplace add acaprino/figs`

## Plugin Index

| Plugin | Category | Description | Docs |
|--------|----------|-------------|------|
| [ai-tooling](plugins/ai-tooling.md) | ai-ml | Prompt engineering, brainstorming, planning, execution, Claude Agent SDK | 1 agent, 5 skills, 1 command |
| [figs-hooks](plugins/figs-hooks.md) | security | Session hooks -- startup logo, skill awareness, security gate, autocompact, brainstorm gate, review gate | hooks only |
| [app-analyzer](plugins/app-analyzer.md) | analysis | Android app analysis via ADB and webapp exploration via Playwright | 1 agent |
| [browser-extensions](plugins/browser-extensions.md) | development | Firefox WebExtension development -- Manifest V2/V3, browser.* APIs, AMO publishing | 1 agent, 1 skill |
| [business](plugins/business.md) | business | Legal advisory, privacy policies, GDPR/ePrivacy/CCPA compliance, contract review | 2 agents |
| [cc-usage](plugins/cc-usage.md) | utilities | Claude Code token usage, costs, billing blocks, and activity analysis | 1 skill, 1 command |
| [codebase-mapper](plugins/codebase-mapper.md) | documentation | Human-readable codebase guide generator with standalone doc creation, maintenance, and humanization | 10 agents, 1 skill, 4 commands |
| [csp](plugins/csp.md) | optimization | Constraint programming with Google OR-Tools CP-SAT solver | 1 agent |
| [deep-dive-analysis](plugins/deep-dive-analysis.md) | review | Systematic codebase analysis -- architecture, data flows, anti-patterns | 1 skill, 1 command |
| [digital-marketing](plugins/digital-marketing.md) | marketing | SEO audits, content strategy, brand naming, domain hunting | 2 agents, 2 skills, 3 commands |
| [frontend](plugins/frontend.md) | frontend | UI polish, UX design, CSS, layout, web consulting, shadcn/ui | 2 agents, 7 skills, 1 command |
| [docs](plugins/docs.md) | documentation | Craft top-tier README.md files with progressive disclosure, badges, quick start | 1 skill, 1 command |
| [git-worktrees](plugins/git-worktrees.md) | development-tools | Git worktree management -- create, pause, resume, merge parallel branches | 1 agent, 1 skill, 1 command |
| [humanize](plugins/humanize.md) | review | Rewrite code for readability -- naming, comments, structure | 1 agent, 1 command |
| [learning](plugins/learning.md) | productivity | Mind maps, Obsidian MarkMind export, interactive force-graph visualization | 3 skills, 1 command |
| [marketplace-ops](plugins/marketplace-ops.md) | utilities | Plugin management -- auditing, validation, upstream sync, scaffolding | 1 agent, 2 skills, 3 commands |
| [messaging](plugins/messaging.md) | infrastructure | RabbitMQ and AMQP -- queue design, clustering, high availability | 1 agent |
| [obsidian-development](plugins/obsidian-development.md) | development | Obsidian community plugin development with ReviewBot compliance | 3 skills |
| [playwright-skill](plugins/playwright-skill.md) | testing | Browser automation with Playwright -- testing, screenshots, form filling | 1 skill |
| [project-setup](plugins/project-setup.md) | utilities | CLAUDE.md creation and maintenance with ground truth validation | 1 agent, 2 commands |
| [prompt-improver](plugins/prompt-improver.md) | ai-ml | Intelligent prompt optimization -- enriches vague prompts with research-based clarifying questions | 1 skill, hooks |
| [python-development](plugins/python-development.md) | development | TDD, refactoring, profiling, async, uv, dead code, scaffolding | 1 agent, 8 skills, 2 commands |
| [rag-development](plugins/rag-development.md) | ai-ml | RAG system design and audit -- chunking, embeddings, Qdrant, advanced patterns | 2 agents, 1 skill, 1 command |
| [react-development](plugins/react-development.md) | frontend | React 19 performance, state management, bundle optimization, Vercel best practices | 1 agent, 1 skill, 1 command |
| [research](plugins/research.md) | research | Quick search (Sonnet) and deep multi-source research (Opus) | 2 agents |
| [senior-review](plugins/senior-review.md) | review | Multi-agent code review -- architecture, security, patterns, dead code | 3 agents, 4 commands |
| [stripe](plugins/stripe.md) | payments | Stripe payments, subscriptions, Connect, revenue optimization | 2 agents |
| [system-utils](plugins/system-utils.md) | utilities | File organization, duplicate detection, directory cleanup | 1 skill, 1 command |
| [tauri-development](plugins/tauri-development.md) | development | Tauri 2 desktop/mobile -- IPC optimization, Rust backend, cross-platform | 3 agents, 1 skill |
| [testing](plugins/testing.md) | testing | TDD methodology and behavior-driven test generation | 1 agent, 1 skill |
| [typescript-development](plugins/typescript-development.md) | development | TypeScript best practices and dead code detection via Knip | 2 skills |
| [workflows](plugins/workflows.md) | workflow | Cross-plugin pipelines -- feature e2e, frontend redesign, UI studio, reviews | 7 commands |
| [xterm](plugins/xterm.md) | frontend | xterm.js terminal emulator -- addons, PTY wiring, debugging, features | 1 skill, 2 commands |

## Quick Start Recipes

**Build a feature end-to-end:**
```
/feature-e2e "add user authentication"
```

**Review code before shipping:**
```
/code-review              # auto-detect scope
/full-review src/         # deep analysis + multi-agent review
```

**Optimize React performance:**
```
/review-react src/
```

**Map an unfamiliar codebase:**
```
/map-codebase ../other-project
```

**Track your usage and costs:**
```
/cc-usage 30d
```

See the [workflows plugin](plugins/workflows.md) for more pipeline commands with Mermaid diagrams.
