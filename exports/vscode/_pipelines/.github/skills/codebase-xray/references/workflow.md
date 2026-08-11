# X-Ray Workflow

The complete workflow driven by `/xray-team-analyze <target> [flags]`, running on the `xray-orchestrator` agent. Paths written as `$XRAY/...` refer to this skill's directory (see "Resolving the skill directory" in `SKILL.md`).

This is the only entry point. Small single-package repos are handled by detection rule 5, which produces one partition named `root`; the pipeline shape does not change.

The per-phase output templates live in the worker agent definitions under `.github/agents/`, not here. Read the relevant agent file when you need a template.

## CRITICAL RULES

1. **Execute phases in order.** No skipping unless `--skip-synthesis` or `--skip-interconnect` is set.
2. **Dispatch workers with explicit file ownership.** Every dispatch prompt enumerates the owned output files.
3. **Run isolation.** All output goes to `$RUN_DIR` until the publish step. Concurrent runs never share files.
4. **Respect the wave barriers.** Wave 2 starts only after every partition's `01-structure.md` and `02-interfaces.md` exist on disk.
5. **Do not hand off to the `plan` agent.** Execute immediately.
6. **Code is ground truth.** Document what the code actually does, not what you think it should do.
7. **Resume-safe.** Re-dispatch only missing workers on resume.

## Subagents

All five ship with this bundle under `.github/agents/`. Each worker accepts an `output_dir` input, so partition scoping stays out of the worker logic.

| Agent | Phases | Owned output |
|---|---|---|
| `xray-structure-worker` | 1 + 2 | `01-structure.md`, `02-interfaces.md` |
| `xray-behavior-worker` | 3 + 4 | `03-flows.md`, `04-semantics.md` |
| `xray-quality-worker` | 5 + 6 | `05-risks.md`, `06-documentation.md` |
| `xray-synthesizer` | consolidation | `01..07.md` at the run root |
| `xray-interconnect-mapper` | contract mapping | `08-interconnect-map.md` at the run root |

Dispatch each one with `#agent/runSubagent`. They are listed in the `agents:` allowlist of `xray-orchestrator`, and each is marked `user-invocable: false`, so they never clutter the agents dropdown.

If `#agent/runSubagent` is unavailable (the tool was disabled, or you were invoked from an agent without it), say so explicitly, then execute each worker's role inline, one partition at a time, in the same wave order. Read the agent definition file for the role you are executing: it carries the phase spec and the output template. The file layout is the coordination mechanism, so the output is identical and only wall-clock time changes. Do not degrade silently.

## Tool Integration

The scripts in `$XRAY/scripts/` are language-aware and support **Python, Java, JavaScript, TypeScript (incl. TSX/JSX), SQL, PL/SQL, Rust**. Run them with `#execute/runInTerminal` instead of manual file reading whenever the target file matches one of those languages.

- **Phases 1-2 (Structure):** `ast_parser.py` for class/function/import extraction, `classifier.py` for file classification. Do NOT parse AST manually or count imports with `#search/textSearch`.
- **Phase 5 (Risks):** `usage_finder.py` to trace symbol usages. Multi-language: matches Python `from/import`, Java `import`, JS/TS `import`/`require`, Rust `use`, etc.
- **Phase 6 (Docs):** `doc_review.py` for link validation and marker checks, `rewrite_comments.py` for multi-language comment quality analysis.

For unsupported languages, use `#read/readFile`, `#search/textSearch`, and `#search/usages` directly. Tree-sitter is optional (see Prerequisites in `SKILL.md`): when `tree-sitter-language-pack` is installed, Java/JS/TS/Rust use tree-sitter parsers for higher fidelity; otherwise a regex fallback is used. Python always uses the stdlib `ast` module. SQL and PL/SQL use a regex-based DDL extractor.

Do NOT use raw shell commands (`cat`, `grep`, `find`) to extract structure when a dedicated script exists. The scripts use real parsers, which are faster, more accurate, and consume fewer tokens than reading files line by line.

## Forbidden Files

