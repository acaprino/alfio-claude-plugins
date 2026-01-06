# Refactoring Summary

**File:** `path/to/file.ext`
**Date:** YYYY-MM-DD
**Refactored By:** [Your Name]
**Duration:** [Time Spent]
**Risk Level:** [Low/Medium/High]

---

## Overview

[2-3 sentence summary of what was refactored and why]

---

## Changes Made

### 1. [Change Category - e.g., "Extracted Methods for Complexity Reduction"]

**Lines Affected:** XXX-YYY

**Description:**
[Detailed description of what was changed and why]

**Rationale:**
[Business/technical justification for this change]

**Pattern Applied:**
[Reference to pattern from patterns.md]

**Risk Level:** Low/Medium/High

**Before:**
```language
[Code snippet before refactoring]
```

**After:**
```language
[Code snippet after refactoring]
```

---

### 2. [Change Category]

**Lines Affected:** XXX-YYY

**Description:**
[Detailed description]

**Rationale:**
[Justification]

**Pattern Applied:**
[Pattern reference]

**Risk Level:** Low/Medium/High

**Before:**
```language
[Code snippet before]
```

**After:**
```language
[Code snippet after]
```

---

### 3. [Change Category]

**Lines Affected:** XXX-YYY

**Description:**
[Detailed description]

**Rationale:**
[Justification]

**Pattern Applied:**
[Pattern reference]

**Risk Level:** Low/Medium/High

---

## Metrics Improvement

### Complexity Metrics

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| Avg Cyclomatic Complexity | XX.X | Y.Y | -Z.Z (-W%) | ✓ |
| Max Cyclomatic Complexity | XX | Y | -Z (-W%) | ✓ |
| Avg Function Length (lines) | XX | Y | -Z (-W%) | ✓ |
| Max Function Length (lines) | XX | Y | -Z (-W%) | ✓ |
| Avg Nesting Depth | X.X | Y.Y | -Z.Z (-W%) | ✓ |
| Max Nesting Depth | X | Y | -Z (-W%) | ✓ |
| Total Functions | X | Y | +Z (+W%) | Note: More but simpler |

### Documentation Metrics

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| Module Docstring | No/Yes | Yes | Added | ✓ |
| Docstring Coverage | XX% | YY% | +Z% | ✓ |
| Type Hint Coverage | XX% | YY% | +Z% | ✓ |
| Documented Functions | X/Y | Z/Z | All documented | ✓ |

### Code Size Metrics

| Metric | Before | After | Change | Note |
|--------|--------|-------|--------|------|
| Total Lines of Code | XXX | YYY | +ZZ | More verbose but clearer |
| Blank Lines | XX | YY | +Z | Improved readability |
| Comment Lines | XX | YY | +Z | Better documentation |

---

## Validation Results

### Test Results

**Test Suite:** [Name]
**Tests Run:** XXX
**Tests Passed:** XXX ✓
**Tests Failed:** 0
**Test Coverage:** XX% (unchanged/improved)

**Details:**
- All existing tests pass without modification ✓
- No regression detected ✓
- Test execution time: [Duration] (±X% change)

### Performance Validation

**Benchmark Results:**

| Function | Before | After | Change | Status |
|----------|--------|-------|--------|--------|
| `function_name()` | X.XX ms | Y.YY ms | +Z% | ✓ Within threshold |
| `another_function()` | X.XX ms | Y.YY ms | -Z% | ✓ Faster |

**Performance Assessment:**
- No function shows >10% regression ✓
- Overall performance impact: [Negligible/Positive/Within acceptable range]

### Code Quality Validation

**Linter Results:**
- Warnings Before: XX
- Warnings After: Y
- Reduction: Z warnings fixed

**Type Checker Results:**
- Type Errors Before: XX
- Type Errors After: 0 ✓
- New Type Coverage: YY%

---

## Risk Assessment

### Overall Risk: [Low/Medium/High]

**Risk Factors:**

✓ **Low Risk Factors:**
- All tests passing
- No public API changes
- Performance within acceptable range
- Changes are mechanical refactorings
- Full test coverage maintained

⚠ **Medium Risk Factors:**
- [If any, list here]

✗ **High Risk Factors:**
- [If any, list here]

### Risk Mitigation

[If medium/high risk, describe mitigation steps taken]

---

## Human Review Recommendations

**Review Required:** [Yes/No]

**Review Focus Areas:**
1. [Specific area if review needed - e.g., "Verify business logic in extracted payment_calculator() function"]
2. [Another area if applicable]
3. [Another area if applicable]

**Review Checklist:**
- [ ] Verify all tests pass
- [ ] Review extracted functions for correctness
- [ ] Confirm no unintended behavior changes
- [ ] Validate performance is acceptable
- [ ] Check documentation accuracy
- [ ] Verify error handling remains robust

---

## Breaking Changes

**API Changes:** [None/Listed Below]

[If any breaking changes, list them here with migration guide]

**Migration Guide:**
[If applicable, provide guidance for updating calling code]

---

## Lessons Learned

### What Went Well
1. [Positive outcome or discovery]
2. [Another positive aspect]

### Challenges Encountered
1. [Challenge faced and how it was resolved]
2. [Another challenge]

### Recommendations for Future
1. [Suggestion for similar refactorings]
2. [Process improvement suggestion]

---

## Related Refactorings

### Recommended Follow-Ups

Based on this refactoring, these related improvements are recommended:

1. **[Related File/Function]**
   - Issue: [Similar problem]
   - Estimated Effort: [Duration]
   - Priority: [Low/Medium/High]

2. **[Another Related Area]**
   - Issue: [Description]
   - Estimated Effort: [Duration]
   - Priority: [Low/Medium/High]

---

## Commit Information

**Branch:** `feature/refactor-[description]`
**Commits:** X commit(s)

**Commit Messages:**
- `[commit-hash]` - [Commit message]
- `[commit-hash]` - [Commit message]

**Pull Request:** #XXX (if applicable)

---

## Sign-Off

**Refactored By:** [Your Name]
**Date:** YYYY-MM-DD

**Reviewed By:** [Reviewer Name] (if applicable)
**Review Date:** YYYY-MM-DD

**Approved For Merge:** [Yes/Pending/No]

---

## Appendix

### Files Modified
- `path/to/file1.ext` - [Description of changes]
- `path/to/file2.ext` - [Description of changes]

### References
- [Link to relevant documentation]
- [Link to related issues/PRs]
- [Link to patterns used]

### Additional Notes
[Any other relevant information, context, or observations]
