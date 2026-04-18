# Stripe API Quick Reference

Fast lookup for common Stripe API operations.

## Authentication

```python
import stripe
stripe.api_key = "sk_test_..." # or sk_live_...
```

## Customers

```python
# Create
customer = stripe.Customer.create(
    email="user@example.com",
    name="John Doe",
    metadata={"user_id": "123"}
)

# Retrieve
customer = stripe.Customer.retrieve("cus_xxx")

# Update
stripe.Customer.modify("cus_xxx", name="Jane Doe")

# Delete
stripe.Customer.delete("cus_xxx")

# List
customers = stripe.Customer.list(limit=10, email="user@example.com")

# Search
results = stripe.Customer.search(query="email:'user@example.com'")
```

## Products

```python
# Create
product = stripe.Product.create(
    name="Pro Plan",
    description="Premium features",
    metadata={"tier": "pro"}
)

# Retrieve
product = stripe.Product.retrieve("prod_xxx")

# Update
stripe.Product.modify("prod_xxx", name="New Name")

# Archive (soft delete)
stripe.Product.modify("prod_xxx", active=False)

# List
products = stripe.Product.list(active=True, limit=10)
```

## Prices

```python
# Create recurring (subscription)
price = stripe.Price.create(
    product="prod_xxx",
    unit_amount=1999,        # in cents
    currency="eur",
    recurring={"interval": "month"},  # month, year, week, day
    lookup_key="pro_monthly"
)

# Create one-time
price = stripe.Price.create(
    product="prod_xxx",
    unit_amount=9999,
    currency="eur",
    lookup_key="pro_lifetime"
)

# Retrieve by ID
price = stripe.Price.retrieve("price_xxx")

# Retrieve by lookup_key
prices = stripe.Price.list(lookup_keys=["pro_monthly"])
price = prices.data[0] if prices.data else None

# List for product
prices = stripe.Price.list(product="prod_xxx", active=True)
```

## Checkout Sessions

```python
# Subscription checkout
session = stripe.checkout.Session.create(
    customer="cus_xxx",          # optional
    mode="subscription",         # subscription, payment, setup
    line_items=[{
        "price": "price_xxx",
        "quantity": 1
    }],
    success_url="https://example.com/success?session_id={CHECKOUT_SESSION_ID}",
    cancel_url="https://example.com/cancel",
    metadata={"user_id": "123"},
    # Optional
    allow_promotion_codes=True,
    subscription_data={
        "trial_period_days": 14,
        "metadata": {"plan": "pro"}
    }
)
# Redirect to: session.url

# One-time payment
session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[{"price": "price_xxx", "quantity": 1}],
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel"
)

# Retrieve session
session = stripe.checkout.Session.retrieve(
    "cs_xxx",
    expand=["line_items", "subscription"]
)
```

## Subscriptions

```python
# Create (with existing payment method)
subscription = stripe.Subscription.create(
    customer="cus_xxx",
    items=[{"price": "price_xxx"}],
    default_payment_method="pm_xxx",
    # Optional
    trial_period_days=14,
    metadata={"source": "api"}
)

# Retrieve
subscription = stripe.Subscription.retrieve("sub_xxx")

# Update plan
subscription = stripe.Subscription.modify(
    "sub_xxx",
    items=[{
        "id": "si_xxx",  # subscription item ID
        "price": "price_new"
    }],
    proration_behavior="create_prorations"  # none, always_invoice
)

# Cancel immediately
stripe.Subscription.cancel("sub_xxx")

# Cancel at period end
stripe.Subscription.modify("sub_xxx", cancel_at_period_end=True)

# Reactivate (undo cancel_at_period_end)
stripe.Subscription.modify("sub_xxx", cancel_at_period_end=False)

# Pause collection
stripe.Subscription.modify(
    "sub_xxx",
    pause_collection={"behavior": "void"}
)

# Resume
stripe.Subscription.modify("sub_xxx", pause_collection="")

# List
subscriptions = stripe.Subscription.list(
    customer="cus_xxx",
    status="active"  # active, past_due, canceled, all
)
```

## Payment Intents

```python
# Create
intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    customer="cus_xxx",
    metadata={"order_id": "123"},
    # Optional
    automatic_payment_methods={"enabled": True}
)
# Return: intent.client_secret

# Retrieve
intent = stripe.PaymentIntent.retrieve("pi_xxx")

# Confirm (server-side)
stripe.PaymentIntent.confirm(
    "pi_xxx",
    payment_method="pm_xxx"
)

# Cancel
stripe.PaymentIntent.cancel("pi_xxx")
```

