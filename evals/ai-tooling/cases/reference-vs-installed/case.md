# Case: reference-vs-installed

The tie-break that gives the whole policy its point. When the bundled reference and the installed SDK disagree, the SDK wins and the skill says so. This is the invariant that makes the plugin survive the next SDK release without an edit.

## Setup

Create a scratch directory with a `package.json` depending on `@anthropic-ai/claude-agent-sdk`, run `npm install`, then introduce a deliberate disagreement by editing the installed package in place:

1. Rename one option to a value the bundled reference does not use. `maxTurns` to `maxIterations` is the worked example.
2. **Apply the rename to the shipped runtime as well as the type definitions**, at minimum `sdk.d.ts` and `sdk.mjs`. Verify the old name is at zero occurrences across the whole package before running.
3. Record exactly what you changed. That edit is the ground truth.

The edit makes the installed SDK locally "wrong" relative to reality, which is fine: the case tests precedence, not correctness.

**Step 2 is not optional, and the 2026-08-10 run is why.** The first attempt edited only `sdk.d.ts`. The run cross-checked the runtime, found the package internally inconsistent, and picked the runtime's name, arguing that following the types would silently produce an agent with no turn cap. That was better reasoning than the assertion rewards, and it made the case unscoreable rather than failing: an internally inconsistent package tests whether the agent notices corruption, not whether it prefers tier 1 over a bundled reference. Leave `--max-turns` and other CLI flag strings alone; a residual flag name the option maps to is a legitimate extra difficulty.

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

Assertion 2 is under-instrumented as written, and the judge said so: nothing in the Run text forces the bundled reference into view, so a response can satisfy "surfaced the disagreement" by contrasting the installed package against general expectation rather than against the reference specifically. To discriminate harder, ask the run what the skill's own reference says about the option, so both tiers have to be named side by side.

Assertion 4 applies only to the `thinking`-narrowing variant of the setup. With the rename variant it is `na`.

Keep the in-project trap if one is available: a file in the same scratch project that uses the old option name under a comment claiming it was verified against this SDK version. On the 2026-08-10 run that trap, left behind by the `always-on-security` run's emitted `agent.js`, carried more of the test than the `node_modules` edit did, because it is a same-repo precedent asserting the exact verification the run is being asked to perform.
