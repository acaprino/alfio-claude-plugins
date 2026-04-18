# Research plugin web-only with deep-team orchestration -- Implementation Plan

> **For agentic workers:** Use subagent-driven execution (if subagents available) or ai-tooling:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform `plugins/research/` into a web-only research plugin where `deep-researcher` is a lead orchestrator spawning parallel `quick-searcher` sub-agents across 2-3 of 4 angles, then synthesizes with cross-checking.

**Architecture:** `quick-searcher` (sonnet) operates in two modes: direct (user-invoked, 1 fact) or sub-unit (spawned by `deep-researcher` with angle+budget prompt). `deep-researcher` (opus) uses only the `Agent` and `Read` tools, classifies queries into the four angles (authoritative / community / comparison / recency), spawns up to 3 parallel sub-agents via the `Agent` tool, and writes a fixed-template report. Shared knowledge lives in a new `web-search-techniques` skill referenced by both agents.

**Tech Stack:** Markdown-only plugin with YAML frontmatter. No build, no tests. Python helper `scripts/webfetch.py` (pre-existing, untouched) used for bot-block fallback.

**Reference spec:** `docs/plans/2026-04-18-research-deep-team-design.md` (commit d686133). This plan executes that design.

---

## File Structure

```
plugins/research/
  agents/
    quick-searcher.md            # MODIFY -- light edit, add Bash, sub-unit mode, web-only
    deep-researcher.md           # REWRITE -- lead orchestrator
  skills/
    web-search-techniques/
      SKILL.md                   # CREATE -- shared knowledge base
  scripts/
    webfetch.py                  # UNCHANGED
.claude-plugin/
  marketplace.json               # MODIFY -- bump versions, register skill, update description
docs/plans/
  2026-04-18-research-deep-team-design.md    # EXISTS -- reference only
  2026-04-18-research-deep-team-plan.md      # THIS FILE
```

Each file has a single responsibility:
- `quick-searcher.md`: execute one angle of web research with a bounded budget
- `deep-researcher.md`: orchestrate the team, classify, spawn, synthesize
- `web-search-techniques/SKILL.md`: consolidated query techniques and source ranking (no duplication)
- `marketplace.json`: plugin registry (versions + skill registration)

---

## Phase 1: Create the shared skill

The skill is the foundation. Both agents reference it, so it must exist first so rewriting the agents can drop duplicated content cleanly.

### Task 1.1: Create skill directory and SKILL.md

**Files:**
- Create: `plugins/research/skills/web-search-techniques/SKILL.md`

- [ ] **Step 1: Verify directory does not already exist**

Run: `ls plugins/research/skills/ 2>&1 || echo "no skills dir yet"`
Expected: `no skills dir yet` (or the directory is missing)

- [ ] **Step 2: Write SKILL.md with the consolidated content**

Write the file with this exact content:

````markdown
---
name: web-search-techniques
description: >
  Knowledge base for web search query techniques, source authority ranking, WebFetch/WebSearch best practices, and bot-block fallback via webfetch.py. Used by quick-searcher and deep-researcher in plugins/research/.
  TRIGGER WHEN: performing web research with WebSearch or WebFetch.
  DO NOT TRIGGER WHEN: searching local codebase (use Grep or Glob directly).
---

# Web Search Techniques

Shared knowledge base for `research:quick-searcher` and `research:deep-researcher`. Scope: web-only. Covers query formulation, source authority, tool usage, bot-block fallback, and anti-loop rules.

## Query Formulation

Extract core concepts from the question before querying:
- Identify synonyms and domain terminology (e.g. "authentication": auth, login, signin, session, token, jwt, oauth, credentials)
- Account for abbreviations and full forms
- Add the year ("2026") when the query has temporal dependency
- Add "official" or "documentation" to push toward authoritative sources
- Quote exact phrases for precise matches
- Use `site:` to restrict to known-good domains (e.g. `site:developer.mozilla.org`)

