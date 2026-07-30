# Decision Frame

The operational classifier the auditor uses to promote a candidate to a finding. Use it as a checklist. If a candidate fails any of the gates, it does not become a high-severity finding.

This file is the load-bearing filter between "suspicion" and "report". The auditor will see many code shapes that resemble missed unification or wrong abstraction. The job of this frame is to drop the false positives, calibrate severity on the survivors, and force every promoted finding to carry the evidence that justifies its category and level.

The flow is fixed:

1. Run the pre-flight questions in order.
2. If any pre-flight question disqualifies the candidate, drop it or downgrade to Low.
3. If the candidate survives, calibrate severity using the risk categories below.
4. Apply the false-positive gates as a final safety net before writing the finding into the report.

## Pre-flight questions (run in order)

1. **When this concern changes, where do I have to touch?** Count the call sites. If N grows linearly with features, this is a unification candidate. If N stays at 1, this is already a layer and there is nothing to promote.

2. **Has this pattern appeared three or more times?** The Rule of Three. Two is coincidence; three is a pattern. A finding with fewer than three sites is downgraded to Low or omitted. This is the single most common reason to drop a candidate.

3. **Will the two sites realistically diverge under future requirements?** If yes, the duplication is essential to the design, not accidental. Leave it. Examples of essential divergence: two retry policies serving different SLOs; two `User` models in different bounded contexts; two pagination encoders for an internal API versus a public API.

4. **Are these sites in different bounded contexts?** If yes, do not unify even when the code looks identical today. Bounded-context fusion is the most expensive form of wrong abstraction because it leaks domain concerns across team boundaries and turns every future change into a multi-team coordination problem. When in doubt, ask whether the two sites are owned by the same team and serve the same business question; if not, leave them duplicated.

5. **Does every new feature add a flag, branch, or parameter to a shared layer?** If yes, the layer is a wrong abstraction. The growth pattern of a healthy abstraction is "callers use it as-is and the layer rarely changes". The growth pattern of a wrong abstraction is "every caller pushes another knob onto the layer". Look at the layer's commit history: if its parameter list keeps growing without a clear shape, the layer has been forced to host concerns that want to live elsewhere.

6. **Can a future reader understand a call site without chasing definitions across files?** Locality of Behaviour gate. If no, the abstraction has a hidden cognitive cost that may outweigh the deduplication value. Weigh that cost against the change-coupling benefit. A layer that saves 50 lines of duplication but forces every reader to traverse four files to understand one call site is a net loss for the codebase.

## Severity calibration

Default to **Medium**. Escalate or de-escalate only when the evidence supports it. Reserve High for findings you can argue for in one paragraph; reserve Low for code smells with no concrete pressure.

- **High** when the missed unification or wrong abstraction creates:
  - **Security risk**: duplicated authorization checks, scattered token storage, inconsistent input validation, ad-hoc CSRF or rate-limit handling.
  - **Data-correctness risk**: money arithmetic, date and timezone handling, currency conversion, monotonic identifiers, decimal precision policies.
  - **Operational risk**: multiple incompatible retry policies on the same external service, inconsistent error handling for the same failure mode, scattered timeout and backoff configurations.

- **Medium** (default) when the pattern creates maintenance drag (god service, flag soup, premature interface, leaky abstraction) but no immediate failure mode. The cost is paid in slow change velocity and onboarding friction, not in production incidents.

- **Low** when the pattern is a code smell with no concrete pressure to fix it now. Example: a strategy-pattern-for-two-strategies that is stable, small, and not on a hot change path. Flagging is informational; the user may close the finding without acting.

## Gates against false positives

These gates run after severity calibration and decide what actually appears in the report.

- **Rule of Three downgrade.** Findings citing fewer than three sites under unification are auto-downgraded to Low or omitted. This applies even when the code looks visually similar; two sites are not enough evidence to promote a unification candidate.
- **Single-source-file confidence flag.** Findings whose evidence comes from a single deep-dive file are marked Medium-confidence in the report. A finding that depends on `01-structure.md` alone has less weight than one corroborated by `03-flows.md` plus `04-semantics.md`.
- **Bounded-context-unverified flag.** Findings where the bounded-context check has not been performed must be explicitly flagged: "context-membership unverified". This is honest about the limitation: if the auditor cannot tell from deep-dive output whether two sites live in the same domain, the user must verify before acting on the suggested direction.
