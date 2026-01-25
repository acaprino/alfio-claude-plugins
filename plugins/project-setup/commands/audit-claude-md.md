---
name: audit-claude-md
description: Audit .claude.md file for accuracy, obsolete information, and best practices compliance
subagent: project-setup:claude-md-auditor
---

# Audit .claude.md File

This command launches the claude-md-auditor agent to verify your `.claude.md` file contains accurate, up-to-date information grounded in your actual codebase.

## What This Does

The agent will:
1. Read your `.claude.md` file
2. Verify every claim against your actual codebase
3. Detect obsolete file paths, dependencies, or commands
4. Check for best practices (conciseness, progressive disclosure, instruction economy)
5. Ask you questions when encountering ambiguities
6. Generate a detailed audit report with prioritized fixes
7. Optionally apply improvements if you approve

## When to Use

- After major refactoring or restructuring
- When you suspect `.claude.md` is outdated
- Before onboarding new team members
- Quarterly maintenance check
- After significant dependency updates
- When Claude seems to be working from wrong assumptions

## Example Usage

Just run the command and the agent will guide you through the audit process:

```
/audit-claude-md
```

The agent may ask questions like:
- "I found both npm and yarn - which package manager should .claude.md reference?"
- "Should deprecated features still be documented for backward compatibility?"
- "I see multiple data fetching patterns - which is preferred?"

## Output

You'll receive:
- Comprehensive audit report
- List of verified vs incorrect claims
- Obsolete information flagged
- Best practices assessment
- Prioritized recommendations
- Optional: Improved version of .claude.md

## Related Commands

- `/create-claude-md` - Create new .claude.md from scratch (interactive)
- `/improve-claude-md` - Guided improvement of existing .claude.md
