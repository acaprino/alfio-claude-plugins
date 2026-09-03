# Case: claims-carry-status

The interconnect map is the one X-ray artifact every reviewer reads, and it declares itself a fallible hypothesis index. What makes that honest is the status on every row: `verified` means enforced in code and cites where, `documented` cites the document, `unverified` says the code relies on it and nothing enforces it, `disputed` cites both sides. A `verified` without an enforcement citation is the single most damaging row the map can carry, because a reviewer will build a finding on it.

## Setup

A scratch Python package with a small service layer: a repository class whose `connect()` must precede `query()`, a validator that the HTTP handler calls before the service, a `balance` that the code assumes non-negative in three places and checks in one, and a docstring stating a rule the code does not enforce. Run `/codebase-xray:analyze src/` first so a run directory exists.

## Run

Spawn `codebase-xray:semantic-interconnect-mapper` with the run directory as primary context and `src/` as the target, output to `interconnect.md` in the scratch directory.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every row in `## Invariants`, `## Assumptions` and every bullet in `## Contracts` carries exactly one of `verified`, `documented`, `unverified`, `disputed` |
| 2 | MUST | Every row marked `verified` cites a file and line, and the cited line enforces the claim (an assert, a validator, a type, a runtime check) |
| 3 | MUST | The ordering constraint `connect()` before `query()` appears as an implicit contract with a caller citation |
| 4 | MUST | The docstring rule the code does not enforce is `documented`, not `verified` |
| 5 | MUST | The map proposes no fix and no recommendation |
| 6 | SHOULD | The `balance` assumption is listed once with its three reliance sites, not three times |

## Scoring notes

Assertion 2 is the case. Read each `verified` row's citation and ask whether that line would fail if the claim were false; a `verified` that cites a call site rather than an enforcement site is a fail. Assertion 5 is the mapper's no-recommendations rule; a "should add validation" anywhere is a fail even when the advice is right.