NEVER read or include contents from:
- `.env`, `.env.*`: environment variables with secrets
- `credentials.*`, `secrets.*`, `*secret*`, `*credential*`
- `*.pem`, `*.key`, `*.p12`, `*.pfx`: certificates and private keys
- `id_rsa*`, `id_ed25519*`: SSH keys
- `.npmrc`, `.pypirc`, `.netrc`: auth tokens
- Any file that appears to contain API keys, passwords, or tokens

When agent hooks are enabled, `$XRAY/hooks/xray_guard.py` denies these at the tool layer for every worker. If you encounter one anyway, note its existence only (`.env` present, contains environment config). NEVER quote contents.

## Pre-flight

1. Parse arguments. The user types them after `/xray-team-analyze` in the chat input:
   - `<target>`: directory to analyze (default: workspace root)
   - `--critical`: prioritize auth, payment, and persistence flows in Phases 3-4
   - `--comments`: activate the comment audit in Phase 6
   - `--depth=lite|full`: lite skips Phases 3, 4, and 6 (behavior workers not dispatched; quality workers write only `05-risks.md`; synthesizer skips 03/04/06)
   - `--docs-only`: documentation health only. Dispatch structure workers (Wave 1 is still needed to scope the public API surface), then quality workers restricted to Phase 6. Skip Phases 3, 4, 5 and the interconnect map.
   - `--partition <path>`: manual partition (repeatable; overrides auto-detect)
   - `--partition-name <name>`: symbolic name for the N-th manual partition (1-indexed; optional)
   - `--skip-synthesis`: per-partition reports only, no consolidation, no interconnect map, no publish
   - `--skip-interconnect`: stop after synthesis, no `08-interconnect-map.md`
   - `--run-name <name>`: explicit run identity for concurrent or repeated analyses
   - `--yes`: auto-accept the partition checkpoint

   If no target was given, ask for it with `#vscode/askQuestions` before doing anything else.

   Reject `--phase N` with an explicit error: phases are split across waves and workers here, so starting mid-pipeline is not coherent. Point the user at `--depth=lite`, `--docs-only`, or `--skip-interconnect` instead.

2. Resolve the run (see "Concurrent Runs Model" in `SKILL.md`):
   - Compute `run-id`: `--run-name` (normalized to `[a-z0-9-]`) or `<slug-of-target>-<YYYYMMDD-HHMMSS>`; append `-2`, `-3`, ... on collision
   - Set `RUN_DIR = .deep-dive/runs/<run-id>`
   - Read `.deep-dive/runs.json`: list active runs; offer to resume a matching in-progress run or start this one alongside. A root `state.json` with `current_phase` and no `runs.json` is a pre-runs legacy layout: offer to migrate it into `.deep-dive/runs/legacy-<date>/` first
   - Register the run in `runs.json` (read-modify-write, append `{run_id, target, mode: "team", started_at}` to `active`). Never drop entries you did not create.

Track the four phases with `#todos` so the user sees progress while workers run.

## Phase 0: Knowledge Discovery and Partition Detection

### Initialize state

Create `$RUN_DIR/` with `#edit/createDirectory` and `$RUN_DIR/state.json` with `#edit/createFile`:

```json
{
  "run_id": "<run-id>",
  "target": "<target>",
  "mode": "team",
  "status": "in_progress",
  "flags": { "critical": false, "comments": false, "docs_only": false, "depth": "full" },
  "partitions": [],
  "phases": {
    "phase_0_knowledge": "pending",
    "phase_0_detection": "pending",
    "phase_1_partition_workers": "pending",
    "phase_2_synthesis": "pending",
    "phase_3_interconnect": "pending"
  },
  "workers_dispatched": [],
  "files_created": [],
  "started_at": "<ISO_TIMESTAMP>",
  "completed_at": null
}
```

### Project Knowledge Discovery (X-ray Phase 0)

Runs once for the whole run, inline on the orchestrator, before partition detection. It is **global**: it does not run per partition, and no partition worker owns any of its output. It also runs at every depth, `--depth=lite` included. It is the cheap discovery pass; Phase 6 is the expensive audit, and conflating the two is what made lite mode blind to a project's own documentation.

This phase owns discovery of **how the repository documents itself**. It does not evaluate whether the documentation is accurate, which is Phase 6.

