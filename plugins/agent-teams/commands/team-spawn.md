---
description: "Spawn an agent team using presets (review, debug, feature, fullstack, research, deep-search, security, migration, docs, codebase-mapper, app-analysis, tauri, ui-studio) or custom composition"
argument-hint: "<preset|custom> [--name team-name] [--members N] [--delegate]"
---

# Team Spawn

Spawn a multi-agent team using preset configurations or custom composition. Handles team creation, teammate spawning, and initial task setup.

## Pre-flight Checks

1. Verify that `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set:
   - If not set, inform the user: "Agent Teams requires the experimental feature flag. Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your environment."
   - Stop execution if not enabled

2. Parse arguments from `$ARGUMENTS`:
   - First positional arg: preset name or "custom"
   - `--name`: team name (default: auto-generated from preset)
   - `--members N`: override default member count
   - `--delegate`: enter delegation mode after spawning

## Phase 1: Team Configuration

### Preset Teams

If a preset is specified, use these configurations:

**`review`** -- Multi-dimensional code review using specialized reviewers (default: 3 members)

- Spawn specialized agents per dimension (prefer marketplace experts over generic team-reviewer):
  - Security: `senior-review:security-auditor`
  - Architecture: `senior-review:code-auditor`
  - Performance: `react-development:react-performance-optimizer` (React) or `agent-teams:team-reviewer` (general)
- Team name default: `review-team`

**`debug`** -- Competing hypotheses debugging (default: 3 members)

- Spawn 3 `agent-teams:team-debugger` agents, each assigned a different hypothesis
- Each debugger can sub-delegate to `research:deep-researcher` for evidence gathering
- Team name default: `debug-team`

**`feature`** -- Parallel feature development (default: 3 members)

- Spawn 1 `agent-teams:team-lead` + 2 specialized implementers
- Lead auto-selects implementer agents based on codebase context:
  - Python: `python-development:python-engineer`
  - React/frontend: `frontend:frontend-engineer`
  - Rust: `tauri-development:rust-engineer`
  - General: `agent-teams:team-implementer`
- Team name default: `feature-team`

**`fullstack`** -- Full-stack development with specialized layer agents (default: 4 members)

- Spawn 1 `agent-teams:team-lead` + 3 layer-specific agents:
  - Frontend: `frontend:frontend-engineer` or `frontend:web-designer`
  - Backend: `python-development:python-engineer` or `agent-teams:team-implementer`
  - Tests: `testing:test-writer` or `python-development:python-test-engineer`
- Team name default: `fullstack-team`

**`research`** -- Parallel codebase, web, and documentation research (default: 3 members)

- Spawn specialized researchers:
  - Codebase: `research:deep-researcher` (multi-source investigation)
  - Web: `research:quick-searcher` (fast lookups) or `general-purpose`
  - Docs: `codebase-mapper:codebase-explorer` (project understanding)
- Team name default: `research-team`

**`deep-search`** -- Deep multi-source investigation with iterative refinement (default: 4 members)

- Spawn a coordinated research team for complex questions requiring systematic coverage:
  - Lead researcher: `research:deep-researcher` (orchestrates the investigation, cross-references findings)
  - Codebase analyst: `research:deep-researcher` (focused on local code, git history, architecture)
  - Web researcher: `research:deep-researcher` (focused on web sources, docs, articles, comparisons)
  - Domain expert: auto-selected based on topic:
    - Security topic: `senior-review:security-auditor`
    - Architecture topic: `senior-review:code-auditor`
    - Frontend topic: `frontend:frontend-engineer`
    - Python topic: `python-development:python-engineer`
    - Tauri topic: `tauri-development:tauri-desktop`
    - Business topic: `business:business-planner`
    - General topic: `codebase-mapper:codebase-explorer`
- Each researcher covers a different angle and reports structured findings with citations
- Lead synthesizes all findings into a unified report with confidence levels
- Team name default: `deep-search-team`

**`security`** -- Comprehensive security audit using specialized agents (default: 4 members)

- Spawn specialized security reviewers:
  - OWASP/vulnerabilities: `senior-review:security-auditor`
  - Platform compliance: `platform-engineering:platform-reviewer`
  - Distributed flows: `senior-review:distributed-flow-auditor`
  - Auth/secrets: `senior-review:security-auditor` (second instance, different scope)
- Load `senior-review:defect-taxonomy` skill for CWE/OWASP classification
- Team name default: `security-team`

**`migration`** -- Codebase migration or large refactor (default: 4 members)

- Spawn 1 `agent-teams:team-lead` (coordination + migration plan)
- 2 specialized implementers (auto-selected by codebase language)
- 1 `senior-review:code-auditor` (verify migration correctness)
- Team name default: `migration-team`

**`docs`** -- Parallel documentation generation (default: 3 members)

- Spawn documentation specialists:
  - Explorer: `codebase-mapper:codebase-explorer` (build context brief)
  - Tech writer: `codebase-mapper:documentation-engineer` (write docs)
  - Reviewer: `senior-review:code-auditor` (verify accuracy)
- Team name default: `docs-team`

**`codebase-mapper`** -- Parallel codebase documentation with phased pipeline (default: 8 members across 3 phases)

- Runs in three sequential phases (see `/team-codebase-map` for full pipeline):
  - **Phase 1** (1 agent, sequential): `codebase-mapper:codebase-explorer` builds context brief
  - **Phase 2** (6 agents, parallel):
    - Overview: `codebase-mapper:overview-writer`
    - Tech stack: `codebase-mapper:tech-writer`
    - Workflows: `codebase-mapper:flow-writer`
    - Onboarding: `codebase-mapper:onboarding-writer`
    - Ops: `codebase-mapper:ops-writer`
    - Config: `codebase-mapper:config-writer`
  - **Phase 3** (1 agent, sequential): `codebase-mapper:guide-reviewer` reviews all docs and produces INDEX.md
- Team name default: `codebase-mapper-team`
- **Shortcut**: Use `/team-codebase-map` for the full orchestrated pipeline

**`app-analysis`** -- Competitive app analysis (default: 3 members)

- Spawn analysis specialists:
  - App mapper: `app-analyzer:app-analyzer` (navigation + UX audit)
  - Researcher: `research:deep-researcher` (competitive intelligence)
  - Designer: `frontend:web-designer` (design system extraction)
- Team name default: `app-analysis-team`

**`tauri`** -- Tauri desktop/mobile development (default: 4 members)

- Spawn Tauri specialists:
  - Lead: `agent-teams:team-lead`
  - Rust backend: `tauri-development:rust-engineer`
  - Frontend: `frontend:frontend-engineer` or `react-development:react-performance-optimizer`
  - Platform: `tauri-development:tauri-desktop` or `tauri-development:tauri-mobile`
- Team name default: `tauri-team`

**`ui-studio`** -- Parallel UI design and build pipeline (default: 3+3 members in two phases)

- Runs in two parallel waves (see `/team-design` for full pipeline):
  - **Design wave** (3 parallel agents):
    - Design direction: `frontend:web-designer`
    - Layout: `frontend:ui-layout-designer`
    - UX patterns: `frontend:web-designer`
  - **Polish wave** (3-4 parallel agents):
    - UI polish: `frontend:web-designer`
    - Performance: `react-development:react-performance-optimizer`
    - Code review: `senior-review:code-auditor`
    - Security: `senior-review:security-auditor` (optional)
- Sequential phases between waves: brainstorm, component architecture, plan, execute
- Team name default: `ui-studio-team`
- **Shortcut**: Use `/team-design` for the full orchestrated pipeline

### Custom Composition

If "custom" is specified:

1. Use AskUserQuestion to prompt for team size (2-5 members)
2. For each member, ask for role selection: team-lead, team-reviewer, team-debugger, team-implementer
3. Ask for team name if not provided via `--name`

## Skills to Load

Before spawning, invoke the relevant skills for the preset to inform team configuration:

| Preset | Skills to reference |
|--------|-------------------|
| review | `agent-teams:multi-reviewer-patterns`, `senior-review:defect-taxonomy` |
| debug | `agent-teams:parallel-debugging`, `deep-dive-analysis:deep-dive-analysis` |
| feature | `agent-teams:parallel-feature-development`, `agent-teams:task-coordination-strategies`, `ai-tooling:writing-plans` |
| fullstack | `agent-teams:parallel-feature-development`, `agent-teams:task-coordination-strategies`, `ai-tooling:writing-plans` |
| research | `agent-teams:team-composition-patterns` |
| deep-search | `agent-teams:team-composition-patterns`, `agent-teams:team-communication-protocols` |
| security | `agent-teams:multi-reviewer-patterns`, `senior-review:defect-taxonomy`, `platform-engineering:platform-engineering` |
| migration | `agent-teams:parallel-feature-development`, `agent-teams:task-coordination-strategies`, `ai-tooling:writing-plans` |
| docs | `codebase-mapper:codebase-mapper`, `agent-teams:team-composition-patterns` |
| codebase-mapper | `codebase-mapper:codebase-mapper`, `agent-teams:task-coordination-strategies`, `agent-teams:team-communication-protocols` |
| app-analysis | `agent-teams:team-composition-patterns` |
| tauri | `agent-teams:parallel-feature-development`, `tauri-development:tauri`, `agent-teams:task-coordination-strategies` |
| ui-studio | `ai-tooling:brainstorming`, `frontend:frontend`, `agent-teams:parallel-feature-development`, `agent-teams:team-communication-protocols` |

## Phase 2: Team Creation

1. Use the `Teammate` tool with `operation: "spawnTeam"` to create the team
2. For each team member, use the `Task` tool with:
   - `team_name`: the team name
   - `name`: descriptive member name (e.g., "security-reviewer", "hypothesis-1")
   - `subagent_type`: the specialized agent type matching the role (see table below)
   - `prompt`: Role-specific instructions referencing the appropriate agent definition

### Subagent Types by Preset

Use the **most specialized agent** available. The team-lead's Ecosystem Integration section has the full mapping. Key defaults:

| Preset | Role | Default subagent_type | Preferred specialist (when applicable) |
|--------|------|-----------------------|----------------------------------------|
| review | security | `agent-teams:team-reviewer` | `senior-review:security-auditor` |
| review | architecture | `agent-teams:team-reviewer` | `senior-review:code-auditor` |
| review | performance | `agent-teams:team-reviewer` | `react-development:react-performance-optimizer` (React) |
| debug | investigator | `agent-teams:team-debugger` | -- |
| feature | lead | `agent-teams:team-lead` | -- |
| feature | implementer | `agent-teams:team-implementer` | `python-development:python-engineer`, `frontend:frontend-engineer`, `tauri-development:rust-engineer` |
| fullstack | lead | `agent-teams:team-lead` | -- |
| fullstack | frontend | `agent-teams:team-implementer` | `frontend:frontend-engineer` |
| fullstack | backend | `agent-teams:team-implementer` | `python-development:python-engineer` |
| fullstack | tests | `agent-teams:team-implementer` | `testing:test-writer` |
| research | researcher | `general-purpose` | `research:deep-researcher`, `codebase-mapper:codebase-explorer` |
| deep-search | lead researcher | -- | `research:deep-researcher` |
| deep-search | codebase analyst | -- | `research:deep-researcher` |
| deep-search | web researcher | -- | `research:deep-researcher` |
| deep-search | domain expert | -- | Auto-detect from topic |
| security | OWASP | `agent-teams:team-reviewer` | `senior-review:security-auditor` |
| security | platform | `agent-teams:team-reviewer` | `platform-engineering:platform-reviewer` |
| security | distributed | `agent-teams:team-reviewer` | `senior-review:distributed-flow-auditor` |
| migration | lead | `agent-teams:team-lead` | -- |
| migration | implementer | `agent-teams:team-implementer` | Auto-detect from codebase |
| migration | verifier | `agent-teams:team-reviewer` | `senior-review:code-auditor` |
| docs | explorer | -- | `codebase-mapper:codebase-explorer` |
| docs | writer | -- | `codebase-mapper:documentation-engineer` |
| docs | verifier | -- | `senior-review:code-auditor` |
| codebase-mapper | explorer | -- | `codebase-mapper:codebase-explorer` |
| codebase-mapper | overview | -- | `codebase-mapper:overview-writer` |
| codebase-mapper | tech | -- | `codebase-mapper:tech-writer` |
| codebase-mapper | flow | -- | `codebase-mapper:flow-writer` |
| codebase-mapper | onboarding | -- | `codebase-mapper:onboarding-writer` |
| codebase-mapper | ops | -- | `codebase-mapper:ops-writer` |
| codebase-mapper | config | -- | `codebase-mapper:config-writer` |
| codebase-mapper | reviewer | -- | `codebase-mapper:guide-reviewer` |
| app-analysis | mapper | -- | `app-analyzer:app-analyzer` |
| app-analysis | researcher | -- | `research:deep-researcher` |
| app-analysis | designer | -- | `frontend:web-designer` |
| tauri | lead | `agent-teams:team-lead` | -- |
| tauri | rust | -- | `tauri-development:rust-engineer` |
| tauri | frontend | -- | `frontend:frontend-engineer` |
| tauri | platform | -- | `tauri-development:tauri-desktop` or `tauri-development:tauri-mobile` |
| ui-studio | design direction | -- | `frontend:web-designer` |
| ui-studio | layout | -- | `frontend:ui-layout-designer` |
| ui-studio | UX patterns | -- | `frontend:web-designer` |
| ui-studio | polish | -- | `frontend:web-designer` |
| ui-studio | performance | -- | `react-development:react-performance-optimizer` |
| ui-studio | review | -- | `senior-review:code-auditor` |
| ui-studio | security | -- | `senior-review:security-auditor` |

## Phase 3: Initial Setup

1. Use `TaskCreate` to create initial placeholder tasks for each teammate
2. Display team summary:
   - Team name
   - Member names and roles
   - Display mode (tmux/iTerm2/in-process)
3. If `--delegate` flag is set, transition to delegation mode

## Output

Display a formatted team summary:

```
Team "{team-name}" spawned successfully!

Members:
  - {member-1-name} ({role})
  - {member-2-name} ({role})
  - {member-3-name} ({role})

Use /team-status to monitor progress
Use /team-delegate to assign tasks
Use /team-shutdown to clean up
```
