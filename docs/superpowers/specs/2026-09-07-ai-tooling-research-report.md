# ai-tooling September 2026 refresh: the research report

Committed as evidence of the 2026-09-07 refresh, per the retention rule in the
`custom-plugin-refresh` skill. This is the verbatim output of the deep research run whose
prompt is in `2026-09-07-ai-tooling-research-prompt.md`. What the refresh actually did with
each finding is in `2026-09-07-ai-tooling-research-integration-design.md`; which sources were
verified against their primary pages, and which were not, is in
`2026-09-07-ai-tooling-source-verification.md`.

**Read this as a transcript, not as the knowledge base.** Seven of its framings were corrected
against the sources before anything entered a plugin body, and one claim was dropped outright.
The verification file records every correction. Where this report and a plugin body disagree,
the plugin body is the corrected text.

**The body below is reproduced verbatim and is not held to this repository's prose conventions.**
It contains the dash-aside construct that `CLAUDE.md` bans in our own writing. Editing it to house
style would break both its value as evidence and the digest recorded here, so it is left as it
came back. The convention governs what we write, not what we quote.

sha256 of the body below, as returned: `c18b3461e924b2b4a0a8b58b1d4f164c8fababb5d525bb5e6c0f336c184ccc85`

---

# Deep-research synthesis: prompting techniques that are actually measured by task × model class

(Pasted by the operator into the session on 2026-09-07; the output of a `/research:team-research --depth deep` run on the prompt saved as `prompt-engineering-deep-research.md`. Reproduced verbatim below.)

**Research window:** June 2025–7 September 2026. **All source/revision/venue metadata and availability below were checked 7 September 2026.** I treated a technique as "actionable" only where I could recover a model, task/dataset, metric, baseline and numerical effect. Results marked **single-source** should not yet become hard universal optimizer rules.

Class notation: **FR** = frontier reasoning; **HO** = hybrid open reasoner; **SO** = small open-weight instruct ≲30B; **ON** = older non-reasoning. `✓` means directly measured on that class; `—` means I found no admissible measurement; `△` means only an adjacent model outside your exact taxonomy.

## Executive answer

The main update is that the evidence increasingly argues **against global prompt recipes**. Model-family × task interactions are large enough that the optimizer should have conditional rules for few-shot count, rubric design, agent instructions, rule count, prompt format and RAG abstention rather than one default.

The strongest KB changes I would make are:

| Task/archetype | Technique worth adding | Measured effect | FR | HO | SO | ON |
|---|---|---:|:---:|:---:|:---:|:---:|
| Classification | **Calibrate shot count per model; 1–2 examples can be a format rescue, not a universal optimum** | Llama-3.1-8B AG News macro-F1 **.525→.866 at 2-shot, +.341**, but .553 at 8-shot; Llama-4-Scout instead best zero-shot | — | — | ✓ | ✓ |
| Judge / scalar rating | **Prefer 0–5 as the initial scale, then benchmark-calibrate** | pooled human–LLM ICC **.805→.853 vs 0–10, +.048**; but MT-Bench reverses it, .517 vs .570 | — | ✓ | ✓ | ✓ |
| Judge / rubric | **Permute score-option positions and aggregate 3–5 judgments when the judge is position-sensitive** | examples: Qwen3.5-27B HANNA ΔPearson **+.076**; Gemma3-12B SummEval **+.035** | — | ✓ | ✓ | — |
| Judge / non-verifiable | **Give a high-quality reference answer when one exists** | Llama3.1-8B judge acc **71.8→79.4%, +7.6 pp**; Mistral7B **61.2→69.6%, +8.4 pp** | — | — | ✓ | — |
| Judge / multilingual | **Generate an explicit criterion checklist before scoring** | Qwen2.5-7B MMEval reasoning pairwise acc **.64→.77, +.13**; LitEval Kendall **.17→.38, +.21** | — | — | ✓ | — |
| Agent / tools | **Tool description = purpose + usage guidance + parameter semantics; examples optional, not default** | full description augmentation median success **+5.85 pp**; examples ablation showed no overall material benefit | — | ✓ | △ | ✓ |
| Agent / system prompt | **Do not assume few-shot demonstrations help tool use** | Gemma-family hardware agent ECC **.956→.571 (-38.5 pp)** and .731→.179 (-55.2 pp) vs Markdown system prompt | — | ✓ | ✓* | — |
| Long-running agent | **Represent progress as externally verifiable state, not prose reminders** | GPT-5.4 controller success **69–78%**; frontier black-box agents fall to **3/9** at 100-item tasks | ✓ | — | — | ✓ |
| Coding-agent instruction files | **Prefer prohibitive guardrails over generic positive guidance** | Opus 4.6: removing "do not refactor unrelated code" reduced pass rate **20 pp**, p=.016; positive "guidance" rules tended to hurt | ✓ | — | — | — |
| General constraint-following | **Treat >5 simultaneous independent constraints as high-risk** | strongest CSE model falls below 50% joint success at **k=7**; 12/15 models do so at **k≤3** | ✓ | ✓ | — | — |
| Prompt format | **No universal Markdown/XML/JSON winner; calibrate format per task/model** | GPT-4o HumanEval: JSON **.886→.901, +1.5 pp**; LLM-"tuned" rewrite **.886→.748, −13.8 pp** | — | — | — | ✓ |
| Persona / role | **Use roles to steer depth/style, not as an accuracy enhancer** | GPT-4o-mini: generic expert role depth **+0.185**, but clarity **−0.180**; accuracy ≈unchanged | — | — | — | ✓ |
| Creative ideation | **Partition generations across heterogeneous ordinary personas** | unique semantic combinations bootstrap mean **39.15→56.97, +17.82**; one persistent persona develops fixation | — | — | — | ✓ |
| Coding/testing | **Generate tests independently of the implementation/trajectory** | overall fault detection **14%→25%, +11 pp**; GPT-5-mini +13.6 reported points vs agent-history condition | ✓ | △ | — | ✓ |
| RAG | **Explicit sufficiency/abstention check helps some models but cannot be trusted alone** | under conflicting evidence GPT-5.5 abstention **0→47.9%**; Gemini2.5 **5.2→55.2%**; Claude4.6 only **7.2→11.2%** | ✓ | ✓ | — | ✓ |
| Italian/multilingual | **Do not automatically translate Italian prompts to English** | GPT-4o-mini code pass rates: Python EN 23.35% vs IT 23.91%; Java 32.78 vs 33.39; ClassEval 37 vs 33 — task-dependent sign | — | △ | — | ✓ |
| Multimodal | **Sequence modalities according to the reasoning structure, not "image first" universally** | GPT-4o chemistry TF .32 vs interleaved .72 **+40 pp**; economics reverses: TF .73 vs interleaved .48 **−25 pp** | — | — | — | ✓ |

