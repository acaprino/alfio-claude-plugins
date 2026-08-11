# abstraction-architect evals

Thirteen behavioural invariants. This plugin has no ground-truth bug list to measure recall against, so these assert the **philosophy** the 2.0 recentering installed, in the same shape as `evals/ai-tooling/`.

Two standing rules, inherited from that harness:

- **Assertions target the philosophy, never the wording.** A case fails when the behaviour is gone, not when a sentence was rephrased.
- **A case that fails once keeps its case forever.** Cases are never retired for being green.

Source spec: `docs/superpowers/specs/2026-08-10-abstraction-architect-recentering-design.md`.

## Why these thirteen

Each one guards a mechanism that a well-meaning future edit removes without noticing. Cases 1 and 2 guard the two-track model, which reads like an inconsistency to anyone who has just learned the Rule of Three. Cases 9 and 10 come from the epistemic-independence doctrine and guard the concept index against becoming a self-confirming truth. Cases 11 and 12 guard the two mechanisms this recentering exists to break: a diff extractor that only sees code shapes, and a catalog that quietly becomes the boundary of the findable. Case 13 comes from a live incident during this recentering's own implementation, where two authoritative specifications each owned one fact of the same contract correctly: it guards per-decision ownership against collapsing into a source-ranking heuristic ("prefer the more recent, the more specific, the one closer to the code"), the plausible-looking shortcut that would throw away whichever document happened to lose the ranking.

## Running

Each case states a stimulus and an assertion. Run the stimulus against the installed plugin, then score against the assertion. Record results in a dated copy of `scorecard-template.md`.

**Verify the installed version first.** `evals/ai-tooling/RESULTS.md` records a sweep that was nearly invalidated by scoring a stale install. Check that the installed `abstraction-architect` is the version under test before scoring anything.
