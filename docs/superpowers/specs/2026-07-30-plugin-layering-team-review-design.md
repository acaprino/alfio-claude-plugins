# Plugin layering around codebase-xray, and the dead-code consolidation

Date: 2026-07-30
Status: approved, pending implementation plan
Marketplace: 15.0.0 to 16.0.0

## Problem

`team-review` is the flagship pipeline of this marketplace, and its dependency list does not describe it honestly. Two separate problems overlap.

**The layering is inverted.** The intended architecture puts `codebase-xray` at the root, since it is the component that establishes how the code actually works, with two consumers on top: `team-codebase-map` for documentation and `team-review` for review, each with narrow-scoped non-team alternatives. The declared graph says something else:

```
senior-review   --hard-->  codebase-xray, agent-teams, abstraction-architect,
                           react-development, platform-engineering,
                           python-development, typescript-development
codebase-mapper --hard-->  senior-review, agent-teams, text-humanizer
codebase-xray   --opt--->  senior-review
```

The root cause is a single misplaced file. `semantic-interconnect-mapper` lives in `plugins/senior-review/agents/` but is a context-building asset of the xray layer. Its consumers, in order of dependence, are `codebase-xray:team-analyze` (which needs it to emit `08-interconnect-map.md`), `codebase-mapper` (Phase 1b plus the `tech-writer`, `flow-writer`, `ops-writer`, and `guide-reviewer` agents), and only third `senior-review:team-review` (Phase 1b). Its own frontmatter already describes it as plugin-neutral: "Phase 1b for pipelines that need a structured map ... Used by /team-review (fed by codebase-xray) and by /map-codebase".

That misplacement forces two distortions. `codebase-mapper` declares a hard dependency on `senior-review` when what it actually needs is a context mapper, and it is missing the hard dependency on `codebase-xray` that `map-codebase.md:5` already exercises. And `codebase-xray` must keep `senior-review` in `optionalDependencies`, a compromise CLAUDE.md documents with an instruction not to promote it, because promoting it would close a cycle against the hard `senior-review -> codebase-xray` edge.

The VS Code export is independent evidence that the intended layering is the correct one. `exports/vscode/README.md:192` and `:200` record that the mapper was vendored as `xray-interconnect-mapper` inside the X-ray pipeline as its own phase, and that Phase 1a and 1b of `team-review` collapse into a single X-ray run because the interconnect map already arrives from there. Porting to a host with no plugin dependency system produced the layering by itself.

**The dependency list is over-declared.** Of `senior-review`'s seven hard dependencies only two are real. `python-development` and `typescript-development` are never spawned; they appear only as read-if-present knowledge-base pointers in `api-contract-auditor.md:167-168` and `cleanup-auditor.md:6`. `abstraction-architect` is declared hard even though `team-review.md:123` already documents graceful degradation for it. `react-development` and `platform-engineering` are genuine spawn targets but conditional on React or fullstack detection, and they carry no degradation note, so three conditional dimensions behave in two different ways.

**Separately, `cleanup-dead-code` should not exist as a narrow command.** The dead-code capability belongs inside the review commands: a lite pass in `code-review` and `pr-review`, a full pass as a step of `team-review`. Most of that is already true and unstated. `code-review.md` Agent B2 (lines 310-393) already runs ruff, vulture, knip, and tsc against the changed files, and `cleanup-auditor` is already an always-on dimension of `team-review`. What is missing is the lite pass in `pr-review`, which has none, and what is broken is the dimension-to-agent table in `team-review.md:231`, which resolves the dead-code dimension to `general-purpose` in direct contradiction with the always-on table at `:106`. CLAUDE.md records that the export fixed this contradiction and the plugin did not.

## Decisions taken

Four forks were resolved before this spec was written:

1. **Move the shared asset and fix the declarations**, rather than dependency hygiene alone or a full three-layer redesign of the team infrastructure.
2. **`agent-teams` stays a hard dependency on all four pipeline plugins.** The marketplace 13.2.0 policy is left intact so this change stays about the layering of context assets. Demoting it remains a separate decision, evaluable across all four plugins at once.
3. **No compatibility alias** for the moved agent. The major bump on `senior-review` and on the marketplace signals the break; a spawnable stub returning empty output would confuse more than a clean "Agent type not found".
4. **The removal machinery is absorbed into `code-review`'s Fix Loop**, not extracted into a skill and not deleted.

