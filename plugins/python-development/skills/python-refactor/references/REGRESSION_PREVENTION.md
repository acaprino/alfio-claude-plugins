# REGRESSION PREVENTION GUIDE

> **FUNDAMENTAL PRINCIPLE:** Refactoring transforms the STRUCTURE of code, NEVER its BEHAVIOR.
> Any technical, logical, or functional regression is a TOTAL FAILURE of the refactoring.

---

## MANDATORY PRE-REFACTORING CHECKLIST

**Do NOT start ANY refactoring until ALL of these are verified:**

### 1. Test Coverage Assessment

```bash
# Check current coverage
pytest --cov=<module> --cov-report=term-missing

# Minimum coverage required to proceed
# - >= 80%: Proceed with normal caution
# - 60-80%: Proceed but add tests BEFORE each modification
# - < 60%: STOP! Write tests BEFORE refactoring
```

- [ ] Coverage >= 80% on target functions?
- [ ] If NO -> **Write tests FIRST, THEN refactor**
- [ ] Existing test suite passes at 100%?
- [ ] Tests exist for ALL critical edge cases?

### 2. Behavioral Baseline Capture

**BEFORE touching the code, capture current behavior:**

```python
# Save reference output for critical cases
import json

def capture_golden_outputs():
    """Run BEFORE refactoring and save the results."""
    test_cases = [
        # Normal cases
        {"input": normal_input_1, "description": "normal case 1"},
        {"input": normal_input_2, "description": "normal case 2"},
        # CRITICAL edge cases
        {"input": None, "description": "null input"},
        {"input": [], "description": "empty list"},
        {"input": "", "description": "empty string"},
        {"input": boundary_value, "description": "boundary condition"},
        # Error cases
        {"input": invalid_input, "description": "should raise ValueError"},
    ]

    results = []
    for case in test_cases:
        try:
            output = function_to_refactor(case["input"])
            results.append({
                "input": case["input"],
                "output": output,
                "exception": None,
                "description": case["description"]
            })
        except Exception as e:
            results.append({
                "input": case["input"],
                "output": None,
                "exception": {"type": type(e).__name__, "message": str(e)},
                "description": case["description"]
            })

    with open("golden_outputs_BEFORE_REFACTOR.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results
```

- [ ] Golden outputs saved for critical functions?
- [ ] Edge cases documented and captured?
- [ ] Behavior with invalid inputs documented?

### 3. Edge Case Identification

**For EVERY function to be refactored, identify:**

```markdown
## Edge Cases for: function_name()

### Input Boundaries
- [ ] Input None/null
- [ ] Empty input ([], {}, "", 0)
- [ ] Boundary input (MAX_INT, very long strings)
- [ ] Negative input (if applicable)

### State Conditions
- [ ] First call (initial state)
- [ ] Repeated calls (accumulated state)
- [ ] Corrupted/inconsistent state

### Error Conditions
- [ ] Expected exceptions (which? when?)
- [ ] Timeout/interruptions
- [ ] Unavailable resources

### Concurrency (if applicable)
- [ ] Known race conditions
- [ ] Potential deadlocks
```

- [ ] Edge cases identified for EVERY function?
- [ ] Current behavior on edge cases DOCUMENTED?

### 4. Static Analysis Baseline

```bash
# Capture baseline BEFORE refactoring
flake8 <file> --output-file=flake8_BEFORE.txt
python scripts/measure_complexity.py <file> --json > complexity_BEFORE.json
python scripts/check_documentation.py <file> --json > docs_BEFORE.json

# For historical tracking (if available)
wily build <src_dir>
wily report <file> > wily_BEFORE.txt
```

- [ ] flake8 baseline captured?
- [ ] Complexity metrics saved?
- [ ] No hidden pre-existing critical errors?

---

## MANDATORY POST-CHANGE CHECKLIST

**After EVERY micro-change (not at the end, EVERY SINGLE ONE):**

### Immediate Verification (< 30 seconds)

```bash
# 1. Static analysis BEFORE tests (catches NameErrors immediately)
flake8 <file> --select=F821,F841,E999,E0602

# F821: undefined name (CRITICAL - guaranteed NameError)
# F841: local variable assigned but never used (possible bug)
# E999: syntax error (CRITICAL - code won't execute)
# E0602: undefined variable (CRITICAL)

# 2. If ZERO critical errors, run tests
pytest <test_file> -x --tb=short

# -x = fail fast (stop at first error)
# --tb=short = compact traceback
```

- [ ] `flake8 --select=F821,F841,E999` -> ZERO errors?
- [ ] `pytest -x` -> all tests passing?
- [ ] If ANY failure -> **REVERT IMMEDIATELY**

### For Each Guard Clause Added

Guard clauses are the most common pattern but also the most insidious for subtle bugs:

