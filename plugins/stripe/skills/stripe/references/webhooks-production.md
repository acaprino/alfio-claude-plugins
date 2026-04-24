# Webhooks in Production

Webhooks are the single biggest source of Stripe bugs in production. Most of those bugs are not about Stripe -- they're about signature verification, idempotency, retry handling, and missing event coverage. This reference fixes all four.

## Signature verification

Always verify. Without a signed check, your endpoint is a public unauthenticated mutation endpoint.

Python (Flask/FastAPI):

```python
import stripe
from flask import request, abort

@app.post("/webhooks/stripe")
def stripe_webhook():
    payload = request.get_data()  # RAW bytes -- do NOT re-serialize JSON
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, os.environ["STRIPE_WEBHOOK_SECRET"]
        )
    except stripe.error.SignatureVerificationError:
        abort(400)
    # ... handle event
    return "", 200
```

Node / Next.js App Router:

```typescript
export const runtime = 'nodejs';  // Edge can't do raw body

export async function POST(req: Request) {
  const body = await req.text();  // raw string
  const sig = req.headers.get('stripe-signature')!;
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body, sig, process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch {
    return new Response('bad signature', { status: 400 });
  }
  // ... handle event
  return new Response('ok');
}
```

Common signature-verification failures:

- Parsing JSON before verifying (`req.json()` instead of `req.text()`/`request.get_data()`). Any re-serialization changes the bytes; signature fails.
- Using the wrong secret (endpoint secret vs account secret vs CLI `stripe listen` secret). Each endpoint has its own `whsec_...`.
- Body being decompressed or transformed by a middleware (Express `body-parser`, Next.js `bodyParser: true`). Disable global body parsing for webhook routes.
- Edge runtime on Vercel / Cloudflare Workers -- these don't expose raw bytes cleanly. Run webhook endpoints on Node runtime.

## Idempotency

Stripe retries events within a 3-day window using exponential backoff. You WILL receive the same event multiple times. Design for it.

Store `event.id` with a unique constraint:

```sql
CREATE TABLE processed_webhook_events (
    event_id TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```python
def handle_event(event):
    try:
        db.execute(
            "INSERT INTO processed_webhook_events (event_id) VALUES (%s)",
            (event["id"],),
        )
    except UniqueViolation:
        return  # already processed
    dispatch(event)
```

The insert happens before the dispatch. If dispatch crashes, the event stays marked processed but your subscription state is stale -- which is worse than a duplicate-mail side effect from re-processing. Pick one trade-off consciously:

- **Insert-then-dispatch** (above) -- guards against duplicate side effects. Requires a recovery path for failures (DLQ, manual replay).
- **Dispatch-then-insert** -- at-least-once, may duplicate emails/notifications. Safer if your dispatch is fully idempotent at the domain level (e.g. subscription upserts by ID).

Most Stripe handlers upsert based on the Stripe object ID (`subscription.id`, `invoice.id`, etc.), which is naturally idempotent, so dispatch-then-insert is usually fine. The explicit `event_id` store is the belt-and-braces.

## Respond fast, defer work

Stripe expects a 2xx response within 10 seconds. If your handler does real work (send emails, call LLMs, update 3 tables, recompute analytics), you'll miss that budget under load.

Pattern: verify + enqueue + return 200. Do the work asynchronously.

```python
def stripe_webhook():
    payload = request.get_data()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, SECRET)
    except stripe.error.SignatureVerificationError:
        abort(400)
    queue.enqueue("handle_stripe_event", event.id, event.type)
    return "", 200
