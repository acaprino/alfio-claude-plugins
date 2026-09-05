# ai-tooling Prompt Engineering Refresh (September 2026) - Design and record

Date: 2026-09-05
Status: executed in the same pass; this document is the record
Plugin: `ai-tooling` v5.1.0 -> v5.2.0, marketplace 27.0.1 -> 27.1.0

## Goal

Two things, asked for together: a checkup of `/ai-tooling:prompt-optimize` and the
`prompt-engineer` role behind it, and a research-grounded refresh of the prompt-engineering
knowledge they carry, with three declared priorities: forcing a specific output shape (JSON and
schemas) from a prompt, doing so on small and weak open-weight models such as Gemma, and the
task-specific literature on extraction (information extraction, NER, relation extraction,
parsing).

## Checkup findings

### 1. The reasoning-patterns reference was not shipped on any host (defect, fixed)

`plugins/ai-tooling/references/reasoning-patterns.md` sat at the kernel root. The compiler ships
`roles/`, `workflows/`, `contracts/`, `policies/` and `skills/<name>/**` and nothing else, so from
the kernel neutralization (2026-08-25, commit `3c52c3d3`, which deleted the old hand-mirrored copy
from the Claude package) until this pass, the file existed in the checkout and in no installed
package. The role reads it in two places and the command in two more, on every host. The read
fails silently: the agent falls back to its own recollection of the patterns, which is the
behaviour the reference exists to replace. Every existing gate passed: the bundled-path linter
checks the *form* of a path, the registration linter checks catalog entries, the drift gate
checks that packages reproduce from kernels, and a kernel that never ships a file reproduces
perfectly.

Fix: the knowledge base now lives in a new skill, `prompt-engineering`, whose `references/`
directory the compiler copies wholesale. The role and the command read
`${CLAUDE_PLUGIN_ROOT}/skills/prompt-engineering/references/<file>`.

Guard: `scripts/lint_bundled_paths.py` gained a third pass, `shipped refs`, which resolves every
`${CLAUDE_PLUGIN_ROOT}/...` reference in a kernel body against the generated Claude package and
fails the ones no package contains. Its first run found the same defect in two more plugins,
baselined in its `UNSHIPPED` map and not fixed here because they are outside this task:

- `research`: `scripts/websearch.py` and `scripts/webfetch.py` (the serper backend, the
  `--check-key` pre-flight and the bot-block fallback are dead for installed users).
- `peer-review`: the four `protocol/*.md` documents read by two roles, the workflow and the
  skill; `mcp/server.py` and `mcp/profiles.example.json`; and `.mcp.json` itself. The compiler
  has no MCP concept, so the server needs a design decision rather than a file move.

Both were fixed in the next release, marketplace 27.2.0: the files moved under their plugins'
skills, the compiler gained the `mcp.servers` capability, and the `UNSHIPPED` baseline is empty.

### 2. Host-vocabulary debt in the command (cleared)

The command's spawn block named `subagent_type`, one of the Claude primitives the
host-vocabulary linter forbids in neutral bodies, grandfathered at count 1. The dispatch is now
stated as an obligation ("spawn the `prompt-engineer` agent with this brief"), the way
`abstraction-architect`'s audit command already does, and the grandfathered entry is deleted.

### 3. Documentation drift (fixed)

`docs/plugins/ai-tooling.md` still described the pre-5.0.0 command (a six-dimension scorecard and
a before/after comparison) and listed "Constitutional AI" and "role-based prompting" as the
agent's patterns. Neither matched the shipped bodies.

### 4. Target-model handling was frontier-only (improved)

`--model claude|gpt|gemini` had no way to name an open-weight target, and the analysis had a
reasoning-model gate but no small-model gate. The three declared priorities all turn on that
gate: what enforces an output shape, and what a prompt may assume, differs by model class more
than by vendor.

## Research

Five `research:deep-researcher` runs in parallel, one per sub-question, per the
`custom-plugin-refresh` protocol: reasoning and token-efficiency patterns since June 2025;
official vendor prompting guidance as of September 2026; structured-output enforcement on small
open-weight models; task-specific extraction prompting; automatic prompt optimization, evals,
context engineering and injection defense.

