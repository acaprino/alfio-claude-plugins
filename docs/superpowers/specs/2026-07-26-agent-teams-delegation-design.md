# Design: Delegate agent-teams to upstream, relocate local pipelines

Date: 2026-07-26
Status: approved (design discussion in session; decisions confirmed by Alfio)
Marketplace target version: 9.0.0

## Goal

Stop maintaining a local copy of the generic multi-agent orchestration content that `wshobson/agents` already publishes as its `agent-teams` plugin. Delete the local `plugins/agent-teams/` and point users at the upstream install. Keep, without loss, the four locally authored team pipelines by relocating each one into the plugin whose agents it orchestrates.

Driver: the local plugin was upstream-synced and required recurring merge maintenance. The generic core (6 commands, 4 agents, 6 skills) diverges little from upstream in value; the real local value lives in the pipelines and in the quality-gate skill sections, which move to better homes.

## Decisions (confirmed)

1. Delegation mode: full removal of `plugins/agent-teams/`; upstream becomes the provider of the generic core.
2. The four local pipelines are relocated to host plugins, not deleted.
3. Residual references from relocated pipelines to upstream generic skills/agents become a declared hard prerequisite on the upstream plugin (consistent with the hard-dependency policy adopted in marketplace 8.2.0, when the superpowers conditional-phrasing rule was dropped and superpowers became a declared dependency of `ai-tooling` and `agent-teams`).
4. Local-only `team-spawn` presets (`app-analysis`, `tauri`, `docs`, `deep-search`) are deleted. Their agents remain reachable directly; `deep-search` routing is remapped to `/research:team-research`.

## Upstream reference

- Repo: `wshobson/agents`, plugin `plugins/agent-teams/` (MIT, author Seth Hobson).
- Install: `/plugin marketplace add wshobson/agents` then `/plugin install agent-teams@claude-code-workflows`.
- Upstream ships commands `team-spawn`, `team-status`, `team-shutdown`, `team-review`, `team-debug`, `team-feature`, `team-delegate`; agents `team-lead`, `team-reviewer`, `team-debugger`, `team-implementer`; the same six skill names as local.
- Because the upstream plugin is also named `agent-teams`, `agent-teams:*` skill/agent references and `/agent-teams:*` command references resolve identically once the upstream plugin is installed. Note: upstream `/agent-teams:team-review` is the generic 78-line multi-reviewer, not our pipeline.
- Team tools (`TeamCreate`, `TeamDelete`, `TaskCreate`, `SendMessage`, etc.) are native Claude Code experimental features, not plugin content. Relocated pipelines keep working without the upstream plugin installed; only skill/agent references need it.

## 1. Removal

