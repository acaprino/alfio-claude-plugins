#!/usr/bin/env python3
"""
Sync Subscriptions Script

Synchronizes Stripe subscription data with your local database.
Useful for:
- Initial data migration
- Periodic reconciliation
- Disaster recovery

Usage:
    python sync_subscriptions.py [--dry-run]
    
    --dry-run: Show what would be updated without making changes
"""

import stripe
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# ============================================================================
# Configuration - Customize for your database
# ============================================================================

# Example: Using a JSON file as a simple "database"
# Replace with your actual database connection
DATABASE_FILE = "subscriptions_db.json"


class DatabaseAdapter:
    """
    Abstract database adapter. Replace this with your actual database implementation.
    
    Examples:
    - Firebase Firestore
    - PostgreSQL
    - MongoDB
    - SQLite
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._load_db()
    
    def _load_db(self):
        """Load the database (JSON file in this example)."""
        try:
            with open(DATABASE_FILE, "r") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {"users": {}, "subscriptions": {}}
    
    def _save_db(self):
        """Save the database."""
        if self.dry_run:
            print("  [DRY RUN] Would save to database")
            return
        with open(DATABASE_FILE, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def get_user_by_stripe_customer_id(self, customer_id: str) -> Optional[Dict]:
        """Find a user by their Stripe customer ID."""
        for user_id, user in self.data["users"].items():
            if user.get("stripe_customer_id") == customer_id:
                return {"id": user_id, **user}
        return None
    
    def update_user_subscription(
        self,
        user_id: str,
        subscription_data: Dict[str, Any]
    ) -> None:
        """Update a user's subscription data."""
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {}
        
        self.data["users"][user_id]["subscription"] = subscription_data
        self.data["users"][user_id]["updated_at"] = datetime.utcnow().isoformat()
        
        if self.dry_run:
            print(f"  [DRY RUN] Would update user {user_id}")
            print(f"    subscription_status: {subscription_data.get('status')}")
            print(f"    plan: {subscription_data.get('plan')}")
        else:
            self._save_db()
            print(f"  Updated user {user_id}")
    
    def get_all_stripe_customers(self) -> List[str]:
        """Get all Stripe customer IDs from the database."""
        customer_ids = []
        for user in self.data["users"].values():
            if "stripe_customer_id" in user:
                customer_ids.append(user["stripe_customer_id"])
        return customer_ids


# ============================================================================
# Firestore Adapter Example (uncomment and modify if using Firebase)
# ============================================================================

# import firebase_admin
# from firebase_admin import firestore, credentials
# 
# class FirestoreAdapter:
#     def __init__(self, dry_run: bool = False):
#         self.dry_run = dry_run
#         cred = credentials.ApplicationDefault()
#         firebase_admin.initialize_app(cred)
#         self.db = firestore.client()
#     
#     def get_user_by_stripe_customer_id(self, customer_id: str) -> Optional[Dict]:
#         users = self.db.collection("users").where(
#             "stripe_customer_id", "==", customer_id
#         ).limit(1).stream()
#         for user in users:
#             return {"id": user.id, **user.to_dict()}
#         return None
#     
#     def update_user_subscription(self, user_id: str, subscription_data: Dict) -> None:
#         if self.dry_run:
#             print(f"  [DRY RUN] Would update user {user_id}")
#             return
#         self.db.collection("users").document(user_id).update({
#             "subscription": subscription_data,
#             "updated_at": firestore.SERVER_TIMESTAMP
#         })


# ============================================================================
# Sync Logic
# ============================================================================

def extract_subscription_data(subscription: stripe.Subscription) -> Dict[str, Any]:
    """Extract relevant data from a Stripe subscription object."""
    price = subscription["items"]["data"][0]["price"]
    product = price.get("product")
    
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "plan": price.lookup_key or price.id,
        "price_id": price.id,
        "product_id": product if isinstance(product, str) else product.id if product else None,
        "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
        "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "canceled_at": datetime.fromtimestamp(subscription.canceled_at).isoformat() if subscription.canceled_at else None,
        "trial_start": datetime.fromtimestamp(subscription.trial_start).isoformat() if subscription.trial_start else None,
        "trial_end": datetime.fromtimestamp(subscription.trial_end).isoformat() if subscription.trial_end else None,
        "synced_at": datetime.utcnow().isoformat()
    }


