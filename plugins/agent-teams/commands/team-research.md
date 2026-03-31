---
description: "Deep multi-source research with parallel investigators covering codebase, web, and domain-specific analysis"
argument-hint: "<question-or-topic> [--scope codebase|web|all] [--domain security|architecture|frontend|python|tauri|business] [--depth quick|standard|deep]"
---

# Team Research

Orchestrate a deep research investigation using multiple specialized researchers working in parallel. Each researcher covers a different angle (codebase, web sources, domain expertise) and findings are synthesized into a unified report.

## Skills to Load

Before starting, invoke these skills:
- `agent-teams:team-composition-patterns` -- team sizing and agent selection
- `agent-teams:team-communication-protocols` -- coordination between researchers

## Pre-flight Checks

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
2. Parse `$ARGUMENTS`:
   - `<question-or-topic>`: the research question, topic, or area to investigate
   - `--scope`: what to search -- `codebase` (local only), `web` (external only), `all` (both, default)
   - `--domain`: hint for selecting the domain expert -- `security`, `architecture`, `frontend`, `python`, `tauri`, `business`, or auto-detect
   - `--depth`: research depth -- `quick` (2 researchers), `standard` (3 researchers, default), `deep` (4 researchers with domain expert)

## Phase 1: Question Analysis

1. Analyze the research question to understand:
   - Is it about the local codebase, external knowledge, or both?
   - What domain does it touch? (security, architecture, frontend, backend, etc.)
   - What would a complete answer look like? (facts, comparisons, recommendations, code examples)
2. Break the question into sub-questions that can be investigated in parallel
3. Determine researcher count and roles based on `--depth`:
   - `quick`: 2 researchers (codebase + web)
   - `standard`: 3 researchers (codebase + web + docs/context)
   - `deep`: 4 researchers (codebase + web + docs + domain expert)

## Phase 2: Team Spawn

1. Use `Teammate` tool with `operation: "spawnTeam"`, team name: `research-{timestamp}`
2. Spawn researchers using specialized agents:

**Codebase Analyst** (always, unless `--scope web`):
- `subagent_type`: `research:deep-researcher`
- Focus: local code, git history, architecture, patterns, dependencies
- Tools: Grep, Glob, Read, Bash (for git log/blame)
- Prompt: "Search the local codebase for {sub-question}. Cite every finding with file:line."

**Web Researcher** (always, unless `--scope codebase`):
- `subagent_type`: `research:deep-researcher`
- Focus: documentation, articles, comparisons, best practices, release notes
- Tools: WebSearch, WebFetch, Read
- Prompt: "Search the web for {sub-question}. Cite every finding with source URL."

**Context Builder** (standard + deep):
- `subagent_type`: `codebase-mapper:codebase-explorer`
- Focus: build a context brief of the project/area under investigation
- Tools: Read, Glob, Grep, Bash
- Prompt: "Explore {area} to understand the project structure, entry points, and key patterns."

**Domain Expert** (deep only):
- Auto-select `subagent_type` based on `--domain` or auto-detected topic:

| Domain | Agent |
|--------|-------|
| security | `senior-review:security-auditor` |
| architecture | `senior-review:code-auditor` |
| frontend | `frontend:frontend-engineer` |
| python | `python-development:python-engineer` |
| tauri | `tauri-development:tauri-desktop` |
| business | `business:business-planner` |
| distributed | `senior-review:distributed-flow-auditor` |
| performance | `react-development:react-performance-optimizer` |
| general | `research:deep-researcher` (additional instance) |

- Focus: domain-specific analysis, validation of findings from other researchers
- Prompt: "As a {domain} expert, analyze {topic}. Validate or challenge findings from other researchers."

## Phase 3: Investigation

1. Create tasks with `TaskCreate` for each researcher:
   - Subject: "{role}: {sub-question}"
   - Description: Include scope, focus area, citation requirements, and output format
2. All researchers work in parallel (no blockedBy dependencies)
3. Monitor `TaskList` for completion
4. Track: "{completed}/{total} investigations complete"

## Phase 4: Synthesis

After all researchers report:

1. **Cross-reference findings**:
   - Do codebase findings align with web research?
   - Does the domain expert validate or contradict other findings?
   - Are there gaps that no researcher covered?

2. **Assess confidence**:
   - High: multiple researchers agree with strong evidence
   - Medium: some agreement, some gaps
   - Low: contradicting findings or insufficient evidence

3. **Present consolidated report**:

```
## Research Report: {question/topic}

### Summary
{2-3 sentence answer to the research question}

### Findings

#### From Codebase Analysis
- {finding 1} -- `file:line` citation
- {finding 2} -- `file:line` citation

#### From Web Research
- {finding 1} -- {URL} citation
- {finding 2} -- {URL} citation

#### From Context Analysis
- {architectural insight}
- {pattern observation}

#### Domain Expert Assessment
- {validation/contradiction of findings}
- {domain-specific recommendation}

### Confidence: {High/Medium/Low}

### Recommendations
1. {actionable recommendation}
2. {actionable recommendation}

### Open Questions
- {anything that needs further investigation}
```

## Phase 5: Cleanup

1. Send `shutdown_request` to all researchers
2. Call `Teammate` cleanup to remove team resources
