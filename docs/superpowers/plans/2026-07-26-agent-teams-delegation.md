# Agent-Teams Upstream Delegation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `plugins/agent-teams/`, delegate its generic core to the upstream `wshobson/agents` plugin, and relocate the four locally authored pipelines (`team-review`, `team-deep-dive`, `team-codebase-map`, `team-research`) into their host plugins without capability loss.

**Architecture:** Pure markdown/JSON restructuring in a plugin marketplace repo. Four command files move to host plugins and gain hard-prerequisite blocks on the upstream plugin; local-only quality-gate content moves into a new `senior-review:review-quality-gates` skill; ~40 dependent files get namespace rewires; marketplace.json loses the agent-teams entry and goes to 9.0.0.

**Tech Stack:** Markdown, JSON, one JS hook handler (`team-spawn-gate.js`), `gh api` for upstream fetches, PowerShell/Git Bash.

**Spec:** `docs/superpowers/specs/2026-07-26-agent-teams-delegation-design.md`

## Global Constraints

- Work happens on branch `agent-teams-delegation` (created from master at 8c83f14). Each task ends with a commit on that branch (`wip(agent-teams-delegation): task N <short summary>`). Task 14 squash-merges the branch into master as ONE commit (the v9.0.0 commit) and pushes: master receives plugin content and marketplace.json together, satisfying the CLAUDE.md marketplace workflow.
- No dash-aside constructs in any authored text (no `X — Y — Z`, `X -- Y -- Z`, or spaced-hyphen asides). Rewrite as sentences, parentheses, or colons.
- Command filenames never change; only their directory (and therefore namespace) changes.
- Artifact paths never change: `.team-review/`, `.deep-dive/`, `.codebase-map/`.
- Bare (namespace-less) mentions of `/team-review` in prose stay untouched.
- The `agent-teams:` skill/agent namespace stays valid in references that are meant to resolve via the installed upstream plugin. Only the four pipeline command namespaces are rewritten.
- No tests or CI exist. Verification is greps, `python -m json.tool` on marketplace.json, and `node --check` on the gate handler.
- Repo root: `D:\Projects\alfio-claude-plugins`. All paths below are relative to it.

---

### Task 1: Fetch upstream reference material

**Files:**
- Create: `.upstream-scratch/wshobson-agent-teams/skills/multi-reviewer-patterns/SKILL.md`
- Create: `.upstream-scratch/wshobson-agent-teams/commands.txt`

**Interfaces:**
- Produces: the upstream skill body used by Task 2's diff, and the upstream command list used for sanity checks. `.upstream-scratch/` is never committed.

- [ ] **Step 1: Fetch the upstream multi-reviewer-patterns skill**

```bash
mkdir -p .upstream-scratch/wshobson-agent-teams/skills/multi-reviewer-patterns
gh api "repos/wshobson/agents/contents/plugins/agent-teams/skills/multi-reviewer-patterns/SKILL.md" --jq '.content' | base64 -d > .upstream-scratch/wshobson-agent-teams/skills/multi-reviewer-patterns/SKILL.md
```

- [ ] **Step 2: Fetch the upstream command list**

```bash
gh api "repos/wshobson/agents/contents/plugins/agent-teams/commands" --jq '.[].name' > .upstream-scratch/wshobson-agent-teams/commands.txt
cat .upstream-scratch/wshobson-agent-teams/commands.txt
```

Expected: exactly `team-debug.md team-delegate.md team-feature.md team-review.md team-shutdown.md team-spawn.md team-status.md` (7 files, one per line). If `team-research.md`, `team-codebase-map.md`, or `team-deep-dive.md` appear, STOP: upstream has changed since the design and the relocation plan must be revisited.

- [ ] **Step 3: Confirm the upstream skill lacks the local-only sections**

```bash
grep -c "Adversarial Verification Panel\|Completeness Critic\|Context Sharing Pattern" .upstream-scratch/wshobson-agent-teams/skills/multi-reviewer-patterns/SKILL.md || echo "0 as expected"
```

Expected: `0 as expected`. If any section exists upstream, exclude that section from Task 2's extraction.

---

### Task 2: Create `senior-review:review-quality-gates` skill

**Files:**
- Create: `plugins/senior-review/skills/review-quality-gates/SKILL.md`
- Read: `plugins/agent-teams/skills/multi-reviewer-patterns/SKILL.md` (source of moved content)
- Read: `.upstream-scratch/wshobson-agent-teams/skills/multi-reviewer-patterns/SKILL.md` (diff baseline)

**Interfaces:**
- Produces: skill `senior-review:review-quality-gates` with body sections titled exactly `## Adversarial Verification Panel`, `## Completeness Critic`, `## Context Sharing Pattern`, and `## Deduplication and Severity Calibration`. Tasks 3 and 8 reference these exact titles.

- [ ] **Step 1: Diff local against upstream to isolate local-only content**

