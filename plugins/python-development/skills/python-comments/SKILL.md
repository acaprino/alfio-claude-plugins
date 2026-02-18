---
name: python-comments
description: Write and audit Python code comments using antirez's 9-type taxonomy. Two modes - write (add/improve comments in code) and audit (classify and assess existing comments with structured report). Use when users request comment improvements, docstring additions, comment quality reviews, or documentation audits. Applies systematic comment classification with Python-specific mapping (docstrings, inline comments, type hints).
---

# Python Comments

## Purpose

Two operational modes for Python code comments:

1. **Write mode** - Add missing comments, improve existing ones, fix negative-type comments
2. **Audit mode** - Classify all comments, identify gaps, produce structured quality report

Core principle: comments explain *why*, code explains *what*. Type hints explain *types*.

## When to Invoke

**Write mode triggers:**
- User requests "add comments", "document this", "improve comments"
- Code review flags missing docstrings or unclear logic
- New module/class/function lacks documentation
- Complex algorithm or business rule needs explanation

**Audit mode triggers:**
- User requests "review comments", "comment quality", "documentation audit"
- Pre-release documentation review
- Onboarding prep for new team members
- Legacy code assessment

## When NOT to Invoke

- Code is scheduled for deletion
- User wants API reference generation (use documentation tools instead)
- User wants type stub generation (use type hint tools instead)
- Trivial scripts or one-off scripts where comments add no value

## Antirez Comment Taxonomy for Python

Nine comment types from antirez's "Writing system software: code comments". See `references/taxonomy.md` for full detail.

### Positive Types (write these)

| Type | Name | Python Form | Purpose |
|------|------|-------------|---------|
| 1 | Function | Docstring | What the function/class/module does |
| 2 | Design | Docstring or `#` | Architecture rationale, API design choices |
| 3 | Why | Inline `#` | Non-obvious reasoning behind code |
| 4 | Teacher | Inline `#` | Domain knowledge, algorithm explanation |
| 5 | Checklist | Inline `#` | Steps that must not be skipped or reordered |
| 6 | Guide | `#` section headers | Navigation aids in long modules |

### Negative Types (detect and fix these)

| Type | Name | Detection | Fix |
|------|------|-----------|-----|
| 7 | Trivial | Restates the code | Delete |
| 8 | Debt | `TODO`, `FIXME`, `HACK` | Resolve or create issue |
| 9 | Backup | Commented-out code | Delete (git preserves history) |

## Python-Specific Mapping

### Docstrings vs Inline Comments

- **Docstrings** (`"""..."""`) - Types 1-2. Describe *interface* (what, args, returns, raises). Follow PEP 257.
- **Inline comments** (`#`) - Types 3-6. Describe *implementation* (why, how, context).
- **Type hints** - Reduce comment burden. Document *semantics* in docstrings, not types.

### Type Hints Reduce Comment Burden

```python
# BAD: Comment duplicates type hint
def process(data: list[dict]) -> bool:
    """Process data.

    Args:
        data: A list of dictionaries  # Redundant - type hint says this
    """

# GOOD: Docstring adds semantic meaning
def process(data: list[dict]) -> bool:
    """Process sensor readings and flag anomalies.

    Args:
        data: Sensor readings keyed by timestamp, each containing
              'value', 'unit', and optional 'calibration_offset'
    """
```

### PEP 257 Essentials

- One-line docstrings: `"""Return the user's full name."""` (imperative mood, period)
- Multi-line: summary line, blank line, elaboration
- All public modules, classes, functions, methods need docstrings
- Private methods: docstring if logic is non-obvious

## Write Mode Workflow

Execute in four phases.

### Phase 1: Scan

1. Read entire file/module being commented
2. Identify all existing comments and docstrings
3. Map code structure: modules, classes, functions, complex blocks
4. Note type hints already present (reduces docstring burden)

**Output:** Inventory of existing documentation and code structure.

### Phase 2: Classify Gaps

For each code element, determine what's missing:

1. **Module-level** - Missing module docstring? Missing guide comments for sections?
2. **Class-level** - Missing class docstring? Missing design rationale?
3. **Function-level** - Missing docstring? Missing parameter semantics? Missing why-comments on complex logic?
4. **Block-level** - Complex algorithms without teacher comments? Non-obvious conditions without why-comments? Multi-step processes without checklist comments?

Prioritize gaps by impact:
- **Critical** - Public API without docstring, complex algorithm without explanation
- **High** - Non-obvious business rule without why-comment, multi-step process without checklist
- **Medium** - Missing guide comments in long modules, missing design rationale
- **Low** - Private helpers without docstrings (skip if logic is obvious)

**Output:** Prioritized gap list with comment type needed for each.

### Phase 3: Write

Apply comments following these rules:

1. **Choose correct type** - Use taxonomy from Phase 2 classification
2. **Choose correct form** - Docstring for types 1-2, inline `#` for types 3-6
3. **Choose correct style** - Match project's existing docstring style; default to Google style. See `references/docstring-styles.md`
4. **Write concisely** - Every word must earn its place
5. **Fix negatives** - Delete trivial comments (type 7), resolve or issue-track debt (type 8), delete backup code (type 9)

