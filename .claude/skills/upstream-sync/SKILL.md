---
name: upstream-sync
description: >
  The sync table of every plugin ported from an external repository, the default
  upstream-update strategy (classify each file, preserve local customizations, apply targeted
  Edits), the `gh api` fetch patterns, and the non-obvious per-plugin sync notes.
  TRIGGER WHEN: the user asks for "upstream updates", asks to sync or re-pull a plugin from
  its upstream source, or asks which plugins are upstream-synced and what drifted.
  DO NOT TRIGGER WHEN: vendoring from a repository for the FIRST time (use
  `external-repo-intake`), refreshing a hand-authored plugin that has no upstream (use
  `custom-plugin-refresh`), or mirroring our content outward (use `downstream-exports`).
---

# Upstream-synced plugins

Some plugins are ported from external repositories and should be kept in sync with their upstream source. When asked to update one of these plugins, fetch the latest content from the upstream URL using `gh api` and apply any changes, then follow the standard marketplace update workflow in `CLAUDE.md`.

Nothing listed under "Deliberately not vendored" in `CLAUDE.md` belongs in the table below. Those areas were removed and delegated on purpose; do not add rows for them on a future pass. The `obra/superpowers` row is the single exception, and it is scoped: it syncs into `exports/vscode/`, never into `plugins/`. Read the exception paragraph in `CLAUDE.md` before touching it.

