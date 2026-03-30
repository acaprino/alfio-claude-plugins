---
description: >
  "Full codebase review pipeline -- deep-dive structural analysis followed by comprehensive multi-agent code review covering architecture, security, performance, testing, documentation, best practices, CI/CD, dead code, and consolidated quality scoring" argument-hint: "<target path or description> [--skip-deep-dive] [--security-focus] [--performance-critical] [--strict-mode] [--framework react|spring|django|rails]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Full Review Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.full-review-pipeline/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, missing files, access issues), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.

## Pre-flight Checks

### 0. Dependency check

This command requires agents, skills, and commands from other plugins. Before proceeding, verify they are installed:

**Required plugins:**
- `deep-dive-analysis` -- deep-dive-analysis skill/command (Phase 1)
- `senior-review` -- code-auditor, security-auditor agents (Phase 2)

Check by looking for the agent/skill files. If a required plugin is missing, STOP and tell the user:

```
Missing required plugin(s): [list]

This workflow command depends on agents and skills from other ACP plugins.
Install them with:
  claude plugin marketplace add acaprino/alfio-claude-plugins --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/alfio-claude-plugins
```

### 1. Check for existing session

Check if `.full-review-pipeline/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask:

  ```
  Found an in-progress full review pipeline session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```

- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 2. Initialize state

Create `.full-review-pipeline/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "skip_deep_dive": false,
    "security_focus": false,
    "performance_critical": false,
    "strict_mode": false,
    "framework": null
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--skip-deep-dive`, `--security-focus`, `--performance-critical`, `--strict-mode`, and `--framework` flags.

### 3. Identify review target

Determine what code to review from `$ARGUMENTS`:

- If a file/directory path is given, verify it exists
- If a description is given (e.g., "recent changes", "authentication module"), identify the relevant files
- List the files that will be reviewed and confirm with the user

**Output file:** `.full-review-pipeline/00-scope.md`

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
- Framework: [name or auto-detected]

## Pipeline Phases

1. Deep Dive Structural Analysis
2. Senior Code Review
   - 2A: Architecture Review
   - 2B: Security Vulnerability Assessment
   - 2C: Performance Analysis
   - 2D: Test Coverage Analysis
   - 2E-react: React Performance Review (if React files in scope)
   - 2E: Documentation & API Review
   - 2F: Framework & Language Best Practices
   - 2G: CI/CD & DevOps Practices
   - 2H: Dead Code Analysis
   - 2I: Code Quality, Pattern Analysis & Scoring
3. Consolidated Report
```

Update `state.json`: add `"00-scope.md"` to `files_created`, add step 0 to `completed_phases`.

---

## Phase 1: Deep Dive Structural Analysis

**Skip if:** `--skip-deep-dive` flag is set. If skipped, proceed directly to Phase 2.

Run the deep-dive-analysis skill on the target path. This produces comprehensive structural and semantic understanding of the codebase that will enrich all subsequent review phases.

Spawn 4 agents in parallel using the Agent tool:

### Agent A: Structure Extraction

```
Task:
  subagent_type: "general-purpose"
  description: "Deep dive structure extraction"
  prompt: |
    Analyze the target code and build a structural map.

    ## Target
    [Insert target path from 00-scope.md]

    ## Instructions
    For each file extract:
    - Module/file name and path
    - Language and framework
    - Imports and dependencies (internal and external)
    - Exported symbols (functions, classes, constants, types)
    - File size and complexity indicators (nesting depth, cyclomatic complexity estimate)
    - Entry points and initialization sequences

    Organize findings by module/package boundaries.

    Write to `.full-review-pipeline/dd-01-structure.md`
```

### Agent B: Interface & Contract Analysis

```
Task:
  subagent_type: "general-purpose"
  description: "Deep dive interface analysis"
  prompt: |
    Analyze the target code's public interfaces and contracts.

    ## Target
    [Insert target path from 00-scope.md]

    ## Instructions
    For each module, document:
    - Function signatures with parameter types and return types
    - Class hierarchies and method signatures
    - API endpoints with request/response shapes
    - Configuration interfaces and environment variables
    - Event contracts (emitted/consumed events)
    - Database schema and migration state
    - External service integrations and their contracts

    Write to `.full-review-pipeline/dd-02-interfaces.md`
```

