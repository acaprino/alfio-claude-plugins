---
description: >
  Answer a question about IBKR behaviour with evidence instead of a guess.
  TRIGGER WHEN: the user asks whether IBKR supports something, why an order was refused, what a code
  means, or wants a claim about venue behaviour verified against a real gateway.
  DO NOT TRIGGER WHEN: auditing a whole codebase (use /ibkr-trading:ibkr-audit), or designing a system
  from scratch (use the ibkr-architect agent).
argument-hint: "[question, code, or contract]"
---

# IBKR Behaviour Verification

Resolve a question about how Interactive Brokers behaves, and report the answer with its provenance.

Load the `ibkr-trading` skill, then follow the ladder below **in order**, stopping at the first rung
that produces a real answer. Say which rung you stopped at. Never skip a cheaper rung to reach for a
more impressive one.

## Rung 0: is it a code?

If the question is about a message code, answer immediately, with no gateway:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/ibkr-trading/scripts/ibkr_probe.py codes <code> [<code> ...]
```

Report the grade `ib_async` assigns it, and the consequence. For an undocumented code, say so
explicitly: `ib_async` treats it as fatal and will mark a working order `Cancelled` locally without
telling the venue, so the order may still be live.

Then read `error-codes-and-verdicts.md` for which of the three layers refused: venue, terminal, or
client library.

## Rung 1: read the capability list

Most "does IBKR support X" questions are answered by `ContractDetails.orderTypes` for the contract in
question. This is free and definitive in the negative direction.

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/ibkr-trading/scripts/ibkr_probe.py capabilities --stock AAPL
```

Requires a running paper Gateway (see Rung 3 setup). Report:

- whether the token is present in `orderTypes`
- the market rule bands, if the question touches prices
- the size semantics, if the question touches quantities

**If the token is absent, stop.** The answer is no for that contract on that exchange, and no probe
will change it. A refusal is the venue declining an unsupported attribute, not a precaution to bypass.

## Rung 2: read the documentation, and quote it

Fetch the page and **quote the sentence** that answers the question, with its URL.

IBKR's documentation serves clean Markdown: append `.md` to any page URL. The index is
`https://ibkrcampus.com/docs/llms.txt`, with per-section indexes such as
`https://ibkrcampus.com/docs/tws-api/llms.txt`. The rendered HTML site returns 403 to naive fetchers,
which is bot detection and not evidence of absence; use the `.md` form, or drive a browser.

Three rules:

- **A claim you cannot locate as a sentence on the page does not exist.** If a search result asserts
  something the page does not contain, the search result is wrong and the question is still open.
- **Silence is a result.** Report "the page says nothing about this, checked today at this URL" rather
  than filling the gap with a plausible answer.
- **Never cite a forum post or an AI summary as the basis for a design decision.** They are hypotheses.

## Rung 3: probe it

When the documentation is silent or the token is present but the order is still refused, measure it.

Set up a disposable paper Gateway if one is not running:

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/ibkr-trading/scripts
python $S/ibkr_gateway.py doctor
python $S/ibkr_gateway.py install
python $S/ibkr_gateway.py configure --user <paper-username>   # export IB_PASSWORD first
python $S/ibkr_gateway.py start
```

Then pick the probe that matches the question:

| Question is about | Probe |
|---|---|
| Whether a shape is accepted | `ibkr_probe.py shape --type STP --tif GTC --attr allOrNone` |
| Which combinations work | `ibkr_probe.py matrix --types LMT,STP --tifs DAY,GTC,IOC` |
| Lifecycle, states, attachment, TIF rewriting | `ibkr_probe.py bracket --parent-tif DAY --child-tif GTC` |
| Prices, increments, size rules | `ibkr_probe.py capabilities` |

Constraints to respect and to state in the report:

- **The what-if budget is IBKR's, not ours**: at most one per minute, roughly one per ten real
  submissions. The scripts enforce the spacing; do not pass `--no-budget` without saying why.
- **Paper only.** Live ports are refused and the account prefix is re-checked after connecting. If the
  user asks to probe a live account, decline and explain that a read-only capability dump against
  their production terminal is the closest safe equivalent.
- **A `REFUSED` verdict is trustworthy for that shape. An `ACCEPTED` verdict is a credit check
  passing**, not a promise: presets and book state can still refuse the real order.

## Rung 4: report as unresolved

If none of the above settles it, say so. A clear "unresolved, and here is the measurement that would
settle it" is a better deliverable than a confident guess.

## Output

Report in this shape:

1. **Answer**, in one sentence.
2. **Provenance**: `MEASURED` (probe transcript), `DOCUMENTED` (quoted sentence and URL), or
   `UNRESOLVED`.
3. **Scope**: which contract, which order type, which account entity the answer covers. An answer
   measured on a `STP` parent says nothing about a `LMT` parent, and this must be stated, not implied.
4. **Evidence**: the quote, or the probe output, or both.
5. **What follows**: which decisions in the user's system depend on this, and whether any of them now
   rest on a premise that just changed.
6. **Residual unknowns**, if the answer is partial, each with its cheapest settling experiment.

If the verification contradicts something the user already shipped, say that plainly and first. A
decision built on a premise that has now been measured false is the most valuable output this command
can produce.
