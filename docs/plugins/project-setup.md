# Project Setup Plugin

> Keep your CLAUDE.md accurate and effective. Audits every claim against your actual codebase, detects outdated information, and generates tailored configuration through interactive questionnaires.

## Agents

### `claude-md-auditor`

Audits `.claude.md` files by verifying ground truth, detecting obsolete information, and checking alignment with best practices.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | .claude.md auditing, creation, verification, improvement |

**Core capabilities:**
- **Ground Truth Verification** - Validates every claim against actual codebase
- **Obsolescence Detection** - Finds outdated file paths, dependencies, commands
- **Best Practices Compliance** - Checks instruction economy, conciseness, progressive disclosure
- **Tailored Creation** - Generates .claude.md based on your preferences
- **Guided Improvement** - Helps prioritize and apply fixes incrementally

**Enforces these best practices:**
- Conciseness (<300 lines, ideally <100)
- Instruction economy (~150-200 instruction budget)
- Progressive disclosure (reference docs, don't embed)
- Pointers over copies (reference files, not code)

## Commands

### `/create-claude-md`

Create a new `.claude.md` file through an interactive questionnaire about your workflow and preferences.

### `/maintain-claude-md`

Audit and optionally improve your existing `.claude.md` file with ground truth verification.

**Two workflows:**
1. **Audit-only**: Review findings, no changes applied
2. **Audit + improvements**: Fix issues with guided prioritization

---

**Related:** [marketplace-ops](marketplace-ops.md) (plugin management and validation)
