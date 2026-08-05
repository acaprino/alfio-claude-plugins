---
description: "Launch a multi-reviewer parallel code review with specialized review dimensions, preceded by a context-building pipeline (deep-dive + interconnect map) so reviewers can hunt cross-component logic bugs, not just local issues"
argument-hint: "<target> [--reviewers auto|security,performance,...] [--base-branch main] [--all] [--deep] [--skip-interconnect] [--fast] [--rigorous]"
---

## Prerequisites

This command requires the upstream `agent-teams` plugin from `wshobson/agents` (MIT, Seth Hobson). It provides the `agent-teams:multi-reviewer-patterns` and `agent-teams:team-communication-protocols` skills and the `agent-teams:team-reviewer` fallback agent used below. Install it first:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

The team infrastructure itself is a native Claude Code feature and needs no plugin, but it is experimental and OFF by default: it requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, best set persistently in the `env` block of `~/.claude/settings.json`. As of Claude Code 2.1.178 there are no `TeamCreate`/`TeamDelete` tools: the team forms implicitly when the first teammate is spawned, and team resources are cleaned up automatically when the session ends. If teammate spawning is unavailable in this session, stop and tell the user to enable the flag and restart Claude Code; do not fall back to plain subagents without saying so.

# Team Review (Pipeline)

Orchestrate a multi-dimensional code review as a **4-phase pipeline**:

1. **Phase 1 -- Context Building (sequential)**: one agent runs deep-dive analysis, another builds an interconnect map (contracts, invariants, assumptions, domain rules, integration hot-spots). Output goes to `.team-review/`.
2. **Phase 2 -- Adversarial Review (parallel)**: specialized reviewers read the context files and hunt for violations within their dimension. Each writes structured findings to `.team-review/findings-<dim>.md`.
3. **Phase 3 -- Consolidation**: findings are deduplicated and organized by severity.
4. **Phase 4 -- Report & Cleanup**.

The pipeline lets reviewers find problems that are invisible from local-only inspection: broken implicit contracts, invariant drift, bypass paths to business rules, non-idempotent retry paths, terminal state mutations.

**Backward compat**: pass `--skip-interconnect` to run the old parallel-only behavior (no context phase, no `logic-integrity-auditor`).

## Skills to Load

Before starting, invoke these skills to inform the review process:
- `agent-teams:multi-reviewer-patterns` -- dimension allocation, deduplication rules, severity calibration
- `senior-review:review-quality-gates` -- context-sharing pattern, adversarial verification panel, completeness critic
- `senior-review:defect-taxonomy` -- 140+ defect subcategories with CWE/OWASP mappings (includes `logic-integrity.md`)
- `agent-teams:team-communication-protocols` -- message type selection, shutdown protocol

## Pre-flight Checks

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set.
2. Parse `$ARGUMENTS`:
   - `<target>`: file path, directory, git diff range (e.g., `main...HEAD`), or PR number (e.g., `#123`)
   - `--reviewers`: comma-separated dimensions OR `auto` (default: `auto`)
   - `--base-branch`: base branch for diff comparison (default: `main`)
   - `--all`: force all dimensions regardless of auto-detection
   - `--deep`: run Phase 1a `codebase-xray` in full mode (default: `--depth=lite`)
   - `--skip-interconnect`: skip Phase 1 entirely and run reviewers with raw code only (backward-compat mode; `logic-integrity-auditor` is also skipped)
   - `--fast`: skip the verification + completeness-critic gate entirely (Phase 4b and 4c)
   - `--rigorous`: verify every finding above the confidence floor, ignoring the cost-guard cap
3. Check for existing `.team-review/state.json`:
   - If present with `status: "in_progress"`: ask user whether to resume or start fresh (archive to `.team-review-<ISO-timestamp>/`).
   - If present with `status: "complete"`: ask whether to archive and start fresh.
   - If absent: proceed to new session.
