# Runner Playbook

Detection signals and measurement commands per test runner. Used by `/testing:test-audit`, `/testing:test-consolidate`, and the test-suite-auditor. Every command here is read-only with respect to the code; commands that RUN the suite are marked, and the caller decides whether running is permitted (`--no-run`).

## Detection

Check in this order; the first match wins unless the project visibly uses several stacks (then report each).

| Runner | Detection signal |
|---|---|
| pytest | `pytest.ini`, `[tool.pytest.ini_options]` in `pyproject.toml`, `conftest.py`, `setup.cfg [tool:pytest]` |
| Vitest | `vitest.config.*`, `"vitest"` in package.json devDependencies |
| Jest | `jest.config.*`, `"jest"` key or devDependency in package.json |
| Mocha | `.mocharc.*`, `"mocha"` devDependency |
| go test | `go.mod` plus any `*_test.go` |
| cargo test | `Cargo.toml` plus `#[test]` or `tests/` dir |
| JUnit (Gradle) | `build.gradle(.kts)` with `test` task, `src/test/java` or `src/test/kotlin` |
| JUnit (Maven) | `pom.xml` with surefire, `src/test/java` |
| dotnet test | `*.csproj` with xunit/nunit/mstest package refs |
| RSpec | `.rspec`, `spec/` dir, `rspec` in Gemfile |
| PHPUnit | `phpunit.xml(.dist)`, `phpunit` in composer.json |

## Measurement commands

| Runner | List tests (no run) | Run with timing (RUNS) | Count skipped | Coverage (RUNS) |
|---|---|---|---|---|
| pytest | `pytest --collect-only -q` | `pytest -q --durations=20` | grep `skip\|xfail` markers; `pytest -rs` summary | `pytest --cov=<pkg> --cov-report=term-missing` (pytest-cov) |
| Vitest | `vitest list` | `vitest run --reporter=verbose` | grep `\.skip\|\.todo`; reporter summary | `vitest run --coverage` |
| Jest | `jest --listTests` | `jest --verbose` | grep `\.skip\|xit\|xdescribe`; reporter summary | `jest --coverage` |
| Mocha | `mocha --dry-run` (10+) | `mocha --reporter spec` | grep `\.skip`; pending count in output | via nyc: `nyc mocha` |
| go test | `go test -list '.*' ./...` | `go test -v ./...` (per-test timing in output) | grep `t\.Skip`; `--- SKIP` lines | `go test -coverprofile=cover.out ./...` then `go tool cover -func=cover.out` |
| cargo test | `cargo test -- --list` | `cargo test -- --nocapture` (use `cargo nextest run` for per-test timing when available) | grep `#\[ignore\]`; `ignored` count in output | `cargo llvm-cov` or `cargo tarpaulin` when configured |
| Gradle | `gradle test --dry-run` (approx) | `gradle test` then read `build/test-results/test/*.xml` (has per-test `time`) | `@Disabled\|@Ignore` grep; `skipped` attr in XML | JaCoCo report when the plugin is applied |
| Maven | n/a; read surefire reports after run | `mvn test` then `target/surefire-reports/*.xml` | `skipped` attr in XML | JaCoCo when configured |
| dotnet | `dotnet test --list-tests` | `dotnet test --logger "trx"` (per-test times in trx) | `Skip=` grep; `skipped` in summary | `dotnet test --collect:"XPlat Code Coverage"` |
| RSpec | `rspec --dry-run -f doc` | `rspec --profile 20` | grep `skip\|pending\|xit`; pending count | SimpleCov when configured |
| PHPUnit | `phpunit --list-tests` | `phpunit --log-junit report.xml` (per-test times) | `markTestSkipped` grep; summary | `phpunit --coverage-text` (xdebug/pcov) |

Notes:

- **Per-module coverage** means the report broken down by source path, not the aggregate percentage. pytest-cov `term-missing`, `go tool cover -func`, JaCoCo XML, and lcov reports all provide it; the aggregate number alone is not a usable audit metric.
- When a command above is missing from the project (no coverage plugin, no nextest), report the metric as "tooling absent" rather than improvising an install. Installing tooling is a user decision.

## Flaky detection

Flakiness is proven by disagreement between identical runs, never inferred from style alone.

1. Preferred: rerun the suite (or the suspect subset) 3-5 times and diff the outcomes. `pytest -p no:randomly --lf`, `vitest run --retry=0` repeated, `go test -count=5 ./pkg/...`, `cargo test` repeated.
2. Where CI history is accessible (`gh run list` / `gh api`), passes and failures of the same commit across attempts are equivalent evidence and cost no local runtime.
3. Static signatures justify SUSPICION only (report as candidates, not findings): real timestamps or `sleep` in tests, shared mutable module state, order-dependent fixtures, unmocked network calls, port or tmpdir collisions.
4. Randomized-order plugins (`pytest-randomly`, Jest `--randomize`) convert order-dependence into reproducible failures; note their absence in the audit when order-coupling is suspected.
