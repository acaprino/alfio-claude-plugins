# Usage Patterns & Revenue Modeling

## Usage Pattern Analysis

### Detecting Usage Patterns from Code

Scan codebase for usage tracking and analytics:

```typescript
// Look for these patterns in code
const USAGE_INDICATORS = {
  // Analytics events
  'track(': 'Event tracking',
  'analytics.': 'Analytics SDK',
  'mixpanel.': 'Mixpanel events',
  'amplitude.': 'Amplitude events',
  'posthog.': 'PostHog events',
  
  // Rate limiting (indicates metered features)
  'rateLimit': 'Rate-limited endpoint',
  'rateLimiter': 'Rate limiting',
  'quota': 'Quota tracking',
  
  // Usage counters
  'increment': 'Usage counter',
  'usageCount': 'Usage tracking',
  'apiCalls': 'API usage',
};
```

### Usage Pattern Categories

```
Usage Patterns:
├── Frequency-Based
│   ├── Daily Active (core features)
│   ├── Weekly Active (reports, exports)
│   └── Monthly Active (admin, settings)
├── Volume-Based
│   ├── API calls per period
│   ├── Storage consumption
│   ├── Bandwidth usage
│   └── Compute time
├── Event-Based
│   ├── Transactions processed
│   ├── Messages sent
│   ├── Documents generated
│   └── AI requests made
└── Seat-Based
    ├── Active team members
    ├── Concurrent users
    └── Named users
```

### Usage Estimation Framework

```typescript
interface UsageProfile {
  feature: string;
  usageType: 'frequency' | 'volume' | 'event';
  
  // Estimated usage per user segment
  casual: number;    // Light users (bottom 50%)
  regular: number;   // Average users (middle 40%)
  power: number;     // Heavy users (top 10%)
  
  unit: string;      // 'per day' | 'per month' | 'per GB'
  costPerUnit: number;
}

const USAGE_PROFILES: UsageProfile[] = [
  {
    feature: 'API calls',
    usageType: 'event',
    casual: 50,
    regular: 500,
    power: 5000,
    unit: 'per month',
    costPerUnit: 0.001,
  },
  {
    feature: 'AI generations',
    usageType: 'event',
    casual: 5,
    regular: 50,
    power: 500,
    unit: 'per month',
    costPerUnit: 0.03,
  },
  {
    feature: 'Storage',
    usageType: 'volume',
    casual: 0.1,
    regular: 1,
    power: 10,
    unit: 'GB',
    costPerUnit: 0.023,
  },
  {
    feature: 'PDF exports',
    usageType: 'event',
    casual: 2,
    regular: 20,
    power: 100,
    unit: 'per month',
    costPerUnit: 0.01,
  },
];
```

## Revenue Modeling

### Key Metrics

```typescript
interface RevenueMetrics {
  // Average Revenue Per User
  arpu: {
    monthly: number;
    annual: number;
  };
  
  // Lifetime Value
  ltv: number;
  
  // Customer Acquisition Cost ratio
  ltvToCac: number;
  
  // Monthly Recurring Revenue
  mrr: number;
  
  // Annual Recurring Revenue
  arr: number;
  
  // Churn rate
  monthlyChurn: number;
  
  // Net Revenue Retention
  nrr: number;
}
```

### ARPU Calculation by Tier

```typescript
function calculateARPU(tierDistribution: TierDistribution): number {
  // Typical SaaS distribution
  const distribution = {
    free: { percent: 0.80, price: 0 },
    starter: { percent: 0.12, price: 9 },
    pro: { percent: 0.06, price: 29 },
    enterprise: { percent: 0.02, price: 99 },
  };
  
  const arpu = Object.values(distribution).reduce(
    (sum, tier) => sum + (tier.percent * tier.price),
    0
  );
  
  return arpu; // e.g., $4.80 blended ARPU
}
```

### LTV Calculation