### Agent C: Flow Tracing & Semantics

```
Task:
  subagent_type: "general-purpose"
  description: "Deep dive flow tracing and semantics"
  prompt: |
    Trace critical execution paths and understand business semantics.

    ## Target
    [Insert target path from 00-scope.md]

    ## Instructions
    Trace:
    - Request lifecycle (entry -> middleware -> processing -> response)
    - Data transformation pipelines
    - Error propagation paths and recovery mechanisms
    - State mutation flows and side effects
    - Authentication/authorization flow
    - Background job and queue processing flows

    Understand semantics:
    - Business purpose of each module
    - Design decisions and trade-offs visible in code
    - Assumptions embedded in the code
    - Implicit contracts not documented anywhere
    - Domain model and bounded contexts

    Write to `.full-review-pipeline/dd-03-flows-semantics.md`
```

### Agent D: Risk & Anti-Pattern Detection

```
Task:
  subagent_type: "general-purpose"
  description: "Deep dive risk and anti-pattern detection"
  prompt: |
    Analyze the target code for risks, anti-patterns, and technical debt.

    ## Target
    [Insert target path from 00-scope.md]

    ## Instructions
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

    Write to `.full-review-pipeline/dd-04-risks.md`
```

After all 4 agents complete, produce `.full-review-pipeline/01-deep-dive-summary.md`:

```markdown
# Phase 1: Deep Dive Analysis Summary

## Codebase Overview

[2-3 paragraph summary of codebase architecture and purpose]

## Structure Highlights

[Key structural findings from dd-01-structure.md]

## Interface Contracts

[Key interface findings from dd-02-interfaces.md]

## Critical Flows

[Key flow findings from dd-03-flows-semantics.md]

## Risks & Technical Debt

[Key risk findings from dd-04-risks.md]

## Key Areas for Review Focus

[List of areas that need special attention in the code review phase, organized by concern type]
```

Update `state.json`: set `current_phase` to "checkpoint-1", add phase 1 to `completed_phases`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

Display a summary of deep dive findings:

```
Phase 1 complete: Deep dive analysis done.

Summary:
- Files analyzed: [count]
- Modules identified: [count]
- Risks detected: [X critical, Y high, Z medium]
- Key areas flagged for review: [count]

Please review:
- .full-review-pipeline/01-deep-dive-summary.md
- .full-review-pipeline/dd-01-structure.md (structure)
- .full-review-pipeline/dd-02-interfaces.md (interfaces)
- .full-review-pipeline/dd-03-flows-semantics.md (flows)
- .full-review-pipeline/dd-04-risks.md (risks)

1. Continue -- proceed to senior code review (enriched with deep dive context)
2. Pause -- save progress and stop here
```

Do NOT proceed to Phase 2 until the user approves.

---

## Phase 2: Senior Code Review

Read `.full-review-pipeline/01-deep-dive-summary.md` and `.full-review-pipeline/00-scope.md` for full context.

This phase runs the senior-review process enriched with deep dive findings. All review agents receive the deep dive context to produce deeper, more targeted analysis.

### Deep Dive Context Injection

When deep dive was performed (not skipped), each review agent prompt in Phase 2 gets the relevant deep-dive findings injected:

- For code-auditor (2A): structure, interfaces, flows, semantics, risks
- For security-auditor (2B): flows (data paths), semantics (assumptions), risks
- For performance agent (2C): structure, flows
- For test/docs agents (2D, 2E): interfaces, flows, risks
- For best practices agents (2F): all deep-dive findings
- For CI/CD agent (2G): structure, risks
- For dead code agent (2H): structure, interfaces
- For code-auditor (2I -- scoring pass): all deep-dive findings

Use this context to strengthen analysis. Do NOT re-report findings already covered in the deep dive -- instead focus on new issues the deep dive missed or issues that become apparent when combining deep-dive context with the specialized perspective.

---

### Step 2A: Architecture Review (parallel with 2B)

Run steps 2A and 2B in parallel using multiple Agent tool calls in a single response.