\*The hardware study labels several Gemma/Qwen local architectures differently from your exact taxonomy; I map only structurally compatible cases. Sources for these rows are developed below.

---

# 1. Technique-to-task map

### What replaced *The Prompt Report*?

I found a useful **2025/2026 peer-reviewed taxonomy**, Liu et al., *A comprehensive taxonomy of prompt engineering techniques for large language models*. It organizes techniques into profile/instruction, knowledge, reasoning/planning and reliability, but it is a **survey/taxonomy, not a quantitative meta-analysis of task × technique × current-model effect sizes**. So it is useful for ontology maintenance but not as the optimizer's measurement table.

The closest recent quantitative multi-technique study I found is Santana et al., arXiv:2506.05614: **14 techniques × 10 software-engineering tasks × four models** including DeepSeek-V3 and o3-mini. It is still only one domain. Selected aggregate task-level results versus the simple control prompt were:

| Task | Best non-covered technique | Metric | Best | Control | Δ |
|---|---|---|---:|---:|---:|
| Clone detection | nearest-neighbor exemplar selection, ES-KNN | F1 | 68.60 | 66.03 | +2.57 |
| Exception-type prediction | ES-KNN | accuracy | 82.50 | 78.16 | +4.34 |
| Code translation | ES-KNN | CodeBLEU | 42.08 | 30.19 | **+11.89** |
| Assert generation | ES-KNN | BLEU | 65.44 | 25.24 | **+40.20** |
| Mutant generation | ES-KNN | BLEU | 69.93 | 67.98 | +1.95 |
| Code generation | Universal Self-Consistency | CodeBLEU | 24.44 | 23.18 | +1.26 |

Bug fixing and summarization are important negative controls: the nominal best prompting variants were essentially tied with, or slightly worse than, the control. ES-KNN was particularly consistent for tasks where selecting semantically similar examples gives the model a local task pattern. The study explicitly found no globally dominant technique. arXiv:2506.05614 remains a preprint as of the check date.

A second useful result is **prompt-technique aging**. Rudyk et al., arXiv:2608.24641, accepted at **ICSME 2026**, partially replicated code-prompt experiments across model generations. Few-shot relative to zero-shot changed differently by family: Qwen2→Qwen2.5 went from negative few-shot effects to approximately **+7.2%, +1.4%, −1.3%** across evaluated settings; GPT-3.5→GPT-4o showed diminishing few-shot gains, roughly **+11% to +4.8%** in one corresponding comparison. The important optimizer finding is not the precise winner: **prompt-technique transfer across model generations is empirically unsafe**.

### Classification is the clearest new example

On AG News, Llama-3.1-8B is catastrophically poor zero-shot but is "repaired" by one or two demonstrations: macro-F1 **.5250 zero-shot → .8646 one-shot → .8664 two-shot**, then down to **.5530 at eight shots**. By contrast, Llama-4-Scout-17B is best at zero-shot, **.8771**, and one-shot falls to **.6948**. GPT-4o-mini improves from .8446 to .8970 by eight shots, but that gain is not statistically significant in the study. This is arXiv:2607.22969 v1, single task, n=200, so it is **highly actionable as a warning but not enough for a universal k-selector**.

**KB rule:** replace "use 3–5 examples" with **"sweep k∈{0,1,2,3,5,8} on the target model when classification accuracy matters; a demonstration may primarily repair task/output interpretation rather than add knowledge."**

---

# 2. Judge and evaluator prompts

