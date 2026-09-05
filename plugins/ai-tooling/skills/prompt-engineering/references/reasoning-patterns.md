# Reasoning Patterns for Prompt Engineering

On-demand reference for the `prompt-engineer` agent and the `/prompt-optimize` command. Read this file when a task needs reasoning structure beyond plain few-shot or basic chain-of-thought, or when the target is a reasoning model and you must decide whether any explicit pattern is warranted at all. Each pattern below states what it is, when to apply it, the prompt skeleton, and the main failure modes. Patterns 11-14 are the token-efficiency patterns: read them, plus the "Cost-aware selection" section, whenever token cost or latency is part of the optimization target.

> **Maintenance note.** This file mixes three kinds of content with different shelf lives:
> selection policy (stable), the pattern catalog (slow-moving), and empirical results (dated and
> model-specific). Splitting it into selection / catalog / evidence was considered in the
> 2026-08-10 review and deliberately deferred: the selection cheat sheet and the reasoning-model
> section are the parts read on most invocations, and they are already at the top. If the
> empirical numbers below start driving decisions on their own, that is the signal to split and
> to date each result. Empirical results were re-checked on 2026-09-05 against arXiv metadata;
> venue and revision status is stated inline where it matters.

## Selection cheat sheet

| Task shape | First-choice pattern |
|---|---|
| Any task on a reasoning model (extended thinking, o-series, R1 class) | None by default; see "Reasoning models change the defaults" below |
| Specific factual question over a known domain | Step-Back |
| Math, logic, multi-step arithmetic | Chain-of-Thought + Self-Consistency |
| Tool use, search, multi-turn interaction with environment | ReAct |
| Open-ended exploration with backtracking | Tree-of-Thought |
| Complex task that decomposes into ordered sub-tasks | Plan-and-Solve or Least-to-Most |
| Long generation needing structure (essay, report) | Skeleton-of-Thought |
| Iterative correction loop on a single output | Reflexion / Self-Refine |
| Multi-hop QA where intermediate questions are needed | Self-Ask |
| Math/symbolic/commonsense where output-token cost or latency matters | Chain of Draft (few-shot, frontier models) |
| Mixed-difficulty workload under a cost target | Token-budget prompting (TALE-style) on models that accept a budget; the native effort setting on reasoning models |
| Any task on a reasoning model at its lowest effort setting | A brief explicit plan or thought summary at the start of the answer: the one scaffold that helps there (OpenAI GPT-5 guide) |
| Hybrid open reasoner (Qwen3, Gemma 4, DeepSeek V3.x, gpt-oss) under a cost target | Prompt-based depth self-selection at 9B and below; draft-agreement routing from 8B to 32B; see "Reasoning models change the defaults" |
| Small open reasoner (Gemma 4 E2B/E4B, Phi-4-mini, Qwen3-8B) | Zero-shot first; CoT and few-shot CoT are per-model choices that measured anywhere from a gain to a 56-point loss |

If two patterns fit, prefer the one that adds the least latency and token cost; the "Cost-aware selection" section below puts numbers on this.

## Reasoning models change the defaults

Reasoning models (Claude with extended/adaptive thinking, OpenAI o-series and successors, DeepSeek R1 class) internalize most of the patterns in this file. Determine the model class BEFORE selecting any pattern.

On reasoning models:

