# Team Review Pipeline

The complete workflow driven by `/team-review <target> [flags]`, running on the `review-orchestrator` agent.

Six phases. Context building feeds parallel adversarial review, which feeds consolidation, which feeds two quality gates, which feed the report.

The gate specs (verification panel, completeness critic, context-sharing pattern, anchor routing) live in `SKILL.md` alongside this file. This reference drives the sequence; `SKILL.md` is the source of truth for what each gate does.

## CRITICAL RULES

1. **Execute phases in order.** The only skips are the ones the flags authorize.
2. **Every reviewer gets an explicit output path.** That path is its contract.
3. **Verify by file existence**, with `#search/fileSearch`, never by trusting a returned summary.
4. **Never drop a finding silently.** Filtered and cost-guard-skipped findings are counted in the report.
5. **Report-only.** No agent in this pipeline edits source code.
6. **Session isolation.** All output goes under `.team-review/`. The X-ray pass owns `.deep-dive/`; do not write there.
7. **Resume-safe.** Re-dispatch only the reviewers whose findings file is missing.

## Reviewer roster

| Dimension | Agent | When |
|---|---|---|
| Security | `review-security-auditor` | always |
| Architecture | `review-code-auditor` | always |
| Logic integrity | `review-logic-integrity-auditor` | always, unless `--skip-interconnect` |
| Codebase hygiene | `review-cleanup-auditor` | always |
| UI race conditions | `review-ui-race-auditor` | conditional |
| React performance | `review-react-performance-optimizer` | conditional |
| General performance | `review-generic-reviewer` (dimension `performance`) | conditional |
| Platform compliance | `review-platform-reviewer` | conditional |
| Distributed flows | `review-distributed-flow-auditor` | conditional |
| Circular dependencies | `review-chicken-egg-detector` | conditional |
| API contracts | `review-api-contract-auditor` | conditional |
| Testing quality | `review-generic-reviewer` (dimension `testing`) | conditional |
| Data migrations | `review-generic-reviewer` (dimension `migrations`) | conditional |
| Abstraction | `review-abstraction-architect` | conditional, diff targets only |

Support agents: `review-verification-lens` (Phase 4b, three per finding), `review-completeness-critic` (Phase 4c).

Two scoping rules that are easy to get wrong:

- **`review-cleanup-auditor` scans the whole codebase, not the diff.** It is the only hygiene pass in this bundle, covering all five dimensions (dead code, orphan assets, VCS artifacts, dependency and barrel-file bloat, stale documentation). Every other always-on reviewer is diff-scoped. Do not narrow it to the changed files: orphan assets and phantom deps are by definition in files the diff never touched.
- **`review-abstraction-architect` also searches the whole codebase.** The diff is only its anchor; the prior art it hunts for lives in files that did not change.

Every agent in the roster ships inside this bundle, so no dimension can be skipped for a missing dependency. A dimension is skipped only when its activation rule did not fire.

## Pre-flight

1. Parse the arguments the user typed after `/team-review`:
   - `<target>`: file path, directory, git diff range (`main...HEAD`), or PR number (`#123`)
   - `--reviewers`: comma-separated dimension list, or `auto` (default)
   - `--base-branch`: base for diff comparison (default `main`)
   - `--all`: force every dimension regardless of detection
   - `--deep`: run the Phase 1 X-ray at full depth (default `--depth=lite`)
   - `--skip-interconnect`: skip Phase 1 entirely; reviewers get raw code only and `review-logic-integrity-auditor` is not spawned
   - `--fast`: skip both quality gates (Phase 4b and 4c)
   - `--rigorous`: verify every finding above the confidence floor, ignoring the cost-guard cap

   If no target was given, ask with `#vscode/askQuestions`.

2. Check `.team-review/state.json`:
   - `status: "in_progress"`: offer resume or fresh start (archive the old session to `.team-review-<ISO-timestamp>/`)
   - `status: "complete"`: offer to archive and start fresh
   - absent: proceed

3. Create `.team-review/` and `state.json`:

```json
{
  "target": "<target>",
  "status": "in_progress",
  "flags": {
    "reviewers": "auto", "all": false, "deep": false,
    "skip_interconnect": false, "fast": false, "rigorous": false
  },
  "xray_run_dir": null,
  "dimensions": [],
  "phases": {
    "phase_0_resolution": "pending",
    "phase_0b_detection": "pending",
    "phase_1_context": "pending",
    "phase_2_review": "pending",
    "phase_3_consolidation": "pending",
    "phase_4b_verification": "pending",
    "phase_4c_critic": "pending",
    "phase_5_report": "pending"
  },
  "files_created": [],
  "started_at": "<ISO_TIMESTAMP>"
}
```

Track the phases with `#todos` so the user sees progress while reviewers run.

## Phase 0: Target Resolution

