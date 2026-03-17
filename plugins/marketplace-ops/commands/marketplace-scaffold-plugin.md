---
description: "Scaffold a new plugin with proper directory structure, starter files, and marketplace.json registration"
argument-hint: "<plugin-name> [--with-agent] [--with-skill] [--with-command] [--category <cat>]"
---

# Scaffold New Plugin

Create a new plugin following anvil-toolset conventions.

## Procedure

### 1. Parse arguments

- `plugin-name`: required, kebab-case
- `--with-agent`: create an agent .md starter
- `--with-skill`: create a skill directory with SKILL.md starter
- `--with-command`: create a command .md starter
- `--category`: plugin category (default: "utilities")
- If no --with flags, ask the user what components they want

### 2. Create directory structure

```
plugins/<plugin-name>/
  agents/          (if --with-agent)
  skills/          (if --with-skill)
  commands/        (if --with-command)
```

### 3. Create starter files

**Agent starter** (`agents/<plugin-name>.md`):
```markdown
---
name: <plugin-name>
description: >
  [FILL: When/how to use this agent]
model: opus
color: [FILL: pick from red, blue, green, yellow, purple, orange, pink, cyan]
---

# ROLE
[FILL: Agent purpose]

# CAPABILITIES
[FILL: What this agent does]
```

**Skill starter** (`skills/<skill-name>/SKILL.md`):
```markdown
---
name: <skill-name>
description: "[FILL: When/how to use this skill]"
---

# [Skill Title]

[FILL: Skill instructions]
```

**Command starter** (`commands/<command-name>.md`):
```markdown
---
description: "[FILL: What this command does]"
argument-hint: "[FILL: expected arguments]"
---

# [Command Title]

[FILL: Command procedure]
```

### 4. Register in marketplace.json

Add entry to `plugins[]` array:
```json
{
  "name": "<plugin-name>",
  "source": "./plugins/<plugin-name>",
  "description": "[FILL]",
  "version": "1.0.0",
  "author": { "name": "Alfio" },
  "license": "MIT",
  "keywords": ["<plugin-name>"],
  "category": "<category>",
  "strict": false,
  "agents": [...],
  "skills": [...],
  "commands": [...]
}
```

### 5. Bump metadata.version

Increment the marketplace metadata.version.

### 6. Report

Show created files and remind user to fill [FILL] placeholders.
