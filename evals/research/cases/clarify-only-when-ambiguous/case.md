# Case: clarify-only-when-ambiguous

## Run
Two fresh sessions, scratch directory.
Run A: `/research:team-research "What is the maximum payload size of an AWS Lambda synchronous invocation, and has it changed since 2024?"`
Run B: `/research:team-research "best database"`
In B, answer the clarification with any consistent choices, then `Approve`.

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Run A asks no clarifying question (it may state that none was needed) and goes to the plan |
| 2 | MUST | Run B asks clarifying questions, at most four, in a single question-tool call, before the plan |
| 3 | MUST | Run B's plan restates the question using the answers given |
| 4 | SHOULD | Run A is routed to `quick` or to a direct quick-searcher answer rather than `standard` |