- Delete `plugins/agent-teams/` entirely: 10 commands, 4 agents, 6 skills.
- Delete `docs/plugins/agent-teams.md` (397-line plugin doc).
- Remove the `agent-teams` entry from `.claude-plugin/marketplace.json` (currently v3.2.0, lines ~1355-1410), including its `dependencies: ["superpowers"]` and `optionalDependencies: ["abstraction-architect"]`. The superpowers hard dependency survives on `ai-tooling` only.
- Accepted losses (explicit): local-only `team-spawn` presets (`app-analysis`, `tauri`, `docs`, `codebase-mapper`, `deep-search`), the Ecosystem Integration sections of the 4 team agents, the generic bodies of the 6 skills (upstream's versions are used instead), local preset documentation in `team-composition-patterns/references/preset-teams.md`.

## 2. Relocations

| Source (plugins/agent-teams/commands/) | Destination | New invocation |
|---|---|---|
| `team-review.md` | `plugins/senior-review/commands/team-review.md` | `/senior-review:team-review` |
| `team-deep-dive.md` | `plugins/deep-dive-analysis/commands/team-deep-dive.md` | `/deep-dive-analysis:team-deep-dive` |
| `team-codebase-map.md` | `plugins/codebase-mapper/commands/team-codebase-map.md` | `/codebase-mapper:team-codebase-map` |
| `team-research.md` | `plugins/research/commands/team-research.md` | `/research:team-research` |

Rules for the moved files:

- Command filenames do not change, so prose references to bare `/team-review` (for example in `semantic-interconnect-mapper.md`, `api-contract-auditor.md`, `defect-taxonomy/references/logic-integrity.md`) stay valid and are left untouched.
- Artifact paths (`.team-review/`, `.deep-dive/`, `.codebase-map/`) do not change.
- Each moved command gains a Prerequisites block at the top declaring the upstream plugin as required (see section 3).
- Internal cross-references between the four pipelines are rewritten to the new namespaces (for example `team-deep-dive` Phase 4 menu pointing at `/agent-teams:team-review`).

### New skill: `senior-review:review-quality-gates`

The local-only sections of `agent-teams:multi-reviewer-patterns` move into a new skill directory `plugins/senior-review/skills/review-quality-gates/SKILL.md`:

- Adversarial Verification Panel
- Completeness Critic
- Context Sharing Pattern
- The local dedup/severity-calibration rules that `team-review` cites

Extraction criterion: diff the local `multi-reviewer-patterns/SKILL.md` against upstream's version (cached at `.upstream-scratch/wshobson-agent-teams/` or freshly fetched). Only content absent upstream goes into the new skill; anything upstream already covers is delegated.

Consumers updated to point at `senior-review:review-quality-gates`:

- `plugins/senior-review/commands/code-review.md` lines ~839, ~841, ~867 (Steps 4b/4c). Graceful-degradation fallbacks in that file are kept but the primary reference changes. This closes a latent breakage: those sections do not exist in upstream `multi-reviewer-patterns`, so after delegation the old reference would have found the skill installed but the sections missing.
- The relocated `team-review.md` (verification panel, completeness critic, dedup sections).
- `docs/references/agent-teams-best-practices.md` line ~127 (canonical home of the two quality gates).

## 3. Hard prerequisite on upstream

- Each relocated pipeline command opens with a Prerequisites block naming the upstream plugin and the two install commands, and stating that the command requires it (for `agent-teams:team-communication-protocols`, `agent-teams:task-coordination-strategies`, `agent-teams:team-composition-patterns`, `agent-teams:parallel-feature-development`, and, for team-review only, the `agent-teams:team-reviewer` fallback agent for the 4 generic dimensions).
- References keep the `agent-teams:` namespace unchanged since the upstream plugin resolves them.
- CLAUDE.md amendment: the conditional-phrasing rule for superpowers was already dropped in marketplace 8.2.0 (superpowers is a declared hard dependency of `ai-tooling` and `agent-teams`); extend the same policy by stating that the relocated team pipelines declare upstream `agent-teams` (wshobson/agents) as a hard prerequisite.

## 4. Rewiring map

Namespace rewrite `/agent-teams:team-review` -> `/senior-review:team-review` in:

- `plugins/senior-review/agents/`: `code-auditor.md`, `security-auditor.md`, `logic-integrity-auditor.md`, `cleanup-auditor.md`, `distributed-flow-auditor.md`, `ui-race-auditor.md`, `chicken-egg-detector.md` (Pipeline Conventions blocks and frontmatter).
- `plugins/senior-review/commands/`: `full-review.md` (deprecation notice), `cleanup-dead-code.md` (DO-NOT-TRIGGER note), `code-review.md` (DO-NOT-TRIGGER note).
- `plugins/platform-engineering/agents/platform-reviewer.md`, `plugins/react-development/agents/react-performance-optimizer.md` (pipeline blocks).
- `plugins/abstraction-architect/agents/abstraction-architect.md` (TRIGGER WHEN), `plugins/abstraction-architect/commands/audit.md` (Related + monorepo advice, which also moves to `/deep-dive-analysis:team-deep-dive`), and the abstraction-architect `description` in `marketplace.json`.

Namespace rewrite `/agent-teams:team-deep-dive` -> `/deep-dive-analysis:team-deep-dive` in:

- `plugins/deep-dive-analysis/agents/`: `partition-structure-worker.md`, `partition-behavior-worker.md`, `partition-quality-worker.md`, `deep-dive-synthesizer.md` (frontmatter and body).
- `plugins/deep-dive-analysis/skills/deep-dive-analysis/SKILL.md` (team-mode escalation at ~L354; downstream consumer note at ~L360 also becomes `/senior-review:team-review`).
- `plugins/abstraction-architect/agents/abstraction-architect.md` (~L41, interconnect-map input note).

`plugins/ai-tooling/skills/acp-loader/SKILL.md`:

- Workflow Awareness table: pipeline rows point at `/senior-review:team-review`, `/deep-dive-analysis:team-deep-dive`, `/codebase-mapper:team-codebase-map`, `/research:team-research`. Generic rows (`team-feature`, `team-debug`) keep `/agent-teams:*` with a note that they require the upstream wshobson plugin. Rows for dead presets (`app-analysis`, `tauri`) are removed; the host plugins' own commands and skills remain the direct route.
- Decision tree ~L70: the Tauri entry points at tauri-development skills directly instead of `agent-teams:team-spawn tauri`.

`plugins/acp-hooks/hooks/handlers/team-spawn-gate.js` (11 hardcoded command strings):

- `review` phrases -> `/senior-review:team-review`.
- `deep-search` and `research` phrases -> `/research:team-research`.
- `docs`, `app-analysis`, `tauri` preset entries -> removed.
- `fullstack`, `migration`, `security` presets and `team-debug`, `team-feature` -> keep `/agent-teams:*` (upstream provides them; injection text notes the upstream plugin requirement).
- `STATIC_FALLBACK_CATALOG` keeps the 4 `agent-teams:team-*` agent ids (they exist when upstream is installed).
- `buildAgentCatalog()` self-updates from `marketplace.json`; no change needed.
- `marketplace.json`: remove `"agent-teams"` from acp-hooks `optionalDependencies`.

`plugins/libgdx-development/agents/libgdx-architect.md` ~L276: the Ecosystem Integration bullet cites upstream `/agent-teams:team-feature` with the wshobson provenance noted.

## 5. Docs, CLAUDE.md, README, memory

- `docs/README.md`: remove the agent-teams index row (L13); replace the quickstart example (L58) and the "How Plugins Work"-style mentions; reword L82 and L88.
- `README.md`: replace `/agent-teams:team-feature` examples (L45, L157) with a surviving command (use `/senior-review:team-review`); remove the plugin table row (L96); reword L146; extend the delegated-upstream section (the one covering frontend and superpowers) with agent-teams and the upstream install commands.
- `docs/references/agent-teams-best-practices.md`: stays (cross-cutting knowledge base). Reword the scope statement (L3-L5), point the quality-gates note (L127) at `senior-review:review-quality-gates`, update "Where this applies" (L197-L198) to the relocated pipeline homes.
- Per-plugin docs Related/capability notes updated: `acp-hooks.md`, `clean-code.md`, `ai-tooling.md`, `git-worktrees.md`, `app-analyzer.md`, `platform-engineering.md`, `python-development.md`, `react-development.md`, `tauri-development.md`, `senior-review.md`. References to dead presets are dropped; generic team references gain the upstream provenance; `/team-review` phase references move to `/senior-review:team-review`.
- `CLAUDE.md`: plugin count 44 -> 43 and list updated; remove the agent-teams sync-table row and the agent-teams-specific sync notes (stale-tool-name greps, description-rewrite note); add an agent-teams row to "Deliberately not vendored" (removed in marketplace 9.0.0, upstream `wshobson/agents`, pipelines relocated); amend the conditional-phrasing rule per section 3; update the maintenance-class list ("agent-teams workflows" entry) and the `docs/references` pointer prose.
- Memory: update `vendoring-to-refs-shelved.md` to record that on 2026-07-26 the delegation was applied to agent-teams (generic core delegated, four pipelines relocated); the shelved status now covers only the remaining synced plugins.

## 6. Versioning and commit

- Minor bumps: `senior-review` (new command + new skill), `deep-dive-analysis`, `codebase-mapper`, `research` (new commands), `acp-hooks` (gate rewrite), `ai-tooling` (acp-loader rewrite).
- Patch bumps: `abstraction-architect`, `libgdx-development`, `platform-engineering`, `react-development` (reference updates).
- `metadata.version`: 8.2.0 -> 9.0.0 (plugin removal is a breaking marketplace change, precedent: frontend removal in 7.0.0).
- Single atomic commit: deletions, relocations, new skill, all rewiring, docs, CLAUDE.md, marketplace.json. Push to master.
- Commit message: `Delegate agent-teams to wshobson/agents, relocate team pipelines (v9.0.0)` with a body listing relocation map and removals.

## 7. Verification

- `Grep 'agent-teams'` across the repo; expected survivors only: upstream install/prerequisite prose, CLAUDE.md not-vendored row and amended rule, README delegation section, `agent-teams:*` skill/agent references that intentionally resolve via the upstream plugin, gate entries pointing at upstream commands, spec files under `docs/superpowers/`.
- `Grep '/agent-teams:team-(review|deep-dive|codebase-map|research|spawn)'` must return no functional references except the documented upstream `team-spawn` survivors.
- Validate `marketplace.json` (JSON parse) and `node --check` on `team-spawn-gate.js`.
- `git status` clean of strays; `git diff --stat` scope sanity check.

## Out of scope

- No changes to the native Agent Teams feature flags or settings.
- No relocation of `docs/references/agent-teams-best-practices.md` (name kept; content reworded only where it names the removed plugin).
- No changes to the other upstream-synced plugins.
