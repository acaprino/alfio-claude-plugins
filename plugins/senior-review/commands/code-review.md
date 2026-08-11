---
description: >
  Unified code review - auto-detects scope and runs architecture, security, dead-code and VCS-hygiene analysis in parallel, then optionally fixes and cleans up what it found. Automatically uses X-ray context if available.
  TRIGGER WHEN: the user asks for a code review, PR review, branch audit, security/architecture analysis of recent changes, or asks to find and remove dead code, unused exports, unused dependencies, orphan assets, or generated artifacts committed to git.
  DO NOT TRIGGER WHEN: a full multi-phase pipeline is needed (use /senior-review:team-review) or reviewing a single file for style (use clean-code).
argument-hint: "[PR number | --branch <name> | --commits N] [--fix] [--commit] [--auto-comment] [--strict] [--security-focus] [--fast] [--rigorous]"
---

# Code Review

You are a thorough code reviewer. Your job is to review code changes (uncommitted edits, recent commits, a pull request, or a branch diff), analyze them in depth, and produce a structured review with confidence-scored findings. Optionally post review comments directly on PRs.

## CRITICAL RULES

1. **Always review in context.** Read full files, not just diffs. Understand what the code does before judging changes.
2. **Score every finding.** Each finding gets a confidence score (0-100) indicating how certain you are it's a real issue.
3. **Check CLAUDE.md compliance.** If the project has a CLAUDE.md, verify changes follow its conventions.
4. **Never enter plan mode.** Execute immediately.
5. **Run agents in parallel.** Fire all review agents in a single response.
6. **Skip documentation files.** Ignore `.md`, `.txt`, `.rst`, `README*`, `CHANGELOG*`, `LICENSE*`. Focus only on code.

## Step 0: Pre-Review Skip Check (PR only)

If `$ARGUMENTS` contains a PR number (Case C), run a quick eligibility check **before** gathering any context. Launch a **haiku** agent that checks:

```bash
# Fetch PR metadata
gh pr view <N> --json state,isDraft,author,title,labels

# Check for prior Claude comments
gh pr view <N> --comments --json comments --jq '.comments[].author.login'
```

**Skip the review and stop** if ANY of these are true:
- PR state is `CLOSED` or `MERGED`
- PR is a draft (`isDraft: true`)
- PR is trivial/automated: author is a bot, title matches version-only bumps (`chore(deps):`, `bump *`, `Merge branch`), or has label `skip-review`
- Claude has already commented on this PR (check for `claude` or `github-actions[bot]` with Claude-style review content in comments)

**Still review** Claude-generated PRs (author is Claude but content is real code).

If skipped, print the reason and stop:
```
Skipping review: [PR is closed / PR is draft / PR is trivial / Already reviewed]
```

If not a PR review (Cases A, B, D, E), skip this step entirely.

---

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

### Fullstack App Auto-Detection

Detect if the codebase is a fullstack application by checking for **2+ of these signals**:

- `package.json` with frontend framework (react, vue, svelte, angular, next, nuxt)
- Backend framework config (`pyproject.toml` with fastapi/django/flask, `package.json` with express/nest/hono, `Cargo.toml` with actix/axum)
- API route definitions (files matching `*/routes/*`, `*/api/*`, `*/endpoints/*`)
- Tauri config (`tauri.conf.json`, `Cargo.toml` with tauri)
- Electron config (`electron-builder.yml`, main process with `BrowserWindow`)
- Mobile config (`android/`, `ios/`, `capacitor.config.ts`, react-native)
- `docker-compose.yml` with multiple services

If 2+ signals found, set `FULLSTACK_APP=true` and run Agent D (Platform Engineering Review) in Step 3.

## Step 1b: Intent Discovery

Before diving into file contents, understand **what the change is trying to accomplish**. Run a single bash call:

```bash
echo "BRANCH:" && git rev-parse --abbrev-ref HEAD && echo "COMMITS:" && git log --oneline ${MERGE_BASE:-HEAD~1}..HEAD
```

