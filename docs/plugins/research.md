# Research Plugin

> Search and research toolkit - fast lookups and deep multi-source investigation with query optimization across codebases and web sources.

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
| **Model** | `inherit` |
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

## Commands

### `/research:team-research`

Deep web research with parallel investigators covering complementary source angles plus domain-specific expertise, synthesized into one report with confidence levels. It researches the web and nothing else: it reads no local codebase and depends on no local plugin.

**Prerequisites:** requires the upstream `agent-teams` plugin (`wshobson/agents`, MIT) for the `agent-teams:team-composition-patterns` and `agent-teams:team-communication-protocols` skills:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

| | |
|---|---|
| **Invoke** | `/research:team-research <question-or-topic> [--domain <topic-domain>] [--depth quick\|standard\|deep]` |

**Depth levels:**

| Depth | Researchers | Roles |
|-------|-------------|-------|
| `quick` | 2 | The 2 most relevant source angles |
| `standard` | 3 | The 3 most relevant source angles |
| `deep` | 4 | 3 source angles + Domain expert |

Every researcher is a `research:deep-researcher` instance. The angle researchers each get one of the four angles the agent already classifies into (authoritative, community, comparison, recency), and no two get the same one: overlapping angles produce agreement that means nothing, since they read the same sources. The domain expert is a dedicated instance given a persona from `--domain` or the detected topic; any domain works (security, python, finance, nutrition, law), so the plugin stays usable on any subject. A question about local code belongs to Grep, Glob, or a codebase-oriented plugin: this command has no local-codebase capability and says so rather than improvising one.

```
/research:team-research "Best practices for WebSocket reconnection" --depth deep
/research:team-research "GDPR retention rules for transaction logs" --domain law
/research:team-research "Should we migrate from REST to gRPC?" --depth deep --domain architecture
```

Synthesis cross-references the angles against each other and against the domain expert's assessment, assigns an overall confidence level (High/Medium/Low), and lists open questions the researchers could not resolve. Agreement counts as evidence only across angles that read different source families; two researchers who read the same page agreeing counts once.

---

**Related:** [digital-marketing](digital-marketing.md) (SEO research and content strategy) | [learning](learning.md) (turn findings into a mind map)
