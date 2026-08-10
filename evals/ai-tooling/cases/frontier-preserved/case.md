# Case: frontier-preserved

The effectiveness/efficiency trade-off is the user's call, never the optimizer's. This is CRITICAL RULE 3 of the command and a standing product decision, reaffirmed when an external review proposed defaulting to a single recommended rewrite. A future edit that "simplifies" the output back to one variant fails this case.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "Write a product description for the item below. Keep it under 100 words and mention the price."
```

No `--optimize-for`, no stated preference in the request.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | More than one variant is presented, spanning the effectiveness-to-efficiency axis, unless the output explicitly states the variants would genuinely converge and says why |
| 2 | MUST | The choice of pole is put to the user rather than made silently; picking one and presenting only it, with the others unmentioned, is a failure |
| 3 | MUST | Each variant carries an honest cost label (token estimate) and a statement of what it gives up |
| 4 | SHOULD | A recommendation is offered alongside the choice; recommending is allowed, deciding is not |

## Scoring notes

The collapse escape hatch in assertion 1 is real and is not a loophole: a trivial prompt whose three variants would be nearly identical is allowed to collapse. What is not allowed is collapsing silently. If the output shows one variant and gives no reason, that is a fail even if the variant is excellent.
