# 🔌 Alfio Claude Plugins

Custom Claude Code plugin marketplace with development workflow agents, skills, and commands for Python development, code review, Tauri/Rust, frontend optimization, and AI tooling.

---

## 📑 Table of Contents

- [Installation](#-installation)
- [Plugins Overview](#-plugins-overview)
- [Python Development](#-python-development-plugin)
  - [Agents](#-agents)
  - [Skills](#-skills)
  - [Commands](#-commands)
- [Code Review](#-code-review-plugin)
  - [Agents](#-agents-1)
  - [Skills](#-skills-1)
- [Tauri Development](#-tauri-development-plugin)
  - [Agents](#-agents-2)
  - [Skills](#-skills-2)
- [Frontend Optimization](#-frontend-optimization-plugin)
  - [Agents](#-agents-3)
- [AI Tooling](#-ai-tooling-plugin)
  - [Agents](#-agents-4)
- [Stripe](#-stripe-plugin)
  - [Skills](#-skills-3)
- [Utilities](#-utilities-plugin)
  - [Skills](#-skills-4)
  - [Commands](#-commands-2)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📦 Installation

### 🌐 From GitHub (Recommended)

**Step 1:** Add the marketplace
```bash
claude plugin marketplace add acaprino/alfio-claude-plugins
```

**Step 2:** Install the plugins you need
```bash
claude plugin install python-development@alfio-claude-plugins
claude plugin install code-review@alfio-claude-plugins
claude plugin install tauri-development@alfio-claude-plugins
claude plugin install frontend-optimization@alfio-claude-plugins
claude plugin install ai-tooling@alfio-claude-plugins
claude plugin install stripe@alfio-claude-plugins
```

### 💻 From Local Path (Development)

Use `--plugin-dir` to load plugins for current session:
```bash
claude --plugin-dir /path/to/alfio-claude-plugins
```

### ✅ Verify Installation

```bash
# List marketplaces
claude plugin marketplace list

# List installed plugins
claude plugin list
```

---

## 🗂️ Plugins Overview

| Plugin | Description | 🤖 Agents | 🛠️ Skills | ⚡ Commands |
|--------|-------------|:------:|:------:|:--------:|
| [🐍 **python-development**](#-python-development-plugin) | Modern Python, Django, FastAPI, testing, packaging | 3 | 6 | 2 |
| [🔍 **code-review**](#-code-review-plugin) | Code review and deep analysis | 1 | 1 | 1 |
| [🦀 **tauri-development**](#-tauri-development-plugin) | Tauri 2 mobile/desktop and Rust engineering | 2 | 1 | - |
| [⚛️ **frontend-optimization**](#-frontend-optimization-plugin) | React performance, UI polish, and UX design | 3 | - | - |
| [🧠 **ai-tooling**](#-ai-tooling-plugin) | Prompt engineering and LLM optimization | 1 | - | 1 |
| [💳 **stripe**](#-stripe-plugin) | Payments, subscriptions, Connect, billing, revenue optimization | - | 2 | - |
| [🗂️ **utilities**](#-utilities-plugin) | File organization, cleanup, and directory management | - | 1 | 1 |

---

## 🐍 Python Development Plugin

> Modern Python development ecosystem with frameworks, testing, packaging, and code refactoring.

### 🤖 Agents

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

#### `django-pro`

Expert Django developer specializing in Django 5.x, DRF, async views, and scalable architectures.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Django apps, DRF APIs, ORM optimization, Celery tasks, Django Channels |

**Invocation:**
```
Use the django-pro agent to [design/implement/optimize] [feature]
```

**Expertise:**
- Django 5.x async views and middleware
- Django REST Framework patterns
- ORM optimization (select_related, prefetch_related)
- Celery background tasks
- Django Channels WebSockets

---

#### `fastapi-pro`

Expert FastAPI developer for high-performance async APIs with modern Python patterns.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | FastAPI microservices, async SQLAlchemy, Pydantic V2, WebSockets |

**Invocation:**
```
Use the fastapi-pro agent to [build/optimize] [API/service]
```

**Expertise:**
- FastAPI 0.100+ with Annotated types
- SQLAlchemy 2.0+ async patterns
- Pydantic V2 validation
- OAuth2/JWT authentication
- OpenTelemetry observability

---

### 🛠️ Skills

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

**Synergy:** Works with `python-testing-patterns` and `python-performance-optimization`

---

#### `python-testing-patterns`

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

### ⚡ Commands

#### `/python-scaffold`

Generate production-ready Python project structures.

```
/python-scaffold FastAPI REST API for user management
```

**Project types:**
- FastAPI (APIs, microservices)
- Django (full-stack web apps)
- Library (reusable packages)
- CLI (command-line tools)

**Generates:**
- Complete directory structure
- pyproject.toml with dependencies
- pytest configuration
- Makefile with common tasks
- .env.example and .gitignore

---

#### `/python-refactor`

Execute 4-phase refactoring workflow on target code.

```
/python-refactor src/legacy_module.py
```

**Outputs:**
- Pre-refactoring analysis report
- Prioritized issue list
- Refactoring plan with risk assessment
- Post-refactoring metrics comparison

---

## 🔍 Code Review Plugin

> Tools for systematic code review and deep codebase analysis.

### 🤖 Agents

#### `senior-code-reviewer`

Expert code review agent providing systematic analysis of quality, security, and performance.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Pre-deployment reviews, security audits, architecture assessment |

**Invocation:**
```
Use the senior-code-reviewer agent to review [file/feature]
```

**Output includes:**
- Executive summary (DEPLOY / FIX-FIRST / REDESIGN)
- Findings by severity (CRITICAL, HIGH, MEDIUM, LOW)
- Quality scores (Security, Performance, Maintainability)
- Prioritized action plan

---

### 🛠️ Skills

#### `deep-dive-analysis`

AI-powered systematic codebase analysis combining structure extraction with semantic understanding.

| | |
|---|---|
| **Invoke** | `/deep-dive-analysis` |
| **Use for** | Codebase understanding, architecture mapping, onboarding |

**Capabilities:**
- 📊 Extract code structure (classes, functions, imports)
- 🔗 Map internal/external dependencies
- 🏗️ Recognize architectural patterns
- ⚠️ Identify anti-patterns and red flags
- 🔄 Trace data and control flows

---

### ⚡ Commands

#### `/senior-code-review`

Perform systematic code review with security, performance, and architecture analysis.

```
/senior-code-review src/api/users.py
```

**Analysis phases:**
1. 🚨 **Fast-fail scan** - Critical security/data issues
2. 🔒 **Security audit** - OWASP Top 10, auth, input validation
3. ⚡ **Performance** - Algorithm complexity, N+1 queries
4. 🧹 **Code quality** - DRY, SOLID, error handling
5. 🏗️ **Architecture** - Design patterns, scalability

**Outputs:**
- Executive summary with DEPLOY/FIX-FIRST/REDESIGN recommendation
- Findings by severity (CRITICAL, HIGH, MEDIUM, LOW)
- Quality scores (Security, Performance, Maintainability, Testing)
- Prioritized action plan with effort estimates

---

## 🦀 Tauri Development Plugin

> Specialized tools for Tauri 2 cross-platform development and Rust engineering.

### 🤖 Agents

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

### 🛠️ Skills

#### `tauri2-mobile`

Expert guidance for Tauri 2 mobile app development (Android/iOS).

| | |
|---|---|
| **Invoke** | `/tauri2-mobile` |
| **Use for** | 📱 Mobile setup, plugins, testing, store deployment |

**Quick commands:**
| Task | Command |
|------|---------|
| 🤖 Init Android | `npm run tauri android init` |
| 🔧 Dev Android | `npm run tauri android dev` |
| 📦 Build APK | `npm run tauri android build --apk` |
| 🍎 Build iOS | `npm run tauri ios build` |

---

## ⚛️ Frontend Optimization Plugin

> React performance optimization, UI polish, and UX design tools.

### 🤖 Agents

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

## 🧠 AI Tooling Plugin

> Prompt engineering and LLM optimization tools.

### 🤖 Agents

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

### ⚡ Commands

#### `/prompt-optimize`

Analyze and optimize prompts for better results, reduced token usage, and improved reliability.

```
/prompt-optimize "You are a helpful assistant that..."
```

**Optimization phases:**
1. 📊 **Analysis** - Parse structure, count tokens, detect patterns
2. 🔍 **Issue detection** - Redundancy, ambiguity, missing constraints
3. ✨ **Optimization** - Apply clarity, token reduction, structure patterns
4. ✅ **Validation** - Compare metrics, test scenarios

**Outputs:**
- Current prompt analysis with scores (Clarity, Specificity, Token efficiency)
- Optimized prompt with all improvements applied
- Metrics comparison (before/after tokens, scores)
- Recommendations for further improvement

**Optimization patterns applied:**
- 🎯 Clarity optimization (vague → specific)
- ⚡ Token reduction (remove filler, compress)
- 🔧 Structure improvement (Role, Task, Constraints, Format)
- 🛡️ Reliability patterns (constraints, verification, fallbacks)

---

## 💳 Stripe Plugin

> Comprehensive Stripe integration for payments, subscriptions, marketplaces, and billing.

### 🛠️ Skills

#### `stripe-agent`

Complete Stripe API integration covering payments, subscriptions, Connect marketplaces, and compliance.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Payment processing, subscriptions, marketplaces, billing, webhooks |

**Core capabilities:**
- 💳 **Payments** - Payment intents, checkout sessions, payment links
- 🔄 **Subscriptions** - Recurring billing, metered usage, tiered pricing
- 🏪 **Connect** - Marketplace payments, platform fees, seller onboarding
- 🧾 **Billing** - Invoices, customer portal, tax calculation
- 🔔 **Webhooks** - Event handling, subscription lifecycle
- 🔒 **Security** - 3D Secure, SCA compliance, fraud prevention (Radar)
- ⚖️ **Disputes** - Chargeback handling, evidence submission

**Quick reference:**
| Task | Method |
|------|--------|
| Create customer | `stripe.Customer.create()` |
| Checkout session | `stripe.checkout.Session.create()` |
| Subscription | `stripe.Subscription.create()` |
| Payment link | `stripe.PaymentLink.create()` |
| Report usage | `stripe.SubscriptionItem.create_usage_record()` |
| Connect account | `stripe.Account.create(type="express")` |

**Includes:**
- 📜 Python utility scripts (customer management, webhooks, sync)
- 🔥 Firebase integration reference
- 📋 API cheatsheet

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

**Capabilities:**
- 📊 **Feature Discovery** - Scan routes, components, services to build feature inventory
- 💰 **Cost Mapping** - Calculate fixed, variable, and per-use costs from service integrations
- 📈 **Usage Analysis** - Model user consumption patterns and set optimal tier limits
- 🏷️ **Tier Design** - Create Free/Pro/Enterprise tiers with healthy margins
- 📉 **Revenue Modeling** - Calculate ARPU, LTV, break-even, and 12-month projections

**Output Example:**
```
═══════════════════════════════════════════════════════════
                    PRICING STRATEGY REPORT
═══════════════════════════════════════════════════════════
📁 CODEBASE ANALYSIS - Services & Features discovered
💰 COST BREAKDOWN - Fixed + Variable + Feature costs
📊 USAGE PATTERN ANALYSIS - Distribution & tier limits
📈 REVENUE MODEL - ARPU, LTV, break-even, projections
🏷️ RECOMMENDED TIERS - Free, Pro, Business, Enterprise
═══════════════════════════════════════════════════════════
```

**Key Metrics Calculated:**
| Metric | Formula |
|--------|---------|
| ARPU | (Free×$0 + Pro×$X + Biz×$Y) / Total Users |
| LTV | (ARPU × Margin) / Monthly Churn |
| Break-even | Fixed Costs / (ARPU - Variable Cost) |
| Optimal Price | (Cost Floor × 0.3) + (Value Ceiling × 0.7) |

**Includes:**
- 📜 Reference docs for pricing patterns, subscriptions, usage modeling
- 🔥 Stripe integration patterns
- ✅ Checkout optimization best practices
- 📋 Implementation checklist

---

## 🗂️ Utilities Plugin

> File organization, cleanup, duplicate detection, and directory management.

### 🛠️ Skills

#### `file-organizer`

Personal organization assistant for maintaining clean, logical file structures.

| | |
|---|---|
| **Invoke** | Skill reference or `/organize-files` |
| **Use for** | Messy folders, duplicates, old files, project restructuring |

**Capabilities:**
- 📊 **Analyze** - Review folder structure and file types
- 🔍 **Find Duplicates** - Identify duplicate files by hash
- 📁 **Suggest Structure** - Propose logical folder organization
- 🤖 **Automate** - Move, rename, organize with approval
- 🗑️ **Cleanup** - Identify old/unused files for archiving

**Organization patterns:**
- By type: Documents, Images, Videos, Archives, Code
- By purpose: Work vs Personal, Active vs Archive
- By date: Current year, Previous years, Old files

---

### ⚡ Commands

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

## 💡 Usage Examples

### 🐍 Python Development Workflow
```
1️⃣ /python-scaffold FastAPI microservice
2️⃣ Implement features with python-pro agent
3️⃣ /python-refactor on complex modules
4️⃣ Use python-testing-patterns for test coverage
```

### 🔍 Code Review Workflow
```
1️⃣ /senior-code-review src/features/auth/
2️⃣ Address CRITICAL and HIGH issues first
3️⃣ /python-refactor on flagged modules
4️⃣ Use react-performance-optimizer for React-specific issues
```

### 🦀 Tauri App Optimization
```
1️⃣ Use tauri-optimizer for IPC and Rust backend
2️⃣ Use react-performance-optimizer for React frontend
3️⃣ Use ui-polisher for animations and polish
```

### 🔧 Legacy Code Modernization
```
1️⃣ /deep-dive-analysis to understand codebase
2️⃣ /python-refactor on legacy modules
3️⃣ Use python-testing-patterns to add test coverage
4️⃣ Use senior-code-reviewer before merge
```

---

## 📁 Project Structure

```
alfio-claude-plugins/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── python-development/
│   │   ├── agents/
│   │   │   ├── python-pro.md
│   │   │   ├── django-pro.md
│   │   │   └── fastapi-pro.md
│   │   ├── skills/
│   │   │   ├── python-refactor/
│   │   │   ├── python-testing-patterns/
│   │   │   ├── python-performance-optimization/
│   │   │   ├── async-python-patterns/
│   │   │   ├── python-packaging/
│   │   │   └── uv-package-manager/
│   │   └── commands/
│   │       ├── python-scaffold.md
│   │       └── python-refactor.md
│   ├── code-review/
│   │   ├── agents/
│   │   │   └── senior-code-reviewer.md
│   │   ├── skills/
│   │   │   └── deep-dive-analysis/
│   │   └── commands/
│   │       └── senior-code-review.md
│   ├── tauri-development/
│   │   ├── agents/
│   │   │   ├── tauri-optimizer.md
│   │   │   └── rust-engineer.md
│   │   └── skills/
│   │       └── tauri2-mobile/
│   ├── frontend-optimization/
│   │   └── agents/
│   │       ├── react-performance-optimizer.md
│   │       ├── ui-polisher.md
│   │       └── ui-ux-designer.md
│   ├── ai-tooling/
│   │   ├── agents/
│   │   │   └── prompt-engineer.md
│   │   └── commands/
│   │       └── prompt-optimize.md
│   ├── stripe/
│   │   └── skills/
│   │       ├── stripe-agent/
│   │       │   ├── SKILL.md
│   │       │   ├── scripts/
│   │       │   │   ├── stripe_utils.py
│   │       │   │   ├── webhook_handler.py
│   │       │   │   ├── sync_subscriptions.py
│   │       │   │   └── setup_products.py
│   │       │   └── references/
│   │       │       ├── firebase-integration.md
│   │       │       └── api-cheatsheet.md
│   │       └── revenue-optimizer/
│   │           ├── SKILL.md
│   │           └── references/
│   │               ├── pricing-patterns.md
│   │               ├── stripe.md
│   │               ├── cost-analysis.md
│   │               ├── subscription-patterns.md
│   │               ├── usage-revenue-modeling.md
│   │               └── checkout-optimization.md
│   └── utilities/
│       ├── skills/
│       │   └── file-organizer/
│       │       └── SKILL.md
│       └── commands/
│           └── organize-files.md
├── LICENSE
└── README.md
```

---

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. ➕ Add your agent/skill following the existing structure
4. 📝 Update `marketplace.json` with your additions
5. 🚀 Submit a pull request

### 🤖 Agent Template

```markdown
---
name: agent-name
description: Brief description of the agent's purpose
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
---

Agent instructions and expertise...
```

### 🛠️ Skill Template

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

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**📊 Total:** 🤖 10 Agents | 🛠️ 11 Skills | ⚡ 5 Commands
