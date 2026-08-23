---
description: Writes 10 documents with Mermaid diagrams and an INDEX.md entry point into .codebase-map/. Use when the user asks to onboard to an unfamiliar project, generate a codebase tour, or produce a full narrative guide for new contributors. Not for structured AST or dependency analysis (use `/xray-team-analyze` in the `_pipelines` bundle) or just API docs (use /docs-create).
agent: map-codebase-orchestrator
argument-hint: "[target-path]"
---

# Map Codebase

Generate a human-readable guide for an unfamiliar codebase. Produces 10 narrative documents with inline Mermaid diagrams, organized for progressive learning.

## Pre-flight

`$SKILLS` is the installed skills directory: the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists.

1. **Determine target path**: Use the argument if provided, otherwise use the current working directory.

2. **Check for existing output**:
   ```bash
   ls .codebase-map/ 2>/dev/null
   ```
   - If `.codebase-map/` exists with content, ask the user: "A codebase map already exists. Overwrite it? (y/n)"
   - If user declines, stop here

3. **Create output directories**:
   ```bash
   mkdir -p .codebase-map/_internal
   ```

## Phase 1: Explore (sequential)

Dispatch one `codebase-explorer` with `#agent/runSubagent`:

**Agent task:**
> Explore this project and write a context brief to `.codebase-map/_internal/context-brief.md`. Follow your exploration strategy to understand what the project does, its tech stack, directory structure, key entry points, data model, and main workflows. Read actual code - do not guess from file names. Include file paths for every claim.

**Verify** with `#search/fileSearch` that `.codebase-map/_internal/context-brief.md` exists and is non-empty.

If the context brief is missing or empty, stop and report the error.

## Phase 1.5: Confirm Project Profile (sequential)

The `codebase-explorer` wrote a `## Project Profile` section as the first section of `.codebase-map/_internal/context-brief.md`. Surface it for a quick confirmation before the writers run.

1. Read the `## Project Profile` section from `.codebase-map/_internal/context-brief.md`.
2. Present a compact summary to the user: project type and domain, primary audience, register, scope, and any items the explorer marked low-confidence.
3. Ask the user to confirm or adjust (use `#vscode/askQuestions`). The default is the inferred profile; the user only corrects.
4. If the user adjusts anything, overwrite the `## Project Profile` section in `context-brief.md` with the corrected values, so the writers read the confirmed profile.

This is the only interactive checkpoint. Profiling itself is autonomous; this step is a light safety net, not a questionnaire. Keep it to one question.

## Phase 1b: Interconnect Map (sequential)

Dispatch one `xray-interconnect-mapper`, if that agent is available. It ships in the `_pipelines` bundle, installed separately; if it is absent, skip straight to Phase 2 in degraded mode. This phase produces structured facts (contracts, invariants, domain rules, integration hot-spots) that the writer agents cite instead of paraphrasing code.

