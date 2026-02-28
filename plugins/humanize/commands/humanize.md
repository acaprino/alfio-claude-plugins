# Humanize

Use the `humanize` agent to rewrite source code to be more readable and human-friendly without changing its behavior.

**Usage:** Provide file paths, directories, or describe what to clean up.

**Examples:**
- `src/utils.py` — humanize a specific file
- `src/` — humanize all source files in a directory
- `src/api/ --dry-run` — preview changes without modifying files

**What it does:**
- Renames vague variables and functions to domain-meaningful names
- Removes AI-generated boilerplate and paraphrase comments
- Restructures for narrative reading flow
- Extracts deeply nested logic into named sub-functions
- Removes dead code and useless error handlers

**Constraints:** Never changes behavior, never renames public exports without warning.

Humanize the following:

$ARGUMENTS
