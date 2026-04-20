---
description: "Launch a multi-reviewer parallel code review with specialized review dimensions, preceded by a context-building pipeline (deep-dive + interconnect map) so reviewers can hunt cross-component logic bugs, not just local issues"
argument-hint: "<target> [--reviewers auto|security,performance,...] [--base-branch main] [--all] [--deep] [--skip-interconnect]"
---

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
- `agent-teams:multi-reviewer-patterns` -- dimension allocation, deduplication rules, severity calibration, **context-sharing pattern**
- `senior-review:defect-taxonomy` -- 140+ defect subcategories with CWE/OWASP mappings (includes `logic-integrity.md`)
- `agent-teams:team-communication-protocols` -- message type selection, shutdown protocol

## Pre-flight Checks

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set.
2. Parse `$ARGUMENTS`:
   - `<target>`: file path, directory, git diff range (e.g., `main...HEAD`), or PR number (e.g., `#123`)
   - `--reviewers`: comma-separated dimensions OR `auto` (default: `auto`)
   - `--base-branch`: base branch for diff comparison (default: `main`)
   - `--all`: force all dimensions regardless of auto-detection
   - `--deep`: run Phase 1a `deep-dive-analysis` in full mode (default: `--depth=lite`)
   - `--skip-interconnect`: skip Phase 1 entirely and run reviewers with raw code only (backward-compat mode; `logic-integrity-auditor` is also skipped)
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
       "skip_interconnect": false
     },
     "current_phase": 0,
     "phases": {
       "phase_0_resolution": "pending",
       "phase_0b_detection": "pending",
       "phase_1a_deep_dive": "pending",
       "phase_1b_interconnect": "pending",
       "phase_2_review": "pending",
       "phase_3_consolidation": "pending",
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
| Codebase hygiene | `senior-review:cleanup-auditor` | Dead code + orphan assets + generated artifacts tracked in VCS + phantom/unused deps + barrel-file and eager-bundle bloat |

### Conditional dimensions (auto-detected from context)

Run these checks against the changed files and codebase to decide which extra reviewers to spawn:

| Signal | Detection rule | Dimension activated | Agent |
|--------|---------------|---------------------|-------|
| **UI/frontend files** | Changed files include `.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, or files containing scroll/focus/layout manipulation | UI race conditions | `senior-review:ui-race-auditor` |
| **React project** | `package.json` has `react` in dependencies AND changed files include `.tsx`/`.jsx` | React performance | `react-development:react-performance-optimizer` |
| **Non-React frontend** | Frontend files detected but no React dependency | General performance | `agent-teams:team-reviewer` (performance dimension) |
| **Fullstack app** | 2+ signals: frontend framework in `package.json`, backend framework config, API route definitions, `docker-compose.yml` with multiple services, Tauri/Electron config | Platform compliance | `platform-engineering:platform-reviewer` |
| **Multi-service / messaging** | Changed files touch API routes, message handlers, gRPC definitions, queue consumers/producers, or `docker-compose.yml` with multiple services | Distributed flows | `senior-review:distributed-flow-auditor` |
| **Init/startup code** | Changed files touch startup sequences, dependency injection, config bootstrap, migration runners, or service registration | Circular dependencies | `senior-review:chicken-egg-detector` |
| **Test files** | Changed files match `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`, `conftest.py`, `__tests__/` | Testing quality | `agent-teams:team-reviewer` (testing dimension) |
| **API files** | Changed files touch route definitions, serializers, OpenAPI/Swagger specs, GraphQL schemas | API contracts | `agent-teams:team-reviewer` (API dimension) |
| **Migration files** | Changed files match database migration patterns (Alembic, Django, Rails, Prisma, SQL migrations) | Data migrations | `agent-teams:team-reviewer` (migration dimension) |

### Detection implementation

Run these bash commands to gather signals:

```bash
# 1. Classify changed file extensions
echo "$CHANGED_FILES" | sed 's/.*\.//' | sort | uniq -c | sort -rn

# 2. Check for React
cat package.json 2>/dev/null | grep -q '"react"' && echo "REACT=true"

# 3. Check for fullstack signals (count matches)
FULLSTACK_SIGNALS=0
[ -f package.json ] && grep -qE '"(react|vue|svelte|angular|next|nuxt)"' package.json && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))
grep -rql 'fastapi\|django\|flask\|express\|nest\|hono\|actix\|axum' pyproject.toml Cargo.toml package.json 2>/dev/null && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))
ls -d */routes */api */endpoints 2>/dev/null && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))
[ -f docker-compose.yml ] && grep -c 'image:\|build:' docker-compose.yml | awk '$1>1{print "MULTI_SERVICE"}' && FULLSTACK_SIGNALS=$((FULLSTACK_SIGNALS+1))

