# Review Pipeline Epistemic Independence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the single epistemic point of failure from the review pipeline, so that a wrong premise formed by X-ray or the interconnect map can no longer propagate to N reviewers and arrive as N concordant false findings.

**Architecture:** Three interventions on two plugins. A strips undue authority from the interconnect map. B adds provenance to every finding and an independent Premise Auditor that vetoes on counterexample. C splits documentation discovery from documentation health, makes the X-ray run directory immutable for orchestrated consumers, replaces the metric that rewarded correlation, and adds the regression case.

**Tech Stack:** Static markdown plugin content. No build step, no runtime framework. Verification is stdlib-only Python linters plus grep assertions on shipped content.

**Source spec:** `docs/superpowers/specs/2026-08-10-review-pipeline-epistemic-independence-design.md`

## Global Constraints

Every task's requirements implicitly include this section.

- **No dash-aside construct anywhere**, in content, comments or commit messages. This targets the rhetorical pattern of bracketing a clause between dashes in any form: em dash, double hyphen, spaced hyphen. Substituting `--` for an em dash is not the fix. Rewrite into separate sentences, parentheses, or colons. Hyphenated compounds are unrelated and fine.

  **Scope the check to lines you added.** These files already use `--` as a field separator and as a single appositive dash, which is house style and is not the banned construct: the ban is on *wrapping* a clause between two dashes. A whole-file grep therefore returns pre-existing hits that are not defects, and chasing them is out of scope for every task in this plan. Always pipe through the added lines only, as the verify steps do. Never "fix" a pre-existing `--` you did not introduce.
- **Stage explicit paths, never `git add -A`.** Other sessions run this repository concurrently. Diff `marketplace.json`, `exports/vscode/package.json` and any CHANGELOG before staging.
- **Bundled paths**: any self-reference to a plugin file uses `${CLAUDE_PLUGIN_ROOT}/...` or a skill-relative `references/...` path inside that same skill. No plugin reaches into another plugin's files by path.
- **The forbidden edge stays closed**: nothing in `codebase-xray` may reference a `senior-review` agent, skill or command at runtime. Passing a file path into a prompt is not a reference; naming an agent or invoking a skill is.
- **Do not weaken** the `## CRITICAL PRINCIPLE: ABSOLUTE SOURCE OF TRUTH` block at `plugins/codebase-xray/skills/analyze/SKILL.md:110-128`. Rules 2 and 7 stay verbatim.
- **No second taxonomy.** The status vocabulary is the existing `verified | documented | unverified` plus exactly one new value, `disputed`.
- **Agent frontmatter**: `model: inherit`, `color` from `red, blue, green, yellow, purple, orange, pink, cyan`, `name` kebab-case matching the filename, long `description` in YAML `>` form.
- **Version bumps land in Task 14 only.** `scripts/check_version_bumps.py` evaluates the whole pushed range, so one bump in the range covers every commit in it. Do not bump per task.
- **Push once, at the end of Task 14.** Not before.

**Canonical new artifact names.** Every task that writes or reads these uses exactly these paths:

| Artifact | Produced by | Mutability |
|---|---|---|
| `<run-dir>/knowledge/navigation.md` | X-ray Phase 0 | written once per run |
| `<run-dir>/knowledge/documentation-leads.md` | X-ray Phase 0 | written once per run |
| `.team-review/01a-review-knowledge-leads.md` | senior-review Phase 0c | **immutable once written** |
| `.team-review/01b-independent-claims.md` | Premise Auditor, Phase 1c | written once |
| `.team-review/01-knowledge-provenance.md` | reconciliation step | derived, post-join |
| `.team-review/02-interconnect.md` | mapper, Phase 1b | unchanged path, do not renumber |

**Canonical flag rename.** `senior-review`'s `--skip-interconnect` becomes `--no-context`. The old name is **removed, with no alias**, in senior-review 9.0.0. This applies **only to `senior-review`**. `codebase-xray:team-analyze` has a flag with the same string and a different meaning (stop after synthesis, do not produce `08-interconnect-map.md`), where the name is accurate. Do not touch any occurrence under `plugins/codebase-xray/` or under the `xray-*` files in the export.

**Canonical new field names.** `Load-bearing premise` (finding field), `premise_provenance` with values `independent | shared-context | mixed`, Lens 0 return keys `premise_verdict` with values `HOLDS | REFUTED | UNCERTAIN`, `refutation_target` with values `PREMISE | SUPPORT`, `counterexample`.

---

### Task 1: The invariant, the context status, and the metrics

The doctrine lands first because six later tasks cite this section by name.

**Files:**
- Modify: `plugins/senior-review/skills/review-quality-gates/SKILL.md` (sections at `:18-31`, `:49-73`, `:75-83`)
- Modify: `plugins/senior-review/commands/team-review.md:414`

**Interfaces:**
- Produces: a section titled exactly `## Shared-Context Provenance Rule`, cited by Tasks 2, 4, 7, 8, 10, 11. A subsection titled exactly `### Epistemic status of the shared context`, cited by Tasks 4 and 8.

- [ ] **Step 1: Add the invariant as a first-level section**

Insert immediately after the `# Review Quality Gates` heading at `:14-16`, before `## Context Sharing Pattern`:

```markdown
## Shared-Context Provenance Rule

> **Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.**

This is the pipeline's first-level invariant, not quality advice. Three consequences bind every gate below:

1. A reviewer that consumed a claim from the deep-dive output or the interconnect map has not verified that claim. It must re-derive the claim independently before standing a finding on it.
2. Concordance between reviewers who share a premise is an **echo**. It raises no confidence and no severity. Consolidation reports it as such.
3. No metric may reward agreement with a shared artifact. Utilization of the map is an operational number, never a quality signal.
```

- [ ] **Step 2: Rewrite the rationale that made the failure feel sanctioned**

Replace the paragraph at `:25-27` (`### Why context sharing matters` and the sentence beginning "Without shared context, each reviewer re-reads the code from scratch. This is wasteful"):

```markdown
### Why context sharing matters, and where it stops

Phase 1 surfaces concerns that are invisible from local inspection: broken implicit contracts, invariant drift, bypass paths, non-idempotent retries, terminal state mutations. Reviewers use the map as a **checklist of things to hunt**, which is where its value is.

The economy argument applies to re-reading the whole codebase. It never applies to re-deriving a premise a finding stands on. Controlled redundancy on load-bearing premises is deliberate: it is the only thing that makes agreement between reviewers mean anything. A pipeline that spends tokens re-verifying one premise and saves them everywhere else is spending them correctly.
```

- [ ] **Step 3: Add the epistemic status clause to the skill's prompt template**

Inside the fenced template at `:51-73`, immediately after the `## Context files` block, insert:

```
### Epistemic status of the shared context

The shared context is NOT ground truth. It is an index of hypotheses produced by
one upstream observer.

- Claims marked `verified` may be reused directly.
- Claims marked `documented`, `unverified` or `disputed` are hypotheses. You MUST
  independently re-derive any such claim before using it as the premise of a finding.
- Actively search for code paths, tests or documents that contradict the context.
  Finding one is a result, not a failure.
- Silence in the context is not evidence of absence. A concern the map does not
  mention may still be real; look anyway.
```

- [ ] **Step 4: Replace the metric section**

Replace `### Quality metric: context utilization rate` at `:75-83` in full:

```markdown
### Metrics

**Map utilization rate** (operational, not a quality signal): the fraction of findings citing an interconnect anchor. It says how much of the map was consumed. It says nothing about whether the review was good, and a high value on a wrong map is the signature of the failure this pipeline is built to avoid. Do not set a target for it.

Quality signals:

| Metric | Meaning |
|---|---|
| **Independent premise reconstruction rate** | fraction of findings whose load-bearing premise was obtained **without exposure to that premise**: derived by the Premise Auditor in Phase 1c, or genuinely re-derived by a reviewer. **Lens 0 does not count.** Mode 2 receives the finding, the declared premise, the map and the deep-dive output, so it is deliberately primed. It falsifies well and derives nothing independently, and counting it here would let dependent observation masquerade as independent corroboration inside the very metrics built to stop that |
| **Premise challenge rate** | fraction of eligible premises (provenance `shared-context` or `mixed`) actually attacked by Lens 0 |
| **Map challenge rate** | fraction of consumed map rows explicitly tested rather than assumed |
| **Map gap rate** | rules, paths and invariants discovered independently that the map never carried, meaning `[MAP-GAP]` findings over total findings |
| **Cross-source corroboration rate** | findings corroborated across code, tests and documentation |

Cross-source corroboration is a diagnostic over findings for which multiple semantically relevant sources exist. It is not a number to maximize. Many findings are provable entirely from code, and a low rate on those is correct.
```

- [ ] **Step 5: Remove the quality-metric label from the user-facing report**

In `plugins/senior-review/commands/team-review.md:414`, replace the line

```
   Findings citing interconnect anchors: {count} ({pct}%) <- quality metric
```

with

```
   Map utilization: {count} findings cite an anchor ({pct}%, operational)
   Independent premise reconstruction: {ipr_count} findings ({ipr_pct}%)
   Premise challenge: {pc_count} of {eligible} eligible premises attacked by Lens 0
```

- [ ] **Step 6: Verify the content landed and no dash-aside was introduced**

