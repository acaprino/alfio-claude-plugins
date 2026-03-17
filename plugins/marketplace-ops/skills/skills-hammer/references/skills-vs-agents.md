# Skills vs Agents Decision Framework

## Core Concepts

**Skills = "La ricetta" (the recipe)** -- knowledge that shapes what the agent knows
- SKILL.md + references/ directories loaded into the active agent's context
- Composable: Claude auto-selects the right skill for the task
- Teach expertise, conventions, patterns, domain knowledge
- Do NOT change who is doing the work or what tools are available

**Agents = "Il collega specializzato" (the specialist colleague)** -- isolated worker with own context
- Agent .md files with frontmatter (name, description, model, tools, color) + system prompt
- Own context window, tool permissions, execution isolation
- Return results to parent; protect main context from noise
- Change WHO is doing the work and what they can access

## Decision Table

| Signal | Use Skill | Use Agent |
|--------|-----------|-----------|
| Adds domain knowledge / conventions | Yes | No |
| Needs tool permission isolation | No | Yes |
| Should be available to ANY agent | Yes | No |
| Runs independently, returns results | No | Yes |
| Multiple alternatives for same domain | Separate skills | No |
| Protects main context from large output | No | Yes |
| Reusable recipes / checklists | Yes | No |
| Parallel execution needed | No | Yes |
| Builds something new from scratch | No | Yes |
| Reference docs / API guides | Yes (references/) | No |

## Rule of Thumb

Start with a composable Skill. Escalate to an Agent when you need:
1. **Isolation** -- own context window to avoid polluting the parent
2. **Tool restrictions** -- specific tool subset (e.g., read-only agent)
3. **Parallel work** -- independent tasks that run concurrently
4. **Specialist persona** -- distinct role with its own system prompt

If none of these apply, a skill is the right choice.

## Patterns from Real Restructures

### tauri-development (3 skills -> 1 skill + 3 agents)
- **Before:** 3 separate skills (tauri2-desktop, tauri2-mobile, rust-development) each trying to be both knowledge AND worker
- **After:** 1 unified skill (tauri2-mobile - knowledge/recipes) + 3 agents (rust-engineer, tauri-optimizer, tauri2-mobile - specialist workers)
- **Why:** The skills were being invoked as isolated workers needing specific tools. Skills don't have tool restrictions or context isolation -- agents do.

### frontend (4 agents -> 2 agents + skill restructure)
- **Before:** 4 agents doing overlapping work, CSS knowledge buried in an agent prompt
- **After:** 2 focused agents (ui-ux-designer, ui-layout-designer) + component library skills as separate alternatives (shadcn-ui, daisyui, radix-ui) + css-master skill for CSS knowledge
- **Why:** CSS knowledge is recipes/conventions (skill territory). Component libraries are alternative knowledge bases (separate skills, not merged). Layout and UX design need isolation and specialist personas (agents).

## Anti-patterns

| Anti-pattern | Why it's wrong | Fix |
|--------------|----------------|-----|
| Merging alternative libraries into one skill | Bloats context, forces irrelevant knowledge | Separate skills per library (shadcn-ui, daisyui, radix-ui) |
| Splitting layers of same domain into separate skills | Fragments knowledge that belongs together | One unified skill with references/ for depth |
| Skill that needs specific tool permissions | Skills inherit parent's tools, can't restrict | Make it an agent with explicit `tools` field |
| Agent that's just a knowledge dump with no isolation need | Wastes a context window, adds latency | Convert to a skill |
| One mega-agent covering an entire domain | Too broad, poor at any specific task | Split into focused agents + shared skill for knowledge |

## Combination Pattern

The most common healthy architecture is: **1 skill (knowledge) + N agents (specialists)**

```
plugins/<domain>/
  skills/
    <domain>/          # unified knowledge base
      SKILL.md         # recipes, conventions, patterns
      references/      # deep reference material
    <alt-1>/           # alternative library/framework skill
    <alt-2>/           # another alternative
  agents/
    <specialist-1>.md  # focused worker agent
    <specialist-2>.md  # another focused worker
```

The skill teaches; the agents do.
