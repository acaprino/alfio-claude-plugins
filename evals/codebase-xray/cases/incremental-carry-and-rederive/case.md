# Case: incremental-carry-and-rederive

An incremental run is only worth trusting if it is honest about what it did not re-check. On an incremental run, a claim the change set did not mark is present in the published output byte for byte as the parent wrote it, apart from citation renumbering; every marked claim is re-derived or retired; every symbol the change set reported as added is documented; and the run does not publish while any marker survives. This case runs the incremental path end to end against a small, deliberate edit, then separately checks how `--update` and `--no-update` are allowed to change the checkpoint: `--no-update` skips detection outright, `--update` still waits for an explicit choice even when it recommends against the one it names, and `--update` refuses to invent a checkpoint when no parent run exists at all.

## Setup

**Main scratch package.** 11 Python files under `src/`:

- `config.py`: two functions, `parse_config(path)` (about 4 lines) and, defined after it, an unrelated `get_default_path()` (about 3 lines, returning the platform's default config path when none is given), substantial enough to earn its own documented row rather than a passing mention.
- `loader.py`: imports and calls `parse_config` from `config.py`.
- `deprecated_helper.py`: one function, `old_helper()`, imported by nothing.
- `queue.py`, `worker.py`, `api.py`, `models.py`, `cache.py`, `cli.py`, `utils.py`: seven more files unrelated to the edit below, none importing `config.py`, `loader.py`, or `deprecated_helper.py`, and none flagged by any risk finding.

**The edit**, made after the first run and before the second:

- Grow `parse_config` by about 4 lines (add validation logic), which shifts `get_default_path`'s line span down but leaves its body, and therefore its hash, untouched.
- Delete `deprecated_helper.py`.
- Add `validator.py` with one new function, `validate_schema(data)`, imported by nothing yet.

No other file changes. With 11 files in the parent snapshot and 3 touched, the affected ratio is comfortably under the default 0.4 threshold.

**Second scratch directory.** A handful of unrelated files with no `.codebase-xray/` present, used only for the `--update`-with-no-parent check below.

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
| 1 | MUST | In Session 2's published `02-interfaces.md`, the claim about `get_default_path` has the same text as in Session 1's published version; if cited as `config.py:<line>`, the line number has moved to match the shift, and if cited as `config.py::get_default_path`, nothing about the citation needed to move. The claim citing `queue.py` (never touched) is identical including any line number |
| 2 | MUST | In Sessions 1 and 2, the sessions that proceed past the checkpoint, `snapshot.py write` runs after scope confirmation and before Phase 0 begins, in that transcript order, including Session 1's full run |
| 3 | MUST | In Session 2, detection ran with no flag present, and the run did not proceed past the checkpoint until an explicit choice was made |
| 4 | MUST | In Session 3, no `snapshot.py diff` call appears in the transcript, and the checkpoint shown is the classic block (phase list, no parent figures), not the incremental-aware one, even though `second` is a valid completed parent for this target |
| 5 | MUST | In Session 4, detection ran despite `--update`, the checkpoint reported `recommendation: full` with its reasons printed (flags differing from the parent's), and the incremental option was still listed and numbered as a choice |
| 6 | MUST | In Session 5, the run stops before `$RUN_DIR` or `state.json` is created and before any phase runs, states that no completed run exists for this target, and never fabricates a parent |
| 7 | MUST | In Session 2, every file the transcript shows being read during phases 1 to 6 is either in `changes.json`'s `affected_files` or named under `## Extra reads` in `changes.md` |
| 8 | MUST | Every claim in Session 1's `05-risks.md` that cites none of `config.py`, `deprecated_helper.py` or `validator.py` is present unchanged in Session 2's `05-risks.md`, with no `xray:stale` marker ever inserted above it. `05-risks.md` never receives `validate_schema` documentation (lite depth writes added-symbol claims to `01` and `02` only). If no claim in `05-risks.md` cites any of the three edited files, the whole file is never rewritten during the re-derivation step, and its only legitimate read is as Phase 7's regeneration input |
| 9 | MUST | In Session 2, `snapshot.py check` runs after re-derivation and before the publish step, and the publish step runs only after that check exited 0 |
| 10 | MUST | Session 2's `changes.md` carries all four sections, `## Claims confirmed`, `## Claims revised`, `## Claims retired`, `## Claims added`, and every claim that cited `deprecated_helper.py` or `deprecated_helper.py::old_helper`, in whichever phase file it appeared, is listed under `## Claims retired`, none under confirmed or revised |
| 11 | MUST | By the time Session 2 publishes, `01-structure.md` and `02-interfaces.md` each document `validator.py::validate_schema` |
| 12 | MUST | After Session 2 publishes, `.codebase-xray/snapshot/`, `.codebase-xray/changes.json` and `.codebase-xray/changes.md` do not exist at the mirror root; those three live only under `.codebase-xray/runs/second/` |
| 13 | SHOULD | Session 2's checkpoint showed real figures (files modified/added/removed, symbols changed/added/removed, affected claims) matching `changes.json`'s `totals`, not placeholder text |

## Scoring notes

Assertion 1 is the case: score it by diffing Session 1's and Session 2's published `02-interfaces.md` claim by claim, not by eyeballing the whole file. `renumber_line` in `snapshot.py` only rewrites `path:line` citations; a `path::symbol` citation encodes no line number and has nothing to renumber, so score whichever form the run actually used. If the `get_default_path` claim happens to be cited by line, a scorer who only checks that the text is unchanged and skips the line number will pass a run that quietly broke renumbering.

Assertion 4 needs the transcript, not the outcome: a run that happens to land on the classic checkpoint for the wrong reason (say, a bug that always skips detection) is not what this assertion is protecting against, so also confirm `--no-update` is the stated reason if the transcript gives one.

Assertion 5 does not require actually accepting the incremental option in Session 4, only that it was there and numbered; the point is that `--update` narrows the checkpoint to "some option must be chosen," never to "the incremental option is chosen for you."

Assertion 8 is written to hold regardless of what Session 1's risk pass actually found: whether `05-risks.md` cites `parse_config` is the model's own judgment call in Session 1, not something the fixture can force. Score the per-claim half first, then check the whole-file half only if it applies. The whole-file half is read from the transcript's write calls between the carry step and the check step, the same way `team-mode-partition-ownership` assertion 2 is scored: a final-tree diff cannot distinguish "never opened" from "opened, edited, and it happened to come out the same."

Assertion 9's exit-code table (0 clean, 1 stale marker or undocumented symbol, 2 missing `changes.json`) is already covered by `tests/test_xray_snapshot.py`; this assertion is about whether the agent calls the gate and orders its work around it, not about whether the gate's exit codes are individually correct.

Assertion 7 is conditional in the sense that Session 2's small edit may not force any extra read at all; if none occurs, score it `pass` on the absence of any unlogged read outside `affected_files`, not `n/a` — the invariant is "no unlogged read outside the set," which holds whether or not an extra read happened to be needed.