Read both SKILL.md files fully. Identify every section present locally but absent upstream. Known local-only sections (verified 2026-07-26): `Adversarial Verification Panel`, `Completeness Critic`, `Context Sharing Pattern`, plus any local dedup/severity-calibration rules that upstream's version does not carry. Content that exists in both stays out of the new skill (upstream provides it).

- [ ] **Step 2: Write the new SKILL.md**

Create `plugins/senior-review/skills/review-quality-gates/SKILL.md`. Frontmatter (exact):

```yaml
---
name: review-quality-gates
description: >
  Quality gates for multi-reviewer code review pipelines: adversarial verification
  panel, completeness critic, finding deduplication and severity calibration, and
  the context sharing pattern for parallel reviewers.
  TRIGGER WHEN: running /senior-review:team-review quality gates; running
  /senior-review:code-review Steps 4b/4c (adversarial verification and completeness
  check); consolidating or deduplicating findings from multiple parallel reviewers.
  DO NOT TRIGGER WHEN: single-reviewer style review without a consolidation phase,
  or generic team coordination (the upstream agent-teams skills cover that).
---
```

Body: the local-only sections identified in Step 1, moved verbatim (headings normalized to `## Adversarial Verification Panel`, `## Completeness Critic`, `## Context Sharing Pattern`, `## Deduplication and Severity Calibration`). Scan the moved text for dash-asides inherited from local edits and rewrite any found. Do not add new prose beyond a one-line intro sentence under the H1: `# Review Quality Gates` followed by `Gates and consolidation rules shared by /senior-review:team-review and /senior-review:code-review.`

- [ ] **Step 3: Verify the sections landed**

```bash
grep -c "^## " plugins/senior-review/skills/review-quality-gates/SKILL.md
grep "Adversarial Verification Panel" plugins/senior-review/skills/review-quality-gates/SKILL.md
```

Expected: at least 4 H2 sections; the panel heading present.

---

### Task 3: Relocate `team-review` into senior-review

**Files:**
- Move: `plugins/agent-teams/commands/team-review.md` -> `plugins/senior-review/commands/team-review.md`
- Modify: `plugins/senior-review/commands/team-review.md` (after move)
- Modify: `plugins/senior-review/commands/code-review.md` (lines ~839, ~841, ~867)

**Interfaces:**
- Consumes: skill `senior-review:review-quality-gates` (Task 2) with its four exact section titles.
- Produces: command `/senior-review:team-review`. All later tasks rewire references to this exact namespace.

- [ ] **Step 1: Move the file**

```bash
git mv plugins/agent-teams/commands/team-review.md plugins/senior-review/commands/team-review.md
```

- [ ] **Step 2: Insert the Prerequisites block**

Immediately after the frontmatter of `plugins/senior-review/commands/team-review.md`, insert:

```markdown
## Prerequisites

This command requires the upstream `agent-teams` plugin from `wshobson/agents` (MIT, Seth Hobson). It provides the `agent-teams:multi-reviewer-patterns` and `agent-teams:team-communication-protocols` skills and the `agent-teams:team-reviewer` fallback agent used below. Install it first:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

The team tools themselves (TeamCreate, TaskCreate, TeamDelete) are native Claude Code features and need no plugin.
```

- [ ] **Step 3: Repoint the quality-gate references inside team-review.md**

In the moved file, the references at former lines 22, 296, 308, 322 name `agent-teams:multi-reviewer-patterns` for dedup rules, the Adversarial Verification Panel, and the Completeness Critic. Change each reference that targets a section moved in Task 2 to `senior-review:review-quality-gates` (same section titles). References to generic multi-reviewer guidance that stayed upstream keep `agent-teams:multi-reviewer-patterns`. The `team-communication-protocols` reference (former line 24) keeps its `agent-teams:` namespace.

- [ ] **Step 4: Fix self-references and frontmatter**

In the moved file, replace every occurrence of `/agent-teams:team-review` with `/senior-review:team-review`, and any `/agent-teams:team-deep-dive` mention with `/deep-dive-analysis:team-deep-dive`. Check the frontmatter description for `agent-teams` wording and update the namespace if present.

- [ ] **Step 5: Repoint code-review.md Steps 4b/4c**

In `plugins/senior-review/commands/code-review.md`: at ~L839 and ~L867, change `agent-teams:multi-reviewer-patterns` to `senior-review:review-quality-gates` (section names `## Adversarial Verification Panel` and `## Completeness Critic` stay). At ~L841 and ~L867 the graceful-degradation fallbacks currently keyed on "if `agent-teams` is not installed": rekey them to "if the skill is unavailable" so they guard the local skill. At ~L5 the DO-NOT-TRIGGER note pointing at `/agent-teams:team-review` becomes `/senior-review:team-review`.

- [ ] **Step 6: Verify**

```bash
grep -n "agent-teams" plugins/senior-review/commands/team-review.md
grep -n "agent-teams" plugins/senior-review/commands/code-review.md
```

