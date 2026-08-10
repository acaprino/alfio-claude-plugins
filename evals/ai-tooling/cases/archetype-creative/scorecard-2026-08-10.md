<!-- Scorecard produced by an independent judge that read only this case file and the
candidate output. It could not read plugins/ai-tooling/, so it judged the output against the
assertions rather than against the implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.0 working tree (NOT the installed plugin, which
  was 4.1.0 on this machine; see the run note in RESULTS.md)
- **How the component was exercised:** a fresh subagent adopted the 5.0.0 component body from the
  working tree and received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: archetype-creative

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | pass | Classified in prose as a creative archetype, and the classification drives the evaluation rather than following it. Diagnosis: "The original errs toward under-specification, which for this archetype is the safer direction to err." Rewrite: "The trade-off axis for a creative prompt is not tokens, it is **latitude versus control**, and only you know your tolerance." Reasoning section: "Single-pass creative generation with no decomposition, no retrieval, no tool use, and no cost constraint sits outside what a pattern buys you." |
| 2 | MUST | pass | No dimension is scored at all: "No archetype table, no full rubric, no reference loads." Determinism is treated as a cost rather than a target: "variant A will produce more similar scenes across runs than variant B. If the outputs start converging on one scene, that is the signal to drop to B, not to add more constraints." Ranking of the variants is explicitly refused: "treat the two variants as a choice to make by reading, not as a ranked pair." Nothing is scored low on determinism and then optimized upward. |
| 3 | MUST | pass | Neither variant imposes output shape. Both close with an explicit anti-structure line: "Output the scene and nothing else: no title, no preamble, no commentary afterward." No ordering prescription of the "setting, then character, then hook" kind appears anywhere. The structural fills are named and withheld: "**POV, tense, person, character, era, named place.** All left open." The one shape-prescribing line considered (`Something must occur, however small, and the scene must end mid-motion rather than at rest.`) is explicitly kept out of both variants and offered as the user's call. |
| 4 | MUST | pass | Latitude is named as a protected property in the contract: "This is where the prompt wants variation, and it is the part an \"improvement\" is most likely to destroy." Every narrowing change is itemized in the semantic diff under `Behaviors: added` and flagged for approval: "Three behavior additions, all of them constraints you have to approve." The rejection rationale is explicit: "the fastest way to make a creative prompt worse is to fill them." Few-shot examples are declined for the same reason: "On a prompt whose whole purpose is originality, examples become the thing to imitate." |
| 5 | SHOULD | pass | Diagnosis item 1: "**\"Avoid cliche\" is a bare negative with no referent.** The model has no defined class to check itself against, so it complies nominally and still produces the stock kit". The fix stays proscriptive rather than prescriptive about content: it names the basin to avoid ("boarded arcades, rusting fairground rides, wheeling gulls, peeling paint, grey sea standing in for sorrow") and guards the overcorrection ("An image that calls attention to its own novelty is the same failure in different clothes. Aim for exact, not unusual."). |

**MUST assertions passed: 4/4**

**Case verdict: PASS**

## Observations

Assertion 1 holds, but on weaker footing than the assertion text implies. The output explicitly declines the archetype machinery ("No archetype table, no full rubric"), so the classification is never a labeled step. It exists as scattered prose across three later sections, and the earliest unambiguous instance ("for this archetype") sits at the *end* of the diagnosis rather than before it. What carries the assertion's intent earlier is the contract table's "Intentional freedoms" row, which identifies the prompt as one whose unspecified dimensions are deliberate. A future candidate that skipped both the archetype table and the word "creative" could produce an equally good rewrite and fail this assertion on vocabulary alone, which suggests the assertion is testing for a label where the case cares about a behavior.

Assertion 2 is the one that was not really exercised. The failure it guards against requires a rubric to exist so a dimension can be scored low; this candidate ran no rubric, so determinism was never marked N/A and never excluded by name. The invariant held because nothing was scored, not because the archetype-aware N/A path was demonstrated. The strongest positive evidence is indirect: the third check treats cross-run convergence as the signal to move to the higher-latitude variant. That is the right disposition, but a run that takes the deep path with the full rubric would test this assertion far more directly.

Two near-misses on assertion 3, both of which I scored as passes. First, variant A carries four labeled blocks ("Length:", "What the scene has to do:", "Register:", "Two failure modes to stay out of:"), which at a glance read like the template the case warns about. They are prompt-side scaffolding constraining content and register, not output shape, and no ordering is prescribed, so the scoring note's named near-miss does not apply. The assertion's phrase "section headers" is ambiguous between prompt-side and output-side headers; under a prompt-side reading variant A would arguably fail, which I take to be a preference about prompt formatting rather than the invariant the case is defending. Second, "Length: 350-500 words" is the closest thing to the assertion's "length schema". I scored it a pass because "short" is already in the source contract, the number is disambiguation of an existing constraint rather than a new one, and the output surfaces it as a reversible assumption ("If you meant 150, change the number"). It is a single bound, not a per-section length spec.

One further note on assertion 4: the "Register: literary. Exact sentences. No stacked metaphors. Do not close on an aphorism." line narrows latitude at the sentence and ending level, and it does not appear as its own `Behaviors: added` row in the semantic diff. It is reported, but in prose before and after the diff (diagnosis item 5, and "the aphorism ban are cheap to delete if they feel fussy") rather than in the structured change list. That is a reporting-completeness gap in the diff, not a hidden change.
