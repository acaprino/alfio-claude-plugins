# Finding Lifecycle

One entry per finding, carried by ID. The claim and falsifier are verbatim for the
whole run (R10).

## States

| State | Terminal | Meaning |
|---|---|---|
| OPEN | no | raised, not yet answered |
| CHALLENGED | no | answered; the challenger has not yet replied or a closure was invalidated |
| RESOLVED_ACCEPT | yes | respondent accepted; becomes a concrete edit in the verdict |
| RESOLVED_REFUTE | yes | refuted with positive evidence satisfying the falsifier as stated |
| RESOLVED_WITHDRAWN | yes | challenger withdrew, naming the evidence that falsified it |
| STANDOFF | yes | both substantive positions survive the available evidence |
| UNTESTABLE | yes | falsifier inadmissible after one restatement (R9) |
| TRANSMISSION_ARTIFACT | yes | the finding attacks material absent from the source (R15) |
| CERTIFICATION_FAILED | yes | closure invalidated at certification, no round budget left (R12) |

STANDOFF is reserved for substantive survival. A procedural failure routes to
UNTESTABLE, TRANSMISSION_ARTIFACT, or CERTIFICATION_FAILED, never to STANDOFF.

## Transitions

- OPEN -> CHALLENGED: the respondent answers with ACCEPT, REFUTE, NEEDS-EVIDENCE, or
  DISAGREE, plus evidence at a locator for every non-ACCEPT verdict.
- CHALLENGED -> RESOLVED_*: the challenger concedes (naming the falsifying evidence)
  or the respondent accepts.
- CHALLENGED -> STANDOFF: evidence saturation, or the round cap (labeled
  cap-terminated).
- any non-terminal -> UNTESTABLE: falsifier fails admissibility twice.
- any -> TRANSMISSION_ARTIFACT: the attacked material is absent from the source at
  the recorded digest.
- proposed RESOLVED_REFUTE -> CHALLENGED: substantiated MISREPRESENTED flag at
  certification. One corrective round if budget remains, else CERTIFICATION_FAILED.
- A withdrawal that names no falsifying evidence does not close the finding: it stays
  CHALLENGED and the verdict reports the unexplained withdrawal as a run weakness.

## Saturation test (mechanical, run per finding per round)

new evidence since previous round = NO on both sides
AND both positions unchanged
=> STANDOFF now. No further rounds for this finding.

## Ledger entry template

```
Finding F<NN>
  claim (verbatim): <...>
  falsifier (verbatim): <...> | admissibility: OK | RESTATED | INADMISSIBLE
  challenger evidence: <...>
  respondent position: ACCEPT | REFUTE | NEEDS-EVIDENCE | DISAGREE
  respondent evidence: <locator>
  restatements: none | RESTATED AS "<...>" confirmed by challenger in R<N>
  state: <one of the nine states>
  new evidence since previous round: YES | NO
```
