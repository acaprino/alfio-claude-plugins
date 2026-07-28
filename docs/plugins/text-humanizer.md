# Text Humanizer Plugin

> Remove AI writing traces from any prose, in any language. A self-contained leaf plugin (zero dependencies) extracted from digital-marketing in marketplace 13.3.0, consumed by digital-marketing, codebase-mapper, business, and clean-code.

## Agents

### `text-humanizer`

Expert editor agent that removes AI writing traces from prose, articles, blog posts, and documentation. Detects 24 patterns (inflated symbolism, promotional language, AI vocabulary, filler phrases) and rewrites for natural human voice with a self-evaluation pass.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Humanizing AI-generated text, rewriting AI-sounding copy, polishing articles / blog posts / documentation prose |

**Invocation:**
```
Use the text-humanizer agent to humanize [file or pasted text]
```

Runs in two passes: (1) pattern-removal rewrite, (2) self-evaluation that flags any remaining AI tells and revises. Preserves tables and factual content, enforces a zero dashes-as-connectors policy, and returns a brief quality score (Directness, Rhythm, Trust, Authenticity, Refinement).

---

## Skills

### `anti-ai-writing-patterns`

Knowledge base listing 24 common AI-writing patterns (inflated symbolism, promotional language, formulaic sentence structures, etc.) and rewrite guidelines, based on Wikipedia's "Signs of AI writing" page. Loaded by the `text-humanizer` agent and `/humanize-text` command.

| | |
|---|---|
| **Invoke** | Skill reference (auto-loaded by humanize workflows) |
| **Trigger** | Editing or reviewing text to remove AI traces |

**Pattern categories:** inflated significance, promotional language, AI vocabulary, filler phrases, formulaic intros / conclusions, em-dash overuse, tricolon overuse, "not just X but Y" pattern, hedged certainty, and 15 more, plus a "personality and soul" section on avoiding sterile, voiceless prose.

---

## Commands

### `/humanize-text`

Remove AI writing traces from text. Detects 24 patterns and rewrites for natural human voice with a self-evaluation pass.

```
/humanize-text path/to/article.md
/humanize-text "paste prose directly here"
/humanize-text path/to/article.md --score   # include self-eval pattern-scan score
```

Delegates to the `text-humanizer` agent. See the `anti-ai-writing-patterns` skill for the 24-pattern catalog. For source code readability use `/clean-code:clean-code` instead.

---

## Ecosystem Integration

Consumers across the marketplace:

- **digital-marketing**: `/llm-seo-audit` and the `llm-seo-optimize` agent route AI-sounding copy to `/text-humanizer:humanize-text` to raise E-E-A-T credibility.
- **codebase-mapper**: `/docs-create` and `/humanize-docs` run the agent as their final AI-trace-removal pass on generated documentation.
- **business**: the `business-planner` agent humanizes the GTM strategy deliverable before hand-off.
- **clean-code**: routes prose targets here (`/clean-code:clean-code` handles source code, `/humanize-text` handles text).

---

**Related:** [digital-marketing](digital-marketing.md) (SEO and content workflows) | [codebase-mapper](codebase-mapper.md) (documentation generation) | [clean-code](clean-code.md) (source code readability)