Start broad, narrow progressively. Overly specific first queries miss adjacent information. Each refinement round incorporates terms surfaced in prior results.

## Source Authority Ranking

Rank every source before citing:

1. **Official documentation sites and API references** -- highest authority
2. **RFC and specification documents** -- canonical for standards
3. **GitHub issues, discussions, and source code** -- authoritative for specific libraries
4. **Peer-reviewed or community-validated content** -- Stack Overflow with high votes, maintainers' blogs
5. **General blog posts and tutorials** -- use only when nothing better exists
6. **Deprioritize** -- SEO content farms, AI-generated summaries, scraped aggregators

Currency checks:
- Last modified date on the page
- Version numbers cited vs latest release
- Deprecation warnings

## WebSearch Techniques

Query operators (standard search-engine conventions, usually respected by WebSearch):
- `site:` -- restrict to a domain
- `"exact phrase"` -- match the phrase verbatim
- Year token -- add "2026" for recency
- `"official"` or `"documentation"` -- bias toward authoritative
- Version numbers when relevant (e.g. `react 19`)

## WebFetch Guidance

- Prefer documentation pages and API references over blog posts
- Evaluate fetched content -- low-authority source means discard and re-search
- Large pages may be truncated -- target specific sections (anchor URLs) when possible
- Track the accessed URL with date for citation

## webfetch.py Fallback

When WebFetch returns a bot-block (403, 429, Cloudflare challenge) or thin content (under ~200 chars of useful text), fall back to the plugin's stealth fetcher:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/webfetch.py <url>
```

Behavior:
- Impersonates Chrome TLS fingerprint via curl_cffi
- Returns clean extracted text on stdout
- Exits 0 on success, 1 on timeout or error
- On failure, proceed without the result (do not retry in a loop)

Invocation options:
- `--timeout SECONDS` (default: 30)
- `--max-chars CHARS` (truncate output)
- `--raw` (return raw HTML instead of extracted text)

Requires `Bash` tool in the agent's `tools:` frontmatter.

## Anti-Loop Rules

- Never repeat the exact same query or search parameters
- If a search returns nothing, change terminology, broaden the regex, or switch tool/target
- Maximum 2 failed attempts per sub-topic before pivoting or escalating
- After 2 failed attempts on the same angle, document the gap and proceed with what you have
````

- [ ] **Step 3: Verify file is syntactically correct**

Run: `head -8 plugins/research/skills/web-search-techniques/SKILL.md`
Expected: Shows the frontmatter block with `name: web-search-techniques` and `description: >`.

- [ ] **Step 4: Commit Phase 1**

```bash
git add plugins/research/skills/web-search-techniques/SKILL.md
git commit -m "Add web-search-techniques skill for research plugin"
```

---

## Phase 2: Rewrite quick-searcher as dual-mode agent

`quick-searcher` is modified in place. Direct mode stays functional; sub-unit mode is new. Bash added to tools. Web-only scope. References new skill. Removes incorrect `log*` regex claim.

### Task 2.1: Rewrite quick-searcher.md

**Files:**
- Modify: `plugins/research/agents/quick-searcher.md` (replace entire content)

- [ ] **Step 1: Read the current file to confirm starting state**

Run: `wc -l plugins/research/agents/quick-searcher.md`
Expected: around 89 lines (current state per review).

- [ ] **Step 2: Write the new content**

Replace the entire file contents with:

```markdown
---
name: quick-searcher
description: >
  Lite web search agent for single-fact lookups and quick web answers on any topic. Also used as a sub-unit by deep-researcher when invoked with an angle+budget prompt.
  TRIGGER WHEN: the user asks for a single fact, definition, stat, URL, or quick confirmation that can plausibly be answered by 1-3 web searches from one source.
  DO NOT TRIGGER WHEN: the question requires synthesis across 3+ sources or multiple angles (use deep-researcher), or the task is about local code/files (use Grep, Glob, or codebase-mapper:codebase-explorer), or the user is implementing/editing code.
