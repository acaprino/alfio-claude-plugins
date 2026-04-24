# Embedded Checkout

Stripe Checkout can render three ways. This file is about the middle option -- the one that mounts inside your React tree instead of redirecting.

## Decision matrix

| Mode | When to use | Trade-off |
|------|-------------|-----------|
| **Hosted (redirect)** | Fastest to ship; no UI work. `session.url` redirect. | User leaves your domain. Loses analytics context, breaks SPAs. |
| **Embedded** (`ui_mode: 'embedded'`) | You want Checkout inside your page. React component mount. | Some UI constraints; Stripe controls the payment form visuals. |
| **Payment Element** (custom) | Full control over layout; multi-step checkout; you write the UI. | You implement Payment Intents manually, handle SCA, error states. |

Pick embedded when: you have a page-level checkout route, you want SPA navigation (no full redirect), you're fine with Stripe's layout within the component. Pick custom Payment Element when: checkout is multi-step with your own fields (shipping, upsells), or you need the payment form inside a larger form.

Embedded has two sub-modes:

- `ui_mode: 'embedded'` -- renders inline where you mount the component (card-like section within your page).
- `ui_mode: 'embedded_page'` -- renders as a full-page embed (newer variant; useful when your checkout route is a dedicated page but you still want SPA navigation).

Default to `'embedded'` unless you're building a dedicated checkout route that would otherwise be a redirect target.

## Server: create the session

```typescript
// app/api/checkout/embedded/route.ts
import { stripe } from '@/lib/stripe';

export const runtime = 'nodejs';

export async function POST(req: Request) {
  const { priceId, userId } = await req.json();

  const session = await stripe.checkout.sessions.create({
    ui_mode: 'embedded',
    mode: 'subscription',
    line_items: [{ price: priceId, quantity: 1 }],
    return_url: `${process.env.APP_URL}/checkout/return?session_id={CHECKOUT_SESSION_ID}`,
    client_reference_id: userId,
    metadata: { userId },
    automatic_tax: { enabled: true },
  });

  return Response.json({ clientSecret: session.client_secret });
}
```

Key differences from redirect mode:

