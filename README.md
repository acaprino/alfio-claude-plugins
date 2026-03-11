# Alfio Claude Plugins

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/marketplace-v1.56.0-green.svg)](.claude-plugin/marketplace.json)
[![Plugins](https://img.shields.io/badge/plugins-22-orange.svg)](#plugins-overview)

22 ready-to-install plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) -- Anthropic's official AI coding CLI. Specialized agents, skills, and commands for Python, code review, frontend, Tauri/Rust, AI tooling, Obsidian, and more -- so you spend less time prompting and more time shipping.

**22 plugins | 19 agents | 25 skills | 18 commands** -- install only what you need.

---

## Why Use These Plugins?

- **Specialized agents outperform generic prompts** -- each plugin encodes domain expertise that took months to develop
- **Multi-agent orchestration** -- code review runs architecture, security, and pattern analysis in parallel
- **Cross-plugin workflows** -- chain brainstorming, planning, implementation, review, and cleanup into single commands
- **Install only what you need** -- each plugin is independent with no runtime dependencies
- **Community-driven and open source** -- MIT licensed, contributions welcome

### Agents, Skills, and Commands

| Type | What it is | How to use |
|------|-----------|------------|
| **Agent** | A specialized AI persona with domain expertise | `Use the python-pro agent to implement rate limiting` |
| **Skill** | A knowledge module that enhances Claude's capabilities | Referenced automatically when relevant |
| **Command** | A slash command that triggers a specific workflow | `/code-review`, `/python-scaffold`, `/feature-e2e` |

---

## Table of Contents

- [Installation](#installation)
- [Plugins Overview](#plugins-overview)
- [Quick Start Workflows](#quick-start-workflows)
- **Development** -- [Python](#python-development-plugin) | [TypeScript](#typescript-development-plugin) | [Tauri/Rust](#tauri-development-plugin) | [Obsidian](#obsidian-development-plugin) | [Browser Extensions](#browser-extensions-plugin)
- **Frontend** -- [Frontend](#frontend-plugin) | [Frontend Design](#frontend-design-plugin)
- **Review & Quality** -- [Code Review](#code-review-plugin) | [Humanize](#humanize-plugin) | [Deep Dive Analysis](#deep-dive-analysis-plugin) | [Code Documentation](#code-documentation-plugin)
- **AI & Planning** -- [AI Tooling](#ai-tooling-plugin) | [Research](#research-plugin) | [Project Setup](#project-setup-plugin)
- **Infrastructure** -- [Messaging](#messaging-plugin) | [CSP](#csp-plugin) | [Stripe](#stripe-plugin) | [Business](#business-plugin)
- **Tools & Workflows** -- [Utilities](#utilities-plugin) | [Workflows](#workflows-plugin) | [App Explorer](#app-explorer-plugin) | [Mobile Development](#mobile-development-plugin) | [Digital Marketing](#digital-marketing-plugin)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

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
# ... see Plugins Overview for all 22 available plugins
```

### From Local Path (Development)

Use `--plugin-dir` to load plugins for current session:
```bash
claude --plugin-dir /path/to/alfio-claude-plugins
```

### Verify Installation

```bash
# List marketplaces
claude plugin marketplace list

# List installed plugins
claude plugin list
```

---

## Plugins Overview

| Plugin | Description | Agents | Skills | Commands |
|--------|-------------|:------:|:------:|:--------:|
| [**python-development**](#python-development-plugin) | Modern Python development ecosystem with testing, packaging, async patterns, and code refactoring tools | 1 | 8 | 2 |
| [**humanize**](#humanize-plugin) | Make AI-generated code look human-written -- fixes names, removes boilerplate | 1 | - | 1 |
| [**deep-dive-analysis**](#deep-dive-analysis-plugin) | Understand any codebase in minutes with 7-phase systematic analysis | - | 1 | 1 |
| [**code-review**](#code-review-plugin) | Catch bugs before they ship -- 3 agents review architecture, security, and patterns in parallel | 3 | - | 3 |
| [**tauri-development**](#tauri-development-plugin) | Build cross-platform desktop and mobile apps with Tauri 2 and Rust | 2 | 1 | - |
| [**frontend**](#frontend-plugin) | Optimize React performance, polish UI, design layouts, and master modern CSS | 5 | 2 | 1 |
| [**frontend-design**](#frontend-design-plugin) | Design distinctive interfaces from scratch, avoiding generic AI aesthetics | - | 1 | - |
| [**ai-tooling**](#ai-tooling-plugin) | Brainstorm, plan, and execute with structured AI-assisted workflows | 1 | 3 | 1 |
| [**stripe**](#stripe-plugin) | Integrate Stripe payments without reading 500 pages of docs | - | 2 | - |
| [**utilities**](#utilities-plugin) | Clean up messy folders, find duplicates, and remove dead code | - | 1 | 2 |
| [**business**](#business-plugin) | Navigate tech law, compliance, contracts, and risk management | - | 1 | - |
| [**project-setup**](#project-setup-plugin) | Create and maintain accurate CLAUDE.md files with ground truth verification | 1 | - | 2 |
| [**code-documentation**](#code-documentation-plugin) | Generate accurate docs by analyzing your code first, not guessing | 1 | - | 2 |
| [**csp**](#csp-plugin) | Solve scheduling, routing, and assignment problems with OR-Tools CP-SAT | 1 | - | - |
| [**digital-marketing**](#digital-marketing-plugin) | Run SEO audits, content strategy, and conversion optimization | 2 | - | 2 |
| [**messaging**](#messaging-plugin) | Design and optimize RabbitMQ messaging with expert AMQP patterns | 1 | - | - |
| [**research**](#research-plugin) | Find precise answers fast with advanced multi-source search strategies | 1 | - | - |
| [**mobile-development**](#mobile-development-plugin) | Analyze competitor Android apps via ADB with automated screenshots | - | 1 | - |
| [**typescript-development**](#typescript-development-plugin) | Write clean TypeScript with coding standards and Knip dead code detection | - | 2 | - |
| [**workflows**](#workflows-plugin) | Run entire dev workflows with one command -- brainstorm to review to cleanup | - | - | 4 |
| [**app-explorer**](#app-explorer-plugin) | Map any webapp's screens and navigation with Playwright crawling | - | 1 | - |
| [**browser-extensions**](#browser-extensions-plugin) | Build Firefox extensions with expert Manifest V2/V3 and AMO publishing guidance | - | 1 | - |
| [**obsidian-development**](#obsidian-development-plugin) | Pass ObsidianReviewBot on first submission with compliant scaffolding and checks | - | 3 | - |

> **frontend** vs **frontend-design**: Use `frontend` for React/CSS optimization and hands-on UI work. Use `frontend-design` for designing new interfaces from scratch with creative flair.

---

## Quick Start Workflows

### Feature End-to-End (`/feature-e2e`)

The most complete pipeline -- takes a feature idea from brainstorming through implementation to code review in a single command.

```
/feature-e2e "add user authentication"
```

```mermaid
graph TD
    A["/feature-e2e 'add auth'"] --> B["Phase 1: Brainstorm Design"]
    B --> |"interactive Q&A"| C{{"Checkpoint 1: Approve design?"}}
    C --> D["Phase 2: Write Plan"]
    D --> |"TDD task breakdown"| E{{"Checkpoint 2: Approve plan?"}}
    E --> F["Phase 3: Execute Plan"]
    F --> |"batches of 3 tasks"| G{{"Checkpoint 3: Approve code?"}}
    G --> H["Phase 4: Code Review"]
    H --> H1["Architecture Agent"]
    H --> H2["Security Agent"]
    H --> H3["Pattern Scoring Agent"]
    H1 & H2 & H3 --> I{{"Checkpoint 4: Review findings"}}
    I --> J["Phase 5: Humanize Code"]
    J --> K["Done"]

    style H1 fill:#4a9eff,color:#fff
    style H2 fill:#4a9eff,color:#fff
    style H3 fill:#4a9eff,color:#fff
    style C fill:#f5a623,color:#fff
    style E fill:#f5a623,color:#fff
    style G fill:#f5a623,color:#fff
    style I fill:#f5a623,color:#fff
```

---

### Code Review (`/code-review`)

Auto-detects scope (uncommitted changes, commits, or PR) and fires 4 agents in parallel.

```
/code-review              # auto-detect scope
/code-review 42           # review PR #42
/code-review --auto-comment  # post findings as PR comments
```

```mermaid
graph TD
    A["/code-review"] --> B{"Auto-detect scope"}
    B --> |"uncommitted"| C["Gather diff + context"]
    B --> |"PR number"| C
    B --> |"branch diff"| C
    C --> D["Launch 4 agents in parallel"]
    D --> D1["Architecture Review"]
    D --> D2["Security Audit"]
    D --> D3["Pattern Scoring"]
    D --> D4["Dead Code Detection"]
    D1 & D2 & D3 & D4 --> E["Consolidate findings"]
    E --> F["Confidence-scored review table"]
    F --> |"--auto-comment"| G["Post to PR"]
    F --> H["Output to terminal"]

    style D1 fill:#4a9eff,color:#fff
    style D2 fill:#4a9eff,color:#fff
    style D3 fill:#4a9eff,color:#fff
    style D4 fill:#4a9eff,color:#fff
```

---

### Full Review (`/full-review`)

Deep 6-phase review with progressive parallelization -- each wave builds on prior findings.

```
/full-review src/ --security-focus
```

```mermaid
graph TD
    A["/full-review src/"] --> B["Phase 1: Architecture Review"]
    B --> C["Phase 2: Security & Performance"]
    C --> C1["Security Agent"]
    C --> C2["Performance Agent"]
    C1 & C2 --> D{{"Checkpoint: Approve?"}}
    D --> E["Phase 3: Testing & Docs"]
    E --> E1["Test Coverage Agent"]
    E --> E2["API & Docs Agent"]
    E1 & E2 --> F["Phase 4: Best Practices"]
    F --> F1["Framework Agent"]
    F --> F2["CI/CD Agent"]
    F --> F3["Dead Code Agent"]
    F1 & F2 & F3 --> G["Phase 5: Quality Scoring"]
    G --> |"reads all prior phases"| H["Phase 6: Consolidated Report"]

    style C1 fill:#4a9eff,color:#fff
    style C2 fill:#4a9eff,color:#fff
    style E1 fill:#4a9eff,color:#fff
    style E2 fill:#4a9eff,color:#fff
    style F1 fill:#4a9eff,color:#fff
    style F2 fill:#4a9eff,color:#fff
    style F3 fill:#4a9eff,color:#fff
    style D fill:#f5a623,color:#fff
```

---

### AI-Assisted Planning

Three skills that chain together -- each one feeds into the next with hard gates preventing premature implementation.

```mermaid
graph LR
    A["Brainstorming"] --> |"design doc"| B["Writing Plans"]
    B --> |"task plan"| C["Executing Plans"]

    A1["Explore context"] --> A2["Clarifying Q&A"]
    A2 --> A3["2-3 approaches"]
    A3 --> A4["Write design doc"]

    B1["Read design"] --> B2["Break into tasks"]
    B2 --> B3["5 steps per task: test-first"]
    B3 --> B4["Save plan .md"]

    C1["Load plan"] --> C2["Execute batch of 3"]
    C2 --> C3["Report + wait feedback"]
    C3 --> |"next batch"| C2

    subgraph "1. brainstorming skill"
        A1 --> A2 --> A3 --> A4
    end
    subgraph "2. writing-plans skill"
        B1 --> B2 --> B3 --> B4
    end
    subgraph "3. executing-plans skill"
        C1 --> C2 --> C3
    end

    style A fill:#7c3aed,color:#fff
    style B fill:#7c3aed,color:#fff
    style C fill:#7c3aed,color:#fff
```

---

### Frontend Redesign (`/frontend-redesign`)

Full redesign pipeline from UX audit to polished implementation with parallel final audit.

```
/frontend-redesign src/ --framework react
```

```mermaid
graph TD
    A["/frontend-redesign"] --> B["Phase 1: UX Audit"]
    B --> C["Phase 2: Layout & Grid"]
    C --> D{{"Checkpoint 1: Approve designs?"}}
    D --> E["Phase 3: Implement Designs"]
    E --> F["Phase 4: React Performance"]
    F --> G["Phase 5: UI Polish"]
    G --> H{{"Checkpoint 2: Final approval?"}}
    H --> I["Phase 6: Design Audit"]
    I --> I1["UX Patterns Agent"]
    I --> I2["Layout System Agent"]
    I --> I3["CSS & Visual Agent"]
    I1 & I2 & I3 --> J["Consolidated Report"]

    style I1 fill:#4a9eff,color:#fff
    style I2 fill:#4a9eff,color:#fff
    style I3 fill:#4a9eff,color:#fff
    style D fill:#f5a623,color:#fff
    style H fill:#f5a623,color:#fff
```

---

### Tauri Pipeline (`/tauri-pipeline`)

Desktop app optimization across Rust backend, Tauri IPC, and React frontend layers.

```
/tauri-pipeline             # full pipeline
/tauri-pipeline --rust-only  # backend only
```

```mermaid
graph TD
    A["/tauri-pipeline"] --> B["Phase 1: Rust Backend Review"]
    B --> C["Phase 2: Tauri IPC Optimization"]
    C --> D{{"Checkpoint: Approve backend?"}}
    D --> E["Phase 3: React Performance"]
    E --> F["Phase 4: Layout Composition"]
    F --> G["Phase 5: UI Polish"]
    G --> H["Phase 6: Consolidated Report"]

    style D fill:#f5a623,color:#fff
```

---

### Mobile Intelligence (`/mobile-intel`)

Competitive analysis pipeline -- analyze a competitor Android app and scaffold your own.

```
/mobile-intel com.competitor.app
```

```mermaid
graph TD
    A["/mobile-intel"] --> B["Phase 1: Competitor Analysis"]
    B --> |"ADB screenshots"| C{{"Checkpoint 1: Review analysis?"}}
    C --> D["Phase 2: Brainstorm Features"]
    D --> |"interactive Q&A"| E{{"Checkpoint 2: Approve features?"}}
    E --> F["Phase 3: UX Design"]
    F --> G["Phase 4: Implementation Plan"]
    G --> H{{"Checkpoint 3: Approve plan?"}}
    H --> I["Phase 5: Scaffold Tauri 2 App"]

    style C fill:#f5a623,color:#fff
    style E fill:#f5a623,color:#fff
    style H fill:#f5a623,color:#fff
```

---

### More Workflows

<details>
<summary>Python Development, Legacy Modernization, Tauri Optimization, CLAUDE.md, CSP</summary>

#### Python Development
```
1. /python-scaffold FastAPI microservice
2. Implement features with python-pro agent
3. /python-refactor on complex modules
4. Use python-tdd for test coverage
```

#### Legacy Code Modernization
```
1. /deep-dive-analysis to understand codebase
2. /python-refactor on legacy modules
3. Use python-tdd to add test coverage
4. /humanize to clean up naming and comments
```

#### Tauri App Optimization
```
1. Use tauri-optimizer for IPC and Rust backend
2. Use react-performance-optimizer for React frontend
3. Use ui-layout-designer for page composition
4. Use ui-polisher for animations and polish
```

#### CLAUDE.md Maintenance
```
1. /maintain-claude-md for quarterly maintenance
2. Review audit findings
3. Choose: audit-only or apply improvements
4. Or /create-claude-md to start fresh
```

#### Optimization & Scheduling with CSP
```
1. Use or-tools-expert agent for constraint programming
2. Model problem with variables, domains, and constraints
3. Enable parallelism and performance optimizations
4. Test on small instances before scaling up
```

**Example problems:** Employee shift scheduling, job shop scheduling, bin packing, vehicle routing, assignment problems with cost minimization.

</details>

### Diagram Legend

| Symbol | Meaning |
|--------|---------|
| Blue boxes | Parallel agents (run simultaneously) |
| Orange diamonds | Checkpoints (require user approval to proceed) |
| Purple boxes | Skills (knowledge modules with structured workflows) |

---

## Python Development Plugin

> Stop wrestling with boilerplate. Get production-ready Python projects scaffolded in seconds, with built-in refactoring workflows and testing patterns that enforce best practices.

### Agents

#### `python-pro`

Expert Python developer mastering Python 3.12+ features, modern tooling (uv, ruff), and production-ready practices.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Modern Python patterns, async programming, performance optimization, type hints |

**Invocation:**
```
Use the python-pro agent to [implement/optimize/review] [feature]
```

**Expertise:**
- Python 3.12+ features (pattern matching, type hints, dataclasses)
- Modern tooling: uv, ruff, mypy, pytest
- Async/await patterns with asyncio
- Performance profiling and optimization
- FastAPI, Django, Pydantic integration

---

### Skills

#### `python-refactor`

Systematic 4-phase refactoring workflow transforming complex code into clean, maintainable code.

| | |
|---|---|
| **Invoke** | `/python-refactor` or skill reference |
| **Use for** | Legacy modernization, complexity reduction, OOP transformation |

**4-Phase Workflow:**
1. **Analysis** - Measure complexity metrics, identify issues
2. **Planning** - Prioritize issues, select refactoring patterns
3. **Execution** - Apply patterns incrementally with test validation
4. **Validation** - Verify tests pass, metrics improved, no regression

**Key Features:**
- 7 executable Python scripts for metrics
- Cognitive complexity calculation
- flake8 integration with 16 curated plugins
- OOP transformation patterns
- Regression prevention checklists

**Synergy:** Works with `python-tdd` and `python-performance-optimization`

---

#### `python-tdd`

Comprehensive testing strategies with pytest, fixtures, mocking, and TDD.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Unit tests, integration tests, fixtures, mocking, coverage |

**Patterns included:**
- pytest fixtures (function, module, session scoped)
- Parameterized tests
- Mocking with unittest.mock
- Async testing with pytest-asyncio
- Property-based testing with Hypothesis
- Database testing patterns

---

#### `python-performance-optimization`

Profiling and optimization techniques for Python applications.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Profiling, bottleneck identification, memory optimization |

**Tools covered:**
- cProfile and py-spy for CPU profiling
- memory_profiler for memory analysis
- pytest-benchmark for benchmarking
- Line profiling and flame graphs

---

#### `async-python-patterns`

Async/await patterns for high-performance concurrent applications.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | asyncio, concurrent I/O, WebSockets, background tasks |

**Patterns included:**
- Event loop fundamentals
- gather(), create_task(), wait_for()
- Producer-consumer with asyncio.Queue
- Semaphores for rate limiting
- Async context managers and iterators

---

#### `python-packaging`

Creating and distributing Python packages with modern standards.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Library creation, PyPI publishing, CLI tools |

**Topics covered:**
- pyproject.toml configuration
- Source layout (src/) best practices
- Entry points and CLI tools
- Publishing to PyPI/TestPyPI
- Dynamic versioning with setuptools-scm

---

#### `uv-package-manager`

Fast Python dependency management with uv (10-100x faster than pip).

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dependency management, virtual environments, lockfiles |

**Key commands:**
| Task | Command |
|------|---------|
| Create project | `uv init my-project` |
| Add dependency | `uv add requests` |
| Sync from lock | `uv sync --frozen` |
| Run script | `uv run python app.py` |

---

#### `python-comments`

Write and audit Python code comments using antirez's 9-type taxonomy.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Comment quality review, docstring improvements, documentation audits |

**Two modes:**
- **Write** - Add/improve comments in code using systematic classification
- **Audit** - Classify and assess existing comments with structured report

**Features:**
- 9-type comment taxonomy (Function, Design, Why, Teacher, Checklist, Guide, Trivial, Debt, Backup)
- Python-specific mapping (docstrings, inline comments, type hints)
- Quality scoring and improvement recommendations

---

### Commands

#### `/python-scaffold`

Scaffold production-ready Python projects with modern tooling. Presents plan and confirms before writing files.

```
/python-scaffold FastAPI REST API for user management
```

**Project types:** FastAPI, Django, Library, CLI, Generic

**Generates:** Directory structure, pyproject.toml, pytest config, Makefile, .env.example, .gitignore. Verifies with `uv sync` + `pytest` after scaffolding.

---

#### `/python-refactor`

Metrics-driven 4-phase refactoring with checkpoint approval before execution and persistent output files.

```
/python-refactor src/legacy_module.py
```

**Phases:** Analysis -> Planning -> (Checkpoint) -> Execution -> Validation

**Output:** `.python-refactor/` directory with analysis, plan, execution log, and validation report.

---

## Humanize Plugin

> Make AI-generated code indistinguishable from human-written code. Fixes vague names, removes boilerplate comments, and adds meaningful documentation -- with mandatory test validation.

### Agents

#### `humanize`

Rewrites source code to make it more readable and human-friendly without changing behavior.

| | |
|---|---|
| **Model** | `sonnet` |
| **Use for** | Code cleanup, naming improvements, removing AI-generated boilerplate |

**Invocation:**
```
Use the humanize agent to clean up [file/module]
```

**What it does:**
- Renames vague variables and parameters to domain-meaningful names
- Removes paraphrase comments and empty boilerplate docstrings
- Adds brief why-comments for non-obvious business logic

**What it does NOT do:**
- Does not reorder code, extract functions, or change control flow
- Does not remove error handling, validations, or imports
- Does not modify test files (unless renaming symbols it renamed in source)

---

### Commands

#### `/humanize`

Quick command to humanize source files.

```
/humanize src/utils.py
```

**Examples:**
| Command | Action |
|---------|--------|
| `/humanize src/utils.py` | Humanize a specific file |
| `/humanize src/` | Humanize all source files in a directory |
| `/humanize src/api/ --dry-run` | Preview changes without modifying files |

---

## Deep Dive Analysis Plugin

> Understand any codebase in minutes. Seven-phase analysis maps structure, traces flows, identifies risks, and documents the WHY behind the code -- not just what it does.

### Skills

#### `deep-dive-analysis`

AI-powered systematic codebase analysis combining structure extraction with semantic understanding.

| | |
|---|---|
| **Invoke** | `/deep-dive-analysis` |
| **Use for** | Codebase understanding, architecture mapping, onboarding |

**Capabilities:**
- Extract code structure (classes, functions, imports)
- Map internal/external dependencies
- Recognize architectural patterns
- Identify anti-patterns and red flags
- Trace data and control flows

---

### Commands

#### `/deep-dive-analysis`

7-phase systematic codebase analysis with state management, output files, and phased execution: structure -> interfaces -> flows -> semantics -> risks -> documentation -> report.

```
/deep-dive-analysis src/core/ --critical
```

**Output:** `.deep-dive/` directory with 7 phase files and a final consolidated report.

---

## Code Review Plugin

> Catch bugs before they ship. Three specialized agents review architecture, security, and code patterns in parallel -- like having a senior architect, security auditor, and quality engineer on every PR.

### Agents

#### `architect-review`

Master software architect specializing in modern architecture patterns, clean architecture, microservices, event-driven systems, and DDD.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Architecture integrity, scalability review, design pattern assessment |

**Invocation:**
```
Use the architect-review agent to review [system/design]
```

---

#### `security-auditor`

Expert security auditor specializing in DevSecOps, comprehensive cybersecurity, and compliance frameworks.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Security audits, DevSecOps, compliance (GDPR/HIPAA/SOC2), threat modeling |

**Invocation:**
```
Use the security-auditor agent to audit [system/codebase]
```

**Expertise:**
- Vulnerability assessment and threat modeling
- OAuth2/OIDC secure authentication
- OWASP standards and cloud security
- Security automation and incident response

---

#### `pattern-quality-scorer`

Pattern consistency analyzer and quantitative code quality scorer.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Pattern deviation detection, anti-pattern checklists, quality scoring |

**Invocation:**
```
Use the pattern-quality-scorer agent to analyze [codebase]
```

**Methodology:**
- 16-item anti-pattern checklist
- 6 mental models (security engineer, performance engineer, team lead, systems architect, SRE, pattern detective)
- 1-10 Code Quality Score per category

---

### Commands

#### `/full-review`

Orchestrate comprehensive multi-dimensional code review using all specialized review agents.

```
/full-review src/features/auth/ --security-focus
```

**Options:**
| Flag | Effect |
|------|--------|
| `--security-focus` | Prioritize security analysis |
| `--performance-critical` | Deep performance review |
| `--strict-mode` | Strictest quality standards |
| `--framework react\|django` | Framework-specific checks |

---

#### `/code-review`

Unified code review -- auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. Runs architecture, security, and pattern analysis agents in parallel with confidence scoring.

```
/code-review                    # auto-detect: uncommitted changes or branch diff
/code-review 42                 # review PR #42
/code-review --commits 3        # review last 3 commits
/code-review --branch feature   # review branch diff
/code-review --auto-comment     # post findings as PR comments
```

---

#### `/pr-enhance`

Analyze current branch changes, generate comprehensive PR description with risk assessment and review checklist, and optionally create the PR via `gh`.

```
/pr-enhance --create
```

---

## Tauri Development Plugin

> Build fast, secure cross-platform apps. Expert Rust engineering plus Tauri 2 optimization for desktop and mobile -- with concrete performance targets for startup time, memory, and IPC latency.

### Agents

#### `tauri-optimizer`

Expert in Tauri v2 + React optimization for trading and high-frequency data scenarios.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | IPC optimization, state management, memory leaks, WebView tuning |

**Invocation:**
```
Use the tauri-optimizer agent to analyze [project/file]
```

**Performance targets:**
| Metric | Target | Critical |
|--------|--------|----------|
| Startup time | < 1s | < 2s |
| Memory baseline | < 100MB | < 150MB |
| IPC latency | < 0.5ms | < 1ms |
| Frame rate | 60 FPS | > 30 FPS |

---

#### `rust-engineer`

Expert Rust developer specializing in systems programming and memory safety.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Ownership patterns, async tokio, FFI, performance optimization |

**Invocation:**
```
Use the rust-engineer agent to implement [feature]
```

**Checklist enforced:**
- Zero unsafe code outside core abstractions
- clippy::pedantic compliance
- Complete documentation with examples
- MIRI verification for unsafe blocks

---

### Skills

#### `tauri2-mobile`

Expert guidance for Tauri 2 mobile app development (Android/iOS).

| | |
|---|---|
| **Invoke** | `/tauri2-mobile` |
| **Use for** | Mobile setup, plugins, testing, store deployment |

**Quick commands:**
| Task | Command |
|------|---------|
| Init Android | `npm run tauri android init` |
| Dev Android | `npm run tauri android dev` |
| Build APK | `npm run tauri android build --apk` |
| Build iOS | `npm run tauri ios build` |

---

## Frontend Plugin

> Five specialized agents for every layer of frontend work -- React performance, UI polish, UX design, layout composition, and modern CSS. Use `frontend` for hands-on optimization; use [`frontend-design`](#frontend-design-plugin) for designing new interfaces from scratch.

### Agents

#### `react-performance-optimizer`

Expert in React 19 performance including React Compiler and Server Components.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Bundle analysis, re-render optimization, virtualization |

**Invocation:**
```
Use the react-performance-optimizer agent to analyze [component/app]
```

**Performance targets:**
| Metric | Web | Desktop |
|--------|-----|---------|
| Bundle (initial) | < 200KB | < 3MB |
| Frame rate | 60 FPS | 60 FPS |
| Render time | < 16ms | < 16ms |

---

#### `ui-polisher`

Senior UI polish specialist and motion designer for premium interfaces.

| | |
|---|---|
| **Model** | `sonnet` |
| **Use for** | Micro-interactions, animations, transitions, loading states |

**Invocation:**
```
Use the ui-polisher agent to improve [component/page]
```

---

#### `ui-ux-designer`

Elite UI/UX designer for beautiful, accessible interfaces and design systems.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Design systems, user flows, wireframes, accessibility |

**Invocation:**
```
Use the ui-ux-designer agent to design [feature/system]
```

---

#### `ui-layout-designer`

Spatial composition specialist for grid systems, responsive breakpoint strategy, and CSS Grid/Flexbox developer handoff.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Page structure, above-the-fold layouts, responsive strategy, layout-to-CSS specs |

**Invocation:**
```
Use the ui-layout-designer agent to design [layout/page]
```

**Philosophy:** Structure first. Proportions second. Chrome last. Uses 8px spatial system and content-priority-driven layout.

---

#### `css-master`

Expert CSS developer for hands-on CSS work -- refactoring styles, migrating SASS/preprocessors to native CSS, setting up CSS architecture, adopting modern CSS features.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | CSS refactoring, SASS-to-native migration, CSS architecture, Container Queries, View Transitions, Scroll-driven animations |

**Invocation:**
```
Use the css-master agent to [refactor/migrate/architect] [styles]
```

---

### Skills

#### `css-master`

Comprehensive CSS reference covering modern CSS features, architecture methodologies, and production patterns.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Container Queries, View Transitions, Masonry, Scroll-driven animations, legacy CSS refactoring |

**Source:** Ported from [paulirish/dotfiles](https://github.com/paulirish/dotfiles).

---

### Commands

#### `/review-design`

Unified frontend design review -- auto-detects scope: diff mode for changed frontend files, or full audit for entire frontend. UX patterns, CSS architecture, and React performance.

```
/review-design src/ --framework react     # full audit
/review-design --full                     # explicit full audit
/review-design                            # auto-detect: diff mode if changes exist
```

**Output:** `.design-review/report.md` -- actionable checklist with scores, grouped by category (UX, Layout, CSS).

---

## Frontend Design Plugin

> Design interfaces that look hand-crafted, not AI-generated. Creative, polished web components and pages that avoid the generic aesthetic of typical AI output.

### Skills

#### `frontend-design`

Create polished web components, pages, and applications with creative design that avoids generic AI output.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Web components, landing pages, UI design, production-grade interfaces |

**Source:** Ported from [anthropics/claude-code](https://github.com/anthropics/claude-code) frontend-design plugin.

---

## AI Tooling Plugin

> Think before you build. Structured brainstorming, planning, and execution workflows that prevent wasted effort and keep complex projects on track.

### Agents

#### `prompt-engineer`

Expert prompt engineer for designing and optimizing LLM prompts.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Prompt design, token optimization, A/B testing, production systems |

**Invocation:**
```
Use the prompt-engineer agent to optimize [prompt/system]
```

**Prompt patterns:**
- Zero-shot / Few-shot prompting
- Chain-of-thought / Tree-of-thought
- ReAct pattern
- Constitutional AI
- Role-based prompting

---

### Skills

#### `brainstorming`

Explore user intent, requirements, and design before any creative or implementation work.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Feature design, requirements exploration, creative ideation |

**Source:** Ported from [obra/superpowers](https://github.com/obra/superpowers).

---

#### `writing-plans`

Create structured implementation plans from specs or requirements before touching code.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Multi-step task planning, spec-to-plan conversion |

**Source:** Ported from [obra/superpowers](https://github.com/obra/superpowers).

---

#### `executing-plans`

Execute written implementation plans in a separate session with review checkpoints.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Plan execution, checkpoint reviews, staged implementation |

**Source:** Ported from [obra/superpowers](https://github.com/obra/superpowers).

---

### Commands

#### `/prompt-optimize`

Analyze, score, and optimize prompts for LLMs -- evaluates clarity, specificity, structure, token efficiency, robustness, and output control. Shows before/after comparison.

```
/prompt-optimize "You are a helpful assistant that..." --optimize-for tokens
```

**Phases:** Analyze (6-dimension scorecard) -> Optimize -> Compare (before/after scores + token count)

---

## Stripe Plugin

> Integrate Stripe without reading 500 pages of docs. Covers payments, subscriptions, Connect marketplaces, billing, webhooks, and revenue optimization with ready-to-use patterns.

### Skills

#### `stripe-agent`

Complete Stripe API integration covering payments, subscriptions, Connect marketplaces, and compliance.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Payment processing, subscriptions, marketplaces, billing, webhooks |

**Core capabilities:**
- **Payments** - Payment intents, checkout sessions, payment links
- **Subscriptions** - Recurring billing, metered usage, tiered pricing
- **Connect** - Marketplace payments, platform fees, seller onboarding
- **Billing** - Invoices, customer portal, tax calculation
- **Webhooks** - Event handling, subscription lifecycle
- **Security** - 3D Secure, SCA compliance, fraud prevention (Radar)
- **Disputes** - Chargeback handling, evidence submission

**Quick reference:**
| Task | Method |
|------|--------|
| Create customer | `stripe.Customer.create()` |
| Checkout session | `stripe.checkout.Session.create()` |
| Subscription | `stripe.Subscription.create()` |
| Payment link | `stripe.PaymentLink.create()` |
| Report usage | `stripe.SubscriptionItem.create_usage_record()` |
| Connect account | `stripe.Account.create(type="express")` |

**Prerequisites:**
```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
pip install stripe
```

---

#### `revenue-optimizer`

Monetization expert that analyzes codebases to discover features, calculate service costs, model usage patterns, and create data-driven pricing strategies with revenue projections.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Feature cost analysis, pricing strategy, usage modeling, revenue projections, tier design |

**5-Phase Workflow:**
1. **Discover** - Scan codebase for features, services, and integrations
2. **Cost Analysis** - Calculate per-user and per-feature costs
3. **Design** - Create pricing tiers based on value + cost data
4. **Implement** - Build payment integration and checkout flows
5. **Optimize** - Add conversion optimization and revenue tracking

**Key Metrics Calculated:**
| Metric | Formula |
|--------|---------|
| ARPU | (Free×$0 + Pro×$X + Biz×$Y) / Total Users |
| LTV | (ARPU × Margin) / Monthly Churn |
| Break-even | Fixed Costs / (ARPU - Variable Cost) |
| Optimal Price | (Cost Floor × 0.3) + (Value Ceiling × 0.7) |

---

## Utilities Plugin

> Tame messy folders and bloated codebases. Organizes files, finds duplicates, removes dead code, and cleans up directories with approval before any changes.

### Skills

#### `file-organizer`

Personal organization assistant for maintaining clean, logical file structures.

| | |
|---|---|
| **Invoke** | Skill reference or `/organize-files` |
| **Use for** | Messy folders, duplicates, old files, project restructuring |

**Capabilities:**
- **Analyze** - Review folder structure and file types
- **Find Duplicates** - Identify duplicate files by hash
- **Suggest Structure** - Propose logical folder organization
- **Automate** - Move, rename, organize with approval
- **Cleanup** - Identify old/unused files for archiving

---

### Commands

#### `/organize-files`

Quick command to organize files and directories.

```
/organize-files Downloads
```

**Examples:**
| Command | Action |
|---------|--------|
| `/organize-files Downloads` | Organize Downloads by type |
| `/organize-files ~/Documents find duplicates` | Find duplicate files |
| `/organize-files ~/Projects archive old` | Archive inactive projects |
| `/organize-files . cleanup` | Clean up current directory |

---

#### `/cleanup-dead-code`

Find and remove dead code -- auto-detects language: Knip for TypeScript/JavaScript, vulture + ruff for Python.

| | |
|---|---|
| **Invoke** | `/cleanup-dead-code [path] [--dry-run] [--dependencies-only] [--exports-only] [--production]` |
| **Use for** | Dead code removal, dependency cleanup, export pruning, unused import removal |

---

## Business Plugin

> Navigate tech law without a lawyer on retainer. Contract review, GDPR/CCPA compliance, IP protection, and risk assessment tailored to software businesses.

### Skills

#### `legal-advisor`

Expert legal advisor specializing in technology law, compliance, and risk mitigation.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Contract review, compliance, IP protection, privacy policies, risk assessment |

**Core capabilities:**
- **Contract Management** - Review, negotiate, draft, and manage contracts
- **Privacy & Data Protection** - GDPR, CCPA, data processing agreements
- **Intellectual Property** - Patents, trademarks, copyrights, trade secrets
- **Compliance** - Regulatory mapping, policy development, audit preparation
- **Risk Management** - Legal risk assessment, mitigation strategies, insurance

**Legal domains covered:**
| Domain | Topics |
|--------|--------|
| Software | Licensing, SaaS agreements, open source |
| Privacy | GDPR, CCPA, data transfers, consent |
| IP | Patents, trademarks, copyrights, trade secrets |
| Employment | Agreements, NDAs, non-competes, IP assignments |
| Corporate | Formation, governance, equity, M&A |

---

## Project Setup Plugin

> Keep your CLAUDE.md accurate and effective. Audits every claim against your actual codebase, detects outdated information, and generates tailored configuration through interactive questionnaires.

### Agents

#### `claude-md-auditor`

Expert auditor for `.claude.md` files that verifies ground truth, detects obsolete information, and ensures alignment with best practices.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | .claude.md auditing, creation, verification, improvement |

**Core capabilities:**
- **Ground Truth Verification** - Validates every claim against actual codebase
- **Obsolescence Detection** - Finds outdated file paths, dependencies, commands
- **Best Practices Compliance** - Checks instruction economy, conciseness, progressive disclosure
- **Tailored Creation** - Generates .claude.md based on your preferences
- **Guided Improvement** - Helps prioritize and apply fixes incrementally

**Best practices enforced:**
- Conciseness (<300 lines, ideally <100)
- Instruction economy (~150-200 instruction budget)
- Progressive disclosure (reference docs, don't embed)
- Pointers over copies (reference files, not code)

### Commands

#### `/create-claude-md`

Creates a new `.claude.md` file through interactive questionnaire about your workflow and preferences.

#### `/maintain-claude-md`

Audits and optionally improves your existing `.claude.md` file with ground truth verification.

**Two workflows:**
1. **Audit-only**: Review findings, no changes applied
2. **Audit + improvements**: Fix issues with guided prioritization

---

## Code Documentation Plugin

> Generate docs that match reality. Analyzes your code bottom-up before writing a single line -- so documentation reflects what the code actually does, not what someone assumed.

### Agents

#### `documentation-engineer`

Expert documentation engineer that creates accurate technical documentation by analyzing existing code first. Uses bottom-up analysis to ensure documentation reflects reality.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | API docs, architecture docs, tutorials, documentation management |

**Invocation:**
```
Use the documentation-engineer agent to document [codebase/feature]
```

**Capabilities:**
- Documentation-as-code workflows
- API documentation generation
- Architecture and design docs
- Tutorials and onboarding guides
- Documentation reorganization and compaction

---

### Commands

#### `/docs-create`

Analyze code bottom-up and generate accurate documentation -- API reference, architecture guides, or full project docs. Confirms scope before generating.

```
/docs-create src/api/ --api-only
```

---

#### `/docs-maintain`

Audit and refactor existing documentation to ensure accuracy and completeness.

```
/docs-maintain docs/
```

---

## CSP Plugin

> Solve complex scheduling, routing, and assignment problems that would take days to model from scratch. Expert constraint programming with Google OR-Tools CP-SAT.

### Agents

#### `or-tools-expert`

Master constraint programmer specializing in modeling and solving complex optimization problems using Google OR-Tools CP-SAT.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | Constraint programming, scheduling, optimization, routing, assignment problems |

**Core capabilities:**
- **CSP Modeling** - Variables, domains, linear and global constraints
- **Scheduling** - Job shop, flow shop, nurse scheduling, resource allocation
- **Optimization** - Minimize/maximize objectives, multi-objective problems
- **Performance** - Parallel solving, hints, domain tightening, symmetry breaking
- **Debugging** - Infeasibility analysis, assumptions, solution enumeration

**Problem types:**
| Problem Type | Examples |
|--------------|----------|
| Scheduling | Job shop, nurse shifts, project scheduling (RCPSP) |
| Assignment | Task allocation, load balancing, bin packing |
| Routing | TSP, VRP, circuit problems |
| Classic CSP | N-Queens, Sudoku, graph coloring |
| Planning | Production planning, workforce optimization |

**Prerequisites:**
```bash
pip install ortools
# or with uv
uv add ortools
```

**Resources:**
- [OR-Tools Documentation](https://developers.google.com/optimization/cp)
- [CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/) - comprehensive guide
- [CP-SAT Log Analyzer](https://cpsat-log-analyzer.streamlit.app/)

---

## Digital Marketing Plugin

> Drive organic traffic and conversions. Technical SEO audits, content strategy, and marketing optimization with Playwright-powered analysis and persistent reports.

### Agents

#### `seo-specialist`

Expert SEO strategist specializing in technical SEO, content optimization, and search engine rankings.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Technical SEO audits, keyword research, on-page optimization, structured data |

**Invocation:**
```
Use the seo-specialist agent to [audit/optimize/research] [target]
```

**Expertise:**
- Technical SEO audits (crawl errors, broken links, redirect chains)
- Keyword research and competition analysis
- On-page optimization and content structure
- Structured data / schema markup implementation
- Core Web Vitals and performance optimization
- E-E-A-T factors and algorithm update recovery

---

#### `content-marketer`

Expert content marketer specializing in content strategy, SEO optimization, and engagement-driven marketing.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Content strategy, editorial calendars, campaign management, lead generation |

**Invocation:**
```
Use the content-marketer agent to [plan/create/optimize] [content/campaign]
```

**Expertise:**
- Content strategy and editorial planning
- Multi-channel content creation (blog, email, social, video)
- SEO-optimized content production
- Lead generation and conversion optimization
- Analytics, A/B testing, and ROI measurement
- Brand voice consistency and thought leadership

---

### Commands

#### `/seo-audit`

5-phase technical SEO audit with Playwright analysis, scoring, checkpoint before fixes, and persistent report.

```
/seo-audit https://example.com
```

**Phases:** Discovery -> Technical Audit -> Score -> (Checkpoint) -> Fix -> Report

**Output:** `.seo-audit/` directory with discovery, audit, scorecard, fixes, and final report.

---

#### `/content-strategy`

Marketing and conversion audit using 3 parallel agents (UX/Conversion, Content/Copy, Social/Visual) with checkpoint before changes and persistent report.

```
/content-strategy https://example.com
```

**Phases:** Scope -> Parallel Audit (3 agents) -> Synthesis -> (Checkpoint) -> Apply -> Report

**Output:** `.content-strategy/` directory with scope, audit, plan, changes, and final report.

---

## Messaging Plugin

> Design reliable messaging systems from the start. Expert AMQP patterns, queue design, high availability configuration, and performance tuning for RabbitMQ.

### Agents

#### `rabbitmq-expert`

Expert in RabbitMQ messaging, configuration, and optimization.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | RabbitMQ setup, queue design, AMQP patterns, high availability, performance tuning |

**Invocation:**
```
Use the rabbitmq-expert agent to [design/configure/optimize] [messaging system]
```

---

## Research Plugin

> Find precise answers fast. Advanced multi-source search strategies with query optimization across codebases and web sources -- when you need more than a simple grep.

### Agents

#### `search-specialist`

Expert search specialist for advanced information retrieval, query optimization, and knowledge discovery across diverse sources.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Information retrieval, query optimization, web search, codebase search |

**Invocation:**
```
Use the search-specialist agent to research [topic/question]
```

---

## Mobile Development Plugin

> Know your competition inside out. Automated Android app analysis via ADB -- navigate, screenshot, and document UX/UI patterns into comprehensive competitive reports.

### Skills

#### `analyze-mobile-app`

Mobile app competitive analyzer with automated ADB-based navigation, screenshot capture, and report generation.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Competitor app analysis, UX/UI documentation, mobile app research |

**Capabilities:**
- Navigate Android apps via ADB
- Capture and annotate screenshots
- Document UX/UI patterns
- Generate comprehensive analysis reports

---

## TypeScript Development Plugin

> Write clean TypeScript that follows established standards. Metabase coding patterns plus Knip dead code detection for unused files, exports, and dependencies.

### Skills

#### `typescript-write`

Write TypeScript and JavaScript code following Metabase coding standards and best practices.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | TypeScript/JavaScript development, code refactoring, coding standards |

#### `knip`

Knip finds unused files, dependencies, exports, and types in JavaScript/TypeScript projects. Plugin system for frameworks (React, Next.js, Vite), test runners (Vitest, Jest), and build tools.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dead code detection, unused dependency cleanup, bundle size optimization, CI dependency hygiene |

---

## Workflows Plugin

> Run entire development workflows with one command. Chains brainstorming, planning, implementation, code review, and cleanup into automated pipelines with checkpoints at each stage.

### Commands

#### `/feature-e2e`

End-to-end feature pipeline: brainstorm design, write implementation plan, execute with TDD checkpoints, review changes (architecture + security + patterns), and humanize code.

| | |
|---|---|
| **Invoke** | `/feature-e2e <feature description> [--skip-brainstorm] [--skip-humanize] [--strict-mode]` |
| **Pipeline** | brainstorming -> writing-plans -> executing-plans -> code-review -> humanize |
| **Checkpoints** | After design, plan, execution, and review phases |
| **Dependencies** | ai-tooling, code-review, humanize plugins |

#### `/frontend-redesign`

Full frontend redesign pipeline: UX audit, layout system design, implementation, React performance optimization, UI polish, and final design audit with visual report.

| | |
|---|---|
| **Invoke** | `/frontend-redesign <target path> [--framework react\|vue\|svelte] [--skip-performance] [--strict-mode]` |
| **Pipeline** | ui-ux-designer -> ui-layout-designer -> frontend-design -> react-performance-optimizer -> ui-polisher -> design audit |
| **Checkpoints** | After layout spec and polish phases |
| **Output** | `.frontend-redesign/report.md` -- actionable checklist with before/after comparison |
| **Dependencies** | frontend, frontend-design plugins |

#### `/mobile-intel`

Competitive mobile intelligence: analyze competitor Android app via ADB, brainstorm differentiating features, design improved UX, write implementation plan, and scaffold Tauri 2 mobile app.

| | |
|---|---|
| **Invoke** | `/mobile-intel <app-package-name> [--device <device-id>] [--skip-scaffold]` |
| **Pipeline** | analyze-mobile-app -> brainstorming -> ui-ux-designer -> writing-plans -> tauri2-mobile |
| **Checkpoints** | After analysis, brainstorm, and plan phases |
| **Pre-flight** | Verifies ADB device connection |
| **Dependencies** | mobile-development, ai-tooling, frontend, tauri-development plugins |

#### `/tauri-pipeline`

End-to-end Tauri 2 desktop app pipeline: Rust backend review, Tauri IPC optimization, React performance, layout composition, and UI polish.

| | |
|---|---|
| **Invoke** | `/tauri-pipeline <target path> [--rust-only] [--frontend-only] [--strict-mode]` |
| **Pipeline** | rust-engineer -> tauri-optimizer -> react-performance-optimizer -> ui-layout-designer -> ui-polisher |
| **Checkpoints** | After Tauri IPC review |
| **Pre-flight** | Verifies `src-tauri/` directory and `tauri.conf.json` exist |
| **Dependencies** | tauri-development, frontend plugins |

---

## App Explorer Plugin

> Automated webapp explorer that crawls a local web application using Playwright BFS, mapping all screens, interactive elements, navigation flows, and user workflows into a structured JSON sitemap with per-screen screenshots.

### Skills

#### `app-explorer`

Crawls local web applications via Playwright breadth-first search. Maps screens, interactive elements, and navigation flows into structured JSON with screenshots. Computes UX metrics (min clicks, average depth, deepest screens).

| | |
|---|---|
| **Trigger** | `/app-explorer`, "explore my app", "map the webapp", "crawl my frontend" |
| **Features** | Authenticated SPAs, session persistence, mobile viewport, per-screen screenshots |
| **Output** | JSON sitemap with UX metrics |

---

## Browser Extensions Plugin

> Expert Firefox extension (WebExtension) developer covering Manifest V2/V3, all 51 browser.* APIs, content scripts, background scripts, native messaging, cross-browser compatibility, AMO publishing, and web-ext CLI tooling.

### Skills

#### `firefox-extension-dev`

Comprehensive Firefox WebExtension development guidance covering the full extension lifecycle.

| | |
|---|---|
| **Trigger** | Firefox extension, WebExtension, browser add-on, manifest.json, content scripts, AMO publishing |
| **Coverage** | Manifest V2/V3, browser.* APIs, native messaging, sidebar extensions, cross-browser porting |

---

## Obsidian Development Plugin

> Obsidian community plugin development with ObsidianReviewBot compliance, project scaffolding, and pre-submission checks.

### Skills

#### `obsidian-plugin-development`

Write Obsidian plugin code that passes the ObsidianReviewBot automated review on first submission. Covers all required eslint-plugin-obsidianmd rules with code examples.

| | |
|---|---|
| **Trigger** | Writing, reviewing, or fixing Obsidian community plugin code |
| **Coverage** | 21 required rules (sentence case, no inline styles, promise handling, etc.), API reference |
| **Reference** | Condensed TypeScript API reference for Plugin, Vault, Workspace, Setting, Modal, and more |

#### `obsidian-scaffold`

Scaffold a new Obsidian community plugin project that is bot-compliant from day one.

| | |
|---|---|
| **Trigger** | Creating a new Obsidian plugin from scratch |
| **Creates** | `manifest.json`, `package.json`, `tsconfig.json`, `esbuild.config.mjs`, `.eslintrc.json`, `src/main.ts` |
| **Validates** | Plugin ID, name, and description against ObsidianReviewBot rules |

#### `obsidian-check`

Pre-submission lint and review. Auto-installs `eslint-plugin-obsidianmd` if missing, runs all 28 ESLint rules (including `ui/sentence-case`), plus additional manual checks not covered by the linter.

| | |
|---|---|
| **Trigger** | Before pushing or submitting an Obsidian plugin |
| **Auto-setup** | Installs `eslint-plugin-obsidianmd` with recommended config if not present |
| **Checks** | TypeScript compilation, 28 ESLint rules (sentence case, inline styles, commands, manifest, etc.), 6 manual checks, manifest validation, LICENSE |
| **Output** | Structured report with severity grouping, file:line locations, and suggested fixes |

---

---

<details>
<summary><h2>Project Structure</h2></summary>

```
alfio-claude-plugins/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── python-development/
│   │   ├── agents/
│   │   │   └── python-pro.md
│   │   ├── skills/
│   │   │   ├── python-refactor/
│   │   │   ├── python-tdd/
│   │   │   ├── python-performance-optimization/
│   │   │   ├── async-python-patterns/
│   │   │   ├── python-packaging/
│   │   │   ├── uv-package-manager/
│   │   │   └── python-comments/
│   │   └── commands/
│   │       ├── python-scaffold.md
│   │       └── python-refactor.md
│   ├── humanize/
│   │   ├── agents/
│   │   │   └── humanize.md
│   │   └── commands/
│   │       └── humanize.md
│   ├── deep-dive-analysis/
│   │   ├── skills/
│   │   │   └── deep-dive-analysis/
│   │   └── commands/
│   │       └── deep-dive-analysis.md
│   ├── code-review/
│   │   ├── agents/
│   │   │   ├── architect-review.md
│   │   │   ├── security-auditor.md
│   │   │   └── pattern-quality-scorer.md
│   │   └── commands/
│   │       ├── full-review.md
│   │       ├── code-review.md
│   │       └── pr-enhance.md
│   ├── tauri-development/
│   │   ├── agents/
│   │   │   ├── tauri-optimizer.md
│   │   │   └── rust-engineer.md
│   │   └── skills/
│   │       └── tauri2-mobile/
│   ├── frontend/
│   │   ├── agents/
│   │   │   ├── react-performance-optimizer.md
│   │   │   ├── ui-polisher.md
│   │   │   ├── ui-ux-designer.md
│   │   │   ├── ui-layout-designer.md
│   │   │   └── css-master.md
│   │   ├── skills/
│   │   │   └── css-master/
│   │   └── commands/
│   │       └── review-design.md
│   ├── frontend-design/
│   │   └── skills/
│   │       └── frontend-design/
│   ├── ai-tooling/
│   │   ├── agents/
│   │   │   └── prompt-engineer.md
│   │   ├── skills/
│   │   │   ├── brainstorming/
│   │   │   ├── writing-plans/
│   │   │   └── executing-plans/
│   │   └── commands/
│   │       └── prompt-optimize.md
│   ├── stripe/
│   │   └── skills/
│   │       ├── stripe-agent/
│   │       └── revenue-optimizer/
│   ├── utilities/
│   │   ├── skills/
│   │   │   └── file-organizer/
│   │   └── commands/
│   │       ├── organize-files.md
│   │       └── cleanup-dead-code.md
│   ├── business/
│   │   └── skills/
│   │       └── legal-advisor/
│   ├── project-setup/
│   │   ├── agents/
│   │   │   └── claude-md-auditor.md
│   │   └── commands/
│   │       ├── create-claude-md.md
│   │       └── maintain-claude-md.md
│   ├── code-documentation/
│   │   ├── agents/
│   │   │   └── documentation-engineer.md
│   │   └── commands/
│   │       ├── docs-create.md
│   │       └── docs-maintain.md
│   ├── csp/
│   │   └── agents/
│   │       └── or-tools-expert.md
│   ├── digital-marketing/
│   │   ├── agents/
│   │   │   ├── seo-specialist.md
│   │   │   └── content-marketer.md
│   │   └── commands/
│   │       ├── seo-audit.md
│   │       └── content-strategy.md
│   ├── messaging/
│   │   └── agents/
│   │       └── rabbitmq-expert.md
│   ├── research/
│   │   └── agents/
│   │       └── search-specialist.md
│   ├── mobile-development/
│   │   └── skills/
│   │       └── analyze-mobile-app/
│   ├── typescript-development/
│   │   └── skills/
│   │       ├── typescript-write/
│   │       └── knip/
│   ├── workflows/
│   │   └── commands/
│   │       ├── feature-e2e.md
│   │       ├── frontend-redesign.md
│   │       ├── mobile-intel.md
│   │       └── tauri-pipeline.md
│   ├── app-explorer/
│   │   └── skills/
│   │       └── app-explorer/
│   ├── browser-extensions/
│   │   └── skills/
│   │       └── firefox-extension-dev/
│   └── obsidian-development/
│       └── skills/
│           ├── obsidian-plugin-development/
│           │   └── references/
│           ├── obsidian-scaffold/
│           └── obsidian-check/
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