Findings are classified per the protocol (clear win, subtle shift, no change, open question) in
the section below, which was written after the runs returned.

### Reasoning and token-efficiency patterns (2025-06 to 2026-09)

| Finding | Class | Where it landed |
|---|---|---|
| Few-shot CoT hurts RL-trained reasoners; more exemplars, even optimal R1 traces, degrade further; distilling demos into insights recovers +14.0% AIME'25 on GPT-4.1 (arXiv 2509.23196) | clear win | new reasoning-model bullet, new `Reasoning Traces as Exemplars` anti-pattern, new eval case |
| Overthinking replicated at scale: R1-32B on AIME peaks 55.8% at 12K thinking tokens, 54.9% at 16K; past ~7K negative flips outnumber positive 83 to 11; optimal budget 1.5K to 8K by difficulty; commitment boundary lets early exit cut chains up to 55% (arXiv 2604.10739, 2606.13603) | clear win | "Cap the thinking by difficulty" bullet, with numbers replacing the old "~20x on trivial questions" folklore |
| Hybrid open reasoners switch on mode tokens, not prose (Mid-Think 2601.07036); prompt-based depth self-selection Pareto-optimal at 9B and below, draft-agreement routing 32% to 73% fewer thinking tokens at parity from 8B to 32B (HRBench 2605.28398, DART 2606.23181) | clear win | new bullet, two cheat-sheet rows, decision-guide step 0 |
| Small open reasoners: prompting strategy changes model rankings; Gemma-4-E4B loses with CoT on GSM8K, Phi-4-reasoning collapses 0.67 to 0.11 under few-shot CoT (arXiv 2604.07035 v2) | clear win | new bullet, cheat-sheet row, model-class table in SKILL.md |
| At the lowest effort setting a brief explicit plan helps (OpenAI GPT-5 guide) | subtle shift | the flat "no scaffold" rule gained its one exception, in the reference, the role and the command |
| Short-m@k: vote among the first chains to finish, up to 40% fewer thinking tokens than majority vote (arXiv 2505.17813) | clear win | Self-Consistency cost note |
| PREMISE: prompt-only brevity holds accuracy on Claude 3.7 Sonnet and Gemini at up to 87.5% fewer reasoning tokens (arXiv 2506.10716); DART's benchmarking caveat (cap thinking and answer separately) | clear win | cost-aware selection, parity claims |
| A token budget in the prompt is a soft hint; precise control needed decoding-time tokens (BudgetThinker 2508.17196); `budget_tokens` returns 400 on Claude 4.7+ | clear win | TALE failure modes, role token-reduction bullet |
| Status of the eight cited papers: Sketch-of-Thought EMNLP 2025, "To CoT or not" ICLR 2025, Wharton v1 only, Chain of Draft unreplicated | no change, dated | inline status notes |
| Gemini thinking controls, "Reasoning Models Struggle to Control their Chains of Thought" (2603.05706), Wharton reports 3 to 5 | open question | not read; next refresh |

### Vendor guidance (as of 2026-09-05)