```
Task:
  subagent_type: "senior-review:code-auditor"
  description: "Code audit enriched with deep dive context"
  prompt: |
    Review the architectural design and structural integrity of the target code.
    You have deep dive analysis context -- use it to go deeper than a surface-level review.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert contents of .full-review-pipeline/01-deep-dive-summary.md]
    [Insert key findings from .full-review-pipeline/dd-01-structure.md and dd-03-flows-semantics.md]

    ## Instructions
    Evaluate:
    1. **Component boundaries**: Separation of concerns, module cohesion -- cross-reference with structural map
    2. **Dependency management**: Circular dependencies, coupling -- use the dependency graph from deep dive
    3. **API design**: Endpoint design, schemas, error contracts -- validate against interface analysis
    4. **Data model**: Schema design, relationships, access patterns
    5. **Design patterns**: Appropriate use, missing abstractions, over-engineering
    6. **Architectural consistency**: Does code follow established patterns identified in deep dive?
    7. **Flow integrity**: Do the traced execution paths reveal architectural weaknesses?

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - Architectural impact assessment
    - Specific improvement recommendation

    Do NOT re-report issues already in the deep dive risk report. Focus on architectural
    implications and new issues visible from your specialized perspective.

    Write your findings as a structured markdown document.
```

### Step 2B: Security Vulnerability Assessment (parallel with 2A)

```
Task:
  subagent_type: "senior-review:security-auditor"
  description: "Security audit enriched with deep dive context"
  prompt: |
    Execute a comprehensive security audit on the target code.
    You have deep dive context including traced data flows and identified risks -- use them.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert contents of .full-review-pipeline/01-deep-dive-summary.md]
    [Insert key findings from .full-review-pipeline/dd-03-flows-semantics.md and dd-04-risks.md]

    ## Instructions
    Analyze:
    1. **OWASP Top 10**: Injection, broken auth, sensitive data exposure, XXE, broken access control, misconfig, XSS, insecure deserialization, vulnerable components, insufficient logging
    2. **Input validation**: Missing sanitization -- trace input paths from the flow analysis
    3. **Authentication/authorization**: Flawed logic, privilege escalation -- use the auth flow traces
    4. **Cryptographic issues**: Weak algorithms, hardcoded secrets, improper key management
    5. **Dependency vulnerabilities**: Known CVEs -- cross-reference with risk report
    6. **Configuration security**: Debug mode, verbose errors, permissive CORS, missing security headers
    7. **Data flow security**: Follow data from entry to storage using traced flows -- find where sanitization is missing

    For each finding:
    - Severity (Critical / High / Medium / Low) with CVSS score if applicable
    - CWE reference where applicable
    - File and line location
    - Proof of concept or attack scenario
    - Specific remediation steps with code example

    Do NOT re-report security risks already in the deep dive risk report unless you have
    additional context or a more specific attack scenario.

    Write your findings as a structured markdown document.
```

After both 2A and 2B complete, consolidate into `.full-review-pipeline/02-architecture-security.md`:

```markdown
# Phase 2A-2B: Architecture & Security Review

## Architecture Findings

[Summary from 2A, organized by severity]

## Security Findings

[Summary from 2B, organized by severity]

## Critical Issues for Subsequent Steps

[List findings that affect testing, performance, documentation, or best practices review]
```

Update `state.json`: add steps 2A and 2B to `completed_phases`.

---

### Step 2C: Performance Analysis (parallel with 2D and 2E)

Run steps 2C, 2D, and 2E in parallel using multiple Agent tool calls in a single response.

```
Task:
  subagent_type: "general-purpose"
  description: "Performance analysis enriched with deep dive context"
  prompt: |
    You are a performance engineer. Analyze the target code for performance issues.
    You have deep dive context including execution flow traces -- use them to identify bottlenecks.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert key findings from .full-review-pipeline/dd-01-structure.md and dd-03-flows-semantics.md]

    ## Prior Phase Context
    [Insert critical/high findings from .full-review-pipeline/02-architecture-security.md]

    ## Instructions
    Analyze:
    1. **Database performance**: N+1 queries, missing indexes, unoptimized queries, connection pool sizing -- use flow traces to identify hot paths
    2. **Memory management**: Leaks, unbounded collections, large object allocations
    3. **Caching**: Missing opportunities, stale cache risks, invalidation issues
    4. **I/O bottlenecks**: Synchronous blocking calls, missing pagination, large payloads
    5. **Concurrency**: Race conditions, deadlocks, thread safety
    6. **Frontend performance**: Bundle size, render performance, unnecessary re-renders, missing lazy loading
    7. **Scalability**: Horizontal scaling barriers, stateful components, single points of failure

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - Estimated performance impact
    - Specific optimization recommendation with code example

    Write your findings as a structured markdown document.
```

