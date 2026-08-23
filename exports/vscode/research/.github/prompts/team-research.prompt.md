---
description: Deep web research run with clarification, plan approval, parallel iterative researchers, a citation check and a report written to disk. Web only.
argument-hint: <question> [--depth auto|quick|standard|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto|websearch|serper] [--domain <hint>]
agent: research-orchestrator
---

# Team Research

Run the deep research pipeline on `$ARGUMENTS` exactly as the `research-orchestrator` agent body describes: pre-flight (backend detection), clarify only when the question is ambiguous, plan for approval, wave 1 of `deep-researcher` instances in parallel, gap analysis with `quick-searcher` verifiers and a second wave at `--depth deep`, synthesis, citation check, and delivery of `research/<YYYY-MM-DD>-<slug>.md` (or `--out`) plus `<stem>.researchers.md`.

**This prompt researches the web, and only the web.** It never reads or searches a local codebase and dispatches nothing from another bundle. A question about local code belongs to `#search/textSearch`, `#search/fileSearch`, or a codebase-oriented bundle, not here.

Load the `web-search-techniques` skill before planning: it defines the two search backends (`#websearch`, and serper.dev through `websearch.py` when `SERPER_API_KEY` is set), the operators and the reading rules the dispatch blocks refer to.
