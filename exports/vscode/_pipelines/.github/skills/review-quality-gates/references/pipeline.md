# Team Review Pipeline

The complete workflow driven by `/team-review <target> [flags]`, running on the `review-orchestrator` agent.

Evidence discovery and context building feed parallel adversarial review, which feeds consolidation, which feeds two quality gates, which feed the report. Two derivations run side by side during context building, so that the review has a second observer rather than one observer explored N times.

The gate specs (verification panel, completeness critic, context-sharing pattern, anchor routing) live in `SKILL.md` alongside this file. This reference drives the sequence; `SKILL.md` is the source of truth for what each gate does.

## CRITICAL RULES

1. **Execute phases in order.** The only skips are the ones the flags authorize.
2. **Every reviewer gets an explicit output path.** That path is its contract.
3. **Verify by file existence**, with `#search/fileSearch`, never by trusting a returned summary.
4. **Never drop a finding silently.** Filtered and cost-guard-skipped findings are counted in the report.
5. **Report-only.** No agent in this pipeline edits source code.
6. **Session isolation.** All output goes under `.team-review/`. The X-ray pass owns `.deep-dive/`; do not write there.
7. **Resume-safe.** Re-dispatch only the reviewers whose findings file is missing.
8. **Shared context is not corroboration.** Per `## Shared-Context Provenance Rule` in `SKILL.md`, a claim a reviewer took from the X-ray output or the map is not a claim that reviewer verified, and agreement between reviewers who share a premise is an echo. Phase 1c, Phase 3 and Phase 4b all enforce this.

## Reviewer roster

| Dimension | Agent | When |
|---|---|---|
| Security | `review-security-auditor` | always |
| Architecture | `review-code-auditor` | always |
| Logic integrity | `review-logic-integrity-auditor` | always, unless `--no-context` |
| Codebase hygiene | `review-cleanup-auditor` | always |
| UI race conditions | `review-ui-race-auditor` | conditional |
| React performance | `review-react-performance-optimizer` | conditional |
| TypeScript type safety | `type-safety-auditor` from the `typescript-development` bundle (skipped with a note when that bundle is not installed) | conditional |
| General performance | `review-generic-reviewer` (dimension `performance`) | conditional |
| Platform / runtime integration | `review-platform-reviewer` | conditional |
| Distributed flows | `review-distributed-flow-auditor` | conditional |
| Circular dependencies | `review-chicken-egg-detector` | conditional |
| Temporal resilience | `review-temporal-resilience-auditor` | conditional |
| Data integrity | `review-data-integrity-auditor` | conditional |
| Resource lifecycle | `review-resource-lifecycle-auditor` | conditional |
| API contracts | `review-api-contract-auditor` | conditional |
| Testing quality | `test-suite-auditor` from the `testing` bundle (fallback: `review-generic-reviewer`, dimension `testing`, when that bundle is not installed) | conditional |
| Data migrations | `review-generic-reviewer` (dimension `migrations`) | conditional |
| Abstraction | `review-abstraction-architect` | conditional, diff targets only |

Support agents: `review-premise-auditor` (Phase 1c, one per run, blind to the shared context), `review-verification-lens` (Phase 4b, up to four per finding; lens 0 is gated on provenance and lens 3 on survival), `review-completeness-critic` (Phase 4c).

Two scoping rules that are easy to get wrong:

- **`review-cleanup-auditor` scans the whole codebase, not the diff.** It is the only hygiene pass in this bundle, covering all five dimensions (dead code, orphan assets, VCS artifacts, dependency and barrel-file bloat, stale documentation). Every other always-on reviewer is diff-scoped. Do not narrow it to the changed files: orphan assets and phantom deps are by definition in files the diff never touched.
- **`review-abstraction-architect` also searches the whole codebase.** The diff is only its anchor; the prior art it hunts for lives in files that did not change.

Every agent in the roster ships inside this bundle except the two cross-bundle rows marked above (testing quality and TypeScript type safety), so a dimension is normally skipped only when its activation rule did not fire. Those two are the exception: each names what happens when its bundle is absent, and neither is ever dispatched blind.

## Pre-flight

