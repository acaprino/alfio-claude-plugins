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
python plugins/marketplace-ops/skills/marketplace-audit/scripts/audit_marketplace.py
```

### Step 2: Review findings

The script checks:

1. **File existence** - Every path in marketplace.json agents/skills/commands arrays resolves to a real file or directory
2. **Orphaned files** - Agent .md files, skill directories, or command .md files on disk not registered in any plugin
3. **Frontmatter validation**
   - Agents: must have `name`, `description`, `model`, `color`
   - Skills: must have `name`, `description`
   - Commands: must have `description`
4. **Naming conventions**
   - All names are kebab-case
   - Agent filename matches frontmatter `name` field
   - Plugin directory name matches marketplace.json `name` field
5. **Marketplace.json schema**
   - Every plugin has: name, source, description, version, author, license, keywords, category, strict
   - No duplicate plugin names
   - No duplicate keywords across plugins (warning only)
6. **Version sanity**
   - All versions are valid semver
   - metadata.version is present

### Step 3: Fix issues

Address findings by severity:

- **CRITICAL**: Missing referenced files, broken paths, missing required frontmatter
- **WARNING**: Orphaned files, naming mismatches, overlapping keywords
- **INFO**: Suggestions for improvement, consolidation opportunities

### Step 4: Re-validate

Run the script again after fixes to confirm a clean audit.
