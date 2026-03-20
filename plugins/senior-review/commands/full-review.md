---
description: >
  "Orchestrate comprehensive multi-dimensional code review using specialized review agents. Optionally enriched with deep-dive structural and semantic analysis for deeper context." argument-hint: "<target path or description> [--deep-dive] [--security-focus] [--performance-critical] [--strict-mode] [--framework react|spring|django|rails]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Comprehensive Code Review Orchestrator

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Write output files.** Each phase MUST produce its output file in `.full-review/` before the next phase begins. Read from prior phase files -- do NOT rely on context window memory.
3. **Stop at checkpoints.** When you reach a `PHASE CHECKPOINT`, you MUST stop and wait for explicit user approval before continuing. Use the AskUserQuestion tool with clear options.
4. **Halt on failure.** If any step fails (agent error, missing files, access issues), STOP immediately. Present the error and ask the user how to proceed. Do NOT silently continue.
5. **Use only local agents.** All `subagent_type` references use agents bundled with this plugin or `general-purpose`. No cross-plugin dependencies.
6. **Never enter plan mode autonomously.** Do NOT use EnterPlanMode. This command IS the plan -- execute it.

## Pre-flight Checks

Before starting, perform these checks:

### 1. Check for existing session

Check if `.full-review/state.json` exists:

- If it exists and `status` is `"in_progress"`: Read it, display the current phase, and ask the user:

  ```
  Found an in-progress review session:
  Target: [target from state]
  Current phase: [phase from state]

  1. Resume from where we left off
  2. Start fresh (archives existing session)
  ```

- If it exists and `status` is `"complete"`: Ask whether to archive and start fresh.

### 2. Initialize state

Create `.full-review/` directory and `state.json`:

```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "flags": {
    "deep_dive": false,
    "security_focus": false,
    "performance_critical": false,
    "strict_mode": false,
    "framework": null
  },
  "current_step": 1,
  "current_phase": 1,
  "completed_steps": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--deep-dive`, `--security-focus`, `--performance-critical`, `--strict-mode`, and `--framework` flags. Update the flags object accordingly.

### 3. Identify review target

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

- Deep Dive: [yes/no]
- Security Focus: [yes/no]
- Performance Critical: [yes/no]
- Strict Mode: [yes/no]
- Framework: [name or auto-detected]

## Review Phases

1. Architecture Review
2. Security & Performance
3. Testing & Documentation
4. Best Practices & Standards
5. Code Quality, Pattern Analysis & Scoring
6. Consolidated Report
```

Update `state.json`: add `"00-scope.md"` to `files_created`, add step 0 to `completed_steps`.

---

## Phase 0: Deep Dive Context Gathering (if --deep-dive)

Skip this phase entirely if `--deep-dive` flag is not set.

**Note:** This phase does NOT require the `deep-dive-analysis` plugin -- it uses `general-purpose` agents to perform its own structural analysis. The `deep-dive-analysis` plugin is a separate, standalone tool.

When `--deep-dive` is active, run deep-dive analysis on the target path to gather structural and semantic context that strengthens all subsequent review phases.

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
    - Request lifecycle (entry -> processing -> response)
    - Data transformation pipelines
    - Error propagation paths
    - State mutation flows and side effects

    Write to `.full-review/dd-03-flows.md`

    ## Phase 4: Semantic Understanding
    Understand the WHY behind the code:
    - Business purpose of each module
    - Design decisions and trade-offs
    - Assumptions embedded in the code
    - Implicit contracts not documented anywhere

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
    - Anti-patterns: god objects, spaghetti code, shotgun surgery, feature envy
    - Red flags: swallowed exceptions, hardcoded credentials, race conditions, N+1 queries
    - Technical debt: TODO/FIXME comments, deprecated APIs, outdated patterns
    - Failure modes: what breaks under load, edge cases, missing error handling

    Write to `.full-review/dd-05-risks.md`
```

After all 3 agents complete, produce `.full-review/00-deep-dive-context.md` summarizing key findings from all 5 deep-dive files. This summary will be injected into subsequent review agent prompts.

Update `state.json`: add `"phase_0"` to `completed_steps`.

---

## Deep Dive Context Injection

When `--deep-dive` flag is active, each review agent prompt in Phases 1-5 gets this additional section inserted after the existing context sections:

```
## Deep Dive Context

[Insert relevant deep-dive findings from .full-review/00-deep-dive-context.md:
- For architect-review (Phase 1): structure, interfaces, flows, semantics
- For security-auditor (Phase 2A): flows (data paths), semantics (assumptions), risks
- For performance agent (Phase 2B): structure, flows
- For test/docs agents (Phase 3): interfaces, flows, risks
- For best practices agents (Phase 4): all deep-dive findings
- For pattern-quality-scorer (Phase 5): all deep-dive findings]

Use this context to strengthen your analysis. Do NOT re-report findings already
covered in the deep dive -- instead focus on new issues the deep dive missed or
issues that become apparent when combining deep-dive context with your
specialized perspective.
```

---

## Phase 1: Architecture Review (Step 1A)

### Step 1A: Architecture & Design Review

```
Agent tool call:
  - description: "Architecture review for $ARGUMENTS"
  - subagent_type: "senior-review:architect-review"
  - prompt: |
    Review the architectural design and structural integrity of the target code.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Instructions
    Evaluate the code for:
    1. **Component boundaries**: Proper separation of concerns, module cohesion
    2. **Dependency management**: Circular dependencies, inappropriate coupling, dependency direction
    3. **API design**: Endpoint design, request/response schemas, error contracts, versioning
    4. **Data model**: Schema design, relationships, data access patterns
    5. **Design patterns**: Appropriate use of patterns, missing abstractions, over-engineering
    6. **Architectural consistency**: Does the code follow the project's established patterns?

    For each finding, provide:
    - Severity (Critical / High / Medium / Low)
    - Architectural impact assessment
    - Specific improvement recommendation

    Write your findings as a structured markdown document.
```

### Large Change Set Handling

Before launching review agents, check the scope size. If the target contains more than 500 lines of code across all files, batch the files into groups of 3-5 files per agent invocation. Run batches sequentially, then consolidate findings before writing the phase output file.

After completing, write to `.full-review/01-architecture.md`:

```markdown
# Phase 1: Architecture Review

## Architecture Findings

[Summary from 1A, organized by severity]

## Critical Issues for Phase 2 Context

[List any findings that should inform security or performance review]
```

### Machine-Readable Summary for Downstream Agents

At the end of `.full-review/01-architecture.md`, include a structured block for efficient agent-to-agent communication:

```xml
<machine_summary>
[
  {"severity": "CRITICAL|HIGH|MEDIUM|LOW", "type": "category", "file": "path", "line": N, "description": "brief finding"},
  ...
]
</machine_summary>
```

Phase 5 (pattern-quality-scorer) should read from `<machine_summary>` blocks rather than parsing full prose reports. This saves tokens and improves scoring precision.

Update `state.json`: set `current_step` to 2, `current_phase` to 2, add step 1A to `completed_steps`.

---

## Phase 2: Security & Performance Review (Steps 2A-2B)

Read `.full-review/01-architecture.md` for context from Phase 1.

Run all three agents in parallel using multiple Task tool calls in a single response.

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
    [Insert contents of .full-review/01-architecture.md -- focus on the "Critical Issues for Phase 2 Context" section]

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
    [Insert contents of .full-review/01-architecture.md -- focus on the "Critical Issues for Phase 2 Context" section]

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

### Step 2C: Failure Flow & Resilience Analysis

```
Agent tool call:
  - description: "Failure flow analysis for $ARGUMENTS"
  - subagent_type: "senior-review:failure-flow-tracer"
  - run_in_background: true
  - prompt: |
    Trace failure paths, kill scenarios, and resume/retry correctness in the target code.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Phase 1 Context
    [Insert contents of .full-review/01-architecture.md -- focus on state management and resource lifecycle findings]

    ## Instructions
    Analyze the target code for failure-path bugs:

    1. **Persisted State Map** -- Identify all files/databases/caches created by the code.
       For each: who writes, who reads, what validates it, what could invalidate it.

    2. **Kill Point Analysis** -- For each await/async operation, simulate process termination.
       What persisted state is left inconsistent? Does the next run handle it?

    3. **Cache Invalidation** -- For every cached/persisted artifact, is there a validity key
       (hash, version, fingerprint)? If source data changes between runs, is the cache
       properly invalidated? Can stale cached results be silently mixed with fresh results?

    4. **Resource Lifecycle** -- Are DB connections, file handles, temp files, subprocesses
       guaranteed to be cleaned up via try/finally or context managers on the error path?

    5. **Concurrency Under Failure** -- For parallel operations: if one task fails or the
       parent is killed, what happens to sibling tasks? Are side effects already committed?

    6. **Resume/Retry Correctness** -- If the code has resume/retry logic, trace the full
       cycle: start -> partial completion -> kill -> resume. What assumptions does resume
       make? What if those assumptions are violated?

    For each finding: severity, concrete step-by-step scenario, file + line, confidence (0-100), fix.

    Write your findings as a structured markdown document.
```

