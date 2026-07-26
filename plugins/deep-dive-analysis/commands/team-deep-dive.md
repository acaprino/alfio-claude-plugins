---
description: >
  Multi-agent variant of /deep-dive-analysis for large or partitioned codebases. Auto-detects partitions (workspaces / dirs / language clusters), spawns 3 deep-dive workers per partition across 2 waves, synthesizes consolidated .deep-dive/01..07.md plus a global .deep-dive/08-interconnect-map.md.
  TRIGGER WHEN: the user wants deep-dive analysis on a monorepo or wants a cross-partition interconnection map produced as part of the same flow.
  DO NOT TRIGGER WHEN: the project is a single small directory (use /deep-dive-analysis) or the user wants a documentation-only audit (use /deep-dive-analysis --docs-only).
argument-hint: "<target> [--critical] [--comments] [--depth=lite|full] [--partition <path>] [--partition-name <name>] [--skip-interconnect] [--skip-synthesis] [--yes]"
---

## Prerequisites

This command requires the upstream `agent-teams` plugin from `wshobson/agents` (MIT, Seth Hobson). It provides the `agent-teams:task-coordination-strategies`, `agent-teams:team-communication-protocols`, and `agent-teams:parallel-feature-development` skills used below. Install it first:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

The team tools themselves (TeamDelete, TaskList, TaskUpdate) are native Claude Code features and need no plugin.

# Team Deep-Dive

Orchestrate a partitioned multi-agent deep-dive plus global interconnect map.

## CRITICAL RULES

1. **Execute phases in order.** No skipping unless `--skip-synthesis` or `--skip-interconnect` is set.
2. **Spawn agents with file ownership.** Every spawn prompt enumerates the owned output files.
3. **Wait for the global Wave 1 barrier** before spawning Wave 2 workers.
4. **Never enter plan mode.** Execute immediately.
5. **Resume-safe.** Re-spawn only missing workers on resume.

## Skills to Load

Before starting, invoke these skills:
- `agent-teams:task-coordination-strategies` — task dependencies, addBlockedBy semantics
- `agent-teams:team-communication-protocols` — spawn prompt anatomy, shutdown
- `agent-teams:parallel-feature-development` — file ownership patterns

## Pre-flight Checks

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
2. Parse `$ARGUMENTS`:
   - `<target>`: directory to analyze (default: cwd)
   - `--critical`: prioritize auth/payment/persistence in Phase 3-4
   - `--comments`: activate comment audit in Phase 6
   - `--depth=lite|full`: lite skips Phase 3-4 (workers B not spawned, synthesizer skips 03/04/06)
   - `--partition <path>`: manual partition (repeatable; overrides auto-detect)
   - `--partition-name <name>`: symbolic name for the N-th manual partition (1-indexed; optional)
   - `--skip-interconnect`: skip Phase 3
   - `--skip-synthesis`: skip Phase 2 AND Phase 3
   - `--yes`: auto-accept partition checkpoint
   - REJECT with explicit error if `--phase N` or `--docs-only` are passed (suggest classic `/deep-dive-analysis`)
3. Check `.deep-dive/state.json`:
   - If `mode == "team"` and `status == "in_progress"`: prompt to resume or archive
   - If `mode == "classic"`: refuse to start; instruct user to archive first
   - If `status == "complete"`: prompt to archive

## Phase 0: Pre-flight + Partition Detection

### Initialize state

Create `.deep-dive/` and `.deep-dive/state.json`:

```json
{
  "target": "$ARGUMENTS_TARGET",
  "mode": "team",
  "status": "in_progress",
  "flags": {
    "critical": false,
    "comments": false,
    "depth": "full"
  },
  "partitions": [],
  "phases": {
    "phase_0_detection": "pending",
    "phase_1_partition_workers": "pending",
    "phase_2_synthesis": "pending",
    "phase_3_interconnect": "pending"
  },
  "agents_spawned": [],
  "files_created": [],
  "started_at": "<ISO_TIMESTAMP>",
  "completed_at": null
}
```

