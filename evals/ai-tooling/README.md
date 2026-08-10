# ai-tooling eval harness

Measures whether `ai-tooling` still behaves the way it is designed to behave. Unlike the `senior-review` harness next door, these cases have no bug ground truth to recall: the plugin's value is a set of **behavioral invariants**, and the failure mode is drift, where a later edit quietly removes one and nothing notices.

Each case states an input, the command or agent to run, and assertions that either hold or do not. Assertions target the philosophy, never the wording: "does not require explicit private reasoning" is an invariant, "says the phrase private reasoning" is not. A rewrite of the agent that keeps the philosophy must still pass.

This directory is a development asset of the marketplace repository. It is not part of the `ai-tooling` plugin, is not registered in `marketplace.json`, and is never shipped.

## Protocol

For each case in `cases/`:

1. **Materialize the setup** the case describes. Some cases need a scratch project with a specific `package.json` or `pyproject.toml`; the case gives the exact contents. Never run these in the marketplace repository itself, or the plugin's own files become part of the context under test.
2. **Run the case's command in a FRESH session.** Context from a previous case leaks the answers, especially for the source-of-truth cases where a leaked API shape defeats the whole point.
3. **Score each assertion** `pass`, `fail`, or `n/a`. An assertion is `n/a` only when the case explicitly makes it conditional.
4. **Record the run** in a copy of `scorecard-template.md` inside the case directory (`scorecard-<date>.md`), and add one row to `RESULTS.md`.

MUST assertions are the invariant. A single MUST failure fails the case, regardless of how good the rest of the output was. SHOULD assertions describe quality: record them, but they do not fail the case on their own.

## Metrics

- **Invariant pass rate** = MUST assertions passed / total MUST assertions, across all cases.
- **Regression set**: which invariants have ever failed. An invariant that fails once is worth a permanent case, even after it is fixed.
- **Cost per case**: wall-clock and, where visible, token spend. The audit-depth cases are the ones where cost IS the assertion.

## Rules

- Never tell the session under test what the assertions are. The case file is for the scorer.
- Never let the session read this directory. If it does, the run is void.
- An assertion that turns out to encode a preference rather than an invariant gets deleted, with a note in the case file saying why. Cases are not sacred; invariants are.
- A case that passes only because the model guessed well is still a pass, but note it: these are single-run observations, not measurements, and the same epistemic rule the plugin teaches applies to its own harness.

## Cases

| Case | Component | Invariant under test |
|---|---|---|
| `no-explicit-cot` | `/prompt-optimize` | No explicit private-reasoning scaffold is imposed or requested |
| `frontier-preserved` | `/prompt-optimize` | With no declared target, the frontier is shown and the pole is the user's pick |
| `optimize-for-shortcut` | `/prompt-optimize` | A declared target skips the question and delivers that pole |
| `already-good-prompt` | `prompt-engineer` | An excellent prompt can be left alone |
| `contract-preserved` | `prompt-engineer` | Hard constraints and the output interface survive the rewrite, and changes are reported |
| `archetype-creative` | `prompt-engineer` | Determinism dimensions are N/A for a creative prompt, not optimized |
| `audit-depth` | `prompt-engineer` | A trivial prompt gets the quick pass, not the full ladder |
| `epistemic-labels` | `prompt-engineer` | No unmeasured claim is stated as a measurement |
| `trust-boundary` | `prompt-engineer` | Untrusted interpolated content is treated as a boundary, not as a string to filter |
| `pinned-old-sdk` | `agent-sdk-builder` | The installed version is inspected and honored |
| `reference-vs-installed` | `agent-sdk-builder` | When the bundled reference and the installed SDK disagree, the SDK wins |
| `always-on-security` | `agent-sdk-builder` | An every-call rule uses a `PreToolUse` hook, never `canUseTool` alone |
| `progressive-disclosure` | `agent-sdk-builder` | Only the reference the task needs is loaded |
