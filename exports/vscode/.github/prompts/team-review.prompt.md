---
description: Multi-dimensional adversarial code review. Builds context with an X-ray pass plus an interconnect map, auto-detects which review dimensions the target warrants, dispatches specialized reviewers in parallel, then runs a 3-lens verification panel and a completeness critic before reporting. Session output under .team-review/.
agent: review-orchestrator
argument-hint: <target> [--reviewers auto|security,performance,...] [--base-branch main] [--all] [--deep] [--skip-interconnect] [--fast] [--rigorous]
---

# Team Review

Run the multi-dimensional review pipeline on the target the user named in the chat input after `/team-review`.

Expected form: `<target> [--reviewers auto|<list>] [--base-branch main] [--all] [--deep] [--skip-interconnect] [--fast] [--rigorous]`

`<target>` is a file path, a directory, a git diff range such as `main...HEAD`, or a PR number such as `#123`. If no target was given, ask for it with `#vscode/askQuestions` before doing anything else.

## Steps

1. **Read `.github/skills/review-quality-gates/references/pipeline.md`.** That is the full six-phase workflow. Follow it exactly; do not improvise the phase order or the file names.

2. **Load `.github/skills/review-quality-gates/SKILL.md`** for the context-sharing pattern, the per-dimension anchor routing table, the verification panel spec, and the completeness critic spec.

3. **Verify the reviewer agents exist.** The roster is in the pipeline reference. They ship under `.github/agents/` and are declared in the `agents:` allowlist of `review-orchestrator`. If `#agent/runSubagent` is unavailable, say so explicitly and stop: a single-agent review is a different product, and delivering one silently would misrepresent the coverage.

4. **Execute.** Show the detected dimension plan before spawning anything. Reviewers cost tokens proportional to the file count times the dimension count, and the user approves that spend.

## Notes

- Phase 1 runs the X-ray pipeline at `--depth=lite` (or full depth under `--deep`) and copies its `08-interconnect-map.md` into `.team-review/02-interconnect.md`. This requires the `codebase-xray` skill and the `xray-*` agents from the same bundle. Without them, run with `--skip-interconnect`.
- Reviewers read the X-ray **run directory**, not the `.deep-dive/` root mirror. A concurrent X-ray run can republish the root mid-review.
- The barrier between review and consolidation is file existence, verified with `#search/fileSearch`. Do not trust a reviewer's returned summary.
- Nothing in this pipeline edits source code. The report ends the run, and `.team-review/` stays on disk.
- Add `.team-review/` and `.deep-dive/` to your `.gitignore`.
