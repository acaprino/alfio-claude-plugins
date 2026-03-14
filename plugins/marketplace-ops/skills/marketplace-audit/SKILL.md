---
name: marketplace-audit
description: >
  Validate anvil-toolset marketplace integrity -- checks marketplace.json
  consistency, verifies all referenced files exist, validates frontmatter
  fields, detects orphaned plugins/skills/agents/commands, and reports
  naming convention violations. Use when auditing, validating, or
  troubleshooting the plugin marketplace.
---

# Marketplace Audit

Run a comprehensive structural validation of the anvil-toolset marketplace.

## Audit steps

### Step 1: Run the validation script

Execute the audit script to get a machine-readable report:

```bash
# Validate only
python plugins/marketplace-ops/skills/marketplace-audit/scripts/audit_marketplace.py

# Validate and auto-fix color issues (invalid, missing, disharmonious)
python plugins/marketplace-ops/skills/marketplace-audit/scripts/audit_marketplace.py --fix
```

### Step 2: Review findings

The script checks:

1. **File existence** - Every path in marketplace.json agents/skills/commands arrays resolves to a real file or directory
2. **Orphaned files** - Agent .md files, skill directories, or command .md files on disk not registered in any plugin
3. **Frontmatter validation**
   - Agents: must have `name`, `description`, `model`, `color`
   - Skills: must have `name`, `description`
   - Commands: must have `description`
4. **Color consistency and harmony**
   - All agents within a plugin should use the same color
   - Warn when a single color is overused across too many plugins (>3)
   - Report color distribution across all plugins
   - Valid colors: red, blue, green, yellow, purple, orange, cyan, magenta, violet, teal, indigo, gold, rust, pink
   - Use `--fix` to auto-correct invalid or missing colors
5. **Naming conventions**
   - All names are kebab-case
   - Agent filename matches frontmatter `name` field
   - Plugin directory name matches marketplace.json `name` field
   - Workflow command output directories match command filename (e.g., `feature-e2e.md` uses `.feature-e2e/`)
   - No naming collisions between commands in different plugins (e.g., two plugins both defining `full-review.md`)
   - Skill directory name matches frontmatter `name` field
   - No em dash characters anywhere (use hyphen `-` or double hyphen `--`)
6. **Cross-reference consistency**
   - Marketplace `name` matches git remote repo name
   - Each plugin `name` matches its source directory name
   - Marketplace `name` matches CLAUDE.md project header
7. **Marketplace.json schema**
   - Every plugin has: name, source, description, version, author, license, keywords, category, strict
   - No duplicate plugin names
   - No duplicate keywords across plugins (warning only)
8. **Version sanity**
   - All versions are valid semver
   - metadata.version is present

### Step 3: Fix issues

Address findings by severity:

- **CRITICAL**: Missing referenced files, broken paths, missing required frontmatter
- **WARNING**: Orphaned files, naming mismatches, overlapping keywords, color inconsistencies
- **INFO**: Suggestions for improvement, consolidation opportunities

### Step 4: Evaluate color harmony

After the script passes, review the color distribution in the report output and evaluate semantic harmony:

1. Read each plugin's description and category from marketplace.json
2. Consider the nature of each plugin - similar domains should have visually related colors, distinct domains should contrast
3. Guiding principles:
   - Warm colors (red, orange, yellow, gold, pink) for creative/outward-facing plugins
   - Cool colors (blue, cyan, teal, indigo, violet) for analytical/development plugins
   - Earthy/neutral (green, rust, magenta, purple) for tooling/infrastructure
4. If colors feel disharmonious, propose a new assignment with reasoning and apply after user confirmation

### Step 5: Re-validate

Run the script again after fixes to confirm a clean audit.