**Agent task:**
> Build the interconnect map for this project.
>
> Primary context source: `.codebase-map/_internal/context-brief.md` (produced by codebase-explorer).
> Target files: the whole project (infer scope from the context brief's directory structure).
> Output path: `.codebase-map/_internal/interconnect.md`
>
> Produce the full structured map following your agent definition: Call Graph (2-3 hop for public entry points), Contracts (formal / structural / implicit), Invariants, Domain Rules, Assumptions (verified / documented / unverified), Integration Hot-Spots, Change Impact Radius, and Reviewer Hints (which anchors each downstream writer should read).
>
> Every claim must cite file:line. No recommendations, no fixes. Empty sections are acceptable if nothing applies.

**Verify:** Check that `.codebase-map/_internal/interconnect.md` exists and contains the required anchors (`## Contracts`, `## Invariants`, `## Domain Rules`, `## Assumptions`, `## Integration Hot-Spots`).

If the file is missing, skip it and continue to Phase 2 in degraded mode -- writers will not receive interconnect facts but can still use the context brief. Log a warning.

## Phase 2: Write (6 writers, concurrent)

Dispatch all 6 writers in a single message so they run concurrently. Every writer first reads the `## Project Profile` and `## Why / Context` sections of `.codebase-map/_internal/context-brief.md` and `$SKILLS/codebase-mapper/references/audience-adaptation.md`, then calibrates register, depth, and vocabulary to the confirmed profile (a consumer-app guide favors plain language and user value; a technical-tool guide favors precision and depth).

### Agent 1: `overview-writer`
> Read `.codebase-map/_internal/context-brief.md` (especially `## Project Profile` and `## Why / Context`), then write `.codebase-map/00-executive-summary.md` (plain-language, for anyone, zero jargon), `.codebase-map/01-overview.md`, and `.codebase-map/02-features.md`. Put a "Why this exists / Context" section and a "Scope and Non-Goals" section in 01-overview. Include a Mermaid mindmap in the overview. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 2: `tech-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/03-tech-stack.md` and `.codebase-map/04-architecture.md`. Include a Mermaid component/layer diagram in the architecture doc. If `.codebase-map/_internal/interconnect.md` exists, read its `## Call Graph`, `## Contracts`, and `## Integration Hot-Spots` anchors and cite those structured facts in the architecture doc instead of paraphrasing code. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 3: `flow-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/05-workflows.md` and `.codebase-map/06-data-model.md`. Include Mermaid flowcharts and sequence diagrams for workflows, and an ER diagram for the data model. If `.codebase-map/_internal/interconnect.md` exists, read its `## Invariants` (especially temporal), `## Integration Hot-Spots`, and `## Domain Rules` anchors and encode those facts directly in sequence diagrams and data-flow narratives. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 4: `onboarding-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/07-getting-started.md` and `.codebase-map/08-open-questions.md`. Make getting-started practical with copy-pasteable commands. Make open-questions specific and actionable. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 5: `ops-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/09-project-anatomy.md`. Document the annotated directory tree, every configuration file and what it controls, all environment variables, scripts and executables, startup sequence, and default ports/URLs. If `.codebase-map/_internal/interconnect.md` exists, read its `## Integration Hot-Spots` anchor (rows of type Env/config) and use it as the authoritative list of env vars and config files. Verify claims by reading actual config files and grepping for env var usage. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 6: `config-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/10-configuration-guide.md`. Write a practical guide covering configuration walkthrough, environment profiles, configuration recipes, common day-to-day operations with exact commands, troubleshooting with real error messages from the codebase, and a quick-reference cheat sheet. Verify by reading actual config files and grepping for error messages. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

**Verify** with `#search/fileSearch` that `00-executive-summary.md` and the 10 numbered documents (01-10) exist:
```bash
ls -la .codebase-map/0*.md .codebase-map/10*.md
```

(`11-glossary.md` is produced in Phase 3.) If any are missing, report which ones failed and stop.

## Phase 3: Review (sequential)

Dispatch one `guide-reviewer` with `#agent/runSubagent`:

**Agent task:**
> Read all documents in `.codebase-map/` (00 and 01 through 10) and the context brief in `_internal/`. If `.codebase-map/_internal/interconnect.md` exists, also read its `## Invariants` and `## Domain Rules` anchors, and and, if the `_pipelines` bundle is installed, use its `defect-taxonomy` skill's `logic-integrity.md` reference to detect documentation-reality drift (docs that describe behavior contradicting documented invariants/contracts). Flag any drift as a "⚠ known inconsistency" note in the relevant doc and add a corresponding item to 08-open-questions.md. Review for terminology consistency, add cross-references between documents, fix any AI boilerplate in tone, validate Mermaid diagram syntax, and detect gaps. Apply edits directly. Also read the `## Project Profile` from the context brief and `$SKILLS/codebase-mapper/references/audience-adaptation.md`, then: (a) verify register consistency, so the tone across all docs matches the profile's register, and fix drift; (b) verify the plain-language layer serves a non-technical reader; (c) write `.codebase-map/11-glossary.md`, a domain and technical glossary with plain definitions, built from terminology across all docs and the interconnect glossary and domain-rule signals. Then write `.codebase-map/INDEX.md` as the entry point with a navigable summary table that includes 00-executive-summary and 11-glossary, plus per-audience reading paths (a non-technical path starting at 00 and 11, and a developer path).

**Verify** with `#search/fileSearch` that `.codebase-map/INDEX.md` exists.

## Completion

Print a summary:

```
Codebase map generated in .codebase-map/

  INDEX.md              - Entry point and navigation
  00-executive-summary.md - Plain-language summary for anyone
  01-overview.md        - Project overview with concept mindmap
  02-features.md        - Feature catalog
  03-tech-stack.md      - Technologies and dependencies
  04-architecture.md    - Code organization with component diagram
  05-workflows.md       - User and system flows with diagrams
  06-data-model.md      - Entities and relationships with ER diagram
  07-getting-started.md - Developer onboarding guide
  08-open-questions.md  - Knowledge gaps to clarify
  09-project-anatomy.md - Config files, env vars, scripts, directory tree
  10-configuration-guide.md - Configuration recipes, operations, troubleshooting
  11-glossary.md        - Domain and technical glossary

Start reading from INDEX.md
```