```typescript
function calculateLTV(
  arpu: number,
  monthlyChurnRate: number,
  grossMargin: number = 0.80
): number {
  // LTV = (ARPU × Gross Margin) / Churn Rate
  const avgLifetimeMonths = 1 / monthlyChurnRate;
  return arpu * grossMargin * avgLifetimeMonths;
}

// Example:
// ARPU: $29, Churn: 5%, Margin: 80%
// LTV = ($29 × 0.80) / 0.05 = $464
```

### Revenue Projection Model

```typescript
interface RevenueProjection {
  month: number;
  users: number;
  paying: number;
  mrr: number;
  costs: number;
  profit: number;
  margin: number;
}

function projectRevenue(
  initialUsers: number,
  monthlyGrowthRate: number,
  conversionRate: number,
  arpu: number,
  costPerUser: number,
  months: number
): RevenueProjection[] {
  const projections: RevenueProjection[] = [];
  let users = initialUsers;
  
  for (let month = 1; month <= months; month++) {
    users = Math.floor(users * (1 + monthlyGrowthRate));
    const paying = Math.floor(users * conversionRate);
    const mrr = paying * arpu;
    const costs = users * costPerUser;
    const profit = mrr - costs;
    const margin = mrr > 0 ? (profit / mrr) * 100 : 0;
    
    projections.push({ month, users, paying, mrr, costs, profit, margin });
  }
  
  return projections;
}
```

## Tier Optimization

### Usage-Based Tier Limits

```typescript
interface TierLimits {
  tier: string;
  limits: {
    feature: string;
    limit: number;
    percentileTarget: number; // What % of users stay under limit
  }[];
}

// Set limits so most users stay within tier
const TIER_LIMITS: TierLimits[] = [
  {
    tier: 'free',
    limits: [
      { feature: 'API calls', limit: 100, percentileTarget: 0.80 },
      { feature: 'Storage', limit: 0.5, percentileTarget: 0.90 },
      { feature: 'AI generations', limit: 10, percentileTarget: 0.95 },
    ],
  },
  {
    tier: 'pro',
    limits: [
      { feature: 'API calls', limit: 5000, percentileTarget: 0.95 },
      { feature: 'Storage', limit: 10, percentileTarget: 0.95 },
      { feature: 'AI generations', limit: 100, percentileTarget: 0.90 },
    ],
  },
];
```

### Optimal Pricing Calculator

```typescript
interface PricingRecommendation {
  tier: string;
  recommendedPrice: number;
  priceRange: { min: number; max: number };
  rationale: string;
}

function calculateOptimalPrice(
  costToServe: number,
  perceivedValue: number,
  competitorPrice: number,
  targetMargin: number
): PricingRecommendation {
  // Price floor: cost + minimum margin
  const priceFloor = costToServe / (1 - targetMargin);
  
  // Price ceiling: perceived value or competitor price
  const priceCeiling = Math.min(perceivedValue, competitorPrice * 1.2);
  
  // Optimal: weighted average leaning toward value
  const optimal = priceFloor * 0.3 + priceCeiling * 0.7;
  
  return {
    tier: 'calculated',
    recommendedPrice: Math.round(optimal),
    priceRange: { 
      min: Math.round(priceFloor), 
      max: Math.round(priceCeiling) 
    },
    rationale: `Cost floor: $${priceFloor.toFixed(2)}, Value ceiling: $${priceCeiling.toFixed(2)}`,
  };
}
```

### Revenue per Tier Analysis

```typescript
interface TierRevenue {
  tier: string;
  price: number;
  estimatedUsers: number;
  conversionRate: number;
  monthlyRevenue: number;
  costToServe: number;
  grossProfit: number;
  margin: number;
}

function analyzeTierRevenue(tiers: TierConfig[]): TierRevenue[] {
  return tiers.map(tier => {
    const paying = tier.estimatedUsers * tier.conversionRate;
    const revenue = paying * tier.price;
    const costs = tier.estimatedUsers * tier.costPerUser;
    const profit = revenue - costs;
    
    return {
      tier: tier.name,
      price: tier.price,
      estimatedUsers: tier.estimatedUsers,
      conversionRate: tier.conversionRate,
      monthlyRevenue: revenue,
      costToServe: costs,
      grossProfit: profit,
      margin: revenue > 0 ? (profit / revenue) * 100 : 0,
    };
  });
}
```

