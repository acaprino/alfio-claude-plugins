# Case 7: The five excluded dimensions never produce an autonomous finding

**Guards:** `references/scope-boundaries.md` "Excluded dimensions and their owners."

**Why it decays:** dependency cycles, god classes, and oversized public APIs are exactly what a generically competent reviewer flags on reflex, and they are real, valid observations. A future edit that blends this agent's judgement with general code-quality instincts, or a prompt change aimed at catching more, reintroduces one of them as a standalone finding without anyone noticing it duplicates a dimension `senior-review` already owns.

**Stimulus:**

> A codebase has an obvious circular dependency between two modules, a class with a dozen unrelated responsibilities, and a public API surface with forty exported functions where five would do. None of these three, on its own, involves a concept represented, owned, computed or implemented more than once. Audit it.

**Assertion (PASS):** none of the three is reported as its own finding. Any of them may appear as supporting evidence inside a D1 to D7 finding, or in Cross-Reviewer Notes.

**Assertion (FAIL):** a standalone finding reads "circular dependency between X and Y," "this class has too many responsibilities," or "the public API surface is too large."
