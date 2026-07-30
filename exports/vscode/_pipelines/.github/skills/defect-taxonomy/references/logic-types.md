# Comparison & Logic Errors + Type & Conversion Errors

Reference for defect taxonomy categories 3 and 4.

---

## Category 3: Comparison and Logic Errors

### 3.1 Wrong Comparison Operators
- **CWE**: 597
- **Pattern**: Identity vs equality confusion
  - Java: `==` on objects (compares reference) vs `.equals()` (compares value)
  - JS: `==` (coercing) vs `===` (strict)
  - Python: `is` (identity) vs `==` (equality)
- **Detection**: ESLint `eqeqeq`, SpotBugs `EC_UNRELATED_TYPES`, `RC_REF_COMPARISON`
- **Fix**: Always `.equals()` for objects, `===` in JS, `==` in Python (reserve `is` for `None`/singletons)
- **Difficulty**: Low

### 3.2 Floating-Point Comparison
- **CWE**: 1339
- **Pattern**: `0.1 + 0.2 !== 0.3` due to IEEE 754 representation
- **Detection**: Static analysis for `==`/`!=` on floats, ESLint custom rule
- **Fix**: Epsilon comparison `Math.abs(a - b) < 1e-9`, `BigDecimal` (Java), `decimal` module (Python), integer cents for currency
- **Difficulty**: Medium
- **Signature**: `if (total == 0.3)`, `price1 == price2` on doubles

### 3.3 Off-by-One in Conditions
- **CWE**: 193 (related)
- **Pattern**: `<` vs `<=` errors in loop bounds, pagination, tree traversal, fence-post
- **Detection**: Boundary-value tests, mutation testing (changing `<` to `<=`)
- **Fix**: Half-open intervals `[start, end)`, explicit boundary test cases, property-based testing
- **Difficulty**: Medium

### 3.4 Boolean Logic Errors
- **CWE**: N/A
- **Pattern**: De Morgan violations, redundant conditions, contradictory predicates, tautologies
- **Detection**: Satisfiability checking, tautology/contradiction detection, code review
- **Fix**: Truth tables for complex expressions, extract named boolean methods, simplify with De Morgan
- **Difficulty**: Medium
- **Signature**: `if (!a && !b)` intended as `if (!(a && b))` -- De Morgan confusion

### 3.5 Short-Circuit Evaluation Misuse
- **CWE**: N/A
- **Pattern**: Side effects in `&&`/`||` second operand, null-check ordering bugs
- **Detection**: AST analysis for side-effect expressions in short-circuit positions
- **Fix**: Separate side effects from conditions, null checks always on left side
- **Difficulty**: Medium
- **Signature**: `if (process() && validate())` -- `validate()` skipped when `process()` false

### 3.6 Operator Precedence Errors
- **CWE**: 783
- **Pattern**: `&` vs `&&` confusion in C/Java, `flags & MASK == 0` parsed as `flags & (MASK == 0)`
- **Detection**: `-Wparentheses` (GCC/Clang), SpotBugs `BIT_AND_ZZ`
- **Fix**: Explicit parentheses always, `(flags & MASK) == 0`
- **Difficulty**: Low-Medium
- **Signature**: `if (a & b == 0)`, `x << 1 + y` parsed as `x << (1 + y)`

### 3.7 Negation Errors
- **CWE**: N/A
- **Pattern**: Double negation obscuring intent, negating wrong part of compound expression
- **Detection**: Mutation testing (inverting conditions), code review for `!(!x)`
- **Fix**: Positive naming (`isValid` not `isNotInvalid`), extract predicate methods
- **Difficulty**: Medium
- **Signature**: `if (!list.isEmpty() == false)`, `if (!(a > b && c < d))` intended scope unclear

### 3.8 Boundary Condition Errors
- **CWE**: N/A
- **Pattern**: `MAX_VALUE + 1` overflow, empty collection edge, null vs empty string, zero-element
- **Detection**: Property-based testing, boundary-value analysis, fuzzing
- **Fix**: Explicit boundary checks, handle empty/null/zero/max as first-class cases
- **Difficulty**: Medium
- **Signature**: Missing check for empty list before `.get(0)`, `Integer.MAX_VALUE + 1`

