# Case 4: One defect gets one primary dimension

**Guards:** `references/dimensions.md` "Single primary classification" and the precedence ordering.

**Why it decays:** a reviewer trained to be thorough will notice that a single defect genuinely satisfies several dimensions' proof rules at once, and reporting it under each one feels like completeness rather than the report bug the plugin explicitly names as its failure mode. A future edit chasing recall could turn "report the deepest reason" back into "report every reason that applies."

**Stimulus:**

> A refund window is duplicated in three modules. One of the three, `RefundPolicy`, reads as the intended canonical source, but the other two never call it. Audit it.

**Assertion (PASS):** exactly one finding, classified D2 competing sources of truth, since no module is actually settled as the owner despite `RefundPolicy` looking canonical. The D1 (duplicated knowledge), D5 (three occurrences) and D6 (prior art bypassed) readings appear as supporting evidence inside that one finding, not as separate findings.

**Assertion (FAIL):** two or more findings are opened for the same defect, under any combination of D1, D2, D5 or D6.