After all three complete, consolidate into `.full-review/02-security-performance.md`:

```markdown
# Phase 2: Security & Performance Review

## Security Findings

[Summary from 2A, organized by severity]

## Performance Findings

[Summary from 2B, organized by severity]

## Failure Flow & Resilience Findings

[Summary from 2C, organized by severity]

## Critical Issues for Phase 3 Context

[List findings that affect testing or documentation requirements]
```

Include `<machine_summary>` blocks at the end of `.full-review/02-security-performance.md` (same format as Phase 1).

Update `state.json`: set `current_step` to "checkpoint-1", add steps 2A and 2B to `completed_steps`.

---

## PHASE CHECKPOINT 1 -- User Approval Required

Display a summary of findings from Phase 1 and Phase 2 and ask:

```
Phases 1-2 complete: Architecture, Security, and Performance reviews done.

Summary:
- Architecture: [X critical, Y high, Z medium findings]
- Security: [X critical, Y high, Z medium findings]
- Performance: [X critical, Y high, Z medium findings]
- Resilience: [X critical, Y high, Z medium findings]

Please review:
- .full-review/01-architecture.md
- .full-review/02-security-performance.md

1. Continue -- proceed to Testing & Documentation review
2. Fix critical issues first -- I'll address findings before continuing
3. Pause -- save progress and stop here
```

If `--strict-mode` flag is set and there are Critical findings, recommend option 2.

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 3: Testing & Documentation Review (Steps 3A-3B)

Read `.full-review/01-architecture.md` and `.full-review/02-security-performance.md` for context.

Run both agents in parallel using multiple Task tool calls in a single response.

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
    [Insert key findings from .full-review/01-architecture.md and .full-review/02-security-performance.md]

    ## Instructions
    Evaluate:
    1. **Inline documentation**: Are complex algorithms and business logic explained?
    2. **API documentation**: Are endpoints documented with examples? Request/response schemas?
    3. **Architecture documentation**: ADRs, system diagrams, component documentation
    4. **README completeness**: Setup instructions, development workflow, deployment guide
    5. **Accuracy**: Does documentation match the actual implementation?
    6. **Changelog/migration guides**: Are breaking changes documented?

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

## Phase 4: Best Practices & Standards (Steps 4A-4B)

Read all previous `.full-review/*.md` files for full context.

Run all three agents in parallel using multiple Task tool calls in a single response.

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
    2. **Framework patterns**: Does it follow the framework's recommended patterns? (e.g., React hooks, Django views, Spring beans)
    3. **Deprecated APIs**: Are any deprecated functions/libraries/patterns used?
    4. **Modernization opportunities**: Where could modern language/framework features simplify code?
    5. **Package management**: Are dependencies up-to-date? Unnecessary dependencies?
    6. **Build configuration**: Is the build optimized? Development vs production settings?

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
    1. **CI/CD pipeline**: Build automation, test gates, deployment stages, security scanning
    2. **Deployment strategy**: Blue-green, canary, rollback capabilities
    3. **Infrastructure as Code**: Are infrastructure configs version-controlled and reviewed?
    4. **Monitoring & observability**: Logging, metrics, alerting, dashboards
    5. **Incident response**: Runbooks, on-call procedures, rollback plans
    6. **Environment management**: Config separation, secret management, parity between environments

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
    - React/Next.js: page components, API routes, middleware
    - pytest: fixtures, conftest, parametrize, plugin hooks
    - General: __all__ exports, dunder methods, getattr/importlib dynamic access, decorators

    For each finding, provide:
    - Severity (High / Medium / Low)
    - File and line location
    - Category (unused import, unused function, unused variable, unused constant/module-level definition, unused export, unreachable code, unused file)
    - Confidence (0-100) -- how certain this is truly dead code
    - Recommended action

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

## Phase 5: Code Quality, Pattern Analysis & Scoring (Step 5)

Read all `.full-review/*.md` files (01 through 04) for full context before analyzing.

### Step 5: Code Quality, Pattern Consistency & Scoring

