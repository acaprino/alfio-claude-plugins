# Flake8 Plugins Guide for Human-Readable Code

Curated 16-plugin selector list for readability-focused linting. Per-plugin rule walkthroughs live in each plugin's PyPI README; this file is the **selection rationale** + recommended-setup tiers + the small set of rules worth memorizing.

## When to use

Setting up flake8 for a new project, or auditing an existing flake8 / ruff config to see which readability rules are missing. For ruff equivalents, see notes below.

## The curated 16 plugins (the local IP)

Organized in three priority tiers. The tier you adopt depends on team appetite for lint-driven feedback.

### Essential (5) -- highest ROI, install first

| # | Plugin | Codes | Catches |
|---|--------|-------|---------|
| 1 | **flake8-bugbear** | `B` | Likely bugs: mutable default args (B006), bare `except` (B001), function-call defaults (B008) |
| 2 | **flake8-simplify** | `SIM` | Pythonic alternatives: nested-if collapse (SIM102), `contextlib.suppress` (SIM105), ternary (SIM108) |
| 3 | **flake8-cognitive-complexity** | `CCR` | Sonar cognitive-complexity score per function (15 default threshold) |
| 4 | **pep8-naming** | `N` | snake_case / PascalCase / SCREAMING_SNAKE_CASE compliance |
| 5 | **flake8-docstrings** | `D` | PEP 257: missing docstrings, imperative mood, period termination |

### Recommended (7) -- catches subtler issues

| # | Plugin | Codes | Catches |
|---|--------|-------|---------|
| 6 | **flake8-comprehensions** | `C4` | Wasteful comprehension patterns (`list(map(...))`, `dict([(k,v)])`) |
| 7 | **flake8-expression-complexity** | `ECE` | Too-complex single expressions (lambda chains, deep ternaries) |
| 8 | **flake8-functions** | `CFQ` | Function length, parameter count, return count |
| 9 | **flake8-variables-names** | `VNE` | Single-letter / numeric / shadowed names |
| 10 | **tryceratops** | `TC` | try/except antipatterns (catching too broad, raise-from-from, abuse-of-finally) |
| 11 | **flake8-builtins** | `A` | Shadowing built-ins (`list = ...`, `id = ...`, `type = ...`) |
| 12 | **flake8-eradicate** | `E800` | Commented-out code (use VCS instead) |

### Optional (4) -- strict / opinionated

| # | Plugin | Codes | Catches |
|---|--------|-------|---------|
| 13 | **flake8-unused-arguments** | `U` | Unused function arguments (often a refactor smell) |
| 14 | **flake8-annotations** | `ANN` | Missing type annotations |
| 15 | **pydoclint** | `DOC` | Docstring/signature mismatch (param name typo, missing param in docstring) |
| 16 | **flake8-spellcheck** | `SC` | Spelling in identifiers and comments (US English dict + custom whitelist) |

## Recommended setup tiers

### Minimal (5)
```bash
pip install flake8 flake8-bugbear flake8-simplify \
            flake8-cognitive-complexity pep8-naming flake8-docstrings
```

### Recommended (12)
```bash
pip install flake8 flake8-bugbear flake8-simplify \
            flake8-cognitive-complexity pep8-naming flake8-docstrings \
            flake8-comprehensions flake8-expression-complexity \
            flake8-functions flake8-variables-names tryceratops \
            flake8-builtins flake8-eradicate
```

### Full (16) -- adds the strict/opinionated tier
```bash
# Plus:
pip install flake8-unused-arguments flake8-annotations pydoclint flake8-spellcheck
```

## Gotchas