Expected: in team-review.md only the Prerequisites block and intentional `agent-teams:*` upstream skill/agent references remain; zero `/agent-teams:` command references. In code-review.md zero occurrences of `agent-teams:multi-reviewer-patterns` and zero `/agent-teams:` references.

---

### Task 4: Relocate `team-deep-dive` into deep-dive-analysis

**Files:**
- Move: `plugins/agent-teams/commands/team-deep-dive.md` -> `plugins/deep-dive-analysis/commands/team-deep-dive.md`
- Modify: `plugins/deep-dive-analysis/commands/team-deep-dive.md` (after move)
- Modify: `plugins/deep-dive-analysis/agents/partition-structure-worker.md`
- Modify: `plugins/deep-dive-analysis/agents/partition-behavior-worker.md`
- Modify: `plugins/deep-dive-analysis/agents/partition-quality-worker.md`
- Modify: `plugins/deep-dive-analysis/agents/deep-dive-synthesizer.md`
- Modify: `plugins/deep-dive-analysis/skills/deep-dive-analysis/SKILL.md` (~L354, ~L360)

**Interfaces:**
- Produces: command `/deep-dive-analysis:team-deep-dive`. Task 8 rewires abstraction-architect references to it.

- [ ] **Step 1: Move the file**

```bash
git mv plugins/agent-teams/commands/team-deep-dive.md plugins/deep-dive-analysis/commands/team-deep-dive.md
```

Note: if `plugins/deep-dive-analysis/commands/` does not exist yet, create it first; the plugin currently registers its command from the skills-based layout, so also confirm in Task 13 how the marketplace entry lists commands.

- [ ] **Step 2: Insert the Prerequisites block**

Immediately after the frontmatter, insert:

```markdown
## Prerequisites

This command requires the upstream `agent-teams` plugin from `wshobson/agents` (MIT, Seth Hobson). It provides the `agent-teams:task-coordination-strategies`, `agent-teams:team-communication-protocols`, and `agent-teams:parallel-feature-development` skills used below. Install it first:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

The team tools themselves (TeamDelete, TaskList, TaskUpdate) are native Claude Code features and need no plugin.
```

- [ ] **Step 3: Fix self-references**

In the moved file, replace every `/agent-teams:team-deep-dive` with `/deep-dive-analysis:team-deep-dive` and every `/agent-teams:team-review` with `/senior-review:team-review` (the Phase 4 menu has one). Skill references keep the `agent-teams:` namespace.

- [ ] **Step 4: Update the four worker agents**

In each of `partition-structure-worker.md`, `partition-behavior-worker.md`, `partition-quality-worker.md`, `deep-dive-synthesizer.md`: replace every `/agent-teams:team-deep-dive` with `/deep-dive-analysis:team-deep-dive` (frontmatter description and body).

- [ ] **Step 5: Update the deep-dive SKILL.md**

In `plugins/deep-dive-analysis/skills/deep-dive-analysis/SKILL.md`: ~L354 `/agent-teams:team-deep-dive <target>` becomes `/deep-dive-analysis:team-deep-dive <target>`; ~L360 `/agent-teams:team-review` becomes `/senior-review:team-review`.

- [ ] **Step 6: Verify**

```bash
grep -rn "/agent-teams:team-deep-dive" plugins/deep-dive-analysis/
```

Expected: zero matches.

---

### Task 5: Relocate `team-codebase-map` into codebase-mapper

**Files:**
- Move: `plugins/agent-teams/commands/team-codebase-map.md` -> `plugins/codebase-mapper/commands/team-codebase-map.md`
- Modify: `plugins/codebase-mapper/commands/team-codebase-map.md` (after move)

**Interfaces:**
- Produces: command `/codebase-mapper:team-codebase-map`. Task 9 points acp-loader at it.

- [ ] **Step 1: Move the file**

```bash
git mv plugins/agent-teams/commands/team-codebase-map.md plugins/codebase-mapper/commands/team-codebase-map.md
```

- [ ] **Step 2: Insert the Prerequisites block**

Immediately after the frontmatter, insert:

```markdown
## Prerequisites

This command requires the upstream `agent-teams` plugin from `wshobson/agents` (MIT, Seth Hobson). It provides the `agent-teams:task-coordination-strategies` and `agent-teams:team-communication-protocols` skills used below. Install it first:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

The team tools themselves (TeamCreate, TeamDelete, TaskList) are native Claude Code features and need no plugin.
```

- [ ] **Step 3: Fix self-references and verify**

Replace any `/agent-teams:team-codebase-map` occurrences in the moved file with `/codebase-mapper:team-codebase-map`; skill references keep `agent-teams:`. Then:

```bash
grep -rn "/agent-teams:" plugins/codebase-mapper/
```

Expected: zero matches.

---

### Task 6: Relocate `team-research` into research

**Files:**
- Move: `plugins/agent-teams/commands/team-research.md` -> `plugins/research/commands/team-research.md`
- Modify: `plugins/research/commands/team-research.md` (after move)

**Interfaces:**
- Produces: command `/research:team-research`. Tasks 9 and 10 route deep-search phrases to it.