```
Agent tool call:
  - description: "Code quality, pattern analysis and scoring for $ARGUMENTS"
  - subagent_type: "senior-review:pattern-quality-scorer"
  - prompt: |
    Perform a comprehensive code quality review, pattern consistency analysis, and quantitative scoring.
    You have access to all prior phase findings — use them as context for calibrated, holistic scoring.

    ## Review Scope
    [Insert contents of .full-review/00-scope.md]

    ## Prior Phase Context
    [Extract <machine_summary> blocks from .full-review/01-architecture.md, .full-review/02-security-performance.md,
     .full-review/03-testing-documentation.md, .full-review/04-best-practices.md -- use structured data for precision.
     Only fall back to reading full prose if machine_summary blocks are missing.]

    ## Instructions

    ### Context Assessment
    Determine the code's scope, maturity stage (prototype/production/legacy). Use prior phase findings
    to calibrate focus areas — don't duplicate what's already been covered in detail.

    ### Code Quality Analysis
    Analyze the target code for:
    1. **Code complexity**: Cyclomatic complexity, cognitive complexity, deeply nested logic
    2. **Maintainability**: Naming conventions, function/method length, class cohesion
    3. **Code duplication**: Copy-pasted logic, missed abstraction opportunities
    4. **Clean Code principles**: SOLID violations, code smells, anti-patterns
    5. **Technical debt**: Areas that will become increasingly costly to change
    6. **Error handling**: Missing error handling, swallowed exceptions, unclear error messages

    ### Pattern Consistency Detection
    For each file, identify the dominant patterns and flag deviations:
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

    ### Mental Models
    Apply all six perspectives:
    - **Security Engineer**: Assume all input is malicious
    - **Performance Engineer**: What's the Big-O? What's the I/O pattern?
    - **Team Lead**: Maintainable in 6 months? Can juniors understand it?
    - **Systems Architect**: How does this fail? Blast radius?
    - **SRE**: What breaks at 3 AM?
    - **Pattern Detective**: Dominant patterns per file, then scan for violations

    ### Quantitative Code Quality Score
    Rate each category using ALL findings from all phases combined:
    - **9-10**: Excellent — production-ready, exemplary patterns
    - **7-8**: Good — minor issues, safe to deploy
    - **5-6**: Adequate — notable issues need attention before deploy
    - **3-4**: Poor — significant issues, needs rework
    - **1-2**: Critical — fundamental problems, unsafe

    Provide scores for: Security, Performance, Maintainability, Resilience, Testing, and an Overall score.

    Write your findings as a structured markdown document with an Executive Summary, Code Quality Findings,
    Pattern Consistency Findings, What's Done Well, and the Code Quality Score table.
```

Write output to `.full-review/05-quality-scoring.md`:

```markdown
# Phase 5: Code Quality, Pattern Analysis & Scoring

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
| Maintainability | X/10  |
| Resilience      | X/10  |
| Testing         | X/10  |
| **Overall**     | **X/10** |
```

Update `state.json`: set `current_step` to 6, `current_phase` to 6, add step 5 to `completed_steps`.

---

## Phase 6: Consolidated Report (Step 6)

Read all `.full-review/*.md` files (01 through 05). Generate the final consolidated report.

**Output file:** `.full-review/06-final-report.md`

```markdown
# Comprehensive Code Review Report

## Review Target

[From 00-scope.md]

## Executive Summary

[2-3 sentence overview of overall code health and key concerns]

## Code Quality Score

[From Phase 5 pattern-quality-scorer analysis]

| Category        | Score |
|-----------------|-------|
| Security        | X/10  |
| Performance     | X/10  |
| Maintainability | X/10  |
| Resilience      | X/10  |
| Testing         | X/10  |
| **Overall**     | **X/10** |

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
- **Dead Code**: [count] findings ([breakdown by severity])

## Recommended Action Plan

1. [Ordered list of recommended actions, starting with critical/high items]
2. [Group related fixes where possible]
3. [Estimate relative effort: small/medium/large]

## Review Metadata

- Review date: [timestamp]
- Phases completed: [list]
- Flags applied: [list active flags]
```

Update `state.json`: set `current_step` to 7, add step 6 to `completed_steps`, set `status` to `"complete"`, `last_updated` to current timestamp.

---

## Completion

Present the final summary:

```
Comprehensive code review complete for: $ARGUMENTS

## Review Output Files
- Scope: .full-review/00-scope.md
- Architecture: .full-review/01-architecture.md
- Security & Performance: .full-review/02-security-performance.md
- Testing & Documentation: .full-review/03-testing-documentation.md
- Best Practices: .full-review/04-best-practices.md
- Quality Scoring: .full-review/05-quality-scoring.md
- Final Report: .full-review/06-final-report.md

## Summary
- Total findings: [count]
- Critical: [X] | High: [Y] | Medium: [Z] | Low: [W]
- Code Quality Score: [X/10]

## Next Steps
1. Review the full report at .full-review/06-final-report.md
2. Address Critical (P0) issues immediately
3. Plan High (P1) fixes for current sprint
4. Add Medium (P2) and Low (P3) items to backlog
```
