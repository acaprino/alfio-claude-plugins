# Research plugin -- web-only with deep-team orchestration (design)

**Date**: 2026-04-18
**Status**: approved for implementation planning
**Scope**: `plugins/research/`

## Goal

Transform `plugins/research/` so that `deep-researcher` is itself a lead orchestrator that spawns parallel `quick-searcher` sub-agents, each investigating one independent angle of a web research query, then synthesizes findings with cross-checking. Scope the plugin explicitly to **web research only** (any topic), deflecting codebase work to other tools.

## Why

Two pressures converge:

1. **Review findings** on the current agents (see `#team research-agents-review` session, 2026-04-18):
   - Activation gray zone between quick/deep for medium-complexity queries
   - Deep-researcher description contains unreachable `Bash` fallback reference (Finding 1 tech-reviewer, critical)
   - Incorrect `log*` regex wildcard claim in both files (Finding 2 tech-reviewer, high)
   - Three hard limits (20 tool calls / 3 rounds / 5 WebFetches) with unclear precedence (Finding 1 quality-reviewer, high)
   - Hard limits unenforceable (agents can't count their own tool calls -- Finding 3 quality-reviewer, high)
   - ~35 lines of cross-file duplication (Finding cross-file-duplication quality-reviewer)
   - Plugin has no `skills/` dir, breaking marketplace pattern (Finding 1 consistency-reviewer, medium)
   - No reciprocal escape hatch deep -> quick (Finding 2 activation-reviewer, medium)

2. **User intent**: turn deep research into a team-of-agents pattern (one sub-agent per angle, parallel, unified output) natively inside the `research` plugin, not as an external `agent-teams` preset.

## Scope

### In scope
- `plugins/research/agents/quick-searcher.md` (light edit)
- `plugins/research/agents/deep-researcher.md` (full rewrite as lead orchestrator)
- New `plugins/research/skills/web-search-techniques/SKILL.md` (shared knowledge)
- `plugins/research/scripts/webfetch.py` (keep as-is, document better)
- `.claude-plugin/marketplace.json` (version bumps, dependency declaration if needed)

### Out of scope
- Codebase search workflows (delegated to `Grep`, `Glob`, `codebase-mapper:codebase-explorer`)
- New slash command (user chose "total replacement", no new command)
- New lead agent (user chose total replacement of existing `deep-researcher`)
- Changes to `agent-teams:team-spawn` presets (`research`, `deep-search`) -- they remain and keep working

## Architecture

```
+-------------------------+
|    quick-searcher       |  sonnet, lite
|  (plugins/research/)    |  - direct invocation: 1-fact web lookup
|                         |  - sub-unit mode: workhorse inside deep-researcher team
+-------------------------+
            ^
            | (spawned via Agent tool, 2-3 parallel)
            |
+-------------------------+
|    deep-researcher      |  opus, lead orchestrator
|  (plugins/research/)    |  - classifies query into angles (A/B/C/D)
|                         |  - spawns N quick-searcher sub-agents in parallel
|                         |  - synthesizes with cross-checking
+-------------------------+
            |
            v
+-------------------------+
|  web-search-techniques  |  shared skill
|  (SKILL.md)             |  - query techniques
|                         |  - source authority ranking
|                         |  - WebFetch fallback via webfetch.py
+-------------------------+
```

### Roles

**`quick-searcher`** (sonnet, ~80-90 lines)
- Two invocation modes:
  - **Direct mode**: user-invoked, single-fact web lookup, 3-10 tool calls
  - **Sub-unit mode**: spawned by `deep-researcher` with explicit angle + budget in prompt; returns structured findings on that angle only
- Tools: `Read, Grep, Glob, WebFetch, WebSearch, Bash`
  - Bash added for `webfetch.py` fallback on bot-block
  - Grep/Glob retained for re-reading locally saved fetches, NOT for repo search
- References shared skill `web-search-techniques`

**`deep-researcher`** (opus, ~150-180 lines, full rewrite)
- Lead orchestrator, never does web calls itself
- Tools: `Agent` (to spawn sub-researchers), plus `Read` for reading sub reports
- Workflow:
  1. Parse query -> classify into 2-3 of four angles
  2. Spawn N `quick-searcher` sub-agents in parallel via `Agent` tool, each with:
     - Angle-specific prompt
     - Planning-time budget (5 WebSearch + 3 WebFetch + 1 round)
     - Required output template
  3. Wait for all sub reports
  4. Synthesize final report with cross-checking (template below)
- References shared skill `web-search-techniques` (for understanding what sub-agents do)

### The four angles

| Angle | Sources | Activates when |
|---|---|---|
| A. Authoritative | Official docs, API ref, RFCs, spec documents, institutional sites, papers | Always (default baseline) |
| B. Community | StackOverflow, Reddit, GitHub issues, forums, mailing lists | Query needs usage experience, edge cases, real-world behavior |
| C. Comparison | Review articles, "X vs Y", curated blog comparisons | Query asks to choose/evaluate/compare |
| D. Recency | Changelogs, announcements, news, trend articles | Query has temporal dependency ("2026", "current", "latest") |

- Default if query does not clearly match: activate A + B
- Max 3 sub-agents in parallel
- Lead chooses 2, 3, or all 4 based on query classification; never fewer than 2 in deep mode (otherwise use `quick-searcher` direct)

### Planning-time budgets (per-sub, not runtime counters)

Lead assigns budgets in each sub-agent's prompt:
- Max **5 WebSearch** calls
- Max **3 WebFetch** calls
- **1 round** of search, then synthesize and return
- Optional: fallback to `${CLAUDE_PLUGIN_ROOT}/scripts/webfetch.py` via Bash if WebFetch returns bot-block or <200 chars

Lead itself:
- 1 round of classification (planning, 0 web calls)
- 1 round of sub-agent spawn
- 1 round of synthesis (0 web calls)
- No global tool-call counter -- budget is enforced by sub-agent quotas

Total team budget (worst case, 3 subs): ~24 web operations. Better than current 20-cap because it's predictable and parallelized.

## Output template (deep-researcher)

Fixed structure, filled by lead after synthesizing sub reports:

```markdown
## Answer
[1-2 paragraphs directly answering the query]

## Findings per angle

### A. Authoritative sources
1. [claim] -- source: [URL], accessed: [date]
2. [claim] -- source: [URL]

### B. Community
1. [claim] -- source: [URL] (StackOverflow, N upvotes)
2. ...

### [other activated angles]

## Convergences and contradictions
- **Convergence**: [angles A+B agree on X]
- **Contradiction**: [A says Y, C says not-Y -- resolved/unresolved]

## Confidence assessment
- High: [claims with 2+ independent angles]
- Medium: [claims with 1 authoritative source]
- Low: [claims not cross-verified]

## Gaps
- [What could not be verified]
- [Sub-agent reports that returned empty or failed]

## Sub-agents metadata
- Angles activated: [A, B, D]
- Approximate budget used: ~N WebSearch + M WebFetch
```

## TRIGGER WHEN / DO NOT TRIGGER WHEN

### `quick-searcher`
```yaml
description: >
  Lite web search agent for single-fact lookups and quick web answers on any topic.
  Also used as a sub-unit by deep-researcher when invoked with an angle+budget prompt.
  TRIGGER WHEN: the user asks for a single fact, definition, stat, URL, or quick
  confirmation that can plausibly be answered by 1-3 web searches from one source.
  DO NOT TRIGGER WHEN: the question requires synthesis across 3+ sources or multiple
  angles (use deep-researcher), or the task is about local code/files (use Grep/Glob
  or codebase-mapper:codebase-explorer), or the user is implementing/editing code.
```

### `deep-researcher`
```yaml
description: >
  Web research lead orchestrator for any topic. Classifies the query into 2-3 of
  four angles (authoritative / community / comparison / recency) and spawns
  parallel quick-searcher sub-agents, one per angle, then synthesizes findings
  with cross-checking.
  TRIGGER WHEN: the user asks an open-ended web research question requiring
  synthesis across multiple sources or angles (e.g. "compare X vs Y", "audit the
  ecosystem around Z", "what are current best practices for W in 2026").
  DO NOT TRIGGER WHEN: the question is a single-fact lookup answerable from one
  source (use quick-searcher), or the task is about local code/files (use Grep,
  Glob, or codebase-mapper:codebase-explorer), or it is a code-quality audit
  (use senior-review:code-auditor), or the user is implementing/editing code.
```

## Shared skill

### `plugins/research/skills/web-search-techniques/SKILL.md`

Consolidates content duplicated between the two agents today. Frontmatter:

```yaml
name: web-search-techniques
description: >
  Knowledge base for web search query techniques, source authority ranking,
  WebFetch/WebSearch best practices, and bot-block fallback via webfetch.py.
  Used by quick-searcher and deep-researcher in plugins/research/.
  TRIGGER WHEN: performing web research with WebSearch or WebFetch.
  DO NOT TRIGGER WHEN: searching local codebase (use Grep/Glob directly).
```

Sections (scope: web-only):
- **Query formulation** -- keyword techniques, synonyms, domain terminology, year filters, site: operator
- **Source authority ranking** -- docs > RFCs > GitHub issues > high-voted SO > blogs
- **WebSearch techniques** -- site:, quoted phrases, year, "official"/"documentation"
- **WebFetch guidance** -- prefer docs, evaluate quality, handle truncation, target sections
- **webfetch.py fallback** -- when (bot-block, thin content), how (`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/webfetch.py <url>`), expected output
- **Anti-loop** -- never repeat same query; 2 failed attempts max per sub-topic; pivot

Removed from the skill (since scope is web-only):
- Repo Grep examples
- Glob patterns for source files
- Git-history guidance
- `log*` regex wildcard example (was incorrect; see tech review Finding 2)

## Fixes from review findings absorbed into design

| Finding | Reviewer | How this design addresses it |
|---|---|---|
| Bash fallback unreachable | tech (critical) | Bash added to both agents' `tools` lists; fallback documented in shared skill |
| `log*` regex wildcard claim is wrong | tech (high) | Removed entirely (out of web scope) |
| 3 hard limits with no precedence | quality (high) | Replaced with per-sub planning-time budget assigned by lead |
| Hard limits unenforceable | quality (high) | Budget is planning-time (in prompt), not runtime counter |
| Max 3 rounds vs deliver-after-2 conflict | quality (high) | Sub-agents do 1 round; lead does 1 synthesis round; no conflict possible |
| Internal redundancy (Tool Selection vs Planning) | quality (medium) | Full rewrite; sections reorganized; content consolidated |
| Anti-loop thresholds inconsistent (3 vs 2) | quality (medium) | Standardized to 2 in shared skill |
| Bash fallback in description (not body) | activation (medium), tech (medium) | Moved to body (shared skill); removed from description |
| Gray zone medium-complexity queries | activation (high) | Deep description requires "synthesis across multiple sources" -- explicit |
| No escape hatch deep -> quick | activation (medium) | Deep lead has minimum-2-angles rule; if only 1 angle matches, returns "use quick-searcher" |
| No deflection for codebase mapping / audit | activation (low) | Both descriptions explicitly deflect to codebase-mapper and code-auditor |
| Plugin has no skill dir | consistency (medium) | New `skills/web-search-techniques/` created |
| Frontmatter order drift | consistency (low) | Kept as-is (within marketplace drift tolerance) |

## Trade-offs and risks

1. **Token cost**: deep research with 3 subs consumes ~3x tokens of current single-agent deep. Mitigated by subs being sonnet (cheaper), not opus.
2. **Latency**: parallel spawn adds overhead (~2-3s initial) but real parallelism reduces wall-clock vs serial single-agent processing 3 angles.
3. **Partial-failure cascade**: if a sub fails or returns empty, lead must handle gracefully -- covered in output template "Gaps" section.
4. **Lead prompt complexity**: classification + spawn + synthesis. Mitigated by 4 well-defined categories and default fallback (A+B).
5. **Breaking change for existing deep-researcher callers**: invocation pattern unchanged (same agent name, same description shape) but runtime behavior changes from serial single-agent to parallel team. Callers who expected a single agent get a faster team; no API change.
6. **Scope narrowing**: removing codebase search from `deep-researcher` means callers who used it for mixed code+web queries must now use a team preset (`/agent-teams:team-spawn research` already exists for this). Document the deprecation in the spec; marketplace.json description updated to clarify web-only.

## File changes summary

**Modify:**
- `plugins/research/agents/quick-searcher.md` -- description update, sub-unit mode section, remove codebase examples, remove incorrect regex, add Bash to tools, reference new skill
- `plugins/research/agents/deep-researcher.md` -- full rewrite as lead orchestrator
- `.claude-plugin/marketplace.json` -- bump `plugins[].version` for `research` (2.5.3 -> 2.6.0 minor: breaking-ish behavior), bump `metadata.version`, update plugin description to reflect web-only scope

**Create:**
- `plugins/research/skills/web-search-techniques/SKILL.md`
- Register skill in marketplace.json under `plugins[research].skills`

**Keep as-is:**
- `plugins/research/scripts/webfetch.py`

## Success criteria

1. `quick-searcher` can be invoked directly and returns a 1-source web answer in under 10 tool calls
2. `deep-researcher` invocation on a sample query ("compare X vs Y ecosystem in 2026") produces a structured report with findings from 2-3 angles and a confidence/gaps section
3. Zero references in either agent body to tools not declared in the `tools:` frontmatter
4. Shared skill exists and is referenced by both agents (no duplicate content)
5. Review findings from the 2026-04-18 research-agents-review team are all addressed (13 findings -> closed)

## Out-of-scope future work

- Adding a research-team preset to `agent-teams:team-spawn` that reuses this architecture (separate decision)
- Caching web results between sub-agents (optimization)
- Adding more angles (e.g., "academic/papers") as 5th category -- current 4 are deliberately small
