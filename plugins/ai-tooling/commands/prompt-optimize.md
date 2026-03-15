---
description: "Analyze, evaluate, and optimize prompts for LLMs -- improve clarity, reduce token usage, add structure, and test variations"
argument-hint: "<prompt text or file path> [--model claude|gpt|gemini] [--optimize-for clarity|tokens|reliability] [--compare]"
---

# Prompt Optimization

## CRITICAL RULES

1. **Read the prompt first.** If `$ARGUMENTS` is a file path, read the file. If inline text, use it directly.
2. **Never modify the user's original prompt** until they approve the optimization.
3. **Show before/after.** Always present the original alongside the optimized version.
4. **Never enter plan mode.** Execute immediately.

## Workflow: Single-Pass Analysis & Optimization

Execute the full analysis and optimization in a single `prompt-engineer` subagent call. The agent uses `<analysis>` tags for chain-of-thought reasoning before producing the final output.

```
Task:
  subagent_type: "prompt-engineer"
  description: "Analyze and optimize the prompt in a single pass"
  prompt: |
    You are evaluating and optimizing a prompt.

    ## Input
    - Original Prompt: [Insert the prompt from $ARGUMENTS]
    - Optimization Target: [--optimize-for flag value, default "balanced"]
    - Target Model: [--model flag value, default "claude"]

    ## Phase 1: Analysis (inside <analysis> tags)
    Think through the prompt inside <analysis> tags. Evaluate on a 1-5 scale for:
    Clarity, Specificity, Structure, Token Efficiency, Robustness, Output Control.
    Identify ambiguities, missing edge cases, structural weaknesses, and injection vulnerabilities.

    ## Phase 2: Output (outside tags)
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
    [The fully rewritten, ready-to-use prompt. Use XML tags if target model is Claude.
     Enforce clear hierarchy. Resolve all issues identified in analysis.]
    ```

    ### Key Changes & Impact
    - **Word count**: [original] -> [optimized] words
    - [Bullet points explaining the 3 most impactful structural changes and why]

    If --optimize-for is:
    - "clarity": Prioritize unambiguous language, even if longer
    - "tokens": Minimize word count while preserving meaning
    - "reliability": Add constraints, examples, and output format for consistent results
```

If `--compare` flag is set, add a section with 2-3 alternative variations optimized for different goals (clarity vs tokens vs reliability) and present all for comparison.

## Quick Examples

- `/prompt-optimize "Summarize this document"` -- Analyze and improve a simple prompt
- `/prompt-optimize prompts/system.md --optimize-for tokens` -- Reduce token count of a system prompt
- `/prompt-optimize prompts/agent.md --model gpt --compare` -- Optimize for GPT with variations
