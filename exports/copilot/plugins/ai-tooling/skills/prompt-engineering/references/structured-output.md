# Forcing an output shape: JSON, schemas, enums, templates

On-demand reference for the `prompt-engineer` agent and the `/prompt-optimize` command. Read it
whenever something parses the model's output, and always when the target is an open-weight
model. It answers one question: given this model class and this schema, which rung of the
enforcement ladder does the prompt assume, and what does that rung cost in validity, accuracy,
latency and setup. The extraction shapes that decide *what* goes in the schema live in
`extraction-prompting.md`; the vendor quotes behind the API rows live in `model-guidance.md`.

Every number below is **measured** on the named model, engine and benchmark at the cited date,
and **predicted** on yours until you run the eval at the end. Numbers checked 2026-09-05.

## Three facts that frame every decision

**Validity is not correctness.** Constrained decoding takes schema validity to 100% on every
model measured; it does not take the answer to correct. On an ordering-agent task (arXiv
2607.18261, 2026-05) strict schema mode lifted Llama-3.1-8B from 68.7% to 100% valid while
semantic success moved from 31.7% to 36.0%, and lifted Gemma-2-2B from 91.7% to 100% valid while
semantic success went from 0.0% to 2.0%, with 41.7% of orders accepted unsafely inside perfectly
valid JSON. On Qwen2.5-0.5B ("The Constraint Tax", arXiv 2605.26128, 2026-05) a hard schema
raised validity from 61.5% to 100% and cut answer accuracy from 19.7% to 11.0%, pushing
wrong-but-valid outputs from 49.5% to 88.9%; on Qwen2.5-1.5B tool calls, prompt-only JSON
reached 91.5% executable accuracy against 48.0% under a hard tool-call schema, both 100% valid.
Across 21 models the Structured Output Benchmark (arXiv 2604.25359, 2026-04) found near-perfect
schema compliance and a best exact leaf-value accuracy of 83.0% on text. A parser that never
fails is not a system that is right; report validity and correctness as two numbers.

**The format tax is in the prompt, not the sampler.** "Let Me Speak Freely?" (arXiv 2408.02442,
2024) reported GSM8K collapsing from 75.99 to 49.25 on GPT-3.5-turbo and from 86.51 to 23.44 on
Claude 3 Haiku under JSON mode. The collapse traced to key ordering: every JSON-mode response put
the `answer` key before the `reason` key, which turned chain-of-thought into direct answering.
dottxt's rebuttal re-ran Llama-3-8B with identical prompts under grammar enforcement and got
structured at or above unstructured on every task; an independent replication found the gap
task-dependent. "The Format Tax" (arXiv 2604.03616, 2026-04) settles it on six open models over
MATH-500, GPQA, ZebraLogic and WritingBench: format instructions alone cost Qwen3-8B 6.6 points,
Qwen3-32B 5.8, Nemotron 3 Nano 4.9, OLMo 3-7B 3.5, SmolLM3-3B 3.4 and OLMo 3.1-32B 0.9, "before
any decoder constraint is applied", and "degradation is similar whether or not the constraint
is applied"; Claude Haiku 4.5, Grok 4.1 Fast and GPT-5.4-nano showed near-zero or positive
deltas. The loss is real, it is one to seven points rather than sixty, it lands on reasoning
tasks, and the remedy is ordering or a two-stage pass, never dropping the format instruction.

**Prompt-only compliance on small models is a coin you cannot afford to flip.** Measured
prompt-only JSON validity: 68.7% for Llama-3.1-8B and 91.7% for Gemma-2-2B against 100% for
Qwen3-30B-A3B and gpt-oss-120B (arXiv 2607.18261); at most 72% for Qwen3-8B and Qwen3-32B on a
simple repeated schema (SqueezeBits, 2025-09); 61.5% for Qwen2.5-0.5B (arXiv 2605.26128);
82.55% average with a 0% to 100% range across 24 StructuredRAG experiments on Gemini 1.5 Pro and
4-bit Llama 3 8B, lists and composite objects hardest (arXiv 2408.11061). Under about 30B the
instruction is a courtesy to the model, not a guarantee to the parser.

## The enforcement ladder

Pick the rung by model class and by what a parse failure costs. State the rung in the variant.

