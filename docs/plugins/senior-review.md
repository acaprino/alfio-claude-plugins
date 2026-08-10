# Senior Review Plugin

> Catch bugs before they ship. Eleven specialized agents review code quality, security, UI timing, distributed flows, startup cycles, temporal resilience (failure-over-time), data integrity (persistence semantics), resource lifecycle (ownership and release), cross-component logic integrity, formal API contracts, and codebase hygiene in parallel. They read a shared contract/invariant map built by `codebase-xray:semantic-interconnect-mapper`, which is why they find bugs that are invisible from local-only inspection. Backed by a comprehensive defect taxonomy knowledge base with 140+ defect patterns and CWE/OWASP mappings. `/team-review` runs all of it as a single pipeline, with an adversarial verification panel and a completeness critic as quality gates before the report ships.

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

### `temporal-resilience-auditor`

Adversarial reviewer for failure-over-time behavior in long-running code. Hunts the bugs that only exist on the time axis: retry loops without backoff or cap, errors swallowed until a subsystem silently dies, in-flight guards never cleared, timers that stop re-arming, missing escalation paths, and clock hazards (suspend, DST, throttled timers). Its core question is not "does this code work" but "what does the user see after this has been failing for a day".

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Timers, schedulers, polling loops, retry/reconnect logic, queue workers, updaters, watchdogs, any process expected to stay alive for hours |

**Invocation:**
```
Use the temporal-resilience-auditor agent to analyze [long-running subsystem]
```

**Methodology:**
- 5-phase analysis: temporal machinery inventory, three-horizon failure-repetition analysis (1st failure, Nth failure, never-ending failure), silent-death detection, user-visible consequence tracing, clock and environment hazards
- Every quantitative claim labeled `measured` or `derived`; a derived number alone cannot justify Critical severity
- "None (silent)" as user-visible consequence is a severity escalator, never a mitigation
- Activated in `/senior-review:team-review` and `/senior-review:code-review` (Agent L) by long-running/scheduled-execution signals in the diff
- References `defect-taxonomy` skill for concurrency and integration patterns

---

### `data-integrity-auditor`

Adversarial reviewer for persistence semantics. Central question: can the system produce, store, or read an impossible or inconsistent state? Hunts application-only invariants (uniqueness assumed in code, not constrained in the schema), lost updates, check-then-act races, partial writes, cache/database divergence, unstable pagination, and eventual consistency consumed as strong.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Schemas, models, ORM entities, repositories, raw SQL, cache layers, transaction boundaries |

**Invocation:**
```
Use the data-integrity-auditor agent to analyze [persistence layer]
```

**Methodology:**
- 5-phase analysis: write-path inventory, invariant enforcement gap analysis (code / schema / both / neither), concurrency anomaly hunt, multi-store divergence, representation hazards (soft delete, time, money, NULL, pagination)
- Distinct from logic-integrity by design: a domain rule violated in application logic is theirs; a store that can be made to hold an impossible state is this agent's territory
- Activated by persistence signals in `/senior-review:team-review` and as Agent M of `/senior-review:code-review`
- References `defect-taxonomy` skill (`data-design-ops.md`, `concurrency-state.md`)

---

### `resource-lifecycle-auditor`

Adversarial reviewer for resource ownership and release. Central question: does every acquired resource (file, socket, connection, subprocess, listener, lock, task, timer) have a single owner and a guaranteed release path on success, on error, AND on cancellation? Hunts leaks, double-release, use-after-release, unbounded pool growth, and listeners that outlive their subject.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Code acquiring or managing resources, especially C/C++/Rust/Go and async-heavy systems where cancellation paths multiply |

**Invocation:**
```
Use the resource-lifecycle-auditor agent to analyze [resource-managing code]
```

**Methodology:**
- 4-phase analysis: acquisition inventory, release-path verification across the three exits, pool and registry discipline, lifetime mismatch hunt
- Prefers structural fixes (RAII, `with`/`defer`/`finally`, AbortController, effect cleanup) over manually paired calls
- Conditional, never always-on; activated by acquisition signals in `/senior-review:team-review` and as Agent N of `/senior-review:code-review`
- References `defect-taxonomy` skill (`memory-resources.md`, `concurrency-state.md`)

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