1. Parse the arguments the user typed after `/team-review`:
   - `<target>`: file path, directory, git diff range (`main...HEAD`), or PR number (`#123`)
   - `--reviewers`: comma-separated dimension list, or `auto` (default)
   - `--base-branch`: base for diff comparison (default `main`)
   - `--all`: force every dimension regardless of detection
   - `--deep`: run the Phase 1 X-ray at full depth (default `--depth=lite`)
   - `--no-context`: raw mode. Skip Phases 0c and 1 entirely; reviewers get raw code only, and neither `review-logic-integrity-auditor` nor `review-premise-auditor` is dispatched
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
    "no_context": false, "fast": false, "rigorous": false
  },
  "xray_run_dir": null,
  "dimensions": [],
  "phases": {
    "phase_0_resolution": "pending",
    "phase_0b_detection": "pending",
    "phase_0c_evidence_discovery": "pending",
    "phase_1_context": "pending",
    "phase_1c_premise_audit": "pending",
    "phase_1d_reconciliation": "pending",
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
4. Write `.team-review/00-scope.md` with the target, the file list, and the active flags. Append a `## Pre-review work tree` section containing the output of `git status --porcelain` at this moment: the Phase 5 workspace hygiene check diffs against it. Mark the phase complete.

## Phase 0b: Dimension Detection

Skip if an explicit `--reviewers` list was given. Force everything if `--all`.

The four always-on dimensions run unconditionally. For the conditional ones, gather signals and apply the rules below.

### Signals

Gather these with the search tools rather than a shell pipeline, so detection works the same on Windows and POSIX:

| Signal | How to gather |
|---|---|
| Changed-file extensions | Tally the extensions in the Phase 0 file list |
| React dependency | `#search/textSearch` for `"react"` in `package.json` |
| TypeScript project | `#search/fileSearch` for `tsconfig.json` at the project root, combined with changed files ending in `.ts` or `.tsx` |
| Frontend framework | `#search/textSearch` for `"(react\|vue\|svelte\|angular\|next\|nuxt)"` in `package.json` |
| Backend framework | `#search/textSearch` for `fastapi\|django\|flask\|express\|nest\|hono\|actix\|axum` across `package.json`, `pyproject.toml`, `Cargo.toml` |
| API surface | `#search/fileSearch` for `**/{routes,api,endpoints,handlers}/**` |
| Multi-service compose | `#search/textSearch` for `^\s*(image\|build):` in `docker-compose.y*ml`, more than one match |
| Messaging | `#search/textSearch` for `rabbitmq\|amqp\|kafka\|grpc\|pubsub\|celery\|dramatiq` in the diff content |
| Startup code | `#search/textSearch` for `def main\|if __name__\|on_startup\|lifespan\|create_app\|bootstrap\|init_` in the diff content |
| Long-running / scheduled code | `#search/textSearch` for `setInterval\|setTimeout\|cron\|schedule\|retry\|reconnect\|backoff\|watchdog\|heartbeat\|keepalive\|poll\|daemon\|updater` in the diff content |
| Persistence code | `#search/textSearch` for `transaction\|commit\|rollback\|UPDATE \|INSERT \|upsert\|unique\|constraint\|ON CONFLICT\|FOR UPDATE\|session.add\|prisma.\|typeorm\|sqlalchemy\|redis` in the diff content |
| Resource acquisition | `#search/textSearch` for `open(\|createReadStream\|socket\|getConnection\|acquire\|addEventListener\|subscribe(\|mutex\|semaphore\|new Worker\|subprocess\|Popen\|spawn(\|tokio::spawn\|asyncio.create_task\|createObjectURL` in the diff content |
| Test files | Changed files matching `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`, `conftest.py`, `__tests__/` |
| Migration files | Changed files matching Alembic, Django, Rails, Prisma, or plain SQL migration patterns |
| Contract files | Changed files matching `*.proto`, `openapi*.y*ml`, `swagger*`, `*.graphql`, `asyncapi*` |

### Activation rules

| Dimension | Activate when |
|---|---|
| UI race conditions | Changed files include `.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, or files manipulating scroll, focus, or layout |
| React performance | React in dependencies AND changed files include `.tsx` or `.jsx` |
| TypeScript type safety | Changed files end in `.ts` or `.tsx` AND `tsconfig.json` exists at the project root |
| General performance | Frontend files detected but no React dependency |
| Platform / runtime integration | Two or more of: frontend framework, backend framework, API routes, multi-service compose, Tauri or Electron config |
| Distributed flows | Changed files touch API routes, message handlers, gRPC definitions, or queue consumers/producers, or multi-service compose |
| Circular dependencies | Changed files touch startup sequences, dependency injection, config bootstrap, migration runners, or service registration |
| Temporal resilience | Diff or changed files touch timers, schedulers, polling loops, retry/reconnect logic, cron jobs, queue workers, background daemons, updaters, or watchdogs (the long-running / scheduled code signal). Its mandate is failure-over-time: what does the user see after this has been failing for a day |
| Data integrity | The persistence-code signal fires: schemas, models, ORM entities, repositories, raw SQL, cache layers, or transaction boundaries. Its mandate: can the store be made to hold an impossible state |
| Resource lifecycle | The resource-acquisition signal fires: files, sockets, connections, subprocesses, listeners, locks, tasks, or timers acquired in the diff, weighted higher for C/C++/Rust/Go and async-heavy code. Its mandate: does every acquire release on success, error, AND cancellation |
| API contracts | Changed files touch contract files, route definitions, serializers, or DTO/schema declarations |
| Testing quality | Changed files include test files |
| Data migrations | Changed files include migration files |
| Abstraction | The target resolved to a diff (git range, PR, or uncommitted changes) AND the diff adds at least one function, method, class, module, constant table, or block longer than roughly five lines. Never activate for a plain file or directory target: there is no diff to anchor on |

### Show the plan

```
Context detection complete:
  Always:   security, architecture, logic-integrity, hygiene
  Detected: ui-races (6 .tsx files), react-perf (React project),
            ts-safety (TypeScript project), distributed-flows (API routes + RabbitMQ),
            temporal-resilience (retry + scheduler code), data-integrity (ORM writes + transactions), abstraction (diff adds 4 units)
  Skipped:  platform (not fullstack), chicken-egg (no startup code),
            testing (no test files changed), api-contracts (no contract files),
            migrations (no migration files)

Pipeline plan:
  Phase 0c: review evidence discovery (inline)
  Phase 1:  X-ray pass (--depth=lite) + interconnect map
            |  Phase 1c: review-premise-auditor (parallel, blind)
  Phase 1d: knowledge reconciliation (inline)
  Phase 2:  {N} reviewers in parallel
  Phase 4b: verification panel, up to 4 lenses per selected finding
  Phase 4c: completeness critic
```

Mark `phase_0b_detection` complete.

## Phase 0c: Review Evidence Discovery

Runs inline on the orchestrator, on every invocation **except** raw mode (`--no-context`). That flag means "give me the raw mode", and a normally-on phase does not override it: `01a-review-knowledge-leads.md` distributed to N reviewers is itself shared context, so keeping this phase alive under the flag would make findings legitimately `shared-context`, let Lens 0 fire, and stop the mode reproducing the pre-pipeline behaviour it exists to provide.

This phase owns discovery of **what evidence is relevant to this review**. X-ray owns discovery of how the repository documents itself. The two are different jobs and the division is deliberate.

**This phase MUST NOT read `.deep-dive/` in any form**, including the mirror and the output of previous runs. A previous X-ray run is still an X-ray derivation, and admitting one would contaminate the single artifact that has to be demonstrably independent of X-ray. X-ray's leads enter at the Phase 1d join and nowhere earlier.

1. Read `AGENTS.md`, `.github/copilot-instructions.md`, `CLAUDE.md` and equivalent project instruction files, and follow any navigation rule they state. If the project says a specific file is where to look first to find where a concept lives, open that file before opening any code. Discover the conventions from the repository itself, never from a prior X-ray run.
2. Extract the concepts, domains and symbols the diff touches. Names of changed functions, classes, modules and config keys are the starting set; add the domain nouns that appear in the diff's own strings and comments.
3. For each concept, search the project's indexes and documentation for a relevant entry with `#search/textSearch`, and search the tests for behaviour that encodes it.
4. Write `.team-review/01a-review-knowledge-leads.md` with `#edit/createFile`.

**This file is immutable once written.** No later phase appends to it. X-ray's own leads are joined into a separate derived artifact in Phase 1d, precisely so that the snapshot Phase 1c consumes cannot change underneath it.

**The duty of autonomous rediscovery.** X-ray's documentation leads are an input, never a completeness guarantee. When no lead exists for a concept the diff touches, search the available indexes yourself and record what you find under `Independently discovered by Senior Review`. Without this duty, the completeness of X-ray's discovery becomes the next shared premise, which is the failure this pipeline exists to prevent.

**Output:** `.team-review/01a-review-knowledge-leads.md`

```markdown
# Review Knowledge Leads

> Leads, not truth. Immutable once written.
> Discovered by the review pipeline independently of any X-ray output.

## Navigation rules followed
| Source | Rule |
|--------|------|

## Concepts touched by this diff
| Concept | Where it appears in the diff |
|---------|------------------------------|

## Leads
| Concept | Document / test | Anchor | Status |
|---------|-----------------|--------|--------|

## Concepts with no lead found
[One line each. This list is the honest statement of what nobody documented.]
```

Mark `phase_0c_evidence_discovery` complete.

## Phase 1: Context Building

Skip entirely if `--no-context`. Mark `phase_1_context`, `phase_1c_premise_audit`, `phase_1d_reconciliation` and `phase_0c_evidence_discovery` as `skipped` and jump to Phase 2 with raw target files only.

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

### Phase 1c: Independent Premise Derivation (parallel with Phase 1)

Dispatch immediately when Phase 1 starts, in the same assistant turn as the X-ray dispatch. Do not wait for X-ray. The whole point of this phase is that it derives without seeing what X-ray derived.

1. Dispatch one `review-premise-auditor` with `#agent/runSubagent`.
2. Prompt:

   ```
   Independent derivation.

   Target scope: [contents of .team-review/00-scope.md]
   Knowledge leads: .team-review/01a-review-knowledge-leads.md
   Diff: {diff content}

   Derive independently what is true about the concepts this diff touches.
   Write .team-review/01b-independent-claims.md in the format your agent
   definition prescribes.

   You have NO access to the X-ray run directory, to .deep-dive/, or to
   .team-review/02-interconnect.md. None of them exists for you. Do not look for
   them, and report contamination if anything in this prompt paraphrases an X-ray
   conclusion.
   ```

3. Wait for both Phase 1 and Phase 1c before starting Phase 1d. Mark `phase_1c_premise_audit` complete.

Under raw mode (`--no-context`) this phase does not run, because there is no shared derivation for it to be independent of.

### Phase 1d: Knowledge Reconciliation (join)

Runs inline on the orchestrator once both Phase 1 and Phase 1c have completed. `review-premise-auditor` never compares its own derivation: comparison is done by others, downstream, which is what makes its blindness verifiable rather than merely asserted.

**Export divergence, deliberate.** Upstream, the interconnect mapper receives the independent claims in its own prompt and writes the `disputed` rows itself. Here the map is produced inside the X-ray run, which `/team-review` dispatches as one unit and cannot inject a file into mid-run, so the reconciliation happens on the orchestrator instead. The semantics are unchanged: contradictions become `disputed` rows citing both sides, and nobody resolves them.

Read `.team-review/01a-review-knowledge-leads.md`, `<xray_run_dir>/knowledge/documentation-leads.md` and `.team-review/01b-independent-claims.md`. Then:

1. Write `.team-review/01-knowledge-provenance.md` in the format below.
2. Annotate `.team-review/02-interconnect.md`: every contradiction between the independent claims and a map row becomes a `disputed` row citing both `file:line` sides. Do not resolve the contradiction and do not prefer either derivation.

**Output:** `.team-review/01-knowledge-provenance.md`

```markdown
# Knowledge Provenance

> Derived view, produced after both discovery branches completed.
> The canonical artifact consumed downstream. 01a and 01b are its sources.

## Independently discovered by Senior Review
[rows from 01a-review-knowledge-leads.md]

## Inherited from X-Ray
[rows from <xray_run_dir>/knowledge/documentation-leads.md]

## Missing
| Concept | In scope because |
|---------|------------------|
| [concept] | [where it appears in the diff] |

## Disputed
| Claim | Independent derivation says | X-ray says |
|-------|------------------------------|------------|
| [claim] | [X at file:line] | [Y at file:line] |
```

**Missing and Disputed are different states and must never collapse into one section.** Absence of evidence is not contradictory evidence.

| Section | Maps to in the interconnect map | Never |
|---|---|---|
| `Missing` | a coverage gap, and `unverified` on any related row | never `disputed`: nobody finding documentation is not two sources disagreeing |
| `Disputed` | `disputed`, both `file:line` sides cited | never silently resolved in favour of either derivation |

Collapsing them would drain `disputed` of the precise meaning the rest of this pipeline depends on, which is that two derivations reached incompatible conclusions and a reviewer must settle it.

Two asymmetries here are diagnostics worth reading, not noise. A row present in `Independently discovered by Senior Review` and absent from `Inherited from X-Ray` means X-ray's discovery had a gap. The reverse means Phase 0c had one. Both are recorded and neither is silently reconciled.

Mark `phase_1d_reconciliation` complete.

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
- Knowledge provenance: .team-review/01-knowledge-provenance.md

### Epistemic status of the shared context

The shared context is NOT ground truth. It is an index of hypotheses produced by
one upstream observer.

- Claims marked `verified` may be reused directly.
- Claims marked `documented`, `unverified` or `disputed` are hypotheses. You MUST
  independently re-derive any such claim before using it as the premise of a finding.
- Actively search for code paths, tests or documents that contradict the context.
  Finding one is a result, not a failure.
- Silence in the context is not evidence of absence. A concern the map does not
  mention may still be real; look anyway.

Per `## Review Focus Hints` in the interconnect map, focus your reading on these anchors:
{anchors for this dimension, from the routing table in SKILL.md}

## Instructions
Follow your agent definition's analysis phases, knowledge-base loading, output format, and
severity classification. Cite file:line for every finding. Score every finding 0-100 for
confidence.

## Premise declaration (required on every finding)

Every finding carries two extra fields:

- **Load-bearing premise:** the single proposition whose falsity collapses this
  finding. It must be minimal, falsifiable and scoped.
    Bad:  "The implementation is broken."
    Bad:  "Heartbeat handling is incorrect."   (a paraphrase of your finding)
    Good: "No credential-bearing response path exists after registration."
- **premise_provenance:** one of `independent`, `shared-context`, `mixed`.
  This records CAUSAL DEPENDENCE, not citation. If you absorbed the premise from
  the X-ray output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.

Write your report to .team-review/findings-{dimension}.md with #edit/createFile.
```

Under `--no-context`, omit the "Context files", epistemic-status and anchors sections entirely and do not dispatch `review-logic-integrity-auditor`. Keep the premise declaration block: in raw mode every finding is `independent` by construction, and saying so explicitly is what lets Phase 3 tell corroboration from echo without special-casing the mode.

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
- `--no-context` does NOT skip it. That rule removes only `review-logic-integrity-auditor` and `review-premise-auditor`. It runs with `deep_dive_path: none`, degrades to search-based prior-art hunting, and reports the reduced confidence in its Gaps section.

### Generic-reviewer dimensions

For `migrations` and `performance`, dispatch `review-generic-reviewer` and name the dimension in the prompt. Its definition carries the per-dimension checklists.

### Testing dimension

Prefer `test-suite-auditor` from the `testing` bundle. It is a cross-bundle reference: when that bundle is not installed, dispatch `review-generic-reviewer` with dimension `testing` instead (the pre-specialist behavior) and note the fallback in the dimension plan. When dispatching the specialist, append to its prompt: scope its detection dimensions D2 to D8 to the modules owned by the changed test files, keep D1/D9 statistics suite-wide as context only, never run the full suite inside the review (reuse CI history or existing report artifacts, mark anything unmeasured), and write output to `.team-review/findings-testing.md`.

### TypeScript type-safety dimension

Dispatch `type-safety-auditor` from the `typescript-development` bundle. It is a cross-bundle reference: when that bundle is not installed, skip the dimension and report it as "not installed" under Skipped, so the user can tell it apart from a dimension whose activation rule did not fire. There is no generic fallback, because the checklist it audits against lives in that bundle's `type-safety-rules` skill. It takes the standard reviewer prompt and writes to `.team-review/findings-ts-safety.md`.

Mark `phase_2_review` as `in_progress`.

## Phase 3: Collect and Consolidate

1. **Barrier.** Poll with `#search/fileSearch` until `.team-review/findings-<dimension>.md` exists for every dispatched dimension. A reviewer whose file never appears counts as failed; record it and continue with the rest. If a reviewer returned content but wrote no file, save its output to the expected path yourself.
2. **Delivery gate** (per `SKILL.md`, section `## Delivery Gate`): consolidation does not start until every dispatched dimension has either a findings file or an explicit no-findings report. Content salvaged from a reviewer's returned text is saved marked `[undelivered -- collected by orchestrator]` and the dimension is reported as **degraded**; a dimension with no artifact at all is reported as **not delivered**. Neither is ever presented as a clean dimension.
3. Report progress as `{completed}/{total} reviews complete`.
4. Apply the consolidation rules:
   - **Deduplicate**: merge findings on the same `file:line` describing the same issue. Credit every reviewer that found it.
   - **Co-locate**: same `file:line`, different issues, stay separate and get tagged as co-located.
   - **Severity conflicts**: take the higher rating.
   - **Cross-reference, weighted by provenance**: per `## Shared-Context Provenance Rule` in `SKILL.md`, agreement is only corroboration when the agreeing findings did not inherit the same premise.
     - Findings that agree and are all `independent`, or whose load-bearing premises are disjoint: **corroborated**. Report as a likely-real root cause.
     - Findings that agree and share the same `shared-context` premise: **echo**. Report under the finding as `Echo: N dimensions agreed from the shared premise "[premise text]"`. This raises no confidence and no severity, and it is not evidence that the finding is real.
     - Mixed sets: corroboration counts only the independent members.
   - **Route cross-reviewer notes**: scan every `## Cross-Reviewer Notes` section and fold those observations into the consolidated report under the dimension they belong to.
   - **Collect `[MAP-GAP]` findings**: any logic-integrity finding carrying the `[MAP-GAP]` marker is also listed in the report as an interconnect-map coverage gap, so the mapper's blind spot is recorded alongside the defect it hid.
   - **Organize by severity**: Critical, High, Medium, Low.
5. Write `.team-review/99-consolidated.md`. Mark `phase_3_consolidation` complete.

## Phase 4b: Adversarial Verification

Skip if `--fast` (mark `skipped`). Otherwise drive the panel exactly per `SKILL.md`, section `## Adversarial Verification Panel`.

1. Apply the confidence floor: findings at `>= 50%`. An unscored finding counts as 60, so it is not silently skipped.
2. Selection: verify everything if `--rigorous` or 25 or fewer findings survive. Otherwise narrow to stakes plus uncertainty band per the skill, and record how many are left `unverified (cost-guard)`.
3. **Lens 0 first.** For each selected finding whose `premise_provenance` is `shared-context` or `mixed`, dispatch one `review-verification-lens` with `lens: 0` using the Lens 0 prompt from the skill, resolving the X-ray line to `{xray_run_dir}/`. Apply the skill's Lens 0 resolution table: a `REFUTED` verdict targeting `PREMISE` discards the finding (`filtered: premise-refuted`) without dispatching lenses 1-2; targeting `SUPPORT` on `mixed` provenance strikes the shared leg and restates the finding from the surviving independent evidence before it proceeds; targeting `SUPPORT` on `shared-context` provenance discards it the same way. `UNCERTAIN` and `HOLDS` proceed to lenses 1-2, `UNCERTAIN` tagged `premise-contested`. Findings declared `independent` skip lens 0 entirely.
4. For each finding that reaches this step, dispatch two `review-verification-lens` subagents (lenses 1 and 2), all in the same turn across findings. Substitute the finding, the diff, and the full file content into each prompt. Dispatch lens 3 only for findings that survive lenses 1-2, per the skill's gated-lens rule.
5. Apply the survival rule: survives if at least 2 of lenses 1-2 vote REAL; `filtered` if at least 2 vote FALSE_POSITIVE; a tie or fewer than 2 valid verdicts means it survives, marked `contested`. Final severity is the lens-3 vote when confirmed real, otherwise the original.
6. Write `.team-review/98-verification.md`: one row per verified finding with per-lens verdicts (including, for findings that reached lens 0, its verdict, refutation target, and counterexample), final severity, and flag (`verified` / `contested` / `filtered: premise-refuted` / `filtered`), plus the trailing `unverified (cost-guard)` count.
7. Update `99-consolidated.md`: drop `filtered` findings, apply recalibrated severities, tag `contested`, `premise-contested` and `unverified (cost-guard)`.
8. Mark `phase_4b_verification` complete.

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
Verification: {verified} verified (4-lens panel), {filtered} false positives, {contested} contested, {premise_refuted} premise-refuted{cost_guard_note}

### Critical ({count})
[findings with file:line, category, and map anchor where applicable]

### High ({count})
### Medium ({count})
### Low ({count})

### Summary
Total findings: {count} (Critical: N, High: N, Medium: N, Low: N)
Coverage gaps: see .team-review/97-coverage-gaps.md ({gap_count} gaps, {followup} follow-up round)
Map utilization: {count} findings cite an anchor ({pct}%, operational)
Independent premise reconstruction: {ipr_count} findings ({ipr_pct}%)
Premise challenge: {pc_count} of {eligible} eligible premises attacked by Lens 0
Corroborated findings: {n_corroborated} (independent agreement)
Echoes: {n_echo} (agreement inherited from a shared premise, not corroboration)

### Coverage Gaps
[the ## Coverage Gaps list from 97-coverage-gaps.md]
```

`{cost_guard_note}` is `, narrowed to stakes+band (N unverified)` when the guard fired, otherwise empty.

Before finalizing, run the **workspace hygiene check** (per `SKILL.md`, section `## Delivery Gate`): compare `git status --porcelain` against the `## Pre-review work tree` snapshot in `00-scope.md`. Any file the review created outside `.team-review/` (probe scripts, measurement harnesses, scratch fixtures) is removed now and its removal noted in the report. The review leaves the work tree exactly as it found it, plus `.team-review/`.

Set `state.json` to `status: "complete"`, mark `phase_5_report` complete, and tell the user the findings and context are preserved in `.team-review/`. Do not delete the session.

## Resume Logic

If pre-flight finds `status: "in_progress"`:

- `phase_0_resolution` incomplete: restart from zero
- `phase_0b_detection` incomplete: re-run detection from the existing `00-scope.md`
- `phase_0c_evidence_discovery` incomplete: re-run it. If `01a-review-knowledge-leads.md` already exists, it is immutable and complete; do not append to it
- `phase_1_context` incomplete: re-run the X-ray pass, or reuse `xray_run_dir` if it is already populated
- `phase_1c_premise_audit` incomplete: re-dispatch `review-premise-auditor`. Its blindness contract is unchanged on resume
- `phase_1d_reconciliation` incomplete: re-run the join from `01a`, `01b` and the X-ray leads on disk
- `phase_2_review` incomplete: re-dispatch only the dimensions whose findings file is missing
- `phase_3_consolidation` incomplete: re-consolidate from the findings on disk
- `phase_4b_verification` incomplete: re-run the panel
- `phase_4c_critic` incomplete: re-run the critic
- everything complete: present the report from the files on disk

## Raw mode (`--no-context`)

Reviewers receive the target and diff only. No context artifact is produced or distributed.

- Phases skipped: 0c, 1, 1c, 1d
- Not dispatched: `review-logic-integrity-auditor`, `review-premise-auditor`
- Reviewers receive target plus diff only, with no context paths and no anchors
- Every finding is `independent` by construction, so Lens 0 never fires and consolidation never reports an echo
- `review-abstraction-architect` still runs, with `deep_dive_path: none`
- Report structure unchanged

Use it for targets under roughly 100 LOC where the context pass costs more than it returns, for quick scans, and when the X-ray skill is not installed or produces no usable output.

`--skip-interconnect` was the old name for this flag and no longer exists. Use `--no-context`. The X-ray pipeline keeps its own `--skip-interconnect`, which is a different flag with a different meaning: there it skips only the interconnect map.

## Quick Examples

- `/team-review main...HEAD`: review the branch diff, auto-detect dimensions
- `/team-review #123`: review a pull request
- `/team-review src/auth/ --all`: force every dimension on a directory
- `/team-review main...HEAD --deep`: full-depth X-ray context instead of lite
- `/team-review main...HEAD --fast`: skip the verification panel and the critic
- `/team-review main...HEAD --rigorous`: verify every finding above the floor
- `/team-review src/api --reviewers security,api-contracts`: two dimensions, no detection
- `/team-review src/utils/dates.ts --no-context`: quick scan, no context pass
