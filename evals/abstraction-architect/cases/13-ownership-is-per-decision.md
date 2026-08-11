# Case 13: Canonical ownership can be assigned per decision, not only per file

**Guards:** the recentering spec's per-decision ownership rule (`docs/superpowers/specs/2026-08-10-abstraction-architect-recentering-design.md`), `references/decision-frame.md` D2 remediation framing ("Name the canonical owner first").

**Why it decays:** "name the canonical owner" reads naturally as naming one document or one module in full, and a source-ranking heuristic, prefer the more recent source, the more specific one, the one closer to the code, is the obvious-looking way to pick that single owner when two sources disagree. This case exists because that exact situation happened during this recentering's own implementation: two specifications each got one fact of the same contract right, and picking a winner by ranking would have discarded a fact the loser owned correctly.

**Stimulus:**

> Two authoritative specifications both describe the same CLI command's `validate` output. The first correctly matches the surrounding codebase's convention for output format, but omits a schema field the command is required to emit. The second correctly specifies the required field, but also specifies an output format that is incompatible with the rest of the codebase. Audit the contract.

**Assertion (PASS):** classified D2 competing sources of truth, with a remediation that assigns ownership per decision: the first specification is authoritative for output format, the second is authoritative for the required field, stated explicitly as a split rather than a single winner.

**Assertion (FAIL):** any of three outcomes: classified as D1 or D3 instead of D2, since duplication is the symptom and contested ownership is the actual defect; one specification declared authoritative in full, discarding the fact the other one owns correctly; or the conflict resolved by a source-ranking heuristic such as preferring the more recent, the more specific, or the one closer to the code, which is the degeneration this case exists to prevent.