- [ ] **Step 1: Move the file**

```bash
git mv plugins/agent-teams/commands/team-research.md plugins/research/commands/team-research.md
```

If `plugins/research/commands/` does not exist, create it.

- [ ] **Step 2: Insert the Prerequisites block**

Immediately after the frontmatter, insert:

```markdown
## Prerequisites

This command requires the upstream `agent-teams` plugin from `wshobson/agents` (MIT, Seth Hobson). It provides the `agent-teams:team-composition-patterns` and `agent-teams:team-communication-protocols` skills used below. Install it first:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

The team tools themselves (TeamCreate, TaskCreate, TeamDelete, TaskList) are native Claude Code features and need no plugin.
```

- [ ] **Step 3: Fix self-references and verify**

Replace any `/agent-teams:team-research` occurrences in the moved file with `/research:team-research`; skill references keep `agent-teams:`. Then:

```bash
grep -rn "/agent-teams:" plugins/research/
```

Expected: zero matches.

---

### Task 7: Delete the agent-teams plugin and its docs

**Files:**
- Delete: `plugins/agent-teams/` (everything remaining: 6 commands, 4 agents, 6 skills)
- Delete: `docs/plugins/agent-teams.md`
- Modify: `.claude-plugin/marketplace.json` (remove the agent-teams entry, ~L1355-1405)

**Interfaces:**
- Consumes: Tasks 3-6 must be complete (the four pipeline files already moved out).
- Produces: a marketplace.json without an `agent-teams` plugin entry. `buildAgentCatalog()` in the gate handler auto-adjusts.

- [ ] **Step 1: Confirm the four pipelines are out**

```bash
ls plugins/agent-teams/commands/
```

Expected: exactly `team-debug.md team-delegate.md team-feature.md team-shutdown.md team-spawn.md team-status.md` (6 files; `team-review.md`, `team-deep-dive.md`, `team-codebase-map.md`, `team-research.md` gone). STOP if any pipeline file is still present.

- [ ] **Step 2: Delete plugin and doc**

```bash
git rm -r plugins/agent-teams
git rm docs/plugins/agent-teams.md
```

- [ ] **Step 3: Remove the marketplace entry**

In `.claude-plugin/marketplace.json`, delete the entire object in `plugins[]` whose `"name"` is `"agent-teams"` (starts ~L1355, currently v3.2.0; includes its `dependencies: ["superpowers"]` and `optionalDependencies: ["abstraction-architect"]`). The superpowers hard dependency survives on the `ai-tooling` entry only. Mind the comma of the preceding/following entry.

- [ ] **Step 4: Verify JSON**

```bash
python -m json.tool .claude-plugin/marketplace.json > /dev/null && echo OK
grep -c '"name": "agent-teams"' .claude-plugin/marketplace.json || echo "0 as expected"
```

Expected: `OK` then `0 as expected`.

---

### Task 8: Namespace rewires in reviewer agents and abstraction-architect

**Files:**
- Modify: `plugins/senior-review/agents/code-auditor.md` (~L258, ~L266)
- Modify: `plugins/senior-review/agents/security-auditor.md` (~L158, ~L166, ~L170)
- Modify: `plugins/senior-review/agents/logic-integrity-auditor.md` (~L5, L14-L217 block refs)
- Modify: `plugins/senior-review/agents/cleanup-auditor.md` (~L4, ~L281, ~L289, ~L293)
- Modify: `plugins/senior-review/agents/distributed-flow-auditor.md` (~L288, ~L296, ~L300)
- Modify: `plugins/senior-review/agents/ui-race-auditor.md` (~L231, ~L239, ~L243)
- Modify: `plugins/senior-review/agents/chicken-egg-detector.md` (~L271, ~L279, ~L283)
- Modify: `plugins/senior-review/commands/full-review.md` (~L3, L5, L11, L13)
- Modify: `plugins/senior-review/commands/cleanup-dead-code.md` (~L5)
- Modify: `plugins/platform-engineering/agents/platform-reviewer.md` (~L148, ~L156, ~L160)
- Modify: `plugins/react-development/agents/react-performance-optimizer.md` (~L682, ~L690, ~L694)
- Modify: `plugins/abstraction-architect/agents/abstraction-architect.md` (~L5, ~L41)
- Modify: `plugins/abstraction-architect/commands/audit.md` (~L63, L68-L69)
- Modify: `.claude-plugin/marketplace.json` (abstraction-architect `description`, ~L1522)

**Interfaces:**
- Consumes: `/senior-review:team-review` (Task 3), `/deep-dive-analysis:team-deep-dive` (Task 4).

- [ ] **Step 1: Blanket rewrite of the two pipeline namespaces**

In every file listed above, apply:
- `/agent-teams:team-review` -> `/senior-review:team-review`
- `agent-teams:team-review` (namespaced without slash, if present) -> `senior-review:team-review`
- `/agent-teams:team-deep-dive` -> `/deep-dive-analysis:team-deep-dive`
- `agent-teams:team-deep-dive` -> `deep-dive-analysis:team-deep-dive`

