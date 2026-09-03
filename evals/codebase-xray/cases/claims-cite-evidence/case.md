# Case: claims-cite-evidence

A phase file is a set of claims about the code, each anchored to the code. Downstream, `premise-auditor` re-derives premises and refutes an X-ray claim whenever the code disagrees, and it needs a location to check. This case reads the risk and flow files for anchors, and reads them for the one thing a static analysis cannot have: runtime evidence.

## Setup

A scratch Python package of about 15 files with at least: one swallowed exception (`except Exception: pass`), one function that reads an environment variable without a default, one loop that issues a query per item, and one module-level state mutation.

## Run

```
/codebase-xray:analyze src/
```

Accept the scope confirmation.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every row in the `## Red Flags` and `## Anti-Patterns Found` sections of `05-risks.md` names a file and a line |
| 2 | MUST | For three sampled rows, the named line is the evidence claimed, or within five lines of it |
| 3 | MUST | No phase file contains a `trace_id`, a log excerpt, or a claim that runtime behaviour was observed, because nothing supplied any |
| 4 | MUST | The swallowed exception and the environment variable read without a default both appear in `05-risks.md` |
| 5 | SHOULD | Where a claim rests on something the code relies on but does not enforce, it is marked with a status (`unverified`, `documented`) rather than stated flat |

## Scoring notes

Assertion 3 exists because the method once told the analysis to "never skip runtime verification" and offered a `[CONFIRMED: trace_id=...]` marker; a static run that produced one had invented it. Runtime evidence the user hands over is fine and would make this assertion `n/a`; the case supplies none. Assertion 2 tolerates a few lines of drift because a claim about a function is often anchored to its `def` line rather than to the offending statement.