Writing rules per type:
- **Type 1 (Function):** Imperative mood. Document purpose, args semantics (not types if hints exist), returns, raises, side effects. See `references/docstring-styles.md`
- **Type 2 (Design):** Explain *why this approach* over alternatives. Place at module/class level or above complex function
- **Type 3 (Why):** One line above the non-obvious code. Start with "why" reasoning, not "what" description
- **Type 4 (Teacher):** Explain domain concept or algorithm. Link to external reference if applicable
- **Type 5 (Checklist):** Number the steps. Mark order-dependent sequences. Note what breaks if skipped
- **Type 6 (Guide):** Section headers in long modules. Use `# --- Section Name ---` or `# region`/`# endregion`

**Output:** Commented code.

### Phase 4: Verify

1. **No trivial comments added** - Every comment adds information not in the code
2. **No type duplication** - Docstrings don't repeat type hints
3. **Style consistency** - All docstrings follow the same style (Google/NumPy/Sphinx)
4. **Existing comments preserved** - Don't delete valid existing comments unless explicitly negative types
5. **Code unchanged** - Only comments/docstrings modified, zero logic changes

**Output:** Final commented code passing all checks.

## Audit Mode Workflow

Execute in four phases.

### Phase 1: Collect

1. Extract all comments and docstrings from target code
2. Record location (file, line, scope)
3. Record form (docstring, inline `#`, block `#`)
4. Record associated code element (module, class, function, block)

**Output:** Comment inventory with locations.

### Phase 2: Classify

For each comment, assign:
- **Type** (1-9 from taxonomy)
- **Quality** (good / adequate / poor)
- **Accuracy** (correct / outdated / misleading)

Quality criteria per type - see `references/taxonomy.md` for detail:
- Type 1 (Function): Covers purpose, args, returns, raises? Imperative mood?
- Type 2 (Design): Explains rationale? References alternatives considered?
- Type 3 (Why): Explains reasoning, not just restates code?
- Type 4 (Teacher): Accurate domain explanation? Links to sources?
- Type 5 (Checklist): Steps numbered? Consequences of skipping noted?
- Type 6 (Guide): Consistent format? Matches actual code sections?
- Type 7 (Trivial): Delete candidate
- Type 8 (Debt): Has actionable resolution path?
- Type 9 (Backup): Delete candidate

**Output:** Classified comment inventory with quality assessments.

### Phase 3: Gap Analysis

Identify what's missing:
1. **Public API coverage** - Percentage of public functions/classes/modules with docstrings
2. **Why-comment coverage** - Complex logic blocks with non-obvious reasoning explained
3. **Design documentation** - Architecture decisions documented at module/class level
4. **Negative type count** - Number of trivial, debt, and backup comments

Severity levels:
- **Critical** - Public API without docstrings, misleading comments
- **High** - Complex logic without why-comments, outdated comments
- **Medium** - Missing design rationale, missing guide comments
- **Low** - Missing private method docstrings, minor style inconsistencies

**Output:** Gap analysis with severity ratings.

### Phase 4: Report

Generate structured audit report.

## Audit Report Format

```
## Comment Audit Report

### Summary
- **Files analyzed:** N
- **Total comments:** N (docstrings: N, inline: N)
- **Comment density:** N comments per 100 LOC
- **Type distribution:** Type 1: N, Type 2: N, ... Type 9: N
- **Quality score:** N/10

### Critical Gaps
- [ ] {file}:{line} - {element} - Missing {type} comment - {impact}

### Issues Found
#### Negative Comments (fix or remove)
- {file}:{line} - Type {N} ({name}) - "{comment text}" - Action: {delete/resolve/rewrite}

#### Outdated Comments
- {file}:{line} - "{comment text}" - Mismatch: {description}

#### Quality Issues
- {file}:{line} - Type {N} - Issue: {description}

### Coverage Metrics
| Scope | With Docstring | Without | Coverage |
|-------|---------------|---------|----------|
| Modules | N | N | N% |
| Classes | N | N | N% |
| Public functions | N | N | N% |
| Public methods | N | N | N% |

### Recommendations
1. **Priority 1:** {action} - {N elements affected}
2. **Priority 2:** {action} - {N elements affected}
3. **Priority 3:** {action} - {N elements affected}

### Comment Style
- **Detected style:** {Google/NumPy/Sphinx/mixed}
- **Consistency:** {consistent/inconsistent}
- **Recommendation:** {standardize on X style}
```

See `references/examples/audit-mode-examples.md` for complete report examples.

## Key Constraints

- **NEVER add trivial comments** - If the code says `x += 1`, do not add `# increment x`
- **NEVER add placeholder docstrings** - `"""Process data."""` on a complex function is worse than nothing
- **NEVER duplicate type hints** - If type hints exist, document semantics not types
- **NEVER change code logic** - Comments and docstrings only, zero functional changes
- **PRESERVE existing style** - Match the project's existing docstring style
- **PRESERVE valid comments** - Only modify/delete comments that are negative types (7-9) or demonstrably wrong

## Integration with Same-Package Skills

- **python-refactor** - Refactoring may require updating comments. Run write mode after refactoring to update docstrings
- **python-testing-patterns** - Test docstrings benefit from type 1 (function) comments. Audit mode can assess test documentation
- **python-performance-optimization** - Performance-critical code benefits from type 4 (teacher) comments explaining algorithm choices
- **python-packaging** - Package-level documentation (`__init__.py` docstrings) follows type 1+2 patterns