Combined with conversation context (user description, PR title/body if available), write a 2-3 line intent summary:

```
Intent: Simplify tax calculation by replacing the multi-tier rate lookup
with a flat-rate computation. Must not regress edge cases in tax-exempt handling.
```

**Pass this intent to every agent** in Step 3. Intent shapes how hard each reviewer looks -- a "fix typo" intent means less scrutiny than a "rewrite auth middleware" intent.

**When intent is ambiguous:** Ask one question: "What is the primary goal of these changes?" Do not proceed until intent is established.

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

6. **Check for deep-dive context** (optional -- requires `codebase-xray` plugin) -- if `.deep-dive/` exists and contains completed analysis files:
   - Read `.deep-dive/01-structure.md` for structural context
   - Read `.deep-dive/03-flows.md` for execution flow context
   - Read `.deep-dive/04-semantics.md` for design decision context
   - Read `.deep-dive/05-risks.md` for known risk context
   - Include a "Deep Dive Context" section in each agent's prompt (see template below)
   - Note in the review output that deep-dive context was used
   - If `.deep-dive/` does not exist or is incomplete, proceed normally without it -- this is expected behavior when the `codebase-xray` plugin is not installed or hasn't been run
   - This is a deliberate classification, not an oversight: `code-review` consumes a pre-existing analysis rather than starting a run, so per the X-ray Concurrent Runs Model the mirror is the correct contract for it. If this command is ever changed to invoke the X-ray skill itself, it moves to the immutable run directory (`$XRAY_RUN_DIR`) at that point

### Deep Dive Context Template

When deep-dive output is available, append this section to each agent prompt after existing context sections:

```
## Deep Dive Context

The following context was gathered from a prior deep-dive analysis. It is an index
of hypotheses produced by one upstream observer, not ground truth.

Use it to know WHERE to look. Do not use it to know WHAT IS TRUE: re-derive any
claim you intend to stand a finding on. Actively look for code paths that
contradict it; finding one is a result, not a failure. Silence in this context is
not evidence of absence.

Do not restate findings already reported here as if they were your own; add the
issues your specialized perspective reveals.

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

### Shared Instructions for All Agents

Include these instructions in every agent prompt:

```
## Intent
[paste the 2-3 line intent summary from Step 1b]

## Diff Scope & Pre-existing Classification

Classify every finding into one of three tiers:

- **Primary** -- lines added or modified in the diff. Your main focus. Full confidence.
- **Secondary** -- unchanged code in the same function/block as a changed line. Report
  if the diff makes the issue newly relevant, noting the interaction.
- **Pre-existing** -- issues in unchanged code unrelated to the diff. Mark these with
  `[PRE-EXISTING]` prefix. They are reported separately and do NOT count toward the verdict.

Rule: if you'd flag the same issue on an identical diff without the surrounding file,
it's pre-existing. If the diff makes it newly relevant, it's secondary.

## Premise declaration (required on every finding)

Every finding carries two extra fields:

- **Load-bearing premise:** the single proposition whose falsity collapses this
  finding. It must be minimal, falsifiable and scoped.
    Bad:  "The implementation is broken."
    Bad:  "Heartbeat handling is incorrect."   (a paraphrase of your finding)
    Good: "No credential-bearing response path exists after registration."
- **premise_provenance:** one of `independent`, `shared-context`, `mixed`.
  This records CAUSAL DEPENDENCE, not citation. If you absorbed the premise from
  the deep-dive output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.
