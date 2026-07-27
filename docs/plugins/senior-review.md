# Senior Review Plugin

> Catch bugs before they ship. Nine specialized agents review code quality, security, UI timing, distributed flows, startup cycles, cross-component logic integrity, formal API contracts, and codebase hygiene in parallel. A semantic interconnect mapper turns codebases into a shared contract/invariant map consumable by every reviewer. Backed by a comprehensive defect taxonomy knowledge base with 140+ defect patterns and CWE/OWASP mappings. `/team-review` runs all of it as a single pipeline, with an adversarial verification panel and a completeness critic as quality gates before the report ships.

## Agents

### `code-auditor`

Adversarial code quality auditor combining architecture review, failure flow tracing, pattern consistency analysis, and quantitative scoring.

| | |
|---|---|
| **Model** | `inherit` |
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
| **Model** | `inherit` |
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
| **Model** | `inherit` |
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
| **Model** | `inherit` |
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
| **Model** | `inherit` |
| **Use for** | Startup dependency analysis, circular initialization detection, bootstrap cycle auditing, service startup ordering review |

**Invocation:**
```
Use the chicken-egg-detector agent to analyze [system/infrastructure]
```

**Methodology:**
- 6-phase analysis: component inventory and init sequence discovery, dependency graph construction, bootstrap sequence analysis, temporal coupling detection, migration and schema dependency analysis, infrastructure dependency mapping
- Finds cases where component A requires B to be ready but B requires A - creating deadlocks, flaky startups, or hidden temporal coupling
- Concrete evidence: every finding includes file:line references for both sides of the dependency cycle
- References `defect-taxonomy` skill for integration error patterns

---

### `semantic-interconnect-mapper`

Phase 1b context-builder that produces a structured map of a codebase's contracts, invariants, domain rules, assumptions, integration hot-spots, and call graph. Output is consumed by every downstream reviewer (logic-integrity-auditor, code-auditor, security-auditor, distributed-flow-auditor, api-contract-auditor, chicken-egg-detector, ui-race-auditor) so they can find cross-component bugs instead of only local issues.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Grep, Glob |
| **Use for** | Pre-review context building when running `/senior-review:team-review` or `/map-codebase`; generating the `.team-review/02-interconnect.md` artifact that drives the logic-integrity and contract reviewers |

**Invocation:**
```
Used automatically by /senior-review:team-review Phase 1b (after deep-dive analysis) and by /map-codebase pipelines; rarely invoked directly
```

**Output sections:** `## Contracts` (formal + implicit), `## Invariants` (temporal + structural), `## Assumptions` (unverified), `## Domain Rules`, `## Integration Hot-Spots` (HTTP, queue, IPC, env/config), `## Call Graph`. Each section is self-contained so reviewers can Grep a single heading and get full context.

---

### `logic-integrity-auditor`

Adversarial reviewer that hunts for violations of contracts, invariants, assumptions, domain rules, ordering, idempotency, and state machines documented in the interconnect map. Catches bugs no local-only reviewer can see - logic drift across components, implicit contracts silently broken, terminal states mutated, retry paths double-committing.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | `/senior-review:team-review` Phase 2 (always-on in the review preset); logic/contract/invariant audit of code with an associated interconnect map |

**Invocation:**
```
Used automatically by /senior-review:team-review; requires .team-review/02-interconnect.md (produced by semantic-interconnect-mapper)
```

**Methodology:** Reads the interconnect map + target files, proves violations of documented contracts / invariants / domain rules / assumptions. Stops and reports if interconnect map is absent (precondition failure).

---

### `api-contract-auditor`

Adversarial auditor for formal API contracts - OpenAPI / Swagger, JSON Schema, GraphQL SDL, gRPC `.proto`, AsyncAPI for event schemas, TypeScript DTOs, Pydantic models. Hunts for contract-code drift, breaking changes hidden as minor version bumps, missing nullable markers, type mismatches between producer and consumer schemas, underspecified error responses.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Glob, Grep, Bash |
| **Use for** | Auditing OpenAPI/Swagger/GraphQL/gRPC specs for drift vs implementation; reviewing a PR that touches an API boundary; spec-first development audit; checking backwards compatibility before a release |

**Invocation:**
```
Use the api-contract-auditor agent to review [spec file or API boundary]
```

