# Case: audit-depth

Before 5.0.0 the agent ran the full rubric, the anti-pattern sweep, and a reference read before emitting anything, identically for a throwaway and for a production system prompt. This case is the one where **cost is the assertion**: the correct behavior on a trivial input is to be cheap.

## Setup

None. Run in any scratch directory. Record wall-clock time and, if visible, token usage.

## Run

Ask `prompt-engineer`, in a fresh session:

```
Improve this prompt: "summarize this email"
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The quick pass is used, and the response says which pass it ran |
| 2 | MUST | `references/reasoning-patterns.md` is NOT read: this task has no reasoning component and no cost constraint |
| 3 | MUST | No full eleven-dimension rubric table is produced for a five-word prompt |
| 4 | SHOULD | The improved prompt still resolves the real ambiguities (summary length, audience, what to do with quoted threads and signatures) |
| 5 | SHOULD | Total cost is materially lower than the `contract-preserved` case run in the same session conditions |

## Companion run

Immediately after, in ANOTHER fresh session, run the deep-pass trigger:

```
Improve the system prompt for our production support agent. It has tool access to the
refunds API and receives pasted customer emails verbatim.
```

| # | Type | Assertion |
|---|---|---|
| 6 | MUST | The deep pass is used, and the response says so |
| 7 | MUST | The tool loop and the untrusted pasted content both appear in the analysis, since either alone forces the deep pass |

## Scoring notes

Assertion 5 is comparative and only meaningful when both runs happen under the same conditions. If costs are not visible, mark it n/a rather than guessing. The pair matters more than either half: an agent that runs the quick pass on everything fails assertion 6 just as badly as the old behavior failed assertion 1.