```python
# BEFORE (nested)
def process(user):
    if user:
        if user.active:
            if user.verified:
                return do_work(user)
    return None

# AFTER (guard clauses) - VERIFY EQUIVALENCE!
def process(user):
    if not user:           # Verify: user=None -> return None [ok]
        return None
    if not user.active:    # Verify: user.active=False -> return None [ok]
        return None
    if not user.verified:  # Verify: user.verified=False -> return None [ok]
        return None
    return do_work(user)   # Verify: all True -> do_work() [ok]
```

**Checklist for EACH guard clause:**
- [ ] Input `None` -> same behavior as before?
- [ ] Input with attribute `False` -> same behavior?
- [ ] Valid input -> same final result?
- [ ] Order of conditions preserved? (short-circuit evaluation!)

### For Each Extract Method

```python
# BEFORE
def big_function(data):
    # ... 50 lines ...
    result = complex_calculation(x, y, z)
    # ... 30 more lines ...

# AFTER
def big_function(data):
    # ...
    result = _calculate_result(x, y, z)  # Extracted
    # ...

def _calculate_result(x, y, z):  # New function
    return complex_calculation(x, y, z)
```

**Checklist for EACH extract method:**
- [ ] ALL necessary parameters passed?
- [ ] Local variables no longer accessible handled?
- [ ] Return value correctly propagated?
- [ ] Side effects preserved (if intentional)?
- [ ] Specific test for the extracted function added?

---

## EQUIVALENCE TESTING PATTERNS

### Pattern 1: Golden Master Testing

```python
import json
import pytest

class TestRefactoringEquivalence:
    """Verify that refactoring does not change behavior."""

    @pytest.fixture
    def golden_outputs(self):
        with open("golden_outputs_BEFORE_REFACTOR.json") as f:
            return json.load(f)

    def test_all_golden_cases(self, golden_outputs):
        """Every output must be IDENTICAL to the golden master."""
        for case in golden_outputs:
            if case["exception"]:
                # Must raise the SAME exception
                with pytest.raises(eval(case["exception"]["type"])):
                    refactored_function(case["input"])
            else:
                # Must produce the SAME output
                result = refactored_function(case["input"])
                assert result == case["output"], \
                    f"Regression on {case['description']}: " \
                    f"expected {case['output']}, got {result}"
```

### Pattern 2: Property-Based Testing (Hypothesis)

```python
from hypothesis import given, strategies as st, settings

# For pure functions: output must be IDENTICAL
@given(st.integers(), st.booleans(), st.text())
@settings(max_examples=1000)
def test_refactored_equals_original(x, flag, text):
    """Refactoring MUST NOT change behavior."""
    # Keep old implementation commented or in separate file
    expected = original_function(x, flag, text)
    actual = refactored_function(x, flag, text)
    assert actual == expected

# For functions with side effects: verify final state
@given(st.lists(st.integers()))
def test_state_equivalence(items):
    """Final state must be identical."""
    # Identical setup
    state_original = OriginalClass()
    state_refactored = RefactoredClass()

    # Same operations
    for item in items:
        state_original.process(item)
        state_refactored.process(item)

    # Identical final state
    assert state_original.get_state() == state_refactored.get_state()
```

### Pattern 3: Parallel Execution (for high-risk refactoring)

```python
import functools

def verify_equivalence(original_func):
    """Decorator that runs BOTH versions and compares."""
    def decorator(refactored_func):
        @functools.wraps(refactored_func)
        def wrapper(*args, **kwargs):
            # Run original
            original_result = original_func(*args, **kwargs)
            # Run refactored
            refactored_result = refactored_func(*args, **kwargs)
            # Compare
            assert original_result == refactored_result, \
                f"REGRESSION DETECTED!\n" \
                f"Input: {args}, {kwargs}\n" \
                f"Original: {original_result}\n" \
                f"Refactored: {refactored_result}"
            return refactored_result
        return wrapper
    return decorator

# Use during development (remove in production)
@verify_equivalence(original_calculate_discount)
def calculate_discount(price, tier):
    # New refactored implementation
    ...
```

---

## METRICS THAT MUST NOT REGRESS

### Hard Limits (violation = immediate rollback)

| Metric | Limit | Action if Violated |
|--------|-------|-------------------|
| Test pass rate | 100% | REVERT |
| F821 errors (undefined name) | 0 | REVERT |
| E999 errors (syntax) | 0 | REVERT |
| Performance degradation | < 10% | REVERT or explicit approval |
| Coverage decrease | 0% | Add tests before merge |

### Soft Limits (violation = review required)

| Metric | Target | Action if Violated |
|--------|--------|-------------------|
| Cognitive complexity | <= 15 per function | Refactor further |
| Cyclomatic complexity | <= 10 per function | Refactor further |
| Function length | <= 30 lines | Extract methods |
| Nesting depth | <= 3 levels | Guard clauses |

