# Decision Frame

What happens **after** a candidate has passed its dimension's gate: whether it is promoted, at what severity, and how the remediation is framed.

This file does not restate the gates. Track A gates `A1` to `A5` and track B gates `K1` to `K6` live in `references/evidence-tracks.md`, and duplicating them here would create two authorities over one rule, which is the D2 defect this plugin exists to find.

## Promotion

A candidate becomes a finding when all three hold:

1. **Its dimension's gate passed**, per `references/evidence-tracks.md`.
2. **Every cited representation has been read against current source.** A finding whose prior art you have not opened and compared is not reportable. Near-identical names routinely hide different behaviour, and an index entry is a search target rather than a proof.
3. **The lenses have been applied and recorded**, per `references/dimensions.md`. A lens does not veto, with one exception: an L2 verdict of "consolidating adds a hop and saves nothing" changes the suggested direction rather than the finding.

A candidate that fails any of the three is dropped. Silence is the correct output when the proof is not there.

## Severity calibration

Default to **Medium**. Escalate or de-escalate only when the evidence supports it. Reserve High for findings you can argue for in one paragraph. Reserve Low for smells with no concrete pressure.

**Severity follows consequence, never occurrence count.** There is no mapping of the form two equals Low, three equals Medium. Two independent authoritative permission policies can be High on two occurrences; four duplicated formatting constants can be Low on four.

- **High** when the finding creates:
  - **Security risk**: duplicated authorization rules, scattered token handling, an eligibility predicate that guards access and disagrees with itself, competing authorities over a permission fact.
  - **Data-correctness risk**: money arithmetic, rounding or pricing sequence, date and timezone handling, derivable state with repair code, two authorities over a value that reconciliation depends on.
  - **Operational risk**: incompatible retry or timeout policies on the same dependency, a status vocabulary that drifts between a producer and a consumer, a transition rule enforced in one path and not another.
- **Medium**, the default, when the finding creates maintenance drag: a mechanism repeated three times, a layer that is accumulating flags, a redundant representation with a real but bounded mapping cost. The cost is paid in change velocity, not in incidents.
- **Low** when the pattern is a smell with no concrete pressure. A stable strategy-for-two on a cold path. A second occurrence noted so the third is recognisable.

## Confidence

Severity says how much it matters. Confidence says how sure you are, and they are reported separately.

- **High confidence**: every cited representation was read on current source, and the dimension gate passed on evidence from more than one signal.
- **Medium confidence**: the gate passed but one input was unavailable, for example a missing X-ray file or an `unusable` concept index.
- **Low confidence**: a single signal, worth manual verification. Say what would raise it.

Two flags are mandatory when they apply, because they mark the failure modes that cost the most:

- **`Bounded-context exception: unverified`** when context membership could not be determined. On track B this caps the finding at Low confidence and it is never promoted above Medium severity, because unifying across a context boundary is the most expensive wrong move available.
- **`Index-seeded: yes`** when a concept index entry pointed at the evidence. This is provenance, not a quality signal, and nothing in the report or in any consuming pipeline may reward it.

## Remediation framing

`Suggested direction` names the target layer or the move in one sentence. It is not a refactoring plan, a file list or a migration sequence.

Frame it with L4, the option price, when the recommendation is contested:

> The upfront cost of unifying these three sites is one module plus indirection at each call site. The future value is that a threshold change becomes one edit rather than three, and finance has changed it twice this year. Recommendation: unify.

Frame the reverse the same way. An abstraction whose expected value no longer covers its cost gets an inline recommendation, and the intermediate state is supposed to look worse than both endpoints.

Match the remediation to the dimension. This is the difference between an actionable finding and a shallow one:

| Dimension | The move |
|---|---|
| D1 | Give the knowledge one authoritative statement, then have the others call it |
| D2 | Name the canonical owner first. Extracting a helper before ownership is settled adds an authority |
| D3 | Collapse the representations, or document the boundary that justifies keeping them |
| D4 | Derive instead of storing, or make one copy authoritative and the other a cache with a stated invalidation rule |
| D5 | Design the shared mechanism |
| D6 | Migrate to the canonical implementation and delete the reimplementation |
| D7 | Inline the abstraction back to its call sites, then redesign from what they reveal |