This is one of the areas where there is enough new evidence to make several fairly concrete rules.

## FR

For agentic rubric verification, RuVerBench tests one rubric criterion at a time against long deep-research and coding outputs. Strong frontier judges already perform well with a simple **binary criterion-specific verification prompt**, e.g. GPT-5.4 balanced accuracy about **91.4% on deep-research rubrics and 89.4% on coding rubrics**. Making the instructions artificially "strict" does **not** reliably help strong judges; prompt variants sometimes reduce performance. RuVerBench v2, arXiv:2606.29920, was accepted to **EMNLP 2026**.

For frontier judges, therefore, the optimizer should prefer:

> one criterion → binary satisfaction decision → brief evidence-based justification → do not expand the criterion.

Not a giant holistic rubric prompt.

## HO

**Scale choice:** Qwen3-32B and DeepSeek-v3.2 are part of the 0–5/0–10/0–100 study. Across all judges and datasets, human–LLM ICC was **.853 for 0–5, .805 for 0–10, .840 for 0–100**. But heterogeneity matters: MT-Bench had **.517 / .570 / .470**, so 0–10 actually won there. Qwen's model-aggregated ICC was .731/.684/.714; DeepSeek .696/.670/.624.

**Rubric-label order:** Qwen3.5 judges show measurable option-position bias. Balanced score permutations improved human correlation—for example **+0.076 Pearson on HANNA with Qwen3.5-27B**. Much of the benefit appears within roughly 3–5 permutations, although effect size is model/dataset specific.

**Strictness is capacity-dependent:** in RuVerBench agentic coding, changing default to strict prompting improved some weaker open judges—e.g. Qwen3.5-27B by **+11.8 points** in the reported overall metric—but the same strategy is not reliably beneficial for stronger models. This should be a **conditional fallback**, not the base judge template.

## SO

Two techniques have unusually strong evidence here.

First, **reference-guided judging**. In arXiv:2602.16802, adding a good reference answer to the evaluator improves judge accuracy dramatically for several smaller models:

- Llama-3.1-8B: **71.8→79.4%, +7.6 pp**
- Mistral-7B-v0.3: **61.2→69.6%, +8.4 pp**
- Gemma2-9B: **80.8→85.7%, +4.9 pp**
- one counterexample: Qwen2.5-14B **83.3→82.4%, −0.9 pp**

So the rule is strong but not universal.

Second, **checklist engineering**. GlobalNLP 2025 used Qwen2.5-7B as a multilingual judge. On MMEval reasoning, pairwise accuracy increased from **.64 to .77 (+.13)**; on LitEval, pointwise Kendall correlation rose from **.17 to .38 (+.21)**. The technique creates an intermediate checklist of concepts/criteria, then judges against it. This is peer-reviewed workshop evidence rather than only an arXiv preprint.

SLMJury adds an important negative result. Across 0.6–14B judges, its best closed-ended judge, Phi-4 14B, reaches **89.55%** accuracy. But multi-agent Reflect–Critique–Refine debate **degrades** judge accuracy in all tested configurations; majority voting among the three strongest judges gives only a negligible gain over the best single judge. Persona wrappers can also severely damage weaker judges even though strong small judges are relatively persona-resistant. arXiv:2606.07810 v1, currently unreviewed.

## ON

GPT-4o and Gemini2.5 also support the 0–5 pooled-default finding. GPT's model-level human-agreement ICC is **.816 / .760 / .810** for 0–5/0–10/0–100; Gemini is .782/.749/.784.

### What I would put in the judge optimizer

The default template should therefore be **criterion-decomposed, reference-guided where a trustworthy reference exists, and 0–5 only when scalar rating is genuinely needed**. For score-selection judges, add permutation calibration when testing detects position sensitivity. Do not default to debate, strong judge personas or a monolithic 20-item rubric.

I did **not** find a sufficiently clean 2025-06→2026-09 prompt-only result showing that "ask the judge for a confidence probability" improves human agreement/calibration. Treat confidence elicitation as **not measured**, not a recommended technique.

Likewise, I found no in-window study establishing pairwise as generically superior to pointwise. The closest clean direct result is pre-window arXiv:2504.14716, where adversarial distractors flipped pairwise preferences roughly **35%** of the time versus about **9%** for absolute scoring. It should remain background evidence, not a new 2026 rule.

---

# 3. Agent instructions and tool descriptions

## FR

The most surprising result is the Opus 4.6 coding-agent rule study. On SWE-bench Verified:

- having rule files improved pass rate by roughly **7–14 pp** depending condition;
- random rules helped about as much as expert-curated rules;
- **negative constraints/guardrails were the only individually beneficial rule type**;
- removing the particularly useful "do not refactor unrelated code" guardrail cost **20 pp**, McNemar p=.016;
- increasing the persistent file from 0 to **50 rules did not produce a statistically significant collapse**; one count experiment had 60.3% at zero rules and 66.7% at 50.

That directly contradicts applying synthetic constraint-count findings to coding-agent instruction files. More on that distinction in §4.

For long-horizon goals, prompt restatement is not enough. PushBench shows Claude Code Sonnet 4.6 and Codex/GPT-5.4 doing reasonably well at 50-artifact jobs but falling to **3/9 successful runs per condition at 100 artifacts**. A controller that exposes externally verified state/progress achieves **69–78% success** and eliminates duplicate submissions.

