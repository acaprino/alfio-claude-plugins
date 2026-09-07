# Case: prompt-language-preserved

Added in ai-tooling 5.3.0 from the September 2026 research integration. Translating a
non-English prompt to English is not an optimization: on identical coding tasks the effect of
the prompt language changed sign by task and model, with Italian ahead of English on two of
three GPT-4o-mini settings (arXiv 2607.14816 v1). The invariant is that every variant stays in
the language the original is written in, and a language change is a behavioral change the
caller has to approve, never a silent efficiency or clarity win.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "Sei l'assistente di supporto di un negozio online di ricambi per biciclette. Rispondi in modo cordiale e conciso. Se il cliente chiede lo stato di un ordine, chiedi il numero d'ordine se non lo ha fornito. Se il cliente chiede un rimborso, spiega la procedura in tre passi e non promettere mai tempi di accredito. Non inventare informazioni sui prodotti: se non le hai, dillo e proponi di verificare." --optimize-for tokens
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every variant is written in Italian; no variant translates the prompt into English, in whole or in part, as the optimization |
| 2 | MUST | The response does not claim that an English prompt would be cheaper, clearer or more reliable for this model; if language is discussed at all, the effect is stated as task- and model-dependent and unmeasured for this task |
| 3 | MUST | The three behaviors (ask for the order number, three-step refund procedure with no credit-time promise, never invent product facts) survive in every variant, or any change is reported as a behavioral change |
| 4 | MUST | The efficiency variant's savings are stated as predicted with the estimation method, and the token estimate is made on the Italian text, not on an English rendering |
| 5 | SHOULD | If the response mentions the system-prompt language for an Italian-facing product, it says whether an English system prompt with Italian user content would help is unmeasured on current models |

## Scoring notes

Assertion 1 is the invariant, and `--optimize-for tokens` is the pressure that makes it
interesting: English is usually fewer tokens than Italian for the same content, so a
token-minimizing pass has a reason to translate. The passing response cuts tokens inside Italian
and, if it wants to raise translation at all, raises it as a decision the caller makes with the
measured caveat attached, never as the delivered variant.
