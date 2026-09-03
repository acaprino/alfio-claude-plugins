# Case: incremental-carry-and-rederive

An incremental run is only worth trusting if it is honest about what it did not re-check. On an incremental run, a claim the change set did not mark is present in the published output byte for byte as the parent wrote it, apart from citation renumbering; every marked claim is re-derived or retired; every symbol the change set reported as added is documented; and the run does not publish while any marker survives. This case runs the incremental path end to end against a small, deliberate edit, and separately checks the three ways the `--update` / `--no-update` flags are allowed to change what happens at the checkpoint, never whether there is one.

## Setup

**Main scratch package.** 11 Python files under `src/`:

- `config.py`: two functions, `parse_config(path)` (about 4 lines) and, defined after it, an unrelated `get_default_path()` (about 3 lines).
- `loader.py`: imports and calls `parse_config` from `config.py`.
- `deprecated_helper.py`: one function, `old_helper()`, imported by nothing.
- `queue.py`, `worker.py`, `api.py`, `models.py`, `cache.py`, `cli.py`, `utils.py`: seven more files unrelated to the edit below, none importing `config.py`, `loader.py`, or `deprecated_helper.py`, and none flagged by any risk finding.

**The edit**, made after the first run and before the second:

- Grow `parse_config` by about 4 lines (add validation logic), which shifts `get_default_path`'s line span down but leaves its body, and therefore its hash, untouched.
- Delete `deprecated_helper.py`.
- Add `validator.py` with one new function, `validate_schema(data)`, imported by nothing yet.

No other file changes. With 11 files in the parent snapshot and 3 touched, the affected ratio is comfortably under the default 0.4 threshold.

**Second scratch directory.** A handful of unrelated files with no `.deep-dive/` present, used only for the `--update`-with-no-parent check below.

## Run

All in the main scratch package unless stated otherwise. Keep the full transcript of every session.

**Session 1, fresh session.** Full run, before the edit:

```
/codebase-xray:analyze src/ --depth=lite --run-name first
```

Accept the classic scope confirmation (no candidate parent exists yet).

Apply the edit described above once Session 1 has published.

**Session 2, fresh session.** No update flag:

```
/codebase-xray:analyze src/ --depth=lite --run-name second
```

Detection should run on its own. At the checkpoint, choose option 1, incremental update from `first`.

**Session 3, fresh session.** `--no-update`, no further edit:

```
/codebase-xray:analyze src/ --depth=lite --no-update --run-name third
```

At the checkpoint, choose Cancel.

**Session 4, fresh session.** `--update`, still no further edit, and deliberately not `--depth=lite` so the requested flags differ from `second`'s recorded flags:

```
/codebase-xray:analyze src/ --update --run-name fourth
```

At the checkpoint, read which option is the incremental one and note its number, then choose Cancel.

**Session 5, fresh session, in the second scratch directory**, which has no prior run:

```
/codebase-xray:analyze src/ --update
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | In Session 2's published `02-interfaces.md`, the claim citing `config.py::get_default_path` has the same text as in Session 1's published version and its line number has moved to match the shift, and the claim citing `queue.py` (never touched, never renumbered) is identical including its line number |
| 2 | MUST | In Sessions 1, 2, 3 and 4, `snapshot.py write` runs after scope confirmation and before Phase 0 begins, in that transcript order, including Session 1's full run |
| 3 | MUST | In Session 2, detection ran with no flag present, and the run did not proceed past the checkpoint until an explicit choice was made |
| 4 | MUST | In Session 3, no `snapshot.py diff` call appears in the transcript, and the checkpoint shown is the classic block (phase list, no parent figures), not the incremental-aware one, even though `second` is a valid completed parent for this target |
| 5 | MUST | In Session 4, detection ran despite `--update`, the checkpoint reported `recommendation: full` with its reasons printed (flags differing from the parent's), and the incremental option was still listed and numbered as a choice |
| 6 | MUST | In Session 5, the run stops before any phase work or run directory is left behind, states that no completed run exists for this target, and never fabricates a parent |
| 7 | MUST | In Session 2, every file the transcript shows being read during phases 1 to 6 is either in `changes.json`'s `affected_files` or named under `## Extra reads` in `changes.md` |
| 8 | MUST | In Session 2, `05-risks.md` is never rewritten during the re-derivation step (no `xray:stale` marker was inserted into it, and `validate_schema` documentation was not added to it); its only legitimate read is as Phase 7's regeneration input |
| 9 | MUST | In Session 2, `snapshot.py check` runs after re-derivation and before the publish step, and the publish step runs only after that check exited 0 |
| 10 | MUST | Session 2's `changes.md` carries all four sections, `## Claims confirmed`, `## Claims revised`, `## Claims retired`, `## Claims added`, and the claim that cited `deprecated_helper.py::old_helper` is listed under `## Claims retired`, not confirmed or revised |
| 11 | MUST | By the time Session 2 publishes, `01-structure.md` and `02-interfaces.md` each document `validator.py::validate_schema` |
| 12 | MUST | After Session 2 publishes, `.deep-dive/snapshot/`, `.deep-dive/changes.json` and `.deep-dive/changes.md` do not exist at the mirror root; those three live only under `.deep-dive/runs/second/` |
| 13 | SHOULD | Session 2's checkpoint showed real figures (files modified/added/removed, symbols changed/added/removed, affected claims) matching `changes.json`'s `totals`, not placeholder text |

## Scoring notes

Assertion 1 is the case: score it by diffing Session 1's and Session 2's published `02-interfaces.md` claim by claim, not by eyeballing the whole file. The `get_default_path` row is the one that must change its cited line number while its claim text stays byte for byte identical; a scorer who only checks that the text is unchanged and skips the line number will pass a run that quietly broke renumbering.

Assertion 4 needs the transcript, not the outcome: a run that happens to land on the classic checkpoint for the wrong reason (say, a bug that always skips detection) is not what this assertion is protecting against, so also confirm `--no-update` is the stated reason if the transcript gives one.

Assertion 5 does not require actually accepting the incremental option in Session 4, only that it was there and numbered; the point is that `--update` narrows the checkpoint to "some option must be chosen," never to "the incremental option is chosen for you."

Assertion 8 is read from the transcript's write calls between the carry step and the check step, the same way `team-mode-partition-ownership` assertion 2 is scored: a final-tree diff cannot distinguish "never opened" from "opened, edited, and it happened to come out the same."

Assertion 9's exit-code table (0 clean, 1 stale marker or undocumented symbol, 2 missing `changes.json`) is already covered by `tests/test_xray_scripts.py`; this assertion is about whether the agent calls the gate and orders its work around it, not about whether the gate's exit codes are individually correct.

Assertion 7 is conditional in the sense that Session 2's small edit may not force any extra read at all; if none occurs, score it `pass` on the absence of any unlogged read outside `affected_files`, not `n/a` — the invariant is "no unlogged read outside the set," which holds whether or not an extra read happened to be needed.
