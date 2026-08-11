# Cross-Model Peer Review Protocol

Version: 1.0.0
Status: normative. Requirement numbers are stable identifiers; binding documents cite them.

This protocol is harness-independent and provider-independent. No requirement names a
tool, a vendor, a model, or a transport. A conforming implementation supplies a binding
document stating, for each requirement, the concrete mechanism that satisfies it.

The deliverable of a run is not a review. It is a reduction in decisional uncertainty:
accepted changes, evidence-backed refutations, and precise standoffs for a human to
settle. Finding count is never a quality measure.

## Vocabulary

- **artifact**: the intent document on trial (a plan or a spec).
- **packet**: the self-contained challenge brief built from the artifact.
- **packet builder**: the role that constructs the packet.
- **challenger**: the role that attacks the artifact. It sees only the packet plus any
  granted amendments.
- **respondent**: the role that answers findings with evidence from the authoritative
  source.
- **authoritative source**: the repository or corpus the artifact is about.
- **GIVEN**: a statement supplied to a participant by the packet.
- **TO JUDGE**: a statement the packet explicitly submits for evaluation.
- **DERIVED**: a statement a participant established through its own access to the
  authoritative source.
- **ledger**: the run state carrying every finding verbatim from birth to terminal state.

## Requirements

### R1. Roles, not identities
A run has four roles: artifact, packet builder, challenger, respondent. The proposer
(whoever wrote the artifact) is out of scope: the protocol judges the artifact, never
its author. No rule may condition on which vendor, model, or person fills a role.

### R2. Artifact immutability
The artifact does not change during a run. Accepted changes are applied after the
verdict. A changed artifact means a new run.

### R3. Packet contract
The packet is immutable once sent and contains, in order: Mandate; Artifact (verbatim,
with byte length and content digest); Ground truth (source facts with locators, each
flagged GIVEN); Constraints; Considered and rejected (each entry split into a decision,
flagged GIVEN, and a rationale, flagged TO JUDGE); Known weaknesses of this artifact
(written against the builder's own side); Open questions; Out of scope; Response
contract. Material named by the artifact enters by mechanical extraction: judgment
controls how much of each source, never which sources.

### R4. Provenance, recorded on four axes
Each role's provenance is recorded on four separate axes: model, runtime, context,
human. The axes are never collapsed into one label and never scored. When challenger
and respondent are both model-based, decorrelation SHOULD hold on the model axis at
minimum; when a role is filled by a human, the model axis is absent and the requirement
falls on the remaining axes. A participant whose context axis is packet-only can still
derive consequences from the artifact, but it has no independent path to the
authoritative source and therefore can never promote a GIVEN source fact to DERIVED.

### R5. Egress consent
The packet is the complete set of bytes leaving the local environment. Before any
transmission the operator is shown its size, its section list, and the destination,
and gives explicit consent. A dry-run mode MUST exist that builds the packet and stops
without any transmission.

### R6. Challenge contract
The first challenge round contains, in order: a frame challenge (is the mandate the
right question, is the decomposition natural, which rejection rationale fails), before
any finding; context requests by locator; findings, capped, each carrying claim,
section attacked, failure scenario, severity, and falsifier; a cannot-assess section;
a strongest-objection section. Praise, restating the artifact, and generic advice are
banned.

### R7. Positive evidence
A refutation requires positive evidence at a stable locator in the authoritative
source. Absence of evidence is not a refutation: absence and contradiction are
different states. A refutation must satisfy the finding's falsifier as stated, not a
weaker restatement of it. No concession without verification; no defensiveness either.

### R8. Respondent inspection
The respondent MUST be capable of inspecting the authoritative source material needed
to evaluate the challenger's claims. The mechanism is binding-specific. A respondent
whose context axis is packet-only does not conform.

### R9. Falsifier admissibility
Before investigation, each falsifier is checked: decidable against the authoritative
source or a runnable procedure, decidable in bounded effort, and actually dispositive
for the claim. An inadmissible falsifier earns one restatement request; if still
inadmissible, the finding terminates as UNTESTABLE, which is neither accepted nor
refuted and is reported separately.

### R10. Verbatim carry
A finding's claim and falsifier travel verbatim through the ledger for the whole run.
Any restatement is labeled as such and must be confirmed by the challenger before it
can support a refutation.

### R11. Mechanical termination
A run terminates when all findings are terminal, or by evidence saturation (same
claim, same evidence, same positions across a round set STANDOFF for that finding
immediately), or at the round cap (remaining findings become STANDOFF, labeled
cap-terminated). A run with findings never terminates after the first challenge round.
STANDOFF means exactly one thing: both substantive positions survive the evidence
available at termination. Procedural failures never produce it.

### R12. Certification
Before the verdict, the challenger sees the proposed terminal state of its own
findings and may flag one as MISREPRESENTED, quoting its original text against the
respondent's rendering. A substantiated flag is a procedural failure of the
refutation: it invalidates the proposed closure, strikes the restatement, and reverts
the finding to CHALLENGED. If the round budget allows, one corrective round runs
against the original claim; otherwise the finding terminates as CERTIFICATION_FAILED,
neither accepted nor refuted, reported separately. A misrepresentation never
manufactures a standoff. An unsubstantiated flag is discarded.

### R13. Ledger-computed verdict
The verdict is computed from the ledger, never written freehand. Prose may explain a
state; it may never change one. The verdict reports, at minimum: accepted changes,
refutations with evidence, standoffs with what would settle each, untestable findings,
certification failures, transmission artifacts, unexplained withdrawals (reported as a
weakness of the run), refused context requests, the four-axis provenance of each role,
and any GIVEN -> DERIVED promotions.

### R14. Repetition of a GIVEN is never independent corroboration
Within a participant's contribution, repeating a GIVEN fact corroborates nothing. The
rule is about the act, not the fact: a participant that independently reaches the
authoritative source and verifies the fact there has derived it, and the ledger
records the promotion GIVEN -> DERIVED with the deriving role and locator, after which
it counts. Agreement produced by reading the packet back never counts.

### R15. Source-to-request transmission fidelity
The challenger judges the packet, never the artifact. The packet records the
artifact's byte length and content digest, and the verdict verifies that the source
document, the packet embedding, and the outgoing request are byte-identical. What the
remote participant internally perceived is unverifiable by construction; the guarantee
deliberately stops at the request boundary. A finding attacking material absent from
the source terminates as TRANSMISSION_ARTIFACT, neither accepted nor refuted, reported
separately so the run is repeated rather than trusted.

## Doctrine

Cross-family independence is the strongest practical model-level independence
available in this workflow, not absolute independence. Two frontier participants may
share a training corpus, conventions, and reasoning patterns. What makes a second
participant worth its cost is that its errors are sufficiently decorrelated, not that
it is a clean-room observer.