1. Resolve the target type:
   - **File or directory**: use as-is
   - **Git diff range**: `git diff <range> --name-only` via `#execute/runInTerminal`
   - **PR number**: `gh pr diff <number> --name-only`
   - **Uncommitted work**: `#search/changes` also surfaces the working-tree diff without shelling out
2. Collect the full diff content for distribution to reviewers.
3. Collect the changed file paths and extensions for Phase 0b.
4. Write `.team-review/00-scope.md` with the target, the file list, and the active flags. Mark the phase complete.

## Phase 0b: Dimension Detection

Skip if an explicit `--reviewers` list was given. Force everything if `--all`.

The four always-on dimensions run unconditionally. For the conditional ones, gather signals and apply the rules below.

### Signals

Gather these with the search tools rather than a shell pipeline, so detection works the same on Windows and POSIX:

| Signal | How to gather |
|---|---|
| Changed-file extensions | Tally the extensions in the Phase 0 file list |
| React dependency | `#search/textSearch` for `"react"` in `package.json` |
| Frontend framework | `#search/textSearch` for `"(react\|vue\|svelte\|angular\|next\|nuxt)"` in `package.json` |
| Backend framework | `#search/textSearch` for `fastapi\|django\|flask\|express\|nest\|hono\|actix\|axum` across `package.json`, `pyproject.toml`, `Cargo.toml` |
| API surface | `#search/fileSearch` for `**/{routes,api,endpoints,handlers}/**` |
| Multi-service compose | `#search/textSearch` for `^\s*(image\|build):` in `docker-compose.y*ml`, more than one match |
| Messaging | `#search/textSearch` for `rabbitmq\|amqp\|kafka\|grpc\|pubsub\|celery\|dramatiq` in the diff content |
| Startup code | `#search/textSearch` for `def main\|if __name__\|on_startup\|lifespan\|create_app\|bootstrap\|init_` in the diff content |
| Test files | Changed files matching `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`, `conftest.py`, `__tests__/` |
| Migration files | Changed files matching Alembic, Django, Rails, Prisma, or plain SQL migration patterns |
| Contract files | Changed files matching `*.proto`, `openapi*.y*ml`, `swagger*`, `*.graphql`, `asyncapi*` |

### Activation rules

| Dimension | Activate when |
|---|---|
| UI race conditions | Changed files include `.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, or files manipulating scroll, focus, or layout |
| React performance | React in dependencies AND changed files include `.tsx` or `.jsx` |
| General performance | Frontend files detected but no React dependency |
| Platform compliance | Two or more of: frontend framework, backend framework, API routes, multi-service compose, Tauri or Electron config |
| Distributed flows | Changed files touch API routes, message handlers, gRPC definitions, or queue consumers/producers, or multi-service compose |
| Circular dependencies | Changed files touch startup sequences, dependency injection, config bootstrap, migration runners, or service registration |
| API contracts | Changed files touch contract files, route definitions, serializers, or DTO/schema declarations |
| Testing quality | Changed files include test files |
| Data migrations | Changed files include migration files |
| Abstraction | The target resolved to a diff (git range, PR, or uncommitted changes) AND the diff adds at least one function, method, class, module, constant table, or block longer than roughly five lines. Never activate for a plain file or directory target: there is no diff to anchor on |

### Show the plan

```
Context detection complete:
  Always:   security, architecture, logic-integrity, hygiene
  Detected: ui-races (6 .tsx files), react-perf (React project),
            distributed-flows (API routes + RabbitMQ), abstraction (diff adds 4 units)
  Skipped:  platform (not fullstack), chicken-egg (no startup code),
            testing (no test files changed), api-contracts (no contract files),
            migrations (no migration files)

Pipeline plan:
  Phase 1:  X-ray pass (--depth=lite) + interconnect map
  Phase 2:  {N} reviewers in parallel
  Phase 4b: verification panel, 3 lenses per selected finding
  Phase 4c: completeness critic
```

Mark `phase_0b_detection` complete.

## Phase 1: Context Building

Skip entirely if `--skip-interconnect`. Mark `phase_1_context` as `skipped` and jump to Phase 2 with raw target files only.

The Claude Code original split this into two phases: a deep-dive skill invocation, then a separate interconnect-mapper agent. Here it is one X-ray run, because the ported X-ray pipeline already produces the interconnect map as its own Phase 3.

1. Run the X-ray pipeline over the target:
   - Preferred: dispatch `xray-orchestrator` once with `#agent/runSubagent`, passing the target, `--depth=lite` (or full depth under `--deep`), `--yes`, and `--run-name review-<timestamp>`.
   - If subagent nesting is unavailable, read `.github/skills/codebase-xray/references/workflow.md` and dispatch the X-ray workers yourself. They are in your `agents:` allowlist for exactly this case.
   - If an X-ray run for this target already completed recently and the user has not changed the code since, offer to reuse it instead of re-running.

