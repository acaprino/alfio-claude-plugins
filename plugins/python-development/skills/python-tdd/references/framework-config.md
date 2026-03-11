# Framework Configuration

Reference for pytest configuration, coverage tooling, markers, plugins, and CI/CD integration.

## pytest Configuration

### pyproject.toml (preferred)

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
```

### pytest.ini (alternative)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --strict-markers --tb=short --cov=src --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks integration tests
    unit: marks unit tests
    e2e: marks end-to-end tests
```

## Coverage Configuration

### pyproject.toml coverage settings

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__main__.py",
    "*/conftest.py",
]

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

[tool.coverage.html]
directory = "htmlcov"
```

### Threshold gates

- `fail_under = 80` - blocks test run if line coverage drops below 80%
- Combine with `--cov-fail-under=80` in addopts for CLI enforcement
- Use branch coverage (`branch = true`) to catch untested conditionals

## Markers

### Built-in useful markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `@pytest.mark.skip(reason="...")` | Unconditionally skip | Feature not ready |
| `@pytest.mark.skipif(condition)` | Skip on condition | OS-specific tests |
| `@pytest.mark.xfail(reason="...")` | Expected failure | Known bug |
| `@pytest.mark.parametrize` | Run with multiple inputs | Data-driven tests |

### Custom markers and running by marker

```bash
# Register in pyproject.toml (see above), then use:
pytest -m unit              # run only unit tests
pytest -m "not slow"        # skip slow tests
pytest -m "integration"     # run integration tests only
pytest -m "not e2e"         # exclude e2e tests
```

## Recommended Plugins

| Plugin | Purpose | Install |
|--------|---------|---------|
| `pytest-cov` | Coverage reporting | `pip install pytest-cov` |
| `pytest-asyncio` | Async test support | `pip install pytest-asyncio` |
| `pytest-mock` | Thin mock wrapper | `pip install pytest-mock` |
| `hypothesis` | Property-based testing | `pip install hypothesis` |
| `pytest-xdist` | Parallel test execution | `pip install pytest-xdist` |
| `pytest-randomly` | Randomize test order | `pip install pytest-randomly` |
| `pytest-timeout` | Per-test timeouts | `pip install pytest-timeout` |
| `pytest-sugar` | Better terminal output | `pip install pytest-sugar` |

Install all at once:

```bash
pip install pytest-cov pytest-asyncio pytest-mock hypothesis pytest-xdist pytest-randomly
# or with uv
uv add --dev pytest-cov pytest-asyncio pytest-mock hypothesis pytest-xdist pytest-randomly
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml --cov-fail-under=80

      - name: Upload coverage
        if: matrix.python-version == '3.12'
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### Coverage threshold enforcement

- **CI gate**: `--cov-fail-under=80` exits non-zero if coverage drops below threshold
- **pyproject.toml gate**: `fail_under = 80` under `[tool.coverage.report]`
- **PR checks**: Use codecov or coveralls to block merge if coverage decreases

### Metrics to track

| Metric | Target | Tool |
|--------|--------|------|
| Line coverage | >= 80% | pytest-cov, coverage.py |
| Branch coverage | >= 70% | coverage.py with `branch = true` |
| Coverage delta | No decrease | Codecov PR comments |
| Test execution time | < 5 min | CI timing, pytest-timeout |
| Flaky test count | 0 | pytest-randomly, CI history |

## Version Requirements

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.11+ | 3.12+ recommended for improved error messages |
| pytest | 8.0+ | Improved assertion introspection |
| pytest-cov | 5.0+ | Supports latest coverage.py |
| coverage.py | 7.0+ | Branch coverage improvements |
| pytest-asyncio | 0.23+ | Auto mode for async fixtures |
| hypothesis | 6.90+ | Python 3.12+ support |
| pytest-xdist | 3.5+ | Load balancing improvements |
