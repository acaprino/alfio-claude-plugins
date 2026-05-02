# ACP Documentation

Custom Claude Code plugin marketplace. Agents, skills, and commands for development workflows, code quality, AI tooling, and more.

**Install:** `claude plugin marketplace add acaprino/alfio-claude-plugins`

## Plugin Index

| Plugin | Category | Description | Docs |
|--------|----------|-------------|------|
| [ai-tooling](plugins/ai-tooling.md) | ai-ml | Prompt engineering, brainstorming, planning, execution, Claude Agent SDK | 1 agent, 5 skills, 1 command |
| [acp-hooks](plugins/acp-hooks.md) | security | Session hooks: skill awareness, security gate, autocompact, brainstorm gate, review gate, docs gate, team spawn gate | hooks only |
| [agent-teams](plugins/agent-teams.md) | development | Orchestrate multi-agent teams for parallel code review, debugging, codebase mapping, and coordinated feature development | 4 agents, 6 skills, 10 commands |
| [app-analyzer](plugins/app-analyzer.md) | analysis | Android app analysis via ADB and webapp exploration via Playwright | 1 agent |
| [browser-extensions](plugins/browser-extensions.md) | development | Firefox WebExtension development: Manifest V2/V3, browser.* APIs, AMO publishing | 1 agent, 1 skill, 3 commands |
| [business](plugins/business.md) | business | Legal advisory, privacy policies, GDPR/ePrivacy/CCPA compliance, SaaS business planning | 3 agents, 1 skill |
| [cc-usage](plugins/cc-usage.md) | utilities | Claude Code token usage, costs, billing blocks, and activity analysis | 1 skill, 1 command |
| [clean-code](plugins/clean-code.md) | review | Rewrite source code for readability without changing behavior | 1 agent, 1 command |
| [codebase-mapper](plugins/codebase-mapper.md) | documentation | Human-readable codebase guide generator with standalone doc creation, maintenance, and humanization | 10 agents, 1 skill, 4 commands |
| [csp](plugins/csp.md) | optimization | Constraint programming with Google OR-Tools CP-SAT solver | 1 agent |
| [deep-dive-analysis](plugins/deep-dive-analysis.md) | review | Systematic codebase analysis -- architecture, data flows, anti-patterns | 1 skill, 1 command |
| [digital-marketing](plugins/digital-marketing.md) | marketing | SEO + AEO audits, GA4/GTM with Consent Mode v2, content strategy, brand naming, domain hunting, text humanization, customer review replies | 5 agents, 5 skills, 7 commands |
| [docker](plugins/docker.md) | development | Optimized multi-stage Dockerfiles for any language or framework | 1 skill |
| [docs](plugins/docs.md) | documentation | Craft top-tier README.md files with progressive disclosure, badges, quick start | 1 skill, 1 command |
| [frontend](plugins/frontend.md) | frontend | UI polish, UX design, CSS, layout, web consulting, Radix/shadcn/daisyUI | 3 agents, 5 skills, 1 command |
| [git-worktrees](plugins/git-worktrees.md) | development-tools | Git worktree management -- create, pause, resume, merge parallel branches | 1 agent, 1 skill, 1 command |
| [grabber-development](plugins/grabber-development.md) | development | Expert Python web scraping: stealth browsers, TLS impersonation, anti-bot bypass, proxy architecture, AI extraction | 4 agents, 1 skill |
| [ibkr-trading](plugins/ibkr-trading.md) | algotrading | Interactive Brokers algotrading -- TWS API, ib_async, order execution | 1 agent, 1 skill, 1 command |
| [learning](plugins/learning.md) | productivity | Mind maps, Obsidian MarkMind export, interactive force-graph visualization | 3 skills, 1 command |
| [marketplace-ops](plugins/marketplace-ops.md) | utilities | Plugin management -- auditing, validation, upstream sync, scaffolding | 1 agent, 2 skills, 4 commands |
| [messaging](plugins/messaging.md) | infrastructure | RabbitMQ and AMQP -- queue design, clustering, high availability | 1 agent |
| [mt5-trading](plugins/mt5-trading.md) | algotrading | MetaTrader 5 Python algotrading -- API, polling events, order execution | 1 agent, 1 skill, 1 command |
| [obsidian-development](plugins/obsidian-development.md) | development | Obsidian community plugin development with ReviewBot compliance | 3 skills |
| [opentelemetry](plugins/opentelemetry.md) | development | OpenTelemetry Python: distributed tracing, context propagation, exporters, /otel-audit | 1 agent, 1 skill, 1 command |
| [platform-engineering](plugins/platform-engineering.md) | development | Cross-platform security, architecture, and performance rulebook with /platform-review | 1 agent, 1 skill, 1 command |
| [playwright-skill](plugins/playwright-skill.md) | testing | Browser automation with Playwright -- testing, screenshots, form filling | 1 skill |
| [project-setup](plugins/project-setup.md) | utilities | CLAUDE.md creation and maintenance with ground truth validation | 1 agent, 2 commands |
| [prompt-improver](plugins/prompt-improver.md) | ai-ml | Intelligent prompt optimization -- enriches vague prompts with research-based clarifying questions | 1 skill, hooks |
| [python-development](plugins/python-development.md) | development | TDD, refactoring, profiling, async, uv, dead code, Pydantic v2, scaffolding, /python-audit | 3 agents, 9 skills, 3 commands |
| [rag-development](plugins/rag-development.md) | ai-ml | RAG system design and audit -- chunking, embeddings, Qdrant, advanced patterns | 2 agents, 1 skill, 1 command |
| [react-development](plugins/react-development.md) | frontend | React 19 performance, state management, bundle optimization, Vercel best practices | 1 agent, 1 skill, 1 command |
| [research](plugins/research.md) | research | Quick search (Sonnet) and deep multi-source research (Opus) with shared web-search-techniques skill | 2 agents, 1 skill |
| [senior-review](plugins/senior-review.md) | review | Multi-agent code review: architecture, security, patterns, distributed flows, logic integrity, API contracts, startup cycles, UI races, codebase hygiene | 9 agents, 1 skill, 4 commands |
| [stripe](plugins/stripe.md) | payments | Stripe payments, subscriptions, Connect, revenue optimization, webhook auditing | 3 agents, 1 skill, 1 command |
| [system-utils](plugins/system-utils.md) | utilities | File organization, duplicate detection, directory cleanup | 1 skill, 1 command |
| [tauri-development](plugins/tauri-development.md) | development | Tauri 2 desktop/mobile -- IPC optimization, Rust backend, cross-platform | 3 agents, 1 skill |
| [testing](plugins/testing.md) | testing | TDD methodology, E2E testing patterns, behavior-driven test generation | 1 agent, 2 skills |
| [typescript-development](plugins/typescript-development.md) | development | Hands-on TypeScript engineer agent, best practices, Knip dead code detection, and enterprise TypeScript mastery | 1 agent, 3 skills |
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

See the [agent-teams plugin](plugins/agent-teams.md) for multi-agent pipeline commands with Mermaid diagrams.