**Optimizer implication:** for agentic jobs, convert "keep going until you have N valid results" into a stateful invariant such as `verified_done / target`, not repeated prose.

## HO

MCP tool-description augmentation has the cleanest general ablation. Across MCP-Universe, enriching descriptions with purpose, guidance, limits, parameter explanation and examples gives median task success **+5.85 pp** and partial-goal completion **+15.12%**, but also **+67.46% execution steps** and regressions on 16.67% of tasks. GPT-4.1 alone goes **18.18→29.44% success (+11.26 pp)**; Qwen3-Coder goes **19.91→25.97 (+6.06 pp)**.

Crucially, ablation does **not** support "put examples in every tool description": removing examples had essentially no overall success penalty. Compact **purpose + guidance** was sometimes better than the full verbose description. I found no isolated controlled experiment proving that renaming a parameter alone improves tool selection.

The local hardware-agent study reinforces this. Comprehensive descriptions usually reduce tool failures, but system-prompt demonstrations are dangerous on some Gemma variants: one Gemma configuration drops **.956→.571 ECC**, another **.731→.179**, going from Markdown instructions to few-shot. GPT-OSS/Qwen hybrid models show only tiny gains from Markdown itself.

## SO

History scope becomes especially important. In the same hardware benchmark, Llama-3.1-8B gets **ECC .445 with task-scoped history versus .157 with run-cumulative history**, a **+28.8 pp** advantage for clearing irrelevant accumulated state. Larger open models often show the opposite or much smaller effect.

That is a concrete small-model rule:

**SO agent → prefer current-task state + compact persistent invariants; do not indiscriminately replay the whole trajectory.**

## ON

GPT-4.1 benefits from richer MCP descriptions as above. OpenAI's GPT-4.1 engineering guidance also reports an internal **+2% SWE-bench Verified pass rate** from providing tools through the API's parsed tool definitions rather than manually injecting schemas into the system prompt. This is vendor-measured rather than peer-reviewed; it corroborates the research but should have lower evidence weight.

### Skills, instruction files, progressive disclosure and subagents

Anthropic's **Agent Skills** design—always expose compact `name`/`description`, load the full skill only after selection—is a sensible **progressive-disclosure architecture**, and Anthropic's September 2025 tool-writing guidance strongly recommends distinct purpose and high-signal descriptions. Claude Code, Codex and GitHub Copilot likewise recommend scoped instruction files and avoiding conflicts. But I found **no public isolated effect-size experiment** for:

- progressive disclosure vs loading all skills;
- trigger-phrase calibration;
- "ideal" skill-description length;
- orchestrator→subagent brief format;
- subagent→orchestrator return-summary format.

Those should stay documented as **vendor guidance, not measured optimizer rules**.

---

# 4. Instruction-following capacity by model size

This section gives the clearest answer to the "8–12 rules" question.

## FR

Constraint Saturation Evaluation (CSE), arXiv:2608.12426, varies **1–12 simultaneous independently verifiable constraints**, 36 types, 369,753 checks. The smallest `k` at which probability of satisfying **all constraints** falls below 50% is:

| Model | k* |
|---|---:|
| GPT-5.5 | **7** |
| Claude 4.7 Opus | **6** |
| Gemini 3.1 Pro | **4** |
| Claude 4.6 Opus | **3** |
| GPT-5.4 Pro | **3** |
| GPT-5.2 | **2** |

At `k=8`, aggregate per-constraint correctness remains around **40.7%**, yet success on **all eight** is only **5.7%**. Each additional constraint multiplies the mean per-constraint survival rate by about .922. Structural constraints deteriorate roughly twice as fast as simple lexical ones.

So "the model can follow each rule individually" is a very poor predictor of conjunction success.

## HO

In the same CSE benchmark, DeepSeek-V4-Pro reaches the <50% boundary at **k=3**; a Qwen3-235B-class model at **k=2**. Thus open reasoning does not eliminate compositional saturation.

## SO / ON

The peer-reviewed **ManyIFEval / StyleMBPP** paper in Findings of EMNLP 2025 independently confirms the multiplicative failure. A striking older-model example: Gemini-1.5-Pro follows one "characters per line" constraint about **99%** of the time alone but only **20%** when composed with five other instructions, **−79 pp**. Claude-3.5 falls approximately **97%→2%, −95 pp** in the analogous condition. It also includes Llama-3.1-8B among the open models.

### Rule ordering

CSE randomized order and found essentially no generic order relationship: mean absolute Spearman `|ρ| ≈ .029`. So I found no evidence for a universal "put the most important rule first" accuracy effect in ordinary non-conflicting constraints.

### Priority statements and conflicting rules

ManyIH-Bench goes up to 12 instruction privilege tiers. Even frontier models are around 40% overall; moving from 6→12 tiers degrades 11/12 tested models. Merely changing priority encoding from ordinal labels to scalar numbers changes GPT-5.4 by about **8.4 points** and Opus 4.6 by **8.0 points**, despite logically preserving the ordering.