### Run partition detection algorithm

If `--partition` was provided one or more times, skip auto-detect: use the manual list directly. Apply `--partition-name` mappings if provided; otherwise derive names from path basename.

Otherwise, run the detection chain (first rule that matches wins):

1. **Explicit workspace manifests** (in order):
   - `pnpm-workspace.yaml` -> `packages` field paths
   - `package.json` with `workspaces` field
   - `lerna.json` `packages`
   - `nx.json` + `apps/` + `libs/`
   - `turbo.json` + `apps/` + `packages/`
   - `Cargo.toml` `[workspace] members`
   - `pyproject.toml` `[tool.uv.workspace] members` or equivalent
2. **Convention-based monorepo:**
   - `apps/`, `packages/`, or `services/` at root with >1 subdirectory
   - `src/` with sub-dirs each having their own `package.json` / `pyproject.toml`
3. **Layer split:**
   - `src/{backend,frontend}`, `src/{api,web}`, `src/{server,client}`, or root-level `backend/` + `frontend/`
4. **Language split:**
   - Use `${CLAUDE_PLUGIN_ROOT}/skills/deep-dive-analysis/scripts/classifier.py` to count files per language
   - If ≥2 languages with ≥20 files each: partition per language (`*.py` -> "python", `*.ts/*.tsx` -> "typescript")
5. **Fallback:** single partition wrapping the entire target, name = `root`

**Always excluded paths:** `node_modules/`, `dist/`, `build/`, `.next/`, `target/`, `vendor/`, `__pycache__/`, `.venv/`.

**Partition naming rules:**
1. From workspace path -> basename
2. On collision -> slug-ified path
3. From language fallback -> language name
4. From single-partition fallback -> `root`

Normalize names: lowercase, separators -> hyphen, strip accents, allowed chars `[a-z0-9-]`.

For each partition, compute `file_count` and `loc_estimate` (use `classifier.py` + `wc -l` or `cloc` if available).

### Checkpoint

Present to the user:

```
Deep-dive team-mode scope:
Target: <target>

Detected partitioning strategy: <strategy name>

Proposed partitions (<N>):
  P1: <path>          (<language>, <file-count> files, ~<loc>k LOC)
  ...

Spawn plan: <N> partitions × 3 agents = <3N> workers + 1 synthesizer + 1 interconnect-mapper = <3N+2> agents total.

Note: token cost scales linearly with file count × agents. Consider `--depth=lite` for monorepos with many partitions.

Options:
  [A] Accept and start
  [M] Modify partition list (rename, regroup, exclude one)
  [m] Manual: provide partition paths
  [c] Cancel
```

If `--yes`, auto-select `[A]`.

If `[M]`, prompt for changes:
- `rename <old> <new>`
- `exclude <name>`
- `merge <name1> <name2> [<merged-name>]`
- `done` to finalize

If `[m]`, prompt for paths and optional names.

If `[c]`, set state to `cancelled` and exit.

Finalize `partitions` array in `state.json` with `{name, path, language_primary, file_count, loc_estimate, status: "pending"}` for each. Mark `phase_0_detection: "complete"`.

## Phase 1: Partition Workers (2 waves)

### Wave 1: Structure workers (parallel)

For each partition `P_i` in `state.json`:

1. Create directory `.deep-dive/partitions/<P_i.name>/`
2. Spawn `deep-dive-analysis:partition-structure-worker`:
   - `subagent_type`: `deep-dive-analysis:partition-structure-worker`
   - Task title: `"P<i>.A — Structure+Interfaces for partition <P_i.name>"`
   - Task prompt:

