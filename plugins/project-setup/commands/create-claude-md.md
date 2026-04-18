---
name: create-claude-md
description: >
  Create a new CLAUDE.md file tailored to your project through interactive questionnaire.
  TRIGGER WHEN: the user asks to create/generate/scaffold a CLAUDE.md for a project that doesn't have one.
  DO NOT TRIGGER WHEN: auditing or updating an existing CLAUDE.md (use /project-setup:maintain-claude-md).
subagent: project-setup:claude-md-auditor
---

# Create CLAUDE.md File

This command launches an interactive session to create a new `CLAUDE.md` file perfectly tailored to your project and preferences.

## What This Does

The agent will:
1. Analyze your project bottom-up (dependencies, entry points, source, config, tests, docs)
2. Ask you questions about your workflow and preferences
3. Clarify any ambiguous patterns found in the codebase
4. Generate a concise, accurate `CLAUDE.md` following best practices
5. Verify all claims against your actual codebase
6. Review the draft with you before finalizing

## When to Use

- Starting a new project
- Existing project without CLAUDE.md
- Current CLAUDE.md is severely outdated (easier to start fresh)
- Want to establish new team conventions

## Example Questions You'll Be Asked

The agent will ask about:
- **Project context**: What's the main purpose? Development phase?
- **Claude's role**: Feature dev, bug fixing, refactoring, testing?
- **Workflow preferences**: Testing vs deployment focus? Required checks?
- **Patterns**: Preferred code patterns when multiple exist?
- **Documentation style**: Minimal pointers vs detailed guidance?
- **Special considerations**: Monorepo guidance? Environment-specific instructions?

## Example Interactive Flow

```
Agent: I've analyzed the codebase. I found both Redux and Zustand for state management.
       Which should Claude prioritize?
You:   Zustand - we're migrating away from Redux

Agent: Should CLAUDE.md mention the migration?
You:   Yes, note that Redux is legacy

Agent: I see custom hooks in src/hooks/. Should Claude:
       A) Follow existing patterns strictly
       B) Suggest improvements
       C) Create new hooks as needed
You:   A

Agent: Perfect! Generating your CLAUDE.md...
       [Shows draft]
       Should I add anything about API conventions?
You:   Yes, we always use React Query for data fetching

Agent: Done! Created CLAUDE.md (87 lines, all claims verified)
```

## Output

You'll receive:
- New `CLAUDE.md` file sized to project complexity (simple <100, medium <300, complex 500+)
- Detailed project structure with file/directory purpose annotations
- Tailored to your specific project and preferences
- All claims verified against codebase
- Verification commands to confirm accuracy
- Follows WHAT/WHY/HOW structure
- Single entry point -- references existing docs/ for deep dives, but no satellite structure files

## Best Practices Built In

Your new CLAUDE.md will:
- Include detailed project structure mapping files/directories to their purpose
- Scale length to project complexity, but stay under ~40k characters (Claude Code performance warning threshold). If the project needs more, link out to `docs/` instead of inlining
- Reference files instead of duplicating code
- Delegate style enforcement to linters
- Include only universally applicable guidance
- Be grounded in actual codebase reality
- Be self-contained -- no satellite files needed
- Mark unverifiable claims with `[UNVERIFIED]` and resolve before finalizing
- Use regular hyphens `-` or `--`, never em dashes

## Related Commands

- `/maintain-claude-md` - Audit and improve existing CLAUDE.md
