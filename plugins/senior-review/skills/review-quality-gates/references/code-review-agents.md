# Code-review agent prompts (Agents A-N)

Full spawn prompts for `/senior-review:code-review` Step 3. The command's dispatch
table names each agent, its `subagent_type`, and its run condition; this file holds
the complete `Agent tool call` block to use verbatim (with the shared Intent and
Diff Scope instructions substituted in). Loaded on demand by the command; not used
by `/senior-review:team-review`, whose reviewers carry their prompts in their agent
definitions.

### Agent A: Code Audit (Architecture + Failure Flow + Pattern Consistency + Scoring)

```
Agent tool call:
  - description: "Code audit for senior-review command"
  - subagent_type: "senior-review:code-auditor"
  - run_in_background: true
  - prompt: |
    Perform a comprehensive code audit of the following changes covering architecture,
    failure flow analysis, pattern consistency, and quality scoring.
    You have both the diff AND the full file contents for context.

    ## Changed Files
    [list of changed code files with line counts]

    ## Full File Contents
    [paste full contents of each changed file]

    ## Diff
    [paste the git diff output]

    ## Recent Commit History
    [paste git log output -- shows business context for changed files]

    ## Project Conventions (from CLAUDE.md)
    [paste relevant conventions, or "none found"]

    ## Instructions
    Analyze the CHANGED code in context across all dimensions:

    **Architecture & Code Quality:**
    1. Design concerns -- coupling, broken abstractions, inappropriate patterns
    2. Code quality -- naming, complexity, duplication
    3. Error handling -- missing or incorrect in new/modified code
    4. Over/under-engineering -- is the solution appropriately scoped?
    5. CLAUDE.md compliance -- do changes follow project conventions?
    6. Flow correctness -- trace modified flows within provided files. If the flow calls external modules not present in context, state "Cannot verify downstream impact in [Module] -- out of scope" rather than guessing.

    **Failure Flow Analysis:**
    7. Resource lifecycle -- are DB connections, file handles, temp files cleaned up on BOTH success AND error paths (try/finally)? If the process is killed during an async operation, what state is left behind?
    8. Persisted state validity -- if code writes cache/state files for later resume, is there a validity key to detect stale data? Can a resumed run silently produce wrong results?
    9. Kill point analysis -- for each await/async operation, simulate termination. What persisted state is left inconsistent?
    10. Cache invalidation -- can stale cached results be silently mixed with fresh results?
    11. Concurrency under failure -- if one task fails or parent is killed, what happens to siblings?

    **Pattern Consistency:**
    12. Identify dominant patterns per file, flag deviations in the diff
    13. Run the 16-item anti-pattern checklist
    14. Check CLAUDE.md compliance

    **Scoring:**
    15. Produce a quantitative Code Quality Score (Security, Performance, Maintainability, Consistency, Resilience, Overall -- each X/10)

    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100), concrete fix.
    Include the full scoring table in your output.
```

### Agent B: Security Assessment

```
Agent tool call:
  - description: "Security review for senior-review command"
  - subagent_type: "senior-review:security-auditor"
  - run_in_background: true
  - prompt: |
    Review the following code changes for security vulnerabilities.
    You have both the diff AND the full file contents for context.

    ## Changed Files
    [list of changed code files]

    ## Full File Contents
    [paste full contents of each changed file]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Check the CHANGED code for:
    1. Injection risks -- SQL, command, XSS injection
    2. Input validation -- missing or insufficient
    3. Auth/authz -- flawed logic, missing checks, privilege escalation
    4. Secrets exposure -- hardcoded credentials, tokens, keys
    5. Insecure defaults -- debug mode, verbose errors, permissive CORS
    6. Dependency risks -- new packages trustworthy and up to date?
    7. Data exposure -- sensitive data in logs, errors, responses

    For each finding: severity, CWE if applicable, file + line, confidence (0-100), attack scenario, concrete fix.
```

### Agent B2: Dead Code, Unused Parameters & VCS Hygiene

This is the **lite** codebase-hygiene pass, and it draws from two owners. Dead
code is `senior-review:cleanup-auditor` D1. The VCS half is the
`repo-hygiene:repo-hygiene` skill at its **lite** profile, which is the same
check definitions the full pass uses with the perimeter narrowed to files the
diff adds. Load the `repo-hygiene:repo-hygiene` skill rather than restating its patterns here: one
definition, two perimeters, no drift.

