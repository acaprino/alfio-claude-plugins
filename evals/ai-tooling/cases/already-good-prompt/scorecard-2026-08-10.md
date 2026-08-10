<!-- Scorecard produced by an independent judge that read only this case file and the
candidate output. It could not read plugins/ai-tooling/, so it judged the output against the
assertions rather than against the implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.0 working tree (NOT the installed plugin, which
  was 4.1.0 on this machine; see the run note in RESULTS.md)
- **How the component was exercised:** a fresh subagent adopted the 5.0.0 component body from the
  working tree and received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: already-good-prompt

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | **fail** | See below |
| 2 | MUST | **fail** | See below |
| 3 | MUST | **pass** | See below |
| 4 | SHOULD | **fail** | See below |

**MUST passed: 1 / 3**

**Verdict: FAIL**

---

## Assertion 1 (MUST) — fail

The output does not take the "no material optimization warranted" branch. It opens with `**Headline finding: this prompt is already good.**` but then ships a rewrite that grows the prompt from `~130` to `~330` estimated tokens and adds five behaviors. So it must clear the second branch: every proposed change justified against a named defect.

Most changes do clear it. D1 (`total_cents` has no defined unit`), D2 (`Trust boundary is undeclared.`), D3 (`issue_date has no disambiguation rule, while total_cents does.`), D4 (`"No preamble" is one-sided.`), D5 (`The invoice boundary is undefined.`), D6 (`Schema literal mixes two notations.`) and D7 (`Multiple invoices in one file.`) are each named, and D1 in particular is argued to a concrete failure (`JPY 99,000 could return 9900000 or 99000`). That is genuine defect-driven work, not manufactured churn.

But the assertion is scoped to **only** changes justified against a named defect, and three changes in Variant A are not.

1. **Reorganization justified purely as structure.** Section 3's rationale says:

   > "Rules are split into field rules and document rules so the classification and trust instructions are not buried among per-field mechanics."

   No defect is named. This is the exact fail condition the assertion spells out.

2. **A worked example added with no defect behind it.** Variant A inserts:

   > "Example of a well-formed output:
   > {"invoice_number": "INV-2025-0042", "issue_date": "2025-03-04", "total_cents": 123456, "currency": "EUR"}"

   Its only justification is placement, not a defect:

   > "The example output object sits immediately after the schema, which is where a format anchor does the most work for determinism."

   The output's own diagnosis contradicts the need for it:

   > "Anti-patterns from the catalog: none present. No vague instructions, no contradictions, no over-constraining, no emphasis escalation, no missing output anchor."

   The case's scoring notes name "adding few-shot examples that were not needed" as churn to fail on. Variant B compounds it with "two worked examples".

3. **Two added behaviors that appear in the rewrite but in no diagnosis item.** The `invoice_number` disambiguation rule ("Not a PO number, order number, customer number, or account number.") and the currency rule ("If a symbol is ambiguous on its own ("$" with no country or code stated anywhere in the document), use null.") both surface in the semantic diff as additions:

   > "Behaviors:    added: a present-but-ambiguous currency symbol resolves to null"
   > "Behaviors:    added: issue_date and invoice_number carry disambiguation rules against neighbouring fields"

   D3 names only `issue_date`. No D-item names `invoice_number` or `currency`.

Three of the four churn patterns in the scoring notes were avoided: `total_cents` was not renamed, the JSON block was not converted to prose, and no reasoning scaffold was added (section 4 refuses one explicitly). The fourth was hit.

## Assertion 2 (MUST) — fail

Only one variant is offered as text (Variant A, section 3). C and B exist only as rows in the frontier table. Variant A does not preserve the schema or two of the three rules.

**JSON schema — changed.**

Original:

```
{"invoice_number": string, "issue_date": "YYYY-MM-DD", "total_cents": integer, "currency": "ISO 4217 code"}
```

Variant A:

```
{"invoice_number": string|null, "issue_date": string|null, "total_cents": integer|null, "currency": string|null}
```

Every one of the four type positions is rewritten. `"YYYY-MM-DD"` and `"ISO 4217 code"` are deleted from the schema outright and relocated into prose rules. The output states the intent plainly: "the schema stays a one-line type map ... and formats moved into the rules, which resolves D6 without losing the format signal." Relocating them is still not surviving unchanged.

**Rule 1 — changed.** Original: `Use null for any field not present in the document. Never infer a missing value.` Variant A: `Use null for any field the document does not state. Never infer or guess an absent value.` Both clauses reworded.

**Rule 2 — survives.** `if several totals appear, use the one labeled as the amount due.` appears verbatim inside the `total_cents` field rule, and the output flags this deliberately: "The `total_cents` tie-break keeps the original's exact wording, because it is contract behavior and it was already clear." This is the one element of the four that is fully intact.

**Rule 3 — changed.** Original: `If the document is not an invoice, return {"error": "not_an_invoice"}.` Variant A: `If the document is not an invoice, output {"error": "not_an_invoice"} and nothing else. An invoice is a document requesting payment...` The verb changed and a scope clause plus a definition were appended.

**Field names — survive.** `invoice_number`, `issue_date`, `total_cents`, `currency`, and the `{"error": "not_an_invoice"}` object are all present with identical spelling.

**`{{DOCUMENT}}` placeholder — survives.** Verbatim, inside identical `<document>` / `</document>` tags.

The output's own semantic diff claims:

> "Interface:    unchanged: four keys, the error object, the {{DOCUMENT}} placeholder and the <document> tags are all preserved byte-for-byte"

That claim is true as written, because it is scoped to keys and tags. It is not the assertion's claim. The schema line and two of three rules are not preserved. To the output's credit the rule edits are disclosed rather than smuggled ("Constraints:  strengthened: ..."), but disclosure is not preservation.

## Assertion 3 (MUST) — pass

Both elements are recorded as caller-relied behavior in the extracted contract, before any change is proposed.

> "**Hard constraints** | JSON only, no preamble. Exact key names and types. `null` for absent fields, never inferred. Non-invoice yields exactly `{"error": "not_an_invoice"}`."

> "**Behavioral invariants** | Multiple totals resolve to the one labeled as amount due. Absence is reported, not filled. The error branch short-circuits extraction."

> "Renaming any of these breaks the caller as thoroughly as deleting it."

Neither is treated as a gap. The never-infer stance is treated as binding precedent when resolving a new case: "I chose null, which is consistent with the prompt's existing "never infer" stance." D5 questions *which documents* trip the escape, not the escape itself, and defers rather than resolving: "this one is genuinely ambiguous rather than simply missing, so per my contract discipline I am not resolving it silently".

## Assertion 4 (SHOULD) — fail

Half the assertion holds. Over-constraint is explicitly ruled out: "no over-constraining". Output determinism does score high on the original:

> "| Output determinism | 4 | 5 | Schema and no-preamble were present; exactly-one-object and no-fence were not. |"

Constraint correctness does not:

> "| Constraint correctness | 3 | 5 | No contradictions originally; the unit rule was simply absent. |"

3 out of 5 is the midpoint, not a high score, and the stated reason for the deduction is a missing rule rather than an incorrect constraint. The note concedes the constraints were correct ("No contradictions originally") and then marks the dimension down anyway for a completeness gap that D1 already carries.

---

## Observations

The near miss is assertion 1, and it is close. The output is far from the pathology the case guards against: it names the prompt as already good up front, refuses a reasoning scaffold with an argument rather than by omission ("any in-prompt scaffold ... would put the prompt in direct conflict with itself"), lists the anti-patterns that are absent, offers a max-efficiency pole, and pushes four additions into an explicit sign-off list. D1 is a real and well-argued defect that a careless reviewer would miss. What fails it is the "only" quantifier: one restructuring justified by clarity alone, one unneeded example, and two behaviors that reach the rewrite without a diagnosis entry.

Assertion 2 is the unambiguous failure and does not turn on judgment. The output preserves the *interface* byte-for-byte and says so accurately, but the assertion covers the schema literal and the three rule sentences, and those were rewritten. Notably the rewrite is transparent about it, which means this is a scope failure rather than a silent-drift failure. If the intended invariant is narrower (keys, placeholder, and the semantics of the three rules survive, wording may be tightened), the case wording should say so; as written, "survive unchanged" is what was checked and it does not hold.

Assertion 4 reads more like a preference than an invariant. "Score high" has no defined threshold, and the output's constraint-correctness 3 rests on a defensible if arguable reading. It is a SHOULD and does not move the verdict, but a rubric with a stated pass line would make it scoreable rather than judgeable.

One thing worth flagging that no assertion covers: the output cites reading `plugins\ai-tooling\agents\prompt-engineer.md` and `plugins\ai-tooling\references\reasoning-patterns.md`, and several sections lean on those files ("The reference's decision guide", "Self-Consistency at N=10 measures at roughly 119 tokens per accuracy point"). Those claims were not verified here, per the hard constraint against reading under `plugins/`.
