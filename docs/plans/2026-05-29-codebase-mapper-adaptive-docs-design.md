# Codebase Mapper: Audience-Adaptive Documentation Redesign

Date: 2026-05-29
Status: Design approved, pending spec review
Plugin: `codebase-mapper` (2.6.0; audit fixes bump to 2.6.1; redesign targets 2.7.0)

## Problem

The plugin generates accurate developer documentation but under-delivers on the mission it should serve: truly understanding a project's scope, purpose, functioning, and context, then producing documentation that is excellent and comprehensible by everyone (not only a developer on their first day).

Concrete gaps in the current implementation:

1. **Reads only code.** `codebase-explorer` reads README/CLAUDE/CONTRIBUTING plus source. The WHY (why the project exists, domain, history, decisions, constraints) lives outside code: git history, ADRs, CHANGELOG, issues/PRs, in-repo product copy. No step reconstructs it.
2. **Single fixed audience.** The writing guidelines target "a smart colleague on their first day" (a developer). Every document is developer-centric. There is no plain-language layer for non-technical readers (PM, designer, domain expert, stakeholder, client).
3. **No explicit scope.** Boundaries and non-goals (what the project deliberately does not do) are never stated.
4. **Shallow-by-design exploration.** "Sample strategically, do not read every file" is in tension with truly understanding a non-trivial project.
5. **"Sublime" is asserted via tone rules, not engineered.** No analogies, mental models, layered structure, or worked examples calibrated to the reader.

## Goals

- Documentation **reflects the project**: a cybersecurity tool reads as precise and technical; a consumer fishing app reads as vivid, benefit-led, and accessible.
- Documentation is **comprehensible by everyone**, including non-technical readers, via an always-present plain-language entry point and a domain glossary.
- The pipeline **autonomously** infers project type, purpose, context, and target audience. A confirm step exists only as a lightweight safety net; the agent must be genuinely smart at inference without leaning on the user.
- The WHY (purpose, problem solved, domain context, key decisions) and the SCOPE (boundaries, non-goals) are captured and documented.
- The adaptive capability is **centralized** (a shared reference consumed by all writers), not duplicated per command, and **adopted at graduated depth** across the plugin.

## Non-goals

- No dropping of documents per project type. The document set stays stable; depth and register scale. Honest gaps are still noted, never padded.
- No heavy profiling machinery in `docs-maintain` (drift audit), where audience adaptation adds little.
- No second full codebase read for profiling: profiling rides on the existing exploration pass.
- No change to the existing Phase 1b interconnect-map integration.

## Design decisions (locked)

| Dimension | Decision |
|---|---|
| Audience reach | Everyone, including non-technical readers |
| Profiling mechanism | Infer autonomously, then confirm (confirm is a correction safety net) |
| Architecture | Full adaptive redesign (option B) |
| Blast radius | Shared spine plus graduated adoption |

## Architecture

### 1. The Project Profile (new artifact)

A structured profile produced during exploration and written into the context brief. It is the artifact that makes documentation reflect the project.

Profile schema (captured in `context-brief.md`, surfaced for confirmation):

- **Project type / domain**: e.g. security tool, consumer app, dev library, internal service, data/ML pipeline, game, CLI. Inferred from manifests/dependencies, naming, README framing, presence of UI, domain vocabulary, distribution channel (app store vs package registry vs internal), and recurring themes in git history.
- **Purpose and problem (the WHY)**: what problem it solves, for whom, the value proposition. Mined from README, CHANGELOG, ADRs, git log, issue/PR titles, and in-repo landing or marketing copy.
- **Audience and register**: the target reader(s) and the register on a spectrum from technical-precise to accessible-vivid.
- **Scope and non-goals**: what the project does and what it explicitly does not do.
- **Maturity**: prototype/experimental vs production, inferred from tests, CI, versioning, CHANGELOG.
- **Confidence and signals**: every inference cites the signals it rests on. Low-confidence items are flagged for the confirm step.

### 2. Autonomous profiling (placement)

Profiling is folded into `codebase-explorer` rather than a separate agent. The explorer already reads exactly the right signals during its single deep pass, so combining avoids a redundant read. The explorer gains a "Project Profile" section (first section of the context brief) plus a "Why / Context" dossier section. The explorer's prompt is upgraded to reason explicitly from signals to classification, with confidence and citations.

### 3. Confirm gate (Phase 1.5 of map-codebase)

After exploration and before the writers run, the `map-codebase` command surfaces the inferred Profile (type, audience, register, scope, confidence) and asks the user to confirm or adjust. Default path is fully autonomous; the user intervenes only to correct. Low-confidence inferences are highlighted.

### 4. Shared register model (the spine)

New reference: `plugins/codebase-mapper/skills/codebase-mapper/references/audience-adaptation.md`. Read on demand by every agent that writes documentation. Contents:

- **Register matrix**: maps the Project Profile to register parameters: tone, jargon policy, example style, diagram style, what to emphasize vs de-emphasize, whether and how prominently to include the plain-language layer and glossary.
- **4-5 archetypes** with concrete calibrations:
  - Technical / infrastructure (security tool, library, CLI): precise, complete, contract/threat-aware, deep internals, short plain layer.
  - Consumer app: benefit-led, vivid, plain language, screenshots/flows, light internals, prominent plain layer.
  - Domain / business (internal line-of-business): domain-glossary-heavy, workflow-led, stakeholder framing.
  - Data / ML pipeline: data-lineage-led, dataset and transform framing.
  - Game: core-loop and mechanics framing.
