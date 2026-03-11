# Stripe Plugin

> Integrate Stripe without reading 500 pages of docs. Covers payments, subscriptions, Connect marketplaces, billing, webhooks, and revenue optimization with ready-to-use patterns.

## Skills

### `stripe-agent`

Complete Stripe API integration covering payments, subscriptions, Connect marketplaces, and compliance.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Payment processing, subscriptions, marketplaces, billing, webhooks |

**Core capabilities:**
- **Payments** - Payment intents, checkout sessions, payment links
- **Subscriptions** - Recurring billing, metered usage, tiered pricing
- **Connect** - Marketplace payments, platform fees, seller onboarding
- **Billing** - Invoices, customer portal, tax calculation
- **Webhooks** - Event handling, subscription lifecycle
- **Security** - 3D Secure, SCA compliance, fraud prevention (Radar)
- **Disputes** - Chargeback handling, evidence submission

**Quick reference:**
| Task | Method |
|------|--------|
| Create customer | `stripe.Customer.create()` |
| Checkout session | `stripe.checkout.Session.create()` |
| Subscription | `stripe.Subscription.create()` |
| Payment link | `stripe.PaymentLink.create()` |
| Report usage | `stripe.SubscriptionItem.create_usage_record()` |
| Connect account | `stripe.Account.create(type="express")` |

**Prerequisites:**
```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
pip install stripe
```

---

### `revenue-optimizer`

Monetization expert that analyzes codebases to discover features, calculate service costs, model usage patterns, and create data-driven pricing strategies with revenue projections.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Feature cost analysis, pricing strategy, usage modeling, revenue projections, tier design |

**5-Phase Workflow:**
1. **Discover** - Scan codebase for features, services, and integrations
2. **Cost Analysis** - Calculate per-user and per-feature costs
3. **Design** - Create pricing tiers based on value + cost data
4. **Implement** - Build payment integration and checkout flows
5. **Optimize** - Add conversion optimization and revenue tracking

**Key Metrics Calculated:**
| Metric | Formula |
|--------|---------|
| ARPU | (Free x $0 + Pro x $X + Biz x $Y) / Total Users |
| LTV | (ARPU x Margin) / Monthly Churn |
| Break-even | Fixed Costs / (ARPU - Variable Cost) |
| Optimal Price | (Cost Floor x 0.3) + (Value Ceiling x 0.7) |
