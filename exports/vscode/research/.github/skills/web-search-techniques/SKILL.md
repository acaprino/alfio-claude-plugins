---
name: web-search-techniques
description: >
  Knowledge base for web search query techniques, source authority ranking, `#web/fetch` and
  `#websearch` best practices, and bot-block fallback via webfetch.py. Used by quick-searcher and
  deep-researcher in this bundle. Use when performing web research with `#websearch` or
  `#web/fetch`. Not for searching local codebase (use `#search/textSearch` or `#search/fileSearch`
  directly).
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: research
---

# Web Search Techniques

Shared knowledge base for `quick-searcher` and `deep-researcher`. Scope: web-only. Covers query formulation, source authority, tool usage, bot-block fallback, and anti-loop rules.

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

## `#websearch` Techniques

Query operators (standard search-engine conventions, usually respected by `#websearch`):
- `site:` -- restrict to a domain
- `"exact phrase"` -- match the phrase verbatim
- Year token -- add "2026" for recency
- `"official"` or `"documentation"` -- bias toward authoritative
- Version numbers when relevant (e.g. `react 19`)

## `#web/fetch` Guidance

- Prefer documentation pages and API references over blog posts
- Evaluate fetched content -- low-authority source means discard and re-search
- Large pages may be truncated -- target specific sections (anchor URLs) when possible
- Track the accessed URL with date for citation

## webfetch.py Fallback

When `#web/fetch` returns a bot-block (403, 429, Cloudflare challenge) or thin content (under ~200 chars of useful text), fall back to the stealth fetcher shipped with this skill:

```bash
python3 $SKILLS/web-search-techniques/scripts/webfetch.py <url>
```

`$SKILLS` is the installed skills directory: the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists. When this bundle is installed as an agent plugin rather than copied into the workspace, the skill lives outside all four; in that case resolve `scripts/webfetch.py` relative to this file.

Behavior:
- Impersonates Chrome TLS fingerprint via curl_cffi
- Returns clean extracted text on stdout
- Exits 0 on success, 1 on timeout or error
- On failure, proceed without the result (do not retry in a loop)

Invocation options:
- `--timeout SECONDS` (default: 30)
- `--max-chars CHARS` (truncate output)
- `--raw` (return raw HTML instead of extracted text)

Requires `#execute/runInTerminal` tool in the agent's `tools:` frontmatter.

## Anti-Loop Rules

- Never repeat the exact same query or search parameters
- If a search returns nothing, change terminology, broaden the regex, or switch tool/target
- Maximum 2 failed attempts per sub-topic before pivoting or escalating
- After 2 failed attempts on the same angle, document the gap and proceed with what you have
