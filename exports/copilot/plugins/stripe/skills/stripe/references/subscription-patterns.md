# Subscription System Patterns

## Database Schema

```sql
-- Users table (add these columns)
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);

-- Subscriptions table
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) NOT NULL,
  stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
  stripe_customer_id VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL, -- active, canceled, past_due, trialing, paused
  price_id VARCHAR(255) NOT NULL,
  current_period_start TIMESTAMP NOT NULL,
  current_period_end TIMESTAMP NOT NULL,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  canceled_at TIMESTAMP,
  trial_end TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

## Prisma Schema

```prisma
model Subscription {
  id                   String   @id @default(cuid())
  userId               String   @unique
  user                 User     @relation(fields: [userId], references: [id])
  stripeSubscriptionId String   @unique
  stripeCustomerId     String
  status               String   // active, canceled, past_due, trialing
  priceId              String
  currentPeriodStart   DateTime
  currentPeriodEnd     DateTime
  cancelAtPeriodEnd    Boolean  @default(false)
  canceledAt           DateTime?
  trialEnd             DateTime?
  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt
}
```

## Subscription State Machine

```
                    ┌──────────────┐
                    │   trialing   │
                    └──────┬───────┘
                           │ trial ends + payment succeeds
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   canceled   │◄───│    active    │───►│   past_due   │
└──────────────┘    └──────────────┘    └──────┬───────┘
       ▲                   ▲                    │
       │                   │ payment succeeds   │ payment fails 3x
       │                   └────────────────────┤
       └────────────────────────────────────────┘
```

## Subscription Service

```typescript
// lib/subscription.ts
export class SubscriptionService {
  async getSubscription(userId: string) {
    return db.subscription.findFirst({
      where: { userId, status: { in: ['active', 'trialing'] } },
    });
  }

  async isActive(userId: string): Promise<boolean> {
    const sub = await this.getSubscription(userId);
    return !!sub && ['active', 'trialing'].includes(sub.status);
  }

  async getPlan(userId: string) {
    const sub = await this.getSubscription(userId);
    if (!sub) return PLANS.free;
    return PLANS[this.getPlanIdFromPriceId(sub.priceId)];
  }

  async hasFeature(userId: string, feature: string): Promise<boolean> {
    const plan = await this.getPlan(userId);
    return plan.features.includes(feature);
  }

  async checkLimit(userId: string, resource: string, current: number): Promise<boolean> {
    const plan = await this.getPlan(userId);
    return current < (plan.limits[resource] ?? Infinity);
  }
}
```

## Webhook Idempotency

```typescript
// Prevent duplicate processing
async function handleWebhook(event: Stripe.Event) {
  const processed = await db.webhookEvent.findUnique({
    where: { stripeEventId: event.id },
  });
  
  if (processed) {
    console.log(`Event ${event.id} already processed`);
    return;
  }

  await db.$transaction(async (tx) => {
    // Record that we're processing this event
    await tx.webhookEvent.create({
      data: { stripeEventId: event.id, type: event.type },
    });
    
    // Process the event
    await processEvent(event, tx);
  });
}
```

## Trial Implementation

```typescript
// Create subscription with trial
const session = await stripe.checkout.sessions.create({
  mode: 'subscription',
  subscription_data: {
    trial_period_days: 14,
  },
  // ... other options
});

// Check trial status
function getTrialStatus(subscription: Subscription) {
  if (subscription.status !== 'trialing') return null;
  
  const daysLeft = Math.ceil(
    (subscription.trialEnd.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );
  
  return { isTrialing: true, daysLeft, endsAt: subscription.trialEnd };
}
```

## Upgrade/Downgrade Handling

```typescript
async function changePlan(userId: string, newPriceId: string) {
  const sub = await getSubscription(userId);
  
  const updated = await stripe.subscriptions.update(sub.stripeSubscriptionId, {
    items: [{
      id: sub.items.data[0].id,
      price: newPriceId,
    }],
    proration_behavior: 'create_prorations', // or 'none', 'always_invoice'
  });
  
  await syncSubscription(updated);
  return updated;
}
```

## Cancellation Flow

```typescript
// Cancel at period end (recommended)
async function cancelSubscription(userId: string) {
  const sub = await getSubscription(userId);
  
  await stripe.subscriptions.update(sub.stripeSubscriptionId, {
    cancel_at_period_end: true,
  });
  
  // Optionally collect feedback
  await db.cancellationFeedback.create({
    data: { userId, reason: 'too_expensive' }, // from user input
  });
}

// Reactivate before period ends
async function reactivateSubscription(userId: string) {
  const sub = await getSubscription(userId);
  
  await stripe.subscriptions.update(sub.stripeSubscriptionId, {
    cancel_at_period_end: false,
  });
}
```

## Dunning (Failed Payment Recovery)

```typescript
// Handle failed payments
async function handlePaymentFailed(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;
  const user = await getUserByCustomerId(customerId);
  
  const attemptCount = invoice.attempt_count;
  
  if (attemptCount === 1) {
    await sendEmail(user.email, 'payment-failed-soft', {
      updatePaymentUrl: await getUpdatePaymentUrl(customerId),
    });
  } else if (attemptCount === 2) {
    await sendEmail(user.email, 'payment-failed-warning', {
      updatePaymentUrl: await getUpdatePaymentUrl(customerId),
      daysUntilCancellation: 7,
    });
  } else if (attemptCount >= 3) {
    await sendEmail(user.email, 'subscription-canceled', {
      reactivateUrl: `${APP_URL}/pricing`,
    });
  }
}

async function getUpdatePaymentUrl(customerId: string) {
  const session = await stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: `${APP_URL}/settings/billing`,
  });
  return session.url;
}
```

## Grace Period Access

```typescript
// Allow limited access during past_due
async function checkAccess(userId: string, feature: string): Promise<boolean> {
  const sub = await getSubscription(userId);
  
  if (!sub) return PLANS.free.features.includes(feature);
  
  if (sub.status === 'active' || sub.status === 'trialing') {
    return PLANS[sub.planId].features.includes(feature);
  }
  
  // Grace period: 7 days after going past_due
  if (sub.status === 'past_due') {
    const daysPastDue = Math.floor(
      (Date.now() - sub.currentPeriodEnd.getTime()) / (1000 * 60 * 60 * 24)
    );
    if (daysPastDue <= 7) {
      return PLANS[sub.planId].features.includes(feature);
    }
  }
  
  return false;
}
```