Both halves are diff-scoped. The **full** passes belong elsewhere and this agent
never reaches for them: orphan assets, dependency and barrel-file hygiene and
stale documentation to `senior-review:cleanup-auditor` in
`/senior-review:team-review`, and whole-tree workspace hygiene to
`repo-hygiene:workspace-auditor`. The lite profile exists precisely so this
agent cannot widen: its checks C4 through C7 are repository-historical and are
not available at this perimeter, because a stale ignore rule or an old stash
cannot have been caused by the diff under review.

```
Agent tool call:
  - description: "Dead code and diff-scoped VCS hygiene detection for senior-review command"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Detect dead code, unused parameters, and VCS hygiene defects in the files
    changed by the diff. Use BOTH automated tools AND manual analysis.

    ## Changed Files
    [list of changed code files with line counts]

    ## Full File Contents
    [paste full contents of each changed file]

    ## Diff
    [paste the git diff output]

    ## Phase 1: Automated Lint (MANDATORY)

    You MUST run actual linting tools via Bash on the changed files. Do NOT
    skip this phase or substitute it with manual reading.

    **Auto-detect language from changed file extensions:**

    ### Python files (.py)

    Run ruff on EACH changed Python file. Use the project's ruff config
    first (respects pyproject.toml/ruff.toml rules including isort, style
    checks, etc.). Only fall back to a manual --select if no config exists:

    ```bash
    # Step 1: Check if project has ruff config
    # Look for [tool.ruff] in pyproject.toml, or ruff.toml/.ruff.toml

    # Step 2a: If ruff config exists -- use it (catches ALL configured rules)
    ruff check --output-format json <file>

    # Step 2b: If NO ruff config -- use broad defaults
    ruff check --select E,F,I,W,ARG --output-format json <file>
    ```

    Rule coverage with broad defaults:
    - E: pycodestyle errors (E402 module-level import not at top, etc.)
    - F: pyflakes (F401 unused imports, F841 unused variables, F811 redefined names)
    - I: isort (I001 import sorting)
    - W: pycodestyle warnings
    - ARG: unused arguments (ARG001-ARG005)

    If `ruff` is not on the PATH, run it through `uvx ruff` instead (no
    environment mutation). If `uvx` is unavailable too, do NOT install
    anything: a review is observational and must not modify the environment.
    Report "Ruff unavailable -- automated Python lint dimension degraded"
    and proceed to Phase 2.

    Also run vulture on each changed Python file if available:

    ```bash
    vulture --min-confidence 80 <file>
    ```

    If vulture is not installed, skip it (ruff covers the critical rules).

    ### TypeScript/JavaScript files (.ts, .tsx, .js, .jsx)

    If the project has a tsconfig.json, run:

    ```bash
    npx knip --include files,exports,dependencies --no-progress
    ```

    If knip is not available, use the TypeScript compiler for unused checks:

    ```bash
    npx tsc --noEmit --noUnusedLocals --noUnusedParameters 2>&1 | grep -E "(changed files pattern)"
    ```

    ### Other languages

    Skip automated lint; rely on Phase 3 manual analysis.

    ## Phase 2: VCS Hygiene (MANDATORY)

    Dead code is not the only hygiene defect a diff can introduce. Check the
    changed files for artifacts that should never have been committed. This
    phase is cheap and its false-positive rate is near zero, which is why it
    runs on every review instead of waiting for a full team-review.

    Scope it to the changed files only, same as Phase 1.

    ```bash
    # 1. Generated artifacts newly tracked by this diff
    #    (build output, bundles, coverage, compiled assets, lockfile-adjacent
    #     caches, editor and OS metadata)
    git diff --name-only --diff-filter=A $BASE...HEAD | grep -iE \
      '(^|/)(dist|build|out|coverage|\.next|\.nuxt|target|__pycache__|node_modules)/|\.(pyc|pyo|class|o|so|dll|map|tsbuildinfo)$|(^|/)\.DS_Store$|(^|/)Thumbs\.db$'

    # 2. Filesystem garbage (shell-redirection artifacts and stray files)
    git diff --name-only --diff-filter=A $BASE...HEAD | grep -iE \
      '(^|/)(nul|con|prn|aux)$|\.(bak|old|orig|swp|tmp)$'

    # 3. .gitignore gap: for every hit above, check whether a pattern already
    #    covers it. A tracked file matching an existing pattern means it was
    #    committed before the pattern was added and needs `git rm --cached`.
    git check-ignore -v <path>
    ```

    Report each hit as a finding. Never delete anything here. Removal of what
    this half finds belongs to `/repo-hygiene:tidy`, not to Step 7c, which no
    longer owns the `garbage` or `gitignore` phases. Name the owning command
    alongside the phase so the finding routes without being re-derived.

    ## Phase 3: Manual Diff Analysis

    After collecting lint results, also manually analyze the diff for issues
    that linters miss:

    1. Unreachable code -- code after return/raise/break added by the diff
    2. Unused exports -- new exports that no consumer imports
    3. Orphaned code -- existing code that became dead because the diff
       removed its only caller
    4. Parameters accepted but never read in the function body (cross-check
       with ARG results from Phase 1 to avoid duplicates)

    ## Filtering Rules

    Report ONLY findings related to code introduced or exposed by the diff.

    Do NOT flag:
    - Pre-existing issues unrelated to the diff
    - Framework conventions (Django views, pytest fixtures, signal handlers,
      route decorators, FastAPI dependencies, click/typer callbacks)
    - Symbols exported via __all__, used via getattr, referenced dynamically,
      or used as configuration keys looked up at runtime
    - Dunder methods (__init__, __str__, etc.)
    - Parameters prefixed with _ (conventional unused marker)
    - Abstract method parameters (required by interface contract)
    - **kwargs / **args intentionally passed through

    To filter: cross-reference each lint finding's file and line against the
    diff hunks. Discard findings on lines NOT touched by the diff.

    ## Output Format

    For each finding provide:
    - Source: "ruff [RULE]", "vulture", "knip", "tsc", "vcs", or "manual"
    - Severity (High / Medium / Low)
    - File + line (for VCS findings, the path alone)
    - Confidence score (0-100)
    - Load-bearing premise: the single proposition whose falsity collapses this
      finding. Minimal, falsifiable, scoped. Not a paraphrase of the finding
    - premise_provenance: independent | shared-context | mixed (causal dependence
      on the X-ray output or interconnect map, not citation of it)
    - What is unused or misplaced, and why
    - Recommended action (remove, prefix with _, verify dynamic usage, add to
      __all__, or `/repo-hygiene:tidy` for anything the filesystem and git decide)
    - Fix phase, owner-qualified: `/senior-review:code-review --commit` phase
      `exports` for dead code, `/repo-hygiene:tidy` phase `garbage` or
      `gitignore` for VCS findings. A bare phase name is ambiguous now that two
      commands own disjoint phase sets, so always name the command
```

