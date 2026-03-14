---
description: "Full codebase review pipeline -- deep-dive structural analysis followed by senior multi-agent code review with consolidated scoring"
argument-hint: "<target path or description> [--skip-deep-dive] [--security-focus] [--performance-critical] [--strict-mode] [--framework react|spring|django|rails]"
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
- `senior-review` -- architect-review, security-auditor, pattern-quality-scorer agents, full-review command pattern (Phase 2)

Check by looking for the agent/skill files. If a required plugin is missing, STOP and tell the user:

```
Missing required plugin(s): [list]

This workflow command depends on agents and skills from other anvil-toolset plugins.
Install them with:
  claude plugin marketplace add acaprino/anvil-toolset --plugin <name>

Or install the full marketplace:
  claude plugin marketplace add acaprino/anvil-toolset
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
2. Senior Code Review (Architecture + Security + Performance + Testing + Best Practices + Quality Scoring)
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

### Step 2A: Architecture Review (parallel with 2B)

Run steps 2A and 2B in parallel using multiple Agent tool calls in a single response.

```
Task:
  subagent_type: "senior-review:architect-review"
  description: "Architecture review enriched with deep dive context"
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
    - Attack scenario
    - Specific remediation steps

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

## Critical Issues for Phase 2C-2D Context

[List findings that affect testing, performance, or best practices review]
```

Update `state.json`: add steps 2A and 2B to `completed_phases`.

---

### Step 2C: Performance & Testing Review (parallel)

Run steps 2C and 2D in parallel.

### Step 2C: Performance Analysis

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
    1. **Database performance**: N+1 queries, missing indexes, unoptimized queries -- use flow traces to identify hot paths
    2. **Memory management**: Leaks, unbounded collections, large allocations
    3. **Caching**: Missing opportunities, stale cache risks, invalidation issues
    4. **I/O bottlenecks**: Synchronous blocking, missing pagination, large payloads
    5. **Concurrency**: Race conditions, deadlocks, thread safety
    6. **Scalability**: Horizontal scaling barriers, stateful components, single points of failure

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - Estimated performance impact
    - Specific optimization with code example

    Write your findings as a structured markdown document.
```

### Step 2D: Test Coverage Analysis

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
    2. **Test quality**: Behavior vs implementation testing, assertion quality
    3. **Test pyramid**: Unit vs integration vs E2E ratio
    4. **Edge cases**: Boundary conditions, error paths, concurrent scenarios
    5. **Security test gaps**: Are security-critical paths tested?
    6. **Integration gaps**: Are interface contracts (from deep dive) validated by tests?

    For each finding:
    - Severity (Critical / High / Medium / Low)
    - What is untested
    - Specific test recommendation

    Write your findings as a structured markdown document.
```

After 2C and 2D complete, consolidate into `.full-review-pipeline/03-performance-testing.md`:

```markdown
# Phase 2C-2D: Performance & Testing Review

## Performance Findings

[Summary from 2C, organized by severity]

## Test Coverage Findings

[Summary from 2D, organized by severity]
```

Update `state.json`: add steps 2C and 2D to `completed_phases`.

---

## PHASE CHECKPOINT 2 -- User Approval Required

Display a summary of all review findings so far:

```
Phases 1-2 (partial) complete: Deep dive + Architecture + Security + Performance + Testing.

Summary:
- Deep Dive Risks: [X critical, Y high, Z medium]
- Architecture: [X critical, Y high, Z medium findings]
- Security: [X critical, Y high, Z medium findings]
- Performance: [X critical, Y high, Z medium findings]
- Test Coverage: [X critical, Y high, Z medium findings]

Please review:
- .full-review-pipeline/02-architecture-security.md
- .full-review-pipeline/03-performance-testing.md

