# Case: constraint-saturation

Added in ai-tooling 5.3.0 from the September 2026 research integration. Joint compliance with
simultaneous output constraints is multiplicative and saturates early on every model class
measured: the count at which all-constraints success fell below 50% ranged from 2 to 7 across
fifteen current models (arXiv 2608.12426). The invariant is that the optimizer counts the
constraints an output must satisfy at once and, above five, proposes a split into stages or a
verify-and-retry step as its own variant rather than tightening the wording. The second half of
the invariant is the exception: a persistent coding-agent rule file is not a set of simultaneous
output constraints (fifty rules did not collapse a coding agent, arXiv 2604.11088 v2), so the
cap must not be applied there.

## Setup

Create a scratch directory with two files.

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

## Run

Two runs, fresh session each:

```
/prompt-optimize newsletter.md --model claude
```

```
/prompt-optimize CLAUDE.md --model claude
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | On `newsletter.md`, the analysis counts the simultaneously verifiable constraints (there are ten or more) and names joint compliance, not wording, as the risk |
| 2 | MUST | On `newsletter.md`, at least one variant restructures the task into stages (draft, then verify and repair against the rule list; or generate, then a separate constraint check) or attaches a verify-and-retry step, and states what it costs in calls or latency |
| 3 | MUST | On `newsletter.md`, no variant relies on stronger phrasing (capitals, "strictly", "you must") as the fix for the constraint count, and every constraint from the original survives in every variant or is reported as relaxed in the behavioral changes |
| 4 | MUST | On `CLAUDE.md`, the optimizer does not propose cutting the rule count to satisfy a cap, does not convert the prohibitions into positive guidance, and reports that a persistent agent rule file is not subject to the simultaneous-constraint limit |
| 5 | MUST | Every quality claim about compliance is labelled predicted; no variant claims a compliance rate it has not measured |
| 6 | SHOULD | On `CLAUDE.md`, the defects hunted are conflicting or unverifiable rules, and the optimizer says the twelve rules read as guardrails, which is the rule type with measured benefit |
| 7 | SHOULD | The working threshold is stated as this plugin's synthesis of the measured curves, not as a number a paper optimized |

## Scoring notes

Assertion 2 is the invariant. A variant that keeps every rule and adds a validator or a second
pass is the passing shape; a variant that quietly drops three rules to make the prompt "cleaner"
fails assertion 3 unless the drop is reported as a relaxation the caller has to approve.

Assertion 4 is the other half. A rewrite of `CLAUDE.md` that trims it to five rules because
"models cannot follow more than five" has applied the output-constraint result to the one task
family where it was measured not to hold.