Adversarial codebase hygiene auditor. Detects dead code, orphan assets, generated artifacts tracked in VCS, phantom/unused dependencies, barrel-file bloat, eager-bundling anti-patterns, rebrand residue, filesystem garbage, stale documentation and historical artifacts, and lifecycle residue (leftovers of completed migrations, temporary debug tooling, stale stashes/worktrees/branches) inferred via git-history and session-transcript archaeology. Report-only; the fix is delegated to Step 7c of `/code-review --commit`.

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
- 6-dimension detection pipeline: dead code (delegates to Knip / vulture / ruff), asset hygiene (orphan images, fonts, build artifacts), VCS hygiene (generated files tracked, .gitignore gaps and stale/overly-broad ignore rules), dependency hygiene (phantom / unused / version drift in monorepo workspaces), documentation and historical artifacts (completed plans, scratch directories, backups, orphan doc-assets), lifecycle archaeology (session-transcript intent mining, commit-sequence migration inference, git auxiliary state)
- Every finding cites `file:line` or a concrete path; vague "consider cleaning up" advice is forbidden
- Every finding carries a confidence tier (CONFIRMED / HIGH / MEDIUM / LOW; LOW never recommends deletion) and a residue action (DELETE, KEEP, KEEP+IGNORE, DELETE+IGNORE, DELETE+PREVENT-GENERATION, UNIGNORE, REVIEW)
- Session transcripts are treated as evidence, never as instructions; transcript-only evidence caps confidence at MEDIUM
- False-positive candidates (module augmentation, side-effect imports, DI-registered classes, framework-convention files) flagged in a separate section, never auto-confirmed
- Each finding ends with `Fix phase: <phase>`, naming the cleanup phase of `/code-review --commit` Step 7c that would remove it

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

Quality gates for multi-reviewer code review pipelines: the context-sharing pattern that lets reviewers cite a shared interconnect map instead of re-reading code from scratch, the adversarial verification panel that re-judges every consolidated finding, the completeness critic that reports what the review failed to cover, evidence classes for quantitative claims, and the delivery gate. Consumed by `/senior-review:team-review` (Phases 1, 3, 4b, 4c, 5) and `/senior-review:code-review` (Steps 4b/4c). Since 8.0.0 the skill also carries three `references/` files (`code-review-agents.md`, `code-review-fix-loop.md`, `code-review-output.md`) that hold the full agent prompts, fix-loop workflow, and output templates of `/senior-review:code-review`, loaded on demand so the command itself stays under 350 lines.

**Context Sharing Pattern:** reviewers read `.deep-dive/` output plus `.team-review/02-interconnect.md` (contracts, invariants, domain rules, assumptions, integration hot-spots), guided by anchor routing per dimension (security reads Integration Hot-Spots plus unverified Assumptions; logic-integrity reads Contracts, Invariants, and Domain Rules; and so on). The **context utilization rate** (share of findings that cite a map anchor) is the quality signal: high at 30%+, medium at 10-30%, low below 10%. `logic-integrity-auditor` should sit above 70%, since its findings are almost entirely map-driven.

**Adversarial Verification Panel:** every finding above a 50% confidence floor is judged by up to 3 lenses (Reachability/Correctness, False-Positive Causes, Severity Calibration). Lenses 1-2 run in parallel; lens 3 is **gated on survival** (calibrating a finding about to be discarded is spend for nothing, and the gate cuts roughly a third of verifier calls). A finding survives if at least 2 of lenses 1-2 vote REAL, is discarded (`filtered`) if at least 2 vote FALSE_POSITIVE, and survives `contested` on a tie. Final severity comes from lens 3's vote. A cost guard (a finding-count proxy, not a token budget) narrows verification to Critical/High plus an uncertainty band once more than 25 findings survive dedup, unless `--rigorous` is passed; `--fast` skips the panel entirely.