**Methodology:**
- 5-phase audit: contract inventory (find every spec artifact) -> contract-vs-implementation drift -> breaking-change detection (BREAKING / SAFE / AMBIGUOUS classification) -> consumer-side audit (hand-written + generated clients) -> cross-contract coherence
- Every finding cites producer `file:line` AND consumer `file:line`
- Handles OpenAPI 3.1, GraphQL SDL, gRPC, AsyncAPI, JSON Schema, Pydantic, TypeScript DTOs, Zod schemas
- Fulfills the `semantic-interconnect-mapper` `## Contracts` (formal) anchor

---

### `cleanup-auditor`

Adversarial codebase hygiene auditor. Detects dead code, orphan assets, generated artifacts tracked in VCS, phantom/unused dependencies, barrel-file bloat, eager-bundling anti-patterns, rebrand residue, and filesystem garbage. Report-only; the fix is delegated to `/cleanup-dead-code`.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Glob, Grep, Bash |
| **Use for** | Codebase cleanup review, technical-debt audit, dead-code detection with asset/VCS/dep coverage, monorepo dependency hygiene. Always-on dimension in `/senior-review:team-review`. |

**Invocation:**
```
Use the cleanup-auditor agent to scan [path]
```
Also spawned automatically by `/senior-review:team-review` as the "Codebase hygiene" dimension.

**Methodology:**
- 4-dimension detection pipeline: dead code (delegates to Knip / vulture / ruff), asset hygiene (orphan images, fonts, build artifacts), VCS hygiene (generated files tracked, .gitignore gaps), dependency hygiene (phantom / unused / version drift in monorepo workspaces)
- Every finding cites `file:line` or a concrete path; vague "consider cleaning up" advice is forbidden
- False-positive candidates (module augmentation, side-effect imports, DI-registered classes, framework-convention files) flagged in a separate section, never auto-confirmed
- Each finding ends with the exact `/cleanup-dead-code --phase=<phase>` command that would fix it

---

## Skills

### `defect-taxonomy`

Comprehensive defect knowledge base with 16 macro-categories and 140+ subcategories of source code defects. Synthesizes MITRE CWE, OWASP Top 10, NASA Power of 10, IBM ODC, IEEE 1044, and Beizer's taxonomy.

**Reference files:**
- `concurrency-state.md` - Concurrency/parallelism + variable/state errors
- `logic-types.md` - Comparison/logic + type/conversion errors
- `logic-integrity.md` - Cross-component logic invariants, contract drift, state machine integrity
- `memory-resources.md` - Memory management + error handling + performance
- `security.md` - Security vulnerabilities (14 subcategories)
- `distributed-integration.md` - API/contract + distributed systems + communication + integration
- `data-design-ops.md` - Data/persistence + design patterns + build/deploy + testing
- `detection-matrix.md` - Detection strategy matrix per category
- `review-frameworks.md` - Cognitive models, failure flow methodology, anti-patterns, scoring

---

### `review-quality-gates`

Quality gates for multi-reviewer code review pipelines: the context-sharing pattern that lets reviewers cite a shared interconnect map instead of re-reading code from scratch, the adversarial verification panel that re-judges every consolidated finding, and the completeness critic that reports what the review failed to cover. Consumed by `/senior-review:team-review` (Phases 1, 4b, 4c) and `/senior-review:code-review` (Steps 4b/4c).

**Context Sharing Pattern:** reviewers read `.deep-dive/` output plus `.team-review/02-interconnect.md` (contracts, invariants, domain rules, assumptions, integration hot-spots), guided by anchor routing per dimension (security reads Integration Hot-Spots plus unverified Assumptions; logic-integrity reads Contracts, Invariants, and Domain Rules; and so on). The **context utilization rate** (share of findings that cite a map anchor) is the quality signal: high at 30%+, medium at 10-30%, low below 10%. `logic-integrity-auditor` should sit above 70%, since its findings are almost entirely map-driven.

**Adversarial Verification Panel:** every finding above a 50% confidence floor is judged by 3 parallel lenses (Reachability/Correctness, False-Positive Causes, Severity Calibration). A finding survives if at least 2 of lenses 1-2 vote REAL, is discarded (`filtered`) if at least 2 vote FALSE_POSITIVE, and survives `contested` on a tie. Final severity comes from lens 3's vote. A cost guard (a finding-count proxy, not a token budget) narrows verification to Critical/High plus an uncertainty band once more than 25 findings survive dedup, unless `--rigorous` is passed; `--fast` skips the panel entirely.

