---
name: writing-plans
description: >
  Use when you have a spec or requirements for a multi-step task, before touching code.
  Also use after brainstorming when the task involves 3+ files or multiple implementation
  steps. TRIGGER when: (1) user says 'write a plan', 'create a plan', 'implementation plan',
  'plan this', 'break this into tasks'; (2) the conversation has produced a design, spec,
  or set of decisions and is naturally transitioning toward implementation -- e.g., the user
  approved an approach, confirmed architecture choices, or said "let's do it" / "go ahead" /
  "proceed". A conversation that evolved through brainstorming into a confirmed design MUST
  invoke this skill before writing any code, even if the user never explicitly said "write
  a plan". DO NOT TRIGGER when: user wants to brainstorm first (use brainstorming), wants
  to execute an existing plan (use executing-plans), or is doing a simple one-file change.
---

Source: Ported from [obra/superpowers](https://github.com/obra/superpowers) -- `skills/writing-plans`

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans -- one per subsystem. Each plan should produce working, testable software on its own.

## UI/Frontend Visual Checkpoint

If the plan involves UI or frontend work (new views, layouts, components, visual redesigns), generate a **standalone HTML mockup** before writing the detailed task list:

1. Create a single `.html` file with **React** and a UI library (shadcn/ui, Radix UI, daisyUI, or other appropriate library) loaded from CDN (esm.sh, unpkg, cdn.tailwindcss.com), showing the full layout with:
   - All views/screens as navigable tabs or scrollable sections
   - Realistic placeholder content (domain-appropriate, not lorem ipsum)
   - Colors, typography, and spacing matching the design spec
   - Responsive behavior with at least one mobile breakpoint
   - Key states visible (empty, loaded, error, loading)
   - Interactive navigation and state transitions (React useState for tab switching, modals, etc.)
   - The file must open directly in a browser without npm install
2. Save it next to the plan: `docs/plans/YYYY-MM-DD-<feature-name>-mockup.html`
3. Tell the user to open it in a browser and ask for approval before proceeding
4. Only write the detailed implementation plan after the user confirms the visual direction

This avoids investing in a detailed plan for a layout the user hasn't validated visually.

**Skip this step if:** the task is backend-only, CLI-only, or the user explicitly says they don't need a mockup.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Use subagent-driven execution (if subagents available) or ai-tooling:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits

## Plan Review Loop

After completing each chunk of the plan:

1. Dispatch plan-document-reviewer subagent (see plan-document-reviewer-prompt.md) for the current chunk
   - Provide: chunk content, path to spec document
2. If Issues Found:
   - Fix the issues in the chunk
   - Re-dispatch reviewer for that chunk
   - Repeat until Approved
3. If Approved: proceed to next chunk (or execution handoff if last chunk)

**Chunk boundaries:** Use `## Chunk N: <name>` headings to delimit chunks. Each chunk should be <=1000 lines and logically self-contained.

**Review loop guidance:**
- Same agent that wrote the plan fixes it (preserves context)
- If loop exceeds 5 iterations, surface to human for guidance
- Reviewers are advisory - explain disagreements if you believe feedback is incorrect

## Execution Handoff

After saving the plan:

**"Plan complete and saved to `docs/plans/<filename>.md`. Ready to execute?"**

**Execution path depends on harness capabilities:**

**If harness has subagents (Claude Code, etc.):**
- Prefer subagent-driven execution: fresh subagent per task + review between tasks
- Do NOT offer a choice - subagent-driven is the standard approach

**If harness does NOT have subagents:**
- Execute plan in current session using ai-tooling:executing-plans
- Task-by-task execution with verification at each step