### Agent C: UI Race Condition Analysis

**Only run this agent if the changed files include UI/frontend code** (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, `.qml`, or files containing scroll/focus/layout manipulation).

```
Agent tool call:
  - description: "UI race condition analysis for senior-review command"
  - subagent_type: "senior-review:ui-race-auditor"
  - run_in_background: true
  - prompt: |
    Analyze the following UI code changes for race conditions between async rendering,
    layout, and event handlers.
    You have both the diff AND the full file contents for context.

    ## Changed Files
    [list of changed code files]

    ## Full File Contents
    [paste full contents of each changed file]

    ## Diff
    [paste the git diff output]

    ## Project Conventions (from CLAUDE.md)
    [paste relevant conventions, or "none found"]

    ## Instructions
    Analyze the CHANGED code for UI timing bugs:

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

    For each finding: severity (Critical/High/Medium/Low), step-by-step timeline
    (T0->T1->...->RESULT), file + line, confidence (0-100), concrete fix.
```

### Agent D: Platform Engineering Review

**Only run this agent if fullstack app signals were detected** (2+ signals from auto-detection in Step 1). Skip entirely for libraries, CLI tools, or single-layer projects.

`platform-engineering` is a hard dependency of `senior-review`, so this agent is always available. Skip the dimension only when the fullstack signal did not match.