- **No explicit CoT scaffolds.** OpenAI's official guidance: "think step by step" and "explain your reasoning" prompts are unnecessary on reasoning models (the page says unnecessary, not harmful). Anthropic: "Prefer general instructions over prescriptive steps. A prompt like 'think thoroughly' often produces better reasoning than a hand-written step-by-step plan"; manual CoT with `<thinking>`/`<answer>` tags is a fallback for when thinking is off. The Wharton "Decreasing Value of Chain of Thought" study (Meincke et al., 2025, arXiv:2506.07142, v1 only and unpublished as of 2026-09) measured explicit CoT on reasoning models at marginal gains for 20-80% added time cost. One exception, from the OpenAI GPT-5 guide: at the **lowest effort setting** ("minimal"), asking for a brief explanation of the thought process at the start of the answer, and prompting the planning explicitly, improves results, because the model has few reasoning tokens to plan with. Use that scaffold there and nowhere else.
- **Never paste worked reasoning traces as exemplars.** Few-shot CoT often does worse than direct answering on RL-trained reasoners, and adding more exemplars, even optimal DeepSeek-R1 traces, degrades accuracy further through copied steps and failed strategy transfer; distilling the demonstrations into explicit insights instead recovered +14.0% on AIME'25 for GPT-4.1 and +2.7% for o1-mini (arXiv 2509.23196, 2025-09). Start zero-shot; if examples are needed for format or tone, show input and output only; if the demonstrations carry a strategy, state the strategy as an instruction. On Claude, an example that carries `<thinking>` tags teaches that reasoning style, which is the same mechanism pointed the other way.
- **Spend effort elsewhere**: precise success criteria, input curation, and the native effort setting beat any reasoning scaffold. The control is a parameter, not prompt text: `effort` on Claude (where `budget_tokens` is deprecated on 4.6 and returns a 400 error from 4.7 on, and Anthropic reports adaptive thinking beating extended thinking in internal evaluations), `reasoning_effort` on OpenAI, `thinking_level` on Gemini 3. A token budget written into the prompt is a soft hint on every one of them.
- **Patterns that keep value**: Self-Consistency only where answers are cheaply verifiable, and then voting among the first chains to finish rather than all of them (short-m@k, pattern 3); Tree-of-Thought only for genuinely search-structured tasks (game playing, theorem proving), preferably with deterministic checkers instead of model-judged scoring at the nodes.
- **Verification prompts are model-dependent.** "Check your answer against the criteria before finishing" still helps mid-tier models on coding and math, but the newest top-tier models self-verify; carried-over verification instructions there cause over-verification (token and latency waste). Anthropic's own guidance: a self-check instruction helps, except on Opus 5, where it should be removed. Remove them when migrating upward.
- **Cap the thinking by difficulty; overthinking is measured, not folklore.** On DeepSeek-R1-32B over AIME 2024/25 (arXiv 2604.10739, 2026-04), accuracy rises about 3.2 points per 500 thinking tokens from 0.5K to 2K, peaks at 55.8% at 12K, and falls to 54.9% at 16K; past about 7K tokens, correct-to-incorrect flips outnumber the reverse (83 to 11 at 16K), and 67.5% of the sampled negative flips were the model explicitly rejecting a correct answer. The optimal budget scales with difficulty (about 1.5K tokens at MATH-500 level 1 to about 8K at level 5); stopping at about 6K cut compute by about half for about 6% accuracy; a stop rule keyed on answer oscillation and hesitation markers ("wait", "reconsider") kept 97% of peak accuracy at 60% of compute. Reasoning traces also cross a commitment boundary well before the thinking block ends, after which further steps leave the answer unchanged (arXiv 2606.13603, 2026-06: early exit shortens chains up to 55% at negligible loss). Prompt-side levers: a lower effort level, and Anthropic's "choose an approach and commit to it, avoid revisiting decisions" for Opus 4.6 at high effort.
- **Hybrid open reasoners are controlled through their mode switch, not through prose.** On think/no-think models (Qwen3, Gemma 4, DeepSeek V3.x, gpt-oss) a few trigger tokens decide whether the model reasons (Mid-Think, arXiv 2601.07036: a leading "Okay" induces reasoning, the newline after `</think>` suppresses it), so control depth through the native mode token or a thinking prefill, not through "think briefly". Under a cost target, HRBench (arXiv 2605.28398, 2026-05, six hybrid models from 2B to 1.1T) finds training-free prompt-based depth self-selection Pareto-optimal on math and science at small scale (Qwen3.5-9B: 47.6% accuracy with 24% token savings, against 44.1% and 13% for an external router), speculative fast-then-escalate winning on code and at 20B and above, and no strategy dominating. Draft-agreement routing (DART, arXiv 2606.23181, EMNLP 2026 Findings) samples two no-think drafts, answers directly when they agree and thinks only when they disagree: thinking tokens fall 32% to 73% at parity or better from 8B to 32B (Qwen3-8B on MATH-500: 88.2% at 1,743 mean thinking tokens against 85.6% at 5,343 for always-think), and it trails always-think below 4B.
- **Small open reasoners get no default at all.** On Gemma 4 E2B/E4B/26B-A4B, Phi-4-mini-reasoning, Phi-4-reasoning, Qwen3-8B and Qwen3-30B-A3B (arXiv 2604.07035 v2, 2026-05, 19,992 evaluations), "prompting strategy changes model rankings rather than shifting all models uniformly": Gemma-4-E4B drops from 0.40 zero-shot to 0.34 with CoT on GSM8K, Phi-4-reasoning collapses from 0.67 under CoT to 0.11 under few-shot CoT on the same set, and some failures are interface adherence rather than reasoning. Evaluate zero-shot first; treat CoT and few-shot CoT as per-model choices, never as a default.

