# Maintain Documentation

Use the `documentation-engineer` agent to audit and refactor existing documentation:

$ARGUMENTS

This command provides a comprehensive documentation management workflow:

## What This Does

1. **Audit Phase** - Inventories all existing documentation and identifies:
   - Outdated content (doesn't match current code)
   - Duplicate documentation (same topic in multiple places)
   - Missing documentation (undocumented public APIs)
   - Broken links
   - Orphaned pages (not linked from anywhere)

2. **Planning Phase** - Creates a refactoring plan to fix identified issues:
   - Merge duplicate content
   - Update outdated sections
   - Link or archive orphaned pages
   - Fix broken references

3. **Interactive Decision** - Asks if you want to execute the refactoring plan

4. **Execution Phase** (optional) - Applies refactoring with your approval:
   - Reorganizes documentation structure
   - Merges and consolidates content
   - Updates references and links
   - Verifies no content was lost

## When to Use

Use this command when you need to:
- Perform quarterly documentation health checks
- Clean up docs after major codebase refactoring
- Fix scattered or duplicated documentation
- Prepare documentation before onboarding new team members
- Identify gaps in API documentation coverage
- Ensure documentation matches current implementation

## Example Interactive Flow

**Audit-only workflow** (report without changes):
```
You:   /docs-maintain --audit-only

Agent: I've inventoried your documentation. Found:
       - 3 duplicate documentation files
       - 5 outdated sections that don't match code
       - 2 orphaned pages
       - 1 broken link

       [Detailed audit report provided]
```

**Full refactoring workflow** (audit → plan → execute):
```
You:   /docs-maintain

Agent: I've inventoried your documentation. Found:
       - 3 duplicate documentation files
       - 5 outdated sections that don't match code
       - 2 orphaned pages
       - 1 broken link

       Should I create a refactoring plan to fix these?
You:   Yes

Agent: Here's the refactoring plan:
       1. Merge UserAPI.md and user-api-reference.md → api/users.md
       2. Update 5 outdated sections to match current code
       3. Link orphaned pages from main README or archive them
       4. Fix broken link in README.md

       Approve this plan?
You:   Yes

Agent: Executing refactoring...
       ✓ Merged duplicate files
       ✓ Updated outdated sections
       ✓ Fixed orphaned pages
       ✓ Fixed broken links

       Verification: All original content preserved, structure improved
```

## Options/Flags

- `--audit-only` - Generate audit report without creating refactoring plan or executing changes
- `--plan-only` - Generate refactoring plan without executing (stops after planning phase)
- `--merge-duplicates` - Focus specifically on identifying and merging duplicate content
- `[path]` - Target specific folder or file (default: entire project)

**Examples:**
```bash
/docs-maintain                        # Full workflow on entire project
/docs-maintain --audit-only           # Report only, no changes
/docs-maintain --plan-only            # Audit + plan, no execution
/docs-maintain docs/                  # Manage only docs/ folder
/docs-maintain README.md              # Check specific file
/docs-maintain --merge-duplicates     # Focus on duplicates
```

## Issues Detected

The audit phase checks for:

- **Outdated Content** - Documentation that doesn't match current code implementation
- **Duplicate Documentation** - Same topic documented in multiple files
- **Missing Documentation** - Public APIs, classes, functions without docs
- **Broken Links** - References to non-existent files or URLs
- **Orphaned Pages** - Documentation files not linked from any other docs
- **Inconsistent Structure** - Disorganized file hierarchy
- **Stale Examples** - Code examples that no longer work

## Output

**Audit-only mode** produces:
- Comprehensive inventory of all documentation files
- Categorized list of issues with severity levels
- Recommendations for improvements
- No files modified

**Full refactoring mode** produces:
- All audit findings
- Detailed refactoring plan
- Executed changes with verification
- Summary of improvements made
- Confirmation that no content was lost

## Quick Examples

```bash
# Quarterly documentation maintenance
/docs-maintain

# Quick health check without changes
/docs-maintain --audit-only

# Focus on cleaning up duplicates
/docs-maintain --merge-duplicates

# Manage API documentation only
/docs-maintain docs/api/

# Check if README is current
/docs-maintain README.md
```

## Tips for Best Results

1. **Run audit-only first** on large projects to understand scope before refactoring
2. **Target specific folders** for large codebases to manage incrementally
3. **Review the plan** carefully before approving execution
4. **Use version control** - commit before running to easily review or revert changes
5. **Run after major refactors** to keep docs in sync with code changes
6. **Schedule regularly** - quarterly audits prevent documentation debt

## Related Commands

- `/docs-create` - Create NEW documentation from code analysis (use when docs don't exist)
- `/docs-maintain` - Audit and improve EXISTING documentation (use when docs exist but need maintenance)
