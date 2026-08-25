# Python Packaging Reference

`pyproject.toml` shape, src-layout, build/publish flow, and the gotchas that bite when distributing to PyPI. The full PEP 621 metadata schema lives upstream; this file is the recommended baseline + the trip-wires.

## When to use

Setting up a new Python package for distribution, or auditing an existing `pyproject.toml`. For decision-tree (when to package vs ship as a private repo), see `python-packaging/SKILL.md`.

## Recommended `pyproject.toml` baseline

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-awesome-package"
version = "1.0.0"
description = "An awesome Python package"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [{name = "Your Name", email = "you@example.com"}]
keywords = ["example", "package"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "requests>=2.28.0,<3.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7", "pytest-cov", "ruff", "mypy"]
docs = ["sphinx>=5", "sphinx-rtd-theme"]

[project.urls]
Homepage = "https://github.com/username/repo"
Repository = "https://github.com/username/repo"
"Bug Tracker" = "https://github.com/username/repo/issues"

[project.scripts]
my-cli = "my_package.cli:main"

[tool.setuptools]
package-dir = {"" = "src"}                  # src-layout
zip-safe = false

[tool.setuptools.packages.find]
where = ["src"]
include = ["my_package*"]

[tool.setuptools.package-data]
my_package = ["py.typed", "*.pyi", "data/*.json"]
```

## Gotchas (the trip-wires)

- **Always use src-layout** (`src/my_package/`), never flat layout (`my_package/` at repo root). Flat layout means `pip install -e .` plus a stale local import can shadow the installed package, leading to "tests pass locally, fail in CI" mysteries.
- **`py.typed` marker file** is required for downstream type checkers to honor your annotations. Add an empty `py.typed` to your package dir AND list it in `package-data`. PEP 561.
- **`license = {text = "MIT"}` vs `license = {file = "LICENSE"}`** -- newer setuptools prefers `text` for SPDX identifiers; `file` includes the LICENSE file content. Don't mix them.
- **Version conflicts**: `dependencies = ["requests>=2.28.0,<3.0.0"]` -- always pin upper-bounds for runtime deps to avoid breaking when a dep majors. Loose `>=` is the leading cause of "worked yesterday" issues.
- **`requires-python = ">=3.11"`** matters: pip uses it to skip the package on incompatible Pythons. Forgetting this means users on 3.9 get the wheel and crash on import.
- **Build backend choice**: `setuptools` (default), `hatchling` (modern, simpler), `flit_core` (minimal pure-Python), `pdm-backend`, `poetry-core`. Pick one and stick with it. Mixing backends across a monorepo is friction.
- **`twine check dist/*`** before `twine upload`. Catches malformed README rendering, missing classifiers, and other PyPI-rejection issues before you publish.
- **Test on TestPyPI first** (`twine upload --repository testpypi dist/*`). PyPI uploads are immutable -- you cannot delete or replace a version, only yank it.
- **Use API tokens, not passwords** for PyPI uploads. Configure in `~/.pypirc` or via `TWINE_PASSWORD` env var.
- **Wheels and sdists**: `python -m build` produces both. Wheels (`.whl`) are pre-built for fast install; sdist (`.tar.gz`) is the source fallback. Always ship both.

## Build + publish (the canonical flow)

```bash
# Modern: PEP 517 build
pip install build twine
python -m build                            # produces dist/*.whl + dist/*.tar.gz
twine check dist/*                         # verify before upload
twine upload --repository testpypi dist/*  # test first
twine upload dist/*                        # publish to PyPI
```

For uv users, replace `pip install build twine` with `uv tool install build twine`.

## src-layout structure

```
my-awesome-package/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── py.typed                       # PEP 561 marker
│       ├── core.py
│       └── cli.py
└── tests/
    ├── test_core.py
    └── test_cli.py
```

Then `pip install -e ".[dev]"` installs editable + dev deps.

## Versioning conventions

| Strategy | Use |
|----------|-----|
| **Semantic versioning** (semver) | Public APIs, libraries -- MAJOR.MINOR.PATCH |
| **CalVer** (e.g. 2026.4.26) | Apps, end-user tools where API stability isn't promised |
| **Pre-release** (1.0.0a1, 1.0.0b1, 1.0.0rc1) | Alpha / beta / RC channels |
| **Post-release** (1.0.0.post1) | Metadata-only fixes (typo in README, wrong classifier) |

PyPI accepts PEP 440 versions only -- `1.0.0-rc1` is invalid; use `1.0.0rc1`.

## Common classifiers (the few you need)

```toml
classifiers = [
    "Development Status :: 4 - Beta",       # 1=Planning, 4=Beta, 5=Production/Stable
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries",
    "Typing :: Typed",                      # if you ship type hints
]
```

Full list: https://pypi.org/classifiers/.

## Entry points (CLI commands + plugin systems)

```toml
[project.scripts]
my-cli = "my_package.cli:main"              # `my-cli` command runs my_package.cli.main()

[project.entry-points."my_package.plugins"]
plugin1 = "my_package.plugins:plugin1"      # plugin discovery via importlib.metadata
```

## Trusted publishing (the modern PyPI auth)

For GitHub Actions, configure **trusted publishing** in PyPI project settings -- no API token needed, uses OIDC. Workflow:

```yaml
- uses: pypa/gh-action-pypi-publish@release/v1
```

Requires PyPI project to have the GH org/repo/workflow registered. Token-free, audit-friendly.

## Official docs

- PEP 621 (pyproject.toml `[project]` table): https://peps.python.org/pep-0621/
- PEP 517 (build backends): https://peps.python.org/pep-0517/
- PEP 561 (`py.typed` marker): https://peps.python.org/pep-0561/
- PEP 440 (version specifiers): https://peps.python.org/pep-0440/
- packaging.python.org tutorials: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- setuptools `pyproject.toml`: https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html
- hatchling: https://hatch.pypa.io/latest/config/build/
- flit_core: https://flit.pypa.io/
- twine: https://twine.readthedocs.io/
- `python -m build`: https://build.pypa.io/
- TestPyPI: https://test.pypi.org/
- PyPI trusted publishers: https://docs.pypi.org/trusted-publishers/
- PyPI classifiers: https://pypi.org/classifiers/

## Related

- `python-packaging/SKILL.md` -- decision tree (when to package, src vs flat, build backend choice)
- `uv-package-manager` skill -- modern dep management that pairs with this
- `python-tdd/references/framework-config.md` -- pytest config that lives in the same `pyproject.toml`
