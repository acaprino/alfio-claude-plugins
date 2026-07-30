# Framework Configuration

pytest + coverage + plugins + CI integration. Most surface lives in pytest/coverage docs; this file is the recommended baseline shape and the threshold conventions.

## When to use

Setting up `pyproject.toml` for a new Python project's test suite, or auditing an existing test config for missing essentials (markers registered, branch coverage, fail-under threshold, parallel execution).

## Recommended `pyproject.toml` baseline

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
    "unit: marks unit tests",
    "e2e: marks end-to-end tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/migrations/*", "*/__main__.py", "*/conftest.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
skip_empty = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
    "@overload",
]
```

## Gotchas

- **`--strict-markers` is non-negotiable** -- without it, typos in `@pytest.mark.foo` silently pass instead of erroring. Every marker must be registered in `markers`.
- **`branch = true` matters more than line coverage.** Catches untested conditionals (the `if x:` where you never tested the false branch). Always set it.
- **`filterwarnings = ["error", ...]`** turns warnings into failures by default -- you opt back in for known noise. Without `error`, deprecation traps land in production.
- **Coverage gate is double-set on purpose**: `--cov-fail-under=80` in `addopts` AND `fail_under = 80` under `[tool.coverage.report]`. The first fails the pytest run, the second fails standalone `coverage report`.
- **`exclude_lines` for `if TYPE_CHECKING:` and `@overload`** -- otherwise import-time-only code shows as uncovered.
- **`ignore_errors` and `pragma: no cover` are easy to abuse** -- audit them periodically. They hide real coverage gaps.
- **`pytest-randomly`** is the cheapest way to catch hidden test interdependencies (tests passing only because of run order). Add it day one.
- **`pytest-asyncio` mode**: in `[tool.pytest.ini_options]` set `asyncio_mode = "auto"` if you want async test functions auto-detected; otherwise decorate with `@pytest.mark.asyncio`.

## Marker patterns

```bash
pytest -m unit                          # only unit tests
pytest -m "not slow"                    # skip slow
pytest -m integration                   # only integration
pytest -m "not e2e"                     # exclude e2e
pytest -k "test_login or test_signup"   # name-based selection (not marker)
```

## Plugin selector (the curated list)

| Plugin | Purpose |
|--------|---------|
| `pytest-cov` | Coverage reporting |
| `pytest-asyncio` | Async test support |
| `pytest-mock` | Thin `unittest.mock` wrapper with cleanup |
| `hypothesis` | Property-based testing |
| `pytest-xdist` | Parallel test execution (`-n auto`) |
| `pytest-randomly` | Randomize test order (catches order dependencies) |
| `pytest-timeout` | Per-test timeouts (kills hung tests in CI) |
| `pytest-sugar` | Better terminal output |

Install all: `uv add --dev pytest-cov pytest-asyncio pytest-mock hypothesis pytest-xdist pytest-randomly pytest-timeout`

## CI metrics worth tracking

| Metric | Target | Tool |
|--------|--------|------|
| Line coverage | >= 80% | pytest-cov + coverage.py |
| Branch coverage | >= 70% | coverage.py with `branch = true` |
| Coverage delta | No decrease | Codecov PR comments |
| Test execution time | < 5 min | `pytest --durations=10`, pytest-timeout |
| Flaky test count | 0 | pytest-randomly + CI history |

## Version floor

| Tool | Min | Notes |
|------|-----|-------|
| Python | 3.11+ | 3.12+ recommended for improved error messages |
| pytest | 8.0+ | Improved assertion introspection |
| pytest-cov | 5.0+ | Latest coverage.py support |
| coverage.py | 7.0+ | Branch coverage improvements |
| pytest-asyncio | 0.23+ | Auto mode |
| hypothesis | 6.90+ | Python 3.12+ support |
| pytest-xdist | 3.5+ | Load balancing |

## Official docs

- pytest config reference: https://docs.pytest.org/en/stable/reference/customize.html
- pytest markers: https://docs.pytest.org/en/stable/example/markers.html
- coverage.py config reference: https://coverage.readthedocs.io/en/latest/config.html
- coverage.py exclude_lines: https://coverage.readthedocs.io/en/latest/excluding.html
- pytest-cov: https://pytest-cov.readthedocs.io/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-xdist: https://pytest-xdist.readthedocs.io/
- pytest-randomly: https://github.com/pytest-dev/pytest-randomly
- hypothesis: https://hypothesis.readthedocs.io/
- Codecov: https://docs.codecov.com/

## Related

- `tdd-best-practices.md` -- the discipline this config supports
- `pytest-infrastructure.md` -- conftest patterns, fixture scoping, sys.modules race
- `python-comments` skill -- pairs well via the `D` ruff rule set for docstring coverage