Accepted consequence of decision 4: `/senior-review:code-review --fix` becomes the only place from which removal happens, so after a `team-review` the removal requires a second command. That is the cost of having no dedicated narrow command.

## Part A: codebase-xray becomes the root

### The move

One file, 259 lines, content unchanged:

```
plugins/senior-review/agents/semantic-interconnect-mapper.md
   -> plugins/codebase-xray/agents/semantic-interconnect-mapper.md
```

New namespace: `codebase-xray:semantic-interconnect-mapper`. Frontmatter is left as-is: `name`, the `description` with its TRIGGER WHEN and DO NOT TRIGGER WHEN clauses (already accurate, it cites both pipelines), `tools: Read, Write, Glob, Grep`, `model: inherit`, `color: cyan`.

### Namespaced references to rewrite

Line numbers are anchors valid at the time of writing. Confirm each by grep at implementation time, since earlier edits shift later ones.

| File | Line |
|---|---|
| `plugins/codebase-mapper/agents/flow-writer.md` | 20 |
| `plugins/codebase-mapper/agents/ops-writer.md` | 20 |
| `plugins/codebase-mapper/agents/tech-writer.md` | 20 |
| `plugins/codebase-mapper/commands/map-codebase.md` | 53 |
| `plugins/codebase-mapper/commands/team-codebase-map.md` | 83 |
| `plugins/codebase-mapper/skills/codebase-mapper/SKILL.md` | 69 |
| `plugins/codebase-xray/commands/team-analyze.md` | 296 |
| `plugins/codebase-xray/skills/analyze/SKILL.md` | 379 |
| `plugins/senior-review/commands/team-review.md` | 198 |
| `plugins/senior-review/skills/review-quality-gates/SKILL.md` | 23 |
| `docs/plugins/codebase-mapper.md` | 10, 171 |
| `docs/plugins/codebase-xray.md` | 80 |
| `.claude-plugin/marketplace.json` | 651 (agent path), 823 (description text naming "the senior-review semantic-interconnect-mapper") |

Bare-name references carry no namespace and stay valid as text: `senior-review/agents/api-contract-auditor.md:31,166`, `senior-review/agents/logic-integrity-auditor.md:6,28`, `senior-review/skills/defect-taxonomy/references/logic-integrity.md:3`, `senior-review/commands/team-review.md:167`, `codebase-mapper/commands/team-codebase-map.md:46`.

Documentation ownership moves with the agent: the `### semantic-interconnect-mapper` section at `docs/plugins/senior-review.md:115` moves into `docs/plugins/codebase-xray.md`. The remaining bare mentions at `docs/plugins/senior-review.md:145,171,257` stay, since they describe how `team-review` consumes the map.

### Dependency declarations after the change

| Plugin | dependencies | optionalDependencies |
|---|---|---|
| `codebase-xray` | `agent-teams@claude-code-workflows` | none |
| `senior-review` | `codebase-xray`, `agent-teams@claude-code-workflows` | `abstraction-architect`, `react-development`, `platform-engineering`, `python-development`, `typescript-development` |
| `codebase-mapper` | `codebase-xray`, `agent-teams@claude-code-workflows`, `text-humanizer` | `senior-review` |
| `abstraction-architect` | `codebase-xray` | none |

The `codebase-xray -> senior-review` optional edge is removed outright rather than demoted. After the move, the only references from xray to senior-review are next-step suggestions in prose (`analyze.md:487,589`, `team-analyze.md:316,352`), which are not runtime dependencies. The hard graph becomes a tree rooted at `codebase-xray`.

`codebase-mapper` keeps `senior-review` as optional for one reason only: `guide-reviewer.md:65` reads `defect-taxonomy/references/logic-integrity.md` for drift-detection patterns, and the instruction there already says "Optionally load".

### Graceful degradation parity

