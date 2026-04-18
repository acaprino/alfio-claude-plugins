---
description: >
  Validate skill and agent quality -- deterministic checks (activation patterns, token budget, body size, examples, frontmatter) plus AI body review (structure, clarity, redundancy, tool restrictions, isolation).
  TRIGGER WHEN: the user asks to validate skill/agent quality, enforce trigger patterns, check token budgets, or run pre-commit marketplace checks.
  DO NOT TRIGGER WHEN: checking structural JSON references only (use /marketplace-ops:marketplace-health) or doing an AI-only content review (use /marketplace-ops:marketplace-review).
argument-hint: "[plugin-name] [--all] [--skip-ai]"
---

# Skills Validation

Deterministic activation-quality checks plus AI-powered body review for all skills and agents.

## What this validates

### Deterministic checks (script)

1. **Directive voice** -- description uses ALWAYS invoke, MUST use, TRIGGER WHEN, or use PROACTIVELY
2. **TRIGGER WHEN clause** -- explicit activation boundary present
3. **DO NOT TRIGGER WHEN clause** -- explicit exclusion boundary present
4. **Negative constraint** -- "Do not X directly" prevents Claude from bypassing (skills only)
5. **Passive pattern detection** -- flags "Helps with", "Can be used for", "Use when" and similar low-activation wording
6. **Description length** -- hard limit 1024 chars, recommended under 300
7. **Token budget** -- total description chars across all components vs 15,000 char budget
8. **SKILL.md body size** -- warn over 300 lines, flag over 500 lines, suggest references/ split
9. **Agent body size** -- flag over 800 lines
10. **Em dash detection** -- flags the em dash character anywhere
11. **Token estimate** -- SKILL.md body chars/4, target under 5,000 tokens
12. **Example tags** -- detects `<example>` tags, recommends 3-5
13. **context: fork** -- reports if skill uses isolated subagent context
14. **disable-model-invocation** -- reports if auto-triggering is disabled
15. **allowed-tools in agents** -- flags agents with unrestricted tool access
16. **!command preprocessor** -- detects shell command injection in skill body

### AI review dimensions (Step 5)

- **Structure** -- section organization, logical flow, no wall-of-text
- **Clarity** -- actionable instructions, no vague directives, teaches only what Claude lacks
- **Redundancy** -- no repetition, no filler, every sentence adds unique value
- **Progressive disclosure** -- large content split into references/ appropriately
- **Tool restrictions** -- agents have appropriate tools for their role
- **Isolation needs** -- destructive skills should use context: fork

## Procedure

### Step 1: Run the validation script

```bash
# Validate all plugins
python plugins/marketplace-ops/skills/skills-creator/scripts/validate_skills.py --all

# Validate a specific plugin
python plugins/marketplace-ops/skills/skills-creator/scripts/validate_skills.py <plugin-name>
```

### Step 2: Review the report

The script outputs:
- Token budget usage (current chars / 15,000 budget)
- Estimated total body tokens across all skills
- Per-component issues grouped by plugin
- Activation score summary table (1-5 per component)
- Components scoring below 3/5 flagged for attention

### Step 3: Fix low-scoring descriptions

For each component scoring below 3/5, rewrite the description following the high-activation template:

```yaml
description: >
  "<Domain summary>" argument-hint: "<usage hint>".
  TRIGGER WHEN: <specific triggers>.
  DO NOT TRIGGER WHEN: <exclusions>.
```

### Step 4: Re-validate deterministic checks

Run the script again to confirm all scores improved.

### Step 5: AI body quality review

Skip this step if the user passed `--skip-ai`.

Read the SKILL.md body and agent body of each component that scored below 4/5 OR was flagged for token/line/body issues. For each, evaluate these dimensions:

#### 5A. Structure (score 1-5)

- **5/5**: Clear headers (## Purpose, ## Procedure, ## Constraints, ## Output), logical flow
- **3/5**: Some structure but sections bleed into each other or headers are vague
- **1/5**: Wall-of-text, no headers, instructions mixed with examples

#### 5B. Clarity (score 1-5)

- **5/5**: Every instruction is specific, imperative, teaches only what Claude doesn't already know
- **3/5**: Mostly clear but has vague directives ("handle appropriately", "use best judgment")
- **1/5**: Instructions repeat common knowledge, contradict each other, or are ambiguous

#### 5C. Redundancy (score 1-5)

- **5/5**: Every sentence adds unique value, no repetition
- **3/5**: Some duplication between description and body, or preambles before actionable content
- **1/5**: Same instruction stated multiple ways, "You are an expert in..." throat-clearing, verbose filler

#### 5D. Progressive disclosure (score 1-5)

- Skip if body <150 lines
- **5/5**: Body under 300 lines OR large body with well-used references/ directory
- **3/5**: Body >300 lines with references/ but wrong content split
- **1/5**: Body >300 lines with no references/ directory

#### 5E. Tool restrictions (score 1-5, agents only)

- **5/5**: Tools list matches agent's actual needs precisely
- **3/5**: Slightly over-permissive but not dangerous
- **1/5**: All tools allowed when agent only needs Read/Grep, or missing tools it clearly needs

#### 5F. Isolation needs (score 1-5)

- **5/5**: Pure knowledge/conventions skill (no isolation needed) OR destructive skill with context: fork
- **3/5**: Runs shell commands but low risk
- **1/5**: Performs destructive operations, generates huge output, or calls external APIs without context: fork

#### Output format

For each reviewed component:

```
### <plugin>/<component> -- Body Quality

| Dimension   | Score | Issue |
|-------------|-------|-------|
| Structure   | X/5   | ...   |
| Clarity     | X/5   | ...   |
| Redundancy  | X/5   | ...   |
| Disclosure  | X/5   | ...   |
| Tool restr. | X/5   | ...   |
| Isolation   | X/5   | ...   |

**Top fix:** <single most impactful improvement>
```

### Step 6: Final re-validate

Run the script one more time to confirm all deterministic fixes landed cleanly.
