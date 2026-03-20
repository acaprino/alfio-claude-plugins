---
description: >
  "Unified code review -- auto-detects scope and runs architecture, security, and pattern analysis agents in parallel. Automatically uses deep-dive context if available." argument-hint: "[PR number | --branch <name> | --commits N] [--auto-comment] [--strict] [--security-focus]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Code Review

You are a thorough code reviewer. Your job is to review code changes -- uncommitted edits, recent commits, a pull request, or a branch diff -- analyze them in depth, and produce a structured review with confidence-scored findings. Optionally post review comments directly on PRs.

## CRITICAL RULES

1. **Always review in context.** Read full files, not just diffs. Understand what the code does before judging changes.
2. **Score every finding.** Each finding gets a confidence score (0-100) indicating how certain you are it's a real issue.
3. **Check CLAUDE.md compliance.** If the project has a CLAUDE.md, verify changes follow its conventions.
4. **Never enter plan mode.** Execute immediately.
5. **Run agents in parallel.** Fire all review agents in a single response.
6. **Skip documentation files.** Ignore `.md`, `.txt`, `.rst`, `README*`, `CHANGELOG*`, `LICENSE*`. Focus only on code.

## Step 1: Identify Review Target

From `$ARGUMENTS`, determine what to review using this priority:

**Case A -- Uncommitted/staged changes exist** (no explicit PR or branch arg):

```bash
git diff --name-only          # unstaged changes
git diff --cached --name-only # staged changes
```

If either has results, use uncommitted changes as the review target. The diff source is "uncommitted changes".

**Case B -- `--commits N` flag provided:**

Use `git diff HEAD~N..HEAD` as the review target. The diff source is "last N commits".

**Case C -- PR number provided** (e.g. `42`, `#42`):

```bash
gh pr view 42 --json number,title,body,baseRefName,headRefName,files
gh pr diff 42
```

**Case D -- `--branch <name>` provided:**

```bash
git log main..<branch> --oneline
git diff main...<branch>
```

**Case E -- No arguments, no uncommitted changes:**

Detect current branch and compare against main/master:

```bash
CURRENT=$(git branch --show-current)
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff ${BASE}...${CURRENT}
```

If the branch is main/master with no diff, fall back to last commit (`HEAD~1..HEAD`).

### Filter code files

Exclude: `.md`, `.txt`, `.rst`, `.json` (config-only), `.yaml`/`.yml` (config-only), images, lock files.
Include: source code files (`.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.rs`, `.go`, `.java`, `.rb`, `.css`, `.scss`, `.html`, etc.)

If no code files remain, say so and stop.

## Step 2: Gather Context

For each changed code file:

1. **Read the full file** -- understand surrounding context
2. **Get the diff** -- know exactly what changed
3. **Get recent commit history for changed files** -- understand the business context behind the code

```bash
git log -n 5 --oneline <file>
```

4. **Check for past PR comments** on the same files (if reviewing a PR):

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '.[].path' | sort -u
```

5. **Read CLAUDE.md** if it exists -- note project conventions, naming rules, patterns

6. **Check for deep-dive context** (optional -- requires `deep-dive-analysis` plugin) -- if `.deep-dive/` exists and contains completed analysis files:
   - Read `.deep-dive/01-structure.md` for structural context
   - Read `.deep-dive/03-flows.md` for execution flow context
   - Read `.deep-dive/04-semantics.md` for design decision context
   - Read `.deep-dive/05-risks.md` for known risk context
   - Include a "Deep Dive Context" section in each agent's prompt (see template below)
   - Note in the review output that deep-dive context was used
   - If `.deep-dive/` does not exist or is incomplete, proceed normally without it -- this is expected behavior when the `deep-dive-analysis` plugin is not installed or hasn't been run

### Deep Dive Context Template

When deep-dive output is available, append this section to each agent prompt after existing context sections:

```
## Deep Dive Context

The following context was gathered from a prior deep-dive analysis. Use it to
strengthen your review. Do NOT re-report findings already covered here --
instead focus on new issues or issues that become apparent when combining
this context with your specialized perspective.

### Structure & Flows
[Insert relevant excerpts from 01-structure.md and 03-flows.md]

### Design Decisions & Assumptions
[Insert relevant excerpts from 04-semantics.md]

