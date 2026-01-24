# Refactor Documentation

Use the `documentation-engineer` agent to reorganize, compact, and fix existing documentation:

$ARGUMENTS

This command will:
1. Inventory all existing docs
2. Create a refactoring plan (merge duplicates, fix outdated, restructure)
3. Execute the plan with your approval
4. Verify no content was lost

## Quick Examples

- `/refactor-docs` - Refactor all project documentation
- `/refactor-docs docs/` - Refactor only the docs folder
- `/refactor-docs --plan-only` - Generate plan without executing
- `/refactor-docs --merge-duplicates` - Focus on merging duplicate content