## Default upstream-update strategy

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
| `docker` (multi-stage-dockerfile) | `github/awesome-copilot` - `skills/multi-stage-dockerfile/SKILL.md` | `plugins/docker/skills/multi-stage-dockerfile/SKILL.md` |
| `codebase-xray` (semantic-interconnect-mapper) | `wshobson/agents` - `plugins/agent-orchestration/agents/context-manager.md` (pattern cherry-picked, not a direct copy) | `plugins/codebase-xray/agents/semantic-interconnect-mapper.md`. Owned by `senior-review` until marketplace 16.0.0. |
| `typescript-development` (mastering-typescript) | `SpillwaveSolutions/mastering-typescript-skill` - `mastering-typescript/` | `plugins/typescript-development/skills/mastering-typescript/SKILL.md`, `plugins/typescript-development/skills/mastering-typescript/references/*.md`, `plugins/typescript-development/skills/mastering-typescript/scripts/validate-setup.sh`, `plugins/typescript-development/skills/mastering-typescript/assets/tsconfig-template.json`, `plugins/typescript-development/skills/mastering-typescript/assets/eslint-template.js`. Adaptation on sync: SKILL.md frontmatter is rewritten to local convention (keep only `name` and `description`; strip upstream `version`, `category`, `triggers`, `author`, `license`, `tags`). Description uses `description: >` multiline form with explicit TRIGGER WHEN / DO NOT TRIGGER WHEN routing, scoping this skill to enterprise/advanced TS work (advanced type system, JS-to-TS migration, toolchain bootstrap, Zod, deep React + TS, NestJS, LangChain.js) and routing routine TS/JS writes to `typescript-development:typescript-write`, React perf to `react-development:review-react`, and dead-code to `typescript-development:knip`. Without this rewrite the skill failed to auto-activate on its core scenarios because upstream's single-paragraph "Use when..." description loses the router race against `typescript-write` (added in v2.1.0). The local `Source: ...` attribution line at the top of SKILL.md and the body content are NOT subject to upstream-driven frontmatter changes on future syncs. |
| `codebase-cleanup` (cherry-pick, MIT) | `wshobson/agents` - `plugins/codebase-cleanup/commands/` | `plugins/codebase-cleanup/commands/deps-audit.md`, `plugins/codebase-cleanup/commands/refactor-clean.md`, `plugins/codebase-cleanup/commands/tech-debt.md`. Upstream `agents/code-reviewer.md` and `agents/test-automator.md` intentionally NOT vendored (heavy overlap with local `senior-review/*` and `testing/*` coverage). Frontmatters rewritten to local style with TRIGGER WHEN / DO NOT TRIGGER WHEN routing notes, emojis stripped from `deps-audit.md`, license-description strings normalized to colon-separated form. |
| `kotlin-development` (full vendor, MIT) | `Jeffallan/claude-skills` - `skills/kotlin-specialist/` | `plugins/kotlin-development/skills/kotlin-specialist/SKILL.md`, `plugins/kotlin-development/skills/kotlin-specialist/references/{coroutines-flow,multiplatform-kmp,android-compose,ktor-server,dsl-idioms}.md`. Adaptation on sync: strip upstream extra frontmatter fields (`license`, `metadata.author`, `version`, `domain`, `triggers`, `role`, `scope`, `output-format`, `related-skills`); keep only `name` and `description` in local frontmatter; rewrite upstream single-paragraph `description` into local `description: >` multiline form with TRIGGER WHEN / DO NOT TRIGGER WHEN. Add MIT attribution header comment immediately after the frontmatter on SKILL.md and at the top of every reference file. Drop the upstream `[Documentation](https://jeffallan.github.io/...)` link at the bottom of SKILL.md. Single-connector em-dashes ("X — Y") in code comments are preserved as-is (they are NOT bracketed asides). |
| `exports/vscode` (superpowers methodology, MIT) | `obra/superpowers` - `skills/` at version 6.2.0 | `exports/vscode/.github/skills/{using-superpowers,brainstorming,writing-plans,executing-plans,subagent-driven-development,dispatching-parallel-agents,systematic-debugging,test-driven-development,requesting-code-review,receiving-code-review,verification-before-completion,using-git-worktrees,finishing-a-development-branch,writing-skills}/**` plus `exports/vscode/.github/agents/{superpowers,sp-implementer,sp-worker,sp-code-reviewer,sp-task-reviewer,sp-re-reviewer}.agent.md`. This row targets `exports/`, not `plugins/`: see the scoped-exception paragraph in `CLAUDE.md`. **Check [obra/superpowers#764](https://github.com/obra/superpowers/issues/764) first**; if official Copilot support shipped, delete the vendored copy instead of syncing it. Excluded on purpose and NOT to be pulled on a sync: `using-superpowers/references/*-tools.md` (other harnesses), `systematic-debugging/{CREATION-LOG,test-academic,test-pressure-*}.md` (skill-development artifacts), `writing-skills/anthropic-best-practices.md` (Anthropic docs, not MIT), and the two vestigial document-reviewer prompt templates. Adaptations to re-apply on every sync are the twelve in the `downstream-exports` skill plus the superpowers-specific ones in that skill's vendored-upstream section. |
| `project-setup` (Karpathy Working Principles distillation, MIT) | `multica-ai/andrej-karpathy-skills` - `skills/karpathy-guidelines/SKILL.md` | Canonical `## Working Principles` block embedded in `plugins/project-setup/agents/claude-md-auditor.md` (REQUIRED SECTION) and in `plugins/project-setup/examples/good-claude-md-example.md`. The plugin's `create-claude-md` always inserts the block into generated CLAUDE.md files inline; `maintain-claude-md` flags absence, missing principles, or missing sub-bullets as High findings and offers surgical Edits. Adaptation: principles 1-4 are a tighter distillation of upstream's 4 principles (title + 2 lead sentences + 3 locally authored sub-bullets per principle covering the deeper meta-rules: root-cause analysis, evergreen tests, surgical diffs); principle #5 (Centralize Shared Logic) is locally authored. The block is always delivered inline and is never linked out to an external file or `docs/` pointer - this replaces the older optional deep-dive reference pattern (removed in plugin v1.14.0). Attribution comment preserved at the REQUIRED SECTION header in the auditor agent. Upstream is the source of truth for the lead sentences of principles 1-4; if upstream evolves the principle set or wording, update the auditor's canonical block and re-bump `project-setup`. The locally authored sub-bullets and principle #5 are NOT subject to upstream sync. |

## How to sync a plugin

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

- **`domain-hunter`**: upstream Step 3 uses dedicated Twitter/Reddit Python scripts. Replace with `WebSearch` queries targeting `site:x.com` / `site:reddit.com`.
- **`wshobson/agents` (codebase-cleanup)**: commands only. `agents/code-reviewer.md` and `agents/test-automator.md` are intentionally NOT vendored (overlap with `senior-review/*` and `testing/*`).
- **`wshobson/agents` (codebase-cleanup)**: upstream `description:` is a single line. Rewrite into local `description: >` multiline with TRIGGER WHEN / DO NOT TRIGGER WHEN. Strip emojis where the destination plugin has none. Normalize ``'Copyleft - requires...'`` to ``'Copyleft: requires...'``.
- **`obra/superpowers` (exports/vscode)**: check issue #764 before diffing anything; official Copilot support turns this row into a deletion. The attribution header goes AFTER the frontmatter (an HTML comment above the opening `---` stops the file parsing as a skill). Upstream `*-prompt.md` templates map to `sp-*` agents, so an upstream template change is an edit to an agent file, not a new file in the skill directory. Keep `user-invocable: true` and the upstream "Use when..." descriptions: these skills are user entry points, not agent-loaded knowledge bases.
- **`Jeffallan/claude-skills` (kotlin)**: strip extra upstream frontmatter fields (`license`, `metadata.author`, `version`, `domain`, `triggers`, `role`, `scope`, `output-format`, `related-skills`). Drop the trailing `[Documentation](https://jeffallan.github.io/...)` link. Preserve single-connector em-dashes (`X — Y`) inside code comments; they are not bracketed asides.
