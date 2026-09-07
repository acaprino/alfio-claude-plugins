# ai-tooling September 2026 refresh: the research prompt

Committed as evidence of the 2026-09-07 refresh, per the retention rule in the
`custom-plugin-refresh` skill. This is the exact text given to `/research:team-research
--depth deep --no-clarify --domain "LLM prompt engineering"`, reproduced verbatim below.
Its `<already_covered>` block is what kept the run off the ground the 2026-09-05 refresh had
already covered, and it is the reason the report's negative findings mean anything: a source
listed there was excluded by instruction, not missed.

sha256 of the body below, as run: `571b670e2485e77d6ba2e46980c0d8386bb1b30198745ae8e3f033bd39c076de`

---

Which prompting techniques are measured to work, per task family and per model class, in results published from June 2025 to September 2026, for the task families and questions that a prompt-optimization knowledge base does not yet cover?

<purpose>
The findings update the knowledge base of a prompt optimizer. The optimizer classifies every prompt by archetype (extraction/classification, structured generation, creative/generative, reasoning, agentic/tool-use, judge/evaluator, system policy, meta-prompt) and by target model class, then applies the technique measured for that cell. The four model classes: frontier reasoning model (Claude 4.6 and later, GPT-5.x and GPT-6, Gemini 3, o-series); hybrid open reasoner (Qwen3, Gemma 4, DeepSeek V3.x, gpt-oss); small open-weight instruct model under roughly 30B (Gemma 3, Llama 3.x 8B, Phi-4-mini, Mistral Small, served through Ollama, llama.cpp or vLLM); older non-reasoning model (GPT-4 class, Claude 3.x, Gemini 2.x). A finding is useful only if it names the task family, the model class it was measured on, the metric, the effect size against a baseline, and the source with its revision and venue status.
</purpose>

<already_covered>
Do not re-research these areas. Cite their sources only when a new result confirms, extends or contradicts them.
- Reasoning scaffolds and token-efficient reasoning: CoT, Step-Back, Self-Consistency, Tree-of-Thought, ReAct, Reflexion, Plan-and-Solve, Least-to-Most, Self-Ask, Skeleton-of-Thought, Chain of Draft, Concise CoT, token-budget prompting, Sketch-of-Thought; reasoning-model defaults; overthinking (arXiv 2604.10739, 2606.13603); hybrid reasoner control (2601.07036, 2605.28398, 2606.23181); small reasoners (2604.07035); few-shot CoT on reasoners (2509.23196); PREMISE (2506.10716); short-m@k (2505.17813); the token-cost benchmark (2505.14880).
- Structured-output enforcement: the format tax (2604.03616, 2408.02442), the constraint tax (2605.26128), validity versus correctness (2607.18261, 2604.25359), JSONSchemaBench, SchemaBench, StructEval, CRANE, schema key wording (2604.14862), serving stacks (Ollama, llama.cpp, vLLM, SGLang, llguidance, XGrammar).
- Extraction: NER, relation and event extraction, document and table extraction (2312.17617, 2409.00369, CodeNER 2507.20423, DiZiNER 2604.15866, 2502.16377, 2606.22606, ExtractBench 2607.29677, LangExtract).
- Vendor prompting pages as of 2026-09-05 (Anthropic, OpenAI, Gemini 3, Gemma 4): thinking and effort settings, prefill, prompt-caching economics, emphasis and overtriggering, structured-output API support.
- Evals and judge safeguards (2606.19544, 2605.06939, 2607.09665), delimiter sensitivity between examples (2510.05152), GEPA (2507.19457), prompt-injection defenses (2606.18530, 2505.18333, 2606.07808), Claude context-management primitives, the Chroma context-rot report.
</already_covered>

