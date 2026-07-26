---
description: Audit a codebase for missed unification opportunities and wrong abstractions, or check with --diff whether newly written code was already available for reuse. Auto-launches /deep-dive-analysis:deep-dive-analysis when .deep-dive/ is missing or incomplete. Report-only.
argument-hint: "[path] [--diff [<base-ref>]] [--scope <subpath>] [--severity-floor low|medium|high] [--focus unification|wrong-abstraction|both]"
---

# /abstraction-architect:audit

Audit a codebase for the two failure modes of pure architecture: missed unification (cross-cutting concerns scattered across call sites that should be a single layer) and wrong abstractions (god services, flag-soup functions, premature interfaces, leaky abstractions). Report-only.

## Usage

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --severity-floor high              # only high-severity findings
/abstraction-architect:audit --focus wrong-abstraction          # restrict to one category
/abstraction-architect:audit --scope src/api --focus unification
/abstraction-architect:audit --diff                             # did the code I just wrote already exist?
/abstraction-architect:audit --diff origin/master               # same, against an explicit base ref
```

## Arguments

- `[path]` (optional) — codebase root. Default: current working directory.
- `--diff [<base-ref>]` (optional) — run the agent in diff-anchored mode instead of a whole-codebase audit. Takes the changed code as the anchor and searches the rest of the codebase for prior art, reporting whether an added unit duplicates something that already exists or has become the third occurrence that justifies unifying. Base ref defaults to the merge base with the default branch, falling back to `HEAD` for uncommitted work.
- `--scope <subpath>` (optional) — limit findings to a subtree. Deep-dive is still run on the full codebase; the agent filters findings by scope.
- `--severity-floor low|medium|high` (optional) — drop findings below this severity. Default: `medium`.
- `--focus unification|wrong-abstraction|both` (optional) — restrict to one finding category. Default: `both`.

## What this command does

1. **Resolves the target path.** Defaults to the current working directory if `[path]` is omitted.

2. **Checks for `.deep-dive/`.** Looks for the required files: `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`. The optional `08-interconnect-map.md` is also checked; if absent the audit proceeds without bounded-context fusion analysis.

3. **Auto-launches deep-dive if needed.** If `.deep-dive/` is missing or incomplete, prints the status message *"No deep-dive output found at `.deep-dive/`. Launching `/deep-dive-analysis:deep-dive-analysis` first. This may take several minutes on a large codebase."* then invokes `/deep-dive-analysis:deep-dive-analysis` automatically without a confirmation prompt. If deep-dive fails, aborts with the path of the deep-dive log.

   Under `--diff` this step is skipped. Diff mode consumes only `01-structure.md` and `02-interfaces.md`, uses whatever is already on disk, and runs on `Glob` plus `Grep` alone when nothing is. Launching a full deep-dive to review a handful of changed files is not worth the wait.

4. **Resolves the diff (`--diff` only).** Runs `git diff --name-only <base-ref>...HEAD` plus `git diff --name-only` for uncommitted work, and passes the union as `changed_files`. Aborts with a clear message when the path is not a git repository.

5. **Spawns the `abstraction-architect` agent** via the `Agent` tool, passing the codebase path, the mode, the deep-dive path when present, `changed_files` under `--diff`, and the parsed scope / severity-floor / focus flags.

6. **The agent writes the report** to `<path>/.abstraction-architect/findings.md`, or `findings-diff.md` under `--diff`.

7. **Prints to the user:**
   - The absolute path of the report.
   - Summary counts: total findings, high / medium / low breakdown.
   - The top three high-severity findings as one-line previews.

The full report stays in the file so the user opens it deliberately.

## Output location

`<path>/.abstraction-architect/findings.md`, or `<path>/.abstraction-architect/findings-diff.md` under `--diff`.

The directory is created automatically if missing. Re-running the command overwrites the previous report.

## Prerequisites

- The `deep-dive-analysis` plugin must be installed (declared as a dependency in `marketplace.json`). `--diff` degrades gracefully without deep-dive output and reports the reduced confidence in its Gaps section.
- `--diff` requires the target path to be a git repository.
- For monorepos large enough to benefit from partitioned analysis, run `/agent-teams:team-deep-dive` first to produce `08-interconnect-map.md`; the auditor will then include bounded-context fusion findings.

## Related commands

- `/deep-dive-analysis:deep-dive-analysis` — produces the `.deep-dive/` input this command consumes. Auto-launched by this command when missing.
- `/agent-teams:team-deep-dive` — partitioned deep-dive for monorepos; adds `08-interconnect-map.md` to the output.
- `/senior-review:code-review` and `/agent-teams:team-review` — both run this agent in diff mode as their abstraction dimension, so a review already answers the "was this already available?" question for the changed code. Use `--diff` here when you want that check on its own, without the rest of the review.
- `/clean-code:clean-code` — style and readability cleanup. Different concern.

## Out of scope

This command does not produce a refactoring plan. The `suggested direction` field in each finding names the target layer or refactoring move in one sentence. A future `/abstraction-architect:plan-refactor <finding-id>` command will turn a finding into a step-by-step plan.
