# Claude Code Daodan

The Daodan is the symbiote that augments its host. This repository is the Daodan of Claude Code: a marketplace of agents, skills, and commands that augment the base model into a specialized toolkit covering development workflows, code quality, AI tooling, scraping, trading, observability, and more. Remote: `acaprino/claude-code-daodan` on GitHub.

## Project structure

```
.claude-plugin/
  marketplace.json          # plugin registry (versions, metadata)
plugins/
  <plugin-name>/
    agents/                 # agent .md files (frontmatter + system prompt)
    skills/                 # skill directories (SKILL.md + optional references/)
    commands/               # slash-command .md files
    hooks/                  # hook handlers (JS/Python) + hooks.json (acp-hooks, prompt-improver)
```

40 plugins: clean-code, deep-dive-analysis, tauri-development, react-development, xterm, ai-tooling, python-development, stripe, system-utils, messaging, research, business, project-setup, app-analyzer, typescript-development, csp, digital-marketing, senior-review, obsidian-development, browser-extensions, learning, marketplace-ops, acp-hooks, prompt-improver, codebase-mapper, git-worktrees, rag-development, docs, testing, platform-engineering, ibkr-trading, mt5-trading, opentelemetry, docker, grabber-development, codebase-cleanup, libgdx-development, kotlin-development, pwa-expert, abstraction-architect.

## Plugin anatomy