---

## Category 4: Type and Conversion Errors

### 4.1 Implicit Type Coercion
- **CWE**: N/A
- **Pattern**: JS `"5" + 3 = "53"` but `"5" - 3 = 2`, C integer promotion widening/narrowing
- **Detection**: TypeScript strict mode, Flow, `-Wconversion` (GCC/Clang), `-Wimplicit-int-conversion`
- **Fix**: Explicit conversions (`Number()`, `parseInt()`), TypeScript, type annotations
- **Difficulty**: Medium
- **Signature**: `"" + number` for string conversion, implicit bool-to-int

### 4.2 Integer Overflow / Underflow
- **CWE**: 190, 191
- **Pattern**: C/C++ undefined behavior, Java silent wrapping, Rust panics (debug) or wraps (release)
- **Detection**: `-ftrapv`, UBSan (`-fsanitize=undefined`), `Math.addExact()` (Java), Clippy
- **Fix**: Checked arithmetic, wider types, `Math.addExact`/`Math.multiplyExact`, Rust `checked_add`
- **Difficulty**: Medium-Hard
- **Signature**: `int total = price * quantity` -- can overflow, `array[offset + len]` -- offset+len wraps

### 4.3 Truncation Errors
- **CWE**: 197
- **Pattern**: Float-to-int loses precision, long-to-int loses high bits, currency rounding
- **Detection**: `-Wconversion`, `-Wfloat-conversion`, Coverity `MISRA_CAST`
- **Fix**: `BigDecimal` for currency, explicit casts with range checks, `Math.toIntExact()` (Java)
- **Difficulty**: Medium
- **Signature**: `int price = (int) calculateTotal()`, `short s = (short) largeInt`

### 4.4 Unsafe Casts / Downcasts
- **CWE**: 704
- **Pattern**: `ClassCastException`, C-style casts hiding errors, `as` keyword misuse
- **Detection**: SpotBugs `BC_UNCONFIRMED_CAST`, `-Wold-style-cast` (C++)
- **Fix**: `instanceof`/pattern matching (Java 17+), `dynamic_cast` + null check (C++), generics, type guards (TS)
- **Difficulty**: Medium
- **Signature**: `(SpecificType) genericObject` without prior `instanceof` check

### 4.5 Generic Type Erasure (JVM)
- **CWE**: N/A
- **Pattern**: `List<String>` becomes raw `List` at runtime, heap pollution, unchecked casts
- **Detection**: `-Xlint:unchecked`, SpotBugs, IntelliJ inspections
- **Fix**: Never mix raw/parameterized types, `Collections.checkedList()`, super type tokens
- **Difficulty**: Medium
- **Signature**: `List rawList = typedList;`, `(List<String>) object` -- unchecked cast

### 4.6 Variance Errors
- **CWE**: N/A
- **Pattern**: `List<Dog>` is NOT a subtype of `List<Animal>` (invariant), TS covariant method params (unsound)
- **Detection**: Compiler errors (Java), TypeScript `--strictFunctionTypes`
- **Fix**: PECS principle (Producer-Extends, Consumer-Super), `? extends T`/`? super T`, `@covariant`/`@contravariant`
- **Difficulty**: Medium-Hard
- **Signature**: `List<Animal> animals = dogs;` -- compile error, `void process(List<Animal>)` won't accept `List<Dog>`

### 4.7 Serialization Type Mismatches
- **CWE**: 502
- **Pattern**: JSON/Protobuf schema evolution breaking clients, field rename/removal, type changes
- **Detection**: Schema validation, consumer-driven contract testing, compatibility checkers
- **Fix**: Schema registries with compatibility rules, never remove required fields, additive-only changes, field numbering (Protobuf)
- **Difficulty**: Medium-Hard
- **Signature**: Server adds required field, old clients send without it -- deserialization fails
