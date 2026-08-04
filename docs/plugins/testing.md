# Testing Plugin

> Test-suite hygiene and generation toolkit: binding rules for where tests go and when to create them, a whole-suite auditor, gated quarantine and consolidation workflows, and a behavior-driven test-writer.

## Required dependencies

Both are upstream plugins, delegated as of marketplace 18.0.0 (the local vendored copies of `tdd` and `e2e-testing-patterns` were removed):

```bash
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock

claude plugin marketplace add wshobson/agents
claude plugin install developer-essentials@claude-code-workflows
```

| Dependency | Provides | Referenced as |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | Language-agnostic TDD methodology (red-to-green workflow, behavior-first tests, mocking discipline) | `mattpocock-skills:tdd` |
| [wshobson/agents](https://github.com/wshobson/agents) | Playwright/Cypress E2E patterns (page objects, fixtures, waiting, network mocking, visual regression) | `developer-essentials:e2e-testing-patterns` |

Both upstreams are multi-skill bundles, so the install brings companion skills along.

## Agents

### `test-writer`

Generates focused, behavior-driven test suites or guides interactive TDD sessions. Works with any language and test framework.

| | |
|---|---|
| **Model** | inherit |
| **Use for** | Writing tests for existing code, TDD for new features |
| **Modes** | Generate (write complete test suite) or Interactive TDD (guide red-green-refactor cycle) |

Since plugin 2.0.0 it is bound by the test-hygiene search-before-write protocol: before creating any test file it locates the existing test file for the target source file and extends it. Parallel test files, skip markers to get green, and softened assertions are explicit anti-patterns.

### `test-suite-auditor`

Adversarial whole-suite hygiene auditor. Report-only: it never edits, moves, or deletes.

| | |
|---|---|
| **Model** | inherit |
| **Use for** | Test-suite audits, flaky/dead test detection, redundancy and layer assessment |
| **Wired into** | `/testing:test-audit`, and senior-review's testing-quality dimension (`/senior-review:team-review`, `/senior-review:code-review` Agent F) when this plugin is installed |

Nine detection dimensions: inventory and layer distribution, orphan tests, skipped and disabled, failing and flaky, duplicate coverage, contradictory tests, implementation-coupled tests, never-failing tests, runtime and coverage distribution. Every finding carries evidence (`file:line` or command output) and a fix path pointing at the quarantine or consolidation workflow.

---

## Skills

### `test-hygiene`

The plugin's knowledge base: why suites degrade under agentic coding, the 7 binding rules, the remediation ladder, and the layer model with runtime budgets.

| | |
|---|---|
| **Trigger** | Creating or placing test files, auditing suite health, quarantining, consolidating |

**Reference docs included:**

| Reference | Content |
|-----------|---------|
| `prevention-rules.md` | The full ruleset: search-before-write protocol, mirror-the-source placement, one file per source, layers with budgets, behavior over implementation, no skip markers, assertion integrity, delete with the feature |
| `remediation-workflow.md` | TEST_AUDIT.md format, quarantine protocol and lifecycle, per-module consolidation, safety-net e2e tests, mutation-testing guidance (weekly job, no runner shipped) |
| `runner-playbook.md` | Per-runner detection and measurement commands (pytest, Vitest, Jest, Mocha, go test, cargo test, JUnit, dotnet, RSpec, PHPUnit) plus flaky-detection methods |

---

## Commands

### `/testing:test-audit`

Whole-suite health audit producing a versioned `TEST_AUDIT.md` (counts, runtime, skipped, failing, flaky, orphans, layer distribution, slowest tests, per-module coverage, with deltas per run). With `--fix`, quarantines accepted categories into `tests/_quarantine/` (excluded from CI, ledger per file, one commit per category, suite gate between batches, hard restore on failure). The category acceptance gate is never bypassed by any flag.

```
/testing:test-audit [path] [--fix] [--yes] [--no-run] [--runner <cmd>] [--scope <subpath>]
```

### `/testing:test-consolidate`

Per-module consolidation: inventories the BEHAVIORS the module's tests cover (table with duplicates, contradictions, implementation-coupling, never-failing flags), gets keep/delete lists approved, rewrites one test file per source file, deletes the originals in the same commit, and verifies module coverage did not drop (revert on failure). Also processes the module's quarantine backlog.

```
/testing:test-consolidate <module-path> [--runner <cmd>] [--coverage-cmd <cmd>] [--dry-run]
```

---

**Related:** [python-development](python-development.md) (Python-specific TDD with pytest) | [senior-review](senior-review.md) (spawns `test-suite-auditor` as its testing dimension when this plugin is installed, generic fallback otherwise) | [project-setup](project-setup.md) (injects the condensed Test-Suite Rules block into target projects' CLAUDE.md)
