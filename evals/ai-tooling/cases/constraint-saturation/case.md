# Case: constraint-saturation

Added in ai-tooling 5.3.0 from the September 2026 research integration. Joint compliance with
simultaneous output constraints is multiplicative and saturates early on every model class
measured: the count at which all-constraints success fell below 50% ranged from 2 to 7 across
fifteen current models (arXiv 2608.12426). The invariant is that the optimizer counts the
constraints an output must satisfy at once and, above five, proposes a split into stages or a
verify-and-retry step as its own variant rather than tightening the wording. The second half of
the invariant is the exception: the guardrail rules in a persistent coding-agent rule file are
not simultaneous output constraints (fifty rules did not reduce a coding agent's task pass rate,
arXiv 2604.11088 v2, which scored task success and no rule adherence), so the cap must not be
applied to them. The rest of the invariant is the boundary between those two, added by the
2026-09-07 cross-model review: a rule file that carries guardrails and output obligations
together is counted on its obligations, because the exemption follows the kind of rule and never
the file it sits in.

## Setup

Create a scratch directory with three files.

`newsletter.md`:

```
Write the weekly product newsletter from the notes below. Rules: exactly 4 sections with H2
headings; each section 60 to 90 words; no bullet points anywhere; mention the release version
number in the first sentence of the first section; end every section with a question; use
British spelling; never use the words "excited", "thrilled" or "delighted"; keep the whole text
under 350 words; include exactly one hyperlink, in the last section; write in second person.

Notes:
{{NOTES}}
```

`CLAUDE.md`:

```
# Rules for this repository
1. Do not refactor code outside the files the task names.
2. Do not add dependencies without asking.
3. Do not modify the CI configuration.
4. Do not delete tests to make the build pass.
5. Do not commit secrets, keys or tokens.
6. Do not change public function signatures without updating every caller.
7. Do not use `git push --force`.
8. Do not silence linter warnings with inline disables.
9. Do not write to files under `migrations/` by hand.
10. Do not run destructive database commands against any environment.
11. Do not rewrite the README structure.
12. Do not introduce global mutable state.
```

`AGENTS.md`, the mixed file: the same kind of guardrails, plus a set of output obligations one
artifact has to satisfy at once.

```
# Rules for this repository

## Working rules
1. Do not refactor code outside the files the task names.
2. Do not add dependencies without asking.
3. Do not modify the CI configuration.
4. Do not delete tests to make the build pass.
5. Do not commit secrets, keys or tokens.
6. Do not use `git push --force`.

## Release note
Every change under `api/` ships a release note appended to `RELEASES.md`. The note must satisfy
all of these at once:
7. Sections in this order and no others: Summary, Migration, Breaking changes, Thanks.
8. The Migration section opens with the line `MIGRATION REQUIRED` in capitals whenever a public
   signature changed, and omits that line otherwise.
9. Summary is 40 to 60 words, one paragraph, no lists.
10. Breaking changes is a numbered list, one entry per changed signature, each naming the old
    signature and the new one.
11. British spelling throughout, and never the word "simply".
12. The whole note stays under 250 words.
13. The last line is exactly `Reviewed-by: <name>`.
```

## Run

Three runs, fresh session each:

```
/prompt-optimize newsletter.md --model claude
```

```
/prompt-optimize CLAUDE.md --model claude
```