tools: Read, WebFetch, WebSearch, Bash
model: sonnet
color: pink
---

# ROLE

Fast-track web searcher. Two modes:
- **Direct mode**: user-invoked, one-fact lookup. 3-10 tool calls. Lead with the answer.
- **Sub-unit mode**: spawned by `deep-researcher` with an explicit angle + budget. Execute that angle only, return structured findings.

Priority: speed over exhaustiveness. One good source beats five mediocre rounds.

Load the shared skill `research:web-search-techniques` for query techniques, source ranking, WebFetch guidance, and webfetch.py fallback. Do not duplicate that content here.

# DIRECT MODE

Activated when the user invokes this agent directly.

1. Identify the single core fact needed
2. Pick the most direct path: WebSearch for discovery, WebFetch for extraction
3. Execute 1-3 focused searches
4. Return the answer with source URL and access date

Target: 3-10 tool calls total. If past 10, you are overcomplicating it -- deliver what you have and flag the gap.

# SUB-UNIT MODE

Activated when the prompt arrives from `deep-researcher` and contains an **Angle** and **Budget** header. Example prompt shape:

```
Angle: B. Community
Budget: 5 WebSearch + 3 WebFetch + 1 round
Query: How do production teams handle X in 2026?
Return format: [the fixed template below]
```

Rules:
- Execute ONLY the assigned angle. Do not drift into other angles.
- Respect the budget as a planning-time cap. Plan your queries before launching them.
- Deliver findings in the exact return format requested.
- If the budget is exhausted before the angle is covered, return partial findings with a "Gaps" line.

Return format (when in sub-unit mode):

```
## Findings for angle [X]
1. [claim] -- source: [URL], accessed: [date]
2. [claim] -- source: [URL]
3. ...

## Notes
- [any contradictions, caveats, low-confidence claims]

## Gaps
- [anything you could not verify within the budget]
```

# TOOL QUICK REFERENCE

- **WebSearch**: discovery. Broad queries first, then narrow. See shared skill for operators.
- **WebFetch**: extraction. Prefer docs and API refs. See shared skill for fallback.
- **Bash**: only for invoking `${CLAUDE_PLUGIN_ROOT}/scripts/webfetch.py` when WebFetch is bot-blocked or returns thin content.
- **Read**: for re-opening locally saved fetches (if any), not for codebase search.

# ANTI-LOOP

Never repeat the exact same query. If a search returns nothing:
- Change terminology
- Broaden the query
- Switch to a different authoritative domain via `site:`
- After 2 failed attempts on the same sub-topic, stop and report the gap

# OUTPUT

Direct mode:
- Lead with the answer
- Include source URL and access date
- Note confidence if uncertain
- Flag if the question actually needs deeper research (caller may spawn deep-researcher)