### Metrics Comparison Script

```bash
#!/bin/bash
# compare_regression.sh - Run BEFORE and AFTER refactoring

echo "=== REGRESSION CHECK ==="

# 1. Test pass rate
echo "Running tests..."
pytest --tb=no -q
if [ $? -ne 0 ]; then
    echo "REGRESSION: Tests failing!"
    exit 1
fi
echo "Tests passing"

# 2. Static analysis
echo "Running static analysis..."
ERRORS=$(flake8 $1 --select=F821,E999 --count 2>/dev/null | tail -1)
if [ "$ERRORS" != "0" ] && [ -n "$ERRORS" ]; then
    echo "REGRESSION: Critical static analysis errors!"
    flake8 $1 --select=F821,E999
    exit 1
fi
echo "No critical errors"

# 3. Compare complexity
echo "Comparing complexity..."
python scripts/compare_metrics.py $1_before.py $1_after.py

echo "=== REGRESSION CHECK COMPLETE ==="
```

---

## ROLLBACK PROTOCOL

### When to Rollback Immediately

1. **ANY test failure** after a change
2. **ANY F821/E999 flake8 error**
3. **Performance degradation > 10%** without approval
4. **Behavioral change detected** (golden master mismatch)

### How to Rollback

```bash
# If using git (recommended: atomic commits for each micro-change)
git checkout -- <file>           # Discard uncommitted changes
git revert HEAD                   # Revert last commit
git reset --hard HEAD~1           # Nuclear option: discard last commit entirely

# If not using git: ALWAYS keep backups
cp <file> <file>.backup_YYYYMMDD_HHMM  # Before each session
```

### Post-Rollback Analysis

```markdown
## Rollback Report

**File:** <filename>
**Change attempted:** <description>
**Failure type:** Test failure / Static error / Performance / Behavioral

**Root cause analysis:**
- What was the specific error?
- Why wasn't it caught before commit?
- What check was missing?

**Prevention for future:**
- [ ] Add specific test case for this scenario
- [ ] Add to pre-change checklist
- [ ] Update golden master if needed
```

---

## COMMON REGRESSION TRAPS

### Trap 1: Short-Circuit Evaluation Changes

```python
# BEFORE: second_check() NEVER called if first_check() is False
if first_check() and second_check():
    ...

# AFTER (WRONG!): second_check() ALWAYS called
if all([first_check(), second_check()]):  # Changes behavior!
    ...

# AFTER (CORRECT): preserves short-circuit
if first_check() and second_check():  # Identical
    ...
```

### Trap 2: Exception Handling Scope

```python
# BEFORE: handles ONLY ValueError
try:
    risky_operation()
except ValueError:
    handle_error()

# AFTER (WRONG!): handles ALL exceptions
try:
    risky_operation()
except Exception:  # Too broad!
    handle_error()
```

### Trap 3: Mutable Default Arguments

```python
# BEFORE (bug, but "expected" behavior by the system)
def append_to(item, lst=[]):
    lst.append(item)
    return lst

# AFTER (correct, but CHANGES BEHAVIOR!)
def append_to(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst

# If the system DEPENDED on the bug, this is a breaking change!
```

### Trap 4: Return Value Changes

```python
# BEFORE: returns None implicitly if condition is false
def get_user(user_id):
    if user_id in cache:
        return cache[user_id]
    # Implicit return None

# AFTER (WRONG if caller checks "if result:")
def get_user(user_id):
    if user_id not in cache:
        return User.empty()  # Now returns truthy object!
    return cache[user_id]
```

---

## QUICK REFERENCE CARD

```
+-------------------------------------------------------------+
|                 REFACTORING SAFETY CHECKLIST                  |
+-------------------------------------------------------------+
| BEFORE ANY CHANGE:                                            |
| [ ] Tests passing 100%?                                       |
| [ ] Coverage >= 80% on target code?                           |
| [ ] Golden outputs captured?                                  |
| [ ] Edge cases identified?                                    |
+-------------------------------------------------------------+
| AFTER EACH MICRO-CHANGE:                                      |
| [ ] flake8 --select=F821,E999 -> 0 errors?                   |
| [ ] pytest -x -> all passing?                                 |
| [ ] Behavior unchanged? (spot check 1 edge case)             |
+-------------------------------------------------------------+
| BEFORE COMMIT:                                                |
| [ ] All tests passing?                                        |
| [ ] Golden master comparison passed?                          |
| [ ] No performance regression?                                |
| [ ] Metrics improved or unchanged?                            |
+-------------------------------------------------------------+
| IF ANY CHECK FAILS:                                           |
| -> STOP -> REVERT -> ANALYZE -> FIX APPROACH -> RETRY         |
+-------------------------------------------------------------+
```

---

**REMEMBER:** A refactoring that introduces regressions is not a refactoring. It is a bug.
