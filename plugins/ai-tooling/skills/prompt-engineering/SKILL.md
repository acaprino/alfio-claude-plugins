---
name: prompt-engineering
description: >
  Knowledge base behind the prompt-engineer agent and /prompt-optimize: the source-of-truth order for model facts, the model-class gate, and four on-demand references (reasoning patterns and token-efficient reasoning, output-shape enforcement down to small open-weight models, extraction prompting, dated vendor guidance).
  TRIGGER WHEN: designing, reviewing or optimizing a prompt, system message or agent instructions; forcing JSON or a schema out of a model, especially a small one such as Gemma; prompting for extraction (NER, relations, events, fields from documents); deciding whether a reasoning scaffold, few-shot examples or a thinking budget belongs in a prompt.
  DO NOT TRIGGER WHEN: building an agent on the Claude Agent SDK (use agent-sdk-builder), or the question is about a model's pricing or API surface with no prompt involved.
---

# Prompt engineering knowledge base

The `prompt-engineer` agent and the `/prompt-optimize` command carry the method: extract the
behavioral contract, classify the archetype, diagnose, rewrite, report the semantic diff, label
every claim predicted, measured or verified. This skill carries the knowledge the method draws
on, split into references that are read only when a task needs them. Read this file first; it
tells you which reference to open and what every reference assumes you already decided.

## Source of truth

Model facts move faster than any bundled document. Three tiers, stop at the first that answers:

1. **The target model's current official page.** Anthropic: "Prompting best practices" at
   platform.claude.com plus the per-model page. OpenAI: the Model guidance hub and the
   reasoning best-practices page at developers.openai.com. Google: the Gemini 3 developer
   guide and the Gemma prompt-formatting page at ai.google.dev. When a prompt ships to
   production, fetch the page and confirm any vendor fact the rewrite restates.
2. **A measurement on that model**, yours or a published one on the same model and task.
3. **These references.** Orientation, dated, quoted; never the authority over tier 1.

A fact you could not confirm is unconfirmed, not confirmed absent: tag it *(verify)* in the
rewrite rather than deleting it or letting it read as checked.

## What decays and what does not

| Shelf life | Content | Lives in |
|---|---|---|
| **Stable** | The method: behavioral contract, archetype-aware rubric, semantic diff, epistemic labels, audit depth | the `prompt-engineer` role |
| **Slow** | The pattern catalog, the extraction shapes, the enforcement ladder | `reasoning-patterns.md`, `extraction-prompting.md`, `structured-output.md` |
| **Model-sensitive** | Thinking modes, effort names, prefill, cache multipliers, structured-output support, Gemma templates, the model-fit rows below | `model-guidance.md`; refresh every three months, like the `agent-sdk-builder` skill |
| **Measured and dated** | Every number with an arXiv ID or a vendor benchmark | the reference that cites it; each carries its check date |

## The model-class gate

Every reference assumes this decision was made first. Turn the target model into a class, then
read the row; the vendor matters less than the class.

| Class | Examples | Thinking control | Reasoning scaffold | Examples | Output shape | Measure first |
|---|---|---|---|---|---|---|
| **Frontier reasoning model** | Claude 4.6 and later, the Claude 5 family, GPT-5.x and GPT-6, Gemini 3, o-series, DeepSeek R1 by API | The native setting: `effort` on Claude (`budget_tokens` returns 400 from 4.7 on), `reasoning_effort` on OpenAI, `thinking_level` on Gemini 3 | None by default; a brief explicit plan only at the lowest effort setting | Zero-shot first; input and output only; never worked reasoning traces | Ask first, retries second, API structured outputs or an enum tool third; last-turn prefill is gone on Claude 4.6 and later | Overthinking cost on easy inputs; parse-failure rate if parsed |
| **Hybrid open reasoner** | Qwen3, Gemma 4, DeepSeek V3.x, gpt-oss | Mode tokens or a thinking prefill, not prose; depth self-selection at 9B and below, draft-agreement routing from 8B to 32B | None by default; the reasoning-patterns reference names the training-free options | Zero-shot first; input and output only | Constrained decoding in the serving stack; the schema in the prompt is a courtesy, not the enforcement | Think versus no-think per task; output validity |
| **Small open-weight instruct model** | Gemma 3, Llama 3.x 8B, Phi-4-mini, Mistral Small, anything under roughly 30B on Ollama, llama.cpp, vLLM or Transformers | None | A per-model choice: CoT measured anywhere from a gain to a 56-point loss on this class, so test zero-shot first | Input and output only, delimiter pinned, retrieved rather than random for extraction, kept short | Validate-and-repair at minimum, constrained decoding when the stack offers it; the format instruction alone is never the enforcement (prompt-only validity measured 61% to 92% below 8B); prefilling the opening brace is still available when thinking is off | Output validity before anything else; then answer accuracy and the wrong-but-valid rate as separate numbers |
| **Older non-reasoning model** | GPT-4 class, Claude 3.x, Gemini 2.x without thinking | Not applicable | The classic catalog applies; CoT pays on math, logic and symbolic tasks and adds variance elsewhere | 3-5 diverse examples in delimited blocks | JSON mode where the API has it; prefill on Claude 4.5 and earlier; validate-and-repair | Format drift across runs |

A model that fits two rows (a Gemma 4 served through Ollama with thinking off) takes the more
conservative row for output shape and the more specific row for thinking control.

## Reference router

| You need to decide | Read | It settles |
|---|---|---|
| Whether any reasoning scaffold belongs in the prompt, which one, and what it costs in tokens; how to build the efficiency pole of a variant frontier | `references/reasoning-patterns.md` | The selection cheat sheet, the reasoning-model defaults per class, the token-efficient patterns, cost-aware selection |
| How to make the model return JSON, a schema, an enum or a fixed template, and what holds on a small model | `references/structured-output.md` | The enforcement ladder, per-rung costs, reason-then-format ordering, the measured compliance of prompt-only techniques, serving-stack options |
| How to prompt for NER, relation or event extraction, document fields, tables, classification | `references/extraction-prompting.md` | The per-task shapes, what fails, the error taxonomy to diagnose against, the small-model order of operations |
| What a vendor currently says about a named model before restating it | `references/model-guidance.md` | Quoted, dated vendor statements and their consequence for a prompt |

Skip every reference for a prompt that is purely persona or single-turn free-text generation
with no reasoning component, no parsed output and no cost constraint. That is the quick pass in
the role's audit-depth rule, and it stays cheap on purpose.

## Two rules every reference shares

- **A number in these files is measured on the model it names and predicted on yours.** Apply
  it as a hypothesis, then run the eval the reference ends with. The epistemic labels in the
  `prompt-engineer` role are not optional vocabulary.
- **The efficiency pole is the caller's to pick, never the optimizer's.** Where a technique
  trades accuracy for tokens, present both ends with costs and let the caller choose.
