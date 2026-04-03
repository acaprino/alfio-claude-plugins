# Senior Review Plugin

> Catch bugs before they ship. Five specialized agents review code quality, security, UI timing, distributed flows, and startup cycles in parallel -- backed by a comprehensive defect taxonomy knowledge base with 140+ defect patterns and CWE/OWASP mappings.

## Agents

### `code-auditor`

Adversarial code quality auditor combining architecture review, failure flow tracing, pattern consistency analysis, and quantitative scoring.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Architecture integrity, failure path analysis, pattern consistency, quality scoring |

**Invocation:**
```
Use the code-auditor agent to review [system/codebase]
```

**Methodology:**
- 4 cognitive frameworks (Boundary Detective, Abstraction Inspector, Chaos Engineer, State Auditor)
- 6-phase failure flow analysis (persisted state, kill points, resume/retry, cache invalidation, resource lifecycle, async concurrency)
- 16-item anti-pattern checklist
- 6 mental models (security engineer, performance engineer, team lead, systems architect, SRE, pattern detective)
- Quantitative 1-10 Code Quality Score per category (Security, Performance, Maintainability, Consistency, Resilience)
- References `defect-taxonomy` skill for CWE-mapped detection strategies

---

### `security-auditor`

Security auditor with attacker mindset specializing in vulnerability detection, CWE/OWASP mapping, and attack scenario construction.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Security audits, vulnerability assessment, OWASP/CWE compliance, threat modeling |

**Invocation:**
```
Use the security-auditor agent to audit [system/codebase]
```

**Expertise:**
- Input trust boundaries (injection, XSS, path traversal, command injection)
- Auth/authz (JWT, CSRF, privilege escalation)
- Secrets and cryptographic misuse
- API and header security
- Dependency vulnerabilities
- References `defect-taxonomy` skill for comprehensive CWE-mapped patterns

---

### `ui-race-auditor`

Framework-agnostic UI race condition analyst detecting timing bugs between async data loading, rendering, and event handlers.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | UI timing bugs, scroll races, focus races, stale closures, measurement races |

**Invocation:**
```
Use the ui-race-auditor agent to analyze [UI component/codebase]
```

---

### `distributed-flow-auditor`

Adversarial cross-service flow analyst for microservices, agent-based, and multi-module distributed systems. Traces request flows, API/message contracts, saga orchestration, timeout chains, and integration boundaries across multiple services or modules.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Cross-service analysis, distributed flow tracing, contract verification, multi-service code review |

**Invocation:**
```
Use the distributed-flow-auditor agent to analyze [multi-service system]
```

**Methodology:**
- 6-phase analysis: service topology discovery, contract extraction, cross-boundary flow tracing, timeout chain validation, resilience pattern audit, message ordering and delivery
- Hunts for contract mismatches, cascading timeout violations, missing idempotency, broken saga compensation, message ordering bugs, and split-brain risks
- Both sides of every boundary verified: producer `file:line` AND consumer `file:line`
- References `defect-taxonomy` skill for CWE-mapped detection strategies

---

### `chicken-egg-detector`

Detects chicken-and-egg problems, circular initialization dependencies, and bootstrap deadlocks across services, modules, and infrastructure. Traces startup ordering, init sequences, config bootstrapping, and migration dependencies.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Startup dependency analysis, circular initialization detection, bootstrap cycle auditing, service startup ordering review |

**Invocation:**
```
Use the chicken-egg-detector agent to analyze [system/infrastructure]
```

**Methodology:**
- 6-phase analysis: component inventory and init sequence discovery, dependency graph construction, bootstrap sequence analysis, temporal coupling detection, migration and schema dependency analysis, infrastructure dependency mapping
- Finds cases where component A requires B to be ready but B requires A -- creating deadlocks, flaky startups, or hidden temporal coupling
- Concrete evidence: every finding includes file:line references for both sides of the dependency cycle
- References `defect-taxonomy` skill for integration error patterns

---

## Skills

### `defect-taxonomy`

Comprehensive defect knowledge base with 16 macro-categories and 140+ subcategories of source code defects. Synthesizes MITRE CWE, OWASP Top 10, NASA Power of 10, IBM ODC, IEEE 1044, and Beizer's taxonomy.

**Reference files:**
- `concurrency-state.md` - Concurrency/parallelism + variable/state errors
- `logic-types.md` - Comparison/logic + type/conversion errors
- `memory-resources.md` - Memory management + error handling + performance
- `security.md` - Security vulnerabilities (14 subcategories)
- `distributed-integration.md` - API/contract + distributed systems + communication + integration
- `data-design-ops.md` - Data/persistence + design patterns + build/deploy + testing
- `detection-matrix.md` - Detection strategy matrix per category
- `review-frameworks.md` - Cognitive models, failure flow methodology, anti-patterns, scoring

---

## Commands

### `/full-review`

Multi-phase comprehensive code review with checkpoints and persistent sessions. 5 phases: Code Audit, Security & Performance, Testing & Documentation, Best Practices, Consolidated Report.

```
/full-review src/features/auth/ --security-focus
```

**Options:**
| Flag | Effect |
|------|--------|
| `--deep-dive` | Gather structural/semantic context first |
| `--security-focus` | Prioritize security analysis |
| `--performance-critical` | Deep performance review |
| `--strict-mode` | Strictest quality standards |
| `--framework react\|django` | Framework-specific checks |

---

### `/code-review`

Unified code review that auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. Fires code-auditor, security-auditor, and dead code agents in parallel.

```
/code-review                    # auto-detect: uncommitted changes or branch diff
/code-review 42                 # review PR #42
/code-review --commits 3        # review last 3 commits
/code-review --branch feature   # review branch diff
/code-review --auto-comment     # post findings as PR comments
```

---

### `/cleanup-dead-code`

Find and remove dead code. Auto-detects language: Knip for TypeScript/JavaScript, vulture + ruff for Python. Runs tests before and after to catch regressions.

```
/cleanup-dead-code src/ --dry-run
```

| Flag | Effect |
|------|--------|
| `--dry-run` | Report findings without modifying files |
| `--dependencies-only` | Only check unused dependencies |
| `--exports-only` | Only check unused exports |
| `--production` | Skip devDependencies |

**Safety:** Checks `git status` before starting. Reverts changes when tests fail. Asks for approval before removing Python functions/classes (high false-positive rate).

**Related:** Delegates to `typescript-development:knip` (TS/JS) and `python-development:python-dead-code` (Python) skills.

---

### `/pr-review`

Analyze current branch changes, generate a PR description with risk assessment and review checklist, and optionally create the PR via `gh`.

```
/pr-review --create
```

---

**Related:** [agent-teams](agent-teams.md) (`/team-review` and `/team-spawn security` use these agents) | [typescript-development](typescript-development.md) (Knip for dead code) | [python-development](python-development.md) (vulture/ruff for dead code)
