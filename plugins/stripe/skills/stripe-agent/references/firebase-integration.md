# Firebase + Stripe Integration Guide

This guide covers integrating Stripe payments with Firebase/Firestore for subscription-based web applications.

## Architecture Overview

The integration follows this pattern:

1. **Frontend** creates Checkout Sessions via Cloud Functions
2. **Stripe** handles payment collection securely
3. **Webhooks** sync subscription state to Firestore
4. **Security Rules** control access based on subscription status

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│ Cloud Func   │────▶│   Stripe    │
│   (React)   │     │  (Backend)   │     │   Checkout  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                    ┌──────────────┐              │
                    │  Firestore   │◀─────────────┘
                    │  (Database)  │    Webhooks update
                    └──────┬───────┘    subscription status
                           │
                    ┌──────▼───────┐
                    │   Security   │
                    │    Rules     │
                    └──────────────┘
```

## Firestore Data Model

### Users Collection

```
/users/{userId}
{
  email: "user@example.com",
  displayName: "John Doe",
  createdAt: Timestamp,
  
  // Stripe data
  stripeCustomerId: "cus_xxx",
  
  // Subscription (synced by webhooks)
  subscription: {
    status: "active" | "trialing" | "past_due" | "canceled" | "none",
    plan: "pro_monthly",
    subscriptionId: "sub_xxx",
    currentPeriodEnd: Timestamp,
    cancelAtPeriodEnd: false
  }
}
```

### Products Collection (Optional - for dynamic pricing)

```
/products/{productId}
{
  name: "Pro Plan",
  description: "Full access",
  active: true,
  
  // Prices subcollection
  /prices/{priceId}
  {
    unit_amount: 999,
    currency: "eur",
    interval: "month",
    lookup_key: "pro_monthly"
  }
}
```

## Cloud Functions Implementation

### 1. Create Checkout Session

```typescript
// functions/src/stripe.ts
import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

admin.initializeApp();
const db = admin.firestore();

export const createCheckoutSession = functions.https.onCall(
  async (data, context) => {
    // Require authentication
    if (!context.auth) {
      throw new functions.https.HttpsError(
        'unauthenticated',
        'Must be logged in'
      );
    }

    const userId = context.auth.uid;
    const { priceId, successUrl, cancelUrl } = data;

    // Get or create Stripe customer
    const userDoc = await db.collection('users').doc(userId).get();
    const userData = userDoc.data();
    
    let customerId = userData?.stripeCustomerId;
    
    if (!customerId) {
      // Create new Stripe customer
      const customer = await stripe.customers.create({
        email: context.auth.token.email,
        metadata: { firebaseUID: userId }
      });
      
      customerId = customer.id;
      
      // Save to Firestore
      await db.collection('users').doc(userId).set(
        { stripeCustomerId: customerId },
        { merge: true }
      );
    }

    // Create checkout session
    const session = await stripe.checkout.Session.create({
      customer: customerId,
      mode: 'subscription',
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: { firebaseUID: userId }
    });

    return { sessionId: session.id, url: session.url };
  }
);
```

### 2. Create Billing Portal Session

```typescript
export const createPortalSession = functions.https.onCall(
  async (data, context) => {
    if (!context.auth) {
      throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
    }

    const userId = context.auth.uid;
    const userDoc = await db.collection('users').doc(userId).get();
    const customerId = userDoc.data()?.stripeCustomerId;

    if (!customerId) {
      throw new functions.https.HttpsError('not-found', 'No subscription found');
    }

    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: data.returnUrl
    });

    return { url: session.url };
  }
);
```

### 3. Webhook Handler

```typescript
export const stripeWebhook = functions.https.onRequest(async (req, res) => {
  const sig = req.headers['stripe-signature'] as string;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(req.rawBody, sig, webhookSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    res.status(400).send(`Webhook Error: ${err}`);
    return;
  }

  // Handle events
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutComplete(session);
      break;
    }
    
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      await syncSubscriptionToFirestore(subscription);
      break;
    }
    
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentFailed(invoice);
      break;
    }
  }

  res.json({ received: true });
});

async function handleCheckoutComplete(session: Stripe.Checkout.Session) {
  const customerId = session.customer as string;
  const subscriptionId = session.subscription as string;

  // Find user by customer ID
  const usersRef = db.collection('users');
  const snapshot = await usersRef
    .where('stripeCustomerId', '==', customerId)
    .limit(1)
    .get();

  if (snapshot.empty) {
    console.error('No user found for customer:', customerId);
    return;
  }

  const userDoc = snapshot.docs[0];
  
  // Get full subscription details
  const subscription = await stripe.subscriptions.retrieve(subscriptionId);
  
  // Update user document
  await userDoc.ref.update({
    subscription: {
      status: subscription.status,
      subscriptionId: subscription.id,
      plan: subscription.items.data[0].price.lookup_key || subscription.items.data[0].price.id,
      currentPeriodEnd: admin.firestore.Timestamp.fromMillis(subscription.current_period_end * 1000),
      cancelAtPeriodEnd: subscription.cancel_at_period_end
    }
  });
}

