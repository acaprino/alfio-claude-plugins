# Case 9: The agent can contradict its own index and reports it

**Guards:** `references/concept-index-protocol.md` "Contradiction is reportable."

**Why it decays:** the index is a persisted, structured artifact that looks already-verified, and a future edit optimizing for consistency across repeated runs on the same repo could let a `settled` `canonical_owner` stand unchallenged rather than being re-proven against current source every time. That is precisely the self-corroboration this repository's epistemic-independence doctrine exists to prevent: a shared artifact cannot be allowed to vouch for itself.

**Stimulus:**

> The concept index records `canonical_owner: {"status": "settled", "symbol": "PricingEngine"}` for a pricing concept. Current source shows three separate modules now write to the price: `PricingEngine`, `PromotionsService`, and an inline calculation in `CheckoutController`, none of which defers to the others. Audit the change.

**Assertion (PASS):** the finding is reported as a competing-authority defect, since the settled owner is in fact contested, and Gaps states plainly that the index was wrong.

**Assertion (FAIL):** the agent treats `PricingEngine` as the settled owner and does not report the other two writers, or it silently updates its own understanding without stating in Gaps that the index disagreed with what it found.
