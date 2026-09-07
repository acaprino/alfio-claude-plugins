# Case: judge-prompt-shape

Added in ai-tooling 5.3.0 from the September 2026 research integration. The judge archetype now
has its own reference with a measured default shape: one criterion per judge, a binary decision
with quoted evidence, a reference answer when a trustworthy one exists, a checklist step for
open-ended criteria, and a 0-5 scale where a scalar is needed. Three popular additions measured
as zero or negative on at least one model class: a judge persona, a debate among judges, and a
1-10 scale. The invariant is that the optimizer treats those as defects to report, decomposes the
rubric, and keeps agreement with humans predicted until kappa is measured on the caller's labels.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "You are a world-class senior technical writer with 20 years of experience judging documentation. Rate the following answer on a scale of 1 to 10 considering accuracy, completeness, clarity, tone, formatting, and whether it follows the style guide. Be very strict. Output the score and a short justification.

Question: {{QUESTION}}
Reference answer: {{REFERENCE}}
Candidate answer: {{CANDIDATE}}" --model gpt
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The archetype is classified as judge / evaluator and the judge reference is consulted; the rewrite is made for a judge, not for a generic assistant |
| 2 | MUST | The six bundled criteria are decomposed: at least one variant runs one criterion per judgment (or per call), each with its own binary satisfied / not satisfied decision and a quoted evidence span, and the variant says why (shared bias across a monolithic rubric) |
| 3 | MUST | The persona line and the 1-10 scale are each reported as a defect with its measured basis, and no variant keeps a 1-10 or 1-100 scale as the default; where a scalar survives it is 0-5 and the variant says the pooled default reverses on some benchmarks |
| 4 | MUST | The reference answer placeholder survives in every variant and is used as the reference the judge grades against; removing it is reported as a relaxation |
| 5 | MUST | The "be very strict" instruction is not carried forward on the frontier target as a quality lever; if a variant keeps it, the variant names the weaker-judge class it is measured to help and labels it a conditional fallback |
| 6 | MUST | Agreement with humans is stated as predicted until Cohen's kappa is measured on the caller's own labels, one kappa per criterion, and the delivery names that kappa as the measurement that decides whether the judge is usable |
| 7 | SHOULD | At least one variant adds a checklist step for the open-ended criteria (clarity, tone) before scoring |
| 8 | SHOULD | The response does not propose a debate among judges or a majority vote as an improvement |

## Scoring notes

Assertion 3 is the invariant most likely to fail quietly: a rewrite that keeps "1 to 10" because
"the caller's pipeline expects it" has to report the scale as an interface it preserved and name
the measured cost, not treat it as neutral. The passing shape either moves to 0-5 and reports the
interface change, or keeps 1-10 with the change flagged as a decision the caller must make.

Assertion 5 distinguishes deleting a line from understanding it. "Be very strict" helped a 27B
open judge by eleven points and moved GPT-5.4 by less than one; a variant for a GPT target that
keeps it as if it were free has not read the reference.

## Revisions

**2026-09-07, after the first run.** Assertion 6's third clause said the delivery must name
per-criterion kappa as "the first number to collect". The run named kappa as the number that
decides whether the judge is usable, and spent the word "first" on a different metric for a
different dimension. Two careful readers split on whether "first" means ordinally first in the
delivery or first among agreement numbers, which makes the clause depend on bullet ordering
rather than on substance. It now asks what the clause was reaching for. The scorer passed the old
wording on the two substantive halves and flagged the third; the recorded outcome stands, and the
new wording tests the same thing without the ambiguity.

Two clauses in this case are structurally unfalsifiable and are kept deliberately, not by
oversight. Assertion 4's "removing it is reported as a relaxation" can only fire if a variant
drops the reference placeholder, which none did; assertion 5's "if a variant keeps it" is an
escape hatch for a defensible alternative shape. Neither adds discrimination on a passing run,
and both would earn their place on a failing one.
