# `research` 6.0.0: parity with the commercial deep-research products

**Date**: 2026-08-23
**Plugin**: `research` (5.0.0 to 6.0.0), marketplace 24.1.0 to 25.0.0
**Status**: design approved in session, spec pending user review

## 1. Goal

Make `/research:team-research` behave as closely as the Claude Code harness allows to OpenAI Deep Research, Anthropic Research (Claude) and Gemini Deep Research: scope the question with the user, show a plan, run many iterative investigators in parallel, read sources rather than skim snippets, loop until the question saturates, and deliver a long-form, fully cited report as a document. Everything stays inside the existing `research` plugin: the same command, the same two agents, the same skill, restructured and made parametric. No new plugin, no new command.

The plugin stays a **web-research tool and nothing else**. It reads no local codebase, spawns no agent from another local plugin, and after this release declares no dependency at all.

## 2. What the real products do, and where 5.0.0 falls short

| Behaviour of the real products | `research` 5.0.0 today |
|---|---|
| Scope is clarified before work starts (OpenAI asks scoping questions; Gemini shows an editable plan and waits) | No scoping step, no plan shown |
| The question is decomposed into sub-questions derived from that question | Four fixed source angles (authoritative, community, comparison, recency) are the unit of work |
| Iterative: search, read, find gaps, search again, backtrack, until saturation | One round; an explicit rule forbids a second wave |
| Dozens to hundreds of pages read over 5 to 30+ minutes | 5 searches + 3 fetches per angle, about 24 operations worst case |
| Effort scales with query complexity (Anthropic's lead assigns 1 agent for a fact, 2-4 subagents for a comparison, 10+ for an open-ended survey) | Fixed 2-3 angles regardless of the question |
| Long-form structured report: summary, sections, tables, inline citations, bibliography, limitations | "Answer + findings list" in chat |
| A dedicated pass that maps every claim to a source (Anthropic's citation agent) | None |
| A persistent document | Chat output only |
| Lead keeps its context clean: subagents return compressed reports, not raw pages | Same in spirit, but at 3 researchers it never mattered |

Section 11 records the verified facts behind the left column, with sources.

## 3. Decisions taken in the brainstorm

1. **Surface**: restructure the existing `/research:team-research` into the flagship, parametric by flags. No new command, no new plugin.
2. **Gates**: clarify (only when the question is ambiguous), then plan approval. Both skippable for unattended runs.
3. **Report**: written to a file, executive summary in chat.
4. **Scale**: complexity-scaled, Anthropic numbers, `--depth` overrides.
5. **Engine**: lead + parallel researchers in waves, plain subagents through the `Agent` tool. The experimental agent-teams flag and the `agent-teams@claude-code-workflows` dependency are dropped.
6. **serper.dev**: optional search backend behind a stdlib script, auto-detected from `SERPER_API_KEY`, never required, always reported.

## 4. The command: `/research:team-research`

### 4.1 Signature

```
/research:team-research "<question>" [--depth auto|quick|standard|deep] [--no-clarify] [--auto]
                        [--out <file-or-dir>] [--backend auto|websearch|serper] [--domain <hint>]
```

| Flag | Default | Meaning |
|---|---|---|
| `--depth` | `auto` | `auto` picks the tier from the question's complexity (section 4.3); a named tier forces it |
| `--no-clarify` | off | Skip the clarification gate; the plan gate still runs |
| `--auto` | off | Skip both gates: print the plan and run. For unattended use |
| `--out` | `research/<YYYY-MM-DD>-<slug>.md` in the current working directory | A file path, or a directory (the default filename goes inside it) |
| `--backend` | `auto` | `auto`: serper when `SERPER_API_KEY` is set, else native `WebSearch`. `serper` without a key stops with the setup line. `websearch` forces native search even when the key is set |
| `--domain` | detected | Free-form hint that shapes vocabulary, source families and the reviewer persona in synthesis (security, law, finance, nutrition, anything) |

### 4.2 Phases

**Phase 0, pre-flight.** Parse flags. Detect the backend (`SERPER_API_KEY` present, `WebSearch` in the toolset). If neither search path is available, stop with the reason before any plan. Confirm the question is about external knowledge; if it is about local code, say so and stop (unchanged rule).

**Phase 1, clarify** (skipped by `--no-clarify` and `--auto`). Read the question for ambiguity on: scope, audience and purpose (decision, overview, teaching), time window, geography or jurisdiction, what a good answer looks like (facts, comparison table, recommendation). If at least one dimension is genuinely open, ask 2-4 questions in **one** `AskUserQuestion` call, multiple choice where possible, and fold the answers into the restated question. If nothing is open, skip straight to the plan and say so in one line. Never ask for the sake of asking: a clear question gets no questions.

**Phase 2, plan** (shown for approval unless `--auto`). The lead writes:

- the restated question (after clarification);
- the tier chosen and why (one line);
- 3 to 12 sub-questions, each with: the source families it should draw on (official/primary, community/practitioner, comparative, recency/news, academic when relevant), and its boundary against its neighbours;
- the researcher assignment (one researcher per sub-question; closely related sub-questions may share one researcher at `quick`);
- estimated pages read, estimated wall time, backend in use, and for serper an approximate call count;
- the output path.

Present it via `AskUserQuestion` with options `Approve`, `Change depth`, `Edit the plan` (free text merged into the plan, then re-shown once). With `--auto` the plan is printed and execution starts. The approved plan is recorded verbatim in the report appendix.

**Phase 3, wave 1.** Spawn one `research:deep-researcher` per sub-question, **all in one message** so they run in parallel. Each spawn prompt carries the fixed block defined in section 5.4: objective, boundaries, budget, backend, domain hint, return format. The lead does not search during this phase.

**Phase 4, gap analysis.** Read every researcher report. Build three lists: contradictions between researchers, sub-questions left uncovered or thin (exit reason `budget-exhausted` or `target-not-found`, or fewer than two independent sources on the load-bearing claims), and new threads the researchers surfaced that the plan did not anticipate. Then:

- `quick`: no second wave; everything goes to limitations.
- `standard`: spawn `research:quick-searcher` in verifier mode for each contradiction (one per contested claim, parallel), and re-spawn once any researcher that returned empty or errored; no researchers for newly surfaced threads, which go to limitations.
- `deep`: spawn wave 2 in one message: one `deep-researcher` per uncovered or newly surfaced thread (capped so the total stays within the tier band), plus verifiers for contradictions. A researcher that returned empty or errored in wave 1 is re-spawned **once** with a reworded objective; if it fails again the gap is recorded. Wave 2 is the last wave; there is no wave 3.

**Phase 5, synthesis.** The lead writes the report described in section 6, in prose, from the compressed researcher reports only. The `--domain` persona is applied here: the lead writes as a senior practitioner of that domain would, which shapes emphasis and vocabulary, not the facts.

**Phase 6, citation check.** One pass over the draft against the merged source table: every factual claim carries at least one `[n]` that resolves to a source a researcher actually read; a claim with no resolvable source is rewritten as explicitly unverified or moved to limitations, never silently kept; every `[n]` in the sources section is cited at least once; dates and numbers quoted in the text match the source row. The pass is recorded as done in the run header.

**Phase 7, deliver.** Write the report file (`--out`) and, beside it, a companion `<report-stem>.researchers.md` holding every researcher and verifier report verbatim, in spawn order, each under a heading naming its wave and objective. The companion is Anthropic's "write subagent output to the filesystem" lesson applied at the only point the harness allows: the lead holds the reports once they return, so it saves them before compressing them into the appendix, and evals and readers audit claims against the researchers' own ledgers instead of against the lead's summary of them. Then print in chat: the run header, the executive summary, both paths, and the run metadata (tier, researchers spawned per wave, pages read, backend, wall time, failures).

### 4.3 Tiers

| Tier | Picked by `auto` when | Researchers | Pages read (target) | Waves | Per-researcher budget (searches / pages / rounds) |
|---|---|---|---|---|---|
| `quick` | One well-defined question with a small number of authoritative answers | 1-2 | ~10 | 1 | 8 / 6 / 2 |
| `standard` | A comparison, a "how do people do X", a bounded survey | 3-5 | 30-60 | 1 + verifiers | 15 / 12 / 4 |
| `deep` | Open-ended, multi-faceted, decision-grade, or explicitly "thorough" | 6-12 across two waves | 100+ | 2 + verifiers | 25 / 20 / 6 |

A one-fact question (single answer, single source) is not a tier: `auto` routes it to a direct `research:quick-searcher` call and says so. Budgets are planning-time caps written into the spawn prompt, as today; nobody counts runtime tool calls.

Calibration against the published numbers (section 11): `standard` at 3-5 researchers x 15 searches is 45-75 searches, which brackets Gemini's ~80 searches per Deep Research task and the 30-60 searches reported for OpenAI's; `deep` at 6-12 researchers x 25 searches is 150-300, above Gemini Max's ~160, which is the point: the top tier is the one people reach for when they want the run to be exhaustive, and cost is accepted for it. Pages read (30-60 standard, 100+ deep) sit under the "hundreds of sources" all four vendors claim, because a source here is a page actually read and entered in a ledger, not a search hit.

### 4.4 Failure handling

- Researcher returns empty or errors: recorded in the methodology appendix; re-spawned once with a reworded objective (deep and standard), then recorded as a gap.
- More than half the researchers of a wave fail: stop, report which failed and why, do not synthesize from scraps.
- `WebSearch` unavailable and no serper key: stop at pre-flight.
- `--backend serper` with no key: stop with the setup line (`export SERPER_API_KEY=...`, where to get a key).
- Bot-blocked or paywalled primary sources: listed by URL in limitations so the user can open them.
- File write fails (`--out` not writable): print the whole report in chat and say why.

## 5. The agents

### 5.1 `deep-researcher`: an iterative investigator of one sub-question

The self-orchestrating Mode A (the agent spawning `quick-searcher` sub-agents per angle) is deleted: orchestration now lives in the command. The old Mode B (execute yourself) becomes the only mode, and it is rebuilt around a loop. The agent stays directly invokable by a user for a one-sub-question investigation; when invoked without a lead's spawn block it runs at the `standard` per-researcher budget and returns the same report format.

Frontmatter: `tools: Read, WebSearch, WebFetch, Bash` (Bash for `webfetch.py` and `websearch.py`), `model: inherit`, `color: pink`. The `Agent` tool is removed.

### 5.2 The loop

1. **Orient**: 2-3 broad, short queries to map the terrain: vocabulary, the obvious primary sources, the competing claims. Short queries first; long precise ones only once the vocabulary is known.
2. **Read**: fetch the pages that matter (official docs, primary sources, high-signal threads) with `WebFetch`; on bot-block or thin content fall back to `webfetch.py`; if the `playwright-skill` plugin is installed, a browser drive is the last resort for a primary source that matters (prose pointer, not a dependency; skip silently when absent). Snippets qualify a page for reading; only read pages enter the ledger.
3. **Ledger**: after every round update a private ledger: claims (with the source id, the date the source carries, the source's authority rank), contradictions, open threads, queries tried.
4. **Narrow**: next round's queries come from the ledger's open threads and from vocabulary found in read pages. Never repeat a query; after 2 empty attempts on a thread, pivot or drop it.
5. **Stop** when any holds: two consecutive rounds add no new claim; the budget is spent; the sub-question is answered with at least two independent sources behind every load-bearing claim. Record the exit reason.
6. **Compress** into the return format (5.5). Raw page content never goes back to the lead.

Source quality gate on entry to the ledger: the skill's authority ranking, the date the page carries, and discard rules for SEO farms, AI rewrites and scraped aggregators. Prefer primary over secondary when both state the same thing; keep both when they disagree.

### 5.3 Backends in the loop

The spawn prompt names the backend. With `serper`, discovery runs through `websearch.py` (the `scholar` vertical for academic threads, `news` with `--since` for recency threads, `--num 30-50` for the orient round); with `websearch`, through the native tool. A claim whose sources surface on both indexes (when the researcher has both) is noted as cross-index corroborated. Reading is always `WebFetch` / `webfetch.py`; serper is never used to read.

### 5.4 Spawn block (written by the lead)

```
Role: researcher (wave 1 | wave 2)
Objective: <the sub-question, one paragraph, with what a complete answer contains>
Boundaries: <what neighbouring researchers cover; do not investigate it>
Source families: <official/primary | community | comparative | recency | academic>, in priority order
Domain hint: <--domain or detected>
Backend: websearch | serper   (serper: `python ${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py ...`)
Budget: <N> searches / <M> pages read / <R> rounds
Return format: the researcher report (section 5.5), nothing else
```

### 5.5 Researcher report (returned to the lead)

```
## Researcher report: <sub-question>
Exit reason: saturated | budget-exhausted | target-not-found | error
Rounds: R, searches: N, pages read: M, backend: websearch | serper

### Claims
1. <claim> [S1][S3]   (one sentence each; numbers carry date and unit)
...

### Sources read
| id | title | site | date carried | URL | authority rank (1-5) |

### Contradictions seen
- <claim A> [S2] vs <claim B> [S5]: <which is later / primary / more specific>

### Open threads
- <what surfaced that this researcher did not pursue, and why>

### Searched and not found
- <queries that returned nothing useful>
```

### 5.6 `quick-searcher`

Keeps its direct mode (single fact, 1-3 searches, lead with the answer) and its `sonnet` model. The old sub-unit mode (angle + budget from deep-researcher) is replaced by a **verifier mode**: the prompt carries one contested claim and the two conflicting sources; the agent finds a third independent source (different site, ideally a primary one), rules which version stands or that it cannot be settled, and returns claim, ruling, the third source with date, and its confidence. Budget 5 searches / 3 pages.

## 6. The report

File: `research/<YYYY-MM-DD>-<slug>.md` (slug from the restated question, ASCII, max 60 chars) or `--out`. Structure:

1. **Title and run header**: question as finally scoped; date; tier; researchers per wave; pages read; backend; wall time; "citation check: done".
2. **Executive summary**: the answer in 5-10 sentences, with overall confidence (high / medium / low) and the one-line reason for it.
3. **Key findings**: numbered, one sentence each, inline `[n]` citations.
4. **One section per sub-question**: prose, not bullet dumps. Comparison questions get a table. Numbers carry their date and unit. Disagreements are written out: "A reports X [3], B reports Y [7]; B is later and primary, so Y is taken".
5. **Contradictions and resolutions**: the explicit ledger, including verifier rulings.
6. **Confidence and limitations**: what rests on one source; what could not be verified; what was out of scope; paywalled or bot-blocked URLs.
7. **Sources**: `[n] Title, site, date carried by the page, URL, authority rank`, ordered by first citation. Only sources a researcher read.
8. **Methodology appendix**: the approved plan verbatim; per researcher: objective, exit reason, budget used, queries (compressed); failures and re-spawns.

Length by tier: quick 1-2 pages, standard 4-8, deep 10-25. In chat: sections 1-2 plus the path and run metadata.

## 7. The optional serper.dev backend

### 7.1 Script: `plugins/research/scripts/websearch.py`

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py "<query>" [--vertical search|news|scholar]
       [--num N] [--since h|d|w|m|y] [--gl <cc>] [--hl <lang>] [--page P] [--json] [--timeout S]
```

- Stdlib only (`urllib.request`, `json`, `argparse`, `os`). No new dependency.
- Reads `SERPER_API_KEY` from the environment; header `X-API-KEY`; `POST https://google.serper.dev/<vertical>` with JSON body `{q, num, gl, hl, page, tbs}` (`--since` maps to `tbs=qdr:h|d|w|m|y`). `--num` defaults to 10 and is capped at 100; the script prints a one-line stderr note the first time a call asks for more than 10, since that costs two credits instead of one. Google operators (`site:`, quotes, `-term`, `filetype:`, `before:`/`after:YYYY-MM-DD`) pass through inside the query string.
- Default output: a compact list, one result per block: rank, title, URL, snippet, date when the API returns one; then answer box, knowledge graph and "people also ask" when present. `--json` prints the raw response.
- Exit codes: 0 success; 1 HTTP error, timeout, malformed response (one line on stderr); 2 key missing (stderr: the setup line). Agents pivot on non-zero, never retry in a loop.
- UTF-8 forced on stdout (same Windows guard as `webfetch.py`).
- Lives beside `webfetch.py`; the export mirrors it into the skill directory as it does `webfetch.py` (the `downstream-exports` source map already carries that rule for plugin-root content).

### 7.2 Rules

- **Never required.** Absence of the key changes the backend, nothing else. No prompt, no warning beyond the plan line "backend: websearch".
- **Always reported**: in the plan, in every spawn block, in the report header.
- **Snippets never become claims.** Serper qualifies pages for reading; reading is `WebFetch`/`webfetch.py`.
- **Cost stated once**: the plan carries an approximate call count for the tier when serper is active; the skill notes the free tier and the paid pricing with the date checked.
- **Provider interface**: the script is written so a second provider (Tavily, Exa) would be one more request builder and response normalizer behind the same CLI. Not built; one line in the skill. serper's own `scrape.serper.dev` page scraper is likewise noted and not wired: `webfetch.py` already covers the fetch fallback, and a second paid fetch path would need its own evidence of being better.

### 7.3 Skill section

`web-search-techniques/SKILL.md` gains a "Search backends" section: the selection rule, when the serper verticals earn their call, the Google operators serper honours (`site:`, quotes, `-term`, `filetype:`), `--since` for recency, cross-index corroboration, and the cost note.

## 8. Evals: `evals/research/`

Same shape as `evals/ai-tooling/`: behavioural invariants over a transcript and the produced file, never answer keys, never shipped, not registered in `marketplace.json`. Cases (each a `cases/NN-<slug>.md` with the question, flags, the invariant, and how to check it):

1. Without `--auto`, the plan is shown before the first search.
2. A clear question gets no clarifying questions; an ambiguous one gets at most four, in one call.
3. No claim in the report cites a source absent from the sources table.
4. Every source in the table appears in some researcher's "Sources read" (nothing cited from a snippet alone).
5. The backend is stated in the header, and `--backend serper` without a key stops with the setup line.
6. Researcher counts stay inside the tier band; `deep` runs exactly two waves at most.
7. A one-fact question is routed to `quick-searcher` rather than spawning researchers.
8. A wave where more than half the researchers fail stops the run instead of synthesizing.

Plus `README.md` (protocol), `RESULTS.md` (runs), `scorecard-template.md`.

## 9. Repository obligations

- `research` 5.0.0 to **6.0.0** (flags, agent modes and the agent contract change). Marketplace 24.1.0 to **25.0.0**: the dependency set changes (`agent-teams@claude-code-workflows` dropped; `dependencies: []`). Lint pass 8 stays satisfied (no unused hard dependency; nothing to declare).
- `marketplace.json` `research` description rewritten (it still describes Mode A/B).
- `CLAUDE.md`: the `research` paragraph (still says "declares `agent-teams@claude-code-workflows` (hard, team skills)" and "runs 2 to 4 `research:deep-researcher` instances over the source angles"), the list of four team pipelines that declare agent-teams (becomes three), and the dependency table.
- `README.md`: the plugin row, the dependency graph edge `research --> agentteams`, and the agent-teams prerequisite prose.
- `docs/plugins/research.md`: rewritten.
- `exports/vscode/CHANGELOG.md`: a `## 25.0.0` section.
- Export twins, adapted by hand per the `downstream-exports` skill: `exports/vscode/research/.github/agents/deep-researcher.agent.md`, `quick-searcher.agent.md`, `research-orchestrator.agent.md` (the export-only orchestrator, which carries the command's logic in VS Code since prompts cannot dispatch), `prompts/team-research.prompt.md`, `skills/web-search-techniques/SKILL.md`; `websearch.py` mirrored into the skill directory beside `webfetch.py`. Check with `python scripts/mirror_export.py --check --since origin/master`.
- `evals/research/` added.
- The plan ends at commit. No push.

## 10. Out of scope

- Reading local code (standing rule).
- Any dependency on another local plugin (standing rule).
- Tavily, Exa or other providers (interface note only).
- Images, PDFs beyond what `WebFetch` extracts.
- Persistent memory across runs.
- A VS Code-side clarification gate beyond what `vscode/askQuestions` already gives the export orchestrator.
- Interrupting a run to refine focus mid-flight (OpenAI and Perplexity offer it). The harness has no channel for it: an interrupted run is a stopped run, and the user restarts with a narrower plan.
- Streaming key findings before the report (Perplexity). The lead prints nothing between the plan and the delivery beyond spawn visibility the harness already gives.

## 11. Verified facts about the real products

Collected 2026-08-23 by a browser-assisted research pass (openai.com, help.openai.com and perplexity.ai answer 403 to a plain fetch; they were read through a real Chromium session). Primary sources unless marked secondary. These are the facts the left column of section 2 and the calibrations in sections 4.3, 5.2 and 7 rest on.

**OpenAI Deep Research**
- Asks clarifying questions and shows an editable plan: "Deep research may ask clarifying questions to confirm your goals, alongside a research plan before it starts. You can review and edit that plan" (Help Center FAQ, updated 2026-08-15, https://help.openai.com/en/articles/10500283-deep-research-faq). Progress is visible and the run can be interrupted to refine focus or sources. The API has no plan step; the docs recommend an intermediate model to clarify intent and rewrite the prompt before the research model runs (https://developers.openai.com/api/docs/guides/deep-research).
- Iteration: "plan and execute a multi-step trajectory ... backtracking and reacting to real-time information where necessary" (launch post, 2025-02-02, https://openai.com/index/introducing-deep-research/). API output exposes `web_search_call` items with actions `search`, `open_page`, `find_in_page`, plus reasoning items, then the final message.
- Duration and sources: "5 to 30 minutes", "hundreds of online sources" (launch post); API "can take tens of minutes", `max_tool_calls` is the cost knob. Secondary (PromptLayer, 2025-10-17): 30-60 searches and 120-150 page fetches per task.
- Output: structured report with citations, table of contents, "sources used" section, activity history; downloadable as Markdown, Word, PDF (Help Center). API: final text with `annotations[]` of `url`, `title`, `start_index`, `end_index`.
- Architecture: one RL-trained agent (o3 variant) with browsing and Python. API models `o3-deep-research-2025-06-26`, `o4-mini-deep-research-2025-06-26`; 200k context, 100k output, Responses API, background mode (https://developers.openai.com/api/docs/models/o3-deep-research).
- Stated limits: hallucinated facts, weak at separating authority from rumour, poor confidence calibration, citation formatting errors (launch post); read-only on connected apps (Help Center).

**Anthropic Research / Advanced Research**
- Agentic: "multiple searches that build on each other while determining exactly what to investigate next" (2025-04-15, https://claude.com/blog/research); Advanced Research "breaks down your request into smaller parts, investigating each deeply before compiling a comprehensive report", "hundreds of internal and external sources", most reports 5-15 minutes, up to 45 (2025-05-01, https://claude.com/blog/integrations; support article https://support.claude.com/en/articles/11088861-using-research-on-claude-ai).
- No primary source says it asks clarifying questions or shows a user-editable plan; the lead agent writes its plan to memory internally.
- Architecture (engineering post, 2025-06-13, https://www.anthropic.com/engineering/built-multi-agent-research-system): orchestrator-worker; lead plans, saves plan to memory, spawns parallel subagents each with its own context; subagents return condensed findings; a separate CitationAgent maps claims to sources at the end. Multi-agent beat single-agent by 90.2% on the internal eval; token usage explains 80% of variance on BrowseComp; parallel subagents and parallel tool calls cut time by up to 90%; multi-agent costs ~15x chat tokens.
- Delegation rule: each subagent gets objective, output format, tool guidance, clear boundaries. Effort scaling: simple fact = 1 agent, 3-10 tool calls; direct comparison = 2-4 subagents, 10-15 calls each; complex = 10+ subagents with divided responsibilities. Start wide then narrow; extended thinking as scratchpad; interleaved thinking after tool results.
- Eval: start with ~20 queries; LLM-as-judge rubric over factual accuracy, citation accuracy, completeness, source quality, tool efficiency; keep human eval for edge cases such as SEO farms chosen over authoritative sources.
- Production lessons: resume from checkpoint; full tracing; subagent outputs written to the filesystem to avoid lossy relay through the lead; subagent execution currently synchronous.
- Nothing newer on the Research feature found for 2026.

**Google Gemini Deep Research**
- Plan shown and editable before execution: submit, "Gemini creates a research plan", "Edit plan", "Start research" (https://support.google.com/gemini/answer/15719111; launch post 2024-12-11 https://blog.google/products/gemini/google-gemini-deep-research/). API: `agent_config.collaborative_planning=True` returns the plan for refinement over turns (https://ai.google.dev/gemini-api/docs/interactions/deep-research, updated 2026-08-11). No clarifying questions described.
- Four stages: planning, searching, reasoning, reporting; "hundreds of websites" (https://gemini.google/overview/deep-research/). App: about 5-10 minutes; API: most tasks within 20 minutes, cap 60.
- Published cost guide (API): Deep Research ~80 searches, ~250k input / ~60k output tokens, $1-3 per task; Deep Research Max ~160 searches, ~900k / ~80k, $3-7 (agents `deep-research-preview-04-2026`, `deep-research-max-preview-04-2026`; Max post 2026-04-21 https://blog.google/innovation-and-ai/models-and-research/gemini-models/next-generation-gemini-deep-research/).
- Output: multi-page report with sections and citations, export to Docs, Audio Overview, visualizations on Ultra.

**Perplexity Deep Research**
- "iteratively searches, reads documents, and reasons about what to do next, refining its research plan as it learns"; "dozens of searches, reads hundreds of sources"; 2-4 minutes (2025-02-14, https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research).
- "For broad queries, Research now asks clarifying questions before starting"; follow-ups can be added while running; key findings stream before the report; report lands in an editable file (Help Center, updated 2026-07-16, https://www.perplexity.ai/help-center/en/articles/13600190-what-s-new-in-advanced-deep-research). No user-editable plan.

**serper.dev**
- No public API reference is reachable (`/api-reference`, `/docs`, `/pricing` all 404); the homepage (read in a browser, 2026) is primary for endpoints, the sample response and pricing; parameter semantics come from client libraries (secondary: LiteLLM docs https://docs.litellm.ai/docs/search/serper, Flowise issue #6541 of 2026-06-22, the LangChain wrapper).
- Verticals at `https://google.serper.dev/<type>`: `search`, `news`, `images`, `places`, `maps`, `videos`, `shopping`, `scholar`, `patents`, `autocomplete`; a page scraper at `https://scrape.serper.dev` (POST `{url, includeMarkdown}`; secondary, MCP server README).
- Request: POST JSON `q`, `gl` (default us), `hl` (default en), `location`, `num` (default 10), `page`, `tbs` (`qdr:h|d|w|m|y`), `autocorrect`; Google operators (`site:`, `filetype:`, `before:`/`after:` YYYY-MM-DD) work inside `q`. Auth header `X-API-KEY`.
- Response (homepage sample): `knowledgeGraph{...}`, `organic[]{title, link, snippet, position, sitelinks[], date?}`, `peopleAlsoAsk[]`, `relatedSearches[]`; clients also read `answerBox`, `topStories`, `searchParameters`, `credits`.
- Pricing (homepage): 2,500 free queries, no card; Starter $50 for 50k credits ($1.00/1k, 50 qps); Standard $375 for 500k ($0.75/1k); Scale $1,250 for 2.5M ($0.50/1k); Ultimate $3,750 for 12.5M ($0.30/1k). Credits valid 6 months, deducted only on successful responses, 1-2 s typical latency. Secondary: `num` above 10 (up to 100) costs 2 credits per query.
- Alternatives, for the interface note only: Tavily (Bearer auth, LLM-ready snippets and optional `raw_content`, `search_depth`, `topic` general/news/finance; https://docs.tavily.com/documentation/api-reference/endpoint/search); Exa (`x-api-key`, neural search with `text`/`highlights`/`summary` per result; https://exa.ai/docs/reference/search). Serper is a raw Google SERP proxy: cheapest per call, snippets only unless the scrape endpoint is also called.

**Gaps left by the pass**: no official serper parameter reference; the clarifier model in the OpenAI API guide; current ChatGPT per-plan quotas; o4-mini-deep-research pricing; any Anthropic 2026 publication on Research; Gemini app source counts and Max benchmark numbers.