```
Agent tool call:
  - description: "Platform engineering review for senior-review command"
  - subagent_type: "platform-engineering:platform-reviewer"
  - run_in_background: true
  - prompt: |
    Review the following code changes against the platform-engineering rulebook.
    You have both the diff AND the full file contents for context.

    ## Platforms Detected
    [list detected platform signals: SPA, PWA, Mobile, Electron, Tauri]

    ## Changed Files
    [list of changed code files]

    ## Full File Contents
    [paste full contents of each changed file]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Evaluate the CHANGED code against platform-engineering rules:
    1. **Server validation**: Is business logic (prices, discounts, eligibility)
       validated server-side? Are client-only checks trusted?
    2. **Auth token storage**: Are JWTs in localStorage? Missing httpOnly/Secure/SameSite?
       OAuth flow correct for the platform?
    3. **API security**: Unauthenticated endpoints? Missing rate limiting? Permissive CORS?
       Verbose error responses? GraphQL introspection exposed?
    4. **XSS/CSP**: Weak or missing CSP? dangerouslySetInnerHTML with user data?
       unsafe-inline/unsafe-eval?
    5. **Secrets exposure**: API keys in frontend bundles? REACT_APP_/VITE_/NEXT_PUBLIC_ secrets?
    6. **Architecture**: Business logic in client code? Missing API versioning? Missing pagination?
       Direct DB connections from client?
    7. **Performance**: Bundle size over budget? Missing code splitting? Unoptimized images?
       N+1 queries? Missing connection pooling?
    8. **Platform-specific**: Electron (nodeIntegration, contextIsolation, sandbox)?
       Tauri (overly permissive commands)? Mobile (cert pinning, memory leaks)?

    For each finding: severity (MUST/DO/DON'T), file + line, confidence (0-100),
    real-world incident reference if applicable, concrete fix.
```

### Agent E: Git Blame & History Analysis

Run in parallel with Agents A-D. Provides historical context that other agents lack.

```
Agent tool call:
  - description: "Git blame and history analysis for senior-review command"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Analyze the git history and blame data for the following changed files to find
    history-based issues that pure code analysis would miss.

    ## Changed Files
    [list of changed code files]

    ## Diff
    [paste the git diff output]

    ## PR Context
    [PR title and description, or branch name and recent commit messages]

    ## Instructions

    For each changed file, run:

    ```bash
    # Recent history (last 10 commits on this file)
    git log -n 10 --oneline --format="%h %ad %s" --date=short <file>

    # Blame on changed line ranges
    git blame -L <start>,<end> <file>

    # Churn frequency (commits in last 30 days)
    git log --since="30 days ago" --oneline <file> | wc -l
    ```

    Look for these patterns:
    1. **High churn** -- file changed 3+ times in the last month. Flag as risk factor
       with recent commit subjects for context.
    2. **Revert-reintroduce** -- the diff reintroduces code or patterns that were
       previously removed or reverted. Cross-reference with `git log` subjects.
    3. **Contradicting recent fixes** -- the change modifies lines that were part of
       a recent bugfix. The new change might undo the fix.
    4. **Single-author hotspot** -- all recent changes by one author, now modified
       by someone else. Flag for knowledge transfer risk.
    5. **Stale context** -- blame shows surrounding code unchanged for 1+ year while
       the diff assumes behavior that may have drifted.

    For each finding: severity (High/Medium/Low), file + line, confidence (0-100),
    description with specific commit references (hashes and subjects).

    If no history-based issues found, say so explicitly.
```

### Agent F: Testing Review (conditional)

**Only run this agent if the diff touches test files** (`test_*`, `*_test.*`, `*.spec.*`, `*.test.*`, `conftest.py`, `fixtures/`, `__tests__/`).

The `testing` plugin is a hard dependency of `senior-review`, so `testing:test-suite-auditor` is always available. There is no generic fallback variant: a spawn failure here means a broken install, not a missing optional plugin.

```
Agent tool call:
  - description: "Testing review for senior-review command"
  - subagent_type: "testing:test-suite-auditor"
  - run_in_background: true
  - prompt: |
    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed test files + their corresponding source files]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Run your detection pipeline scoped to the modules owned by the changed
    test files (D2 to D8 on those modules; D1/D9 statistics suite-wide as
    context only). Do NOT run the full suite inside this review (no-run
    semantics): reuse CI history or existing report artifacts, and mark
    anything unmeasured as such.

    For each finding: severity (Critical/High/Medium/Low), file + line,
    confidence (0-100), description, suggested fix path.

    If the changed tests look solid, say so explicitly.
```

### Agent G: API Contract Review (conditional)

**Only run this agent if the diff touches API-related files** (route definitions, serializers, type signatures, API versioning, OpenAPI/Swagger specs, GraphQL schemas).