```

Run all selected agents **in parallel** in a single response; conditional agents run only when their dispatch condition matches:

### Dispatch table

The full spawn prompt for every agent lives in the `senior-review:review-quality-gates` skill, file `references/code-review-agents.md` (resolve it inside that skill's installed directory). Read that file now, then spawn the selected agents in a single response using its `Agent tool call` blocks verbatim, substituting the shared instructions above.

| Agent | Dimension | subagent_type | Run when |
|-------|-----------|---------------|----------|
| A | Code audit: architecture, failure flow, patterns, scoring | `senior-review:code-auditor` | Always |
| B | Security | `senior-review:security-auditor` | Always |
| B2 | Dead code, unused parameters, VCS hygiene (lite, diff-scoped) | `general-purpose` | Always |
| C | UI race conditions | `senior-review:ui-race-auditor` | Changed files include UI/frontend code (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, `.qml`, or scroll/focus/layout manipulation) |
| D | Platform / runtime integration | `platform-engineering:platform-reviewer` | Fullstack signals (2+, Step 1). Skip with a note if the `platform-engineering` plugin is not installed |
| E | Git blame and history | `general-purpose` | Always |
| F | Testing quality | `testing:test-suite-auditor` (fallback `general-purpose` when the `testing` plugin is not installed) | Diff touches test files |
| G | API contracts | `general-purpose` | Diff touches API-related files (routes, serializers, OpenAPI/GraphQL/proto specs, DTOs) |
| H | Data migrations | `general-purpose` | Diff touches migration files |
| I | React performance | `react-development:react-performance-optimizer` | Diff touches `.tsx`/`.jsx` AND React in dependencies. Skip with a note if the `react-development` plugin is not installed |
| J | Abstraction and reuse (prior art, Rule of Three) | `abstraction-architect:abstraction-architect` | Diff adds at least one function/method/class/module/constant table or 5+ line block. Skip with a note if the `abstraction-architect` plugin is not installed |
| K | TypeScript type safety | `typescript-development:type-safety-auditor` | Diff touches `.ts`/`.tsx` AND `tsconfig.json` at project root. Skip with a note if the `typescript-development` plugin is not installed |
| L | Temporal resilience (failure-over-time) | `senior-review:temporal-resilience-auditor` | Diff touches timers, schedulers, polling, retry/reconnect, cron, queue workers, daemons, updaters, watchdogs |
| M | Data integrity (persistence semantics) | `senior-review:data-integrity-auditor` | Diff touches schemas, models, ORM, raw SQL, caches, or transaction boundaries |
| N | Resource lifecycle (ownership and release) | `senior-review:resource-lifecycle-auditor` | Diff acquires files, sockets, connections, subprocesses, listeners, locks, tasks, or timers |

Four dimensions live in plugins declared as `optionalDependencies` (D, I, J, K): when the plugin is absent, skip the dimension and report it as "not installed" under Skipped rather than attempting the spawn (which would fail with "Agent type not found"). Agent F degrades differently: it falls back to `general-purpose` with the testing checklist from the reference file. Everything else resolves to `senior-review` agents or `general-purpose` and always runs when its condition matches.

---

## Step 4: Consolidate Findings & Extract Score

After all agents complete, run the merge pipeline:

### 4a. Confidence Gating

Apply a three-tier confidence filter to all findings:

| Confidence | Action |
|------------|--------|
| **< 0.50 (< 50%)** | **Suppress** -- finding is speculative, discard it. Record suppressed count. |
| **0.50 - 0.69** | **Flag** -- include in report but mark as low-confidence |
| **>= 0.70** | **Report** -- full confidence, include normally |

### 4b. Deduplication

When multiple agents flag the same issue, merge them:

1. Compute fingerprint: `normalize(file) + line_bucket(line, +-3) + normalize(title)`
2. When fingerprints match:
   - Keep the **highest severity**
   - Keep the **highest confidence** with strongest evidence
   - **Union** the evidence from all agents
   - Weigh the agreement by provenance, per `## Shared-Context Provenance Rule` in the `senior-review:review-quality-gates` skill, instead of just noting which agents flagged it:
     - All agreeing agents report `independent` `premise_provenance`, or their load-bearing premises are disjoint: **corroborated**. Note the agreeing agents; the merge is a likely-real root cause.
     - All agreeing agents share the same `shared-context` premise: **echo**. Note it as `Echo: N agents agreed from the shared premise "[premise text]"`. This raises no confidence and no severity, and it is not evidence the finding is real.
     - Mixed: count only the independent agents toward corroboration.