In `team-review.md` Phase 0b, the `react-development` row (`:115`) and the `platform-engineering` row (`:117`) gain the degradation clause already carried by the `abstraction-architect` row at `:123`: when the plugin is not installed, skip the dimension and record it under Skipped rather than attempting a spawn that would fail. All three conditional dimensions then behave identically, matching the demotion to `optionalDependencies`.

## Part B: dead code as lite and full passes

### Deletion

`plugins/senior-review/commands/cleanup-dead-code.md` (269 lines) is deleted. Its Step 2 detection was already duplicated by `cleanup-auditor` across all five dimensions. Its Step 3 removal machinery is absorbed into `code-review`.

### Absorption into code-review

A new **Step 7c: Cleanup Phases** is added to `code-review.md` inside the Fix Loop, directly after Step 7b (Apply Fixes). The existing Step 7c (Re-review Offer) and Step 7d (Post-fix Options) shift down to 7d and 7e. The new step runs only when cleanup findings were accepted at Step 7a. It carries the source command's critical rules unchanged:

- Pre-flight: `git status` must be clean; warn and halt otherwise.
- Phase isolation: one commit per category, never mixed, so each step is independently revertible.
- Gate after every phase: build must pass and tests must not regress against the baseline; on failure, `git reset --hard HEAD~1` and halt.
- Grep-before-delete: a final confirmation grep with zero results before any removal, skipped on any match.
- Never remove what is used through side effects: dynamic imports, decorators, framework conventions, module augmentation in `*.d.ts` with `declare module`.
- Python functions and classes require explicit user approval, since vulture's false-positive rate is high.

Phase order is preserved: `garbage`, `brand`, `assets`, `gitignore`, `deps`, `exports`, `docs`, lowest risk first, stopping at the first gate failure. The `docs` phase stays report-only unless explicitly applied.

### The lite perimeter

Lite is dimension D1 (dead code via ruff, vulture, knip, tsc) plus dimension D3 (generated artifacts tracked in VCS, filesystem garbage, `.gitignore` gaps), both scoped to the files in the diff. Neither command gains an agent: the work goes into an existing spawn.

- `code-review.md`: Agent B2 ("Dead Code & Unused Parameter Detection", a backgrounded `general-purpose` spawn at lines 310-393) already covers D1 in its Phase 1 Automated Lint. D3 is added to that same agent's prompt as a second mandatory phase, so the agent count does not change.
- `pr-review.md`: has no dead-code coverage at all today, and its Phase 2 spawns two agents in parallel. The lite pass is added to the prompt of the existing risk-assessment agent rather than as a third spawn, keeping the command as light as it is now.

D3 is included because it is nearly free to compute and has a false-positive rate close to zero, and because without it a committed `nul` file or a tracked build artifact stays invisible until someone runs a full `team-review`.

### The full perimeter

Full is all five dimensions across the whole codebase via `cleanup-auditor`, already always-on in `team-review`. One fix: `team-review.md:231` currently maps the dead-code dimension to `general-purpose`, contradicting `:106`. It is corrected to `senior-review:cleanup-auditor`.

### Reference fan-out

Every pointer to the deleted command is rewritten to `/senior-review:code-review --fix`, naming the relevant cleanup phase where the original named one.

| File | Lines |
|---|---|
| `plugins/abstraction-architect/skills/abstraction-architect/SKILL.md` | 6, 33 |
| `plugins/codebase-cleanup/commands/deps-audit.md` | 5 |
| `plugins/codebase-cleanup/commands/refactor-clean.md` | 5 |
| `plugins/codebase-cleanup/commands/tech-debt.md` | 5 |
| `plugins/python-development/commands/python-audit.md` | 5, 130 |
| `plugins/python-development/commands/python-refactor.md` | 5 |
| `plugins/senior-review/agents/cleanup-auditor.md` | 6, 14, 23, 154, 218, 252 |
| `docs/plugins/codebase-cleanup.md` | 44, 81, 115 |
| `docs/plugins/python-development.md` | 306 |
| `docs/plugins/senior-review.md` | 177, 195, 295, 300 |
| `docs/plugins/system-utils.md` | 45 |
| `docs/plugins/typescript-development.md` | 74 |
| `.claude-plugin/marketplace.json` | 610 (description text), 663 (command path) |