**Rung 0, at every rung.** Describe the schema in the prompt even when the engine constrains:
llama.cpp's README states the JSON schema "is only used to constrain the model output and is not
injected into the prompt", SGLang's docs call it "advisable to explicitly include instructions
in the prompt", and Ollama's guidance still says to add "return as JSON". Put a reasoning key
before the answer key, or move reasoning to its own phase (rung 4). Ask for JSON or Python,
never XML, at 8B and below: BFCL V4's format-sensitivity study found Llama-3.1-8B-Instruct
dropping significantly on XML return formats and even claude-3.7-sonnet losing on them.
Temperature 0 on local stacks (Ollama's own advice; Gemini 3 is the exception, whose vendor says
to keep 1.0 and use `responseSchema`). Measure validity, answer accuracy and the wrong-but-valid
rate as three numbers.

**Rung 1, format instruction only.** Enums, classification, flat schemas of a dozen keys or
fewer, where a parse failure is cheap and retried by a human. Expect roughly 60% to 92%
syntactic validity from 0.5B to 8B and about 100% at the 30B class and on frontier APIs. Prefill
the opening brace where the stack allows it (Transformers `continue_final_message=True`,
documented with the example `{"name": "`; any raw completions endpoint; Claude 4.5 and earlier),
only when thinking is off, because a prefilled `content` closes the thinking block. On a
reasoning task keep the reasoning out of the JSON turn: the one-to-seven-point tax above.

**Rung 2, instruction plus validate-and-repair.** Schema validation in the caller (Pydantic,
Zod) with two or three retries that feed the validator's error back as a new message; Instructor
documents this loop and recommends two to three attempts for validation errors, five for rate
limits, with a token budget and a stop condition always set. It clears the 8% to 40% syntactic
failures of rung 1 at the price of extra calls only on failures, needs no engine support, and
is the floor for any small open-weight model in production. Move here when measured validity is
under about 95% and latency tolerates a retry.

**Rung 3, API structured outputs or constrained decoding.** On frontier APIs: Anthropic's own
order is ask first, retries second, then an enum tool or structured outputs (see
`model-guidance.md` for what their schema support rejects and what it costs in tokens and cache
invalidation); OpenAI's Responses API `text.format` with `strict: true` *(verify)*; Gemini
`responseSchema` *(verify)*. On open-weight models: Ollama `format` with a JSON Schema,
llama.cpp `json_schema` or a GBNF grammar, vLLM or SGLang with XGrammar or llguidance. Validity
goes to 100% (arXiv 2607.18261; SqueezeBits; arXiv 2605.26128). At 8B semantic accuracy also
improves modestly: Llama-3.1-8B +4.3 points semantic success and 5 points less unsafe
acceptance; Qwen3-8B +20 to +25 points on GitHub-medium schemas where unconstrained fell to
61.1%; Guidance raised Llama-3.1-8B on GSM8K from 80.1 to 83.8, Last Letter 50.7 to 54.0 and
Shuffled Objects 52.6 to 55.9 (JSONSchemaBench, arXiv 2501.10868). Per-token cost is near zero
with XGrammar or llguidance; Outlines added 3.5 to 8 seconds of grammar compilation per schema
and roughly doubled time per token at 8B in the same benchmark. Keep schemas flat: on
GitHub-Hard schemas empirical coverage was Guidance 0.41, llama.cpp 0.39, XGrammar 0.28,
Outlines 0.03, and llama.cpp's converter rejects float bounds, nested `$ref`,
`patternProperties`, `uniqueItems`, `not` and if/then/else while defaulting
`additionalProperties` to false. Move here when retries exceed budget, the schema is nested, or
an exact-parse guarantee is required. At 1.5B and below the constraint tax above can halve
answer accuracy: keep rung 2, or add a domain validator and fail closed.

