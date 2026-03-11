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

## Commands

### `/prompt-optimize`

Analyze, score, and optimize prompts for LLMs -- evaluates clarity, specificity, structure, token efficiency, robustness, and output control. Shows before/after comparison.

```
/prompt-optimize "You are a helpful assistant that..." --optimize-for tokens
```

**Phases:** Analyze (6-dimension scorecard) -> Optimize -> Compare (before/after scores + token count)