1. Read `AGENTS.md`, `.github/copilot-instructions.md`, `CLAUDE.md` and any equivalent project instruction file at the workspace root and in the target's ancestors. Record any navigation instruction they give, especially a statement of the form "look here first to find where a concept lives".
2. Locate the canonical indexes the project actually uses. Search with `#search/fileSearch` for, at minimum: `**/SEARCH_INDEX.md`, `**/INDEX.md`, `docs/README.md`, `README.md`, `**/BY_DOMAIN.md`, `**/adr/**`, `**/decisions/**`, `**/architecture/**`, `**/domains/**`, `.codebase-map/INDEX.md`. Record what exists, not what you expected to exist.
3. For each concept, symbol and subsystem the run will cover across all partitions, search the located documents for an entry with `#search/textSearch`. Record the concept, the document, and the anchor or heading that matched.
4. Write both output files with `#edit/createFile`. Every row is a lead with status `documented` or `unverified`. Nothing here is `verified`, because this phase reads no code.

**Output file:** `$RUN_DIR/knowledge/navigation.md`

```markdown
# Project Knowledge Navigation

## Project instructions read
| File | Navigation rule it states |
|------|---------------------------|

## Canonical indexes found
| Index | Path | What it indexes |
|-------|------|-----------------|

## Conventions observed
[How this repository organizes its knowledge, in prose. Name the file the project treats as its semantic index, if it has one.]

## Not found
[Index kinds searched for and absent. An absent index is a fact worth recording.]
```

**Output file:** `$RUN_DIR/knowledge/documentation-leads.md`

```markdown
# Documentation Leads

> Leads, not truth. Every row is a pointer to where the project claims a concept lives.
> Status is `documented` or `unverified`. No row here is `verified`: this phase reads no code.

| Concept / symbol | Document | Anchor | Status |
|------------------|----------|--------|--------|

## Concepts in scope with no lead
[Concepts the scope touches for which no document was found. This list is what a
downstream consumer must discover independently.]
```

### Detection algorithm

If `--partition` was provided one or more times, skip auto-detect and use the manual list. Apply `--partition-name` mappings if provided; otherwise derive names from the path basename.

Otherwise run the detection chain (first rule that matches wins):

1. **Explicit workspace manifests** (in order):
   - `pnpm-workspace.yaml` -> `packages` field paths
   - `package.json` with a `workspaces` field
   - `lerna.json` `packages`
   - `nx.json` + `apps/` + `libs/`
   - `turbo.json` + `apps/` + `packages/`
   - `Cargo.toml` `[workspace] members`
   - `pyproject.toml` `[tool.uv.workspace] members` or equivalent
2. **Convention-based monorepo:**
   - `apps/`, `packages/`, or `services/` at root with more than one subdirectory
   - `src/` with sub-dirs each having their own `package.json` / `pyproject.toml`
3. **Layer split:**
   - `src/{backend,frontend}`, `src/{api,web}`, `src/{server,client}`, or root-level `backend/` + `frontend/`
4. **Language split:**
   - Use `python "$XRAY/scripts/classifier.py"` to count files per language
   - If two or more languages have at least 20 files each: partition per language (`*.py` -> `python`, `*.ts`/`*.tsx` -> `typescript`)
5. **Fallback:** single partition wrapping the entire target, name = `root`

**Always excluded paths:** `node_modules/`, `dist/`, `build/`, `.next/`, `target/`, `vendor/`, `__pycache__/`, `.venv/`.

**Partition naming rules:**
1. From workspace path -> basename
2. On collision -> slug-ified path
3. From language fallback -> language name
4. From single-partition fallback -> `root`

Normalize names: lowercase, separators to hyphen, strip accents, allowed chars `[a-z0-9-]`.

For each partition compute `file_count` and `loc_estimate` (use `classifier.py` plus `wc -l`, or `cloc` if available).

### Checkpoint

Present to the user:

```
X-ray scope:
Target: <target>
Run: <run-id>  (concurrent active runs: <count or "none">)

Detected partitioning strategy: <strategy name>

Proposed partitions (<N>):
  P1: <path>          (<language>, <file-count> files, ~<loc>k LOC)
  ...

Dispatch plan: <N> partitions x <2|3> workers = <2N|3N> workers
               + 1 synthesizer + 1 interconnect mapper = <total> agents.

Note: token cost scales linearly with file count x workers. Consider --depth=lite
for monorepos with many partitions.

Options:
  [A] Accept and start
  [M] Modify partition list (rename, regroup, exclude one)
  [m] Manual: provide partition paths
  [c] Cancel
```

Use `#vscode/askQuestions` for the choice. If `--yes`, auto-select `[A]` without asking.

If `[M]`, prompt for changes: `rename <old> <new>`, `exclude <name>`, `merge <name1> <name2> [<merged-name>]`, `done` to finalize.

If `[m]`, prompt for paths and optional names.

If `[c]`, set state to `cancelled`, remove the run from `active` in `runs.json`, and exit.

Finalize the `partitions` array in `state.json` with `{name, path, language_primary, file_count, loc_estimate, status: "pending"}` for each. Mark `phase_0_detection: "complete"`.

## Phase 1: Partition Workers (2 waves)

### Wave 1: Structure workers

For each partition `P_i`:

1. Create `$RUN_DIR/partitions/<P_i.name>/`
2. Dispatch `xray-structure-worker` with `#agent/runSubagent` and this prompt:

```
You are xray-structure-worker on partition "<P_i.name>".

Identity: P<i>.A
Run directory: <RUN_DIR>
Output directory: <RUN_DIR>/partitions/<P_i.name>
Owned files:
  - <output_dir>/01-structure.md
  - <output_dir>/02-interfaces.md
DO NOT touch any other file under .deep-dive/.

Target path for this partition: <P_i.path>
Active flags: --critical=<bool> --comments=<bool> --depth=<lite|full>

Sibling partitions (for cross-partition citation lookup):
  <list each P_j.name -> P_j.path, or "none" if this is the only partition>

Skill directory: <resolved $XRAY path>
```

3. Record the dispatch in `workers_dispatched[]` as `{name: "P<i>.A", type: "xray-structure-worker", partition: "<P_i.name>"}`.

Issue all `P_i.A` dispatches in a single assistant turn so VS Code can run them concurrently. Do not wait on one before dispatching the next.

**Wave 1 barrier.** Poll with `#search/fileSearch` until, for every partition, both `01-structure.md` and `02-interfaces.md` exist under `$RUN_DIR/partitions/<name>/`. A worker whose files never appear counts as failed. Do not rely on returned summaries alone: file existence is the contract.

Mark each `partitions[i].status` as `"failed"` if its files are missing, `"structure_done"` otherwise. Mark `phase_1_partition_workers: "wave1_done"`.

If EVERY partition failed, abort: mark the run `failed`, remove it from `active` in `runs.json`, and report.

### Wave 2: Behavior + Quality workers

Skip behavior workers if `--depth=lite` or `--docs-only`.

For each partition `P_i` with `status == "structure_done"`:

1. If neither `--depth=lite` nor `--docs-only` is set, dispatch `xray-behavior-worker`:

```
You are xray-behavior-worker on partition "<P_i.name>".

Identity: P<i>.B
Run directory: <RUN_DIR>
Output directory: <RUN_DIR>/partitions/<P_i.name>
Owned files:
  - <output_dir>/03-flows.md
  - <output_dir>/04-semantics.md
DO NOT touch any other file under .deep-dive/.

Target path for this partition: <P_i.path>
Active flags: --critical=<bool> --comments=<bool> --depth=<lite|full>
Sibling partitions: <list, or "none">

Required reads before writing:
  - <P_i.path>: source files
  - <RUN_DIR>/partitions/*/01-structure.md (ALL partitions, written by Wave 1)
  - <RUN_DIR>/partitions/*/02-interfaces.md (ALL partitions)

Cross-partition citations: when you find an outgoing call or import that leaves
your partition, cite it as <other-partition>::<symbol>.

Skill directory: <resolved $XRAY path>
```

2. Dispatch `xray-quality-worker` with the same template. Owned files: `05-risks.md` and `06-documentation.md` at full depth; `05-risks.md` only under `--depth=lite`; `06-documentation.md` only under `--docs-only`.