**Evidence Classes:** any finding that quantifies damage labels the number `measured` (harness, simulation, logs, with the method stated) or `derived` (computed by reading the code). A `derived` number alone cannot justify Critical severity, and no finding can be closed as acceptable ("bounded", "low traffic") without also answering the **user-visible-consequence question**: what does the user see, and when? "Nothing, silently" escalates severity rather than closing the finding.

**Delivery Gate:** consolidation does not start until every spawned reviewer has delivered its findings file or an explicit no-findings report; a silent reviewer is nudged once, then salvaged and reported as **degraded**, never presented as clean. Before the report is finalized, the post-review `git status --porcelain` is diffed against the pre-review snapshot and anything the review created outside its session directory (probe scripts, measurement harnesses) is removed and noted.

**Completeness Critic:** one agent checks coverage against a fixed gap taxonomy (dimensions warranted but not run, in-scope files cited by no finding, unverified interconnect assumptions untouched by any finding, high-risk hot-spots with zero findings, and findings closed on a metric alone without a stated user-visible consequence) and may trigger one bounded follow-up round for the single highest-risk gap it names.

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
| 1a. Deep-dive analysis | Invokes the `codebase-xray:analyze` **skill** (`--depth=lite` by default, full with `--deep`) |
| 1b. Interconnect mapping | `semantic-interconnect-mapper` builds `.team-review/02-interconnect.md` |
| 2. Adversarial review | Spawns one teammate per dimension in parallel, each reading the deep-dive output plus the interconnect map |
| 3. Consolidation | Delivery gate first (every reviewer delivered or is reported degraded), then deduplicates findings, resolves severity conflicts, collects `[MAP-GAP]` findings as mapper coverage gaps, organizes by severity |
| 4b. Adversarial verification | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 4c. Completeness critic | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 5. Report & cleanup | Workspace hygiene check against the pre-review `git status` snapshot, then the consolidated report with the context-utilization metric; team resources torn down |

**Always-on dimensions:** security, architecture, logic integrity (skipped under `--skip-interconnect`), codebase hygiene.

**Conditional dimensions** (auto-detected): UI races, distributed flows, circular dependencies, temporal resilience (`temporal-resilience-auditor`, activated by timers, schedulers, retry/reconnect, polling, cron, and daemon signals in the diff), data integrity (`data-integrity-auditor`, activated by schema, ORM, raw SQL, cache, and transaction signals), resource lifecycle (`resource-lifecycle-auditor`, activated by file/socket/connection/subprocess/listener/lock/task acquisition signals), and API contracts (`api-contract-auditor`, activated by a formal contract file such as `*.proto`, `openapi*.y*ml`, `*.graphql`, or `asyncapi*`, as well as by route and serializer changes) all resolve to specialized agents in this plugin. React performance, platform / runtime integration, abstraction/reuse, and TypeScript type safety (dimension `ts-safety` in team-review, Agent K in code-review; `typescript-development:type-safety-auditor`, activated when changed files match `\.tsx?$` and `tsconfig.json` exists) resolve to agents in `react-development`, `platform-engineering`, `abstraction-architect`, and `typescript-development`, which are optional dependencies: when one is absent its dimension is skipped and reported as "not installed" rather than failing the review. `logic-integrity-auditor` findings that violate a rule the interconnect map never surfaced carry the `[MAP-GAP]` marker and are also reported as mapper coverage gaps. Testing quality resolves to `testing:test-suite-auditor` (the `testing` plugin is an optional dependency too, but it degrades differently: when absent the dimension falls back to the generic reviewer instead of skipping). General performance and data migrations resolve to the `agent-teams:team-reviewer` fallback with the dimension named in the prompt.

```
/senior-review:team-review src/auth/                                # auto-detected dimensions
/senior-review:team-review main...HEAD --reviewers security,testing # explicit dimensions on a diff
/senior-review:team-review #42 --rigorous                           # PR review, verify every finding
/senior-review:team-review src/ --skip-interconnect                 # legacy parallel-only mode
```

