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
    hooks/                  # hook handlers (JS/Python) + hooks.json (anvil-hooks, prompt-improver)
```

32 plugins: humanize, deep-dive-analysis, tauri-development, frontend, react-development, xterm, ai-tooling, python-development, stripe, system-utils, messaging, research, business, project-setup, mobile-development, typescript-development, csp, digital-marketing, senior-review, app-explorer, workflows, obsidian-development, browser-extensions, learning, marketplace-ops, playwright-skill, anvil-hooks, prompt-improver, cc-usage, codebase-mapper, git-worktrees, rag-development.

## Plugin anatomy

**Agents** - Markdown files with YAML frontmatter:
- `name`: agent identifier (kebab-case)
- `description`: when/how to use the agent (use YAML multiline `>` for long descriptions)
- `model`: LLM model (default: `opus`)
- `tools` (optional): comma-separated tool list (e.g. `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task`); omit to allow all tools
- `color`: UI accent color (one of: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`)
- Body: terse keyword-list style system prompt; simple agents ~50-200 lines, complex agents up to ~560 lines

**Skills** - Directory with `SKILL.md` (frontmatter: `name`, `description`) and optional supplementary subdirs: `references/` (docs), `scripts/`, `templates/`, `assets/`, `lib/`.

**Commands** - Slash-command `.md` files with YAML frontmatter (`description`, `argument-hint`) and usage instructions/examples.

**Hooks** - Used by `anvil-hooks` plugin. Contains `hooks.json` (hook definitions) and `handlers/` directory with JS handler scripts. Uses `plugins/anvil-hooks/.claude-plugin/plugin.json` instead of marketplace registration for hook configuration.

## Conventions

- Agent names: kebab-case matching the filename (e.g. `quick-searcher.md`)
- Plugin names: kebab-case directory names
- Default model: `opus` (Opus 4.6); exceptions noted per-agent (e.g. `quick-searcher` uses `sonnet`)
- Agent body style: terse keyword lists, imperative tone, structured with markdown headers
- Skills supplementary subdirs: `references/`, `scripts/`, `templates/`, `assets/`, `lib/` as needed
- No build step or runtime framework - plugins are markdown with optional helper scripts (Python, JS) in skills' `scripts/` subdirs
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

1. Create `plugins/<name>/` with `agents/`, `skills/`, `commands/`, and/or `hooks/` subdirectories as needed
2. Write agent/skill/command markdown files following existing patterns
3. Register the plugin in `.claude-plugin/marketplace.json` - add entry to `plugins[]` with `name`, `source`, `description`, `version` (start at `1.0.0`), `author`, `license`, `keywords`, `category`, `strict`, paths to agents/skills/commands, and optionally `dependencies`/`optionalDependencies` (arrays of plugin names)
4. Bump `metadata.version` and commit everything together

## Git workflow

- Single branch: `master`
- Commit style: imperative, descriptive (e.g. "Add high-value keywords to prompt-engineer agent")
- No PR workflow - direct push to master

## Build / CI

None. No tests, no build step, no CI pipeline. All content is static markdown.

## Documentation

`docs/plugins/` contains per-plugin documentation. `docs/plans/` holds implementation plans used by planning skills.

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
| `playwright-skill` | `lackeyjb/playwright-skill` - `skills/playwright-skill/` | `plugins/playwright-skill/skills/playwright-skill/SKILL.md`, `plugins/playwright-skill/skills/playwright-skill/API_REFERENCE.md`, `plugins/playwright-skill/skills/playwright-skill/run.js`, `plugins/playwright-skill/skills/playwright-skill/package.json`, `plugins/playwright-skill/skills/playwright-skill/lib/helpers.js` |
| `react-development` (react-best-practices) | `vercel-labs/agent-skills` - `skills/react-best-practices/` | `plugins/react-development/skills/react-best-practices/SKILL.md`, `plugins/react-development/skills/react-best-practices/references.md`, `plugins/react-development/skills/react-best-practices/rules/*.md` |
| `digital-marketing` (domain-hunter) | `ReScienceLab/opc-skills` - `skills/domain-hunter/` | `plugins/digital-marketing/skills/domain-hunter/SKILL.md`, `plugins/digital-marketing/skills/domain-hunter/references/registrars.md`, `plugins/digital-marketing/skills/domain-hunter/references/spaceship-api.md` |
| `prompt-improver` | `severity1/claude-code-prompt-improver` | `plugins/prompt-improver/skills/prompt-improver/SKILL.md`, `plugins/prompt-improver/skills/prompt-improver/references/*.md`, `plugins/prompt-improver/hooks/handlers/improve-prompt.js` |

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