**Agents** - Markdown files with YAML frontmatter:
- `name`: agent identifier (kebab-case)
- `description`: when/how to use the agent (use YAML multiline `>` for long descriptions)
- `model`: LLM model (default: `inherit`, the agent follows the session model)
- `tools` (optional): comma-separated tool list (e.g. `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task`); omit to allow all tools
- `color`: UI accent color (one of: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`)
- Body: terse keyword-list style system prompt; simple agents ~50-200 lines, complex agents up to ~700 lines

**Skills** - Directory with `SKILL.md` (frontmatter: `name`, `description`) and optional supplementary subdirs: `references/` (docs), `scripts/`, `templates/`, `assets/`, `lib/`.

**Commands** - Slash-command `.md` files with YAML frontmatter (`description`, `argument-hint`) and usage instructions/examples.

**Hooks** - Used by `acp-hooks` and `prompt-improver` plugins. Contains `hooks.json` (hook definitions) and `handlers/` directory with JS handler scripts. `acp-hooks` also uses `plugins/acp-hooks/.claude-plugin/plugin.json` for supplementary hook configuration alongside marketplace registration.

## Conventions

- Agent names: kebab-case matching the filename (e.g. `quick-searcher.md`)
- Plugin names: kebab-case directory names
- Default model: `inherit` (agents follow the session model instead of pinning one); exceptions noted per-agent (e.g. `quick-searcher` uses `sonnet`)
- Agent body style: terse keyword lists, imperative tone, structured with markdown headers
- Skills supplementary subdirs: `references/`, `scripts/`, `templates/`, `assets/`, `lib/` as needed
- No build step or runtime framework - plugins are markdown with optional helper scripts (Python, JS) in skills' `scripts/` subdirs
- Avoid the dash-aside construct anywhere (code, comments, commit messages, documentation). The rule targets the *rhetorical pattern* of bracketing a clause between dashes, in any form: `—` (em dash), `--` (double hyphen), or ` - ` (spaced hyphen). All three are banned when used to wrap a parenthetical aside (e.g., "lorem ipsum -- lorem ipsum -- lorem ipsum"). Substituting `--` for `—` is **not** the fix. Rewrite into separate sentences, parentheses, colons, or just delete the aside. Hyphenated compounds (`file-ownership`, `multi-agent`) are unrelated and fine.

## Marketplace update workflow

When changes modify plugins (agents, skills, commands), update the marketplace **before committing**:

1. **Bump plugin version** - increment `version` for the changed plugin in `.claude-plugin/marketplace.json`
2. **Bump marketplace version** - increment `metadata.version` in the same file
3. **Commit together** - stage both the plugin files and `marketplace.json` in one commit
4. **Push to remote** - `git push` to `master`

Key fields in `.claude-plugin/marketplace.json`:
- `metadata.version`: overall marketplace version
- `plugins[].version`: per-plugin version
- Install command: `claude plugin marketplace add acaprino/claude-code-daodan`

## Adding a new plugin

1. Create `plugins/<name>/` with `agents/`, `skills/`, `commands/`, and/or `hooks/` subdirectories as needed
2. Write agent/skill/command markdown files following existing patterns
3. Register the plugin in `.claude-plugin/marketplace.json` - add entry to `plugins[]` with `name`, `source`, `description`, `version` (start at `1.0.0`), `author`, `license`, `keywords`, `category`, `strict`, paths to agents/skills/commands, and optionally `dependencies`/`optionalDependencies` (arrays of plugin names)
4. Bump `metadata.version` and commit everything together

## Git workflow

- Single branch: `master`
- Commit style: imperative, descriptive (e.g. "Add high-value keywords to prompt-engineer agent")
- Primary workflow: direct push to master (PRs used occasionally)

## Build / CI

None. No tests, no build step, no CI pipeline. All content is static markdown.

## Documentation

`docs/plugins/` contains per-plugin documentation. `docs/references/` holds cross-cutting knowledge bases that inform changes across multiple plugins — notably [`agent-teams-best-practices.md`](docs/references/agent-teams-best-practices.md), the source of truth when restructuring any plugin that spawns multi-agent teams or pipeline reviewers (`senior-review`, `codebase-mapper`, `research`, `deep-dive-analysis`).

## External-repository intake

When the user asks to "import", "pull", "vendor", "cherry-pick", or "borrow from" an external GitHub repository (anything not already in the sync table below), follow this workflow before touching any local file. This section covers the *first* intake. Re-syncing repositories already registered uses the separate workflow under "Upstream-synced plugins" below.

### 1. Classify the operation

We do not fork, submodule, or add runtime dependencies. The only intake mode for this marketplace is **vendoring**: a one-shot or tracked copy of upstream content into our tree, with attribution preserved and the content adapted to our conventions.

| Sub-mode | When to pick | Example |
|---|---|---|
| **Full vendoring** | Upstream is a complete drop-in (a single SKILL.md, a small set of references) and there is no local equivalent | `kotlin-development` |
| **Cherry-pick vendoring** | Upstream has many files but only a subset adds value, or the upstream commands collide with our existing namespace | `wshobson/agents` (3 codebase-cleanup commands imported, 2 agents skipped for overlap) |
| **Hybrid merge** | Upstream covers ground that overlaps with a local file; append upstream content as a delimited section instead of creating a duplicate | `wshobson/agents` e2e-testing-patterns `references/details.md` kept inline in the local SKILL.md sections |
| **Inspiration only** | We adopt patterns or workflow ideas but write our own content from scratch; no upstream text copied | `deep-dive-analysis` from `gsd-build/get-shit-done` |

Combinations are normal (the `wshobson/agents` intake used cherry-pick plus hybrid merge plus new files across codebase-cleanup and e2e-testing-patterns; its multi-agent generic core and the reverse-engineering vendor were later delegated back upstream).

### 2. Decide the four dimensions

Before writing any file, lock down each dimension. State them back to the user via `AskUserQuestion` whenever a meaningful choice exists.

| Dimension | Question | Common answers |
|---|---|---|
| **Selection** | Full repo or cherry-pick? | Cherry-pick if upstream is large, has collisions, or carries unused infrastructure |
| **Merge** | Standalone new files or merged into existing local files? | Merge when overlap exists; standalone for orphan topics |
| **Sync strategy** | One-shot snapshot or ongoing sync? | Snapshot when upstream changes slowly or churn is unwanted; ongoing sync when upstream is actively maintained and aligned with our direction |
| **Tracking** | Register in the upstream-synced table or leave untracked? | Register only if "ongoing sync" was chosen; snapshots can still be registered for re-import convenience |

### 3. License compliance gate

Block before fetching:

1. Read the upstream `LICENSE` file. The four expected outcomes:
   - **MIT / BSD / ISC / Apache-2.0**: proceed; preserve attribution header in every derived file.
   - **MPL-2.0**: proceed for documentation-only content; flag to the user before importing source code.
   - **GPL-2.0 / GPL-3.0 / AGPL**: STOP. Ask the user explicitly; the marketplace is MIT and incompatible licensing must be a conscious decision.
   - **No license / proprietary**: STOP. Do not import.
2. For Apache-2.0 specifically, check whether upstream has a `NOTICE` file. If it does, preserve its contents alongside the derived files.
3. Attribution header on every derived file (new or merged section):
   ```
   <!--
   Portions of this file are derived from <owner>/<repo>
   (https://github.com/<owner>/<repo>), <SPDX-license> License.
   Snapshot YYYY-MM-DD.
   -->
   ```

### 4. Fetch and inspect (read-only)

Use `gh api repos/<owner>/<repo>/contents/<path>` with `--jq '.content' | base64 -d`. Save everything to `.upstream-scratch/<repo>/` (excluded from commits). Read every fetched file before writing local files. Count and assess size before proposing the merge plan.

### 5. Adapt to local conventions

Before saving any derived file, scan for and rewrite:

- **Dash-aside construct** ("X — Y — Z" / "X -- Y -- Z" / "X - Y - Z" bracketing a clause): replace with sentences, parentheses, or colons. Never substitute one dash form for another.
- **Emoji**: remove if the destination plugin's existing files have none.
- **Upstream-specific cross-references**: rewrite `[reference/foo.md](foo.md)` style links to point at the local destination path (or remove if the target was not imported). Rewrite `{{template_vars}}` and references to upstream-only commands.
- **Namespace prefixes**: rewrite upstream `<their-plugin>:X` skill references to the local `<our-plugin>:X` equivalent, or drop them when we vendor no equivalent.
- **Stale tool names** in team-related imports: `Teammate` -> `TeamCreate`, `Task tool to spawn` -> `Agent tool`.

### 6. Wire the new content into existing agents and commands

Importing content that no agent reads is wasted work. After saving derived files:

1. Add a `## References Library` (or equivalent) entry in the host plugin's `SKILL.md` that indexes every new/extended reference with a one-line topic description.
2. Update any command or agent that should now consult the new references. Add explicit `Read plugins/<plugin>/skills/.../<file>.md` instructions in the relevant prompt sections.
3. Avoid preloading discipline: the consumers must read references on-demand, not all upfront. State this in the wiring text.

### 7. Decide on tracking and re-sync

If the sub-mode is "ongoing sync" (or "snapshot but worth tracking for re-import"), append a row to the upstream-synced table below, with:
- Plugin (and sub-skill, if applicable) plus license tag for non-MIT sources
- Upstream repo plus the specific subpath
- Full list of derived local files and any merged sections

Then append the matching `gh api` fetch loop to the "How to sync a plugin" code block below. Do this even for snapshots; it makes a future re-import a one-command operation rather than archaeology.

If the sub-mode is "inspiration only", do NOT add a sync-table row. Add an inline note in the affected file describing what was adopted from where, but no sync entry.

### 8. Version bump and commit

- Bump every plugin whose `version` in `marketplace.json` had content added.
- Bump `metadata.version` (minor bump for first-time intake of a new upstream; patch bump for follow-up reworks of an existing intake).
- Single commit with the imported files, the local edits, the SKILL.md wiring, the CLAUDE.md sync-table update, and the version bumps together.
- Commit message: `Cherry-pick / Vendor / Import <subject> from <owner>/<repo> (v<new>)` with a short description block listing new files, merged sections, license, and attribution date.

### 9. Verification before push

- `grep` derived files for any leftover upstream-only references, stale tool names, or dash-aside constructs.
- Validate `marketplace.json` JSON syntax.
- `git status` shows nothing in `.upstream-scratch/` staged.
- `git diff --stat` to sanity-check scope.

---

## Upstream-synced plugins

Some plugins are ported from external repositories and should be kept in sync with their upstream source. When asked to update one of these plugins, fetch the latest content from the upstream URL using `gh api` and apply any changes, then follow the standard marketplace update workflow.

### Default upstream-update strategy

When the user asks for "upstream updates" (or similar), this is the default workflow. Do not blindly overwrite local files - most syncs need targeted merging because local has legitimate customizations.

1. **Check all synced plugins in parallel**. For each file in the sync table below, diff the upstream against the local version. Spawn Explore agents when there are many files to parallelize the diffing. Focus the reports on: which files differ, what changed, and whether the drift is intentional or worth pulling.

2. **Classify each file** before touching it:
   - **Clear win** - new upstream file missing locally, or a bug/fact fix with no local conflict. Pull directly.
   - **Minor refinement** - small wording/metadata changes. Pull if no local frontmatter or content conflicts.
   - **Hard merge** - upstream rewrote a section we also evolved locally. Layer upstream changes onto local; do not overwrite.
   - **Intentional drift** (do not touch) - local namespace rewrites (upstream `<their-plugin>:` -> local `<our-plugin>:`), local polish (typo fixes, expanded triggers), style conventions (no dash-aside construct per CLAUDE.md; no emojis in some plugins), local-only additions (custom presets, Ecosystem Integration sections), upstream dash-asides rewritten to sentences/parens/colons.

3. **Preserve these local customizations** on every merge:
   - Source attribution lines at the top of files
   - Frontmatter: localized `description` (often multiline with `>`), `tools`, `color`, `version`, `model`
   - Plugin-specific style: no dash-aside construct (rewrite "X — Y — Z" / "X -- Y -- Z" / "X - Y - Z" asides into sentences, parens, or colons), no emojis in some plugins
   - Namespace replacements (upstream `<their-plugin>:X` -> local `<our-plugin>:X`)
   - Local-only sections (e.g., `## Ecosystem Integration` blocks added during earlier syncs)

4. **For judgment calls**, ask the user via `AskUserQuestion`:
   - When upstream rewrote a section we also evolved (merge vs keep vs overwrite)
   - When upstream adds a feature that conflicts with local direction
   - When a file is flagged as "major drift"

5. **Apply targeted Edits, not Writes** - prefer surgical edits that fix specific bugs (stale tool names, added items in a list) over replacing whole files. Only use Write for new files or when the entire file is being replaced.

6. **Watch for stale tool names** (common drift source): `` `Teammate` tool `` / `` `Task` tool to spawn `` / `` Call `Teammate` cleanup `` / `` operation: "spawnTeam" `` -> fix to `` `TeamCreate` tool `` / `` `Agent` tool `` / `` `TeamDelete` ``. Grep team-related imports after any sync to catch these.

7. **Version bump and commit** - bump each touched plugin's `version` in `.claude-plugin/marketplace.json`, bump `metadata.version`, and commit everything together with a descriptive message like "Sync upstream updates for X and Y (vN.N.N)". Push to master.

8. **Verify** - run `Grep` for any remaining stale tool names, confirm marketplace.json is consistent, then `git status` / `git diff --stat` before committing.


| Plugin | Upstream source | Files to sync |
|--------|----------------|---------------|
| `deep-dive-analysis` (inspiration) | `gsd-build/get-shit-done` - `agents/gsd-codebase-mapper.md` | `plugins/deep-dive-analysis/commands/deep-dive-analysis.md` (patterns adopted, not direct copy) |
| `react-development` (react-best-practices) | `vercel-labs/agent-skills` - `skills/react-best-practices/` | `plugins/react-development/skills/react-best-practices/SKILL.md`, `plugins/react-development/skills/react-best-practices/references.md`, `plugins/react-development/skills/react-best-practices/rules/*.md` |
| `digital-marketing` (domain-hunter) | `ReScienceLab/opc-skills` - `skills/domain-hunter/` | `plugins/digital-marketing/skills/domain-hunter/SKILL.md`, `plugins/digital-marketing/skills/domain-hunter/references/registrars.md`, `plugins/digital-marketing/skills/domain-hunter/references/spaceship-api.md`, `plugins/digital-marketing/skills/domain-hunter/examples/auto-video-editing-domain.md` |
| `prompt-improver` | `severity1/claude-code-prompt-improver` (v0.6+: upstream replaced `scripts/improve-prompt.py` with a declarative nudge engine: `scripts/engine.py`, `scripts/rules.py`, `scripts/nudge_builtins.py`, `nudges/<Event>/*.json`) | `plugins/prompt-improver/skills/prompt-improver/SKILL.md`, `plugins/prompt-improver/skills/prompt-improver/references/*.md`, `plugins/prompt-improver/hooks/handlers/improve-prompt.js`, `plugins/prompt-improver/hooks/handlers/plan-guidance.js`, `plugins/prompt-improver/hooks/handlers/background-exec.js`, `plugins/prompt-improver/hooks/handlers/subagent-routing.js`. Local stays a flat-JS-handler port (cherry-pick adoption, 2026-06-10): improve + plan-guidance + background-exec + subagent-routing nudges are ported; the approach-assessment, output-readability, ask-user-question, plan-mode, and workflow nudges are intentionally NOT vendored (overlap with native Claude Code behavior; would inject context on nearly every prompt). |
| `testing` (tdd) | `mattpocock/skills` - `skills/engineering/tdd/` | `plugins/testing/skills/tdd/SKILL.md`, `plugins/testing/skills/tdd/references/tests.md`, `plugins/testing/skills/tdd/references/deep-modules.md`, `plugins/testing/skills/tdd/references/mocking.md`, `plugins/testing/skills/tdd/references/interface-design.md`, `plugins/testing/skills/tdd/references/refactoring.md`. Intentional drift (decided 2026-07-12): upstream 2026-06-30 reshaped the skill to a red->green reference-only framing with "pre-agreed seams", moved refactoring out to its code-review skill, DELETED deep-modules/interface-design/refactoring, and flattened tests.md/mocking.md to the tdd/ top level. Local keeps the red-green-refactor loop, the references/ subdir, and all three deleted files; do NOT re-propose the reshape on future syncs. Content-level additions to the surviving files (tests.md, mocking.md, e.g. the tautological-tests anti-pattern pulled 2026-07-12) ARE still synced. |
| `docker` (multi-stage-dockerfile) | `github/awesome-copilot` - `skills/multi-stage-dockerfile/SKILL.md` | `plugins/docker/skills/multi-stage-dockerfile/SKILL.md` |
| `testing` (e2e-testing-patterns) | `wshobson/agents` - `plugins/developer-essentials/skills/e2e-testing-patterns/` (upstream split SKILL.md into a slim tier + `references/details.md` in 2026 for Codex's 8 KB body cap) | `plugins/testing/skills/e2e-testing-patterns/SKILL.md`. Local intentionally keeps the detailed content INLINE in SKILL.md (well under the 5k-word ceiling); on future syncs diff upstream `references/details.md` against the local inline sections, not as a local-only gap. |
| `senior-review` (semantic-interconnect-mapper) | `wshobson/agents` - `plugins/agent-orchestration/agents/context-manager.md` (pattern cherry-picked, not a direct copy) | `plugins/senior-review/agents/semantic-interconnect-mapper.md` |
| `typescript-development` (mastering-typescript) | `SpillwaveSolutions/mastering-typescript-skill` - `mastering-typescript/` | `plugins/typescript-development/skills/mastering-typescript/SKILL.md`, `plugins/typescript-development/skills/mastering-typescript/references/*.md`, `plugins/typescript-development/skills/mastering-typescript/scripts/validate-setup.sh`, `plugins/typescript-development/skills/mastering-typescript/assets/tsconfig-template.json`, `plugins/typescript-development/skills/mastering-typescript/assets/eslint-template.js`. Adaptation on sync: SKILL.md frontmatter is rewritten to local convention (keep only `name` and `description`; strip upstream `version`, `category`, `triggers`, `author`, `license`, `tags`). Description uses `description: >` multiline form with explicit TRIGGER WHEN / DO NOT TRIGGER WHEN routing, scoping this skill to enterprise/advanced TS work (advanced type system, JS-to-TS migration, toolchain bootstrap, Zod, deep React + TS, NestJS, LangChain.js) and routing routine TS/JS writes to `typescript-development:typescript-write`, React perf to `react-development:review-react`, and dead-code to `typescript-development:knip`. Without this rewrite the skill failed to auto-activate on its core scenarios because upstream's single-paragraph "Use when..." description loses the router race against `typescript-write` (added in v2.1.0). The local `Source: ...` attribution line at the top of SKILL.md and the body content are NOT subject to upstream-driven frontmatter changes on future syncs. |
| `codebase-cleanup` (cherry-pick, MIT) | `wshobson/agents` - `plugins/codebase-cleanup/commands/` | `plugins/codebase-cleanup/commands/deps-audit.md`, `plugins/codebase-cleanup/commands/refactor-clean.md`, `plugins/codebase-cleanup/commands/tech-debt.md`. Upstream `agents/code-reviewer.md` and `agents/test-automator.md` intentionally NOT vendored (heavy overlap with local `senior-review/*` and `testing/*` coverage). Frontmatters rewritten to local style with TRIGGER WHEN / DO NOT TRIGGER WHEN routing notes, emojis stripped from `deps-audit.md`, license-description strings normalized to colon-separated form. |
| `kotlin-development` (full vendor, MIT) | `Jeffallan/claude-skills` - `skills/kotlin-specialist/` | `plugins/kotlin-development/skills/kotlin-specialist/SKILL.md`, `plugins/kotlin-development/skills/kotlin-specialist/references/{coroutines-flow,multiplatform-kmp,android-compose,ktor-server,dsl-idioms}.md`. Adaptation on sync: strip upstream extra frontmatter fields (`license`, `metadata.author`, `version`, `domain`, `triggers`, `role`, `scope`, `output-format`, `related-skills`); keep only `name` and `description` in local frontmatter; rewrite upstream single-paragraph `description` into local `description: >` multiline form with TRIGGER WHEN / DO NOT TRIGGER WHEN. Add MIT attribution header comment immediately after the frontmatter on SKILL.md and at the top of every reference file. Drop the upstream `[Documentation](https://jeffallan.github.io/...)` link at the bottom of SKILL.md. Single-connector em-dashes ("X — Y") in code comments are preserved as-is (they are NOT bracketed asides). |
| `project-setup` (Karpathy Working Principles distillation, MIT) | `multica-ai/andrej-karpathy-skills` - `skills/karpathy-guidelines/SKILL.md` | Canonical `## Working Principles` block embedded in `plugins/project-setup/agents/claude-md-auditor.md` (REQUIRED SECTION) and in `plugins/project-setup/examples/good-claude-md-example.md`. The plugin's `create-claude-md` always inserts the block into generated CLAUDE.md files inline; `maintain-claude-md` flags absence, missing principles, or missing sub-bullets as High findings and offers surgical Edits. Adaptation: principles 1-4 are a tighter distillation of upstream's 4 principles (title + 2 lead sentences + 3 locally authored sub-bullets per principle covering the deeper meta-rules: root-cause analysis, evergreen tests, surgical diffs); principle #5 (Centralize Shared Logic) is locally authored. The block is always delivered inline and is never linked out to an external file or `docs/` pointer - this replaces the older optional deep-dive reference pattern (removed in plugin v1.14.0). Attribution comment preserved at the REQUIRED SECTION header in the auditor agent. Upstream is the source of truth for the lead sentences of principles 1-4; if upstream evolves the principle set or wording, update the auditor's canonical block and re-bump `project-setup`. The locally authored sub-bullets and principle #5 are NOT subject to upstream sync. |

### Deliberately not vendored

Five areas were vendored, then handed back to their upstreams because maintaining the copy cost more than it returned. Do NOT re-import them, and do not add sync-table rows for them on a future "upstream updates" pass. The README documents all five for users.

| Area | Upstream | Removed in |
|---|---|---|
| Frontend and design (`frontend` plugin: 3 agents, 5 skills, 1 command) | `pbakaus/impeccable`, `nextlevelbuilder/ui-ux-pro-max-skill`, `paulirish/dotfiles` | marketplace 7.0.0 |
| Brainstorming, planning, execution (`ai-tooling` skills `brainstorming`, `writing-plans`, `executing-plans`) | `obra/superpowers` | marketplace 8.0.0, ai-tooling 3.0.0 |
| Multi-agent generic core (`agent-teams` plugin: 6 commands, 4 agents, 6 skills) | `wshobson/agents` | marketplace 9.0.0 |
| Browser automation (`playwright-skill` plugin: 1 skill) | `lackeyjb/playwright-skill` | marketplace 11.0.0 |
| Binary reverse engineering (`reverse-engineering` plugin: 3 agents, 4 skills) | `wshobson/agents` | marketplace 12.0.0 |

Places that used to invoke the removed planning skills now load the superpowers skills directly: `acp-loader` (Skill Priority). As of marketplace 8.2.0, superpowers is a declared hard dependency (`dependencies: ["superpowers"]` in `marketplace.json`) of `ai-tooling`, and the phrasing in that place is unconditional: load the skills, and if they are unavailable stop and tell the user to install superpowers (`claude plugin install superpowers@claude-plugins-official`). This supersedes the earlier rule that kept superpowers references conditional; do not reintroduce conditional phrasing.

The same policy applies to the team pipelines: `/senior-review:team-review`, `/deep-dive-analysis:team-deep-dive`, `/codebase-mapper:team-codebase-map`, and `/research:team-research` declare the upstream `agent-teams` plugin (wshobson/agents) as a hard prerequisite in their Prerequisites blocks. The upstream plugin keeps the same `agent-teams:*` namespace, so those references resolve as written once it is installed (`/plugin marketplace add wshobson/agents`, then `/plugin install agent-teams@claude-code-workflows`). The four pipelines and the `senior-review:review-quality-gates` skill are local content with no upstream sync.

Browser automation follows the same pattern as of marketplace 11.0.0: the vendored `playwright-skill` plugin was a byte-level copy of its upstream (only convention adaptations: TRIGGER WHEN frontmatter, temp-dir portability, emoji stripping), so it was removed and delegated. `app-analyzer`, `pwa-expert`, `digital-marketing`, and `grabber-development` declare `playwright-skill` as a hard dependency (`dependencies: ["playwright-skill"]` in `marketplace.json`). The upstream plugin keeps the same `playwright-skill:playwright-skill` namespace, so existing references resolve as written once it is installed (`claude plugin marketplace add lackeyjb/playwright-skill`, then `claude plugin install playwright-skill@playwright-skill`). Their commands and agents state this install path in their dependency-check blocks; do not point those blocks back at this marketplace.

Binary reverse engineering follows the same pattern as of marketplace 12.0.0: the vendored `reverse-engineering` plugin was a byte-level copy of `wshobson/agents` `plugins/reverse-engineering/` (only convention adaptations: MIT attribution comments, agent `model: inherit` and `color: purple`, three upstream `references/details.md` files kept inline in the local SKILL.md bodies), so it was removed and delegated. Upstream publishes it under the same `reverse-engineering` plugin name with identical agent and skill names in the `claude-code-workflows` marketplace (`claude plugin marketplace add wshobson/agents`, then `claude plugin install reverse-engineering@claude-code-workflows`). No local plugin references or depends on it, so no dependency declarations or reference rewrites were needed.

### How to sync a plugin

The sync table above gives the upstream repo and the local target files. Single-file pattern:

```bash
gh api "repos/<owner>/<repo>/contents/<upstream-path>" --jq '.content' | base64 -d
```

For directories, list children first then iterate:

```bash
gh api "repos/<owner>/<repo>/contents/<dir>" --jq '.[].name' | while read f; do
  gh api "repos/<owner>/<repo>/contents/<dir>/$f" --jq '.content' | base64 -d
done
```

After fetching, compare with the local file, apply changes while preserving local additions (attribution headers, frontmatter conventions, namespace replacements, no-dash-aside style), bump the plugin and `metadata.version`, commit + push.

**Non-obvious per-plugin sync notes** (read alongside the sync table):

- **`prompt-improver`**: upstream (v0.6+) ships a Python nudge engine (`scripts/engine.py` + `nudges/*.json`); the local handlers are flat JS files under `plugins/prompt-improver/hooks/handlers/`. Re-port logic per handler, never copy Python files as-is, and keep the not-vendored nudge list in the sync table row in mind.
- **`domain-hunter`**: upstream Step 3 uses dedicated Twitter/Reddit Python scripts. Replace with `WebSearch` queries targeting `site:x.com` / `site:reddit.com`.
- **`mattpocock/skills` (tdd)**: upstream restructured `tdd/` under `skills/engineering/tdd/` in 2026. Old top-level paths return 404.
- **`wshobson/agents` (codebase-cleanup)**: commands only. `agents/code-reviewer.md` and `agents/test-automator.md` are intentionally NOT vendored (overlap with `senior-review/*` and `testing/*`).
- **`wshobson/agents` (codebase-cleanup)**: upstream `description:` is a single line. Rewrite into local `description: >` multiline with TRIGGER WHEN / DO NOT TRIGGER WHEN. Strip emojis where the destination plugin has none. Normalize ``'Copyleft - requires...'`` to ``'Copyleft: requires...'``.
- **`Jeffallan/claude-skills` (kotlin)**: strip extra upstream frontmatter fields (`license`, `metadata.author`, `version`, `domain`, `triggers`, `role`, `scope`, `output-format`, `related-skills`). Drop the trailing `[Documentation](https://jeffallan.github.io/...)` link. Preserve single-connector em-dashes (`X — Y`) inside code comments; they are not bracketed asides.

---

## Custom plugin maintenance

A "custom plugin" is any plugin NOT listed in the "Upstream-synced plugins" table above. Its content is hand-authored or research-grounded and has no upstream source to re-pull. The list is large (libgdx-development, ibkr-trading, mt5-trading, rag-development, opentelemetry, stripe, csp, grabber-development, browser-extensions, obsidian-development, business, research, codebase-mapper, python-development, typescript-development, senior-review, digital-marketing, docs, learning, app-analyzer, project-setup, marketplace-ops, system-utils, git-worktrees, platform-engineering, testing, react-development, tauri-development, messaging, xterm, clean-code, deep-dive-analysis, ai-tooling, acp-hooks). If a plugin is not in the sync table, it falls under this section.

Custom plugins decay differently than vendored ones. There is no upstream commit to diff against. Versions, framework recommendations, breaking-change notes, and "current as of 2026" claims become stale silently. The maintenance protocol below is the antidote.

### Freshness risk classes

Classify each plugin into one of four classes. The class determines refresh cadence and triage priority.

| Class | What it tracks | Typical cadence | Examples |
|---|---|---|---|
| **Very fast** | Versions bump every few months; breaking changes are common; ecosystem reshuffles | Every 3 months | rag-development (embedding models, rerankers, vector DBs), digital-marketing/ga4-implementation (Consent Mode, GA4 events), react-development (React 19, Vercel guidance) |
| **Fast** | Framework releases 2-3x per year; APIs evolve | Every 6 months | libgdx-development, opentelemetry, tauri-development, stripe (API additions, webhook event types), grabber-development (anti-bot vendor moves), browser-extensions, pwa-expert (browser version churn, WebKit feature rollout, framework PWA library churn) |
| **Moderate** | Major releases ~yearly; breaking changes rare | Every 12 months | ibkr-trading, mt5-trading, csp (OR-Tools), python-development, typescript-development, messaging (RabbitMQ majors), obsidian-development, abstraction-architect (theory is stable; URL list in further-reading.md decays on a yearly cadence) |
| **Slow** | Workflow knowledge that ages by behavior change, not version bumps | Opportunistic; review only when symptoms appear | senior-review, codebase-mapper, team pipeline workflows, ai-tooling skills, project-setup, marketplace-ops, system-utils, git-worktrees, learning, docs, research, business, clean-code, deep-dive-analysis, platform-engineering, testing methodology, xterm, app-analyzer, acp-hooks |

If unsure, default to "Fast" (6 months). Reclassify after the first refresh based on how much actually changed.

### Where hard-coded versions hide

Predictable hot spots, in priority order:

1. **Agent body** -- "Core Knowledge" / "Library Landscape" sections list package names and versions
2. **SKILL.md** -- "Quick Start" steps name install commands with versions
3. **References** -- changelog / breaking-changes sections; benchmark numbers; "as of YYYY" lines
4. **Audit command** -- checklists referencing specific version-gated features
5. **Marketplace.json description** -- if the description name-drops versions (e.g. "RabbitMQ 4.x coverage")

The agent and SKILL.md are the highest-value targets per minute of refresh effort. Reference files matter less for typical users (progressively disclosed) but matter most for power users.

### Update protocol

Steps to refresh a custom plugin. Same protocol regardless of risk class; only the cadence differs.

1. **Re-research the domain** with `research:deep-researcher`. Use angles A (Authoritative) + D (Recency) at minimum. Prompt template:
   ```
   Angles: A + D
   Query: <framework> current version, breaking changes since <version-in-plugin>,
   recommended baseline versions of dependencies, deprecations, ecosystem changes.
   Focus: facts that would change recommendations in an existing knowledge base.
   ```
   Optional: add angle B (Community) if real-world usage patterns are part of what you cover.

2. **Diff the findings against the plugin**. Spawn Explore agents to grep the plugin for the specific version strings and section titles that came up in research. For each, decide:
   - **Clear win**: outdated fact with a confirmed replacement, apply Edit
   - **Subtle shift**: framework changed defaults but old approach still works, mention both
   - **No change**: research confirmed our content is still accurate
   - **Open question**: research was inconclusive, leave a comment and revisit next cycle

3. **Surgical Edits only**. Do not rewrite whole files. Replace specific lines and sentences. Preserve structure so future refreshes have stable anchors.

4. **Bump versions**. Patch bump for fact updates (`1.2.3 -> 1.2.4`). Minor bump if a new section, file, or reference was added (`1.2.3 -> 1.3.0`). Always bump `metadata.version` too (patch is fine unless the marketplace shape itself changed).

5. **Commit with a refresh tag**. Format:
   ```
   Refresh <plugin-name> for <framework> v<new-version> (v<plugin-version>)
   ```
   This makes the git log a searchable record of which plugins got attention when. Use this to decide what to refresh next: anything not touched in a full risk-class cadence is overdue.

### Triage on demand

When you sit down to do a refresh pass and don't know where to start:

```bash
# Plugins not refreshed in the last 6 months
git log --since="6 months ago" --name-only --pretty=format: -- plugins/ \
  | grep -v "^$" | awk -F/ '{print $2}' | sort -u > /tmp/recently-touched.txt

# Compare against the full plugin list in marketplace.json. The difference is your work queue.
```

Refresh the "Very fast" and "Fast" classes first if any are on the work queue; defer "Moderate" and "Slow" classes unless something specific prompted the review.

### When to upgrade a custom plugin to upstream-synced

If during a refresh you discover that someone else's open-source repo now publishes content that overlaps significantly with one of our custom plugins, evaluate vendoring it instead of maintaining from scratch. Follow the "External-repository intake" workflow in this file, then move the plugin's row from this section's mental model into the "Upstream-synced plugins" sync table.
