# Code-review fix loop (Step 7)

The complete `--fix` / `--commit` workflow for `/senior-review:code-review`:
severity acceptance, targeted fixes (7b), and the gated five-phase cleanup
removal (7c). Loaded on demand by the command when the fix loop is entered.

## Step 7: Fix Loop (if --fix, --commit, or verdict is "Ready with fixes")

After presenting the review (Step 5/6), offer an interactive fix cycle. Skip this step if the verdict is "Ready to merge" with no findings, or if the user didn't request fixes.

**The two flags are distinct contracts.** `--fix` means edit and verify: apply the fixes, run the tests, and leave the working tree modified with NO commits, so the user reviews and commits themselves. `--commit` implies `--fix` and adds the commits: one per fix or batch in 7b, one per phase in 7c. When the loop is entered via the verdict rather than a flag, ask which contract the user wants before touching anything.

The loop has two kinds of work: targeted fixes for review findings (7b) and bulk removal for codebase-hygiene findings (7c). The second is the only place in the marketplace that deletes application code at scale (bulk removal of test files belongs to the `testing` plugin's gated `/testing:test-consolidate` workflow), so it carries its own pre-flight, gates, and per-phase commits. **7c therefore requires `--commit`**: its per-phase commits are its revert mechanism (`git reset --hard HEAD~1` on a failed gate), and running it uncommitted would make a failed gate unrecoverable. Under plain `--fix`, skip 7c and say why: "cleanup phases need --commit (per-phase commits are the revert mechanism)". A review with no hygiene findings skips 7c entirely.

### 7a. Severity Acceptance

Present a single prompt listing all severity levels with findings. Use `AskUserQuestion` with `multiSelect: true`:

When Critical or High findings exist:
- [x] **Critical + High (Recommended)** -- N issues
- [ ] **Medium** -- N issues
- [ ] **Low** -- N issues

When only Medium/Low findings exist:
- [ ] **Medium** -- N issues
- [ ] **Low** -- N issues

Only include severity levels that have findings.

### 7b. Apply Fixes

For the selected severities, spawn one or more fix subagents:

```
Agent tool call:
  - description: "Fix [N] review findings"
  - subagent_type: "general-purpose"
  - prompt: |
    Fix the following code review findings. For each finding, apply the
    minimal correct fix. Run tests after fixing to verify no regressions.

    ## Findings to Fix
    [filtered findings at selected severities with file:line and suggested fix]

    ## Rules
    - Fix ONLY the listed findings, do not refactor surrounding code
    - Run existing tests after each fix
    - If a fix would require significant refactoring, note it and skip
    - {if --commit: Commit each fix or batch of related fixes | if --fix only:
      Do NOT commit anything; leave the working tree modified for the user}
```

Wait for all fixes to complete before proceeding.

### 7c. Cleanup Phases

Run this sub-step only when the accepted findings include codebase-hygiene items (dead code, orphan assets, generated artifacts tracked in VCS, unused or phantom deps, stale docs). Skip it entirely otherwise. This is the only place in the marketplace that performs bulk removal of application code (test-file bulk removal is owned by the `testing` plugin's gated `/testing:test-consolidate` workflow); detection lives in `senior-review:cleanup-auditor` and in Agent B2 above, and neither of them deletes anything.

#### Critical rules

These are non-negotiable. Removal at this scale is safe only because of them.

1. **`--commit` required.** This sub-step never runs under plain `--fix` (see Step 7 intro): the per-phase commits below are the revert mechanism.
2. **Git pre-flight.** `git status` must be clean before the first phase. Warn and halt if the working tree has uncommitted changes. Fixes from 7b must already be committed.
3. **Phase isolation.** Each phase gets its own commit, never mixing categories, so every step is independently revertible.
4. **Gate after every phase.** The project build must pass and tests must not regress against the baseline recorded before the first phase. On either failure, `git reset --hard HEAD~1` and halt.
5. **Grep-before-delete.** For every asset, export, or dependency candidate, run a final confirmation Grep and proceed only on zero results. Skip any item with matches and log it separately.
6. **Never remove what is used through side effects.** Dynamic imports, decorators, framework conventions (Next.js `pages/` and `app/`, Django views, pytest fixtures), and module augmentation in `*.d.ts` with `declare module`.
7. **Python functions and classes require explicit approval.** vulture's false-positive rate is high; present them separately and wait for user confirmation.

#### Baseline

Before the first phase, record the starting commit (`git rev-parse HEAD`), run the build, and run the test suite to capture pass and fail counts. Resolve `BUILD_CMD` and `TEST_CMD` from the project (`package.json` scripts, `pyproject.toml`, or the project equivalent), preferring unit tests over e2e. If the baseline build or tests already fail, halt: the branch must be stable before subtraction.

#### Phase order

Lowest risk first, stopping at the first gate failure. Run only the phases the accepted findings actually require.

1. `brand` -- rebrand residue. Requires the user to confirm the old brand name first.
2. `assets` -- orphan static files. Watch for dynamic references built from template literals, so Grep partial basenames too. For eager `import.meta.glob` bloat, switch to `{ eager: false }` with lazy resolution rather than removing the glob, unless every file in it is provably unused; removing the glob needs user sign-off.
3. `deps` -- unused and phantom dependencies. Move phantom deps to the correct workspace's manifest instead of deleting them unless confirmed unused everywhere. Re-install after editing and commit the manifest together with the lockfile. Never touch implicitly-used devDependencies (`prettier`, `eslint`, `typescript`, `@types/*` matching runtime deps) without grepping config files first.
4. `exports` -- dead exports, types, files, and unused Python symbols, in ascending risk order: ruff `F401` and `F841` auto-fix, then Knip unused exports and types verified by Grep across all workspaces, then Knip unused files verified against dynamic require and framework-convention paths, then vulture functions and classes under rule 6.
5. `docs` -- stale documentation and historical artifacts. Last on purpose, so it also catches doc references made stale by the `exports` phase. Detection-only unless the user explicitly opts into removal.

#### Per-phase template

For every phase `P`:

- **P.1 Confirm zero references.** Grep each candidate across source and docs, excluding the file being removed. Skip anything with a match.
- **P.2 Apply removals in batches** of 5 to 20 items. Delete files or edit export lines for code, `git rm` for assets, `git rm --cached` for generated artifacts, manifest edit plus re-install for deps, append for `.gitignore`.
- **P.3 Gate.** Run `BUILD_CMD` then `TEST_CMD`. On failure, `git reset --hard HEAD~1`, report which phase failed, and halt.
- **P.4 Commit.** One commit per phase: `chore(cleanup): <phase> -- <count> items removed`, with a short summary of what went in the body.
- **P.5 Proceed** to the next phase, or halt if the gate failed.

#### The docs phase

Highest false-positive rate of the five, so removal is opt-in and gated per item.

- Without an explicit opt-in, output the categorized report and stop.
- Plans, ADRs, and archive folders need per-item confirmation. A stale plan is indistinguishable from an active one to a tool. Show path, last-modified date, checklist completion percentage, and the first few lines of the body.
- Stale doc references are edits, not deletions. Rewrite the paragraph or strike the bullet; never delete a whole document over one stale link. If a document ends up effectively empty, propose its deletion as a separate confirmed item.
- Orphan doc-assets follow the same Grep-before-delete rule, searching only `*.md`, `*.mdx`, `*.rst`, `*.adoc`. Watch for inline base64 images that reference no filename.
- ADRs are historical record. The default action for `Status: Superseded` is to move them under a `superseded/` subfolder, not to delete them.

#### Cleanup report

After the last phase, or at the first gate failure, present one row per phase with status, items removed, and the commit sha, plus the before-and-after test counts and the reverted phase if any. Then run the alignment check: Grep the removed symbols, paths, and dependency names against `CLAUDE.md` and propose updates for any hit, since a cleanup that leaves the project instructions describing deleted code has only moved the problem.

Four phase names that used to live here now belong to `/repo-hygiene:tidy`: `garbage`, `gitignore`, `scratch` and `git-state`. They left because the filesystem and git decide them without reading a symbol, so the build-and-test gate below protects nothing there. A hygiene finding naming one of those is not this loop's to apply.

This step is pure subtraction. It does not refactor architecture, does not touch test files unless they reference removed symbols, and does not run a bundle analyzer.

### 7d. Re-review Offer

After fixes land, present:
- **Run another review round (Recommended)** -- verify fixes and check for new issues
- **Proceed without re-review**

If another round: run the full Step 1-7 flow again (fresh agents, fresh scope).

### 7e. Post-fix Options

After the fix-review cycle completes (clean verdict or user chose to stop):

**On a feature branch:**
- **Create a PR (Recommended)** -- push and open via `gh pr create`
- **Continue without PR**

**On main/master:**
- **Continue**

$ARGUMENTS

