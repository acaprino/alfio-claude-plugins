<!-- Scorecard produced by an independent judge that read only this case file and the
candidate output. It could not read plugins/ai-tooling/, so it judged the output against the
assertions rather than against the implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.0 working tree (NOT the installed plugin, which
  was 4.1.0 on this machine; see the run note in RESULTS.md)
- **How the component was exercised:** a fresh subagent adopted the 5.0.0 component body from the
  working tree and received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: optimize-for-shortcut

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | pass | "`--optimize-for tokens` selects the efficiency pole, so I am delivering C directly without asking you to pick." Header: "## Delivered: Variant C (max efficiency)". |
| 2 | MUST | pass | "Token-budget prompting (pattern 13) redirected to output length; brevity instruction (Concise CoT mechanism); minimal one-clause trust boundary". Also: "**Token-budget prompting (pattern 13)** does apply, redirected from a thinking budget to an output budget, and **Concise CoT's** brevity mechanism ... is what the "under 250 words, no preamble" line is doing." And redundancy is named as the defect being removed: "Redundant Context (detailed/thorough/comprehensive/complete are one instruction stated four times)". |
| 3 | MUST | pass | "**Token counts are estimates**, characters/4 on the prompt text." And in the comparison preamble: "Input estimates: characters/4 on the prompt text, labeled est. Output estimates assume a ~3,000-word source and ~1.33 tokens per English word." Delivered figure is labeled: "**~59 tokens (est.), down 3% on input and roughly 60-75% on output.**" |
| 4 | SHOULD | pass | "**Coverage. The model now triages rather than covers.**" And: "**C stops doing the thing the original prompt was written to do.** On a dense source, points will be dropped, and which points get dropped is the model's judgment, not a rule you set." |

**MUST passed: 3 / 3**

**Verdict: PASS**

## Observations

Assertion 1 is the one worth examining closely, because the output does display a full three-variant frontier (A/B/C) before delivering. Judged against the assertion as written, that is not a failure: the frontier is presented as information, the pole is never put back to the user as a question, and the output states in one sentence that it is delivering C "without asking you to pick". The trailing "Pass `--compare` if you want to be asked instead" is a documented escape hatch, not a request for a decision, and it appears after the delivered artifact rather than in place of it. A stricter reading that treats any frontier display on a declared-pole run as a shortcut violation would flip this row, but that reading is not what the assertion says, and the case text itself only forbids making the user "answer a question they have already answered".

Assertion 2 passes clearly and is not a near miss: the compression is attributed to two named techniques rather than to adjective deletion, and the named lever is genuinely the mechanism doing the work (an output-length budget), not a label pasted onto a paraphrase. One caveat that does not affect the outcome: the technique names carry internal catalog numbering ("pattern 13"), which a reader outside the plugin cannot resolve on its own. Concise CoT and token-budget prompting are named in prose alongside it, so the assertion is satisfied without the catalog reference.

One near miss sits in the header row of the comparison table: the "Original" row lists "Technique applied: none", which is correct but means the technique naming lives only in the variant rows. It is present where the assertion needs it.

Assertion 4, marked SHOULD, is the row most exposed to preference rather than invariant. It asks for a named trade-off even after the user chose the pole, which is a house style commitment about honesty rather than a property the artifact must have to be correct. It is satisfied here emphatically, so the distinction costs nothing on this run, but a future output that delivers a correct efficiency pole with a one-line trade-off note should not be penalized as heavily as the MUST rows.

Assertion 3 is an invariant and is met redundantly: the estimate label and its method appear in the comparison preamble, in the honesty note, and on the delivered figure. The output goes further than the assertion requires by separating estimate reliability (input counts firm, output counts soft), which is honest rather than hedging.
