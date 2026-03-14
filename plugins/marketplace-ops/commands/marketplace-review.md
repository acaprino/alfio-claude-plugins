---
description: "AI-powered quality review of plugin descriptions, trigger keywords, agent prompts, skill instructions, and command definitions -- evaluates activation accuracy, content quality, and cross-plugin coherence"
argument-hint: "[plugin-name] [--all] [--fix]"
---

# Marketplace AI Review

Perform an AI-driven quality evaluation of plugin content across the anvil-toolset marketplace.

## What this evaluates

This review goes beyond structural validation (which `/marketplace-health` handles) and analyzes the **semantic quality** of every plugin component using AI judgment.

## Procedure

### Step 1: Load marketplace data

Read `.claude-plugin/marketplace.json` to get the full plugin registry.

### Step 2: For each plugin (or the specified one), evaluate these dimensions

#### A. Plugin Description Quality (marketplace.json)

Evaluate the `description` field:
- **Clarity**: Is it immediately clear what the plugin does?
- **Trigger coverage**: Does it mention enough trigger scenarios for Claude to auto-invoke?
- **Specificity**: Does it name concrete actions, not just abstract categories?
- **Conciseness**: Is it under 200 characters while still informative?
- **Differentiation**: Does it distinguish this plugin from similar ones?

Score: 1-5. Flag descriptions scoring below 3.

#### B. Agent Description & Prompt Quality

For each agent .md file, read the full content and evaluate:
- **Description trigger words**: Are the trigger phrases in `description` specific enough for Claude to know WHEN to use this agent? Descriptions should be slightly "pushy" -- Claude tends to under-trigger
- **Description action coverage**: Does the description cover all the agent's actual capabilities?
- **System prompt structure**: Does the body follow terse keyword-list style with clear sections?
- **System prompt completeness**: Does the prompt cover role, capabilities, conventions, output format?
- **System prompt length**: Is it appropriately sized? (simple agents 60-200 lines, complex up to 800)
- **Tool selection**: Are the tools listed appropriate and minimal for the agent's purpose? Are any critical tools missing?
- **Model choice**: Is the model appropriate for the task complexity?

Score: 1-5 per dimension. Flag any below 3.

#### C. Skill Description & Content Quality

For each SKILL.md, read the full content and evaluate:
- **Description trigger words**: Does `description` contain specific trigger phrases? It should tell Claude WHEN to activate, not just WHAT it does
- **Description pushiness**: Claude under-triggers -- is the description assertive enough? (e.g., "Use PROACTIVELY when..." or "You MUST use this before...")
- **Content conciseness**: Is SKILL.md under 500 lines? Claude already knows most things -- skills should only add context Claude lacks
- **Instruction clarity**: Are steps actionable and unambiguous?
- **Reference usage**: Does it use references/ subdirectory for detailed docs instead of bloating SKILL.md?

Score: 1-5 per dimension. Flag any below 3.

#### D. Command Quality

For each command .md, evaluate:
- **Description**: Clear, actionable, includes key trigger terms
- **Argument hint**: Present and helpful (if the command accepts arguments)
- **Procedure clarity**: Steps are unambiguous and complete

Score: 1-5. Flag below 3.

#### E. Keyword & Category Analysis

Cross-plugin analysis:
- **Keyword relevance**: Do plugin keywords actually match the plugin's capabilities?
- **Keyword completeness**: Are there obvious missing keywords that would help discoverability?
- **Category accuracy**: Does the category correctly classify the plugin?
- **Cross-plugin overlap**: Identify plugins with >50% keyword overlap that might be candidates for merging
- **Taxonomy gaps**: Are there capability areas with no plugin coverage?

### Step 3: Generate report

Output a structured report per plugin:

```
## Plugin: <name> (v<version>)

### Description Quality: X/5
- Current: "<description>"
- Issues: ...
- Suggested: "<improved description>"

### Agents (N total)
| Agent | Triggers | Prompt | Tools | Score |
|-------|----------|--------|-------|-------|
| name  | X/5      | X/5    | X/5   | X/5   |

Issues:
- agent-name: "<specific issue and fix>"

### Skills (N total)
| Skill | Triggers | Pushiness | Conciseness | Score |
|-------|----------|-----------|-------------|-------|
| name  | X/5      | X/5       | X/5         | X/5   |

Issues:
- skill-name: "<specific issue and fix>"

### Commands (N total)
| Command | Description | Args | Procedure | Score |
|---------|-------------|------|-----------|-------|
| name    | X/5         | X/5  | X/5       | X/5   |

Issues:
- command-name: "<specific issue and fix>"
```

### Step 4: Summary and recommendations

```
## Marketplace Review Summary

Overall Score: X/5
Plugins reviewed: N
Components reviewed: N agents, N skills, N commands

Top issues:
1. ...
2. ...
3. ...

Consolidation opportunities:
- Plugins X and Y share 70% keywords -- consider merging
- Skill Z could be shared between plugins A and B

Missing coverage:
- No plugin covers <area>
```

### Step 5: With --fix flag

For each issue scored below 3:
- Propose the specific edit (old text -> new text)
- Ask for user confirmation before applying
- After fixes, bump affected plugin versions and metadata.version

## Quality rubric reference

### Description trigger word examples (good vs bad)

**Bad** (too vague, Claude won't trigger):
- "Handles code review"
- "Development utilities"
- "Frontend tools"

**Good** (specific triggers, Claude knows when to activate):
- "Use when reviewing pull requests, analyzing diffs, or auditing code quality"
- "Use PROACTIVELY when writing Python -- covers testing, packaging, async patterns"
- "Expert CSS developer for active CSS work - refactoring styles, migrating SASS/preprocessors"

### Agent prompt body examples (good vs bad)

**Bad** (verbose prose):
- "You are an expert in CSS development who helps developers write better stylesheets..."

**Good** (terse keyword-list):
- "# ROLE\nCSS architecture expert\n\n# CAPABILITIES\n- Refactor SASS to native CSS\n- CSS Grid/Flexbox layouts\n- Container queries, cascade layers"
