# Research Plugin

> Deep web research modelled on the commercial deep-research products (clarify, plan, parallel iterative researchers, citation check, report file), plus quick single-fact lookups. Web only: it reads no local codebase and depends on nothing.

## Command

### `/research:team-research`

| | |
|---|---|
| **Invoke** | `/research:team-research "<question>" [--depth auto\|quick\|standard\|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto\|websearch\|serper] [--domain <hint>]` |
| **Writes** | `research/<YYYY-MM-DD>-<slug>.md` (or `--out`) and `<stem>.researchers.md` beside it |

Phases: pre-flight (backend detection), clarify (2-4 questions in one call, only when the question is ambiguous; `--no-clarify` skips), plan (sub-questions with source families and boundaries, shown for approval; `--auto` skips both gates), wave 1 (one `deep-researcher` per sub-question, parallel), gap analysis (verifiers on contradictions; at `deep` a targeted wave 2), synthesis (long-form report in prose), citation check (every claim resolves to a source a researcher read), deliver (file + companion + chat summary).

| Tier | Researchers | Pages read | Waves | Per-researcher budget |
|---|---|---|---|---|
| `quick` | 1-2 | ~10 | 1 | 8 searches / 6 pages / 2 rounds |
| `standard` | 3-5 | 30-60 | 1 + verifiers | 15 / 12 / 4 |
| `deep` | 6-12 | 100+ | 2 + verifiers | 25 / 20 / 6 |

`auto` picks the tier from the question; a one-fact question is answered by `quick-searcher` directly with no run. Report sections: run header, executive summary, key findings, one section per sub-question, contradictions and resolutions, confidence and limitations, sources (only pages actually read), methodology (the approved plan verbatim, per-researcher budgets and exit reasons).

```
/research:team-research "Best practices for WebSocket reconnection in 2026"
/research:team-research "GDPR retention rules for transaction logs" --domain law --depth deep
/research:team-research "Should we migrate from REST to gRPC?" --auto --out docs/research/
```

## Agents

### `deep-researcher`

Iterative investigator for one sub-question: orient with broad queries, read the pages that matter, keep a ledger (claims, sources with dates and authority rank, contradictions, open threads), narrow round by round, stop at saturation or budget, return a compressed cited report. Spawned by the command; directly invokable for one focused investigation.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, WebSearch, WebFetch, Bash |

### `quick-searcher`

Single-fact lookups (1-3 searches, lead with the answer) and the verifier the command spawns to settle one contested claim with a third independent source.

| | |
|---|---|
| **Model** | `sonnet` |
| **Tools** | Read, WebFetch, WebSearch, Bash |

## Skill

### `web-search-techniques`

Query formulation, source authority ranking, the two search backends, reading rules (WebFetch, then `webfetch.py` on a bot-block, browser only if `playwright-skill` happens to be installed), anti-loop rules. Loaded by both agents and the command.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/websearch.py` | Optional serper.dev backend. Used when `SERPER_API_KEY` is set or `--backend serper`; `--vertical search\|news\|scholar`, `--num`, `--since h\|d\|w\|m\|y`, `--gl`, `--hl`, `--json`. Exit 2 with a setup line when the key is missing, 1 on HTTP errors. Stdlib only |
| `scripts/webfetch.py` | Bot-block fallback fetcher (Chrome TLS impersonation via curl_cffi, httpx fallback) |

Backend rule: `auto` uses serper when the key is set, native `WebSearch` otherwise; the choice is stated in the plan, in each researcher report and in the report header. Serper never replaces reading: snippets qualify a page for fetching, only read pages are cited.

---

**Related:** [digital-marketing](digital-marketing.md) (SEO research and content strategy) | [learning](learning.md) (turn findings into a mind map)
