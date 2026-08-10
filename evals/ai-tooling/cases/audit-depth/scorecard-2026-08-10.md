<!-- Scorecard produced by an independent judge that read only this case file and the
candidate output. It could not read plugins/ai-tooling/, so it judged the output against the
assertions rather than against the implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.0 working tree (NOT the installed plugin, which
  was 4.1.0 on this machine; see the run note in RESULTS.md)
- **How the component was exercised:** a fresh subagent adopted the 5.0.0 component body from the
  working tree and received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: audit-depth (quick-pass run only)

Candidate: `C:\Users\alfio\AppData\Local\Temp\claude\D--Projects-alfio-claude-plugins\10016771-ecb3-4b02-a328-463a9cd8e542\scratchpad\evalrun\out\audit-depth-quick.md`
Case: `D:\Projects\alfio-claude-plugins\evals\ai-tooling\cases\audit-depth\case.md`
Scope: only the first run (quick-pass trigger) was executed. The companion deep-pass run was not.

## Scores

| # | Type | Result | Evidence |
|---|---|---|---|
| 1 | MUST | pass | Opening line: "**Pass: quick.** Single-turn, no tool loop, no downstream parser, and if it regresses the person who typed it finds out immediately and re-runs it." The pass is named explicitly and the selection is justified. |
| 2 | MUST | pass | `RUN-ACCOUNTING: files_read=D:\Projects\alfio-claude-plugins\plugins\ai-tooling\agents\prompt-engineer.md` — the agent definition is the only file read; no `references/` file appears. Corroborated in-body by "No archetype table, no rubric, no reference reads." |
| 3 | MUST | pass | "No archetype table, no rubric, no reference reads." No rubric table appears anywhere in the output. The only tabular artifact is the five-line contract re-check block ("Constraints: ... Behaviors: ... Interface: ... Trust: ... Reasoning: unchanged"), which is a behavioral diff, not a dimension rubric. |
| 4 | SHOULD | fail (3 of 4 resolved) | Length: "in under 100 words" (A) and "Keep the whole summary under 120 words" (B). Audience: "Summarize the email below for me, the recipient". Quoted threads: "Thread: summarize the current state, then note who is waiting on whom. Skip quoted text already superseded by a later message." Signatures: no rule anywhere in either variant covers signature blocks, disclaimers, or footer boilerplate. Scored strictly against the assertion's own enumeration; SHOULD, so it does not block the verdict. |
| 5 | SHOULD | na | The comparison cannot be established from the output alone. The candidate contains no wall-clock or token figures for this run (its only token arithmetic — "original about 4 tokens, A about 90, B about 300" — is about the prompts under discussion, not run cost), and the `contract-preserved` run's cost is not present here. Per the case's scoring notes, marked n/a rather than guessed. |
| 6 | MUST | na | Companion run not executed. |
| 7 | MUST | na | Companion run not executed. |

## Result

MUST assertions passed: **3 / 3 scored** (assertions 6 and 7 excluded as `na`).

Case verdict: **PASS on the MUSTs that could be scored — but the case as a whole is PARTIAL, because the companion deep-pass run was not executed.** The case explicitly states that "the pair matters more than either half", so no conclusion about the agent's depth *selection* is licensed by this half alone: this run shows the agent going cheap on a trivial input, and shows nothing about whether it goes deep when depth is warranted.

## Observations

The output is unusually strong evidence for assertion 2 because the RUN-ACCOUNTING line is a positive record rather than an absence: exactly one file was read, and it was the agent definition itself, so the reference layer was untouched rather than merely unquoted. Assertion 3 is satisfied in spirit as well as letter — the response is not a stripped-down rubric with rows omitted, it is a different shape entirely (contract, defects, rewrite, contract re-check), which is what the case's framing of "be cheap" implies. Two things sit outside the assertions but are worth recording. First, the closing paragraph names the escalation condition ("If B goes into a tool, a script, or anything that summarizes mail you did not read first ... That version deserves the full treatment") — that is the deep-pass trigger of assertions 6 and 7 being anticipated from inside the quick pass, which is suggestive but is not a substitute for actually running the companion and cannot be scored as one. Second, the output volunteers "All **predicted**, not measured. No eval was run", an epistemic label belonging to a different case's assertions; noted only so a reader does not mistake it for evidence here. The single genuine shortfall is signature handling in assertion 4: the response reasons carefully about quoted-thread supersession and even about long-context block ordering, so the omission reads as an oversight in an otherwise thorough edge-case list rather than a deliberate scope decision, and it is the one place where the cheap pass visibly cost something.
