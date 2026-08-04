---
name: python-tdd
description: >
  Generate focused, behavior-driven Python tests using TDD methodology with pytest.
  TRIGGER WHEN: writing Python tests, improving coverage, reviewing test quality, or practicing red-green-refactor workflows with pytest.
  DO NOT TRIGGER WHEN: the target is non-Python (use mattpocock-skills:tdd for language-agnostic TDD or developer-essentials:e2e-testing-patterns for browser E2E; both are upstream plugins that the testing plugin declares as hard dependencies).
---

# Python Testing Patterns

Generate focused, behavior-driven tests with pytest. Prioritize observable behavior over implementation details. For framework configuration (pyproject.toml, plugins, CI), see `references/framework-config.md`. For deep conftest patterns and heavy-dep mocking, see `references/pytest-infrastructure.md`. For full TDD discipline, see `references/tdd-best-practices.md`.

## 1. Test Philosophy

### What to test
- Observable behavior and return values
- User-facing workflows and API contracts
- Edge cases and error handling at system boundaries
- State transitions and side effects
- Data validation and transformation rules

### What NOT to test
- Framework internals (pytest, SQLAlchemy, FastAPI mechanics)
- Implementation details (private methods, internal variable names)
- Third-party library behavior
- Simple utility functions with no branching logic
- That objects are truthy -- this asserts nothing useful

### Mocking strategy

**DO mock**: External API calls / HTTP requests, database queries in unit tests, file system operations, time-dependent behavior (`datetime.now`, `time.time`), environment variables.

**DON'T mock**: Your own models and dataclasses, simple utility functions, the function under test itself, framework features you rely on.

### Test count discipline

- Max **10 tests** per file for simple modules.
- Max **15 tests** per file for complex modules.
- More than that = the module is too complex; suggest splitting it.

## 2. TDD Workflow

### Red-Green-Refactor

1. **RED** -- write a failing test. Must fail for the right reason (NOT import error, NOT syntax error).
2. **GREEN** -- write the minimal code to make it pass. No more.
3. **REFACTOR** -- improve code while all tests stay green. No new behavior.

### Coverage targets

| Priority | What | Target |
|----------|------|--------|
| P0 | Critical paths (auth, payments, data integrity) | 100% line + branch |
| P1 | Core business logic + public API | 90%+ line |
| P2 | Utilities, helpers, config | 80%+ line |

Overall: 80%+ line coverage; 100% on critical paths.

## 3. Naming Convention (BDD)

**Class-based grouping** -- nest by feature, then scenario:

```python
class TestUserService:
    class TestCreateUser:
        def test_should_create_when_valid_data(self): ...
        def test_should_raise_when_email_exists(self): ...
```

**Flat function naming** -- `test_<action>_should_<outcome>_when_<condition>`:

```python
def test_create_user_should_succeed_when_valid_data(): ...
def test_login_should_fail_when_password_expired(): ...
```

## 4. AAA Structure (Arrange-Act-Assert)

```python
def test_transfer_should_debit_sender_when_sufficient_funds():
    # Arrange
    sender = make_account(balance=100)
    receiver = make_account(balance=50)

    # Act
    transfer(sender, receiver, amount=30)

    # Assert
    assert sender.balance == 70
    assert receiver.balance == 80
```

## 5. Reusable Fakes via Factory Fixtures

Prefer factory fixtures in `conftest.py` over raw dicts:

```python
# conftest.py
@pytest.fixture
def make_user():
    def _make_user(name="Test User", email="test@example.com", active=True):
        return User(name=name, email=email, active=active)
    return _make_user

def test_deactivate_user(make_user):
    user = make_user(active=True)
    user.deactivate()
    assert user.active is False
```

## 6. Core Patterns (the few worth memorizing)

### Fixtures -- narrowest scope possible

```python
@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="module")  # or scope="session" for engine
def api_client(): yield TestClient(app)
```

Share via `conftest.py` -- pytest auto-discovers.

### Parametrization with custom IDs

```python
@pytest.mark.parametrize("input_val,expected", [
    pytest.param("user@example.com", True, id="valid-email"),
    pytest.param("no-at-sign.com", False, id="missing-at"),
    pytest.param("", False, id="empty-string"),
])
def test_is_valid_email(input_val, expected):
    assert is_valid_email(input_val) == expected
```

### Mocking -- the only patterns you need

```python
@patch("myapp.services.requests.get")                      # patch where USED (top-level import)
def test_fetch_user(mock_get):
    mock_get.return_value.json.return_value = {"id": 1}
    result = fetch_user(1)
    mock_get.assert_called_once_with("https://api.example.com/users/1")

@patch("myapp.services.UserRepository", autospec=True)     # autospec catches signature drift
def test_repo_call(MockRepo): ...

@patch("myapp.client.requests.get", side_effect=ConnectionError("timeout"))
def test_network_error(mock_get):
    with pytest.raises(ServiceUnavailableError):
        fetch_data("https://api.example.com/data")
```

### The lazy-import gotcha (the rule that catches everyone)