That demonstrates **priority-format fragility**, but it is not evidence that adding "IMPORTANT" or "highest priority" improves compliance.

CSE's impossible-conflict probes also show asymmetrical sacrifice behavior: concrete inclusion can dominate avoidance; explicit prohibition can dominate a competing requirement. But because these are contradictory instruction pairs, this is **not** a causal test that rewriting every positive instruction as a negative one improves normal prompts.

### What should replace "8–12 rules"?

For **ordinary generation where each rule must simultaneously hold**, I would encode this derived operational rule:

> **0–3:** normal.
> **4–5:** monitor/verifier recommended.
> **>5:** split into stages or verify/retry unless target-model evals prove otherwise.

That **3–5 threshold is my synthesis**, not a threshold directly optimized by a paper.

And add an exception:

> **Persistent coding-agent guardrail files are a different task family.** Opus 4.6 showed no collapse through 50 rules on SWE-bench; do not apply the 3–5 compositional-output limit to them.

This distinction is one of the most important findings of the research.

---

# 5. Prompt format, ordering and role/persona

## Prompt format

There is **no defensible universal rule that Markdown > XML > JSON > prose**.

The best clean controlled comparison I found is GPT-4o on HumanEval, 8,200 executions:

| Prompt representation | Average pass rate | Δ vs plain |
|---|---:|---:|
| Plain baseline | .886 | — |
| JSON | **.901** | **+1.5 pp** |
| Markdown | .890 | +0.4 pp |
| YAML | .873 | −1.3 pp |
| LLM-"optimized" rewrite | **.748** | **−13.8 pp** |

The format main effect is statistically significant but small; the generated "optimized" prompts are dramatically harmful. This is arXiv:2608.21074 v1, a seminar/preprint study rather than a reviewed venue, and **only GPT-4o**.

Separate robustness work across 52 Natural Instructions tasks shows that semantically irrelevant punctuation/format changes still move scores substantially on small models. Llama3.1-8B had median accuracy .563 and cross-format spread .161; Qwen2.5-7B spread .190. DeepSeek-V3 is much more stable, spread .045, and GPT-4.1 .032. Ensembling predictions over semantically equivalent prompt formats reduces spread—DeepSeek .045→.028, GPT-4.1 .032→.018—with almost no accuracy change.

Thus:

**format is a model/task hyperparameter, not semantic truth.**

I found no post-June-2025 controlled multi-family benchmark demonstrating a universal benefit of **XML specifically**, nor a clean whitespace-only winner.

## Persona and role prompting

The strongest 2026 study finds that a one-line expert role mostly changes **response character**, not capability. With GPT-4o-mini over 1,140 open-ended questions:

- overall rating: baseline 4.390 vs generic expert 4.373;
- accuracy: 4.054 vs 4.052, effectively zero;
- expertise depth: **3.638→3.823, +.185**;
- clarity: **4.896→4.716, −.180**.

More elaborate persona retrieval increases depth further but also worsens clarity.

**Optimizer rule:** persona prompting should live under **style/depth/audience control**, not "improve accuracy."

No FR, HO or SO direct replication of that exact experiment was found.

---

# 6. Long-context and retrieval-grounded prompting

## Many-shot ICL

I did **not** find a post-June-2025 current-model study supporting a universal many-shot count or a clean condition where many-shot prompting systematically beats fine-tuning.

The recent AG-News result actually cautions against monotonicity: Llama3.1-8B peaks at two examples and collapses again by eight; some larger models are best zero-shot.

The canonical pre-window many-shot paper remains useful background—it found large gains up to hundreds/thousands of examples on GPT-4o/Gemini1.5 in some tasks—but I would **not port its shot-count defaults into GPT-5/6, Claude 4.6 or Qwen3 without new measurements**.

## RAG: abstention when the documents do not support an answer

A very relevant August 2026 peer-reviewed article directly tests three prompts:

- **P1:** answer from context;
- **P2:** answer only if evidence is sufficient, otherwise abstain;
- **P3:** assess evidence sufficiency first, then answer/abstain.

Models include GPT-5.5, Claude Sonnet4.6, GPT-4o-mini, Gemini2.5Flash and DeepSeek V3/R1.

Under **conflicting retrieved evidence**, P1→P3 abstention changes include:

- GPT-5.5: **0→47.9%**
- Gemini2.5: **5.2→55.2%, +50 pp**
- Claude Sonnet4.6: **7.2→11.2%, only +4 pp**

Even after prompting, all seven models have high over-answer rates under conflict; across the benchmark they remain **65–91%** in the worst conflicting-evidence condition. Claude4.6 is especially instructive: it often notices the conflict but answers anyway.

So the KB rule should be:

> **RAG prompt:** explicitly test evidence sufficiency before answering and specify abstention, but never treat that instruction as a verifier. Conflicting evidence needs retrieval/conflict checking outside the generation prompt.

That result is much stronger than generic "tell the model to say I don't know."

A second 2026 small-model benchmark similarly finds that explicit abstention prompting still answers **41.6% of misleading-context questions**, with 63% of those answers copying the planted wrong entity.

## Lost in the middle / later