```
Agent tool call:
  - description: "API contract review for senior-review command"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Review the API contract changes for backwards compatibility and correctness.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed API-related files]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Analyze the CHANGED API code for:
    1. **Breaking changes** -- removed fields, renamed endpoints, changed response
       shapes, tightened input validation that rejects previously valid requests
    2. **Versioning** -- is the change backwards compatible? If not, is there a
       version bump or migration path?
    3. **Input validation** -- new endpoints missing validation, overly permissive
       schemas, type coercion risks
    4. **Response consistency** -- error response format matches existing patterns,
       pagination follows conventions, status codes are correct
    5. **Documentation sync** -- if OpenAPI/Swagger specs exist, do they match the
       implementation changes?

    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100),
    description, suggested fix.
```

### Agent H: Data Migrations Review (conditional)

**Only run this agent if the diff touches migration files** (database migrations, schema changes, backfill scripts, Alembic/Django/Rails/Prisma migration files).

```
Agent tool call:
  - description: "Data migrations review for senior-review command"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Review the database migration changes for safety and correctness.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed migration files]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Analyze the migration for:
    1. **Reversibility** -- is the migration reversible? Is there a down/rollback
       function? Would rollback lose data?
    2. **Lock risk** -- will the migration lock tables during execution? For large
       tables: does it use batched operations or online DDL?
    3. **Data integrity** -- does the migration preserve existing data? Are NOT NULL
       constraints added with proper defaults? Are foreign keys safe?
    4. **Ordering** -- does this migration depend on another migration running first?
       Is the dependency declared?
    5. **Backfill safety** -- if backfilling data: is it batched? Is there a progress
       indicator? What happens if it fails midway?
    6. **Zero-downtime compatibility** -- can old code run against the new schema
       and vice versa? (column additions are safe, renames/removals are not)

    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100),
    description, suggested fix.
```

### Agent I: React Performance Review (conditional)

**Only run this agent if the diff touches `.tsx` or `.jsx` files AND the project has React as a dependency** (check `package.json` for `react` in dependencies/devDependencies).

`react-development` is a hard dependency of `senior-review`, so this agent is always available. Skip the dimension only when the React signal did not match.

```
Agent tool call:
  - description: "React performance review for senior-review command"
  - subagent_type: "react-development:react-performance-optimizer"
  - run_in_background: true
  - prompt: |
    Review the following React code changes for performance issues,
    anti-patterns, and optimization opportunities.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed .tsx/.jsx files]

    ## Full File Contents
    [paste full contents of each changed React file]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Analyze the CHANGED React code for:
    1. **React Compiler compatibility** -- patterns that break automatic memoization
       (external mutables, dynamic property access, non-idiomatic hooks)
    2. **Server Components** -- client-only APIs in server components, missing
       'use client' directives, unnecessary client boundaries
    3. **Re-render optimization** -- missing keys, unstable references in props,
       inline object/function creation in render, expensive computations without
       useMemo/useCallback where warranted
    4. **State management** -- derived state that should be computed, unnecessary
       state, state that belongs higher/lower in the tree
    5. **Bundle impact** -- large imports that could be lazy-loaded, barrel file
       re-exports pulling in unused code
    6. **External store subscriptions** -- useSyncExternalStore patterns,
       tearing risks with concurrent features

    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100),
    description, concrete fix with code example.
```

### Agent J: Structural Entropy Review (conditional)

**Run this agent whenever the diff adds code**, meaning at least one added function, method, class, module, constant table, or block longer than roughly five lines. Skip it for diffs that are purely deletions, renames, formatting, or config edits.

This is the only agent whose question is about the rest of the codebase rather than about the diff. Every other agent reads the diff and judges it on its own terms; this one takes the diff as an anchor and asks whether it adds a second place where a concept the codebase already owns now lives. It covers seven dimensions over two evidence tracks: duplicated domain knowledge, competing sources of truth, redundant representation, and duplicated or derivable state on the knowledge track, judged by semantic identity and ownership; missed unification, prior art available, and abstraction fitness on the form track, judged by recurrence. The knowledge-track questions are seeded by a concept index at `.abstraction-architect/concept-index.json` when one exists; without it the agent degrades to diff-anchored discovery and says so.

`abstraction-architect` is a hard dependency of `senior-review`, so this agent is always available. Skip the dimension only when the diff adds no code. There is no fallback and none is needed: the check depends on that agent's dimension catalog, evidence gates and decision frame, and a freelance grep for similar names produces false positives that cost more than the finding is worth.