def sync_customer_subscriptions(
    customer_id: str,
    db: DatabaseAdapter,
    stats: Dict[str, int]
) -> None:
    """Sync all subscriptions for a single customer."""
    
    # Find user in database
    user = db.get_user_by_stripe_customer_id(customer_id)
    if not user:
        print(f"  Warning: No user found for customer {customer_id}")
        stats["not_found"] += 1
        return
    
    user_id = user["id"]
    
    # Get subscriptions from Stripe
    subscriptions = stripe.Subscription.list(customer=customer_id, limit=10)
    
    if not subscriptions.data:
        # No subscriptions - update user to reflect this
        db.update_user_subscription(user_id, {
            "status": "none",
            "synced_at": datetime.utcnow().isoformat()
        })
        stats["no_subscription"] += 1
        return
    
    # Use the most recent/active subscription
    # Priority: active > trialing > past_due > canceled
    priority = {"active": 0, "trialing": 1, "past_due": 2, "canceled": 3, "incomplete": 4}
    sorted_subs = sorted(
        subscriptions.data,
        key=lambda s: (priority.get(s.status, 99), -s.created)
    )
    
    primary_sub = sorted_subs[0]
    subscription_data = extract_subscription_data(primary_sub)
    
    # Update database
    db.update_user_subscription(user_id, subscription_data)
    stats["synced"] += 1


def sync_all_subscriptions(dry_run: bool = False) -> Dict[str, int]:
    """
    Sync all Stripe subscriptions with the database.
    
    Returns stats dict with counts of synced, not_found, etc.
    """
    print("=" * 60)
    print("Stripe Subscription Sync")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)
    
    # Initialize
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        print("Error: STRIPE_SECRET_KEY not set")
        sys.exit(1)
    
    db = DatabaseAdapter(dry_run=dry_run)
    
    stats = {
        "total": 0,
        "synced": 0,
        "not_found": 0,
        "no_subscription": 0,
        "errors": 0
    }
    
    # Option 1: Iterate through all Stripe customers
    print("\nFetching customers from Stripe...")
    
    customers = stripe.Customer.list(limit=100)
    all_customers = []
    
    # Handle pagination
    while True:
        all_customers.extend(customers.data)
        if not customers.has_more:
            break
        customers = stripe.Customer.list(
            limit=100,
            starting_after=customers.data[-1].id
        )
    
    print(f"Found {len(all_customers)} customers\n")
    
    # Process each customer
    for i, customer in enumerate(all_customers, 1):
        stats["total"] += 1
        print(f"[{i}/{len(all_customers)}] Processing {customer.email or customer.id}")
        
        try:
            sync_customer_subscriptions(customer.id, db, stats)
        except Exception as e:
            print(f"  Error: {e}")
            stats["errors"] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("Sync Complete!")
    print("=" * 60)
    print(f"Total customers:     {stats['total']}")
    print(f"Successfully synced: {stats['synced']}")
    print(f"No user in DB:       {stats['not_found']}")
    print(f"No subscription:     {stats['no_subscription']}")
    print(f"Errors:              {stats['errors']}")
    
    return stats


# ============================================================================
# Alternative: Sync only specific customers from database
# ============================================================================

def sync_from_database(dry_run: bool = False) -> Dict[str, int]:
    """
    Alternative approach: Start from database users and sync their Stripe data.
    Use this when you have users in your database that may or may not have
    Stripe subscriptions.
    """
    print("Syncing from database users...")
    
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    db = DatabaseAdapter(dry_run=dry_run)
    
    stats = {"total": 0, "synced": 0, "errors": 0}
    
    customer_ids = db.get_all_stripe_customers()
    print(f"Found {len(customer_ids)} users with Stripe customer IDs\n")
    
    for customer_id in customer_ids:
        stats["total"] += 1
        try:
            sync_customer_subscriptions(customer_id, db, stats)
        except Exception as e:
            print(f"  Error syncing {customer_id}: {e}")
            stats["errors"] += 1
    
    return stats


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("Running in DRY RUN mode - no changes will be made\n")
    
    sync_all_subscriptions(dry_run=dry_run)