"Lost-in-the-later" remains observable in 2025–26 across o3, Qwen3, GPT-4o, Gemini1.5 and Llama variants; reasoning/CoT does **not** automatically solve grounding and sometimes reduces contextual use.

The paper's explicit "use only the input context / consider all segments evenly" CK prompt improved contextual grounding and summarization, but the exact intervention tables I could verify were primarily on Llama-3.2-90B, which falls outside your four strict cells. Therefore:

**phenomenon confirmed across classes; prompt-treatment effect not cell-admissible.**

## Quote-first, citations, Chain of Density

I searched specifically for 2025-06→2026-09 controlled prompt-only ablations of:

- quote evidence before answering;
- mandatory citation instructions;
- quote-first vs answer-first;
- recent Chain-of-Density successors;
- faithfulness wording in summarization.

I did **not** find a result meeting your full model+baseline+effect-size criterion that was not already covered by your vendor/context sources. I would leave those cells **unmeasured**, rather than importing vendor advice as experimental evidence.

---

# 7. Generation task families

## Code generation and agentic coding

### Strong technique 1 — independent/test-first validation

The clearest result is not "ask for better tests"; it is **prevent the test generator from seeing the potentially faulty implementation**.

Across five models, generating tests after faulty code reduces fault detection from **25% to 14%, −11 pp**. Using fresh task-only context rather than full agent history improves fault detection by approximately:

- GPT-5-mini: **+13.6**
- GPT-4.1-mini: **+17.7**
- Claude Haiku 4.5: +10.6
- DeepSeek: +13.8
- Llama3.3-70B: +7.9

reported percentage-point differences in the paper.

This is a strong reason for a **separate test-generation subagent/context**.

### Strong technique 2 — relevant exemplar retrieval

From the 14-technique SE study, ES-KNN is the most consistently successful non-reasoning technique for code translation, assert generation, clone detection and exception prediction. For translation, CodeBLEU is **30.19→42.08 (+11.89)**; assert generation BLEU **25.24→65.44 (+40.20)**.

### Strong technique 3 — coding-agent guardrails

On Claude Opus4.6 SWE-bench, negative scope guardrails are the only individually beneficial rule type, while generic positive directives can harm.

### Harmful techniques

Three unusually clear harms:

1. **implementation-aware test generation**: 25→14% fault detection;
2. automated generic "prompt tuning" of GPT-4o HumanEval: **−13.8 pp** pass rate;
3. few-shot system examples in some Gemma tool agents: **−38.5 to −55.2 pp ECC**.

I did **not** find a sufficiently controlled in-window study isolating "write the full specification first" versus an otherwise identical direct prompt on a modern SWE-bench agent. Repository context is clearly important in agent systems, but existing evidence bundles retrieval, tool harness and instruction files rather than isolating a specification-first phrase.

## Creative/open-ended generation

Ordinary personas are useful here for a different reason than "expertise": **distribution partitioning**.

In a GPT-4o ideation experiment:

- default: bootstrap mean **39.15 unique idea combinations**;
- "creative entrepreneur" personas: **50.40, +11.25**;
- heterogeneous ordinary-person personas: **56.97, +17.82**.

Pairwise semantic distance also increases from **2.04→2.36 (+.32)** under ordinary personas. But within one persona, repeated generations become progressively more fixed; the category-generation slope declines significantly.

So for portfolio generation:

> **sample across distinct perspectives; refresh/reset the persona between batches.**

Do not interpret "act as a world-class creative genius" as the diversity-optimal persona—it measured worse than mundane heterogeneous personas.

## Conversational product system policies

I did not find a qualifying 2025-06→2026-09 controlled study isolating:

- refusal wording A vs B;
- escalation-rule wording;
- positive vs empathetic refusal style;
- a prompt-only intervention preserving assistant persona over long product conversations,

with effect sizes on your exact model classes.

There are persona-stability benchmarks and CHI work showing drift or systematic stereotyping over turns, but they do not provide a clean prompt-technique baseline sufficient for your optimizer.

Keep this cell **open**.

---

# 8. Multimodal and multilingual prompting

## Multimodal

The clearest controlled evidence is the peer-reviewed June 2025 study comparing **text-first, image-first and interleaved** prompts on GPT-4o, Gemini1.5 and Claude3-class models.

There is no universal winner. Examples make the interaction obvious:

| Model/task | Text-first | Image-first | Interleaved | Winner |
|---|---:|---:|---:|---|
| GPT-4o chemistry | .32 | .67 | **.72** | interleaved, +40 pp vs TF |
| GPT-4o economics | **.73** | .58 | .48 | TF, +25 pp vs interleaved |
| Gemini1.5 chemistry | .25 | **.43** | **.43** | image/interleaved, +18 pp |
| Claude3 physics | **.48** | .18 | .26 | TF, +30 pp vs IF |

The paper's broader conclusion is that sequencing should follow the **logical dependency structure** of the question; nested/cross-referenced tasks often benefit from interleaving rather than blindly putting the image first.

This is, however, **ON-only evidence**. I found no equivalently controlled 2026 comparison on Gemini3, GPT-5 vision, Claude4.6+, Gemma4 or Qwen3-VL.

