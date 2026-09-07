# Scorecard: reasoning-trace-exemplars

- **Date:** 2026-09-07
- **Component run:** `/prompt-optimize`
- **Model / session:** `claude-opus-5[1m]`, a workflow subagent in a fresh context, one per case. Scored by a second fresh subagent per case, holding the case file and the run output and barred from reading `plugins/`, `docs/` and `.peer-review/`.
- **Plugin version under test:** 5.4.0
- **Run stage:** working tree (bodies, not the loader)
- **Setup materialized:** None. Run in an empty scratch directory outside the repository.

The run agent read the component bodies from the working tree at `plugins/ai-tooling/` and adopted them as its instructions, because the installed cache is at 5.2.0, two releases behind. It was barred from `evals/`, `.peer-review/` and `docs/`. This exercises the bodies and not the loader: skill auto-activation, command wiring and the real agent dispatch are untested here, and protocol step 0 requires this case to be re-run against the installed package once the cache reaches 5.4.0.

## Assertions

| # | Type | Outcome (pass / fail / n/a) | Evidence |
|---|------|-----------------------------|----------|
| 1 | MUST | pass | Scorecard row: "\| Model fit \| 1 \| The central defect. Two worked reasoning traces are pasted as few-shot exemplars and sent to a reasoning model, and \"Show your reasoning\" is an explicit CoT scaffold on top. This prompt is written for the 2022 non-reasoning class." Mechanism named in anti-pattern 1: "**Reasoning Traces as Exemplars.** Few-shot CoT often does worse than direct answering on RL-trained reasoners, and adding exemplars degrades further through copied steps and failed strategy transfer; distilling demonstrations into explicit insights recovered +14.0% on AIME'25 for GPT-4.1 (arXiv 2509.23196)." Target class stated up front: "**Model class:** frontier reasoning model." Token cost is raised separately and is explicitly subordinated to fit: "Only ~106 est. tokens, but roughly 65% of them are the two exemplars, which are the part that is actively counterproductive on this class. Dense-looking, wrong content." So the defect is model-fit, not bloat. |
| 2 | MUST | pass | All three variants ship without the worked examples (A's prompt block contains only `<answer_line_examples>` holding "Answer: $8 / Answer: 80 km/h / Answer: cannot determine (no distance is given)"; B and C contain no example block at all). Reported, not silent, under Behavioral changes: "**Behaviors removed:** the two worked examples. This is the point of the change on this model class, but it removes two things the examples were silently carrying: the demonstration that the answer includes its unit or currency, and the demonstration that the working is one line. Both are restated as instructions, so the mechanism moved from imitation to instruction." And on the reasoning line: "**Reasoning changed:** the explicit scaffold is gone. Visible working is now a presentation requirement rather than a reasoning aid, and depth moves to the `effort` parameter." |
| 3 | MUST | pass | A: "- Working: one short step per line, each line a single calculation, conversion, or statement of a quantity." plus "- Final line, with nothing after it: Answer: <value>". B: "Show the working as short steps, one per line, then a final line with nothing after it: Answer: <value with its unit or currency>." C: "Working: at most 3 lines, at most 10 words each." plus "Last line, nothing after it: Answer: <value with unit>." The trap is refused explicitly: "if it discards everything but the last line, C is, and the working could be dropped entirely, which no variant here does because \"Show your reasoning\" is in the original contract." |
| 4 | MUST | pass | No variant prompt contains a private-reasoning scaffold; A's tags are `<instructions>`, `<answer_line_examples>` and `<problem>`, and B and C are prose plus `<problem>`. Depth is routed to the native parameter instead of prompt text: "The lever for depth is `output_config: {\"effort\": ...}`, not prompt text." and anti-pattern 2 states the scaffold is not re-added for reasoning: "\"Show your reasoning\" as a scaffold is unnecessary on this class. It survives in the rewrites only as a *presentation* requirement, because the caller's output contract wants visible working, not because it improves the reasoning." Nearest miss is a note beside A, not a variant: "A self-check line (\"verify the arithmetic before the final line\") is worth testing on mid-tier models and should be **removed on Opus 5**", which is a verification instruction offered for a lower class and withdrawn on the stated frontier target. |
| 5 | SHOULD | pass | The token is unchanged in all three: A "<problem>\n{{PROBLEM}}\n</problem>", B "<problem>\n{{PROBLEM}}\n</problem>", C "<problem>\n{{PROBLEM}}\n</problem>". The surrounding contract change is flagged rather than hidden: "`{{PROBLEM}}` keeps its name but now must be interpolated **inside** `<problem>` tags, so the caller's template changes." |
| 6 | SHOULD | fail | No small or open-weight model appears anywhere in the output. The only class contrast drawn is historical: "This prompt is written for the 2022 non-reasoning class." and the only per-model qualification concerns a different technique: "A self-check line (\"verify the arithmetic before the final line\") is worth testing on mid-tier models and should be **removed on Opus 5**". The exemplars themselves are called unconditionally defective, with no row where they would be a legitimate per-model choice: "roughly 65% of them are the two exemplars, which are the part that is actively counterproductive on this class" and "\| Model fit \| 1 \| The central defect." The model-class gate is invoked ("every current Claude ... sits in that row of the model-class gate") but its other rows are never described, so the distinction the assertion asks for is gestured at and not made. |

## Cost

- Wall-clock: not instrumented per case. The five runs and five scorings together took about 14.6 minutes of wall clock across ten agents with a concurrency cap.
- References loaded: The command and the role, plus `reasoning-patterns.md` (the reasoning-model section, which the command's reasoning-pattern check names). Not independently instrumented.
- Tokens / agents, if visible: 1,031,667 output tokens across all ten agents of the run, not attributed per case. Run output for this case: 19,315 bytes.

## Observations

All four MUST assertions pass and the case passes. The single SHOULD failure (6) is recorded and does not fail the case.

Adversarial checks I ran, so the passes are not passes for the wrong reason:

1. Assertion 3 was genuinely exercised rather than trivially satisfied. Variant C is the one that could have quietly dropped the visible-working requirement in the name of efficiency, and it is where the pressure actually lands: it caps the working at "at most 3 lines, at most 10 words each" and the output concedes the cost in its own comparison ("Working too terse to audit on hard problems"). Constraining is not deleting, and the output names the temptation and refuses it by reference to the caller's contract. That is the trap resolved correctly, not avoided.

2. Assertion 2 was checked against the possibility that the exemplars were removed and then reintroduced under another name. Variant A does add a specimen block, and the output pre-empts the objection: "The specimens are the **final line only**, deliberately not input-to-output pairs. Input-to-output pairs would be legal under the \"input and output only\" rule, but here they would demonstrate a response with no working in it, which contradicts the working requirement." The specimens carry no reasoning trace and no problem text, so the diagnosed defect does not return through the back door.

3. Assertion 4 was checked against the substitution failure mode, not just the literal phrase "think step by step". No variant contains thinking tags, a private scratchpad, or a step-by-step directive; the depth lever is moved to a native API parameter and the CoT phrase survives only as an output-format requirement, which is what assertion 3 requires it to be. The two assertions therefore hold together rather than in tension, which is the discrimination this case exists to test.

4. Assertion 1 was checked for the "right vocabulary, wrong content" failure: an answer that calls the exemplars a defect while only costing them in tokens. The output separates the two, scoring model fit 1 with the mechanism and citation, and explicitly labelling the token share as secondary and mis-spent rather than as the finding.

One judgment call worth recording: the output is heavy with unverified predictive claims (its own honesty note says "Every quality claim above is **predicted**"), including scores, token deltas and effect sizes. None of the six assertions asks for measurement, so this does not bear on scoring, and the output flags its own unverified status rather than asserting measured results.

## Assertion quality

Assertion 5 is ambiguous enough that two careful readers would score it differently. "Survives byte-identical" is satisfied by the placeholder token, which is unchanged in all three variants, but every variant now requires it to be interpolated inside `<problem>` tags, which the output itself calls a caller-side template change and a possible breaking change. A reader who takes the assertion to be about the interpolation contract rather than the literal string would score it fail. If the intent is the token, say "the literal string `{{PROBLEM}}` is unchanged"; if the intent is the contract, say so and the assertion becomes a different, stricter test that this output would fail.

Assertion 6 is narrower than the invariant it seems to want. It names one specific contrast (frontier versus small open model) as the way to demonstrate that the exemplar defect is model-conditional. The output does mark model-conditionality in two other places: it identifies the prompt as written for "the 2022 non-reasoning class", and it makes a separate technique conditional on tier ("worth testing on mid-tier models and should be removed on Opus 5"). I scored fail because neither says the exemplars themselves could be a legitimate choice on another class, which is what the assertion asks. But a reader who treats the assertion as "shows the defect is class-conditional at all" would pass it on the 2022 line. Rewriting it as "the response states that these exemplars are a defect only for the reasoning class, and names at least one class where they would be acceptable" would remove the disagreement and keep the invariant.

Assertions 1 through 4 are clean invariants: each names an observable property of the output, each has a defined failure mode, and 3 and 4 together are what stop a cheap pass on 2. No preference-shaped assertions among the MUSTs.

## Verdict

- MUST assertions: 4 passed / 4 total
- Case result: PASS (all MUST passed)
