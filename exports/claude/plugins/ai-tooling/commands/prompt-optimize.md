---
description: >
  Present the efficiency-versus-effectiveness frontier as labelled variants and let the user pick.
  TRIGGER WHEN: the user wants to review or optimize a prompt, system message, or agent instructions for clarity/tokens/reliability.
argument-hint: "<prompt text or file path> [--model claude|gpt|gemini|<open-weight model, e.g. gemma-3-12b>] [--optimize-for clarity|tokens|reliability] [--compare]"
---

# Prompt Optimization

## CRITICAL RULES

1. **Read the prompt first.** If `$ARGUMENTS` is a file path, read the file. If inline text, use it directly.
2. **Never modify the user's original prompt** until they approve a variant.
3. **Show the frontier.** Efficiency vs effectiveness is the user's call, not the optimizer's: present variants along that axis with honest cost labels, and let the user pick. `--optimize-for` is the shortcut for users who already know their pole.
4. **Name the model class.** `--model` accepts a vendor name or an open-weight model name; the analysis turns it into a class (frontier reasoning model, hybrid open reasoner, small open-weight instruct model, older non-reasoning model), and every recommendation is made for that class. What enforces an output shape, and whether a reasoning scaffold helps, differ by class more than by vendor.
5. **Never enter plan mode.** Execute immediately.

## Step 1: Analysis and variant frontier (single agent pass)

Spawn the `prompt-engineer` agent via the `Agent` tool, description "Analyze the prompt and generate the variant frontier", with the brief below as its prompt. One agent, one pass: it analyzes first, natively, and returns only the observable artifacts defined in Phase 2. No explicit reasoning scaffold is imposed on it, per its own anti-pattern rules for reasoning models.