2. Record the run directory (`.deep-dive/runs/<run-id>/`) in `state.json` as `xray_run_dir`. Reviewers read from there, **not** from the `.deep-dive/` root mirror: a concurrent X-ray run can republish the root mid-review.

3. Verify the run produced at minimum `01-structure.md`, `02-interfaces.md`, and `05-risks.md`. If it did not, halt and report. Do not fake the context with a general-purpose agent: the file names and section anchors that Phase 2 depends on come from the X-ray pipeline itself, and a freelance substitute breaks the contract for `review-logic-integrity-auditor`.

4. Copy `<xray_run_dir>/08-interconnect-map.md` to `.team-review/02-interconnect.md`. Verify it contains the required anchors: `## Contracts`, `## Invariants`, `## Domain Rules`, `## Assumptions`, `## Integration Hot-Spots`, `## Review Focus Hints`. Empty sections are fine; missing anchors are not.

   If the X-ray run produced no `08-interconnect-map.md` (it was skipped or failed), treat the run as interconnect-less: proceed without `review-logic-integrity-auditor` and note the degradation in the report. Do not silently continue as though the map existed.

5. Mark `phase_1_context` complete.

## Phase 2: Adversarial Review (parallel)

Dispatch one subagent per selected dimension with `#agent/runSubagent`. Issue every dispatch in a single assistant turn so they run concurrently.

### Reviewer prompt template

```
You are reviewing for the {dimension} dimension.

## Target
[contents of .team-review/00-scope.md]

## Diff
{diff content}

## Context files (read these before analyzing code)
- X-ray output: {xray_run_dir}/ (01-structure.md, 02-interfaces.md, 05-risks.md)
- Interconnect map: .team-review/02-interconnect.md

Per `## Review Focus Hints` in the interconnect map, focus your reading on these anchors:
{anchors for this dimension, from the routing table in SKILL.md}

## Instructions
Follow your agent definition's analysis phases, knowledge-base loading, output format, and
severity classification. Cite file:line for every finding. Score every finding 0-100 for
confidence.

Write your report to .team-review/findings-{dimension}.md with #edit/createFile.
```

Under `--skip-interconnect`, omit the "Context files" and anchors sections entirely and do not spawn `review-logic-integrity-auditor`.

### Abstraction dimension addendum

`review-abstraction-architect` takes named inputs rather than a free-form dimension prompt. Append:

```
mode: diff
codebase_path: {target root}
deep_dive_path: {xray_run_dir, or "none"}
changed_files: {the same file list used to build the diff above}
report_path: .team-review/findings-abstraction.md
severity_floor: medium
```

Three things invert the default reviewer contract for this one:

- Its search space is the **whole codebase**, not the diff. The diff is only the anchor; the prior art it hunts for is by definition in files that did not change. Do not scope it to the changed files.
- It runs fine on lite-depth output, since it consumes only `01-structure.md` and `02-interfaces.md`. Do not force `--deep` on its account.
- `--skip-interconnect` does NOT skip it. That rule removes only `review-logic-integrity-auditor`. It runs with `deep_dive_path: none`, degrades to search-based prior-art hunting, and reports the reduced confidence in its Gaps section.

### Generic-reviewer dimensions

For `testing`, `migrations`, and `performance`, dispatch `review-generic-reviewer` and name the dimension in the prompt. Its definition carries the per-dimension checklists.

Mark `phase_2_review` as `in_progress`.

## Phase 3: Collect and Consolidate

1. **Barrier.** Poll with `#search/fileSearch` until `.team-review/findings-<dimension>.md` exists for every dispatched dimension. A reviewer whose file never appears counts as failed; record it and continue with the rest. If a reviewer returned content but wrote no file, save its output to the expected path yourself.
2. Report progress as `{completed}/{total} reviews complete`.
3. Apply the consolidation rules:
   - **Deduplicate**: merge findings on the same `file:line` describing the same issue. Credit every reviewer that found it.
   - **Co-locate**: same `file:line`, different issues, stay separate and get tagged as co-located.
   - **Severity conflicts**: take the higher rating.
   - **Cross-reference**: flag findings that surfaced in more than one dimension. Independent rediscovery is a strong signal of a real root cause.
   - **Route cross-reviewer notes**: scan every `## Cross-Reviewer Notes` section and fold those observations into the consolidated report under the dimension they belong to.
   - **Organize by severity**: Critical, High, Medium, Low.
4. Write `.team-review/99-consolidated.md`. Mark `phase_3_consolidation` complete.

## Phase 4b: Adversarial Verification

Skip if `--fast` (mark `skipped`). Otherwise drive the panel exactly per `SKILL.md`, section `## Adversarial Verification Panel`.

