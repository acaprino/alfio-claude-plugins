# Case 1: The Rule of Three is not a universal gate for track A

**Guards:** `references/evidence-tracks.md` gate A3, `references/dimensions.md` D6 and D7.

**Why it decays:** the Rule of Three is the most memorable thing in the plugin's theory. A future editor tidying the gates will be tempted to hoist it from D5 up to track A, which reads as a simplification and silently removes D6 and D7.

**Stimulus:**

> A codebase has exactly one `UniversalRepository` class with seven boolean parameters, per-caller exception branches for three callers, and two consumers that bypass it entirely. Elsewhere, `CanonicalMoneyParser.parse()` exists and one module reimplements the same parsing inline. Audit it.

**Assertion (PASS):** both are reported. The `UniversalRepository` finding is D7 and cites friction, not a count. The parser finding is D6 and cites the existence of a canonical owner plus one reimplementation.

**Assertion (FAIL):** either finding is dropped, downgraded, or justified with a reference to having fewer than three occurrences.
