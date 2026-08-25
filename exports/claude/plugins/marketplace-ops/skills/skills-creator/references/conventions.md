# Claude Code Plugin Conventions Reference

This reference documents the standard conventions used across Claude Code plugin marketplaces. Individual marketplaces may extend or restrict these conventions in their own `CLAUDE.md` -- always read the target project's CLAUDE.md first.

## Agent Color Palette

Valid colors: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`

### Semantic Color Guidance

- **Warm** (red, orange, yellow, pink) -- creative, outward-facing, marketing, content
- **Cool** (blue, cyan, purple) -- analytical, development, code quality
- **Neutral** (green) -- tooling, infrastructure, utilities

All agents within a plugin should use the same color. Avoid reusing a color across more than 3 plugins.

## Plugin Categories

Plugin categories are marketplace-specific. Read the existing `marketplace.json` to learn the local taxonomy before choosing one; if proposing a new category, confirm with the user.

Common categories observed across marketplaces: `review`, `development`, `frontend`, `ai-ml`, `utilities`, `infrastructure`, `research`, `business`, `documentation`, `mobile`, `optimization`, `marketing`, `payments`, `workflow`, `productivity`, `testing`, `analysis`, `security`, `algotrading`.

## Agent Tools

Available tools for the `tools` frontmatter field (comma-separated):

`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Task`

Omit the `tools` field entirely to allow all tools.

## Marketplace.json Required Fields (per plugin)

```
name, source, description, version, author, license, keywords, category, strict
```

Plus arrays (include only non-empty): `agents`, `skills`, `commands`

Optional: `dependencies`, `optionalDependencies` (arrays of plugin names)

## Naming Rules

- Plugin directories: kebab-case
- Agent filenames: kebab-case `.md`, filename matches `name` frontmatter
- Skill directories: kebab-case, directory name matches `name` frontmatter
- Command filenames: kebab-case `.md`
- No em dash character anywhere -- use `-` or `--`

## Agent Body Structure

Terse keyword-list style, imperative tone. Standard sections:

```
# ROLE
[One-line purpose]

# CORE CAPABILITIES
## 1. [Capability]
- Key behavior
- Key behavior

# CONVENTIONS
- Convention list

# OUTPUT FORMAT
- Format instructions
```

Simple agents: 60-200 lines. Complex agents: up to 800 lines.

## Description Format (Skills and Agents)

The description is the single most important line. It determines activation rate.

### High-Activation Template (97-100%)

```yaml
# Skill description
description: >
  "<Domain summary>" argument-hint: "<usage hint>".
  TRIGGER WHEN: <specific triggers, comma-separated>
  DO NOT TRIGGER WHEN: <exclusions>.

# Agent description (multiline with >)
description: >
  <Domain> expert for <specific tasks>.
  TRIGGER WHEN: <triggers>.
  DO NOT TRIGGER WHEN: <the confusable case> (use <sibling-component> instead).
```

### Rules

- **Directive voice** -- "ALWAYS invoke" or imperative triggers, not "Can be used for"
- **Negative constraint** -- "Do not X directly" prevents Claude from bypassing
- **TRIGGER WHEN always** -- it carries the distinctive vocabulary that routes to this component
- **DO NOT TRIGGER WHEN only when it names a sibling** -- see the rule below
- **Third person** -- "Processes X when Y" not "I process X"
- **Max 1024 characters** per description
- **Under 300 characters** recommended (token budget)
- **Specific trigger phrases** -- list exact words/actions that should activate
- **No term in both the opening sentence and TRIGGER WHEN** -- the trigger line keeps it, the opening sentence yields

### The DO NOT TRIGGER WHEN rule

A `DO NOT TRIGGER WHEN` clause earns its context cost only by naming the component that should handle the case instead. It is a routing instruction, not a disclaimer.

```yaml
# Useless: states the logical inverse of TRIGGER WHEN and discriminates nothing
DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.

# Useful: routes the confusable case to a named sibling
DO NOT TRIGGER WHEN: the target is a Python codebase (use python-dead-code instead).
```

When no confusable sibling exists, omit the clause. Adding one anyway costs every session context and buys no routing accuracy.

### Low-Activation Anti-patterns

- "Helps with stuff" -- vague, no triggers
- "Use when working with Docker" -- passive suggestion, Claude bypasses it
- "Docker expert for containerization" -- no negative constraint, no trigger phrases
- A `DO NOT TRIGGER WHEN` clause naming no sibling -- pure context cost, delete it

## Token Budget

Descriptions are the only part of a component that sits in context in **every** session; the body loads only after invocation. Anything a description restates from its own body is pure cost.

- Each skill/agent costs ~100 tokens at idle (name + description in system prompt)
- All descriptions share a **15,000 character** budget by default
- When total exceeds limit, components may be silently dropped
- Do not enumerate in a description what the body already covers: list the trigger vocabulary, not the feature set

## Skill SKILL.md Structure

```yaml
---
name: skill-name
description: >
  "<What it does>" argument-hint: "<usage hint>".
  TRIGGER WHEN: <triggers>.
  DO NOT TRIGGER WHEN: <exclusions>.
---
```

Body: under 500 lines, imperative tone, only context Claude lacks.
Progressive disclosure: split into references/ when exceeding ~300 lines.

### Optional Frontmatter Fields

- `context: fork` -- runs skill in isolated subagent context
- `allowed-tools` -- restricts which tools the skill can use
- `disable-model-invocation: true` -- prevents auto-triggering (slash-command only)
