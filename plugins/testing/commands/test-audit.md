---
description: >
  Measure test-suite health into a versioned TEST_AUDIT.md (counts, runtime, skipped, failing,
  flaky, orphans, layers, coverage) and optionally quarantine the rot with --fix.
  TRIGGER WHEN: the user asks to audit the test suite, measure test health, find dead or flaky
  or redundant tests, or quarantine failing tests to get CI trustworthy again.
  DO NOT TRIGGER WHEN: consolidating one module's tests (use /testing:test-consolidate), or
  writing new tests (use the test-writer agent).
argument-hint: "[path] [--fix] [--yes] [--no-run] [--runner <cmd>] [--scope <subpath>]"
---

# /testing:test-audit

Whole-suite health audit. Produces a versioned `TEST_AUDIT.md` at the target root; with `--fix`, moves the confirmed rot (orphan, long-skipped, failing, flaky tests) into `tests/_quarantine/` in gated, individually revertible commits. Measurement and quarantine only: consolidation is `/testing:test-consolidate`.

## Usage

```
/testing:test-audit                       # measure and report
/testing:test-audit src/backend           # audit a subtree's suite
/testing:test-audit --no-run              # static audit only, reuse CI/last-run data
/testing:test-audit --runner "pnpm vitest run"   # override runner detection
/testing:test-audit --fix                 # measure, then quarantine accepted categories
/testing:test-audit --fix --yes           # same, skipping per-batch re-confirmation
```

## Arguments

- `[path]` (optional): audit root. Default: current working directory.
- `--fix` (optional): after the audit, run the quarantine workflow (Step 5). Requires a git repository with a clean working tree.
- `--yes` (optional): under `--fix`, skip the per-batch file-list re-confirmation. The category acceptance gate of Step 5a is NEVER skipped, by any flag.
- `--no-run` (optional): never execute the suite. Metrics that need a run are reused from CI history (`gh run list` when available) or the newest local report files, and marked `stale` in the output.
- `--runner <cmd>` (optional): full run command override when detection would pick wrong (monorepos with several runners).
- `--scope <subpath>` (optional): restrict dimensions D2 to D8 to tests owned by the subpath; D1/D9 statistics stay suite-wide for context.

## Step 0: Pre-flight

1. Load the `test-hygiene` skill of this plugin. Its `references/runner-playbook.md` drives Steps 1 and 2; its `references/remediation-workflow.md` defines the `TEST_AUDIT.md` format and the quarantine protocol used below.
2. Under `--fix`: verify the target is a git repository (`git rev-parse --git-dir`) with a clean working tree (`git status --porcelain` empty). Dirty or not a repo: halt with the reason. Uncommitted work and quarantine moves must never share a commit.

## Step 1: Runner detection

Detect the runner(s) per the playbook's detection table; `--runner` overrides. Multiple stacks detected: audit each, one section per runner. No runner detected: report "no test runner detected at <path>" with the signals checked, and stop.

## Step 2: Mechanical measurement

Collect via Bash, using the playbook's per-runner commands:

1. Test file list and per-layer counts (list-tests command; no execution).
2. Skip/disable marker counts (grep table from the skill's `prevention-rules.md` section 6).
3. Unless `--no-run`: one timed full run (pass/fail/skip counts, total runtime, top-10 slowest), plus 2 to 4 reruns of the failing set for flaky classification, plus per-module coverage when tooling is configured.
4. Under `--no-run`: pull the same numbers from CI (`gh run list` / `gh api`) or the newest local report artifacts (junit XML, coverage files); mark every reused number `stale` with its source and date.

## Step 3: Qualitative audit (agent)

Spawn this plugin's `test-suite-auditor` agent with: the target path, the Step 2 metrics, the scope, run permission (`--no-run` propagates), and an output path of `<path>/.test-audit/findings.md`. The agent covers the judgment dimensions (orphans, duplicates, contradictions, implementation-coupling, never-failing tests) and returns the findings report. It is report-only; nothing moves in this step.

## Step 4: Write TEST_AUDIT.md

Prepend a `## Audit <ISO date>` section to `<path>/TEST_AUDIT.md` (create the file when absent) in the format defined by `remediation-workflow.md` section 1: the metrics table with deltas against the previous audit section, then the findings summary by severity from Step 3, then the recommended remediation order.

Without `--fix`, print the report path, the metrics table, and the top findings, and stop here.

## Step 5: Quarantine (only with `--fix`)

Follows the gated shape of `/senior-review:code-review --fix` Step 7: acceptance gate, baseline, one commit per batch, verification gate between batches, hard revert on failure.

### 5a: Category acceptance gate

Build the four candidate batches from Steps 2 and 3, keeping only confirmed findings (never false-positive candidates):

- `orphan`: test files whose source is confirmed deleted
- `skipped`: skip markers older than 30 days
- `failing`: red on the current baseline run
- `flaky`: rerun or CI disagreement

Present the non-empty categories via `AskUserQuestion` with `multiSelect: true` (label: category and file count; description: sample paths). Only accepted categories proceed. This gate is never bypassed: `--yes` affects only the per-batch re-confirmation below.

### 5b: Baseline

Record the starting commit (`git rev-parse HEAD`) and the baseline suite result (pass count, fail count). Under `--no-run` the baseline is the newest CI result, recorded with its run id.

### 5c: Batch execution

Process accepted categories in fixed order, lowest ambiguity first: `orphan`, `skipped`, `failing`, `flaky`. Per batch:

1. Preview the exact file list and target paths (`tests/_quarantine/<original relative path>`). Confirm the batch unless `--yes`.
2. First batch only: add the runner's CI exclusion for `tests/_quarantine/` (playbook table) and create `tests/_quarantine/README.md` with the ledger header.
3. `git mv` each file to its mirrored quarantine path; append one ledger row per file (original path, date, category, reason, evidence).
4. Run the suite (or, under `--no-run`, the runner's collect-only check to prove nothing imports the moved files). Gate: the suite passes and the pass count does not drop below baseline minus the quarantined tests' own contribution.
5. Gate failed: restore with `git reset --hard HEAD` (safe: the pre-flight guaranteed a clean tree and every prior batch is already committed, so HEAD is exactly the pre-batch state) plus `git clean -fd tests/_quarantine` for the untracked ledger of a first batch, report the failing move, and halt the fix loop.
6. Gate passed: commit `chore(tests): quarantine <category>, <N> files`.

### 5d: Refresh the audit

Amend the current `## Audit <date>` section of `TEST_AUDIT.md` with the post-quarantine numbers (suite green or not, remaining counts) and include the update in the final batch's commit, or a trailing `chore(tests): refresh TEST_AUDIT.md after quarantine` commit when the last batch was already committed.

### 5e: Report

Per-batch table (category, files, commit sha, gate result), the new suite status, and next steps:

- `/testing:test-consolidate <module>` for the modules ranked worst by duplicate/implementation-coupling density in Step 3.
- The quarantine lifecycle reminder from the skill: entries are processed when their module is next touched; entries older than 3 months become deletion candidates, dropped only through the consolidation approval gate with evidence beyond age.

## Output locations

- `<path>/TEST_AUDIT.md`: the versioned audit ledger (committed).
- `<path>/.test-audit/findings.md`: the full auditor report backing the latest audit section.
- `tests/_quarantine/` plus its `README.md` ledger: only under `--fix`.
