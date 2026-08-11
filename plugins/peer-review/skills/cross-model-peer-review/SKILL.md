---
name: cross-model-peer-review
description: >
  Doctrine for putting a plan or spec in front of a second model family: when the cost is earned, the GIVEN versus DERIVED provenance rules, when to skip it.
  TRIGGER WHEN: running or configuring /peer-review:review, deciding whether an artifact warrants external challenge, or interpreting a verdict's standoffs and promotions.
  DO NOT TRIGGER WHEN: reviewing code diffs (use senior-review), or running same-family multi-reviewer pipelines (use senior-review:review-quality-gates).
---

# Cross-Model Peer Review

The protocol is the product, this plugin is its Claude Code implementation. The
normative text is `${CLAUDE_PLUGIN_ROOT}/protocol/PROTOCOL.md`: harness-independent,
provider-independent, its requirement numbers stable identifiers that this skill and
every agent in this plugin cite by number rather than restate loosely. Read it before
touching a run that behaves unexpectedly; this skill explains why the rules exist and
when to reach for the command at all, not what each phase does mechanically.

## The doctrine

Two statements govern everything else in the protocol. Both are quoted verbatim from
`PROTOCOL.md`'s Doctrine section and R14.

> Cross-family independence is the strongest practical model-level independence
> available in this workflow, not absolute independence. Two frontier participants may
> share a training corpus, conventions, and reasoning patterns. What makes a second
> participant worth its cost is that its errors are sufficiently decorrelated, not that
> it is a clean-room observer.

A second model is not oracle, not a clean room, and not free of the anchoring risk of
having read the same packet the first model wrote in spirit. It is worth running
because its errors are unlikely to be the same errors, not because it is independent
in any absolute sense. Run it for decorrelation, not for purity.

> Within a participant's contribution, repeating a GIVEN fact corroborates nothing. The
> rule is about the act, not the fact: a participant that independently reaches the
> authoritative source and verifies the fact there has derived it, and the ledger
> records the promotion GIVEN -> DERIVED with the deriving role and locator, after which
> it counts. Agreement produced by reading the packet back never counts.

This is the provenance rule that keeps the ledger honest. A fact enters a run as
**GIVEN** (supplied by the packet), **TO JUDGE** (submitted for evaluation, most
notably a considered-and-rejected rationale), or **DERIVED** (established by a
participant's own access to the authoritative source, most notably the respondent's
repository access under R8). A GIVEN fact stays GIVEN, however many times it is
repeated inside one contribution, until a participant reaches the source itself and
the ledger records the promotion with the deriving role and a locator. Reading the
packet back and calling it verification is the single most common way a run's evidence
looks stronger than it is.

## The six hardening rules

Each rule targets one specific way a two-participant debate degrades into theater.

| Failure mode | What protects against it | Requirement |
|---|---|---|
| Anchoring on the packet builder's framing | A rejection rationale enters the packet flagged TO JUDGE, never GIVEN, so the challenger owes it scrutiny instead of deference; the first challenge round opens with a frame challenge (is the mandate the right question, is the decomposition natural) before a single finding is raised | R3, R6 |
| Strategic packet omission | Ground truth and constraints are built by mechanical extraction: naming a source in the artifact is what earns it a place, never a relevance judgment made by the packet builder. The packet builder must also name at least three genuine weaknesses of its own artifact. The challenger can request more context, and every refusal is recorded and surfaced in the verdict rather than silently dropped | R3, R6 |
| False falsifiers | Every falsifier is checked for admissibility, decidable against the source, decidable in bounded effort, actually dispositive, before any investigation starts. One that still fails after a single restatement request terminates UNTESTABLE rather than being forced toward ACCEPT or REFUTE either way | R9 |
| Debate laundering | A finding's claim and falsifier travel verbatim through the whole ledger; the challenger certifies the proposed terminal state of its own findings before the verdict and can flag a misrepresentation by quoting its own original words against the respondent's rendering; the verdict itself is computed from the ledger and prose may only explain a state, never assign one | R10, R12, R13 |
| Premature convergence | A refutation requires positive evidence at a stable locator, never absence of evidence standing in for one; a withdrawal that names no falsifying evidence does not close its finding and is reported as a run weakness regardless of outcome; a run with findings can never terminate after round one, and saturation is a mechanical same-claim-same-evidence-same-position test, never a shortcut taken because the round is running long | R7, R11 |
| Transmission fidelity | The packet records the artifact's byte length and content digest, and the verdict verifies source, packet embedding, and outgoing request are byte-identical before any finding is trusted; a finding attacking material genuinely absent from the source terminates TRANSMISSION_ARTIFACT and the run is repeated rather than the finding being judged on its merits | R15 |

## When not to run a review

A run costs a transmission of real bytes to an external service and several rounds of
model time. Three situations do not earn that cost:

- **The artifact is too vague to attack.** A packet built from a vague plan produces
  ground truth with nothing pinned down and findings that stand on air; the challenger
  ends up debating what the artifact might mean instead of whether it holds up.
  Sharpen the plan or spec into decidable claims first, then run the review.
- **The decision was already made for reasons outside the artifact.** The protocol
  judges the artifact, never its author (R1). It also has no way to weigh a
  constraint that is not written down, so the reasoning behind the decision goes
  unjudged too. Record the outside reason directly instead of asking a challenger to
  attack a document that cannot represent it.
- **The target is a diff.** This plugin reviews plans and specs, not code changes; the
  command itself refuses anything that looks like a unified diff or a source file.
  `senior-review` owns diff and PR review.

## Relationship to senior-review

`senior-review:review-quality-gates` states the same rule this skill's doctrine states,
one level up: evidence derived from a shared context artifact cannot independently
corroborate a claim contained in that same artifact, so N reviewers agreeing on a
premise they were all given is one observation, not N. That rule guards against shared
context collapsing independence **across reviewers** inside one review pipeline. R14
above guards against the identical collapse **across the two participants of one
debate**. Same failure mode, different multiplicity; neither plugin depends on the
other to enforce it.