```
Agent tool call:
  - description: "Structural entropy review for senior-review command"
  - subagent_type: "abstraction-architect:abstraction-architect"
  - run_in_background: true
  - prompt: |
    [Include shared instructions: Intent + Diff Scope]

    mode: diff
    codebase_path: [repo root]
    xray_path: [.codebase-xray/ if Step 2 produced one, otherwise "none"]
    concept_index_path: [repo root]/.abstraction-architect/concept-index.json
    changed_files: [list of changed files]
    report_path: [scratch path for this review]
    severity_floor: medium

    ## Diff
    [paste the git diff output]

    ## Instructions
    Follow the `PROCESS (mode = diff)` section of your agent definition.

    Your search space is the WHOLE codebase, not the diff. The prior
    representation you are hunting for is by definition in files that did not
    change, so never limit Grep to the changed files.

    Use your own report contract: sections A to G in precedence order (D2
    competing sources of truth, D4 duplicated or derivable state, D3 redundant
    representation, D1 duplicated domain knowledge, D6 prior art available, D5
    missed unification, D7 abstraction fitness), one primary dimension per
    finding, then section H for second occurrences noted but not flagged, then
    section I for confidence and gaps.

    Do NOT re-flag single-file smells that `senior-review:code-auditor` already
    owns: leaky abstractions, premature interfaces with one implementation, and
    god objects visible inside one file. Your findings must cite at least one
    site outside the diff.

    For each finding: its primary dimension (D1 to D7), severity
    (Critical/High/Medium/Low), file + line for BOTH the new code and the
    existing representation it collides with, confidence (0-100), the
    behavioral difference if any, and the suggested direction in one sentence.
```

### Agent K: TypeScript Type-Safety Review (conditional)

**Only run this agent if the diff touches `.ts` or `.tsx` files AND `tsconfig.json` exists at the project root.** On React projects both Agent I and Agent K run: the charters are orthogonal (performance vs type safety) and consolidation deduplicates any collision.

`typescript-development` is a hard dependency of `senior-review`, so this agent is always available. Skip the dimension only when the TypeScript signal did not match.

```
Agent tool call:
  - description: "TypeScript type-safety review for senior-review command"
  - subagent_type: "typescript-development:type-safety-auditor"
  - run_in_background: true
  - prompt: |
    Review the following TypeScript changes for type-system erosion.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed .ts/.tsx files]

    ## tsconfig
    [paste tsconfig.json and any extended configs]

    ## Full File Contents
    [paste full contents of each changed TypeScript file]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Analyze the CHANGED TypeScript code for:
    1. **Any erosion**: explicit any, untyped JSON.parse and response.json() results, any generic defaults
    2. **Unsound casts**: shape-changing as casts without runtime checks, as unknown as bypasses
    3. **Boundary validation**: HTTP payloads, queue messages, storage reads, and env access reaching typed code without a schema parse or guard
    4. **Assertion abuse**: unjustified non-null assertions, @ts-ignore instead of @ts-expect-error with reason
    5. **Configuration drift**: strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes missing or weakened by this diff
    6. **Exhaustiveness**: discriminated-union switches without never defaults, lookup tables without satisfies
    7. **Generics soundness**: unconstrained exported type parameters, type predicates that do not verify the shape they claim

    Cite rule ids from the type-safety-rules skill in every finding.
    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100),
    description, concrete fix with a code example.
```

### Agent L: Temporal Resilience Review (conditional)

**Only run this agent if the diff touches long-running or scheduled execution machinery**: timers (`setInterval`/`setTimeout` chains, cron), polling loops, retry/reconnect/backoff logic, queue workers, background daemons, updaters, watchdogs, or heartbeats. Detection: grep the diff for `setInterval|setTimeout|cron|schedule|retry|reconnect|backoff|watchdog|heartbeat|keepalive|poll|daemon|updater`. This agent lives in `senior-review` itself, so there is no plugin-availability check.

This dimension exists because the synchronous lenses (A through K) each see the code in an instant; none of them owns the question "what does the user see after this has been failing for a day". Resilience findings otherwise fall on the seam between architecture and performance, and each reviewer sees only half.