1. Continue -- proceed to quality scoring and final report
2. Fix critical issues first -- address findings before continuing
3. Pause -- save progress and stop here
```

If `--strict-mode` flag is set and there are Critical findings, recommend option 2.

Do NOT proceed until the user approves.

---

### Step 2E: Code Quality, Pattern Analysis & Scoring

Read all `.full-review-pipeline/*.md` files for full context.

```
Task:
  subagent_type: "senior-review:pattern-quality-scorer"
  description: "Code quality scoring enriched with deep dive and review context"
  prompt: |
    Perform comprehensive code quality review, pattern consistency analysis, and quantitative scoring.
    You have deep dive analysis AND prior review phase findings -- use all of them for calibrated scoring.

    ## Review Scope
    [Insert contents of .full-review-pipeline/00-scope.md]

    ## Deep Dive Context
    [Insert contents of .full-review-pipeline/01-deep-dive-summary.md]

    ## Prior Review Findings
    [Insert summaries from .full-review-pipeline/02-architecture-security.md and 03-performance-testing.md]

    ## Instructions

    ### Code Quality Analysis
    1. **Code complexity**: Cyclomatic/cognitive complexity, nesting depth
    2. **Maintainability**: Naming, function length, class cohesion
    3. **Code duplication**: Copy-pasted logic, missed abstractions
    4. **Clean Code**: SOLID violations, code smells
    5. **Technical debt**: Areas increasingly costly to change
    6. **Error handling**: Missing handling, swallowed exceptions

    ### Pattern Consistency Detection
    For each file, identify dominant patterns and flag deviations:
    - Error handling style
    - Resource management
    - Import conventions
    - Null/optional handling
    - Async patterns

    ### Anti-Pattern Checklist
    Flag: god objects, premature optimization, callback hell, mutable global state,
    swallowed exceptions, tight third-party coupling, missing validation, sync I/O
    blocking event loops, DB queries in loops, missing transaction boundaries, no rollback,
    TODO/FIXME in critical paths.

    ### Mental Models (all six)
    - **Security Engineer**: All input is malicious
    - **Performance Engineer**: Big-O and I/O patterns
    - **Team Lead**: Maintainable in 6 months?
    - **Systems Architect**: How does this fail? Blast radius?
    - **SRE**: What breaks at 3 AM?
    - **Pattern Detective**: Dominant patterns, then scan for violations

    ### Quantitative Code Quality Score
    Rate using ALL findings from deep dive + all review phases:
    - **9-10**: Excellent -- production-ready, exemplary
    - **7-8**: Good -- minor issues, safe to deploy
    - **5-6**: Adequate -- notable issues, fix before deploy
    - **3-4**: Poor -- significant issues, needs rework
    - **1-2**: Critical -- fundamental problems, unsafe

    Provide scores for: Security, Performance, Maintainability, Testing, Architecture, Overall.

    Write findings as structured markdown with Executive Summary, findings, What's Done Well, and Score table.
```

Write to `.full-review-pipeline/04-quality-scoring.md`:

```markdown
# Phase 2E: Code Quality, Pattern Analysis & Scoring

## Executive Summary

[2-3 sentence overview]

## Code Quality Findings

[Organized by severity]

## Pattern Consistency Findings

[Pattern deviations, anti-patterns]

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
| **Overall**     | **X/10** |
```

Update `state.json`: add step 2E to `completed_phases`.

---

## Phase 3: Consolidated Report

Read all `.full-review-pipeline/*.md` files (dd-* through 04). Generate the final consolidated report.

**Output file:** `.full-review-pipeline/05-final-report.md`

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
| **Overall**     | **X/10** |

## Deep Dive Insights

[Key structural and semantic findings that informed the review]

## Findings by Priority

### Critical Issues (P0 -- Must Fix Immediately)

[All Critical findings from deep dive + all review phases, with source reference]

### High Priority (P1 -- Fix Before Next Release)

[All High findings]

### Medium Priority (P2 -- Plan for Next Sprint)

[All Medium findings]

### Low Priority (P3 -- Track in Backlog)

[All Low findings]

## Findings by Category

- **Architecture**: [count] findings ([breakdown])
- **Security**: [count] findings ([breakdown])
- **Performance**: [count] findings ([breakdown])
- **Code Quality**: [count] findings ([breakdown])
- **Pattern Consistency**: [count] findings ([breakdown])
- **Testing**: [count] findings ([breakdown])
- **Technical Debt**: [count] findings ([breakdown])

## Recommended Action Plan

1. [Ordered list starting with critical items]
2. [Group related fixes]
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
- Performance & Testing: .full-review-pipeline/03-performance-testing.md
- Quality Scoring: .full-review-pipeline/04-quality-scoring.md
- Final Report: .full-review-pipeline/05-final-report.md

## Summary
- Total findings: [count]
- Critical: [X] | High: [Y] | Medium: [Z] | Low: [W]
- Code Quality Score: [X/10]

## Next Steps
1. Review the full report at .full-review-pipeline/05-final-report.md
2. Address Critical (P0) issues immediately
3. Plan High (P1) fixes for current sprint
4. Add Medium (P2) and Low (P3) items to backlog
```

If `--strict-mode` is set and Critical findings exist:
```
STRICT MODE: Unresolved critical issues found. Review .full-review-pipeline/05-final-report.md before merging.
```