```
You are partition-structure-worker on partition "<P_i.name>".

Identity: P<i>.A
Owned files:
  - .deep-dive/partitions/<P_i.name>/01-structure.md
  - .deep-dive/partitions/<P_i.name>/02-interfaces.md
DO NOT touch any other file under .deep-dive/.

Target path for this partition: <P_i.path>
Active flags: --critical=<bool> --comments=<bool> --depth=<lite|full>

Sibling partitions (for cross-partition citation lookup if needed):
  <list each P_j.name -> P_j.path>

Required reads before writing:
  - <P_i.path>: all source files within scope
  - ${CLAUDE_PLUGIN_ROOT}/skills/deep-dive-analysis/SKILL.md
  - Scripts at ${CLAUDE_PLUGIN_ROOT}/skills/deep-dive-analysis/scripts/

Completion: when done, call TaskUpdate to mark your task completed.
```

3. Record spawn in `agents_spawned[]` with `{name: "P<i>.A", type: "partition-structure-worker", partition: "<P_i.name>", task_id: "..."}`.

After spawning all `P_i.A`: monitor via `TaskList`. Wait until every `P_i.A` task is `completed` OR `failed`.

For each partition: if `P_i.A` failed, mark `partitions[i].status = "failed"`. If completed, mark `partitions[i].status = "structure_done"`.

Mark `phase_1_partition_workers: "wave1_done"`.

### Wave 2: Behavior + Quality workers (parallel)

Skip workers B if `--depth=lite`.

For each partition `P_i` where `partitions[i].status == "structure_done"`:

1. If `--depth != lite`: spawn `deep-dive-analysis:partition-behavior-worker`:
   - Task title: `"P<i>.B — Flows+Semantics for partition <P_i.name>"`
   - Task prompt:

```
You are partition-behavior-worker on partition "<P_i.name>".

Identity: P<i>.B
Owned files:
  - .deep-dive/partitions/<P_i.name>/03-flows.md
  - .deep-dive/partitions/<P_i.name>/04-semantics.md
DO NOT touch any other file under .deep-dive/.

Target path for this partition: <P_i.path>
Active flags: --critical=<bool> --comments=<bool> --depth=<lite|full>

Sibling partitions: <list>

Required reads before writing:
  - <P_i.path>: source files
  - .deep-dive/partitions/*/01-structure.md (ALL partitions, already written by Wave 1)
  - .deep-dive/partitions/*/02-interfaces.md (ALL partitions)

Cross-partition citations: when you find an outgoing call/import that leaves
your partition, cite it as <other-partition>::<symbol>.

Completion: TaskUpdate to mark completed.
```

2. Spawn `deep-dive-analysis:partition-quality-worker`:
   - Task title: `"P<i>.C — Risks+Docs for partition <P_i.name>"`
   - Task prompt: same template as B, but with `partition-quality-worker` type, owned files `05-risks.md` and `06-documentation.md`.

Record both spawns in `agents_spawned[]`.

Monitor `TaskList`. For each partition, when both `P_i.B` (or only `P_i.C` in lite mode) and `P_i.C` complete:
- Mark `partitions[i].status = "done"`

When all partitions reach `done` or `failed`: mark `phase_1_partition_workers: "complete"` (or `"failed"` if EVERY partition is failed).

## Phase 2: Synthesis

Skip if `--skip-synthesis`.

Spawn a single `deep-dive-analysis:deep-dive-synthesizer`:
- Task prompt:

```
You are deep-dive-synthesizer.

Identity: SYNTH
Owned files: .deep-dive/01-structure.md through 07-final-report.md (skip 03, 04, 06 if depth=lite).
DO NOT touch .deep-dive/08-interconnect-map.md or any partition file.

Active flags: <flags from state.json>

Partitions to consolidate:
  <for each partition: {name, path, status, language_primary}>

For any partition with status=failed, add a "⚠ Missing partitions" callout in every consolidated file. The 07-final-report.md opens with a "Partial Completeness Warning" section.

Read .deep-dive/partitions/*/ and apply the consolidation rules in your agent definition.

Completion: TaskUpdate to mark completed.
```

Monitor. On completion: mark `phase_2_synthesis: "complete"`. On failure: mark `phase_2_synthesis: "failed"` and `phase_3_interconnect: "skipped_due_to_phase_2_failure"`, then jump to Phase 4.

## Phase 3: Interconnect Map

Skip if `--skip-interconnect` or `--skip-synthesis` or Phase 2 failed.