4. Initialize `.team-review/` with `state.json`:

   ```json
   {
     "target": "$ARGUMENTS",
     "status": "in_progress",
     "flags": {
       "reviewers": "auto",
       "all": false,
       "deep": false,
       "skip_interconnect": false,
       "fast": false,
       "rigorous": false
     },
     "current_phase": 0,
     "phases": {
       "phase_0_resolution": "pending",
       "phase_0b_detection": "pending",
       "phase_1a_deep_dive": "pending",
       "phase_1b_interconnect": "pending",
       "phase_2_review": "pending",
       "phase_3_consolidation": "pending",
       "phase_4b_verification": "pending",
       "phase_4c_critic": "pending",
       "phase_4_report": "pending"
     },
     "files_created": [],
     "started_at": "ISO_TIMESTAMP"
   }
   ```

## Phase 0: Target Resolution

1. Determine target type:
   - **File/Directory**: use as-is for review scope
   - **Git diff range**: `git diff {range} --name-only` to get changed files
   - **PR number**: `gh pr diff {number} --name-only` to get changed files
2. Collect the full diff content for later distribution to reviewers.
3. Collect the list of changed file paths and extensions for Phase 0b.
4. Write `.team-review/00-scope.md` with target, files, flags. Mark phase complete in `state.json`.

## Phase 0b: Context Detection (when `--reviewers auto` or omitted)

Analyze changed files and codebase to determine which review dimensions are relevant. Skip if explicit `--reviewers` list was provided.

### Always-on dimensions (run for every review)

| Dimension | Agent | Rationale |
|-----------|-------|-----------|
| Security | `senior-review:security-auditor` | Every change can introduce vulnerabilities |
| Architecture | `senior-review:code-auditor` | Coupling, abstractions, failure flows, pattern consistency, scoring |
| **Logic integrity** | `senior-review:logic-integrity-auditor` | **Hunts violations of contracts/invariants/domain rules surfaced in Phase 1b** (skipped if `--skip-interconnect`) |
| Codebase hygiene | `senior-review:cleanup-auditor` | The **full** hygiene pass across all five dimensions and the whole codebase: dead code, orphan assets, generated artifacts tracked in VCS, phantom/unused deps plus barrel-file and eager-bundle bloat, and stale documentation. `/senior-review:code-review` and `/senior-review:pr-review` run only the lite subset (dead code + VCS hygiene, scoped to the diff), so this dimension is where the other three dimensions get covered at all |

### Conditional dimensions (auto-detected from context)

Run these checks against the changed files and codebase to decide which extra reviewers to spawn.

Five of these dimensions live in plugins declared as `optionalDependencies` of `senior-review`: React performance (`react-development`), platform compliance (`platform-engineering`), abstraction (`abstraction-architect`), testing quality (`testing`), and TypeScript type safety (`typescript-development`). A dimension whose plugin is absent is **skipped with a note**, never spawned. Attempting the spawn fails with "Agent type not found" and takes the phase down with it. Report the reason as "not installed" so the user can tell it apart from a dimension that simply did not match. Testing quality degrades differently from the other four: when the `testing` plugin is not installed the dimension is not skipped; it falls back to the generic `agent-teams:team-reviewer` with the testing dimension named in the prompt, which is the pre-testing-plugin behavior. Everything else in the table resolves to `senior-review` agents or to the `agent-teams` fallback, both of which are hard dependencies and always present.

