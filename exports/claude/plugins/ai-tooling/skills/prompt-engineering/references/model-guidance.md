# Model guidance: what the vendors currently say

On-demand reference for the `prompt-engineer` agent and the `/prompt-optimize` command. This is
the **model-sensitive** file: every fact in it is a vendor statement about a named model on a
named page, checked on the date at the top of each section, and every one of them can be stale
by the time you read it. The source-of-truth order in `SKILL.md` puts the vendor page above this
file: when a prompt ships to production, fetch the page and confirm the fact before you rely on
it. Facts marked *(verify)* were located in search results but the page was not read at the last
refresh; treat them as unconfirmed.

The general method (the behavioral contract, the rubric, the semantic diff, the epistemic labels)
does not live here and does not decay with model releases.

## Anthropic (checked 2026-09-05)

The prompt-engineering docs are now one page, "Prompting best practices"
(platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices),
covering Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5, Opus 4.8, 4.7, 4.6, Sonnet 5, Sonnet
4.6 and Haiku 4.5, plus one page per model. The old per-technique URLs redirect to an overview
that calls it "the living reference". The standalone prefill page is gone.

| Topic | Current statement | Consequence for a prompt |
|---|---|---|
| Structure | "XML tags help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs"; consistent tag names; `<document index="n">` inside `<documents>` | XML when the prompt mixes kinds of content. The docs no longer say anything about headings sufficing for simple prompts; that half of the old rule is ours, predicted, not the vendor's |
| Role | "Setting a role in the system prompt focuses Claude's behavior and tone for your use case. Even a single sentence makes a difference" | One sentence of role, always. The page never calls role prompting unnecessary |
| Examples | "Include 3-5 examples for best results", relevant and diverse, in `<example>` or `<examples>` tags; `<thinking>` tags inside examples teach the reasoning pattern to thinking models | 3-5 examples remains the number. An example that shows reasoning is an instruction to reason that way |
| Long context | For "20k+ tokens": longform data at the top, above the query, instructions and examples; "Queries at the end can improve response quality by up to 30 percent in tests, especially with complex, multidocument inputs"; ask for quotes first | Unchanged |
| Emphasis | Opus 4.5 and 4.6 "are also more responsive to the system prompt than previous models. If your prompts were designed to reduce undertriggering on tools or skills, these models may now overtrigger. The fix is to dial back any aggressive language"; "Instructions like 'If in doubt, use [tool]' will cause overtriggering". The page's own sample prompts still write hard rules with "NEVER" and "MUST" | The target is triggering and anti-laziness language, not capitals as such. Dial back "CRITICAL: you MUST use this tool"; keep a plainly stated hard rule |
| Reasoning style | "Prefer general instructions over prescriptive steps. A prompt like 'think thoroughly' often produces better reasoning than a hand-written step-by-step plan"; manual CoT with thinking and answer tags only as a fallback when thinking is off; a self-check instruction helps, except on Opus 5 where it causes over-verification and should be removed; with thinking off, Opus 4.5 over-reacts to the word "think" | No step-by-step scaffold on a thinking model. Remove carried-over verification instructions when moving to Opus 5 |
| Thinking mode | Claude 4.6 and later use adaptive thinking (`thinking: {type: "adaptive"}`); on Fable 5.1, Mythos 5.1, Fable 5 and Mythos 5 thinking is always on and adaptive is the only mode; "In internal evaluations, adaptive thinking reliably drives better performance than extended thinking"; on Opus 4.6 through 4.8 and Sonnet 4.6 thinking is off when the parameter is omitted; on Opus 5 and Sonnet 5 it is on by default and Opus 5 can disable it only at effort `high` or lower | Do not write prompts that assume thinking is off on a 5-family model |
| Budget control | `budget_tokens` is deprecated on Opus 4.6 and Sonnet 4.6 and **returns a 400 error on Claude 4.7 and later**; control moved to `output_config: {"effort": ...}` with `max_tokens` as the hard limit; effort levels on Fable 5.1 are `low`, `medium`, `high` (default), `xhigh`, `max`, and "effort level names don't correspond to the same amount of thinking across models" | A token-budget instruction in the prompt is not the lever on Claude; effort is. Leave `max_tokens` room for thinking at `xhigh` and `max` |
| Overthinking | For Opus 4.6 at high effort: "choose an approach and commit to it, avoid revisiting decisions", or a lower effort; adaptive triggering is itself promptable ("Thinking adds latency... When in doubt, respond directly") | Prompt text and effort are the two anti-overthinking levers |
| Prefill | "Starting with Claude 4.6 models and Claude Mythos Preview, prefilled responses ... on the last assistant turn are no longer supported. Requests with prefilled assistant messages to these models return a 400 error ... Earlier models continue to support prefills, and adding assistant messages elsewhere in the conversation is not affected" | Prefill is dead on the last turn from 4.6 up. It is still a valid lever on earlier Claude models and on open-weight models served locally |
| Format migration | "Try asking the model to conform to your output structure first, as newer models can reliably match complex schemas when told to, especially if implemented with retries. For classification tasks, use either tools with an enum field containing your valid labels or structured outputs" | The vendor's own ladder: ask, then retries, then enum tool or structured outputs |
| Structured outputs | Generally available, no beta header; JSON mode is `output_config.format` with `type: "json_schema"` (legacy `output_format` deprecated; Python SDK v1.0+ requires `output_config`); strict tool use is `strict: true`; supported on every Claude 5 model plus Opus 4.5+, Sonnet 4.5+, Haiku 4.5; **unsupported schema features**: recursive schemas, `minimum` and `maximum`, `minLength` and `maxLength`, `additionalProperties` other than `false`; compiled grammars are cached 24 hours; the injected format prompt costs tokens; changing `output_config.format` invalidates the prompt cache | Numeric and length bounds must be enforced by your validator, not the schema. Batch schema changes like any cache-breaking edit |
| Prompt caching | Writes: 1.25x for the 5-minute TTL, **2x for the 1-hour TTL** (`cache_control: {"type": "ephemeral", "ttl": "1h"}`); reads 0.1x, and **0.025x on Fable 5.1 and Mythos 5.1**; minimum cacheable prompt 512 tokens on Fable 5.1, Mythos 5.1, Opus 5, Fable 5, Mythos 5; 1,024 on Opus 4.8, Sonnet 5, Sonnet 4.6, Sonnet 4.5, Opus 4.1, Opus 4; 2,048 on Opus 4.7; 4,096 on Opus 4.6, Opus 4.5, Haiku 4.5; shorter prompts silently report zero cache tokens | The "shortening a cached prefix saves ~10% of what it appears to" rule becomes ~2.5% on Fable 5.1. Below the minimum, nothing is cached and the economics revert to full price |
| Fable 5.1 | Writes fewer user-facing updates (ask for them; remove "keep it brief" lines); uses less bold and fewer headers, so remove anti-formatting rules; may issue one tool call per turn in coding loops, addressed by a turn-scoped system message (beta `mid-conversation-system-clear-at-2026-08-21`); for accounts created on or after 2026-08-31, a replayed thinking block whose prefix changed returns 400 (beta `thinking-binding-controls-2026-08-01`); at `low` effort it searches less; "Because cache reads are now cheaper ... experiment with later compaction points" | Prompts migrated from 4.x carry rules written against behaviors this model no longer has; delete them rather than keep them for safety |
| Tools | Current models "benefit from explicit direction to use specific tools"; parallel tool calling is the default and promptable to about 100%; the tool-definition page says "Provide extremely detailed descriptions, as this is by far the most important factor in tool performance" and adds an `input_examples` field *(verify)*; Skill authoring guidance: the SKILL.md description says what and when, keep the body under 500 lines *(verify)* | Tool descriptions are the highest-leverage prompt surface in an agent |

