---
name: python-tdd
description: "Generate focused, behavior-driven Python tests using TDD methodology with pytest. Use when writing tests, improving coverage, reviewing test quality, or practicing red-green-refactor workflows."
---

# Python Testing Patterns

Generate focused, behavior-driven tests with pytest. Prioritize observable behavior over implementation details.

## 1. Test Philosophy

### What to Test
- Observable behavior and return values
- User-facing workflows and API contracts
- Edge cases and error handling at system boundaries
- State transitions and side effects
- Data validation and transformation rules

### What NOT to Test
- Framework internals (pytest, SQLAlchemy, FastAPI mechanics)
- Implementation details (private methods, internal variable names)
- Third-party library behavior
- Simple utility functions with no branching logic
- That objects are truthy -- this asserts nothing useful

### Mocking Strategy
**DO mock:**
- External API calls and HTTP requests
- Database queries in unit tests
- File system operations
- Time-dependent behavior (`datetime.now`, `time.time`)
- Environment variables

**DON'T mock:**
- Your own models and dataclasses
- Simple utility functions
- The function under test itself
- Framework features you rely on

### Test Count Discipline
- Max **10 tests** per file for simple modules
- Max **15 tests** per file for complex modules
- If you need more, the module is too complex -- suggest splitting it

## 2. TDD Workflow

### Red-Green-Refactor Cycle
1. **RED** - Write a failing test. It must fail for the right reason (not import error, not syntax error).
2. **GREEN** - Write the minimal code to make it pass. No more.
3. **REFACTOR** - Improve code while all tests stay green. No new behavior.

### Coverage Gap Analysis
| Priority | What to Cover | Target |
|----------|--------------|--------|
| P0 | Critical paths (auth, payments, data integrity) | 100% line + branch |
| P1 | Core business logic and public API | 90%+ line |
| P2 | Utilities, helpers, config | 80%+ line |

Overall target: 80%+ line coverage, 100% for critical paths.

See `references/tdd-best-practices.md` for full TDD discipline and advanced workflows.

## 3. Test Generation Rules

### Naming Convention (BDD Style)
**Class-based grouping** - nest by feature, then scenario:

```python
class TestUserService:
    class TestCreateUser:
        def test_should_create_when_valid_data(self): ...
        def test_should_raise_when_email_exists(self): ...

    class TestDeleteUser:
        def test_should_soft_delete_when_active(self): ...
```

**Flat function naming** - `test_<action>_should_<outcome>_when_<condition>`:

```python
def test_create_user_should_succeed_when_valid_data(): ...
def test_create_user_should_raise_when_email_exists(): ...
def test_login_should_fail_when_password_expired(): ...
```

### Test Structure (AAA Pattern)
Every test follows Arrange-Act-Assert:

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

### Reusable Fakes
Use factory fixtures in `conftest.py` instead of raw dicts:

```python
# conftest.py
import pytest

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

## 4. Core Patterns

### Fixtures
Setup/teardown with yield. Use the narrowest scope possible.

```python
@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session  # test runs here
    session.rollback()
    session.close()

@pytest.fixture(scope="module")
def api_client():
    client = TestClient(app)
    yield client

@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()
```

Share fixtures across files via `conftest.py` -- pytest discovers them automatically.

### Parametrization
Use `@pytest.mark.parametrize` with custom IDs for readable output:

```python
@pytest.mark.parametrize("input_val,expected", [
    pytest.param("user@example.com", True, id="valid-email"),
    pytest.param("no-at-sign.com", False, id="missing-at"),
    pytest.param("", False, id="empty-string"),
    pytest.param("a@b.c", True, id="minimal-valid"),
])
def test_is_valid_email(input_val, expected):
    assert is_valid_email(input_val) == expected
```

### Mocking
Patch where the object is used, not where it is defined:

```python
from unittest.mock import patch, MagicMock

@patch("myapp.services.requests.get")
def test_fetch_user_should_return_parsed_data(mock_get):
    mock_get.return_value.json.return_value = {"id": 1, "name": "Alice"}
    mock_get.return_value.raise_for_status = MagicMock()

    result = fetch_user(1)

    assert result.name == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1")
