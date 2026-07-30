# Claude Code Daodan Documentation

The augmentation symbiote for Claude Code. Agents, skills, and commands for development workflows, code quality, AI tooling, and more.

**Install:** `claude plugin marketplace add acaprino/claude-code-daodan`

## Plugin Index

| Plugin | Category | Description | Docs |
|--------|----------|-------------|------|
| [abstraction-architect](plugins/abstraction-architect.md) | code-quality | Pure-architecture audits: missed unification, wrong abstractions, diff-anchored prior-art search | 1 agent, 1 skill, 1 command |
| [ai-tooling](plugins/ai-tooling.md) | ai-ml | Prompt engineering, Claude Agent SDK | 1 agent, 1 skill, 1 command |
| [app-analyzer](plugins/app-analyzer.md) | analysis | Android app analysis via ADB and webapp exploration via Playwright | 1 agent |
| [browser-extensions](plugins/browser-extensions.md) | development | Firefox WebExtension development: Manifest V2/V3, browser.* APIs, AMO publishing | 1 agent, 1 skill, 3 commands |
| [business](plugins/business.md) | business | Legal advisory, privacy policies, GDPR/ePrivacy/CCPA compliance, SaaS business planning | 3 agents, 1 skill |
| [clean-code](plugins/clean-code.md) | review | Rewrite source code for readability without changing behavior | 1 agent, 1 command |
| [codebase-cleanup](plugins/codebase-cleanup.md) | review | Multi-language dependency security audits, SOLID-driven refactoring, and prioritized tech-debt remediation roadmaps | 3 commands |
| [codebase-mapper](plugins/codebase-mapper.md) | documentation | Human-readable codebase guide generator with standalone doc creation, maintenance, and humanization | 10 agents, 1 skill, 5 commands |
| [csp](plugins/csp.md) | optimization | Constraint programming with Google OR-Tools CP-SAT solver | 1 agent |
| [codebase-xray](plugins/codebase-xray.md) | review | Systematic codebase analysis - architecture, data flows, anti-patterns - plus the shared interconnect mapper that review and documentation build on | 5 agents, 1 skill, 2 commands |
| [digital-marketing](plugins/digital-marketing.md) | marketing | SEO + AEO audits, GA4/GTM with Consent Mode v2, content strategy, brand naming, domain hunting, text humanization, customer review replies | 4 agents, 4 skills, 6 commands |
| [docker](plugins/docker.md) | development | Optimized multi-stage Dockerfiles for any language or framework | 1 skill |
| [docs](plugins/docs.md) | documentation | Craft top-tier README.md files with progressive disclosure, badges, quick start | 1 skill, 1 command |
| [grabber-development](plugins/grabber-development.md) | development | Expert Python web scraping: stealth browsers, TLS impersonation, anti-bot bypass, proxy architecture, AI extraction | 4 agents, 1 skill |
| [ibkr-trading](plugins/ibkr-trading.md) | algotrading | Interactive Brokers algotrading - TWS API, ib_async, order execution | 1 agent, 1 skill, 1 command |
| [kotlin-development](plugins/kotlin-development.md) | development | Idiomatic Kotlin - coroutines, Flow/StateFlow, Kotlin Multiplatform (KMP), Jetpack Compose, Ktor server, type-safe DSLs | 1 skill |
| [libgdx-development](plugins/libgdx-development.md) | development | libGDX cross-platform game dev - rendering pipeline, Scene2D + Ashley ECS, Box2D, AssetManager, Desktop/Android/iOS/HTML5 deploy, /libgdx-audit | 1 agent, 1 skill, 1 command |
| [learning](plugins/learning.md) | productivity | Mind maps, Obsidian MarkMind export, interactive force-graph visualization | 3 skills, 1 command |
| [marketplace-ops](plugins/marketplace-ops.md) | utilities | Plugin management - auditing, validation, upstream sync, scaffolding | 1 agent, 2 skills, 4 commands |
| [messaging](plugins/messaging.md) | infrastructure | RabbitMQ and AMQP - queue design, clustering, high availability | 1 agent |
| [mt5-trading](plugins/mt5-trading.md) | algotrading | MetaTrader 5 Python algotrading - API, polling events, order execution | 1 agent, 1 skill, 1 command |
| [obsidian-development](plugins/obsidian-development.md) | development | Obsidian community plugin development with ReviewBot compliance | 3 skills |
| [opentelemetry](plugins/opentelemetry.md) | development | OpenTelemetry Python: distributed tracing, context propagation, exporters, /otel-audit | 1 agent, 1 skill, 1 command |
| [platform-engineering](plugins/platform-engineering.md) | development | Cross-platform security, architecture, and performance rulebook with /platform-review | 1 agent, 1 skill, 1 command |
| [project-setup](plugins/project-setup.md) | utilities | CLAUDE.md creation and maintenance with ground truth validation | 1 agent, 2 commands |
| [prompt-improver](plugins/prompt-improver.md) | ai-ml | Intelligent prompt optimization - enriches vague prompts with research-based clarifying questions | 1 skill, hooks |
| [pwa-expert](plugins/pwa-expert.md) | frontend | Progressive Web Apps 2025-2026: manifest, service workers, Web Push, install flows, store distribution | 1 agent, 1 skill, 3 commands |
| [python-development](plugins/python-development.md) | development | TDD, refactoring, profiling, async, uv, dead code, Pydantic v2, scaffolding, /python-audit | 3 agents, 9 skills, 3 commands |
| [rag-development](plugins/rag-development.md) | ai-ml | RAG system design and audit - chunking, embeddings, Qdrant, advanced patterns | 2 agents, 1 skill, 1 command |
| [react-development](plugins/react-development.md) | frontend | React 19 performance, state management, bundle optimization, Vercel best practices | 1 agent, 1 skill, 1 command |
| [research](plugins/research.md) | research | Quick search (Sonnet) and deep multi-source research with shared web-search-techniques skill | 2 agents, 1 skill, 1 command |
| [senior-review](plugins/senior-review.md) | review | Multi-agent code review: architecture, security, patterns, distributed flows, logic integrity, API contracts, startup cycles, UI races, codebase hygiene | 8 agents, 2 skills, 3 commands |
| [stripe](plugins/stripe.md) | payments | Stripe payments, subscriptions, Connect, revenue optimization, webhook auditing | 3 agents, 1 skill, 1 command |
| [system-utils](plugins/system-utils.md) | utilities | File organization, duplicate detection, directory cleanup | 1 skill, 1 command |
| [tauri-development](plugins/tauri-development.md) | development | Tauri 2 desktop/mobile - IPC optimization, Rust backend, cross-platform | 3 agents, 1 skill |
| [testing](plugins/testing.md) | testing | TDD methodology, E2E testing patterns, behavior-driven test generation | 1 agent, 2 skills |
| [text-humanizer](plugins/text-humanizer.md) | writing | Removes AI writing traces from prose in any language via 24 documented patterns. Zero-dependency leaf, consumed by digital-marketing, codebase-mapper, business, and clean-code | 1 agent, 1 skill, 1 command |
| [typescript-development](plugins/typescript-development.md) | development | Hands-on TypeScript engineer agent, best practices, Knip dead code detection, and enterprise TypeScript mastery | 1 agent, 3 skills |
| [xterm](plugins/xterm.md) | frontend | xterm.js terminal emulator - addons, PTY wiring, debugging, features | 1 skill, 2 commands |