3. Record the dedup count, split into corroborated merges and echo merges

### 4c. Separate Pre-existing

Pull out findings with `[PRE-EXISTING]` prefix into a separate list. These are reported in their own section and do NOT count toward the verdict.

### 4d. Sort & Score

- Sort by severity (Critical first) -> confidence (descending) -> file path -> line number
- Extract the Code Quality Score from code-auditor (Agent A) directly

## Step 4b: Adversarial Verification Panel

Skip this step if `--fast` was passed. Otherwise verify findings with the 4-lens panel defined in the `senior-review:review-quality-gates` skill, section `## Adversarial Verification Panel`. This replaces the former single-validator step: four independent lenses (premise veto, reachability/correctness, false-positive causes, severity) catch more failure modes than one judge, and the scope widens from Critical/High only to every finding above the confidence floor.

If the skill is unavailable, fall back to the legacy behavior: one `general-purpose` validator per Critical/High finding returning VALID/FALSE_POSITIVE (opus for bug/logic/architecture findings, sonnet for style/CLAUDE.md findings).

### Selection

- **Default:** every finding with confidence `>= 50%` that survived Step 4b deduplication, regardless of severity.
- **Cost guard** (more than 25 surviving findings AND `--rigorous` not set): narrow to all Critical/High plus any Medium/Low in the 50-75% confidence band or with conflicting reviewer severity. The rest pass through tagged `unverified (cost-guard)`. Note the narrowing in the report.
- **`--rigorous`:** verify everything above the floor, ignoring the cap.

The cost-guard threshold is a finding-count proxy (no token budget exists in this substrate).

### Panel

**Lens 0 first.** For each selected finding whose `premise_provenance` is `shared-context` or `mixed`, **or whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance**, spawn lens 0 (`subagent_type: senior-review:premise-auditor`, mode 2, inheriting the session model) using the Lens 0 prompt from the skill, with the deep-dive line resolved to the `.deep-dive/` mirror and the interconnect-map and knowledge-provenance lines omitted, since this command builds neither. A finding declaring no provenance is `shared-context` whenever `.deep-dive/` context was injected into the agent prompts, and the report records the agent as format-non-compliant; it is `independent` only when no such context was supplied at all. Defaulting the other way would send exactly the non-compliant findings Lens 0 exists to catch straight past the veto. Apply the skill's Lens 0 resolution table: a `REFUTED` verdict targeting `PREMISE` discards the finding (`filtered: premise-refuted`) without spawning lenses 1-2; targeting `SUPPORT` on `mixed` provenance strikes the shared leg and restates the finding from the surviving independent evidence before it proceeds; targeting `SUPPORT` on `shared-context` provenance discards it the same way. `UNCERTAIN` and `HOLDS` proceed to lenses 1-2, `UNCERTAIN` tagged `premise-contested`. Findings declared `independent` whose premise carries no such quantifier skip lens 0 entirely and proceed directly to lenses 1-2.

For each finding that reaches this step, spawn lenses 1 and 2 in parallel using the lens prompts from the skill (`general-purpose`; inherit the session model; `run_in_background: true`), substituting the finding, the diff, and the full file content. Spawn lens 3 (`model: sonnet`) only for findings that survive lenses 1-2, per the skill's gated-lens rule: calibrating a finding about to be discarded is spend for nothing.

### Survival rule

A finding discarded by Lens 0 never reaches this rule. Otherwise apply the skill's rule: survive on `>= 2` of lenses 1-2 voting REAL; discard (`filtered`, counted) on `>= 2` FALSE_POSITIVE; tie or fewer-than-2-verdicts means survive and mark `contested`. Final severity is the lens-3 vote when confirmed real, else the original.

