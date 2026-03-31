---
description: >
  "Validate skill and agent descriptions for activation quality -- checks directive patterns, trigger clauses, token budget, body size, and scores each component 1-5" argument-hint: "[plugin-name] [--all]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Skills Validation

Run deterministic activation-quality checks on all skill and agent descriptions.

## What this validates

Checks every skill SKILL.md and agent .md against the conventions in skills-creator:

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

### Step 4: Re-validate

Run the script again to confirm all scores improved.
