# Python Development Plugin

> Stop wrestling with boilerplate. Get production-ready Python projects scaffolded in seconds, with built-in refactoring workflows and testing patterns that enforce best practices.

## Agents

### `python-pro`

Expert Python developer mastering Python 3.12+ features, modern tooling (uv, ruff), and production-ready practices.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Modern Python patterns, async programming, performance optimization, type hints |

**Invocation:**
```
Use the python-pro agent to [implement/optimize/review] [feature]
```

**Expertise:**
- Python 3.12+ features (pattern matching, type hints, dataclasses)
- Modern tooling: uv, ruff, mypy, pytest
- Async/await patterns with asyncio
- Performance profiling and optimization
- FastAPI, Django, Pydantic integration

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

**Related:** [senior-review](senior-review.md) (`/cleanup-dead-code` uses python-dead-code skill) | [humanize](humanize.md) (post-refactor code cleanup) | [workflows](workflows.md) (`/feature-e2e` for end-to-end development)
