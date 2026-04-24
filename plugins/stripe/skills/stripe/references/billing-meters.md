# Billing Meters (Usage-Based Billing)

Stripe's current usage-based billing primitive. Replaces the legacy `usage_type=metered` + `create_usage_record` flow, which was **removed** in Stripe API version `2025-03-31.basil`.

If you are still on API version `2025-02-24.acacia` or earlier, your old integration keeps working, but any new work must use Meters.

## Mental model

Three objects, in this order:

1. **Meter** (`stripe.billing.Meter`) -- defines an event name (e.g. `api_request`) and an aggregation formula (`sum`, `count`, `last_during_period`). One meter per metric you bill on.
2. **Price** -- a recurring Price with `recurring.meter` pointing at the meter ID. This is how a subscription knows "charge against this meter".
3. **Meter Event** (`stripe.billing.MeterEvent`) -- reported as the customer uses the feature. Stripe aggregates events against the meter for each billing period.

The Subscription ties it together: attach the meter-backed Price to a Subscription Item, and Stripe invoices based on aggregated meter events.

## Create a meter

```python
import stripe
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
stripe.api_version = "2026-04-22.dahlia"

meter = stripe.billing.Meter.create(
    display_name="API requests",
    event_name="api_request",
    default_aggregation={"formula": "sum"},
    customer_mapping={
        "event_payload_key": "stripe_customer_id",
        "type": "by_id",
    },
    value_settings={"event_payload_key": "value"},
)
```

- `event_name` is the key you'll send with each meter event. Keep it stable; you can't change it later.
- `formula` options: `sum` (add values), `count` (count events, value ignored), `last_during_period` (take the latest value -- useful for seats).
- `customer_mapping.event_payload_key` is the field in each event payload that identifies the customer. Almost always `stripe_customer_id`.

## Create a meter-backed price

```python
price = stripe.Price.create(
    product="prod_xxx",
    currency="eur",
    recurring={
        "interval": "month",
        "meter": meter.id,
        "usage_type": "metered",
    },
    billing_scheme="per_unit",
    unit_amount_decimal="0.10",  # 0.10 cents per unit (1/1000th of a euro)
    lookup_key="api_request_metered_monthly",
)
```

For tiered/graduated pricing:

```python
tiered = stripe.Price.create(
    product="prod_xxx",
    currency="eur",
    recurring={"interval": "month", "meter": meter.id, "usage_type": "metered"},
    billing_scheme="tiered",
    tiers_mode="graduated",
    tiers=[
        {"up_to": 1000, "unit_amount_decimal": "0"},        # free bucket
        {"up_to": 10000, "unit_amount_decimal": "0.05"},    # 0.05c / unit
        {"up_to": "inf", "unit_amount_decimal": "0.02"},    # 0.02c / unit
    ],
)
```

Attach to a subscription the same way as any other price:

```python
stripe.Subscription.create(
    customer="cus_xxx",
    items=[{"price": price.id}],
)
```

## Record usage (meter events)

### Single event

```python
import time

stripe.billing.MeterEvent.create(
    event_name="api_request",
    payload={
        "stripe_customer_id": "cus_xxx",
        "value": "1",         # string, matches `value_settings.event_payload_key`
    },
    identifier="req_2026_04_24_abc123",  # for idempotency (see below)
    timestamp=int(time.time()),
)
```

```typescript
await stripe.billing.meterEvents.create({
  event_name: 'api_request',
  payload: {
    stripe_customer_id: 'cus_xxx',
    value: '1',
  },
  identifier: 'req_2026_04_24_abc123',
  timestamp: Math.floor(Date.now() / 1000),
});
```

### Idempotency via `identifier`

The `identifier` field is meter-scoped idempotency. Stripe dedupes events with the same `(event_name, identifier)` pair. Always send one -- use your application's request ID, message ID, or a hash of the operation. Without it, a retry will double-count usage.

### Bulk / high-throughput (V2)

For volumes > 1,000 events/sec, use the V2 Meter Event Stream endpoint (`/v2/billing/meter_events`). V2 accepts up to 10,000 events/sec on live mode (200k+ via sales contact) and validates asynchronously, trading sync validation errors for throughput. Reach for V2 when batch-reporting from a queue; stick with V1 `MeterEvent.create` for direct per-request reporting.

