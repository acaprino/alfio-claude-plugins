# Figs Conventions Reference

## Agent Color Palette

Valid colors: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`

### Semantic Color Guidance

- **Warm** (red, orange, yellow, pink) -- creative, outward-facing, marketing, content
- **Cool** (blue, cyan, purple) -- analytical, development, code quality
- **Neutral** (green) -- tooling, infrastructure, utilities

All agents within a plugin should use the same color. Avoid reusing a color across more than 3 plugins.

## Plugin Categories

Valid categories: `review`, `development`, `frontend`, `ai-ml`, `utilities`, `infrastructure`, `research`, `business`, `documentation`, `mobile`, `optimization`, `marketing`, `payments`, `workflow`, `productivity`

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

## Skill SKILL.md Structure

```yaml
---
name: skill-name
description: >
  Third-person description with specific triggers.
  Include WHEN to use and WHAT it does.
---
```

Body: under 500 lines, imperative tone, only context Claude lacks.
Progressive disclosure: split into references/ when exceeding ~300 lines.