```bash
grep -c "Shared-Context Provenance Rule" plugins/senior-review/skills/review-quality-gates/SKILL.md
grep -c "Epistemic status of the shared context" plugins/senior-review/skills/review-quality-gates/SKILL.md
grep -c "quality metric" plugins/senior-review/commands/team-review.md
git diff -U0 | grep -E '^\+' | grep -nE '—|[a-z] -- [a-z]|[a-z] - [a-z]'
```

Expected: `1`, `1`, `0`, and no output from the last command.

- [ ] **Step 7: Commit**

```bash
git add plugins/senior-review/skills/review-quality-gates/SKILL.md plugins/senior-review/commands/team-review.md
git commit -m "Make shared-context provenance a first-level invariant"
```

---

### Task 2: logic-integrity-auditor becomes map-first, never map-authoritative

**Files:**
- Modify: `plugins/senior-review/agents/logic-integrity-auditor.md` (`:32`, `:56`, `:197`, `:202`)

**Interfaces:**
- Consumes: the `## Shared-Context Provenance Rule` section name from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Rewrite Prime Directive 1**

Replace line `:32`:

```markdown
1. **Map-first, never map-authoritative.** Read `.team-review/02-interconnect.md` before touching target code, and let it tell you where to look first. The map is a fallible hypothesis index produced by one upstream observer, not ground truth. Per `## Shared-Context Provenance Rule` in the `senior-review:review-quality-gates` skill, a claim you took from the map is not a claim you verified.
```

- [ ] **Step 2: Replace the empty-section rule that forbade searching**

Replace line `:56` in full. The old text ("If the map has empty sections (e.g., no invariants identified), skip L2 scanning entirely. Do not search where the map says nothing.") is deleted:

```markdown
An empty map section is a hypothesis about the code, not a fact about it. It lowers the priority of that category; it never removes it. Run the independent discovery pass below for every category the target's shape makes plausible, and report what you find as `[MAP-GAP]`.
```

- [ ] **Step 3: Add the independent discovery pass to Phase 2**

Insert at the head of `### Phase 2: Targeted Hunt`, before "For each reviewable item from Phase 1":

```markdown
For every review category in scope, execute these four in order. Steps 2 to 4 are not optional when step 1 produces nothing.

1. **Mapped anchors first.** Hunt the items Phase 1 extracted. This is where your unique value is concentrated.
2. **Independent discovery.** Derive candidates yourself from the changed code, `.team-review/01-knowledge-provenance.md`, the tests, the callers and callees, and semantic siblings of the changed symbols. Do this without consulting the map.
3. **Contradiction hunt.** For each map row you are about to use as a premise, spend one search actively looking for a code path, test or document that contradicts it. Alternate entry points, probe and bootstrap paths, retry and reconnection flows, admin tools and batch jobs are where contradictions hide.
4. **Report the gaps.** Anything found by steps 2 or 3 that the map never carried is a `[MAP-GAP]` finding with full `file:line` evidence for both the rule and the violation.

The scope budget in `## Pipeline Conventions` still binds. Independent discovery is bounded work, not an unbounded re-read.
```

- [ ] **Step 4: Delete the anti-pattern that made MAP-GAP unreachable**

Delete line `:202` in full ("Do NOT read the full target codebase if the map did not flag an anchor. Your job is to verify specific concerns, not rediscover the whole system."). Replace with:

```markdown
- Do NOT re-read the whole codebase indiscriminately. Independent discovery is scoped to the changed symbols, their neighbours, and the categories the target's shape makes plausible. Bounded independent search is required; unbounded rediscovery is not.
```

- [ ] **Step 5: Verify the contradiction is gone**

```bash
grep -c "Do not search where the map says nothing" plugins/senior-review/agents/logic-integrity-auditor.md
grep -c "map-first, never map-authoritative" -i plugins/senior-review/agents/logic-integrity-auditor.md
grep -c "Independent discovery" plugins/senior-review/agents/logic-integrity-auditor.md
```

Expected: `0`, `1`, at least `2`.

- [ ] **Step 6: Commit**

```bash
git add plugins/senior-review/agents/logic-integrity-auditor.md
git commit -m "Make the interconnect map guidance, not authority, for logic integrity"
```

---

### Task 3: The map declares its status and carries four states

**Files:**
- Modify: `plugins/codebase-xray/agents/semantic-interconnect-mapper.md` (`:20`, `:129-132`, `:163-240`)

**Interfaces:**
- Produces: the four-value status vocabulary `verified | documented | unverified | disputed` used by Tasks 7, 8, 10 and 11. The mandatory map header line, cited by Task 8.

- [ ] **Step 1: Add the status declaration to the output format**

In the `## OUTPUT FORMAT` fenced block, immediately after the `> Produced by ...` line at `:174`, add a second blockquote line:

```markdown
> **Status: fallible hypothesis index, not ground truth.** Every row below is a claim by one observer. Rows marked `documented`, `unverified` or `disputed` MUST be independently re-derived before being used as the premise of a finding. An absent row is not evidence of absence.
```

- [ ] **Step 2: Extend Prime Directive 1 with the fourth state**

Replace `:20`:

```markdown
1. **Ground truth only, status always.** Every claim in the map cites a `file:line`. If you cannot cite evidence, omit the claim or mark it `unverified`. Every row in every section carries one of four statuses: `verified` (enforced in code, cite where), `documented` (a comment, docstring or project document declares it, cite where), `unverified` (the code relies on it but nothing enforces or documents it), `disputed` (an independent derivation contradicts it, cite both sides).
```

- [ ] **Step 3: Extend the status vocabulary in Phase 5**

Replace the three-item list at `:129-132` with four items, adding:

```markdown
- `disputed` (an independently derived claim contradicts this one; cite both `file:line` sources and do not resolve the conflict yourself, the reviewers do that)
```

- [ ] **Step 4: Add the status column to the sections that lack it**

In `## OUTPUT FORMAT`, add a `Status` column to the `## Invariants` table, add `-- **status:** [verified|documented|unverified|disputed]` to the `### Formal` and `### Structural` contract bullets (the `### Implicit` bullets already carry it, normalize their wording to the same four values), and add a status suffix to each `## Domain Rules` bullet.

Note on the `--` in that suffix: it is the trailing field separator this file already uses on every contract bullet (`- [Contract description] -- file:line`). A trailing separator is not the banned construct, which is a clause bracketed between dashes on both sides. Match the file's existing style and do not "fix" it.

- [ ] **Step 5: Add the disputed-input instruction**

In `## INPUTS`, add a fourth numbered input:

```markdown
4. **Independent claims** (optional, provided by the invoking command as a file path): a set of claims derived independently of your primary context source. When the path is provided, compare it against your own derivation. Every contradiction becomes a `disputed` row citing both sides. Do not resolve the contradiction, and do not prefer your own derivation by default.
```

- [ ] **Step 6: Verify**

```bash
grep -c "fallible hypothesis index" plugins/codebase-xray/agents/semantic-interconnect-mapper.md
grep -c "disputed" plugins/codebase-xray/agents/semantic-interconnect-mapper.md
grep -c "senior-review" plugins/codebase-xray/agents/semantic-interconnect-mapper.md
```

Expected: `1`, at least `5`, and **`0` for the third**, which proves the forbidden edge stayed closed.

- [ ] **Step 7: Commit**

```bash
git add plugins/codebase-xray/agents/semantic-interconnect-mapper.md
git commit -m "Give the interconnect map a declared status and a disputed state"
```

---

### Task 4: X-ray Phase 0, Project Knowledge Discovery

**Files:**
- Modify: `plugins/codebase-xray/skills/analyze/SKILL.md` (after `:128`)
- Modify: `plugins/codebase-xray/commands/analyze.md` (`:100-107`, `:109-141`, and a new phase section before `## Phase 1`)
- Modify: `plugins/codebase-xray/commands/team-analyze.md` (phase list and run-dir layout)

**Do not touch the partition workers.** Phase 0 is global to the run and is not partitioned. `partition-quality-worker.md` describes only the phases it executes (5 and 6) on its own partition, so it has no phase list to extend and no Phase 0 output path to own.

**Interfaces:**
- Produces: `<run-dir>/knowledge/navigation.md` and `<run-dir>/knowledge/documentation-leads.md`, consumed by Task 7 reconciliation.

- [ ] **Step 1: Add the lead-versus-evidence distinction to the doctrine**

Do not touch rules 1 to 9. Immediately after rule 9 at `:126`, and before the `See references/...` line at `:128`, insert:

```markdown
### Documents play two roles, and only one of them is constrained above

As **evidence**, a document is an unverified claim requiring validation. Rules 2 and 7 govern that role and are not negotiable: a document never establishes a technical fact.

As a **discovery lead**, a document is a first-class input that must be collected early. A project's own index telling you that a concept named X exists and lives in module Y is not a claim about behaviour; it is a pointer telling you where to look and what to look for. Refusing to read it does not make the analysis more rigorous, it makes it blind to intent and to code paths the structure alone does not reveal.

Phase 0 collects leads. Phase 6 audits documents as evidence. Never let the second role suppress the first.
```

- [ ] **Step 2: Add the Phase 0 section to the command**

Insert immediately before `## Phase 1: Structure Extraction` at `:145`:

