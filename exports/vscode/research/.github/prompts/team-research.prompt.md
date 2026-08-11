---
description: Deep web research with parallel investigators covering complementary source angles plus domain-specific analysis.
argument-hint: <question-or-topic> [--domain <topic-domain>] [--depth quick|standard|deep]
agent: research-orchestrator
---

# Team Research

Orchestrate a deep web research investigation using multiple researchers working in parallel. Each one covers a different source angle, and findings are synthesized into a unified report with cross-checking.

**This command researches the web, and only the web.** It never reads or searches a local codebase, and it dispatches nothing from another bundle. A question about local code belongs to `#search/textSearch`, `#search/fileSearch`, or a codebase-oriented bundle, not here.

## Pre-flight Checks

1. Load the `web-search-techniques` skill for query formulation, source authority ranking, and the bot-block fallback.
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

## Phase 2: Dispatch

1. Dispatch every researcher with `#agent/runSubagent`, in one turn so they run in parallel. Only the agents in this agent's `agents:` allowlist can be dispatched.
2. Assign each researcher one role:

**Angle Researchers** (2 to 3, one per angle chosen in Phase 1):
- agent: `deep-researcher`, one instance per angle
- Focus: the angle's characteristic sources. Authoritative goes to primary documentation, specifications and vendor material; community goes to forums, issue trackers and practitioner write-ups; comparison weighs named alternatives against each other; recency hunts what changed and when.
- Tools: `#websearch`, `#web/fetch`, `#read/readFile`
- Prompt: "Research {sub-question} from the {angle} angle. Cite every finding with its source URL and the date the source carries."
- Give each instance a different angle. Two researchers on the same angle produce agreement that means nothing, since they read the same sources.

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

Dispatched subagents end when they return. Leave `.research/` in place: it is the run's evidence.
