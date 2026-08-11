# Case 5: The index is never the sole evidence for a finding

**Guards:** `references/concept-index-protocol.md` epistemic status: "Index entries nominate search targets; current source code proves findings."

**Why it decays:** the index is already a structured, pre-digested artifact, and under time or token pressure it is faster to cite it directly than to reopen the files it points at. A future edit optimizing diff-mode latency on large repositories is the likeliest place this shortcut gets taken, especially since a stale index usually still looks plausible.

**Stimulus:**

> The concept index records `RefundPolicy` as the settled canonical owner of the refund window, with `evidence` pointing at `domain/refund_policy.py`. Current source shows that file was deleted last week, and the refund window is now only defined inline in two call sites. Audit the change that removed it.

**Assertion (PASS):** no finding cites the index entry as evidence for `RefundPolicy` still being the owner. The contradiction, the index says settled while current source shows the file is gone, is reported in Gaps.

**Assertion (FAIL):** a finding treats the index's `canonical_owner` as current fact, or reports `RefundPolicy` as the owner without noting the file no longer exists.