### Backfill and late events

- Stripe accepts `timestamp` up to **35 days** in the past (inside the billing window).
- Events outside the current billing period land in the historical usage and surface via the Meter Usage Analytics API, but won't re-open a closed invoice.
- For after-the-fact corrections, use `stripe.billing.MeterEventAdjustment.create` with `type=cancel` to void a previously reported event by its identifier.

## Webhook events

Meters emit their own events. Handle these in the webhook receiver:

- `billing.meter.created` / `billing.meter.updated` / `billing.meter.deactivated` -- lifecycle
- `v1.billing.meter.error_report_triggered` -- a reported event failed validation (bad customer id, wrong event name, etc.). Monitor this in production.
- `v1.billing.meter.no_meter_found` -- you sent an event for an `event_name` that has no meter. Alerting on this catches typos fast.

```python
if event["type"] == "v1.billing.meter.error_report_triggered":
    errors = event["data"]["object"]["validation_errors"]
    # log, page, or feed into a DLQ
```

## Migration from legacy usage records

Legacy shape:

```python
# OLD -- removed in 2025-03-31.basil
price = stripe.Price.create(
    product="prod_xxx",
    recurring={"interval": "month", "usage_type": "metered"},
    billing_scheme="per_unit",
    unit_amount=10,
)
stripe.SubscriptionItem.create_usage_record(
    "si_xxx",
    quantity=150,
    timestamp=int(time.time()),
    action="increment",
)
```

New shape, same billing behavior:

```python
# NEW
meter = stripe.billing.Meter.create(
    display_name="API requests",
    event_name="api_request",
    default_aggregation={"formula": "sum"},
    customer_mapping={"event_payload_key": "stripe_customer_id", "type": "by_id"},
    value_settings={"event_payload_key": "value"},
)
price = stripe.Price.create(
    product="prod_xxx",
    recurring={"interval": "month", "meter": meter.id, "usage_type": "metered"},
    billing_scheme="per_unit",
    unit_amount_decimal="0.10",
)
# Instead of create_usage_record per subscription item:
stripe.billing.MeterEvent.create(
    event_name="api_request",
    payload={"stripe_customer_id": "cus_xxx", "value": "150"},
    identifier="usage_2026_04_24_cus_xxx",
)
```

Key differences:

| Aspect | Legacy (removed) | Meters |
|--------|------------------|--------|
| Addressing | SubscriptionItem id | Customer id (via `stripe_customer_id`) |
| Aggregation | Specified on price (`sum` or `max`) | Specified on meter (`sum`, `count`, `last_during_period`) -- no `max` |
| Idempotency | Implicit via `timestamp` + `action` | Explicit via `identifier` |
| Reporting before subscription | Not allowed | Allowed (event queues until subscribed) |
| Throughput | Per-item REST call | V2 stream supports up to 10k/sec |

### Migration recipe for existing subscriptions

1. For each legacy metered price, create an equivalent meter + meter-backed price with the same `unit_amount`.
2. Use subscription schedules to phase existing customers onto the new price at the end of their current billing period -- cutting mid-period causes proration weirdness.
3. Stop calling `create_usage_record` for migrated subscriptions; start calling `MeterEvent.create` instead. A short overlap window reporting to both is safe if the new price isn't active yet.
4. After all subs are migrated, archive the legacy price (`stripe.Price.modify(..., active=False)`).
5. Watch `v1.billing.meter.error_report_triggered` -- most migrations trip on customer ID mismatches, not on price math.

Gotchas:

- The `max` aggregation formula has no direct equivalent on meters. If you used it, model with `last_during_period` + client-side max.
- You cannot change a meter's `event_name` after creation. Plan naming carefully; prefer stable domain nouns (`api_request`, `seat`, `gb_stored`).
- Meter events for customers without an active meter-backed subscription are accepted and stored, but not invoiced. They do surface via the Meter Usage Analytics API.

## Related

- `subscription-patterns.md` -- full subscription lifecycle
- `usage-revenue-modeling.md` -- modeling usage distributions for pricing
- Official migration guide: https://docs.stripe.com/billing/subscriptions/usage-based-legacy/migration-guide
- Meters overview: https://docs.stripe.com/billing/subscriptions/usage-based
