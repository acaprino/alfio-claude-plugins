---
description: >
  Remove AI writing traces from text -- detects 24 patterns (inflated symbolism, promotional language, AI vocabulary, filler phrases, etc.) and rewrites for natural human voice with self-evaluation pass.
  TRIGGER WHEN: the user asks to humanize prose/text, remove AI-sounding copy, or rewrite articles/blog posts/documentation for natural voice.
  DO NOT TRIGGER WHEN: cleaning up source code (use /clean-code:clean-code) or translating text.
argument-hint: "<file or text> [--score]"
---

# Humanize Text

Use the `text-humanizer` agent to remove AI writing traces from prose, articles, blog posts, documentation, or any non-code text.

**This is for TEXT/PROSE. For source code readability, use `/humanize` instead.**

## Step 1: Identify Input

From `$ARGUMENTS`, determine what to humanize:
- If a file path: read and humanize the file content
- If inline text: humanize the provided text
- If no arguments: ask the user for text to humanize

## Step 2: Run Text Humanizer

```
Task:
  subagent_type: "text-humanizer"
  description: "Remove AI writing traces from text"
  prompt: |
    Humanize the following text. Remove all AI writing patterns, inject real
    personality, and produce natural human-sounding prose.

    Follow the full process:
    1. Draft rewrite (fix all 24 AI patterns)
    2. Self-evaluate: "What makes the below so obviously AI generated?"
    3. Final rewrite addressing remaining tells
    4. Brief change summary
    5. Quality score (if --score flag provided)

    Text to humanize:
    [input text]
```

## Step 3: Output

If the input was a file, offer to write the humanized version back:

```
Humanized version ready.

1. Overwrite the original file
2. Write to a new file (e.g. [filename].humanized.md)
3. Just show the result (don't write)
```

If `--score` flag is set, include the 5-dimension quality scoring table.

## When to use what

- `/humanize` -- source code readability (naming, comments, structure)
- `/humanize-text` -- prose/text AI trace removal (this command)

$ARGUMENTS
