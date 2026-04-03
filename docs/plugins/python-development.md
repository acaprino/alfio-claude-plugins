# Python Development Plugin

> Stop wrestling with boilerplate. Get production-ready Python projects scaffolded in seconds, with built-in refactoring workflows and testing patterns that enforce best practices.

## Agents

### `python-engineer`

Hands-on Python 3.12+ engineer. Designs system architecture and implements production-ready code using modern tooling (uv, ruff, FastAPI, Pydantic). Async-first, type-safe, well-tested.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Planning new Python projects, designing architecture, making tech stack decisions, implementing Python features |

**Invocation:**
```
Use the python-engineer agent to [design/implement/optimize] [feature]
```

**Expertise:**
- Python 3.12+ features (pattern matching, generics, Protocol typing, dataclasses)
- Modern tooling: uv, ruff, mypy/pyright, pyproject.toml
- Web frameworks: FastAPI, Django 5.x, SQLAlchemy 2.0+, Pydantic v2
- Data pipelines, structured logging, async I/O
- Docker multi-stage builds, K8s manifests, cloud deploy

---

### `python-refactor-agent`

Expert Python refactoring agent. Cleans up legacy code, reduces complexity, removes dead code using vulture/ruff, and improves documentation/comments.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Refactoring code, removing dead code, optimizing imports, reducing cognitive complexity, improving code readability and docstrings |

**Invocation:**
```
Use the python-refactor-agent to refactor [module/file]
```

**Capabilities:**
- Code quality tools: ruff, vulture, mypy
- Refactoring patterns: Extract Method, Replace Conditional with Polymorphism, introducing Dataclasses/Protocols
- Complexity reduction: flattening nested loops/conditionals
- Dead code removal: unused imports, variables, functions, and classes
- Documentation: antirez's 9-type comment taxonomy, Google-style docstrings
- Leverages `python-refactor`, `python-dead-code`, `python-comments`, and `python-performance-optimization` skills

---

### `python-test-engineer`

Expert Python test engineer. Writes focused, behavior-driven pytest suites, handles TDD workflows, and improves code coverage.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Writing tests, improving test coverage, fixing broken tests, setting up pytest configurations, red-green-refactor workflows |

**Invocation:**
```
Use the python-test-engineer to write tests for [module/feature]
```

**Capabilities:**
- Testing frameworks: pytest, unittest, coverage, tox, nox
- Mocking: unittest.mock, pytest-mock, patching external APIs and databases
- Fixtures: reusable, modular pytest fixtures for database setup, API clients, mock data
- TDD workflow: Red-Green-Refactor cycles
- Pytest infrastructure rules: conftest execution order, mock placement strategy, mock target resolution, test marker discipline
- Leverages the `python-tdd` skill for best practices

---

## Skills

### `python-refactor`

Systematic 4-phase refactoring workflow that transforms complex code into clean, maintainable code.

| | |
|---|---|
| **Invoke** | `/python-refactor` or skill reference |
| **Use for** | Legacy modernization, complexity reduction, OOP transformation |

**4-Phase Workflow:**
1. **Analysis** - Measure complexity metrics, identify issues
2. **Planning** - Prioritize issues, select refactoring patterns
3. **Execution** - Apply patterns incrementally with test validation
4. **Validation** - Verify tests pass, metrics improved, no regression

**Key Features:**
- 7 executable Python scripts for metrics
- Cognitive complexity calculation
- flake8 integration with 16 curated plugins
- OOP transformation patterns
- Regression prevention checklists

**Synergy:** Works with `python-tdd` and `python-performance-optimization`

---

### `python-tdd`

Testing strategies with pytest, fixtures, mocking, and TDD.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Unit tests, integration tests, fixtures, mocking, coverage |

**Patterns included:**
- pytest fixtures (function, module, session scoped)
- Parameterized tests
- Mocking with unittest.mock
- Async testing with pytest-asyncio
- Property-based testing with Hypothesis
- Database testing patterns

---

### `python-performance-optimization`

Profiling and optimization techniques for Python applications.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Profiling, bottleneck identification, memory optimization |

**Tools covered:**
- cProfile and py-spy for CPU profiling
- memory_profiler for memory analysis
- pytest-benchmark for benchmarking
- Line profiling and flame graphs

---

### `async-python-patterns`

Async/await patterns for high-performance concurrent applications.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | asyncio, concurrent I/O, WebSockets, background tasks |

**Patterns included:**
- Event loop fundamentals
- gather(), create_task(), wait_for()
- Producer-consumer with asyncio.Queue
- Semaphores for rate limiting
- Async context managers and iterators

---

### `python-packaging`

Create and distribute Python packages with modern standards.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Library creation, PyPI publishing, CLI tools |

**Topics covered:**
- pyproject.toml configuration
- Source layout (src/) best practices
- Entry points and CLI tools
- Publishing to PyPI/TestPyPI
- Dynamic versioning with setuptools-scm

---

### `uv-package-manager`

Fast Python dependency management with uv (10-100x faster than pip).

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dependency management, virtual environments, lockfiles |

**Key commands:**
| Task | Command |
|------|---------|
| Create project | `uv init my-project` |
| Add dependency | `uv add requests` |
| Sync from lock | `uv sync --frozen` |
| Run script | `uv run python app.py` |

---

### `python-dead-code`

Detect and remove unused Python code using vulture and ruff.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dead code detection, unused imports, unreachable code, framework-aware cleanup |

**Two-tool approach:**
- Ruff: Fast lint-level checks (F401 unused imports, F841 unused variables, F811 redefined names)
- Vulture: Deeper analysis for unused functions, classes, and unreachable code

**Framework-aware:** Handles false positives for Django, FastAPI, pytest, click, and more.

---

### `python-comments`

Write and audit Python code comments using antirez's 9-type taxonomy.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Comment quality review, docstring improvements, documentation audits |

**Two modes:**
- **Write** - Add/improve comments in code using systematic classification
- **Audit** - Classify and assess existing comments with structured report

**Features:**
- 9-type comment taxonomy (Function, Design, Why, Teacher, Checklist, Guide, Trivial, Debt, Backup)
- Python-specific mapping (docstrings, inline comments, type hints)
- Quality scoring and improvement recommendations

---

## Commands

### `/python-scaffold`

Scaffold production-ready Python projects with modern tooling. Presents the plan and asks for confirmation before writing files.

```
/python-scaffold FastAPI REST API for user management
```

**Project types:** FastAPI, Django, Library, CLI, Generic

**Generates:** Directory structure, pyproject.toml, pytest config, Makefile, .env.example, .gitignore. Verifies the result with `uv sync` + `pytest` after scaffolding.

---

### `/python-refactor`

Metrics-driven 4-phase refactoring with checkpoint approval before execution and persistent output files.

```
/python-refactor src/legacy_module.py
```

**Phases:** Analysis -> Planning -> (Checkpoint) -> Execution -> Validation

**Output:** `.python-refactor/` directory with analysis, plan, execution log, and validation report.

---

**Related:** [senior-review](senior-review.md) (`/cleanup-dead-code` uses python-dead-code skill) | [clean-code](clean-code.md) (post-refactor code cleanup) | [agent-teams](agent-teams.md) (`/team-feature` for end-to-end development)
