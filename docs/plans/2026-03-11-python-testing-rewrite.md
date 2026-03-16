# [ARCHIVED] Python Testing Patterns Skill Rewrite

> **Status:** COMPLETED -- skill rewritten and renamed to `python-tdd`.
>
> **Note:** This plan is archived. The skill now lives at `plugins/python-development/skills/python-tdd/`. All references to `python-testing-patterns` in this document are historical -- the current skill name is `python-tdd` (plugin version 1.13.0).

> **For Claude:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** Rewrite the `python-testing-patterns` skill to be a workflow-oriented testing guide that teaches Claude how to generate focused, behavior-driven Python tests using TDD methodology.

**Architecture:** Replace the existing 900-line reference cookbook SKILL.md with a concise workflow-focused SKILL.md (~300 lines) plus two reference files for detailed patterns and CI config. Synthesize content from three sources: Alfredo Perez's "Reliable Unit Tests with Claude Code" article, ECC Python Testing skill, and alirezarezvani's TDD Guide.

**Tech Stack:** Python, pytest, pytest-cov, pytest-asyncio, hypothesis, unittest.mock

---

### Task 1: Create references directory and tdd-best-practices.md

**Files:**
- Create: `plugins/python-development/skills/python-testing-patterns/references/tdd-best-practices.md`

**Step 1: Create the references directory**

Run: `mkdir -p plugins/python-development/skills/python-testing-patterns/references`

**Step 2: Write tdd-best-practices.md**

Content covers:
- Red-Green-Refactor cycle discipline (RED: write failing test, GREEN: minimal code to pass, REFACTOR: improve while green)
- Cycle discipline rules (complete one cycle before next, commit after each GREEN, small iterations)
- Test naming conventions (`should_<expected>_when_<condition>` and BDD `WHEN/SHOULD` style)
- AAA pattern (Arrange-Act-Assert)
- Test quality principles (independence, speed <100ms, determinism, clarity)
- Coverage goals by type (line 80%+, branch 70%+, function 90%+)
- Critical path rules (auth, payments, data validation = 100%)
- P0/P1/P2 coverage gap prioritization
- Anti-patterns list (testing framework internals, excessive mocks, `assert obj is not None`, testing implementation not behavior)

Source: alirezarezvani's `references/tdd-best-practices.md` + Alfredo Perez article's philosophy

**Step 3: Commit**

```bash
git add plugins/python-development/skills/python-testing-patterns/references/tdd-best-practices.md
git commit -m "Add TDD best practices reference for python-testing-patterns"
```

---

### Task 2: Create framework-config.md reference

**Files:**
- Create: `plugins/python-development/skills/python-testing-patterns/references/framework-config.md`

**Step 1: Write framework-config.md**

Content covers:
- pytest configuration (pytest.ini and pyproject.toml examples)
- Coverage configuration (coverage.run, coverage.report, exclude_lines)
- Marker configuration (slow, integration, unit, e2e)
- CI/CD integration (GitHub Actions workflow for Python + pytest-cov)
- Coverage threshold gates (pytest --cov-fail-under, pyproject.toml fail_under)
- Coverage services (Codecov, Coveralls, SonarCloud)
- Version requirements (Python 3.10+, pytest 7+, pytest-cov, pytest-asyncio)

Source: alirezarezvani's `references/framework-guide.md` + `references/ci-integration.md` + existing SKILL.md config section

**Step 2: Commit**

```bash
git add plugins/python-development/skills/python-testing-patterns/references/framework-config.md
git commit -m "Add framework config reference for python-testing-patterns"
```

---

### Task 3: Rewrite SKILL.md

**Files:**
- Modify: `plugins/python-development/skills/python-testing-patterns/SKILL.md` (full rewrite)

**Step 1: Write the new SKILL.md**

Structure (~300 lines):