## OpenAI (checked 2026-09-05)

The Model guidance hub (developers.openai.com/api/docs/guides/prompt-guidance) now carries only
GPT-6 Astra, with GPT-5.6 Sol as the comparison model. The "Reasoning best practices" page is the
only current official statement on chain-of-thought and examples, and it still frames o3, o4-mini
and o1 against GPT-4.1: two model generations stale, confirmed as official, weakly current.

| Topic | Current statement | Consequence for a prompt |
|---|---|---|
| Chain-of-thought | "Avoid chain-of-thought prompts: Since these models perform reasoning internally, prompting them to 'think step by step' or 'explain your reasoning' is unnecessary" (the page says unnecessary, never harmful) | No scaffold by default |
| Effort floor | GPT-5 guide: `reasoning_effort` minimal, low, medium (default), high; at **minimal**, "prompting the model to give a brief explanation summarizing its thought process at the start of the final answer, for example via a bullet point list, improves performance", and "prompted planning is likewise more important, as the model has fewer reasoning tokens to do internal planning"; the `verbosity` parameter controls answer length, not thinking, and natural-language verbosity overrides are honoured | The exception to the no-scaffold rule: at the lowest effort a brief explicit plan helps. At medium and above, use the parameter, not prose |
| Examples | "Try zero shot first, then few shot if needed: Reasoning models often don't need few-shot examples to produce good results" | Zero-shot first. "Format or tone" as the reason to add examples is our inference, not the page's |
| Delimiters | "Use delimiters like markdown, XML tags, and section titles"; "Be very specific about your end goal" | Unchanged |
| Agentic dials | GPT-5 guide: lower eagerness with lower effort, explicit tool-call budgets ("absolute maximum of 2 tool calls"), early-stop criteria and escape hatches ("even if it might not be fully correct"); higher persistence with "keep going until the user's query is completely resolved"; tool preambles for plan and progress; reasoning reuse through `previous_response_id` lifted Tau-Bench Retail from 73.9% to 78.2%; contradictory instructions burn reasoning tokens, so resolve the hierarchy before deployment | Eagerness is a prompt-and-parameter setting, not a model constant. A contradiction in the prompt costs money on every call |
| GPT-6 Astra | Does not support the `none` reasoning effort; migrating from `none` or `minimal`, "start with `low` and compare results"; "more likely to ask the user a question when additional input could materially change the result"; "more sensitive to information in context", and "unclear or conflicting guidance in a skill file may cause the model to pause and block work early"; prompt it to "bias towards action and carry the user's intended task to completion" and to treat "can you..." as an instruction to do the work; "The user's instructions take precedence over guidelines provided in a skill"; tends toward detailed, formatted responses; migration: move tool calling to the Responses API, remove `temperature` and `top_p` | Clean the instruction hierarchy before migrating; the model stops on conflicts that older models talked past |
| Structured outputs | Definitions moved from `response_format` to `text.format` with `json_schema` and `strict: true` on the Responses API *(verify)*; the prompt-engineering guide says to "remove output schema definitions from the prompt where possible and use Structured Outputs instead" *(verify)* | Schema in the API, not in the prompt, when the API offers it |
| Evals and optimizer | The Evals platform becomes read-only for existing users on 2026-10-31 and is scheduled to shut down on 2026-11-30 (announced 2026-06-03); the dataset-backed prompt optimizer goes with it; the docs say to review any optimized prompt by hand before production; promptfoo was acquired by OpenAI on 2026-03-09 and "will remain open source under the current license" | Do not build a new eval pipeline on OpenAI Evals. promptfoo remains a valid CLI-first choice |

