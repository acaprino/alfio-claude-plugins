---
name: test-hygiene
description: >
  Test-suite hygiene: binding rules for WHERE tests go and WHEN to create them, plus the
  remediation ladder for suites that have already degraded (measure, quarantine, consolidate).
  Use when creating or placing any test file, deciding whether to extend an existing test or
  create a new one, auditing test-suite health, quarantining failing or flaky tests, or
  consolidating redundant tests.
  Not for writing the test content itself or browser E2E mechanics (those knowledge bases are
  upstream Claude Code plugins, not ported to this catalog), or Python pytest specifics (see
  the python-development bundle's python-tdd skill).
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: testing
---

<!-- Vendored from plugins/testing/skills/test-hygiene/ in acaprino/claude-code-daodan, MIT. -->

# Test-Suite Hygiene

Rules and workflows that keep a test suite small, trustworthy, and navigable while agents and humans keep adding to it.

## Why suites degrade under agentic coding

For an agent, writing a new test file costs nearly nothing; understanding the existing suite costs context. The dominant strategy becomes "create a new one", and the implicit goal is "task closed, CI green", never "suite healthy". Nobody measures suite health, so nobody optimizes it. The result compounds fast: parallel test files for the same module, the same behavior asserted at three layers, implementation-coupled tests that break on every refactor and get replaced instead of repaired, and skip markers that quietly turn the safety net into decoration. These rules exist to make the healthy move the cheap move.

## The binding rules

Full protocol with per-rule detail in `references/prevention-rules.md`. The condensed form:

1. **Search before writing.** Locate the existing test file for the target source file and extend it. Creating a parallel test file for an already-tested source file is forbidden.
2. **Deterministic ownership per layer.** Unit tests: one test file per source file, mirroring the source path (`src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following the project's established convention. Integration, contract, and e2e tests are behavior-owned: one file per behavioral scope (a flow, an endpoint, a contract), legitimately spanning several source modules. The violation at those layers is an unexplained second file for the same scope, not multi-module reach.
3. **Explicit layers** (unit, integration, e2e), each in its own directory with a runtime budget. A new test goes in the lowest layer that can express the behavior.
4. **Behavior, not implementation.** Test through public interfaces. A refactor that preserves behavior must not break tests.
5. **No skip markers to get green.** Fix the test, or quarantine it with a tracked reason.
6. **Never weaken an assertion** to make a failing test pass. A failing assertion is a signal about the code, not an obstacle in the test.
7. **Delete tests with the feature**, in the same commit.

## The remediation ladder

When the suite has already degraded, rules alone do not repair it. Bonify in layers, opportunistically, alongside normal development. Full mechanics in `references/remediation-workflow.md`.

1. **Measure first.** `/test-audit` produces a versioned `TEST_AUDIT.md`: counts, runtime, skipped, failing, flaky, orphans, layer distribution, slowest tests, per-module coverage. In a degraded suite, instinct misjudges what is dead; numbers do not.
2. **Quarantine, do not delete.** `/test-audit --fix` moves failing, flaky, orphan, and long-skipped tests to `tests/_quarantine/`, excluded from CI, each with a ledger entry. The suite turns green and trustworthy immediately; a failure becomes a signal again. Quarantined entries are processed only when their module is next touched; entries older than 3 months become deletion candidates, dropped only through the approval gate with evidence beyond age (feature removed, replacement coverage, temporary origin).
3. **Consolidate per module.** `/test-consolidate <module>` inventories the BEHAVIORS the module's tests cover (often 40 tests cover 9 behaviors), then rewrites one file per owner at the correct layer and deletes the originals in the same commit, with a coverage gate.
4. **Verify.** Coverage per module must not drop across a consolidation. A temporary drop in total coverage while pruning fake coverage is normal and desirable.

Order remediation by risk (production bugs, then churn from git log), not by how messy a module looks.

## Layer model and budgets

Defaults; a project's own convention overrides them.

| Layer | Contains | Budget (default) |
|---|---|---|
| `unit` | Pure logic, no I/O, no mocks of internal modules | Individual test under 100ms; whole layer under 60s |
| `integration` | Real boundaries (DB, HTTP, filesystem) via containers or fixtures | Whole layer under 5min |
| `e2e` | Critical user flows only | Roughly 20 tests per project; not a regression dumping ground |

A behavior's primary proof lives at ONE layer. Cross-layer overlap is duplication only when two tests protect substantially the same failure mode through the same observable contract without adding independent risk coverage; a calculation checked at unit, its persistence at integration, and the user flow at e2e are three behaviors, not one repeated. When a unit test needs a database, it is an integration test in the wrong directory; move it instead of mocking the database.

## Related knowledge

- Writing the test content (red-to-green workflow, behavior-first design, mocking discipline) and browser E2E patterns (page objects, fixtures, waiting, network mocking): those knowledge bases are upstream Claude Code plugins ([mattpocock/skills](https://github.com/mattpocock/skills) and [wshobson/agents](https://github.com/wshobson/agents)) and are not ported to this catalog. Rely on the binding rules here, the test-writer agent in this bundle, and the project's own conventions.
- Python pytest specifics (conftest architecture, coverage gates, pytest-randomly): the python-development bundle covers those in its python-tdd skill; read it when present, this file stays language-agnostic.
- Runner detection and measurement commands for the audit workflows: `references/runner-playbook.md`.
