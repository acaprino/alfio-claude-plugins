---
description: >
  "[DEPRECATED -- prefer /agent-teams:team-review] Legacy orchestrator for multi-dimensional code review with deep-dive structural and semantic analysis, multi-service distributed flow analysis, and resilience pattern auditing. Kept for backward compatibility; new work should use /agent-teams:team-review which provides the same phased pipeline with better parallelism and context sharing." argument-hint: "<target path(s) or description> [--skip-deep-dive] [--distributed] [--security-focus] [--performance-critical] [--strict-mode] [--framework react|spring|django|rails]".
  TRIGGER WHEN: the user explicitly invokes /senior-review:full-review.
  DO NOT TRIGGER WHEN: the user asks for a generic code review, multi-dimensional audit, or uses /team-review -- prefer /agent-teams:team-review.
deprecated: true
---

# Comprehensive Code Review Orchestrator (DEPRECATED)

> **Deprecation notice.** This command is superseded by `/agent-teams:team-review`, which runs the same kind of phased pipeline (deep-dive -> interconnect map -> parallel reviewers -> consolidation) through the agent-teams orchestration layer and adds a `logic-integrity-auditor` dimension that hunts contract / invariant / domain-rule violations surfaced by the interconnect map. `/senior-review:full-review` remains available for one release for backward compatibility and will be removed in a future iteration. The underlying specialist agents (`senior-review:security-auditor`, `senior-review:code-auditor`, `senior-review:ui-race-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:chicken-egg-detector`) are **not** deprecated -- they are invoked directly by `/agent-teams:team-review`.
>
> Migration: replace `/senior-review:full-review <target>` with `/agent-teams:team-review <target>`. Flags `--security-focus`, `--performance-critical`, and `--framework` have no direct analog; use `--reviewers` with an explicit dimension list instead. Flag `--skip-deep-dive` maps to `--skip-interconnect` in the new command.

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `$SESSION_DIR/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Checkpoints are informational.** When you reach a `PHASE CHECKPOINT`, display the summary and continue automatically. Only stop for user approval if `--strict-mode` is set AND there are Critical findings.
4. **Halt on failure.** If any step fails (agent error, missing files, access issues), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Use only local agents.** All `subagent_type` references use agents bundled with this plugin or `general-purpose`. No cross-plugin dependencies.
6. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.
7. **Use session directory for all paths.** Every reference to `.full-review/` in this command means `$SESSION_DIR` -- the session-specific directory determined during pre-flight (e.g., `.full-review-auth/`). Do NOT use a bare `.full-review/` directory.

## Pre-flight Checks

Before starting, perform these checks:

### 1. Check for existing sessions

Scan for directories matching `.full-review-*/state.json` in the project root.

- If one or more sessions have `status: "in_progress"`:
  List all sessions with their target, phase, and started_at, then ask:

  ```
  Found existing review session(s):

  [#] .full-review-<label>/ -- Target: [target] -- Phase [N] -- Started [date]
  ...

  1. Resume session [label] (repeat for each in-progress session)
  N. Start a new session
  ```

- If sessions exist but all are `"complete"`: proceed to starting a new session.
- If no `.full-review-*` directories exist: proceed to starting a new session.

### 2. Determine session directory

Derive a short label from the review target:
- Path targets: use the final meaningful segment (e.g., `src/auth` -> `auth`, `./lib/database.ts` -> `database`)
- Description targets: extract the primary noun (e.g., "recent payment changes" -> `payments`)
- Fallback: `YYYYMMDD-HHmm` timestamp
- Kebab-case, lowercase, no file extensions
- If `.full-review-<label>/` already exists, append `-2`, `-3`, etc.

Set `$SESSION_DIR` = `.full-review-<label>/` for all subsequent operations.

### 3. Initialize state

Create `$SESSION_DIR` directory and `state.json`:

```json
{
  "session_dir": ".full-review-<label>",
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "skip_deep_dive": false,
    "security_focus": false,
    "performance_critical": false,
    "strict_mode": false,
    "distributed": false,
    "framework": null
  },
  "current_step": 1,
  "current_phase": 0,
  "completed_steps": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--skip-deep-dive`, `--security-focus`, `--performance-critical`, `--strict-mode`, `--distributed`, and `--framework` flags. Update the flags object accordingly.

Multiple target paths are supported (e.g., `/full-review services/payment services/order`). Store all paths in a `"targets"` array in `state.json`. If a single directory is given with `--distributed`, auto-discover sub-services within it (look for nested `package.json`, `go.mod`, `pom.xml`, `pyproject.toml`, `Dockerfile` at depth 2+).

### 4. Identify review target

Determine what code to review from `$ARGUMENTS`:

- If a file/directory path is given, verify it exists
- If a description is given (e.g., "recent changes", "authentication module"), identify the relevant files
- List the files that will be reviewed and confirm with the user

**Output file:** `.full-review/00-scope.md`

```markdown
# Review Scope

## Target

[Description of what is being reviewed]

## Files

[List of files/directories included in the review]

## Flags

- Skip Deep Dive: [yes/no]
- Security Focus: [yes/no]
- Performance Critical: [yes/no]
- Strict Mode: [yes/no]
- Distributed: [yes/no/auto-detected]
- Framework: [name or auto-detected]

## Review Phases

0. Deep Dive Context Gathering (structural + semantic analysis)
1. Code Audit (Architecture + Failure Flow + Pattern Analysis)
2. Security, Performance & Specialized Reviews
   - 2A: Security Vulnerability Assessment
   - 2B: Performance & Scalability Analysis
   - 2C: UI Race Condition Analysis (if UI files in scope)
   - 2D: Distributed Flow Analysis (if multi-service)
   - 2E: React Performance Review (if React files in scope)
3. Testing & Documentation
4. Best Practices, CI/CD & Dead Code
5. Quality Scoring (calibrated with all prior findings)
6. Consolidated Report
```

### 5. Distributed system auto-detection

After identifying files, check whether the target is a multi-service system. **Skip if `--distributed` flag is already set.**

**Auto-detection criteria (2+ of these = distributed system):**
1. 2+ independent build roots (`package.json`/`go.mod`/`pom.xml`/`pyproject.toml`) at different directory levels within scope
2. `docker-compose.yml` with 2+ service definitions
3. Grep finds HTTP client calls with URLs referencing other service names, or message broker publish/subscribe patterns
4. Kubernetes manifests with 2+ `Deployment` or `Service` kind definitions
5. 2+ `.proto` files or OpenAPI specs in different directories

When auto-detected, ask the user:

```
Detected multi-service architecture:
- [service-a] ([language])
- [service-b] ([language])
...

1. Include distributed flow analysis (recommended)
2. Skip distributed flow analysis (single-service focus)
```

If confirmed, set `distributed: true` in `state.json` and add a `## Services` section to `00-scope.md` listing each service with its path and detected language/framework.

### 6. Fullstack app auto-detection

Check if the target is a fullstack application by looking for **2+ of these signals**:

1. `package.json` with frontend framework (react, vue, svelte, angular, next, nuxt)
2. Backend framework config (`pyproject.toml` with fastapi/django/flask, `package.json` with express/nest/hono, `Cargo.toml` with actix/axum)
3. API route definitions (files matching `*/routes/*`, `*/api/*`, `*/endpoints/*`)
4. Tauri config (`tauri.conf.json`, `Cargo.toml` with tauri)
5. Electron config (`electron-builder.yml`, main process with `BrowserWindow`)
6. Mobile config (`android/`, `ios/`, `capacitor.config.ts`, react-native)
7. `docker-compose.yml` with services

If 2+ signals found, set `fullstack_app: true` in `state.json` and add a `## Platforms Detected` section to `00-scope.md` listing detected platforms (SPA, PWA, Mobile, Electron, Tauri). Include Step 2F in Phase 2.

Update `state.json`: add `"00-scope.md"` to `files_created`, add step 0 to `completed_steps`.

---

## Phase 0: Deep Dive Context Gathering

**Skip this phase entirely if `--skip-deep-dive` flag is set.** If skipped, proceed directly to Phase 1.

Run deep-dive analysis on the target path to gather structural and semantic context that strengthens all subsequent review phases.

**Agent tool parameters (use ONLY these):** `description` (required), `prompt` (required), `subagent_type`, `run_in_background`, `model`, `isolation`, `resume`. Do NOT pass any other parameters -- the Agent tool rejects unknown fields.

Spawn 3 agents in parallel using the Agent tool:

### Agent A: Structure + Interfaces

```
Agent tool call:
  - description: "Deep dive structure and interfaces for review context"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Analyze the target code and produce two output files.

    ## Target
    [Insert target path from 00-scope.md]

    ## Phase 1: Structure Extraction
    Scan all files and build a structural map. For each file extract:
    - Module/file name and path
    - Language and framework
    - Imports and dependencies
    - Exported symbols (functions, classes, constants)
    - File size and complexity indicators

    Write to `.full-review/dd-01-structure.md`

    ## Phase 2: Interface Analysis
    For each module, document the public interface:
    - Function signatures with parameter types and return types
    - Class hierarchies and method signatures
    - API endpoints with request/response shapes
    - Configuration interfaces and event contracts

    Write to `.full-review/dd-02-interfaces.md`
```

### Agent B: Flows + Semantics

```
Agent tool call:
  - description: "Deep dive flows and semantics for review context"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Analyze the target code and produce two output files.

    ## Target
    [Insert target path from 00-scope.md]

    ## Phase 3: Flow Tracing
    Trace critical execution paths:
    - Request lifecycle (entry -> middleware -> processing -> response)
    - Data transformation pipelines
    - Error propagation paths and recovery mechanisms
    - State mutation flows and side effects
    - Authentication/authorization flow
    - Background job and queue processing flows

    Write to `.full-review/dd-03-flows.md`

    ## Phase 4: Semantic Understanding
    Understand the WHY behind the code:
    - Business purpose of each module
    - Design decisions and trade-offs
    - Assumptions embedded in the code
    - Implicit contracts not documented anywhere
    - Domain model and bounded contexts

    Write to `.full-review/dd-04-semantics.md`
```

### Agent C: Risks

```
Agent tool call:
  - description: "Deep dive risk detection for review context"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Analyze the target code for risks and anti-patterns.

    ## Target
    [Insert target path from 00-scope.md]

    ## Phase 5: Pattern & Risk Detection
    Scan for:
    - Anti-patterns: god objects, spaghetti code, shotgun surgery, feature envy, primitive obsession
    - Red flags: swallowed exceptions, hardcoded credentials, race conditions, N+1 queries, unbounded loops
    - Technical debt: TODO/FIXME comments, deprecated APIs, outdated patterns, dead code
    - Failure modes: what breaks under load, edge cases, missing error handling, cascading failures
    - Dependency risks: outdated packages, known CVEs, unnecessary dependencies, version pinning issues

    For each finding, provide:
    - Location (file + line)
    - Severity (Critical/High/Medium/Low)
    - Impact description
    - Recommended fix

    Write to `.full-review/dd-05-risks.md`
```

After all 3 agents complete, produce `.full-review/00-deep-dive-context.md` summarizing key findings from all 5 deep-dive files. This summary will be injected into subsequent review agent prompts.

Update `state.json`: add `"phase_0"` to `completed_steps`.

---

## PHASE CHECKPOINT 0 (if deep dive was run)

Display a brief summary of deep dive findings, then continue automatically to Phase 1.

```
Phase 0 complete: Deep dive analysis done.
- Files analyzed: [count] -- Risks detected: [X critical, Y high, Z medium]
- Output: $SESSION_DIR/00-deep-dive-context.md
```

Continue to Phase 1 immediately.

---

## Deep Dive Context Injection

When deep dive was performed (not skipped), each review agent prompt in Phases 1-5 gets this additional section inserted after the existing context sections:

```
## Deep Dive Context

[Insert relevant deep-dive findings from .full-review/00-deep-dive-context.md:
- For code-auditor (Phase 1): structure, interfaces, flows, semantics, risks
- For security-auditor (Phase 2A): flows (data paths), semantics (assumptions), risks
- For performance agent (Phase 2B): structure, flows
- For ui-race-auditor (Phase 2C): structure (component hierarchy), flows (render/layout/event timing), semantics (state management assumptions)
- For test/docs agents (Phase 3): interfaces, flows, risks
- For distributed-flow-auditor (Phase 2D): structure (service boundaries), flows (cross-service calls), semantics (business transaction assumptions)
- For best practices agents (Phase 4): all deep-dive findings
- For quality scoring (Phase 5): all deep-dive findings]

Use this context to strengthen your analysis. Do NOT re-report findings already
covered in the deep dive -- instead focus on new issues the deep dive missed or
issues that become apparent when combining deep-dive context with your
specialized perspective.
```

---

## Phase 1: Code Audit (Step 1A)

### Step 1A: Architecture, Failure Flow & Pattern Analysis

```
Agent tool call:
  - description: "Code audit for $ARGUMENTS"
  - subagent_type: "senior-review:code-auditor"
  - prompt: |
    Perform a comprehensive code audit of the target code covering architecture, failure flow
    analysis, and pattern consistency.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Instructions
    Analyze across all dimensions:

    **Architecture & Design:**
    1. Component boundaries -- separation of concerns, module cohesion
    2. Dependency management -- circular deps, inappropriate coupling, direction
    3. API design -- endpoints, schemas, error contracts, versioning
    4. Data model -- schema design, relationships, access patterns
    5. Design patterns -- appropriate use, missing abstractions, over-engineering
    6. Architectural consistency -- does code follow established patterns?

    **Failure Flow Analysis:**
    7. Resource lifecycle -- DB connections, file handles, temp files cleaned up on error paths?
    8. Persisted state validity -- validity keys for caches/state files? Stale data risk on resume?
    9. Kill point analysis -- simulate termination at each await. What state is left?
    10. Cache invalidation -- stale-fresh result mixing risk?
    11. Concurrency under failure -- sibling task behavior on failure, committed side effects?
    12. Resume/retry correctness -- what assumptions does resume make? What if violated?

    **Pattern Consistency:**
    13. Dominant patterns per file, flag deviations in the target code
    14. Run 16-item anti-pattern checklist
    15. Consistency anti-patterns (mixed error handling, inline constructs bypassing patterns)

    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100), fix.

    Write your findings as a structured markdown document.
```

### Large Change Set Handling

Before launching review agents, check the scope size. If the target contains more than 500 lines of code across all files, batch the files into groups of 3-5 files per agent invocation. Run batches sequentially, then consolidate findings before writing the phase output file.

After completing, write to `.full-review/01-code-audit.md`:

```markdown
# Phase 1: Code Audit

## Architecture Findings

[Organized by severity]

## Failure Flow & Resilience Findings

[Kill points, persisted state, cache invalidation, resource lifecycle]

## Pattern Consistency Findings

[Pattern deviations, anti-patterns]

## Critical Issues for Phase 2 Context

[List any findings that should inform security or performance review]
```

### Machine-Readable Summary for Downstream Agents

At the end of `.full-review/01-code-audit.md`, include a structured block for efficient agent-to-agent communication:

```xml
<machine_summary>
[
  {"severity": "CRITICAL|HIGH|MEDIUM|LOW", "type": "category", "file": "path", "line": N, "description": "brief finding"},
  ...
]
</machine_summary>
```

Update `state.json`: set `current_step` to 2, `current_phase` to 2, add step 1A to `completed_steps`.

---

## PHASE CHECKPOINT 1

Display a brief summary of findings from Phase 1, then continue automatically to Phase 2.

```
Phase 1 complete: Code Audit done.
- Architecture: [X critical, Y high, Z medium] -- Failure Flow: [X critical, Y high, Z medium] -- Patterns: [X deviations]
- Output: $SESSION_DIR/01-code-audit.md
```

If `--strict-mode` is set AND there are Critical findings, stop and ask the user whether to fix critical issues first or continue. Otherwise, continue to Phase 2 immediately.

---

## Phase 2: Security & Performance Review (Steps 2A-2E)

Read `.full-review/01-code-audit.md` for context from Phase 1.

Run all agents in parallel using multiple Agent tool calls in a single response (Steps 2C, 2D, 2E only when applicable).

### Step 2A: Security Vulnerability Assessment

```
Agent tool call:
  - description: "Security audit for $ARGUMENTS"
  - subagent_type: "senior-review:security-auditor"
  - run_in_background: true
  - prompt: |
    Execute a comprehensive security audit on the target code.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Phase 1 Context
    [Insert contents of .full-review/01-code-audit.md -- focus on the "Critical Issues for Phase 2 Context" section]

    ## Instructions
    Analyze for:
    1. **OWASP Top 10**: Injection, broken auth, sensitive data exposure, XXE, broken access control, misconfig, XSS, insecure deserialization, vulnerable components, insufficient logging
    2. **Input validation**: Missing sanitization, unvalidated redirects, path traversal
    3. **Authentication/authorization**: Flawed auth logic, privilege escalation, session management
    4. **Cryptographic issues**: Weak algorithms, hardcoded secrets, improper key management
    5. **Dependency vulnerabilities**: Known CVEs in dependencies, outdated packages
    6. **Configuration security**: Debug mode, verbose errors, permissive CORS, missing security headers

    For each finding, provide:
    - Severity (Critical / High / Medium / Low) with CVSS score if applicable
    - CWE reference where applicable
    - File and line location
    - Proof of concept or attack scenario
    - Specific remediation steps with code example

    Write your findings as a structured markdown document.
```

### Step 2B: Performance & Scalability Analysis

```
Agent tool call:
  - description: "Performance analysis for $ARGUMENTS"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    You are a performance engineer. Conduct a performance and scalability analysis of the target code.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Phase 1 Context
    [Insert contents of .full-review/01-code-audit.md -- focus on the "Critical Issues for Phase 2 Context" section]

    ## Instructions
    Analyze for:
    1. **Database performance**: N+1 queries, missing indexes, unoptimized queries, connection pool sizing
    2. **Memory management**: Memory leaks, unbounded collections, large object allocation
    3. **Caching opportunities**: Missing caching, stale cache risks, cache invalidation issues
    4. **I/O bottlenecks**: Synchronous blocking calls, missing pagination, large payloads
    5. **Concurrency issues**: Race conditions, deadlocks, thread safety
    6. **Frontend performance**: Bundle size, render performance, unnecessary re-renders, missing lazy loading
    7. **Scalability concerns**: Horizontal scaling barriers, stateful components, single points of failure

    For each finding, provide:
    - Severity (Critical / High / Medium / Low)
    - Estimated performance impact
    - Specific optimization recommendation with code example

    Write your findings as a structured markdown document.
```

### Step 2C: UI Race Condition Analysis (conditional)

**Only run this agent if the target includes UI/frontend code** (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, `.qml`, or files containing scroll/focus/layout manipulation). Skip entirely for backend-only codebases.

```
Agent tool call:
  - description: "UI race condition analysis for $ARGUMENTS"
  - subagent_type: "senior-review:ui-race-auditor"
  - run_in_background: true
  - prompt: |
    Analyze the target UI code for race conditions between async rendering,
    layout/reflow, and event handlers.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Phase 1 Context
    [Insert contents of .full-review/01-code-audit.md -- focus on state management and component interaction findings]

    ## Instructions
    Analyze the target code for UI timing bugs:

    1. **Async-Render-Event Triangle** -- Map data sources that trigger re-renders,
       layout-dependent operations (scroll, focus, measurement), and event handlers
       that read layout state. Identify where these three interact.

    2. **Scroll Race Analysis** -- For every scrollIntoView, scrollTop assignment,
       or scrollToIndex call: is the layout complete when it fires? Can reflow after
       the call shift scrollTop and trigger false "user scrolled" detection?

    3. **Batch Render Timing** -- For bulk state updates (history restore, list load,
       large dataset): do effects/callbacks that depend on layout fire before or
       after all items are rendered and measured?

    4. **Stale Closure Audit** -- Do event handlers, timers, or observers capture
       DOM references or layout values that can go stale between capture and use?

    5. **Programmatic vs User Event Discrimination** -- Do scroll/focus/resize
       handlers distinguish between programmatic manipulation and genuine user
       interaction? Missing guards cause false state transitions.

    6. **Cross-Component Layout Coupling** -- Does component A resize/reflow and
       affect component B's scroll position, measurements, or visibility without
       B being notified?

    For each finding: severity, step-by-step timeline (T0->T1->...->RESULT),
    file + line, confidence (0-100), concrete fix.

    Write your findings as a structured markdown document.
```

### Step 2D: Distributed Flow Analysis (conditional)

**Only run this agent if the review targets multiple services/paths OR the `--distributed` flag is set OR auto-detection identified multi-service architecture.** Skip entirely for single-module monoliths.

```
Agent tool call:
  - description: "Distributed flow analysis for $ARGUMENTS"
  - subagent_type: "senior-review:distributed-flow-auditor"
  - run_in_background: true
  - prompt: |
    Analyze cross-service flows, contracts, and integration patterns
    across the target services.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md -- includes all service paths and detected services]

    ## Phase 1 Context
    [Insert contents of .full-review/01-code-audit.md -- focus on architecture and boundary findings]

    ## Instructions
    Analyze all cross-boundary interactions between the services in scope:
    1. Build service topology map from file-system heuristics
    2. Extract and compare contracts on both sides (API, message, shared DB)
    3. Trace end-to-end flows through the call chain
    4. Validate timeout chains (inner < outer rule)
    5. Audit resilience patterns (idempotency, circuit breakers, retries, sagas)
    6. Check message ordering and delivery guarantees

    Write your findings as a structured markdown document.
```

### Step 2E: React Performance Review (conditional)

**Only run this agent if the target includes React files** (`.tsx`, `.jsx`, or `package.json` listing `react` as a dependency). Skip entirely for non-React codebases.

```
Agent tool call:
  - description: "React performance review for $ARGUMENTS"
  - subagent_type: "react-development:react-performance-optimizer"
  - run_in_background: true
  - prompt: |
    Audit the React performance, state management, and bundle optimization of the target code.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Phase 1 Context
    [Insert contents of .full-review/01-code-audit.md -- focus on component interaction and state management findings]

    ## Instructions
    Evaluate:
    1. **External store selector audit (CRITICAL)**: Selectors returning objects/arrays without `useShallow`, selectors with `.filter()`/`.map()`/`.reduce()` creating new references, `useStore()` with no selector
    2. **React Compiler readiness**: Is `babel-plugin-react-compiler` configured? Identify patterns the compiler can vs cannot auto-optimize
    3. **useEffect/useCallback infinite loop detection**: Callbacks that update state listed in their own deps, called from effects depending on the callback
    4. **Stale closure detection**: State/props captured in `useEffect(..., [])` closures without ref indirection
    5. **useEffect cleanup audit**: Missing AbortController, unclosed WebSocket/Channel, missing clearInterval/removeEventListener
    6. **React 19 API adoption**: use(), useOptimistic(), useDeferredValue(), useFormStatus(), useActionState()
    7. **State management patterns**: Zustand/Jotai/Redux selector patterns, prop drilling, state duplication, useEffect chains
    8. **Bundle optimization**: Heavy imports, missing code splitting, lazy loading opportunities, tree-shaking blockers
    9. **Virtualization**: Large lists/tables not using TanStack Virtual or similar
    10. **Re-render prevention**: Children as props pattern, component splitting for isolation

    For each finding: severity (Critical/High/Medium/Low), file + line, issue description, specific fix with code example.
    Note what's done well.

    Write your findings as a structured markdown document.
```

### Step 2F: Platform Engineering Review (conditional)

**Only run this agent if fullstack app signals were detected** (2+ signals from pre-flight auto-detection, `fullstack_app: true` in state.json). Skip entirely for libraries, CLI tools, or single-layer projects.

```
Agent tool call:
  - description: "Platform engineering review for $ARGUMENTS"
  - subagent_type: "platform-engineering:platform-reviewer"
  - run_in_background: true
  - prompt: |
    Conduct a comprehensive platform engineering review of the target code
    against the platform-engineering rulebook.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md -- includes detected platforms]

    ## Phase 1 Context
    [Insert contents of .full-review/01-code-audit.md -- focus on architecture and security findings]

    ## Instructions
    Execute the full 4-phase platform engineering review:

    1. **Platform Context Detection**: Identify target platforms from package.json,
       manifest files, build configs. Set platform flags (SPA, PWA, Mobile, Electron, Tauri).

    2. **Security Audit**: Server validation (client-only business logic), auth token
       storage (JWTs in localStorage, missing httpOnly/Secure/SameSite), API security
       (auth, rate limiting, CORS), XSS/CSP (weak CSP, dangerouslySetInnerHTML),
       secrets in bundles (REACT_APP_/VITE_/NEXT_PUBLIC_), platform-specific security
       (Electron nodeIntegration, Tauri permissions, mobile cert pinning, PWA cache).

    3. **Architecture Audit**: Client-server boundary (business logic placement),
       API design (versioning, pagination, RFC 7807 errors), offline-first readiness,
       infrastructure (monolith vs microservices, CI/CD, feature flags).

    4. **Performance Audit**: Bundle size budgets (<170KB web, <20MB APK, <10MB Tauri),
       image optimization, Core Web Vitals (LCP/INP/CLS), API/DB performance (N+1,
       pooling, indexes), mobile performance (push vs poll, memory leaks), rendering
       strategy (CSR/SSR/SSG/ISR), caching strategy.

    For each finding: severity (MUST violation / DO recommendation / DON'T warning),
    file + line, real-world incident reference if applicable, concrete fix with code example.

    Write your findings as a structured markdown document with verdict
    (PASS / PASS WITH WARNINGS / FAIL).
```

After all agents complete, consolidate into `.full-review/02-security-performance.md`:

```markdown
# Phase 2: Security & Performance Review

## Security Findings

[Summary from 2A, organized by severity]

## Performance Findings

[Summary from 2B, organized by severity]

## UI Race Condition Findings (if applicable)

[Summary from 2C, organized by severity, or "N/A -- no UI files in scope"]

## Distributed Flow Findings (if applicable)

[Summary from 2D, organized by severity, or "N/A -- single-module scope"]

## React Performance Findings (if applicable)

[Summary from 2E, organized by severity, or "N/A -- no React files in scope"]

## Platform Engineering Findings (if applicable)

[Summary from 2F, organized by MUST/DO/DON'T severity, or "N/A -- not a fullstack app"]

## Critical Issues for Phase 3 Context

[List findings that affect testing or documentation requirements]
```

Include `<machine_summary>` blocks at the end of `.full-review/02-security-performance.md` (same format as Phase 1).

Update `state.json`: set `current_step` to "checkpoint-2", add steps 2A-2E to `completed_steps`.

---

## PHASE CHECKPOINT 2

Display a brief summary of findings from Phase 2, then continue automatically to Phase 3.

```
Phase 2 complete: Security & Performance done.
- Security: [X critical, Y high, Z medium] -- Performance: [X critical, Y high, Z medium]
- Specialized: UI Race [X or N/A], Distributed [X or N/A], React Perf [X or N/A]
- Output: $SESSION_DIR/02-security-performance.md
```

If `--strict-mode` is set AND there are Critical findings, stop and ask the user whether to fix critical issues first or continue. Otherwise, continue to Phase 3 immediately.

---

## Phase 3: Testing & Documentation Review (Steps 3A-3B)

Read `.full-review/01-code-audit.md` and `.full-review/02-security-performance.md` for context.

Run both agents in parallel using multiple Agent tool calls in a single response.

### Step 3A: Test Coverage & Quality Analysis

```
Agent tool call:
  - description: "Test coverage analysis for $ARGUMENTS"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    You are a test automation engineer. Evaluate the testing strategy and coverage for the target code.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Prior Phase Context
    [Insert security and performance findings from .full-review/02-security-performance.md that affect testing requirements]

    ## Instructions
    Analyze:
    1. **Test coverage**: Which code paths have tests? Which critical paths are untested?
    2. **Test quality**: Are tests testing behavior or implementation? Assertion quality?
    3. **Test pyramid adherence**: Unit vs integration vs E2E test ratio
    4. **Edge cases**: Are boundary conditions, error paths, and concurrent scenarios tested?
    5. **Test maintainability**: Test isolation, mock usage, flaky test indicators
    6. **Security test gaps**: Are security-critical paths tested? Auth, input validation, etc.
    7. **Performance test gaps**: Are performance-critical paths tested? Load testing?
    8. **Integration gaps**: Are interface contracts validated by tests?
    9. **Test infrastructure design** (Python/pytest): Are heavy dependency mocks (ortools, scipy, prometheus_client, ML libs) centralized in root `tests/conftest.py`? Are there mocks in sub-directory conftest files that should be lifted to root? Root conftest runs first -- sub-conftest is too late if root-level tests trigger collection-time imports.
    10. **Mock correctness**: Do `monkeypatch.setattr`/`patch` targets resolve to actual module-level attributes? Are lazy-imported functions (imported inside other functions) patched at their DEFINITION site, not usage site? Do mock return values match real API signatures?
    11. **Test marker discipline**: Do tests requiring real heavy dependencies have `@pytest.mark.slow` or `@pytest.mark.e2e`? Are default `addopts` configured to exclude heavy tests from fast runs (`-m 'not slow and not e2e'`)?
    12. **External service mock coverage**: Are ALL external services (DB, auth, cloud storage, email, payment, cloud APIs) mocked in integration conftest? Unmocked services cause hangs via credential lookups (google.auth.default, subprocess gcloud) or real API calls. Run `ruff check` on test files to catch import issues.

    For each finding, provide:
    - Severity (Critical / High / Medium / Low)
    - What is untested or poorly tested
    - Specific test recommendations with example test code

    Write your findings as a structured markdown document.
```

### Step 3B: Documentation & API Review

```
Agent tool call:
  - description: "Documentation review for $ARGUMENTS"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    You are a technical documentation architect. Review documentation completeness and accuracy.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Prior Phase Context
    [Insert key findings from .full-review/01-code-audit.md and .full-review/02-security-performance.md]

    ## Instructions
    Evaluate:
    1. **Inline documentation**: Are complex algorithms and business logic explained?
    2. **API documentation**: Are endpoints documented with examples? Request/response schemas?
    3. **Architecture documentation**: ADRs, system diagrams, component documentation
    4. **README completeness**: Setup instructions, development workflow, deployment guide
    5. **Accuracy**: Does documentation match the actual implementation?
    6. **Changelog/migration guides**: Are breaking changes documented?
    7. **Onboarding**: Could a new developer understand the codebase from the docs alone?

    For each finding, provide:
    - Severity (Critical / High / Medium / Low)
    - What is missing or inaccurate
    - Specific documentation recommendation

    Write your findings as a structured markdown document.
```

After both complete, consolidate into `.full-review/03-testing-documentation.md`:

```markdown
# Phase 3: Testing & Documentation Review

## Test Coverage Findings

[Summary from 3A, organized by severity]

## Documentation Findings

[Summary from 3B, organized by severity]
```

Include `<machine_summary>` blocks at the end of `.full-review/03-testing-documentation.md`.

Update `state.json`: set `current_step` to 4, `current_phase` to 4, add steps 3A and 3B to `completed_steps`.

---

## Phase 4: Best Practices & Standards (Steps 4A-4C)

Read all previous `.full-review/*.md` files for full context.

Run all three agents in parallel using multiple Agent tool calls in a single response.

### Step 4A: Framework & Language Best Practices

```
Agent tool call:
  - description: "Framework best practices review for $ARGUMENTS"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    You are an expert in modern framework and language best practices. Verify adherence to current standards.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## All Prior Findings
    [Insert a concise summary of critical/high findings from all prior phases]

    ## Instructions
    Check for:
    1. **Language idioms**: Is the code idiomatic for its language? Modern syntax and features?
    2. **Framework patterns**: Does it follow the framework's recommended patterns? (e.g., React hooks, Django views, Spring beans, Tauri commands)
    3. **Deprecated APIs**: Are any deprecated functions/libraries/patterns used?
    4. **Modernization opportunities**: Where could modern language/framework features simplify code?
    5. **Package management**: Are dependencies up-to-date? Unnecessary dependencies? Proper lockfile?
    6. **Build configuration**: Is the build optimized? Development vs production settings?
    7. **Type safety**: Are type annotations used where available? Any unsafe type casts?

    For each finding, provide:
    - Severity (Critical / High / Medium / Low)
    - Current pattern vs recommended pattern
    - Migration/fix recommendation with code example

    Write your findings as a structured markdown document.
```

### Step 4B: CI/CD & DevOps Practices Review

```
Agent tool call:
  - description: "CI/CD and DevOps practices review for $ARGUMENTS"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    You are a DevOps engineer. Review CI/CD pipeline and operational practices.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Critical Issues from Prior Phases
    [Insert critical/high findings from all prior phases that impact deployment or operations]

    ## Instructions
    Evaluate:
    1. **CI/CD pipeline**: Build automation, test gates, deployment stages, security scanning, linting gates
    2. **Deployment strategy**: Blue-green, canary, rollback capabilities, zero-downtime deployment
    3. **Infrastructure as Code**: Are infrastructure configs version-controlled and reviewed?
    4. **Monitoring & observability**: Logging, metrics, alerting, dashboards, distributed tracing
    5. **Incident response**: Runbooks, on-call procedures, rollback plans, post-mortem process
    6. **Environment management**: Config separation, secret management, parity between environments
    7. **Container/runtime**: Dockerfile best practices, image scanning, resource limits

    For each finding, provide:
    - Severity (Critical / High / Medium / Low)
    - Operational risk assessment
    - Specific improvement recommendation

    Write your findings as a structured markdown document.
```

### Step 4C: Dead Code Analysis

```
Agent tool call:
  - description: "Dead code analysis for $ARGUMENTS"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    You are a dead code detection specialist. Analyze the target code for unused symbols.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Instructions
    1. **Auto-detect language**: Check for package.json (TS/JS) or pyproject.toml / *.py (Python)
    2. **For TypeScript/JavaScript**: Run Knip analysis -- unused files, dependencies, exports, types
    3. **For Python**: Run vulture (--min-confidence 80) + ruff (F401, F841, F811) -- unused imports, variables, functions, classes, unreachable code
    4. **For mixed projects**: Analyze both

    Account for framework conventions before flagging:
    - Django: views in urls.py, signal handlers, admin classes, management commands
    - FastAPI/Flask: route handlers, dependency injection, event handlers
    - React/Next.js: page components, API routes, middleware, dynamic imports
    - pytest: fixtures, conftest, parametrize, plugin hooks
    - General: __all__ exports, dunder methods, getattr/importlib dynamic access, decorators, re-exports

    For each finding, provide:
    - Severity (High / Medium / Low)
    - File and line location
    - Category (unused import, unused function, unused variable, unused constant/module-level definition, unused export, unreachable code, unused file, unused dependency)
    - Confidence (0-100) -- how certain this is truly dead code
    - Recommended action (remove, verify, defer)

    Write your findings as a structured markdown document.
```

After all three complete, consolidate into `.full-review/04-best-practices.md`:

```markdown
# Phase 4: Best Practices & Standards

## Framework & Language Findings

[Summary from 4A, organized by severity]

## CI/CD & DevOps Findings

[Summary from 4B, organized by severity]

## Dead Code Findings

[Summary from 4C, organized by severity]
```

Include `<machine_summary>` blocks at the end of `.full-review/04-best-practices.md`.

Update `state.json`: set `current_step` to 5, `current_phase` to 5, add steps 4A, 4B, and 4C to `completed_steps`.

---

## Phase 5: Quality Scoring (Step 5)

Read all `.full-review/*.md` files for full context. This phase runs AFTER all prior review phases because it needs all findings for calibrated scoring.

```
Agent tool call:
  - description: "Code quality scoring for $ARGUMENTS"
  - subagent_type: "senior-review:code-auditor"
  - prompt: |
    Perform quantitative code quality scoring and pattern analysis.
    You have deep dive analysis (if performed) AND all prior review phase findings -- use all of them for calibrated scoring.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## All Prior Review Findings
    [Insert summaries from:
     - .full-review/01-code-audit.md
     - .full-review/02-security-performance.md
     - .full-review/03-testing-documentation.md
     - .full-review/04-best-practices.md]

    ## Instructions

    ### Context Assessment
    Determine the code's scope, maturity stage (prototype/production/legacy). Use prior phase findings
    to calibrate focus areas -- don't duplicate what's already been covered in detail.

    ### Code Quality Analysis
    1. **Code complexity**: Cyclomatic/cognitive complexity, deeply nested logic
    2. **Maintainability**: Naming conventions, function/method length, class cohesion
    3. **Code duplication**: Copy-pasted logic, missed abstraction opportunities
    4. **Clean Code principles**: SOLID violations, code smells, anti-patterns
    5. **Technical debt**: Areas that will become increasingly costly to change
    6. **Error handling**: Missing error handling, swallowed exceptions, unclear error messages

    ### Mental Models (all six perspectives)
    - **Security Engineer**: Assume all input is malicious
    - **Performance Engineer**: What's the Big-O? What's the I/O pattern?
    - **Team Lead**: Maintainable in 6 months? Can juniors understand it?
    - **Systems Architect**: How does this fail? Blast radius?
    - **SRE**: What breaks at 3 AM?
    - **Pattern Detective**: Dominant patterns per file, then scan for violations

    ### Quantitative Code Quality Score
    Rate each category using ALL findings from deep dive + all review phases combined:
    - **9-10**: Excellent -- production-ready, exemplary patterns
    - **7-8**: Good -- minor issues, safe to deploy
    - **5-6**: Adequate -- notable issues, fix before deploy
    - **3-4**: Poor -- significant issues, needs rework
    - **1-2**: Critical -- fundamental problems, unsafe

    Provide scores for: Security, Performance, Architecture, Maintainability, Testing, Documentation, Resilience, and Overall.

    Write findings as structured markdown with Executive Summary, Code Quality Findings,
    What's Done Well, and the Code Quality Score table.
```

Write to `.full-review/05-quality-scoring.md`:

```markdown
# Phase 5: Code Quality Scoring

## Executive Summary

[2-3 sentence overview of code quality]

## Code Quality Findings

[Any new findings not covered in prior phases, organized by severity]

## What's Done Well

[Positive observations]

## Code Quality Score

| Category        | Score |
|-----------------|-------|
| Security        | X/10  |
| Performance     | X/10  |
| Architecture    | X/10  |
| Maintainability | X/10  |
| Testing         | X/10  |
| Documentation   | X/10  |
| Resilience      | X/10  |
| **Overall**     | **X/10** |
```

Update `state.json`: set `current_step` to 6, `current_phase` to 6, add step 5 to `completed_steps`.

---

## Phase 6: Consolidated Report (Step 6)

Read all `.full-review/*.md` files (01 through 05). Generate the final consolidated report. Use the Code Quality Score from Phase 5's scoring output (`.full-review/05-quality-scoring.md`).

**Output file:** `.full-review/06-final-report.md`

```markdown
# Comprehensive Code Review Report

## Review Target

[From 00-scope.md]

## Executive Summary

[3-4 sentence overview combining deep dive insights (if performed) with review findings.
Highlight the relationship between structural issues found in deep dive and the concrete
problems found during review.]

## Code Quality Score

[From Phase 5 quality scoring]

| Category        | Score |
|-----------------|-------|
| Security        | X/10  |
| Performance     | X/10  |
| Architecture    | X/10  |
| Maintainability | X/10  |
| Testing         | X/10  |
| Documentation   | X/10  |
| Resilience      | X/10  |
| **Overall**     | **X/10** |

## Deep Dive Insights (if applicable)

[Key structural and semantic findings that informed the review.
Analysis of how deep dive findings correlated with review findings.
Did the structural analysis accurately predict the review issues?
Were there surprises the deep dive missed?]

## Findings by Priority

### Critical Issues (P0 -- Must Fix Immediately)

[All Critical findings from all phases, with source phase reference]

- Security vulnerabilities with CVSS > 7.0
- Data loss or corruption risks
- Authentication/authorization bypasses
- Production stability threats

### High Priority (P1 -- Fix Before Next Release)

[All High findings from all phases]

- Performance bottlenecks impacting user experience
- Missing critical test coverage
- Architectural anti-patterns causing technical debt
- Outdated dependencies with known vulnerabilities

### Medium Priority (P2 -- Plan for Next Sprint)

[All Medium findings from all phases]

- Non-critical performance optimizations
- Documentation gaps
- Code refactoring opportunities
- Test quality improvements

### Low Priority (P3 -- Track in Backlog)

[All Low findings from all phases]

- Style guide violations
- Minor code smell issues
- Nice-to-have improvements

## Findings by Category

- **Code Quality**: [count] findings ([breakdown by severity])
- **Architecture**: [count] findings ([breakdown by severity])
- **Pattern Consistency**: [count] findings ([breakdown by severity])
- **Security**: [count] findings ([breakdown by severity])
- **Performance**: [count] findings ([breakdown by severity])
- **Resilience**: [count] findings ([breakdown by severity])
- **Testing**: [count] findings ([breakdown by severity])
- **Documentation**: [count] findings ([breakdown by severity])
- **Best Practices**: [count] findings ([breakdown by severity])
- **CI/CD & DevOps**: [count] findings ([breakdown by severity])
- **UI Race Conditions**: [count] findings ([breakdown by severity])
- **React Performance**: [count] findings ([breakdown by severity])
- **Distributed Integration**: [count] findings ([breakdown by severity])
- **Dead Code**: [count] findings ([breakdown by severity])
- **Platform Engineering**: [count] findings ([breakdown by MUST/DO/DON'T])

## Recommended Action Plan

1. [Ordered list of recommended actions, starting with critical/high items]
2. [Group related fixes where possible]
3. [Estimate relative effort: small/medium/large]

## Review Metadata

- Review date: [timestamp]
- Phases completed: [list]
- Flags applied: [list active flags]
- Deep dive: [yes/no]
```

Update `state.json`: set `current_step` to 7, add step 6 to `completed_steps`, set `status` to `"complete"`, `last_updated` to current timestamp.

---

## CLAUDE.md Alignment Check

After the review, check if findings suggest the project's `CLAUDE.md` is stale:

1. Read `CLAUDE.md` (if it exists)
2. Cross-reference review findings with documented conventions, structure, and workflows
3. If any documented information is outdated or missing, note it in the review output and propose updates to the user

---

## Completion

Present the final summary:

```
Comprehensive code review complete for: $ARGUMENTS

## Review Output Files
- Scope: $SESSION_DIR/00-scope.md
- Deep Dive Context: $SESSION_DIR/00-deep-dive-context.md (if performed)
- Code Audit: $SESSION_DIR/01-code-audit.md
- Security & Performance: $SESSION_DIR/02-security-performance.md
- Testing & Documentation: $SESSION_DIR/03-testing-documentation.md
- Best Practices: $SESSION_DIR/04-best-practices.md
- Quality Scoring: $SESSION_DIR/05-quality-scoring.md
- Final Report: $SESSION_DIR/06-final-report.md

## Summary
- Total findings: [count]
- Critical: [X] | High: [Y] | Medium: [Z] | Low: [W]
- Code Quality Score: [X/10]

## Next Steps
1. Review the full report at $SESSION_DIR/06-final-report.md
2. Address Critical (P0) issues immediately
3. Plan High (P1) fixes for current sprint
4. Add Medium (P2) and Low (P3) items to backlog
```

After presenting the summary, ask:

```
1. Keep all review files (default)
2. Keep only the final report -- delete intermediate files
3. Delete all review files -- cleanup session directory entirely
```

**Cleanup behavior by option:**

- **Option 1:** No action. All files remain in `$SESSION_DIR/`.
- **Option 2:** Delete intermediate files (`00-scope.md`, `00-deep-dive-context.md`, `01-code-audit.md`, `02-security-performance.md`, `03-testing-documentation.md`, `04-best-practices.md`, `05-quality-scoring.md`, `state.json`, and any `dd-*.md` deep-dive files). Keep only `06-final-report.md`. Move it to project root as `full-review-report-<label>.md`, then remove the empty `$SESSION_DIR/` directory.
- **Option 3:** Delete the entire `$SESSION_DIR/` directory and all its contents.