```
You are evaluating and optimizing a prompt.

## Input
- Original Prompt: [Insert the prompt from $ARGUMENTS]
- Optimization Target: [--optimize-for flag value, or "frontier" when absent]
- Target Model: [--model flag value, default "claude"]

## Phase 1: Analysis (private)
Analyze the prompt thoroughly before writing any output. Extract its behavioral contract
first, then classify the archetype and score on a 1-5 scale only the rubric dimensions that
archetype wants, marking the rest N/A. Identify ambiguities, missing edge cases, structural
weaknesses, and injection vulnerabilities.
Do not include this working in the response: Phase 2 defines the only output you produce.

Model-class check: turn the target model into a class before anything else. Frontier
reasoning model (Claude 4.6 and later, GPT-5.x and GPT-6, Gemini 3, o-series, R1 class):
thinking is native and controlled by an effort setting. Hybrid open reasoner (Qwen3, Gemma 4,
DeepSeek V3.x, gpt-oss): thinking is switched by mode tokens. Small open-weight instruct model
(Gemma 3, Llama 3.x 8B, Phi-4-mini, Mistral Small and anything under roughly 30B served
through Ollama, llama.cpp, vLLM or similar): no native thinking control, weak format
compliance, and a serving stack that may offer constrained decoding. Older non-reasoning
model: the classic patterns apply. Read the model-fit rows of
`${CLAUDE_PLUGIN_ROOT}/skills/prompt-engineering/SKILL.md` for the class before scoring model
fit, and `${CLAUDE_PLUGIN_ROOT}/skills/prompt-engineering/references/model-guidance.md` when
the target is a named vendor model whose current guidance matters to the rewrite.

Usage-profile check: determine how the prompt is used (one-off, repeated system prompt,
agent loop) and whether prompt caching applies. Which tokens matter follows from this:
output tokens bill at full price and dominate latency; a cached prefix bills 0.1x on reads
(0.025x on Claude Fable 5.1 and Mythos 5.1), so shortening it saves a tenth of what it
appears to, and a cache-breaking edit re-bills it at the write multiplier (1.25x for the
5-minute TTL, 2x for the 1-hour TTL).

Reasoning-pattern check: for a frontier reasoning model, default to NO explicit scaffold:
direct instructions plus precise success criteria, with the effort setting as the lever;
consult the "Reasoning models change the defaults" section of
`${CLAUDE_PLUGIN_ROOT}/skills/prompt-engineering/references/reasoning-patterns.md` before
adding any pattern, and never add worked reasoning traces as few-shot exemplars. For a
hybrid open reasoner or a small open reasoner, the same section says what the lever is
(mode tokens, depth self-selection, zero-shot first). Otherwise, decide whether the task
would benefit from a structured reasoning scaffold beyond plain instructions (CoT,
Step-Back, ReAct, Tree-of-Thought, Self-Consistency, Reflexion, Plan-and-Solve,
Least-to-Most, Self-Ask, Skeleton-of-Thought). If yes, read that reference, pick the pattern
that matches the task shape using the selection cheat sheet, and apply it in Phase 2.
For the efficiency variant, always consult that file's token-efficient patterns
(Chain of Draft, Concise CoT, token-budget prompting, Sketch-of-Thought) and its
"Cost-aware selection" section: the efficiency pole is built from those techniques,
not from bare word-deletion.
If the existing prompt already scores 4+ on every dimension, do not add a pattern just
for completeness: record the decision in the analysis instead.

Output-shape check: if anything parses the output (JSON, a schema, an enum, a fixed
template), read `${CLAUDE_PLUGIN_ROOT}/skills/prompt-engineering/references/structured-output.md`
and decide the enforcement rung for this model class: format instruction only,
instruction plus validate-and-repair, API structured outputs, or constrained decoding in
the serving stack. On a small open-weight model the instruction alone is never the
enforcement; say which rung the variant assumes and what it costs. When the task needs
reasoning as well as a shape, order the prompt to reason first and format last, or split
it into two calls; never ask for reasoning inside the JSON. Where the target is a Claude
4.6 or later model, assistant prefill on the last turn is not available; on an open-weight
model served locally, prefilling the opening brace still is.

Task-family check: if the archetype is extraction or classification (NER, relations,
events, fields from documents, labels from a fixed set), read
`${CLAUDE_PLUGIN_ROOT}/skills/prompt-engineering/references/extraction-prompting.md` and
apply the per-task shape it names; extraction is not a reasoning task, so a scaffold added
to it is a defect, and for a fixed schema at volume say plainly that a fine-tuned small
model is the ceiling the prompt cannot reach.

## Phase 2: Output
Based on your analysis, respond strictly in this format:

### Diagnostic Scorecard (original, predicted)
State the archetype and the model class in one line each, then one row per applicable
dimension. Include the conditional dimensions (output determinism, tool-use correctness,
trust boundaries, evalability, creative latitude) only when this archetype wants them, and
list the ones you marked N/A with a short reason underneath.

| Dimension | Score (1-5) | Key issue |
|-----------|:---:|-------|
| Intent alignment | X | ... |
| Instruction clarity | X | ... |
| Constraint correctness | X | ... |
| Model fit | X | ... |
| Context efficiency | X | ... |
| Robustness | X | ... |

### Variant Frontier
Produce 3 variants by default:
- **A. Max effectiveness**: prioritize quality, robustness, and output control; token cost is secondary.
- **B. Balanced**: resolve the analysis issues at neutral or lower token cost.
- **C. Max efficiency**: minimum tokens at estimated parity, built with a token-efficient
  technique where reasoning is involved.

Collapse to fewer variants only when they would genuinely converge (trivial or already
near-optimal prompts); say that you did and why. Each variant is a fully rewritten,
ready-to-use prompt in its own fenced block. Use XML tags if the target model is Claude
and the prompt mixes instructions, context, or examples; headings suffice for simple prompts.
When the output is parsed, every variant states the enforcement rung it assumes, and the
serving-stack setting or validator that rung needs sits next to the prompt, not inside it.

### Comparison
| Variant | Tokens (est.) | Delta vs original | Technique applied | Enforcement (if parsed) | Predicted effect (unmeasured) | What you give up |

Token estimates: characters/4 on the prompt text, labeled "est.". If a variant also
constrains reasoning or output length, state the expected output-token effect
separately: that is where most of the real savings live.

### Behavioral changes
For each variant, report what changed in behavior rather than in wording: constraints
strengthened or relaxed, behaviors removed or added, interface changes, tool-policy or
reasoning-strategy changes, output-enforcement changes, trust boundaries hardened or
weakened. Print only the lines that are true. If a variant changes nothing behavioral, say
so in one line. Lead with any relaxation or removal instead of burying it under the token
saving.

### Honesty note
Close with these caveats, adapted to the case:
- Label every quality claim predicted, measured, or verified. A score this pass assigned is
  predicted by definition, including the scorecard above.
- Predicted scores and parity are single-pass estimates by the same model that wrote
  the variants, not measurements; small formatting changes alone are known to swing
  task accuracy, so treat the deltas as hypotheses.
- To actually verify "fewer tokens, same results": run a paired eval (identical inputs
  per variant, pre-declared non-inferiority margin). The prompt-engineer prompt-evals
  guidance covers the method; promptfoo fits in CI.
- If the output is parsed, say that schema compliance on this model class is predicted
  until measured on a hundred real inputs, and name the parse-failure rate as the first
  number to collect.
- If the prompt is a cached system prompt, repeat the cache-economics warning from
  the analysis.
```

## Step 2: The user picks the pole

After the agent returns, present its output and ask the user which variant to adopt, via AskUserQuestion: one option per variant, each label naming the pole and each description carrying the token estimate and the main trade-off; put your recommended variant first with "(Recommended)". Skip the question and deliver the matching pole directly when:

- `--optimize-for` was passed (clarity -> A, reliability -> A with constraints and examples emphasized, tokens -> C), or
- the user already stated their target in the request.

`--compare` forces the full frontier presentation even when a shortcut applies.

## Step 3: Deliver

Deliver the chosen variant ready to copy, with its token estimate, the enforcement rung and its setting when the output is parsed, and 1-2 test inputs the user can validate it with. Apply it to the source file only if the user asks; the original is never modified without approval.

## Quick Examples

- `/prompt-optimize "Summarize this document"`: full frontier, user picks the pole
- `/prompt-optimize prompts/system.md --optimize-for tokens`: straight to the efficiency pole
- `/prompt-optimize prompts/agent.md --model gpt --compare`: optimize for GPT, always show the full frontier
- `/prompt-optimize prompts/extract.md --model gemma-3-12b`: small open-weight target: the variants name their enforcement rung and the extraction shape they use
