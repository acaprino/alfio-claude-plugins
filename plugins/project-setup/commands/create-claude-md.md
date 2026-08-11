---
name: create-claude-md
description: >
  Ask the questionnaire first, then write a file sized to the codebase.
  TRIGGER WHEN: the user asks to create/generate/scaffold a CLAUDE.md for a project that doesn't have one.
  DO NOT TRIGGER WHEN: auditing or updating an existing one (use /project-setup:maintain-claude-md).
subagent: project-setup:claude-md-auditor
---

# Create CLAUDE.md File

This command launches an interactive session to create a new `CLAUDE.md` file perfectly tailored to your project and preferences.

## Pre-flight: detect existing deep-dive output

Before the agent starts its own bottom-up analysis, check whether the project already has technical-reference output on disk from a previous `/codebase-xray:analyze` session:

```bash
ls .deep-dive/01-structure.md .deep-dive/02-interfaces.md 2>/dev/null
```

If both files exist, prompt the user:

```
Found .deep-dive/ from a previous /codebase-xray:analyze session.
Available technical references:
  - 01-structure.md (file inventory, dependency graph, entry points, naming conventions)
  - 02-interfaces.md (public APIs, contracts, "How to Add a New Module")
  - 05-risks.md [if present] (anti-patterns, red flags, tech debt)
  - 03-flows.md / 04-semantics.md / 07-final-report.md [if --depth=full was used]

Use these as the technical source for CLAUDE.md? You'll still answer the
workflow/preferences questions interactively.

  [Y] Use deep-dive output (faster, claims already verified)
  [n] Re-analyze bottom-up (full discovery from scratch)
```

If the user accepts, the spawned `claude-md-auditor` agent skips Phase 1 (Bottom-Up Discovery) and ingests `.deep-dive/01-structure.md` and `.deep-dive/02-interfaces.md` as ground truth, with 3-5 spot-checks against current code to confirm freshness. See the agent's "Phase 0: Deep-Dive Detection" section for the full protocol.

If the user declines (or `.deep-dive/` is absent), the agent does its own bottom-up analysis as in step 1 below.

## What This Does

The agent will:
1. Analyze your project bottom-up (dependencies, entry points, source, config, tests, docs) -- OR ingest `.deep-dive/` if the pre-flight check accepted that shortcut
2. Ask you questions about your workflow and preferences
3. Clarify any ambiguous patterns found in the codebase
4. Generate a concise, accurate `CLAUDE.md` following best practices
5. Detect whether the project has a test suite and, if so, offer the canonical `## Test-Suite Rules` block (on by default)
6. Verify all claims against your actual codebase
7. Review the draft with you before finalizing

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
- Evergreen project-structure map: top-level layout, repeating structural patterns, role per category. File-by-file annotation only where names alone do not reveal purpose, where the file is itself a key entry point, or to disambiguate sibling names with overlapping roles. No exhaustive trees
- Tailored to your specific project and preferences
- All claims verified against codebase
- Verification commands to confirm accuracy
- Follows WHAT/WHY/HOW structure
- Includes a canonical `## Working Principles` section (5 principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution, Centralize Shared Logic). Principles 1-4 are inspired by upstream agentic-coding meta-rules and each carries 3 inline sub-bullets covering the deeper guidance (root-cause analysis, evergreen tests, surgical diffs); principle 5 enforces DRY / Single Source of Truth for external calls and cross-cutting concerns. The block is always inserted inline - never linked to an external file
- When the project has tests (offered, on by default): the canonical `## Test-Suite Rules` block (7 binding rules: search before writing, one mirrored test file per source file, explicit layers, behavior over implementation, no skip markers to get green, no weakened assertions, delete tests with the feature). Self-contained and inserted inline, in the HOW group
- Single entry point -- references existing docs/ for deep dives, but no satellite structure files

## Best Practices Built In

Your new CLAUDE.md will:
- Include an evergreen project-structure map: top-level layout, repeating structural patterns, role of each category. Avoid exhaustive file-by-file trees (they decay on every add/rename and add tokens without evergreen value); Claude recovers transient details via Glob on demand. File-by-file annotation only where the name alone is ambiguous, where the file is a key entry point, or to disambiguate sibling names
- Scale length to project complexity, but stay under ~40k characters (Claude Code performance warning threshold). If the project needs more, link out to `docs/` instead of inlining
- Reference files instead of duplicating code
- Delegate style enforcement to linters
- Include only universally applicable guidance
- Be grounded in actual codebase reality
- Be self-contained -- no satellite files needed
- Mark unverifiable claims with `[UNVERIFIED]` and resolve before finalizing
- Use regular hyphens `-` or `--`, never em dashes
- Avoid internal duplication: each file path, pointer, and external resource appears once unless every occurrence carries a genuinely distinct directive (e.g., "where the doc lives" in one section and "what rule to follow when modifying it" in another, with an anti-pattern example). Before finalizing, the agent runs the Phase 4b dedup pass on the draft itself and surfaces any candidate duplicates as per-finding questions
- Always embed the `## Working Principles` block inline (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution, Centralize Shared Logic - with 3 deeper-meta-rule sub-bullets under each of principles 1-4) so Claude approaches every task with explicit assumptions, minimal code, surgical edits, verifiable success criteria, and DRY-by-default routing of shared logic through single utilities. The block is self-contained and never replaced with an external link
- Embed the `## Test-Suite Rules` block inline when the project has a test suite, so agents extend existing tests instead of piling up parallel files, keep layers explicit, and never soften a failing assertion to get CI green

## Related Commands

- `/maintain-claude-md` - Audit and improve existing CLAUDE.md
- `/codebase-xray:analyze` - Run first to generate `.deep-dive/` technical references; this command can then ingest them as the structure backbone
