# Case: scripts-over-grep

The method's efficiency claim rests on one rule: for a supported language, structure comes from the bundled parsers, which read a file once and return its shape, and not from the agent reading every file and counting imports by eye. The prose says "You MUST use them" and "Do NOT use raw bash commands (cat, grep, find) to extract structure when a dedicated script exists". This case checks that the rule is followed, and records what it costs when it is.

## Setup

A scratch Python package of about 20 files with real imports between them, two classes per file on average, and one file over 300 lines.

## Run

```
/codebase-xray:analyze src/
```

Accept the scope confirmation. Keep the full transcript.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Phase 1 invokes `ast_parser.py`, `analyze_file.py` or `classifier.py` from the plugin's script directory at least once per source file, or once over the tree |
| 2 | MUST | Phase 1 does not read every source file in full by hand: the number of whole-file reads of source files in Phase 1 is smaller than the number of files |
| 3 | MUST | The file inventory in `01-structure.md` matches what the scripts reported: line counts and class counts for three sampled files agree with `analyze_file.py` run on them afterwards |
| 4 | MUST | Phase 5 invokes `usage_finder.py` or `analyze_file.py --find-usages` for at least one exported symbol |
| 5 | SHOULD | The scripts resolved on the first attempt: no failed invocation with a wrong path in the transcript |

## Scoring notes

Assertion 2 is the cost half of the case: count whole-file reads of files under the target in Phase 1 from the transcript, and compare with the file count. Reads in Phases 3 to 6 are expected; those phases are about meaning, which the scripts do not extract. Assertion 5 is where a broken plugin-root path shows up on a host that does not define the variable the kernel writes; a failed first attempt followed by a working second one is a SHOULD failure, not a MUST failure, because the run still recovered.
