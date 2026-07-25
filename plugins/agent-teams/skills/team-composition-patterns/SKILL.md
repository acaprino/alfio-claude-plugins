---
name: team-composition-patterns
description: >
  Design optimal agent team compositions with sizing heuristics, preset
  configurations, and agent type selection. Use this skill when deciding how many
  agents to spawn for a task, when choosing between a review team versus a feature
  team versus a debug team, when selecting the correct subagent_type for each role
  to ensure agents have the tools they need, when configuring display modes (tmux,
  iTerm2, in-process) for a CI or local environment, or when building a custom
  team composition for a non-standard workflow such as a migration or security
  audit.
version: 1.1.1
---

# Team Composition Patterns

Best practices for composing multi-agent teams, selecting team sizes, choosing agent types, and configuring display modes for Claude Code's Agent Teams feature.

## When to Use This Skill

- Deciding how many teammates to spawn for a task
- Choosing between preset team configurations
- Selecting the right agent type (subagent_type) for each role
- Configuring teammate display modes (tmux, iTerm2, in-process)
- Building custom team compositions for non-standard workflows

## Team Sizing Heuristics

| Complexity   | Team Size | When to Use                                                 |
| ------------ | --------- | ----------------------------------------------------------- |
| Simple       | 1-2       | Single-dimension review, isolated bug, small feature        |
| Moderate     | 2-3       | Multi-file changes, 2-3 concerns, medium features           |
| Complex      | 3-4       | Cross-cutting concerns, large features, deep debugging      |
| Very Complex | 4-5       | Full-stack features, comprehensive reviews, systemic issues |

**Rule of thumb**: Start with the smallest team that covers all required dimensions. Adding teammates increases coordination overhead.

### Token cost multiplier

A team costs **3-10x the tokens of a single Claude** (typical ~7x for plan-mode workflows). Each teammate runs in its own context window and consumes tokens independently. Drivers of cost:

- Number of teammates (linear).
- Token budget per teammate (linear in exploration depth).
- Duration of unsupervised exploration (the largest variance source; unbounded scope explodes here).

Cheap-team recipe: Opus lead + Sonnet teammates, 2-3 teammates, scope-bounded spawn prompts, Haiku for any role where summarization is the main job. Cost killers: unbounded scope, no file ownership (forces rework), no task dependencies (forces rework on unstable foundations), no `TaskCompleted` quality gates (forces rework on broken code).

### Hard limits (as of 2026-05)

These are enforced by the harness and cannot be worked around with prompt engineering:

- **One team per lead.** A lead can only manage one team at a time. Clean up before creating the next.
- **No nested teams.** Teammates cannot spawn their own teams or further teammates.
- **No nested subagents.** A teammate spawned with `Agent` cannot itself call `Agent` to spawn a sub-subagent.
- **Lead is fixed for the team's lifetime.** No promotion, no leadership transfer.
- **Permissions set at spawn.** Per-teammate at spawn time is not supported.
- **No session resumption for in-process teammates.** `/resume` and `/rewind` do not restore them.
- **Broadcast removed.** Send one `message` per recipient by name.

Reference: `docs/references/agent-teams-best-practices.md` § Hard limits.

## Preset Team Compositions

### Review Team

- **Size**: 3 reviewers
- **Agents**: prefer specialized `senior-review:security-auditor` + `senior-review:code-auditor` + a third dimension matching the diff (e.g. `senior-review:ui-race-auditor` for frontend changes, `senior-review:distributed-flow-auditor` for cross-service changes). Fall back to `agent-teams:team-reviewer` only when no specialized agent fits the dimension.
- **Default dimensions**: security, code quality (architecture + patterns + scoring), and one context-driven dimension
- **Use when**: Code changes need multi-dimensional quality assessment. For pipeline reviews driven by `/team-review`, the command auto-selects specialized agents based on the diff and adds Phase 1 context (deep-dive + interconnect map) automatically.

### Debug Team

- **Size**: 3 investigators
- **Agents**: 3x `team-debugger`
- **Default hypotheses**: 3 competing hypotheses
- **Use when**: Bug has multiple plausible root causes

### Feature Team

- **Size**: 3 (1 lead + 2 implementers)
- **Agents**: 1x `team-lead` + 2x `team-implementer`
- **Use when**: Feature can be decomposed into parallel work streams

### Fullstack Team

- **Size**: 4 (1 lead + 3 implementers)
- **Agents**: 1x `team-lead` + 1x frontend `team-implementer` + 1x backend `team-implementer` + 1x test `team-implementer`
- **Use when**: Feature spans frontend, backend, and test layers

### Research Team

- **Size**: 3 researchers
- **Agents**: 3x `research:deep-researcher` (for systematic multi-source investigation) or `general-purpose` fallback; use `research:quick-searcher` for single-fact lookups
- **Default areas**: Each assigned a different research question, module, or topic
- **Capabilities**: Codebase search (Grep, Glob, Read), web search (WebSearch, WebFetch)
- **Use when**: Need to understand a codebase, research libraries, compare approaches, or gather information from code and web sources in parallel

### Security Team

- **Size**: 4 reviewers
- **Agents**: prefer `senior-review:security-auditor` for OWASP / auth / secrets, `platform-engineering:platform-reviewer` for client-side hardening (CSP, token storage, secrets in bundles), `senior-review:distributed-flow-auditor` for cross-service auth flows, and `codebase-cleanup:deps-audit` (or `senior-review:cleanup-auditor`) for dependencies / supply chain. Fall back to `agent-teams:team-reviewer` only if a dimension has no specialized agent.
- **Default dimensions**: OWASP / vulnerabilities, platform / client-side security, cross-service auth, dependencies / supply chain
- **Use when**: Comprehensive security audit covering multiple attack surfaces.

