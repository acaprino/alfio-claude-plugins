---
description: Analyze, evaluate, and optimize prompts for LLMs - improve clarity, reduce token usage, add structure, and test variations. Use when the user wants to review or optimize a prompt, system message, or agent instructions for clarity/tokens/reliability. Not for the user wants the prompt-improver hook (which runs automatically) or generating new prompts from scratch.
agent: prompt-engineer
argument-hint: <prompt text or file path> [--model claude|gpt|gemini] [--optimize-for clarity|tokens|reliability] [--compare]
---

# Prompt Optimization

## CRITICAL RULES

1. **Read the prompt first.** If `$ARGUMENTS` is a file path, read the file. If inline text, use it directly.
2. **Never modify the user's original prompt** until they approve the optimization.
3. **Show before/after.** Always present the original alongside the optimized version.
4. **Never enter plan mode.** Execute immediately.

## Workflow: Single-Pass Analysis & Optimization

Execute the full analysis and optimization in a single `prompt-engineer` subagent call. The agent uses `<analysis>` tags for chain-of-thought reasoning before producing the final output.

You are evaluating and optimizing a prompt.

### Input
- Original Prompt: [Insert the prompt from $ARGUMENTS]
- Optimization Target: [--optimize-for flag value, default "balanced"]
- Target Model: [--model flag value, default "claude"]

### Phase 1: Analysis (inside <analysis> tags)
Think through the prompt inside <analysis> tags. Evaluate on a 1-5 scale for:
Clarity, Specificity, Structure, Token Efficiency, Robustness, Output Control.
Identify ambiguities, missing edge cases, structural weaknesses, and injection vulnerabilities.

Reasoning-pattern check: first determine the target model class. For reasoning models
(extended thinking, o-series, R1 class), default to NO explicit scaffold: direct
instructions plus precise success criteria; consult the "Reasoning models change the
defaults" section of `$SKILLS/agent-sdk-builder/references/reasoning-patterns.md` before adding
any pattern. Otherwise, decide whether the task would benefit from a structured
reasoning scaffold beyond plain instructions (CoT, Step-Back, ReAct, Tree-of-Thought,
Self-Consistency, Reflexion, Plan-and-Solve, Least-to-Most, Self-Ask, Skeleton-of-Thought).
If yes, read `$SKILLS/agent-sdk-builder/references/reasoning-patterns.md`, pick the pattern
that matches the task shape using the selection cheat sheet, and apply it in Phase 2.
If the existing prompt already scores 4+ on every dimension, do not add a pattern just
for completeness -- record the decision in the analysis instead.

### Phase 2: Output (outside tags)
Based on your analysis, respond strictly in this format:

### Prompt Scorecard
| Dimension | Before (1-5) | Expected After (1-5) | Notes |
|-----------|:---:|:---:|-------|
| Clarity | X | Y | [key issue] |
| Specificity | X | Y | [key issue] |
| Structure | X | Y | [key issue] |
| Token Efficiency | X | Y | [key issue] |
| Robustness | X | Y | [key issue] |
| Output Control | X | Y | [key issue] |

### Optimized Prompt
```
[The fully rewritten, ready-to-use prompt. Use XML tags if target model is Claude and
 the prompt mixes instructions, context, or examples; headings suffice for simple prompts.
 Enforce clear hierarchy. Resolve all issues identified in analysis.]
```

### Key Changes & Impact
- **Word count**: [original] -> [optimized] words
- **Reasoning pattern applied**: [pattern name from reasoning-patterns.md, or "none -- not warranted"]
- [Bullet points explaining the 3 most impactful structural changes and why]

If --optimize-for is:
- "clarity": Prioritize unambiguous language, even if longer
- "tokens": Minimize word count while preserving meaning
- "reliability": Add constraints, examples, and output format for consistent results

If `--compare` flag is set, add a section with 2-3 alternative variations optimized for different goals (clarity vs tokens vs reliability) and present all for comparison.

## Quick Examples

- `/prompt-optimize "Summarize this document"` -- Analyze and improve a simple prompt
- `/prompt-optimize prompts/system.md --optimize-for tokens` -- Reduce token count of a system prompt
- `/prompt-optimize prompts/agent.md --model gpt --compare` -- Optimize for GPT with variations