<sub_questions>
1. Technique-to-task map. Surveys and meta-analyses of prompting techniques published 2025-06 to 2026-09 (successors to "The Prompt Report", Schulhoff et al.), and any benchmark that measures several techniques across several task families on named models. Deliver a matrix: task family by technique by model class, with effect size and source. Boundary: no depth on reasoning scaffolds, structured output or extraction; those cells may cite the covered sources only.
2. Judge and evaluator prompts. How to write the prompt of an LLM-as-judge: pointwise versus pairwise, scale choice, rubric and checklist designs, reference-guided versus reference-free, decomposition into one criterion per judge, calibration and confidence elicitation, the templates that measured the highest agreement with humans, and results with small open models as judges. Boundary: judge bias measurements and eval tooling are covered; the deliverable is the prompt shape and its measured agreement.
3. Agent instructions and tool descriptions. What is measured about system prompts for agents, tool and function descriptions (ablations on description length, examples in descriptions, parameter naming), instruction files and skills (Anthropic's Agent Skills and "writing tools for agents", OpenAI's agent design guidance, the instruction-file guidance of Claude Code, Codex and Copilot), trigger-phrase calibration, progressive disclosure, the brief an orchestrator gives a subagent and the summary it gets back, and instruction persistence and drift across many turns. Boundary: prompt-injection defense is covered.
4. Instruction-following capacity by model size. How many simultaneous constraints a model follows, by class and size (IFEval, IFBench, ComplexBench, FollowBench, InFoBench and their 2026 successors), the measured effect of rule count, rule ordering, explicit priority statements, negative ("never") versus positive phrasing, and conflicting rules. Deliver the numbers that would replace a rule of thumb such as "8 to 12 rules". Boundary: emphasis and overtriggering language is covered.
5. Prompt format and role by model family. Measured effects of markdown, XML, JSON and plain prose as the prompt's own format, of section order and whitespace, on Claude, GPT, Gemini, Llama, Qwen and Gemma; and the evidence on persona and role prompting: whether a one-sentence role changes accuracy, on which tasks, on which model class. Boundary: delimiters between few-shot examples and long-context placement are covered.
6. Long-context and retrieval-grounded prompting. Many-shot in-context learning (how many shots, their ordering, when it beats fine-tuning, on which classes), prompting over retrieved documents (quote-first, citation instructions, abstention when the context lacks the answer, the status of lost-in-the-middle in 2026), and summarization prompting (chain of density and its successors, faithfulness instructions). Boundary: context-management primitives and the Chroma report are covered.
7. Generation task families. Code-generation prompting (specification-first, test-first, repository context, measured on SWE-bench-class tasks), creative and open-ended generation (constraint versus latitude, output diversity, mode-collapse mitigation), and conversational system policies for product surfaces (persona stability, refusal phrasing, escalation rules). Deliver, per family, the two or three techniques with the strongest measured evidence and the ones that measured as harmful.
8. Multimodal and multilingual prompting. Prompting vision and document models (image placement, resolution, describe-then-answer, PDF and scanned-document prompting, audio), and prompting in a language other than English, Italian first: system-prompt language choice, translate-then-prompt, and format compliance of small open models on non-English input.
</sub_questions>

<answer_requirements>
- Prefer results from 2025-06 to 2026-09; admit earlier work only as the canonical citation a newer result builds on.
- Source order: peer-reviewed or arXiv papers with venue status stated (the venue, or "v1 only, unpublished as of 2026-09"); vendor documentation and engineering blogs quoted with their date; benchmark leaderboards; practitioner posts only when they report a measurement.
- Every claim carries: model and size, task and dataset, metric, effect size with its baseline, source with arXiv ID and version, date checked. Mark single-source and unreplicated results as such. A claim measured only on GPT-4-class models is a claim about older non-reasoning models, not about current ones.
- For every technique, state whether it was measured on each of the four model classes; "not measured on this class" is a finding, not an omission.
- Record what was searched and not found. No answer is better than a guessed one.
- Organize the synthesis by sub-question, then by model class, and end with one table of every source: ID, title, venue status, date, which sub-question it served.
</answer_requirements>