Bare `/team-review` mentions (no namespace) stay untouched. `.team-review/` paths stay untouched.

- [ ] **Step 2: Update the marketplace description of abstraction-architect**

In `.claude-plugin/marketplace.json` at the abstraction-architect entry (~L1519-1556), its `description` says the diff mode "runs as the Abstraction dimension of /agent-teams:team-review and /senior-review:code-review". Change to "/senior-review:team-review and /senior-review:code-review".

- [ ] **Step 3: Verify**

```bash
grep -rnE "agent-teams:team-review($|[^e])|agent-teams:team-deep-dive" plugins/ .claude-plugin/
```

Expected: zero matches. (The pattern excludes `agent-teams:team-reviewer`, the upstream fallback agent that `plugins/senior-review/commands/team-review.md` intentionally references.)

---

### Task 9: Rewrite acp-loader routing

**Files:**
- Modify: `plugins/ai-tooling/skills/acp-loader/SKILL.md` (~L70 decision tree, L118-L125 Workflow Awareness table)

**Interfaces:**
- Consumes: the four new pipeline namespaces (Tasks 3-6).

- [ ] **Step 1: Decision tree (~L70)**

The entry `Is this Tauri/Rust work? --> Check: tauri-development skills, agent-teams:team-spawn tauri` loses the team-spawn preset: it becomes `--> Check: tauri-development skills`.

- [ ] **Step 2: Workflow Awareness table (L118-L125)**

Replace the current table with:

```markdown
| Task | Command |
|------|---------|
| Build a new feature end-to-end | `/agent-teams:team-feature` (requires the upstream wshobson/agents agent-teams plugin) |
| Full codebase review (deep-dive + review) | `/senior-review:team-review` |
| Debug with competing hypotheses | `/agent-teams:team-debug` (requires the upstream wshobson/agents agent-teams plugin) |
| Deep multi-source research | `/research:team-research` |
| Map an unfamiliar codebase | `/codebase-mapper:team-codebase-map` |
| Deep-dive a monorepo or partitioned codebase | `/deep-dive-analysis:team-deep-dive` |
```

Rows for `team-spawn fullstack`, `team-spawn app-analysis`, `team-spawn tauri` are removed. Keep the sentence after the table ("If the user's request matches a team scope, suggest the team command...") unchanged.

- [ ] **Step 3: Sweep the rest of the file**

```bash
grep -n "agent-teams" plugins/ai-tooling/skills/acp-loader/SKILL.md
```

Expected survivors: only the two table rows marked "requires the upstream" plus, if present, the Skill Priority mention of superpowers (which does not involve agent-teams). Any other `/agent-teams:` occurrence (examples list, priority examples) gets the same treatment: pipeline namespaces rewritten, dead presets removed.

---

### Task 10: Rewrite the team-spawn gate handler

**Files:**
- Modify: `plugins/acp-hooks/hooks/handlers/team-spawn-gate.js` (command strings at ~L38, 53, 66, 80, 94, 107, 120, 132, 145, 158, 171)
- Modify: `.claude-plugin/marketplace.json` (acp-hooks `optionalDependencies`, ~L827-831)

**Interfaces:**
- Consumes: `/senior-review:team-review` (Task 3), `/research:team-research` (Task 6).
- Produces: a gate that only auto-suggests commands that exist locally or upstream.

- [ ] **Step 1: Remap the 11 preset command strings**

Read the handler first, then apply this mapping to the `command:` fields:

| Preset entry | New command |
|---|---|
| review | `/senior-review:team-review` |
| security | `/agent-teams:team-spawn security` (upstream, keep) |
| fullstack | `/agent-teams:team-spawn fullstack` (upstream, keep) |
| research | `/research:team-research` |
| deep-search (currently `/agent-teams:team-research`) | `/research:team-research` |
| migration | `/agent-teams:team-spawn migration` (upstream, keep) |
| docs | remove the whole preset entry (phrases included) |
| app-analysis | remove the whole preset entry |
| tauri | remove the whole preset entry |
| debug (`/agent-teams:team-debug`) | keep |
| feature (`/agent-teams:team-feature`) | keep |

If `research` and `deep-search` collapse to the same command, merge their phrase lists into one entry rather than keeping two entries with the same target.

- [ ] **Step 2: Soften the injection text for upstream commands**

For the entries that keep `/agent-teams:*`, the injected instruction currently says to launch the command without asking for confirmation. Add one sentence to the injected text for those entries only: `If the agent-teams plugin (wshobson/agents) is not installed, tell the user to install it (/plugin marketplace add wshobson/agents, /plugin install agent-teams@claude-code-workflows) instead of running the command.` Local-namespace entries keep the current text.

- [ ] **Step 3: Leave the catalog logic alone**

