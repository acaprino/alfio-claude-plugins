---
description: "Parallel codebase mapping pipeline -- explore project, run 6 writers in parallel, then review and produce INDEX.md"
argument-hint: "[target-path] [--skip-review] [--writers N]"
---

# Team Codebase Map

Orchestrate the codebase-mapper pipeline using parallel agent teams. Phase 2 runs 6 writers simultaneously, dramatically reducing total documentation time.

## Skills to Load

Before starting, invoke these skills:
- `codebase-mapper:codebase-mapper` -- writing guidelines, tone rules, diagram conventions
- `agent-teams:task-coordination-strategies` -- phased task dependencies
- `agent-teams:team-communication-protocols` -- coordination between writers

## Pre-flight Checks

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
2. Parse `$ARGUMENTS`:
   - `[target-path]`: project root to map (default: current working directory)
   - `--skip-review`: skip Phase 3 reviewer pass
   - `--writers N`: limit parallel writers (default: 6, min: 1, max: 6)

## Pipeline Overview

The sequential map-codebase command runs agents one-by-one. This team version parallelizes Phase 2:

```
Phase 1: Explore (sequential -- 1 agent)
  - codebase-explorer builds context brief
         |
         v
Phase 1b: Interconnect Map (sequential -- 1 agent)
  - semantic-interconnect-mapper builds structured facts
    (contracts, invariants, domain rules, integration hot-spots)
         |
         v
Phase 2: Write (parallel -- 6 agents)
  - overview-writer   --> 01-overview.md, 02-features.md
  - tech-writer       --> 03-tech-stack.md, 04-architecture.md      [reads interconnect]
  - flow-writer       --> 05-workflows.md, 06-data-model.md         [reads interconnect]
  - onboarding-writer --> 07-getting-started.md, 08-open-questions.md
  - ops-writer        --> 09-project-anatomy.md                      [reads interconnect]
  - config-writer     --> 10-configuration-guide.md
         |
         v
Phase 3: Review (sequential -- 1 agent)
  - guide-reviewer --> INDEX.md                                      [drift detection]
```

## Phase 1: Explore (Sequential)

Spawn a single explorer agent:

1. Create output directories:
   ```bash
   mkdir -p .codebase-map/_internal
   ```

2. Spawn `codebase-mapper:codebase-explorer`:
   - Task: "Explore the project at {target-path} and write a context brief to `.codebase-map/_internal/context-brief.md`. Follow your exploration strategy to understand what the project does, its tech stack, directory structure, key entry points, data model, and main workflows. Read actual code -- do not guess from file names. Include file paths for every claim."
   - Wait for completion

3. Verify `.codebase-map/_internal/context-brief.md` exists and is non-empty
4. If missing or empty, stop and report the error

**CHECKPOINT**: Present a brief summary of what the explorer found. Ask user to confirm before continuing to Phase 1b.

## Phase 1b: Interconnect Map (Sequential)

Spawn a single `senior-review:semantic-interconnect-mapper` agent:

