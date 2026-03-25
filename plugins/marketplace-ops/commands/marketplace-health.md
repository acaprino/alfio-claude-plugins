---
description: >
  "Quick marketplace health check -- validates marketplace.json, checks file references, reports plugin counts and version status" argument-hint: "[--fix] [--verbose]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Marketplace Health Check

Run a quick health check on the figs marketplace.

## Procedure

1. Read `.claude-plugin/marketplace.json`
2. Count plugins, agents, skills, commands
3. For each plugin, verify that all referenced files/directories exist
4. Check for orphaned plugin directories not in marketplace.json
5. Validate marketplace metadata.version is present

## Output format

```
Marketplace Health Report
=========================
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
- Add orphaned plugins to marketplace.json with sensible defaults
- Remove references to missing files
- Bump metadata.version after fixes

## With --verbose flag

Show per-plugin breakdown with version, category, and asset counts.
