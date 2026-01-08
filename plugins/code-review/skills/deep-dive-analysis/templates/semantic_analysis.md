# Semantic Analysis: {FILE_PATH}

> AI-powered deep analysis generated on {DATE}
> Classification: {CRITICAL|HIGH_COMPLEXITY|STANDARD|UTILITY}

---

## Executive Summary

**Purpose:** {One sentence: WHY does this code exist?}

**Responsibility:** {What does this code OWN in the system?}

**Pattern(s):** {Repository, Service, State Machine, etc.}

---

## Semantic Understanding

### What Problem Does This Solve?

{2-3 sentences describing the business/technical problem this code addresses.
Not what it DOES, but what problem would exist WITHOUT it.}

### Key Insight

{The single most important thing to understand about this code.
What would a new developer be surprised by? What's non-obvious?}

---

## Component Analysis

### Primary Abstractions

| Name | Type | Responsibility | Why It Exists |
|------|------|----------------|---------------|
| {Name} | class/function | {What it owns} | {Why not inline} |

### Behavioral Analysis

#### Core Behavior

```
TRIGGER: {What causes this code to run}
    │
    ▼
PRECONDITIONS: {What must be true before execution}
    │
    ▼
PROCESSING: {What transformations occur}
    │
    ▼
SIDE EFFECTS: {What changes in the world}
    │
    ▼
POSTCONDITIONS: {What is guaranteed after execution}
```

#### State Transitions (if applicable)

```mermaid
stateDiagram-v2
    {STATE_DIAGRAM}
```

#### Decision Points

| Condition | True Path | False Path | Impact |
|-----------|-----------|------------|--------|
| {condition} | {behavior} | {behavior} | {what_changes} |

---

## Dependency Analysis

### Why Each Dependency?

| Dependency | Category | Purpose | Replaceable? |
|------------|----------|---------|--------------|
| {import} | internal/external | {why needed} | {yes/no + why} |

### Data Flow

```
INPUTS                    PROCESSING                 OUTPUTS
────────────────────────────────────────────────────────────────
{source} ──────┐
               │
{source} ──────┼──────► {this_component} ──────► {destination}
               │              │
{source} ──────┘              │
                              ▼
                         {side_effect}
```

### Integration Points

| External System | Operation | Protocol | Failure Mode |
|-----------------|-----------|----------|--------------|
| {system} | {what_we_do} | {http/amqp/etc} | {what_if_fails} |

---

## Quality Assessment

### Strengths

- {What this code does well}
- {Good patterns applied}
- {Clear design decisions}

### Concerns

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| {issue} | HIGH/MEDIUM/LOW | line N | {fix} |

### Red Flags Found

```
{NONE | List of identified anti-patterns or risks}
```

---

## Contract Documentation

### Public Interface

#### `{function_or_method_name}()`

**Purpose:** {What this does at business level}

**Signature:**
```python
def {name}({params}) -> {return_type}:
```

**Semantics:**

| Parameter | Meaning | Valid Range | What If Invalid |
|-----------|---------|-------------|-----------------|
| {param} | {semantic_meaning} | {constraints} | {error_behavior} |

**Returns:**

| Condition | Return Value | Meaning |
|-----------|--------------|---------|
| success | {type} | {what_it_represents} |
| failure | {exception/none} | {why_and_when} |

**Side Effects:**
- {What changes beyond return value}

**Example:**
```python
# Typical usage
result = {function}({typical_args})

# Edge case
result = {function}({edge_case_args})
```

---

## Flow Tracing

### Primary Flow: {FLOW_NAME}

```
1. Entry: {where_flow_starts}
   │
   ├── Validation: {what_is_checked}
   │
   ├── Processing Step 1: {description}
   │   └── Calls: {other_components}
   │
   ├── Processing Step 2: {description}
   │   └── Side Effect: {what_changes}
   │
   └── Exit: {what_is_returned/emitted}
```

### Error Flow: {ERROR_SCENARIO}

```
1. Error Occurs: {where_and_why}
   │
   ├── Caught By: {handler}
   │
   ├── Recovery Action: {what_happens}
   │
   └── Final State: {system_state_after}
```

---

## Contextual Understanding

### Relationship to System

```
                    ┌─────────────────┐
                    │   {upstream}    │
                    └────────┬────────┘
                             │ {what_it_provides}
                             ▼
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│ {peer_left}  │◄──►│  THIS COMPONENT │◄──►│ {peer_right} │
└──────────────┘    └────────┬────────┘    └──────────────┘
                             │ {what_it_provides}
                             ▼
                    ┌─────────────────┐
                    │  {downstream}   │
                    └─────────────────┘
```

### Who Calls This?

| Caller | When | Why |
|--------|------|-----|
| {module} | {trigger} | {purpose} |

### What Does This Call?

| Callee | When | Why |
|--------|------|-----|
| {module} | {condition} | {purpose} |

---

## Testing Implications

### What Must Be Tested

| Scenario | Input | Expected Outcome | Why Critical |
|----------|-------|------------------|--------------|
| {happy_path} | {input} | {output} | {business_value} |
| {edge_case} | {input} | {output} | {risk_if_broken} |
| {error_case} | {input} | {exception} | {security/stability} |

### Test Doubles Needed

| Dependency | Mock Strategy | Behavior to Simulate |
|------------|---------------|---------------------|
| {dep} | {mock/stub/fake} | {what_to_return} |

---

## Maintenance Notes

### Change Impact Analysis

If modifying this code, also check:
- [ ] {related_file_1} - {why}
- [ ] {related_file_2} - {why}
- [ ] {test_file} - {update_fixtures}

### Known Limitations

| Limitation | Reason | Workaround |
|------------|--------|------------|
| {what} | {why_it_exists} | {how_to_handle} |

### Future Considerations

{What might need to change? What assumptions might break?}

---

## Verification Status

| Aspect | Status | Evidence |
|--------|--------|----------|
| Structure | VALIDATED | AST parsing |
| Behavior | {VERIFIED/UNVERIFIED} | {source:line or "needs review"} |
| Integration | {VERIFIED/UNVERIFIED} | {trace_id or "needs runtime check"} |

---

## Links

- **Context:** [CONTEXT.md](../../CONTEXT.md)
- **Callers:** {list_of_files_that_import_this}
- **Callees:** {list_of_files_this_imports}

---

*Analysis generated following AI_ANALYSIS_METHODOLOGY.md*
