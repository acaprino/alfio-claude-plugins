# AI Tooling Plugin

> Prompt engineering knowledge base and optimization, and Agent SDK guidance.

**Note:** the `acp-loader` skill was removed in ai-tooling 4.0.0, together with the `acp-hooks` plugin that injected it at session start. Its generic behavior (check for a relevant skill before acting) is covered by the superpowers `using-superpowers` skill, which loads itself through its own SessionStart hook.

**Note:** the `brainstorming`, `writing-plans`, and `executing-plans` skills used to live here as ports of [obra/superpowers](https://github.com/obra/superpowers). They were removed in ai-tooling 3.0.0: superpowers maintains them upstream and ships the full methodology around them. Since ai-tooling 3.1.0, superpowers is a declared hard dependency of this plugin, not an optional companion. See the [README](../../README.md#brainstorming-planning-and-execution) for install instructions.

## Agents

### `prompt-engineer`

Authors, restructures and evaluates the text that steers a model. It carries the method: it extracts a prompt's behavioral contract before touching it, classifies the archetype and scores only the rubric dimensions that archetype wants, rewrites, reports a semantic diff of what changed in behavior rather than in wording, and labels every quality claim predicted, measured or verified.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | System prompts, agent instructions, few-shot design, token optimization, output-shape enforcement, extraction prompts, prompt evals |

**Invocation:**
```
Use the prompt-engineer agent to optimize [prompt/system]
```

**Audit depth:** a quick pass for throwaway prompts (contract, defects, rewrite), a deep pass for anything that is a system prompt, drives a tool loop, ships to production, is parsed downstream or handles untrusted input. The deep pass loads only the references the task needs from the `prompt-engineering` skill.

---

## Skills

### `prompt-engineering`

The knowledge base behind the agent and the command, loadable on its own. Its `SKILL.md` carries the source-of-truth order for model facts (the vendor's current page, then a measurement, then the bundled references), the model-class gate every recommendation is made against (frontier reasoning model, hybrid open reasoner, small open-weight instruct model, older non-reasoning model), and a router to four on-demand references:

| Reference | Covers |
|---|---|
| `reasoning-patterns.md` | Chain-of-Thought, Step-Back, Self-Consistency, Tree-of-Thought, ReAct, Reflexion, Plan-and-Solve, Least-to-Most, Self-Ask, Skeleton-of-Thought; the token-efficient patterns (Chain of Draft, Concise CoT, token-budget prompting, Sketch-of-Thought); how reasoning models, hybrid open reasoners and small open models change the defaults; cost-aware selection |
| `structured-output.md` | Forcing JSON, a schema, an enum or a template: the enforcement ladder from format instruction to validate-and-repair to API structured outputs to constrained decoding, what each rung costs, and what holds on small open-weight models such as Gemma |
| `extraction-prompting.md` | Per-task prompt shapes for NER, relation and event extraction, schema-guided document and table extraction, with measured gains, failure modes and the small-model order of operations |
| `model-guidance.md` | What Anthropic, OpenAI and Google currently say about their models, quoted and dated: thinking modes, effort, prefill, caching, structured outputs, Gemma templates |

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | designing, reviewing or optimizing a prompt; forcing JSON or a schema from a model; prompting for extraction; deciding on a reasoning scaffold, examples or a thinking budget |

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

Analyzes a prompt in one `prompt-engineer` pass and presents the efficiency-versus-effectiveness frontier as labelled variants (max effectiveness, balanced, max efficiency), each with a token estimate, the technique applied, the enforcement rung it assumes when the output is parsed, what it gives up, and the behavioral changes it makes. The user picks the pole; `--optimize-for` skips the question for a user who already knows it, and `--compare` forces the full frontier.

```
/prompt-optimize "You are a helpful assistant that..." --optimize-for tokens
/prompt-optimize prompts/extract.md --model gemma-3-12b
```

**Flags:** `--model claude|gpt|gemini|<open-weight model name>` (the analysis turns it into a model class), `--optimize-for clarity|tokens|reliability`, `--compare`.

**Phases:** Analyze (contract, archetype, model class, usage profile, reasoning-pattern, output-shape and task-family checks) -> Variant frontier -> The user picks -> Deliver with test inputs.

---

**Related:** upstream wshobson/agents agent-teams (generic team orchestration); local team pipelines live in senior-review, codebase-xray, codebase-mapper, research
