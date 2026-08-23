# Case: plan-before-search

## Run
Fresh session, scratch directory:
```
/research:team-research "What are the trade-offs between SQLite and PostgreSQL for a single-node web app in 2026?" --no-clarify
```
Answer the plan gate with `Approve`.

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | A plan listing sub-questions is shown through a question tool and approval is awaited before any WebSearch, WebFetch or websearch.py call appears in the transcript |
| 2 | MUST | The plan names the tier, the backend and the output path |
| 3 | MUST | The approved plan appears verbatim in the report's Methodology section |
| 4 | SHOULD | Sub-questions are derived from the question (not a fixed list of source angles) |