| Signal | Detection rule | Dimension activated | Agent |
|--------|---------------|---------------------|-------|
| **UI/frontend files** | Changed files include `.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, or files containing scroll/focus/layout manipulation | UI race conditions | `senior-review:ui-race-auditor` |
| **React project** | `package.json` has `react` in dependencies AND changed files include `.tsx`/`.jsx`. Requires the `react-development` plugin: when it is not installed, skip and note it under Skipped instead of spawning (the spawn would fail) | React performance | `react-development:react-performance-optimizer` |
| **TypeScript project** | Changed files match `\.tsx?$` AND `tsconfig.json` exists at the project root. Requires the `typescript-development` plugin: when it is not installed, skip and note it under Skipped instead of spawning (the spawn would fail) | TypeScript type safety | `typescript-development:type-safety-auditor` |
| **Non-React frontend** | Frontend files detected but no React dependency | General performance | `agent-teams:team-reviewer` (performance dimension) |
| **Fullstack app** | 2+ signals: frontend framework in `package.json`, backend framework config, API route definitions, `docker-compose.yml` with multiple services, Tauri/Electron config. Requires the `platform-engineering` plugin: when it is not installed, skip and note it under Skipped instead of spawning (the spawn would fail) | Platform compliance | `platform-engineering:platform-reviewer` |
| **Multi-service / messaging** | Changed files touch API routes, message handlers, gRPC definitions, queue consumers/producers, or `docker-compose.yml` with multiple services | Distributed flows | `senior-review:distributed-flow-auditor` |
| **Init/startup code** | Changed files touch startup sequences, dependency injection, config bootstrap, migration runners, or service registration | Circular dependencies | `senior-review:chicken-egg-detector` |
| **Test files** | Changed files match `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`, `conftest.py`, `__tests__/`. Prefers the `testing` plugin: when it is not installed, do not attempt spawning `testing:test-suite-auditor` (the spawn would fail); fall back to `agent-teams:team-reviewer` (testing dimension) and note the fallback under the detection display | Testing quality | `testing:test-suite-auditor` |
| **API files** | Changed files touch a formal contract file (`*.proto`, `openapi*.y*ml`, `swagger*`, `*.graphql`, `asyncapi*`, JSON Schema), or route definitions, serializers, or DTO/model declarations | API contracts | `senior-review:api-contract-auditor` |
| **Migration files** | Changed files match database migration patterns (Alembic, Django, Rails, Prisma, SQL migrations) | Data migrations | `agent-teams:team-reviewer` (migration dimension) |
| **Diff target adding code** | Target resolved to a diff in Phase 0 (git range, PR number, or uncommitted changes) AND the diff adds at least one function, method, class, module, constant table, or block longer than roughly five lines. Requires the `abstraction-architect` plugin: when it is not installed, skip and note it under Skipped instead of spawning (the spawn would fail). Never activated for plain file/directory targets: there is no diff to anchor on, and the whole-tree question belongs to `/abstraction-architect:audit` | Abstraction (**was the changed code already available elsewhere?** Prior art per added unit + Rule of Three on this diff) | `abstraction-architect:abstraction-architect` (mode `diff`) |

### Detection implementation

Run these bash commands to gather signals:

```bash
# 1. Classify changed file extensions
echo "$CHANGED_FILES" | sed 's/.*\.//' | sort | uniq -c | sort -rn

# 2. Check for React
cat package.json 2>/dev/null | grep -q '"react"' && echo "REACT=true"

# 2b. Check for a TypeScript project
echo "$CHANGED_FILES" | grep -qE '\.tsx?$' && [ -f tsconfig.json ] && echo "TS_PROJECT=true"

# 3. Check for fullstack signals (count matches)
FULLSTACK_SIGNALS=0
[ -f package.json ] && grep -qE '"(react|vue|svelte|angular|next|nuxt)"' package.json && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))
grep -rql 'fastapi\|django\|flask\|express\|nest\|hono\|actix\|axum' pyproject.toml Cargo.toml package.json 2>/dev/null && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))
ls -d */routes */api */endpoints 2>/dev/null && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))
[ -f docker-compose.yml ] && grep -c 'image:\|build:' docker-compose.yml | awk '$1>1{print "MULTI_SERVICE"}' && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))