**Rung 4, reason first, then constrain.** For math, logic, multi-step extraction, or whenever
constrained accuracy on the same prompt is below free text. Three shapes: two calls, freeform
answer then a reformat call (The Format Tax: significantly better in 42 of 72 model-task-format
comparisons, +6.8 points on average, worse in 2); the model's thinking mode with the constraint
applied after it (+9.2 points on average, but significantly worse in 11 of 72, so measure);
or one grammar with a free-text reasoning region before the constrained answer (CRANE, ICML
2025, up to +10 points over both constrained and unconstrained baselines on GSM-Symbolic and
FOLIO; "Thinking Before Constraining", arXiv 2601.07525, up to 27% over natural generation).
Engine notes: vLLM applies the constraint after the thinking block is parsed out unless
`--structured-outputs-config.enable_in_reasoning=True`; Ollama masks after the end-of-thinking
token, which is why `think=false` silently disables `format` on gemma4 under Ollama 0.20.x
(issue #15260); do not prefill the brace here, because it closes the thinking block.

## Prompt-side levers, and what each is worth

| Lever | Worth | Evidence |
|---|---|---|
| The schema in the prompt, keys named and typed | Required at every rung; the engines do not inject it | llama.cpp README, SGLang docs, Ollama blog |
| Key names | An instruction channel under constrained decoding: changing only the key wording "can substantially affect accuracy" with prompt, model and structure fixed; Qwen responds more to schema wording, Llama more to prompt wording, non-additively | arXiv 2604.14862, 2026-04 |
| Key order | Reason key before answer key, or the chain-of-thought becomes a direct answer | arXiv 2408.02442 |
| One example of the output | Raises compliance on small models; "Follow the Format" prompting beat an f-string template 76.5% to 67.0% on 4-bit Llama 3 8B *(verify: snippet, not the read abstract)* | arXiv 2408.11061 |
| "Respond only with JSON" | Prevents preamble; costs one to seven points on reasoning tasks for open models and nothing on frontier models; keep it and move the reasoning | arXiv 2604.03616 |
| Prefilling the opening brace | Strong where the stack allows it and thinking is off; unavailable on the last turn of Claude 4.6 and later | Transformers docs; Anthropic docs |
| Temperature 0 | Recommended by Ollama for schema output; keep 1.0 on Gemini 3 | Ollama blog; Gemini 3 guide |
| JSON or Python over XML | At 8B and below XML return formats lose significantly | BFCL V4 format sensitivity, 2025-07 |
| Stop sequences, negative examples | No measured source found at this refresh; treat as unmeasured | searched, not found |
| Stripping code fences in the parser | Required for Gemma 4 on Ollama, which fences JSON even under `format` | Ollama issue #15595 |

## Serving stacks for open-weight models

| Stack | Constraint mechanism | What to know |
|---|---|---|
| Ollama | `format` takes a full JSON Schema (since 2024-12); build the schema with Pydantic or Zod | Set temperature 0 and still say "return as JSON"; `think=false` disables `format` on gemma4 in 0.20.x; gemma4:e4b and gemma4:31b fence the JSON and 31b may ignore the schema (issues #15260, #15595); the MLX runner reportedly ignores `format` *(verify: issue #16776, unread)* |
| llama.cpp | GBNF grammars; `json_schema` and `response_format` on llama-server, `--json` on the CLI, converted to GBNF | Schema not injected into the prompt; `additionalProperties` defaults to false; supports `minLength`/`maxLength`, integer-only bounds, anchored `pattern`, limited `$ref` and anyOf/oneOf; rejects float bounds, nested `$ref`, `patternProperties`, `uniqueItems`, `not`, if/then/else |
| vLLM | Four backends (xgrammar, guidance, outlines, lm-format-enforcer), `auto` picks per request; `choice`, `regex`, `json`, `grammar`, `structural_tag` | The old `guided_*` request fields were removed in v0.12.0; constraints apply after thinking unless `enable_in_reasoning` is set; some Qwen3 Coder setups lose structured outputs when reasoning is enabled |
| SGLang | XGrammar default, Outlines, llguidance; JSON schema, regex, EBNF; one constraint per request | Its docs ask for the format instruction in the prompt as well; overlaps grammar work with decoding better than vLLM in the SqueezeBits benchmark |
| Transformers | No decoding constraint; `continue_final_message=True` prefills the assistant turn | The prefill closes a thinking block on reasoning models; prefill the reasoning field instead when thinking is wanted |
| Instructor (client side) | Pydantic validation with retries that carry the error back | Two to three attempts for validation errors, five for rate limits, `token_budget` and stop conditions always set |
| llguidance / Guidance | The engine under Guidance, MIT, 1.0.0 since 2025-06; about 50 µs of CPU per token on a 128k tokenizer | Integrated in OpenAI Structured Output, llama.cpp, SGLang, vLLM, TensorRT-LLM, mistral.rs, onnxruntime-genai; widest coverage on hard schemas and faster than unconstrained decoding by fast-forwarding forced tokens |
| XGrammar-2 | Tag-triggered structure switching for tool calls, cross-grammar cache | Claims over 6x faster compilation and near-zero overhead (arXiv 2601.04426, self-reported); recommended for simple repetitive schemas, llguidance for dynamic complex ones |

## Gemma

- **Gemma 2 and 3**: no system role; `<start_of_turn>user` ... `<end_of_turn>` then
  `<start_of_turn>model`; system-level instructions go in the first user turn. No official JSON
  guidance on the page. No authoritative Gemma 3 versus peers JSON-reliability measurement was
  found at this refresh; the rung-1 numbers above for Gemma-2-2B (91.7% valid, 0.0% semantic
  success on an agent task) are the closest evidence, and they say to enforce and to validate.
- **Gemma 4** (E2B, E4B, 12B, 26B-A4B, 31B): a native `system` role; thinking enabled with
  `<|think|>` in the system instruction; tool declarations and calls are tag-formatted
  (`<|tool_call>call:name{param:<|"|>value<|"|>}<tool_call|>`) with every string literal wrapped
  in `<|"|>`, so use the engine's tool parser rather than asking for raw JSON tool calls. Under
  Ollama 0.20.x expect fenced JSON even with `format` on e4b and 31b, and never combine
  `think=false` with `format`; when either bites, run the grammar in llama.cpp or vLLM instead.

## Benchmarks worth knowing by name

- **JSONSchemaBench** (arXiv 2501.10868): 10K real schemas, six frameworks; coverage, compile
  time, per-token time, and the over-constrained versus under-constrained error classes.
- **SchemaBench** (arXiv 2502.18878): about 40K schemas; "the latest LLMs are still struggling
  to generate a valid JSON string" without constraints.
- **StructEval** (arXiv 2505.20139, v3 2026-04): 18 formats, 44 task types; GPT-4o 76.02,
  o1-mini 75.58, best open model Qwen3-4B 67.04; JSON, CSV, HTML and YAML-to-JSON near solved;
  text-to-TOML 35.8%, text-to-Mermaid 18.9%, Matplotlib-to-TikZ 28.4% still hard.
- **The Structured Output Benchmark** (arXiv 2604.25359): compliance near perfect, leaf-value
  accuracy 83.0% text, 67.2% images, 23.7% audio.
- **BFCL V4** format sensitivity (2025-07): 26 prompt variations over five dimensions; format
  cases run only for prompt-mode, non-function-calling models.

## The eval an output-shape decision needs

Report four numbers separately, on at least a hundred real inputs: schema validity, answer
accuracy, executable accuracy where the output is acted on, and the wrong-but-valid rate. A
parse failure is scored apart from a wrong answer. Domain validation runs after schema
validation and the system fails closed on either. The decision between rungs is made on these
numbers, never on the prompt looking right.

## Sources

- "Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of LLMs", arXiv 2408.02442, v3 2024-10-14; dottxt, "Say What You Mean: A Response to 'Let Me Speak Freely'"; D. Castillo, "Structured outputs can hurt the performance of LLMs", 2024-12-08
- "The Format Tax", arXiv 2604.03616, 2026-04-04
- "The Constraint Tax: Measuring Validity-Correctness Tradeoffs in Structured Outputs for Small Language Models", arXiv 2605.26128, 2026-05-20
- "When JSON Is Not Enough: Semantic Reliability of Schema-Constrained LLM Ordering Agents", arXiv 2607.18261, 2026-05
- "The Structured Output Benchmark", arXiv 2604.25359, 2026-04-28
- JSONSchemaBench, arXiv 2501.10868, v3 2025-02-27; SchemaBench, arXiv 2502.18878; StructEval, arXiv 2505.20139; StructuredRAG, arXiv 2408.11061
- CRANE, arXiv 2502.09061, ICML 2025; "Thinking Before Constraining", arXiv 2601.07525, rev 2026-05; "Schema Key Wording as an Instruction Channel", arXiv 2604.14862, 2026-04
- XGrammar-2, arXiv 2601.04426, rev 2026-08-05; llguidance README (github.com/guidance-ai/llguidance); SqueezeBits, "Guided Decoding Performance on vLLM and SGLang", 2025-09-16
- vLLM structured outputs docs; SGLang structured outputs docs; llama.cpp grammars/README.md; Ollama, "Structured outputs", 2024-12-06; Ollama issues #15260 and #15595 (2026-04); Transformers chat-templating docs; Instructor retrying docs
- Gemma prompt structure (Gemma 1 to 3) and Gemma 4 prompt formatting and function calling, ai.google.dev; BFCL V4 leaderboard and format-sensitivity study, gorilla.cs.berkeley.edu
- Not read, worth the next refresh: LM Studio, LMQL, TGI grammar support, jsonrepair; BFCL per-model scores for Gemma 3 and 4, Llama 3.x, Qwen3, Phi-4; "Attributing Structured-Output Gains in Function Calling" (arXiv 2607.02595); "Brief Is Better" (arXiv 2604.02155)
