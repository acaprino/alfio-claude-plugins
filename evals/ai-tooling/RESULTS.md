# ai-tooling eval results

One row per scored run. Newest first. A case with no row has never been run: an empty table means the harness exists and has not yet been exercised, which is a different and more honest statement than a table of assumed passes.

| Date | Case | Version | Component | MUST passed | Result | Scorecard |
|---|---|---|---|---|---|---|
| | | | | | | |

## Standing notes

- Created 2026-08-10 alongside ai-tooling 5.0.0. Zero runs scored so far.
- Every row is a single-run observation, not a measurement. The same predicted/measured/verified rule the plugin teaches applies here: one passing run predicts the invariant holds, it does not verify it.
- When an invariant fails and is fixed, keep the case forever. The regression set is the part of this harness that compounds.
