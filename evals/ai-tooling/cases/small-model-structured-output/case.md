# Case: small-model-structured-output

Added in ai-tooling 5.2.0 from the September 2026 refresh. On a small open-weight model a format
instruction is the weakest form of enforcement and, measured, often no enforcement at all: output
validity is the first failure on that class, before accuracy. The invariant is that the optimizer
names the enforcement rung each variant assumes (format instruction only, instruction plus
validate-and-repair, API structured outputs, constrained decoding in the serving stack) and never
presents "respond only with JSON" as sufficient on that target.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "Read the customer email below and return a JSON object with the fields intent (one of: refund, cancel, question, complaint), order_id (string or null), and urgency (low, medium, high). Respond only with JSON.

Email:
{{EMAIL}}" --model gemma-3-4b
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The target is classified as a small open-weight model and the recommendations are made for that class; a rewrite that reasons as if the target were a frontier API model (structured-outputs parameter, last-turn prefill unavailable, effort settings) fails |
| 2 | MUST | Every variant states the enforcement rung it assumes, and no variant treats the "respond only with JSON" instruction as the enforcement by itself: at least validate-and-repair, or constrained decoding through the serving stack, is named as what makes the shape hold |
| 3 | MUST | The mechanism outside the prompt (a validator with a retry, a grammar or JSON-schema setting in the serving stack) is placed next to the prompt as a setting, not written into the prompt as more words |
| 4 | MUST | The four `intent` values, the three `urgency` values and the `null` option for `order_id` appear unchanged as literals in every variant. Reformatting the schema around them (spacing, quoting style, key order) is not a change to them |
| 4b | MUST | Every interface-visible change the rewrite makes to the template (a field name, a label value, a delimiter, a pinned key order, what the caller must interpolate) is reported as an interface change |
| 5 | MUST | Compliance is stated as predicted until measured, with the parse-failure rate named as the first number to collect and the wrong-but-valid rate beside it, since a schema catches a malformed object and not an obligation it does not express |
| 6 | SHOULD | If any variant asks the model to reason before answering, the reasoning is placed before the JSON or in a separate call, never inside the JSON object |
| 7 | SHOULD | The response notes that a Gemma 3 chat template has no system role, so a system-style instruction belongs in the first user turn |

## Scoring notes

Assertion 2 is the invariant. A variant may keep "respond only with JSON" as a courtesy to the
model; it fails only when that line is what the response relies on for compliance. The passing
shape names the rung and its cost ("constrained decoding through the `format` parameter: the
schema holds, at some latency; reasoning inside the constrained call is not available").

Assertion 3 separates a setting from a prompt edit. Writing "validate the JSON and retry" inside
the prompt tells the model to do something it cannot do; the validator is the caller's code.

## Revisions

**2026-09-07, after the first run.** Assertion 4 was split in two on the scorer's report.

Its first clause said the label sets "survive byte-identical" without naming the unit of
comparison. All three variants of the run reformatted the schema line while leaving every label
literal untouched, so a reader taking the line as the unit fails it and a reader taking the
literals as the unit passes it. It now names the literals, which is what the clause was always
about.

Its second clause was vacuous as written: it fired only if a field name or label value changed,
and none did, so it was never exercised. The behaviour it reaches for, that an interface change
is reported rather than made quietly, is now assertion 4b and is phrased against changes a
correct rewrite does make. The run reported its delimiter and key-order changes, so it would
pass 4b, but that was not tested at the time and 4b carries no outcome for this run.