### Known Risks
[Insert relevant excerpts from 05-risks.md]
```

## Step 2b: Large Change Set Handling

Before proceeding, check the total size of changed code:

```bash
git diff --shortstat  # or the equivalent for the detected diff source
```

If total changed lines exceed 500, batch the files into groups of 3-5 files per agent invocation. Run each batch sequentially, consolidating findings across batches before scoring. This prevents context window overflow and "lost in the middle" attention degradation.

## Step 3: Run Parallel Review Agents

**Agent tool parameters (use ONLY these):** `description` (required), `prompt` (required), `subagent_type`, `run_in_background`, `model`, `isolation`, `resume`. Do NOT pass any other parameters -- the Agent tool rejects unknown fields.

Run all agents **in parallel** in a single response (Agent F only when UI files are in scope):

### Agent A: Architecture & Code Quality

```
Agent tool call:
  - description: "Architecture review for senior-review command"
  - subagent_type: "senior-review:architect-review"
  - run_in_background: true
  - prompt: |
    Review the following code changes for architectural soundness and code quality.
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
    Analyze the CHANGED code in context for:
    1. Design concerns -- coupling, broken abstractions, inappropriate patterns
    2. Code quality -- naming, complexity, duplication
    3. Error handling -- missing or incorrect in new/modified code
    4. Consistency -- do changes follow existing codebase patterns?
    5. Over/under-engineering -- is the solution appropriately scoped?
    6. CLAUDE.md compliance -- do changes follow project conventions?
    7. Flow correctness -- trace modified flows within provided files. If the flow calls external modules not present in context, state "Cannot verify downstream impact in [Module] -- out of scope" rather than guessing.
    8. Resource lifecycle -- are DB connections, file handles, temp files cleaned up on BOTH success AND error paths (try/finally)? If the process is killed during an async operation, what state is left behind?
    9. Persisted state validity -- if code writes cache/state files for later resume, is there a validity key to detect stale data? Can a resumed run silently produce wrong results?

    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100), concrete fix.
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

### Agent C: Pattern Consistency

```
Agent tool call:
  - description: "Pattern consistency analysis"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    You are a pattern consistency analyst. Analyze code changes for pattern deviations and anti-patterns.
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

    ### Pattern Consistency
    For each file, identify dominant patterns in the FULL file, then check if the DIFF follows them:
    - Error handling style, async patterns, naming conventions
    - Import conventions, null handling, resource management

    ### Anti-patterns
    Flag: swallowed exceptions, tight coupling, mutable globals, TODO in critical paths,
    hardcoded magic numbers, duplicated logic, missing type safety.

    ### CLAUDE.md Compliance
    Check each changed file against project conventions. Flag any deviations.

    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100), concrete fix.
```

### Agent D: Dead Code Detection

```
Agent tool call:
  - description: "Dead code detection for senior-review command"
  - subagent_type: "general-purpose"
  - run_in_background: true
  - prompt: |
    Analyze the following code changes for dead code introduced or exposed by the diff.
    You have both the diff AND the full file contents for context.

    ## Changed Files
    [list of changed code files with line counts]

    ## Full File Contents
    [paste full contents of each changed file]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Check ONLY for dead code introduced or exposed by the reviewed changes:
    1. Unused imports -- new imports added by the diff that are never referenced
    2. Unused functions/variables/constants -- new definitions (including module-level constants, class attributes, and configuration values) that are never called, read, or imported by any other module
    3. Unreachable code -- code after return/raise/break added by the diff
    4. Unused exports -- new exports that no consumer imports
    5. Orphaned code -- existing code that became dead because the diff removed its only caller

    Do NOT flag:
    - Pre-existing dead code unrelated to the diff
    - Framework conventions (Django views, pytest fixtures, signal handlers, route decorators)
    - Symbols exported via __all__, used via getattr, referenced dynamically, or used as configuration keys looked up at runtime
    - Dunder methods (__init__, __str__, etc.)

    For each finding provide:
    - Severity (High / Medium / Low)
    - File + line
    - Confidence score (0-100) -- how certain this is truly dead code
    - What is unused and why
    - Recommended action (remove, verify dynamic usage, add to __all__)
```

### Agent E: Failure Flow Analysis

```
Agent tool call:
  - description: "Failure flow analysis for senior-review command"
  - subagent_type: "senior-review:failure-flow-tracer"
  - run_in_background: true
  - prompt: |
    Trace failure paths, kill scenarios, and resume/retry correctness in the changed code.
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
    Analyze the CHANGED code for failure-path bugs:

    1. **Persisted State Map** -- Identify all files/databases/caches written by the changed code.
       For each: who writes, who reads, what validates it, what could invalidate it.

    2. **Kill Point Analysis** -- For each await/async operation in the diff, simulate process
       termination at that exact point. What persisted state is left inconsistent? Does the
       next run handle it?

    3. **Cache Invalidation** -- For every cached/persisted artifact, is there a validity key
       (hash, version, fingerprint)? If the source data changes between runs, is the cache
       properly invalidated? Can stale cached results be silently mixed with fresh results?

    4. **Resource Lifecycle** -- Are DB connections, file handles, temp files, subprocesses
       guaranteed to be cleaned up via try/finally or context managers? Check the ERROR path,
       not just the happy path.

    5. **Concurrency Under Failure** -- For asyncio.gather, thread pools, or parallel operations:
       if one task fails or the parent is killed, what happens to sibling tasks? Are side effects
       (file writes, DB updates) already committed? Is progress reporting accurate during
       concurrent execution or does it batch/delay?

    6. **Resume Correctness** -- If the code has resume/retry logic, trace the full cycle:
       start → partial completion → kill → resume. What assumptions does resume make about
       the environment? What if those assumptions are violated (input file changed, config
       changed, output dir moved)?

    For each finding: severity (Critical/High/Medium/Low), concrete step-by-step scenario,
    file + line, confidence (0-100), concrete fix.
```

