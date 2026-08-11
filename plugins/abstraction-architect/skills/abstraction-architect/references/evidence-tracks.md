# Evidence Tracks

Two kinds of evidence support a structural finding, and they are not interchangeable. Getting the wrong one produces either a noisy report or an empty one.

**The track determines the nature of the evidence. The dimension determines the gate.**

Track membership does not by itself impose a count. This is the single most common misreading, and it is worth stating twice: being on track A does not mean "three or more occurrences". Only D5 uses the Rule of Three as a strict gate.

| Track | Question it answers | Failure it guards against |
|---|---|---|
| A, form | Does the same *mechanism* recur, and would unifying it pay? | Extracting a shape from a sample of two and getting the wrong abstraction |
| B, knowledge | Does the same *fact* have more than one authoritative representation? | Two owners of one truth drifting apart, where waiting for a third is meaningless |

## Why the Rule of Three does not cover both

The Rule of Three protects against one specific risk: extracting a shape too early, with a sample of two, and producing an abstraction whose shape is anchored to a coincidence. It says nothing about the opposite risk, which is knowledge with two authoritative representations.

`references/theory.md` states the underlying reason: DRY targets duplicated *knowledge*, not duplicated lines. Two competing authorities over the same fact is already the defect. There is no third occurrence to wait for, and waiting produces exactly the drift the principle exists to prevent.

The Rule of Three therefore returns to its original meaning here: a gate that justifies **creating a new unification**, not a universal filter for the form family.

## Track A: form

Applies to D5 missed unification, D6 prior art available, D7 abstraction fitness.

```
A1  Same structural responsibility?
A2  Same lifecycle and boundary?
A3  Occurrences per the dimension's own rule
    D5: three or more independent occurrences (Rule of Three)
    D6: one canonical implementation plus at least one reimplementation or bypass
    D7: no count at all; friction inside a single abstraction is the evidence
A4  Would one shared abstraction reduce change cost?
A5  Is the divergence unlikely to be intentional?
```

Gate A3 is where the per-dimension rule enters. A D7 candidate that fails A3 because it has only one occurrence has been judged against the wrong rule: a wrong abstraction is a single object, and counting copies of it is a category error.

L3, bounded context, is an important lens on track A but not an absolute gate. Two contextually separate implementations may still legitimately share an infrastructural mechanism such as a retry policy or a logging facade.

## Track B: knowledge

Applies to D1 duplicated domain knowledge, D2 competing sources of truth, D3 redundant representation, D4 duplicated or derivable state.

Two representations are sufficient evidence. In exchange, the semantic proof is much stricter than a count.

```
K1  Same semantic fact?
K2  Same domain meaning?
K3  Same lifecycle?
K4  Same authority scope?
K5  If the fact changes, are both expected to remain consistent?
K6  Is there no legitimate bounded-context reason for divergence?
```

K6 is a **hard gate** on this track. A candidate that cannot demonstrate K6 is not reported. A candidate whose context membership could not be determined is reported with `Bounded-context exception: unverified`, and `references/decision-frame.md` governs how far it may then be promoted.

Failing to demonstrate any of K1 through K6 means no finding. Silence is the correct output when the proof is not there.

## The discriminating question

Every track B candidate resolves to one question, and it is the fastest route to the answer:

> **Can these representations legitimately disagree?**

If yes, this is not duplicated knowledge, whatever the surface similarity. If no, and they must stay consistent, two representations are enough.

Worked contrast:

```
Billing.REFUND_DAYS = 30            Shipping.Status: PENDING/COMPLETE/FAILED
Support.refundAllowed = age <= 30   Payment.Status:  PENDING/COMPLETE/FAILED

Can they legitimately disagree?     Can they legitimately disagree?
No. One policy, two owners.         Yes. Same shape, different knowledge.
FINDING (D1 or D2).                 NO FINDING.
```

The left column has no textual similarity and is a finding. The right column is textually identical and is not. A detector that matches on shape gets both backwards, which is precisely why this file exists.

## What the report must show

Every finding carries the track it was judged on and the gate results, so a reader can see why it was admitted:

```
Evidence track: KNOWLEDGE            Evidence track: FORM
Semantic identity: proven            Occurrences: 4
Occurrences: 2                       Independent implementations: yes
Must remain consistent: yes          Shared lifecycle: yes
Bounded-context exception: none      Rule of Three: satisfied
Canonical owner: ambiguous           Index-seeded: no
Index-seeded: <yes|no>
```
