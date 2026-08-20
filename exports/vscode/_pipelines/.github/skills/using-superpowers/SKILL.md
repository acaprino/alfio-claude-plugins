---
name: using-superpowers
description: >
  Use when starting any development conversation. Establishes how to find and use the superpowers skills, requiring skill invocation before any response, including clarifying questions.
user-invocable: true
license: MIT
metadata:
  author: Jesse Vincent
  source: obra/superpowers
  upstream-version: "6.3.0"
  snapshot: "2026-08-20"
---

<!--
Portions of this file are derived from obra/superpowers
(https://github.com/obra/superpowers), MIT License.
Snapshot 2026-08-20, upstream version 6.3.0.
-->

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before writing an implementation plan:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → brainstorming first, then implementation skills.
- "Fix this bug" → systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## How skills work here

VS Code loads a skill automatically when your request matches its description, and the user can force one by typing `/skill-name` in the Chat view. Skills are read from `.github/skills/`, `.claude/skills/`, and `.agents/skills/` in the workspace, plus `~/.copilot/skills/` for personal ones. They activate in Agent mode only.

Workflows that delegate need the `superpowers` agent rather than the default chat agent. VS Code gates `#agent/runSubagent` behind an `agents:` allowlist, and only that agent declares the sp-* subagents. If a skill tells you to dispatch and you are running as the default agent, say so and let your human partner switch. Doing the subagent's work inline instead is the failure this note exists to prevent.

## User Instructions

User instructions (`.github/copilot-instructions.md`, `AGENTS.md`, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
