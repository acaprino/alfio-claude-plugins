# senior-review eval harness

Measures whether the senior-review architecture actually produces a more senior reviewer, and which components pay for themselves. Each case is a diff with a **known ground truth**: bugs that were really there, established either by a production post-mortem, by the fix commit that later landed, or by deliberate injection. A run replays the review against the pre-fix state and scores what it found.

This directory is a development asset of the marketplace repository. It is not part of the `senior-review` plugin, is not registered in `marketplace.json`, and is never shipped.

## Protocol

For each case in `cases/`:

1. **Prepare the target.** Check out the case's `repo` at `review_rev` in a scratch worktree (`git worktree add <tmp> <review_rev>`). The bugs listed in the case are present at that revision.
2. **Run one command per scorecard row**, scoped as the case specifies:
   - `/senior-review:code-review` (scope per the case's `review_scope`)
   - `/senior-review:team-review <review_scope>`
   - Claude Code's built-in `/code-review` as the vanilla baseline
   Run each in a FRESH session so no context leaks between runs, and never in the same session that is scoring.
3. **Score against the ground truth.** For every bug in the case's table: `found` (a finding matches the defect, regardless of wording), `partial` (the right location or mechanism but the wrong conclusion), `missed`. Matching is by mechanism, not by phrasing.

   A case may also carry a `must_not_report` block. Each entry is a claim the review must NOT produce at that revision, because it is false at the system level even though a plausible local reading supports it. Scoring an entry: `avoided` (no finding matches the claim), `reported` (a finding matching the claim survived the pipeline's own verification), `caught` (a finding matching the claim was produced but killed by the verification panel, and the record names the lens that killed it). Only `reported` is a failure. `caught` is the outcome the panel exists to produce, and the case notes which lens did it.
4. **Count false positives.** Findings that survive the pipeline's own verification but do not correspond to a real defect at that revision. Pre-existing findings correctly tagged `[PRE-EXISTING]` are excluded from the FP count.
5. **Record cost**: wall-clock time and, where visible, token spend or agent count.
6. Fill a copy of `scorecard-template.md` into the case directory (`scorecard-<command>-<date>.md`) and add one row to `RESULTS.md`.

## Metrics

- **Recall** = found / total known bugs (partial counts 0.5).
- **FP rate** = false positives / total findings reported.
- **Dimension attribution**: which dimension found each true positive. This is the metric that says which auditors earn their keep.
- **Evidence discipline**: fraction of quantitative claims labeled `measured` vs `derived` vs unlabeled.
- **Anti-finding rate** = `reported` / total `must_not_report` entries. This measures precision against known-plausible falsehoods, which recall cannot see. A pipeline that finds every real bug and also reports a confident falsehood is not a better reviewer.

## Rules

- Never fix anything during a run. The review is observational; the worktree is discarded afterwards.
- Never tell the reviewer what the known bugs are. The case file is for the scorer, not for the reviewed session.
- A case whose ground truth turns out wrong (the "bug" was not real at that revision) gets corrected in the case file, with a note, before its runs count.

## Case sources

| Source | Cases |
|---|---|
| Jupiter updater post-mortem (2026-08-10, production ground truth) | `jupiter-updater` |
| Jupiter fix-commit history (bug = what the later fix commit repaired) | `jupiter-market-state-tristate`, `jupiter-economic-events-upsert`, `jupiter-cache-convergence`, `jupiter-trade-failure-drop`, `jupiter-position-notice-owner` |
| Synthetic, bug injected by construction (targets the newest dimensions) | `synthetic-payment-double-insert`, `synthetic-cache-stale-read`, `synthetic-connection-pool-leak`, `synthetic-retry-storm` |
| Jupiter false-positive incident (2026-08-10, precision ground truth) | `jupiter-credential-refill` |

Synthetic cases carry their buggy code inline in the case file; materialize it into a scratch repo before running (instructions per case).