- **"For everyone" layering rule**: every guide gets a plain-language entry point. In technical projects it is brief and hands off quickly to depth; in consumer/mixed projects it is the centerpiece.

This single file is the reason the blast radius stays graduated and free of duplication: the capability is defined once and consumed at the appropriate depth by each command.

### 5. map-codebase (full implementation)

- The audience is no longer the constant "smart colleague on first day". It is the audience defined in the Project Profile.
- Output is a **stable document set with adaptive depth and register**. No document disappears; depth scales to the Profile, and gaps stay honest.
- **Two always-present additions** (prominence scaled by the Profile):
  - `00-executive-summary.md`: one page, plain language, analogies, what/why/who, zero jargon. The "for everyone" entry point.
  - `11-glossary.md`: domain glossary, high value for non-technical readers.
- **New content**: a "Why this exists / Context" treatment (the WHY) and a "Scope and Non-Goals" section. Both appear in plain form in `00-executive-summary.md` and are expanded with file-cited detail in `01-overview.md`.
- **guide-reviewer** additionally checks register consistency (does the tone match the Profile?) and that the plain-language layer plus glossary genuinely serve a non-technical reader. INDEX offers reading paths per audience: a non-technical path starting at 00 plus glossary, and a developer path as today.

### 6. Graduated adoption (rest of the plugin)

- **documentation-engineer / docs-create** (medium touch): infer a lightweight profile or accept one passed as an argument, read `audience-adaptation.md`, and calibrate the generated technical document's framing, glossary inclusion, and plain-language intro to the audience.
- **doc-humanizer / humanize-docs** (light touch): humanize toward the target register rather than a single fixed narrative tone.
- **docs-maintain** (minimal): when adding missing sections, match the existing document's register. No profiler.

### 7. writing-guidelines.md change

The shared writing guidelines replace the single fixed audience with a parameter: "the audience defined in the Project Profile; default to a smart colleague on their first day when no profile exists". The guidelines link to `audience-adaptation.md`.

## Output structure (new .codebase-map/ layout)

```
.codebase-map/
  INDEX.md                    # Entry point with per-audience reading paths
  00-executive-summary.md     # NEW: plain-language, for anyone
  01-overview.md              # + Why/Context, + Scope/Non-Goals
  02-features.md
  03-tech-stack.md
  04-architecture.md
  05-workflows.md
  06-data-model.md
  07-getting-started.md
  08-open-questions.md
  09-project-anatomy.md
  10-configuration-guide.md
  11-glossary.md              # NEW: domain glossary
  _internal/
    context-brief.md          # now leads with Project Profile + Why/Context dossier
    interconnect.md           # Phase 1b structured map (unchanged)
```

## Files touched

New:
- `references/audience-adaptation.md` (register matrix, archetypes, layering rule)

Edited (codebase-mapper plugin):
- `agents/codebase-explorer.md` (Project Profile + Why/Context inference; signal-based reasoning)
- `commands/map-codebase.md` (Phase 1.5 confirm gate; writers read the Profile; 00 and 11 added; reviewer register check)
- `agents/overview-writer.md` (owns 00-executive-summary; plain-language top; Why/Scope)
- `agents/tech-writer.md`, `agents/flow-writer.md`, `agents/onboarding-writer.md`, `agents/ops-writer.md`, `agents/config-writer.md` (read Profile + audience-adaptation; adapt depth/register)
- `agents/guide-reviewer.md` (register consistency; non-technical readability; owns 11-glossary or assigns it; per-audience INDEX)
- `agents/documentation-engineer.md` (consume register; lightweight profile; adaptive framing)
- `agents/doc-humanizer.md` (target register)
- `commands/docs-create.md`, `commands/humanize-docs.md` (pass/consume register)
- `skills/codebase-mapper/SKILL.md` (document Profile, Phase 1.5, new docs, register model, References Library entry for audience-adaptation.md)
- `skills/codebase-mapper/references/writing-guidelines.md` (audience as parameter)

Marketplace:
- `.claude-plugin/marketplace.json` (codebase-mapper description reflects adaptive docs; plugin version bump 2.6.0 -> 2.7.0; metadata.version bump)

## Risks and open questions

- **Glossary ownership**: whether `11-glossary.md` is written by `guide-reviewer` (which sees all docs and the interconnect glossary signals) or by a writer. Leaning reviewer, since it has the cross-document view. To finalize in the plan.
- **Profile confidence threshold**: when to force the confirm gate vs proceed silently. Default: always show a compact profile summary, but only block on low-confidence type/audience.
- **Token budget**: adding 00 and 11 plus richer profiling increases output. Acceptable given the goal; depth scaling keeps technical projects from bloating.
- **Backward compatibility**: existing `.codebase-map/` outputs from prior versions lack 00/11. Regeneration overwrites cleanly; no migration needed.

## Versioning

The 5 audit fixes ship first as `codebase-mapper` 2.6.1 (this design doc rides along in the same commit). The adaptive redesign is a separate minor bump: 2.6.1 -> 2.7.0 (new capability, new references, new docs). Bump `metadata.version` with each.