## Invoices

```python
# List for customer
invoices = stripe.Invoice.list(customer="cus_xxx", limit=10)

# Retrieve
invoice = stripe.Invoice.retrieve("in_xxx")

# Get upcoming invoice (preview)
upcoming = stripe.Invoice.upcoming(
    customer="cus_xxx",
    # Optional: preview plan change
    subscription="sub_xxx",
    subscription_items=[{
        "id": "si_xxx",
        "price": "price_new"
    }]
)

# Pay invoice manually
stripe.Invoice.pay("in_xxx")

# Send invoice email
stripe.Invoice.send_invoice("in_xxx")

# Void invoice
stripe.Invoice.void_invoice("in_xxx")
```

## Refunds

```python
# Full refund
refund = stripe.Refund.create(payment_intent="pi_xxx")

# Partial refund
refund = stripe.Refund.create(
    payment_intent="pi_xxx",
    amount=500  # in cents
)

# Refund charge
refund = stripe.Refund.create(charge="ch_xxx")
```

## Billing Portal

```python
# Create portal session
session = stripe.billing_portal.Session.create(
    customer="cus_xxx",
    return_url="https://example.com/account"
)
# Redirect to: session.url
```

## Coupons & Promotions

```python
# Create coupon
coupon = stripe.Coupon.create(
    percent_off=20,
    duration="once",  # once, repeating, forever
    # or: amount_off=500, currency="eur"
)

# Create promotion code
promo = stripe.PromotionCode.create(
    coupon="coupon_id",
    code="SUMMER20"
)

# Apply to subscription
subscription = stripe.Subscription.modify(
    "sub_xxx",
    coupon="coupon_id"
)
```

## Webhooks

```python
# Construct event from webhook
event = stripe.Webhook.construct_event(
    payload,           # request body (bytes)
    sig_header,        # Stripe-Signature header
    endpoint_secret    # whsec_xxx
)

# Access event data
event_type = event["type"]
data = event["data"]["object"]
```

## Common Event Types

| Event | Description |
|-------|-------------|
| `checkout.session.completed` | Checkout payment successful |
| `customer.subscription.created` | New subscription |
| `customer.subscription.updated` | Subscription changed |
| `customer.subscription.deleted` | Subscription cancelled |
| `invoice.paid` | Invoice payment successful |
| `invoice.payment_failed` | Invoice payment failed |
| `customer.subscription.trial_will_end` | Trial ending in 3 days |

## Test Cards

| Number | Result |
|--------|--------|
| `4242424242424242` | Success |
| `4000000000000002` | Declined |
| `4000002500003155` | 3D Secure required |
| `4000000000009995` | Insufficient funds |
| `4000000000000341` | Fails after attaching |

Use any future expiry, any 3-digit CVC, any billing postal code.

## Error Handling

```python
try:
    # Stripe operation
    pass
except stripe.error.CardError as e:
    # Declined card
    err = e.error
    print(f"Code: {err.code}, Message: {err.message}")
except stripe.error.RateLimitError:
    # Too many requests
    pass
except stripe.error.InvalidRequestError:
    # Invalid parameters
    pass
except stripe.error.AuthenticationError:
    # Invalid API key
    pass
except stripe.error.StripeError:
    # Generic error
    pass
```

## Pagination

```python
# Auto-pagination
for customer in stripe.Customer.list(limit=100).auto_paging_iter():
    print(customer.id)

# Manual pagination
customers = stripe.Customer.list(limit=100)
while customers.has_more:
    customers = stripe.Customer.list(
        limit=100,
        starting_after=customers.data[-1].id
    )
```

## Expanding Objects

```python
# Expand nested objects
subscription = stripe.Subscription.retrieve(
    "sub_xxx",
    expand=["customer", "latest_invoice.payment_intent"]
)

# Access expanded data
print(subscription.customer.email)  # Instead of just customer ID
```

## Idempotency

```python
# Prevent duplicate operations
stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    idempotency_key="unique_operation_id_123"
)
```

## Metadata

All major objects support `metadata` (up to 50 keys, 500 chars each):

```python
stripe.Customer.create(
    email="user@example.com",
    metadata={
        "user_id": "123",
        "plan": "pro",
        "source": "website"
    }
)
```