# 4. Check for multi-service / messaging patterns in diff
echo "$DIFF_CONTENT" | grep -qiE 'rabbitmq\|amqp\|kafka\|grpc\|pubsub\|queue\|celery\|dramatiq' && echo "MESSAGING=true"
echo "$CHANGED_FILES" | grep -qiE 'routes?\b|api/|endpoints?/|handlers?/' && echo "API_FILES=true"

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
  - Always: security, architecture, logic-integrity, dead-code
  - Detected: ui-races (6 .tsx files), react-perf (React project), distributed-flows (API routes + RabbitMQ)
  - Skipped: platform (not fullstack), chicken-egg (no startup code), testing (no test files changed)

Pipeline plan:
  Phase 1a: deep-dive-analysis (--depth=lite)
  Phase 1b: semantic-interconnect-mapper
  Phase 2:  {N} reviewers in parallel
  Phase 3:  consolidation
  Phase 4:  report
```

Mark `phase_0b_detection` complete in `state.json`.

## Phase 1: Context Building

Skip this phase entirely if `--skip-interconnect` was passed. Mark `phase_1a_deep_dive` and `phase_1b_interconnect` as `skipped` in `state.json`. Jump to Phase 2 with raw target files only.

### Phase 1a: Deep-Dive Analysis

1. Invoke the `deep-dive-analysis:deep-dive-analysis` skill (or the command `/deep-dive-analysis:deep-dive-analysis`) against the target:
   - Default mode: `--depth=lite` (structure + interfaces + risks only)
   - If `--deep` flag: full analysis
   - Target scope: the files from Phase 0
2. Deep-dive writes its output to `.deep-dive/` (or a session directory it chooses). Record the directory path in `state.json -> files_created`.
3. Verify on completion that at minimum `01-structure.md`, `02-interfaces.md`, and `05-risks.md` exist.
4. Mark `phase_1a_deep_dive` complete.

If deep-dive fails or produces no output, halt the pipeline and report the error. Do not proceed with an empty context (it would defeat the purpose of Phase 2's logic-integrity reviewer).

### Phase 1b: Semantic Interconnect Mapping

1. Spawn a single teammate with `subagent_type: senior-review:semantic-interconnect-mapper`.
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

1. Use `TeamCreate` tool to create the team with `team_name: "review-{timestamp}"` and `description`.
2. For each selected dimension (always-on + detected conditional), use `Agent` tool to spawn a teammate using the **most specialized agent**.

### Dimension-to-agent mapping

| Dimension | subagent_type |
|-----------|---------------|
| Security | `senior-review:security-auditor` |
| Architecture (+ failure flows, patterns, scoring) | `senior-review:code-auditor` |
| **Logic integrity (contracts/invariants/domain rules)** | `senior-review:logic-integrity-auditor` |
| Dead code & lint | `general-purpose` |
| UI race conditions | `senior-review:ui-race-auditor` |
| React performance | `react-development:react-performance-optimizer` |
| General performance | `agent-teams:team-reviewer` |
| Platform compliance | `platform-engineering:platform-reviewer` |
| Distributed flows | `senior-review:distributed-flow-auditor` |
| Circular dependencies | `senior-review:chicken-egg-detector` |
| Testing quality | `agent-teams:team-reviewer` |
| API contracts | `agent-teams:team-reviewer` |
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

## Phase 5: Report and Cleanup

1. Present the consolidated report to the user:

   ```
   ## Code Review Report: {target}

   Session: .team-review/
   Context: deep-dive ({lite|full}) + interconnect map ({anchor count} anchors)
   Reviewed by: {dimensions} ({N} reviewers)
   Files reviewed: {count}

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
   Findings citing interconnect anchors: {count} ({pct}%) <- quality metric
   Pipeline time: Phase 1: {t1}, Phase 2: {t2}, total: {total}
   ```

2. Send `shutdown_request` to all reviewers.
3. Call `TeamDelete` to remove team resources.
4. Update `state.json` -> `status: "complete"`, mark `phase_4_report` complete.
5. Inform the user that detailed findings and context are preserved in `.team-review/` for future reference (do not auto-delete).

## Backward Compatibility

Running `team-review <target> --skip-interconnect` reproduces the legacy parallel-only behavior:
- No Phase 1
- No `logic-integrity-auditor`
- Reviewers receive only the target + diff (no context files)
- Output identical in structure to the pre-pipeline version

Use this mode for quick scans, for targets with fewer than ~100 LOC where the pipeline adds more overhead than value, or when the deep-dive plugin is unavailable.
