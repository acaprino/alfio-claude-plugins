# Case: majority-failure-stops

## Setup
Simulate failing researchers by running with network access blocked for subagents, or in an environment where WebFetch and WebSearch fail (e.g. offline), with `SERPER_API_KEY` unset. If that cannot be arranged, score every assertion n/a and say so.

## Run
```
/research:team-research "Compare the three most used Python web frameworks" --auto --depth standard
```

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | If pre-flight detects no backend, the run stops at pre-flight with the reason and no researcher is spawned |
| 2 | MUST | If researchers are spawned and more than half return `error` or empty, the lead stops, names the failed researchers, and writes no report |
| 3 | MUST | No synthesis is produced from fewer than half of the planned researchers |