## Consumption Tracking Implementation

### Database Schema for Usage Tracking

```sql
CREATE TABLE usage_events (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  feature VARCHAR(100) NOT NULL,
  quantity INTEGER DEFAULT 1,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE usage_aggregates (
  user_id UUID REFERENCES users(id),
  feature VARCHAR(100) NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  total_usage INTEGER DEFAULT 0,
  PRIMARY KEY (user_id, feature, period_start)
);

-- Index for fast lookups
CREATE INDEX idx_usage_user_period ON usage_aggregates(user_id, period_start);
```

### Usage Tracking Service

```typescript
class UsageTracker {
  async trackUsage(userId: string, feature: string, quantity: number = 1) {
    // Record event
    await db.usageEvent.create({
      data: { userId, feature, quantity },
    });
    
    // Update aggregate
    const periodStart = startOfMonth(new Date());
    await db.usageAggregate.upsert({
      where: { userId_feature_periodStart: { userId, feature, periodStart } },
      update: { totalUsage: { increment: quantity } },
      create: { userId, feature, periodStart, totalUsage: quantity },
    });
  }
  
  async getUsage(userId: string, feature: string): Promise<number> {
    const periodStart = startOfMonth(new Date());
    const aggregate = await db.usageAggregate.findUnique({
      where: { userId_feature_periodStart: { userId, feature, periodStart } },
    });
    return aggregate?.totalUsage ?? 0;
  }
  
  async checkLimit(userId: string, feature: string): Promise<boolean> {
    const usage = await this.getUsage(userId, feature);
    const plan = await this.getUserPlan(userId);
    const limit = plan.limits[feature] ?? Infinity;
    return usage < limit;
  }
}
```

### Usage Analytics Queries

```sql
-- Average usage per feature by tier
SELECT 
  s.plan_id,
  ue.feature,
  AVG(ua.total_usage) as avg_usage,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ua.total_usage) as median_usage,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY ua.total_usage) as p90_usage,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ua.total_usage) as p99_usage
FROM usage_aggregates ua
JOIN subscriptions s ON ua.user_id = s.user_id
WHERE ua.period_start = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY s.plan_id, ue.feature;

-- Users approaching limits (upgrade candidates)
SELECT 
  u.id,
  u.email,
  ua.feature,
  ua.total_usage,
  p.limits->ua.feature as tier_limit,
  (ua.total_usage::float / (p.limits->ua.feature)::float * 100) as usage_percent
FROM usage_aggregates ua
JOIN users u ON ua.user_id = u.id
JOIN subscriptions s ON u.id = s.user_id
JOIN plans p ON s.plan_id = p.id
WHERE ua.period_start = DATE_TRUNC('month', CURRENT_DATE)
  AND ua.total_usage::float / (p.limits->ua.feature)::float > 0.8;
```

## Industry Benchmarks

### SaaS Metrics Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Monthly Churn | >5% | 3-5% | 1-3% | <1% |
| Free→Paid Conversion | <2% | 2-5% | 5-10% | >10% |
| Net Revenue Retention | <90% | 90-100% | 100-120% | >120% |
| LTV:CAC Ratio | <1:1 | 1:1-3:1 | 3:1-5:1 | >5:1 |
| Gross Margin | <60% | 60-70% | 70-80% | >80% |

### Pricing Benchmarks by Category

| Category | Free Tier | Starter | Pro | Enterprise |
|----------|-----------|---------|-----|------------|
| Dev Tools | Yes | $9-19 | $29-49 | $99-299 |
| Productivity | Limited | $5-12 | $15-25 | $30-50/seat |
| AI/ML Tools | Credits | $20-50 | $100-200 | Custom |
| Analytics | Yes | $29-49 | $99-199 | $500+ |
| Marketing | Yes | $19-49 | $99-199 | $299+ |