- **Cognitive complexity > Cyclomatic complexity** for readability. Cyclomatic counts branches; cognitive penalizes nesting (a triple-nested `if` is exponentially worse than three sequential ones). Use `flake8-cognitive-complexity` (or ruff's `C901`).
- **`flake8-docstrings` checks PEP 257 compliance** but not coverage -- pair with `interrogate` for "% functions with docstrings."
- **`flake8-bugbear B006` is the highest-value single rule** -- mutable default arg is one of the top 3 Python footguns.
- **`tryceratops TRY003` ("avoid specifying long messages outside exception class")** is opinionated -- toggle if your team prefers inline messages.
- **`pep8-naming N803`** flags non-snake_case argument names. Disable for compatibility shims that mirror C library APIs.
- **Spell-check (`flake8-spellcheck`) needs a whitelist file** (`whitelist.txt`) for project-specific terms -- otherwise it flags every brand name and acronym.

## Rules you'll be tempted to disable but shouldn't

- `B006` (mutable default args)
- `B008` (function-call default args, e.g. `datetime.now()` in a default)
- `B904` ("raise without from inside except" -- always preserve traceback chain)
- `SIM102` (collapse nested ifs)
- `SIM105` (`contextlib.suppress` over try/except/pass)
- `N803` / `N806` (snake_case discipline)
- `E800` (no commented-out code -- VCS exists)

## ruff: the 2025+ alternative

`ruff` re-implements most of these in Rust at 100× the speed. Equivalent rule sets:

```toml
[tool.ruff.lint]
select = [
  "E", "W", "F",         # pycodestyle + pyflakes
  "B",                   # flake8-bugbear
  "SIM",                 # flake8-simplify
  "C4",                  # flake8-comprehensions
  "C901",                # cognitive complexity (mccabe-based)
  "N",                   # pep8-naming
  "D",                   # pydocstyle
  "TRY",                 # tryceratops
  "A",                   # flake8-builtins
  "ERA",                 # flake8-eradicate
  "ARG",                 # flake8-unused-arguments
  "ANN",                 # flake8-annotations
  "I",                   # isort
  "UP",                  # pyupgrade
]
```

ruff covers ~95% of the curated 16 plus more. New projects in 2025-2026 should start with ruff; flake8 stays for legacy projects with custom plugin sets.

## Per-plugin documentation

| Plugin | Docs |
|--------|------|
| flake8 (core) | https://flake8.pycqa.org/ |
| flake8-bugbear | https://github.com/PyCQA/flake8-bugbear |
| flake8-simplify | https://github.com/MartinThoma/flake8-simplify |
| flake8-cognitive-complexity | https://github.com/Melevir/flake8-cognitive-complexity |
| pep8-naming | https://github.com/PyCQA/pep8-naming |
| flake8-docstrings | https://github.com/pycqa/flake8-docstrings |
| flake8-comprehensions | https://github.com/adamchainz/flake8-comprehensions |
| flake8-expression-complexity | https://github.com/best-doctor/flake8-expression-complexity |
| flake8-functions | https://github.com/best-doctor/flake8-functions |
| flake8-variables-names | https://github.com/best-doctor/flake8-variables-names |
| tryceratops | https://github.com/guilatrova/tryceratops |
| flake8-builtins | https://github.com/gforcada/flake8-builtins |
| flake8-eradicate | https://github.com/wemake-services/flake8-eradicate |
| flake8-unused-arguments | https://github.com/nhoad/flake8-unused-arguments |
| flake8-annotations | https://github.com/sco1/flake8-annotations |
| pydoclint | https://github.com/jsh9/pydoclint |
| flake8-spellcheck | https://github.com/MichaelAquilina/flake8-spellcheck |
| ruff (modern alternative) | https://docs.astral.sh/ruff/ |

## Cognitive complexity reference

Threshold guidance from Sonar (which flake8-cognitive-complexity adapts):

| Score | Quality |
|-------|---------|
| 0-10 | Clean, easy to understand |
| 11-15 | Moderate -- watch for further additions |
| 16-25 | Hard to understand, refactor candidate |
| 26+ | Untestable in practice |

Default flake8-cognitive-complexity threshold is 15. Lower to 10 for high-discipline projects.

## Related

- `cognitive_complexity_guide.md` -- the full Sonar-derived metric explanation with worked examples
- `anti-patterns.md` -- catalog with detection criteria + impact analysis
- `patterns.md` -- positive refactoring patterns (the alternatives these plugins suggest)
- `python-refactor/SKILL.md` -- workflow that runs these plugins as gates
