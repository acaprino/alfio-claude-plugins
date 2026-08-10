<!-- Scorecard produced by an independent judge that read only this case file and the
candidate output. It could not read plugins/ai-tooling/, so it judged the output against the
assertions rather than against the implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.0 working tree (NOT the installed plugin, which
  was 4.1.0 on this machine; see the run note in RESULTS.md)
- **How the component was exercised:** a fresh subagent adopted the 5.0.0 component body from the
  working tree and received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: no-explicit-cot

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | pass | No variant contains `think step by step`, `<thinking>`, `<analysis>`, or a reason-first-then-answer instruction. A's instruction is direct (`Read the ticket in <ticket> and assign exactly one category.`) and its output contract puts the label first (`{"category": "bug\|billing\|feature_request\|other", "confidence": ..., "evidence": ..., "rationale": ...}`). B and C carry the same shape. The decision is stated explicitly: `**Reasoning-pattern decision, recorded:** no explicit scaffold added. Target is Claude, a reasoning-model class, where the default is direct instructions plus precise success criteria`. |
| 2 | MUST | pass | No `<analysis>` block appears anywhere in the output. The body is the enumerated deliverable: `### Diagnostic Scorecard (original, predicted)`, `### Variant Frontier`, `### Comparison`, `### Behavioral changes`, `### Honesty note`. |
| 3 | SHOULD | na | The case makes this conditional on a scaffold being added, and none was: `Reasoning:    unchanged, deliberately. No explicit scaffold was added`. |
| 4 | SHOULD | pass | The clause is treated as an output requirement, not stripped: `I treated it as an **audit trail for a human triager**, not as an accuracy device`, and `the visible explanation is an audit artifact, not a reasoning step`. All three variants keep a `rationale` field, and the one place it is degraded is surfaced as a behavior change: `removed: the verbatim evidence quote, and the rationale is capped at 12 words. "Explain your choice" survives in name`. |

**MUST passed: 2 / 2**

**Verdict: PASS**

## Observations

The near miss the scoring notes warn about is handled cleanly rather than by luck. The candidate keeps the caller's explanatory requirement in every variant while refusing to add one of its own, and it separates the two explicitly by arguing that on a thinking-enabled model a post-hoc explanation is a rationalization of a committed label rather than a reasoning step. It also declines to move `evidence` ahead of `category`, and says why, which is the one edit that would have quietly turned the preserved requirement into an imposed scaffold. That is the invariant holding for the right reason.

Assertion 2 is the one worth flagging. The output opens with a `## Setup note` section, before the scorecard, that discloses which audit pass ran, three ambiguities resolved by assumption, and a recorded rationale for rejecting Self-Consistency and Chain of Draft. It also closes with a `Files read for this run:` line. Neither is an `<analysis>` block, and neither walks through intermediate working toward the answer, so I scored it a pass: these are assumption disclosures and a decision record, and assertion 3 presupposes that a reasoning-pattern decision is reportable in the output. But a stricter reader could treat the assertion's enumeration ("the response is the scorecard, variants, comparison, behavioral changes, and honesty note") as a closed whitelist, in which case the setup note, the `### Which pole do you want?` section, the `### Test inputs` section, and the files-read line are all outside it. If the case intends that enumeration as a whitelist rather than a characterization, it should say so, because as written the clause that carries the invariant is the `<analysis>`/working-dump clause and the enumeration reads as descriptive.

One assertion looks closer to a preference than an invariant: assertion 4 is defensible as a real property (not destroying a caller requirement), but nothing in it distinguishes preserving the requirement from preserving it *well*. Variant C keeps the word "explain" while capping the rationale at 12 words, which the candidate itself concedes stops being an explanation a human can act on. It passes the assertion either way, so the assertion cannot detect the failure mode it seems aimed at.
