# TypeScript and Next.js Patterns

Stripe integrations for TypeScript projects, with a strong focus on Next.js App Router. The rest of this plugin leans Python; this file is the canonical TS reference.

## Setup

```bash
pnpm add stripe @stripe/stripe-js @stripe/react-stripe-js
```

Server-side client in `lib/stripe.ts`:

```typescript
import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2026-04-22.dahlia',
  typescript: true,
});
```

Client-side publishable key. Next.js exposes it via `NEXT_PUBLIC_`:

```typescript
import { loadStripe } from '@stripe/stripe-js';
export const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);
```

## Webhook handler (Route Handler)

The single most important pattern. Four things must be right: Node runtime, raw body, signature verification, idempotency.

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest } from 'next/server';
import Stripe from 'stripe';
import { stripe } from '@/lib/stripe';

export const runtime = 'nodejs';        // MUST NOT be 'edge' -- Edge can't do raw body
export const dynamic = 'force-dynamic'; // webhooks are never cacheable

export async function POST(req: NextRequest) {
  const body = await req.text();                   // raw string, not .json()
  const sig = req.headers.get('stripe-signature');

  if (!sig) return new Response('missing signature', { status: 400 });

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'invalid';
    return new Response(`bad signature: ${msg}`, { status: 400 });
  }

  // Idempotency: reject duplicates by event.id
  const inserted = await db.processedEvents.create({
    data: { eventId: event.id },
  }).catch(() => null);
  if (!inserted) return new Response('already processed', { status: 200 });

  await handleEvent(event);
  return new Response('ok');
}

async function handleEvent(event: Stripe.Event) {
  // Discriminated union -- compiler narrows event.data.object per case
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;  // Stripe.Checkout.Session
      await activateSubscription(session);
      break;
    }
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted': {
      const subscription = event.data.object;  // Stripe.Subscription
      await syncSubscription(subscription);
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object;  // Stripe.Invoice
      await markPastDue(invoice);
      break;
    }
    case 'entitlements.active_entitlement_summary.updated': {
      const summary = event.data.object;
      await refreshEntitlementCache(summary);
      break;
    }
    default:
      // Intentionally ignore -- subscribe only to events you handle in Dashboard
      break;
  }
}
```

Why these four choices matter:

- `runtime = 'nodejs'` -- Edge runtime can't expose raw bytes without transformations that break signature verification. Running webhooks on Edge looks like it works, then fails under load.
- `req.text()` -- `req.json()` re-serializes; the byte sequence changes; signature fails. Always read the body as text.
- Signature verification -- `constructEvent` throws on mismatch; a 400 response tells Stripe not to retry (signature issues don't get better with retries).
- Idempotency via `event.id` -- Stripe retries for up to 3 days. Double-processing is guaranteed at some point.

## Server Action for Checkout Session

Next.js Server Actions are the modern way to trigger Checkout from a form without a separate API route:

```typescript
// app/actions/checkout.ts
'use server';

import { stripe } from '@/lib/stripe';
import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';

export async function createCheckoutSession(formData: FormData) {
  const priceId = formData.get('priceId') as string;
  const userId = (await cookies()).get('userId')?.value;
  if (!userId) redirect('/login');

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.APP_URL}/billing/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.APP_URL}/pricing`,
    client_reference_id: userId,
    metadata: { userId },
    allow_promotion_codes: true,
    automatic_tax: { enabled: true },  // requires Stripe Tax
  });

  redirect(session.url!);
}
```

```tsx
// app/pricing/page.tsx
import { createCheckoutSession } from '@/app/actions/checkout';

export default function Pricing() {
  return (
    <form action={createCheckoutSession}>
      <input type="hidden" name="priceId" value="price_xxx" />
      <button type="submit">Subscribe</button>
    </form>
  );
}
```

Notes:

- Server Actions run on the server with full access to `process.env.STRIPE_SECRET_KEY`. Don't accidentally call Stripe from a client component.
- `redirect()` must happen outside a try/catch in a Server Action -- it throws a `NEXT_REDIRECT` marker that React Server Components catch. Catching it yourself swallows the redirect.
- `session.url!` is non-null when `mode !== 'embedded'`. For embedded checkout, use `client_secret` instead; see `embedded-checkout.md`.

## Type-narrowing Stripe events

