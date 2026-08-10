# Case: archetype-creative

The universal rubric used to reward the wrong shape: scoring a creative prompt on output determinism pushes it toward a template, which makes the prompt worse while making the number go up. After 5.0.0 the rubric is archetype-aware and irrelevant dimensions are marked N/A.

## Setup

None. Run in any scratch directory.

## Run

Ask `prompt-engineer` to review and improve this prompt. The framing matters: it must trip the
deep pass, or the rubric never runs and assertion 2 cannot be exercised at all.

```
This is the production prompt behind the "opening scene" feature in our writing app. It ships
to users. Review and improve it, and give me the rubric.

    Write a short opening scene for a literary novel set in a coastal town in decline.
    Establish mood and a sense of place. Avoid cliche. Do not explain the scene afterwards.
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The prompt is treated as a creative or generative archetype before scoring. The test is behavioral, not lexical: a run that never writes the word "creative" but visibly protects latitude and declines determinism passes; a run that says "creative archetype" and then optimizes for a fixed shape fails |
| 2 | MUST | A rubric is actually produced, and output determinism in it is marked N/A or explicitly excluded, not scored low and then optimized upward. If no rubric ran at all this assertion is `fail`, not `pass`: the archetype-N/A path is what is under test and an unexercised path is not a passing one |
| 3 | MUST | No variant adds a fixed output template, section headers, a length schema, or a required structure the source prompt did not ask for |
| 4 | MUST | Creative latitude is treated as a property to protect; a change that narrows it is reported as a behavior change |
| 5 | SHOULD | "Avoid cliche" is recognized as underspecified and improvable without becoming prescriptive about content |

## Scoring notes

Watch for the subtle version of the failure: not a literal template, but "structure the scene as setting, then character, then hook", which is a template wearing prose. That fails assertion 3. Tightening the negative constraint "do not explain the scene afterwards" is legitimate and is not a latitude reduction, because it is already in the contract.

Assertion 3 says "output template". Read that as constraining the shape of the generated scene. Prompt-side scaffolding that constrains content or register (a length bound, a list of images to avoid) is not an output template, even when it is written as labeled lines.

The 2026-08-10 run passed 4/4 while never running a rubric, because the original framing was a bare review request and the agent correctly took the quick pass. The invariant held because nothing was scored, which is not the same as holding. That is why the Run text now names a production surface and asks for the rubric.
