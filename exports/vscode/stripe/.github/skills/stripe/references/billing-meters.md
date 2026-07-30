# Billing Meters (Usage-Based Billing)

Modern usage-based billing primitive. The legacy `usage_type=metered` + `SubscriptionItem.create_usage_record` flow was **removed** in API version `2025-03-31.basil`. On any newer version, metered prices must be backed by a Meter.

## When to use

Bill by API calls, seats, GB stored, generated tokens, or any metric that aggregates per billing period. Skip if you bill a flat subscription or per-item one-off charges -- a plain `Price` is enough.

## The 3-object mental model

1. **Meter** -- defines an `event_name` and aggregation (`sum`, `count`, `last_during_period`). The `max` aggregation from the legacy API has no equivalent.
2. **Price** -- a recurring Price with `recurring.meter` pointing at the meter ID.
3. **MeterEvent** -- reported as usage happens, identified by `stripe_customer_id` in the payload (not subscription-item id like the legacy API).

## Gotchas

- **Idempotency is explicit via `identifier`.** Always send one; Stripe dedupes `(event_name, identifier)` pairs. Retries without an identifier double-count.
- **Backfill window is ~35 days.** Later corrections need `MeterEventAdjustment` with `type=cancel`.
- **`event_name` is immutable** after creation. Pick stable domain nouns (`api_request`, `seat`, `gb_stored`).
- **Events for customers without an active meter-backed subscription are accepted but not invoiced.** Useful for "report early, bill later" flows.
- **High throughput (>1k events/sec)** uses the V2 `/v2/billing/meter_events` stream; trades sync validation for up to 10k/sec.
- **Webhooks worth subscribing to:** `v1.billing.meter.error_report_triggered` (validation failures), `v1.billing.meter.no_meter_found` (typos in event_name).

## Migration from legacy usage records

Map `SubscriptionItem.create_usage_record(si_xxx, quantity=150, ...)` to `stripe.billing.MeterEvent.create(event_name=..., payload={stripe_customer_id, value: "150"}, identifier=...)`. Key differences: customer-addressed instead of subscription-item-addressed, explicit `identifier` instead of implicit timestamp idempotency, no `max` aggregation. For in-flight subscriptions, use subscription schedules to phase onto the meter-backed price at period end.

## Official docs

- Overview: https://docs.stripe.com/billing/subscriptions/usage-based
- Implementation guide (canonical code samples): https://docs.stripe.com/billing/subscriptions/usage-based/implementation-guide
- Recording usage: https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api
- Migration from legacy: https://docs.stripe.com/billing/subscriptions/usage-based-legacy/migration-guide
- API reference (Meter): https://docs.stripe.com/api/billing/meter
- API reference (MeterEvent): https://docs.stripe.com/api/billing/meter-event
- Breaking change notice: https://docs.stripe.com/changelog/basil/2025-03-31/deprecate-legacy-usage-based-billing

## Related

- `webhooks-production.md` -- `v1.billing.meter.*` events
- `usage-revenue-modeling.md` -- modeling usage distributions for pricing