```markdown
## Phase 0: Project Knowledge Discovery

Runs in **every depth, including `--depth=lite`**, and runs first. It executes inline in the orchestrating context, not as a spawned agent: reading project instructions and globbing for index files is cheap, and Phase 7 already sets the precedent for inline work.

Phases 1 through 7 keep their numbers. `--phase N` is a user-facing flag and renumbering would break every invocation that names a phase.

**Phase 0 is a preamble, not a selectable analysis phase.** It runs before every invocation, `--phase 5` and `--docs-only` included, and it does not change the numbering semantics of phases 1 to 7. `--phase 5` still means "run phase 5 and nothing else from the analysis set", with the preamble in front of it. `--phase 0` runs the preamble alone, which is a legitimate way to ask only "how does this repository document itself".

This phase owns discovery of **how the repository documents itself**. It does not evaluate whether the documentation is accurate, which is Phase 6.

1. Read `CLAUDE.md`, `AGENTS.md` and any equivalent project instruction file at the repository root and in the target's ancestors. Record any navigation instruction they give, especially a statement of the form "look here first to find where a concept lives".
2. Locate the canonical indexes the project actually uses. Glob for, at minimum: `**/SEARCH_INDEX.md`, `**/INDEX.md`, `docs/README.md`, `README.md`, `**/BY_DOMAIN.md`, `**/adr/**`, `**/decisions/**`, `**/architecture/**`, `**/domains/**`, `.codebase-map/INDEX.md`. Record what exists, not what you expected to exist.
3. For each concept, symbol and subsystem in the analysis scope, search the located documents for an entry. Record the concept, the document, and the anchor or heading that matched.
4. Write both output files. Every row is a lead with status `documented` or `unverified`. Nothing here is `verified`, because this phase reads no code.

**Output file:** `$RUN_DIR/knowledge/navigation.md`

```markdown
# Project Knowledge Navigation

## Project instructions read
| File | Navigation rule it states |
|------|---------------------------|

## Canonical indexes found
| Index | Path | What it indexes |
|-------|------|-----------------|

## Conventions observed
[How this repository organizes its knowledge, in prose. Name the file the project treats as its semantic index, if it has one.]

## Not found
[Index kinds searched for and absent. An absent index is a fact worth recording.]
```

**Output file:** `$RUN_DIR/knowledge/documentation-leads.md`

```markdown
# Documentation Leads

> Leads, not truth. Every row is a pointer to where the project claims a concept lives.
> Status is `documented` or `unverified`. No row here is `verified`: this phase reads no code.

| Concept / symbol | Document | Anchor | Status |
|------------------|----------|--------|--------|

## Concepts in scope with no lead
[Concepts the scope touches for which no document was found. This list is what a
downstream consumer must discover independently.]
```
```

- [ ] **Step 3: Wire Phase 0 into both depth modes**

In `### Full depth (default)` at `:113`, add before Wave 1:

```markdown
**Phase 0 (inline, before any agent spawns):** Project Knowledge Discovery. Writes `$RUN_DIR/knowledge/navigation.md` and `$RUN_DIR/knowledge/documentation-leads.md`.
```

In `### Lite depth (--depth=lite)` at `:128`, replace the skip sentence at `:135` so that it reads:

```markdown
Skip Phase 3 (Flow Tracing), Phase 4 (Semantic Understanding), and Phase 6 (Documentation Health). **Phase 0 (Project Knowledge Discovery) is not skippable and runs in lite exactly as in full**: it is the cheap discovery pass, while Phase 6 is the expensive audit. Conflating the two is what made lite mode blind to a project's own documentation. In Phase 5, skip detailed state machine diagrams and Mermaid flowcharts for non-critical files, focusing on anti-patterns, red flags, and tech debt items.
```

In the interactive menu at `:100-107`, add `0. Project Knowledge Discovery (always runs)` to the displayed phase list.

- [ ] **Step 4: Mirror the run-dir layout**

In `plugins/codebase-xray/skills/analyze/SKILL.md`, in the `## Concurrent Runs Model` tree at `:89-100`, add under `<run-id>/`:

```
│       ├── knowledge/                   # Phase 0: navigation.md, documentation-leads.md
```

Apply the same addition to the run-dir layout in `plugins/codebase-xray/commands/team-analyze.md`, and add Phase 0 to its phase list as an inline step the orchestrator runs once for the whole run, before partition detection.

- [ ] **Step 5: Verify**

```bash
grep -c "Project Knowledge Discovery" plugins/codebase-xray/commands/analyze.md
grep -c "knowledge/documentation-leads.md" plugins/codebase-xray/commands/analyze.md
grep -c "ANY INFORMATION NOT VERIFIED WITH IRREFUTABLE EVIDENCE" plugins/codebase-xray/skills/analyze/SKILL.md
python scripts/lint_bundled_paths.py
```

Expected: at least `1`, at least `1`, exactly `1` (the doctrine is intact), and the linter exits clean.

- [ ] **Step 6: Commit**

```bash
git add plugins/codebase-xray/skills/analyze/SKILL.md plugins/codebase-xray/commands/analyze.md plugins/codebase-xray/commands/team-analyze.md plugins/codebase-xray/agents/partition-quality-worker.md
git commit -m "Split documentation discovery from documentation health in X-ray"
```

---

### Task 5: senior-review Phase 0c, Review Evidence Discovery

**Files:**
- Modify: `plugins/senior-review/commands/team-review.md` (new section after Phase 0b at `:199`, and the `state.json` block at `:56-83`)

**Interfaces:**
- Produces: `.team-review/01a-review-knowledge-leads.md`, consumed by Tasks 6, 7. The `phase_0c_evidence_discovery` key in `state.json`.

- [ ] **Step 1: Add the phase key to state.json**

In the `phases` object at `:69-79`, add after `"phase_0b_detection": "pending",`:

```json
     "phase_0c_evidence_discovery": "pending",
     "phase_1c_premise_audit": "pending",
     "phase_1d_reconciliation": "pending",
```

- [ ] **Step 2: Add the phase section**

Insert after Phase 0b ends at `:199`, before `## Phase 1: Context Building`:

```markdown
## Phase 0c: Review Evidence Discovery

Runs inline in the orchestrating context, on every invocation **except** raw mode (`--skip-interconnect` at the time this task runs, renamed to `--no-context` in Task 5b). That flag means "give me the raw mode", and a normally-on phase does not override it: `01a-review-knowledge-leads.md` distributed to N reviewers is itself shared context, so keeping this phase alive under the flag would make findings legitimately `shared-context`, let Lens 0 fire, and stop the mode reproducing the pre-pipeline behaviour it exists to provide.

This phase owns discovery of **what evidence is relevant to this review**. X-ray owns discovery of how the repository documents itself. The two are different jobs and the division is deliberate.

**This phase MUST NOT read `.deep-dive/` in any form**, including the mirror and the output of previous runs. A previous X-ray run is still an X-ray derivation, and admitting one would contaminate the single artifact that has to be demonstrably independent of X-ray. X-ray's leads enter at the Phase 1d join and nowhere earlier.

1. Read `CLAUDE.md`, `AGENTS.md` and equivalent project instruction files, and follow any navigation rule they state. If the project says a specific file is where to look first to find where a concept lives, open that file before opening any code. Discover the conventions from the repository itself, never from a prior X-ray run.
2. Extract the concepts, domains and symbols the diff touches. Names of changed functions, classes, modules and config keys are the starting set; add the domain nouns that appear in the diff's own strings and comments.
3. For each concept, search the project's indexes and documentation for a relevant entry, and search the tests for behaviour that encodes it.
4. Write `.team-review/01a-review-knowledge-leads.md`.

**This file is immutable once written.** No later phase appends to it. X-ray's own leads are joined into a separate derived artifact in Phase 1d, precisely so that the snapshot Phase 1c consumes cannot change underneath it.

**The duty of autonomous rediscovery.** X-ray's documentation leads are an input, never a completeness guarantee. When no lead exists for a concept the diff touches, search the available indexes yourself and record what you find under `Independently discovered by Senior Review`. Without this duty, the completeness of X-ray's discovery becomes the next shared premise, which is the failure this pipeline exists to prevent.

**Output:** `.team-review/01a-review-knowledge-leads.md`

```markdown
# Review Knowledge Leads

> Leads, not truth. Immutable once written.
> Discovered by senior-review independently of any X-ray output.

## Navigation rules followed
| Source | Rule |
|--------|------|

## Concepts touched by this diff
| Concept | Where it appears in the diff |
|---------|------------------------------|

## Leads
| Concept | Document / test | Anchor | Status |
|---------|-----------------|--------|--------|

## Concepts with no lead found
[One line each. This list is the honest statement of what nobody documented.]
```

Mark `phase_0c_evidence_discovery` complete in `state.json`.
```

- [ ] **Step 3: Add the new phase to the raw-mode skip list**

At `:203`, add `phase_0c_evidence_discovery` to the phases marked `skipped` in `state.json` under the raw-mode flag, alongside `phase_1a_deep_dive` and `phase_1b_interconnect`.

The prose rewrite of the mode's own section belongs to Task 5b, which renames it. Do not rewrite `## Backward Compatibility` here: touching the same section from two tasks is how the two halves drift.

- [ ] **Step 4: Verify**

```bash
grep -c "Review Evidence Discovery" plugins/senior-review/commands/team-review.md
grep -c "01a-review-knowledge-leads.md" plugins/senior-review/commands/team-review.md
grep -c "immutable once written" -i plugins/senior-review/commands/team-review.md
grep -c "MUST NOT read" plugins/senior-review/commands/team-review.md
grep -A8 "## Backward Compatibility" plugins/senior-review/commands/team-review.md | grep -c "0c"
```

Expected: at least `1`, at least `3`, at least `1`, at least `1`, at least `1`.

- [ ] **Step 5: Commit**

```bash
git add plugins/senior-review/commands/team-review.md
git commit -m "Add Review Evidence Discovery as a normally-on review phase"
```

---

### Task 5b: Rename the raw-mode flag to `--no-context`

A separate task from 5 because a reviewer could reasonably accept the new phase and reject a user-facing flag removal, or the reverse.

**Files:**
- Modify: `plugins/senior-review/commands/team-review.md` (10 occurrences)
- Modify: `plugins/senior-review/skills/review-quality-gates/SKILL.md` (2 occurrences)
- Modify: `docs/plugins/senior-review.md` (4 occurrences)

**Do not touch** anything under `plugins/codebase-xray/`, `docs/plugins/codebase-xray.md`, or the `xray-*` files in the export. `/codebase-xray:team-analyze --skip-interconnect` keeps both its name and its meaning: there it really does skip only the interconnect map, so the name is accurate. Renaming the `senior-review` flag removes a collision between two commands that share one flag string with two different meanings; renaming both would create one.

**Interfaces:**
- Produces: the flag name `--no-context` and the section title `## Raw mode (--no-context)`, referenced by Tasks 5, 7, 10 and 11.

- [ ] **Step 1: Rename every occurrence in the command**

In `plugins/senior-review/commands/team-review.md`, replace `--skip-interconnect` with `--no-context` and the `state.json` key `"skip_interconnect"` with `"no_context"` at all ten sites: the `argument-hint` frontmatter, the backward-compat sentence in the intro, the always-on dimensions table row for logic integrity, the `flags` block, the Phase 1 skip condition, the Phase 2 context-omission condition, the abstraction addendum, the Phase 4c critic-context line, and the mode section itself.

- [ ] **Step 2: Replace the section with the mode contract**

Replace the whole `## Backward Compatibility` section at `:429-437`:

```markdown
## Raw mode (`--no-context`)

Reviewers receive the target and diff only. No context artifact is produced or
distributed.

- Phases skipped: 0c, 1a, 1c, 1d, 1b
- Not spawned: `logic-integrity-auditor`, `premise-auditor` (either mode)
- Every finding is `independent` by construction, so Lens 0 never fires and
  consolidation never reports an echo
- Output identical in structure to the pre-pipeline version

Use it for targets under roughly 100 LOC where the context pipeline costs more
than it returns, for quick scans, and when X-ray produces no usable output.

`--skip-interconnect` was removed in senior-review 9.0.0. Use `--no-context`.
```

The rename is the point of this step, not decoration. "Backward compatibility" describes a promise not to break old callers; this is a mode selector, and the compatibility framing is what let the first draft of the design treat the mode as inert history and quietly leave a new phase running inside it.

- [ ] **Step 3: Rename in the skill and the plugin docs**

In `review-quality-gates/SKILL.md`, update the pipeline-mode sentence at `:20` and retitle `### Fallback: --skip-interconnect mode` at `:85` to `### Fallback: raw mode (--no-context)`.

In `docs/plugins/senior-review.md`, update the invoke row at `:301`, the always-on dimensions line at `:318`, the example at `:326`, and the explanatory sentence at `:329`. Add the removal note to the example so a reader with the old flag in a script finds the migration where they look:

```
/senior-review:team-review src/ --no-context    # raw mode, no context phase
```

- [ ] **Step 4: Verify the rename is complete and correctly scoped**

```bash
grep -rn "skip-interconnect\|skip_interconnect" plugins/senior-review/ docs/plugins/senior-review.md
grep -c "no-context\|no_context" plugins/senior-review/commands/team-review.md
grep -rn "skip-interconnect" plugins/codebase-xray/ docs/plugins/codebase-xray.md | wc -l
```

Expected: **no output** from the first, which proves the removal is complete with no alias left behind; at least `9` from the second; and a **non-zero** count from the third, which proves `codebase-xray` was correctly left alone. A zero there means someone over-applied the rename.

- [ ] **Step 5: Commit**

```bash
git add plugins/senior-review/commands/team-review.md plugins/senior-review/skills/review-quality-gates/SKILL.md docs/plugins/senior-review.md
git commit -m "Rename the raw-mode flag to --no-context and drop the old name"
```

---

### Task 6: The Premise Auditor agent

**Files:**
- Create: `plugins/senior-review/agents/premise-auditor.md`

**Interfaces:**
- Consumes: `.team-review/01a-review-knowledge-leads.md` from Task 5.
- Produces: `.team-review/01b-independent-claims.md`, consumed by Task 7. The Lens 0 return schema keys, consumed by Task 10. `subagent_type: senior-review:premise-auditor`, spawned by Tasks 7 and 10.

- [ ] **Step 1: Create the agent file**

```markdown
---
name: premise-auditor
description: >
  Derives claims about the code independently of any shared analysis artifact, and attacks the load-bearing premises of findings produced from those artifacts. Runs in two modes: independent derivation during the context phase, blind to X-ray and to the interconnect map, and adversarial premise challenge during verification, with full context.
  TRIGGER WHEN: /senior-review:team-review Phase 1c runs, or the verification panel spawns Lens 0 for a finding whose premise_provenance is shared-context or mixed.
  DO NOT TRIGGER WHEN: the task is to review code for defects (use the dimension auditors), to build the interconnect map (use codebase-xray:semantic-interconnect-mapper), or to judge whether a finding's described defect is reachable (that is Lens 1).
model: inherit
color: orange
tools: Read, Write, Glob, Grep, Bash
---

# Premise Auditor

You exist because a pipeline that derives one premise and then explores it with N agents has one observer, not N. Your job is to be the second derivation, and later to attack the premises the first derivation produced.

You have two modes. The prompt that spawns you names which one. They have different inputs and different forbidden inputs. Never blend them.

## Mode 1: Independent derivation (Phase 1c)

**Inputs:** the diff and scope, `.team-review/01a-review-knowledge-leads.md`, the repository, and any test or document you reach on your own.

**Forbidden inputs.** Do not read, and do not accept in your prompt:

- `.deep-dive/` in any form, including a run directory under `.deep-dive/runs/`
- `.team-review/02-interconnect.md`
- any summary, excerpt or paraphrase of an X-ray conclusion

If your prompt contains one of these, stop and report the contamination instead of proceeding. Your output is worthless if it is a restatement of the thing it is supposed to be independent of. The knowledge leads file is allowed because it contains pointers to where knowledge lives, never conclusions about how the code behaves.

**Mandate: derive only.** Do not compare your claims against anything. Do not review. Do not propose fixes. Do not rank by severity. Comparison is centralized in the reconciliation step and the mapper, which is what lets a reader verify that your derivation was genuinely blind.

**Method.**

1. From the diff, list the concepts, contracts, invariants and domain rules the changed code appears to depend on.
2. For each one, establish what is actually true by reading the code: the callers and callees, alternate entry points, the tests, and the documents the leads file points at.
3. Hunt specifically for **multiplicity**. Where the code appears to have one path, look for a second: a probe path beside a periodic path, a bootstrap path beside a steady-state path, a retry or reconnection path beside a first-attempt path, an admin or batch path beside the user path. Single-path assumptions are the most common way a true local observation becomes a false global conclusion.
4. Record each claim with its status and its `file:line` evidence.

**Output:** `.team-review/01b-independent-claims.md`

```markdown
# Independent Claims

> Derived without access to X-ray output or the interconnect map.
> Status vocabulary: verified | documented | unverified.
> No claim here is `disputed`: this file has nothing to disagree with yet.

## Claims
| Claim | Status | Evidence |
|-------|--------|----------|

## Multiplicity findings
| Apparent single path | Additional path found | Evidence |
|----------------------|-----------------------|----------|

## Could not establish
[Concepts examined where the code did not settle the question. Say so plainly;
an honest gap is more useful than a confident guess.]
```

## Mode 2: Adversarial premise challenge (Phase 4b, Lens 0)

**Inputs:** everything. The finding, its declared load-bearing premise, the interconnect map, the deep-dive output, `.team-review/01-knowledge-provenance.md`, the repository. Full context is correct here: you are attacking a specific proposition, not producing an independent derivation.

**Mandate: try to falsify the premise, not the finding.** Lens 1 asks whether the described defect is reachable. Lens 2 asks whether the finding is a misread. You ask a different question: **is the proposition the finding stands on true at all, across every path it ranges over?**

**Method.**

1. Restate the premise as a proposition with an explicit scope. If the finding says "heartbeat responses cannot refill credentials", the premise ranges over **all** heartbeat paths, not the one the reviewer read.
2. Search for a counterexample within that scope: another path implementing the same outcome, a caller that satisfies the condition the premise says is never satisfied, a test asserting the behaviour the premise says is absent, a project document describing a mechanism the premise ignores.
3. Search the callers and callees of every symbol the premise names.
4. Consult the navigation indexes and the documents the knowledge provenance file lists. A document does not prove the premise false, but it tells you which code path to go read.
5. Decide what your counterexample actually refutes. This distinction decides the finding's fate and is the single most important judgement you make:
   - **PREMISE**: the counterexample makes the load-bearing proposition itself false. The finding falls regardless of how well its supporting evidence was verified.
   - **SUPPORT**: the counterexample invalidates a piece of shared evidence the finding cited, but the load-bearing proposition survives on other grounds.

**Evidence rule.** A verdict of `REFUTED` requires a `file:line` counterexample. Without one, return `UNCERTAIN`. You may not kill a finding on suspicion. A flagged false positive is cheaper than a killed real bug, and that asymmetry is deliberate.

**Premise form check.** A load-bearing premise must be minimal, falsifiable and scoped. If the premise you were given is a paraphrase of the finding ("the implementation is broken", "heartbeat handling is incorrect") rather than a single proposition whose falsity collapses the finding, report `premise_form: non-compliant`, derive the real premise yourself, and challenge that instead. Never return `HOLDS` merely because a vague premise was hard to attack.

**Output.** Return exactly:

```
- premise_verdict: HOLDS or REFUTED or UNCERTAIN
- refutation_target: PREMISE or SUPPORT        (only when REFUTED)
- counterexample: file:line                    (required when REFUTED)
- premise_form: compliant or non-compliant
- reason: 1-2 sentences citing file:line
```

## ANTI-PATTERNS

- Do NOT return `REFUTED` without a `file:line` counterexample. That is `UNCERTAIN`.
- Do NOT attack the finding's severity, its fix, or its wording. Only the premise.
- Do NOT, in mode 1, read a forbidden input "just for orientation". Blindness that is only mostly true buys nothing.
- Do NOT, in mode 1, write comparisons. If you notice a contradiction with something you happen to know, record your own claim and its evidence, and let reconciliation find the contradiction.
- Do NOT pad either output. An empty multiplicity table on code that genuinely has one path is a correct result.
```

- [ ] **Step 2: Verify frontmatter and the closed edge**

```bash
head -12 plugins/senior-review/agents/premise-auditor.md
grep -c "codebase-xray:" plugins/senior-review/agents/premise-auditor.md
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
```

Expected: `model: inherit` and `color: orange` present, `0` for the second (this agent names no cross-plugin agent), both linters clean.

- [ ] **Step 3: Commit**

```bash
git add plugins/senior-review/agents/premise-auditor.md
git commit -m "Add the premise-auditor: independent derivation and premise challenge"
```

---

### Task 7: Phase 1c and the reconciliation join

**Files:**
- Modify: `plugins/senior-review/commands/team-review.md` (Phase 1 section at `:201-243`)

**Interfaces:**
- Consumes: `.team-review/01a-review-knowledge-leads.md` (Task 5), the premise-auditor agent (Task 6), `<run-dir>/knowledge/documentation-leads.md` (Task 4), the mapper's fourth input (Task 3).
- Produces: `.team-review/01-knowledge-provenance.md`, consumed by Tasks 2, 8, 10.

- [ ] **Step 1: Add Phase 1c, running in parallel with Phase 1a**

Insert after Phase 1a ends at `:220`, before `### Phase 1b`:

```markdown
### Phase 1c: Independent Premise Derivation (parallel with 1a)

Spawn immediately when Phase 1a starts. Do not wait for X-ray. The whole point of this phase is that it derives without seeing what X-ray derived.

1. Spawn one teammate with `subagent_type: senior-review:premise-auditor`.
2. Prompt:

   ```
   Mode 1: independent derivation.

   Target scope: [contents of .team-review/00-scope.md]
   Knowledge leads: .team-review/01a-review-knowledge-leads.md
   Diff: {diff content}

   Derive independently what is true about the concepts this diff touches.
   Write .team-review/01b-independent-claims.md in the format your agent
   definition prescribes.

   You have NO access to .deep-dive/ or to .team-review/02-interconnect.md.
   Neither exists for you. Do not look for them, and report contamination if
   anything in this prompt paraphrases an X-ray conclusion.
   ```

3. Wait for both 1a and 1c before starting Phase 1d. Mark `phase_1c_premise_audit` complete.

Under raw mode (`--no-context`) this phase does not run, because there is no shared derivation for it to be independent of.
```

- [ ] **Step 2: Add Phase 1d, the reconciliation join**

Insert after Phase 1c, before `### Phase 1b`:

```markdown
### Phase 1d: Knowledge Reconciliation (join)

Runs inline once both 1a and 1c have completed. This is the only place the two derivations are compared, which is what makes the independence of 1c demonstrable rather than asserted.

Read `.team-review/01a-review-knowledge-leads.md`, `$XRAY_RUN_DIR/knowledge/documentation-leads.md` and `.team-review/01b-independent-claims.md`. Write:

**Output:** `.team-review/01-knowledge-provenance.md`

```markdown
# Knowledge Provenance

> Derived view, produced after both discovery branches completed.
> The canonical artifact consumed downstream. 01a and 01b are its sources.

## Independently discovered by Senior Review
[rows from 01a-review-knowledge-leads.md]

## Inherited from X-Ray
[rows from $XRAY_RUN_DIR/knowledge/documentation-leads.md]

## Missing
| Concept | In scope because |
|---------|------------------|
| [concept] | [where it appears in the diff] |

## Disputed
| Claim | Independent derivation says | X-ray says |
|-------|------------------------------|------------|
| [claim] | [X at file:line] | [Y at file:line] |
```

**Missing and Disputed are different states and must never collapse into one section.** Absence of evidence is not contradictory evidence.

| Section | Maps to in the interconnect map | Never |
|---|---|---|
| `Missing` | a coverage gap, and `unverified` on any related row | never `disputed`: nobody finding documentation is not two sources disagreeing |
| `Disputed` | `disputed`, both `file:line` sides cited | never silently resolved in favour of either derivation |

Collapsing them would drain `disputed` of the precise meaning the rest of this work depends on, which is that two derivations reached incompatible conclusions and a reviewer must settle it.

Two asymmetries here are diagnostics worth reading, not noise. A row present in `Independently discovered by Senior Review` and absent from `Inherited from X-Ray` means X-ray's discovery had a gap. The reverse means Phase 0c had one. Both are recorded and neither is silently reconciled.

Mark `phase_1d_reconciliation` complete.
```

- [ ] **Step 3: Feed the independent claims into the mapper**

In the Phase 1b prompt at `:227-239`, add the fourth input and the disputed instruction:

```
   Independent claims: .team-review/01b-independent-claims.md
   Knowledge provenance: .team-review/01-knowledge-provenance.md

   Compare the independent claims against your own derivation. Every
   contradiction becomes a `disputed` row citing both sides. Do not resolve
   contradictions and do not prefer your own derivation by default.
```

- [ ] **Step 4: Update the pipeline plan display**

In the plan block at `:189-195`, replace the phase list:

```
Pipeline plan:
  Phase 0c: review evidence discovery (inline)
  Phase 1a: codebase-xray (--depth=lite)   |  Phase 1c: premise-auditor (parallel, blind)
  Phase 1d: knowledge reconciliation (inline)
  Phase 1b: codebase-xray:semantic-interconnect-mapper
  Phase 2:  {N} reviewers in parallel
  Phase 3:  consolidation
  Phase 4:  report
```

- [ ] **Step 5: Verify**

```bash
grep -c "01b-independent-claims.md" plugins/senior-review/commands/team-review.md
grep -c "01-knowledge-provenance.md" plugins/senior-review/commands/team-review.md
grep -c "senior-review:premise-auditor" plugins/senior-review/commands/team-review.md
python scripts/lint_dependency_graph.py
```

Expected: at least `3`, at least `3`, at least `1`, linter clean.

- [ ] **Step 6: Commit**

```bash
git add plugins/senior-review/commands/team-review.md
git commit -m "Add blind premise derivation and the knowledge reconciliation join"
```

---

### Task 8: Finding format at the enforcement point

The orchestrator prompt is the enforcement point because it also reaches reviewers in other plugins, which this repository cannot edit.

**Files:**
- Modify: `plugins/senior-review/commands/team-review.md` (reviewer template at `:272-296`)
- Modify: `plugins/senior-review/commands/code-review.md` (`:163-183`, `:199-222`)
- Modify: `plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md` (shared finding format)

**Interfaces:**
- Consumes: the `### Epistemic status of the shared context` block from Task 1.
- Produces: the `Load-bearing premise` and `premise_provenance` fields, consumed by Tasks 9, 10, 11.

- [ ] **Step 1: Add the two fields to the team-review reviewer template**

In the fenced template at `:276-296`, after the `## Instructions` paragraph, add:

```
## Premise declaration (required on every finding)

Every finding carries two extra fields:

- **Load-bearing premise:** the single proposition whose falsity collapses this
  finding. It must be minimal, falsifiable and scoped.
    Bad:  "The implementation is broken."
    Bad:  "Heartbeat handling is incorrect."   (a paraphrase of your finding)
    Good: "No credential-bearing response path exists after registration."
- **premise_provenance:** one of `independent`, `shared-context`, `mixed`.
  This records CAUSAL DEPENDENCE, not citation. If you absorbed the premise from
  the deep-dive output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.
```

Also insert the `### Epistemic status of the shared context` block from Task 1 immediately after the `## Context files` block in the same template.

- [ ] **Step 2: Rewrite the Deep Dive Context template in code-review**

Replace `plugins/senior-review/commands/code-review.md:170-173`. The current text tells the agent not to re-report findings covered by the deep-dive, which reads as permission to treat the deep-dive as settled:

```
## Deep Dive Context

The following context was gathered from a prior deep-dive analysis. It is an index
of hypotheses produced by one upstream observer, not ground truth.

Use it to know WHERE to look. Do not use it to know WHAT IS TRUE: re-derive any
claim you intend to stand a finding on. Actively look for code paths that
contradict it; finding one is a result, not a failure. Silence in this context is
not evidence of absence.

Do not restate findings already reported here as if they were your own; add the
issues your specialized perspective reveals.
```

- [ ] **Step 3: Add the premise fields to the code-review shared instructions**

In `### Shared Instructions for All Agents` at `:199-222`, add the same `## Premise declaration (required on every finding)` block from Step 1.

- [ ] **Step 4: Add the fields to each agent's own output format**

`code-review-agents.md` has no shared finding template. It holds one prompt per agent (A through N), each inside a fenced block, and several of those carry their own `## Output Format` list (Agent B2's is at `:250-261`, and it lists Source, Severity, File plus line, Confidence, description, Recommended action, Fix phase).

Step 3 is the enforcement point and already reaches every A-N agent, because the shared instructions are included in every agent prompt. This step is for consistency: in each agent block that has an `## Output Format` list of finding fields, add two bullets after the severity and location lines and before the description line:

```
    - Load-bearing premise: the single proposition whose falsity collapses this
      finding. Minimal, falsifiable, scoped. Not a paraphrase of the finding
    - premise_provenance: independent | shared-context | mixed (causal dependence
      on the deep-dive output or interconnect map, not citation of it)
```

Agents whose block has no `## Output Format` list inherit the fields from the shared instructions and need no edit. Enumerate which agents you edited in the commit body, so a later reader can tell an intentional omission from a missed one.

- [ ] **Step 5: Verify**

```bash
grep -c "Load-bearing premise" plugins/senior-review/commands/team-review.md plugins/senior-review/commands/code-review.md plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md
grep -c "Do NOT re-report findings already covered here" plugins/senior-review/commands/code-review.md
grep -c "premise_provenance" plugins/senior-review/commands/team-review.md
```

Expected: each file at least `1`, the second exactly `0`, the third at least `1`.

- [ ] **Step 6: Commit**

```bash
git add plugins/senior-review/commands/team-review.md plugins/senior-review/commands/code-review.md plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md
git commit -m "Require every finding to declare its premise and its provenance"
```

---

### Task 9: Finding format in the eleven local reviewer agents

The orchestrator enforces the fields. The agent bodies document them, so direct invocation produces the same shape.

**Files:**
- Modify, in each one's `## OUTPUT FORMAT` finding block: `plugins/senior-review/agents/` `api-contract-auditor.md`, `chicken-egg-detector.md`, `cleanup-auditor.md`, `code-auditor.md`, `data-integrity-auditor.md`, `distributed-flow-auditor.md`, `logic-integrity-auditor.md`, `resource-lifecycle-auditor.md`, `security-auditor.md`, `temporal-resilience-auditor.md`, `ui-race-auditor.md`

**Interfaces:**
- Consumes: the field names from Task 8.

- [ ] **Step 1: Insert the same two lines into each agent's finding template**

In every file listed above, inside the fenced `## OUTPUT FORMAT` finding block, after the severity or category line and before the scenario or description line, insert verbatim:

```markdown
- **Load-bearing premise:** [the single proposition whose falsity collapses this finding: minimal, falsifiable, scoped. Not a paraphrase of the finding itself]
- **premise_provenance:** independent | shared-context | mixed [causal dependence, not citation: shared-context if you absorbed the premise from the deep-dive output or the interconnect map, even when your finding cites no anchor]
```

- [ ] **Step 2: Verify all eleven landed**

```bash
grep -lc "Load-bearing premise" plugins/senior-review/agents/*.md | wc -l
grep -L "premise_provenance" plugins/senior-review/agents/*.md
```

Expected: `12` for the first (eleven auditors plus premise-auditor from Task 6), and no output from the second.

- [ ] **Step 3: Commit**

```bash
git add plugins/senior-review/agents/
git commit -m "Document the premise fields in every local reviewer output format"
```

---

### Task 10: Lens 0

**Files:**
- Modify: `plugins/senior-review/skills/review-quality-gates/SKILL.md` (`## Adversarial Verification Panel` at `:120-240`)
- Modify: `plugins/senior-review/commands/team-review.md` (Phase 4b at `:362-374`)
- Modify: `plugins/senior-review/commands/code-review.md` (Step 4b at `:284-311`)

**Interfaces:**
- Consumes: the premise fields (Task 8), the premise-auditor agent (Task 6), `.team-review/01-knowledge-provenance.md` (Task 7).
- Produces: the `filtered: premise-refuted` and `premise-contested` tags, consumed by Task 11.

- [ ] **Step 1: Add Lens 0 to the panel section**

In `## Adversarial Verification Panel`, replace the sentence at `:122` describing three lenses, and add before the Lens 1 prompt:

```markdown
The panel has four lenses. **Lens 0 is gated on provenance and runs first**, before lenses 1 and 2, for the same reason lens 3 is gated last: a finding a veto will discard should not consume the other lenses. Lens 3 stays gated on survival.

Lens 0 runs only for findings whose `premise_provenance` is `shared-context` or `mixed`. A finding declared `independent` skips it. A finding that declares nothing is treated as `shared-context` when the pipeline ran, and the report records the reviewer as format-non-compliant. A finding with no `Load-bearing premise` has one derived by Lens 0, with the same note. The pipeline never drops a finding over a missing field.

**Lens 0 prompt (Premise Challenge):** spawn with `subagent_type: senior-review:premise-auditor`, mode 2, inheriting the session model.

```
Mode 2: adversarial premise challenge.

## The Finding
[severity, file:line, description, suggested fix]

## The declared load-bearing premise
[the finding's Load-bearing premise field verbatim, or "none declared"]

## Context available
- Interconnect map: .team-review/02-interconnect.md
- Knowledge provenance: .team-review/01-knowledge-provenance.md
- Deep-dive: $XRAY_RUN_DIR

## Instructions
Follow mode 2 of your agent definition. Attack the premise, not the finding.
Return REFUTED only with a file:line counterexample; without one, return UNCERTAIN.
Decide and state whether the counterexample falsifies the PREMISE itself or only
a piece of shared SUPPORT.
```

**Path substitution differs by command, per Task 12.** In `/team-review` the deep-dive line resolves to `$XRAY_RUN_DIR`, the immutable directory of the run that command started. In `/code-review` it resolves to the `.deep-dive/` mirror, because that command consumes a pre-existing analysis it did not produce. The interconnect map and knowledge provenance lines exist only in the `/team-review` path; in `/code-review` they are omitted, and a finding there is `independent` unless the deep-dive context supplied its premise.

- [ ] **Step 2: Add the resolution table**

Insert immediately before `### Survival rule` at `:220`:

```markdown
### Lens 0 resolution

Refutation type is resolved first, provenance second. Provenance decides only what can survive after a source is invalidated.

| Lens 0 result | Effect |
|---|---|
| `REFUTED`, target `PREMISE` | Finding discarded, counted `filtered: premise-refuted`. Regardless of provenance, and regardless of lenses 1-2, which are not spawned. |
| `REFUTED`, target `SUPPORT`, provenance `mixed` | Strike the shared leg. Restate the finding from the surviving independent evidence and run lenses 1-2 on the reduced finding. |
| `REFUTED`, target `SUPPORT`, provenance `shared-context` | Nothing survives the strike. Discarded, counted `filtered: premise-refuted`. |
| `UNCERTAIN` | Finding proceeds to lenses 1-2, tagged `premise-contested`. |
| `HOLDS` | Finding proceeds to lenses 1-2 unchanged. |

Local correctness cannot outvote a refuted premise. A verifier can be entirely right that the code at the cited line does what the finding says, while the inference from that fact to the finding's conclusion is dead because another path exists. That is why Lens 0 is a veto and not a fourth vote.

A `premise_form: non-compliant` return is recorded in the verification file and reported, whatever the verdict. It means a reviewer declared a paraphrase instead of a premise, and it is a defect in the review, not in the code.
```

- [ ] **Step 3: Extend the survival rule and fail-open**

In `### Survival rule` at `:220-225`, add as the first bullet:

```markdown
- Lens 0 is evaluated **before** the rule below. A finding discarded by Lens 0 never reaches lenses 1-2. A finding whose Lens 0 returned `UNCERTAIN` or `HOLDS` is judged by the rule below exactly as before.
```

In `### Fail-open` at `:227-229`, add:

```markdown
A Lens 0 that errors, returns malformed output, or returns `REFUTED` without a `file:line` counterexample is treated as `UNCERTAIN`. Lens 0 never kills a finding by failing.
```

- [ ] **Step 4: Wire both orchestrators**

In `team-review.md` Phase 4b step 3, replace the spawn instruction so Lens 0 is spawned first for eligible findings, lenses 1-2 only for survivors, lens 3 as today. In the `98-verification.md` row format at step 5, add the Lens 0 verdict, the refutation target and the counterexample. Apply the equivalent edits to `code-review.md` Step 4b at `:284-311`.

- [ ] **Step 5: Verify**

```bash
grep -c "Lens 0" plugins/senior-review/skills/review-quality-gates/SKILL.md
grep -c "premise-refuted" plugins/senior-review/skills/review-quality-gates/SKILL.md plugins/senior-review/commands/team-review.md plugins/senior-review/commands/code-review.md
grep -c "refutation_target" plugins/senior-review/skills/review-quality-gates/SKILL.md
python scripts/lint_dependency_graph.py
```

Expected: at least `6`, each file at least `1`, at least `1`, linter clean.

- [ ] **Step 6: Commit**

```bash
git add plugins/senior-review/skills/review-quality-gates/SKILL.md plugins/senior-review/commands/team-review.md plugins/senior-review/commands/code-review.md
git commit -m "Add Lens 0: counterexample-backed premise veto in the panel"
```

---

### Task 11: Consolidation stops counting echoes as corroboration

**Files:**
- Modify: `plugins/senior-review/commands/team-review.md` (Phase 4 at `:349-360`, report block at `:388-419`)
- Modify: `plugins/senior-review/commands/code-review.md` (`### 4b. Deduplication` at `:263-274`)

**Interfaces:**
- Consumes: `premise_provenance` (Task 8), the invariant section name (Task 1).

- [ ] **Step 1: Replace the cross-reference rule in team-review**

Replace item 4 at `:356` ("**Cross-reference**: note findings that appear in multiple dimensions (a sign of a likely-real root cause).") with:

```markdown
4. **Cross-reference, weighted by provenance.** Per `## Shared-Context Provenance Rule` in the `senior-review:review-quality-gates` skill, agreement is only corroboration when the agreeing findings did not inherit the same premise.
   - Findings that agree and are all `independent`, or whose load-bearing premises are disjoint: **corroborated**. Report as a likely-real root cause.
   - Findings that agree and share the same `shared-context` premise: **echo**. Report under the finding as `Echo: N dimensions agreed from the shared premise "[premise text]"`. This raises no confidence and no severity, and it is not evidence that the finding is real.
   - Mixed sets: corroboration counts only the independent members.
```

- [ ] **Step 2: Apply the same rule to code-review deduplication**

In `### 4b. Deduplication` at `:263-274`, add the same three-way weighting in the command's own vocabulary.

- [ ] **Step 3: Surface the distinction in the report**

In the report block, add to the `### Summary` section:

```
   Corroborated findings: {n_corroborated} (independent agreement)
   Echoes: {n_echo} (agreement inherited from a shared premise, not corroboration)
```

- [ ] **Step 4: Verify**

```bash
grep -c "Echo:" plugins/senior-review/commands/team-review.md
grep -ci "echo" plugins/senior-review/commands/code-review.md
grep -c "a sign of a likely-real root cause" plugins/senior-review/commands/team-review.md
```

Expected: at least `1`, at least `1`, and `0` for the third.

- [ ] **Step 5: Commit**

```bash
git add plugins/senior-review/commands/team-review.md plugins/senior-review/commands/code-review.md
git commit -m "Weight cross-dimension agreement by premise provenance"
```

---

### Task 12: Immutable run directory for orchestrated consumers

**Files:**
- Modify: `plugins/codebase-xray/skills/analyze/SKILL.md` (`## Concurrent Runs Model`, after rule 4 at `:107`)
- Modify: `plugins/senior-review/commands/team-review.md` (`state.json` block, Phase 1a, Phase 1b prompt at `:231`, reviewer template at `:286`, abstraction addendum at `:305`)
- Modify: `plugins/senior-review/commands/code-review.md` (`:154-161`)
- Modify: `plugins/senior-review/skills/review-quality-gates/SKILL.md` (`:22`, `:61`)

**Interfaces:**
- Produces: the `xray` provenance block in `.team-review/state.json`, and the `$XRAY_RUN_DIR` substitution already referenced by Tasks 7 and 10.

- [ ] **Step 1: Add the rule to the X-ray contract**

Insert as rule 6 in `## Concurrent Runs Model`:

```markdown
6. **Mirror is for latest-state consumers only.** `.deep-dive/` is a mutable convenience mirror of the latest published run. It MUST NOT be used by an orchestrated workflow to consume the output of a specific X-ray invocation: rule 4 makes the root mirror owned by whichever run published last, so a concurrent run can replace it between production and consumption. A workflow that started a run and then consumes it MUST retain and propagate the immutable run directory `.deep-dive/runs/<run-id>/`. The general form: a specific invocation implies the immutable run directory, a latest-state consumer implies the mirror. One-shot commands asking for the most recent published analysis are correct on the mirror.
```

- [ ] **Step 2: Record the provenance block**

In the `state.json` template in `team-review.md`, add after `"files_created": []`:

```json
     "xray": {
       "run_id": null,
       "run_dir": null,
       "target": null,
       "depth": null
     },
```

In Phase 1a step 2, replace "Record the directory path in `state.json -> files_created`" with:

```markdown
2. Read `.deep-dive/runs.json` to resolve the run the skill just created, and record it in `state.json -> xray` as `run_id`, `run_dir`, `target` and `depth`. Every later phase derives its paths from this block and never from the `.deep-dive/` root. `$XRAY_RUN_DIR` below always means `state.json -> xray.run_dir`. If the run cannot be resolved, halt: an unresolvable provenance is a broken pipeline, not a reason to fall back to the mirror.
```

- [ ] **Step 3: Substitute the three consuming prompts**

Replace `Deep-dive output: .deep-dive/ (files: ...)` at `:231` with `Deep-dive output: $XRAY_RUN_DIR (files: 01-structure.md, 02-interfaces.md, 05-risks.md, knowledge/documentation-leads.md, ...)`. Replace `- Deep-dive output: .deep-dive/ (see ...)` at `:286` with the `$XRAY_RUN_DIR` form. Replace `deep_dive_path: {.deep-dive/ when Phase 1a ran ...}` at `:305` with `deep_dive_path: {$XRAY_RUN_DIR when Phase 1a ran and produced output, otherwise "none"}`.

- [ ] **Step 4: Update the skill's context-sharing paths, with the nuance the skill needs**

`review-quality-gates` is shared by both commands, and the two are on opposite sides of the rule. Do not blanket-replace. At `:22` and `:61`, state the conditional:

```markdown
Deep-dive output at the path the orchestrating command recorded: `$XRAY_RUN_DIR`
when that command started the X-ray run itself (`/team-review` Phase 1a), or the
`.deep-dive/` mirror when it is consuming an analysis that already existed
(`/code-review` Step 2). A command that started a run never reads the mirror: the
mirror means "latest published run", not "the run I just produced".
```

- [ ] **Step 5: Leave code-review on the mirror, because the rule puts it there**

`code-review` does **not** migrate. `code-review.md:154-161` checks whether a completed `.deep-dive/` analysis already exists and consumes it; it never starts an X-ray run. By the rule added in Step 1 that makes it a latest-state consumer, for which the mirror is the correct and intended contract. Migrating it would contradict the rule this task exists to establish.

Add one clarifying sentence at `:154-161` recording that this is a deliberate classification and not an oversight, and stating that if `code-review` is ever changed to start an X-ray run itself, it moves to the run directory at that point.

- [ ] **Step 6: Verify**

```bash
grep -c 'XRAY_RUN_DIR' plugins/senior-review/commands/team-review.md
grep -nE '\.deep-dive/[0-9]' plugins/senior-review/commands/team-review.md
grep -c 'XRAY_RUN_DIR' plugins/senior-review/skills/review-quality-gates/SKILL.md
grep -c "MUST NOT be used by an orchestrated workflow" plugins/codebase-xray/skills/analyze/SKILL.md
git diff --stat plugins/senior-review/commands/code-review.md
```

Expected: at least `5`; **no output** from the second, which proves no direct mirror file read survives in the command that starts the run; at least `1` for the third; `1` for the fourth; and the last shows a small diff of one or two added lines only, because `code-review` is classified, not migrated. A large diff on `code-review.md` means someone migrated it against the rule.

- [ ] **Step 7: Commit**

```bash
git add plugins/codebase-xray/skills/analyze/SKILL.md plugins/senior-review/commands/team-review.md plugins/senior-review/commands/code-review.md plugins/senior-review/skills/review-quality-gates/SKILL.md
git commit -m "Propagate the immutable X-ray run directory through the review pipelines"
```

---

### Task 13: The regression case

**Files:**
- Create: `evals/senior-review/cases/jupiter-credential-refill/case.md`
- Modify: `evals/senior-review/README.md` (`## Protocol` step 3, `## Metrics`, `## Case sources`)

**Interfaces:**
- Consumes: nothing. This task is independent and can be executed in any order after Task 1.

- [ ] **Step 1: Add the anti-finding field to the protocol**

In `## Protocol` step 3, after the existing scoring sentence, add:

```markdown
A case may also carry a `must_not_report` block. Each entry is a claim the review must NOT produce at that revision, because it is false at the system level even though a plausible local reading supports it. Scoring an entry: `avoided` (no finding matches the claim), `reported` (a finding matching the claim survived the pipeline's own verification), `caught` (a finding matching the claim was produced but killed by the verification panel, and the record names the lens that killed it). Only `reported` is a failure. `caught` is the outcome the panel exists to produce, and the case notes which lens did it.
```

In `## Metrics`, add:

```markdown
- **Anti-finding rate** = `reported` / total `must_not_report` entries. This measures precision against known-plausible falsehoods, which recall cannot see. A pipeline that finds every real bug and also reports a confident falsehood is not a better reviewer.
```

- [ ] **Step 2: Write the case**

Create `evals/senior-review/cases/jupiter-credential-refill/case.md` following the shape of the existing Jupiter cases, with:

```markdown
# Case: jupiter-credential-refill

Source: production incident, 2026-08-10. A `/senior-review:team-review` run reported
a Critical finding that was false at the system level. Ground truth is the code and
the project's own documentation at the reviewed revision.

repo: D:\Projects\jupiter
review_rev: [the revision reviewed on 2026-08-10]
review_scope: the agent heartbeat and auto-registration modules

## must_not_report

- claim: "heartbeat responses cannot refill strategy credentials"
  why_false: >
    Two heartbeat paths exist. The periodic path carries metadata without strategy
    fields, which is true and is what the false finding was built on. The probe
    response path carries the credentials, so the refill converges.
  local_fact_that_is_true: "periodic heartbeat metadata carries no strategy fields"
  evidence:
    - docs/00_navigation/SEARCH_INDEX.md, entry "Credential Refill"
    - docs/01_domains/agents/heartbeat.md, section explaining the two paths
    - docs/01_domains/agents/auto_registration.md, the routable-but-mute record
    - the probe response handler in the agent heartbeat module
  what_should_catch_it:
    - Phase 0c should surface SEARCH_INDEX.md and heartbeat.md as leads
    - Phase 1c should record the second path under Multiplicity findings
    - Lens 0 should return REFUTED, target PREMISE, citing the probe response handler

## known_bugs

(none required: this case scores precision, not recall)

## Notes for the scorer

The failure mode is specifically that four dimensions "confirmed" the finding
independently while all four had been handed the same premise. When scoring a run,
check the consolidated report: agreement between findings sharing one premise must
appear as an echo, never as corroboration. A run that reports the claim AND labels
the agreement as corroboration fails twice.
```

- [ ] **Step 3: Register the case source**

In `## Case sources`, add a row:

```markdown
| Jupiter false-positive incident (2026-08-10, precision ground truth) | `jupiter-credential-refill` |
```

- [ ] **Step 4: Verify**

```bash
ls evals/senior-review/cases/jupiter-credential-refill/case.md
grep -c "must_not_report" evals/senior-review/README.md evals/senior-review/cases/jupiter-credential-refill/case.md
grep -c "Anti-finding rate" evals/senior-review/README.md
```

Expected: the file exists, both files at least `1`, `1`.

- [ ] **Step 5: Fill the revision**

`review_rev` is the one placeholder in this plan that cannot be resolved from this repository. Resolve it from the Jupiter repository before committing: find the revision reviewed on 2026-08-10 with `git -C D:/Projects/jupiter log --until=2026-08-11 --oneline -5` and substitute the hash. Do not commit the case with the bracket text in place.

- [ ] **Step 6: Commit**

```bash
git add evals/senior-review/cases/jupiter-credential-refill/ evals/senior-review/README.md
git commit -m "Add the credential-refill precision case to the senior-review evals"
```

---

### Task 14: Release

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `exports/vscode/_pipelines/.github/**` (mirrored content)
- Modify: `exports/vscode/package.json` (only if the agent contribution list changed)

**Interfaces:**
- Consumes: everything.

- [ ] **Step 1: Load the export skill before touching exports**

Invoke the `downstream-exports` skill. Do not guess the mapping. The export is an **adapted** mirror, not a byte copy: `senior-review` and `codebase-xray` both live in the single `_pipelines` bundle, agent filenames are prefixed (`review-*.agent.md`, `xray-*.agent.md`), the verification lenses are one file (`review-verification-lens.agent.md`), and `review-quality-gates` has `references/pipeline.md` where the source has three separate reference files. The skill holds the source map and the divergences that must survive a sync.

- [ ] **Step 2: Mirror the content**

Apply every content change from Tasks 1 to 12 to the corresponding files in `exports/vscode/_pipelines/.github/`, with the skill's adaptations reapplied. The new `premise-auditor` agent becomes `exports/vscode/_pipelines/.github/agents/review-premise-auditor.agent.md`. Lens 0 goes into `review-verification-lens.agent.md`.

**The flag rename needs care in this bundle, because it carries both plugins.** Rename `--skip-interconnect` to `--no-context` only in the `senior-review` side: `prompts/team-review.prompt.md`, `agents/review-orchestrator.agent.md`, `agents/review-logic-integrity-auditor.agent.md`, `agents/review-generic-reviewer.agent.md`, `skills/review-quality-gates/SKILL.md`, `skills/review-quality-gates/references/pipeline.md`, and the `/team-review` example in `README.md`. Leave every `xray-*` file and the `/xray-team-analyze` example in `README.md` untouched. A blind find-and-replace across `_pipelines` is the specific mistake to avoid here, and Task 5b Step 4's third assertion is what catches it.

- [ ] **Step 3: Bump versions**

```
.claude-plugin/marketplace.json:
  codebase-xray  2.1.0  -> 2.2.0   (new always-on phase, new run-dir artifacts, additive)
  senior-review  8.1.2  -> 9.0.0   (new pipeline phases, new agent, changed finding format
                                    and changed consolidation semantics)
  metadata.version 19.1.3 -> 19.2.0
```

- [ ] **Step 4: Regenerate the extension manifest**

A new agent changed the contribution list, so this is required, not optional:

```bash
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py
```

Then bump `version` in `exports/vscode/package.json`.

- [ ] **Step 5: Run every check**

```bash
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/check_version_bumps.py origin/master HEAD
```

Expected: all five clean. If `check_version_bumps.py` fails, the bump is wrong, not the script.

- [ ] **Step 6: Scan the whole change for the banned construct**

```bash
git diff origin/master --unified=0 | grep -E '^\+' | grep -nE '—|[^-]--[^-]|[a-z] - [a-z]'
```

Expected: no output. Hyphenated compounds and command flags are fine; a clause bracketed between dashes is not.

- [ ] **Step 7: Commit and push, staging explicit paths**

```bash
git status --porcelain
git diff .claude-plugin/marketplace.json exports/vscode/package.json
git add .claude-plugin/marketplace.json exports/vscode/_pipelines exports/vscode/package.json
git commit -m "Release the review pipeline epistemic independence work"
git push
```

Check `git status --porcelain` first and stage only the paths this work touched. Another session may have unrelated changes in the tree.

---

## Self-Review

**Spec coverage.** A1 Task 2, A2 and A3 Task 3, B1 Tasks 1 and 8, B2 Tasks 8 and 9, B3 Tasks 6 and 7, B4 Task 10, B5 Task 11, C1 Task 4, C2 Task 5, C3 Task 7, C3b Task 5b, C4 Task 12, C5 Task 1, C6 Task 13. The spec's "deliberately not done" list is enforced by the Global Constraints. Release mechanics are Task 14.

**Placeholders.** One remains and is declared: `review_rev` in Task 13, which cannot be resolved from this repository. Task 13 Step 5 gives the command to resolve it and forbids committing without it. Two content locations use bracketed guidance inside example templates, which is the existing house style for output templates in this repository, not a plan gap.

**Corrections applied after design review.** Five, two of them logic bugs inherited from the first draft of the spec, all now fixed in both documents:

1. Phase 0c may not read `.deep-dive/` in any form, previous runs included. Reading X-ray navigation output would contaminate the one artifact required to be demonstrably independent of X-ray. Task 5.
2. Raw mode now skips Phase 0c too. The earlier text kept 0c alive and simultaneously claimed every finding would be `independent`, which cannot both hold: `01a` distributed to N reviewers is shared context. Task 5, Steps 2 and 3.
3. `code-review` is off the run-directory perimeter. It never starts an X-ray run, so by this work's own rule it is a latest-state consumer and the mirror is its correct contract. Task 12, Steps 4 and 5.
4. `Missing` and `Disputed` are separate sections with separate mappings. Absence of evidence is not contradictory evidence, and collapsing them would drain `disputed` of its meaning. Task 7.
5. Lens 0 no longer counts toward independent reconstruction. Mode 2 receives the finding, the premise, the map and the deep-dive output, so it is deliberately primed: it falsifies well and derives nothing independently. The metric splits into independent premise reconstruction rate and premise challenge rate. Task 1.

**Type consistency.** Artifact paths, field names, status values and Lens 0 return keys are fixed in Global Constraints and used identically in Tasks 3, 6, 7, 8, 9, 10, 11 and 12. `$XRAY_RUN_DIR` is defined once, in Task 12 Step 2, as `state.json -> xray.run_dir`, and Tasks 7 and 10 reference it under that definition. Tasks 7 and 10 are written before Task 12 in file order but consume a name Task 12 defines: execute Task 12 before or immediately after them if executing out of order, or accept that the string is inert until Task 12 lands, since nothing runs at build time.
