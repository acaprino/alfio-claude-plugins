# 🔌 Alfio Claude Plugins

Custom Claude Code plugin marketplace with development workflow agents, skills, and commands for Python development, code review, Tauri/Rust, frontend optimization, AI tooling, constraint programming, and more.

---

## 📑 Table of Contents

- [Installation](#-installation)
- [Plugins Overview](#-plugins-overview)
- [Python Development](#-python-development-plugin)
- [Code Review](#-code-review-plugin)
- [Comprehensive Review](#-comprehensive-review-plugin)
- [Tauri Development](#-tauri-development-plugin)
- [Frontend Optimization](#-frontend-optimization-plugin)
- [Frontend Design](#-frontend-design-plugin)
- [AI Tooling](#-ai-tooling-plugin)
- [Stripe](#-stripe-plugin)
- [Utilities](#-utilities-plugin)
- [Business](#-business-plugin)
- [Project Setup](#-project-setup-plugin)
- [Code Documentation](#-code-documentation-plugin)
- [CSP](#-csp-plugin)
- [Digital Marketing](#-digital-marketing-plugin)
- [Messaging](#-messaging-plugin)
- [Research](#-research-plugin)
- [Mobile Development](#-mobile-development-plugin)
- [TypeScript Development](#-typescript-development-plugin)
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
claude plugin install comprehensive-review@alfio-claude-plugins
claude plugin install tauri-development@alfio-claude-plugins
claude plugin install frontend-optimization@alfio-claude-plugins
claude plugin install frontend-design@alfio-claude-plugins
claude plugin install ai-tooling@alfio-claude-plugins
claude plugin install stripe@alfio-claude-plugins
claude plugin install business@alfio-claude-plugins
claude plugin install project-setup@alfio-claude-plugins
claude plugin install code-documentation@alfio-claude-plugins
claude plugin install csp@alfio-claude-plugins
claude plugin install digital-marketing@alfio-claude-plugins
claude plugin install messaging@alfio-claude-plugins
claude plugin install research@alfio-claude-plugins
claude plugin install mobile-development@alfio-claude-plugins
claude plugin install typescript-development@alfio-claude-plugins
claude plugin install utilities@alfio-claude-plugins
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
| [🐍 **python-development**](#-python-development-plugin) | Modern Python, Django, FastAPI, testing, packaging | 3 | 7 | 3 |
| [🔍 **code-review**](#-code-review-plugin) | Code review, deep analysis, and code humanization | 2 | 1 | 2 |
| [🏗️ **comprehensive-review**](#-comprehensive-review-plugin) | Multi-agent review orchestration (architecture, security, patterns) | 4 | - | 2 |
| [🦀 **tauri-development**](#-tauri-development-plugin) | Tauri 2 mobile/desktop and Rust engineering | 2 | 1 | - |
| [⚛️ **frontend-optimization**](#-frontend-optimization-plugin) | React performance, UI polish, and UX design | 3 | - | - |
| [🎨 **frontend-design**](#-frontend-design-plugin) | Distinctive, production-grade frontend interfaces | - | 1 | - |
| [🧠 **ai-tooling**](#-ai-tooling-plugin) | Prompt engineering, brainstorming, and planning workflows | 1 | 3 | 1 |
| [💳 **stripe**](#-stripe-plugin) | Payments, subscriptions, Connect, billing, revenue optimization | - | 2 | - |
| [🗂️ **utilities**](#-utilities-plugin) | File organization, cleanup, and directory management | - | 1 | 1 |
| [⚖️ **business**](#-business-plugin) | Legal advisory, compliance, contracts, and risk management | - | 1 | - |
| [⚙️ **project-setup**](#-project-setup-plugin) | .claude.md auditing, creation, and maintenance | 1 | - | 2 |
| [📖 **code-documentation**](#-code-documentation-plugin) | Technical documentation engineering and maintenance | 1 | - | 2 |
| [🧩 **csp**](#-csp-plugin) | Constraint satisfaction and optimization with OR-Tools CP-SAT | 1 | - | - |
| [📢 **digital-marketing**](#-digital-marketing-plugin) | SEO optimization, content marketing, and campaigns | 2 | - | 2 |
| [📨 **messaging**](#-messaging-plugin) | RabbitMQ messaging, configuration, and optimization | 1 | - | - |
| [🔎 **research**](#-research-plugin) | Advanced search and information retrieval | 1 | - | - |
| [📱 **mobile-development**](#-mobile-development-plugin) | Android app competitive analysis via ADB | - | 1 | - |
| [🔷 **typescript-development**](#-typescript-development-plugin) | TypeScript/JavaScript with Metabase coding standards | - | 1 | - |

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

#### `/python-full-refactor`

Execute comprehensive 4-phase systematic refactoring workflow on target code.

```
/python-full-refactor src/legacy_module.py
```

**Outputs:**
- Pre-refactoring analysis report
- Prioritized issue list
- Refactoring plan with risk assessment
- Post-refactoring metrics comparison

---

#### `/humanize-python-code`

Rewrite Python code to feel like it was written by a thoughtful senior developer.

```
/humanize-python-code src/module.py
```

**Focus areas:**
- Readable naming and natural flow
- Remove AI-generated boilerplate
- Improve code structure and clarity

---

## 🔍 Code Review Plugin

> Tools for systematic code review, deep codebase analysis, and code humanization.

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

---

#### `/deep-dive-analysis`

Perform comprehensive codebase analysis with structure extraction and AI-powered semantic understanding.

```
/deep-dive-analysis src/core/
```

---

## 🏗️ Comprehensive Review Plugin

> Multi-agent code review orchestration with architecture, security, pattern analysis, and best practices across multiple phases.

### 🤖 Agents

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

#### `code-reviewer`

Elite code review expert specializing in AI-powered code analysis, security vulnerabilities, performance optimization, and production reliability.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Code quality assurance, static analysis, configuration review |

**Invocation:**
```
Use the code-reviewer agent to review [file/feature]
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

### ⚡ Commands

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

#### `/pr-enhance`

Optimize pull requests with comprehensive descriptions and review facilitation.

```
/pr-enhance
```

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

## 🎨 Frontend Design Plugin

> Create distinctive, production-grade frontend interfaces with high design quality, avoiding generic AI aesthetics.

### 🛠️ Skills

#### `frontend-design`

Create polished web components, pages, and applications with creative design that avoids generic AI output.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Web components, landing pages, UI design, production-grade interfaces |

**Source:** Ported from [anthropics/claude-code](https://github.com/anthropics/claude-code) frontend-design plugin.

---

## 🧠 AI Tooling Plugin

> Prompt engineering, brainstorming, and planning workflows for AI-powered development.

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

### 🛠️ Skills

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

## ⚖️ Business Plugin

> Business operations support for legal advisory, compliance, contracts, and risk management.

### 🛠️ Skills

#### `legal-advisor`

Expert legal advisor specializing in technology law, compliance, and risk mitigation.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Contract review, compliance, IP protection, privacy policies, risk assessment |

**Core capabilities:**
- 📜 **Contract Management** - Review, negotiate, draft, and manage contracts
- 🔒 **Privacy & Data Protection** - GDPR, CCPA, data processing agreements
- 💡 **Intellectual Property** - Patents, trademarks, copyrights, trade secrets
- ✅ **Compliance** - Regulatory mapping, policy development, audit preparation
- ⚖️ **Risk Management** - Legal risk assessment, mitigation strategies, insurance

**Legal domains covered:**
| Domain | Topics |
|--------|--------|
| Software | Licensing, SaaS agreements, open source |
| Privacy | GDPR, CCPA, data transfers, consent |
| IP | Patents, trademarks, copyrights, trade secrets |
| Employment | Agreements, NDAs, non-competes, IP assignments |
| Corporate | Formation, governance, equity, M&A |

---

## ⚙️ Project Setup Plugin

> Tools for auditing, creating, and improving `.claude.md` files with ground truth verification.

### 🤖 Agents

#### `claude-md-auditor`

Expert auditor for `.claude.md` files that verifies ground truth, detects obsolete information, and ensures alignment with best practices.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | .claude.md auditing, creation, verification, improvement |

**Core capabilities:**
- ✅ **Ground Truth Verification** - Validates every claim against actual codebase
- 🔍 **Obsolescence Detection** - Finds outdated file paths, dependencies, commands
- 📏 **Best Practices Compliance** - Checks instruction economy, conciseness, progressive disclosure
- ✏️ **Tailored Creation** - Generates .claude.md based on your preferences
- 🔧 **Guided Improvement** - Helps prioritize and apply fixes incrementally

**Best practices enforced:**
- Conciseness (<300 lines, ideally <100)
- Instruction economy (~150-200 instruction budget)
- Progressive disclosure (reference docs, don't embed)
- Pointers over copies (reference files, not code)

### ⚡ Commands

#### `/create-claude-md`

Creates a new `.claude.md` file through interactive questionnaire about your workflow and preferences.

#### `/maintain-claude-md`

Audits and optionally improves your existing `.claude.md` file with ground truth verification.

**Two workflows:**
1. **Audit-only**: Review findings, no changes applied
2. **Audit + improvements**: Fix issues with guided prioritization

---

## 📖 Code Documentation Plugin

> Technical documentation engineering with AI-powered codebase analysis and management.

### 🤖 Agents

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

### ⚡ Commands

#### `/docs-create`

Create accurate documentation for specified targets using the documentation-engineer agent.

```
/docs-create src/api/
```

---

#### `/docs-maintain`

Audit and refactor existing documentation to ensure accuracy and completeness.

```
/docs-maintain docs/
```

---

## 🧩 CSP Plugin

> Constraint Satisfaction Problems and combinatorial optimization with Google OR-Tools CP-SAT solver.

### 🤖 Agents

#### `or-tools-expert`

Master constraint programmer specializing in modeling and solving complex optimization problems using Google OR-Tools CP-SAT.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | Constraint programming, scheduling, optimization, routing, assignment problems |

**Core capabilities:**
- 🧩 **CSP Modeling** - Variables, domains, linear and global constraints
- 📅 **Scheduling** - Job shop, flow shop, nurse scheduling, resource allocation
- 🎯 **Optimization** - Minimize/maximize objectives, multi-objective problems
- 🚀 **Performance** - Parallel solving, hints, domain tightening, symmetry breaking
- 🔍 **Debugging** - Infeasibility analysis, assumptions, solution enumeration

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

## 📢 Digital Marketing Plugin

> SEO optimization, content marketing, keyword research, and engagement-driven campaigns.

### 🤖 Agents

#### `seo-specialist`

Expert SEO strategist specializing in technical SEO, content optimization, and search engine rankings.

| | |
|---|---|
| **Model** | `default` |
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
| **Model** | `default` |
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

### ⚡ Commands

#### `/seo-audit`

Perform a comprehensive SEO audit and optimization analysis.

```
/seo-audit https://example.com
```

**Examples:**
| Command | Action |
|---------|--------|
| `/seo-audit https://example.com` | Full technical SEO audit |
| `/seo-audit src/pages` | Audit page structure for SEO |
| `/seo-audit --keywords "react tutorial"` | Keyword research and analysis |
| `/seo-audit --schema` | Structured data recommendations |

---

#### `/content-strategy`

Develop a content strategy and marketing plan.

```
/content-strategy "B2B SaaS product launch"
```

**Examples:**
| Command | Action |
|---------|--------|
| `/content-strategy "product launch"` | Full content strategy |
| `/content-strategy --audit src/blog` | Audit existing content |
| `/content-strategy --calendar Q1 2026` | Generate editorial calendar |
| `/content-strategy --competitor "site.com"` | Competitive content analysis |

---

## 📨 Messaging Plugin

> Message broker expertise for RabbitMQ configuration, optimization, and high availability.

### 🤖 Agents

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

## 🔎 Research Plugin

> Advanced search and information retrieval specialist for precise knowledge discovery.

### 🤖 Agents

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

## 📱 Mobile Development Plugin

> Automated competitive analysis of Android mobile apps via ADB.

### 🛠️ Skills

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

## 🔷 TypeScript Development Plugin

> TypeScript and JavaScript development with Metabase coding standards.

### 🛠️ Skills

#### `typescript-write`

Write TypeScript and JavaScript code following Metabase coding standards and best practices.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | TypeScript/JavaScript development, code refactoring, coding standards |

---

## 💡 Usage Examples

### 🐍 Python Development Workflow
```
1️⃣ /python-scaffold FastAPI microservice
2️⃣ Implement features with python-pro agent
3️⃣ /python-full-refactor on complex modules
4️⃣ Use python-testing-patterns for test coverage
```

### 🔍 Code Review Workflow
```
1️⃣ /senior-code-review src/features/auth/
2️⃣ Address CRITICAL and HIGH issues first
3️⃣ /python-full-refactor on flagged modules
4️⃣ Use react-performance-optimizer for React-specific issues
```

### 🏗️ Comprehensive Review Workflow
```
1️⃣ /full-review src/ --security-focus
2️⃣ architect-review checks design patterns and scalability
3️⃣ security-auditor runs OWASP and compliance checks
4️⃣ pattern-quality-scorer generates quality scores
5️⃣ Review consolidated findings and action plan
```

### 🦀 Tauri App Optimization
```
1️⃣ Use tauri-optimizer for IPC and Rust backend
2️⃣ Use react-performance-optimizer for React frontend
3️⃣ Use ui-polisher for animations and polish
```

### 🧠 AI-Assisted Planning
```
1️⃣ Use brainstorming skill to explore requirements
2️⃣ Use writing-plans skill to create implementation plan
3️⃣ Use executing-plans skill to implement with checkpoints
```

### 🔧 Legacy Code Modernization
```
1️⃣ /deep-dive-analysis to understand codebase
2️⃣ /python-full-refactor on legacy modules
3️⃣ Use python-testing-patterns to add test coverage
4️⃣ Use senior-code-reviewer before merge
```

### ⚙️ .claude.md Maintenance
```
1️⃣ /maintain-claude-md for quarterly maintenance
2️⃣ Review audit findings
3️⃣ Choose: audit-only or apply improvements
4️⃣ Or /create-claude-md to start fresh
```

### 🧩 Optimization & Scheduling with CSP
```
1️⃣ Use or-tools-expert agent for constraint programming
2️⃣ Model problem with variables, domains, and constraints
3️⃣ Enable parallelism and performance optimizations
4️⃣ Test on small instances before scaling up
```

**Example problems:**
- 📅 Employee shift scheduling with fairness constraints
- 🏭 Job shop scheduling to minimize makespan
- 📦 Bin packing and resource allocation
- 🚚 Vehicle routing and delivery optimization
- 🎯 Assignment problems with cost minimization

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
│   │   │   ├── uv-package-manager/
│   │   │   └── python-comments/
│   │   └── commands/
│   │       ├── python-scaffold.md
│   │       ├── python-full-refactor.md
│   │       └── humanize-python-code.md
│   ├── code-review/
│   │   ├── agents/
│   │   │   ├── senior-code-reviewer.md
│   │   │   └── humanize.md
│   │   ├── skills/
│   │   │   └── deep-dive-analysis/
│   │   └── commands/
│   │       ├── senior-code-review.md
│   │       └── deep-dive-analysis.md
│   ├── comprehensive-review/
│   │   ├── agents/
│   │   │   ├── architect-review.md
│   │   │   ├── code-reviewer.md
│   │   │   ├── security-auditor.md
│   │   │   └── pattern-quality-scorer.md
│   │   └── commands/
│   │       ├── full-review.md
│   │       └── pr-enhance.md
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
│   │       └── organize-files.md
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
│   └── typescript-development/
│       └── skills/
│           └── typescript-write/
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

**📊 Total:** 🤖 22 Agents | 🛠️ 19 Skills | ⚡ 15 Commands across 18 plugins