# 4. Check for multi-service / messaging patterns in diff
echo "$DIFF_CONTENT" | grep -qiE 'rabbitmq\|amqp\|kafka\|grpc\|pubsub\|queue\|celery\|dramatiq' && echo "MESSAGING=true"
echo "$CHANGED_FILES" | grep -qiE 'routes?\b|api/|endpoints?/|handlers?/' && echo "API_FILES=true"
# Formal contract files. Kept separate from API_FILES on purpose: a change to
# openapi.yaml or schema.graphql matches none of the path patterns above, and
# it is the single strongest signal for the api-contract-auditor dimension.
echo "$CHANGED_FILES" | grep -qiE '\.proto$|\.graphql$|\.gql$|openapi.*\.(ya?ml|json)$|swagger.*\.(ya?ml|json)$|asyncapi.*\.(ya?ml|json)$|schema.*\.json$' && echo "CONTRACT_FILES=true"

# 5. Check for init/startup patterns in diff
echo "$DIFF_CONTENT" | grep -qiE 'def main\b|if __name__|app\.on_startup|@app\.on_event|lifespan|create_app|bootstrap|init_' && echo "STARTUP=true"

# 6. Check for test and migration files
echo "$CHANGED_FILES" | grep -qiE 'test_|_test\.|\.spec\.|\.test\.|conftest|__tests__' && echo "TEST_FILES=true"
echo "$CHANGED_FILES" | grep -qiE 'migrat|alembic|versions/' && echo "MIGRATION_FILES=true"
```

### Display detected dimensions

After detection, display the plan:

```
Context detection complete:
  - Always: security, architecture, logic-integrity, codebase-hygiene
  - Detected: ui-races (6 .tsx files), react-perf (React project), ts-safety (TypeScript project), distributed-flows (API routes + RabbitMQ), abstraction (diff adds 4 units)
  - Skipped: platform (not fullstack), chicken-egg (no startup code)
  - Skipped, plugin not installed: react-perf (react-development)
  - Fallback: testing quality -> agent-teams:team-reviewer (testing plugin not installed)

Pipeline plan:
  Phase 1a: codebase-xray (--depth=lite)
  Phase 1b: codebase-xray:semantic-interconnect-mapper
  Phase 2:  {N} reviewers in parallel
  Phase 3:  consolidation
  Phase 4:  report
```

Show the last two lines only when a dimension matched but its plugin is missing. The three reasons are different signals: "not fullstack" means the code did not need the dimension, "not installed" means it did and the review has a known blind spot, and "Fallback" means the dimension still ran but generically, without the specialized auditor's detection pipeline.

Mark `phase_0b_detection` complete in `state.json`.

## Phase 1: Context Building

Skip this phase entirely if `--skip-interconnect` was passed. Mark `phase_1a_deep_dive` and `phase_1b_interconnect` as `skipped` in `state.json`. Jump to Phase 2 with raw target files only.

### Phase 1a: Deep-Dive Analysis

> **CRITICAL: `codebase-xray:analyze` is a SKILL, NOT an agent.**
> There is no agent named `codebase-xray`. Do NOT call the `Agent` tool with `subagent_type: "codebase-xray:analyze"` -- it will fail with "Agent type not found".
> Invoke it via the `Skill` tool: `Skill(skill: "codebase-xray:analyze", args: "--depth=lite <target>")`.
> The disambiguation matters because the rest of this command (Phase 1b, Phase 2) spawns many `subagent_type: plugin:name` teammates and the same `plugin:name` shape is reused for skill identifiers -- treat Phase 1a as a Skill invocation, full stop.

1. Invoke the `codebase-xray:analyze` **skill** via the `Skill` tool against the target:
   - Default mode: `--depth=lite` (structure + interfaces + risks only)
   - If `--deep` flag: full analysis
   - Target scope: the files from Phase 0
2. Deep-dive writes its output to `.deep-dive/` (or a session directory it chooses). Record the directory path in `state.json -> files_created`.
3. Verify on completion that at minimum `01-structure.md`, `02-interfaces.md`, and `05-risks.md` exist.
4. Mark `phase_1a_deep_dive` complete.

If the skill is unavailable (not installed) or produces no output, halt the pipeline and report the error. Do **not** fall back to spawning a `general-purpose` agent to fake the deep-dive output -- the file naming and section anchors that Phase 1b/Phase 2 depend on come from the skill itself, and a freelance fallback breaks the contract for `logic-integrity-auditor`.

### Phase 1b: Semantic Interconnect Mapping

1. Spawn a single teammate with `subagent_type: codebase-xray:semantic-interconnect-mapper`.
2. Prompt:

   ```
   Build the interconnect map for this review.

   Target scope: [contents of .team-review/00-scope.md]
   Deep-dive output: .deep-dive/ (files: 01-structure.md, 02-interfaces.md, 05-risks.md, ...)

   Read .deep-dive/ and the target files. Produce .team-review/02-interconnect.md
   following the exact output format in your agent definition (Call Graph,
   Contracts formal/structural/implicit, Invariants, Domain Rules, Assumptions,
   Integration Hot-Spots, Change Impact Radius, Reviewer Hints).

   Every claim must cite file:line. No recommendations, no fixes.
   ```

3. Wait for completion. Verify `.team-review/02-interconnect.md` exists and contains the required anchors (`## Contracts`, `## Invariants`, `## Domain Rules`, `## Assumptions`, `## Integration Hot-Spots`, `## Reviewer Hints`). Empty sections are acceptable but the anchors must exist.
4. Mark `phase_1b_interconnect` complete.

