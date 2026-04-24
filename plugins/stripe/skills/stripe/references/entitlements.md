# Feature Entitlements

Stripe-native feature gating. First-class replacement for rolling your own `metadata.features` array or local `plans.json`.

## When to use

- Your billing lives in Stripe (Products + Prices).
- You want Stripe to be the source of truth for "which features does customer X have right now".

Skip if: you self-host billing, or you gate features not tied to a purchased Product (internal roles, experiments, free-for-alumni flags).

## The 3-object mental model

- **Feature** (`stripe.entitlements.Feature`) -- identified by immutable `lookup_key` (your internal code, max 80 chars).
- **ProductFeature** -- attaches a Feature to a Product. When a subscription is active, Stripe grants the feature.
- **ActiveEntitlement** -- the read side; a live set per customer.

## Gotchas

- **`lookup_key` is immutable.** Pick stable names. Can't reuse across live features; archive first.
- **The summary caps at 10 entitlements per customer.** If you need more, use coarser grouping.
- **Entitlements reflect *active* subscriptions only.** Grace-period customers still have access until Stripe ends the subscription (configurable via dunning).
- **Free-tier users have no entitlements.** Grant free-tier features via your own default set, not via a $0 Product.
- **Don't use Entitlements for usage quotas.** "Can use feature X" is entitlement-shaped; "has N credits this month" is Meters-shaped.
- **Cache via webhook, don't query per-request.** Subscribe to `entitlements.active_entitlement_summary.updated` -- payload includes the full summary, no re-query needed.

## Cache pattern (the whole value prop)

```python
if event["type"] == "entitlements.active_entitlement_summary.updated":
    summary = event["data"]["object"]
    keys = [e["lookup_key"] for e in summary["entitlements"]["data"]]
    db.update_customer_entitlements(summary["customer"], keys)
```

Feature check becomes a local lookup against the cached list. Backfill existing customers once on rollout via `ActiveEntitlement.list(customer=...)`.

## Official docs

- Overview and product guide: https://docs.stripe.com/billing/entitlements
- Blog walkthrough: https://stripe.dev/blog/managing-saas-access-control-with-stripe-entitlements-api
- API reference (Feature): https://docs.stripe.com/api/entitlements/feature
- API reference (ActiveEntitlement): https://docs.stripe.com/api/entitlements/active-entitlement

## Related

- `webhooks-production.md` -- event handling and idempotency
- `billing-meters.md` -- complementary primitive for usage quotas
