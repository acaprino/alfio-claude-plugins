# Case: run-isolation

Every analysis is a run under `.deep-dive/runs/<run-id>/`, and the `.deep-dive/` root is a mirror written only at publish. The reason is concurrency: two runs in flight must never touch each other's files, and a consumer that wants a specific run must be able to find it after a later run has replaced the mirror. This case runs twice and checks that the second run neither read nor overwrote the first before publishing.

## Setup

A scratch package of 8 to 12 Python files.

## Run

First, in one session:

```
/codebase-xray:analyze src/ --depth=lite --run-name first
```

Then, in a fresh session, with the first run's output left in place:

```
/codebase-xray:analyze src/ --depth=lite --run-name second
```

Accept the scope confirmation both times. In the second session, when the pre-flight lists the completed first run, choose to start alongside.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | After the second run, `.deep-dive/runs/first/` is byte-identical to what it was after the first run |
| 2 | MUST | During the second run, no file under `.deep-dive/` outside `.deep-dive/runs/second/` changed until the publish step (compare mtimes or hashes captured before the publish step against the transcript's phase order) |
| 3 | MUST | `.deep-dive/runs.json` lists both runs and names `second` as `latest_completed`; the `first` entry was not dropped or rewritten |
| 4 | MUST | The mirror `.deep-dive/01-structure.md` equals `.deep-dive/runs/second/01-structure.md` after publish |
| 5 | SHOULD | The second run's pre-flight showed the first run in its list rather than ignoring it |

## Scoring notes

Assertion 2 needs the transcript: read the phase order and confirm no write outside the run directory appears before the publish step. Assertion 3 is the read-modify-write rule for the registry; an implementation that rewrites `runs.json` from scratch passes assertion 4 and fails this one, which is why both are listed.
