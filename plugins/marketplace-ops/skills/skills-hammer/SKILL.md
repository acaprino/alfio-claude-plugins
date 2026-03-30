---
name: skills-hammer
description: >
  Guided creation of ACP components -- skills, agents, commands, and full plugins. Walks through requirements gathering, generates production-ready files with real content (not placeholders), registers in marketplace.json, and bumps versions. Also trigger on "new skill", "new agent", "new plugin", "add a skill", "add an agent", "skills-hammer". Also helps decide skill vs agent architecture when reorganizing plugins. DO NOT TRIGGER for editing or updating existing components -- only for new creation or architectural decisions (skill vs agent).
  TRIGGER WHEN: the user asks to create, add, scaffold, or build a new skill, agent, command, or plugin
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Skills Hammer

Create new ACP components with proper conventions and real content.

## Decision Flow

Determine what the user wants to create:

```
1. "new skill"   --> Skill Creation workflow
2. "new agent"   --> Agent Creation workflow
3. "new command" --> Command Creation workflow
4. "new plugin"  --> Full Plugin workflow (combines above)
```

If unclear, ask: "What do you want to create -- a skill, agent, command, or full plugin?"

## Skill vs Agent Decision

Before gathering requirements, help the user decide the right component type.

**Key question:** "Does this need its own context/tools/isolation, or is it knowledge that any agent should access?"

- If it's **knowledge, conventions, recipes** --> Skill
- If it needs **isolation, tool restrictions, parallel execution** --> Agent
- If it's a **domain with both knowledge and specialist work** --> Skill + Agent(s)

See [references/skills-vs-agents.md](references/skills-vs-agents.md) for the full decision table, real restructure examples, and anti-patterns.

## Phase 1: Requirements Gathering

Before writing any files, gather enough context to produce real content.

### For Skills

Ask (adapt based on what's already known):
1. What does this skill do? What problem does it solve?
2. What triggers should activate it? (specific user phrases, file types, task patterns)
3. Which plugin should it live in? (existing or new)
4. Does it need bundled resources? (scripts/, references/, assets/)
5. What's the degree of freedom? (rigid workflow vs flexible guidance)

### For Agents

Ask (adapt based on what's already known):
1. What role does this agent fill? What task does it handle?
2. What tools does it need? (Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task -- or all)
3. Which plugin should it live in?
4. What color fits its domain? See [references/conventions.md](references/conventions.md) for the palette and semantic guidance.

### For Commands

Ask (adapt based on what's already known):
1. What does this command do when invoked?
2. What arguments does it expect?
3. Which plugin should it live in?

### For Full Plugins

Ask (adapt based on what's already known):
1. What's the plugin's domain/purpose?
2. What components does it need? (agents, skills, commands)
3. What category? See [references/conventions.md](references/conventions.md) for valid categories.

**Do not ask more than 3-4 questions per message.** Start with the most important, follow up as needed.

## Phase 2: Content Generation

Generate production-ready files with real content -- not [FILL] placeholders.

### Skill Creation

1. Create directory: `plugins/<plugin>/skills/<skill-name>/`
2. Write `SKILL.md` following these rules:
   - Frontmatter: `name` (kebab-case, max 64 chars) and `description` (max 1024 chars, third person, specific triggers)
   - Body: under 500 lines, imperative tone, concise
   - Only add context Claude doesn't already have
   - Progressive disclosure: split into references/ if body exceeds ~300 lines
3. Create `references/`, `scripts/`, `assets/` subdirs only if needed
4. Write any bundled resources

### Agent Creation

1. Create file: `plugins/<plugin>/agents/<agent-name>.md`
2. Write with frontmatter and body following these rules:
   - Frontmatter fields: `name`, `description` (use YAML `>` for multiline), `model: opus`, `color`, optionally `tools`
   - Body: terse keyword-list style, imperative tone, structured with markdown headers
   - Sections: `# ROLE`, `# CAPABILITIES` or `# CORE CAPABILITIES`, `# CONVENTIONS`, `# OUTPUT FORMAT`
   - Simple agents: 60-200 lines; complex agents: up to 800 lines
   - See [references/conventions.md](references/conventions.md) for color palette and style patterns

### Command Creation

1. Create file: `plugins/<plugin>/commands/<command-name>.md`
2. Write with frontmatter: `description`, `argument-hint`
3. Body: step-by-step procedure, clear and actionable

## Phase 3: Marketplace Registration

After files are created:

1. **Read** `.claude-plugin/marketplace.json`
2. **Add paths** to the plugin's `agents`, `skills`, or `commands` arrays
   - Agents: `"./agents/<name>.md"`
   - Skills: `"./skills/<name>"`
   - Commands: `"./commands/<name>.md"`
3. **If new plugin**: add full entry to `plugins[]` with all required fields (name, source, description, version 1.0.0, author, license, keywords, category, strict)
4. **Bump plugin version** (patch for new component in existing plugin)
5. **Bump metadata.version** (patch increment)

## Phase 4: Validation

After registration:

1. Verify the file exists at the registered path
2. Verify frontmatter parses correctly
3. Verify naming conventions (kebab-case, filename matches name field)
4. Verify no em dash characters anywhere
5. Report what was created with file paths

## Anti-patterns

When [scenario], here is what to avoid:

| Scenario | Wrong | Right |
|----------|-------|-------|
| Writing skill descriptions | Vague: "Helps with stuff" | Specific triggers and use cases |
| Writing agent prompts | Verbose prose paragraphs | Terse keyword-list style |
| Skill body length | 800+ lines in SKILL.md | Split into references/ at ~300 lines |
| Creating resources | Empty placeholder dirs | Only create dirs that have files |
| Choosing a plugin | Always create a new one | Prefer adding to existing plugin if domain fits |
| Agent description | First/second person | Third person: "Processes X when Y" |

## Critical Rules

- All names: kebab-case
- Never use em dash -- use hyphen `-` or double hyphen `--`
- Default model for agents: `opus`
- Agent filename must match frontmatter `name` field
- Skill directory name must match frontmatter `name` field
- Always bump both plugin version AND metadata.version
- Stage marketplace.json with component files in same commit
- Write real content, never placeholder text
