# Research Plugin

> Search and research toolkit -- fast lookups and deep multi-source investigation with query optimization across codebases and web sources.

## Agents

### `quick-searcher`

Fast search agent for simple fact-finding, single-concept lookups, and quick answers.

| | |
|---|---|
| **Model** | `sonnet` |
| **Use for** | Quick fact-finding, single-concept lookups, simple queries |

**Invocation:**
```
Use the quick-searcher agent to find [specific fact/file/value]
```

### `deep-researcher`

Expert deep research agent for complex multi-source investigation requiring systematic coverage and cross-referencing.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Complex research, iterative refinement, multi-source cross-referencing, query optimization |

**Invocation:**
```
Use the deep-researcher agent to research [complex topic/question]
```

---

## Skills

### `web-search-techniques`

Shared knowledge base for web search: query techniques, source ranking, WebFetch guidance, and `webfetch.py` fallback for bot-blocked content. Loaded by both `quick-searcher` and `deep-researcher` agents so they don't duplicate content.

| | |
|---|---|
| **Invoke** | Skill reference (auto-loaded by research agents) |
| **Trigger** | Any web search work (operator selection, domain filtering, source quality assessment, WebFetch extraction) |

**Content:**
- Query operators and syntax (`site:`, `intitle:`, `filetype:`, `-exclusion`)
- Source ranking priorities (vendor docs > primary sources > community > aggregators)
- WebFetch guidance: when to fetch, anti-bot fallback via `${CLAUDE_PLUGIN_ROOT}/scripts/webfetch.py` (curl_cffi Chrome TLS impersonation)
- Anti-loop rules (never repeat a query verbatim; change terminology / broaden / switch domain)
- Citation format

---

**Related:** [digital-marketing](digital-marketing.md) (SEO research and content strategy) | [learning](learning.md) (turn findings into a mind map)
