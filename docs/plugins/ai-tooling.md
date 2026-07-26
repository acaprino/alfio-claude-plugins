# AI Tooling Plugin

> Prompt engineering, skill activation, and Agent SDK guidance. The layer that makes Claude Code use the right tool for the job.

**Note:** the `brainstorming`, `writing-plans`, and `executing-plans` skills used to live here as ports of [obra/superpowers](https://github.com/obra/superpowers). They were removed in ai-tooling 3.0.0: superpowers maintains them upstream and ships the full methodology around them. Since ai-tooling 3.1.0, superpowers is a declared hard dependency of this plugin, not an optional companion. See the [README](../../README.md#brainstorming-planning-and-execution) for install instructions.

## Agents

### `prompt-engineer`

Expert prompt engineer for designing and optimizing LLM prompts.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Prompt design, token optimization, A/B testing, production systems |

**Invocation:**
```
Use the prompt-engineer agent to optimize [prompt/system]
```

**Prompt patterns:**
- Zero-shot / Few-shot prompting
- Chain-of-thought / Tree-of-thought
- ReAct pattern
- Constitutional AI
- Role-based prompting

---

## Skills

### `acp-loader`

Skill activation engine that checks every installed skill against the current task. Fires at conversation start and before every task.

| | |
|---|---|
| **Invoke** | Runs automatically at conversation start and before tasks -- not manually invoked |
| **Use for** | Proactive skill discovery and activation |

**Behavior:** Invokes any skill with even a 1% chance of relevance to the current task. User instructions always override skill directives. Skips activation when running as a subagent.

---

### `agent-sdk-builder`

Build apps with the Claude Agent SDK (formerly Claude Code SDK). Covers programmatic agent orchestration, subagent management, custom tools, and deployment workflows.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | `claude-agent-sdk`, `@anthropic-ai/claude-agent-sdk`, "agent sdk", "build an agent", "programmatic claude", "sidecar" |

**Key distinction:** The Agent SDK (`claude-agent-sdk`) runs the full Claude Code agent loop with built-in tools. The Anthropic Client SDK (`anthropic`) is for raw API calls.

**Packages:**
| | TypeScript | Python |
|---|---|---|
| Install | `npm install @anthropic-ai/claude-agent-sdk` | `pip install claude-agent-sdk` |

---

## Commands

### `/prompt-optimize`

Analyze, score, and optimize prompts for LLMs -- evaluates clarity, specificity, structure, token efficiency, robustness, and output control. Shows before/after comparison.

```
/prompt-optimize "You are a helpful assistant that..." --optimize-for tokens
```

**Phases:** Analyze (6-dimension scorecard) -> Optimize -> Compare (before/after scores + token count)

---

**Related:** upstream wshobson/agents agent-teams (generic team orchestration); local team pipelines live in senior-review, deep-dive-analysis, codebase-mapper, research | [acp-hooks](acp-hooks.md) (acp-loader skill awareness)