**After the panel completes:**
- Drop `filtered` findings; apply recalibrated severities; tag `contested`, `premise-contested`, and `unverified (cost-guard)` findings.
- Add to the report: `Verification: X of Y (4-lens panel), Z false positives, W contested, V premise-refuted, U premise-contested`.

Medium and Low findings are no longer skipped by default: they enter the panel like any other finding above the floor (subject to the cost guard).

## Step 4c: Completeness Critic

Skip this step if `--fast` was passed. Otherwise run the critic defined in the `senior-review:review-quality-gates` skill, section `## Completeness Critic` (if the skill is unavailable, skip this step).

1. Spawn one `general-purpose` critic with the skill's critic prompt. Pass the verified findings, the changed-file scope, the agents that ran, and the deep-dive context paths if `.deep-dive/` exists (else "none").
2. If the critic names a single high-risk uncovered area under `## Recommended follow-up` AND the cost guard did not fire: spawn ONE targeted reviewer (the most specialized agent for that area) scoped to the files named, then route its findings back through Step 4 (dedup) and Step 4b (panel). At most one round.
3. Otherwise degrade to report-only.
4. Carry the critic's `## Coverage Gaps` list into the Step 5 report.


## Step 5: Final Review Output

Synthesize everything into the final structured review using the full template in the `senior-review:review-quality-gates` skill, file `references/code-review-output.md` (read it now). The template covers: review scope header (with intent, reviewers, verification counts), overall score, findings tables per dimension, coverage and coverage-gaps sections, pattern consistency, CLAUDE.md compliance, pre-existing issues, and the closing verdict block.

The verdict is one of **Ready to merge / Ready with fixes / Not ready**, with 1-2 sentences of reasoning and a severity-ordered fix list. Under `--strict`, any Critical finding forces `Not ready`.

## Step 5b: CLAUDE.md Alignment Check

Cross-reference the findings with the project's `CLAUDE.md` (already read in Step 2). If any documented convention, structure, or workflow is stale, add a `### CLAUDE.md Staleness` section to the review output. Details in `references/code-review-output.md`.

## Step 6: Auto-Comment on PR (if --auto-comment)

When reviewing a PR with `--auto-comment`, post the review as inline PR comments with committable suggestions where the fix is small and self-contained. The full comment format, the suggestion inclusion rules, and the `gh api` invocations are in `references/code-review-output.md`; follow them exactly.

## Step 7: Fix Loop (if --fix, --commit, or verdict is "Ready with fixes")

**The two flags are distinct contracts.** `--fix` means edit and verify: apply the fixes, run the tests, and leave the working tree modified with NO commits, so the user reviews and commits themselves. `--commit` implies `--fix` and adds the commits: one per fix or batch in 7b, one per phase in 7c. When the loop is entered via the verdict rather than a flag, ask which contract the user wants before touching anything.

The complete workflow lives in the `senior-review:review-quality-gates` skill, file `references/code-review-fix-loop.md` (read it before entering the loop). In brief:

- **7a Severity acceptance**: one multi-select prompt over the severity levels that have findings.
- **7b Apply fixes**: fix subagents apply the minimal correct fix per finding, run tests, and commit only under `--commit`.
- **7c Cleanup phases**: bulk removal of hygiene findings across seven phases (garbage, brand, assets, gitignore, deps, exports, docs), each gated by build+test and committed separately. **7c requires `--commit`**: its per-phase commits are its revert mechanism (`git reset --hard HEAD~1` on a failed gate). Under plain `--fix`, skip 7c and say why. This is the only place in the marketplace that bulk-removes application code; test-file bulk removal belongs to `/testing:test-consolidate`.

Follow the reference file exactly for 7c's critical rules (clean-tree pre-flight, phase isolation, gate-after-every-phase, grep-before-delete, side-effect protections, vulture approval), the baseline capture, the per-phase template, the docs-phase gating, and the cleanup report.