### Step 2D: Test Coverage Analysis (parallel with 2C and 2E)

```
Task:
  subagent_type: "general-purpose"
  description: "Test coverage analysis enriched with deep dive context"
  prompt: |
    You are a test automation engineer. Evaluate testing strategy and coverage.
    Use the deep dive context to identify which critical paths are untested.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert key findings from .full-review-pipeline/dd-02-interfaces.md and dd-03-flows-semantics.md]

    ## Prior Phase Context
    [Insert security findings from .full-review-pipeline/02-architecture-security.md that affect testing]

    ## Instructions
    Analyze:
    1. **Test coverage**: Which critical paths (from flow traces) have tests? Which don't?
    2. **Test quality**: Are tests testing behavior or implementation? Assertion quality?
    3. **Test pyramid adherence**: Unit vs integration vs E2E test ratio
    4. **Edge cases**: Boundary conditions, error paths, concurrent scenarios
    5. **Test maintainability**: Test isolation, mock usage, flaky test indicators
    6. **Security test gaps**: Are security-critical paths tested? Auth, input validation?
    7. **Performance test gaps**: Are performance-critical paths tested? Load testing?
    8. **Integration gaps**: Are interface contracts (from deep dive) validated by tests?

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - What is untested or poorly tested
    - Specific test recommendation with example test code

    Write your findings as a structured markdown document.
```

### Step 2E-react: React Performance Review (conditional, parallel with 2C, 2D, and 2E)

**Only run this agent if the target includes React files** (`.tsx`, `.jsx`, or `package.json` listing `react` as a dependency). Skip entirely for non-React codebases.

```
Task:
  subagent_type: "react-development:react-performance-optimizer"
  description: "React performance review enriched with deep dive context"
  prompt: |
    Audit the React performance, state management, and bundle optimization of the target code.
    You have deep dive context -- use it to identify component-level issues.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert key findings from .full-review-pipeline/dd-01-structure.md and dd-03-flows-semantics.md]

    ## Prior Phase Context
    [Insert critical/high findings from .full-review-pipeline/02-architecture-security.md]

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

    Do NOT re-report performance issues already covered in prior phases. Focus on
    React-specific patterns and optimizations.

    For each finding: severity (Critical/High/Medium/Low), file + line, issue description, specific fix with code example.
    Note what's done well.

    Write your findings as a structured markdown document.
```

### Step 2E: Documentation & API Review (parallel with 2C, 2D, and 2E-react)

```
Task:
  subagent_type: "general-purpose"
  description: "Documentation review enriched with deep dive context"
  prompt: |
    You are a technical documentation architect. Review documentation completeness and accuracy.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert key findings from .full-review-pipeline/dd-02-interfaces.md and dd-03-flows-semantics.md]

    ## Prior Phase Context
    [Insert key findings from .full-review-pipeline/02-architecture-security.md]

    ## Instructions
    Evaluate:
    1. **Inline documentation**: Are complex algorithms and business logic explained? Are assumptions documented?
    2. **API documentation**: Are endpoints documented with examples? Request/response schemas? Error responses?
    3. **Architecture documentation**: ADRs, system diagrams, component documentation
    4. **README completeness**: Setup instructions, development workflow, deployment guide, prerequisites
    5. **Accuracy**: Does documentation match the actual implementation? Cross-reference with interface analysis
    6. **Changelog/migration guides**: Are breaking changes documented? Version history?
    7. **Onboarding**: Could a new developer understand the codebase from the docs alone?

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - What is missing or inaccurate
    - Specific documentation recommendation

    Write your findings as a structured markdown document.
```

After 2C, 2D, 2E, and 2E-react complete, consolidate into `.full-review-pipeline/03-performance-testing-docs.md`:

