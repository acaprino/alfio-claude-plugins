# Case: already-good-prompt

An optimizer that always finds something to change is an optimizer that will eventually damage a good prompt to justify itself. "No material optimization needed" must be a reachable conclusion.

## Setup

None. Run in any scratch directory.

## Run

Ask `prompt-engineer` to optimize this prompt (or run `/prompt-optimize` with it):

```
Extract invoice fields from the document in <document> tags.

Return only JSON matching this schema, with no preamble:
{"invoice_number": string, "issue_date": "YYYY-MM-DD", "total_cents": integer, "currency": "ISO 4217 code"}

Rules:
- Use null for any field not present in the document. Never infer a missing value.
- If several totals appear, use the one labeled as the amount due.
- If the document is not an invoice, return {"error": "not_an_invoice"}.

<document>
{{DOCUMENT}}
</document>
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The output either concludes that no material optimization is warranted, or proposes only changes it can justify against a named defect; "restructured for clarity" with no defect named is a fail |
| 2a | MUST | The field names, the `{"error": "not_an_invoice"}` object, and the `{{DOCUMENT}}` placeholder survive byte-identical in every variant offered |
| 2b | MUST | Any change to the schema literal (including moving a format hint like `"YYYY-MM-DD"` out of it) or to the wording of the three rules is reported as a change. Silent rewording is a fail; a reported rewording is not |
| 3 | MUST | The `{"error": "not_an_invoice"}` escape and the "never infer a missing value" constraint are identified as behavior a caller relies on, not as gaps to fill |
| 4 | SHOULD | Dimensions this prompt deliberately maximizes (output determinism, constraint correctness) score 4 or 5 rather than being marked down for a completeness gap that a diagnosis item already carries |

## Scoring notes

The prompt is strong on purpose: explicit schema, null policy, ambiguity rule, out-of-scope escape, delimited input. Plausible non-defect churn to watch for and fail on: renaming `total_cents`, converting the JSON block to prose, adding few-shot examples that were not needed, or adding a reasoning scaffold to an extraction task.

Assertion 1 turns on the word **only**. A run can name six real defects and still fail it by carrying one change justified as "clearer structure", one example its own diagnosis said was unnecessary, or one behavior that reaches the rewrite without a diagnosis entry. Check the semantic diff's added-behaviors list against the diagnosis list and fail any addition that appears in the first and not the second.

Assertion 2 was one assertion until the 2026-08-10 run, phrased as "the schema, field names, placeholder and three rules survive unchanged". That conflated two different things: an identifier a caller binds to, where any edit breaks them, and rule wording, where tightening is legitimate as long as it is declared. It is split so a run can be right about one and wrong about the other, which is what actually happened.