- `ui_mode: 'embedded'` (or `'embedded_page'`)
- `return_url` instead of `success_url` + `cancel_url` (there's only one outcome -- completion; cancellation is the user navigating away)
- Response is `client_secret`, not `session.url`. Do not expose the session ID to the client; only the client_secret.

Python equivalent:

```python
session = stripe.checkout.Session.create(
    ui_mode="embedded",
    mode="subscription",
    line_items=[{"price": price_id, "quantity": 1}],
    return_url=f"{APP_URL}/checkout/return?session_id={{CHECKOUT_SESSION_ID}}",
    client_reference_id=user_id,
    metadata={"user_id": user_id},
)
return {"clientSecret": session.client_secret}
```

## Client: mount the component

```tsx
// app/pricing/checkout.tsx
'use client';

import { useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  EmbeddedCheckoutProvider,
  EmbeddedCheckout,
} from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

export function Checkout({ priceId, userId }: { priceId: string; userId: string }) {
  const fetchClientSecret = useCallback(async () => {
    const res = await fetch('/api/checkout/embedded', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ priceId, userId }),
    });
    const { clientSecret } = await res.json();
    return clientSecret;
  }, [priceId, userId]);

  return (
    <EmbeddedCheckoutProvider
      stripe={stripePromise}
      options={{ fetchClientSecret }}
    >
      <EmbeddedCheckout />
    </EmbeddedCheckoutProvider>
  );
}
```

`fetchClientSecret` is called by the provider at mount time. Return it as a promise; don't pre-fetch before rendering.

## Return page

After successful payment, the user is redirected to `return_url`. That page reads `session_id` from the query and confirms the outcome:

```tsx
// app/checkout/return/page.tsx
import { stripe } from '@/lib/stripe';

export const dynamic = 'force-dynamic';

export default async function CheckoutReturn({
  searchParams,
}: { searchParams: Promise<{ session_id?: string }> }) {
  const { session_id } = await searchParams;
  if (!session_id) return <p>Missing session</p>;

  const session = await stripe.checkout.sessions.retrieve(session_id);

  if (session.status === 'complete') {
    return <p>Thanks! Your subscription is active.</p>;
  }
  if (session.status === 'open') {
    // payment still in progress or abandoned -- re-open or prompt retry
    return <p>Your payment did not complete. Try again.</p>;
  }
  return <p>Status: {session.status}</p>;
}
```

`session.status` is one of `open`, `complete`, `expired`. Don't grant access here -- grant access from the webhook (`checkout.session.completed`). This page is read-only UI; the webhook is the source of truth. See `webhooks-production.md`.

## `onComplete` vs `return_url`

Embedded Checkout supports either:

- **`return_url`** (used above): on success, Stripe redirects to the URL with `session_id` appended. Best for most cases -- gives you a clean post-purchase page.
- **`onComplete`** callback: Stripe fires a JS callback inside your React tree instead of redirecting. Best for modal/drawer checkout where you want to close the overlay and update state without a full navigation.

If you provide `onComplete`, omit `return_url`:

```tsx
<EmbeddedCheckoutProvider
  stripe={stripePromise}
  options={{
    fetchClientSecret,
    onComplete: () => {
      // close modal, re-fetch user state, show success toast
      onClose();
      router.refresh();
    },
  }}
>
```

`onComplete` only fires client-side. You still need the webhook to grant access server-side.

## Payment method configuration

By default, Checkout shows card + whatever wallets/BNPL the customer's region supports. Override with a payment method configuration (managed in Dashboard -> Settings -> Payment methods):

```typescript
const session = await stripe.checkout.sessions.create({
  ui_mode: 'embedded',
  mode: 'subscription',
  payment_method_configuration: 'pmc_xxx',  // optional; omit to use default
  line_items: [{ price: priceId, quantity: 1 }],
  return_url: `${process.env.APP_URL}/checkout/return?session_id={CHECKOUT_SESSION_ID}`,
});
```

Or explicit list:

```typescript
payment_method_types: ['card', 'klarna', 'affirm', 'apple_pay', 'google_pay'],
```

Prefer `payment_method_configuration` -- it lets you manage the PM list from the Dashboard without re-deploying.

## Apple Pay / Google Pay

With hosted Checkout, wallet domain verification is automatic (Stripe owns the domain). With embedded Checkout, your domain is in the flow, so you must register it:

```typescript
await stripe.paymentMethodDomains.create({
  domain_name: 'yourapp.com',
});
await stripe.paymentMethodDomains.validate('pmd_xxx');
```

Validation checks that `https://yourapp.com/.well-known/apple-developer-merchantid-domain-association` is reachable. Stripe hosts a generic file; you just need to proxy it from that well-known path. See Dashboard -> Settings -> Payment method domains.

Run this once per production domain, once per staging domain. It does not need to run on every deploy.

## Adaptive Pricing

Presents prices in the customer's local currency automatically. Toggle in Dashboard -> Settings -> Payments -> Adaptive Pricing. No code change required, but be aware:

- Reconciliation still uses your default currency.
- Refunds and proration calculations round in the presentation currency, which can introduce small deltas.
- Disable for merchants that have negotiated per-currency pricing with their accounting.

## Embedded vs redirect: pick by requirement

Go embedded if any of these are true:

- Your app is a single-page feel; a full-page Stripe redirect breaks the experience.
- You need the URL to stay on your domain for analytics/attribution.
- You're inside a modal or drawer.

Stay with redirect if:

- You're shipping v0 of a paid product -- redirect Checkout is the fastest 90%-correct option.
- You need maximum form flexibility; eventually migrate to custom Payment Element, not embedded.
- You're on Edge runtime for the whole app -- the React embed still works, but the server session creation must run on Node.

## Common pitfalls

- **Exposing `session.id` instead of `client_secret` to the client** -- anyone with the session ID can retrieve metadata. Only `client_secret` is safe to ship to the browser.
- **Pre-fetching the client secret before render** -- `fetchClientSecret` is called at mount time; pre-fetching means the secret ages on the client. Fetch-on-mount.
- **`return_url` and `onComplete` both set** -- Stripe errors. Pick one.
- **Forgetting wallet domain verification** -- Apple Pay / Google Pay silently don't render on your domain until you verify via `paymentMethodDomains`. Test on a device that supports them; desktop Chrome won't show the issue.
- **Granting access on the return page** -- the return page runs client-side URL manipulation; anyone can navigate to it with a forged `session_id`. Grant access from the webhook, use the return page for UI only.

## Related

- `typescript-nextjs.md` -- broader Next.js patterns
- `webhooks-production.md` -- `checkout.session.completed` handling
- `checkout-optimization.md` -- conversion optimization (form fields, trust signals)
- `stripe.md` -- redirect-mode Checkout
- Official docs: https://docs.stripe.com/checkout/embedded/quickstart
