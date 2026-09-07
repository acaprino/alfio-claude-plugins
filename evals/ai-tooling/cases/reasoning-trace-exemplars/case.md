# Case: reasoning-trace-exemplars

Added in ai-tooling 5.2.0 from the September 2026 refresh. The evidence (arXiv 2509.23196) is
that few-shot examples carrying worked step-by-step reasoning make RL-trained reasoning models
worse, and that more of them make it worse still. The invariant is that the optimizer recognizes
such exemplars as a model-class defect on a reasoning target, and that removing or converting
them is reported as a behavior change rather than done silently, because a caller may rely on the
answer style the exemplars taught.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "Solve the word problem. Show your reasoning, then give the final answer on the last line.

Example 1
Problem: A shop sells pens at 3 for $2. How much do 12 pens cost?
Reasoning: 12 pens is 4 groups of 3. Each group costs $2. 4 x 2 = 8.
Answer: $8

Example 2
Problem: A train travels 60 km in 45 minutes. What is its speed in km/h?
Reasoning: 45 minutes is 0.75 hours. 60 / 0.75 = 80.
Answer: 80 km/h

Problem: {{PROBLEM}}" --model claude
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The worked-reasoning exemplars are identified as a model-fit defect for the stated target class (a reasoning model), with the mechanism named (copied steps, degraded accuracy), not merely as token bloat |
| 2 | MUST | At least one offered variant removes the reasoning traces from the examples or converts them into an explicit instruction, and that change is reported as a behavior change on the reasoning or interface line, never applied silently |
| 3 | MUST | The caller's own output requirement ("show your reasoning, then the final answer on the last line") survives as an output requirement in every variant; the fix targets the exemplars, not the request for a visible rationale |
| 4 | MUST | No variant replaces the exemplars with an explicit private-reasoning scaffold ("think step by step inside tags") on the grounds of the target being a reasoning model |
| 5 | SHOULD | The literal string `{{PROBLEM}}` is unchanged in every variant. This is about the token, not the interpolation contract: a variant that wraps it in tags still passes, and a variant that changes what the caller must interpolate reports that as an interface change under assertion 2's diff |
| 6 | SHOULD | The response states that these exemplars are a defect for the reasoning class specifically, and names at least one model class on which they would be an acceptable choice rather than a defect |

## Scoring notes

The trap is assertion 3 against assertion 2. "Show your reasoning" is an output contract the
caller asked for; the traces inside the examples are a demonstration of how to reason. Removing
the traces while keeping the visible-rationale requirement passes; deleting the requirement to
save tokens fails assertion 3 even if the diff reports it.

Assertion 4 mirrors `no-explicit-cot`: the correct fix on a reasoning model is fewer exemplars
or an instruction, not a different scaffold.

## Revisions

**2026-09-07, after the first run.** Two SHOULD assertions were revised on the scorer's report,
per the harness rule that an ambiguous assertion is fixed rather than kept.

Assertion 5 said "survives byte-identical" without naming the unit. The run left the token
unchanged in all three variants and required it to be interpolated inside tags, which the run
itself called a caller-side template change. A reader taking the assertion to be about the token
passes it; a reader taking it to be about the interpolation contract fails it. It now names the
token, and points the contract question at assertion 2, where a reported interface change belongs.

Assertion 6 named one specific contrast, frontier against small open model, as the only way to
show the defect is class-conditional. The run marked class-conditionality twice by other routes
and never said the exemplars themselves could be legitimate anywhere, which is what the assertion
actually wants. It now asks for that directly. The run scored `fail` on the old wording and would
score `fail` on the new one, so the recorded outcome stands.
