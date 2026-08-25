# Webhooks in Production

Most Stripe production bugs come from four failures: wrong signature verification, missing idempotency, wrong runtime, and missing event coverage. This file is the pass/fail checklist; canonical code lives in Stripe's docs.

## The four things that must be right

1. **Raw body, signature verified.** Use `req.text()` / `request.get_data()` -- never `req.json()`. Call `stripe.webhooks.constructEvent` / `stripe.Webhook.construct_event`. Return 4xx (not 5xx, not 200) on `SignatureVerificationError`.
2. **Idempotency.** Stripe retries up to 3 days. Either store `event.id` with a uniqueness guard OR upsert by Stripe object ID (naturally idempotent). Pick one consciously.
3. **Node runtime for webhooks.** Edge runtimes (Vercel Edge, Cloudflare Workers, Next.js `runtime = 'edge'`) break raw-body handling in subtle ways. Run webhook endpoints on Node.
4. **Respond 2xx within 10s.** Defer heavy work (emails, LLM calls, multi-table writes) to a queue; the handler enqueues and returns.

## Must-have event catalog

Base set -- any subscription SaaS:

- `checkout.session.completed`
- `customer.subscription.created` / `.updated` / `.deleted`
- `invoice.payment_failed`
- `invoice.payment_succeeded` (or `invoice.paid` -- pick one, stay consistent)

Add per feature:

- **Trials:** `customer.subscription.trial_will_end`
- **Entitlements:** `entitlements.active_entitlement_summary.updated`
- **Billing Meters:** `v1.billing.meter.error_report_triggered`, `v1.billing.meter.no_meter_found`
- **Connect platforms:** `account.updated`, `account.application.deauthorized`, `charge.dispute.created`, `charge.dispute.closed`
- **Proactive overage alerts:** `invoice.upcoming` (fires ~7 days before finalization)

**Anti-pattern:** subscribing to `*` (all events). You'll get thousands/day and bury the signal.

## Idempotency sketch

```sql
CREATE TABLE processed_webhook_events (
    event_id TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Insert-then-dispatch guards against duplicate side effects. Dispatch-then-insert is fine if your dispatch is fully idempotent at the domain level (upsert by subscription.id, etc.).

## Multi-environment strategy

One endpoint per environment, one `whsec_...` per endpoint. Never share secrets across prod/staging/local. The CLI `stripe listen --forward-to ...` has its own signing secret, separate from Dashboard endpoints.

## Audit checklist

- [ ] Raw body read before any parsing
- [ ] Correct endpoint secret (matches Dashboard `whsec_...`)
- [ ] 4xx on signature failure (not 500, not 200)
- [ ] `event.id` deduped OR dispatch is upsert-by-object-id
- [ ] Subscribed only to events you handle (no `*`)
- [ ] Covers the base set + feature-specific events above
- [ ] Heavy work deferred to queue
- [ ] 2xx within 10s under load (test with `stripe trigger` + ab)
- [ ] Logs `event.id` + `event.type` for traceability
- [ ] Runtime is Node (not Edge/Worker) on the webhook route

## Official docs

- Best practices: https://docs.stripe.com/webhooks/best-practices
- Full event type list: https://docs.stripe.com/api/events/types
- Quickstart with code samples: https://docs.stripe.com/webhooks/quickstart
- Local testing with CLI: https://docs.stripe.com/webhooks#test-webhook
- Signature verification reference: https://docs.stripe.com/webhooks/signature

## Related

- `stripe-patterns.md` -- API-side idempotency (not webhooks)
- `billing-meters.md` -- meter-specific webhook events
- `entitlements.md` -- entitlement cache pattern
- `stripe-webhooks-auditor` agent -- adversarial audit against a live account
