---
name: improve-claude-md
description: Guided improvement of existing .claude.md with user feedback and prioritization
subagent: project-setup:claude-md-auditor
---

# Improve .claude.md File

This command launches an interactive session to improve your existing `.claude.md` through guided refinement based on audit findings and your priorities.

## What This Does

The agent will:
1. Audit your current `.claude.md` file
2. Present findings and issues categorized by priority
3. Ask which improvements you want to prioritize
4. Request your guidance on uncertain decisions
5. Apply improvements iteratively with your feedback
6. Verify changes maintain important context
7. Final review before applying changes

## When to Use

- Current .claude.md needs updating but has good foundation
- Want to modernize .claude.md based on best practices
- After team discussion about what Claude should know
- Periodic maintenance (quarterly recommended)
- After learning what works/doesn't work with Claude

## Example Interactive Flow

```
Agent: I've audited .claude.md. Found 3 critical issues, 5 high priority, 4 medium priority.

       Critical Issues:
       1. File path src/api/ doesn't exist (actual: src/routes/api/)
       2. References webpack but project uses Vite
       3. Command "npm run build:prod" not found in package.json

       Should I fix all critical issues? (Recommended: Yes)
You:   Yes

Agent: Done. High priority issues:
       1. File is 450 lines (recommend <300)
       2. Duplicates code from README
       3. Contains style rules (should delegate to biome.json)
       4. Missing info about Vite build system
       5. Obsolete Redux docs (project uses Zustand)

       Which should I prioritize?
       A) All of them
       B) Just reduce length and remove duplicates
       C) Let me choose individually
You:   B

Agent: I can reduce from 450 to ~180 lines by:
       - Moving detailed guides to docs/development.md
       - Removing code samples (replace with file references)
       - Removing README duplicates

       I found these patterns to potentially document:
       - Custom hooks usage (src/hooks/)
       - API conventions with React Query
       - Feature-based folder structure

       Should I include these?
You:   Yes for hooks and API conventions, skip folder structure

Agent: I see both REST and GraphQL endpoints. Which should Claude prioritize?
You:   GraphQL - REST is legacy

Agent: Here's the improved version (185 lines):
       [Shows diff]
       Apply these changes?
You:   Yes

Agent: Applied! Your .claude.md is now:
       - 185 lines (was 450)
       - All paths verified
       - No code duplication
       - Focuses on hooks, API conventions, GraphQL
       - References docs/development.md for details
```

## Improvement Categories

### Critical (Auto-fix Recommended)
- Factually incorrect information
- Non-existent file paths
- Broken commands
- Obsolete dependencies

### High Priority (Usually Should Fix)
- Excessive length (>300 lines)
- Code duplication
- Missing important context
- Over-instruction (>200 directives)

### Medium Priority (Consider Based on Goals)
- Organizational improvements
- Better progressive disclosure
- Condensing verbose sections
- Adding helpful pointers

### Low Priority (Nice to Have)
- Formatting consistency
- Minor wording improvements
- Additional examples

## Output

You'll receive:
- Updated `.claude.md` based on your priorities
- All critical issues fixed
- User-approved improvements applied
- Diff showing what changed
- Verification commands
- Maintenance recommendations

## Tips for Best Results

1. **Be specific about priorities**: Tell the agent what matters most to your team
2. **Answer pattern questions**: Help agent understand preferred approaches
3. **Review diffs carefully**: Agent shows changes before applying
4. **Provide context**: Explain decisions so agent understands your preferences
5. **Iterate**: It's okay to try improvements and adjust

## Related Commands

- `/audit-claude-md` - Just audit without changes
- `/create-claude-md` - Start fresh instead of improving
