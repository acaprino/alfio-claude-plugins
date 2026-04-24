# Feature Entitlements

Stripe-native feature gating. First-class alternative to rolling your own `metadata.features` array or a local `plans.json`.

Use Entitlements when:

- Your pricing is already modeled as Products + Prices in Stripe.
- You want Stripe to be the source of truth for "which features does customer X have right now".
- You need your app to react to upgrades / downgrades / cancellations without writing custom reconciliation logic.

Stick with a local map (skip Entitlements) when:

- You self-host billing or use another provider.
- You bundle features that aren't tied to a purchased Product (e.g. internal roles, free-for-alumni flags, gated experiments).

## Object model

Three objects:

- **Feature** (`stripe.entitlements.Feature`) -- a single thing a customer can have access to, identified by a `lookup_key` (your internal code, max 80 chars).
- **ProductFeature** -- attaches a Feature to a Product. When a subscription to that Product is active, Stripe grants the feature.
- **ActiveEntitlement** -- the read side. For each customer, Stripe maintains a live set of entitlements that reflects their current subscriptions.

## Define features

Do this once per feature, at setup time or via migration script:

```python
stripe.entitlements.Feature.create(
    name="Advanced Analytics",
    lookup_key="advanced_analytics",
)
stripe.entitlements.Feature.create(
    name="API access",
    lookup_key="api_access",
)
stripe.entitlements.Feature.create(
    name="Priority support",
    lookup_key="priority_support",
)
```

Rules:

- `lookup_key` is immutable. Pick a stable name.
- Can't reuse a `lookup_key` across live features; archive the old one first if you need to repurpose.
- There's no "soft delete" -- use `stripe.entitlements.Feature.modify(..., active=False)` to archive.

## Attach features to products

```python
stripe.Product.create_feature(
    product="prod_pro",
    entitlement_feature="feat_advanced_analytics",
)
stripe.Product.create_feature(
    product="prod_pro",
    entitlement_feature="feat_api_access",
)
stripe.Product.create_feature(
    product="prod_enterprise",
    entitlement_feature="feat_advanced_analytics",
)
stripe.Product.create_feature(
    product="prod_enterprise",
    entitlement_feature="feat_api_access",
)
stripe.Product.create_feature(
    product="prod_enterprise",
    entitlement_feature="feat_priority_support",
)
```

Typescript equivalent:

```typescript
await stripe.products.createFeature('prod_pro', {
  entitlement_feature: 'feat_advanced_analytics',
});
```

## Query entitlements at runtime

```python
entitlements = stripe.entitlements.ActiveEntitlement.list(customer="cus_xxx")
has_api = any(e.lookup_key == "api_access" for e in entitlements.auto_paging_iter())
```

```typescript
const entitlements = await stripe.entitlements.activeEntitlements.list({
  customer: 'cus_xxx',
});
const hasApi = entitlements.data.some(e => e.lookup_key === 'api_access');
```

**Do not** call this API on every request. The summary has a cap of 10 entitlements per customer; more importantly, it's a network round-trip. Cache locally and invalidate on webhook.

## Caching pattern

Persist entitlements in your own database keyed by customer, and refresh via webhook:

```python
# webhook handler
if event["type"] == "entitlements.active_entitlement_summary.updated":
    summary = event["data"]["object"]
    customer_id = summary["customer"]
    lookup_keys = [e["lookup_key"] for e in summary["entitlements"]["data"]]
    db.execute(
        "UPDATE customers SET entitlements = %s, entitlements_updated_at = NOW() WHERE stripe_customer_id = %s",
        (lookup_keys, customer_id),
    )
```

The `entitlements.active_entitlement_summary.updated` event fires on every subscription create/update/cancel that changes the entitlement set. The event payload includes the full up-to-date list -- you don't need to re-query.

Access check becomes a local DB/cache lookup:

```python
def has_feature(customer_id: str, feature: str) -> bool:
    row = db.get("SELECT entitlements FROM customers WHERE stripe_customer_id = %s", (customer_id,))
    return feature in (row["entitlements"] or [])
```

## Bootstrapping existing customers

The webhook only fires on future changes. For existing customers, backfill once:

```python
for customer in stripe.Customer.list().auto_paging_iter():
    entitlements = stripe.entitlements.ActiveEntitlement.list(customer=customer.id)
    lookup_keys = [e.lookup_key for e in entitlements.auto_paging_iter()]
    persist_entitlements(customer.id, lookup_keys)
```

Re-run this whenever you add a new ProductFeature to an already-live Product; existing subscribers need their cache refreshed.

## Migration from metadata-based gating

Common pre-Entitlements pattern:

```python
# OLD -- store features on the price or product metadata
price = stripe.Price.create(
    product="prod_pro",
    metadata={"features": "advanced_analytics,api_access"},
)
# App read path: fetch subscription -> price -> metadata -> split on ","
```

Migration steps:

1. Create a `Feature` for each distinct string you have in metadata.
2. For each Product, call `Product.create_feature` for each feature it grants.
3. Backfill `ActiveEntitlement` into your cache (see above).
4. Wire the webhook handler.
5. Flip your feature-check function from the metadata read to the cache read.
6. Once everything reads from the cache, delete the `features` metadata.

Do 1-4 in prod before step 5 -- the read path change is the risky part and should come after the writer is proven.

## Constraints and gotchas

- The summary returns a maximum of **10 entitlements** per customer. If you need more, use finer-grained feature grouping or skip Entitlements.
- Entitlements reflect *active* subscriptions only. A customer in a grace period after a failed payment still has their entitlements until Stripe marks the subscription past the grace window (controlled by your subscription settings + dunning config).
- Free tier users (no subscription) have no entitlements. Grant free-tier features via your own default set, not via a "$0 Product".
- Entitlements don't cover usage-based limits. "Can use feature X" is entitlement-shaped; "has N credits this month" is not -- use Billing Meters for quotas.

## Related

- `subscription-patterns.md` -- subscription lifecycle
- `webhooks-production.md` -- full event catalog and idempotency
- Official docs: https://docs.stripe.com/billing/entitlements
- Webhook event reference: `entitlements.active_entitlement_summary.updated`
