# Audit Documentation

Use the `documentation-engineer` agent to audit existing documentation and identify:

- Outdated content (doesn't match current code)
- Duplicates (same topic in multiple places)
- Missing docs (undocumented public APIs)
- Broken links
- Orphaned pages (not linked from anywhere)

Target: $ARGUMENTS

## Quick Examples

- `/audit-docs` - Audit all documentation in the project
- `/audit-docs docs/` - Audit only the docs folder
- `/audit-docs README.md` - Check if README matches current code