## Quick Start Recipes

**Review code before shipping (full multi-reviewer pipeline):**
```
/senior-review:team-review
```

**Quick review of specific changes:**
```
/code-review              # auto-detect scope
```

**Optimize React performance:**
```
/review-react src/
```

**Map an unfamiliar codebase:**
```
/map-codebase ../other-project
```

The four relocated multi-agent pipeline commands are documented in their host plugin docs: `/senior-review:team-review` in [senior-review](plugins/senior-review.md), `/codebase-xray:team-analyze` in [codebase-xray](plugins/codebase-xray.md), `/codebase-mapper:team-codebase-map` in [codebase-mapper](plugins/codebase-mapper.md), `/research:team-research` in [research](plugins/research.md). For generic team orchestration (`/agent-teams:team-feature`, `/agent-teams:team-debug`, `/agent-teams:team-spawn` presets), install the upstream `wshobson/agents` plugin.

## References

Cross-cutting knowledge bases that inform changes across multiple plugins.

- [Agent Teams best practices](references/agent-teams-best-practices.md) — when to spawn a team vs a subagent vs a single Claude, sizing, ownership, hooks, hard limits, and operational do's and don'ts. Source of truth when restructuring `senior-review`, `codebase-mapper`, `research`, `codebase-xray` (the team pipelines). Snapshot 2026-05-16.
