---
name: python-refactor
description: >
  Restructure tangled code into a clear equivalent, preserving behavior.
  TRIGGER WHEN: the user asks for "readable", "maintainable" or "clean" code, a review flags comprehension issues, or the task is legacy modernization or onboarding cleanup.
---

# Python Refactor

Transform complex Python into clear, maintainable code while preserving correctness. Phased workflow with safety-by-design and continuous validation. For deep references (anti-patterns, OOP principles, cognitive complexity, regression prevention), see the `references/` directory.

## When to invoke

- Explicit "human", "readable", "maintainable", "clean", or "refactor" request
- Code review flags comprehension or maintainability issues
- Legacy code modernization
- Onboarding / educational contexts
- Complexity metrics exceed thresholds
- **Red flags**: file > 500 lines with scattered functions and global state, multiple `global` statements, no clear module/class organization, configuration mixed with business logic

## Do NOT invoke when

- Code is performance-critical and profiling shows perf optimization is needed first
- Code is scheduled for deletion or replacement
- External dependencies require upstream contributions instead
- User explicitly requested perf optimization over readability

## Core principles (priority order)

1. **Prefer structured OOP for complex code** -- shared state, multiple concerns, scattered globals = restructure into classes/modules. (But: simple modules with pure functions, click/argparse CLIs, and functional pipelines DON'T need to be forced into classes.)
2. **Clarity over cleverness** -- explicit beats implicit
3. **Preserve correctness** -- all tests pass, behavior identical
4. **Single Responsibility** -- one thing per class/function (SOLID)
5. **Self-documenting structure** -- code = what, comments = why
6. **Progressive disclosure** -- reveal complexity in layers
7. **Reasonable performance** -- never sacrifice >2× without explicit approval

## Hard constraints

- **SAFETY BY DESIGN** -- mandatory migration checklists for destructive changes. CREATE → SEARCH → MIGRATE → VERIFY → only then REMOVE. NEVER remove before 100% migration verified.
- **STATIC ANALYSIS FIRST** -- `flake8 --select=F821,E0602` (or `ruff check --select=F821`) BEFORE tests. Catches NameErrors immediately.
- **PRESERVE BEHAVIOR** -- all existing tests pass after.
- **NO PERF REGRESSION** -- never degrade > 2× without explicit approval.
- **NO API CHANGES** -- public APIs unchanged unless explicitly requested + documented.
- **NO OVER-ENGINEERING** -- simple stays simple.
- **NO MAGIC** -- no framework magic, no metaprogramming unless absolutely necessary.
- **VALIDATE CONTINUOUSLY** -- static analysis + tests after each logical change.

## Regression prevention (MANDATORY)

**Refactoring must NEVER introduce regressions.** Read `references/REGRESSION_PREVENTION.md` before any session.

Before each session:
- Test suite passes 100%
- Coverage ≥ 80% on target code (write tests FIRST if not)
- Golden outputs captured for critical edge cases
- Static analysis baseline saved

After EACH micro-change (not at the end -- every single one):
- `flake8 --select=F821,E999` → 0 errors
- `pytest -x` → all passing
- Spot check 1 edge case for unchanged behavior

If ANY check fails: **STOP → REVERT → ANALYZE → FIX APPROACH → RETRY**.

ANY REGRESSION = TOTAL FAILURE.

## Workflow (4 phases)

### Phase 1: Analysis

1. Read the entire codebase section.
2. Identify readability issues using `references/anti-patterns.md` (script-like/global-state, God Objects, nested conditionals, long functions, magic numbers, cryptic names).
3. Assess architecture against `references/oop_principles.md` (proper classes/modules, encapsulated state, separated responsibilities, SOLID, DI vs hard-coded deps).
4. Measure current metrics with `scripts/measure_complexity.py` or `scripts/analyze_multi_metrics.py`.
5. Run linting analysis (see Tooling below).
6. Check test coverage; identify gaps to fill BEFORE refactoring.
7. Document with `assets/templates/analysis_template.md`.

**Output**: prioritized list of issues by impact and risk.

### Phase 2: Planning

1. **Classify each change**:
   - **Non-destructive** (rename, docs, type hints) → low risk
   - **Destructive** (remove globals, delete functions, replace APIs) → high risk
2. **For DESTRUCTIVE changes -- migration plan is MANDATORY**:
   - Search ALL usages of each element to be removed
   - Document every usage (file, line, type)
   - **No complete migration plan = cannot proceed with the destructive change**
3. Risk assessment per change (Low/Medium/High)
4. Dependency map -- what depends on this code?
5. Test strategy -- what tests are needed? what might break?
6. Order changes safest → riskiest
7. Document expected metric improvements

**Output**: refactoring plan, sequenced changes, migration plans, test strategy, rollback plan.

### Phase 3: Execution

#### Non-destructive (safe anytime)
1. Rename for clarity
2. Extract magic numbers/strings to named constants
3. Add/improve docs and type hints
4. Add guard clauses to reduce nesting

#### Destructive (STRICT PROTOCOL)
1. **CREATE** new structure (no removal) -- write new classes/functions + tests
2. **SEARCH** for ALL usages of the element being removed
3. **CREATE** migration checklist documenting every found usage
4. **MIGRATE** one usage at a time, checking off the list, running static analysis + tests after each
5. **VERIFY** complete migration -- re-run searches, should find zero old references
6. **REMOVE** old code only after 100% migration verified

#### Execution rules
- NEVER skip the migration checklist for destructive changes
- Run static analysis BEFORE tests
- One pattern at a time -- never mix multiple refactoring patterns in a single change
- Atomic commits -- each migration step gets its own commit
- Stop on ANY error (static analysis OR test failure) → immediate fix/revert

#### Recommended order
1. Transform script-like code to proper architecture (`references/examples/script_to_oop_transformation.md`)
2. Rename for clarity
3. Extract magic numbers/strings to constants/enums
4. Improve docs + type hints
5. Extract methods to reduce function length
6. Simplify conditionals with guard clauses
7. Reduce nesting depth
8. Final review: separation of concerns

### Phase 4: Validation

1. **Static analysis FIRST**:
   ```bash
   flake8 <file> --select=F821,E0602          # undefined names/variables -- MUST be 0
   flake8 <file> --select=F401                # unused imports
   flake8 <file>                              # full quality check
   ```
2. **Full test suite** → 100% pass required.
3. **Architecture validation**: global state eliminated/encapsulated, proper modules/classes, separated responsibilities, SOLID compliance.
4. **Before/after metrics** with `scripts/measure_complexity.py` or `scripts/analyze_multi_metrics.py`.
5. **Performance regression check** with `scripts/benchmark_changes.py` for hot paths.
6. **Summary report** using `assets/templates/summary_template.md`.
7. **Flag for human review** if: perf degraded > 10%, public API signatures changed, test coverage decreased, significant architectural changes.

## Refactoring patterns (catalog summary)

Full catalog with examples in `references/patterns.md`. Key patterns:

- **Guard Clauses** -- early returns instead of nested conditionals
- **Extract Method** -- split large functions into focused units (resets the nesting counter -- most powerful for cognitive complexity)
- **Dictionary Dispatch** -- replace if-elif chains with lookup tables
- **Match Statement** (Py 3.10+) -- counts as +1 total, not per branch
- **Named Boolean Conditions** -- extract complex booleans into named variables
- **Encapsulate Global State** -- move globals into classes with proper encapsulation
- **Group Related Functions** -- organize scattered functions into classes by responsibility
- **Create Domain Models** -- replace primitive dicts with dataclasses + enums
- **Apply Dependency Injection** -- replace hard-coded deps with injected ones

For cognitive complexity calculation rules and reduction strategies, see `references/cognitive_complexity_guide.md`.

### Naming conventions

- **Variables**: descriptive, booleans as `is_active` / `has_permission` / `can_edit`, collections as plurals
- **Functions**: verb + object (`calculate_total`, `validate_email`); boolean queries as `is_valid()` / `has_items()`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`; replace magic numbers/strings
- **Classes**: PascalCase nouns (`UserAccount`, `PaymentProcessor`)

## Anti-patterns to fix (priority order)

Full catalog: `references/anti-patterns.md`.

- **Critical**: script-like / procedural code with global state; God Object / God Class
- **High**: complex nested conditionals (> 3 levels), long functions (> 30 lines), magic numbers, cryptic names, missing type hints, missing docstrings
- **Medium**: duplicate code, primitive obsession, long parameter lists (> 5)
- **Low**: inconsistent naming, redundant comments, unused imports

## Tooling

### Primary stack: Ruff + Complexipy (recommended for new projects)

```bash
uv tool install ruff complexipy radon wily

ruff check src/                                 # fast linting (Rust, replaces flake8+plugins)
complexipy src/ --max-complexity-allowed 15     # cognitive complexity (Rust)
radon mi src/ -s                                # maintainability index
```

Full configuration (pyproject.toml, pre-commit, GitHub Actions): `references/cognitive_complexity_guide.md`.

### Alternative: flake8 + curated plugins

For projects already on flake8, see `references/flake8_plugins_guide.md` (curated 16-plugin selector list).

### Multi-metric analysis

`scripts/analyze_multi_metrics.py` combines complexipy + radon + maintainability index in a single report.

| Metric | Tool | Use |
|--------|------|-----|
| Cognitive complexity | **complexipy** | Human comprehension |
| Cyclomatic complexity | **ruff** (C901), radon | Test planning |
| Maintainability index | radon | Overall code health |

### Metric targets

- Cyclomatic complexity: < 10 per function (warning 15, error 20)
- Cognitive complexity: < 15 per function (SonarQube default; warning 20)
- Function length: < 30 lines (warning 50)
- Nesting depth: ≤ 3 levels
- Docstring coverage: > 80% for public functions
- Type-hint coverage: > 90% for public APIs

### Historical tracking with Wily

Trends matter, not just thresholds. Setup + CI integration: `references/cognitive_complexity_guide.md`.

## Common refactoring mistakes

Full guide: `references/REGRESSION_PREVENTION.md`. Key traps:

1. **Incomplete migration** -- removing old code before ALL usages migrated (causes NameErrors).
2. **Partial pattern application** -- applying refactoring to some functions but not others.
3. **Breaking public APIs** -- changing signatures used by external code.
4. **Assuming tests cover everything** -- tests pass but runtime errors occur (run static analysis!).

## When to reach for which tool

- **clean-code** (cross-language plugin) -- multi-language cosmetic cleanup; renames local vars, improves comments, simplifies structure. Lowest regression risk. Use for "make this readable", "clean up naming."
- **python-refactor** (this skill) -- Python-only deep restructuring. OOP transformation, SOLID, complexity metrics, migration checklists, benchmark validation. Use for "refactor this module", "reduce complexity", "transform to OOP."

**Escalation path**: clean-code → python-refactor (safest to most thorough).

## Integration

- **python-tdd** -- set up tests before refactoring, validate coverage after
- **python-performance-optimization** -- deep profiling before/after
- **python-packaging** -- handle pyproject.toml + distribution if refactoring a library
- **uv-package-manager** -- `uv run ruff`, `uv run complexipy` for tool execution
- **async-python-patterns** -- reference async patterns when refactoring async code

## When NOT to refactor

Perf-critical optimized code (profile first), code scheduled for deletion, external deps (contribute upstream), stable legacy code nobody needs to modify.

## Limitations

Cannot improve algorithmic complexity (that's an algorithm change). Cannot add domain knowledge not in code/comments. Cannot guarantee correctness without tests. Style preferences vary -- adjust to team conventions.

## Examples

`references/examples/`:
- `script_to_oop_transformation.md` -- script → clean OOP architecture (flagship case study)
- `python_complexity_reduction.md` -- nested conditionals and long functions
- `typescript_naming_improvements.md` -- naming patterns (cross-language reference)

## Success criteria

1. **Zero regressions** -- all tests pass, behavior unchanged
2. Golden master match for documented critical cases
3. Complexity metrics improved (documented in summary)
4. No perf regression > 10% (or explicit approval)
5. Documentation coverage improved
6. Code easier for humans to understand
7. No new security vulnerabilities
8. Atomic, well-documented git history
9. Wily trend -- complexity not increased vs previous commit
10. Static analysis shows improvement
