---
name: downstream-exports
description: >
  How to mirror our content OUT to hosts that are not Claude Code: the `exports/vscode/`
  source map, the twelve adaptations to re-apply on every mirror, the divergences that must
  survive a sync, the three-family method for a full re-audit, and the verification checks
  plus their known false positives.
  TRIGGER WHEN: the user asks to update, mirror, regenerate, or audit anything under
  `exports/`, or a change lands in a plugin file that feeds an export (`codebase-xray`,
  `senior-review`, `react-development/agents/react-performance-optimizer.md`,
  `platform-engineering/agents/platform-reviewer.md`, `abstraction-architect`).
  DO NOT TRIGGER WHEN: pulling content IN from an external repo (use `external-repo-intake`
  or `upstream-sync`), or changing a plugin file that this skill's source map does not list.
---

# Downstream exports

The mirror image of the `external-repo-intake` skill. That skill covers content flowing *in* from other repos; this one covers our content flowing *out* to hosts that are not Claude Code. `exports/<host>/` holds those ports.

**Direction is one-way: `plugins/` is the source of truth, `exports/` is derived.** Never edit an export and back-port to the plugin. If a fix belongs in both, make it in `plugins/` first, then mirror.

**The obligation is scoped, not global.** Only the plugins in the table below feed an export, and inside those plugins only the listed files. A change to any of the other plugins, or to an unlisted file, needs no export work. Do not re-mirror the whole plugin because one line moved in a file that was never exported.

## Active exports

| Export | Host | Entry points |
|---|---|---|
| `exports/vscode/` | VS Code Copilot (`.github/skills/`, `.github/prompts/`, `.github/agents/`) | `/xray-team-analyze`, `/team-review` |

## Source map for `exports/vscode/`

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

## Vendored upstream content in the export