# Fetch latest playwright-skill files from upstream (lackeyjb/playwright-skill example)
gh api repos/lackeyjb/playwright-skill/contents/skills/playwright-skill/SKILL.md \
  --jq '.content' | base64 -d
gh api repos/lackeyjb/playwright-skill/contents/skills/playwright-skill/run.js \
  --jq '.content' | base64 -d
gh api repos/lackeyjb/playwright-skill/contents/skills/playwright-skill/lib/helpers.js \
  --jq '.content' | base64 -d

# Fetch latest react-best-practices from upstream (vercel-labs/agent-skills example)
# Local target: plugins/react-development/skills/react-best-practices/
gh api repos/vercel-labs/agent-skills/contents/skills/react-best-practices/SKILL.md \
  --jq '.content' | base64 -d
gh api repos/vercel-labs/agent-skills/contents/skills/react-best-practices/AGENTS.md \
  --jq '.content' | base64 -d  # saved locally as references.md
# For rules: iterate all files in skills/react-best-practices/rules/

# Fetch latest domain-hunter files from upstream (ReScienceLab/opc-skills example)
# NOTE: Upstream Step 3 uses dedicated Twitter/Reddit Python scripts - replace with WebSearch
# queries targeting site:x.com and site:reddit.com when syncing
gh api repos/ReScienceLab/opc-skills/contents/skills/domain-hunter/SKILL.md \
  --jq '.content' | base64 -d
gh api repos/ReScienceLab/opc-skills/contents/skills/domain-hunter/references/registrars.md \
  --jq '.content' | base64 -d
gh api repos/ReScienceLab/opc-skills/contents/skills/domain-hunter/references/spaceship-api.md \
  --jq '.content' | base64 -d

# Fetch latest prompt-improver files from upstream (severity1/claude-code-prompt-improver example)
gh api repos/severity1/claude-code-prompt-improver/contents/skills/prompt-improver/SKILL.md \
  --jq '.content' | base64 -d
gh api repos/severity1/claude-code-prompt-improver/contents/skills/prompt-improver/references/question-patterns.md \
  --jq '.content' | base64 -d
gh api repos/severity1/claude-code-prompt-improver/contents/skills/prompt-improver/references/research-strategies.md \
  --jq '.content' | base64 -d
gh api repos/severity1/claude-code-prompt-improver/contents/skills/prompt-improver/references/examples.md \
  --jq '.content' | base64 -d
# NOTE: upstream uses Python (scripts/improve-prompt.py), local version is JS (hooks/handlers/improve-prompt.js)
gh api repos/severity1/claude-code-prompt-improver/contents/scripts/improve-prompt.py \
  --jq '.content' | base64 -d
```

Then compare with the local file, apply upstream changes while preserving local additions (source attribution line at top of each file, plus any plugin-specific sections like Typography Reference or Isolated Prompting for frontend-design in `plugins/frontend/skills/frontend-design/`), bump the plugin version, bump `metadata.version`, and commit + push.

**Important:** Upstream superpowers skills reference other superpowers skills we don't have (e.g. `superpowers:using-git-worktrees`, `superpowers:finishing-a-development-branch`, `superpowers:subagent-driven-development`). When syncing, replace `superpowers:` skill references with either our local `ai-tooling:` equivalents or generic guidance describing the same action. Keep `docs/plans/` path (not upstream's `docs/superpowers/plans/`).
