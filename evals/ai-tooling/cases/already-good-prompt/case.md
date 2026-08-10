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
| 2 | MUST | The JSON schema, the field names, the `{{DOCUMENT}}` placeholder, and the three rules survive unchanged in any variant offered |
| 3 | MUST | The `{"error": "not_an_invoice"}` escape and the "never infer a missing value" constraint are identified as behavior a caller relies on, not as gaps to fill |
| 4 | SHOULD | Dimensions this prompt deliberately maximizes (output determinism, constraint correctness) score high rather than being flagged as over-constraint |

## Scoring notes

The prompt is strong on purpose: explicit schema, null policy, ambiguity rule, out-of-scope escape, delimited input. Plausible non-defect churn to watch for and fail on: renaming `total_cents`, converting the JSON block to prose, adding few-shot examples that were not needed, or adding a reasoning scaffold to an extraction task.
