# Codebase Cleanup Plugin

> Three multi-language slash commands for technical debt reduction: dependency security auditing, SOLID-driven refactoring, and prioritized tech-debt remediation roadmaps. Cherry-picked from `wshobson/agents` and adapted to route around our specialized siblings instead of duplicating them.

**Version:** 1.0.0

## What's inside

No agents, no skills. Three slash commands that read the project, scan against external databases, and produce reports with concrete fix actions.

## Commands

### `/codebase-cleanup:deps-audit`

CVE / license / supply-chain audit across multiple package ecosystems.

```
/codebase-cleanup:deps-audit
/codebase-cleanup:deps-audit . --ecosystem=npm --security-only
/codebase-cleanup:deps-audit --license-check --update-pr
```

| Flag | Effect |
|------|--------|
| `[path]` | Project root (defaults to current directory) |
| `--ecosystem=<name>` | `npm`, `python`, `go`, or `all` (auto-detected by default) |
| `--security-only` | Skip license/size analysis, focus on CVEs |
| `--license-check` | Build the license-compatibility matrix |
| `--update-pr` | Generate a dependency-update pull request body |

**Ecosystems covered:** npm/yarn, pip/poetry/Pipenv, gem, maven/gradle, go modules, cargo, composer, NuGet.

**What it produces:**
- Executive risk summary
- CVE list with severity, exploit availability, patched versions
- License compatibility matrix and policy-strike list
- Outdated-dependency priority queue (security fixes first)
- Bundle-size impact report (npm only)
- Supply-chain checks: typosquatting, maintainer changes, suspicious patterns
- Automated remediation scripts and a PR body template
- GitHub Actions workflow for continuous monitoring

**DO NOT TRIGGER WHEN:**
- Removing dead code or phantom dependencies only: use `/senior-review:code-review --commit`
- Python-only lint, type, complexity, and coverage audit: use `/python-development:python-audit`
- Stripe webhook event audit: use `/stripe:audit-webhooks`

---

### `/codebase-cleanup:refactor-clean`

SOLID-driven refactoring command with before/after metrics. Multi-language examples (Python, TypeScript, Java, Go).

```
/codebase-cleanup:refactor-clean src/orders.py
/codebase-cleanup:refactor-clean src/ --language=typescript --principles=solid --with-tests
```

| Flag | Effect |
|------|--------|
| `[path or code block]` | Target file, directory, or pasted code |
| `--language=<lang>` | `python`, `typescript`, `java`, `go` (or auto-detect) |
| `--principles=<set>` | `solid`, `clean-code`, or `all` |
| `--with-tests` | Generate a regression test suite alongside the refactor |

**What it analyses:**
- Code smells (long methods, large classes, duplicates, magic numbers, nested loops)
- SOLID violations (SRP, OCP, LSP, ISP, DIP)
- Performance issues (O(n²), unnecessary allocation, missing caching)

**What it produces:**
- Prioritized refactoring plan with effort estimates
- Refactored code with method extraction, class decomposition, pattern application
- Before/after metrics: cyclomatic complexity, LOC per method, test coverage
- Migration guide for breaking changes
- Code quality checklist with target thresholds

**DO NOT TRIGGER WHEN:**
- Python-specific metrics-driven refactoring: use `/python-development:python-refactor`
- Pure readability cleanup (no structural changes): use `/clean-code:clean-code`
- Dead code or dependency removal: use `/senior-review:code-review --commit`

---

### `/codebase-cleanup:tech-debt`

Technical debt inventory, ROI scoring, and prioritized remediation roadmap. Spans code, architecture, testing, documentation, and infrastructure debt.

```
/codebase-cleanup:tech-debt
/codebase-cleanup:tech-debt . --dimension=architecture --horizon=quarter --with-roi
```

| Flag | Effect |
|------|--------|
| `[path]` | Project root |
| `--dimension=<axis>` | `code`, `architecture`, `testing`, `docs`, `infra`, or `all` |
| `--horizon=<window>` | `sprint`, `quarter`, or `year` |
| `--with-roi` | Calculate annual cost per debt item and ROI per fix |

**What it produces:**
- Categorized debt inventory with metrics (complexity scores, duplication %, coverage gaps, version lag)
- Impact assessment in hours per month and dollars per year
- Risk classification (critical, high, medium, low)
- KPI dashboard with current / target / files-above-threshold
- Quick-wins list (high value, low effort)
- Medium-term refactoring queue
- Long-term initiatives with quarter-by-quarter rollout
- Implementation strategy (facade, incremental migration, feature flags)
- Prevention strategy (pre-commit hooks, CI quality gates, debt budget)
- Stakeholder-facing executive summary

**DO NOT TRIGGER WHEN:**
- Python-only lint / type / complexity audit: use `/python-development:python-audit`
- Dead code / dependency removal: use `/senior-review:code-review --commit`
- Single-file refactoring pass: use `/python-development:python-refactor` or `/clean-code:clean-code`

---

## Attribution

Vendored from [`wshobson/agents/plugins/codebase-cleanup`](https://github.com/wshobson/agents/tree/main/plugins/codebase-cleanup) (MIT, Seth Hobson). Two upstream agents (`code-reviewer`, `test-automator`) were intentionally skipped to avoid routing collisions with `senior-review/*` and `testing/*`. Each command file carries an inline attribution header. Tracked for ongoing sync in `CLAUDE.md`.

---

**Related:** [senior-review](senior-review.md) (dead-code cleanup, architecture/security audit) | [clean-code](clean-code.md) (readability rewriting) | [python-development](python-development.md) (Python-specific refactor and audit)