`buildAgentCatalog()` reads marketplace.json at runtime and self-updates. `STATIC_FALLBACK_CATALOG` (~L307-310) keeps its 4 `agent-teams:team-*` agent ids (valid when upstream is installed).

- [ ] **Step 4: Remove the optional dependency**

In `.claude-plugin/marketplace.json`, acp-hooks entry (~L798): remove `"agent-teams"` from `optionalDependencies`, keeping `ai-tooling` and `senior-review`.

- [ ] **Step 5: Verify**

```bash
node --check plugins/acp-hooks/hooks/handlers/team-spawn-gate.js && echo SYNTAX-OK
grep -n "team-research\|team-spawn docs\|app-analysis\|tauri" plugins/acp-hooks/hooks/handlers/team-spawn-gate.js
python -m json.tool .claude-plugin/marketplace.json > /dev/null && echo JSON-OK
```

Expected: `SYNTAX-OK`; no `/agent-teams:team-research` and no docs/app-analysis/tauri preset entries; `JSON-OK`.

---

### Task 11: Update READMEs, per-plugin docs, and libgdx

**Files:**
- Modify: `README.md` (~L45, L96, L146, L157)
- Modify: `docs/README.md` (~L13, L58, L82, L88)
- Modify: `docs/plugins/acp-hooks.md` (~L24, L26, L58, L60)
- Modify: `docs/plugins/clean-code.md` (~L60)
- Modify: `docs/plugins/ai-tooling.md` (~L79)
- Modify: `docs/plugins/git-worktrees.md` (~L80)
- Modify: `docs/plugins/app-analyzer.md` (~L43)
- Modify: `docs/plugins/platform-engineering.md` (~L76)
- Modify: `docs/plugins/python-development.md` (~L306)
- Modify: `docs/plugins/react-development.md` (~L94)
- Modify: `docs/plugins/tauri-development.md` (~L118)
- Modify: `docs/plugins/senior-review.md` (~L123, L127, L141, L145, L183, L189, L286)
- Modify: `plugins/libgdx-development/agents/libgdx-architect.md` (~L276)

**Interfaces:**
- Consumes: all four new pipeline namespaces.

- [ ] **Step 1: README.md**

- ~L45 and ~L157: replace the `/agent-teams:team-feature` example with `/senior-review:team-review` (adjust surrounding prose so the example still reads naturally, e.g. "run a full multi-reviewer code review").
- ~L96: delete the agent-teams plugin table row.
- ~L146: the sentence "Everything downstream of the plan stays here: agent-teams for parallel implementation..." now names the upstream provider: rewrite to state that parallel implementation and generic team workflows are delegated to the upstream wshobson/agents agent-teams plugin, while the review, deep-dive, codebase-map, and research pipelines live in senior-review, deep-dive-analysis, codebase-mapper, and research.
- Extend the delegated-upstream section (the one that covers the removed frontend plugin and superpowers) with a new entry: agent-teams generic core delegated to `wshobson/agents` in marketplace 9.0.0, including the two install commands, and noting the four pipelines were relocated (list old -> new namespaces).

- [ ] **Step 2: docs/README.md**

- ~L13: delete the agent-teams index row.
- ~L58: replace the quickstart example `/agent-teams:team-feature "add user authentication"` with `/senior-review:team-review`.
- ~L82: "See the agent-teams plugin for multi-agent pipeline commands" becomes a pointer to the four relocated pipeline commands and the upstream plugin for generic team work.
- ~L88: the sentence naming `references/agent-teams-best-practices.md` keeps the filename but its list of affected plugins becomes "senior-review, codebase-mapper, research, deep-dive-analysis (the team pipelines)".

- [ ] **Step 3: Per-plugin docs**