### Migration Team

- **Size**: 4 (1 lead + 2 implementers + 1 reviewer)
- **Agents**: 1x `team-lead` + 2x `team-implementer` + 1x `team-reviewer`
- **Use when**: Large codebase migration (framework upgrade, language port, API version bump) requiring parallel work with correctness verification

### Deep Search Team

- **Size**: 2-4 (depends on depth level)
- **Agents**: 2-3x `research:deep-researcher` + optional domain expert (auto-selected)
- **Use when**: Complex questions requiring systematic coverage across codebase, web, and domain expertise

### Docs Team

- **Size**: 3 (explorer + writer + verifier)
- **Agents**: 1x `codebase-mapper:codebase-explorer` + 1x `codebase-mapper:documentation-engineer` + 1x `senior-review:code-auditor`
- **Use when**: Creating or overhauling project documentation from code analysis

### App Analysis Team

- **Size**: 2 (mapper + researcher)
- **Agents**: 1x `app-analyzer:app-analyzer` + 1x `research:deep-researcher`
- **Use when**: Competitive app analysis, navigation mapping, feature benchmarking

### Tauri Team

- **Size**: 4 (1 lead + 3 specialists)
- **Agents**: 1x `team-lead` + 1x `tauri-development:rust-engineer` + 1x `typescript-development:typescript-engineer` + 1x `tauri-development:tauri-desktop`
- **Use when**: Building or optimizing Tauri v2 desktop/mobile applications

## Agent Type Selection

When spawning teammates with the `Agent` tool, choose `subagent_type` based on what tools the teammate needs:

| Agent Type                     | Tools Available                           | Use For                                                    |
| ------------------------------ | ----------------------------------------- | ---------------------------------------------------------- |
| `general-purpose`              | All tools (Read, Write, Edit, Bash, etc.) | Implementation, debugging, any task requiring file changes |
| `Explore`                      | Read-only tools (Read, Grep, Glob)        | Research, code exploration, analysis                       |
| `Plan`                         | Read-only tools                           | Architecture planning, task decomposition                  |
| `agent-teams:team-reviewer`    | Read/Write/search/Bash plus TaskList/TaskGet/TaskUpdate/SendMessage | Code review with structured findings                       |
| `agent-teams:team-debugger`    | Read/Write/search/Bash plus TaskList/TaskGet/TaskUpdate/SendMessage | Hypothesis-driven investigation                            |
| `agent-teams:team-implementer` | Read/Write/Edit/search/Bash plus team tools | Building features within file ownership boundaries         |
| `agent-teams:team-lead`        | Read/search/Bash plus Agent Teams coordination tools (Agent, TeamCreate, TeamDelete, TaskCreate/List/Get/Update, SendMessage) | Team orchestration and coordination                        |

**Key distinction**: Read-only agents (Explore, Plan) cannot modify files. Never assign implementation tasks to read-only agents.

## Display Mode Configuration

Configure in `~/.claude/settings.json`:

```json
{
  "teammateMode": "tmux"
}
```

| Mode           | Behavior                       | Best For                                          |
| -------------- | ------------------------------ | ------------------------------------------------- |
| `"tmux"`       | Split panes (auto-detects tmux or iTerm2's `it2` CLI) | Development workflows, monitoring multiple agents |
| `"in-process"` | All teammates in main terminal, Shift+Down to cycle | Simple tasks, CI/CD environments, any terminal without tmux |
| `"auto"` (default) | Split panes if already in tmux, otherwise in-process | Most users; no manual choice needed |

Note: `"iterm2"` is not a separate setting. Split-pane mode uses tmux first and falls back to iTerm2's `it2` CLI automatically. VS Code's integrated terminal, Windows Terminal, and Ghostty do not support split panes -- they always use in-process mode.

## Custom Team Guidelines

When building custom teams:

1. **Every team needs a coordinator** -- Either designate a `team-lead` or have the user coordinate directly
2. **Match roles to agent types** -- Use specialized agents (reviewer, debugger, implementer) when available
3. **Avoid duplicate roles** -- Two agents doing the same thing wastes resources
4. **Define boundaries upfront** -- Each teammate needs clear ownership of files or responsibilities
5. **Keep it small** -- 2-4 teammates is the sweet spot; 5+ requires significant coordination overhead

## Troubleshooting

**A teammate was spawned as `Explore` but needs to write files.**
`Explore` and `Plan` are read-only agents. Change the `subagent_type` to `general-purpose` or an appropriate specialized agent type. Never assign implementation tasks to read-only agents.

**The team is growing too large and coordination is slowing everything down.**
Each additional teammate adds communication overhead. Consolidate roles: can one agent cover two dimensions? A 4-person team doing 6 independent tasks is usually better served by 3 agents covering 2 tasks each.

**tmux mode is not showing panes.**
Ensure tmux is installed and a session is already running before spawning teammates. The `in-process` mode works without tmux and is suitable for CI or scripted environments.

**Two reviewers are flagging the same issues.**
The review dimensions overlap. Redefine each reviewer's focus area: one on correctness/logic, one on security, one on performance/scalability. Overlapping coverage wastes tokens and produces duplicate findings.

**A `team-lead` is spawning teammates but they are not receiving tasks.**
Verify that the lead is using the Agent tool to spawn teammates and passing complete context in the prompt. Teammates start fresh with no prior conversation history -- they need all relevant information in their initial prompt.

## Related Skills

- [parallel-feature-development](../parallel-feature-development/SKILL.md) -- Decompose work streams and assign file ownership once the team is composed
- [team-communication-protocols](../team-communication-protocols/SKILL.md) -- Establish messaging norms and shutdown procedures for the assembled team
