---
description: >
  Tidy the workspace: filesystem garbage, generated artifacts tracked in git, `.gitignore` gaps
  and stale rules, scratch directories, orphan doc-assets, and git auxiliary state. Detects by
  default; applies with --fix or --commit. Use when cleaning up a repository, removing committed
  build output, fixing or auditing `.gitignore`, clearing scratch and pipeline-output
  directories, or listing stale stashes, orphan worktrees and gone-upstream branches. Not for
  targets needing source comprehension (dead code, unused exports, unused dependencies, orphan
  application assets), which /code-review in the `_pipelines` bundle covers, and not for test
  files, which /test-consolidate in the `testing` bundle covers.
argument-hint: "[path] [--fix] [--commit] [--phases=garbage,gitignore,scratch,git-state]"
---

# Tidy

Detect and, on request, apply the workspace-hygiene fixes that the filesystem and git
can decide without reading a line of source. Everything that needs to know what a
symbol means belongs to `/code-review` in the `_pipelines` bundle, and this command never reaches
for it.

## Requirements

$ARGUMENTS

## Prime directives

1. **No build gate, and no pretending to need one.** Nothing this command applies can
   break a build, because nothing it applies is code. That is the reason the gate is
   absent, and it is also the boundary: the moment a proposed removal could change what
   the build sees, it is not this command's to make.
2. **Every mutation is reversible, or it is not made.** Tracked files go through git and
   git remembers them. Untracked files go to quarantine, never to `rm`. Git refs are not
   touched at all. See Phase 4.
3. **Detection is the default.** Without `--fix` or `--commit`, this command reports and
   changes nothing.
4. **Evidence before action.** Apply nothing whose finding does not quote the command
   output that produced it.

## Step 1: Scope and flags

Resolve the target path (default: repository root). Confirm it is inside a git working
tree; if it is not, say so and stop, since five of the seven checks are git queries.

| Flag | Contract |
|---|---|
| none | Detect and report. Nothing is modified. |
| `--fix` | Apply, leaving the working tree modified with no commits. The user reviews `git status` and commits. |
| `--commit` | Implies `--fix`, and adds one commit per phase. |
| `--phases=` | Restrict to the named phases. Default is all four. |

The two flags mean exactly what they mean in `/code-review` in the `_pipelines` bundle, so knowing
one command teaches the other.

## Step 2: Detect

Load the `repo-hygiene` skill and run its catalog at the **full** profile:
C1 filesystem garbage, C2 generated artifacts tracked in git, C3 `.gitignore`
completeness, C4 `.gitignore` archaeology, C5 scratch directories, C6 orphan
doc-assets, C7 git auxiliary state.

Two rules from the skill are the ones that get skipped under time pressure, and both
exist because being wrong is expensive:

- **C2**: a tracked build output may be published on purpose. Run the publication check
  before proposing to untrack anything.
- **C6**: a doc-asset with no literal Markdown link may still be reached from a config,
  a stylesheet, or a template. Run the widening search before calling it orphaned.

## Step 3: Report

Group findings by phase, ordered as the phases run. State the disposition and
confidence of each, and give the deliberately-kept list its own section: an artifact
cleared once should not be re-litigated by the next run.

Stop here unless `--fix` or `--commit` was given.

## Step 4: Apply

### Pre-flight

`--commit` requires a clean working tree, because its per-phase commits are its revert
mechanism and an unrelated modified file would be swept into one of them. If the tree
is dirty, name the dirty paths and stop.

`--fix` has no such requirement. It stages nothing and commits nothing, so an unrelated
change is never at risk. This is the mode for a user who wants the tidy without
interrupting whatever else is in flight, and it is the reason the clean-tree rule is
attached to `--commit` rather than to the command.

**Staging is always by explicit path.** Never `git add -A`, never `git add .`. Several
sessions can share a repository, and a blanket stage publishes someone else's
half-finished work.

### The four phases

Run only the phases the accepted findings require, in this order.

**1. `garbage`** (C1). Filesystem cruft and shell-redirection artifacts. Tracked files:
`git rm`. Untracked files: move to quarantine per the rule below. The safest phase in
the command, and the only one with no judgment in it.

**2. `gitignore`** (C2, C3, C4). Append missing patterns first, then handle tracked
matches. `git rm --cached` is applied **one item at a time, each confirmed**, and the
confirmation shows the publication check's result for that path. The asymmetry is
deliberate: appending a pattern is reversible by editing a line, while untracking a
file that a clean checkout needs produces a repository that builds locally and ships
broken. Regenerate `.gitignore` wholesale only if it was empty or clearly minimal;
otherwise append.

**3. `scratch`** (C5, C6). Scratch and pipeline-output directories, then orphan
doc-assets. Untracked and already ignored: quarantine, no commit. Tracked: `git rm -r`
plus an ignore entry. Orphan doc-assets require item-level approval, and the prompt
shows both searches that failed to find a reference, so the user is approving a real
absence rather than a Grep that was too narrow.

**4. `git-state`** (C7). **Detection-only. Nothing here is ever applied, at any flag.**

The reason is not caution, it is that the revert mechanism does not reach. Every other
phase mutates tracked content, so its commit records the change and reverting restores
it. Dropping a stash produces no diff for any commit to hold. Removing a worktree takes
its uncommitted files with it. Deleting a branch leaves the tip in a reflog that
expires. A per-phase commit cannot roll back a mutation that leaves no trace in the
tree, so this command does not make one. The findings carry `git stash drop`,
`git worktree remove`, and `git branch -d` for the user to run and own.

### Per phase, under `--commit`

1. Re-verify each candidate immediately before acting. A finding is a snapshot; the
   tree may have moved.
2. Apply in batches of five to twenty.
3. Stage by explicit path and commit: `chore(tidy): <phase> -- <count> items`.
4. Proceed to the next phase.

There is no build-and-test gate between phases. Adding one would be ceremony for
`garbage` and `scratch`, and for `gitignore` the protection that actually matters is
the per-item confirmation in the phase itself, not a test suite that passes because the
untracked files are still sitting on disk.

### Quarantine, for untracked removals

Untracked files are the one class git cannot restore, so they are never deleted:

```
.repo-hygiene/quarantine/<YYYY-MM-DD-HHMM>/<original relative path>
```

The run appends `.repo-hygiene/` to `.gitignore` if it is not already ignored, and
reports the quarantine path. The user deletes the directory when satisfied. This is
what makes `--fix` safe without commits: every operation it performs is undoable by
hand, including the ones git has no record of.

## Step 5: Report what happened

One row per phase: status, items, commit sha where one was made, and the quarantine
path if anything was moved. Then the `git-state` findings, unapplied by design, with
their commands.

Close with the alignment check: Grep the removed paths against `README.md`, `CLAUDE.md`,
and `docs/`, and propose an edit for any hit. A tidy that leaves the documentation
describing a deleted directory has moved the mess rather than cleared it.
