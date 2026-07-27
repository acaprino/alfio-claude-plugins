# ai-tooling 2026 Prompt Engineering Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the prompt engineering content of the `ai-tooling` plugin to 2026 state of the art, adding reasoning-model, context engineering, and evals coverage as sections inside existing files.

**Architecture:** Research-first content refresh. One deep-researcher spawn produces sourced findings; findings are classified per the CLAUDE.md update protocol (clear win / subtle shift / no change / open question); only classified findings drive surgical Edits to three markdown files; version bumps and a single commit close the pass.

**Tech Stack:** Static markdown, `research:deep-researcher` agent, `.claude-plugin/marketplace.json` registry. No build, no tests; verification is grep plus JSON parse.

## Global Constraints

- No dash-aside constructs in any written text: no `—`, `--`, or ` - ` bracketing a parenthetical clause (CLAUDE.md convention). Single-connector hyphens in compounds are fine.
- No new files under `plugins/ai-tooling/`. New content lands as sections inside existing files.
- No changes outside these four files: `plugins/ai-tooling/agents/prompt-engineer.md`, `plugins/ai-tooling/references/reasoning-patterns.md`, `plugins/ai-tooling/commands/prompt-optimize.md`, `.claude-plugin/marketplace.json`.
- Surgical Edits only; never rewrite a whole file with Write.
- Agent body style: terse keyword lists, imperative tone, XML section tags preserved.
- Every content change must trace to a research finding classified "clear win" or "subtle shift". No unsourced additions.
- Version bumps: ai-tooling `3.2.1 -> 3.3.0`, metadata `12.0.0 -> 12.0.1`.
- Spec: `docs/superpowers/specs/2026-07-27-ai-tooling-prompt-engineering-refresh-design.md`.

---

### Task 1: Run domain research

**Files:**
- Create: `C:\Users\alfio\AppData\Local\Temp\claude\D--Projects-alfio-claude-plugins\1612f0de-8c74-4b17-a36a-a4d82cb80c84\scratchpad\refresh-findings.md` (scratchpad, never committed)

**Interfaces:**
- Produces: `refresh-findings.md` with one `## Finding N` section per fact, each with a `Source:` line and a `Confidence:` line. Task 2 consumes this file.

- [ ] **Step 1: Spawn the researcher**

Spawn `research:deep-researcher` via the Agent tool with this prompt:

```
Angles: A + D + B
Query: prompt engineering best practices as of 2026, focused on facts that would
change recommendations in an existing 2022-2024-era knowledge base. Specifically:
1. Reasoning models / extended thinking (Claude extended thinking, OpenAI o-series,
   DeepSeek R1 class): when do explicit reasoning-pattern prompts (Chain-of-Thought,
   Tree-of-Thought, Self-Consistency, Plan-and-Solve, Least-to-Most, Step-Back,
   Self-Ask, Skeleton-of-Thought, ReAct, Reflexion) become redundant or actively
   harmful? What do vendors officially recommend? What do practitioners report?
2. Context engineering: how has the discipline reframed prompt engineering
   (system prompt design, tool descriptions, retrieval placement, compaction)?
3. Prompt evals: current recommended practice for evaluating and regression-testing
   prompts (eval-driven development, LLM-as-judge caveats, vendor tooling).
4. Agentic prompting: current guidance for writing system prompts and tool
   descriptions for agents.
5. Still-valid checks: is XML structuring still recommended for Claude? Is
   "instructions first, weighted more heavily" still true for long-context models?
   Are the 10 classic patterns above still cited as useful for non-reasoning models?
Focus: facts with authoritative or well-corroborated sources. For every finding,
name the source. Flag anything inconclusive as inconclusive.
```

- [ ] **Step 2: Save findings to scratchpad**

Write the researcher's findings to `refresh-findings.md` in the scratchpad, one `## Finding N` section per fact, each ending with `Source:` and `Confidence: high|medium|inconclusive` lines. Do not commit this file.

- [ ] **Step 3: Sanity-check coverage**

Confirm the findings file answers all 5 query areas. If an area is missing, spawn `research:quick-searcher` with a single-area follow-up query and append the result. Expected: all 5 areas have at least one finding.

