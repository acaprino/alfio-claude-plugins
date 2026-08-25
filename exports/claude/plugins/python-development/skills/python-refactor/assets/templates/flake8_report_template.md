# Flake8 Code Quality Report

**Target:** `path/to/code`
**Date:** YYYY-MM-DD
**Analysis Type:** [Before Refactoring / After Refactoring]

---

## Executive Summary

**Status:** [PASSED / FAILED]
**Total Issues:** XXX
**Risk Level:** [Low / Medium / High]

[2-3 sentence summary of overall code quality based on flake8 analysis]

---

## Installed Plugins

### ESSENTIAL (Must-Have - Highest Impact)
✓/✗ **flake8-bugbear**: Finds likely bugs and design problems (B codes)
✓/✗ **flake8-simplify**: Suggests simpler, clearer code (SIM codes)
✓/✗ **flake8-cognitive-complexity**: Measures cognitive load (CCR codes)
✓/✗ **pep8-naming**: Enforces clear naming conventions (N codes)
✓/✗ **flake8-docstrings**: Ensures documentation (D codes)

### RECOMMENDED (Strong Readability Impact)
✓/✗ **flake8-comprehensions**: Cleaner comprehensions (C4 codes)
✓/✗ **flake8-expression-complexity**: Prevents complex expressions (ECE codes)
✓/✗ **flake8-functions**: Simpler function signatures (CFQ codes)
✓/✗ **flake8-variables-names**: Better variable naming (VNE codes)
✓/✗ **tryceratops**: Clean exception handling (TC codes)

### OPTIONAL (Nice to Have)
✓/✗ **flake8-builtins**: Prevents shadowing built-ins (A codes)
✓/✗ **flake8-eradicate**: Finds commented-out code (E800 codes)
✓/✗ **flake8-unused-arguments**: Flags unused parameters (U codes)
✓/✗ **flake8-annotations**: Validates type hints (ANN codes)
✓/✗ **pydoclint**: Complete docstrings (DOC codes)
✓/✗ **flake8-spellcheck**: Catches typos (SC codes)

### Missing Plugins

**Missing ESSENTIAL plugins (install these first):**
[List missing essential plugins]

**Installation Command:**
```bash
pip install flake8 [missing-essential-plugins]
```

**Missing RECOMMENDED plugins:**
[List missing recommended plugins]

**Installation Command:**
```bash
pip install [missing-recommended-plugins]
```

**Install all 16 plugins (full suite):**
```bash
pip install flake8 flake8-bugbear flake8-simplify \
    flake8-cognitive-complexity pep8-naming flake8-docstrings \
    flake8-comprehensions flake8-expression-complexity \
    flake8-functions flake8-variables-names tryceratops \
    flake8-builtins flake8-eradicate flake8-unused-arguments \
    flake8-annotations pydoclint flake8-spellcheck
```

---

## Issues by Severity

| Severity | Count | Percentage |
|----------|-------|------------|
| High     | XX    | XX%        |
| Medium   | XX    | XX%        |
| Low      | XX    | XX%        |
| **Total**| **XXX** | **100%** |

### Severity Distribution

```
High   [████████░░] XX%
Medium [██████░░░░] XX%
Low    [███░░░░░░░] XX%
```

---

## Issues by Category

| Category | Count | Description |
|----------|-------|-------------|
| Style Error (PEP 8) | XX | Code style violations |
| Style Warning (PEP 8) | XX | Code style warnings |
| PyFlakes Error | XX | Code logic errors |
| Complexity | XX | High complexity violations |
| Bugbear (Likely Bug) | XX | Potential bugs identified |
| Naming Convention | XX | PEP 8 naming violations |
| Docstring | XX | Missing or malformed docstrings |
| Annotations | XX | Missing type annotations |
| Simplification | XX | Code can be simplified |

---

## Top Issue Types

| Code | Count | Description | Severity |
|------|-------|-------------|----------|
| EXXX | XXX   | [Description of error code] | High/Med/Low |
| EXXX | XXX   | [Description] | High/Med/Low |
| EXXX | XXX   | [Description] | High/Med/Low |
| ... |

