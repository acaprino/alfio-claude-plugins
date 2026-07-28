---
name: acp-loader
description: >
  Skill activation engine that ensures relevant marketplace skills are invoked for every task.
  TRIGGER WHEN: ALWAYS at conversation start and before every task.
  DO NOT TRIGGER WHEN: dispatched as a subagent.
---

# Skill Activation Engine

(Plugin id `acp-loader` kept for install compatibility.)

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

Marketplace skills override default system prompt behavior, but **user instructions always take precedence**:

1. **User's explicit instructions** (CLAUDE.md, direct requests) -- highest priority
2. **Marketplace skills** -- override default system behavior where they conflict
3. **Default system prompt** -- lowest priority

If CLAUDE.md says "don't use TDD" and a skill says "always use TDD," follow the user's instructions. The user is in control.

## How to Access Skills

Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you -- follow it directly. Never use the Read tool on skill files.

Skills are namespaced by plugin: `plugin-name:skill-name` (e.g., `ai-tooling:agent-sdk-builder`, `python-development:python-tdd`).

---

## The Rule

**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means you should invoke the skill to check. If an invoked skill turns out to be wrong for the situation, you don't need to follow it.

## Decision Flow

Before responding to ANY user message, run this check:

```
1. Is the user about to BUILD something new?
   --> Settle requirements and design BEFORE code, then apply the domain skills below

2. Is the user asking to FIX a bug?
   --> Investigate root cause before fixing (no blind patches)

3. Is this React or PWA work?
   --> Check: react-development:react-best-practices, pwa-expert:pwa-development

4. Is this a code review request?
   --> Check: senior-review:code-review, senior-review:team-review

5. Is this Python work?
   --> Check: python-development skills (python-tdd, python-refactor, etc.)

6. Is this Tauri/Rust work?
   --> Check: tauri-development skills

7. Is this about documentation?
   --> Check: codebase-mapper:docs-create

8. Is this about prompts or AI tooling?
   --> Check: ai-tooling:prompt-optimize

9. Could any other installed skill apply?
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
| "Let me just write the code" | Did you settle the requirements? Did you plan? Check first. |

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** -- design and planning skills determine HOW to approach the task. This marketplace no longer ships them: [obra/superpowers](https://github.com/obra/superpowers) is a declared hard dependency of `ai-tooling`, so load its `brainstorming`, `writing-plans`, and `executing-plans` skills for that slot. If they are unavailable, tell the user to install superpowers (`claude plugin install superpowers@claude-plugins-official`) before proceeding.
2. **Domain skills second** (react-best-practices, pwa-development, python-tdd) -- these guide execution
3. **Review skills last** (code-review, team-review) -- these validate the result

Examples:
- "Build a new dashboard" --> design and plan --> react-best-practices --> review
- "Fix a slow React re-render" --> react-development:react-best-practices directly
- "Review this code" --> code-review or team-review
- "Create a Python API" --> design and plan --> python-tdd --> review

## Workflow Awareness

These commands orchestrate multi-agent teams for complex tasks. Prefer them over invoking individual skills:

| Task | Command |
|------|---------|
| Build a new feature end-to-end | `/agent-teams:team-feature` (requires the upstream wshobson/agents agent-teams plugin) |
| Full codebase review (deep-dive + review) | `/senior-review:team-review` |
| Debug with competing hypotheses | `/agent-teams:team-debug` (requires the upstream wshobson/agents agent-teams plugin) |
| Deep multi-source research | `/research:team-research` |
| Map an unfamiliar codebase | `/codebase-mapper:team-codebase-map` |
| X-ray a monorepo or partitioned codebase | `/codebase-xray:team-analyze` |

If the user's request matches a team scope, suggest the team command instead of invoking individual skills.

## Skill Types

**Rigid** (TDD, review checklists): Follow exactly. Don't adapt away the discipline. The gates exist for a reason.

**Flexible** (react-best-practices, pwa-development): Adapt principles to context. Use judgment.

The skill itself tells you which type it is.

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip the process. It means use the process to deliver what was asked.
