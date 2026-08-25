# uv Package Manager Reference

`uv` (Astral) is a Rust-rewritten replacement for pip / pip-tools / pipx / virtualenv / pyenv. Most surface lives at https://docs.astral.sh/uv; this file is the recommended workflows + the gotchas + the migration story.

## When to use

Setting up a new Python project with `uv`, migrating from pip / poetry, or wiring `uv` into CI/CD and Docker. For the architectural opinions (when to migrate, lockfile policy), see `uv-package-manager/SKILL.md`.

## The commands you'll actually use daily

| Task | Command |
|------|---------|
| New project | `uv init my-project` |
| Add a dep | `uv add requests` |
| Add a dev dep | `uv add --dev pytest` |
| Add an optional group | `uv add --optional docs sphinx` |
| Sync from lockfile | `uv sync` |
| Sync with dev + extras | `uv sync --all-extras --dev` |
| Run a command in the env | `uv run pytest` |
| Run a script with inline deps | `uv run script.py` |
| Install a tool globally | `uv tool install ruff` |
| Pin Python version | `uv python install 3.12` then `uv python pin 3.12` |
| Rebuild lockfile from scratch | `uv lock --upgrade` |

## Gotchas

- **`uv.lock` is the source of truth in CI** -- always pass `--frozen` to `uv sync` so CI fails if the lockfile is out of date instead of silently regenerating it. Without `--frozen`, "works on my machine" lockfile drift goes undetected.
- **`uv venv` creates `.venv` automatically** at project root -- don't fight it. If you want a custom location, set `UV_PROJECT_ENVIRONMENT=/path/to/venv`.
- **`uv sync` removes packages not in the lockfile**, including ones you `pip install`-ed manually. This is intentional; if you need ad-hoc packages, `uv add` them or use `uv run --with`.
- **`uv add --dev` writes to `[tool.uv.dev-dependencies]` (NOT `[project.optional-dependencies].dev`)** -- the two are separate by design. Optional groups are user-installable; dev deps are project-internal.
- **`uv pip install` works** for pip-compatible workflows, but does NOT update `pyproject.toml` or the lockfile. Use only for one-off installs in throwaway venvs.
- **Workspaces** (`[tool.uv.workspace]`) are uv-specific -- they share a single lockfile across multi-package monorepos. `uv add --path ./packages/foo` for cross-package deps.
- **`uv tool install` is the modern pipx**. Tools live in isolated venvs under `~/.local/share/uv/tools/`. Use `uv tool run <tool>` (or `uvx <tool>`) for one-shot runs without persistent install.
- **Python version pinning**: `uv python pin 3.12` writes `.python-version`. CI: `uv python install 3.12` ensures it's available. uv manages Python interpreters itself -- no need for pyenv.
- **`uv sync --frozen --no-dev`** in production Dockerfiles -- skip dev deps, fail on stale lock.
- **Cache location**: `~/.cache/uv/` (Linux/macOS), `%LOCALAPPDATA%\uv\cache\` (Windows). `uv cache prune` cleans unreferenced entries.

## CI/CD pattern (GitHub Actions)

```yaml
- uses: actions/checkout@v4
- uses: astral-sh/setup-uv@v2
  with: { enable-cache: true }
- run: uv python install 3.12
- run: uv sync --all-extras --dev --frozen      # <-- --frozen is the key flag
- run: uv run pytest
- run: uv run ruff check .
```

`astral-sh/setup-uv@v2` handles caching automatically. With `enable-cache: true`, the `~/.cache/uv` lookup is keyed on `uv.lock`.

## Docker pattern (multi-stage, prod-ready)

```dockerfile
# Stage 1: build deps with uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project    # deps only, no app code

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "my_package"]
```

`--no-install-project` skips installing the project code itself -- the next stage adds it. This way Docker layer cache only invalidates on dep changes, not source changes.

## Workspace (monorepo) layout

```
monorepo/
├── pyproject.toml                   # root: declares workspace
├── uv.lock                          # ONE shared lockfile
├── packages/
│   ├── package-a/
│   │   └── pyproject.toml
│   └── package-b/
│       └── pyproject.toml
```

Root `pyproject.toml`:
```toml
[tool.uv.workspace]
members = ["packages/*"]
```

In `package-b/pyproject.toml`, depend on package-a:
```toml
dependencies = ["package-a"]

[tool.uv.sources]
package-a = { workspace = true }
```

`uv sync` from root installs both packages in editable mode against the shared `.venv`.

## Migration from pip / poetry / pipenv

| From | Migration step |
|------|----------------|
| **pip + requirements.txt** | `uv init`, then `uv add $(cat requirements.txt)`. Move dev deps via `uv add --dev`. |
| **poetry** | `uv init`, copy `[tool.poetry.dependencies]` deps to `[project.dependencies]`, run `uv lock`. Poetry's `^` becomes `>=` (or pin manually). |
| **pipenv** | `uv init`, port `[packages]` and `[dev-packages]` from Pipfile to `[project.dependencies]` / `[tool.uv.dev-dependencies]`. |
| **pyenv** | `uv python install <version>` replaces pyenv. `.python-version` is shared with pyenv -- works in both. |
| **pipx** | `uv tool install <tool>` replaces pipx. Tools live under `~/.local/share/uv/tools/`. |

## Inline script metadata (PEP 723)

uv can run a single script with inline dep declarations:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "rich"]
# ///

import requests
from rich import print
print(requests.get("https://httpbin.org/json").json())
```

`uv run script.py` resolves and installs deps in a one-shot venv. Great for tutorials, gists, throwaway tools.

## Performance notes (why people switch)

- 10-100× faster than pip for resolution + install (Rust + parallel)
- Single binary, no Python required to run uv itself
- One unified lockfile vs poetry/pipenv's varied formats
- Native virtualenv management (no need for separate `python -m venv`)

## Official docs

- uv home: https://docs.astral.sh/uv/
- Project structure: https://docs.astral.sh/uv/concepts/projects/
- Workspaces: https://docs.astral.sh/uv/concepts/projects/workspaces/
- Tools (pipx replacement): https://docs.astral.sh/uv/concepts/tools/
- Python interpreter management: https://docs.astral.sh/uv/concepts/python-versions/
- Lockfile format: https://docs.astral.sh/uv/concepts/projects/sync/
- pip interface (compat): https://docs.astral.sh/uv/pip/
- GitHub Actions: https://docs.astral.sh/uv/guides/integration/github/
- Docker: https://docs.astral.sh/uv/guides/integration/docker/
- PEP 723 (inline script metadata): https://peps.python.org/pep-0723/

## Related

- `uv-package-manager/SKILL.md` -- the architectural opinions and migration playbook
- `python-packaging/references/packaging-guide.md` -- the publish side that uv supports via `uv build` + `uv publish`
- `python-tdd/references/framework-config.md` -- pytest config in the same `pyproject.toml`