## Google Gemini (checked 2026-09-05)

Gemini 3 developer guide (ai.google.dev/gemini-api/docs/gemini-3, 2026-08-26) and the thinking
page (ai.google.dev/gemini-api/docs/thinking, 2026-09-04, now filed under the Interactions API
with generateContent labelled legacy).

| Topic | Current statement | Consequence for a prompt |
|---|---|---|
| Thinking control | `thinking_level` is `minimal`, `low`, `medium`, `high`; levels are "relative allowances for thinking rather than strict token guarantees"; `thinking_budget` "is still supported for backward compatibility, but we recommend migrating to `thinking_level`" and "You cannot use both"; the default is model-specific (`high` for 3.1 Pro and 3 Flash on one page, "On (medium)" for 3.6 through 3.8 Flash and "On (minimal)" for 3.5 Flash-Lite on the later page): do not state a single default | The lever is `thinking_level`, never a budget instruction in the prompt |
| Temperature | "we strongly recommend keeping the temperature parameter at its default value of 1.0", because lower values "may lead to unexpected behavior, such as looping or degraded performance" | Do not reach for temperature 0 on Gemini 3 to stabilize a format; use `responseSchema` |
| Style | "Be concise in your input prompts"; "Gemini 3 is less verbose and prefers providing direct, efficient answers"; "Place your specific instructions or questions at the end of the prompt, after the data context"; "If you were previously using complex prompt engineering (like chain of thought) to force Gemini 2.5 to reason, try Gemini 3 with `thinking_level: "high"` and simplified prompts" | Same placement rule as Anthropic's long-context guidance; the CoT scaffold migrates into the thinking level |
| Thought signatures | "Always present, even when the model performs minimal reasoning" and must be resent in stateless mode; `thinking_summaries: "none"` disables summaries; minimal or low thinking for fact retrieval, maximum for coding, math and multi-step planning | An agent loop on Gemini 3 must carry signatures between turns |
| Structured output | `responseSchema` on generateContent and an Interactions-API version exist *(verify: page located, not read)* | Prefer the API schema over prompt-only format instructions where it applies |