- `acp-hooks.md`: handler table row and bypass notes stay (the gate still exists); update its description to say it suggests local pipeline commands plus upstream agent-teams commands; ~L60 optional-dep line drops agent-teams.
- `clean-code.md` ~L60, `python-development.md` ~L306: `/team-feature` mentions become "the upstream agent-teams `/agent-teams:team-feature` (wshobson/agents)".
- `ai-tooling.md` ~L79 Related row: "agent-teams (multi-agent orchestration)" becomes "upstream wshobson/agents agent-teams (generic team orchestration); local team pipelines live in senior-review, deep-dive-analysis, codebase-mapper, research".
- `git-worktrees.md` ~L80: reword to reference the relocated pipelines or the upstream plugin, whichever the sentence targets.
- `app-analyzer.md` ~L43: the `/team-spawn app-analysis` mention is a dead preset: delete the sentence (the plugin's own agents are the direct route).
- `platform-engineering.md` ~L76 and `react-development.md` ~L94: preset mentions become `/senior-review:team-review` (both agents are review dimensions of that pipeline).
- `tauri-development.md` ~L118: the `/team-spawn tauri` orchestration note is a dead preset: delete or rewrite to say the tauri agents are invoked directly.
- `senior-review.md`: `/team-review` phase capability statements move to `/senior-review:team-review` where namespaced; bare `/team-review` prose stays; ~L286 Related footer updated.

- [ ] **Step 4: libgdx-architect ~L276**

The Ecosystem Integration bullet recommending `agent-teams:team-feature` becomes: `For parallel Screen/ECS/asset implementation across multiple agents, the upstream agent-teams plugin (wshobson/agents) provides /agent-teams:team-feature.`

- [ ] **Step 5: Verify**

```bash
grep -rn "team-spawn app-analysis\|team-spawn tauri\|team-spawn docs" README.md docs/ plugins/
grep -rn "/agent-teams:" README.md docs/
```

Expected: first grep zero matches; second grep only survivors that explicitly carry the upstream provenance (team-feature/team-debug/team-spawn generic mentions and the install commands).

---

### Task 12: CLAUDE.md, best-practices reference, and memory

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/references/agent-teams-best-practices.md` (~L3-L5, L127, L157, L197-L198)
- Modify: `C:\Users\alfio\.claude\projects\D--Projects-alfio-claude-plugins\memory\vendoring-to-refs-shelved.md`
- Modify: `C:\Users\alfio\.claude\projects\D--Projects-alfio-claude-plugins\memory\MEMORY.md`

**Interfaces:**
- Consumes: final state of all prior tasks (the text below documents it).

- [ ] **Step 1: CLAUDE.md plugin list and count**

The "44 plugins:" sentence becomes "43 plugins:" and `agent-teams` is removed from the list.

- [ ] **Step 2: CLAUDE.md sync table and sync notes**

- Delete the `agent-teams` row from the upstream-synced table. Keep the `senior-review (semantic-interconnect-mapper)` row: it syncs from a different upstream file and is unaffected.
- In "Non-obvious per-plugin sync notes", delete the `agent-teams` bullet (stale tool-name greps) and the `wshobson/agents (agent-teams / reverse-engineering / codebase-cleanup)` bullet's agent-teams mention (keep reverse-engineering and codebase-cleanup).
- In the numbered "Default upstream-update strategy", remove agent-teams-specific examples where they name the plugin (step 6 stale-tool-names note keeps its generic value: reword to reference "team-related imports" or scope it to remaining wshobson syncs).
- The intro line of `docs/plugins/` section naming agent-teams-best-practices.md as source of truth "when restructuring any plugin that spawns multi-agent teams or pipeline reviewers (`agent-teams`, `senior-review`, `codebase-mapper`, `research`)" becomes "(`senior-review`, `codebase-mapper`, `research`, `deep-dive-analysis`)".
- The "Slow" freshness-class row: "agent-teams workflows" becomes "team pipeline workflows (senior-review, deep-dive-analysis, codebase-mapper, research)".

- [ ] **Step 3: CLAUDE.md "Deliberately not vendored" row and hard-dependency paragraph**

Add to the "Deliberately not vendored" table:

```markdown
| Multi-agent generic core (`agent-teams` plugin: 6 commands, 4 agents, 6 skills) | `wshobson/agents` | marketplace 9.0.0 |
```

Update the paragraph after that table (the one describing the superpowers hard-dependency policy adopted in marketplace 8.2.0; it currently ends "do not reintroduce conditional phrasing."):

- Its list of places that load the superpowers skills loses `agent-teams:team-lead` (Planning Phase) and `/agent-teams:team-feature` (Skills to Load): both files are deleted by this change. Only `acp-loader` (Skill Priority) remains.
- "a declared hard dependency (`dependencies: ["superpowers"]` in `marketplace.json`) of `ai-tooling` and `agent-teams`" becomes "of `ai-tooling`".
- Append this text to the paragraph (or as a following paragraph):

```markdown
The same policy applies to the team pipelines: `/senior-review:team-review`, `/deep-dive-analysis:team-deep-dive`, `/codebase-mapper:team-codebase-map`, and `/research:team-research` declare the upstream `agent-teams` plugin (wshobson/agents) as a hard prerequisite in their Prerequisites blocks. The upstream plugin keeps the same `agent-teams:*` namespace, so those references resolve as written once it is installed (`/plugin marketplace add wshobson/agents`, then `/plugin install agent-teams@claude-code-workflows`). The four pipelines and the `senior-review:review-quality-gates` skill are local content with no upstream sync.
```

- [ ] **Step 4: agent-teams-best-practices.md**

- ~L3-L5 scope statement: the file no longer describes a local plugin; reword to "the team pipelines in this marketplace (senior-review, deep-dive-analysis, codebase-mapper, research) and the upstream wshobson/agents agent-teams plugin they build on".
- ~L127: `agent-teams:multi-reviewer-patterns` as home of the quality gates becomes `senior-review:review-quality-gates`, and "/agent-teams:team-review" becomes "/senior-review:team-review".
- ~L157: `/team-review`-style advice stays (bare reference).
- ~L197-L198 "Where this applies": `plugins/agent-teams/` becomes the four pipeline homes; the senior-review line stays.

- [ ] **Step 5: Memory update**

In `vendoring-to-refs-shelved.md`: update the `description` frontmatter line and body to record that on 2026-07-26 the delegation was applied to agent-teams (generic core delegated to wshobson/agents, four pipelines relocated to senior-review, deep-dive-analysis, codebase-mapper, research; marketplace 9.0.0); the shelved status now covers only the remaining synced plugins. Keep the 2026-07-12 feasibility findings intact. Update the matching hook line in `MEMORY.md`.

- [ ] **Step 6: Verify**

```bash
grep -n "agent-teams" CLAUDE.md
```

Expected survivors only: the "Deliberately not vendored" row, the rule-amendment paragraph, the best-practices filename mentions, and remaining wshobson sync rows for reverse-engineering/codebase-cleanup that never named agent-teams.

---

### Task 13: Marketplace version bumps and command registration

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: all content changes final.

- [ ] **Step 1: Register the moved commands and new skill**

Mirror each entry's existing style (some list explicit file paths, some list directories):
- senior-review entry: add `./plugins/senior-review/commands/team-review.md` to its commands list and `./plugins/senior-review/skills/review-quality-gates` to its skills list.
- deep-dive-analysis entry: add `./plugins/deep-dive-analysis/commands/team-deep-dive.md` to commands.
- codebase-mapper entry: add `./plugins/codebase-mapper/commands/team-codebase-map.md` to commands.
- research entry: add `./plugins/research/commands/team-research.md` to commands.
If an entry registers a whole `commands/` directory instead of files, no addition is needed there.

- [ ] **Step 2: Version bumps**

Increment from current values:
- Minor bump: `senior-review`, `deep-dive-analysis`, `codebase-mapper`, `research`, `acp-hooks`, `ai-tooling`.
- Patch bump: `abstraction-architect`, `libgdx-development`, `platform-engineering`, `react-development`.
- `metadata.version`: set to `9.0.0`.

- [ ] **Step 3: Validate**

```bash
python -m json.tool .claude-plugin/marketplace.json > /dev/null && echo JSON-OK
```

Expected: `JSON-OK`.

---

### Task 14: Final verification, atomic commit, push

**Files:**
- No new modifications; commit everything.

- [ ] **Step 1: Repo-wide reference sweep**

```bash
grep -rn "/agent-teams:team-review\|/agent-teams:team-deep-dive\|/agent-teams:team-codebase-map\|/agent-teams:team-research\|/agent-teams:team-spawn app-analysis\|/agent-teams:team-spawn tauri\|/agent-teams:team-spawn docs" --include="*.md" --include="*.js" --include="*.json" . | grep -v ".upstream-scratch" | grep -v "docs/superpowers"
```

Expected: zero matches (spec and plan under docs/superpowers are the only allowed mentions, and they are excluded).

```bash
grep -rn "agent-teams" --include="*.md" --include="*.js" --include="*.json" plugins/ | grep -v "wshobson"
```

Review every hit: each must be either an intentional `agent-teams:*` upstream skill/agent reference below a Prerequisites block, a gate entry keeping an upstream command, or prose that names the upstream plugin with provenance. Fix anything else.

- [ ] **Step 2: Dash-aside scan on authored text**

```bash
grep -rn " -- \|—" plugins/senior-review/skills/review-quality-gates/ plugins/senior-review/commands/team-review.md plugins/deep-dive-analysis/commands/team-deep-dive.md plugins/codebase-mapper/commands/team-codebase-map.md plugins/research/commands/team-research.md
```

Review hits: single-connector em-dashes inside moved upstream-derived text are acceptable only if they are not bracketed asides; rewrite any bracketed aside.

- [ ] **Step 3: Scratch hygiene and scope check**

```bash
git status --short | grep -i upstream-scratch || echo "scratch clean"
git diff --stat HEAD
git status --short
```

Expected: `scratch clean`; the stat covers plugins/, docs/, README.md, CLAUDE.md, marketplace.json only.

- [ ] **Step 4: Commit any remaining work on the branch**

```bash
git add -A ':!.upstream-scratch'
git commit -m "wip(agent-teams-delegation): task 14 final verification fixes" || echo "nothing to commit"
```

The squash-merge into master is NOT part of this task. The controller performs it after the final whole-branch review, with this message:

```
Delegate agent-teams to wshobson/agents, relocate team pipelines (v9.0.0)

Remove plugins/agent-teams (6 generic commands, 4 agents, 6 skills), now
provided by the upstream wshobson/agents agent-teams plugin. Relocate the
four local pipelines: team-review -> senior-review, team-deep-dive ->
deep-dive-analysis, team-codebase-map -> codebase-mapper, team-research ->
research. Local-only quality gates move to senior-review:review-quality-gates.
Rewire acp-loader routing, acp-hooks team-spawn-gate, reviewer pipeline
blocks, docs, README, CLAUDE.md sync table and not-vendored list.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
```

- [ ] **Step 5: Report**

Summarize: files moved, files deleted, version bumps applied, surviving upstream references, and the install commands users need for the generic team workflows.
