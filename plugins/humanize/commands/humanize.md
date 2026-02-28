# Humanize

Use the `humanize` agent to rewrite source code to be more readable and human-friendly without changing its behavior.

**Usage:** Provide file paths, directories, or describe what to clean up.

**Examples:**
- `src/utils.py` — humanize a specific file
- `src/` — humanize all source files in a directory
- `src/api/ --dry-run` — preview changes without modifying files

**What it does:**
- Renames vague variables and parameters to domain-meaningful names
- Removes paraphrase comments and empty boilerplate docstrings
- Adds brief why-comments for non-obvious business logic

**What it does NOT do (by default):**
- Does not reorder code, extract functions, or change control flow
- Does not remove error handling, validations, or imports
- Does not modify test files (unless renaming symbols it renamed in source)

These constraints prevent regressions. If you need deeper restructuring, use `python-refactor` (Python) for full metrics-driven refactoring with OOP transformation and migration checklists.

**Constraints:** Never changes behavior. Validates with tests after each file. Reverts on test failure.

Humanize the following:

$ARGUMENTS
