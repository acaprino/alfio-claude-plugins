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

## Using it

### A first run

```
/research:team-research "How do Rust, Go and Zig handle error propagation, and what do practitioners complain about in each?"
```

What you will see, in order:

1. **A clarification prompt, only if the question is ambiguous.** Up to four multiple-choice questions in one dialog (scope, audience, time window, jurisdiction, what a good answer looks like). A clear question skips this step and the lead says so in one line. Answer with the `Other` field when none of the choices fit.
2. **The research plan**, as a dialog with three options: `Approve` runs it; `Change depth` re-plans at another tier; `Edit the plan` takes free text (drop a sub-question, add one, narrow the time window), merges it, and shows the plan once more. The plan lists the restated question, the tier and why, the backend, the sub-questions with their source families and boundaries, the researcher count, estimated pages read and time, and the output path.
3. **The run.** Researchers spawn in one batch; at `deep` a second batch follows the gap analysis. Nothing is printed between the plan and the delivery beyond the spawn activity the session already shows. `standard` takes on the order of 5-15 minutes, `deep` 15-40.
4. **The delivery**: run header, executive summary, the two file paths and the run metadata (tier, researchers per wave, pages read, backend, wall time, failures and re-spawns). The full report is in the file.

### Choosing the depth

`--depth auto` (the default) reads the question: one well-defined question with a few authoritative answers gets `quick`, a comparison or a "how do people do X" gets `standard`, an open-ended or decision-grade question gets `deep`. Force a tier when you know better: `--depth quick` for a cheap first pass you may deepen later, `--depth deep` when the report is going to drive a decision and you want the second wave and 100+ pages read. A single-fact question ("what is the default port of PostgreSQL") is not a research run at all: the lead answers it through `quick-searcher` with one source and writes no file.

### Reading the output

- `research/<date>-<slug>.md` is the report. Start from the executive summary and key findings; every `[n]` resolves to the Sources section, which lists only pages a researcher actually read, each with the date the page carries and an authority rank from 1 (official documentation) to 5 (general blog). The confidence and limitations section says what rests on one source, what could not be verified, and which primary sources were paywalled or bot-blocked, by URL, so you can open them yourself.
- `research/<date>-<slug>.researchers.md` is the companion: every researcher and verifier report verbatim, in spawn order. Use it to audit a claim back to the researcher that found it, or to see what was searched and not found.
- The methodology appendix holds the approved plan verbatim and, per researcher, the exit reason (`saturated`, `budget-exhausted`, `target-not-found`, `error`) and the budget used. A report whose researchers mostly exited `budget-exhausted` is one worth re-running at the next tier.

### Unattended runs

`--auto` skips both gates: the plan is printed and the run starts. Combine it with `--out` to land the report where you want it:

```
/research:team-research "State of WebGPU support across browsers" --auto --depth standard --out docs/research/
```

`--out` takes a file path or a directory; a directory gets the default filename inside it. `--no-clarify` is the half-way option: no clarification questions, but the plan still waits for approval.

### Enabling the serper.dev backend (optional)

By default the plugin searches with the session's native `WebSearch`. Setting a serper.dev key switches discovery to Google's index and adds the `news` and `scholar` verticals, date filters and up to 100 results per call; the report header then says `Backend: serper`.

1. Get a key at https://serper.dev (2,500 free queries, no card; then $1.00 per 1,000 on the entry plan, down to $0.30 per 1,000 at volume).
2. Export it in the environment Claude Code runs in: `export SERPER_API_KEY=...` (bash, zsh) or `$env:SERPER_API_KEY = "..."` (PowerShell). Put it in your shell profile to make it permanent; restart the session after setting it.
3. Run as usual. `--backend auto` (the default) picks serper whenever the key is present. `--backend websearch` forces the native tool even with the key set; `--backend serper` forces serper and stops with a setup line if the key is missing, so a run is never silently on the weaker index.

Cost per run, order of magnitude: `standard` makes 45-75 serper calls, `deep` 150-300; a call returning more than 10 results costs two credits. The plan states the approximate count before you approve it. Serper never replaces reading: snippets qualify a page for fetching, and only pages actually read are cited.

### When it stops instead of running

| Message | Cause | What to do |
|---|---|---|
| "No search backend available" | `WebSearch` is not in the session's toolset and no serper key is set | Enable web search for the session, or set `SERPER_API_KEY` |
| The `websearch.py` setup line | `--backend serper` was forced and the key is missing or the service failed | Set the key, or drop the flag to fall back to native search |
| "This command has no local-codebase capability" | The question is about local code | Use Grep, Glob, or a codebase-oriented plugin |
| "More than half the researchers failed" | The wave could not search or fetch (offline, blocked, quota) | Fix the connectivity and re-run; nothing is synthesized from a failed wave |

### Using the agents directly

`deep-researcher` can be invoked on its own for one focused investigation ("investigate X in depth across several sources, with citations"): it runs at the `standard` per-researcher budget and returns the same compressed report it would return to the lead. `quick-searcher` answers single facts with one source, and flags when a question actually needs a full run.

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
