---
name: uv-package-manager
description: >
  Handle virtual environments, lockfiles and interpreter version pinning.
  Use when setting up Python projects, managing dependencies, migrating off pip/poetry, or
  optimizing Python development workflows with uv.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: python-development
---

# UV Package Manager

Use uv - an extremely fast Python package installer and resolver written in Rust - for modern Python project management and dependency workflows.

## When to Invoke

- Setting up new Python projects or managing dependencies
- Creating and managing virtual environments
- Installing or switching Python interpreter versions
- Resolving dependency conflicts efficiently
- Migrating from pip, pip-tools, or poetry to uv
- Speeding up CI/CD pipelines with faster installs
- Working with lockfiles for reproducible builds
- Managing monorepo Python projects with workspaces

## Core Concepts

### What is uv?
- **Ultra-fast package installer**: 10-100x faster than pip
- **Written in Rust**: Leverages Rust's performance
- **Drop-in pip replacement**: Compatible with pip workflows
- **Virtual environment manager**: Create and manage venvs
- **Python installer**: Download and manage Python versions
- **Lockfile support**: Reproducible installations

### UV vs Traditional Tools
- **vs pip**: 10-100x faster, better resolver
- **vs pip-tools**: Faster, simpler, better UX
- **vs poetry**: Faster, less opinionated, lighter
- **vs conda**: Faster, Python-focused

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip
pip install uv

# Using Homebrew (macOS)
brew install uv

# Verify
uv --version
```

## Quick Start

```bash
# Create new project
uv init my-project
cd my-project

# Install packages (creates venv if needed)
uv add requests pandas

# Install dev dependencies
uv add --dev pytest black ruff

# Install from requirements.txt
uv pip install -r requirements.txt

# Sync from pyproject.toml
uv sync
```

## Virtual Environment Management

```bash
# Create virtual environment
uv venv
uv venv --python 3.12
uv venv my-env

# Activate
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\activate.bat         # Windows CMD
.venv\Scripts\Activate.ps1         # Windows PowerShell

# Or skip activation with uv run
uv run python script.py
uv run pytest
uv run --python 3.11 python script.py
```

## Package Management

### Adding Dependencies

```bash
uv add requests
uv add "django>=4.0,<5.0"
uv add numpy pandas matplotlib
uv add --dev pytest pytest-cov
uv add --optional docs sphinx
uv add git+https://github.com/user/repo.git
uv add git+https://github.com/user/repo.git@v1.0.0
uv add ./local-package
uv add -e ./local-package
```

### Removing and Upgrading

```bash
uv remove requests
uv remove --dev pytest
uv add --upgrade requests
uv sync --upgrade
uv tree --outdated
```

### Locking Dependencies

```bash
uv lock
uv lock --upgrade
uv lock --upgrade-package requests
uv lock --check
```

## Python Version Management

```bash
uv python install 3.12
uv python install 3.11 3.12 3.13
uv python list
uv python list --all-versions
uv python pin 3.12
```

## Project Configuration

### pyproject.toml with uv

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My awesome project"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "requests>=2.31.0",
    "pydantic>=2.0.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = []

[tool.uv.sources]
my-package = { git = "https://github.com/user/repo.git" }
```

### Using uv with Existing Projects

```bash
# Migrate from requirements.txt
uv add -r requirements.txt

# Migrate from poetry (already have pyproject.toml)
uv sync

# Export to requirements.txt
uv pip freeze > requirements.txt

# Export with hashes
uv pip freeze --require-hashes > requirements.txt
```

## Best Practices

### Project Setup
1. **Always use lockfiles** for reproducibility
2. **Pin Python version** with .python-version
3. **Separate dev dependencies** from production
4. **Use uv run** instead of activating venv
5. **Commit uv.lock** to version control
6. **Use --frozen in CI** for consistent builds
7. **Leverage global cache** for speed
8. **Use workspace** for monorepos
9. **Export requirements.txt** for compatibility
10. **Keep uv updated** for latest features

## Essential Commands

```bash
# Project management
uv init [PATH]              # Initialize project
uv add PACKAGE              # Add dependency
uv remove PACKAGE           # Remove dependency
uv sync                     # Install dependencies
uv lock                     # Create/update lockfile

# Virtual environments
uv venv [PATH]              # Create venv
uv run COMMAND              # Run in venv

# Python management
uv python install VERSION   # Install Python
uv python list              # List installed Pythons
uv python pin VERSION       # Pin Python version

# Package installation (pip-compatible)
uv pip install PACKAGE      # Install package
uv pip uninstall PACKAGE    # Uninstall package
uv pip freeze               # List installed
uv pip list                 # List packages

# Utility
uv cache clean              # Clear cache
uv cache dir                # Show cache location
uv --version                # Show version
```

## References

- `references/uv-reference.md` - monorepo/workspace setup, CI/CD integration (GitHub Actions), Docker integration (single and multi-stage builds), lockfile workflows, performance optimization (cache, parallel, offline), tool comparisons with benchmarks (vs pip, poetry, pip-tools), pre-commit hooks, VS Code integration, extended workflow examples, troubleshooting, migration guides

## Resources

- **Official documentation**: https://docs.astral.sh/uv/
- **GitHub repository**: https://github.com/astral-sh/uv
- **Astral blog**: https://astral.sh/blog
- **Migration guides**: https://docs.astral.sh/uv/guides/