```markdown
# Phase 2C-2E: Performance, Testing, Documentation & React Review

## Performance Findings

[Summary from 2C, organized by severity]

## Test Coverage Findings

[Summary from 2D, organized by severity]

## Documentation Findings

[Summary from 2E, organized by severity]

## React Performance Findings (if applicable)

[Summary from 2E-react, organized by severity, or "N/A -- no React files in scope"]

## Critical Issues for Subsequent Steps

[List findings that affect best practices, CI/CD, or quality scoring]
```

Update `state.json`: add steps 2C, 2D, and 2E to `completed_phases`.

---

## PHASE CHECKPOINT 2 -- User Approval Required

Display a summary of all review findings so far:

```
Phases 1-2 (partial) complete: Deep dive + Architecture + Security + Performance + Testing + Documentation.

Summary:
- Deep Dive Risks: [X critical, Y high, Z medium]
- Architecture: [X critical, Y high, Z medium findings]
- Security: [X critical, Y high, Z medium findings]
- Performance: [X critical, Y high, Z medium findings]
- Test Coverage: [X critical, Y high, Z medium findings]
- Documentation: [X critical, Y high, Z medium findings]

Please review:
- .full-review-pipeline/02-architecture-security.md
- .full-review-pipeline/03-performance-testing-docs.md

1. Continue -- proceed to best practices, CI/CD, dead code analysis, and quality scoring
2. Fix critical issues first -- address findings before continuing
3. Pause -- save progress and stop here
```

If `--strict-mode` flag is set and there are Critical findings, recommend option 2.

Do NOT proceed until the user approves.

---

### Step 2F: Framework & Language Best Practices (parallel with 2G and 2H)

Read all previous `.full-review-pipeline/*.md` files for full context.

Run steps 2F, 2G, and 2H in parallel using multiple Agent tool calls in a single response.

```
Task:
  subagent_type: "general-purpose"
  description: "Framework and language best practices review"
  prompt: |
    You are an expert in modern framework and language best practices. Verify adherence to current standards.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert contents of .full-review-pipeline/01-deep-dive-summary.md]

    ## All Prior Findings
    [Insert a concise summary of critical/high findings from all prior steps]

    ## Instructions
    Check for:
    1. **Language idioms**: Is the code idiomatic for its language? Modern syntax and features?
    2. **Framework patterns**: Does it follow the framework's recommended patterns? (e.g., React hooks, Django views, Spring beans, Tauri commands)
    3. **Deprecated APIs**: Are any deprecated functions, libraries, or patterns used?
    4. **Modernization opportunities**: Where could modern language/framework features simplify code?
    5. **Package management**: Are dependencies up-to-date? Unnecessary dependencies? Proper lockfile?
    6. **Build configuration**: Is the build optimized? Development vs production settings properly separated?
    7. **Type safety**: Are type annotations used where available? Any unsafe type casts or any-typed values?

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - Current pattern vs recommended pattern
    - Migration/fix recommendation with code example

    Write your findings as a structured markdown document.
```

### Step 2G: CI/CD & DevOps Practices (parallel with 2F and 2H)

```
Task:
  subagent_type: "general-purpose"
  description: "CI/CD and DevOps practices review"
  prompt: |
    You are a DevOps engineer. Review CI/CD pipeline and operational practices.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert key findings from .full-review-pipeline/dd-01-structure.md and dd-04-risks.md]

    ## Critical Issues from Prior Steps
    [Insert critical/high findings from all prior steps that impact deployment or operations]

    ## Instructions
    Evaluate:
    1. **CI/CD pipeline**: Build automation, test gates, deployment stages, security scanning, linting gates
    2. **Deployment strategy**: Blue-green, canary, rollback capabilities, zero-downtime deployment
    3. **Infrastructure as Code**: Are infrastructure configs version-controlled and reviewed?
    4. **Monitoring & observability**: Logging, metrics, alerting, dashboards, distributed tracing
    5. **Incident response**: Runbooks, on-call procedures, rollback plans, post-mortem process
    6. **Environment management**: Config separation, secret management, parity between environments
    7. **Container/runtime**: Dockerfile best practices, image scanning, resource limits

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - Operational risk assessment
    - Specific improvement recommendation

    Write your findings as a structured markdown document.
```

### Step 2H: Dead Code Analysis (parallel with 2F and 2G)

