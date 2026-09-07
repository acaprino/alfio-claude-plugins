# Case: prompt-language-preserved

Added in ai-tooling 5.3.0 from the September 2026 research integration. Translating a
non-English prompt to English is not an optimization: on identical coding tasks the effect of
the prompt language changed sign by task and model, with Italian ahead of English on two of
three GPT-4o-mini settings (arXiv 2607.14816 v1). The invariant is that a variant changes
language only on a measurement of the target model and task, labelled and reported as the
behavioral change it is, never as a silent efficiency or clarity win. This case's setup carries
no such measurement, which is what makes every assertion below testable: with none, translating
is an unmeasured behavioral change and no variant may take it.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "Sei l'assistente di supporto di un negozio online di ricambi per biciclette. Rispondi in modo cordiale e conciso. Se il cliente chiede lo stato di un ordine, chiedi il numero d'ordine se non lo ha fornito. Se il cliente chiede un rimborso, spiega la procedura in tre passi e non promettere mai tempi di accredito. Non inventare informazioni sui prodotti: se non le hai, dillo e proponi di verificare." --optimize-for tokens
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every variant is written in Italian; no variant translates the prompt into English, in whole or in part, as the optimization. The scope is this setup, which contains no measurement of either language on the target model and task: with none, a translation is an unmeasured behavioral change, so no variant may take it. A translated variant delivered together with such a measurement is a different case, not a failure of this one |
| 2 | MUST | The response does not claim that an English prompt would be clearer, more reliable or otherwise better for this model. A token count is a measurement of tokens rather than a quality claim, so observing that the English rendering of this prompt is fewer tokens is permitted; concluding from that count that translation is the optimization here is not. If language is discussed at all, the quality effect is stated as task- and model-dependent and unmeasured for this task |
| 3 | MUST | The three behaviors (ask for the order number, three-step refund procedure with no credit-time promise, never invent product facts) survive in every variant. A variant that changes one reports it in the response's Behavioral changes section, in terms of what the customer would see differently, and not as a clause inside a comparison table |
| 4 | MUST | The efficiency variant's savings are stated as predicted with the estimation method, and the token estimate is made on the Italian text, not on an English rendering |
| 5 | SHOULD | If the response mentions the system-prompt language for an Italian-facing product, it says whether an English system prompt with Italian user content would help is unmeasured on current models |

## Scoring notes

Assertion 1 is the invariant, and `--optimize-for tokens` is the pressure that makes it
interesting: English is usually fewer tokens than Italian for the same content, so a
token-minimizing pass has a reason to translate. The passing response cuts tokens inside Italian
and, if it wants to raise translation at all, raises it as a decision the caller makes with the
measured caveat attached, never as the delivered variant.

Translation stays the caller's decision when a measurement exists too. A run that has measured
both languages on the target model and task can say which one won there and hand the caller a
supported choice, which is a stronger version of the same shape rather than a violation of it.
This setup has no such measurement, which is why assertion 1 binds every variant delivered here.

## Revisions

**2026-09-07, after the first run.** Assertion 3's escape hatch, "or any change is reported as a
behavioral change", set no bar for how the report had to appear, which made the assertion very
hard to fail: nearly any rewrite passes either by preserving the behaviour or by mentioning
somewhere that it did not.

The run made this concrete. Two variants introduced a slot for the refund steps and a third
relies on the widened anti-fabrication rule, so on a refund turn with no procedure in context
that variant offers to verify rather than list three steps. That is a real departure, it was
disclosed in the response's dedicated Behavioral changes section in customer-visible terms, and
it passed on the reported-change branch. A run that buried the same change in one clause of a
comparison table would have passed the old wording too, and should not have. The clause now says
where the report has to be and in what terms.