Record both dispatches in `workers_dispatched[]`.

**Wave 2 barrier.** Poll with `#search/fileSearch` for the expected files per partition, which depend on the active flags. Mark `partitions[i].status = "done"` when they appear. When every partition is `done` or `failed`, mark `phase_1_partition_workers: "complete"`.

## Phase 2: Synthesis

Skip if `--skip-synthesis`.

Dispatch a single `xray-synthesizer`:

```
You are xray-synthesizer.

Identity: SYNTH
Run directory: <RUN_DIR>
Owned files: <RUN_DIR>/01-structure.md through <RUN_DIR>/07-final-report.md
(skip 03, 04, 06 if depth=lite; write only 01, 02, 06, 07 if docs_only).
DO NOT touch <RUN_DIR>/08-interconnect-map.md, any partition file, or anything at
the .deep-dive/ root.

Active flags: <flags from state.json>

Partitions to consolidate:
  <for each partition: {name, path, status, language_primary}>

For any partition with status=failed, add a "Missing partitions" callout in every
consolidated file. 07-final-report.md opens with a "Partial Completeness Warning".

Read <RUN_DIR>/partitions/*/ and apply the consolidation rules in your agent
definition.
```

Verify with `#search/fileSearch` that the expected consolidated files exist. On success mark `phase_2_synthesis: "complete"`. On failure mark it `"failed"`, set `phase_3_interconnect: "skipped_due_to_phase_2_failure"`, and jump to Phase 4 without publishing.

## Phase 3: Interconnect Map

Skip if `--skip-interconnect`, `--skip-synthesis`, `--docs-only`, or Phase 2 failed.

Dispatch a single `xray-interconnect-mapper`:

```
You are xray-interconnect-mapper.

Identity: MAP
Run directory: <RUN_DIR>
Owned file: <RUN_DIR>/08-interconnect-map.md
DO NOT touch any consolidated 01..07 file, any partition file, or anything at the
.deep-dive/ root.

Primary context source: the consolidated X-ray output at <RUN_DIR>/01..07.md.
Target files: the union of all partitions (see <RUN_DIR>/01-structure.md
"## Partition Map").
Partitions: <for each partition: {name, path, status}>
X-ray depth: <lite|full>

Produce the full structured map following your agent definition: Call Graph
(2-3 hops for public entry points, cross-partition edges marked), Contracts
(formal / structural / implicit), Invariants, Domain Rules, Assumptions
(verified / documented / unverified), Integration Hot-Spots, Change Impact
Radius, Review Focus Hints.

Every claim must cite file:line. No recommendations, no fixes. Empty sections are
acceptable if nothing applies.
```

Verify with `#search/fileSearch` that `08-interconnect-map.md` exists. On success mark `phase_3_interconnect: "complete"`. On failure mark it `"failed"` and continue to Phase 4: this failure is non-blocking.

## Phase 4: Publish, Completion & Next Steps

1. Update `$RUN_DIR/state.json`: `status: "complete"`, `completed_at: <ISO_TIMESTAMP>`.
2. **Publish** (skip if `--skip-synthesis` or synthesis failed): copy `$RUN_DIR/01-*.md` through `$RUN_DIR/07-final-report.md` (those that exist), `$RUN_DIR/08-interconnect-map.md` (if Phase 3 ran), and `$RUN_DIR/state.json` to the `.deep-dive/` root, overwriting the previous mirror. Update `runs.json` with read-modify-write: remove this run from `active`, set `latest_completed`. The root mirror is the downstream contract.
3. Present the summary:

```
X-ray complete for: <target>
Run: <run-id> (published to .deep-dive/ root)

Partitions: <N> (<list of names + status>)

Output Files:
  Knowledge discovery:   .deep-dive/runs/<run-id>/knowledge/navigation.md, documentation-leads.md (Phase 0)
  Per-partition reports: .deep-dive/runs/<run-id>/partitions/*/01..06.md
  Consolidated reports:  .deep-dive/runs/<run-id>/01-structure.md .. 07-final-report.md
  Interconnect map:      .deep-dive/runs/<run-id>/08-interconnect-map.md (if Phase 3 ran)
  Root mirror:           .deep-dive/01..08.md (for downstream consumers)

Summary:
  - Files analyzed:  <count>
  - Anti-patterns:   <count>  |  Red flags: <count>  |  Tech debt: <count>
  - Documentation gaps: <count>
  - Cross-partition flows: <count>
  - Contracts mapped: <count>  |  Unverified assumptions: <count>
```