1. Apply the confidence floor: findings at `>= 50%`. An unscored finding counts as 60, so it is not silently skipped.
2. Selection: verify everything if `--rigorous` or 25 or fewer findings survive. Otherwise narrow to stakes plus uncertainty band per the skill, and record how many are left `unverified (cost-guard)`.
3. For each selected finding, dispatch three `review-verification-lens` subagents, one per lens, all in the same turn. Substitute the finding, the diff, and the full file content into each prompt.
4. Apply the survival rule: survives if at least 2 of lenses 1-2 vote REAL; `filtered` if at least 2 vote FALSE_POSITIVE; a tie or fewer than 2 valid verdicts means it survives, marked `contested`. Final severity is the lens-3 vote when confirmed real, otherwise the original.
5. Write `.team-review/98-verification.md`: one row per verified finding with per-lens verdicts, final severity, and flag, plus the trailing `unverified (cost-guard)` count.
6. Update `99-consolidated.md`: drop `filtered` findings, apply recalibrated severities, tag `contested` and `unverified (cost-guard)`.
7. Mark `phase_4b_verification` complete.

## Phase 4c: Completeness Critic

Skip if `--fast`. Otherwise drive the critic exactly per `SKILL.md`, section `## Completeness Critic`.

1. Dispatch one `review-completeness-critic`. Pass the verified findings, `.team-review/00-scope.md`, the dimensions that ran and were skipped with reasons, and the context paths.
2. Its output lands at `.team-review/97-coverage-gaps.md`.
3. If it names a single high-risk uncovered area under `## Recommended follow-up`, and neither the cost guard nor `--fast` applies: dispatch ONE targeted reviewer (the most specialized agent for that area, per the roster) for one round, scoped to the files the critic named. Route its findings back through Phase 3 deduplication and Phase 4b verification. At most once.
4. Under the cost guard, degrade to report-only: keep the gaps file, spawn no follow-up, note the skip.
5. Mark `phase_4c_critic` complete.

## Phase 5: Report

```
## Code Review Report: {target}

Session: .team-review/
Context: X-ray ({lite|full}) + interconnect map ({anchor count} anchors)
Reviewed by: {dimensions} ({N} reviewers)
Files reviewed: {count}
Verification: {verified} verified, {filtered} false positives, {contested} contested{cost_guard_note}

### Critical ({count})
[findings with file:line, category, and map anchor where applicable]

### High ({count})
### Medium ({count})
### Low ({count})

### Summary
Total findings: {count} (Critical: N, High: N, Medium: N, Low: N)
Coverage gaps: see .team-review/97-coverage-gaps.md ({gap_count} gaps, {followup} follow-up round)
Findings citing interconnect anchors: {count} ({pct}%)   <- context utilization rate

### Coverage Gaps
[the ## Coverage Gaps list from 97-coverage-gaps.md]
```

`{cost_guard_note}` is `, narrowed to stakes+band (N unverified)` when the guard fired, otherwise empty.

Set `state.json` to `status: "complete"`, mark `phase_5_report` complete, and tell the user the findings and context are preserved in `.team-review/`. Do not delete the session.

## Resume Logic

If pre-flight finds `status: "in_progress"`:

- `phase_0_resolution` incomplete: restart from zero
- `phase_0b_detection` incomplete: re-run detection from the existing `00-scope.md`
- `phase_1_context` incomplete: re-run the X-ray pass, or reuse `xray_run_dir` if it is already populated
- `phase_2_review` incomplete: re-dispatch only the dimensions whose findings file is missing
- `phase_3_consolidation` incomplete: re-consolidate from the findings on disk
- `phase_4b_verification` incomplete: re-run the panel
- `phase_4c_critic` incomplete: re-run the critic
- everything complete: present the report from the files on disk

## `--skip-interconnect` mode

Reproduces the legacy parallel-only behavior:
- No Phase 1
- No `review-logic-integrity-auditor`
- Reviewers receive target plus diff only, with no context paths and no anchors
- `review-abstraction-architect` still runs, with `deep_dive_path: none`
- Report structure unchanged

Use it for quick scans, for targets under roughly 100 LOC where the context pass costs more than it returns, or when the X-ray skill is not installed.

## Quick Examples

- `/team-review main...HEAD`: review the branch diff, auto-detect dimensions
- `/team-review #123`: review a pull request
- `/team-review src/auth/ --all`: force every dimension on a directory
- `/team-review main...HEAD --deep`: full-depth X-ray context instead of lite
- `/team-review main...HEAD --fast`: skip the verification panel and the critic
- `/team-review main...HEAD --rigorous`: verify every finding above the floor
- `/team-review src/api --reviewers security,api-contracts`: two dimensions, no detection
- `/team-review src/utils/dates.ts --skip-interconnect`: quick scan, no context pass
