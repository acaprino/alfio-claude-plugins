# anvil-toolset

Custom Claude Code plugin marketplace. Contains agents, skills, and commands for development workflows, code quality, AI tooling, and more. Remote: `acaprino/anvil-toolset` on GitHub.

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

23 plugins: humanize, deep-dive-analysis, tauri-development, frontend, ai-tooling, python-development, stripe, utilities, messaging, research, business, code-documentation, project-setup, mobile-development, typescript-development, csp, digital-marketing, senior-review, app-explorer, workflows, obsidian-development, browser-extensions, learning.

## Plugin anatomy

**Agents** - Markdown files with YAML frontmatter:
- `name`: agent identifier (kebab-case)
- `description`: when/how to use the agent
- `model`: LLM model (default: `opus`)
- `tools` (optional): comma-separated tool list (e.g. `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task`); omit to allow all tools
- `color`: UI accent color (e.g. `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `cyan`, `magenta`, `violet`, `teal`, `indigo`, `gold`, `rust`, `pink`)
- Body: terse keyword-list style system prompt; simple agents ~60-200 lines, complex agents up to ~800 lines

**Skills** - Directory with `SKILL.md` (frontmatter: `name`, `description`) and optional supplementary subdirs: `references/` (docs), `scripts/`, `templates/`, `assets/`.

**Commands** - Slash-command `.md` files with usage instructions and examples. No frontmatter required.

## Conventions

- Agent names: kebab-case matching the filename (e.g. `senior-code-reviewer.md`)
- Plugin names: kebab-case directory names
- Default model: `opus` (Opus 4.6) for all agents
- Agent body style: terse keyword lists, imperative tone, structured with markdown headers
- Skills supplementary subdirs: `references/`, `scripts/`, `templates/`, `assets/` as needed
- No runtime dependencies - all plugins are pure markdown
- Never use the em dash character anywhere - in code, comments, commit messages, or documentation. Use a regular hyphen `-` or double hyphen `--` instead

## Marketplace update workflow

When changes modify plugins (agents, skills, commands), update the marketplace **before committing**:

1. **Bump plugin version** - increment `version` for the changed plugin in `.claude-plugin/marketplace.json`
2. **Bump marketplace version** - increment `metadata.version` in the same file
3. **Commit together** - stage both the plugin files and `marketplace.json` in one commit
4. **Push to remote** - `git push` to `master`

Key fields in `.claude-plugin/marketplace.json`:
- `metadata.version`: overall marketplace version
- `plugins[].version`: per-plugin version
- Install command: `claude plugin marketplace add acaprino/anvil-toolset`

## Adding a new plugin

1. Create `plugins/<name>/` with `agents/`, `skills/`, and/or `commands/` subdirectories as needed
2. Write agent/skill/command markdown files following existing patterns
3. Register the plugin in `.claude-plugin/marketplace.json` - add entry to `plugins[]` with `name`, `source`, `description`, `version` (start at `1.0.0`), `author`, `license`, `keywords`, `category`, `strict`, and paths to agents/skills/commands
4. Bump `metadata.version` and commit everything together

## Git workflow

- Single branch: `master`
- Commit style: imperative, descriptive (e.g. "Add high-value keywords to prompt-engineer agent")
- No PR workflow - direct push to master

## Build / CI

None. No tests, no build step, no CI pipeline. All content is static markdown.

## Upstream-synced plugins

Some plugins are ported from external repositories and should be kept in sync with their upstream source. When asked to update one of these plugins, fetch the latest content from the upstream URL using `gh api` and apply any changes, then follow the standard marketplace update workflow.

| Plugin | Upstream source | Files to sync |
|--------|----------------|---------------|
| `frontend` (frontend-design) | `anthropics/claude-code` - `plugins/frontend-design/skills/frontend-design/SKILL.md` | `plugins/frontend/skills/frontend-design/SKILL.md` |
| `ai-tooling` (brainstorming) | `obra/superpowers` - `skills/brainstorming/SKILL.md` | `plugins/ai-tooling/skills/brainstorming/SKILL.md` |
| `ai-tooling` (writing-plans) | `obra/superpowers` - `skills/writing-plans/SKILL.md` | `plugins/ai-tooling/skills/writing-plans/SKILL.md` |
| `ai-tooling` (executing-plans) | `obra/superpowers` - `skills/executing-plans/SKILL.md` | `plugins/ai-tooling/skills/executing-plans/SKILL.md` |
| `frontend` (css-master) | `paulirish/dotfiles` - `agents/paulirish-skills/skills/modern-css/SKILL.md` | `plugins/frontend/skills/css-master/SKILL.md`, `plugins/frontend/skills/css-master/references/argyle-cacadia-2025-deck.md` |
| `deep-dive-analysis` (inspiration) | `gsd-build/get-shit-done` - `agents/gsd-codebase-mapper.md` | `plugins/deep-dive-analysis/commands/deep-dive-analysis.md` (patterns adopted, not direct copy) |

### How to sync a plugin

```bash
# Fetch latest SKILL.md from upstream (anthropics/claude-code example)
gh api repos/anthropics/claude-code/contents/plugins/frontend-design/skills/frontend-design/SKILL.md \
  --jq '.content' | base64 -d

# Fetch latest SKILL.md from upstream (obra/superpowers example)
gh api repos/obra/superpowers/contents/skills/brainstorming/SKILL.md \
  --jq '.content' | base64 -d

# Fetch latest SKILL.md from upstream (paulirish/dotfiles example)
gh api repos/paulirish/dotfiles/contents/agents/paulirish-skills/skills/modern-css/SKILL.md \
  --jq '.content' | base64 -d

# Fetch latest gsd-codebase-mapper.md from upstream (gsd-build/get-shit-done example)
gh api repos/gsd-build/get-shit-done/contents/agents/gsd-codebase-mapper.md \
  --jq '.content' | base64 -d
```

Then compare with the local file, apply upstream changes while preserving local additions (source attribution line at top of each file, plus any plugin-specific sections like Typography Reference or Isolated Prompting for frontend-design in `plugins/frontend/skills/frontend-design/`), bump the plugin version, bump `metadata.version`, and commit + push.

**Important:** Upstream superpowers skills reference other superpowers skills we don't have (e.g. `superpowers:using-git-worktrees`, `superpowers:finishing-a-development-branch`, `superpowers:subagent-driven-development`). When syncing, replace `superpowers:` skill references with either our local `ai-tooling:` equivalents or generic guidance describing the same action. Keep `docs/plans/` path (not upstream's `docs/superpowers/plans/`).
