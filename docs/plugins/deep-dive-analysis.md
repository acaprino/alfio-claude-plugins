# Deep Dive Analysis Plugin

> Understand any codebase in minutes. Seven-phase analysis maps structure, traces flows, identifies risks, and documents the WHY behind the code -- not just what it does.

## Agents

These four agents exist to serve `/deep-dive-analysis:team-deep-dive` below. The classic `/deep-dive-analysis` command runs its seven phases inline without spawning agents; nothing here is used outside the team pipeline.

| Agent | Model | Runs during | Produces |
|-------|-------|--------------|----------|
| `partition-structure-worker` | `inherit` | Phase 1 Wave 1: Structure + Interfaces | `.deep-dive/partitions/<name>/01-structure.md`, `02-interfaces.md` |
| `partition-behavior-worker` | `inherit` | Phase 1 Wave 2: Flows + Semantics | `.deep-dive/partitions/<name>/03-flows.md`, `04-semantics.md` |
| `partition-quality-worker` | `inherit` | Phase 1 Wave 2: Risks + Documentation | `.deep-dive/partitions/<name>/05-risks.md`, `06-documentation.md` |
| `deep-dive-synthesizer` | `inherit` | Phase 2: Consolidation | `.deep-dive/01-structure.md` through `07-final-report.md` (consolidated across partitions) |

Each worker owns only its listed output files and never touches another partition's files or the consolidated output. Cross-partition references use `<other-partition>::<symbol>` citation notation.

---

## Skills

### `deep-dive-analysis`

Systematic codebase analysis that combines structure extraction with semantic understanding.

| | |
|---|---|
| **Invoke** | `/deep-dive-analysis` |
| **Use for** | Codebase understanding, architecture mapping, onboarding |

**Capabilities:**
- Extract code structure (classes, functions, imports)
- Map internal/external dependencies
- Recognize architectural patterns
- Identify anti-patterns and red flags
- Trace data and control flows

---

## Commands

### `/deep-dive-analysis`

7-phase systematic codebase analysis with state management, output files, and phased execution: structure -> interfaces -> flows -> semantics -> risks -> documentation -> report.

```
/deep-dive-analysis src/core/ --critical
```

**Output:** `.deep-dive/` directory with 7 phase files and a final consolidated report.

---

### `/deep-dive-analysis:team-deep-dive`

Multi-agent variant of `/deep-dive-analysis` for large or partitioned codebases: auto-detects partitions, runs the structural/behavioral/quality phases in parallel per partition across two waves, then consolidates into the same `.deep-dive/01..07.md` layout plus a global cross-partition interconnect map.

**Prerequisites:** requires the upstream `agent-teams` plugin (`wshobson/agents`, MIT) for the `agent-teams:task-coordination-strategies`, `agent-teams:team-communication-protocols`, and `agent-teams:parallel-feature-development` skills:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

| | |
|---|---|
| **Invoke** | `/deep-dive-analysis:team-deep-dive <target> [--critical] [--comments] [--depth=lite\|full] [--partition <path>] [--skip-interconnect] [--skip-synthesis] [--yes]` |

**Pipeline:**

1. **Partition detection** (Phase 0): explicit workspace manifests (pnpm/npm workspaces, Lerna, Nx, Turbo, Cargo, uv) -> convention-based monorepo layout (`apps/`, `packages/`, `services/`) -> frontend/backend layer split -> language-cluster split -> single-partition fallback. Presents a checkpoint to accept, modify, or manually override the partition list before spawning anything.
2. **Wave 1** (parallel): one `partition-structure-worker` per partition writes structure and interfaces.
3. **Wave 2** (parallel, skipped under `--depth=lite`): `partition-behavior-worker` and `partition-quality-worker` per partition write flows/semantics and risks/documentation, each citing sibling partitions' Wave 1 output for cross-partition calls.
4. **Synthesis**: `deep-dive-synthesizer` consolidates every partition's output into the standard `.deep-dive/01-structure.md` through `07-final-report.md` files, flagging any failed partition inline.
5. **Interconnect map**: `senior-review:semantic-interconnect-mapper` reads the consolidated output and produces `.deep-dive/08-interconnect-map.md`, the global cross-partition contract/invariant map that `/senior-review:team-review` reuses directly.

```
/deep-dive-analysis:team-deep-dive .                                   # auto-detect, full depth
/deep-dive-analysis:team-deep-dive . --depth=lite                      # lite mode, fewer agents
/deep-dive-analysis:team-deep-dive . --partition packages/api --partition packages/web --yes
```

Resume-safe: re-running against an in-progress `.deep-dive/state.json` re-spawns only the missing workers for the phase that stopped.

---

**Related:** [codebase-mapper](codebase-mapper.md) (generates 10 narrative documents from codebase exploration) | [senior-review](senior-review.md) (code review agents that run after deep-dive)
