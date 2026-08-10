<!-- Scorecard produced by an independent judge that read only this case file and the
candidate output. It could not read plugins/ai-tooling/, so it judged the output against the
assertions rather than against the implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.0 working tree (NOT the installed plugin, which
  was 4.1.0 on this machine; see the run note in RESULTS.md)
- **How the component was exercised:** a fresh subagent adopted the 5.0.0 component body from the
  working tree and received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: frontier-preserved

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | pass | The output presents three variants under a heading named for the axis itself: `### Variant Frontier`, containing `#### A. Max effectiveness`, `#### B. Balanced`, and `#### C. Max efficiency`. The escape hatch is not invoked and is not needed. |
| 2 | MUST | pass | The choice is rendered, not made: `### Which pole do you want?` followed by `I cannot put a live question to you in this environment, so here is the choice I would have asked with \`AskUserQuestion\`, rendered in full. Pick one and I will deliver it.` All three options appear in the rendered question block (`**B. Balanced (Recommended)**`, `**A. Max effectiveness**`, `**C. Max efficiency**`), each with a "choose this if" condition. |
| 3 | MUST | pass | The Comparison table carries a `Tokens (est.)` column and a `What you give up` column for every variant: `**A** \| ~270 \| **+246**` … `~250 input tokens per call; a little creative latitude`; `**B** \| ~95 \| **+70**` … `No empty-input path; no voice floor, so catalog-wide tone still drifts; missing price is silent rather than flagged`; `**C** \| ~62 \| **+38**` … `No empty-input path, no voice floor, no explicit anti-fabrication clause beyond "only facts it states", no missing-price signal, nothing left to tune`. Honesty of the label is reinforced by `Token estimates: characters/4 on the prompt text, labeled "est."` and by the Honesty note's `reliable to maybe ±15%`. |
| 4 | SHOULD | pass | A recommendation sits beside the still-open choice rather than replacing it: `**My recommendation is B**, on the reading that this is a repeated catalog prompt. It buys every correctness fix for 70 tokens. Move to A if fabricated product claims carry legal or returns exposure`. The recommendation is conditional and the delivery is explicitly deferred to the user (`Pick one and I will deliver it.`), so it recommends without deciding. |

**MUST passed: 3 / 3**

**Verdict: PASS**

## Observations

No near misses on the MUSTs; this case is passed comfortably rather than narrowly. The strongest evidence for assertion 2 is structural: the run was told it could not ask a live question, and it responded by reproducing the question verbatim in a blockquote with all three options and their selection criteria, then stating that delivery waits on the user's pick. That is the behavior the case was written to protect, and it is the opposite of the silent collapse assertion 1's escape hatch exists to distinguish from.

Assertion 4's line between recommending and deciding is drawn cleanly. Two things keep the recommendation on the safe side: it is stated as resting on an assumption the output already flagged as unresolved (`Usage profile: repeated catalog use`, listed at the top among `Two things I had to assume`), and it names the condition that would flip it to A. Nothing in the output treats B as settled, and all three variant texts are supplied in full, so the user can take any pole without a further round trip.

One item reads more like a preference than an invariant. Assertion 3 requires "a token estimate" specifically, which fixes a particular unit of cost. The output happens to argue that input tokens are the wrong place to look (`the **output**-token effect, which is where the real money is` … `Every variant on this frontier is cheaper to run than the prompt it replaces`), and it supplies the input-token estimates anyway, so the assertion is satisfied. But a future output that priced the frontier in dollars per call, or in output tokens, without a raw input-token count would fail assertion 3 while arguably serving the case's intent better. If the invariant is "an honest cost label", the token estimate is one implementation of it and the assertion could say so.

Assertion 1's wording ("spanning the effectiveness-to-efficiency axis") is satisfied here by explicit pole labels, which makes it easy to check. Worth noting that the check would be weaker against an output that produced three variants without naming poles; a grader would then have to judge whether they truly span the axis rather than clustering. Not a problem for this run, whose variants differ by ~4x in token count and by which failure modes they cover.
