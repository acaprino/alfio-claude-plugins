# Checkout Optimization

## High-Converting Pricing Page

```tsx
function PricingPage() {
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('yearly');
  
  return (
    <div className="pricing-page">
      {/* Billing Toggle */}
      <div className="billing-toggle">
        <button onClick={() => setBillingInterval('monthly')}>Monthly</button>
        <button onClick={() => setBillingInterval('yearly')}>
          Yearly <span className="discount-badge">Save 20%</span>
        </button>
      </div>
      
      {/* Plan Cards */}
      <div className="plan-cards">
        {Object.values(PLANS).map(plan => (
          <PlanCard 
            key={plan.id}
            plan={plan}
            interval={billingInterval}
            recommended={plan.recommended}
          />
        ))}
      </div>
      
      {/* Trust Signals */}
      <TrustSignals />
      
      {/* FAQ */}
      <PricingFAQ />
    </div>
  );
}
```

## Plan Card with Conversion Elements

```tsx
function PlanCard({ plan, interval, recommended }) {
  return (
    <div className={`plan-card ${recommended ? 'recommended' : ''}`}>
      {recommended && <div className="badge">Most Popular</div>}
      
      <h3>{plan.name}</h3>
      
      <div className="price">
        <span className="amount">${plan.price[interval]}</span>
        <span className="interval">/{interval === 'yearly' ? 'year' : 'month'}</span>
      </div>
      
      {interval === 'yearly' && (
        <div className="savings">
          Save ${plan.price.monthly * 12 - plan.price.yearly}/year
        </div>
      )}
      
      <ul className="features">
        {plan.features.map(f => (
          <li key={f}><CheckIcon /> {f}</li>
        ))}
      </ul>
      
      <button 
        className={recommended ? 'cta-primary' : 'cta-secondary'}
        onClick={() => startCheckout(plan.id, interval)}
      >
        {plan.price.monthly === 0 ? 'Start Free' : 'Get Started'}
      </button>
      
      {plan.price.monthly > 0 && (
        <p className="guarantee">14-day money-back guarantee</p>
      )}
    </div>
  );
}
```

## Trust Signals Component

```tsx
function TrustSignals() {
  return (
    <div className="trust-signals">
      <div className="signal">
        <ShieldIcon />
        <span>256-bit SSL encryption</span>
      </div>
      <div className="signal">
        <RefundIcon />
        <span>14-day money-back guarantee</span>
      </div>
      <div className="signal">
        <CancelIcon />
        <span>Cancel anytime</span>
      </div>
      
      {/* Social Proof */}
      <div className="social-proof">
        <div className="customer-logos">
          <img src="/logos/company1.svg" alt="Company 1" />
          <img src="/logos/company2.svg" alt="Company 2" />
        </div>
        <p>Trusted by 10,000+ teams</p>
      </div>
      
      {/* Testimonial */}
      <blockquote className="testimonial">
        "This tool has 10x'd our productivity."
        <cite>— Jane D., CEO at TechCo</cite>
      </blockquote>
    </div>
  );
}
```

## Checkout Flow Best Practices

### 1. Minimize Steps

```tsx
// BAD: Multi-page checkout
// Page 1: Select plan → Page 2: Account → Page 3: Billing → Page 4: Confirm

// GOOD: Single page or 2-step max
// Step 1: Plan + Email → Step 2: Payment (Stripe Checkout handles this)
```

### 2. Pre-fill Known Data

```typescript
const session = await stripe.checkout.sessions.create({
  customer_email: user.email, // Pre-fill email
  customer: user.stripeCustomerId, // Use existing customer
  client_reference_id: user.id,
  // ...
});
```

### 3. Show Price Breakdown

```tsx
function CheckoutSummary({ plan, interval, coupon }) {
  const basePrice = plan.price[interval];
  const discount = coupon ? basePrice * coupon.percentOff / 100 : 0;
  const total = basePrice - discount;
  
  return (
    <div className="checkout-summary">
      <div className="line-item">
        <span>{plan.name} ({interval})</span>
        <span>${basePrice}</span>
      </div>
      {coupon && (
        <div className="line-item discount">
          <span>Discount ({coupon.code})</span>
          <span>-${discount}</span>
        </div>
      )}
      <div className="line-item total">
        <span>Total</span>
        <span>${total}</span>
      </div>
    </div>
  );
}
```

## Upgrade Prompts (Conversion Triggers)

### Feature Gate Prompt

```tsx
function FeatureGate({ feature, children }) {
  const { hasAccess, requiredPlan } = useFeatureAccess(feature);
  
  if (hasAccess) return children;
  
  return (
    <div className="feature-gate">
      <LockIcon />
      <h3>Unlock {feature}</h3>
      <p>Upgrade to {requiredPlan} to access this feature.</p>
      <button onClick={() => showUpgradeModal(requiredPlan)}>
        Upgrade Now
      </button>
    </div>
  );
}
```

### Usage Limit Prompt

```tsx
function UsageLimitBanner({ resource, current, limit }) {
  const percentage = (current / limit) * 100;
  
  if (percentage < 80) return null;
  
  return (
    <div className={`usage-banner ${percentage >= 100 ? 'exceeded' : 'warning'}`}>
      <p>
        You've used {current} of {limit} {resource}.
        {percentage >= 100 ? ' Upgrade to continue.' : ' Consider upgrading.'}
      </p>
      <button onClick={showUpgradeModal}>Upgrade</button>
    </div>
  );
}
```

### Trial Ending Prompt

```tsx
function TrialBanner({ daysLeft }) {
  if (daysLeft > 3) return null;
  
  return (
    <div className="trial-banner">
      <p>
        Your trial ends in {daysLeft} day{daysLeft !== 1 ? 's' : ''}.
        Subscribe now to keep your data.
      </p>
      <button onClick={showSubscribeModal}>Subscribe</button>
    </div>
  );
}
```

## Coupon/Promo Codes

```typescript
// Enable promo codes in checkout
const session = await stripe.checkout.sessions.create({
  allow_promotion_codes: true, // User can enter codes
  // OR apply a specific coupon
  discounts: [{ coupon: 'LAUNCH20' }],
});

// Create coupon programmatically
const coupon = await stripe.coupons.create({
  percent_off: 20,
  duration: 'once', // or 'forever', 'repeating'
  id: 'LAUNCH20',
});
```

## A/B Testing Checkout

```tsx
function PricingPage() {
  const variant = useExperiment('pricing-page-v2');
  
  // Track view
  useEffect(() => {
    track('pricing_page_viewed', { variant });
  }, []);
  
  // Track conversion
  const handleCheckout = (plan) => {
    track('checkout_started', { variant, plan });
    startCheckout(plan);
  };
  
  if (variant === 'control') return <PricingPageV1 onCheckout={handleCheckout} />;
  return <PricingPageV2 onCheckout={handleCheckout} />;
}
```

## Conversion Tracking Events

```typescript
// Track full funnel
const CONVERSION_EVENTS = [
  'pricing_page_viewed',
  'plan_selected',
  'checkout_started',
  'checkout_completed',
  'subscription_activated',
];

// Implementation
function trackConversion(event: string, data: object) {
  // Analytics (Mixpanel, Amplitude, etc.)
  analytics.track(event, data);
  
  // Google Analytics
  gtag('event', event, data);
  
  // Meta/Facebook Pixel
  if (event === 'checkout_completed') {
    fbq('track', 'Purchase', { value: data.amount, currency: 'USD' });
  }
}
```
