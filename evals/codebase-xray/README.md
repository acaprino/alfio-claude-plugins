# codebase-xray eval harness

Measures whether `codebase-xray` still behaves the way it is designed to behave. The plugin has no bug ground truth to recall: its value is a set of **behavioral invariants** (Phase 0 always runs, a run never writes outside its own directory, structure comes from the parsers and not from reading files by hand, a secret file is noted and never quoted, every claim cites where it came from and how sure it is), and the failure mode is drift, where a later edit quietly removes one and nothing notices.

Each case states a target, the command, and assertions that either hold or do not. Assertions target the philosophy, never the wording: "every finding cites a file and a line" is an invariant, "uses the phrase file:line" is not. This directory is a development asset of the marketplace repository: not part of the `codebase-xray` plugin, not registered in `marketplace.json`, never shipped.

The script suite has a separate, mechanical guard: `tests/test_xray_scripts.py` runs on every push. These cases cover what a unit test cannot, which is what the agent does with the scripts.

## Protocol

0. **Establish which version is under test, and prove it.** Check `~/.claude/plugins/cache/<marketplace>/codebase-xray/` against `marketplace.json`; if they differ, update the marketplace and start a new session, or run against the working-tree files and say so in the scorecard. A run whose scorecard does not name the version it exercised is not a result.
1. **Materialize the target** the case describes in a scratch directory, never in this repository: the plugin's own files would become part of the codebase under test. Most cases give a small fixture; `team-mode-partition-ownership` needs a two-package workspace.
2. **Run the case's command in a FRESH session.** Context from a previous case leaks the answers, and a stale `.deep-dive/` in the scratch directory leaks a previous run.
3. **Keep the transcript.** Several assertions read it: whether the scripts were invoked, whether a secret was quoted, whether a worker wrote outside its directory.
4. **Score each assertion** `pass`, `fail`, or `n/a` (only when the case makes it conditional).
5. **Record the run** in a copy of `scorecard-template.md` inside the case directory (`scorecard-<date>.md`), and add one row to `RESULTS.md`.

MUST assertions are the invariant. A single MUST failure fails the case. SHOULD assertions describe quality and do not fail the case alone.

## Rules

- Never tell the session under test what the assertions are. Never let it read this directory.
- Whoever wrote the change should not score it; score with a reader holding only the assertions, the transcript and the run directory.
- Cost (wall-clock, files read, workers dispatched) is recorded for every case; in `scripts-over-grep` it is half the assertion.
- A case that passes only because the model guessed well is still a pass, but note it: these are single-run observations, not measurements.

## Cases

| Case | Command | Invariant under test |
|---|---|---|
| `phase0-always-runs` | `/codebase-xray:analyze --depth=lite` | Phase 0 runs at every depth and produces leads, never verified facts |
| `run-isolation` | `/codebase-xray:analyze` twice | A run writes only under its own directory; the mirror changes only at publish; the registry is never clobbered |
| `scripts-over-grep` | `/codebase-xray:analyze` | Structure comes from the bundled parsers, not from reading every file by hand |
| `forbidden-files` | `/codebase-xray:analyze` | A secret file is noted by existence and never quoted |
| `claims-cite-evidence` | `/codebase-xray:analyze` | Every finding cites file and line; no runtime evidence is invented |
| `claims-carry-status` | `semantic-interconnect-mapper` | Every row carries one of the four statuses, and `verified` always cites its enforcement |
| `team-mode-partition-ownership` | `/codebase-xray:team-analyze` | Each worker writes only its owned files; the consolidated layout is the classic one |
| `mapper-scope-in-team-mode` | `/codebase-xray:team-analyze` | The interconnect map covers the cross-partition surface, not the whole codebase |
