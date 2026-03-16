---
description: "Generate a human-readable codebase guide - explores the project, writes 8 narrative documents with Mermaid diagrams, and produces an INDEX.md entry point"
argument-hint: "[target-path]"
---

# Map Codebase

Generate a human-readable guide for an unfamiliar codebase. Produces 8 narrative documents with inline Mermaid diagrams, organized for progressive learning.

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

## Phase 2: Write (parallel - 4 agents)

Spawn all 4 writer agents simultaneously:

### Agent 1: `overview-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/01-overview.md` and `.codebase-map/02-features.md`. Include a Mermaid mindmap in the overview. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 2: `tech-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/03-tech-stack.md` and `.codebase-map/04-architecture.md`. Include a Mermaid component/layer diagram in the architecture doc. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 3: `flow-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/05-workflows.md` and `.codebase-map/06-data-model.md`. Include Mermaid flowcharts and sequence diagrams for workflows, and an ER diagram for the data model. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

### Agent 4: `onboarding-writer`
> Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/07-getting-started.md` and `.codebase-map/08-open-questions.md`. Make getting-started practical with copy-pasteable commands. Make open-questions specific and actionable. Follow the writing guidelines - narrative tone, no AI boilerplate, file paths for every claim.

**Verify:** Check that all 8 documents exist:
```bash
ls -la .codebase-map/0*.md
```

If any documents are missing, report which ones failed and stop.

## Phase 3: Review (sequential)

Spawn a single `guide-reviewer` agent:

**Agent task:**
> Read all 8 documents in `.codebase-map/` (01 through 08) and the context brief in `_internal/`. Review for terminology consistency, add cross-references between documents, fix any AI boilerplate in tone, validate Mermaid diagram syntax, and detect gaps. Apply edits directly. Then write `.codebase-map/INDEX.md` as the entry point with a navigable summary table and suggested reading paths.

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

Start reading from INDEX.md
```
