# Stripe Integration Patterns

## Setup

```bash
npm install stripe @stripe/stripe-js
```

Environment variables:
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Server-Side Setup

```typescript
// lib/stripe.ts
import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-12-18.acacia',
});
```

## Checkout Session (One-Time or Subscription)

```typescript
// api/checkout/route.ts
export async function POST(req: Request) {
  const { priceId, userId, mode = 'subscription' } = await req.json();
  
  const session = await stripe.checkout.sessions.create({
    mode, // 'subscription' or 'payment'
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.APP_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.APP_URL}/pricing`,
    client_reference_id: userId,
    customer_email: user.email, // Pre-fill if known
    allow_promotion_codes: true,
    billing_address_collection: 'auto',
    metadata: { userId },
  });
  
  return Response.json({ url: session.url });
}
```

## Webhook Handler

```typescript
// api/webhooks/stripe/route.ts
export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get('stripe-signature')!;
  
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    return new Response('Webhook signature verification failed', { status: 400 });
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutComplete(session);
      break;
    }
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      await syncSubscription(subscription);
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentFailed(invoice);
      break;
    }
  }
  
  return new Response('OK');
}
```

## Subscription Sync

```typescript
async function syncSubscription(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;
  const user = await db.user.findFirst({ where: { stripeCustomerId: customerId } });
  
  await db.subscription.upsert({
    where: { stripeSubscriptionId: subscription.id },
    update: {
      status: subscription.status,
      priceId: subscription.items.data[0].price.id,
      currentPeriodEnd: new Date(subscription.current_period_end * 1000),
      cancelAtPeriodEnd: subscription.cancel_at_period_end,
    },
    create: {
      userId: user.id,
      stripeSubscriptionId: subscription.id,
      stripeCustomerId: customerId,
      status: subscription.status,
      priceId: subscription.items.data[0].price.id,
      currentPeriodEnd: new Date(subscription.current_period_end * 1000),
    },
  });
}
```

## Customer Portal

```typescript
// api/billing/portal/route.ts
export async function POST(req: Request) {
  const user = await getCurrentUser();
  
  const session = await stripe.billingPortal.sessions.create({
    customer: user.stripeCustomerId,
    return_url: `${process.env.APP_URL}/settings/billing`,
  });
  
  return Response.json({ url: session.url });
}
```

## Usage-Based Billing

```typescript
// Report usage for metered billing
await stripe.subscriptionItems.createUsageRecord(
  subscriptionItemId,
  {
    quantity: apiCallCount,
    timestamp: Math.floor(Date.now() / 1000),
    action: 'increment',
  }
);
```

## Price Configuration (Dashboard or API)

```typescript
// Create products and prices programmatically
const product = await stripe.products.create({
  name: 'Pro Plan',
  description: 'Full access to all features',
});

const monthlyPrice = await stripe.prices.create({
  product: product.id,
  unit_amount: 2900, // $29.00
  currency: 'usd',
  recurring: { interval: 'month' },
  lookup_key: 'pro_monthly', // Use for easy lookup
});

const yearlyPrice = await stripe.prices.create({
  product: product.id,
  unit_amount: 29000, // $290.00 (save ~17%)
  currency: 'usd',
  recurring: { interval: 'year' },
  lookup_key: 'pro_yearly',
});
```

## Client-Side (React)

```tsx
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

function PricingButton({ priceId }: { priceId: string }) {
  const handleClick = async () => {
    const res = await fetch('/api/checkout', {
      method: 'POST',
      body: JSON.stringify({ priceId }),
    });
    const { url } = await res.json();
    window.location.href = url;
  };
  
  return <button onClick={handleClick}>Subscribe</button>;
}
```

## Essential Webhooks to Handle

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Create subscription record, grant access |
| `customer.subscription.updated` | Sync plan changes, handle upgrades/downgrades |
| `customer.subscription.deleted` | Revoke access, send win-back email |
| `invoice.payment_succeeded` | Update billing status, send receipt |
| `invoice.payment_failed` | Mark past_due, send dunning email |
| `customer.subscription.trial_will_end` | Send trial ending reminder (3 days before) |