## Phase 2: Adversarial Review (parallel)

1. The team forms implicitly when the first teammate is spawned (no `TeamCreate` step; the team name is session-derived and any `team_name` passed to the `Agent` tool is ignored).
2. For each selected dimension (always-on + detected conditional), use `Agent` tool to spawn a teammate using the **most specialized agent**.

### Dimension-to-agent mapping

| Dimension | subagent_type |
|-----------|---------------|
| Security | `senior-review:security-auditor` |
| Architecture (+ failure flows, patterns, scoring) | `senior-review:code-auditor` |
| **Logic integrity (contracts/invariants/domain rules)** | `senior-review:logic-integrity-auditor` |
| **Abstraction (prior art / Rule of Three)** | `abstraction-architect:abstraction-architect` |
| Codebase hygiene (full pass: dead code, assets, VCS, deps, docs) | `senior-review:cleanup-auditor` |
| UI race conditions | `senior-review:ui-race-auditor` |
| React performance | `react-development:react-performance-optimizer` |
| TypeScript type safety | `typescript-development:type-safety-auditor` |
| General performance | `agent-teams:team-reviewer` |
| Platform compliance | `platform-engineering:platform-reviewer` |
| Distributed flows | `senior-review:distributed-flow-auditor` |
| Circular dependencies | `senior-review:chicken-egg-detector` |
| Testing quality | `testing:test-suite-auditor` (fallback: `agent-teams:team-reviewer` when the `testing` plugin is not installed) |
| API contracts | `senior-review:api-contract-auditor` |
| Data migrations | `agent-teams:team-reviewer` |

### Reviewer prompt template (context-aware)

Every reviewer receives the same structural prompt. The key addition vs the old parallel-only mode is the **context paths**.

