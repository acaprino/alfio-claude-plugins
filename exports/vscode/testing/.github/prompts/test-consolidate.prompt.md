---
description: Consolidate one module's redundant tests: inventory the BEHAVIORS its tests cover, get the keep/delete lists approved, rewrite one test file per source file, delete the originals in the same commit, and verify coverage did not drop. Also processes the module's quarantine backlog. Use when the user asks to consolidate, dedupe, or rewrite the tests of a module, or to process quarantined tests for code being touched. Not for measuring whole-suite health or quarantining (use /test-audit) or writing tests for untested code (use the test-writer agent).
argument-hint: <module-path> [--runner <cmd>] [--coverage-cmd <cmd>] [--dry-run]
---

<!-- Adapted from plugins/testing/commands/test-consolidate.md in acaprino/claude-code-daodan, MIT. -->

# /test-consolidate

Per-module test consolidation: the surgical half of the remediation ladder. Turns N overlapping, contradictory, implementation-coupled test files into one clean file per source file without losing a single behavior that mattered. The behavior inventory comes FIRST and gets approved BEFORE any rewrite; skipping that inventory is how consolidations silently lose the six edge cases the ugly tests existed for.

## Arguments

- `<module-path>` (required): the source module whose tests get consolidated.
- `--runner <cmd>` (optional): run command override when detection would pick wrong.
- `--coverage-cmd <cmd>` (optional): coverage command override for the baseline and the verification gate.
- `--dry-run` (optional): stop after the behavior inventory (Step 2). No writes, no deletions.

## Step 1: Preconditions and baseline

1. Consult the `test-hygiene` skill; its `references/remediation-workflow.md` section 3 defines this workflow's contract.
2. Verify a git repository with a clean working tree; halt otherwise.
3. Resolve the test set: every test file resolving to `<module-path>` (imports plus naming convention), wherever it lives, INCLUDING matching entries under `tests/_quarantine/` and their ledger rows.
4. Detect the runner (`--runner` overrides); run the module's tests for a baseline (pass/fail per test). When part of the test set cannot execute locally (missing services, containers, or credentials), say so explicitly, take the baseline for that part from the latest green CI run on the current branch, and record that the Step 7 gate for those tests moves to CI.
5. Record the module's coverage baseline (`--coverage-cmd` or the playbook's per-runner command). No coverage tooling configured: state explicitly that the verification gate degrades from "coverage must not drop" to "count of distinct behaviors must not drop", and require the user to acknowledge before proceeding.

## Step 2: Behavior inventory (always, before any code)

Read every test in scope and produce the inventory table. Behaviors, not tests: 40 tests commonly reduce to 9 behaviors.

| Behavior | file:line | Duplicate of | Value (high/low/none) | Reason |
|---|---|---|---|---|

Flag separately, each with evidence:

- **Contradictory pairs**: tests asserting incompatible outcomes for the same input/state.
- **Implementation-coupled**: internal mocks, call-echo asserts, private access.
- **Never-failing**: no asserts, tautologies, everything mocked.
- **Quarantined entries** for this module, each with a keep (behavior worth preserving in the rewrite) or drop proposal.

Under `--dry-run`, print the inventory and stop.

## Step 3: Safety-net check

Ask the user whether the module sits on a critical business flow. If yes and no e2e test covers that flow (search the e2e layer), propose writing 1 to 3 e2e tests FIRST and pause consolidation until they pass. Keep them few and flow-shaped, following the project's e2e conventions (the dedicated E2E-patterns knowledge base is an upstream Claude Code plugin not ported to this catalog). The safety net is what makes the deletions in Step 6 safe to approve.

## Step 4: Approval gate

Present the inventory via `#vscode/askQuestions`, grouped per source file: the keep-list (behaviors the rewrite will cover) and the delete-list (duplicates, never-failing, dropped quarantine entries). Unanswered rows default to KEEP. No flag bypasses this gate. Contradictory pairs need an explicit ruling: which behavior is the correct one (check the production code and its documented contract before proposing).

## Step 5: Rewrite

One test file per source file in the module, at the correct layer and mirrored path, covering exactly the approved behaviors plus any evident gaps the user approved. Follow the prevention rules of the `test-hygiene` skill and write test content behavior-first, through public interfaces, per this bundle's `test-writer` discipline.

## Step 6: Delete originals, same commit

In the SAME commit as the rewrite: delete every original test file in scope, the approved quarantine entries, and their ledger rows. Commit message: `refactor(tests): consolidate <module>, <N> files -> <M> files`. A rewrite commit that leaves the originals alive creates exactly the duplication this workflow exists to remove.

## Step 7: Verify

Run the suite plus the coverage command. Gates:

1. The suite passes.
2. Module coverage is not below the Step 1 baseline (or, in degraded mode, every approved behavior has a covering test).

Tests that could not execute locally in Step 1 are gated on CI instead: push, watch the run, and treat a red lane as a failed gate.

A gate fails: roll the consolidation commit back, then report which behaviors lost coverage or which tests broke, with the inventory rows involved. The originals come back; nothing is lost. Pick the rollback by push state: `git reset --hard HEAD~1` while the commit exists only locally; `git revert` once it has been pushed, because rewriting history on a shared branch overwrites other sessions' pushes.

## Step 8: Report

- Before/after table: files, test cases, runtime, coverage.
- Behaviors dropped, each with the user's recorded reason from Step 4.
- Quarantine entries processed and entries remaining for other modules.
- Suggested next module by `/test-audit`'s latest remediation ranking, when a `TEST_AUDIT.md` exists.