```markdown
---
name: python-testing-patterns
description: "Generate focused, behavior-driven Python tests using TDD methodology with pytest. Use when writing tests, improving coverage, reviewing test quality, or practicing red-green-refactor workflows."
---

# Python Testing Patterns

## Test Philosophy

Rules for generating meaningful tests that test behavior, not implementation.

### What to Test
- Observable behavior and outcomes
- User-facing workflows and API contracts
- Edge cases and error handling at system boundaries
- State transitions and side effects

### What NOT to Test
- Framework internals (pytest, SQLAlchemy, FastAPI mechanics)
- Implementation details (private methods, internal variable names)
- Third-party library behavior
- Simple utility functions with no branching logic
- That objects are truthy (`assert obj is not None` -- useless)

### Mocking Strategy

**DO Mock:**
- External API calls (HTTP, gRPC, third-party SDKs)
- Database queries in unit tests (use in-memory DB for integration)
- File system operations
- Time-dependent behavior (datetime.now, sleep)
- Environment variables

**DON'T Mock:**
- Your own models/dataclasses
- Simple utility functions
- The function under test
- Framework features you rely on

### Test Count Discipline
- Maximum 10 tests per file for simple modules
- Maximum 15 tests for complex modules with branching
- If you need more, the module under test is too complex -- suggest splitting

## TDD Workflow

### Red-Green-Refactor Cycle

**RED: Write a failing test first**
- Test should fail for the RIGHT reason (not import errors)
- Name test as a specification: `test_should_reject_negative_amounts`
- One behavior per test

**GREEN: Minimal code to pass**
- Write the simplest code that makes the test pass
- Duplicate code is acceptable temporarily
- No over-engineering

**REFACTOR: Improve while green**
- Remove duplication from GREEN phase
- Apply design patterns where appropriate
- Run tests after each small change
- Commit when green

### Coverage Gap Analysis

When analyzing coverage, prioritize gaps:

- **P0 (Critical)**: Uncovered error handlers, auth paths, payment logic, data validation -- fix immediately
- **P1 (High-value)**: Core logic branches, else clauses in business rules -- fix before merge
- **P2 (Low-risk)**: Utility functions, logging, repr methods -- document and defer

Target: 80%+ line coverage, 100% for critical paths (auth, payments, validation).

## Test Generation Rules

### Naming Convention (BDD Style)

Use `describe/when/should` grouping with classes:

    class TestUserService:
        class TestCreateUser:
            def test_should_create_user_when_valid_data(self): ...
            def test_should_raise_when_email_already_exists(self): ...
        class TestDeleteUser:
            def test_should_soft_delete_when_user_exists(self): ...

Or flat functions with descriptive names:

    def test_create_user_should_succeed_when_valid_data(): ...
    def test_create_user_should_raise_when_duplicate_email(): ...

### Test Structure (AAA Pattern)

Every test follows Arrange-Act-Assert:

    def test_should_apply_discount_when_member(self):
        # Arrange
        user = User(membership="gold")
        cart = Cart(items=[Item(price=100)])

        # Act
        total = cart.calculate_total(user)

        # Assert
        assert total == 80.0

### Reusable Fakes

Create factory functions for test data, place in conftest.py or test helpers:

    # tests/conftest.py
    @pytest.fixture
    def make_user():
        def _make_user(**overrides):
            defaults = {"name": "Test User", "email": "test@example.com"}
            defaults.update(overrides)
            return User(**defaults)
        return _make_user

## Core Patterns

### Fixtures (setup/teardown with yield, scope management)
### Parametrization (@pytest.mark.parametrize with custom IDs)
### Mocking (unittest.mock, patch, MagicMock, autospec)
### Async Testing (@pytest.mark.asyncio, async fixtures)
### Monkeypatch (env vars, attributes, methods)
### Property-Based Testing (hypothesis)
### Database Testing (in-memory SQLite, session fixtures)
### Temporary Files (tmp_path)

[Each with a concise example -- 5-10 lines max, not the verbose examples from the old SKILL.md]

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Do This Instead |
|---|---|---|
| `assert component is not None` | Tests nothing useful | Assert specific behavior |
| Mocking the function under test | Tests your mock, not code | Mock dependencies only |
| 40+ tests for simple module | Noise buries signal | Max 10-15, focus on behavior |
| Testing framework internals | Framework authors test that | Test your logic |
| Copy-pasting mock setup | Unmaintainable | Shared fixtures in conftest.py |
| Testing private methods | Couples to implementation | Test through public API |
| Catching exceptions in test | Hides failures | Use pytest.raises |
```

**Step 2: Verify SKILL.md is well-formed**

Run: `head -5 plugins/python-development/skills/python-testing-patterns/SKILL.md`
Expected: Valid YAML frontmatter with name and description

**Step 3: Commit**

```bash
git add plugins/python-development/skills/python-testing-patterns/SKILL.md
git commit -m "Rewrite python-testing-patterns as workflow-oriented testing guide"
```

---

### Task 4: Update marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Bump versions**

- `python-development` plugin version: `1.7.0` -> `1.8.0`
- `metadata.version`: `1.51.0` -> `1.52.0`

**Step 2: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "Bump python-development to 1.8.0 for testing skill rewrite"
```

---

### Task 5: Push to remote

**Step 1: Push all commits**

Run: `git push origin master`