## Gemma (checked 2026-09-05)

| Version | Chat format | System role | Thinking and tools |
|---|---|---|---|
| Gemma 3 and lower (ai.google.dev/gemma/docs/core/prompt-structure, 2025-03-21) | `<start_of_turn>` and `<end_of_turn>`, roles `user` and `model` only | "the `system` role or a system turn is not supported"; "provide system-level instructions directly within the initial user prompt" | No JSON or function-calling guidance on the page |
| Gemma 4 (ai.google.dev/gemma/docs/core/prompt-formatting-gemma4, 2026-06-03) | `<\|turn>` and `<turn\|>`, roles `system`, `user`, `model` | A real system role exists | Thinking is enabled with `<\|think\|>` in the system instruction; an empty `<\|channel\|>thought<channel\|>` block suppresses ghost thinking on the 26B and 31B variants when fine-tuning without it; tools use `<\|tool>`, `<\|tool_call>`, `<\|tool_response>` with every string delimited by `<\|"\|>` |

A prompt written for Gemma 3 that puts the system instruction in the first user turn still works
on Gemma 4 but wastes the system role; a prompt written for Gemma 4 with a system turn is silently
mis-tokenized on Gemma 3. Always check which template the serving stack applies (Ollama and
llama.cpp apply the model's own template; a raw completions endpoint applies none). No official
Gemma JSON-output recommendation was read at this refresh; `structured-output.md` covers what is
measured on it.

## How to refresh this file

1. Fetch the four vendor pages named above; the Google pages carry a visible date, the Anthropic
   and OpenAI pages do not, so diff the quoted statements rather than trusting a date.
2. For each row: confirmed, changed (old to new), or removed. A row whose page has moved is
   unconfirmed, not confirmed absent; tag it *(verify)* rather than deleting it.
3. Update the "checked" date on the section, then update the model-fit rows in `SKILL.md`, the
   cache-economics line in `/prompt-optimize`, and the `<optimization_techniques>` section of the
   `prompt-engineer` role, which restate the load-bearing facts and must agree with this file.