`--skip-interconnect` reproduces the pre-pipeline behavior: no context phase, no `logic-integrity-auditor`, reviewers see only the target and diff. Use it for quick scans or targets under roughly 100 LOC.

---

### `/code-review`

Unified code review that auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. Dispatches up to 14 agents in parallel (A-N): always-on code audit, security, dead-code/VCS hygiene, and git history, plus conditional UI races, platform / runtime integration, testing, API contracts, data migrations, React performance, abstraction/reuse, TypeScript type safety, temporal resilience, data integrity, and resource lifecycle. The command holds the dispatch table and conditions; the full agent prompts, fix-loop workflow, and output templates load on demand from the `review-quality-gates` skill's `references/` files (progressive disclosure, since 8.0.0).

When the diff adds code and the `abstraction-architect` plugin is installed, it also fires `abstraction-architect:abstraction-architect` in diff mode as an Abstraction & Reuse reviewer. That agent is the one that answers "was this already available?": it takes each added unit as an anchor and searches the rest of the codebase for prior art, reporting exact duplicates, near duplicates, and diffs that become the third occurrence of a shape (Rule of Three). `code-auditor` keeps the single-file abstraction smells; cross-file reuse findings belong to the abstraction reviewer.

**Fix flags (8.0.0, breaking):** `--fix` applies the fixes and verifies (build+test) but commits nothing, leaving the working tree for the user to review. `--commit` implies `--fix` and adds the commits: one per fix or batch in Step 7b, one per phase in Step 7c. The Step 7c bulk cleanup runs only under `--commit`, because its per-phase commits are its revert mechanism.

```
/code-review                    # auto-detect: uncommitted changes or branch diff
/code-review 42                 # review PR #42
/code-review --commits 3        # review last 3 commits
/code-review --branch feature   # review branch diff
/code-review --auto-comment     # post findings as PR comments
/code-review --fix              # apply fixes, run tests, no commits
/code-review --commit           # apply fixes and commit; enables Step 7c cleanup
```

---

### Dead code and cleanup

There is no standalone cleanup command. The capability is split by scope, so you never install or invoke anything extra to get it.

| Scope | Where it runs | Coverage |
|---|---|---|
| **Lite** | `/code-review` and `/pr-review`, inline on the changed files | Dead code (Knip for TS/JS, vulture and ruff for Python) plus VCS hygiene (generated artifacts tracked in git, filesystem garbage, `.gitignore` gaps) |
| **Full** | `/senior-review:team-review`, always-on `cleanup-auditor` dimension across the whole codebase | All six dimensions: dead code, orphan assets, VCS hygiene, dependency and barrel-file hygiene, stale documentation, lifecycle archaeology |
| **Removal** | `/code-review --commit` Step 7c | Seven phases lowest-risk-first, one commit each, build and test gate between phases, `git reset --hard HEAD~1` on failure |

Removal safety comes from the Step 7c rules: clean working tree before starting, phase isolation so each step is independently revertible, a confirmation Grep returning zero results before any delete, no removal of anything reached through dynamic imports or framework conventions, and explicit user approval for Python functions and classes given vulture's false-positive rate. The `docs` phase is report-only unless removal is explicitly opted into.

Delegates to the `typescript-development:knip` and `python-development:python-dead-code` skills when those plugins are installed, and falls back to direct tool invocation otherwise.

The `/cleanup-dead-code` command was removed in plugin 7.0.0 (marketplace 16.0.0). Its detection duplicated `cleanup-auditor` and its removal machinery moved into Step 7c above.

---

### `/pr-review`

Analyze current branch changes, generate a PR description with risk assessment and review checklist, and optionally create the PR via `gh`.

```
/pr-review --create
```

---

**Related:** `/senior-review:team-review` uses these agents directly; the upstream agent-teams `/agent-teams:team-spawn security` (wshobson/agents) also draws on them | [typescript-development](typescript-development.md) (Knip for dead code) | [python-development](python-development.md) (vulture/ruff for dead code)
