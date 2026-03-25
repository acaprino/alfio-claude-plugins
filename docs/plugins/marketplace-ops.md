# Marketplace Ops Plugin

> Manage and maintain the figs plugin ecosystem -- audit marketplace integrity, scaffold new plugins, create skills and agents, and review content quality.

## Agents

### `marketplace-manager`

Expert marketplace operations manager for figs.

| | |
|---|---|
| **Model** | opus |
| **Color** | yellow |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch |
| **Use for** | Adding, auditing, reorganizing, versioning, or syncing plugins |

**Capabilities:**
- **Audit & Validation** - Cross-reference marketplace.json vs filesystem, validate frontmatter
- **Plugin Scaffolding** - Create new plugins with proper directory structure and registration
- **Version Management** - Semantic versioning for plugins and marketplace
- **Upstream Sync** - Fetch and merge upstream changes while preserving local additions
- **AI Quality Review** - Score descriptions, prompts, and trigger accuracy (1-5 scale)
- **Consolidation Analysis** - Identify overlapping plugins and suggest reorganization

---

## Skills

### `marketplace-audit`

Structural validation of the marketplace ecosystem.

| | |
|---|---|
| **Invoke** | Skill reference or `/marketplace-audit` |
| **Use for** | Pre-commit validation, detecting orphaned files, frontmatter checks, color harmony |

**Checks:**
- File existence vs marketplace.json references
- Orphaned files not registered in any plugin
- Frontmatter field validation (agents, skills, commands)
- Color consistency and harmony across plugins
- Naming conventions (kebab-case, filename/name match)
- Version sanity (valid semver)

### `skills-hammer`

Guided creation of new figs components.

| | |
|---|---|
| **Invoke** | Skill reference or "create a new skill/agent/plugin" |
| **Use for** | Creating skills, agents, commands, or full plugins with real content |

**Workflow:**
1. **Requirements Gathering** - Ask targeted questions about purpose, triggers, plugin placement
2. **Content Generation** - Write production-ready files (not placeholders)
3. **Marketplace Registration** - Update marketplace.json, bump versions
4. **Validation** - Verify paths, frontmatter, naming conventions

Includes a conventions reference with color palette, categories, agent structure patterns, and naming rules.

---

## Commands

### `/marketplace-health`

Quick marketplace health check -- validates marketplace.json, checks file references, and reports plugin counts and version status.

### `/marketplace-scaffold-plugin`

Scaffold a new plugin with proper directory structure, starter files, and marketplace.json registration.

```
/marketplace-scaffold-plugin my-plugin --with-agent --with-skill --category development
```

### `/marketplace-review`

AI-powered quality review of plugin descriptions, trigger keywords, agent prompts, skill instructions, and command definitions.

---

**Related:** [figs-hooks](figs-hooks.md) (session lifecycle hooks) | [project-setup](project-setup.md) (CLAUDE.md management)
