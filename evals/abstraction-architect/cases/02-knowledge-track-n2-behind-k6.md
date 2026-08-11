# Case 2: The knowledge track admits two representations, gated by K6

**Guards:** `references/evidence-tracks.md` Track B and gate K6, `references/dimensions.md` D1.

**Why it decays:** the Rule of Three is the plugin's best-known idea, and a reviewer who has just internalized it will read "two representations are sufficient evidence" on Track B as an inconsistency rather than a deliberate second rule. A future editor smoothing that apparent inconsistency could either raise Track B's admission count to match Track A, silently deleting real duplicated-knowledge findings until a phantom third occurrence shows up, or drop K6 entirely and admit any two representations that merely look alike, flooding the report with legitimately divergent vocabularies such as status enums that happen to share member names.

**Stimulus:**

> A codebase has `Billing.REFUND_DAYS = 30` and `Support.refundAllowed = age <= 30` in the same billing context. Elsewhere, `Shipping.Status` and `Payment.Status` both define `PENDING`, `COMPLETE` and `FAILED`, but shipping and payment are separate bounded contexts with independent lifecycles. Audit it.

**Assertion (PASS):** the refund pair is reported as duplicated domain knowledge (D1) on Track B, admitted on two representations, with K6 demonstrated: the policy must remain consistent and no bounded context justifies the divergence. The two status enums are not reported: they share a shape but fail K6, since shipping and payment may legitimately disagree.

**Assertion (FAIL):** the refund pair is rejected for having only two occurrences, the status enums are reported because their members match, or both pairs are reported, or neither is.