---

## Files with Most Issues

| File | Issue Count | Primary Issues |
|------|-------------|----------------|
| path/to/file1.py | XXX | E501, C901, D103 |
| path/to/file2.py | XXX | F401, N803, B008 |
| path/to/file3.py | XXX | E302, W503, D100 |
| ... |

---

## High Severity Issues

### Potential Bugs (Bugbear - B codes)

**B001** - Line XXX: Do not use bare `except:`
```python
# File: path/to/file.py:XXX
try:
    dangerous_operation()
except:  # Too broad!
    pass
```
**Impact:** May catch and hide critical errors like KeyboardInterrupt
**Fix:** Catch specific exceptions or use `except Exception:`

---

**B006** - Line XXX: Do not use mutable data structures as default arguments
```python
# File: path/to/file.py:XXX
def append_to_list(item, lst=[]):  # Dangerous!
    lst.append(item)
    return lst
```
**Impact:** Shared mutable default causes unexpected behavior
**Fix:** Use `lst=None` and initialize inside function

---

### PyFlakes Errors (F codes)

**F401** - Lines XXX, YYY, ZZZ: Module imported but unused
**Impact:** Clutters namespace, suggests dead code
**Fix:** Remove unused imports or add to `__all__`

**F841** - Lines XXX, YYY: Local variable assigned but never used
**Impact:** Dead code, possible logic error
**Fix:** Remove assignment or use the variable

---

### Runtime Errors (E9 codes)

[List any E9xx codes - these are critical syntax/runtime errors]

---

## Medium Severity Issues

### Complexity (C codes)

**C901** - Function too complex
```
Function: complex_function() (Line XXX)
Cyclomatic Complexity: XX (threshold: 10)
```
**Impact:** Hard to understand and test
**Recommendation:** Apply Extract Method pattern (see patterns.md)

---

### Naming Conventions (N codes)

**N802** - Lines XXX, YYY: Function name should be lowercase
```python
def CalculateTotal():  # Should be: calculate_total()
    pass
```

**N803** - Lines XXX: Argument name should be lowercase
**N806** - Lines XXX: Variable should be lowercase

---

### Annotations (A codes)

**ANN201** - Lines XXX, YYY, ZZZ: Missing return type annotation
```python
def process_data(data: str):  # Missing -> ReturnType
    return data.upper()
```
**Impact:** Reduced type safety, no IDE support
**Fix:** Add return type annotation

---

## Low Severity Issues

### Style Errors (E/W codes)

**E501** - Line too long (XX > 88 characters)
**E302** - Expected 2 blank lines, found 1
**E303** - Too many blank lines
**W503** - Line break before binary operator

[List most common style violations with counts]

---

### Docstring Issues (D codes)

**D100** - Missing docstring in public module
**D103** - Missing docstring in public function
**D107** - Missing docstring in __init__

**Functions Missing Docstrings:**
1. `function_name()` - Line XXX
2. `another_function()` - Line YYY
3. [...]

---

### Simplification Opportunities (S codes)

**SIM105** - Lines XXX: Use `contextlib.suppress()` instead of try/except/pass
**SIM108** - Lines XXX: Use ternary operator instead of if/else
**SIM118** - Lines XXX: Use `key in dict` instead of `key in dict.keys()`

---

## Detailed Issue List

### Critical Issues (Must Fix)

1. **File:** `path/to/file.py:XXX`
   **Code:** BXXX
   **Severity:** High
   **Message:** [Full error message]
   **Recommendation:** [How to fix]

2. [Continue with all high severity issues...]

---

### Important Issues (Should Fix)

[Medium severity issues with line numbers and recommendations]

---

### Minor Issues (Nice to Fix)

[Low severity issues - can list first 50]

---

## Recommendations

### Immediate Actions (High Priority)

1. **Fix all Bugbear issues (B codes)** - These indicate likely bugs
   - Estimated effort: [Duration]
   - Files affected: [X files]