Spawn a single `senior-review:semantic-interconnect-mapper`:
- Task prompt:

```
Build the interconnect map for this codebase using the team-deep-dive consolidated output as primary context.

Primary context source: `.deep-dive/01-07.md` (consolidated from partition outputs by the synthesizer).
Target files: the entire codebase (union of partitions; see `.deep-dive/01-structure.md ## Partition Map`).
Output path: `.deep-dive/08-interconnect-map.md`

Produce the full structured map following your agent definition: Call Graph (2-3 hop for public entry points, with cross-partition edges marked), Contracts (formal / structural / implicit), Invariants, Domain Rules, Assumptions (verified / documented / unverified), Integration Hot-Spots, Change Impact Radius, Reviewer Hints.

Every claim must cite file:line. No recommendations, no fixes. Empty sections are acceptable if nothing applies.
```

Monitor. On completion: mark `phase_3_interconnect: "complete"`. On failure: mark `phase_3_interconnect: "failed"` and continue to Phase 4 (failure is non-blocking).

## Phase 4: Completion & Next Steps Menu

1. Update `state.json`: `status: "complete"`, `completed_at: <ISO_TIMESTAMP>`.
2. Send `shutdown_request` to all remaining teammates.
3. Call `TeamDelete` to remove team resources.
4. Present summary:

```
Deep dive (team mode) complete for: <target>

Partitions: <N> (<list of names + status>)

Output Files:
  Per-partition reports:    .deep-dive/partitions/*/01..06.md
  Consolidated reports:     .deep-dive/01-structure.md .. 07-final-report.md
  Interconnect map:         .deep-dive/08-interconnect-map.md (if Phase 3 ran)

Summary:
  - Files analyzed:  <count>
  - Anti-patterns:   <count>  |  Red flags: <count>  |  Tech debt: <count>
  - Documentation gaps: <count>
  - Cross-partition flows: <count>
```

5. Show Next Steps Menu:

```
What would you like to do next?

1. Start fixing — execute the action plan
2. Apply quick fixes
3. Deep dive further — re-run a single partition
4. Generate documentation
   4a. CLAUDE.md (suggests /project-setup:create-claude-md or maintain-claude-md)
   4b. Codebase map (suggests /codebase-mapper:map-codebase)
   4c. API / interface docs (suggests /codebase-mapper:docs-create)
5. Run code review — launch /senior-review:team-review (will reuse this .deep-dive/ + 08-interconnect-map.md)
6. Export report
7. Nothing for now
```

Wait for user choice before proceeding.

## Resume Logic

On pre-flight detection of `mode == "team"` and `status == "in_progress"`:

- If `phases.phase_0_detection != "complete"`: archive and restart from zero
- If `phases.phase_1_partition_workers == "pending"`: re-run Phase 1 Wave 1
- If `phases.phase_1_partition_workers == "wave1_done"`: skip Wave 1, re-run Wave 2 for every partition with `status == "structure_done"` (no `B` and `C` outputs yet)
- If `phases.phase_1_partition_workers == "complete"` and `phase_2_synthesis != "complete"`: re-run Phase 2
- If `phases.phase_2_synthesis == "complete"` and `phase_3_interconnect != "complete"`: re-run Phase 3
- If `phases.phase_3_interconnect == "complete"`: present Phase 4 menu directly

## Quick Examples

- `/deep-dive-analysis:team-deep-dive .` — auto-detect, full depth
- `/deep-dive-analysis:team-deep-dive . --depth=lite` — lite mode (2N+2 agents)
- `/deep-dive-analysis:team-deep-dive . --critical` — prioritize security paths in Phase 3-4
- `/deep-dive-analysis:team-deep-dive . --partition packages/api --partition packages/web --yes` — manual partitions, auto-accept
- `/deep-dive-analysis:team-deep-dive . --skip-interconnect` — stop at Phase 2
- `/deep-dive-analysis:team-deep-dive . --skip-synthesis` — only per-partition reports (no consolidation)
