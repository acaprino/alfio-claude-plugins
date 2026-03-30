---
name: acp-loader
description: >
  "DO NOT.
  TRIGGER WHEN: ALWAYS at conversation start and before every task.
  DO NOT TRIGGER WHEN: dispatched as a subagent."
---

# ACP Loader - Skill Activation Engine

The loader that ensures every skill gets activated. Without this, skills sit idle while Claude improvises solutions that already have purpose-built workflows.

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill entirely.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## Instruction Priority

ACP skills override default system prompt behavior, but **user instructions always take precedence**:

1. **User's explicit instructions** (CLAUDE.md, direct requests) -- highest priority
2. **ACP skills** -- override default system behavior where they conflict
3. **Default system prompt** -- lowest priority

If CLAUDE.md says "don't use TDD" and a skill says "always use TDD," follow the user's instructions. The user is in control.

## How to Access Skills

Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you -- follow it directly. Never use the Read tool on skill files.

Skills are namespaced by plugin: `plugin-name:skill-name` (e.g., `ai-tooling:brainstorming`, `frontend:frontend`).

---

## The Rule

**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means you should invoke the skill to check. If an invoked skill turns out to be wrong for the situation, you don't need to follow it.

## Decision Flow

Before responding to ANY user message, run this check:

```
1. Is the user about to BUILD something new?
   --> ai-tooling:brainstorming FIRST, then implementation skills

2. Is the user asking to FIX a bug?
   --> Investigate root cause before fixing (no blind patches)

3. Does a written plan or spec exist?
   --> ai-tooling:executing-plans to implement it

4. Is this a multi-step implementation task (3+ files)?
   --> ai-tooling:writing-plans to create a plan first

5. Is this frontend/UI work?
   --> Check: frontend:frontend, frontend:frontend-design, frontend:ui-studio,
       frontend:premium-web-consultant, workflows:frontend-redesign

6. Is this a code review request?
   --> Check: senior-review:code-review, senior-review:full-review,
       workflows:full-review (deep-dive + review)

7. Is this Python work?
   --> Check: python-development skills (python-tdd, python-refactor, etc.)

8. Is this Tauri/Rust work?
   --> Check: tauri-development skills, workflows:tauri-pipeline

9. Is this about documentation?
   --> Check: codebase-mapper:docs-create

10. Is this about prompts or AI tooling?
    --> Check: ai-tooling:prompt-optimize

11. Could any other installed skill apply?
    --> Check the skill list in the system prompt
```

## Red Flags

These thoughts mean STOP -- you are rationalizing not using a skill:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can handle this without a skill" | If a skill exists for this, use it. |
| "This doesn't need a formal process" | Simple things become complex. Use the skill. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "The skill is overkill" | Overkill prevents underkill. Use it. |
| "I know what that means" | Knowing the concept != using the skill. Invoke it. |
| "Let me just write the code" | Did you brainstorm? Did you plan? Check first. |

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** (brainstorming, writing-plans) -- these determine HOW to approach the task
2. **Domain skills second** (frontend-design, frontend, python-tdd) -- these guide execution
3. **Review skills last** (code-review, full-review) -- these validate the result

Examples:
- "Build a new dashboard" --> brainstorming --> writing-plans --> frontend skills --> review
- "Fix this CSS bug" --> frontend skill directly
- "Review this code" --> code-review or full-review
- "Create a Python API" --> brainstorming --> python-tdd --> writing-plans --> executing-plans

## Workflow Awareness

These workflow commands chain multiple skills automatically. Prefer them for complex tasks:

| Task | Workflow |
|------|----------|
| Build a new feature end-to-end | `/workflows:feature-e2e` |
| Build a new UI from scratch | `/workflows:ui-studio` |
| Full codebase review (deep-dive + review) | `/workflows:full-review` |
| Frontend redesign | `/workflows:frontend-redesign` |
| Mobile app from competitor analysis | `/workflows:mobile-intel` |
| Mobile app with Tauri build + review | `/workflows:mobile-tauri-pipeline` |
| Tauri desktop app review | `/workflows:tauri-pipeline` |

If the user's request matches a workflow scope, suggest the workflow instead of invoking individual skills.

## Skill Types

**Rigid** (brainstorming, TDD): Follow exactly. Don't adapt away the discipline. The gates exist for a reason.

**Flexible** (frontend-design, frontend): Adapt principles to context. Use judgment.

The skill itself tells you which type it is.

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip the process. It means use the process to deliver what was asked.