`cleanup-auditor.md:23` and `:218` are the load-bearing ones: they define the closing line of every finding. They become a reference to the `code-review --fix` cleanup phase, which converges with what the VS Code export already emits.

## Part C: versions, documentation, exports

### Versions

| Plugin | From | To | Reason |
|---|---|---|---|
| `senior-review` | 6.1.2 | 7.0.0 | an agent and a command leave the public namespace |
| `codebase-xray` | 2.0.1 | 2.1.0 | gains an agent |
| `codebase-mapper` | 2.10.2 | 2.11.0 | references rewritten, dependencies restated |
| `abstraction-architect` | 1.1.5 | 1.1.6 | pointer rewrite |
| `codebase-cleanup` | 1.0.1 | 1.0.2 | pointer rewrite |
| `python-development` | 1.21.4 | 1.21.5 | pointer rewrite |
| marketplace | 15.0.0 | 16.0.0 | breaking namespace change |

### CLAUDE.md

Four edits:

1. The downstream-exports source map row for the mapper changes its source path from `senior-review/agents/` to `codebase-xray/agents/`.
2. The paragraph documenting the `codebase-xray` optional-dependency exception, with its instruction not to promote it on a future pass, is removed. The exception no longer exists.
3. The 13.2.0 paragraph's dependency statements for `senior-review` and `codebase-mapper` are restated to match the new tables.
4. A migration note records both removals: `senior-review:semantic-interconnect-mapper` becomes `codebase-xray:semantic-interconnect-mapper`, and `/senior-review:cleanup-dead-code` becomes `/senior-review:code-review --fix`. Same shape as the old-to-new mapping kept for the `codebase-xray` rename.

### README.md

The Mermaid dependency graph needs four edits: drop `deepdive -.-> seniorreview`; replace `codebasemapper --> seniorreview` with `codebasemapper --> deepdive` plus a dotted `codebasemapper -.-> seniorreview`; convert the five `seniorreview -->` edges for `abstraction`, `reactdev`, `platformeng`, `pythondev`, `tsdev` to dotted. The paragraph at `:177` describing the deliberate near-cycle is rewritten, since the hard graph is now acyclic without a compromise.

### Exports

No content change. The export already treats the mapper as an xray asset, and `review-cleanup-auditor` already closes findings with `Fix phase: <phase>` instead of invoking the command. Two entries in `exports/vscode/README.md` shift from being divergences to being alignments: the interconnect-map row at `:192` and the cleanup fix-command row at `:207`. The export's own `metadata.version` inside `skills/codebase-xray/SKILL.md` does not need a bump, since no exported content changes.

## Out of scope

Deliberately unchanged, to keep the change reviewable:

- `defect-taxonomy` stays in `senior-review`. It is a review taxonomy with CWE and OWASP mappings, and `codebase-mapper` touches one reference file through an optional load.
- `review-quality-gates` stays in `senior-review`. Only `code-review` and `team-review` consume it.
- The xray partition workers and `partition-synthesizer` stay where they are.
- `cleanup-auditor` stays in `senior-review` as a detection-only agent.
- `agent-teams` stays a hard dependency everywhere. Demoting it across the four pipeline plugins is a separate decision.
- `research` keeps its self-contained declarations. Nothing here touches it.

## Verification

Before committing:

1. No namespaced reference to `senior-review:semantic-interconnect-mapper` remains anywhere in `plugins/`, `docs/`, `README.md`, or `marketplace.json`.
2. No reference to `cleanup-dead-code` remains outside `exports/vscode/README.md`, where it names the original on purpose, and the CLAUDE.md migration note.
3. `marketplace.json` parses as JSON, every path listed for each plugin exists on disk, and no plugin lists the deleted command or the moved agent under its old owner.
4. The hard-dependency graph is acyclic, verified by walking `dependencies` only.
5. `team-review.md` no longer contains a dimension-to-agent row resolving dead code to `general-purpose`.
6. No dash-aside construct introduced in any edited file, per the repository convention.
