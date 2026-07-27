# ai-tooling Prompt Engineering Refresh (2026) - Design

Date: 2026-07-27
Status: approved by user (conversation), pending spec review
Plugin: `ai-tooling` v3.2.1 -> v3.3.0

## Goal

Refresh the prompt engineering content of the `ai-tooling` plugin to the 2026 state of the art. The current corpus reflects the 2022-2024 era: the reasoning-patterns reference cites only 2022-2023 papers, and the agent has no coverage of context engineering, reasoning models with extended thinking, or prompt evals.

## Scope

In scope:

- `plugins/ai-tooling/agents/prompt-engineer.md`
- `plugins/ai-tooling/references/reasoning-patterns.md`
- `plugins/ai-tooling/commands/prompt-optimize.md` (pattern-list sync plus one structural fix)
- `.claude-plugin/marketplace.json` (version bumps)

Out of scope:

- `agent-sdk-builder` and `acp-loader` skills
- New files (new reference files were explicitly declined; new content lands as sections inside existing files)
- Restructuring of any file layout

## Process

### Phase 1: Research

Single `research:deep-researcher` spawn, angles A (Authoritative) + D (Recency) + B (Community), per the CLAUDE.md custom-plugin update protocol. Query focus:

1. What changed in prompt engineering best practices versus the 2022-2024 corpus in the files (CoT-family patterns, XML structuring, instruction positioning claims).
2. Reasoning models / extended thinking: when explicit reasoning patterns (CoT, ToT, Self-Consistency) become redundant or harmful.
3. Context engineering as the discipline's evolution; prompt evals; agentic prompting (tool descriptions, system prompts for agents).
4. Declared focus: only facts that would change existing recommendations.

### Phase 2: Diff and classify

Each research finding is classified per the update protocol:

- **Clear win**: outdated fact with a confirmed replacement -> surgical Edit
- **Subtle shift**: old approach still works -> mention both
- **No change**: research confirms current content -> no touch
- **Open question**: inconclusive -> inline comment, revisit next cycle

No finding is applied without a verified source from the research phase.

### Phase 3: Expected edits per file

**`agents/prompt-engineer.md`**: refresh `<capabilities>` and `<optimization_techniques>`; possible new entries (context engineering, reasoning-model awareness, evals) as bullets or subsections inside existing sections. Style unchanged: keyword lists, XML tags, no dash-asides.

**`references/reasoning-patterns.md`**: new section on reasoning models / extended thinking and their impact on the applicability of the 10 patterns; update the selection cheat sheet and decision guide accordingly; any post-2023 patterns confirmed relevant by research are added as numbered sections.

**`commands/prompt-optimize.md`**: sync the pattern list in the reasoning-pattern check if it changes; fix the stale `Task:`/`subagent_type` spawn block to the `Agent` tool convention.

### Phase 4: Versioning and commit

- `marketplace.json`: ai-tooling `3.2.1 -> 3.3.0` (minor: new sections), `metadata.version 12.0.0 -> 12.0.1` (patch)
- Single commit: `Refresh ai-tooling for 2026 prompt engineering practices (v3.3.0)`, then push to master

### Phase 5: Verification before push

- Grep touched files for dash-aside constructs and stale tool names
- Validate `marketplace.json` JSON syntax
- `git diff --stat` sanity check of scope

## Success criteria

- Every 2022-2024-era claim in the touched files is either confirmed, updated with a sourced replacement, or annotated as an open question
- Reasoning-model guidance exists and is wired into the cheat sheet and decision guide, not just appended
- The `/prompt-optimize` command and the agent stay consistent with each other on the pattern catalog
- No new files; no changes outside the four files listed in scope
