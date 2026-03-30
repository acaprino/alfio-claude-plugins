# Prompt Improver Plugin

> Intelligent prompt optimization -- enriches vague prompts with research-based clarifying questions before Claude Code executes them. Runs automatically via a UserPromptSubmit hook.

**Upstream:** [severity1/claude-code-prompt-improver](https://github.com/severity1/claude-code-prompt-improver)

## How It Works

A `UserPromptSubmit` hook intercepts prompts before execution. If the prompt is vague (missing specifics, context, or a clear target), the hook invokes the `prompt-improver` skill to research the codebase and generate targeted clarifying questions.

**Flow:** User prompt -> hook evaluates vagueness -> skill runs research + questions -> enriched prompt executes

## Skills

### `prompt-improver`

Transforms vague prompts into actionable requests through systematic research and targeted clarification.

| | |
|---|---|
| **Invoke** | Automatic via hook, or manual skill reference |
| **Trigger** | Vague prompts missing specifics, context, or clear target |

**4-phase workflow:**
1. **Research** - Check conversation history, review codebase structure, read docs, search for patterns
2. **Question generation** - Ask 3-5 targeted questions grounded in research findings (not generic)
3. **Enrichment** - Incorporate answers into an improved, actionable prompt
4. **Execution** - Run the enriched prompt with full context

**Reference files:**
- `references/question-patterns.md` - Taxonomy of clarifying question types
- `references/research-strategies.md` - Strategies for codebase and web research
- `references/examples.md` - Before/after prompt improvement examples

## Hooks

### `improve-prompt.js` (UserPromptSubmit)

Evaluates incoming prompts for vagueness and triggers the skill when enrichment is needed.

| | |
|---|---|
| **Handler** | `hooks/handlers/improve-prompt.js` |
| **Event** | `UserPromptSubmit` |
| **Timeout** | 5s |

---

**Related:** [ai-tooling](ai-tooling.md) (prompt-optimize command) | [acp-hooks](acp-hooks.md) (other session hooks)
