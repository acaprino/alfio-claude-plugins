# ai-tooling eval harness

Measures whether `ai-tooling` still behaves the way it is designed to behave. Unlike the `senior-review` harness next door, these cases have no bug ground truth to recall: the plugin's value is a set of **behavioral invariants**, and the failure mode is drift, where a later edit quietly removes one and nothing notices.

Each case states an input, the command or agent to run, and assertions that either hold or do not. Assertions target the philosophy, never the wording: "does not require explicit private reasoning" is an invariant, "says the phrase private reasoning" is not. A rewrite of the agent that keeps the philosophy must still pass.

This directory is a development asset of the marketplace repository. It is not part of the `ai-tooling` plugin, is not registered in `marketplace.json`, and is never shipped.

## Protocol

For each case in `cases/`:

0. **Establish which version is under test, and prove it.** This step exists because the first attempt to run this harness nearly measured the wrong code: the plugin installed on the machine was two releases behind the working tree, so the components that would have answered were the ones from before the changes these cases guard. Check `~/.claude/plugins/cache/<marketplace>/ai-tooling/` against the version in `marketplace.json`. The two ways of running a case are stages, not alternatives, because they produce different evidence. The **working-tree run** may go first: each case reads the component body from the working tree and adopts it as its instructions, and its scorecard names the version it read and states plainly that it exercised the bodies and not the loader, leaving skill auto-activation and command wiring untested. Once the installed cache reaches the version under test, re-running the same cases against the **installed package** is required rather than optional. Run them in a fresh session (plugins load at session start and cannot be reloaded mid-session), score them with a reader that did not write the change, and name the version. `RESULTS.md` carries a row for each, so a reader can see which kind of evidence a row is. A run whose scorecard does not name the version it exercised is not a result.
1. **Materialize the setup** the case describes. Some cases need a scratch project with a specific `package.json` or `pyproject.toml`; the case gives the exact contents. Never run these in the marketplace repository itself, or the plugin's own files become part of the context under test.
2. **Run the case's command in a FRESH session.** Context from a previous case leaks the answers, especially for the source-of-truth cases where a leaked API shape defeats the whole point.
3. **Score each assertion** `pass`, `fail`, or `n/a`. An assertion is `n/a` only when the case explicitly makes it conditional.
4. **Record the run** in a copy of `scorecard-template.md` inside the case directory (`scorecard-<date>.md`), and add one row to `RESULTS.md`.

MUST assertions are the invariant. A single MUST failure fails the case, regardless of how good the rest of the output was. SHOULD assertions describe quality: record them, but they do not fail the case on their own.

## Metrics

- **Invariant pass rate** = MUST assertions passed / total MUST assertions, across all cases.
- **Regression set**: which invariants have ever failed. An invariant that fails once is worth a permanent case, even after it is fixed.
- **Cost per case**: wall-clock and, where visible, token spend. The audit-depth cases are the ones where cost IS the assertion.
- **Coverage per case**: a body-only observation and an installed-package observation are different evidence, so a case is fully covered only when both exist.

## Rules

- Never tell the session under test what the assertions are. The case file is for the scorer.
- Never let the session read this directory. If it does, the run is void.
- An assertion that turns out to encode a preference rather than an invariant gets deleted, with a note in the case file saying why. Cases are not sacred; invariants are.
- **Whoever wrote the change should not be the one scoring it.** Someone holding the plugin's text and these assertions in mind cannot judge an output neutrally: they know what a passing answer looks like and will pattern-match to it. Score with a reader that has the assertions and the output and nothing else, which is the same judge-independence rule `<prompt_evals>` in the agent asks for. When that is impossible, say so in the scorecard and treat the result as weaker evidence.
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
| `reasoning-trace-exemplars` | `/prompt-optimize` | Worked reasoning traces in few-shot examples are a model-fit defect on a reasoning target, and their removal is reported |
| `small-model-structured-output` | `/prompt-optimize` | On a small open-weight target every variant names its enforcement rung, and a format instruction alone is never the enforcement |
| `constraint-saturation` | `/prompt-optimize` | Above five simultaneously verifiable constraints the optimizer proposes a split or a verifier; in an agent rule file it exempts the guardrail rules and counts the output obligations that file carries |
| `judge-prompt-shape` | `/prompt-optimize` | A judge prompt is decomposed per criterion, its persona and 1-10 scale are reported as defects, and agreement stays predicted until kappa is measured |
| `prompt-language-preserved` | `/prompt-optimize` | A non-English prompt is never translated to English as an optimization, absent a measurement on the target model and task |
| `pinned-old-sdk` | `agent-sdk-builder` | The installed version is inspected and honored |
| `reference-vs-installed` | `agent-sdk-builder` | When the bundled reference and the installed SDK disagree, the SDK wins |
| `always-on-security` | `agent-sdk-builder` | An every-call rule uses a `PreToolUse` hook, never `canUseTool` alone |
| `progressive-disclosure` | `agent-sdk-builder` | Only the reference the task needs is loaded |
