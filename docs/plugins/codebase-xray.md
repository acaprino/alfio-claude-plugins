# Codebase X-Ray Plugin

> Understand any codebase in minutes. Eight-phase analysis discovers how the project documents itself, maps structure, traces flows, identifies risks, and documents the WHY behind the code - not just what it does. Renamed from `deep-dive-analysis` in plugin 2.0.0 (marketplace 14.0.0); the output artifact directory is still `.deep-dive/`.

## Concurrent runs

Every analysis is an isolated run under `.deep-dive/runs/<run-id>/` with its own `state.json`, registered in `.deep-dive/runs.json`. Multiple analyses can proceed at the same time (different targets, different sessions, or a re-analysis alongside an older one) without touching each other's files. On completion a run is **published**: its `01..08.md` files are mirrored to the `.deep-dive/` root, which is the stable contract downstream consumers read (`/senior-review:team-review`, `/senior-review:code-review`, `/codebase-mapper:map-codebase`, `/project-setup:create-claude-md`). Use `--run-name <name>` for explicit run identity; otherwise the run-id derives from the target slug plus a timestamp.

Every run also records the tree it analyzed as `snapshot/manifest.json`: each file with its size, mtime and content hash, each symbol with its span and body hash. A later run on the same target detects that snapshot, diffs it against the current worktree with no model tokens spent, and offers an incremental update: unaffected claims are carried over verbatim, only the claims citing changed symbols or their direct importers are re-derived, and a mechanical gate refuses to publish while any of them is still marked stale. Each run records its parent, so the chain under `.deep-dive/runs/` is the analysis history, and `changes.md` in each run says what changed in the code and what that did to the claims. `--update` requires that a usable parent run exists and stops rather than falling back to a silent full run when one does not, though the checkpoint still offers both the incremental and the full option; `--no-update` skips detection entirely. A target that changed too much is reported as needing a full run rather than being updated quietly.

## Agents

### Partition workers

These four agents exist to serve `/codebase-xray:team-analyze` below. The classic `/codebase-xray:analyze` command runs its eight phases inline without spawning these agents; nothing here is used outside the team pipeline.

| Agent | Model | Runs during | Produces (inside the run directory) |
|-------|-------|--------------|----------|
| `partition-structure-worker` | `inherit` | Phase 1 Wave 1: Structure + Interfaces | `partitions/<name>/01-structure.md`, `02-interfaces.md` |
| `partition-behavior-worker` | `inherit` | Phase 1 Wave 2: Flows + Semantics (skipped under `--depth=lite`) | `partitions/<name>/03-flows.md`, `04-semantics.md` |
| `partition-quality-worker` | `inherit` | Phase 1 Wave 2: Risks + Documentation | `partitions/<name>/05-risks.md`, `06-documentation.md` (05 only under `--depth=lite`) |
| `partition-synthesizer` | `inherit` | Phase 2: Consolidation | `01-structure.md` through `07-final-report.md` (consolidated across partitions) |

Each worker owns only its listed output files and never touches another partition's files, the consolidated output, or the `.deep-dive/` root (other runs may be in flight). Cross-partition references use `<other-partition>::<symbol>` citation notation.

### `semantic-interconnect-mapper`

Context-builder that produces a structured map of a codebase's contracts, invariants, domain rules, assumptions, integration hot-spots, and call graph. Unlike the partition workers, it is shared across the whole marketplace: it serves three pipelines and is the reason this plugin sits at the root of the dependency graph. It lived in `senior-review` until plugin 2.1.0 (marketplace 16.0.0).

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep |
| **Use for** | Building the structured-facts artifact that downstream reviewers and writers cite instead of paraphrasing code |

**Consumers:**

| Pipeline | Phase | Artifact produced |
|---|---|---|
| `/codebase-xray:team-analyze` | Phase 3 | `08-interconnect-map.md`, the global cross-partition view |
| `/senior-review:team-review` | Phase 1b | `.team-review/02-interconnect.md`, which every reviewer reads and which `logic-integrity-auditor` requires |
| `/codebase-mapper:map-codebase` and `/codebase-mapper:team-codebase-map` | Phase 1b | `.codebase-map/_internal/interconnect.md`, cited by `tech-writer`, `flow-writer`, `ops-writer`, and `guide-reviewer` |

**Output sections:** `## Contracts` (formal + implicit), `## Invariants` (temporal + structural), `## Assumptions` (unverified), `## Domain Rules`, `## Integration Hot-Spots` (HTTP, queue, IPC, env/config), `## Call Graph`. Each section is self-contained so consumers can Grep a single heading and get full context.

Input source differs per pipeline: X-ray output for `team-review`, the consolidated partition set for `team-analyze`, and `codebase-explorer`'s context brief for the `codebase-mapper` pipelines. It never proposes fixes; every claim carries a `file:line` citation.

---

## Skills

### `xray-method`