On non-reasoning models the patterns below apply as documented, with one caveat: CoT gains concentrate in math, logic, and symbolic tasks, and come with increased answer variability elsewhere (Sprague et al., 2024, arXiv:2409.12183, ICLR 2025; confirmed on soft-reasoning tasks by arXiv 2508.19827, EMNLP 2025, which also finds that how much a model's CoT drives its answer differs between instruction-tuned, reasoning and distilled models).

---

## 1. Chain-of-Thought (CoT)

Wei et al., 2022. The baseline reasoning pattern.

**What**: Ask the model to produce intermediate reasoning steps before the final answer.

**When**: Arithmetic, commonsense, symbolic reasoning, anything where the answer is a short string but the derivation matters.

**Skeleton**:
```
<task>...</task>
Think step by step. Show your work inside <reasoning> tags, then produce the final answer inside <answer> tags.
```

**Variants**:
- Zero-shot CoT: just "Let's think step by step" (Kojima et al., 2022).
- Few-shot CoT: include 2-4 worked examples with explicit reasoning chains.

**Failure modes**: hallucinated steps that look plausible, premature commitment to a wrong first step, token bloat on simple tasks.

**Reasoning-model note**: redundant on reasoning models (internalized) and officially called unnecessary by OpenAI. Never as few-shot exemplars on a reasoning model: worked reasoning traces degrade RL-trained reasoners (arXiv 2509.23196). On non-reasoning models, expect modest average gains with higher answer variability outside math and symbolic tasks.

**Cost note**: the baseline other patterns are priced against. When output-token cost matters, see Chain of Draft (pattern 11): near-parity on frontier models at roughly a tenth of the tokens.

---

## 2. Step-Back Prompting

Zheng et al., 2023 (Google DeepMind), "Take a Step Back: Evoking Reasoning via Abstraction".

**What**: Before answering the specific question, force the model to first ask and answer a more abstract question that recovers the underlying principles. Then ground the specific answer in those principles.

**When**: STEM questions, factual QA over a known domain, any prompt where the right answer follows from a general rule the model already knows.

**Two-step skeleton**:
```
Step 1 (Abstraction):
  Question: <specific question>
  What is the broader principle or general question behind this?
  Answer the abstract question first.

Step 2 (Reasoning):
  Using the principle from Step 1, answer the original specific question.
```

**Example**:
- Specific: "If pressure of an ideal gas doubles and temperature quadruples, what happens to volume?"
- Step-back: "What is the relationship between pressure, volume, and temperature for an ideal gas?" -> PV = nRT
- Apply: V scales by T/P = 4/2 = 2x.

**Failure modes**: the step-back question is rephrased too narrowly (same as the original), or the abstraction is correct but the application step skips a constraint.

**Cost note**: token-additive by construction (an abstraction question and its answer precede the actual reasoning). Proven for quality on abstraction-friendly tasks; never measured per token. Do not select it to reduce cost.

---

## 3. Self-Consistency

Wang et al., 2022.

**What**: Sample N independent CoT chains, then take the majority vote on the final answer.

**When**: Tasks with a discrete answer space (multiple choice, integers, classification) where a single chain is unreliable.

**Skeleton**: run the same CoT prompt N times with temperature > 0; aggregate answers.

**Failure modes**: expensive (Nx cost), useless when all chains share a systematic bias, breaks when the answer is free-form text rather than a discrete label.

**Reasoning-model note**: reasoning models already sample multiple internal paths. Keep this pattern only when answers are cheaply verifiable and the vote is deterministic.

**Cost note**: the one pattern with consolidated evidence against it on cost grounds. The Token Cost benchmark (arXiv 2505.14880) measures ~119 tokens per accuracy point at N=10 vs ~5 for zero-shot CoT, with the marginal price of the last accuracy points at ~6,700 tokens each. Reserve it for cases where each point is worth ~100x its marginal token price. When you do run it, vote among the first m chains to finish rather than all k (short-m@k, arXiv 2505.17813, v2 2026-02): shorter chains are more often correct within a question (the shortest sampled chain up to 34.5% more accurate than the longest), short-1@k matches majority voting with up to 40% fewer thinking tokens, and short-3@k beats it at every budget with up to 33% less wall time.

---

## 4. Tree-of-Thought (ToT)

Yao et al., 2023.

**What**: Model generates multiple candidate "thoughts" at each step, evaluates them, prunes losing branches, and explores promising ones (BFS or DFS).

**When**: Tasks with a large search space, where backtracking helps: game playing, creative writing with constraints, theorem-proof search, puzzle solving.

**Skeleton**:
```
At each step:
  1. Generate K candidate next-thoughts.
  2. Score each candidate against the goal (the model judges its own thoughts).
  3. Keep the top-M, discard the rest.
  4. Continue from each survivor.
```

**Failure modes**: very expensive, judge-prompt biases dominate, breaks down when the evaluation function is not actually learnable by the model.

**Reasoning-model note**: reserve for genuinely search-structured tasks; prefer deterministic checkers over model-judged scoring at the nodes.

---

## 5. ReAct (Reason + Act)

Yao et al., 2022.

**What**: Interleave reasoning ("Thought:") with tool calls ("Action:") and tool results ("Observation:"). The model thinks, acts, observes, and repeats.

**When**: Agent loops, tool use, RAG with iterative retrieval, anything where the model needs to fetch information mid-reasoning.

**Skeleton**:
```
Thought: <what to do next and why>
Action: <tool_name>(<args>)
Observation: <tool output>
Thought: ...
Action: ...
...
Thought: I have enough information.
Action: finish(<final answer>)
```

**Failure modes**: tool-call hallucination, loops where the model repeats the same query, premature finish, action format drift.

---

## 6. Reflexion / Self-Refine

Shinn et al., 2023 (Reflexion); Madaan et al., 2023 (Self-Refine).

**What**: After producing an initial answer, the model critiques its own output against criteria, then revises. Repeat until satisfied or max iterations reached.

**When**: Code generation, long-form writing, plan refinement, anywhere the first draft is consistently improvable.

**Skeleton**:
```
1. Initial: produce a first answer.
2. Critique: list specific issues with the first answer against <criteria>.
3. Revise: produce a new answer addressing every issue.
4. Stop when no new issues, or after N iterations.
```

**Failure modes**: the critique step rubber-stamps the original, edits introduce new bugs, infinite loop on subjective tasks.

**Reasoning-model note**: model-dependent. The newest top-tier models self-verify; explicit verification loops there add cost without quality gains. Still effective on mid-tier models for code and math.

---

## 7. Plan-and-Solve

Wang et al., 2023.

**What**: Two phases: first produce a numbered plan, then execute each step.

**When**: Multi-step tasks where the steps are not obvious from the question, mid-complexity math word problems, structured analysis tasks.

**Skeleton**:
```
Phase 1: Devise a plan
  List the steps needed to solve this. Number them.

Phase 2: Execute
  Follow your plan step by step. For each step, show the work and the result.
```

**Failure modes**: plans that look complete but skip a required step, plans that are too granular and waste tokens, execution that drifts from the plan.

---

## 8. Least-to-Most

Zhou et al., 2022.

**What**: Decompose the problem into a chain of sub-problems ordered from easiest to hardest, then solve them in order, feeding each answer forward.

**When**: Compositional generalization, length generalization (test problems harder than training examples), tasks with clean ordering of sub-skills.

**Skeleton**:
```
Decomposition:
  Break the question into smaller sub-questions, easiest first.
  Sub-question 1: ...
  Sub-question 2: ...
  ...

Solution:
  Answer sub-question 1.
  Use it to answer sub-question 2.
  ...
  Final answer.
```

**Failure modes**: decomposition is wrong (sub-questions do not actually compose), the model conflates the decomposition and solution phases.

---

## 9. Self-Ask

Press et al., 2022.

**What**: Model asks itself follow-up questions, answers them (often via search), then composes the final answer.

**When**: Multi-hop factual QA, especially with retrieval. Closely related to ReAct but simpler in structure.

**Skeleton**:
```
Question: <original>
Are follow-up questions needed here: Yes.
Follow up: <sub-question 1>
Intermediate answer: <answer>
Follow up: <sub-question 2>
Intermediate answer: <answer>
...
So the final answer is: <answer>
```

**Failure modes**: trivial follow-ups that do not advance the answer, premature "no follow-up needed", model answers from parametric memory when retrieval was required.

---

## 10. Skeleton-of-Thought

Ning et al., 2023.

**What**: First produce a high-level skeleton (1-line bullet points for each section). Then expand each skeleton point independently, possibly in parallel.

**When**: Long-form generation where latency matters: reports, essays, structured documentation, multi-section answers.

**Skeleton**:
```
Phase 1: Skeleton
  List the section headings with a one-line description of each.

Phase 2: Expansion
  For each skeleton item, expand it into a full paragraph.
  (Each expansion can be done independently / in parallel.)
```

**Failure modes**: skeleton is too coarse and expansions drift, expansions duplicate content across sections, no global coherence pass.

---

## 11. Chain of Draft (CoD)

Xu et al., 2025 (arXiv 2502.18600).

**What**: CoT with every thinking step capped to a minimal draft, about 5 words per step, demonstrated through few-shot exemplars written in that draft style.

**When**: math, symbolic, and commonsense tasks on frontier models when output-token cost or latency matters.

**Skeleton**:
```
Think step by step, but keep a minimum draft for each thinking step, with 5 words at most.
Return the final answer after ####.

[2-4 worked examples whose reasoning is written as terse drafts]
```

**Measured**: on GPT-4o / Claude 3.5 Sonnet class models, GSM8K ~91% vs ~95% for full CoT at as little as 7.6% of the output tokens and half the latency; parity or better on symbolic and commonsense tasks. Near-parity, not exact parity, on math. Status 2026-09: v2 (2025-03), no venue, and no replication or refutation found on arXiv through 2026-09; single-source numbers.

**Failure modes**: zero-shot use (drops ~7 points and the outputs stop being concise; the draft-style exemplars are required), models under ~3B parameters (the gap vs CoT widens), problems near their intrinsic token complexity.

---

## 12. Concise CoT (CCoT)

Renze & Guven, 2024 (arXiv 2401.05618).

**What**: a plain brevity instruction ("Be concise") on top of CoT. The cheapest intervention in this file.

**When**: quick verbosity cut on strong models when a stylized pattern like Chain of Draft is not worth setting up.

**Measured**: -49% response length and ~-23% per-token cost with negligible average accuracy impact; but GPT-3.5 lost 27.7 points on math while GPT-4 held parity. Parity is model- and task-conditional.

**Failure modes**: math on weaker models; brevity phrasing is itself prompt-sensitive (wording swings results more than it looks).

---

## 13. Token-budget prompting (TALE-style)

Han et al., 2024 (arXiv 2412.18547, Findings of ACL 2025).

**What**: estimate a per-problem token budget (a cheap preliminary call, or a difficulty heuristic), then inject it into the prompt: "solve this within N tokens". On reasoning models, set the native thinking budget instead.

**When**: mixed-difficulty workloads under a cost target; the budget adapts per item where a fixed style cannot.

**Measured**: 67-69% output-token reduction at under 3-5% average accuracy loss across seven datasets; on GSM8K accuracy improved (81.4% to 84.5%) while mean output fell from 318 to 77 tokens.

**Failure modes**: token elasticity: budgets set too low make the model overshoot them, so calibrate rather than minimize; budget-estimator calls count against the savings. A budget stated in the prompt is a soft hint, not a constraint: precise length control needed control tokens injected during decoding (BudgetThinker, arXiv 2508.17196, a training method), and on API reasoning models the native control is the lever instead (`effort` on Claude, where `budget_tokens` returns a 400 error from 4.7 on; `reasoning_effort` on OpenAI; `thinking_level` on Gemini 3).

---

## 14. Sketch-of-Thought

Aytes et al., 2025 (arXiv 2503.05179, EMNLP 2025). Not to be confused with Skeleton-of-Thought (pattern 10), which shares the SoT abbreviation; use full names.

**What**: reasoning in a compressed notation instead of prose. Three paradigms: Conceptual Chaining (linked key ideas), Chunked Symbolism (equations and variables), Expert Lexicons (domain shorthand); pick one per task.

**When**: highest compression ceiling of the prompt-side patterns, when the task type is known well enough to pick the right notation.

**Measured**: up to 84% token reduction with minimal accuracy loss across 18 datasets, with gains on some math and multi-hop tasks.

**Failure modes**: notation mismatch is expensive: on medical reasoning Expert Lexicons scores 85.7% while Chunked Symbolism collapses to 73.1%. The wrong notation costs more accuracy than the tokens it saves.

---

## Cost-aware selection

What the measurements say when token cost or latency is a constraint:

- **Tokens per accuracy point.** The one cost-aware benchmark of prompting strategies (arXiv 2505.14880) measures vanilla IO and zero-shot CoT at ~5 tokens per accuracy point, Self-Consistency@10 at ~119, and the marginal price of accuracy climbing from ~65 tokens per point to ~6,700 across that range; returns diminish roughly as log(log(tokens)). Chain of Draft, Step-Back, and Plan-and-Solve have no published cost-aware ranking yet.
- **One curve, not competing tricks.** Brevity instructions, word caps, and draft styles all land on the same accuracy-vs-length curve, governed by a per-problem token-complexity threshold (arXiv 2503.01141): roughly 60% of reasoning length is typically removable at little cost, and quality drops past the threshold no matter the phrasing.
- **Prompt-only brevity holds on black-box reasoning APIs.** PREMISE (arXiv 2506.10716, 2025-06) optimized only the prompt and held accuracy on GSM8K, SVAMP and MATH500 (Claude 3.7 Sonnet 96% to 96%, Gemini 91% to 92%) while cutting reasoning tokens by up to 87.5% and dollar cost by 69% to 82%. Shorter is also more often right within a question (arXiv 2505.17813). Measurement caveat from DART (arXiv 2606.23181): under a single generation cap the always-think baseline gets truncated mid-reasoning, which overstates every router's or brevity prompt's gain; cap thinking and answer separately when you measure.
- **Where parity breaks** (replicated): small or weak models, math especially; zero-shot use of few-shot styles; compression past the task's token complexity; genuinely hard problems. A parity claim must state model class, shot regime, and task difficulty; without an eval run it is an estimate, not a result.
- **Cache changes the economics.** With prompt caching, cached prefix reads bill at 0.1x (0.025x on Claude Fable 5.1 and Mythos 5.1) and writes at 1.25x for the 5-minute TTL or 2x for the 1-hour TTL: shortening a cached system prompt saves 10% of what it appears to (2.5% on Fable 5.1), and an edit that breaks the cache re-bills the prefix at the write multiplier. Output tokens bill at full price and dominate latency. Cut reasoning verbosity first, then the uncached input; batch cached-prefix edits. Below the per-model minimum cacheable length (512 to 4,096 tokens depending on the model) nothing is cached at all.
- **The efficiency/effectiveness trade-off belongs to the user.** When both poles are viable, present variants along the frontier (max effectiveness, balanced, max efficiency) with token estimates and what each gives up; do not silently pick a pole.

---

## Combinations

These patterns compose. Common pairings worth knowing:

- **Step-Back + CoT**: recover principles first, then apply them step by step. Strong on STEM and grounded knowledge tasks.
- **Plan-and-Solve + Self-Refine**: plan, execute, critique, revise. Good for code generation and structured writing.
- **ReAct + Reflexion**: agent loop where failed trajectories produce a written lesson that conditions the next attempt.
- **Tree-of-Thought + Self-Consistency**: ToT for exploration, majority vote at the leaves.
- **Skeleton-of-Thought + Few-shot**: each skeleton-point expansion guided by an example.

Do not stack more than two patterns without a clear reason. Each adds latency, tokens, and surface area for prompt drift. On reasoning models, do not stack any of these on top of native thinking: the model already runs its own multi-step process.

## Decision guide

Run through this when designing or optimizing a prompt that needs reasoning:

0. Is the target a reasoning model (adaptive or extended thinking, o-series and GPT-5.x/6, Gemini 3, R1 class)? Default to no explicit pattern: direct instructions, precise success criteria, and the native effort setting. Two exceptions: at the lowest effort setting a brief explicit plan at the start of the answer helps; on a hybrid open reasoner under a cost target, ask the model to pick its own depth by difficulty (9B and below) or route by draft agreement (8B to 32B). Never paste worked reasoning traces as exemplars. On a small open reasoner, measure zero-shot before anything else. Continue below only if the output shows a gap that instructions alone cannot close.
1. Is token cost or latency a stated constraint? Read "Cost-aware selection" first. On capable models prefer Chain of Draft (few-shot) or token-budget prompting over full CoT, and skip Self-Consistency unless each accuracy point is worth ~100x its marginal token price.
2. Is the answer a short discrete label? Consider Self-Consistency over CoT (mind its cost note).
3. Does the right answer follow from a general principle the model knows? Apply Step-Back before CoT.
4. Does the task need external information mid-reasoning? Use ReAct or Self-Ask, not plain CoT.
5. Is the search space large with backtracking valuable? Use Tree-of-Thought.
6. Does the first draft consistently need revision? Add Reflexion / Self-Refine.
7. Is the task obviously decomposable into ordered sub-tasks? Use Plan-and-Solve; use Least-to-Most if the sub-tasks have a clean easy-to-hard ordering.
8. Is the output long and structured? Use Skeleton-of-Thought.
9. None of the above? Plain CoT or zero-shot is fine.

Avoid adding any pattern if a simpler prompt already scores 4+ on every rubric dimension. Patterns are tools to fix specific weaknesses, not defaults.
