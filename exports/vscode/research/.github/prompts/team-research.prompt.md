---
description: Deep multi-source research with parallel investigators covering codebase, web, and domain-specific analysis.
argument-hint: <question-or-topic> [--scope codebase|web|all] [--domain <topic-domain>] [--depth quick|standard|deep]
agent: research-orchestrator
---

# Team Research

Orchestrate a deep research investigation using multiple specialized researchers working in parallel. Each researcher covers a different angle (codebase, web sources, domain expertise) and findings are synthesized into a unified report.

## Skills to Load

Before starting, invoke these skills:

## Pre-flight Checks

2. Parse `$ARGUMENTS`:
   - `<question-or-topic>`: the research question, topic, or area to investigate
   - `--scope`: what to search -- `codebase` (local only), `web` (external only), `all` (both, default)
   - `--domain`: free-form domain hint for the Domain Expert persona (e.g. `security`, `python`, `finance`, `nutrition`, `law`); auto-detected from the topic when omitted
   - `--depth`: research depth -- `quick` (2 researchers), `standard` (3 researchers, default), `deep` (4 researchers with domain expert)

## Phase 1: Question Analysis

1. Analyze the research question to understand:
   - Is it about the local codebase, external knowledge, or both? If it has no local-project component at all (a pure general-knowledge or web topic), treat `--scope` as `web` for the rest of the pipeline: no Codebase Analyst, no Context Builder.
   - What domain does it touch? (security, architecture, frontend, backend, etc.)
   - What would a complete answer look like? (facts, comparisons, recommendations, code examples)
2. Break the question into sub-questions that can be investigated in parallel
3. Determine researcher count and roles based on `--depth`:
   - `quick`: 2 researchers (codebase + web)
   - `standard`: 3 researchers (codebase + web + docs/context)
   - `deep`: 4 researchers (codebase + web + docs + domain expert)

## Phase 2: Dispatch

1. The team forms implicitly when the first researcher is spawned (no `TeamCreate` step; the team name is session-derived and any `team_name` passed to the `Agent` tool is ignored)
2. Spawn researchers using specialized agents:

**Codebase Analyst** (always, unless `--scope web`):
- agent: `deep-researcher`
- Focus: local code, git history, architecture, patterns, dependencies
- Tools: Grep, Glob, Read, Bash (for git log/blame)
- Prompt: "Search the local codebase for {sub-question}. Cite every finding with file:line."

**Web Researcher** (always, unless `--scope codebase`):
- agent: `deep-researcher`
- Focus: documentation, articles, comparisons, best practices, release notes
- Tools: WebSearch, WebFetch, Read
- Prompt: "Search the web for {sub-question}. Cite every finding with source URL."

**Context Builder** (standard + deep, only when the investigation touches a local project):
- agent: `codebase-explorer` (ships in the `codebase-mapper` bundle; skip this role and note it if that bundle is absent)
- Requires the `codebase-mapper` plugin (declared as an optional dependency): when it is not installed, skip this role and note it in the final report instead of spawning (the spawn would fail). Also skipped entirely when the effective scope is `web`.
- Focus: build a context brief of the project/area under investigation
- Tools: Read, Glob, Grep, Bash
- Prompt: "Explore {area} to understand the project structure, entry points, and key patterns."

**Domain Expert** (deep only):
- agent: `deep-researcher`, a dedicated instance carrying a domain persona in its prompt
- The domain comes from `--domain` or the topic detected in Phase 1. Any domain works: security, architecture, python, finance, law, nutrition, history. The persona lives in the prompt, not in a specialized agent, so this role never depends on other plugins being installed.
- Focus: domain-specific analysis, validation of findings from other researchers
- Prompt: "Act as a senior {domain} expert. Analyze {topic} strictly from the {domain} perspective. Validate or challenge the findings from the other researchers, citing evidence for every confirmation or objection."

## Phase 3: Investigation

1. Give each researcher an output path under `.research/` and require it to write there:
   - Subject: "{role}: {sub-question}"
   - Description: Include scope, focus area, citation requirements, and output format
2. All researchers work in parallel (no blockedBy dependencies)
3. Poll with `#search/fileSearch` until every expected output file exists. A researcher whose file never appears counts as failed: record it and synthesize from the rest.
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
2. Team resources are cleaned up automatically when the session ends; there is no `TeamDelete` step