### Agent F: UI Race Condition Analysis

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
    (T0→T1→...→RESULT), file + line, confidence (0-100), concrete fix.
```

## Step 4: Consolidate Agent Findings

After all five agents complete, collect and organize their findings into a single intermediate summary. Group findings by severity and category. This summary becomes the input for Step 4b.

## Step 4b: Quality Scoring

Run the pattern-quality-scorer agent with ALL findings from Step 4 to produce a calibrated quality score:

```
Agent tool call:
  - description: "Quality scoring with all agent findings"
  - subagent_type: "senior-review:pattern-quality-scorer"
  - prompt: |
    Produce a calibrated quality score for the reviewed code changes.
    You have the consolidated findings from all review agents -- use them to score accurately.

    ## Changed Files
    [list of changed code files]

    ## Full File Contents
    [paste full contents of each changed file]

    ## Diff
    [paste the git diff output]

    ## Agent Findings
    ### Architecture & Code Quality (Agent A)
    [paste findings from architect-review]

    ### Security (Agent B)
    [paste findings from security-auditor]

    ### Pattern Consistency (Agent C)
    [paste findings from pattern analysis]

    ### Dead Code (Agent D)
    [paste findings from dead code detection]

    ### Failure Flow (Agent E)
    [paste findings from failure-flow-tracer]

    ## Instructions
    Using ALL agent findings above, produce a quantitative quality score.

    Default score is 10/10. Deduct points based on severity and density of findings. Justify any score below 7 with specific deductions.

    | Category        | Score | Confidence |
    |-----------------|-------|------------|
    | Architecture    | X/10  | X%         |
    | Security        | X/10  | X%         |
    | Code Quality    | X/10  | X%         |
    | Consistency     | X/10  | X%         |
    | Resilience      | X/10  | X%         |
    | **Overall**     | **X/10** | **X%**  |

    Also provide:
    - Executive summary (2-3 sentences)
    - What's done well (positive observations)
    - Top concerns (most impactful issues across all categories)
```

## Step 5: Final Review Output

After scoring completes, synthesize everything into the final structured review:

```
## Code Review -- [PR title or branch name]

### Review Scope
- Files reviewed: [N]
- Lines changed: +X / -Y
- CLAUDE.md compliance: [checked / not found]

### Overall Score: X/10 (confidence: X%)

### Critical & High Findings
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|
| 1 | Critical | ...       | ...     | 95%        | ... |

### Medium & Low Findings
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### Dead Code Findings
| # | Severity | File:Line | Finding | Confidence | Action |
|---|----------|-----------|---------|------------|--------|

### Failure Flow & Resilience
| # | Severity | File:Line | Scenario | Confidence | Fix |
|---|----------|-----------|----------|------------|-----|

### Pattern Consistency
- [pattern deviations found, or "Changes follow established patterns"]

### CLAUDE.md Compliance
- [list any violations, or "All changes comply with project conventions"]

### Top 3 Recommended Actions
1. [highest priority]
2. [second priority]
3. [third priority]
```

If `--strict` and there are Critical findings:

```
STRICT MODE: Critical issues found. Recommend fixing before merging.
```

## Step 6: Auto-Comment on PR (if --auto-comment)

If `--auto-comment` flag is set and reviewing a PR:

Post only **CRITICAL and HIGH severity** findings as inline PR comments. Do NOT auto-comment MEDIUM or LOW findings -- include those only in the summary report. This prevents comment spam and focuses reviewer attention on what matters.

Write each comment body to a temp file first, then use `-F` to avoid shell injection from LLM-generated content:

```bash
# Write the comment body to a temp file (avoids shell escaping issues)
cat > .full-review/temp_inline_comment.md << 'COMMENT_EOF'
**[Severity]** -- [finding summary]

[concrete fix recommendation]
COMMENT_EOF

# Post as inline PR comment using -F (file input)
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  -F body=@.full-review/temp_inline_comment.md \
  -f path="[file]" \
  -f line=[line] \
  -f commit_id="$(gh pr view {number} --json headRefOid --jq '.headRefOid')"
```

Post the overall summary as a regular PR comment (also via temp file):

```bash
cat > .full-review/temp_summary_comment.md << 'SUMMARY_EOF'
## Automated Code Review

**Overall Score: X/10**

[summary of critical/high findings]

[top 3 recommended actions]

---
*Reviewed by: architect-review, security-auditor, pattern-quality-scorer, dead-code-detector, failure-flow-tracer*
SUMMARY_EOF

gh pr comment {number} -F .full-review/temp_summary_comment.md
```

$ARGUMENTS