```
You are reviewing for the {dimension} dimension.

## Target
[Insert contents of .team-review/00-scope.md]

## Diff
{diff content}

## Context files (read these before analyzing code)
- Deep-dive output: .deep-dive/ (see 01-structure.md, 02-interfaces.md, 05-risks.md)
- Interconnect map: .team-review/02-interconnect.md

Per `## Reviewer Hints` in the interconnect map, focus your reading on these anchors:
{anchors-for-this-dimension from the map's Reviewer Hints section}

## Instructions
Follow your agent definition's analysis phases, knowledge-base loading, output format, and severity classification. Cite file:line for every finding.

Write your output to .team-review/findings-{dimension}.md using the structured format your agent prescribes.
```

If `--skip-interconnect` was set, omit the "Context files" and "Reviewer Hints" sections and do NOT spawn the `logic-integrity-auditor`.

**Abstraction dimension addendum.** `abstraction-architect:abstraction-architect` takes named inputs rather than a free-form dimension prompt. Append this block to its prompt:

```
mode: diff
codebase_path: {target root}
deep_dive_path: {.deep-dive/ when Phase 1a ran and produced output, otherwise "none"}
changed_files: {the same file list used to build the diff above}
report_path: .team-review/findings-abstraction.md
severity_floor: medium
```

Three things about this reviewer, because they invert the default reviewer contract:

- Its search space is the **whole codebase**, not the diff. The diff is only the anchor; the prior art it is hunting for is by definition in files that did not change. Do not scope it to the changed files.
- It runs fine on `--depth=lite` output, since it consumes only `01-structure.md` and `02-interfaces.md`. Do not force `--deep` on its account.
- `--skip-interconnect` does NOT skip it (that rule removes only `logic-integrity-auditor`). It runs with `deep_dive_path: none` and degrades to Glob plus Grep, reporting the reduced confidence in its Gaps section.

**Testing dimension addendum.** `testing:test-suite-auditor` (when the `testing` plugin is installed; the `agent-teams:team-reviewer` fallback needs no addendum) partly inverts the default reviewer contract. Append this to its prompt:

```
Scope: run D2 to D8 only on tests owned by the changed modules; keep D1/D9
statistics suite-wide for context. Do NOT run the full suite inside this
review (no-run semantics): reuse metrics from CI history or existing report
artifacts, and mark anything unmeasured as such. Findings in this command's
severity format. Write your output to .team-review/findings-testing.md.
```

Two notes on why: a review is diff-anchored, so a whole-suite execution would dominate the phase's wall clock for findings mostly outside the diff; and suite-wide inventory statistics still matter because parallel-file and cross-layer-duplicate findings are invisible when only the changed test file is read.

### Spawn and task creation

- `name`: `{dimension}-reviewer` (e.g., "security-reviewer", "logic-integrity-reviewer")
- `subagent_type`: from the table above
- `prompt`: the template above, with `{dimension}` and anchors substituted

Use `TaskCreate` for each reviewer:
- Subject: "Review {target} for {dimension} issues"
- Description: the same structural prompt

Mark `phase_2_review` as `in_progress`.

## Phase 3: Monitor and Collect

1. Wait for all review tasks to complete (check `TaskList` periodically).
2. As each reviewer completes, verify `.team-review/findings-{dimension}.md` was written. If a reviewer failed to write its output file, read the task output and save it manually to that path.
3. Track progress: "{completed}/{total} reviews complete".
4. Mark `phase_2_review` complete, `phase_3_consolidation` in_progress.

## Phase 4: Consolidation

Apply the deduplication and calibration rules from the `agent-teams:multi-reviewer-patterns` skill:

1. **Deduplicate**: merge findings that reference the same `file:line` + same issue. Credit all reviewers.
2. **Co-locate**: same `file:line` but different issues -> keep separate, tag as co-located.
3. **Resolve severity conflicts**: use the higher rating.
4. **Cross-reference**: note findings that appear in multiple dimensions (a sign of a likely-real root cause).
5. **Organize by severity**: Critical, High, Medium, Low.

Write `.team-review/99-consolidated.md`. Mark `phase_3_consolidation` complete.

## Phase 4b: Adversarial Verification

Skip this phase if `--fast` was passed (mark `phase_4b_verification` as `skipped`). Otherwise drive the panel exactly per the `senior-review:review-quality-gates` skill, section `## Adversarial Verification Panel`.

1. Apply the confidence floor: select consolidated findings with confidence `>= 50%`. team-review reviewers emit confidence in their findings; if a finding lacks a score, treat it as 60% (in-band) so it is not silently skipped.
2. Apply the selection rule from the skill:
   - If `--rigorous`, or 25 or fewer findings survive: verify all selected findings.
   - Otherwise (more than 25 findings, no `--rigorous`): narrow to stakes + uncertainty band per the skill, and record the count of findings left `unverified (cost-guard)`.
3. For each finding to verify, spawn the 3 lenses in parallel using the three lens prompts from the skill (`general-purpose`; `opus` for lenses 1-2, `sonnet` for lens 3; `run_in_background: true`). Substitute the finding, diff, and full file content into each prompt.
4. Apply the survival rule from the skill: survive if `>= 2` of lenses 1-2 vote REAL; discard (`filtered`) if `>= 2` vote FALSE_POSITIVE; tie or fewer-than-2-verdicts means survive and mark `contested`. Final severity is the lens-3 vote when confirmed real, else the original.
5. Write `.team-review/98-verification.md`: one row per verified finding with the per-lens verdicts, final severity, and flag (`verified` / `contested` / `filtered`), plus a trailing count of `unverified (cost-guard)` findings.
6. Update `99-consolidated.md` to drop `filtered` findings, apply recalibrated severities, and tag `contested` and `unverified (cost-guard)` findings.
7. Mark `phase_4b_verification` complete.

## Phase 4c: Completeness Critic

Skip this phase if `--fast` was passed (mark `phase_4c_critic` as `skipped`). Otherwise drive the critic exactly per the `senior-review:review-quality-gates` skill, section `## Completeness Critic`.

1. Spawn one critic agent (`general-purpose`) with the critic prompt from the skill. Pass the verified findings (post-4b), `.team-review/00-scope.md`, the dimensions that ran, and the context paths (`.deep-dive/` and `.team-review/02-interconnect.md`, or "none" under `--skip-interconnect`).
2. Write the critic output to `.team-review/97-coverage-gaps.md`.
3. If the critic names a single high-risk uncovered area under `## Recommended follow-up` AND neither the cost guard nor `--fast` applies: spawn ONE targeted reviewer (the most specialized agent for that area, per the Phase 2 dimension-to-agent table) for one round, scoped to the files the critic named. Route its findings back through Phase 4 (dedup) and Phase 4b (verification). Do this at most once.
4. If the cost guard applies, degrade to report-only: keep `97-coverage-gaps.md`, spawn no follow-up, and note the skip.
5. Mark `phase_4c_critic` complete.

## Phase 5: Report and Cleanup

1. Present the consolidated report to the user:

   ```
   ## Code Review Report: {target}

   Session: .team-review/
   Context: deep-dive ({lite|full}) + interconnect map ({anchor count} anchors)
   Reviewed by: {dimensions} ({N} reviewers)
   Files reviewed: {count}
   Verification: {verified} verified, {filtered} false positives, {contested} contested{cost_guard_note}

   ### Critical ({count})
   [findings with file:line + category + map anchor where applicable]

   ### High ({count})
   [findings...]

   ### Medium ({count})
   [findings...]

   ### Low ({count})
   [findings...]

   ### Summary
   Total findings: {count} (Critical: N, High: N, Medium: N, Low: N)
   Coverage gaps: see .team-review/97-coverage-gaps.md ({gap_count} gaps, {followup} follow-up round)
   Findings citing interconnect anchors: {count} ({pct}%) <- quality metric
   Pipeline time: Phase 1: {t1}, Phase 2: {t2}, total: {total}

   ### Coverage Gaps
   [paste the ## Coverage Gaps list from .team-review/97-coverage-gaps.md]
   ```

   Where `{cost_guard_note}` is `, narrowed to stakes+band (N unverified)` when the cost guard fired, else empty.

2. Send `shutdown_request` to all reviewers.
3. Team resources are cleaned up automatically when the session ends; there is no `TeamDelete` step.
4. Update `state.json` -> `status: "complete"`, mark `phase_4_report` complete.
5. Inform the user that detailed findings and context are preserved in `.team-review/` for future reference (do not auto-delete).

## Backward Compatibility

Running `team-review <target> --skip-interconnect` reproduces the legacy parallel-only behavior:
- No Phase 1
- No `logic-integrity-auditor`
- Reviewers receive only the target + diff (no context files)
- Output identical in structure to the pre-pipeline version

Use this mode for quick scans, for targets with fewer than ~100 LOC where the pipeline adds more overhead than value, or when the deep-dive plugin is unavailable.
