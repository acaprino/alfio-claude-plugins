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
    hooks/                  # hook handlers (JS/Python) + hooks.json (prompt-improver)
exports/
  <host>/                   # ports of selected plugins to non-Claude-Code hosts
```

39 plugins (`codebase-xray` was named `deep-dive-analysis` until marketplace 14.0.0; its analysis artifact directory is still `.deep-dive/`, which is the stable downstream contract): clean-code, codebase-xray, tauri-development, react-development, xterm, ai-tooling, python-development, stripe, system-utils, messaging, research, business, project-setup, app-analyzer, typescript-development, csp, digital-marketing, senior-review, obsidian-development, browser-extensions, learning, marketplace-ops, prompt-improver, codebase-mapper, rag-development, docs, testing, platform-engineering, ibkr-trading, mt5-trading, opentelemetry, docker, grabber-development, codebase-cleanup, libgdx-development, kotlin-development, pwa-expert, abstraction-architect, text-humanizer.

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

**Hooks** - Used by the `prompt-improver` plugin. Contains `hooks.json` (hook definitions) and `handlers/` directory with JS handler scripts.

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
3. **Check the downstream exports** - if the changed plugin appears in the "Downstream exports" table below, mirror the change into `exports/` in the same commit. Skipping this is how the ports silently rot.
4. **Commit together** - stage the plugin files, `marketplace.json`, and any `exports/` changes in one commit
5. **Push to remote** - `git push` to `master`

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

`docs/plugins/` contains per-plugin documentation. `docs/references/` holds cross-cutting knowledge bases that inform changes across multiple plugins — notably [`agent-teams-best-practices.md`](docs/references/agent-teams-best-practices.md), the source of truth when restructuring any plugin that spawns multi-agent teams or pipeline reviewers (`senior-review`, `codebase-mapper`, `research`, `codebase-xray`).

## External-repository intake

When the user asks to "import", "pull", "vendor", "cherry-pick", or "borrow from" an external GitHub repository (anything not already in the sync table below), follow this workflow before touching any local file. This section covers the *first* intake. Re-syncing repositories already registered uses the separate workflow under "Upstream-synced plugins" below.

### 1. Classify the operation

We do not fork, submodule, or add runtime dependencies. The only intake mode for this marketplace is **vendoring**: a one-shot or tracked copy of upstream content into our tree, with attribution preserved and the content adapted to our conventions.

| Sub-mode | When to pick | Example |
|---|---|---|
| **Full vendoring** | Upstream is a complete drop-in (a single SKILL.md, a small set of references) and there is no local equivalent | `kotlin-development` |
| **Cherry-pick vendoring** | Upstream has many files but only a subset adds value, or the upstream commands collide with our existing namespace | `wshobson/agents` (3 codebase-cleanup commands imported, 2 agents skipped for overlap) |
| **Hybrid merge** | Upstream covers ground that overlaps with a local file; append upstream content as a delimited section instead of creating a duplicate | `wshobson/agents` e2e-testing-patterns `references/details.md` kept inline in the local SKILL.md sections |
| **Inspiration only** | We adopt patterns or workflow ideas but write our own content from scratch; no upstream text copied | `codebase-xray` from `gsd-build/get-shit-done` |

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
- **Stale tool names** in team-related imports: `Teammate` / `Task tool to spawn` -> `Agent tool`; explicit `TeamCreate` / `TeamDelete` steps -> rewrite to implicit team formation (the team forms when the first teammate is spawned) and automatic cleanup at session end (both tools were removed in Claude Code 2.1.178).

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

6. **Watch for stale tool names** (common drift source): `` `Teammate` tool `` / `` `Task` tool to spawn `` -> fix to `` `Agent` tool ``; `` `TeamCreate` `` / `` `TeamDelete` `` / `` Call `Teammate` cleanup `` / `` operation: "spawnTeam" `` -> rewrite to implicit team formation on first spawn and automatic cleanup at session end (Claude Code 2.1.178 removed TeamCreate/TeamDelete). Grep team-related imports after any sync to catch these.

7. **Version bump and commit** - bump each touched plugin's `version` in `.claude-plugin/marketplace.json`, bump `metadata.version`, and commit everything together with a descriptive message like "Sync upstream updates for X and Y (vN.N.N)". Push to master.

8. **Verify** - run `Grep` for any remaining stale tool names, confirm marketplace.json is consistent, then `git status` / `git diff --stat` before committing.


| Plugin | Upstream source | Files to sync |
|--------|----------------|---------------|
| `codebase-xray` (inspiration) | `gsd-build/get-shit-done` - `agents/gsd-codebase-mapper.md` | `plugins/codebase-xray/commands/analyze.md` (patterns adopted, not direct copy) |
| `react-development` (react-best-practices) | `vercel-labs/agent-skills` - `skills/react-best-practices/` | `plugins/react-development/skills/react-best-practices/SKILL.md`, `plugins/react-development/skills/react-best-practices/references.md`, `plugins/react-development/skills/react-best-practices/rules/*.md` |
| `digital-marketing` (domain-hunter) | `ReScienceLab/opc-skills` - `skills/domain-hunter/` | `plugins/digital-marketing/skills/domain-hunter/SKILL.md`, `plugins/digital-marketing/skills/domain-hunter/references/registrars.md`, `plugins/digital-marketing/skills/domain-hunter/references/spaceship-api.md`, `plugins/digital-marketing/skills/domain-hunter/examples/auto-video-editing-domain.md` |
| `prompt-improver` | `severity1/claude-code-prompt-improver` (v0.6+: upstream replaced `scripts/improve-prompt.py` with a declarative nudge engine: `scripts/engine.py`, `scripts/rules.py`, `scripts/nudge_builtins.py`, `nudges/<Event>/*.json`) | `plugins/prompt-improver/skills/prompt-improver/SKILL.md`, `plugins/prompt-improver/skills/prompt-improver/references/*.md`, `plugins/prompt-improver/hooks/handlers/improve-prompt.js`, `plugins/prompt-improver/hooks/handlers/plan-guidance.js`, `plugins/prompt-improver/hooks/handlers/background-exec.js`, `plugins/prompt-improver/hooks/handlers/subagent-routing.js`. Local stays a flat-JS-handler port (cherry-pick adoption, 2026-06-10): improve + plan-guidance + background-exec + subagent-routing nudges are ported; the approach-assessment, output-readability, ask-user-question, plan-mode, and workflow nudges are intentionally NOT vendored (overlap with native Claude Code behavior; would inject context on nearly every prompt). |
| `testing` (tdd) | `mattpocock/skills` - `skills/engineering/tdd/` | `plugins/testing/skills/tdd/SKILL.md`, `plugins/testing/skills/tdd/references/tests.md`, `plugins/testing/skills/tdd/references/deep-modules.md`, `plugins/testing/skills/tdd/references/mocking.md`, `plugins/testing/skills/tdd/references/interface-design.md`, `plugins/testing/skills/tdd/references/refactoring.md`. Intentional drift (decided 2026-07-12): upstream 2026-06-30 reshaped the skill to a red->green reference-only framing with "pre-agreed seams", moved refactoring out to its code-review skill, DELETED deep-modules/interface-design/refactoring, and flattened tests.md/mocking.md to the tdd/ top level. Local keeps the red-green-refactor loop, the references/ subdir, and all three deleted files; do NOT re-propose the reshape on future syncs. Content-level additions to the surviving files (tests.md, mocking.md, e.g. the tautological-tests anti-pattern pulled 2026-07-12) ARE still synced. |
| `docker` (multi-stage-dockerfile) | `github/awesome-copilot` - `skills/multi-stage-dockerfile/SKILL.md` | `plugins/docker/skills/multi-stage-dockerfile/SKILL.md` |
| `testing` (e2e-testing-patterns) | `wshobson/agents` - `plugins/developer-essentials/skills/e2e-testing-patterns/` (upstream split SKILL.md into a slim tier + `references/details.md` in 2026 for Codex's 8 KB body cap) | `plugins/testing/skills/e2e-testing-patterns/SKILL.md`. Local intentionally keeps the detailed content INLINE in SKILL.md (well under the 5k-word ceiling); on future syncs diff upstream `references/details.md` against the local inline sections, not as a local-only gap. |
| `codebase-xray` (semantic-interconnect-mapper) | `wshobson/agents` - `plugins/agent-orchestration/agents/context-manager.md` (pattern cherry-picked, not a direct copy) | `plugins/codebase-xray/agents/semantic-interconnect-mapper.md`. Owned by `senior-review` until marketplace 16.0.0. |
| `typescript-development` (mastering-typescript) | `SpillwaveSolutions/mastering-typescript-skill` - `mastering-typescript/` | `plugins/typescript-development/skills/mastering-typescript/SKILL.md`, `plugins/typescript-development/skills/mastering-typescript/references/*.md`, `plugins/typescript-development/skills/mastering-typescript/scripts/validate-setup.sh`, `plugins/typescript-development/skills/mastering-typescript/assets/tsconfig-template.json`, `plugins/typescript-development/skills/mastering-typescript/assets/eslint-template.js`. Adaptation on sync: SKILL.md frontmatter is rewritten to local convention (keep only `name` and `description`; strip upstream `version`, `category`, `triggers`, `author`, `license`, `tags`). Description uses `description: >` multiline form with explicit TRIGGER WHEN / DO NOT TRIGGER WHEN routing, scoping this skill to enterprise/advanced TS work (advanced type system, JS-to-TS migration, toolchain bootstrap, Zod, deep React + TS, NestJS, LangChain.js) and routing routine TS/JS writes to `typescript-development:typescript-write`, React perf to `react-development:review-react`, and dead-code to `typescript-development:knip`. Without this rewrite the skill failed to auto-activate on its core scenarios because upstream's single-paragraph "Use when..." description loses the router race against `typescript-write` (added in v2.1.0). The local `Source: ...` attribution line at the top of SKILL.md and the body content are NOT subject to upstream-driven frontmatter changes on future syncs. |
| `codebase-cleanup` (cherry-pick, MIT) | `wshobson/agents` - `plugins/codebase-cleanup/commands/` | `plugins/codebase-cleanup/commands/deps-audit.md`, `plugins/codebase-cleanup/commands/refactor-clean.md`, `plugins/codebase-cleanup/commands/tech-debt.md`. Upstream `agents/code-reviewer.md` and `agents/test-automator.md` intentionally NOT vendored (heavy overlap with local `senior-review/*` and `testing/*` coverage). Frontmatters rewritten to local style with TRIGGER WHEN / DO NOT TRIGGER WHEN routing notes, emojis stripped from `deps-audit.md`, license-description strings normalized to colon-separated form. |
| `kotlin-development` (full vendor, MIT) | `Jeffallan/claude-skills` - `skills/kotlin-specialist/` | `plugins/kotlin-development/skills/kotlin-specialist/SKILL.md`, `plugins/kotlin-development/skills/kotlin-specialist/references/{coroutines-flow,multiplatform-kmp,android-compose,ktor-server,dsl-idioms}.md`. Adaptation on sync: strip upstream extra frontmatter fields (`license`, `metadata.author`, `version`, `domain`, `triggers`, `role`, `scope`, `output-format`, `related-skills`); keep only `name` and `description` in local frontmatter; rewrite upstream single-paragraph `description` into local `description: >` multiline form with TRIGGER WHEN / DO NOT TRIGGER WHEN. Add MIT attribution header comment immediately after the frontmatter on SKILL.md and at the top of every reference file. Drop the upstream `[Documentation](https://jeffallan.github.io/...)` link at the bottom of SKILL.md. Single-connector em-dashes ("X — Y") in code comments are preserved as-is (they are NOT bracketed asides). |
| `project-setup` (Karpathy Working Principles distillation, MIT) | `multica-ai/andrej-karpathy-skills` - `skills/karpathy-guidelines/SKILL.md` | Canonical `## Working Principles` block embedded in `plugins/project-setup/agents/claude-md-auditor.md` (REQUIRED SECTION) and in `plugins/project-setup/examples/good-claude-md-example.md`. The plugin's `create-claude-md` always inserts the block into generated CLAUDE.md files inline; `maintain-claude-md` flags absence, missing principles, or missing sub-bullets as High findings and offers surgical Edits. Adaptation: principles 1-4 are a tighter distillation of upstream's 4 principles (title + 2 lead sentences + 3 locally authored sub-bullets per principle covering the deeper meta-rules: root-cause analysis, evergreen tests, surgical diffs); principle #5 (Centralize Shared Logic) is locally authored. The block is always delivered inline and is never linked out to an external file or `docs/` pointer - this replaces the older optional deep-dive reference pattern (removed in plugin v1.14.0). Attribution comment preserved at the REQUIRED SECTION header in the auditor agent. Upstream is the source of truth for the lead sentences of principles 1-4; if upstream evolves the principle set or wording, update the auditor's canonical block and re-bump `project-setup`. The locally authored sub-bullets and principle #5 are NOT subject to upstream sync. |

### Deliberately not vendored

Six areas were removed and delegated to their upstreams because maintaining the local copy cost more than it returned (the first five were vendored copies handed back; `git-worktrees` was locally authored content retired in favor of equivalent upstream coverage). Do NOT re-import or re-create them, and do not add sync-table rows for them on a future "upstream updates" pass. The README documents all six for users.

| Area | Upstream | Removed in |
|---|---|---|
| Frontend and design (`frontend` plugin: 3 agents, 5 skills, 1 command) | `pbakaus/impeccable`, `nextlevelbuilder/ui-ux-pro-max-skill`, `paulirish/dotfiles` | marketplace 7.0.0 |
| Brainstorming, planning, execution (`ai-tooling` skills `brainstorming`, `writing-plans`, `executing-plans`) | `obra/superpowers` | marketplace 8.0.0, ai-tooling 3.0.0 |
| Multi-agent generic core (`agent-teams` plugin: 6 commands, 4 agents, 6 skills) | `wshobson/agents` | marketplace 9.0.0 |
| Browser automation (`playwright-skill` plugin: 1 skill) | `lackeyjb/playwright-skill` | marketplace 11.0.0 |
| Binary reverse engineering (`reverse-engineering` plugin: 3 agents, 4 skills) | `wshobson/agents` | marketplace 12.0.0 |
| Git worktree parallel development (`git-worktrees` plugin: 1 agent, 1 skill, 1 command) | `obra/superpowers` (`using-git-worktrees` skill) | marketplace 13.0.0 |

As of marketplace 8.2.0, superpowers is a declared hard dependency of `ai-tooling` (`dependencies: ["superpowers@claude-plugins-official"]` in `marketplace.json`; cross-marketplace dependencies MUST use the qualified `name@marketplace` form, because a bare name resolves against this marketplace and fails the whole plugin load, which is what silently broke `ai-tooling` until marketplace 12.0.2). Any place that points at the superpowers planning skills says so unconditionally: load the skills, and if they are unavailable stop and tell the user to install superpowers (`claude plugin install superpowers@claude-plugins-official`). This supersedes the earlier rule that kept superpowers references conditional; do not reintroduce conditional phrasing.

The same policy applies to the team pipelines: `/senior-review:team-review`, `/codebase-xray:team-analyze`, `/codebase-mapper:team-codebase-map`, and `/research:team-research` declare the upstream `agent-teams` plugin (wshobson/agents) as a hard prerequisite in their Prerequisites blocks, and as of marketplace 13.2.0 all four owning plugins also declare it as a hard dependency in `marketplace.json` (`"agent-teams@claude-code-workflows"`, qualified form per the superpowers note above). The upstream plugin keeps the same `agent-teams:*` namespace, so those references resolve as written once it is installed (`/plugin marketplace add wshobson/agents`, then `/plugin install agent-teams@claude-code-workflows`). The four pipelines and the `senior-review:review-quality-gates` skill are local content with no upstream sync.

Marketplace 16.0.0 restructured the review and documentation layer so that the hard-dependency graph is a tree rooted at `codebase-xray`, the plugin that establishes how the code actually works. The trigger was one misplaced file: `semantic-interconnect-mapper` lived in `senior-review` while serving three pipelines, which forced `codebase-mapper` to hard-depend on `senior-review` for a context asset and forced `codebase-xray` to keep `senior-review` in `optionalDependencies` to avoid closing a cycle. The agent now lives in `codebase-xray/agents/`, and the current declarations are:

| Plugin | `dependencies` | `optionalDependencies` |
|---|---|---|
| `codebase-xray` | `agent-teams@claude-code-workflows` | none |
| `senior-review` | `agent-teams@claude-code-workflows`, `codebase-xray` | `abstraction-architect`, `react-development`, `platform-engineering`, `python-development`, `typescript-development` |
| `codebase-mapper` | `agent-teams@claude-code-workflows`, `codebase-xray`, `text-humanizer` | `senior-review` |
| `abstraction-architect` | `codebase-xray` | none |

Rules that follow from this shape, all load-bearing:

- **Nothing in `codebase-xray` may reference a `senior-review` agent, skill, or command at runtime.** Prose "next steps" suggestions are fine; a spawn or Skill invocation is not. That edge is what the old cycle was made of.
- **`senior-review`'s five optional dependencies must degrade, never fail.** `python-development` and `typescript-development` are read-if-present knowledge-base pointers and were never spawned. The other three back conditional review dimensions: React performance, platform compliance, and abstraction. Every spawn site says to skip the dimension and report it as "not installed" when its plugin is absent, in `team-review` Phase 0b and in `code-review` Agents D, I, and J. A new conditional dimension backed by another plugin follows the same pattern: `optionalDependencies` plus an explicit skip note.
- **`codebase-mapper` keeps `senior-review` optional for `defect-taxonomy` only** (the drift-detection reference in `guide-reviewer`, already an "Optionally load"). Do not promote it: the mapper agent it used to need is now in `codebase-xray`, which it hard-depends on.

Do not reintroduce the old shape on a future pass. In particular, do not move a shared context asset into a consumer plugin, and do not promote a conditional-dimension plugin back to a hard dependency.

The same pass retired `/senior-review:cleanup-dead-code`. There is no standalone cleanup command: the capability is split by scope instead. The **lite** pass (dead code plus VCS hygiene, scoped to the diff) runs inside existing agents of `/senior-review:code-review` and `/senior-review:pr-review`, adding no spawns. The **full** pass (all five hygiene dimensions across the whole codebase) is the always-on `cleanup-auditor` dimension of `/senior-review:team-review`. **Removal** is Step 7c of `/senior-review:code-review --fix`, which owns the seven-phase workflow with its clean-tree pre-flight, commit-per-phase isolation, build-and-test gate, and `git reset --hard HEAD~1` revert. Migration for anything that pointed at the old command: `/senior-review:cleanup-dead-code --phase=X` becomes `/senior-review:code-review --fix` working phase `X` at Step 7c. Do not recreate the command; `cleanup-auditor` stays detection-only and its findings name a fix phase, never a command.

`research` is deliberately self-contained: it is a general-purpose research tool usable on any topic (not just code), so it must never hard-depend on development plugins. As of research 3.0.0 (marketplace 13.2.1) the team-research Domain Expert role is a domain-prompted `research:deep-researcher` instance (the persona lives in the prompt), replacing the old dispatch table that spawned `senior-review`/`typescript-development`/`python-development`/`tauri-development`/`business`/`react-development` agents; do not reintroduce development-plugin agents into team-research. Its only declarations are `agent-teams@claude-code-workflows` (hard, team skills) and `codebase-mapper` (optional: the Context Builder role, spawned only when the question touches a local project and skipped with a note when the plugin is absent).

Browser automation follows the same pattern as of marketplace 11.0.0: the vendored `playwright-skill` plugin was a byte-level copy of its upstream (only convention adaptations: TRIGGER WHEN frontmatter, temp-dir portability, emoji stripping), so it was removed and delegated. `app-analyzer`, `pwa-expert`, `digital-marketing`, and `grabber-development` declare `playwright-skill` as a hard dependency (`dependencies: ["playwright-skill@playwright-skill"]` in `marketplace.json`; qualified form required for cross-marketplace dependencies, see the superpowers note above). The upstream plugin keeps the same `playwright-skill:playwright-skill` namespace, so existing references resolve as written once it is installed (`claude plugin marketplace add lackeyjb/playwright-skill`, then `claude plugin install playwright-skill@playwright-skill`). Their commands and agents state this install path in their dependency-check blocks; do not point those blocks back at this marketplace.

Binary reverse engineering follows the same pattern as of marketplace 12.0.0: the vendored `reverse-engineering` plugin was a byte-level copy of `wshobson/agents` `plugins/reverse-engineering/` (only convention adaptations: MIT attribution comments, agent `model: inherit` and `color: purple`, three upstream `references/details.md` files kept inline in the local SKILL.md bodies), so it was removed and delegated. Upstream publishes it under the same `reverse-engineering` plugin name with identical agent and skill names in the `claude-code-workflows` marketplace (`claude plugin marketplace add wshobson/agents`, then `claude plugin install reverse-engineering@claude-code-workflows`). No local plugin references or depends on it, so no dependency declarations or reference rewrites were needed.

Git worktrees were retired as of marketplace 13.0.0, with one difference from the other rows: the `git-worktrees` plugin (worktree-agent, worktree-manager skill, `/wt` command) was locally authored, not vendored. It was removed because superpowers' `using-git-worktrees` skill covers the isolation workflow (workspace detection, native-tool-first creation with `git worktree` fallback, project setup, clean-baseline verification) and superpowers is already a hard dependency of `ai-tooling` and a required install for this marketplace. The `/wt` lifecycle extras (pause/resume session context, guided merge) were retired without replacement: plain `git worktree` commands cover them. No local plugin referenced or depended on `git-worktrees` (it only declared an optionalDependency on `senior-review`), so no dependency declarations or reference rewrites were needed. The README documents this in its "Git worktrees (parallel development)" section, alongside a must-have callout for `using-git-worktrees` in the superpowers section.

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

A "custom plugin" is any plugin NOT listed in the "Upstream-synced plugins" table above. Its content is hand-authored or research-grounded and has no upstream source to re-pull. The list is large (libgdx-development, ibkr-trading, mt5-trading, rag-development, opentelemetry, stripe, csp, grabber-development, browser-extensions, obsidian-development, business, research, codebase-mapper, python-development, typescript-development, senior-review, digital-marketing, docs, learning, app-analyzer, project-setup, marketplace-ops, system-utils, platform-engineering, testing, react-development, tauri-development, messaging, xterm, clean-code, codebase-xray, ai-tooling, text-humanizer). If a plugin is not in the sync table, it falls under this section.

Custom plugins decay differently than vendored ones. There is no upstream commit to diff against. Versions, framework recommendations, breaking-change notes, and "current as of 2026" claims become stale silently. The maintenance protocol below is the antidote.

### Freshness risk classes

Classify each plugin into one of four classes. The class determines refresh cadence and triage priority.

| Class | What it tracks | Typical cadence | Examples |
|---|---|---|---|
| **Very fast** | Versions bump every few months; breaking changes are common; ecosystem reshuffles | Every 3 months | rag-development (embedding models, rerankers, vector DBs), digital-marketing/ga4-implementation (Consent Mode, GA4 events), react-development (React 19, Vercel guidance) |
| **Fast** | Framework releases 2-3x per year; APIs evolve | Every 6 months | libgdx-development, opentelemetry, tauri-development, stripe (API additions, webhook event types), grabber-development (anti-bot vendor moves), browser-extensions, pwa-expert (browser version churn, WebKit feature rollout, framework PWA library churn) |
| **Moderate** | Major releases ~yearly; breaking changes rare | Every 12 months | ibkr-trading, mt5-trading, csp (OR-Tools), python-development, typescript-development, messaging (RabbitMQ majors), obsidian-development, abstraction-architect (theory is stable; URL list in further-reading.md decays on a yearly cadence) |
| **Slow** | Workflow knowledge that ages by behavior change, not version bumps | Opportunistic; review only when symptoms appear | senior-review, codebase-mapper, team pipeline workflows, ai-tooling skills, project-setup, marketplace-ops, system-utils, learning, docs, research, business, clean-code, codebase-xray, platform-engineering, testing methodology, xterm, app-analyzer, text-humanizer |

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

---

## Downstream exports

The mirror image of "External-repository intake". That section covers content flowing *in* from other repos; this one covers our content flowing *out* to hosts that are not Claude Code. `exports/<host>/` holds those ports.

**Direction is one-way: `plugins/` is the source of truth, `exports/` is derived.** Never edit an export and back-port to the plugin. If a fix belongs in both, make it in `plugins/` first, then mirror.

**The obligation is scoped, not global.** Only the plugins in the table below feed an export, and inside those plugins only the listed files. A change to any of the other plugins, or to an unlisted file, needs no export work. Do not re-mirror the whole plugin because one line moved in a file that was never exported.

### Active exports

| Export | Host | Entry points |
|---|---|---|
| `exports/vscode/` | VS Code Copilot (`.github/skills/`, `.github/prompts/`, `.github/agents/`) | `/xray-team-analyze`, `/team-review` |

### Source map for `exports/vscode/`

| Source in `plugins/` | Derived in `exports/vscode/.github/` |
|---|---|
| `codebase-xray/skills/analyze/**` (SKILL.md, references, assets, scripts) | `skills/codebase-xray/**` |
| `codebase-xray/commands/team-analyze.md` | `prompts/xray-team-analyze.prompt.md` + `skills/codebase-xray/references/workflow.md` |
| `codebase-xray/agents/partition-{structure,behavior,quality}-worker.md` | `agents/xray-{structure,behavior,quality}-worker.agent.md` |
| `codebase-xray/agents/partition-synthesizer.md` | `agents/xray-synthesizer.agent.md` |
| `codebase-xray/agents/semantic-interconnect-mapper.md` | `agents/xray-interconnect-mapper.agent.md` |
| `senior-review/agents/{security,code,logic-integrity,cleanup,ui-race,distributed-flow,api-contract}-auditor.md` | `agents/review-<same>.agent.md` |
| `senior-review/agents/chicken-egg-detector.md` | `agents/review-chicken-egg-detector.agent.md` |
| `senior-review/commands/team-review.md` | `prompts/team-review.prompt.md` + `skills/review-quality-gates/references/pipeline.md` |
| `senior-review/skills/defect-taxonomy/**` | `skills/defect-taxonomy/**` |
| `senior-review/skills/review-quality-gates/SKILL.md` | `skills/review-quality-gates/SKILL.md` |
| `react-development/agents/react-performance-optimizer.md` | `agents/review-react-performance-optimizer.agent.md` |
| `platform-engineering/agents/platform-reviewer.md` | `agents/review-platform-reviewer.agent.md` |
| `abstraction-architect/agents/abstraction-architect.md` | `agents/review-abstraction-architect.agent.md` |
| `abstraction-architect/skills/abstraction-architect/**` | `skills/abstraction-architect/**` |

Export-only files with no source in `plugins/`, maintained directly in `exports/vscode/`: `agents/xray-orchestrator.agent.md`, `agents/review-orchestrator.agent.md`, `agents/review-generic-reviewer.agent.md`, `agents/review-verification-lens.agent.md`, `agents/review-completeness-critic.agent.md`, `skills/codebase-xray/hooks/xray_guard.py`, `README.md`. The two orchestrators and the three support agents exist because VS Code gates subagent dispatch behind an `agents:` allowlist and has no `general-purpose` subagent; there is nothing upstream to mirror them from.

Deliberately NOT exported: `codebase-xray/commands/analyze.md`, `senior-review/commands/{code-review,pr-review}.md`, `abstraction-architect/commands/audit.md`, and every file of `react-development` and `platform-engineering` other than the single agent listed.

### Adaptations to re-apply on every mirror

A copied file is never correct as-is. Re-apply all of these:

1. **Frontmatter conversion.** Claude Code `name` / `description` / `model: inherit` / `color` / `tools: Read, Write, Glob, Grep, Bash` becomes VS Code `name` / `description` / `user-invocable: false` / `tools:` (YAML list of namespaced ids) / `agents: []` / `hooks:`. Drop `model` and `color`; VS Code has neither. Rewrite `description` to drop TRIGGER WHEN / DO NOT TRIGGER WHEN routing: subagents are dispatched explicitly by an orchestrator, not auto-routed.
2. **Tool names.** `Read` -> `read/readFile`, `Grep` -> `search/textSearch`, `Glob` -> `search/fileSearch`, `Write` -> `edit/createFile`, `Edit` -> `edit/editFiles`, `Bash` -> `execute/runInTerminal`, `WebFetch` -> `web/fetch`, Task-tool spawning -> `agent/runSubagent`. Applies to prose too (`Grep for X`, `` the `Read` tool ``), not only frontmatter. Watch for false positives: `import.meta.glob` in `cleanup-auditor` is Vite vocabulary, not a tool name.
3. **Agent names.** `senior-review:<x>` -> `review-<x>`, X-ray workers -> `xray-<x>`, `semantic-interconnect-mapper` -> `xray-interconnect-mapper`. Every cross-agent reference in a body must resolve to an agent that exists in the export.
4. **Plugin namespaces and commands that do not exist in the export.** `/senior-review:team-review` -> `/team-review`; `/senior-review:code-review --fix` Step 7c cleanup references -> a bare phase label, since no fix command is exported; `typescript-development:` / `python-development:` / `clean-code:` skill pointers -> plain descriptions.
5. **`${CLAUDE_PLUGIN_ROOT}`** -> the `$XRAY` probe over `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/`.
6. **Task-status polling** (`TaskCreate` / `TaskList` / `TaskUpdate`) -> file-existence barriers verified with `#search/fileSearch`.
7. **Team infrastructure** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, `agent-teams` prerequisites, `shutdown_request`) -> delete. VS Code subagents need no flag, no plugin, and no teardown.
8. **`agent-teams:team-reviewer` fallbacks** -> `review-generic-reviewer` with the dimension named in the dispatch prompt.
9. **The `PreToolUse` guard block** on every worker and reviewer, with `--confine .deep-dive` for X-ray workers and `--confine .team-review` for reviewers. Orchestrators do not declare it.

### Divergences that must survive the mirror

These are decisions, not drift. A sync that "fixes" them is a regression:

- **No classic single-context X-ray.** `/codebase-xray:analyze` is not exported; the single-partition fallback covers it. `--phase N` is rejected with an explicit error.
- **`/team-review` Phase 1a and 1b are collapsed into one X-ray run** at `--depth=lite`. The exported X-ray pipeline already emits `08-interconnect-map.md`, so the interconnect mapper is not run a second time. Phase 1 copies that file to `.team-review/02-interconnect.md`.
- **Reviewers read the X-ray run directory**, never the `.deep-dive/` root mirror, which a concurrent run can republish mid-review.
- **The API contracts dimension uses `review-api-contract-auditor`**, not a generic reviewer. Upstream ships the specialized agent but never wires it into `team-review`.
- **No model pinning on the verification lenses.** Upstream pins a cheaper model on lens 3; the correct Copilot model id varies per user, so the export leaves it to the picker.
- **The guard hook enforces only the unambiguous secret patterns.** `*secret*` and `*credential*` stay prompt-level, because `secrets_manager.py` is a legitimate analysis target.
- **Phase 0b detection is expressed on search tools**, not a bash `grep`/`sed`/`awk` pipeline, so it works on Windows without a POSIX layer.

Two former divergences became alignments in marketplace 16.0.0, when the plugins adopted what the export had already worked out. Do not re-add them to the list above: the dead-code dimension now resolves to `cleanup-auditor` in both of `team-review`'s tables, and `cleanup-auditor` findings now end with `Fix phase: <phase>` upstream too. The export needed no content change for either.

### Versioning and verification

The export carries its own `metadata.version` inside `skills/codebase-xray/SKILL.md`. Bump it when the exported content changes, independently of the marketplace version. `exports/` is not registered in `marketplace.json` and is not a plugin.

Before committing an export change, re-run the checks in `exports/vscode/README.md` terms:

- Every `.md` frontmatter parses as YAML, with no fields outside the VS Code schema for its type (skill / agent / prompt)
- Every tool id in `tools:` and every `#tool` reference in prose is a real VS Code tool
- Agent cross-references close in both directions: nothing referenced but undefined, nothing defined but unreferenced, nothing outside every `agents:` allowlist
- `grep` the export for residual Claude Code coupling: `CLAUDE_PLUGIN_ROOT`, `CLAUDE_CODE_`, `Skill(`, `Teammate`, `TaskCreate`, `subagent_type`, `<plugin>:` namespaces. The only legitimate hits are in `README.md`, which names the originals on purpose.
- The guard hook test suite passes: `python exports/vscode/.github/skills/codebase-xray/hooks/test_xray_guard.py` (36 cases across both `--confine` values, secret patterns, path edge cases, and fail-open behavior; runs from any working directory)
