---
name: web-search-techniques
description: >
  Knowledge base for web research: query formulation, source authority ranking, the two search
  backends (native `#websearch`, optional serper.dev through websearch.py), reading pages with
  `#web/fetch` and the webfetch.py bot-block fallback, and the anti-loop rules. Used by
  quick-searcher, deep-researcher and `/team-research`. Use when performing web research with
  `#websearch`, `#web/fetch`, or the bundle's scripts. Not for searching a local codebase (use
  `#search/textSearch` or `#search/fileSearch` directly).
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: research
---

# Web Search Techniques

Shared knowledge base for `quick-searcher`, `deep-researcher` and the `/team-research` lead. Scope: web-only. Covers query formulation, source authority, tool usage, bot-block fallback, and anti-loop rules.

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

1. **Official documentation sites and API references**: highest authority
2. **RFC and specification documents**: canonical for standards
3. **GitHub issues, discussions, and source code**: authoritative for specific libraries
4. **Peer-reviewed or community-validated content**: Stack Overflow with high votes, maintainers' blogs
5. **General blog posts and tutorials**: use only when nothing better exists
6. **Deprioritize**: SEO content farms, AI-generated summaries, scraped aggregators

Currency checks:
- Last modified date on the page
- Version numbers cited vs latest release
- Deprecation warnings

## Search Backends

Two backends produce candidate pages. Neither produces claims: only a page that was read does.

`$SKILLS` is the installed skills directory: the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists.

| Backend | When | How |
|---|---|---|
| Native `#websearch` | Default. Always available when the tool is in the toolset | The tool call, with the operators below |
| serper.dev (Google) | `SERPER_API_KEY` is set, or `--backend serper` | `python $SKILLS/web-search-techniques/scripts/websearch.py "<query>" [--vertical search|news|scholar] [--num N] [--since h|d|w|m|y] [--gl CC] [--hl LANG] [--page P] [--json]`, run in the terminal |

Selection rule (the lead decides once per run and writes it into every spawn prompt): `auto` means serper when the key is set, else native. The chosen backend is stated in the plan, in each researcher report and in the final report header. A run never silently falls back: if serper was forced and the key is missing the script exits 2 with the setup line, and the run stops there.

What serper earns its call for:
- `--vertical scholar` for academic threads, `--vertical news --since w|m` for recency threads
- `--num 30` to `50` on the orient round, to map a topic's vocabulary in one call (above 10 results costs 2 credits; the script says so on stderr)
- `--since` for "what changed lately" questions; `before:YYYY-MM-DD` / `after:YYYY-MM-DD` inside the query for exact windows
- Cross-index corroboration: a claim whose sources surface on both indexes ranks above one found on one index only

Operators both backends honour: `site:` (restrict to a domain), `"exact phrase"`, `-term` (exclude), `filetype:pdf`, a year token (`2026`) for temporal queries, `official` or `documentation` to bias toward primary sources, version numbers when relevant (`react 19`).

Cost note (checked 2026-08-23): serper.dev gives 2,500 free queries, then $1.00 per 1,000 on the entry plan, down to $0.30 per 1,000 at volume; credits are deducted only on successful responses. A `standard` run makes on the order of 50-80 calls, a `deep` run 150-300. Tavily and Exa are LLM-oriented alternatives (LLM-ready snippets, neural search) that would slot behind the same script interface; not built.

## Reading, Not Skimming

A search result is a candidate. A claim enters a researcher's ledger only from a page that was read:
1. `#web/fetch` the page (prefer docs and primary sources; target anchors on long pages)
2. On a bot-block (403, 429, challenge page) or thin content (under ~200 useful characters), `python3 $SKILLS/web-search-techniques/scripts/webfetch.py <url>`
3. If a browser-automation MCP server is configured and the page is a primary source the answer depends on, drive a real browser with it as the last resort; if none is configured, record the URL under limitations and move on. This is a pointer, not a dependency.
4. Record: URL, title, the date the page carries, authority rank (below), and the claims taken from it

## `#web/fetch` Guidance

- Prefer documentation pages and API references over blog posts
- Evaluate fetched content: low-authority source means discard and re-search
- Large pages may be truncated: target specific sections (anchor URLs) when possible
- Track the accessed URL with date for citation

## webfetch.py Fallback

When `#web/fetch` returns a bot-block (403, 429, Cloudflare challenge) or thin content (under ~200 chars of useful text), fall back to the stealth fetcher shipped with this skill:

```bash
python3 $SKILLS/web-search-techniques/scripts/webfetch.py <url>
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

Requires the `#execute/runInTerminal` tool in the agent's `tools:` frontmatter.

## Anti-Loop Rules

- Never repeat the exact same query or search parameters
- If a search returns nothing, change terminology, broaden the regex, or switch tool/target
- Maximum 2 failed attempts per sub-topic before pivoting or escalating
- After 2 failed attempts on the same angle, document the gap and proceed with what you have
