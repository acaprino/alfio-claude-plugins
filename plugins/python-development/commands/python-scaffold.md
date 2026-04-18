---
description: >
  Scaffold production-ready Python projects with modern tooling -- FastAPI, Django, Library, CLI, or Generic -- using uv, pytest, ruff.
  TRIGGER WHEN: the user asks to start a new Python project, bootstrap FastAPI/Django/CLI/library structure, or set up uv+pytest+ruff from scratch.
  DO NOT TRIGGER WHEN: adding to an existing Python project (use python-engineer agent directly) or scaffolding a non-Python project.
argument-hint: "<project-name> [--type fastapi|django|library|cli|generic]"
---

# Python Project Scaffolding

You are a Python project architecture expert. Generate complete project structures with modern tooling (uv, FastAPI, Django), type hints, testing setup, and configuration.

## CRITICAL RULES

1. **Confirm before writing files.** Present the project plan and get user approval before creating anything.
2. **Use uv for everything.** Package management, virtual environments, running scripts.
3. **Never enter plan mode.** Execute immediately.

## Step 1: Determine Project Type

From `$ARGUMENTS`, identify:
- **Project name** (required)
- **Project type** from `--type` flag or infer from description:
  - `fastapi`: REST APIs, microservices, async applications
  - `django`: Full-stack web applications, admin panels
  - `library`: Reusable packages, utilities
  - `cli`: Command-line tools
  - `generic`: Standard Python applications

If type is unclear, ask:

```
Project: [name]

What type of project?
1. FastAPI -- REST APIs, microservices, async
2. Django -- Full-stack web, admin panels
3. Library -- Reusable package
4. CLI -- Command-line tool
5. Generic -- Standard Python application
```

## Step 2: Present Plan & Confirm

Show the complete project structure before creating files:

```
Project: [name]
Type: [type]
Python: >=3.11

Directory structure:
[complete tree]

Key dependencies:
[list]

Tooling:
- Package manager: uv
- Linter: ruff
- Tests: pytest
- Type checking: mypy (library/cli only)

1. Create this project
2. Adjust -- change structure or dependencies
3. Cancel
```

Do NOT create any files until the user confirms.

## Step 3: Scaffold

After approval, create the project:

### FastAPI Project

```
fastapi-project/
├── pyproject.toml
├── .gitignore
├── .env.example
├── Makefile
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── endpoints/
│       │       │   ├── __init__.py
│       │       │   ├── users.py
│       │       │   └── health.py
│       │       └── router.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── security.py
│       │   └── database.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── user.py
│       └── services/
│           ├── __init__.py
│           └── user_service.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── api/
        ├── __init__.py
        └── test_users.py
```

Dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`
Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`

### Django Project

Initialize with `django-admin startproject config .`, then `python manage.py startapp core`.

Dependencies: `django`, `django-environ`, `psycopg[binary]`, `gunicorn`
Dev: `django-debug-toolbar`, `pytest-django`, `ruff`

### Library Project

```
library-name/
├── pyproject.toml (hatchling build backend)
├── LICENSE
├── src/
│   └── library_name/
│       ├── __init__.py
│       ├── py.typed
│       └── core.py
└── tests/
    ├── __init__.py
    └── test_core.py
```

### CLI Project

Same as Library but with `[project.scripts]` entry and `typer` + `rich` dependencies.

### Generic Project

Minimal: `pyproject.toml`, `src/project_name/__init__.py`, `tests/`, `Makefile`.

## Step 4: Verify

After scaffolding, run verification:

```bash
cd [project-name]
uv sync
uv run pytest -v
```

Present results:
```
Project [name] scaffolded successfully.

Files created: [count]
Dependencies installed: [count]
Tests: [pass/fail]

Next steps:
1. cd [project-name]
2. uv sync
3. [type-specific start command]
```
