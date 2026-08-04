# Prevention Rules

The full protocol behind each binding rule in SKILL.md. These rules are written for the agent creating tests, and every one of them is checkable at review time.

## 1. Search before writing (the protocol)

Before creating ANY test file, run this sequence and act on the first hit:

1. **Derive the expected test path** from the source path using the project's convention (see rule 2). If a file exists there, extend it. Done.
2. **Glob for name variants** of the target source file `<name>` across the test tree: `test_<name>*`, `<name>.test.*`, `<name>.spec.*`, `<name>_test.*`.
3. **Grep the test tree for imports** of the target module (its module path, not just the basename) to catch tests that cover it from a misplaced file.
4. **Zero hits on all three** is the only situation in which creating a new test file is legitimate. State the evidence when creating it: what was searched, what was found.

Preference order when a hit exists:

1. Add a case to an existing test group (describe block, test class, parametrize list) covering the same behavior area.
2. Add a new test group to the existing file for the module.
3. Create a new file ONLY when the module has no tests anywhere.

Creating `test_foo_extra.py` next to `test_foo.py` is never acceptable. If the existing file is misplaced relative to the convention, move it as part of the same change instead of forking it.

## 2. Mirror-the-source placement

One deterministic location per source file. If there is exactly one plausible place where a test can live, the agent finds it with a single Glob instead of a semantic search that fails.

| Ecosystem | Source | Test |
|---|---|---|
| Python | `src/pkg/auth/login.py` | `tests/unit/pkg/auth/test_login.py` |
| JS/TS (separate tree) | `src/auth/login.ts` | `tests/unit/auth/login.test.ts` |
| JS/TS (colocated) | `src/auth/login.ts` | `src/auth/login.test.ts` |
| Go | `pkg/auth/login.go` | `pkg/auth/login_test.go` (same package) |
| Rust | `src/auth/login.rs` | Inline `#[cfg(test)]` module; `tests/` only for integration |
| JVM | `src/main/java/x/y/Z.java` | `src/test/java/x/y/ZTest.java` |

The project's established convention wins over this table. What is non-negotiable is that the convention is deterministic and that there is one location per source file.

## 3. One test file per source file

And the inverse: a test file covers exactly one source file. Shared setup goes in fixture files (`conftest.py`, `fixtures.ts`, test helpers), never in a grab-bag test file that covers "miscellaneous" behavior. Grab-bag files are where duplicates hide, because no search for a specific module ever surfaces them.

## 4. Explicit layers with budgets

Directory structure separates `unit`, `integration`, and `e2e` (or the project's equivalents). Assignment rule: a new test goes in the LOWEST layer that can express the behavior. Consequences:

- A "unit" test that needs a real database, network, or filesystem is an integration test in the wrong directory. Move it; do not mock the database to keep it in unit.
- The same behavior is verified at ONE layer. Testing a validation rule in a unit test, again through the API in an integration test, and again through the UI in an e2e test is the most toxic duplication a suite can carry, because one behavior change breaks three tests in three places.
- Budgets (SKILL.md table) are project-tunable defaults. A layer over budget is an audit finding, not background noise.

## 5. Behavior, not implementation

The full treatment lives in the `mattpocock-skills:tdd` skill (behavior-first design, what to mock and what never to mock). The binding consequences enforced here:

- Do not mock modules internal to the project. Needing to is a design signal, not a testing technique.
- Do not test private functions, private attributes, or call sequences (`toHaveBeenCalledWith` chains that restate the implementation line by line).
- A behavior-preserving refactor must leave every test green. A test that breaks on a pure refactor is implementation-coupled and gets rewritten against the public behavior, not patched to track the new internals.

## 6. No skip markers to get green

| Ecosystem | Markers |
|---|---|
| pytest | `@pytest.mark.skip`, `@pytest.mark.xfail`, commented-out test bodies |
| Jest/Vitest/Mocha | `.skip`, `.only` left behind, `xit`, `xdescribe` |
| JUnit | `@Disabled`, `@Ignore` |
| Go | `t.Skip` outside platform guards |
| Rust | `#[ignore]` |
| .NET | `[Skip]`, `Skip = "..."` |

A skipped test is a lie in both directions: it looks like coverage in the file listing and like health in the CI output. The only sanctioned alternative to fixing a broken test immediately is quarantine (see `remediation-workflow.md`): the file moves to `tests/_quarantine/` with a ledger entry stating why and when. `.only` markers are worse than skips (they silently disable the rest of the file) and are always a defect.

## 7. Never weaken an assertion

Widening a numeric tolerance, replacing an equality with a truthiness check, deleting an assert, or wrapping one in a try/except to make CI pass is falsifying the safety net. When a test fails after a change, there are exactly three honest moves:

1. **The code is wrong**: fix the code.
2. **The test's expectation is outdated**: change the assertion AND say so explicitly in the commit message, with the reason the old expectation no longer holds.
3. **Unclear which**: quarantine the test with the question recorded in the ledger, and keep the change that triggered it under review.

Evaluate whether the test is obsolete BEFORE adapting the code to satisfy it. Silently adapting either side is how contradictory tests are born.

## 8. Delete tests with the feature

When a feature, endpoint, flag, or module is removed, its tests are removed in the same commit. Tests for deleted code do not fail; they keep passing against mocks of things that no longer exist, which is why orphan detection needs an audit (dimension D2 of the test-suite-auditor) instead of CI. Deleting them at removal time costs one Grep; finding them six months later costs an investigation.
