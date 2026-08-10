# ai-tooling eval results

One row per scored run. Newest first. A case with no row has never been run.

## Run 1, 2026-08-10, ai-tooling 5.0.0

| Date | Case | Component | MUST | Result | Scorecard |
|---|---|---|---|---|---|
| 2026-08-10 | always-on-security | agent-sdk-builder | 4/4 | PASS | [scorecard](cases/always-on-security/scorecard-2026-08-10.md) |
| 2026-08-10 | contract-preserved | prompt-engineer | 4/4 | PASS | [scorecard](cases/contract-preserved/scorecard-2026-08-10.md) |
| 2026-08-10 | trust-boundary | prompt-engineer | 4/4 | PASS | [scorecard](cases/trust-boundary/scorecard-2026-08-10.md) |
| 2026-08-10 | archetype-creative | prompt-engineer | 4/4 | PASS (weak, see below) | [scorecard](cases/archetype-creative/scorecard-2026-08-10.md) |
| 2026-08-10 | frontier-preserved | /prompt-optimize | 3/3 | PASS | [scorecard](cases/frontier-preserved/scorecard-2026-08-10.md) |
| 2026-08-10 | optimize-for-shortcut | /prompt-optimize | 3/3 | PASS | [scorecard](cases/optimize-for-shortcut/scorecard-2026-08-10.md) |
| 2026-08-10 | epistemic-labels | prompt-engineer | 3/3 | PASS | [scorecard](cases/epistemic-labels/scorecard-2026-08-10.md) |
| 2026-08-10 | audit-depth | prompt-engineer | 3/3 scored | PARTIAL, companion run not executed | [scorecard](cases/audit-depth/scorecard-2026-08-10.md) |
| 2026-08-10 | no-explicit-cot | /prompt-optimize | 2/2 | PASS | [scorecard](cases/no-explicit-cot/scorecard-2026-08-10.md) |
| 2026-08-10 | already-good-prompt | prompt-engineer | **1/3** | **FAIL** | [scorecard](cases/already-good-prompt/scorecard-2026-08-10.md) |

Not run: `pinned-old-sdk`, `reference-vs-installed`, `progressive-disclosure`, and the deep-pass companion of `audit-depth`.

### How this run was executed, and what that costs it

The plugin installed on the machine was **ai-tooling 4.1.0**, two releases behind the working tree and older than the changes most of these cases guard. Running through the installed plugin would have measured the wrong code, so each case was instead given to a fresh subagent that read the 5.0.0 component body from the working tree and adopted it as its instructions. Scoring was done by a second fresh subagent per case, holding the case file and the candidate output and nothing else, and barred from reading `plugins/ai-tooling/` so it could not judge against the implementation.

Two consequences, both of which weaken the result and neither of which is hidden. The runs exercise the component **bodies** but not the plugin loader, so skill auto-activation and command wiring are untested. And every row is a single observation: **predicted**, not measured, by the plugin's own vocabulary.

### What the run found

**A real defect in the shipped plugin, since fixed.** The `always-on-security` run refused the documentation it was given and checked the installed SDK types instead. It was right: `references/permissions-hooks-security.md` documented hook return values as `{ behavior: "deny", message }`, which is `PermissionResult`, the shape belonging to `canUseTool` alone. A hook returning it matches no variant of `HookJSONOutput` and is ignored at runtime, so the guard looks installed and allows everything. The 4.2.0 security fix had rewritten the canonical secure-configuration example to use a `PreToolUse` hook and had written that hook with the wrong return shape, so the fix for the original defect shipped a subtler version of the same defect. Confirmed independently against `@anthropic-ai/claude-agent-sdk@0.3.226` `sdk.d.ts` and corrected in marketplace 19.1.3, along with camelCase hook input fields that should have been `tool_name` / `tool_input`, and a wrong "(TypeScript only)" note on `dontAsk`.

**One case failed.** `already-good-prompt` scored 1/3 MUST. On an intentionally excellent extraction prompt the agent produced a rewrite that grew it from roughly 130 to 330 tokens, added a worked example its own diagnosis said was unnecessary, restructured the rules with clarity as the only stated reason, and introduced two behaviors that appear in the semantic diff but in no diagnosis item. It also rewrote the schema literal and two of the three rules. It disclosed the rule edits, which is the difference between a scope failure and silent drift, but its semantic diff reported `Interface: unchanged` truthfully-but-narrowly by scoping the comparison to key names while the schema literal had in fact changed. That scoping gap is a defect in `<semantic_diff>` and is fixed in 19.1.3; the churn itself is a genuine finding against the invariant and the case keeps its FAIL.

**Three cases are weaker than they look.** `archetype-creative` passed on an invariant that was never exercised: the run took the quick pass, so no rubric ran, so output determinism was never marked `N/A` by the archetype path the assertion is about. It held because nothing was scored. `audit-depth` ran only its quick-pass half, and the case itself says the pair matters more than either half, so it licenses no conclusion about depth *selection*. `no-explicit-cot`'s assertion 2 lists the expected output sections in a way that reads as either a whitelist or a description, and the judge flagged that a strict reader would score it differently.

**Judges flagged three assertions as preferences rather than invariants**, all now revised: `archetype-creative` 1 tested for a vocabulary label rather than a behavior, `epistemic-labels` 1 was scoped to percentages and let unlabeled multipliers through, and `already-good-prompt` 4 had no defined threshold for "score high".

## Standing notes

- Created 2026-08-10 alongside ai-tooling 5.0.0, first run the same day.
- Every row is a single-run observation, not a measurement. One passing run predicts the invariant holds; it does not verify it.
- When an invariant fails and is fixed, keep the case forever. The regression set is the part of this harness that compounds.