### Task 2: Classify findings against current content

**Files:**
- Modify: `C:\Users\alfio\AppData\Local\Temp\claude\D--Projects-alfio-claude-plugins\1612f0de-8c74-4b17-a36a-a4d82cb80c84\scratchpad\refresh-findings.md` (append classification table)

**Interfaces:**
- Consumes: `refresh-findings.md` from Task 1.
- Produces: a `## Classification` table appended to the same file with columns: Finding | Target file | Target section | Class | Action. Tasks 3-5 consume this table.

- [ ] **Step 1: Re-read the three target files**

Read `plugins/ai-tooling/agents/prompt-engineer.md`, `plugins/ai-tooling/references/reasoning-patterns.md`, `plugins/ai-tooling/commands/prompt-optimize.md` in full.

- [ ] **Step 2: Classify every finding**

For each finding assign exactly one class per the CLAUDE.md update protocol:

- `clear-win`: current text states something research contradicts with a confirmed replacement, or a confirmed-relevant topic is absent. Action: Edit with specific anchor.
- `subtle-shift`: old guidance still works but is no longer the default. Action: Edit to mention both, old approach second.
- `no-change`: research confirms current text. Action: none.
- `open-question`: `Confidence: inconclusive`. Action: add an HTML comment `<!-- Open question (2026-07-27): ... revisit next refresh cycle -->` near the relevant section.

Append the table. Every finding must appear in the table exactly once.

- [ ] **Step 3: Derive the edit list**

Under the table, list the concrete edits per file in execution order, each with: target anchor (exact existing text to Edit against), change summary, finding number(s). This list is the input to Tasks 3-5. Expected: every `clear-win` and `subtle-shift` finding maps to at least one edit; `open-question` findings map to comment insertions.

### Task 3: Edit reasoning-patterns.md

**Files:**
- Modify: `plugins/ai-tooling/references/reasoning-patterns.md`

**Interfaces:**
- Consumes: edit list from Task 2.
- Produces: updated reference. Task 4 and Task 5 rely on the final pattern catalog and any new section title chosen here (Task 5 syncs the pattern list in the command; use the exact section title and pattern names from this task).

- [ ] **Step 1: Add the reasoning-model applicability section**

Insert a new section after the `## Selection cheat sheet` block (anchor: the line `If two patterns fit, prefer the one that adds the least latency and token cost.`) titled `## Reasoning models change the defaults`. Content per Task 2's edit list. It must state, with sourced findings only: which of the 10 patterns are absorbed by extended-thinking models, which remain useful, and a rule for deciding (target model class first, pattern second). Keyword-list style, no dash-asides.

- [ ] **Step 2: Update cheat sheet and decision guide**

Edit the `## Selection cheat sheet` table and the `## Decision guide` numbered list so both branch on model class where the research supports it (e.g. a step 0 "Is the target a reasoning model?" in the decision guide). Keep every row/step that research classified `no-change`.

- [ ] **Step 3: Apply remaining classified edits**

Apply every remaining edit-list entry targeting this file: per-pattern updates (e.g. a "Reasoning-model note:" line inside affected pattern sections), new post-2023 pattern sections if any finding was `clear-win`, and open-question comments.

- [ ] **Step 4: Verify style**

Run Grep on the file for `—`, ` -- `, and ` - ` used as aside brackets. Expected: no dash-aside constructs (table cells and hyphenated compounds are fine). Fix any hits.

### Task 4: Edit prompt-engineer.md (agent)

**Files:**
- Modify: `plugins/ai-tooling/agents/prompt-engineer.md`

**Interfaces:**
- Consumes: edit list from Task 2; final pattern catalog from Task 3.
- Produces: updated agent. The `<reasoning_patterns_library>` block must reference the same pattern set Task 3 finalized.

- [ ] **Step 1: Refresh capabilities**

