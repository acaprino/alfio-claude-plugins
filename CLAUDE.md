# Claude Code Daodan

The Daodan is the symbiote that augments its host. This repository is the Daodan of Claude Code: a marketplace of agents, skills, and commands that augment the base model into a specialized toolkit covering development workflows, code quality, AI tooling, scraping, trading, observability, and more. Remote: `acaprino/claude-code-daodan` on GitHub.

## Project structure

`.claude-plugin/marketplace.json` is the plugin registry and the source of truth for which plugins exist and at what version. Each `plugins/<name>/` holds any of `agents/`, `skills/`, `commands/`, `hooks/`. `exports/<host>/` holds ports of selected plugins to hosts that are not Claude Code; `exports/vscode/` is a publishable VS Code extension as well as a directory of bundles.

`codebase-xray` was named `deep-dive-analysis` until marketplace 14.0.0. Its analysis artifact directory is still `.deep-dive/`, which is the stable downstream contract.

## Conventions

- Agent names: kebab-case matching the filename (e.g. `quick-searcher.md`)
- Plugin names: kebab-case directory names
- Default model: `inherit` (agents follow the session model instead of pinning one); exceptions noted per-agent (e.g. `quick-searcher` uses `sonnet`)
- Agent `color` must be one of: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`
- Agent body style: terse keyword lists, imperative tone, structured with markdown headers; simple agents ~50-200 lines, complex agents up to ~700 lines
- Long `description` frontmatter values use the YAML multiline `>` form
- Skills supplementary subdirs: `references/`, `scripts/`, `templates/`, `assets/`, `lib/` as needed
- No build step or runtime framework - plugins are markdown with optional helper scripts (Python, JS) in skills' `scripts/` subdirs
- Avoid the dash-aside construct anywhere (code, comments, commit messages, documentation). The rule targets the *rhetorical pattern* of bracketing a clause between dashes, in any form: `—` (em dash), `--` (double hyphen), or ` - ` (spaced hyphen). All three are banned when used to wrap a parenthetical aside (e.g., "lorem ipsum -- lorem ipsum -- lorem ipsum"). Substituting `--` for `—` is **not** the fix. Rewrite into separate sentences, parentheses, colons, or just delete the aside. Hyphenated compounds (`file-ownership`, `multi-agent`) are unrelated and fine.

## Marketplace update workflow

When changes modify plugins (agents, skills, commands), update the marketplace **before committing**:

1. **Bump plugin version** - increment `version` for the changed plugin in `.claude-plugin/marketplace.json`
2. **Bump marketplace version** - increment `metadata.version` in the same file
3. **Mirror into the downstream export** - since the 2026-07-30 catalog build, `exports/vscode/` carries a bundle for every plugin except `prompt-improver`, so almost any plugin change needs mirroring. Load the `downstream-exports` skill and mirror into `exports/` in the same commit, then run its checker (`python .claude/skills/downstream-exports/scripts/check_export.py`). If an agent or prompt was added, renamed or removed, also regenerate the extension manifest (`python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py`) and bump `version` in `exports/vscode/package.json`. Skipping this is how the ports silently rot.
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

No build step, no runtime tests: all content is static markdown. There IS a consistency CI (`.github/workflows/consistency.yml`, runs on push to `master` and on PRs) that mechanically enforces contracts which used to live only in this file. Four checks, all stdlib-only Python runnable from the repo root:

1. `python scripts/lint_dependency_graph.py` — the dependency-graph linter. Extracts runtime cross-plugin references (agent spawns, skill loads) from plugin bodies and enforces: every runtime reference is declared in `dependencies`/`optionalDependencies`; bare dependency names must exist in this marketplace (cross-marketplace deps use the qualified `name@marketplace` form); the forbidden edge `codebase-xray → senior-review` never reappears; spawns of optional-dependency agents carry a nearby skip note. `--refs` prints the extracted edge list.
2. `python .claude/skills/downstream-exports/scripts/check_export.py` — the export structural checker (see the `downstream-exports` skill).
3. `python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check` — fails if `exports/vscode/package.json` contribution lists are stale relative to the bundles on disk.
4. `python scripts/check_version_bumps.py <base-rev> [<head-rev>]` — over the pushed or PR commit range, a change under `plugins/<name>/` must come with a bump of that plugin's `version` and of `metadata.version` (steps 1 and 2 of the marketplace update workflow).

When a change legitimately trips the linter, fix the declaration (or the reference), not the linter; heuristic misreads go in its `ALLOWLIST` with a reason.

## Documentation

`docs/plugins/` contains per-plugin documentation. `docs/references/` holds cross-cutting knowledge bases that inform changes across multiple plugins — notably [`agent-teams-best-practices.md`](docs/references/agent-teams-best-practices.md), the source of truth when restructuring any plugin that spawns multi-agent teams or pipeline reviewers (`senior-review`, `codebase-mapper`, `research`, `codebase-xray`).

## Repo workflows

Four maintenance workflows live in `.claude/skills/` so they load only when the task calls for them. Load the matching skill before starting; do not improvise these from memory.

| Skill | Load it when |
|---|---|
| `external-repo-intake` | Importing, vendoring, or cherry-picking from an external GitHub repo for the FIRST time. Covers classification, the license gate, convention adaptation, and the commit shape. |
| `upstream-sync` | Re-syncing a plugin already ported from an upstream repo, or answering "which plugins are upstream-synced". Holds the sync table, the merge strategy, and the per-plugin sync notes. |
| `custom-plugin-refresh` | Refreshing a hand-authored plugin that has no upstream. Holds the freshness risk classes, cadences, and the re-research protocol. |
| `downstream-exports` | Touching `exports/`, or changing almost any plugin file (see step 3 of the marketplace update workflow). Holds the source map, the mirror adaptations, the four dispatch shapes, the VS Code extension layer and how to package it, the content that deliberately keeps Claude Code vocabulary, the divergences that must survive a sync, and the verification scripts. |

## Deliberately not vendored

Six areas were removed and delegated to their upstreams because maintaining the local copy cost more than it returned (the first five were vendored copies handed back; `git-worktrees` was locally authored content retired in favor of equivalent upstream coverage). Do NOT re-import or re-create them, and do not add rows for them to the sync table in the `upstream-sync` skill on a future "upstream updates" pass. The README documents all six for users.

| Area | Upstream | Removed in |
|---|---|---|
| Frontend and design (`frontend` plugin: 3 agents, 5 skills, 1 command) | `pbakaus/impeccable`, `nextlevelbuilder/ui-ux-pro-max-skill`, `paulirish/dotfiles` | marketplace 7.0.0 |
| Brainstorming, planning, execution (`ai-tooling` skills `brainstorming`, `writing-plans`, `executing-plans`) | `obra/superpowers` | marketplace 8.0.0, ai-tooling 3.0.0 |
| Multi-agent generic core (`agent-teams` plugin: 6 commands, 4 agents, 6 skills) | `wshobson/agents` | marketplace 9.0.0 |
| Browser automation (`playwright-skill` plugin: 1 skill) | `lackeyjb/playwright-skill` | marketplace 11.0.0 |
| Binary reverse engineering (`reverse-engineering` plugin: 3 agents, 4 skills) | `wshobson/agents` | marketplace 12.0.0 |
| Git worktree parallel development (`git-worktrees` plugin: 1 agent, 1 skill, 1 command) | `obra/superpowers` (`using-git-worktrees` skill) | marketplace 13.0.0 |

As of marketplace 8.2.0, superpowers is a declared hard dependency of `ai-tooling` (`dependencies: ["superpowers@claude-plugins-official"]` in `marketplace.json`; cross-marketplace dependencies MUST use the qualified `name@marketplace` form, because a bare name resolves against this marketplace and fails the whole plugin load, which is what silently broke `ai-tooling` until marketplace 12.0.2). Any place that points at the superpowers planning skills says so unconditionally: load the skills, and if they are unavailable stop and tell the user to install superpowers (`claude plugin install superpowers@claude-plugins-official`). This supersedes the earlier rule that kept superpowers references conditional; do not reintroduce conditional phrasing.

One scoped exception to the superpowers row, taken on 2026-07-30: `exports/vscode/` vendors 14 superpowers skills and the 6 agents that serve them, adapted for VS Code Copilot. This does not reopen the delegation. `plugins/` still delegates, `ai-tooling` still hard-depends on `superpowers@claude-plugins-official`, and nothing under `plugins/` may re-import those skills. The exception exists because there is no Copilot install path for superpowers: the export ships it or nothing does. The vendored copy is pinned to upstream 6.2.0 and tracked by its own row in the `upstream-sync` sync table, which is the only row in that table pointing at `exports/` instead of `plugins/`.

On 2026-07-30 the export was restructured from one bundle into a **catalog of 36 bundles**, one per plugin, and the port was extended from 5 plugins to 38. Later the same day it was packaged as a **single VS Code extension**, because the per-project `cp -r` install was the thing users actually wanted gone. `exports/vscode/` is now both the extension root (`package.json`, `extension.js`, `uninstall.js`, `.vscodeignore`, `CHANGELOG.md`, `LICENSE`) and the catalog, and `exports/vscode/<plugin>/.github/` is still a bundle. `_pipelines` is the former single bundle and the only one carrying more than one plugin (`codebase-xray`, `senior-review`, `abstraction-architect`, plus the vendored superpowers content). Four consequences bind future work:

- **The mirror obligation is global.** Every plugin except `prompt-improver` feeds a bundle, so step 3 of the marketplace workflow applies to almost every plugin change.
- **The bundles stay split on disk even though distribution merged.** The extension ships all 36, but each stays a self-contained `.github/` directory. That is what keeps the per-project install working for anyone who wants a narrower footprint, and what a future release would need to scope contributions per workspace. Do not flatten the directories into one tree.
- **Agents and prompts are contributed; skills are copied.** `package.json` declares every agent and prompt path under `chatAgents` and `chatPromptFiles`, so adding, renaming or removing one means regenerating it with `python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py`. Skills are deliberately absent from that manifest: `extension.js` copies whole skill directories into `~/.copilot/skills/` instead, because 45 of the 66 carry supporting files and a contributed skill loads only its `SKILL.md` ([microsoft/vscode#304721](https://github.com/microsoft/vscode/issues/304721), open). If that issue ships, the copy layer is what to delete.
- **`marketplace-ops` and `ai-tooling/agent-sdk-builder` keep Claude Code vocabulary.** Their subject matter *is* Claude Code, so their tool names and `TRIGGER WHEN` labels are content. Never de-brand or tool-rename them; the `downstream-exports` checker excludes both.

**Watch [obra/superpowers#764](https://github.com/obra/superpowers/issues/764)**, the tracking issue for official GitHub Copilot / VS Code support. When upstream ships it, the vendored copy is the thing to delete rather than to sync: drop the 14 skill directories, drop the `sp-*` and `superpowers` agents that exist only to supply the dispatch layer VS Code gates behind an allowlist, and point the export README at the official install path. Check the issue on every superpowers sync pass, before diffing any file.

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