The method itself: structure extraction fused with semantic reading, the concurrent runs model, Phase 0, and the multi-language script suite (Python stdlib-only; optional tree-sitter for Java/JS/TS/Rust fidelity; Python >= 3.10). Named `analyze` until plugin 3.0.0, when it shared its name with the command and the command shadowed it on any host that lists both under one identifier.

| | |
|---|---|
| **Load as** | `codebase-xray:xray-method`; the `team-analyze` workers read it directly, and `/codebase-xray:analyze` is the command that applies it |
| **Use for** | Codebase understanding, architecture mapping, onboarding, pre-review ground truth |

**Capabilities:**
- Extract code structure (classes, functions, imports)
- Map internal/external dependencies
- Recognize architectural patterns
- Identify anti-patterns and red flags
- Trace data and control flows

---

## Commands

### `/codebase-xray:analyze`

8-phase systematic codebase analysis with per-run state management, output files, and phased execution: project knowledge discovery -> structure -> interfaces -> flows -> semantics -> risks -> documentation -> report.

**Phase 0 (Project Knowledge Discovery)** runs first on every invocation, including `--depth=lite`, `--phase N` and `--docs-only`, and it is a preamble rather than a selectable analysis phase: phases 1 to 7 keep their numbers, so no existing `--phase` invocation changes meaning. It reads the project's own instruction files and indexes and records where the project claims each concept lives, writing `knowledge/navigation.md` and `knowledge/documentation-leads.md`. Both hold **leads, never verified facts**: the phase reads no code, so every row is `documented` or `unverified`. This is the cheap discovery pass, kept deliberately apart from Phase 6, which is the expensive audit of whether those documents are accurate. Conflating the two is what once made lite mode blind to a project's own documentation. `/senior-review:team-review` Phase 1d consumes `knowledge/documentation-leads.md` as one half of its knowledge-provenance join.

```
/codebase-xray:analyze src/core/ --critical
/codebase-xray:analyze src/api --run-name api      # named run, safe to run others concurrently
```

**Output:** `.deep-dive/runs/<run-id>/` with a `knowledge/` directory from Phase 0, 7 phase files, and a final consolidated report, published to the `.deep-dive/` root on completion.

---

### `/codebase-xray:team-analyze`

Multi-agent variant of `/codebase-xray:analyze` for large or partitioned codebases: auto-detects partitions, runs the structural/behavioral/quality phases in parallel per partition across two waves, then consolidates into the same `01..07.md` layout plus a global cross-partition interconnect map, all inside an isolated run directory.

**Prerequisites:** none beyond the host. Worker dispatch, context isolation and the delivery barrier come from the harness the compiler generates for each host, so the plugin declares no dependency and its bodies name no host primitive.

| | |
|---|---|
| **Invoke** | `/codebase-xray:team-analyze <target> [--critical] [--comments] [--depth=lite\|full] [--partition <path>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes]` |

**Pipeline:**

0. **Project knowledge discovery**: the same Phase 0 as `/codebase-xray:analyze`, run once inline for the whole run before partition detection. It is global, not per partition, and no worker owns any of its output: `knowledge/navigation.md` and `knowledge/documentation-leads.md`.
1. **Partition detection** (its own Phase 0): explicit workspace manifests (pnpm/npm workspaces, Lerna, Nx, Turbo, Cargo, uv) -> convention-based monorepo layout (`apps/`, `packages/`, `services/`) -> frontend/backend layer split -> language-cluster split -> single-partition fallback. Presents a checkpoint to accept, modify, or manually override the partition list before dispatching anything. There is no team-creation step: the host harness dispatches each worker and records it as delivered or failed.
2. **Wave 1** (parallel): one `partition-structure-worker` per partition writes structure and interfaces.
3. **Wave 2** (parallel): `partition-behavior-worker` and `partition-quality-worker` per partition write flows/semantics and risks/documentation, each citing sibling partitions' Wave 1 output for cross-partition calls. Under `--depth=lite` the behavior workers are not spawned and quality workers write risks only.
4. **Synthesis**: `partition-synthesizer` consolidates every partition's output into the standard `01-structure.md` through `07-final-report.md` files inside the run directory, flagging any failed partition inline.
5. **Interconnect map**: `codebase-xray:semantic-interconnect-mapper` reads the consolidated output and produces `08-interconnect-map.md`, the global cross-partition contract/invariant map that `/senior-review:team-review` reuses directly.
6. **Publish**: the consolidated set (and interconnect map) is mirrored to the `.deep-dive/` root for downstream consumers, and the run is closed in `runs.json`.

```
/codebase-xray:team-analyze .                                   # auto-detect, full depth
/codebase-xray:team-analyze . --depth=lite                      # lite mode, fewer agents
/codebase-xray:team-analyze . --partition packages/api --partition packages/web --yes
```

Resume-safe: re-running against an in-progress run in `runs.json` re-spawns only the missing workers for the phase that stopped.

---

**Related:** [codebase-mapper](codebase-mapper.md) (generates 10 narrative documents from codebase exploration) | [senior-review](senior-review.md) (code review agents that run after the X-ray)
