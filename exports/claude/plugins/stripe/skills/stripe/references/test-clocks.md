# Test Clocks

Simulate subscription lifecycle (trials, renewals, dunning, proration) in test mode by advancing a clock instead of waiting real time.

## When to use

- Writing tests for trial-end, renewal, or failed-payment flows without stubbing the Stripe SDK.
- Reproducing a customer bug ("my subscription charged twice on upgrade") under controlled conditions.
- Validating dunning email cadence (3-day, 7-day, final notice).

Skip for unit tests of your own handler logic -- mock the Stripe event there. Test clocks are integration-level.

## Gotchas

- **Test mode only.** Clocks don't exist in live mode. Get a dedicated test-mode account or a sandbox account for this.
- **Advance triggers async work.** `TestClock.advance` returns immediately with status `advancing`; events fire as Stripe processes. Poll the clock (or subscribe to `test_helpers.test_clock.ready`) before asserting side effects.
- **Advance window cap: ~2 billing periods at a time.** For a monthly sub, you can advance ~60 days per call; chain calls for longer simulations.
- **3 customers per clock, 3 subscriptions per customer.** Plan scenarios around this.
- **Clocks auto-delete after 30 days.** Don't persist clock IDs in long-running fixtures.
- **Attach at creation.** `Customer.create(test_clock=clock.id)` -- you can't attach a clock to an existing customer.
- **Webhooks fire normally.** Test-clock-driven events still hit your webhook endpoints; makes them great for end-to-end webhook tests against a local `stripe listen`.

## Relevant webhook events

- `test_helpers.test_clock.advancing` -- advance started
- `test_helpers.test_clock.ready` -- advance finished, safe to assert
- Plus all the normal events (`invoice.payment_failed`, `customer.subscription.trial_will_end`, etc.) triggered by the simulated time jump

## Official docs

- Overview: https://docs.stripe.com/billing/testing/test-clocks
- Simulate subscriptions step-by-step: https://docs.stripe.com/billing/testing/test-clocks/simulate-subscriptions
- Advanced API usage (canonical code samples): https://docs.stripe.com/billing/testing/test-clocks/api-advanced-usage
- API reference: https://docs.stripe.com/api/test_clocks

## Related

- `simulate_subscription.py` -- runnable script that exercises a full lifecycle
- `subscription-patterns.md` -- lifecycle concepts being simulated
- `webhooks-production.md` -- handling the events that test clocks fire