I also found no admissible new prompt-only effect-size experiment for:

- "describe the image first, then answer" on current FR models;
- scanned-PDF prompt wording;
- prompting low-resolution vs high-resolution document inputs independently of API/image processing;
- audio prompt wording.

These remain **not measured** for your KB.

## Multilingual, Italian first

A 2026 curated coding benchmark directly translates identical Python/Java tasks into **English, Chinese, Hindi, Spanish and Italian**.

For GPT-4o-mini:

- Python pass rate: EN **23.35**, IT **23.91** → Italian **+0.56 pp**
- Java: EN **32.78**, IT **33.39** → **+0.61 pp**
- ClassEval: EN **37**, IT **33** → **−4 pp**

Other model/task combinations likewise change sign; for one DeepSeek Java setting Italian is roughly +2.08 points, while other cases favor English.

This directly rejects the optimizer rule **"translate non-English user prompts into English first."** The safer rule is:

> preserve the user's task language by default; translate only if target-model evaluations for that archetype demonstrate a benefit.

There is still no broad Italian study showing whether **system instructions should be English while user content remains Italian** for GPT-5/Claude4/Qwen3/Gemma3.

The multilingual checklist-judge study is promising for SO judges, but its languages did **not include Italian**, so its multilingual benefit should not be marked as Italian-tested.

I also found no recent controlled benchmark meeting your criteria for **non-English JSON/format compliance of Gemma3/Llama3.1-8B/Mistral Small specifically**. That remains a useful benchmark to build.

---

# Recommended optimizer rule changes

Taken together, I would change the KB logic in these ways:

| Existing/general intuition | Replacement rule |
|---|---|
| "Use a few examples" | **Few-shot is model × task calibrated.** Test 0/1/2 first; small models can be rescued by one example, while other models degrade. |
| "8–12 rules is okay" | **For simultaneously verifiable output constraints, 3–5 is the conservative zone; split/verify above 5.** Do not apply this cap to agent rule files. |
| "Detailed tool descriptions are better" | **Purpose + usage guidance + parameter semantics first; examples only if evals justify them.** |
| "Give agents more context" | **Small agents: task-scoped context. Long jobs: explicit verified state. More trajectory is not automatically better.** |
| "Positive instructions are clearer" | **Coding-agent persistent rules are an exception: prohibitive scope guardrails have stronger evidence than generic positive guidance.** |
| "Use 1–10 / 1–100 for finer judging" | **0–5 is the pooled judge default; benchmark-specific calibration overrides it.** |
| "A sophisticated judge persona helps" | **No. Reference answer/checklist/decomposition have stronger evidence.** |
| "Pairwise is more reliable" | **Not established universally. Choose protocol from task/eval evidence.** |
| "JSON/Markdown/XML is best" | **No universal prompt syntax winner. Format is a model/task hyperparameter.** |
| "Act as an expert to improve accuracy" | **Persona mainly alters depth/style; don't enable it for accuracy unless target eval says so.** |
| "Use one creative persona" | **Use heterogeneous personas across independent samples; refresh perspective to fight fixation.** |
| "Ask the same coding agent to write code then tests" | **Separate implementation and test contexts.** |
| "Tell RAG to abstain if unsupported" | **Do that, but also independently verify sufficiency/conflict; prompting alone fails badly under misleading evidence.** |
| "Translate Italian to English" | **Do not by default. Language effect changes sign by task/model.** |
| "Put the image first" | **Order/interleave modalities according to information dependency.** |

---

# Searches performed where no qualifying result was found

I specifically searched, but did **not** find evidence meeting your model+task+metric+baseline threshold for: a post-*Prompt Report* quantitative cross-domain meta-analysis; a modern direct universal pointwise-vs-pairwise winner; judge confidence elicitation that improves human agreement; isolated parameter-name ablations; trigger-phrase calibration; measured progressive disclosure vs full skill loading; optimal subagent briefing/return-summary format; explicit-priority statement vs no-priority causal effect; a universal Markdown/XML/JSON/prose winner; a current-model many-shot optimum or many-shot-vs-fine-tuning threshold; controlled quote-first/citation-first RAG prompting; a current Chain-of-Density successor with prompt-only effect sizes; refusal/escalation phrasing for product assistants; current-model scanned-PDF/audio prompt wording; or an Italian-specific experiment on English-vs-Italian system instructions.

That absence is meaningful: those should remain **unknown cells**, not "best practices."

---

# Source ledger

All entries checked **2026-09-07**.

