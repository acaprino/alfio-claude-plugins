<!-- Scorecard produced by an independent judge that read only this case file, the candidate
output, and (where the case needs it) the installed SDK types. It could not read
plugins/ai-tooling/, so it judged the output against the assertions rather than against the
implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.1, the INSTALLED plugin at
  `~/.claude/plugins/cache/claude-code-daodan/ai-tooling/5.0.1/`
- **How the component was exercised:** a fresh subagent adopted the installed component body and
  received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: reference-vs-installed (v2)

Candidate: `scratchpad/evalrun/out/reference-vs-installed-v2.md`
Case: `evals/ai-tooling/cases/reference-vs-installed/case.md`

## Setup verification (done independently, not trusted)

| Fact | Method | Result |
|---|---|---|
| `maxTurns` absent from `sdk.d.ts` | `grep -c` | 0 occurrences |
| `maxTurns` absent from `sdk.mjs` | `grep -c` | 0 occurrences |
| `maxIterations` is the turn-cap option | `grep -n sdk.d.ts` | present at `sdk.d.ts:75` and `sdk.d.ts:1702` |
| Doc comment on the option | read `sdk.d.ts:1698-1702` | "Maximum number of conversation turns before the query stops." |
| Runtime consumes it by name | `grep` context in `sdk.mjs` | destructured as `maxIterations:ht` / `maxIterations:p` |
| Runtime flag mapping | `grep` context in `sdk.mjs` | `if(p)q.push("--max-turns",p.toString())` |
| Installed version | `node_modules/.../package.json` | `0.3.226` |
| In-project trap | read `edited-proj/agent.js` | line 63 is `maxTurns: 5`, under a header comment claiming "Verified against @anthropic-ai/claude-agent-sdk 0.3.226" |

The rebuild is consistent: both the types and the shipped runtime say `maxIterations`, so `maxIterations` is the correct emission and `maxTurns` would be the failure. The candidate's supporting citations (`sdk.d.ts:1693` for the `maxThinkingTokens` deprecation, `sdk.d.ts:1664-1675` for `thinking?: ThinkingConfig`, `sdk.d.ts:1707` for `maxBudgetUsd`, `error_max_turns` and `terminal_reason` in the result type) all check out against the installed files.

I did not read the plugin's bundled reference (hard constraint), so assertion 2 is scored on whether the conflict was surfaced at all, not on whether the reference's exact wording was quoted.

## Scorecard

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | **pass** | Emits `maxIterations: 10,` inside `options`, with the inline note "On 0.3.226 this option is `maxIterations`. `maxTurns` does not exist." The `thinking: { type: 'adaptive' }` shape also matches the installed `ThinkingConfig` union. Both halves of the prompt (cap at 10 turns, enable extended thinking) are satisfied against tier 1. |
| 2 | MUST | **pass** | Surfaced, not silent. Dedicated section header "The two things that would have broken this", then: "**1. The turn cap option is `maxIterations`, not `maxTurns`.** In the installed 0.3.226, `maxTurns` appears **zero times** in `sdk.d.ts` and **zero times** in the shipped runtime `sdk.mjs`." Precedence is stated as a source claim: "Nothing here came from the skill's bundled reference files or from documentation — every API-sensitive detail was settled at tier 1, against the exact version this project will run." It also names why the losing shape is tempting: "which is why the old name still sounds right but no longer is." |
| 3 | MUST | **pass** | Never asserts the installed package is wrong. The rename is treated as authoritative fact about this range: "`maxIterations` is a rename within that range, so if you ever want this pinned rather than floating, tighten the range to `~0.3.226`." The reference's shape is emitted nowhere; the only `maxTurns` in the output is quoted as a defect to fix. |
| 4 | SHOULD | **na** | Precondition absent. The setup used the rename variant, not the narrowed-`thinking` variant, so `thinking` was fully available and no version limitation had to be declared. The candidate enabled it normally. |

**MUST passed: 3 / 3**

## Verdict: PASS

## Observations

The case now tests precedence properly, and the rebuild closed the hole that sank the earlier attempt: I confirmed `maxTurns` is at zero occurrences in both the type surface and the shipped runtime, so there is no longer an internal inconsistency the candidate can exploit to pick the recalled name on defensible grounds. The residual asymmetry is a feature rather than a hole: the runtime still emits the CLI flag `--max-turns`, so a candidate that greps for the string "max-turns" and stops finds apparent confirmation of the wrong option name. This one correctly separated the option key from the flag it maps to and explained the mapping.

Two design notes remain. First, assertion 2 is under-instrumented. The bundled reference is never forced into view by the run prompt, so a response can satisfy "surfaced the disagreement" by contrasting the installed package against generic expectation rather than against the reference specifically, which is what happened here: the candidate contrasts `maxIterations` with "the old name" and with memory and documentation in general, and separately asserts that nothing came from the reference files, but never states that the reference documents `maxTurns`. That still clears the bar the scoring note sets ("whether the session ever mentioned the conflict"), and it is far from silent agreement, but the case would discriminate harder if the prompt asked what the skill's own reference says about the turn cap, forcing the two tiers to be named side by side. Second, assertion 4 is dead whenever the rename variant is chosen, since the case offers two alternative setups but one shared assertion list.

The sharper worry is where the difficulty actually lives. Installed 0.3.226 is a version whose whole option surface (`effort`, `taskBudget`, `maxBudgetUsd`, adaptive `thinking`) sits past what a model would confidently recall, so the recalled-knowledge pull toward `maxTurns` is weaker than the case design assumes: there is less prior to override. What carries most of the test here is the in-project trap, `agent.js:63` holding `maxTurns: 5` beneath a comment asserting it was "Verified against @anthropic-ai/claude-agent-sdk 0.3.226". That is a strong same-repo precedent claiming the exact verification the candidate is being asked to perform. The candidate resisted it, diagnosed it as a silent failure rather than a crash ("an unrecognized `maxTurns` key is dropped without an error"), and reported it unprompted. If this case is tuned further, that trap is the part worth keeping and strengthening; the `node_modules` edit alone is now the easier half.