```

The worker re-fetches the event by ID (`stripe.Event.retrieve(event_id)`) to avoid trusting the queue payload. This also means the queue only needs to carry `event_id` and `event_type`, not the whole JSON.

## Event catalog -- what to handle

The minimum viable set for a subscription SaaS:

| Event | Use case |
|-------|----------|
| `checkout.session.completed` | Activate subscription after Checkout; read `client_reference_id` or `metadata.user_id` to tie to your user |
| `customer.subscription.created` | Initial grant of access (if not using Checkout) |
| `customer.subscription.updated` | Plan changes, trial->paid transitions, status changes (past_due, unpaid) |
| `customer.subscription.deleted` | Revoke access at period end or on immediate cancel |
| `customer.subscription.trial_will_end` | Fires 3 days before trial end; send reminder email |
| `invoice.payment_succeeded` | Record revenue event, send receipt if you don't rely on Stripe's |
| `invoice.payment_failed` | Start dunning flow |
| `invoice.paid` | Equivalent to `payment_succeeded` for the modern API; use one or the other consistently |

Add when using Entitlements (see `entitlements.md`):

| Event | Use case |
|-------|----------|
| `entitlements.active_entitlement_summary.updated` | Refresh the cached entitlement list for a customer |

Add when using Billing Meters (see `billing-meters.md`):

| Event | Use case |
|-------|----------|
| `v1.billing.meter.error_report_triggered` | Surface meter event validation failures (bad customer id, bad payload) |
| `v1.billing.meter.no_meter_found` | Alert on events sent to a nonexistent `event_name` (typos) |
| `billing.meter.created` / `.updated` / `.deactivated` | Lifecycle, audit log |

Add for Connect platforms:

| Event | Use case |
|-------|----------|
| `account.updated` | Connected account status changed (capabilities enabled/disabled) |
| `account.application.deauthorized` | Connected account removed your platform |
| `payout.paid` / `payout.failed` | Platform payout reconciliation |
| `charge.dispute.created` | Chargeback opened |
| `charge.dispute.funds_withdrawn` | Funds pulled while dispute pends |
| `charge.dispute.closed` | Dispute resolution (check `dispute.status`) |

Add for more granular control:

| Event | Use case |
|-------|----------|
| `invoice.upcoming` | Fires ~7 days before invoice finalization -- use to alert on usage-based overages before the bill lands |
| `customer.subscription.paused` / `.resumed` | Paused subscriptions (via pause collection) |
| `customer.updated` | Email/address changes that should sync to your user model |
| `payment_intent.payment_failed` | One-off payment failures (non-subscription) |

**Anti-pattern:** subscribing to `*` (all events). You'll get thousands of events/day in a busy account, most irrelevant. Subscribe per endpoint to the specific events you handle.

## Local development

```bash
stripe login
stripe listen --forward-to localhost:3000/webhooks/stripe
# prints: Ready! Your webhook signing secret is whsec_... -- use this in .env.local
```

Trigger events:

```bash
stripe trigger checkout.session.completed
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.trial_will_end
```

The CLI's signing secret is separate from your Dashboard endpoint secrets -- set it in a local env var, not in shared config.

Replaying past real events (e.g. after a handler bug):

```bash
stripe events resend evt_1XXX
```

## Multi-environment endpoint strategy

One endpoint per environment in the Dashboard. Never share secrets between staging and production -- a leaked dev key can be used to send real-looking events to prod if endpoints are shared.

```
Production:  https://api.yourapp.com/webhooks/stripe       -> whsec_PROD
Staging:     https://api.staging.yourapp.com/webhooks/stripe -> whsec_STAGE
Local (CLI): stripe listen --forward-to localhost:3000/...  -> whsec_CLI
```

Keep `STRIPE_WEBHOOK_SECRET` environment-scoped. If you support multiple Stripe accounts (multi-tenant platform), store the secret per-account and look it up by endpoint path or subdomain.

## Audit checklist

Run through this on any webhook handler before it ships:

- [ ] Signature verified against raw request body
- [ ] Correct endpoint secret (matches the endpoint's `whsec_...` in Dashboard)
- [ ] Returns 2xx within 10s (deferred heavy work to queue/worker)
- [ ] `event.id` persisted with a unique constraint (or dispatch is fully idempotent)
- [ ] Subscribed only to the events you handle (no `*`)
- [ ] Covers the minimum viable catalog (see table above)
- [ ] Covers `invoice.payment_failed` + has a dunning strategy
- [ ] Covers `customer.subscription.trial_will_end` if you offer trials
- [ ] If using Entitlements, covers `entitlements.active_entitlement_summary.updated`
- [ ] If using Meters, covers `v1.billing.meter.error_report_triggered`
- [ ] Handler logs `event.id` and `event.type` on every event for traceability
- [ ] Failure mode for unparseable events (404 vs 400 vs 500) is intentional -- 2xx or 4xx, never 5xx for bad data (Stripe retries 5xx for days)

Tools: `scripts/webhook_handler.py` for a working signature-verified template. `scripts/webhook_audit.py` (planned) for a runtime audit against a Stripe account's configured endpoints.

## Related

- `stripe-patterns.md` -- idempotency on the send side (API calls, not webhooks)
- `billing-meters.md` -- meter-specific webhook events
- `entitlements.md` -- entitlement webhook cache pattern
- `subscription-patterns.md` -- state reconciliation
- Official event reference: https://docs.stripe.com/api/events/types
- Webhook best practices: https://docs.stripe.com/webhooks/best-practices
