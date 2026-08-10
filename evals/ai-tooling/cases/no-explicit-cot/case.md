# Case: no-explicit-cot

Guards the P0 defect fixed in ai-tooling 4.2.0. The command used to instruct its own agent to reason inside `<analysis>` tags, contradicting the agent's own anti-pattern rule against explicit chain-of-thought scaffolds on reasoning models. The invariant is structural: the command must not impose a private-reasoning format, and must not ask for that reasoning to appear in the output.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "Classify each incoming support ticket as bug, billing, or feature request. Explain your choice." --model claude
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The delivered variants do not add an explicit reasoning scaffold (`think step by step`, `<thinking>` tags, `<analysis>` tags, "first reason about X then answer") on the grounds of the target being Claude with extended thinking |
| 2 | MUST | The session's own output contains no `<analysis>` block or equivalent dump of its working; the response is the scorecard, variants, comparison, behavioral changes, and honesty note |
| 3 | SHOULD | If a reasoning scaffold IS added, the output states the model class it was chosen for and why the reasoning-model default was overridden |
| 4 | SHOULD | The "Explain your choice" clause in the source prompt is recognized as an output requirement, not as a reasoning scaffold to strip |

## Scoring notes

Assertion 1 is about the scaffold being added **as an optimization**. A variant that keeps the user's own explanatory requirement is correct: the invariant forbids the optimizer imposing a reasoning format, not preserving what the caller asked for. Confusing the two is the most likely mis-score.
