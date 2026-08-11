---
name: skills-creator
description: >
  Creates new Claude Code plugin components: skills, agents, commands, full plugins. Also decides
  skill vs agent architecture.
  Use when the user asks to create, add, scaffold or build a new skill, agent, command or plugin, or
  says "new skill", "new agent", "new plugin", "skills-creator", "skills-hammer".
  Not for editing or updating an existing component, or auditing marketplace integrity (use
  marketplace-audit instead).
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: marketplace-ops
---

# Skills Creator

Create new Claude Code plugin components (skills, agents, commands, full plugins) with proper conventions and real content. Marketplace-agnostic: read the target `.claude-plugin/marketplace.json` and `CLAUDE.md` for project-specific conventions (author, license, category taxonomy) before scaffolding.

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

## Description Engineering

The `description` field is the single most important line in any skill or agent. It determines whether the component activates at all. Passive descriptions achieve ~50-77% activation; directive descriptions with negative constraints achieve 97-100%.

### The High-Activation Template

```
<Domain> expert. ALWAYS invoke this skill when the user <trigger actions>.
Do not <alternative action> directly.
TRIGGER WHEN: <specific triggers, comma-separated>
DO NOT TRIGGER WHEN: <exclusions>
```

### Examples

```yaml
# BAD (50-77% activation) -- passive, suggestion-style
description: "Helps with Docker containerization tasks"

# GOOD (97-100% activation) -- directive with negative constraint
description: >
  Docker containerization expert. ALWAYS invoke this skill when the user
  asks about Docker, containers, Dockerfiles, or docker-compose.
  Do not run Docker commands or write Dockerfiles directly.
  TRIGGER WHEN: building containers, writing Dockerfiles, debugging Docker issues
  DO NOT TRIGGER WHEN: the task is not about containerization.
```

### Description Rules

1. **Directive voice** -- "ALWAYS invoke" not "Can be used for"
2. **Negative constraint** -- "Do not X directly" prevents Claude from bypassing the skill
3. **Specific trigger phrases** -- list the exact words/phrases that should activate it
4. **Third person** -- "Processes X when Y" not "I process X" or "You should use this"
5. **Max 1024 characters** -- hard limit per description
6. **Include TRIGGER WHEN / DO NOT TRIGGER WHEN** -- explicit activation boundaries

### Token Budget Awareness

Each skill/agent costs ~100 tokens at idle (just name + description in system prompt). All descriptions combined share a **15,000 character budget** by default. When total description text exceeds this limit, skills may be silently dropped from the system prompt.

- Keep individual descriptions **under 300 characters** when possible
- For the current marketplace (~39 plugins, ~80+ components), monitor total description size
- Prefer concise trigger lists over verbose explanations

## Phase 1: Requirements Gathering

Before writing any files, gather enough context to produce real content.

### For Skills

Ask (adapt based on what's already known):
1. What does this skill do? What problem does it solve?
2. What are the exact trigger phrases? (user actions, keywords, file types -- be specific: "when the user says X", "when working on Y files")
3. What should NOT trigger it? (adjacent domains that should be excluded)
4. Which plugin should it live in? (existing or new)
5. Does it need bundled resources? (scripts/, references/, assets/)
6. What's the degree of freedom? (rigid workflow vs flexible guidance)

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
   - Frontmatter: `name` (kebab-case, max 64 chars) and `description` (max 1024 chars)
   - **Description format** -- MUST follow the high-activation template:
     - Directive voice: "ALWAYS invoke this skill when..."
     - Negative constraint: "Do not X directly"
     - Include `TRIGGER WHEN:` and `DO NOT TRIGGER WHEN:` lines
     - Third person, specific trigger phrases
     - See "Description Engineering" section above
   - Optional frontmatter: `context: fork` (isolates in subagent), `allowed-tools` (restricts tool access), `disable-model-invocation: true` (prevents auto-triggering)
   - Body: under 500 lines, imperative tone, concise
   - Only add context Claude doesn't already have -- don't repeat what Claude already knows
   - Progressive disclosure: split into references/ if body exceeds ~300 lines
   - Can use `!command` syntax for dynamic context injection (shell commands that execute before content reaches Claude)
3. Create `references/`, `scripts/`, `assets/` subdirs only if needed
4. Write any bundled resources

### Agent Creation

1. Create file: `plugins/<plugin>/agents/<agent-name>.md`
2. Write with frontmatter and body following these rules:
   - Frontmatter fields: `name`, `description` (use YAML `>` for multiline), `model: inherit`, `color`, optionally `tools`
   - **Description format** -- same directive template as skills:
     - Include `TRIGGER WHEN:` and `DO NOT TRIGGER WHEN:` lines
     - Third person, specific triggers
     - Example: `"Expert X. TRIGGER WHEN: user needs Y. DO NOT TRIGGER WHEN: task is Z."`
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

| Scenario | Wrong | Right |
|----------|-------|-------|
| Writing descriptions | Passive: "Helps with Docker" (50% activation) | Directive: "ALWAYS invoke when user asks about Docker. Do not run Docker commands directly." (97%+ activation) |
| Description tone | "Can be used for...", "Use when..." | "ALWAYS invoke this skill when...", "Do not X directly" |
| Missing exclusions | No DO NOT TRIGGER WHEN clause | Always specify what should NOT trigger the component |
| Writing agent prompts | Verbose prose paragraphs | Terse keyword-list style |
| Skill body length | 800+ lines in SKILL.md | Split into references/ at ~300 lines |
| Skill body content | Repeating what Claude already knows | Only add context Claude lacks; trust built-in knowledge |
| Creating resources | Empty placeholder dirs | Only create dirs that have files |
| Choosing a plugin | Always create a new one | Prefer adding to existing plugin if domain fits |
| Agent description | First/second person | Third person: "Processes X when Y" |
| Token budget | Long verbose descriptions on all components | Keep descriptions under 300 chars when possible; total budget is 15k chars |

## Critical Rules

- All names: kebab-case
- Never use em dash -- use hyphen `-` or double hyphen `--`
- Default model for agents: `inherit` (agents follow the session model)
- Agent filename must match frontmatter `name` field
- Skill directory name must match frontmatter `name` field
- Always bump both plugin version AND metadata.version
- Stage marketplace.json with component files in same commit
- Write real content, never placeholder text