**Completeness Critic:** one agent checks coverage against a fixed gap taxonomy (dimensions warranted but not run, in-scope files cited by no finding, unverified interconnect assumptions untouched by any finding, high-risk hot-spots with zero findings) and may trigger one bounded follow-up round for the single highest-risk gap it names.

**Reviewer Pipeline Conventions:** every Phase 2 reviewer carries a scope budget (stops after ~15 file reads without a finding), a no-findings protocol (a clean "examined X, Y, Z: no issues" report is valid, not a failure), and a `## Cross-Reviewer Notes` section for observations that belong to another dimension.

---

## Commands

### `/senior-review:team-review`

Multi-dimensional code review as a **4-phase pipeline**: context building first, so reviewers hunt cross-component logic bugs, not just what's visible from local inspection.

**Prerequisites:** requires the upstream `agent-teams` plugin (`wshobson/agents`, MIT) for the `agent-teams:multi-reviewer-patterns` and `agent-teams:team-communication-protocols` skills and the `agent-teams:team-reviewer` fallback agent:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

| | |
|---|---|
| **Invoke** | `/senior-review:team-review <target> [--reviewers auto\|security,performance,...] [--base-branch main] [--all] [--deep] [--skip-interconnect] [--fast] [--rigorous]` |
| **Artifact dir** | `.team-review/` (state, scope, interconnect map, per-dimension findings, consolidated report; preserved, not auto-deleted) |

**Pipeline:**

| Phase | What happens |
|-------|---------------|
| 0. Target resolution | Resolves `<target>` (path, git diff range, or PR number) and collects the diff |
| 0b. Context detection | Auto-selects review dimensions from changed files and codebase signals (skipped if `--reviewers` is explicit) |
| 1a. Deep-dive analysis | Invokes the `deep-dive-analysis:deep-dive-analysis` **skill** (`--depth=lite` by default, full with `--deep`) |
| 1b. Interconnect mapping | `semantic-interconnect-mapper` builds `.team-review/02-interconnect.md` |
| 2. Adversarial review | Spawns one teammate per dimension in parallel, each reading the deep-dive output plus the interconnect map |
| 3. Consolidation | Deduplicates findings, resolves severity conflicts, organizes by severity |
| 4b. Adversarial verification | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 4c. Completeness critic | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 5. Report & cleanup | Consolidated report with the context-utilization metric; team resources torn down |

**Always-on dimensions:** security, architecture, logic integrity (skipped under `--skip-interconnect`), codebase hygiene.

**Conditional dimensions** (auto-detected): UI races, React performance, general performance, platform compliance, distributed flows, circular dependencies, testing quality, API contracts, data migrations, and abstraction/reuse (`abstraction-architect:abstraction-architect` in diff mode, only when that plugin is installed and the target resolves to a diff that adds code).

```
/senior-review:team-review src/auth/                                # auto-detected dimensions
/senior-review:team-review main...HEAD --reviewers security,testing # explicit dimensions on a diff
/senior-review:team-review #42 --rigorous                           # PR review, verify every finding
/senior-review:team-review src/ --skip-interconnect                 # legacy parallel-only mode
```

`--skip-interconnect` reproduces the pre-pipeline behavior: no context phase, no `logic-integrity-auditor`, reviewers see only the target and diff. Use it for quick scans or targets under roughly 100 LOC.

---

### `/code-review`

Unified code review that auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. Fires code-auditor, security-auditor, and dead code agents in parallel.

When the diff adds code and the `abstraction-architect` plugin is installed, it also fires `abstraction-architect:abstraction-architect` in diff mode as an Abstraction & Reuse reviewer. That agent is the one that answers "was this already available?": it takes each added unit as an anchor and searches the rest of the codebase for prior art, reporting exact duplicates, near duplicates, and diffs that become the third occurrence of a shape (Rule of Three). `code-auditor` keeps the single-file abstraction smells; cross-file reuse findings belong to the abstraction reviewer.

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

**Related:** `/senior-review:team-review` uses these agents directly; the upstream agent-teams `/agent-teams:team-spawn security` (wshobson/agents) also draws on them | [typescript-development](typescript-development.md) (Knip for dead code) | [python-development](python-development.md) (vulture/ruff for dead code)