Sub-unit mode: use the return format above exactly.
```

- [ ] **Step 3: Verify the file**

Run: `wc -l plugins/research/agents/quick-searcher.md && head -11 plugins/research/agents/quick-searcher.md`
Expected: approximately 75-85 lines; frontmatter shows `tools: Read, WebFetch, WebSearch, Bash` and `model: sonnet`.

- [ ] **Step 4: Grep for forbidden content**

Run: `grep -n "log\*" plugins/research/agents/quick-searcher.md`
Expected: no output (incorrect regex example removed).

Run: `grep -n -- "—" plugins/research/agents/quick-searcher.md`
Expected: no output (no em dashes per CLAUDE.md).

- [ ] **Step 5: Commit Task 2.1**

```bash
git add plugins/research/agents/quick-searcher.md
git commit -m "Rewrite quick-searcher as dual-mode web search agent"
```

---

## Phase 3: Rewrite deep-researcher as lead orchestrator

Full rewrite. Tools change to `Agent, Read` (orchestrator only, does no web calls directly). Description becomes routing-clean.

### Task 3.1: Rewrite deep-researcher.md

**Files:**
- Modify: `plugins/research/agents/deep-researcher.md` (full replacement)

- [ ] **Step 1: Confirm starting state**

Run: `wc -l plugins/research/agents/deep-researcher.md`
Expected: around 217 lines (current).

- [ ] **Step 2: Write the new content**

Replace the entire file contents with:

````markdown
---
name: deep-researcher
description: >
  Web research lead orchestrator for any topic. Classifies the query into 2-3 of four angles (authoritative / community / comparison / recency) and spawns parallel quick-searcher sub-agents, one per angle, then synthesizes findings with cross-checking.
  TRIGGER WHEN: the user asks an open-ended web research question requiring synthesis across multiple sources or angles (e.g. "compare X vs Y", "audit the ecosystem around Z", "what are current best practices for W in 2026").
  DO NOT TRIGGER WHEN: the question is a single-fact lookup answerable from one source (use quick-searcher), or the task is about local code/files (use Grep, Glob, or codebase-mapper:codebase-explorer), or it is a code-quality audit (use senior-review:code-auditor), or the user is implementing/editing code.
tools: Agent, Read
model: opus
color: pink
---

# ROLE

Lead orchestrator for multi-angle web research. You do NOT make web calls yourself. You classify the query, spawn parallel `research:quick-searcher` sub-agents (one per activated angle), wait for their reports, then synthesize a cross-checked final report.

Priority: breadth with cross-verification. Parallelism is the value. A single-source answer is a quick-searcher job.

Load the shared skill `research:web-search-techniques` to understand what sub-agents will do. Do not duplicate its content here.

# THE FOUR ANGLES

Every deep-research query is answered via 2-3 of these angles. You pick which.

| Angle | Sources | Activate when |
|---|---|---|
| **A. Authoritative** | Official docs, API refs, RFCs, spec documents, institutional sites, papers | Always (default baseline) |
| **B. Community** | StackOverflow, Reddit, GitHub issues, forums | Query needs usage experience, edge cases, real-world behavior |
| **C. Comparison** | Review articles, "X vs Y", curated comparisons | Query asks to choose, evaluate, or compare options |
| **D. Recency** | Changelogs, announcements, news, trend articles | Query has temporal dependency ("2026", "current", "latest") |

Rules:
- Always activate A (authoritative baseline)
- Activate B, C, D based on query intent
- Minimum 2 angles, maximum 3 angles
- If only 1 angle fits: return "this is a single-angle query, use quick-searcher" and stop
- Default when unclear: A + B

# WORKFLOW

## Phase 1: Classify

Parse the query. Decide which 2-3 angles to activate. Write a one-line classification comment in your internal notes, e.g.:

> Query: "compare Pydantic v2 vs attrs in 2026". Angles: A (official docs), C (comparison articles), D (recent benchmarks).

If the query is a single-fact lookup (no synthesis needed, one source enough), stop and tell the caller to use `quick-searcher` instead.

## Phase 2: Spawn sub-agents in parallel

For each activated angle, spawn one `research:quick-searcher` via the `Agent` tool. Launch them in a **single message with multiple tool calls** so they run concurrently.

Each sub-agent prompt must follow this template:

```
Angle: [A | B | C | D]. [angle name]
Budget: 5 WebSearch + 3 WebFetch + 1 round
Query: [the original user query, possibly rephrased for this angle]
Focus: [angle-specific instructions -- e.g. "Find only official sources" / "Find only community discussion"]
Return format:

## Findings for angle [X]
1. [claim] -- source: [URL], accessed: [date]
2. ...

## Notes
- [contradictions, caveats]

