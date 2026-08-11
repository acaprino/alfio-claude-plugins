---
description: Edits documentation in place for a human reader. Use when the user asks to humanize existing docs, improve scannability, or rewrite dense technical writing for progressive disclosure. Not for prose or articles (use /humanize-text in the `text-humanizer` bundle) or creating new docs (use /docs-create).
agent: doc-humanizer
argument-hint: <path-to-docs>
---

# Humanize Documentation

## CRITICAL RULES

1. **Path required.** The user must provide a path to documentation files or directory.
2. **Never invent content.** Only restructure and rephrase existing content.
3. **Confirm scope.** Show what will be rewritten before starting.
4. **Never enter plan mode.** Execute immediately.

## Step 1: Validate Target

Parse `$ARGUMENTS` for the documentation path.

If no path provided, ask:
```
Which documentation should I humanize? Provide a path to a file or directory.
```

Verify the path exists and contains documentation files (.md, .rst, .mdx, .txt).

## Step 2: Assess and Confirm Scope

Read the target documentation. Present a brief assessment:

```
Documentation to humanize: [path]

Files found: [count]
Total lines: ~[count]

Issues detected:
- [X] instances of passive voice / AI boilerplate
- [X] dense paragraphs (> 4 sentences)
- [X] monolithic diagrams
- [X] missing progressive disclosure
- [X] mixed reference / tutorial content

1. Proceed with humanization
2. Narrow scope -- I'll specify which files
3. Cancel
```

Use AskUserQuestion. Do NOT proceed until the user confirms.

## Step 3: Rewrite

Spawn the `doc-humanizer` agent:

Rewrite the following documentation to be human-readable.

### Target
[path and file list]

### Instructions

`$SKILLS` is the installed skills directory: the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists.

Read all target files and rewrite them following the codebase-mapper
writing guidelines. Humanize toward the target register (if the user
specified one) or infer it via
$SKILLS/codebase-mapper/references/audience-adaptation.md.
Fix anti-patterns (passive voice, AI boilerplate,
dense text, missing structure) while preserving all factual content.

Rewrite files in-place using `#edit/editFiles`.
Provide a change summary when done.

## Step 4: AI Trace Removal Pass

After the `doc-humanizer` restructures the content, run a second pass with the `text-humanizer` agent to catch remaining AI writing patterns in the prose.

Final polish pass on restructured documentation. Remove any remaining AI
writing patterns (AI vocabulary, filler phrases, inflated significance,
generic conclusions) while preserving the improved structure, code blocks,
diagrams, and ALL tables (do not convert tables to prose).

Do NOT add the self-evaluation pass -- just return the cleaned text.

Files to process:
[list of rewritten files]

## Step 5: Summary

Present before/after summary:

```
Humanization complete:

Files rewritten: [count]
Anti-patterns fixed:
- Passive voice: [count] instances
- AI boilerplate removed: [count] instances
- Paragraphs restructured: [count]
- Diagrams split: [count]
- Progressive disclosure added: [count] files
- AI writing traces removed: second pass applied

All factual content preserved. Review the changes with git diff.
```

## Quick Examples

```bash
/humanize-docs docs/                    # Humanize all docs in docs/
/humanize-docs README.md                # Humanize a single file
/humanize-docs docs/api/reference.md    # Humanize specific API docs
```