```
Task:
  subagent_type: "general-purpose"
  description: "Dead code analysis"
  prompt: |
    You are a dead code detection specialist. Analyze the target code for unused symbols and unreachable code.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert key findings from .full-review-pipeline/dd-01-structure.md and dd-02-interfaces.md]

    ## Instructions
    1. **Auto-detect language**: Check for package.json (TS/JS) or pyproject.toml / *.py (Python) or other project markers
    2. **For TypeScript/JavaScript**: Run Knip analysis -- unused files, dependencies, exports, types
    3. **For Python**: Run vulture (--min-confidence 80) + ruff (F401, F841, F811) -- unused imports, variables, functions, classes, unreachable code
    4. **For mixed projects**: Analyze both language ecosystems

    Account for framework conventions before flagging:
    - Django: views referenced in urls.py, signal handlers, admin classes, management commands
    - FastAPI/Flask: route handlers, dependency injection, event handlers
    - React/Next.js: page components, API routes, middleware, dynamic imports
    - pytest: fixtures, conftest, parametrize, plugin hooks
    - General: __all__ exports, dunder methods, getattr/importlib dynamic access, decorators, re-exports

    For each finding:
    - Severity (High / Medium / Low)
    - File and line location
    - Category (unused import, unused function, unused variable, unused export, unreachable code, unused file, unused dependency)
    - Confidence (0-100) -- how certain this is truly dead code
    - Recommended action (remove, verify, defer)

    Write your findings as a structured markdown document.
```

After 2F, 2G, and 2H complete, consolidate into `.full-review-pipeline/04-practices-cicd-deadcode.md`:

```markdown
# Phase 2F-2H: Best Practices, CI/CD & Dead Code

## Framework & Language Best Practices Findings

[Summary from 2F, organized by severity]

## CI/CD & DevOps Findings

[Summary from 2G, organized by severity]

## Dead Code Findings

[Summary from 2H, organized by severity]
```

Update `state.json`: add steps 2F, 2G, and 2H to `completed_phases`.

---

### Step 2I: Code Quality, Pattern Analysis & Scoring

Read all `.full-review-pipeline/*.md` files for full context. This step runs AFTER all prior review steps because it needs all findings for calibrated scoring.

```
Task:
  subagent_type: "senior-review:code-auditor"
  description: "Code quality scoring enriched with deep dive and all review context"
  prompt: |
    Perform comprehensive code quality review, pattern consistency analysis, and quantitative scoring.
    You have deep dive analysis AND all prior review phase findings -- use all of them for calibrated scoring.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert contents of .full-review-pipeline/01-deep-dive-summary.md]

    ## All Prior Review Findings
    [Insert summaries from:
     - .full-review-pipeline/02-architecture-security.md
     - .full-review-pipeline/03-performance-testing-docs.md
     - .full-review-pipeline/04-practices-cicd-deadcode.md]

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

    ### Pattern Consistency Detection
    For each file, identify dominant patterns and flag deviations:
    - Error handling style (try/catch, Result types, error checks)
    - Resource management (using, defer, finally, context managers)
    - Import conventions (grouping, ordering)
    - Null/optional handling (defensive checks, optional chaining)
    - Async patterns (async/await vs callbacks vs blocking)

    Key question: "Is there an established pattern in this file that this code should follow but doesn't?"

    ### Anti-Pattern Checklist
    Flag any occurrences of: god objects, premature optimization, callback hell, mutable global state,
    swallowed exceptions, tight third-party coupling, missing validation on external data, sync I/O
    blocking event loops, DB queries in loops, missing transaction boundaries, no rollback on partial
    failures, TODO/FIXME in critical paths. Also flag consistency anti-patterns.

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

    Provide scores for: Security, Performance, Architecture, Maintainability, Testing, Documentation, and Overall.

    Write findings as structured markdown with Executive Summary, Code Quality Findings,
    Pattern Consistency Findings, What's Done Well, and the Code Quality Score table.
```

Write to `.full-review-pipeline/05-quality-scoring.md`:

```markdown
# Phase 2I: Code Quality, Pattern Analysis & Scoring

## Executive Summary

[2-3 sentence overview of code quality]

## Code Quality Findings

[Organized by severity]

## Pattern Consistency Findings

[Pattern deviations, anti-patterns detected]

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
| **Overall**     | **X/10** |
```