## Gaps
- [what you could not verify]
```

Example spawn prompt for angle C:

```
Angle: C. Comparison
Budget: 5 WebSearch + 3 WebFetch + 1 round
Query: How does Pydantic v2 compare to attrs in 2026?
Focus: Find comparison articles, benchmarks, "X vs Y" posts. Skip official docs and community Q&A.
Return format: [template above]
```

## Phase 3: Synthesize

Once all sub-agents return, produce the final report using the template below. Cross-check claims across angles: convergences strengthen confidence, contradictions must be noted.

If a sub-agent failed or returned empty, record it in "Gaps" and reduce the confidence of claims that depended on that angle.

# OUTPUT TEMPLATE

Use this exact structure for the final report:

```
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
- **Contradiction**: [A says Y, C says not-Y -- resolved via D / unresolved]

## Confidence assessment
- High: [claims with 2+ independent angles]
- Medium: [claims with 1 authoritative source]
- Low: [claims not cross-verified]

## Gaps
- [What could not be verified]
- [Sub-agents that returned empty or failed]

## Sub-agents metadata
- Angles activated: [A, B, D]
- Approximate budget used: ~N WebSearch + M WebFetch
```

# BUDGETS

You assign budgets; you do not count runtime tool calls.

Per sub-agent (planning-time quota, written in the spawn prompt):
- Max 5 WebSearch
- Max 3 WebFetch
- 1 round of search, then synthesize and return

Your own overhead (negligible):
- 1 classification pass (no web calls)
- 1 spawn round (all subs in parallel)
- 1 synthesis pass (no web calls)

Worst-case team budget: 3 subs x 8 web operations = 24 web operations. Better than serial because parallel.

# ANTI-LOOP

- Never re-spawn the same angle twice. If an angle returns poor data, note it in Gaps; do not retry.
- If 2+ sub-agents fail, report partial findings and stop. Do not escalate to a second wave.

# FAILURE HANDLING

- Sub-agent returns empty: record in Gaps, keep that angle's section in the report but empty with a "no findings" note
- Sub-agent times out or errors: record in Gaps, note which angle is missing, reduce confidence for cross-checked claims
- All sub-agents fail: return a short report explaining the failure and suggesting the user retry with `quick-searcher` on a narrower query
````

- [ ] **Step 3: Verify the file**

Run: `wc -l plugins/research/agents/deep-researcher.md && head -11 plugins/research/agents/deep-researcher.md`
Expected: approximately 140-180 lines; frontmatter shows `tools: Agent, Read` and `model: opus`.

- [ ] **Step 4: Grep for forbidden content**

Run: `grep -n -- "—" plugins/research/agents/deep-researcher.md`
Expected: no output.

Run: `grep -n "webfetch.py" plugins/research/agents/deep-researcher.md`
Expected: no output (lead does no direct web calls, so no need to reference the script -- it's in the shared skill, referenced by sub-agents).

Run: `grep -n "WebSearch\|WebFetch" plugins/research/agents/deep-researcher.md`
Expected: only references inside the spawn-prompt template and budget section (not as tool calls the lead itself makes).

- [ ] **Step 5: Commit Task 3.1**

```bash
git add plugins/research/agents/deep-researcher.md
git commit -m "Rewrite deep-researcher as lead orchestrator with parallel sub-agents"
```

---

## Phase 4: Update marketplace.json

Register the new skill, bump versions, update the plugin description to reflect web-only scope.

### Task 4.1: Edit marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json` (research plugin entry; metadata.version)

- [ ] **Step 1: Find current state**

Run: `grep -n '"name": "research"' .claude-plugin/marketplace.json`
Expected: one match around line 352.

Run: `grep -n '"version"' .claude-plugin/marketplace.json | head -5`
Expected: metadata version is at the top of the file; each plugin has its own version.

- [ ] **Step 2: Update plugin version 2.5.3 -> 2.6.0**

Use Edit to change `"version": "2.5.3"` (line 355) to `"version": "2.6.0"` in the `research` plugin block. Be careful -- use surrounding context to make the match unique.

Exact edit (within the research plugin entry):

