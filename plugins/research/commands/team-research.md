---
description: "Deep web research with parallel investigators covering complementary source angles plus domain-specific analysis"
argument-hint: "<question-or-topic> [--domain <topic-domain>] [--depth quick|standard|deep]"
---

## Prerequisites

This command requires the upstream `agent-teams` plugin from `wshobson/agents` (MIT, Seth Hobson). It provides the `agent-teams:team-composition-patterns` and `agent-teams:team-communication-protocols` skills used below. Install it first:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

The team infrastructure itself (teammate spawning via the `Agent` tool, plus TaskCreate, TaskList) is a native Claude Code feature and needs no plugin, but it is experimental and OFF by default: it requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, best set persistently in the `env` block of `~/.claude/settings.json`. As of Claude Code 2.1.178 there are no `TeamCreate`/`TeamDelete` tools: the team forms implicitly when the first teammate is spawned, and team resources are cleaned up automatically when the session ends. If teammate spawning is unavailable in this session, stop and tell the user to enable the flag and restart Claude Code; do not fall back to plain subagents without saying so.

# Team Research

Orchestrate a deep web research investigation using multiple researchers working in parallel. Each one covers a different source angle, and findings are synthesized into a unified report with cross-checking.

**This command researches the web, and only the web.** It never reads, greps or explores a local codebase, and it depends on no development plugin. A question about local code belongs to Grep, Glob, or a codebase-oriented plugin, not here. Keeping the boundary sharp is what lets this plugin stay usable on any topic, technical or not.

## Skills to Load

Before starting, invoke these skills:
- `agent-teams:team-composition-patterns` -- team sizing and agent selection
- `agent-teams:team-communication-protocols` -- coordination between researchers

## Pre-flight Checks

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
2. Parse `$ARGUMENTS`:
   - `<question-or-topic>`: the research question, topic, or area to investigate
   - `--domain`: free-form domain hint for the Domain Expert persona (e.g. `security`, `python`, `finance`, `nutrition`, `law`); auto-detected from the topic when omitted
   - `--depth`: research depth -- `quick` (2 researchers), `standard` (3 researchers, default), `deep` (4 researchers with domain expert)

## Phase 1: Question Analysis

1. Analyze the research question to understand:
   - Which source angles would answer it? Pick from the four `deep-researcher` classifies into: **authoritative** (primary docs, specs, vendor sources), **community** (forums, issue trackers, practitioner write-ups), **comparison** (alternatives weighed against each other), **recency** (what changed lately, release notes, deprecations).
   - What domain does it touch? (security, architecture, finance, law, nutrition, anything)
   - What would a complete answer look like? (facts, comparisons, recommendations, worked examples)
   - If the question turns out to be about local code rather than external knowledge, say so and stop: this command has no local-codebase capability and must not improvise one.
2. Break the question into sub-questions that can be investigated in parallel
3. Determine researcher count and roles based on `--depth`:
   - `quick`: 2 researchers (the 2 most relevant angles)
   - `standard`: 3 researchers (the 3 most relevant angles)
   - `deep`: 4 researchers (3 angles + domain expert)

## Phase 2: Team Spawn

1. The team forms implicitly when the first researcher is spawned (no `TeamCreate` step; the team name is session-derived and any `team_name` passed to the `Agent` tool is ignored)
2. Spawn researchers using specialized agents:

**Angle Researchers** (2 to 3, one per angle chosen in Phase 1):
- `subagent_type`: `research:deep-researcher`, one instance per angle
- Focus: the angle's characteristic sources. Authoritative goes to primary documentation, specifications and vendor material; community goes to forums, issue trackers and practitioner write-ups; comparison weighs named alternatives against each other; recency hunts what changed and when.
- Prompt: "Research {sub-question} from the {angle} angle. Cite every finding with its source URL and the date the source carries."
- Give each instance a different angle. Two researchers on the same angle produce agreement that means nothing, since they read the same sources.

**Domain Expert** (deep only):
- `subagent_type`: `research:deep-researcher` (dedicated instance with a domain persona)
- The domain comes from `--domain` or the topic detected in Phase 1. Any domain works: security, architecture, python, finance, law, nutrition, history. The persona lives in the prompt, not in a specialized agent, so this role never depends on other plugins being installed.
- Focus: domain-specific analysis, validation of findings from other researchers
- Prompt: "Act as a senior {domain} expert. Analyze {topic} strictly from the {domain} perspective. Validate or challenge the findings from the other researchers, citing evidence for every confirmation or objection."

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
   - Do the angles agree? Agreement between two angles that read different source families is evidence; agreement between two researchers who read the same page is not.
   - Does the domain expert validate or contradict the others?
   - Are there gaps that no angle covered?

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

#### From {angle 1} sources
- {finding 1} -- {URL} citation, {source date}
- {finding 2} -- {URL} citation, {source date}

#### From {angle 2} sources
- {finding 1} -- {URL} citation, {source date}
- {finding 2} -- {URL} citation, {source date}

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