Since 2026-07-30 the export also carries content that flows neither out of `plugins/` nor from this repo at all: 14 skills from `obra/superpowers` 6.2.0 (MIT), plus the six agents that serve them (`superpowers`, `sp-implementer`, `sp-worker`, `sp-code-reviewer`, `sp-task-reviewer`, `sp-re-reviewer`). `plugins/` deliberately does not contain them, so **never try to mirror these from a local plugin, and never treat their absence in `plugins/` as drift.** Their upstream is the external repo, and they are tracked by the `exports/vscode` row of the `upstream-sync` sync table. `CLAUDE.md` records why the "deliberately not vendored" rule has this one scoped exception, and points at [obra/superpowers#764](https://github.com/obra/superpowers/issues/764): if official Copilot support ships, the correct move is deletion, not a sync.

Four adaptations apply to this family beyond the twelve below:

1. **The attribution header goes AFTER the frontmatter**, not before it. An HTML comment above the opening `---` stops the file from parsing as a skill.
2. **Prompt templates become agents.** Upstream ships `*-prompt.md` files meant to be pasted into an ad-hoc `general-purpose` subagent. VS Code dispatches named agents from an allowlist, so each template becomes an `sp-*.agent.md`, and the skill body points at the agent instead of the file.
3. **These skills stay `user-invocable: true`,** unlike the four pipeline skills. They are the user's entry points (`/systematic-debugging`), not knowledge bases an agent loads, so their descriptions keep the upstream "Use when..." activation prose that adaptation 1 strips elsewhere.
4. **No resume, no model pin.** Upstream resumes a live implementer for fix rounds 1-3 and requires an explicit model per dispatch. VS Code can do neither: every round is a fresh dispatch carrying the report file, and the model is a property of the agent file, left unpinned for the same reason the verification lenses are.

## Adaptations to re-apply on every mirror

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
10. **De-branding.** "Claude" as the actor becomes "the agent" or "the AI": the export runs on Copilot. Applies to reference bodies too, not just agent prompts (`AI_ANALYSIS_METHODOLOGY.md`, `SEMANTIC_PATTERNS.md`, `analysis-templates.md` all carry it). The only legitimate "Claude" mentions left are the handful that explicitly compare against "the Claude Code original" when documenting a divergence.
11. **Plugin-dependency degradation notes** get deleted, not translated. Upstream tells `team-review` to skip a conditional dimension when its plugin is absent; in the export every agent ships inside the bundle, so a dimension is skipped only when its activation rule did not fire. Never mirror a "not installed" branch.
12. **Prose capitalization after the tool rename.** `Grep` mid-sentence becomes lowercase `search`, not `Search`, since `Grep` was a proper noun and `search` is not. Sentence-initial occurrences stay capitalized.

## Divergences that must survive the mirror

These are decisions, not drift. A sync that "fixes" them is a regression:

- **No classic single-context X-ray.** `/codebase-xray:analyze` is not exported; the single-partition fallback covers it. `--phase N` is rejected with an explicit error.
- **`/team-review` Phase 1a and 1b are collapsed into one X-ray run** at `--depth=lite`. The exported X-ray pipeline already emits `08-interconnect-map.md`, so the interconnect mapper is not run a second time. Phase 1 copies that file to `.team-review/02-interconnect.md`.
- **Reviewers read the X-ray run directory**, never the `.deep-dive/` root mirror, which a concurrent run can republish mid-review.
- **No model pinning on the verification lenses.** Upstream pins a cheaper model on lens 3; the correct Copilot model id varies per user, so the export leaves it to the picker.
- **The guard hook enforces only the unambiguous secret patterns.** `*secret*` and `*credential*` stay prompt-level, because `secrets_manager.py` is a legitimate analysis target.
- **Phase 0b detection is expressed on search tools**, not a bash `grep`/`sed`/`awk` pipeline, so it works on Windows without a POSIX layer.

Three former divergences became alignments across marketplace 16.0.0 and 16.1.0, when the plugins adopted what the export had already worked out. Do not re-add them to the list above:

- The dead-code dimension resolves to `cleanup-auditor` in both of `team-review`'s tables.
- `cleanup-auditor` findings end with `Fix phase: <phase>` upstream too.
- The API contracts dimension resolves to `api-contract-auditor` upstream, and `review-quality-gates` no longer marks that dimension `(future)`. Upstream also gained the concrete contract-file detection globs the export had introduced, because the old path-only rule (`routes?`, `api/`, `endpoints?/`, `handlers?/`) never fired on a bare `openapi.yaml` or `schema.graphql` change, which is the specialized auditor's core case.

The export needed no content change for any of the three.

## Full re-audit of the export

When the ask is to "regenerate the whole export" rather than mirror one change, **diff every file against its source; do not rewrite the files.** Rewriting 70-odd files to reproduce them identically adds risk without changing the result, and the risk is real: a careless edit mid-audit corrupted a markdown table in `pipeline.md` and had to be reverted. The deliverable is the same (every file verified against its source, not just the recent deltas), the method is comparison.

Sort the files into three families first, because each is audited differently:

| Family | Files | How to audit |
|---|---|---|
| **Byte-copies** (no adaptation applies) | the 19 X-ray `scripts/**`, `templates/*` mirrored to `assets/*`, and the reference bodies that contain no tool names, agent names, or "Claude" | `diff -q` against the source. Any difference is drift, unless it is one of adaptations 10 or 12. |
| **Adapted** | every `*.agent.md`, both `*.prompt.md`, all four `SKILL.md`, and the references that do name tools or agents | Compare **section headers**, not whole bodies: `diff <(grep -o '^#\+ .*' src) <(grep -o '^#\+ .*' exp)`. Header-level differences are renames and export-only additions; a header present in the source and absent in the export is real drift, which is the only thing worth reading line by line. |
| **Export-only** (no source exists) | `agents/{xray,review}-orchestrator`, `agents/review-{generic-reviewer,verification-lens,completeness-critic}`, `agents/superpowers`, `hooks/xray_guard.py` + its tests, `README.md` | Check internal consistency against the regenerated content: allowlists, dispatched agent names, phase names. Nothing upstream to compare to. |
| **Vendored upstream** (source is an external repo) | the 14 superpowers skill directories, `agents/sp-*.agent.md` | Diff against `obra/superpowers` at the pinned version, not against `plugins/`. Same header-level method as the adapted family. Every difference must trace to one of the twelve adaptations, one of the four superpowers-specific ones, or the exclusion list in the sync-table row. |

The 2026-07-30 audit found the byte-copy and adapted families fully in sync, with one real defect in `review-cleanup-auditor` (a directive whose label had drifted from its own content, a phase list missing an entry, and flag syntax for a command the bundle never shipped). Expect that shape again: drift concentrates in agents whose upstream source changed recently, not in the bulk of the tree.

## Versioning and verification

The export carries its own `metadata.version` inside `skills/codebase-xray/SKILL.md`. Bump it when the exported content changes, independently of the marketplace version. `exports/` is not registered in `marketplace.json` and is not a plugin.

Before committing an export change, re-run the checks in `exports/vscode/README.md` terms:

- Every `.md` frontmatter parses as YAML, with no fields outside the VS Code schema for its type (skill / agent / prompt)
- Every tool id in `tools:` and every `#tool` reference in prose is a real VS Code tool
- Agent cross-references close in both directions: nothing referenced but undefined, nothing defined but unreferenced, nothing outside every `agents:` allowlist
- `grep` the export for residual Claude Code coupling: `CLAUDE_PLUGIN_ROOT`, `CLAUDE_CODE_`, `Skill(`, `Teammate`, `TaskCreate`, `subagent_type`, `<plugin>:` namespaces. The only legitimate hits are in `README.md`, which names the originals on purpose.
- The guard hook test suite passes: `python exports/vscode/.github/skills/codebase-xray/hooks/test_xray_guard.py` (36 cases across both `--confine` values, secret patterns, path edge cases, and fail-open behavior; runs from any working directory)

Three of those checks produce false positives that have already cost one pass. Do not act on them without confirming first:

- **`tools:` lists are longer than they look, and not every id has a slash.** `review-orchestrator` declares 16 tool ids. A `grep -A<n>` with n below that silently truncates the list and makes a declared tool look undeclared; `vscode/askQuestions` sits at position 15 and is the one that gets missed. Separately, a `[a-z]+/[a-zA-Z]+` pattern drops `todos` at position 16, since it carries no namespace prefix. Parse the YAML block to its terminator instead of grepping for a shape.
- **Legitimate frontmatter fields that a naive schema check rejects:** `argument-hint` on the two orchestrators (they are user-facing entry points), `user-invocable` on all four skills, and `compatibility` on `codebase-xray/SKILL.md`. The real invariant is distributional, and it holds: the 19 dispatched agents all carry `user-invocable` plus `hooks`, the 2 orchestrators carry neither and add `argument-hint`.
- **`codebase-xray:` matches inside `xray_guard.py`** are message prefixes in error strings, not plugin namespaces. Scope the namespace grep to `.md` files, or read the three hits before concluding anything.
