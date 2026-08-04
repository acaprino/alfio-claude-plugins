<!-- Vendored from plugins/testing/skills/test-hygiene/references/remediation-workflow.md in acaprino/claude-code-daodan, MIT. -->

# Remediation Workflow

Mechanics for bonifying an already-degraded suite. The ladder is: measure, quarantine, consolidate, verify. Never "grand refactor of the suite": that loses the real coverage buried in the mess and blocks development for weeks. Remediation runs opportunistically, per module, alongside normal work.

## 1. Measure first: the TEST_AUDIT.md contract

`/test-audit` maintains a `TEST_AUDIT.md` at the audited root. Format:

- Each run PREPENDS a `## Audit <ISO date>` section, newest first, so the file reads as its own history in addition to git's.
- The section carries a metrics table with a delta column against the previous audit section when one exists:

| Metric | Value | Delta |
|---|---|---|
| Test files | | |
| Test cases | | |
| Total runtime | | |
| Skipped/disabled | | |
| Failing | | |
| Flaky (rerun disagreement) | | |
| Orphan test files | | |
| Layer distribution (unit/integration/e2e) | | |
| Top-10 slowest (list) | | |
| Per-module coverage (when tooling exists) | | |

- Below the table: the audit findings summary (by severity, with file:line evidence) and the recommended remediation order.
- The file is versioned in git and committed with the audit. It is the map and the progress ledger of the bonification.

## 2. Quarantine protocol

Quarantine is the move that makes everything else possible: it turns the suite green and trustworthy in a day without deleting anything. From that moment a CI failure is a signal again, not background noise.

**Layout.** `tests/_quarantine/` mirrors the original relative paths: `tests/unit/auth/test_login.py` moves to `tests/_quarantine/unit/auth/test_login.py`. No renames, so provenance stays searchable.

**Ledger.** `tests/_quarantine/README.md` holds one row per quarantined file:

| Original path | Date | Category | Reason | Evidence |
|---|---|---|---|---|

Categories: `orphan` (source deleted), `failing` (red on current main), `flaky` (rerun disagreement), `skipped` (skip marker older than 30 days). Evidence is a command output line or CI link, not an opinion.

**CI exclusion**, once, in the runner config:

| Runner | Exclusion |
|---|---|
| pytest | `norecursedirs = tests/_quarantine` (or `--ignore=tests/_quarantine`) |
| Vitest | `exclude: ['tests/_quarantine/**']` |
| Jest | `testPathIgnorePatterns: ['<rootDir>/tests/_quarantine/']` |
| Go | Quarantine dir outside the module's package tree, or a `//go:build quarantine` tag |
| Cargo | Move out of `tests/`; ignored files in `src` are not collected |
| JUnit | Exclude the quarantine source set in the build file |

**Lifecycle.** Two rules, both firm:

1. An entry is processed (rewritten into the consolidated file or deleted) only when its module is next touched. Nobody "works through the quarantine" as a standalone project.
2. An entry older than 3 months is deleted without discussion. Three months of nobody needing it is the evidence it was dead.

## 3. Per-module consolidation

Executed by `/test-consolidate <module>`. The order of operations is the whole point; skipping the inventory is how consolidations silently lose the six edge cases that were the only reason the ugly tests existed.

1. **Collect** every test touching the module, wherever it lives, including quarantine entries.
2. **Inventory behaviors, not tests.** Produce the table before writing any code:

   | Behavior | file:line | Duplicate of | Value | Reason |
   |---|---|---|---|---|

   Value is `high`, `low`, or `none`. Flag separately: tests contradicting each other, tests asserting implementation details, tests that cannot fail (no asserts, tautologies, everything mocked).
3. **Approve.** The keep-list and delete-list are explicit and user-approved. Unanswered rows default to keep.
4. **Rewrite** one test file per source file, covering the approved behaviors plus evident gaps, at the correct layer, following the prevention rules.
5. **Delete the originals in the same commit** as the rewrite, including processed quarantine entries and their ledger rows.
6. **Verify**: the module's coverage must not drop below the pre-consolidation baseline. On a drop, revert the commit and report which behaviors lost coverage. Where no coverage tooling exists, the gate degrades to "count of distinct behaviors covered must not drop", stated explicitly.

## 4. Safety net before mass pruning

When confidence in the real coverage is low, add 5-15 e2e tests over the critical business flows BEFORE any large deletion. They are the guarantee that pruning breaks nothing visible, and they unblock deletion decisions psychologically. The dedicated E2E-patterns knowledge base is an upstream Claude Code plugin not ported to this catalog; follow the project's established e2e conventions and keep the tests few and flow-shaped.

## 5. Mutation testing (guidance only)

Mutation testing is the only tool that objectively identifies tests that test nothing: it mutates the code and reports which tests still pass. Configuration guidance, not a shipped runner:

| Stack | Tool |
|---|---|
| JS/TS | Stryker |
| Python | mutmut |
| JVM | PIT |
| Rust | cargo-mutants |
| .NET | Stryker.NET |

Run it as a weekly CI job, never per-commit (CI time cost). Feed surviving mutants into the next audit's D8 dimension (never-failing tests) so pruning decisions rest on data. On a still-dirty suite, mutation results are too noisy to act on; run the quarantine phase first.
