---
description: >
  Run ruff, mypy/pyright, vulture, complexipy/radon and pytest, then report prioritized fixes.
  TRIGGER WHEN: the user asks to audit a Python codebase across lint, types, complexity, dead code and coverage, or to prepare a codebase for release review.
  DO NOT TRIGGER WHEN: only one dimension is in scope: restructuring (use /python-development:python-refactor), dead code alone (use /senior-review:code-review --fix), or test writing (use python-development:python-tdd).
argument-hint: "<path> [--strict] [--skip-types] [--skip-coverage]"
---

# Python Audit

End-to-end Python code-quality audit. Runs the five tools that matter most, aggregates findings, and outputs a prioritized fix list.

## CRITICAL RULES

1. **Use uv for tool execution** -- `uvx ruff`, `uvx mypy`, `uvx vulture` when not in project deps; `uv run ...` when they are.
2. **Run all phases in parallel where possible** -- ruff + vulture + complexity can run concurrently; type-check is separate.
3. **Never auto-fix without approval** -- always show the diff / finding count first, ask before applying.
4. **Scale output to scope** -- for small modules report everything; for 10K+ file repos summarize and prioritize.

## Procedure

### Phase 1 -- Lint (ruff)

```bash
uvx ruff check "$ARGUMENTS" --output-format=json > .python-audit/ruff.json
uvx ruff format --check "$ARGUMENTS"
```

Summarize:
- Total issues by rule category (E/F/W/B/I/N/UP/PL/RUF/PERF)
- Top 5 rules by frequency
- Auto-fixable count (`ruff check --fix` preview)

### Phase 2 -- Types (mypy or pyright)

Detect the project's type checker:
- `mypy.ini`, `[tool.mypy]` in pyproject -> mypy
- `pyrightconfig.json`, `basedpyright` in deps -> pyright / basedpyright
- Neither -> run mypy in strict mode

```bash
uvx mypy --config-file pyproject.toml "$ARGUMENTS" > .python-audit/mypy.txt
# or
uvx pyright "$ARGUMENTS" --outputjson > .python-audit/pyright.json
```

Summarize:
- Total errors / warnings
- Hot files (top 5 by error count)
- Missing-annotation clusters (`disallow_untyped_defs` violations)

### Phase 3 -- Dead Code (vulture + ruff unused)

```bash
uvx vulture "$ARGUMENTS" --min-confidence 80 > .python-audit/vulture.txt
uvx ruff check "$ARGUMENTS" --select F401,F811,F841 --output-format=json > .python-audit/ruff-unused.json
```

Apply framework-aware filtering:
- Django: ignore `admin.py` handlers, `models.Meta`, `signals.py`
- FastAPI: ignore `@app.*` / `@router.*` decorated functions
- pytest: ignore `conftest.py` fixtures, `test_*` functions
- click: ignore `@click.command()` / `@click.group()` targets

### Phase 4 -- Complexity (complexipy + radon)

```bash
uvx complexipy "$ARGUMENTS" --max-complexity-allowed 15 > .python-audit/complexipy.txt
uvx radon mi "$ARGUMENTS" -s > .python-audit/radon-mi.txt
uvx radon cc "$ARGUMENTS" -s -a > .python-audit/radon-cc.txt
```

Flag:
- Functions with cognitive complexity > 15
- Files with Maintainability Index < 65 (yellow) or < 20 (red)
- Average cyclomatic complexity per file

### Phase 5 -- Coverage (if --skip-coverage not set)

```bash
uv run pytest --cov=src --cov-report=json:.python-audit/coverage.json --cov-report=term
```

Flag:
- Overall line coverage < 80%
- Files with 0% coverage (genuinely untested vs excluded)
- Branch coverage delta (if measured)

## Report Format

Write consolidated report to `.python-audit/REPORT.md`:

```markdown
# Python Audit Report -- <target> -- <date>

## Summary
- Lint: <N> issues (<M> auto-fixable)
- Types: <N> errors in <K> files
- Dead code: <N> unused items (confidence >= 80%)
- Complexity: <K> functions exceed threshold
- Coverage: <P>% (target 80%)

## Critical (fix before release)
- [path:line] <issue> -- <why it matters>
- ...

## High
- ...

## Medium / polish
- ...

## Auto-fixable (safe to apply)
- `uvx ruff check --fix` resolves <N> issues; diff summary:
- `uvx ruff format` formats <N> files

## Coverage gaps
| File | Lines | Missed | Note |
|------|-------|--------|------|
| ... | ... | ... | ... |
```

## Exit Codes

Return exit code 1 if any critical issues are present and `--strict` is set; otherwise always exit 0 (the report is the value).

## Synergies

- Deep refactoring with metrics -> `/python-development:python-refactor`
- Dead code removal only -> `/senior-review:code-review --fix`
- Adding tests to raise coverage -> `python-development:python-tdd` skill
- CLAUDE.md updates after cleanup -> `/project-setup:maintain-claude-md`