When a function imports inside another function (lazy import), it is NOT a module-level attribute at the usage site. **Patch at the definition site, not the usage site.**

```python
# WRONG -- AttributeError: module has no attribute 'get_db'
monkeypatch.setattr("myapp.services.processor.get_db", mock_db)

# CORRECT -- patch where get_db is DEFINED
monkeypatch.setattr("myapp.database.get_db", mock_db)
```

Rule: if `monkeypatch.setattr` raises `AttributeError`, check whether the target is a lazy import. If so, patch the module where the function is defined.

### Async tests

```python
@pytest.mark.asyncio
async def test_async_fetch():
    result = await async_fetch("https://api.example.com")
    assert result["status"] == "ok"
```

Set `asyncio_mode = "auto"` in `pyproject.toml` to skip the `@pytest.mark.asyncio` decorator.

### Property-based with hypothesis

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=1000))
def test_deposit_increases_balance(amount):
    account = Account(balance=0)
    account.deposit(amount)
    assert account.balance == amount
```

### Temporary files / env

```python
def test_export(tmp_path):                             # auto-cleaned
    output = tmp_path / "report.csv"
    export_report(output, [{"name": "Alice"}])
    assert "Alice" in output.read_text()

def test_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    assert get_database_url() == "postgresql://localhost/test"
```

## 7. Anti-Patterns

| Anti-pattern | Why it's bad | Do this instead |
|--------------|--------------|-----------------|
| `assert obj is not None` alone | Asserts nothing about behavior | Assert on a specific attribute or return value |
| Mocking the function under test | Tests nothing real | Mock its dependencies instead |
| 40+ tests for a simple module | Sign of over-testing or bloated module | Split module or consolidate parametrized tests |
| Testing framework internals | Validates pytest/SQLAlchemy, not your code | Test your logic through public API |
| Copy-pasting mock setup in every test | Fragile, hard to maintain | Extract into fixtures or factory functions |
| Testing private methods directly | Couples tests to implementation | Test through the public interface |
| Catching exceptions inside test code | Swallows real failures silently | Use `pytest.raises` as context manager |
| No assertions in test body | Test always passes, proves nothing | Every test must assert something |
| Asserting on `mock.called` only | Doesn't verify correct arguments | Use `assert_called_once_with(expected_args)` |
| Hardcoded golden values (`== 660`) | Breaks when algorithm improves, not when behavior is wrong | Assert invariants, use `pytest.approx`, derive from inputs |
| Heavy mocks in sub-directory conftest | Root tests load real deps first; mocks too late | Place ALL heavy dependency mocks in root `tests/conftest.py` |
| Missing markers on heavy-dep tests | Tests break silently when deps are mocked by default | Mark `@pytest.mark.slow`, use `--strict-markers` |
| Incomplete external service mocking | One unmocked service hangs CI (e.g., `google.auth.default()`) | Audit ALL external calls before finalizing integration conftest |
| Patching lazy import at use site | Function not bound at module level | Patch at definition site (see Core Patterns above) |

## 8. Pytest Infrastructure (the load-bearing rules)

### conftest execution order

Root `tests/conftest.py` runs **FIRST**. Sub-directory conftest files run only when their tests are collected.

**Heavy mocks go in root conftest.** If you mock ortools, scipy, prometheus_client, or any large native dependency, do it in root `tests/conftest.py`. Sub-directory conftest mocks are too late -- collection-time imports already loaded the real module.

```python
# tests/conftest.py (ROOT -- runs first, before any test collection)
import sys
from unittest.mock import MagicMock

for _mod in ("ortools", "ortools.sat.python.cp_model",
             "scipy", "scipy.optimize", "prometheus_client"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
```

### External service mock completeness

Every external service the app uses must have a mock in the integration conftest:

| Service | What to mock | Why |
|---------|--------------|-----|
| Database | connection / session | Real DB not in CI |
| Auth | token verification | No auth server in tests |
| Cloud storage | upload / download | `google.auth.default()` hangs |
| Email | send functions | Sends real emails |
| Payment | charge / refund | Hits real API |

Audit: grep production code for external service imports; verify each has a mock.

### Marker discipline

Tests requiring real heavy dependencies (scipy.optimize, real DB, ML models) MUST be marked:

```python
pytestmark = pytest.mark.slow                  # module-level

@pytest.mark.slow                              # per-test or per-class
class TestPortionSolver: ...
```

Default `addopts` in `pyproject.toml`: `-m "not slow and not e2e"`.

For full conftest+sys.modules race + environment-safety patterns, see `references/pytest-infrastructure.md`.

## References

- `references/tdd-best-practices.md` -- TDD discipline, red-green-refactor depth, coverage strategies
- `references/framework-config.md` -- pytest config, plugins, CI/CD
- `references/pytest-infrastructure.md` -- conftest ordering, heavy-dep mocking, mock target decision tree, external service audit
- pytest docs: https://docs.pytest.org/
- unittest.mock docs: https://docs.python.org/3/library/unittest.mock.html
- hypothesis docs: https://hypothesis.readthedocs.io/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