`Stripe.Event` is a discriminated union. Use `switch(event.type)` and the compiler gives you the correct `event.data.object` type per branch:

```typescript
if (event.type === 'customer.subscription.updated') {
  const sub: Stripe.Subscription = event.data.object;
  // sub.status, sub.items.data[0].price.id, etc. are fully typed
}
```

Avoid casting with `as Stripe.Subscription`. If the type doesn't narrow, your event type is wrong, or you're on an SDK version that doesn't know about the event yet. Upgrade the SDK rather than bypassing the check.

## Reading session details on return

For redirect-based Checkout, the success page retrieves session state:

```typescript
// app/billing/success/page.tsx
import { stripe } from '@/lib/stripe';

export default async function Success({
  searchParams,
}: { searchParams: Promise<{ session_id: string }> }) {
  const { session_id } = await searchParams;
  const session = await stripe.checkout.sessions.retrieve(session_id, {
    expand: ['line_items', 'subscription'],
  });

  if (session.payment_status !== 'paid') {
    return <p>Your payment is processing. We'll email when complete.</p>;
  }
  return <p>Thanks! Your subscription is active.</p>;
}
```

Don't grant access on the success page alone -- grant access from the webhook (`checkout.session.completed`). The success page is read-only UI; the webhook is the source of truth. A user closing their browser mid-redirect still gets access via the webhook; a user who landed on the success page but whose webhook hasn't fired yet shouldn't lock them out.

## Customer Portal

```typescript
'use server';
export async function openPortal() {
  const userId = (await cookies()).get('userId')?.value;
  const user = await db.user.findUnique({ where: { id: userId! } });
  if (!user?.stripeCustomerId) throw new Error('no Stripe customer');

  const session = await stripe.billingPortal.sessions.create({
    customer: user.stripeCustomerId,
    return_url: `${process.env.APP_URL}/account`,
  });
  redirect(session.url);
}
```

## Billing Meters (usage reporting)

For metered billing from a Next.js server route or server action:

```typescript
import { stripe } from '@/lib/stripe';

export async function reportApiUsage(customerId: string, count: number, requestId: string) {
  await stripe.billing.meterEvents.create({
    event_name: 'api_request',
    payload: {
      stripe_customer_id: customerId,
      value: String(count),
    },
    identifier: requestId,  // dedupes retries
    timestamp: Math.floor(Date.now() / 1000),
  });
}
```

See `billing-meters.md` for the full model.

## Middleware and auth

Don't do Stripe calls from Edge Middleware. `middleware.ts` runs on Edge by default and can't use the Node-required `stripe` SDK. Keep auth checks in middleware; keep billing in Server Actions and Route Handlers.

## Environment variables

```
# .env.local
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
APP_URL=http://localhost:3000
```

Production `STRIPE_WEBHOOK_SECRET` is the endpoint-scoped secret from Dashboard -> Webhooks. Your local `stripe listen` gives you a different `whsec_` -- never reuse it across environments.

## Common pitfalls in Next.js specifically

- **Running webhooks on Edge runtime** -- raw-body handling breaks silently. Set `runtime = 'nodejs'`.
- **Using `req.json()` in webhook handler** -- re-serializes body, signature fails.
- **Calling Stripe from a Client Component** -- accidentally exposes the secret key if you import `@/lib/stripe`. Keep that import tree server-only (mark files `'use server'` or put them under `app/api`).
- **`NEXT_PUBLIC_STRIPE_SECRET_KEY`** -- the `NEXT_PUBLIC_` prefix ships env vars to the browser. Never prefix a secret this way. Publishable key only.
- **Static page caching on the success page** -- wrap in `export const dynamic = 'force-dynamic'` or use `Suspense` with a streaming boundary; otherwise `searchParams` may be stale.
- **Relying on `session.url` for embedded mode** -- in `ui_mode: 'embedded'`, `session.url` is null. Return `client_secret` to the client instead. See `embedded-checkout.md`.

## Related

- `billing-meters.md` -- usage-based billing model
- `entitlements.md` -- feature gating with webhook-driven cache
- `webhooks-production.md` -- full event catalog and audit checklist
- `embedded-checkout.md` -- client-mountable Checkout alternative
- `stripe.md` -- core patterns (legacy reference, overlaps with this file)
