# Codebase Mapper Plugin

> Generate a human-readable guide for any unfamiliar codebase. The pipeline runs four phases (automated discovery, structured interconnect mapping, parallel document writing, cross-reference review) and produces 10 narrative documents with Mermaid diagrams.

## How it works

The `/map-codebase` command orchestrates a 4-phase pipeline:

1. **Phase 1 (Explore):** The `codebase-explorer` agent scans the project (README, configs, entry points, directory structure) and writes a context brief to `.codebase-map/_internal/context-brief.md`.
2. **Phase 1b (Interconnect Map):** The `senior-review:semantic-interconnect-mapper` agent reads the context brief and produces `.codebase-map/_internal/interconnect.md`: a structured map of contracts, invariants, domain rules, assumptions, integration hot-spots, and call graph. Writers cite these structured facts instead of paraphrasing code. Skipped gracefully (degraded mode) if the senior-review plugin is not installed.
3. **Phase 2 (Write):** Six writer agents run in parallel, each producing 1-2 documents from the context brief and (when present) the interconnect map.
4. **Phase 3 (Review):** The `guide-reviewer` agent reviews all documents for consistency, adds cross-references, detects documentation-reality drift against the interconnect map's invariants and domain rules, and produces `INDEX.md`.

**Output directory:** `.codebase-map/` in the project root, containing 10 numbered documents plus an index. Internal artifacts (context brief, interconnect map) live in `.codebase-map/_internal/`.

**Target audience:** A smart colleague on their first day.

---

## Agents

### Phase 1: Discovery

#### `codebase-explorer`

Explores an unfamiliar project to build a context brief for the writer agents.

| | |
|---|---|
| **Model** | `opus` |
| **Tools** | Read, Bash, Glob, Grep |
| **Produces** | `.codebase-map/_internal/context-brief.md` |

---

### Phase 2: Writers (run in parallel)

| Agent | Model | Produces | Content |
|-------|-------|----------|---------|
| `overview-writer` | `opus` | `01-overview.md`, `02-features.md` | Project overview with mindmap, feature catalog |
| `tech-writer` | `opus` | `03-tech-stack.md`, `04-architecture.md` | Technologies, dependencies, architectural layers with component diagrams |
| `flow-writer` | `opus` | `05-workflows.md`, `06-data-model.md` | User/system workflows with flowcharts, data structures with ER diagrams |
| `onboarding-writer` | `opus` | `07-getting-started.md`, `08-open-questions.md` | Developer onboarding steps, knowledge gaps |
| `ops-writer` | `opus` | `09-project-anatomy.md` | Config files, env vars, startup scripts, directory tree |
| `config-writer` | `opus` | `10-configuration-guide.md` | Environment setup, configuration scenarios, troubleshooting |

All writer agents use the tools: Read, Write, Glob, Grep.

---

### Phase 3: Review

#### `guide-reviewer`

Reviews all generated documents for consistency, adds cross-references, unifies tone, and produces `INDEX.md`. Flags gaps and contradictions.

| | |
|---|---|
| **Model** | `opus` |
| **Tools** | Read, Write, Edit, Glob, Grep |
| **Produces** | `INDEX.md` |

---

## Skills

### `codebase-mapper`

Knowledge base providing writing guidelines, tone rules, and diagram conventions for all codebase-mapper agents.

| | |
|---|---|
| **Invoke** | All codebase-mapper agents reference this automatically |
| **Use for** | Writing style, Mermaid diagram conventions, output structure rules |

---

## Commands

### `/map-codebase`

Generate a human-readable codebase guide.

```
/map-codebase                   # map current directory
/map-codebase ../other-project  # map a different project
```

**Pre-flight:** Checks for existing `.codebase-map/` directory and asks before overwriting.

**Output:** 10 narrative documents in `.codebase-map/` with an `INDEX.md` entry point.

---

## Standalone Documentation Agents

### `documentation-engineer`

Creates accurate technical documentation by analyzing existing code first. Uses bottom-up analysis with the shared writing guidelines.

| | |
|---|---|
| **Model** | `opus` |
| **Tools** | Read, Write, Edit, Glob, Grep, WebFetch, WebSearch |
| **Use for** | API docs, architecture docs, tutorials, documentation management |

---

### `doc-humanizer`

Rewrites existing documentation to follow human-centered writing guidelines. Transforms dense, AI-style docs into clear, scannable content.

| | |
|---|---|
| **Model** | `opus` |
| **Tools** | Read, Write, Edit, Glob, Grep |
| **Use for** | Improving readability of existing docs without changing content |

---

## Additional Commands

### `/docs-create`

Analyze code bottom-up and generate documentation -- API reference, architecture guides, or full project docs.

```
/docs-create src/api/ --api-only
```

---

### `/docs-maintain`

Audit and refactor existing documentation for accuracy and completeness.

```
/docs-maintain docs/
```

---

### `/humanize-docs`

Rewrite existing documentation for readability -- strips AI-style density and applies progressive disclosure.

```
/humanize-docs docs/
```

---

**Related:** [deep-dive-analysis](deep-dive-analysis.md) (structural analysis)
