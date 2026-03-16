---
name: codebase-mapper
description: >
  Knowledge base for the codebase-mapper plugin. Provides writing guidelines, tone rules,
  and diagram conventions for generating human-readable project guides. Referenced by all
  codebase-mapper agents during document generation.
---

# Codebase Mapper Knowledge Base

## Purpose

Generate a human-readable project guide for unfamiliar codebases. Output is narrative, didactic material - not technical dumps or AI-oriented analysis. Target audience: a smart colleague on their first day.

## Output Structure

All output goes to `.codebase-map/` in the project root:

```
.codebase-map/
  INDEX.md                    # Entry point with navigable summary
  01-overview.md              # What is this project, who is it for
  02-features.md              # Functional capabilities
  03-tech-stack.md            # Technologies and dependencies
  04-architecture.md          # How code is organized, layers, components
  05-workflows.md             # Main user/system flows with diagrams
  06-data-model.md            # Data structures, entities, relationships
  07-getting-started.md       # Where to start working, key files, dev setup
  08-open-questions.md        # Gaps, unknowns, things to ask the team
  _internal/
    context-brief.md          # Phase 1 exploration output (internal reference)
```

## Core Principles

### Tone
- Narrative, conversational, didactic
- Write as if explaining to a smart colleague on their first day
- Progressive disclosure: big picture first, then details
- Honest about gaps - never fabricate or speculate

### Content Rules
- Every technical term gets a brief inline explanation on first use
- File paths always included - reference actual code paths for every claim
- Diagrams inline - Mermaid blocks embedded in documents, not separate files
- No AI boilerplate: no "In this document we will...", no "Let's dive in", no trailing summaries

### Diagram Standards
- Use Mermaid syntax exclusively
- Keep diagrams focused - max 15-20 nodes per diagram
- Split complex systems into multiple smaller diagrams
- Use descriptive node labels, not abbreviations
- Supported types: mindmap, flowchart, sequence, erDiagram, block-beta

## Agent Coordination

### Phase 1 - Explore
Single `codebase-explorer` agent reads the project and writes `_internal/context-brief.md`.

### Phase 2 - Write
Four parallel writer agents, each reading context-brief.md:
- `overview-writer` - 01-overview.md, 02-features.md (mindmap)
- `tech-writer` - 03-tech-stack.md, 04-architecture.md (component diagram)
- `flow-writer` - 05-workflows.md, 06-data-model.md (flowcharts, sequence, ER)
- `onboarding-writer` - 07-getting-started.md, 08-open-questions.md

### Phase 3 - Review
Single `guide-reviewer` agent reads all 8 documents, adds cross-references, fixes consistency, and produces INDEX.md.