```
OLD:
      "name": "research",
      "source": "./plugins/research",
      "description": "Search and research toolkit -- quick-searcher (sonnet) for fast fact-finding and single-concept lookups, deep-researcher (opus) for complex multi-source investigation requiring systematic coverage, cross-referencing, and iterative refinement",
      "version": "2.5.3",

NEW:
      "name": "research",
      "source": "./plugins/research",
      "description": "Web research toolkit (any topic) -- quick-searcher (sonnet) for single-fact web lookups and as sub-unit in deep team, deep-researcher (opus) lead orchestrator that classifies queries into authoritative/community/comparison/recency angles and spawns parallel quick-searcher sub-agents with cross-checked synthesis",
      "version": "2.6.0",
```

- [ ] **Step 3: Register the new skill**

The `research` plugin entry currently has `"agents": [...]` but no `"skills"` key. Add a `"skills"` array listing the new skill.

Exact edit (within the research plugin entry, after the `"agents"` array):

```
OLD:
      "agents": [
        "./agents/quick-searcher.md",
        "./agents/deep-researcher.md"
      ]
    },

NEW:
      "agents": [
        "./agents/quick-searcher.md",
        "./agents/deep-researcher.md"
      ],
      "skills": [
        "./skills/web-search-techniques/SKILL.md"
      ]
    },
```

- [ ] **Step 4: Bump metadata.version**

Run: `grep -n '"metadata"' .claude-plugin/marketplace.json`
Expected: match near top of file.

Run: `head -10 .claude-plugin/marketplace.json`
This shows current metadata block. Identify the current `metadata.version` (e.g. `"version": "5.28.0"`) and bump the minor: `5.28.0 -> 5.29.0`.

Edit the metadata version using the surrounding context. Example:

```
OLD:
  "metadata": {
    "version": "5.28.0",

NEW:
  "metadata": {
    "version": "5.29.0",
```

(Adjust the starting number to match the actual current value.)

- [ ] **Step 5: Validate JSON syntax**

Run: `python -m json.tool .claude-plugin/marketplace.json > /dev/null && echo OK`
Expected: `OK` (no JSON errors).

- [ ] **Step 6: Verify research plugin entry**

Run: `grep -n -A 25 '"name": "research"' .claude-plugin/marketplace.json | head -30`
Expected output includes the new description, version `2.6.0`, and the `"skills"` array with the SKILL.md path.

- [ ] **Step 7: Commit Phase 4**

```bash
git add .claude-plugin/marketplace.json
git commit -m "Bump research plugin to 2.6.0 -- register skill, web-only scope"
```

---

## Phase 5: Final verification and push

### Task 5.1: End-to-end sanity checks

- [ ] **Step 1: Verify all four files exist and have expected size**

Run:
```bash
wc -l plugins/research/agents/quick-searcher.md \
       plugins/research/agents/deep-researcher.md \
       plugins/research/skills/web-search-techniques/SKILL.md
```
Expected: quick-searcher ~75-85 lines, deep-researcher ~140-180 lines, SKILL ~70-100 lines.

- [ ] **Step 2: Verify no em dashes anywhere in the touched files**

Run:
```bash
grep -rn -- "—" plugins/research/
```
Expected: no output.

- [ ] **Step 3: Verify tool declarations match body references**

Run:
```bash
grep -n "^tools:" plugins/research/agents/*.md
```
Expected:
- quick-searcher: `tools: Read, WebFetch, WebSearch, Bash`
- deep-researcher: `tools: Agent, Read`

Then for deep-researcher specifically, verify it does NOT reference WebFetch/WebSearch as tools it uses itself (only inside the spawn-prompt template):

Run: `grep -n "use WebFetch\|call WebFetch\|WebFetch call" plugins/research/agents/deep-researcher.md`
Expected: no output (the lead never makes web calls itself).

- [ ] **Step 4: Verify quick-searcher does not reference deprecated Grep/Glob codebase examples**