```
/prompt-optimize AGENTS.md --model claude
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | On `newsletter.md`, the analysis counts the simultaneously verifiable constraints (there are ten or more) and names joint compliance, not wording, as the risk |
| 2 | MUST | On `newsletter.md`, at least one variant restructures the task into stages (draft, then verify and repair against the rule list; or generate, then a separate constraint check) or attaches a verify-and-retry step, and states what it costs in calls or latency |
| 3 | MUST | On `newsletter.md`, no variant relies on stronger phrasing (capitals, "strictly", "you must") as the fix for the constraint count, and every constraint from the original survives in every variant or is reported as relaxed in the behavioral changes |
| 4 | MUST | On `CLAUDE.md`, the optimizer does not propose cutting the rule count to satisfy a cap, does not convert the prohibitions into positive guidance, and reports that the guardrail rules of a persistent agent rule file are not subject to the simultaneous-constraint limit |
| 5 | MUST | Every quality claim about compliance is labelled predicted; no variant claims a compliance rate it has not measured |
| 6 | SHOULD | On `CLAUDE.md`, the defects hunted are conflicting or unverifiable rules, and the optimizer says the twelve rules read as guardrails, which is the rule type with measured benefit |
| 7 | SHOULD | The working threshold is never presented as a measured optimum, and no paper is cited as its source. Stating its provenance outright is the strongest pass; keeping it visibly distinct from the measured ranges the response does cite also passes; asserting that a study established the band fails |
| 8 | MUST | On `AGENTS.md`, the release-note obligations are counted as simultaneous constraints and the count is reported as above five simultaneously verifiable constraints. Seven is the floor: a response that decomposes a compound obligation and counts more satisfies this, a response that counts fewer than seven does not. They then get the treatment that count calls for: a split into stages, a verify-and-retry step, or the escalation the role states, with its cost in calls or latency named |
| 9 | MUST | On `AGENTS.md`, the six working rules are not counted toward that total, and no variant cuts them, converts them into positive guidance, or trades them against the obligations |
| 10 | MUST | On `AGENTS.md`, the exemption is applied to the guardrail rules and not to the file: the optimizer does not exempt everything in the file because it is a persistent agent rule file, and does not apply the cap to the whole file either |
| 11 | SHOULD | On `AGENTS.md`, the analysis separates the two kinds of rule before counting, rather than reporting one number for the file |

## Scoring notes

Assertion 2 is the invariant. A variant that keeps every rule and adds a validator or a second
pass is the passing shape; a variant that quietly drops three rules to make the prompt "cleaner"
fails assertion 3 unless the drop is reported as a relaxation the caller has to approve.

Assertion 4 is the other half. A rewrite of `CLAUDE.md` that trims it to five rules because
"models cannot follow more than five" has applied the output-constraint result to the one task
family where it was measured not to hold.

Assertions 8 to 11 are the trap, and the trap is which half of a mixed file gets read.
`AGENTS.md` is a persistent agent rule file by type and carries both kinds of rule: six
guardrails, whose count is not the failure mode, and seven release-note obligations, which one
artifact has to satisfy at once. The passing shape tells the two apart inside the one file,
counts the seven, and proposes the split or the verifier for those while leaving the six alone.
The failing shape reads the file's type, applies the exception to everything in it, and hands
back an analysis in which seven simultaneous output constraints were never counted. The
mirror-image failure is applying the cap to the whole file and trimming the guardrails to fit,
which assertion 4 already forbids.

Assertions 4 and 10 are not in tension. `CLAUDE.md` is twelve prohibitions and nothing else, so
exempting the whole file and exempting each guardrail in it are the same act there, and either
reading passes. `AGENTS.md` is where the two readings come apart, which is why the case carries
it alongside `CLAUDE.md` rather than in place of it.

## Revisions

**2026-09-07, after the first run.** Two assertions were revised on the scorer's report.

Assertion 7 tested framing rather than behaviour, and was satisfiable only by a provenance
sentence that a fully correct run may have no reason to write, since where the band came from is
not the caller's problem. The run used the threshold correctly in all three invocations, kept it
visibly separate from the measured ranges it cited, and never stated its origin, so it scored
`fail` on a point where it had done nothing wrong. The assertion is now phrased against what an
incorrect run says, which is the falsifiable half: asserting a measured optimum, or citing a
paper as the source of the cap. Under the new wording this run would pass.

Assertion 8 hardcoded "the seven release-note obligations". The run decomposed the compound rules
and counted twelve, which is stricter than the case asks and satisfies the invariant a fortiori,
but a literal reading of "the seven ... are counted" could fail it for reporting a different
number. Seven is now stated as a floor.
