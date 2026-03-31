# AI Tooling Plugin

> Think before you build. Structured brainstorming, planning, and execution workflows that prevent wasted effort and keep complex projects on track.

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

### `brainstorming`

Explore user intent, requirements, and design before any creative or implementation work.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Feature design, requirements exploration, creative ideation |

**Source:** Ported from [obra/superpowers](https://github.com/obra/superpowers).

---

### `writing-plans`

Create structured implementation plans from specs or requirements before touching code.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Multi-step task planning, spec-to-plan conversion |

**Source:** Ported from [obra/superpowers](https://github.com/obra/superpowers).

---

### `executing-plans`

Execute written implementation plans in a separate session with review checkpoints.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Plan execution, checkpoint reviews, staged implementation |

**Source:** Ported from [obra/superpowers](https://github.com/obra/superpowers).

---

### `acp-loader`

Skill activation engine that checks every installed skill against the current task. Fires at conversation start and before every task.

| | |
|---|---|
| **Invoke** | Runs automatically at conversation start and before tasks -- not manually invoked |
| **Use for** | Proactive skill discovery and activation |

**Behavior:** Invokes any skill with even a 1% chance of relevance to the current task. User instructions always override skill directives. Skips activation when running as a subagent.

---

### `claude-agent-sdk`

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

**Related:** [agent-teams](agent-teams.md) (`/team-feature` and `/team-design` use brainstorming, writing-plans, executing-plans) | [acp-hooks](acp-hooks.md) (acp-loader skill awareness)
