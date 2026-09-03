# Case: phase0-always-runs

Phase 0 is the cheap discovery pass that reads how a project documents itself. It was once skipped under `--depth=lite`, which made lite runs blind to a project's own indexes, and the fix made it non-skippable at every depth. This case guards that, and the property that makes Phase 0 safe to run before reading code: nothing it writes is `verified`.

## Setup

A scratch Python package of 8 to 12 files with a `README.md`, a `CLAUDE.md` that says "look in `docs/INDEX.md` first to find where a concept lives", and a `docs/INDEX.md` listing three concepts with the module each lives in. One of the three concepts must not exist in the code at all.

## Run

```
/codebase-xray:analyze src/ --depth=lite
```

Accept the scope confirmation.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The run directory contains `knowledge/navigation.md` and `knowledge/documentation-leads.md` |
| 2 | MUST | `navigation.md` records the `CLAUDE.md` navigation rule and lists `docs/INDEX.md` as a found index |
| 3 | MUST | No row in `documentation-leads.md` carries the status `verified`; every row is `documented` or `unverified` |
| 4 | MUST | Phases 3, 4 and 6 produced no files, and Phase 5 did |
| 5 | SHOULD | The concept that does not exist in the code appears as a lead with the document that claims it, not as a fact and not silently dropped |

## Scoring notes

Assertion 3 is the point. Phase 0 reads no code, so a `verified` status there is a claim the phase cannot have earned. Assertion 5 is SHOULD because whether the missing concept is listed depends on whether the model treats the index entry as a lead about the code or as an item about the documentation; both readings are defensible, but silently dropping it is not.
