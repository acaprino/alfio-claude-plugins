---
description: Quick health check for any Claude Code plugin marketplace - validates marketplace.json, checks file references, reports plugin counts and version status. Use when the user asks to validate marketplace.json, check plugin references, or audit structural integrity of a Claude Code plugin marketplace. Not for reviewing plugin content quality (use /marketplace-review) or authoring new plugins.
argument-hint: [--fix] [--verbose]
---

# Marketplace Health Check

Run a quick health check on a Claude Code plugin marketplace at the current project root.

## Procedure

1. Read `.claude-plugin/marketplace.json`
2. Count plugins, agents, skills, commands
3. For each plugin, verify that all referenced files/directories exist
4. Check for orphaned plugin directories not in marketplace.json
5. Validate `metadata.version` is present at the root

## Output format

```
Marketplace Health Report
=========================
Name: <marketplace-name>
Version: X.Y.Z
Plugins: N
  Agents: N across M plugins
  Skills: N across M plugins
  Commands: N across M plugins

Issues found: N
  [CRITICAL] ...
  [WARNING] ...

Status: HEALTHY | NEEDS ATTENTION | BROKEN
```

## With --fix flag

Attempt automatic fixes:
- Add orphaned plugin directories to marketplace.json with sensible defaults (user confirms each)
- Remove references to missing files (user confirms each)
- Bump `metadata.version` after fixes

## With --verbose flag

Show per-plugin breakdown with version, category, and asset counts.

## Notes

- This command is marketplace-agnostic. It works against any project with a standard Claude Code plugin layout.
- For the detailed integrity audit (frontmatter validation, naming conventions, color harmony, em-dash detection), use `/skills-validate` or run the audit script directly (`python plugins/marketplace-ops/skills/marketplace-audit/scripts/audit_marketplace.py`).
