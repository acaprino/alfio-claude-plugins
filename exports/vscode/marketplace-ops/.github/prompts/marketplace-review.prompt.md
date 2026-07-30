---
description: AI-powered quality review of plugin descriptions, trigger keywords, agent prompts, skill instructions, and command definitions in any Claude Code plugin marketplace - evaluates activation accuracy, content quality, and cross-plugin coherence. Use when the user asks to review plugin/agent/skill quality, audit triggers, or evaluate marketplace content. Not for validating marketplace.json structure alone, which /marketplace-health covers, nor for authoring new components, which /marketplace-scaffold-plugin covers.
argument-hint: [plugin-name] [--all] [--fix]
---

# Marketplace AI Review

Perform an AI-driven quality evaluation of plugin content across any Claude Code plugin marketplace.

## What this evaluates

This review goes beyond structural validation (which `/marketplace-health` handles) and analyzes the **semantic quality** of every plugin component using AI judgment.

## Procedure

### Step 1: Load marketplace data

Read `.claude-plugin/marketplace.json` at the project root to get the full plugin registry.

### Step 2: For each plugin (or the specified one), evaluate these dimensions

#### A. Plugin Description Quality (marketplace.json)

Evaluate the `description` field:
- **Clarity**: Is it immediately clear what the plugin does?
- **Trigger coverage**: Does it mention enough trigger scenarios for Claude to auto-invoke?
- **Specificity**: Does it name concrete actions, not just abstract categories?
- **Length**: Under 1024 chars, ideally under 300 for auto-load discoverability
- **Keyword coverage**: Keywords array contains the concrete domain terms users will search for

#### B. Agent Quality (for each agent in the plugin)

Read the agent `.md` file:
- **Description directive voice**: Uses "ALWAYS invoke", "You MUST", "Use PROACTIVELY" or similar (vs passive "Helps with", "Can be used for")
- **TRIGGER WHEN clause**: present, specific, uses concrete verbs / domain terms
- **DO NOT TRIGGER WHEN clause**: present, names sibling conflicts (which other agent should handle this case instead)
- **Body structure**: clear sections (ROLE, CAPABILITIES, CONVENTIONS, OUTPUT FORMAT or similar)
- **Body size**: 60-200 lines for simple agents, up to ~560 lines for complex; flag over 700 lines
- **Tool restrictions**: minimal but sufficient (e.g., a read-only reviewer should NOT have Write/Edit)
- **Model choice**: justified if not `opus`
- **Color consistency**: matches siblings in the same plugin where appropriate

#### C. Skill Quality (for each skill in the plugin)

Read the skill `SKILL.md`:
- **Description**: same directive voice + TRIGGER WHEN / DO NOT TRIGGER WHEN checks as agents
- **Body size**: under 500 lines; larger content should go in `references/`
- **Progressive disclosure**: uses `references/` for deep content, keeps SKILL.md scannable
- **Action-oriented**: teaches what Claude doesn't already know; avoids restating general best practices
- **Examples**: 3-5 `<example>` tags for high-activation skills

#### D. Command Quality (for each command in the plugin)

Read the command `.md` file:
- **Frontmatter shape**: `description` and `argument-hint` as separate YAML keys (not a single concatenated string)
- **Argument hint**: accurate, shows the expected arguments
- **Body**: actionable procedure, not just marketing copy
- **Integration**: references the agent or skill that does the real work

### Step 3: Cross-plugin coherence

- Detect overlapping triggers between plugins (two agents competing for the same activation)
- Detect orphan references (agent X references skill Y that doesn't exist)
- Identify missing sibling-conflict DO NOT TRIGGER clauses when two plugins cover adjacent domains

### Step 4: Report

Write `.marketplace-review/REPORT.md` with:

```markdown
# Marketplace AI Review -- <marketplace-name> -- <date>

## Summary
- Plugins evaluated: N
- Critical issues: K
- Recommendations: M

## Per-plugin findings
### <plugin-name>
- Description score: X/5 -- <reasoning>
- Agents: ...
- Skills: ...
- Commands: ...
- Recommended fixes:
  - [CRITICAL] ...
  - [WARNING] ...

## Cross-plugin observations
- ...
```

### With --fix flag

For each recommendation, offer to apply the fix with user confirmation. Stage changes via `#edit/editFiles`, do not auto-commit.

## Notes

- Marketplace-agnostic: works on any project with a standard Claude Code plugin layout.
- Complements (does not replace) the deterministic audit run by `/marketplace-health` and the detailed lint in `/skills-validate`.
