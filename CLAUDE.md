# alfio-claude-plugins

Custom Claude Code plugin marketplace. Contains agents, skills, and commands for development workflows, code quality, AI tooling, and more. Remote: `acaprino/alfio-claude-plugins` on GitHub.

## Project structure

```
.claude-plugin/
  marketplace.json          # plugin registry (versions, metadata)
plugins/
  <plugin-name>/
    agents/                 # agent .md files (frontmatter + system prompt)
    skills/                 # skill directories (SKILL.md + optional references/)
    commands/               # slash-command .md files
```

18 plugins: code-review, tauri-development, frontend-optimization, ai-tooling, python-development, stripe, utilities, messaging, research, business, code-documentation, project-setup, mobile-development, typescript-development, csp, digital-marketing, frontend-design, comprehensive-review.

## Plugin anatomy

**Agents** — Markdown files with YAML frontmatter:
- `name`: agent identifier (kebab-case)
- `description`: when/how to use the agent
- `model`: LLM model (default: `opus`)
- `tools`: comma-separated tool list (e.g. `Read, Write, Edit, Bash, Glob, Grep`)
- `color`: UI accent color
- Body: terse keyword-list style system prompt, typically 70-200 lines

**Skills** — Directory with `SKILL.md` (frontmatter: `name`, `description`) and optional `references/` subdirectory for supporting docs.

**Commands** — Slash-command `.md` files with usage instructions and examples. No frontmatter required.

## Conventions

- Agent names: kebab-case matching the filename (e.g. `senior-code-reviewer.md`)
- Plugin names: kebab-case directory names
- Default model: `opus` (Opus 4.6) for all agents
- Agent body style: terse keyword lists, imperative tone, structured with markdown headers
- Skills reference dir: `references/` for supplementary material
- No runtime dependencies — all plugins are pure markdown

## Marketplace update workflow

When changes modify plugins (agents, skills, commands), update the marketplace **before committing**:

1. **Bump plugin version** — increment `version` for the changed plugin in `.claude-plugin/marketplace.json`
2. **Bump marketplace version** — increment `metadata.version` in the same file
3. **Commit together** — stage both the plugin files and `marketplace.json` in one commit
4. **Push to remote** — `git push` to `master`

Key fields in `.claude-plugin/marketplace.json`:
- `metadata.version`: overall marketplace version (currently `1.12.0`)
- `plugins[].version`: per-plugin version
- Install command: `claude plugin marketplace add acaprino/alfio-claude-plugins`

## Adding a new plugin

1. Create `plugins/<name>/` with `agents/`, `skills/`, and/or `commands/` subdirectories as needed
2. Write agent/skill/command markdown files following existing patterns
3. Register the plugin in `.claude-plugin/marketplace.json` — add entry to `plugins[]` with `name`, `source`, `description`, `version` (start at `1.0.0`), `author`, `license`, `keywords`, `category`, `strict`, and paths to agents/skills/commands
4. Bump `metadata.version` and commit everything together

## Git workflow

- Single branch: `master`
- Commit style: imperative, descriptive (e.g. "Add high-value keywords to prompt-engineer agent")
- No PR workflow — direct push to master

## Build / CI

None. No tests, no build step, no CI pipeline. All content is static markdown.

## Upstream-synced plugins

Some plugins are ported from external repositories and should be kept in sync with their upstream source. When asked to update one of these plugins, fetch the latest content from the upstream URL using `gh api` and apply any changes, then follow the standard marketplace update workflow.

| Plugin | Upstream source | Files to sync |
|--------|----------------|---------------|
| `frontend-design` | `anthropics/claude-code` — `plugins/frontend-design/skills/frontend-design/SKILL.md` | `plugins/frontend-design/skills/frontend-design/SKILL.md` |
| `ai-tooling` (brainstorming) | `obra/superpowers` — `skills/brainstorming/SKILL.md` | `plugins/ai-tooling/skills/brainstorming/SKILL.md` |
| `ai-tooling` (writing-plans) | `obra/superpowers` — `skills/writing-plans/SKILL.md` | `plugins/ai-tooling/skills/writing-plans/SKILL.md` |
| `ai-tooling` (executing-plans) | `obra/superpowers` — `skills/executing-plans/SKILL.md` | `plugins/ai-tooling/skills/executing-plans/SKILL.md` |

### How to sync a plugin

```bash
# Fetch latest SKILL.md from upstream (anthropics/claude-code example)
gh api repos/anthropics/claude-code/contents/plugins/frontend-design/skills/frontend-design/SKILL.md \
  --jq '.content' | base64 -d

# Fetch latest SKILL.md from upstream (obra/superpowers example)
gh api repos/obra/superpowers/contents/skills/brainstorming/SKILL.md \
  --jq '.content' | base64 -d
```

Then compare with the local file, apply upstream changes while preserving local additions (source attribution line at top of each file, plus any plugin-specific sections like Typography Reference or Isolated Prompting for frontend-design), bump the plugin version, bump `metadata.version`, and commit + push.
