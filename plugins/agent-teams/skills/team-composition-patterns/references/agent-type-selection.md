# Agent Type Selection Guide

Decision matrix for choosing the right `subagent_type` when spawning teammates.

## Decision Matrix

```
Does the teammate need to modify files?
|-- YES -> Does a marketplace specialist exist for this domain?
|          |-- YES -> Use the specialist (see table below)
|          |         Examples:
|          |         |-- Python code -> python-development:python-engineer
|          |         |-- Security review -> senior-review:security-auditor
|          |         |-- React frontend -> frontend:frontend-engineer
|          |         |-- Rust code -> tauri-development:rust-engineer
|          |         +-- Tests -> testing:test-writer
|          +-- NO -> Does it need a generic team role?
|                    |-- Code review -> agent-teams:team-reviewer
|                    |-- Bug investigation -> agent-teams:team-debugger
|                    |-- Feature building -> agent-teams:team-implementer
|                    +-- Team coordination -> agent-teams:team-lead
+-- NO -> Does it need deep codebase exploration?
          |-- YES -> Explore (or codebase-mapper:codebase-explorer)
          +-- NO -> Plan (for architecture/design tasks)

RULE: Always prefer a marketplace specialist over a generic team agent.
```

## Agent Type Comparison

### Generic Team Agents (fallbacks)

| Agent Type                   | Can Read | Can Write | Can Edit | Can Bash | Specialized        |
| ---------------------------- | -------- | --------- | -------- | -------- | ------------------ |
| general-purpose              | Yes      | Yes       | Yes      | Yes      | No                 |
| Explore                      | Yes      | No        | No       | No       | Search/explore     |
| Plan                         | Yes      | No        | No       | No       | Architecture       |
| agent-teams:team-lead        | Yes      | Yes       | Yes      | Yes      | Team orchestration |
| agent-teams:team-reviewer    | Yes      | Yes       | Yes      | Yes      | Code review        |
| agent-teams:team-debugger    | Yes      | Yes       | Yes      | Yes      | Bug investigation  |
| agent-teams:team-implementer | Yes      | Yes       | Yes      | Yes      | Feature building   |

### Specialized Marketplace Agents (preferred)

| Agent Type | Replaces | Domain |
| --- | --- | --- |
| `senior-review:security-auditor` | team-reviewer (security) | Adversarial security review |
| `senior-review:code-auditor` | team-reviewer (architecture) | Architecture + quality scoring |
| `senior-review:distributed-flow-auditor` | team-reviewer (distributed) | Cross-service flow analysis |
| `senior-review:ui-race-auditor` | team-reviewer (UI races) | Async rendering timing bugs |
| `platform-engineering:platform-reviewer` | team-reviewer (platform) | Cross-platform compliance |
| `react-development:react-performance-optimizer` | team-reviewer (React perf) | React 19 optimization |
| `python-development:python-engineer` | team-implementer (Python) | Python architecture + implementation |
| `python-development:python-test-engineer` | team-implementer (Python tests) | pytest TDD |
| `tauri-development:rust-engineer` | team-implementer (Rust) | Rust ownership, async, FFI |
| `frontend:frontend-engineer` | team-implementer (frontend) | Frontend design + implementation |
| `frontend:web-designer` | team-implementer (CSS/UI) | Styling, animations, design |
| `tauri-development:tauri-desktop` | team-implementer (Tauri) | Tauri IPC, WebView, bundling |
| `tauri-development:tauri-mobile` | team-implementer (mobile) | Tauri mobile plugins, signing |
| `testing:test-writer` | team-implementer (tests) | Language-agnostic test generation |
| `research:deep-researcher` | general-purpose (research) | Multi-source deep investigation |
| `codebase-mapper:codebase-explorer` | general-purpose (exploration) | Project understanding |
| `codebase-mapper:documentation-engineer` | general-purpose (docs) | Technical documentation |
| `app-analyzer:app-analyzer` | general-purpose (app analysis) | Android/web app navigation + UX |

## Common Mistakes

| Mistake                               | Why It Fails                   | Correct Choice                          |
| ------------------------------------- | ------------------------------ | --------------------------------------- |
| Using `Explore` for implementation    | Cannot write/edit files        | `general-purpose` or `team-implementer` |
| Using `Plan` for coding tasks         | Cannot write/edit files        | `general-purpose` or `team-implementer` |
| Using `general-purpose` for reviews   | No review structure/checklists | `team-reviewer`                         |
| Using `team-implementer` for research | Has tools but wrong focus      | `Explore` or `Plan`                     |

## When to Use Each

### general-purpose

- One-off tasks that don't fit specialized roles
- Tasks requiring unique tool combinations
- Ad-hoc scripting or automation

### Explore

- Codebase research and analysis
- Finding files, patterns, or dependencies
- Understanding architecture before planning

### Plan

- Designing implementation approaches
- Creating task decompositions
- Architecture review (read-only)

### team-lead

- Coordinating multiple teammates
- Decomposing work and managing tasks
- Synthesizing results from parallel work

### team-reviewer

- Focused code review on a specific dimension
- Producing structured findings with severity ratings
- Following dimension-specific checklists

### team-debugger

- Investigating a specific hypothesis about a bug
- Gathering evidence with file:line citations
- Reporting confidence levels and causal chains

### team-implementer

- Building code within file ownership boundaries
- Following interface contracts
- Coordinating at integration points
