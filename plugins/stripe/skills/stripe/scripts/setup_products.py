#!/usr/bin/env python3
"""
Setup Products and Prices in Stripe

This script creates a complete product catalog with subscription plans.
Customize the PRODUCTS configuration to match your business model.

Usage:
    python setup_products.py [--live]
    
    --live: Use live mode (default is test mode)
"""

import stripe
import os
import sys
import json

# Configuration: Define your products and prices here
PRODUCTS = [
    {
        "name": "Free Plan",
        "description": "Basic features for individuals",
        "metadata": {"tier": "free"},
        "prices": [
            {
                "unit_amount": 0,
                "currency": "eur",
                "recurring": {"interval": "month"},
                "lookup_key": "free_monthly"
            }
        ]
    },
    {
        "name": "Pro Plan",
        "description": "Advanced features for professionals",
        "metadata": {"tier": "pro"},
        "prices": [
            {
                "unit_amount": 999,  # €9.99
                "currency": "eur",
                "recurring": {"interval": "month"},
                "lookup_key": "pro_monthly"
            },
            {
                "unit_amount": 9990,  # €99.90 (2 months free)
                "currency": "eur",
                "recurring": {"interval": "year"},
                "lookup_key": "pro_yearly"
            }
        ]
    },
    {
        "name": "Enterprise Plan",
        "description": "Full features for teams and businesses",
        "metadata": {"tier": "enterprise"},
        "prices": [
            {
                "unit_amount": 2999,  # €29.99
                "currency": "eur",
                "recurring": {"interval": "month"},
                "lookup_key": "enterprise_monthly"
            },
            {
                "unit_amount": 29990,  # €299.90
                "currency": "eur",
                "recurring": {"interval": "year"},
                "lookup_key": "enterprise_yearly"
            }
        ]
    }
]


def setup_stripe_key():
    """Initialize Stripe with the appropriate API key."""
    api_key = os.environ.get("STRIPE_SECRET_KEY")
    
    if not api_key:
        print("Error: STRIPE_SECRET_KEY environment variable not set")
        print("Set it with: export STRIPE_SECRET_KEY='sk_test_...'")
        sys.exit(1)
    
    stripe.api_key = api_key
    
    # Determine mode from key prefix
    mode = "live" if api_key.startswith("sk_live") else "test"
    print(f"Using Stripe in {mode.upper()} mode")
    
    return mode


def create_product_with_prices(product_config):
    """Create a product and its associated prices."""
    
    # Check if product already exists by name
    existing = stripe.Product.list(limit=100)
    for prod in existing.data:
        if prod.name == product_config["name"]:
            print(f"  Product '{product_config['name']}' already exists (ID: {prod.id})")
            return prod, []
    
    # Create the product
    product = stripe.Product.create(
        name=product_config["name"],
        description=product_config.get("description", ""),
        metadata=product_config.get("metadata", {})
    )
    print(f"  Created product: {product.name} (ID: {product.id})")
    
    # Create prices for this product
    created_prices = []
    for price_config in product_config.get("prices", []):
        # Check if price with lookup_key exists
        lookup_key = price_config.get("lookup_key")
        if lookup_key:
            existing_prices = stripe.Price.list(lookup_keys=[lookup_key])
            if existing_prices.data:
                print(f"    Price with lookup_key '{lookup_key}' already exists")
                created_prices.append(existing_prices.data[0])
                continue
        
        price = stripe.Price.create(
            product=product.id,
            unit_amount=price_config["unit_amount"],
            currency=price_config["currency"],
            recurring=price_config.get("recurring"),
            lookup_key=lookup_key,
            metadata=price_config.get("metadata", {})
        )
        
        interval = price_config.get("recurring", {}).get("interval", "one-time")
        amount = price_config["unit_amount"] / 100
        currency = price_config["currency"].upper()
        
        print(f"    Created price: {amount} {currency}/{interval} (lookup_key: {lookup_key})")
        created_prices.append(price)
    
    return product, created_prices


def main():
    """Main entry point."""
    print("=" * 50)
    print("Stripe Products & Prices Setup")
    print("=" * 50)
    
    mode = setup_stripe_key()
    
    if mode == "live" and "--live" not in sys.argv:
        print("\nWarning: You're using a LIVE key but didn't pass --live flag")
        print("Run with --live to confirm live mode operation")
        sys.exit(1)
    
    print(f"\nCreating {len(PRODUCTS)} products...\n")
    
    results = []
    for product_config in PRODUCTS:
        print(f"Processing: {product_config['name']}")
        product, prices = create_product_with_prices(product_config)
        results.append({
            "product_id": product.id,
            "product_name": product.name,
            "prices": [{"id": p.id, "lookup_key": p.lookup_key} for p in prices]
        })
    
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    
    # Output summary as JSON for easy parsing
    print("\nCreated resources:")
    print(json.dumps(results, indent=2))
    
    print("\nNext steps:")
    print("1. Use lookup_keys to reference prices in your code")
    print("2. Set up webhooks at https://dashboard.stripe.com/webhooks")
    print("3. Configure Customer Portal at https://dashboard.stripe.com/settings/billing/portal")


if __name__ == "__main__":
    main()
