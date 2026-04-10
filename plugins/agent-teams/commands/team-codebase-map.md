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

The sequential map-codebase command runs 8 agents one-by-one. This team version parallelizes Phase 2:

```
Phase 1: Explore (sequential -- 1 agent)
  - codebase-explorer builds context brief
         |
         v
Phase 2: Write (parallel -- 6 agents)
  - overview-writer   --> 01-overview.md, 02-features.md
  - tech-writer       --> 03-tech-stack.md, 04-architecture.md
  - flow-writer       --> 05-workflows.md, 06-data-model.md
  - onboarding-writer --> 07-getting-started.md, 08-open-questions.md
  - ops-writer        --> 09-project-anatomy.md
  - config-writer     --> 10-configuration-guide.md
         |
         v
Phase 3: Review (sequential -- 1 agent)
  - guide-reviewer --> INDEX.md
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

**CHECKPOINT**: Present a brief summary of what the explorer found. Ask user to confirm before spawning 6 parallel writers.

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
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/03-tech-stack.md` and `.codebase-map/04-architecture.md`. Include a Mermaid component/layer diagram in the architecture doc. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `03-tech-stack.md`, `04-architecture.md`

**Agent 3: Flow Writer**
- `subagent_type`: `codebase-mapper:flow-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/05-workflows.md` and `.codebase-map/06-data-model.md`. Include Mermaid flowcharts and sequence diagrams for workflows, and an ER diagram for the data model. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `05-workflows.md`, `06-data-model.md`

**Agent 4: Onboarding Writer**
- `subagent_type`: `codebase-mapper:onboarding-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/07-getting-started.md` and `.codebase-map/08-open-questions.md`. Make getting-started practical with copy-pasteable commands. Make open-questions specific and actionable. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
- Output: `07-getting-started.md`, `08-open-questions.md`

**Agent 5: Ops Writer**
- `subagent_type`: `codebase-mapper:ops-writer`
- Task: "Read `.codebase-map/_internal/context-brief.md`, then write `.codebase-map/09-project-anatomy.md`. Document the annotated directory tree, every configuration file and what it controls, all environment variables, scripts and executables, startup sequence, and default ports/URLs. Verify claims by reading actual config files and grepping for env var usage. Follow the writing guidelines -- narrative tone, no AI boilerplate, file paths for every claim."
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
- Task: "Read all documents in `.codebase-map/` (01 through 10) and the context brief in `_internal/`. Review for terminology consistency, add cross-references between documents, fix any AI boilerplate in tone, validate Mermaid diagram syntax, and detect gaps. Apply edits directly. Then write `.codebase-map/INDEX.md` as the entry point with a navigable summary table and suggested reading paths."
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
