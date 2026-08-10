# Case: reference-vs-installed

The tie-break that gives the whole policy its point. When the bundled reference and the installed SDK disagree, the SDK wins and the skill says so. This is the invariant that makes the plugin survive the next SDK release without an edit.

## Setup

Create a scratch directory with a `package.json` depending on `@anthropic-ai/claude-agent-sdk`, run `npm install`, then introduce a deliberate disagreement by editing the installed type definitions in place:

1. Find the exported options type in `node_modules/@anthropic-ai/claude-agent-sdk/` (the `.d.ts` that declares the `query()` options).
2. Rename one option to a value the bundled reference does not use. For example change `maxTurns` to `maxIterations`, or narrow `thinking` to accept only `{ type: "disabled" }`.
3. Record exactly what you changed. That edit is the ground truth.

The edit makes the installed SDK locally "wrong" relative to reality, which is fine: the case tests precedence, not correctness.

## Run

```
Write a query() call for this project that caps the agent at 10 turns and enables
extended thinking.
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The emitted code matches the INSTALLED type definitions, not the bundled reference |
| 2 | MUST | The disagreement is surfaced rather than silently resolved: the response says the installed SDK differs from what the reference documents |
| 3 | MUST | The response does not claim the installed SDK is wrong and emit the reference's shape anyway |
| 4 | SHOULD | If the narrowed `thinking` type makes the request impossible, that is stated as a version limitation rather than worked around with an invalid value |

## Scoring notes

Undo the `node_modules` edit after the run, or delete the scratch directory. Assertion 2 is the one that distinguishes a skill following the policy from a skill that happened to read the types: silent agreement with tier 1 is correct behavior but weak evidence, so note in the scorecard whether the session ever mentioned the conflict.
