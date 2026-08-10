# Case: archetype-creative

The universal rubric used to reward the wrong shape: scoring a creative prompt on output determinism pushes it toward a template, which makes the prompt worse while making the number go up. After 5.0.0 the rubric is archetype-aware and irrelevant dimensions are marked N/A.

## Setup

None. Run in any scratch directory.

## Run

Ask `prompt-engineer` to review and improve this prompt:

```
Write a short opening scene for a literary novel set in a coastal town in decline.
Establish mood and a sense of place. Avoid cliche. Do not explain the scene afterwards.
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The prompt is classified as a creative or generative archetype before scoring |
| 2 | MUST | Output determinism is marked N/A or explicitly excluded, not scored low and then optimized upward |
| 3 | MUST | No variant adds a fixed output template, section headers, a length schema, or a required structure the source prompt did not ask for |
| 4 | MUST | Creative latitude is treated as a property to protect; a change that narrows it is reported as a behavior change |
| 5 | SHOULD | "Avoid cliche" is recognized as underspecified and improvable without becoming prescriptive about content |

## Scoring notes

Watch for the subtle version of the failure: not a literal template, but "structure the scene as setting, then character, then hook", which is a template wearing prose. That fails assertion 3. Tightening the negative constraint "do not explain the scene afterwards" is legitimate and is not a latitude reduction, because it is already in the contract.
