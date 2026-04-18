---
description: >
  Reply to a customer review with sentiment analysis, adaptive tone, and operational suggestions.
  TRIGGER WHEN: the user pastes a customer review (Airbnb, Booking, Amazon, Trustpilot, App Store, Google) and asks for a reply or response.
  DO NOT TRIGGER WHEN: writing general marketing copy (use content-marketer) or responding to code review comments.
argument-hint: "\"<review text>\" [--brand <name>] [--tone formal|friendly|casual] [--lang <code>] [--sector hospitality|ecommerce|auto]"
---

# Reply to Customer Review

## Invocation

Invoke the `reply-to-customer-review` skill and follow its full workflow.

## Arguments

- `<review text>`: The customer review to respond to (paste inline or provide after invocation)
- `--brand "Name"`: Business name to use in the response sign-off
- `--tone`: Response tone -- `formal`, `friendly`, or `casual` (default: professional-empathetic, mapped to `friendly`)
- `--lang`: Force output language using ISO code (default: same language as the review)
- `--sector`: Force sector specialization -- `hospitality`, `ecommerce`, or `auto` for auto-detection (default: auto)

If invoked without arguments, prompts the user to paste a review.

## Examples

```
/reply-to-customer-review "Camera sporca e personale scortese. Mai piu." --brand "Villa Serena" --tone friendly
/reply-to-customer-review The app crashes every time I try to checkout. Uninstalling.
/reply-to-customer-review --lang en "Prodotto arrivato rotto, assistenza inesistente"
/reply-to-customer-review "Amazing stay! The view was breathtaking and the host was incredibly welcoming." --brand "Casa Luna"
```

## What it does

1. Analyzes the review: language, sentiment, severity, key points, sector
2. Generates an adaptive response calibrated to the review's tone and content
3. Outputs the response (ready to copy), analysis summary, and operational suggestions
4. Accepts follow-up refinements: "more formal", "shorter", "in English", etc.