async function syncSubscriptionToFirestore(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;
  
  const usersRef = db.collection('users');
  const snapshot = await usersRef
    .where('stripeCustomerId', '==', customerId)
    .limit(1)
    .get();

  if (snapshot.empty) return;

  const userDoc = snapshot.docs[0];
  
  const subscriptionData = {
    status: subscription.status,
    subscriptionId: subscription.id,
    plan: subscription.items.data[0].price.lookup_key || subscription.items.data[0].price.id,
    currentPeriodEnd: admin.firestore.Timestamp.fromMillis(subscription.current_period_end * 1000),
    cancelAtPeriodEnd: subscription.cancel_at_period_end
  };

  await userDoc.ref.update({ subscription: subscriptionData });
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  // Optionally notify user, update UI state, etc.
  console.log('Payment failed for invoice:', invoice.id);
}
```

## Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Helper function to check subscription status
    function hasActiveSubscription() {
      return get(/databases/$(database)/documents/users/$(request.auth.uid)).data.subscription.status in ['active', 'trialing'];
    }
    
    function isPremiumPlan() {
      let sub = get(/databases/$(database)/documents/users/$(request.auth.uid)).data.subscription;
      return sub.status in ['active', 'trialing'] && sub.plan in ['pro_monthly', 'pro_yearly', 'enterprise_monthly', 'enterprise_yearly'];
    }
    
    // Users can read/write their own data
    match /users/{userId} {
      allow read: if request.auth.uid == userId;
      allow write: if request.auth.uid == userId && 
                      !request.resource.data.diff(resource.data).affectedKeys()
                        .hasAny(['stripeCustomerId', 'subscription']);
    }
    
    // Premium content - requires active subscription
    match /premium/{document=**} {
      allow read: if request.auth != null && hasActiveSubscription();
    }
    
    // Pro-only features
    match /pro-features/{document=**} {
      allow read, write: if request.auth != null && isPremiumPlan();
    }
  }
}
```

## Frontend Implementation (React)

### Checkout Button Component

```tsx
import { getFunctions, httpsCallable } from 'firebase/functions';
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLIC_KEY!);

export function CheckoutButton({ priceId }: { priceId: string }) {
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    setLoading(true);
    
    try {
      const functions = getFunctions();
      const createCheckout = httpsCallable(functions, 'createCheckoutSession');
      
      const { data } = await createCheckout({
        priceId,
        successUrl: `${window.location.origin}/success`,
        cancelUrl: `${window.location.origin}/pricing`
      });
      
      // Redirect to Stripe Checkout
      window.location.href = (data as any).url;
      
    } catch (error) {
      console.error('Checkout error:', error);
      setLoading(false);
    }
  };

  return (
    <button onClick={handleCheckout} disabled={loading}>
      {loading ? 'Loading...' : 'Subscribe'}
    </button>
  );
}
```

### Subscription Status Hook

```tsx
import { useEffect, useState } from 'react';
import { doc, onSnapshot } from 'firebase/firestore';
import { useAuth } from './useAuth';
import { db } from './firebase';

interface Subscription {
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'none';
  plan: string;
  currentPeriodEnd: Date;
  cancelAtPeriodEnd: boolean;
}

export function useSubscription() {
  const { user } = useAuth();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setSubscription(null);
      setLoading(false);
      return;
    }

    const unsubscribe = onSnapshot(
      doc(db, 'users', user.uid),
      (doc) => {
        const data = doc.data();
        if (data?.subscription) {
          setSubscription({
            ...data.subscription,
            currentPeriodEnd: data.subscription.currentPeriodEnd.toDate()
          });
        } else {
          setSubscription({ status: 'none', plan: '', currentPeriodEnd: new Date(), cancelAtPeriodEnd: false });
        }
        setLoading(false);
      }
    );

    return unsubscribe;
  }, [user]);

  const isActive = subscription?.status === 'active' || subscription?.status === 'trialing';
  const isPro = isActive && ['pro_monthly', 'pro_yearly'].includes(subscription?.plan || '');

  return { subscription, loading, isActive, isPro };
}
```

### Manage Subscription Button

```tsx
export function ManageSubscriptionButton() {
  const [loading, setLoading] = useState(false);

  const handleManage = async () => {
    setLoading(true);
    
    try {
      const functions = getFunctions();
      const createPortal = httpsCallable(functions, 'createPortalSession');
      
      const { data } = await createPortal({
        returnUrl: window.location.href
      });
      
      window.location.href = (data as any).url;
      
    } catch (error) {
      console.error('Portal error:', error);
      setLoading(false);
    }
  };

  return (
    <button onClick={handleManage} disabled={loading}>
      {loading ? 'Loading...' : 'Manage Subscription'}
    </button>
  );
}
```

## Deployment Checklist

1. **Environment Variables**
   - Set `STRIPE_SECRET_KEY` in Cloud Functions config
   - Set `STRIPE_WEBHOOK_SECRET` in Cloud Functions config
   - Set `REACT_APP_STRIPE_PUBLIC_KEY` in frontend .env

2. **Stripe Dashboard**
   - Create products and prices
   - Configure Customer Portal settings
   - Set up webhook endpoint pointing to your Cloud Function

3. **Firebase**
   - Deploy Cloud Functions
   - Update Firestore Security Rules
   - Enable required Firebase services

4. **Testing**
   - Use Stripe test mode
   - Test complete checkout flow
   - Verify webhook events are processed
   - Test subscription cancellation and reactivation