Edit the `<capabilities>` block: add bullets for the confirmed new competencies (expected from research: context engineering, reasoning-model-aware pattern selection, prompt evals; exact wording per Task 2's edit list). Keep existing bullets research classified `no-change`.

- [ ] **Step 2: Refresh optimization techniques and framework**

Apply the edit-list entries for `<optimization_techniques>` and `<prompt_design_framework>`: update any claim research reclassified (candidates flagged at design time: XML structuring wording, instruction-positioning claims for long-context models), inserting `subtle-shift` items as "default X; Y still valid when Z" phrasing.

- [ ] **Step 3: Sync the patterns library block**

If Task 3 added or renamed patterns or added the reasoning-model section, Edit the `<reasoning_patterns_library>` block (line anchor: `Patterns covered:`) so the enumerated list and the read-trigger sentence match the reference exactly, and mention the reasoning-model section as a read trigger when the target is a reasoning model.

- [ ] **Step 4: Verify style**

Grep the file for dash-asides as in Task 3 Step 4. Expected: clean. The agent keeps XML tags, keyword lists, under ~250 lines.

### Task 5: Edit prompt-optimize.md (command)

**Files:**
- Modify: `plugins/ai-tooling/commands/prompt-optimize.md`

**Interfaces:**
- Consumes: final pattern catalog from Task 3.
- Produces: command consistent with agent and reference.

- [ ] **Step 1: Fix the stale spawn block**

Edit the workflow block: replace the line `Task:` (start of the fenced block at "## Workflow: Single-Pass Analysis & Optimization") with `Agent:` and the sentence `Execute the full analysis and optimization in a single \`prompt-engineer\` subagent call.` stays as is. Exact edit:

```
old: Task:
       subagent_type: "prompt-engineer"
new: Agent:
       subagent_type: "prompt-engineer"
```

- [ ] **Step 2: Sync the pattern list**

Edit the "Reasoning-pattern check" paragraph (anchor: `(CoT, Step-Back, ReAct, Tree-of-Thought,`) so the parenthesized pattern list matches Task 3's final catalog, and add the model-class gate if Task 3 introduced one (expected phrasing: check target model class before adding a pattern; reasoning models rarely need explicit scaffolds).

- [ ] **Step 3: Verify style**

Grep for dash-asides. Expected: clean.

### Task 6: Version bumps

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: nothing new.
- Produces: registry consistent with the refresh.

- [ ] **Step 1: Bump ai-tooling version**

Edit the ai-tooling entry (the `"version"` line directly following `"name": "ai-tooling"` / `"source": "./plugins/ai-tooling"`):

```
old: "version": "3.2.1",
new: "version": "3.3.0",
```

(the old_string must be scoped with surrounding lines to be unique in the file).

- [ ] **Step 2: Bump metadata version**

```
old: "version": "12.0.0"
new: "version": "12.0.1"
```

(scope with the `metadata` block context for uniqueness).

- [ ] **Step 3: Validate JSON**

Run: `node -e "JSON.parse(require('fs').readFileSync('.claude-plugin/marketplace.json','utf8')); console.log('valid')"`
Expected: `valid`.

### Task 7: Final verification, commit, push

**Files:**
- No new modifications; commit of Tasks 3-6 output plus the plan file.

- [ ] **Step 1: Full grep sweep**

Grep the three touched plugin files for: `—`, ` -- `, `Task tool`, `Teammate`, `spawnTeam`. Expected: zero hits (excluding legitimate hyphenated compounds; `subagent_type` is a parameter name and is fine).

- [ ] **Step 2: Scope check**

Run: `git status --short` and `git diff --stat`
Expected: only the four in-scope files plus `docs/superpowers/plans/2026-07-27-ai-tooling-prompt-engineering-refresh.md` appear. Nothing from the scratchpad.

- [ ] **Step 3: Commit and push**

```bash
git add plugins/ai-tooling/agents/prompt-engineer.md plugins/ai-tooling/references/reasoning-patterns.md plugins/ai-tooling/commands/prompt-optimize.md .claude-plugin/marketplace.json docs/superpowers/plans/2026-07-27-ai-tooling-prompt-engineering-refresh.md
git commit -m "Refresh ai-tooling for 2026 prompt engineering practices (v3.3.0)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git push
```

Expected: push succeeds to `master`.
