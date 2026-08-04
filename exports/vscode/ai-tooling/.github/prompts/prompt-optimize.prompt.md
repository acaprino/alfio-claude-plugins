---
description: Analyze, evaluate, and optimize prompts for LLMs - improve clarity, reduce token usage, add structure, and test variations. Use when the user wants to review or optimize a prompt, system message, or agent instructions for clarity/tokens/reliability. Not for generating new prompts from scratch.
agent: prompt-engineer
argument-hint: <prompt text or file path> [--model claude|gpt|gemini] [--optimize-for clarity|tokens|reliability] [--compare]
---

# Prompt Optimization

## CRITICAL RULES

1. **Read the prompt first.** If `$ARGUMENTS` is a file path, read the file. If inline text, use it directly.
2. **Never modify the user's original prompt** until they approve a variant.
3. **Show the frontier.** Efficiency vs effectiveness is the user's call, not the optimizer's: present variants along that axis with honest cost labels, and let the user pick. `--optimize-for` is the shortcut for users who already know their pole.
4. **Never enter plan mode.** Execute immediately.

`$SKILLS` is the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists.

## Step 1: Analysis and variant frontier

You are evaluating and optimizing a prompt. Use `<analysis>` tags for chain-of-thought reasoning before producing the final output.

### Input

- Original Prompt: [Insert the prompt from $ARGUMENTS]
- Optimization Target: [--optimize-for flag value, or "frontier" when absent]
- Target Model: [--model flag value, default "claude"]

### Phase 1: Analysis (inside <analysis> tags)

Think through the prompt inside <analysis> tags. Evaluate on a 1-5 scale for:
Clarity, Specificity, Structure, Token Efficiency, Robustness, Output Control.
Identify ambiguities, missing edge cases, structural weaknesses, and injection vulnerabilities.

Usage-profile check: determine how the prompt is used (one-off, repeated system prompt,
agent loop) and whether prompt caching applies. Which tokens matter follows from this:
output tokens bill at full price and dominate latency; a cached prefix bills ~0.1x on
reads, so shortening it saves ~10% of what it appears to, and cache-breaking edits
re-bill it at 1.25x.

Reasoning-pattern check: first determine the target model class. For reasoning models
(extended thinking, o-series, R1 class), default to NO explicit scaffold: direct
instructions plus precise success criteria; consult the "Reasoning models change the
defaults" section of `$SKILLS/agent-sdk-builder/references/reasoning-patterns.md` before adding
any pattern. Otherwise, decide whether the task would benefit from a structured
reasoning scaffold beyond plain instructions (CoT, Step-Back, ReAct, Tree-of-Thought,
Self-Consistency, Reflexion, Plan-and-Solve, Least-to-Most, Self-Ask, Skeleton-of-Thought).
If yes, read `$SKILLS/agent-sdk-builder/references/reasoning-patterns.md`, pick the pattern
that matches the task shape using the selection cheat sheet, and apply it in Phase 2.
For the efficiency variant, always consult that file's token-efficient patterns
(Chain of Draft, Concise CoT, token-budget prompting, Sketch-of-Thought) and its
"Cost-aware selection" section: the efficiency pole is built from those techniques,
not from bare word-deletion.
If the existing prompt already scores 4+ on every dimension, do not add a pattern just
for completeness -- record the decision in the analysis instead.

### Phase 2: Output (outside tags)

Based on your analysis, respond strictly in this format:

#### Prompt Scorecard (original)

| Dimension | Score (1-5) | Key issue |
|-----------|:---:|-------|
| Clarity | X | ... |
| Specificity | X | ... |
| Structure | X | ... |
| Token Efficiency | X | ... |
| Robustness | X | ... |
| Output Control | X | ... |

#### Variant Frontier

Produce 3 variants by default:

- **A. Max effectiveness**: prioritize quality, robustness, and output control; token cost is secondary.
- **B. Balanced**: resolve the analysis issues at neutral or lower token cost.
- **C. Max efficiency**: minimum tokens at estimated parity, built with a token-efficient technique where reasoning is involved.

Collapse to fewer variants only when they would genuinely converge (trivial or already
near-optimal prompts); say that you did and why. Each variant is a fully rewritten,
ready-to-use prompt in its own fenced block. Use XML tags if the target model is Claude
and the prompt mixes instructions, context, or examples; headings suffice for simple prompts.

#### Comparison

| Variant | Tokens (est.) | Delta vs original | Technique applied | Predicted gains | What you give up |

Token estimates: characters/4 on the prompt text, labeled "est.". If a variant also
constrains reasoning or output length, state the expected output-token effect
separately: that is where most of the real savings live.

#### Honesty note

Close with these caveats, adapted to the case:

- Predicted scores and parity are single-pass estimates by the same model that wrote
  the variants, not measurements; small formatting changes alone are known to swing
  task accuracy, so treat the deltas as hypotheses.
- To actually verify "fewer tokens, same results": run a paired eval (identical inputs
  per variant, pre-declared non-inferiority margin). The prompt evals section of your
  agent instructions covers the method; promptfoo fits in CI.
- If the prompt is a cached system prompt, repeat the cache-economics warning from
  the analysis.

## Step 2: The user picks the pole

Present the output and ask the user which variant to adopt with the `#vscode/askQuestions` tool: one option per variant, each label naming the pole and each description carrying the token estimate and the main trade-off; put your recommended variant first with "(Recommended)". Skip the question and deliver the matching pole directly when:

- `--optimize-for` was passed (clarity -> A, reliability -> A with constraints and examples emphasized, tokens -> C), or
- the user already stated their target in the request.

`--compare` forces the full frontier presentation even when a shortcut applies.

## Step 3: Deliver

Deliver the chosen variant ready to copy, with its token estimate and 1-2 test inputs the user can validate it with. Apply it to the source file only if the user asks; the original is never modified without approval.

## Quick Examples

- `/prompt-optimize "Summarize this document"` -- full frontier, user picks the pole
- `/prompt-optimize prompts/system.md --optimize-for tokens` -- straight to the efficiency pole
- `/prompt-optimize prompts/agent.md --model gpt --compare` -- optimize for GPT, always show the full frontier