4. Generate a prioritized action plan from the findings, grouped by urgency:

```
CRITICAL (fix now):
1. [Action derived from 05-risks critical findings]
2. [Action derived from security red flags, or unverified assumptions at inbound
   integration hot-spots in 08-interconnect-map.md]

HIGH (fix soon):
3. [Action derived from anti-patterns or tech debt]
4. [Action derived from documentation gaps]

RECOMMENDED (improve when possible):
5. [Action derived from code quality observations]
6. [Action derived from naming or convention inconsistencies]
```

Each action must cite the specific finding and file (e.g. "Fix missing input validation in `src/auth/login.py::handle_request`, see 05-risks.md").

5. Show the Next Steps Menu:

```
What would you like to do next?

1. Start fixing: execute the action plan (all or selected items)
2. Apply quick fixes: stale comments, outdated references, type hints, naming
3. Analyze further: re-run a single partition as a new run
4. Generate documentation from the published .deep-dive/ mirror, which is now
   available as technical ground truth
5. Export report in a different format
6. Nothing for now
```

Wait for the user's choice. If the user picks option 1, confirm which actions to execute and in what order before starting.

If the user picks option 2, use the dedicated scripts for safe, automated fixes:

1. **Comment cleanup:** run `python "$XRAY/scripts/rewrite_comments.py" rewrite <file> --apply --backup` for each file flagged in Phase 6. The script handles backup, lexer-safe removal of trivial and backup comments, and auto-formatting. Works on Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust. Do NOT hand-edit comments when the script supports the language.
2. **Type hint / annotation fixes:** apply with `#edit/editFiles` one file at a time, verifying syntax after each change.
3. **Stale references:** update outdated names in comments with targeted `#edit/editFiles` replacements.

Present a summary of changes made. For languages outside the supported set, fall back to targeted `#edit/editFiles` changes with explicit before/after diffs shown to the user.

Note that the workers cannot make these edits: their tool sets exclude source-file writes by design. Quick fixes run on the orchestrator, after the run has been published.

## Resume Logic

If pre-flight finds an active run in `runs.json` whose `$RUN_DIR/state.json` says `status == "in_progress"`, offer to resume:

- `phase_0_detection != "complete"`: remove the run and restart from zero
- `phase_1_partition_workers == "pending"`: re-run Wave 1
- `phase_1_partition_workers == "wave1_done"`: skip Wave 1, re-run Wave 2 for every partition with `status == "structure_done"`
- `phase_1_partition_workers == "complete"` and `phase_2_synthesis != "complete"`: re-run Phase 2
- `phase_2_synthesis == "complete"` and `phase_3_interconnect != "complete"`: re-run Phase 3
- `phase_3_interconnect == "complete"`: run the Phase 4 publish step and present the menu directly

Resuming dispatches fresh workers as needed. The run directory carries the run identity.

## Quick Examples

- `/xray-team-analyze .`: auto-detect partitions, full depth, with interconnect map
- `/xray-team-analyze src/`: scope to a subtree
- `/xray-team-analyze . --depth=lite`: skip flows, semantics, and doc health (2N+2 agents)
- `/xray-team-analyze . --critical`: prioritize auth, payment, and persistence paths
- `/xray-team-analyze . --comments`: include the comment quality audit
- `/xray-team-analyze . --docs-only`: documentation health only
- `/xray-team-analyze . --partition packages/api --partition packages/web --yes`: manual partitions, auto-accept
- `/xray-team-analyze . --skip-interconnect`: stop after synthesis
- `/xray-team-analyze . --skip-synthesis`: per-partition reports only
- `/xray-team-analyze apps/backend --run-name backend`: named run, safe alongside other active runs