```

Use `autospec=True` to catch signature mismatches:

```python
@patch("myapp.services.UserRepository", autospec=True)
def test_should_call_repo_with_correct_args(MockRepo):
    instance = MockRepo.return_value
    instance.find_by_id.return_value = User(id=1, name="Alice")

    result = get_user(1)
    instance.find_by_id.assert_called_once_with(1)
```

Simulate errors with `side_effect`:

```python
@patch("myapp.client.requests.get")
def test_should_raise_on_network_error(mock_get):
    mock_get.side_effect = ConnectionError("timeout")

    with pytest.raises(ServiceUnavailableError):
        fetch_data("https://api.example.com/data")
```

### Async Testing
Requires `pytest-asyncio`. Mark async tests and fixtures:

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch_should_return_data():
    result = await async_fetch("https://api.example.com")
    assert result["status"] == "ok"

@pytest.fixture
async def async_db_session():
    session = AsyncSession(bind=async_engine)
    yield session
    await session.close()

@pytest.mark.asyncio
async def test_create_user_async(async_db_session):
    user = User(name="Alice")
    async_db_session.add(user)
    await async_db_session.commit()
    assert user.id is not None
```

### Monkeypatch
Override environment variables and object attributes safely:

```python
def test_should_use_custom_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    assert get_database_url() == "postgresql://localhost/test"

def test_should_fallback_when_env_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_database_url() == "sqlite:///:memory:"

def test_should_use_patched_attribute(monkeypatch):
    monkeypatch.setattr("myapp.config.API_TIMEOUT", 5)
    assert get_timeout() == 5
```

### Property-Based Testing
Use hypothesis to discover edge cases automatically:

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_reverse_roundtrip(s):
    assert s[::-1][::-1] == s

@given(st.integers(min_value=0, max_value=1000))
def test_deposit_should_increase_balance(amount):
    account = Account(balance=0)
    account.deposit(amount)
    assert account.balance == amount
```

### Database Testing
In-memory SQLite for fast, isolated database tests:

```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()

def test_create_and_query_user(db_session):
    db_session.add(User(name="Alice", email="alice@test.com"))
    db_session.commit()

    user = db_session.query(User).filter_by(name="Alice").one()
    assert user.email == "alice@test.com"
```

### Temporary Files
Use `tmp_path` for file system tests -- auto-cleaned after each test:

```python
def test_export_should_write_csv(tmp_path):
    output = tmp_path / "report.csv"
    export_report(output, data=[{"name": "Alice", "score": 95}])

    content = output.read_text()
    assert "Alice" in content
    assert "95" in content
```

## 5. Anti-Patterns

| Anti-Pattern | Why It Is Bad | Do This Instead |
|---|---|---|
| `assert obj is not None` | Asserts nothing about behavior | Assert on a specific attribute or return value |
| Mocking the function under test | Tests nothing real | Mock its dependencies instead |
| 40+ tests for a simple module | Sign of over-testing or bloated module | Split module or consolidate parametrized tests |
| Testing framework internals | Validates pytest/SQLAlchemy, not your code | Test your logic through public API |
| Copy-pasting mock setup in every test | Fragile, hard to maintain | Extract into fixtures or factory functions |
| Testing private methods directly | Couples tests to implementation | Test through the public interface |
| Catching exceptions inside test code | Swallows real failures silently | Use `pytest.raises` as context manager |
| No assertions in test body | Test always passes, proves nothing | Every test must assert something |
| Asserting on `mock.called` only | Does not verify correct arguments | Use `assert_called_once_with(expected_args)` |

## 6. References

- `references/tdd-best-practices.md` - Full TDD discipline, red-green-refactor workflows, coverage strategies
- `references/framework-config.md` - pytest configuration, CI/CD integration, pyproject.toml setup
- [pytest docs](https://docs.pytest.org/)
- [unittest.mock docs](https://docs.python.org/3/library/unittest.mock.html)
- [hypothesis docs](https://hypothesis.readthedocs.io/)
