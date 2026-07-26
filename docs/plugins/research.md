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

Deep multi-source research with parallel investigators covering the local codebase, the web, and domain-specific expertise, synthesized into one report with confidence levels.

**Prerequisites:** requires the upstream `agent-teams` plugin (`wshobson/agents`, MIT) for the `agent-teams:team-composition-patterns` and `agent-teams:team-communication-protocols` skills:

```
/plugin marketplace add wshobson/agents
/plugin install agent-teams@claude-code-workflows
```

| | |
|---|---|
| **Invoke** | `/research:team-research <question-or-topic> [--scope codebase\|web\|all] [--domain security\|architecture\|frontend\|python\|tauri\|business] [--depth quick\|standard\|deep]` |

**Depth levels:**

| Depth | Researchers | Roles |
|-------|-------------|-------|
| `quick` | 2 | Codebase analyst + Web researcher |
| `standard` | 3 | Codebase analyst + Web researcher + Context builder (`codebase-mapper:codebase-explorer`) |
| `deep` | 4 | Codebase analyst + Web researcher + Context builder + Domain expert |

Codebase and web researchers both run as `research:deep-researcher` instances scoped to a different tool set (Grep/Glob/Read/Bash for the codebase angle, WebSearch/WebFetch for the web angle). The domain expert is auto-selected from `--domain` or the detected topic: `security-auditor`, `code-auditor`, `typescript-engineer`, `python-engineer`, `tauri-desktop`, `business-planner`, `distributed-flow-auditor`, or a general `deep-researcher` instance.

```
/research:team-research "How does the auth middleware chain work?" --scope codebase
/research:team-research "Best practices for WebSocket reconnection" --scope web --depth deep
/research:team-research "Should we migrate from REST to gRPC?" --depth deep --domain architecture
```

Synthesis cross-references codebase findings against web research and the domain expert's assessment, assigns an overall confidence level (High/Medium/Low), and lists open questions the researchers could not resolve.

---

**Related:** [digital-marketing](digital-marketing.md) (SEO research and content strategy) | [learning](learning.md) (turn findings into a mind map)
