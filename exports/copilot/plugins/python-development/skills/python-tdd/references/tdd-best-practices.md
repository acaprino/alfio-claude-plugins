# TDD Best Practices for Python

## Red-Green-Refactor Cycle

### RED Phase

- Write exactly one failing test before any production code
- Test must fail for the right reason - verify the failure message
- Test only one behavior per test function
- Use descriptive BDD-style naming before writing the test body
- If the test passes immediately, it is testing nothing new - delete or rethink

### GREEN Phase

- Write the minimum code to make the failing test pass
- Do not add logic beyond what the test requires
- Resist the urge to generalize or optimize
- Commit after reaching GREEN - this is your safe checkpoint

### REFACTOR Phase

- Improve structure, naming, duplication - production code and test code
- All tests must stay green throughout refactoring
- Extract helpers, fixtures, or parametrize only when duplication is clear
- Do not add new behavior during refactor - that requires a new RED phase

### Cycle Discipline

- Complete one full cycle before starting the next
- Keep iterations small - each cycle should take minutes, not hours
- Commit after every GREEN phase
- If stuck in RED for more than 10 minutes, simplify the test

## Test Naming Conventions

Use BDD-style names that describe behavior, not implementation.

Pattern: `test_should_<expected>_when_<condition>`

```python
# Good - describes behavior
def test_should_return_total_when_cart_has_items():
def test_should_raise_auth_error_when_token_expired():
def test_should_send_email_when_order_confirmed():

# Bad - describes implementation
def test_calculate_sum():
def test_check_token():
def test_process_order():
```

Keep max 10 tests per file. Split by behavior group when exceeding this limit.

## Test Structure (AAA Pattern)

Every test follows Arrange-Act-Assert with clear visual separation.

```python
def test_should_apply_discount_when_coupon_is_valid():
    # Arrange
    cart = Cart(items=[Item("book", price=20.00)])
    coupon = Coupon(code="SAVE10", discount_pct=10)

    # Act
    cart.apply_coupon(coupon)

    # Assert
    assert cart.total == 18.00
```

Rules:
- One Act per test - if you need multiple actions, write multiple tests
- No logic in Assert - no loops, no conditionals, no calculations
- Arrange can use fixtures or factories to reduce boilerplate

## Test Quality Principles

### Independence

- Tests must not share mutable state
- Each test creates its own data via fixtures or factories
- Execution order must not matter - use `pytest-randomly` to verify
- Use `tmp_path` fixture for filesystem tests, never shared directories

### Speed

- Unit tests must run in under 100ms each
- Mock all I/O: network, database, filesystem (where appropriate)
- Use `pytest-timeout` to catch slow tests: `@pytest.mark.timeout(1)`
- Reserve slow tests for integration suite with `@pytest.mark.integration`

### Determinism

- No reliance on system time, random values, or environment state
- Inject clocks and random seeds as dependencies
- Tests must produce identical results on any machine, any run order

### Clarity

- A failing test must immediately communicate what broke and why
- Use custom assertion messages for non-obvious comparisons
- Prefer direct assertions over helper methods that obscure intent
- Test code is documentation - optimize for readability over DRY

## Mocking Strategy

### DO Mock

| Target | Reason |
|--------|--------|
| External APIs (Stripe, AWS, etc.) | Non-deterministic, slow, costly |
| Third-party library I/O calls | Network/filesystem side effects |
| System clock / `datetime.now()` | Determinism |
| Email / SMS services | Side effects in tests |

### DO NOT Mock

| Target | Reason |
|--------|--------|
| Framework features (pytest, Django ORM) | Testing the framework, not your code |
| Your own models / dataclasses | Hiding real behavior |
| Simple utility functions | No side effects to isolate |
| Value objects and enums | Pure logic, no reason to fake |

Use reusable fakes over ad-hoc mocks when a dependency appears in 3+ tests.

```python
# Reusable fake - better than repeating mock setup
class FakePaymentGateway:
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.charges = []

    def charge(self, amount):
        self.charges.append(amount)
        if not self.should_succeed:
            raise PaymentError("declined")
        return {"status": "ok"}
```