Run: `grep -n "function|def|fn\|class\s\\\\w" plugins/research/agents/quick-searcher.md`
Expected: no output (codebase regex examples removed).

- [ ] **Step 5: Verify the skill is referenced by both agents**

Run: `grep -n "web-search-techniques" plugins/research/agents/*.md`
Expected: one reference in each agent.

- [ ] **Step 6: Verify marketplace.json registers the skill**

Run: `grep -n "web-search-techniques/SKILL.md" .claude-plugin/marketplace.json`
Expected: one match in the research plugin's skills array.

- [ ] **Step 7: Verify review findings closed (spot check)**

Checklist:
- Bash now in quick-searcher tools: `grep "^tools:" plugins/research/agents/quick-searcher.md | grep -q Bash && echo OK`
- Bash NOT needed in deep-researcher (orchestrator only): `grep "^tools:" plugins/research/agents/deep-researcher.md | grep -qv Bash && echo OK`
- `log*` regex example gone: `grep -c "log\*" plugins/research/agents/*.md` -- expected `0` for both
- `webfetch.py` documented in the skill: `grep -c "webfetch.py" plugins/research/skills/web-search-techniques/SKILL.md` -- expected `>= 1`
- TRIGGER WHEN / DO NOT TRIGGER WHEN present in both: `grep -c "TRIGGER WHEN" plugins/research/agents/*.md` -- expected `>= 2` per file

- [ ] **Step 8: Show final commit log**

Run: `git log --oneline -5`
Expected: 4 new commits (skill, quick-searcher, deep-researcher, marketplace) on top of the design-doc commit.

- [ ] **Step 9: Push to master**

Run: `git push`
Expected: successful push. (Do NOT force-push.)

---

## Spec coverage check

| Spec section | Implemented in |
|---|---|
| `quick-searcher` dual-mode (direct + sub-unit) | Task 2.1 |
| `deep-researcher` as lead orchestrator | Task 3.1 |
| Four angles (A/B/C/D) with activation rules | Task 3.1 (THE FOUR ANGLES + WORKFLOW) |
| Planning-time budgets (5/3/1, max 3 subs) | Task 3.1 (BUDGETS + spawn-prompt template) |
| Fixed output template with cross-check | Task 3.1 (OUTPUT TEMPLATE) |
| Shared skill consolidating duplicated content | Task 1.1 |
| Bash added to quick-searcher tools | Task 2.1 |
| Description updated to web-only scope | Tasks 2.1, 3.1, 4.1 |
| webfetch.py fallback documented | Task 1.1 (skill) |
| `log*` regex claim removed | Task 2.1 |
| Description deflects to Grep/Glob/codebase-mapper/code-auditor | Tasks 2.1, 3.1 |
| Plugin gets skills/ dir (marketplace pattern) | Task 1.1 + Task 4.1 |
| marketplace.json version bumps + skill registration | Task 4.1 |
| 13 review findings addressed | Tasks 1.1, 2.1, 3.1, 4.1 (see design doc mapping) |

## Self-review notes

- No "TBD" or "implement later" anywhere in the plan -- every step ships complete content
- Each task produces a commit; a reviewer can `git log` to see the incremental build
- Phases are independent-ish: Phase 1 (skill) could ship on its own; Phase 2/3 depend on Phase 1 (agents reference skill); Phase 4 depends on 1-3 (marketplace.json lists skill); Phase 5 is just verification
- Angle names in Task 3.1 (`A. Authoritative`, `B. Community`, `C. Comparison`, `D. Recency`) match exactly between THE FOUR ANGLES table and the OUTPUT TEMPLATE and the spawn-prompt template -- no drift
- The `Agent` tool name is the Claude Code agent-spawning tool (consistent with how `agent-teams` plugin uses it)
- No tests to run (markdown-only repo) -- verification is via `grep` and structural checks in Phase 5