| Knowledge-base claim | Verdict | Where it landed |
|---|---|---|
| Cache reads 0.1x, writes 1.25x | changed: 1-hour writes 2x; reads 0.025x on Fable 5.1 and Mythos 5.1; per-model minimum cacheable length | `model-guidance.md`, role, command, reasoning-patterns cost section |
| Heavy role prompting is unnecessary | changed: "Even a single sentence makes a difference"; the docs never call it unnecessary | role design framework |
| Emphasis escalation causes overtriggering | confirmed, scoped to trigger and anti-laziness language on Claude 4.5+; the docs' own examples keep MUST and NEVER for hard rules | role positioning and anti-pattern |
| Prefill 400 since Claude 4.6 | confirmed, with nuance: last turn only; earlier models and non-final turns unaffected; open-weight prefill still valid | `model-guidance.md`, command output-shape check |
| XML when mixing content; headings for simple prompts | half confirmed: the headings half is the plugin's own judgment and is now labelled as such | role XML section |
| Long context on top, query at the end, up to 30% | confirmed; Gemini 3 states the same placement rule | no change |
| Reasoning models want general instructions | confirmed on all three vendors | no change |
| OpenAI: CoT prompts harmful | changed to "unnecessary" (the page's word); the page is two generations stale | reference, `model-guidance.md` |
| 3-5 examples on Claude | confirmed, in `<example>` tags | role |
| Prefer API structured outputs | mixed: Anthropic's own order is ask, retries, then enum tool or structured outputs; unsupported schema features listed | `model-guidance.md`, SKILL.md model-class table |
| New: adaptive thinking on 4.6+, always on for Fable and Mythos 5.x; effort levels; GPT-6 Astra drops `none`, pauses on conflicting guidance; Gemini `thinking_level`, temperature 1.0; Gemma 4 has a system role where Gemma 3 has none | clear win | `model-guidance.md` |
| OpenAI Evals sunset 2026-11-30, promptfoo acquired 2026-03-09 | clear win | role prompt-evals tooling line |

### Extraction prompting

| Finding | Class | Where it landed |
|---|---|---|
| Prompting lags fine-tuning at every size: ICL vs SFT gaps of 6 to 60 F1 in the survey; fine-tuned 0.5B to 3B beats frontier zero-shot RE (arXiv 2606.22606) | clear win | the framing section of `extraction-prompting.md`; the command's task-family check says so plainly |
| Output validity is the first failure on small models (Phi-3-mini 2.72 F1 on a text prompt; Gemini 2.5 Pro excluded for validity; 40%+ format swings under fine-tuning) | clear win | framing section, small-model order of operations |
| Two-stage prompting +16.82 on joint EE, -5.05 on flat NER; "extract all" reminder +15.18 on joint EE; verbose definitions hurt in half the cases; few-shot CoT often worse (arXiv 2409.00369) | clear win | shapes that work, what fails |
| Code-shaped prompts: +19.5 F1 on Phi-3-mini, +5.8 on Llama-3-8B, loses on CoNLL03-style text (CodeNER) | clear win | shapes that work, per-task table |
| Guidelines as docstrings with positive and negative examples: up to +30 TC in low data; contrast is the active ingredient (arXiv 2502.16377) | clear win | shapes that work |
| Disagreement-refined instructions +14.9 F1 at 8B to 24B; content is boundary, entityhood and disambiguation rules (DiZiNER) | clear win | small-model order of operations |
| Source grounding catches demonstration leakage; chunk at 1,000 chars, three passes (LangExtract); omitted key scores as null, long documents drop records, tables over 1,000 rows defeat every VLM (ExtractBench) | clear win | long-document row, eval section |
| Error taxonomy: missing plus unannotated spans over 60% of errors; soft matching +6.3 to +16.5 | clear win | error-taxonomy section |
| GoLLIE, KnowCoder, UniversalNER, GPT-NER, the 2025 EE survey, LMDX | open question | listed in the reference's sources as next-refresh reads |

### Automatic optimization, evals, context engineering, injection

| Finding | Class | Where it landed |
|---|---|---|
| GEPA is the reference optimizer (over 10% above MIPROv2, up to 35x fewer rollouts than RL, ICLR 2026); no neutral head-to-head across the others; hand-review optimized prompts | clear win | role prompt-evals |
| Delimiters between examples swing MMLU by up to 23 points and reorder rankings (arXiv 2510.05152); format sensitivity is mostly parse failure (2607.09665) | clear win | role examples section and prompt-evals |
| Judge validation: kappa not exact match (33 to 41 points overstated), rankings shift up to 14 positions across benchmarks, position bias above 0.10 in production judges, verbosity bias below 0.011 under a pairwise rubric (2606.19544); bias correction can flip sign (2605.06939) | clear win, with one demotion: verbosity control kept as secondary | role prompt-evals |
| "Demystifying evals": 20-50 tasks confirmed, pass@k vs pass^k, Unknown clause, grade state not path, harder variants at saturation | clear win | role prompt-evals |
| Context primitives are API-level on Claude (clearing 100K default, compaction 150K default and 50K minimum, memory tool), layering order, cookbook numbers; Chroma context rot on 18 models; classifiers rot too | clear win | role context-engineering |
| Tool design specifics (response_format, 25,000-token cap, namespacing, consolidation, instrumentation); OpenAI eagerness dials; reasoning reuse +4.3 on Tau-Bench Retail | clear win | role agentic prompting |
| Prompt-only injection defenses are partial and model-dependent (paraphrasing 55% to 84%, spotlighting halves on Haiku and does nothing on Llama 3.1 8B); adaptive attacks defeat static winners; instruction hierarchy breaks in long contexts; both vendors say not fully solvable | clear win | the injection anti-pattern rewritten as three layers |
| Anthropic model-level injection numbers from VentureBeat; Memory for Managed Agents; Agent Skills post | open question | not cited; secondary sources only |

### Structured output on small open-weight models

| Finding | Class | Where it landed |
|---|---|---|
| Validity is not correctness: strict schemas take validity to 100% while semantic success barely moves (Llama-3.1-8B 31.7% to 36.0%, Gemma-2-2B 0.0% to 2.0% with 41.7% unsafe acceptance, arXiv 2607.18261); on Qwen2.5-0.5B a hard schema cut accuracy 19.7% to 11.0% and pushed wrong-but-valid to 88.9% (arXiv 2605.26128); best leaf-value accuracy 83% across 21 models (arXiv 2604.25359) | clear win | framing section of `structured-output.md`; the eval section's four numbers; the command's honesty note |
| The format tax is in the prompt, not the sampler: format instructions alone cost open models 0.9 to 6.6 points on reasoning tasks and frontier models nothing; decoder constraints add almost no further loss (arXiv 2604.03616), which resolves "Let Me Speak Freely" (2408.02442) against dottxt's rebuttal and the 2024 replication | clear win | framing section; rung 1 and rung 4 |
| Prompt-only JSON validity below 8B measured 61% to 92% (Llama-3.1-8B 68.7%, Gemma-2-2B 91.7%, Qwen3-8B at most 72%, Qwen2.5-0.5B 61.5%); about 100% at 30B | clear win | framing section, rung 1, role anti-pattern, SKILL.md model-class table, new eval case |
| Reason first, then constrain: freeform-then-reformat +6.8 points (42 of 72 better, 2 worse); thinking mode +9.2 but 11 of 72 worse; CRANE up to +10, In-Writing up to +27% (ICML 2025, arXiv 2601.07525); key order turned CoT into direct answering in the 2024 collapse | clear win | rung 4, prompt-side levers, role structured-output section, command output-shape check |
| Engines: JSONSchemaBench coverage and speed (Guidance 0.41, llama.cpp 0.39, XGrammar 0.28, Outlines 0.03 on GitHub-Hard; Outlines 3.5 to 8 s compile); SqueezeBits 100% guided vs at most 72% unconstrained on Qwen3-8B/32B; llguidance 50 µs per token; vLLM removed `guided_*` in v0.12.0 and constrains after thinking by default; llama.cpp does not inject the schema and rejects several keywords | clear win | serving-stack table |
| Gemma: no system role through Gemma 3, a system role and tag-formatted tools with `<\|"\|>` delimiters on Gemma 4; Ollama 0.20.x fences JSON under `format` on gemma4 e4b and 31b and ignores `format` with `think=false` | clear win | Gemma section; SKILL.md conservative-row rule |
| Key names are an instruction channel under constrained decoding (arXiv 2604.14862); XML return formats lose at 8B and below (BFCL V4) | clear win | prompt-side levers |
| Stop sequences, negative examples, IFEval by size, Gemma 3 versus peers JSON reliability, BFCL per-model scores, LM Studio, LMQL, TGI, jsonrepair | open question | listed as unmeasured or unread in the reference |

## Versioning

- `plugins/ai-tooling/plugin.toml`: 5.1.0 -> 5.2.0 (minor: a new skill with three references)
- `.claude-plugin/marketplace.json` `metadata.version`: 27.0.1 -> 27.1.0
- Commit: `Refresh ai-tooling for 2026-09 prompt engineering practices and ship its references (v5.2.0)`, one commit carrying the kernel, the generated packages and catalogs, the linter pass, the eval cases, the docs and this record