```
Agent tool call:
  - description: "Temporal resilience review for senior-review command"
  - subagent_type: "senior-review:temporal-resilience-auditor"
  - run_in_background: true
  - prompt: |
    Review the following changes for failure-over-time behavior.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed files matching the temporal signals]

    ## Full File Contents
    [paste full contents of each changed file containing temporal machinery]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Follow your agent definition's analysis phases: inventory the temporal
    machinery, run the three-horizon failure analysis (1st failure, Nth failure,
    never-ending failure), hunt silent-death paths (unbounded awaits, guard
    flags without finally, timers that stop re-arming, catch-and-continue
    erosion, missing escalation), trace the user-visible consequence of every
    failure path, and check clock/suspend/DST hazards.

    Label every quantitative claim `measured` or `derived` per your EVIDENCE
    CLASSES section. If you build a measurement harness, keep it outside the
    work tree and delete it; report the numbers and method in the finding.

    For each finding: severity (Critical/High/Medium/Low), file + line,
    confidence (0-100), failure chain, quantified damage with evidence class,
    user-visible consequence, concrete fix.
```


### Agent M: Data Integrity Review (conditional)

**Only run this agent if the diff touches persistence code**: schemas, models, ORM entities, repositories, raw SQL, cache layers, or transaction boundaries. Detection: grep the diff for `transaction|commit|rollback|UPDATE |INSERT |upsert|unique|constraint|ON CONFLICT|FOR UPDATE|select_for_update|session\.add|\.objects\.|prisma\.|typeorm|sqlalchemy|redis|cache\.` . This agent lives in `senior-review` itself, so there is no plugin-availability check.

This dimension is distinct from logic integrity: a domain rule violated in application logic is theirs; a store that can be MADE to hold an impossible state (the invariant lives in code, not in the schema, and a race or out-of-band write gets past it) is this agent's territory.

```
Agent tool call:
  - description: "Data integrity review for senior-review command"
  - subagent_type: "senior-review:data-integrity-auditor"
  - run_in_background: true
  - prompt: |
    Review the following changes for persistence-semantics defects.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed files matching the persistence signals]

    ## Schema Context
    [paste relevant schema definitions: migrations, ORM models, CREATE TABLE,
    Prisma/Drizzle schemas for the tables the diff touches]

    ## Full File Contents
    [paste full contents of each changed file touching persistence]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Follow your agent definition's analysis phases: inventory the write paths,
    map every invariant to where it is enforced (code / schema / both / neither),
    hunt concurrency anomalies (read-modify-write, check-then-act, isolation
    assumptions, retried writes without idempotency), check multi-store
    divergence (cache/DB, projections), and audit representation hazards
    (soft delete, time, money, NULL semantics, pagination).

    For each finding: severity (Critical/High/Medium/Low), file + line,
    confidence (0-100), the invariant and its enforcement gap, a concrete
    corruption scenario (interleaving or failure), who reads the corrupted
    state, concrete fix (constraint DDL / transaction / lock / version column).
```

### Agent N: Resource Lifecycle Review (conditional)

**Only run this agent if the diff acquires or manages resources**: files, sockets, streams, DB connections, subprocesses, event listeners, subscriptions, locks, tasks/threads/goroutines, timers, or object URLs. Weight the signal higher for manual-resource languages (C/C++/Rust/Go) and async-heavy code. Detection: grep the diff for `open\(|createReadStream|createWriteStream|socket|getConnection|acquire|addEventListener|subscribe\(|lock|mutex|semaphore|new Worker|subprocess|Popen|spawn\(|go func|tokio::spawn|asyncio\.create_task|createObjectURL`. This agent lives in `senior-review` itself, so there is no plugin-availability check.

```
Agent tool call:
  - description: "Resource lifecycle review for senior-review command"
  - subagent_type: "senior-review:resource-lifecycle-auditor"
  - run_in_background: true
  - prompt: |
    Review the following changes for resource ownership and release defects.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed files matching the acquisition signals]

    ## Full File Contents
    [paste full contents of each changed file acquiring resources]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Follow your agent definition's analysis phases: inventory every acquisition,
    verify all three exits (success, error, cancellation) for each, audit pool
    and registry discipline (bounded pools, return-on-error, growing maps,
    timer accumulation, abandoned tasks), and hunt lifetime mismatches
    (listener outlives subject, resource outlives owner, owner outlives
    resource).

    For each finding: severity (Critical/High/Medium/Low), file + line,
    confidence (0-100), the resource and its owner, which exit path is broken,
    the exhaustion scenario, concrete fix preferring structural constructs
    (with/defer/finally/RAII/AbortController/effect cleanup).
```

