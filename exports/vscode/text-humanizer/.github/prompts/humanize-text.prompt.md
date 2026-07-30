---
description: Remove AI writing traces from text. Detects 24 patterns (inflated symbolism, promotional language, AI vocabulary, filler phrases) and rewrites for a natural human voice with a self-evaluation pass.
agent: text-humanizer
argument-hint: <file or text> [--score]
---

# Humanize Text

Remove AI writing traces from prose, articles, blog posts, documentation, or any non-code text.

This is for text and prose. Source code readability is a different job, covered by the `clean-code` bundle of the same catalog.

## Step 1: Identify the input

From the chat input after `/humanize-text`, determine what to humanize:

- A file path: read it with `#read/readFile` and humanize its content.
- Inline text: humanize the provided text.
- Nothing: ask the user for the text with `#vscode/askQuestions`.

## Step 2: Humanize

Load the `anti-ai-writing-patterns` skill for the pattern catalog, then run the full process:

1. Draft rewrite, fixing all 24 AI patterns.
2. Self-evaluate against the question "what makes this so obviously AI generated?"
3. Final rewrite addressing the remaining tells.
4. Brief change summary.
5. Quality score, if the `--score` flag was passed.

## Step 3: Output

If the input was a file, offer to write the humanized version back, using `#vscode/askQuestions`:

1. Overwrite the original file.
2. Write to a new file, for example `<filename>.humanized.md`.
3. Just show the result without writing.

If `--score` was set, include the 5-dimension quality scoring table.
