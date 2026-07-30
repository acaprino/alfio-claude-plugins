# Reasoning Patterns for Prompt Engineering

On-demand reference for the `prompt-engineer` agent and the `/prompt-optimize` command. Read this file when a task needs reasoning structure beyond plain few-shot or basic chain-of-thought, or when the target is a reasoning model and you must decide whether any explicit pattern is warranted at all. Each pattern below states what it is, when to apply it, the prompt skeleton, and the main failure modes.

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

If two patterns fit, prefer the one that adds the least latency and token cost.

## Reasoning models change the defaults

Reasoning models (Claude with extended/adaptive thinking, OpenAI o-series and successors, DeepSeek R1 class) internalize most of the patterns in this file. Determine the model class BEFORE selecting any pattern.

On reasoning models:

- **No explicit CoT scaffolds.** OpenAI's official guidance: "think step by step" prompts are unnecessary on reasoning models and can degrade performance. Anthropic: prefer general instructions ("think thoroughly") over prescriptive step-by-step plans; manual CoT with `<thinking>`/`<answer>` tags is a fallback for when thinking is off. The Wharton "Decreasing Value of Chain of Thought" study (Meincke et al., 2025, arXiv:2506.07142) measured explicit CoT on reasoning models at marginal gains for 20-80% added time cost.
- **Minimize few-shot.** Start zero-shot; add examples only to steer format or tone.
- **Spend effort elsewhere**: precise success criteria, input curation, and thinking budget (adaptive thinking / effort settings) beat any reasoning scaffold.
- **Patterns that keep value**: Self-Consistency only where answers are cheaply verifiable (majority vote over 3-8 traces); Tree-of-Thought only for genuinely search-structured tasks (game playing, theorem proving), preferably with deterministic checkers instead of model-judged scoring at the nodes.
- **Verification prompts are model-dependent.** "Check your answer against the criteria before finishing" still helps mid-tier models on coding and math, but the newest top-tier models self-verify; carried-over verification instructions there cause over-verification (token and latency waste). Remove them when migrating upward.

On non-reasoning models the patterns below apply as documented, with one caveat: CoT gains concentrate in math, logic, and symbolic tasks, and come with increased answer variability elsewhere (Sprague et al., 2024, arXiv:2409.12183).

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

**Reasoning-model note**: redundant on reasoning models (internalized) and officially discouraged by OpenAI. On non-reasoning models, expect modest average gains with higher answer variability outside math and symbolic tasks.

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

---

## 3. Self-Consistency

Wang et al., 2022.

**What**: Sample N independent CoT chains, then take the majority vote on the final answer.

**When**: Tasks with a discrete answer space (multiple choice, integers, classification) where a single chain is unreliable.

**Skeleton**: run the same CoT prompt N times with temperature > 0; aggregate answers.

**Failure modes**: expensive (Nx cost), useless when all chains share a systematic bias, breaks when the answer is free-form text rather than a discrete label.

**Reasoning-model note**: reasoning models already sample multiple internal paths. Keep this pattern only when answers are cheaply verifiable and the vote is deterministic.

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

0. Is the target a reasoning model (extended thinking, o-series, R1 class)? Default to no explicit pattern: direct instructions, precise success criteria, and a thinking budget. Continue below only if the output shows a gap that instructions alone cannot close.
1. Is the answer a short discrete label? Consider Self-Consistency over CoT.
2. Does the right answer follow from a general principle the model knows? Apply Step-Back before CoT.
3. Does the task need external information mid-reasoning? Use ReAct or Self-Ask, not plain CoT.
4. Is the search space large with backtracking valuable? Use Tree-of-Thought.
5. Does the first draft consistently need revision? Add Reflexion / Self-Refine.
6. Is the task obviously decomposable into ordered sub-tasks? Use Plan-and-Solve; use Least-to-Most if the sub-tasks have a clean easy-to-hard ordering.
7. Is the output long and structured? Use Skeleton-of-Thought.
8. None of the above? Plain CoT or zero-shot is fine.

Avoid adding any pattern if a simpler prompt already scores 4+ on every rubric dimension. Patterns are tools to fix specific weaknesses, not defaults.
