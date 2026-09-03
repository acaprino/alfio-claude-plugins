# Case: team-mode-partition-ownership

Team mode partitions the target and dispatches one worker per partition per wave, each owning exactly its files under `partitions/<name>/`. The consolidated set must then be indistinguishable in layout from a classic run, because every downstream consumer reads the same seven files. This case checks the ownership contract from the transcript and the layout from the run directory.

## Setup

A scratch pnpm workspace with two packages, `packages/api` (TypeScript, 8 to 12 files) and `packages/web` (TypeScript, 8 to 12 files), where `web` imports two symbols from `api`. Tree-sitter may be installed or not; note which in the scorecard.

## Run

```
/codebase-xray:team-analyze . --depth=lite --yes
```

Keep the full transcript.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Partition detection found `api` and `web` from the workspace manifest, and the plan named one structure worker and one quality worker per partition |
| 2 | MUST | No worker wrote a file outside its own `partitions/<name>/` directory: every write in the transcript attributed to a worker targets its owned files |
| 3 | MUST | Wave 2 workers were dispatched only after both Wave 1 workers were recorded delivered |
| 4 | MUST | The run directory contains `01-structure.md`, `02-interfaces.md`, `05-risks.md` and `07-final-report.md` at its root with the classic `##` section anchors, and no `03`, `04` or `06` |
| 5 | MUST | The consolidated `01-structure.md` lists the two `api` symbols `web` imports under its cross-partition section, attributed to the right partitions |
| 6 | SHOULD | The synthesizer read partition files by section rather than whole, per the context budget |

## Scoring notes

Assertion 2 is read from the transcript, not inferred from the final tree: a worker that wrote to a sibling's directory and was overwritten by the sibling leaves no trace in the tree. Assertion 3 is the wave barrier, which on hosts without a shared task list is the coordinator's own bookkeeping; a Wave 2 dispatch before both deliveries fails it regardless of the outcome.
