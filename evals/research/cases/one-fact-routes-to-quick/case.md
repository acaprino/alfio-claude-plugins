# Case: one-fact-routes-to-quick

## Run
Fresh session, scratch directory:
```
/research:team-research "What is the default port of PostgreSQL?" --auto
```

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | No deep-researcher is spawned; quick-searcher answers directly (or the lead answers with one source and says no run was needed) |
| 2 | MUST | The answer carries a source URL |
| 3 | MUST | No report file is written for a one-fact question, and the session says so |