| ID | Source | Revision / venue status | Used for |
|---|---|---|---|
| S1 | *Which Prompting Technique Should I Use? An Empirical Investigation of Prompting Techniques for Software Engineering Tasks*, arXiv:2506.05614 | arXiv preprint; no peer-reviewed venue found | Q1, Q7 |
| S2 | *Aging of Prompt Engineering Techniques Across LLM Versions*, arXiv:2608.24641 | accepted **ICSME 2026** | Q1, Q7 |
| S3 | Liu et al., *A comprehensive taxonomy of prompt engineering techniques for large language models* | **Frontiers of Computer Science**, 2026; version of record Oct 2025 | Q1 |
| S4 | *When Does Few-Shot Prompting Help?*, arXiv:2607.22969 v1 | arXiv v1, unpublished | Q1, Q6 |
| S5 | *Grading Scale Impact on LLM-as-a-Judge*, arXiv:2601.03444 | arXiv; authors list "under review" | Q2 |
| S6 | *Am I More Pointwise or Pairwise? Revealing Position Bias in Rubric-Based LLM-as-a-Judge*, arXiv:2602.02219 | arXiv v2 Jun 2026; no accepted venue found | Q2 |
| S7 | *Can LLM-as-a-Judge Reliably Verify Rubrics in Agentic Scenarios?*, arXiv:2606.29920 v2 | **accepted EMNLP 2026** | Q2 |
| S8 | *SLMJury: Can Small Language Models Judge as Well as Large Ones?*, arXiv:2606.07810 v1 | arXiv v1; unpublished | Q2 |
| S9 | *References Improve LLM Alignment in Non-Verifiable Domains*, arXiv:2602.16802 | arXiv preprint | Q2 |
| S10 | *Checklist Engineering Empowers Multilingual LLM Judges*, arXiv:2507.06774 | **GlobalNLP/RANLP 2025 workshop**, peer-reviewed | Q2, Q8 |
| S11 | *MCP Tool Descriptions Are Smelly!*, arXiv:2602.14878 | arXiv preprint | Q3 |
| S12 | *Benchmarking AI Agents for Hardware Design Automation via MCP Tool Calling*, arXiv:2608.26199 | arXiv preprint | Q3, Q5 |
| S13 | *Push Your Agent: Measuring and Enforcing Quantitative Goal Persistence*, arXiv:2605.23574 | arXiv preprint | Q3 |
| S14 | *Do Agent Rules Shape or Distort? Guardrails Beat Guidance in Coding Agents*, arXiv:2604.11088 | arXiv v1; unpublished | Q3, Q4, Q7 |
| S15 | *Large Language Models Can Follow Instructions, But Not Many at Once*, arXiv:2608.12426 | arXiv v1; no accepted venue found | Q4 |
| S16 | *When Instructions Multiply*, arXiv:2509.21051 | **Findings of EMNLP 2025** | Q4 |
| S17 | *Many-Tier Instruction Hierarchy in LLM Agents*, arXiv:2604.09443 | arXiv; no accepted venue found | Q4, Q5 |
| S18 | *When Does Persona Prompting Actually Help?*, arXiv:2605.29420 | arXiv v1; submitted for review | Q5 |
| S19 | *When Punctuation Matters*, arXiv:2508.11383 | arXiv preprint | Q5 |
| S20 | *PromptResponse: Optimizing Prompts for LLM Coding Tasks*, arXiv:2608.21074 | arXiv v1; seminar/preprint, not peer-reviewed | Q5, Q7 |
| S21 | *Lost-in-the-Later*, arXiv:2507.05424 | arXiv preprint | Q6 |
| S22 | Zhang & Wu, *Do LLMs Know When Evidence is Insufficient?* | **Computers, Materials & Continua 89(1), Aug 2026**, peer-reviewed journal | Q6 |
| S23 | *Prompt-Based Abstention Fails Under Misleading Context*, arXiv:2608.22228 | arXiv preprint | Q6 |
| S24 | *On the risk of coding before testing*, arXiv:2607.05139 | arXiv v1 | Q7 |
| S25 | *Examining and Addressing Barriers to Diversity in LLM-Generated Ideas*, arXiv:2602.20408 | working paper / arXiv | Q7 |
| S26 | *Large Language Models for Code Generation from Multilingual Prompts*, arXiv:2607.14816 | arXiv v1 | Q8 |
| S27 | Wardle & Sušnjak, *Image First or Text First?* | **Big Data and Cognitive Computing 9(6), 149**, peer-reviewed; version of record 3 Jun 2025 | Q8 |
| C1 | *Pairwise or Pointwise? Evaluating Feedback Protocols for Bias in LLM-Based Evaluation*, arXiv:2504.14716 | pre-window canonical citation only | Q2 |
| C2 | *Many-Shot In-Context Learning*, arXiv:2405.09798 | pre-window canonical citation only | Q6 |
| C3 | Schulhoff et al., *The Prompt Report*, arXiv:2406.06608 | pre-window baseline survey | Q1 |

## Bottom line for the knowledge base

The most important architectural change is to make the optimizer **empirical and model-aware**, not merely archetype-aware. The 2025–26 evidence repeatedly shows the same technique changing sign between nearby model generations: few-shot can be +34 F1 points or harmful; strict judge prompts can help weaker open judges while hurting stronger ones; cumulative history helps one agent class and destroys another; Italian can beat English on one coding setting and lose on another.

The cells with enough evidence for an actual default today are **judge scale/reference/checklist design, tool-description anatomy, explicit agent progress state, coding-agent negative guardrails, constraint-count caution, independent test generation, RAG sufficiency checks, and heterogeneous-persona creative sampling**. For prompt syntax, many-shot counts, subagent briefs, quote-first RAG, system-policy wording, scanned PDFs/audio, and Italian system-prompt language, the most accurate KB entry is still **"not measured sufficiently."**
