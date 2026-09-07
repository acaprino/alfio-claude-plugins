# ai-tooling eval results

One row per scored run. Newest first. A case with no row has never been run.

## Run 3, 2026-09-07, ai-tooling 5.4.0 (working tree)

The five cases that had never been executed: the two added in 5.2.0, the two added in 5.3.0 and 5.4.0 by the September research integration, and `constraint-saturation` as the peer review rewrote it. The installed cache was at 5.2.0, two releases behind the working tree, so this is the **working-tree** stage of protocol step 0 and every scorecard says so. The installed-package stage is now owed for all five.

Method: one fresh subagent per case, receiving only the case's Run text and the instruction to read the component bodies from the working tree and adopt them, barred from `evals/`, `.peer-review/` and `docs/`. A second fresh subagent per case scored it, holding the case file and the run output and barred from `plugins/`. Neither the runner nor the scorer wrote the change under test.

| Date | Case | Component | MUST | Result | Scorecard |
|---|---|---|---|---|---|
| 2026-09-07 | reasoning-trace-exemplars | /prompt-optimize | 4/4 | PASS | [scorecard](cases/reasoning-trace-exemplars/scorecard-2026-09-07.md) |
| 2026-09-07 | small-model-structured-output | /prompt-optimize | 5/5 | PASS | [scorecard](cases/small-model-structured-output/scorecard-2026-09-07.md) |
| 2026-09-07 | judge-prompt-shape | /prompt-optimize | 6/6 | PASS | [scorecard](cases/judge-prompt-shape/scorecard-2026-09-07.md) |
| 2026-09-07 | prompt-language-preserved | /prompt-optimize | 4/4 | PASS | [scorecard](cases/prompt-language-preserved/scorecard-2026-09-07.md) |
| 2026-09-07 | constraint-saturation | /prompt-optimize | 8/8 | PASS | [scorecard](cases/constraint-saturation/scorecard-2026-09-07.md) |

Twenty-seven MUST assertions, all passed. Two SHOULD failures, both recorded: `reasoning-trace-exemplars` 6, where the response never named a class on which the exemplars would be a legitimate choice, and `constraint-saturation` 7, where the working threshold was used correctly in all three invocations and its provenance never stated.

### The invariants were exercised, not sidestepped

Every case in this run has a trap in it, and the reason to trust the passes is that the scorers checked the trap rather than the vocabulary.

`prompt-language-preserved` is the sharpest. `--optimize-for tokens` gives a token-minimizing pass every reason to translate, and the run did compute the English saving, 69 tokens against 73, and then refused it and cut tokens inside Italian instead. That is the shape the case wants: the translation is raised as a caller's decision with the measured caveat attached, not silently skipped. The scorer recounted the delivered Italian text by hand to confirm the token estimate had not been quietly made on an English draft.

`constraint-saturation` was rewritten by the peer review to add a mixed rule file, and the mixed run is where the new boundary lives. The run typed the file as mixed before counting anything, split it, and counted the release-note obligations at twelve rather than the case's seven by decomposing compound rules, which is stricter than the case asks and satisfies it a fortiori. Its variant D is three real stage prompts with a repair loop, not a sentence saying a split would be possible.

`judge-prompt-shape` hit both of its traps. No variant kept the 1-10 scale, the scale change was reported as an interface break that invalidates score history, and "be very strict" was priced against the benchmark that measures it rather than deleted as noise.

### What the scorers flagged about the assertions themselves

Five assertions were reported as ambiguous or preference-shaped rather than invariant, by scorers that had no stake in them. All five were revised the same day, with the revision noted in the case file; the outcomes above were scored against the wording as it stood during the run. The pattern in four of the five is the same: a clause that a correct run may have no reason to satisfy, or a unit of comparison the assertion never names.


## Run 2, 2026-08-10, ai-tooling 5.0.1 (installed)

The four cases run 1 could not cover, executed against the **installed** plugin at `~/.claude/plugins/cache/claude-code-daodan/ai-tooling/5.0.1/` rather than the working tree, after the marketplace was updated. Same method otherwise: a fresh subagent per run receiving only the Run text, a separate fresh subagent per verdict.

| Date | Case | Component | MUST | Result | Scorecard |
|---|---|---|---|---|---|
| 2026-08-10 | pinned-old-sdk | agent-sdk-builder | 4/4 scored | PASS | [scorecard](cases/pinned-old-sdk/scorecard-2026-08-10.md) |
| 2026-08-10 | reference-vs-installed | agent-sdk-builder | 3/3 | PASS (on the second setup, see below) | [scorecard](cases/reference-vs-installed/scorecard-2026-08-10.md) |
| 2026-08-10 | progressive-disclosure | agent-sdk-builder | 3/3 | PASS | [scorecard](cases/progressive-disclosure/scorecard-2026-08-10.md) |
| 2026-08-10 | audit-depth (deep companion) | prompt-engineer | 2/2 scored | PASS | [scorecard](cases/audit-depth/scorecard-2026-08-10-deep.md) |

With this run every case has been executed at least once, and `audit-depth` has both halves: quick on a five-word prompt, deep on a production agent with a tool loop and untrusted input.

**Executed once is not covered.** Under the two-stage rule in protocol step 0, a case is fully covered only when a working-tree observation and an installed-package observation both exist. Run 1's ten rows are working-tree only and run 2's four are installed only, so as of these two runs no case holds both. Each run section names its stage in its heading, which is where a reader learns which kind of evidence a row is.

### The source-of-truth policy held under a rigged test

`pinned-old-sdk` is the strongest result of either run. The project pinned `0.2.90` with no `node_modules`, so tier 1 was unreadable and tier 2 documents a version a whole minor line ahead. The run said what it could not read, then downloaded the pinned version's own tarball and resolved every option against that version's `sdk.d.ts`, type-checking both emitted snippets under `strict` before handing them over. It also found that `0.2.90` exports a standalone `forkSession()` that current releases do not, which is the exact class of fact the policy exists to stop the skill recalling wrongly in either direction.

`reference-vs-installed` **failed its first setup for a reason that was the case's fault, not the plugin's.** The case says to introduce a disagreement by editing the installed type definitions. Editing only `sdk.d.ts` leaves the shipped runtime still reading the real name, and the run detected exactly that: it cross-checked `sdk.mjs`, found the package internally inconsistent, and chose the runtime's name on the grounds that following the types would produce an agent with no turn cap. That is better reasoning than the assertion was written to reward. The setup was rebuilt to rename the option consistently across types and runtime, and the re-run then emitted the installed name, named the tier that resolved it, and explained why the old name still sounds right. The case file now carries the corrected setup.

The judge's observation on that case is worth keeping: the sharpest part of the test turned out not to be the `node_modules` edit at all, but an in-project trap left behind by the `always-on-security` run, whose `agent.js` set the old option name under a comment claiming it had been verified against this very SDK version. The run resisted a same-repo precedent that asserted the exact verification it was being asked to perform, diagnosed it as a silent failure rather than a crash, and reported it unprompted.

## Run 1, 2026-08-10, ai-tooling 5.0.0 (working tree)

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