## Coverage Goals

### Thresholds by Type

| Metric | Target | Notes |
|--------|--------|-------|
| Line coverage | 80%+ | Baseline for all code |
| Branch coverage | 70%+ | Catches missed conditionals |
| Function coverage | 90%+ | Every public function tested |
| Critical paths | 100% | Auth, payments, data validation |

### Critical Path Rules

These modules require 100% line and branch coverage - no exceptions:

- **Authentication and authorization** - login, token validation, permissions
- **Payment processing** - charges, refunds, webhook handlers
- **Data validation** - input sanitization, schema enforcement
- **Security boundaries** - encryption, hashing, access control

### P0/P1/P2 Gap Prioritization

When improving coverage on an existing codebase, prioritize gaps by risk.

| Priority | What to cover | Examples |
|----------|--------------|----------|
| **P0** | Uncovered error handlers, auth, payments | `except` blocks in payment flow, permission checks |
| **P1** | Core business logic branches | Discount calculations, state transitions, workflow rules |
| **P2** | Utility and helper functions | String formatting, config parsing, convenience wrappers |

### Avoiding Coverage Theater

High coverage does not equal good tests. Watch for these traps:

- Tests that execute code but assert nothing meaningful
- Snapshot tests that nobody reviews when they change
- Tests that duplicate each other with trivial variations
- Covering getters/setters while ignoring complex branching logic

Measure coverage to find gaps, not to prove quality.

## Hardcoded Golden Values

Asserting exact computed results (`assert result.total_kcal == 660`) is one of the most common sources of brittle tests. The algorithm produces a slightly different number after a legitimate improvement, and the test fails -- not because behavior is wrong, but because the "golden" value is stale.

### What to Do Instead

**Assert invariants and contracts** -- properties that must hold regardless of algorithm tuning:

```python
# BAD - breaks when algorithm changes rounding
assert result.total_kcal == 660

# GOOD - assert the contract
assert abs(result.total_kcal - target_kcal) <= target_kcal * 0.05  # within 5%
assert result.total_kcal == sum(
    item["kcal"] for meal in result.meals for item in meal["items"]
)
assert result.total_protein >= min_protein
```

**Use `pytest.approx` for acceptable ranges:**

```python
assert result.total_kcal == pytest.approx(660, abs=30)  # within 30 kcal
```

**Derive expected values from inputs** rather than hardcoding:

```python
expected_kcal = sum(item["kcal"] * scale_factor for item in input_items)
assert result.total_kcal == expected_kcal
```

### When Exact Values ARE Appropriate

- Pure functions with no rounding or scaling (e.g., `2 + 2 == 4`)
- Deterministic serialization (JSON output, string formatting)
- Lookup tables and enum mappings
- Database record counts after known inserts

## Anti-Patterns

| Anti-Pattern | Why It Is Bad | Do This Instead |
|-------------|---------------|-----------------|
| Testing implementation details | Breaks on refactor, provides false confidence | Test observable behavior and outputs |
| Conditionals in test code | Hides test logic, multiple behaviors in one test | Write separate tests for each branch |
| Shared mutable state between tests | Order-dependent failures, flaky tests | Use fixtures with function scope |
| Testing third-party library behavior | Not your code, not your responsibility | Trust the library, mock at boundary |
| Giant test functions (50+ lines) | Hard to read, unclear what is tested | Extract fixtures, split into focused tests |
| Mocking everything | Tests pass but code is broken in production | Only mock I/O and external boundaries |
| Ignoring edge cases | Bugs hide in boundaries and empty inputs | Test nulls, empty collections, max values |
| Asserting too many things | Unclear which assertion failed and why | One logical assertion per test |
| Copy-pasting test setup | Maintenance burden, inconsistent setup | Use `@pytest.fixture` or factory functions |
| Skipping RED phase | No proof the test catches regressions | Always see the test fail first |
| Hardcoded golden values | Breaks on algorithm improvement, not on real bugs | Assert invariants, tolerances, or derived values |
