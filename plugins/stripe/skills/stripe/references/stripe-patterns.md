# Stripe Integration Patterns - Detailed Examples

## Metered and Usage-Based Billing

For API calls, seats, or consumption-based pricing:

```python
# Create metered price
metered_price = stripe.Price.create(
    product="prod_xxx",
    currency="eur",
    recurring={"interval": "month", "usage_type": "metered"},
    billing_scheme="per_unit",
    unit_amount=10,  # 0.10 per unit
    lookup_key="api_calls"
)

# Report usage (do this periodically)
stripe.SubscriptionItem.create_usage_record(
    "si_xxx",  # subscription item id
    quantity=150,
    timestamp=int(datetime.now().timestamp()),
    action="increment"  # or "set" to override
)

# Tiered pricing
tiered_price = stripe.Price.create(
    product="prod_xxx",
    currency="eur",
    recurring={"interval": "month", "usage_type": "metered"},
    billing_scheme="tiered",
    tiers_mode="graduated",  # or "volume"
    tiers=[
        {"up_to": 100, "unit_amount": 50},      # First 100: 0.50 each
        {"up_to": 1000, "unit_amount": 30},     # 101-1000: 0.30 each
        {"up_to": "inf", "unit_amount": 10}     # 1001+: 0.10 each
    ]
)
```

## Stripe Connect (Marketplaces)

Build platforms where you facilitate payments between buyers and sellers:

```python
# Create connected account (Express - recommended)
account = stripe.Account.create(
    type="express",
    country="US",
    email="seller@example.com",
    capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}}
)

# Generate onboarding link
account_link = stripe.AccountLink.create(
    account=account.id,
    refresh_url="https://yourapp.com/reauth",
    return_url="https://yourapp.com/return",
    type="account_onboarding"
)
# Redirect seller to: account_link.url

# Create payment with platform fee (destination charge)
payment_intent = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    application_fee_amount=1000,  # Platform takes 10
    transfer_data={"destination": "acct_xxx"}  # Seller receives 90
)

# Direct charge (charge on connected account)
payment_intent = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    stripe_account="acct_xxx",  # Charge on seller's account
    application_fee_amount=1000
)

# Transfer funds to connected account
transfer = stripe.Transfer.create(
    amount=5000,
    currency="eur",
    destination="acct_xxx"
)
```

## Tax Calculation (Stripe Tax)

Automatic tax calculation and collection:

```python
# Enable automatic tax in checkout
session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[{"price": "price_xxx", "quantity": 1}],
    automatic_tax={"enabled": True},
    success_url="https://yourapp.com/success",
    cancel_url="https://yourapp.com/cancel"
)

# Tax calculation API (preview)
calculation = stripe.tax.Calculation.create(
    currency="eur",
    line_items=[{"amount": 1000, "reference": "L1"}],
    customer_details={"address": {"country": "DE"}, "address_source": "billing"}
)
```

## 3D Secure and SCA Compliance

Handle Strong Customer Authentication (required in EU/UK):

```python
# Payment intent with 3DS when required
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    payment_method="pm_xxx",
    confirmation_method="manual",
    confirm=True,
    return_url="https://yourapp.com/return"  # For 3DS redirect
)

# Check if authentication required
if payment_intent.status == "requires_action":
    # Redirect customer to: payment_intent.next_action.redirect_to_url.url
    pass

# Force 3DS (for high-risk transactions)
payment_intent = stripe.PaymentIntent.create(
    amount=50000,
    currency="eur",
    payment_method_options={
        "card": {"request_three_d_secure": "any"}  # or "automatic"
    }
)

# Webhook: handle authentication
# Event: payment_intent.requires_action
```

**Test cards for 3DS:**
- `4000002500003155` - Requires authentication
- `4000002760003184` - Always authenticates
- `4000008260003178` - Authentication fails

## Fraud Prevention (Stripe Radar)

Built-in fraud protection with Radar:

```python
# Payment with Radar rules
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    payment_method="pm_xxx",
    # Radar evaluates automatically
)

# Check radar outcome after payment
charge = stripe.Charge.retrieve("ch_xxx")
radar_outcome = charge.outcome
# radar_outcome.risk_level: "normal", "elevated", "highest"
# radar_outcome.risk_score: 0-100

# Custom metadata for Radar rules
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    metadata={
        "customer_account_age": "30",  # days
        "order_count": "5"
    }
)

# Block high-risk in Radar Dashboard:
# Rule: "Block if :risk_level: = 'highest'"
# Rule: "Review if ::customer_account_age:: < 7"
```

## Dispute Handling

Manage chargebacks and disputes:

```python
# List disputes
disputes = stripe.Dispute.list(limit=10)

# Retrieve dispute details
dispute = stripe.Dispute.retrieve("dp_xxx")
# dispute.reason: "fraudulent", "duplicate", "product_not_received", etc.
# dispute.status: "needs_response", "under_review", "won", "lost"

# Submit evidence
stripe.Dispute.modify(
    "dp_xxx",
    evidence={
        "customer_name": "John Doe",
        "customer_email_address": "john@example.com",
        "shipping_tracking_number": "1Z999AA10123456784",
        "uncategorized_text": "Customer confirmed receipt via email on..."
    },
    submit=True  # Submit evidence
)

# Webhook events for disputes
# charge.dispute.created - New dispute opened
# charge.dispute.updated - Evidence submitted or status changed
# charge.dispute.closed - Dispute resolved
```

## Idempotency and Best Practices

Prevent duplicate operations:

```python
import uuid

# Idempotent request (safe to retry)
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    idempotency_key=f"order_{order_id}"  # Unique per operation
)

# For retries, use same key
try:
    payment = stripe.PaymentIntent.create(
        amount=2000,
        currency="eur",
        idempotency_key="order_123"
    )
except stripe.error.StripeError:
    # Safe to retry with same idempotency_key
    payment = stripe.PaymentIntent.create(
        amount=2000,
        currency="eur",
        idempotency_key="order_123"
    )

# Generate unique keys
def idempotency_key(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"
```

**Best Practices:**
1. Always use idempotency keys for create/update operations
2. Store payment intent ID before confirming
3. Use webhooks as source of truth (not API responses)
4. Handle `requires_action` status for 3DS
5. Never log full card numbers or CVV
6. Use test mode for development (`sk_test_...`)