2. **Address PyFlakes errors (F codes)** - Dead code and logic issues
   - Estimated effort: [Duration]
   - Files affected: [X files]

3. **Reduce function complexity (C901)** - Apply Extract Method pattern
   - Estimated effort: [Duration]
   - Functions affected: [X functions]

### Short-Term Actions (Medium Priority)

4. **Add missing docstrings (D codes)** - Improve documentation
   - Target: >80% coverage
   - Estimated effort: [Duration]

5. **Add type annotations (ANN codes)** - Improve type safety
   - Target: >90% coverage
   - Estimated effort: [Duration]

6. **Fix naming conventions (N codes)** - Follow PEP 8
   - Estimated effort: [Duration]

### Long-Term Actions (Low Priority)

7. **Address style violations (E/W codes)** - Improve consistency
   - Consider using Black formatter
   - Estimated effort: [Duration]

8. **Apply simplifications (S codes)** - Make code more Pythonic
   - Estimated effort: [Duration]

---

## Comparison with Targets

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total Issues | XXX | 0 | ⚠ |
| High Severity | XX | 0 | ⚠/✓ |
| Medium Severity | XX | <10 | ⚠/✓ |
| Complexity Violations | XX | 0 | ⚠/✓ |
| Docstring Coverage | XX% | >80% | ⚠/✓ |
| Type Hint Coverage | XX% | >90% | ⚠/✓ |

---

## Integration with Refactoring Workflow

### Issues Aligned with Anti-Patterns

[Map flake8 issues to anti-patterns.md categories]

**Complex Nested Conditionals** ← C901 (High complexity)
**God Functions** ← C901 (Complexity), E501 (Too long)
**Magic Numbers** ← No direct flake8 code (manual review needed)
**Cryptic Names** ← N803, N806 (Naming violations)
**Missing Docstrings** ← D100-D107 (Docstring codes)
**Missing Type Hints** ← ANN* codes
**Unclear Error Handling** ← B001 (Bare except)

### Recommended Patterns to Apply

Based on flake8 results, apply these patterns from patterns.md:

1. **Extract Method** - For C901 complexity violations
2. **Guard Clauses** - For deeply nested code (manual + C901)
3. **Add Documentation** - For D codes
4. **Add Type Hints** - For ANN codes
5. **Improve Naming** - For N codes
6. **Simplify Code** - For S codes

---

## Next Steps

1. **Review High Severity Issues** - Fix all B, F, and E9 codes first
2. **Run Refactoring Workflow** - Use patterns from patterns.md
3. **Re-run flake8** - Measure improvements
4. **Compare Reports** - Use compare_flake8_reports.py

**Command to Re-run:**
```bash
python scripts/analyze_with_flake8.py <target> --output after_flake8.json --html after_flake8.html
```

**Command to Compare:**
```bash
python scripts/compare_flake8_reports.py before_flake8.json after_flake8.json --html comparison.html
```

---

## Configuration Used

```ini
[flake8]
max-line-length = 88
max-complexity = 10
max-cognitive-complexity = 10
max-expression-complexity = 7
docstring-convention = google
```

**Configuration File:** `assets/.flake8`
[Copy this file to your project root for consistent analysis]

---

## Additional Resources

- **Flake8 Documentation:** https://flake8.pycqa.org/
- **Plugin Documentation:**
  - flake8-bugbear: https://github.com/PyCQA/flake8-bugbear
  - flake8-docstrings: https://github.com/PyCQA/flake8-docstrings
  - flake8-simplify: https://github.com/MartinThoma/flake8-simplify
- **Anti-Patterns Reference:** `references/anti-patterns.md`
- **Refactoring Patterns:** `references/patterns.md`

---

## Report Metadata

**Generated By:** python-refactor skill
**Skill Version:** 1.1.0
**Timestamp:** YYYY-MM-DD HH:MM:SS
**Flake8 Version:** [Version from --version]
**Python Version:** [Version]

---

## Notes

[Any additional observations, context, or recommendations specific to this codebase]