1. Task:
   > Build the interconnect map for this project.
   >
   > Primary context source: `.codebase-map/_internal/context-brief.md` (produced by codebase-explorer).
   > Target files: the whole project (infer scope from the context brief's directory structure).
   > Output path: `.codebase-map/_internal/interconnect.md`
   >
   > Produce the full structured map following your agent definition: Call Graph (2-3 hop for public entry points), Contracts (formal / structural / implicit), Invariants, Domain Rules, Assumptions (verified / documented / unverified), Integration Hot-Spots, Change Impact Radius, Reviewer Hints.
   >
   > Every claim must cite file:line. No recommendations, no fixes. Empty sections are acceptable if nothing applies.

2. Wait for completion
3. Verify `.codebase-map/_internal/interconnect.md` exists and contains the required anchors
4. If missing, continue to Phase 2 in degraded mode (writers use only the context brief) -- log a warning

## Phase 2: Parallel Write Team (6 agents)

Spawn a write team with 6 specialists working simultaneously:

1. Use `Teammate` tool with `operation: "spawnTeam"`, team name: `codebase-map-writers-{timestamp}`
2. Spawn all 6 agents in parallel:

**Agent 1: Overview Writer**
- `subagent_type`: `codebase-mapper:overview-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/01-overview.md` and `.codebase-map/02-features.md`. Include a Mermaid mindmap in the overview. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `01-overview.md`, `02-features.md`

**Agent 2: Tech Writer**
- `subagent_type`: `codebase-mapper:tech-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/03-tech-stack.md` and `.codebase-map/04-architecture.md`. Include a Mermaid component/layer diagram in the architecture doc. If `.codebase-map/_internal/interconnect.md` exists, read its `## Call Graph`, `## Contracts`, and `## Integration Hot-Spots` anchors and cite those structured facts in the architecture doc instead of paraphrasing code. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `03-tech-stack.md`, `04-architecture.md`

**Agent 3: Flow Writer**
- `subagent_type`: `codebase-mapper:flow-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/05-workflows.md` and `.codebase-map/06-data-model.md`. Include Mermaid flowcharts and sequence diagrams for workflows, and an ER diagram for the data model. If `.codebase-map/_internal/interconnect.md` exists, read its `## Invariants` (especially temporal), `## Integration Hot-Spots`, and `## Domain Rules` anchors and encode those facts directly in sequence diagrams and data-flow narratives. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `05-workflows.md`, `06-data-model.md`

**Agent 4: Onboarding Writer**
- `subagent_type`: `codebase-mapper:onboarding-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/07-getting-started.md` and `.codebase-map/08-open-questions.md`. Make getting-started practical with copy-pasteable commands. Make open-questions specific and actionable. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `07-getting-started.md`, `08-open-questions.md`

**Agent 5: Ops Writer**
- `subagent_type`: `codebase-mapper:ops-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/09-project-anatomy.md`. Document the annotated directory tree, every configuration file and what it controls, all environment variables, scripts and executables, startup sequence, and default ports/URLs. If `.codebase-map/_internal/interconnect.md` exists, read its `## Integration Hot-Spots` anchor (rows of type Env/config) and use it as the authoritative list of env vars and config files. Verify claims by reading actual config files and grepping for env var usage. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `09-project-anatomy.md`

**Agent 6: Config Writer**
- `subagent_type`: `codebase-mapper:config-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/10-configuration-guide.md`. Write a practical guide covering configuration walkthrough, environment profiles, configuration recipes, common day-to-day operations with exact commands, troubleshooting with real error messages from the codebase, and a quick-reference cheat sheet. Verify by reading actual config files and grepping for error messages. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `10-configuration-guide.md`

3. Monitor `TaskList` for completion
4. Track: "{completed}/6 writers complete"

**Verify:** Check that all 10 documents exist:
```bash
ls -la .codebase-map/0*.md .codebase-map/10*.md
```

If any documents are missing, report which ones failed. Continue to Phase 3 with available documents.

## Phase 3: Review (Sequential)

**Skip if** `--skip-review`.

Spawn a single reviewer agent:

- `subagent_type`: `codebase-mapper:guide-reviewer`
- Task: "Read all documents in `.codebase-map/` (01 through 10) and the context brief in `_internal/`. If `.codebase-map/_internal/interconnect.md` exists, also read its `## Invariants` and `## Domain Rules` anchors and use the `senior-review:defect-taxonomy` skill's `logic-integrity.md` reference to detect documentation-reality drift. Flag any drift as a '⚠ known inconsistency' callout in the affected doc and add a corresponding item to 08-open-questions.md. Review for terminology consistency, add cross-references between documents, fix any AI boilerplate in tone, validate Mermaid diagram syntax, and detect gaps. Apply edits directly. Then write `.codebase-map/INDEX.md` as the entry point with a navigable summary table and suggested reading paths."
- Wait for completion

**Verify:** Check that `.codebase-map/INDEX.md` exists.

## Phase 4: Cleanup & Summary

1. Send `shutdown_request` to all remaining teammates
2. Call `Teammate` cleanup to remove team resources
3. Present final summary:

```
Codebase map generated in .codebase-map/ (Team Mode)

## Parallel Execution Summary
- Phase 1 (Explore): 1 agent built context brief
- Phase 2 (Write): 6 agents ran in parallel (saved ~80% writing time)
- Phase 3 (Review): 1 agent unified tone and cross-references

## Output Files
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
