# Pricing Tier Patterns

## Good-Better-Best (3-Tier)

Most effective for SaaS. Anchor users to middle tier.

```typescript
const PLANS = {
  starter: {
    id: 'starter',
    name: 'Starter',
    price: { monthly: 9, yearly: 90 },
    features: ['5 projects', '1 user', 'Basic support', '1GB storage'],
    limits: { projects: 5, users: 1, storage: 1_000_000_000 },
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    price: { monthly: 29, yearly: 290 },
    features: ['Unlimited projects', '5 users', 'Priority support', '10GB storage', 'Advanced analytics'],
    limits: { projects: Infinity, users: 5, storage: 10_000_000_000 },
    recommended: true, // Highlight this tier
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    price: { monthly: 99, yearly: 990 },
    features: ['Everything in Pro', 'Unlimited users', 'SSO/SAML', 'Custom integrations', 'Dedicated support'],
    limits: { projects: Infinity, users: Infinity, storage: 100_000_000_000 },
  },
};
```

## Freemium Model

```typescript
const PLANS = {
  free: {
    id: 'free',
    name: 'Free',
    price: { monthly: 0, yearly: 0 },
    features: ['3 projects', 'Basic features', 'Community support'],
    limits: { projects: 3, apiCalls: 100 },
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    price: { monthly: 19, yearly: 190 },
    features: ['Unlimited projects', 'All features', 'Email support'],
    limits: { projects: Infinity, apiCalls: 10000 },
  },
};
```

## Usage-Based / Metered

```typescript
const PLANS = {
  payAsYouGo: {
    id: 'pay_as_you_go',
    name: 'Pay As You Go',
    basePrice: 0,
    usage: [
      { metric: 'api_calls', price: 0.001, unit: 'per call' },
      { metric: 'storage', price: 0.02, unit: 'per GB/month' },
    ],
  },
  business: {
    id: 'business',
    name: 'Business',
    basePrice: 99,
    included: { api_calls: 50000, storage: 50 },
    overage: [
      { metric: 'api_calls', price: 0.0005, unit: 'per call' },
      { metric: 'storage', price: 0.01, unit: 'per GB/month' },
    ],
  },
};
```

## Per-Seat Pricing

```typescript
const PLAN = {
  id: 'team',
  name: 'Team',
  pricePerSeat: { monthly: 12, yearly: 120 },
  minimumSeats: 3,
  features: ['All features', 'Team collaboration', 'Admin controls'],
};

function calculatePrice(seats: number, interval: 'monthly' | 'yearly') {
  const effectiveSeats = Math.max(seats, PLAN.minimumSeats);
  return effectiveSeats * PLAN.pricePerSeat[interval];
}
```

## Hybrid: Base + Seats + Usage

```typescript
const PLAN = {
  basePrice: { monthly: 49, yearly: 490 },
  includedSeats: 5,
  additionalSeatPrice: { monthly: 10, yearly: 100 },
  usage: {
    apiCalls: { included: 10000, overagePrice: 0.001 },
  },
};
```

## Entitlement Check Implementation

```typescript
// types/plans.ts
interface PlanLimits {
  projects: number;
  users: number;
  storage: number;
  features: string[];
}

// lib/entitlements.ts
export async function canAccessFeature(userId: string, feature: string): Promise<boolean> {
  const sub = await getSubscription(userId);
  if (!sub || sub.status !== 'active') return false;
  return PLANS[sub.planId].features.includes(feature);
}

export async function checkLimit(userId: string, resource: string, current: number): Promise<boolean> {
  const sub = await getSubscription(userId);
  const plan = sub ? PLANS[sub.planId] : PLANS.free;
  return current < plan.limits[resource];
}

// Usage
if (!await canAccessFeature(user.id, 'advanced_analytics')) {
  throw new UpgradeRequiredError('advanced_analytics');
}
```

## Feature Matrix Display

```tsx
function PricingTable() {
  const features = [
    { name: 'Projects', starter: '5', pro: 'Unlimited', enterprise: 'Unlimited' },
    { name: 'Team members', starter: '1', pro: '5', enterprise: 'Unlimited' },
    { name: 'Storage', starter: '1 GB', pro: '10 GB', enterprise: '100 GB' },
    { name: 'API access', starter: false, pro: true, enterprise: true },
    { name: 'SSO/SAML', starter: false, pro: false, enterprise: true },
    { name: 'Support', starter: 'Community', pro: 'Priority', enterprise: 'Dedicated' },
  ];
  
  return (
    <table>
      <thead>
        <tr>
          <th>Feature</th>
          {Object.keys(PLANS).map(plan => <th key={plan}>{PLANS[plan].name}</th>)}
        </tr>
      </thead>
      <tbody>
        {features.map(f => (
          <tr key={f.name}>
            <td>{f.name}</td>
            <td>{renderValue(f.starter)}</td>
            <td>{renderValue(f.pro)}</td>
            <td>{renderValue(f.enterprise)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

## Pricing Psychology Tips

- **Anchor high**: Show enterprise first or highlight middle tier
- **Annual discount**: 15-20% off encourages commitment
- **Round numbers**: $29 feels simpler than $29.99 for B2B
- **Limit free tier**: Enough to hook, not enough to satisfy
- **Feature differentiation**: Each tier should have 1-2 "hero" features
