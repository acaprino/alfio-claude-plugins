# Refactoring Analysis

**File:** `path/to/file.ext`
**Date:** YYYY-MM-DD
**Analyst:** [Your Name/Tool]

---

## Executive Summary

[Brief 2-3 sentence overview of the code quality and recommended refactoring approach]

---

## Current State Metrics

### Complexity Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg Cyclomatic Complexity | X.X | <10 | ⚠/✓ |
| Max Cyclomatic Complexity | XX | <15 | ⚠/✓ |
| Avg Function Length | XX lines | <30 | ⚠/✓ |
| Max Function Length | XX lines | <50 | ⚠/✓ |
| Avg Nesting Depth | X.X | ≤3 | ⚠/✓ |
| Max Nesting Depth | X | ≤3 | ⚠/✓ |

### Documentation Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Module Docstring | Yes/No | Yes | ⚠/✓ |
| Docstring Coverage | XX% | >80% | ⚠/✓ |
| Type Hint Coverage | XX% | >90% | ⚠/✓ |
| Public Functions Documented | X/Y | Y/Y | ⚠/✓ |

---

## Identified Issues

### High Priority

1. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name from anti-patterns.md]
   - **Impact:** [Readability/Maintainability/Performance]
   - **Description:** [What makes this problematic]
   - **Recommended Fix:** [Pattern from patterns.md]

2. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name]
   - **Impact:** [Impact type]
   - **Description:** [Details]
   - **Recommended Fix:** [Pattern]

### Medium Priority

3. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name]
   - **Impact:** [Impact type]
   - **Description:** [Details]
   - **Recommended Fix:** [Pattern]

### Low Priority

4. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name]
   - **Impact:** [Impact type]
   - **Description:** [Details]
   - **Recommended Fix:** [Pattern]

---

## Risk Assessment

### Refactoring Complexity: [Low/Medium/High]

**Factors:**
- **Test Coverage:** [Percentage] - [Good/Poor]
- **Dependencies:** [Number] external dependencies affected
- **Public API Changes:** [None/Minor/Major]
- **Business Logic Complexity:** [Low/Medium/High]

### Risk Level by Issue

| Issue | Current Risk | Refactoring Risk | Net Risk |
|-------|--------------|------------------|----------|
| Issue 1 | High | Low | Worth it |
| Issue 2 | Medium | Medium | Evaluate |
| Issue 3 | Low | High | Skip |

---

## Recommended Refactoring Plan

### Phase 1: Safe Changes (Low Risk)
**Estimated Time:** [Duration]

1. **Rename variables and functions** for clarity
   - Lines: XXX, YYY, ZZZ
   - Risk: Very Low
   - Impact: Readability improved

2. **Extract magic numbers to constants**
   - Lines: XXX, YYY
   - Risk: Very Low
   - Impact: Maintainability improved

3. **Add/improve documentation**
   - All public functions
   - Risk: None
   - Impact: Documentation coverage to >80%

### Phase 2: Structural Changes (Medium Risk)
**Estimated Time:** [Duration]

4. **Apply guard clauses** to reduce nesting
   - Function: `function_name()` (Line XXX)
   - Risk: Low (preserves behavior)
   - Impact: Nesting reduced from X to Y levels

5. **Extract methods** to reduce function length
   - Function: `long_function()` (Line XXX)
   - Extract: 3-4 helper functions
   - Risk: Medium (requires careful testing)
   - Impact: Complexity reduced from XX to Y

### Phase 3: Advanced Refactoring (Higher Risk)
**Estimated Time:** [Duration]

6. **Separate concerns** into distinct layers
   - Mixed data/logic/presentation
   - Risk: Medium-High
   - Impact: Major architectural improvement

7. **Replace primitive obsession** with domain objects
   - Risk: High (API changes)
   - Impact: Type safety and validation improved

---

## Expected Outcomes

### Metrics Improvement Projections

| Metric | Current | Projected | Improvement |
|--------|---------|-----------|-------------|
| Avg Complexity | XX | Y | Z% ↓ |
| Avg Function Length | XX | Y | Z% ↓ |
| Max Nesting | X | Y | Z% ↓ |
| Docstring Coverage | XX% | Y% | Z% ↑ |
| Type Hint Coverage | XX% | Y% | Z% ↑ |

### Qualitative Improvements

- **Readability:** [Description of improvement]
- **Maintainability:** [Description of improvement]
- **Testability:** [Description of improvement]
- **Onboarding:** [Description of improvement]

---

## Test Coverage Assessment

### Current Coverage

- **Overall Coverage:** XX%
- **Critical Paths Covered:** Yes/No
- **Edge Cases Tested:** Yes/No
- **Integration Tests:** Yes/No

### Recommended Test Additions

Before refactoring, add tests for:

1. **[Test Description]** - Current gap in coverage
2. **[Test Description]** - Needed before structural changes
3. **[Test Description]** - Critical path not tested

---

## Dependencies Analysis

### Internal Dependencies

Functions/modules that depend on code being refactored:

1. **[Module/Function Name]** - [Dependency Type]
   - Impact: [Low/Medium/High]
   - Required Changes: [Description]

### External Dependencies

Third-party code or APIs affected:

1. **[Library/API Name]**
   - Impact: [Low/Medium/High]
   - Required Changes: [Description]

---

## Alternatives Considered

### Option A: [Approach Name]
- **Pros:** [List]
- **Cons:** [List]
- **Effort:** [Low/Medium/High]
- **Recommendation:** [Chosen/Not Chosen - Why]

### Option B: [Approach Name]
- **Pros:** [List]
- **Cons:** [List]
- **Effort:** [Low/Medium/High]
- **Recommendation:** [Chosen/Not Chosen - Why]

---

## Sign-Off Checklist

Before proceeding with refactoring:

- [ ] All high-priority issues identified
- [ ] Risk assessment completed
- [ ] Test coverage adequate (>80% recommended)
- [ ] Refactoring plan reviewed by team
- [ ] Time estimate approved
- [ ] Dependencies documented
- [ ] Rollback plan defined

---

## Next Steps

1. **Immediate:** [Action item]
2. **Short-term:** [Action item]
3. **Long-term:** [Action item]

---

## Notes

[Any additional context, concerns, or observations]
