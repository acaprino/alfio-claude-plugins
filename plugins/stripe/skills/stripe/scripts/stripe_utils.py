#!/usr/bin/env python3
"""
Stripe Utility Functions

Common operations for Stripe integration. Import these functions
into your application code.

Usage:
    from stripe_utils import StripeManager
    
    manager = StripeManager()
    customer = manager.get_or_create_customer("user@example.com", "John Doe")
"""

import stripe
import os
from typing import Optional, Dict, Any, List
from datetime import datetime


class StripeManager:
    """
    High-level manager for common Stripe operations.
    Provides a simplified interface for customer, subscription, and payment management.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Stripe manager.
        
        Args:
            api_key: Stripe secret key. If not provided, uses STRIPE_SECRET_KEY env var.
        """
        stripe.api_key = api_key or os.environ.get("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise ValueError("Stripe API key not provided. Set STRIPE_SECRET_KEY environment variable.")
    
    # =========================================================================
    # Customer Operations
    # =========================================================================
    
    def get_or_create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> stripe.Customer:
        """
        Get existing customer by email or create a new one.
        
        This is the recommended way to handle customers - always check for
        existing customers to avoid duplicates.
        
        Args:
            email: Customer email address
            name: Customer name (optional)
            metadata: Additional metadata to store (optional)
            
        Returns:
            Stripe Customer object
        """
        # Search for existing customer
        existing = stripe.Customer.list(email=email, limit=1)
        if existing.data:
            customer = existing.data[0]
            # Update if name provided and different
            if name and customer.name != name:
                customer = stripe.Customer.modify(customer.id, name=name)
            return customer
        
        # Create new customer
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )
    
    def get_customer(self, customer_id: str) -> stripe.Customer:
        """Retrieve a customer by ID."""
        return stripe.Customer.retrieve(customer_id)
    
    def update_customer_metadata(
        self,
        customer_id: str,
        metadata: Dict[str, str]
    ) -> stripe.Customer:
        """Update customer metadata (merges with existing)."""
        return stripe.Customer.modify(customer_id, metadata=metadata)
    
    # =========================================================================
    # Subscription Operations
    # =========================================================================
    
    def get_active_subscription(self, customer_id: str) -> Optional[stripe.Subscription]:
        """
        Get the active subscription for a customer.
        
        Returns None if no active subscription exists.
        """
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1
        )
        return subscriptions.data[0] if subscriptions.data else None
    
    def get_subscription_status(self, customer_id: str) -> Dict[str, Any]:
        """
        Get detailed subscription status for a customer.
        
        Returns a dict with subscription info including:
        - has_subscription: bool
        - status: str (active, past_due, canceled, etc.)
        - plan: str (price lookup_key or id)
        - current_period_end: datetime
        - cancel_at_period_end: bool
        """
        sub = self.get_active_subscription(customer_id)
        
        if not sub:
            # Check for any subscription (including past_due, canceled, etc.)
            all_subs = stripe.Subscription.list(customer=customer_id, limit=1)
            if all_subs.data:
                sub = all_subs.data[0]
            else:
                return {
                    "has_subscription": False,
                    "status": None,
                    "plan": None,
                    "current_period_end": None,
                    "cancel_at_period_end": False
                }
        
        price = sub["items"]["data"][0]["price"]
        return {
            "has_subscription": True,
            "status": sub.status,
            "plan": price.lookup_key or price.id,
            "current_period_end": datetime.fromtimestamp(sub.current_period_end),
            "cancel_at_period_end": sub.cancel_at_period_end,
            "subscription_id": sub.id
        }
    
    def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> stripe.Subscription:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: The subscription to cancel
            immediately: If True, cancel now. If False, cancel at period end.
        """
        if immediately:
            return stripe.Subscription.cancel(subscription_id)
        else:
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
    
    def reactivate_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Reactivate a subscription that was set to cancel at period end."""
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False
        )
    
    def change_subscription_plan(
        self,
        subscription_id: str,
        new_price_lookup_key: str,
        proration: str = "create_prorations"
    ) -> stripe.Subscription:
        """
        Change the plan for an existing subscription.
        
        Args:
            subscription_id: The subscription to modify
            new_price_lookup_key: The lookup_key of the new price
            proration: One of 'create_prorations', 'none', or 'always_invoice'
        """
        # Get the new price by lookup key
        prices = stripe.Price.list(lookup_keys=[new_price_lookup_key], limit=1)
        if not prices.data:
            raise ValueError(f"Price with lookup_key '{new_price_lookup_key}' not found")
        
        new_price = prices.data[0]
        
        # Get current subscription to find the item to update
        sub = stripe.Subscription.retrieve(subscription_id)
        item_id = sub["items"]["data"][0].id
        
        return stripe.Subscription.modify(
            subscription_id,
            items=[{"id": item_id, "price": new_price.id}],
            proration_behavior=proration
        )
    
    # =========================================================================
    # Checkout Operations
    # =========================================================================
    
    def create_checkout_session(
        self,
        price_lookup_key: str,
        success_url: str,
        cancel_url: str,
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        mode: str = "subscription",
        metadata: Optional[Dict[str, str]] = None,
        trial_days: Optional[int] = None
    ) -> stripe.checkout.Session:
        """
        Create a Checkout Session for payment.
        
        Args:
            price_lookup_key: The lookup_key of the price to charge
            success_url: URL to redirect on success (use {CHECKOUT_SESSION_ID} placeholder)
            cancel_url: URL to redirect on cancel
            customer_id: Existing customer ID (optional)
            customer_email: Email for new customer (optional, ignored if customer_id provided)
            mode: 'subscription' or 'payment'
            metadata: Additional metadata
            trial_days: Number of trial days (subscription mode only)
        """
        # Get price by lookup key
        prices = stripe.Price.list(lookup_keys=[price_lookup_key], limit=1)
        if not prices.data:
            raise ValueError(f"Price with lookup_key '{price_lookup_key}' not found")
        
        price = prices.data[0]
        
        params = {
            "mode": mode,
            "line_items": [{"price": price.id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {}
        }
        
        if customer_id:
            params["customer"] = customer_id
        elif customer_email:
            params["customer_email"] = customer_email
        
        if trial_days and mode == "subscription":
            params["subscription_data"] = {"trial_period_days": trial_days}
        
        return stripe.checkout.Session.create(**params)
    
    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> stripe.billing_portal.Session:
        """
        Create a Billing Portal session for customer self-service.
        
        The customer can manage their subscription, update payment method,
        view invoices, etc.
        """
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
    
    # =========================================================================
    # Invoice Operations
    # =========================================================================
    
    def get_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[stripe.Invoice]:
        """Get invoices for a customer."""
        invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
        return invoices.data
    
    def get_upcoming_invoice(self, customer_id: str) -> Optional[stripe.Invoice]:
        """Get the upcoming invoice for a customer (next renewal)."""
        try:
            return stripe.Invoice.upcoming(customer=customer_id)
        except stripe.error.InvalidRequestError:
            # No upcoming invoice (no active subscription)
            return None
    
    # =========================================================================
    # Payment Method Operations
    # =========================================================================
    
    def get_payment_methods(
        self,
        customer_id: str,
        type: str = "card"
    ) -> List[stripe.PaymentMethod]:
        """Get payment methods for a customer."""
        methods = stripe.PaymentMethod.list(customer=customer_id, type=type)
        return methods.data
    
    def get_default_payment_method(self, customer_id: str) -> Optional[stripe.PaymentMethod]:
        """Get the default payment method for a customer."""
        customer = stripe.Customer.retrieve(customer_id)
        default_pm_id = customer.invoice_settings.default_payment_method
        if default_pm_id:
            return stripe.PaymentMethod.retrieve(default_pm_id)
        return None


# =========================================================================
# Standalone Utility Functions
# =========================================================================

def format_amount(amount_cents: int, currency: str = "eur") -> str:
    """
    Format a Stripe amount (in cents) for display.
    
    Args:
        amount_cents: Amount in smallest currency unit (e.g., cents)
        currency: ISO currency code
        
    Returns:
        Formatted string like "€19.99" or "$19.99"
    """
    amount = amount_cents / 100
    
    symbols = {
        "eur": "€",
        "usd": "$",
        "gbp": "£",
        "jpy": "¥",
    }
    
    symbol = symbols.get(currency.lower(), currency.upper() + " ")
    
    # JPY doesn't have decimal places
    if currency.lower() == "jpy":
        return f"{symbol}{int(amount)}"
    
    return f"{symbol}{amount:.2f}"


def is_subscription_active(status: str) -> bool:
    """Check if a subscription status indicates active access."""
    return status in ["active", "trialing"]


def calculate_proration(
    old_price_cents: int,
    new_price_cents: int,
    days_remaining: int,
    days_in_period: int
) -> int:
    """
    Calculate proration amount for a plan change.
    
    Returns the amount to charge (positive) or credit (negative) in cents.
    """
    daily_old = old_price_cents / days_in_period
    daily_new = new_price_cents / days_in_period
    
    return int((daily_new - daily_old) * days_remaining)


# =========================================================================
# Example Usage
# =========================================================================

if __name__ == "__main__":
    # Demo usage
    manager = StripeManager()
    
    # Example: Get or create a customer
    print("Testing Stripe connection...")
    
    try:
        # List products to verify connection
        products = stripe.Product.list(limit=3)
        print(f"✓ Connected successfully. Found {len(products.data)} products.")
        
        for product in products.data:
            print(f"  - {product.name} ({product.id})")
            
    except stripe.error.AuthenticationError:
        print("✗ Authentication failed. Check your API key.")
    except Exception as e:
        print(f"✗ Error: {e}")