Update `state.json`: add step 2I to `completed_phases`.

---

## Phase 3: Consolidated Report

Read all `.full-review-pipeline/*.md` files (dd-* through 05). Generate the final consolidated report.

**Output file:** `.full-review-pipeline/06-final-report.md`

```markdown
# Full Review Pipeline Report

## Review Target

[From 00-scope.md]

## Executive Summary

[3-4 sentence overview combining deep dive insights with review findings.
Highlight the relationship between structural issues found in deep dive
and the concrete problems found during review.]

## Code Quality Score

| Category        | Score |
|-----------------|-------|
| Security        | X/10  |
| Performance     | X/10  |
| Architecture    | X/10  |
| Maintainability | X/10  |
| Testing         | X/10  |
| Documentation   | X/10  |
| **Overall**     | **X/10** |

## Deep Dive Insights

[Key structural and semantic findings that informed the review]

## Findings by Priority

### Critical Issues (P0 -- Must Fix Immediately)

[All Critical findings from deep dive + all review phases, with source phase reference]

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
- Modernization opportunities

### Low Priority (P3 -- Track in Backlog)

[All Low findings from all phases]

- Style guide violations
- Minor code smell issues
- Nice-to-have improvements
- Low-confidence dead code

## Findings by Category

- **Architecture**: [count] findings ([breakdown by severity])
- **Security**: [count] findings ([breakdown by severity])
- **Performance**: [count] findings ([breakdown by severity])
- **Code Quality**: [count] findings ([breakdown by severity])
- **Pattern Consistency**: [count] findings ([breakdown by severity])
- **Testing**: [count] findings ([breakdown by severity])
- **Documentation**: [count] findings ([breakdown by severity])
- **React Performance**: [count] findings ([breakdown by severity])
- **Best Practices**: [count] findings ([breakdown by severity])
- **CI/CD & DevOps**: [count] findings ([breakdown by severity])
- **Dead Code**: [count] findings ([breakdown by severity])
- **Technical Debt**: [count] findings ([breakdown by severity])

## Recommended Action Plan

1. [Ordered list starting with critical items]
2. [Group related fixes where possible]
3. [Estimate relative effort: small/medium/large]

## Deep Dive vs Review Correlation

[Analysis of how deep dive findings correlated with review findings.
Did the structural analysis accurately predict the review issues?
Were there surprises the deep dive missed?]

## Pipeline Metadata

- Review date: [timestamp]
- Phases completed: [list]
- Flags applied: [list]
- Deep dive: [yes/no]
```

Update `state.json`: set `status` to `"complete"`, `last_updated` to current timestamp.

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
Full review pipeline complete for: $ARGUMENTS

## Output Files
- Scope: .full-review-pipeline/00-scope.md
- Deep Dive Structure: .full-review-pipeline/dd-01-structure.md
- Deep Dive Interfaces: .full-review-pipeline/dd-02-interfaces.md
- Deep Dive Flows: .full-review-pipeline/dd-03-flows-semantics.md
- Deep Dive Risks: .full-review-pipeline/dd-04-risks.md
- Deep Dive Summary: .full-review-pipeline/01-deep-dive-summary.md
- Architecture & Security: .full-review-pipeline/02-architecture-security.md
- Performance, Testing & Docs: .full-review-pipeline/03-performance-testing-docs.md
- Best Practices, CI/CD & Dead Code: .full-review-pipeline/04-practices-cicd-deadcode.md
- Quality Scoring: .full-review-pipeline/05-quality-scoring.md
- Final Report: .full-review-pipeline/06-final-report.md

## Summary
- Total findings: [count]
- Critical: [X] | High: [Y] | Medium: [Z] | Low: [W]
- Code Quality Score: [X/10]

## Next Steps
1. Review the full report at .full-review-pipeline/06-final-report.md
2. Address Critical (P0) issues immediately
3. Plan High (P1) fixes for current sprint
4. Add Medium (P2) and Low (P3) items to backlog
```

If `--strict-mode` is set and Critical findings exist:
```
STRICT MODE: Unresolved critical issues found. Review .full-review-pipeline/06-final-report.md before merging.
```
