# Project Setup Plugin

Expert tools for creating and maintaining `CLAUDE.md` files with ground truth verification and best practices compliance.

## Overview

This plugin provides the `claude-md-auditor` agent that helps you maintain accurate, concise, and effective `CLAUDE.md` files based on research from [humanlayer.dev's guide on writing effective CLAUDE.md files](https://www.humanlayer.dev/blog/writing-a-good-claude-md).

## Key Features

- **Ground Truth Verification**: Validates every claim against actual codebase
- **Obsolescence Detection**: Finds outdated file paths, dependencies, commands
- **Best Practices Compliance**: Checks instruction economy, conciseness, progressive disclosure
- **Interactive Workflow**: Asks questions when encountering ambiguities
- **Tailored Creation**: Generates CLAUDE.md based on your preferences
- **Guided Maintenance**: Audit-only or full improvement workflow with prioritization

## Agents

### claude-md-auditor

Expert auditor for `CLAUDE.md` files that verifies ground truth, detects obsolete information, and ensures alignment with best practices.

**Capabilities:**
- Systematically verifies all technical claims
- Detects stale file references and obsolete dependencies
- Evaluates against best practices (conciseness, instruction economy)
- Interactive questionnaire for creating tailored CLAUDE.md
- Asks clarifying questions when encountering ambiguities
- Generates comprehensive audit reports
- Applies improvements with user approval

## Commands

### /create-claude-md

Creates a new `CLAUDE.md` file through interactive questionnaire.

**What it does:**
- Analyzes project structure
- Asks about workflow preferences
- Clarifies ambiguous patterns
- Generates tailored CLAUDE.md
- Verifies all claims

**When to use:**
- New project without CLAUDE.md
- Starting fresh is easier than fixing existing
- Want to establish new conventions

**Example questions:**
- "I found both Redux and Zustand. Which should Claude prioritize?"
- "Should CLAUDE.md emphasize testing or deployment workflows?"
- "Prefer minimal (<100 lines) or detailed (<300 lines)?"

**Related commands:**
- `/maintain-claude-md` - Audit and improve existing CLAUDE.md

### /maintain-claude-md

Audits and optionally improves your existing `CLAUDE.md` file with ground truth verification.

**What it does:**
- Verifies all claims against codebase
- Detects obsolete information
- Checks best practices compliance
- Presents prioritized findings
- Asks if you want to apply improvements
- If yes: Guided improvement workflow
- If no: Audit report only

**When to use:**
- After major refactoring
- Quarterly maintenance
- Before onboarding new team members
- When Claude seems to have wrong assumptions
- Modernize based on best practices
- After learning what works with Claude

**Example flows:**
1. **Audit-only**: Review findings, no changes applied
2. **Audit + improvements**: Fix critical issues, prioritize improvements, apply changes with approval

**Related commands:**
- `/create-claude-md` - Start fresh instead of improving

## Best Practices Enforced

Based on research from humanlayer.dev:

1. **Conciseness**: Target <300 lines (ideally <100)
2. **Instruction Economy**: Respect ~150-200 instruction limit
3. **Progressive Disclosure**: Reference docs instead of embedding
4. **Ground Truth**: Every claim verifiable in codebase
5. **Pointers Over Copies**: Reference files, don't duplicate code
6. **No Style Policing**: Delegate formatting to linters
7. **Universal Applicability**: Only include always-relevant guidance

## Anti-Patterns Detected

The agent flags these issues:

- ❌ Factually incorrect information
- ❌ References to non-existent files
- ❌ Commands that don't work
- ❌ Obsolete dependencies or tools
- ❌ Code duplication that will go stale
- ❌ Over-instruction (>200 directives)
- ❌ Style rules better handled by linters
- ❌ Invented features not in codebase
- ❌ Vague guidance ("use best practices")

## Example Workflow

### Create New CLAUDE.md

```bash
# Start creation
/create-claude-md

# Agent asks series of questions:
# "What will Claude primarily help with?"
> Feature development and testing

# "I see both class and functional components. Preferred pattern?"
> Functional with hooks

# "Prefer minimal or detailed guidance?"
> Minimal with doc references

# Generates tailored CLAUDE.md (87 lines, all verified)
```

### Maintain Existing CLAUDE.md (Audit Only)

```bash
# Run maintenance
/maintain-claude-md

# Agent analyzes and asks:
# "I found both npm and yarn lock files. Which should CLAUDE.md reference?"
> npm

# Agent presents findings and asks:
# "Would you like me to fix these issues?"
> No

# Receives comprehensive audit report with:
# - ✅ 12 verified claims
# - ❌ 3 incorrect/obsolete claims
# - ⚠️ 2 unverifiable claims
# - Prioritized recommendations
```

### Maintain Existing CLAUDE.md (With Improvements)

```bash
# Start maintenance
/maintain-claude-md

# Agent presents findings:
# Critical: 2 issues
# High Priority: 5 issues
# Medium: 3 issues

# "Would you like me to fix these issues?"
> Yes

# "Should I fix all critical issues?"
> Yes

# "Which high priority should I tackle?"
> Reduce length and remove code duplication

# Applies improvements and shows diff for review
```

## Output Examples

### Audit Report Format

```markdown
# CLAUDE.md Audit Report

**Status:** 🟡 NEEDS IMPROVEMENT
**Lines:** 450 (over recommended 300)
**Verified:** 12/17 claims

## Critical Issues
1. File path src/api/ doesn't exist (actual: src/routes/api/)
2. References webpack but project uses Vite

## High Priority
1. File exceeds 300 lines (should condense)
2. Duplicates content from README
3. Contains code snippets that will go stale

## Recommendations
Priority 1: Fix incorrect paths
Priority 2: Reduce to <300 lines via progressive disclosure
Priority 3: Remove code duplication
```

### Interactive Questions

The agent asks clear, contextual questions:

```markdown
**Context:** I found both GraphQL and REST endpoints.

**Question:** Which API pattern should Claude prioritize?

**Options:**
A) GraphQL (newer, in /graphql directory)
B) REST (legacy, in /api directory)
C) Both (document both patterns)

**Impact:** Affects how Claude approaches API tasks.
```

## Verification

All improvements include verification commands:

```bash
# Verify tech stack
cat package.json | grep -E "react|typescript|vite"

# Verify file structure
ls -la src/routes/api/

# Verify linting setup
cat biome.json
```

## Integration

Works well with other agents:
- **documentation-engineer**: Validates doc references in CLAUDE.md
- **code-reviewer**: Gets architecture insights for WHY section
- **explore agent**: Comprehensive codebase understanding

## Maintenance Recommendations

### Update Triggers
- Major dependency changes
- File/folder restructuring
- Workflow changes
- Tool changes (e.g., ESLint→Biome)

### Regular Audits
- Quarterly scheduled audits
- After major refactors
- When onboarding indicates confusion

### Progressive Disclosure Pattern

Instead of embedding everything in CLAUDE.md:

```markdown
# CLAUDE.md (concise)
For detailed development workflows, see docs/development.md
For API conventions, see docs/api-patterns.md
For testing guidelines, see docs/testing.md
```

## Research Foundation

This plugin implements principles from:
- [Writing a Good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

Key insights applied:
- LLMs can follow ~150-200 instructions reliably
- Claude often deprioritizes "may or may not be relevant" content
- Progressive disclosure prevents information overload
- Ground truth prevents hallucination and drift
- Conciseness improves signal-to-noise ratio

## License

MIT
