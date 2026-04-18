---
description: >
  Generate a human-readable codebase guide -- explores the project, writes 10 narrative documents with Mermaid diagrams, and produces an INDEX.md entry point.
  TRIGGER WHEN: the user asks to onboard to an unfamiliar project, generate a codebase tour, or produce a full narrative guide for new contributors.
  DO NOT TRIGGER WHEN: the user wants structured AST/dependency analysis (use /deep-dive-analysis:deep-dive-analysis) or just API docs (use /codebase-mapper:docs-create).
argument-hint: "[target-path]"
---

# Map Codebase

Generate a human-readable guide for an unfamiliar codebase. Produces 10 narrative documents with inline Mermaid diagrams, organized for progressive learning.

## Pre-flight

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

Spawn a single `codebase-explorer` agent:

**Agent task:**
> Explore this project and write a context brief to `.codebase-map/_internal/context-brief.md`. Follow your exploration strategy to understand what the project does, its tech stack, directory structure, key entry points, data model, and main workflows. Read actual code - do not guess from file names. Include file paths for every claim.

**Verify:** Check that `.codebase-map/_internal/context-brief.md` exists and is non-empty.

If the context brief is missing or empty, stop and report the error.

## Phase 1b: Interconnect Map (sequential)

Spawn a single `senior-review:semantic-interconnect-mapper` agent. This produces structured facts (contracts, invariants, domain rules, integration hot-spots) that the writer agents cite instead of paraphrasing code.

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

## Phase 2: Write (parallel - 6 agents)

Spawn all 6 writer agents simultaneously:

### Agent 1: `overview-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/01-overview.md` and `.codebase-map/02-features.md`. Include a Mermaid mindmap in the overview. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

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

**Verify:** Check that all 10 documents exist:
```bash
ls -la .codebase-map/0*.md .codebase-map/10*.md
```

If any documents are missing, report which ones failed and stop.

## Phase 3: Review (sequential)

Spawn a single `guide-reviewer` agent:

**Agent task:**
> Read all 10 documents in `.codebase-map/` (01 through 10) and the context brief in `_internal/`. If `.codebase-map/_internal/interconnect.md` exists, also read its `## Invariants` and `## Domain Rules` anchors, and use the `senior-review:defect-taxonomy` skill's `logic-integrity.md` reference to detect documentation-reality drift (docs that describe behavior contradicting documented invariants/contracts). Flag any drift as a "⚠ known inconsistency" note in the relevant doc and add a corresponding item to 08-open-questions.md. Review for terminology consistency, add cross-references between documents, fix any AI boilerplate in tone, validate Mermaid diagram syntax, and detect gaps. Apply edits directly. Then write `.codebase-map/INDEX.md` as the entry point with a navigable summary table and suggested reading paths.

**Verify:** Check that `.codebase-map/INDEX.md` exists.

## Completion

Print a summary:

```
Codebase map generated in .codebase-map/

  INDEX.md              - Entry point and navigation
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

Start reading from INDEX.md
```
