#!/usr/bin/env python3
"""
Stripe Webhook Handler

A Flask-based webhook endpoint for handling Stripe events.
This handler processes subscription lifecycle events and payment notifications.

Usage:
    # Development (with Flask)
    python webhook_handler.py
    
    # Production: Deploy as Cloud Function or integrate into your app
    
    # Local testing with Stripe CLI:
    stripe listen --forward-to localhost:5000/webhook
"""

import os
import stripe
from flask import Flask, request, jsonify
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")


def verify_webhook(f):
    """Decorator to verify Stripe webhook signatures."""
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = request.get_data()
        sig_header = request.headers.get("Stripe-Signature")
        
        if not WEBHOOK_SECRET:
            print("Warning: STRIPE_WEBHOOK_SECRET not set, skipping verification")
            event = stripe.Event.construct_from(
                request.get_json(), stripe.api_key
            )
        else:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, WEBHOOK_SECRET
                )
            except ValueError as e:
                print(f"Invalid payload: {e}")
                return jsonify({"error": "Invalid payload"}), 400
            except stripe.error.SignatureVerificationError as e:
                print(f"Invalid signature: {e}")
                return jsonify({"error": "Invalid signature"}), 400
        
        return f(event, *args, **kwargs)
    return decorated


# ============================================================================
# Event Handlers - Customize these for your application
# ============================================================================

def handle_checkout_completed(session):
    """
    Handle successful checkout session.
    This is called when a customer completes payment.
    """
    print(f"Checkout completed: {session.id}")
    
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    metadata = session.get("metadata", {})
    
    # TODO: Implement your business logic here
    # Examples:
    # - Update user record in database with subscription info
    # - Send welcome email
    # - Activate premium features
    # - Create user account if this was a new signup
    
    if subscription_id:
        print(f"  Subscription created: {subscription_id}")
        print(f"  Customer: {customer_id}")
        print(f"  Metadata: {metadata}")
        
        # Example: Update your database
        # db.users.update(
        #     {"stripe_customer_id": customer_id},
        #     {"$set": {
        #         "subscription_id": subscription_id,
        #         "subscription_status": "active",
        #         "updated_at": datetime.utcnow()
        #     }}
        # )


def handle_subscription_created(subscription):
    """Handle new subscription creation."""
    print(f"Subscription created: {subscription.id}")
    print(f"  Customer: {subscription.customer}")
    print(f"  Status: {subscription.status}")
    print(f"  Plan: {subscription['items']['data'][0]['price']['id']}")
    
    # TODO: Store subscription info in your database


def handle_subscription_updated(subscription):
    """
    Handle subscription updates.
    This includes plan changes, payment method updates, etc.
    """
    print(f"Subscription updated: {subscription.id}")
    print(f"  Status: {subscription.status}")
    print(f"  Cancel at period end: {subscription.cancel_at_period_end}")
    
    # Check for plan changes
    current_plan = subscription["items"]["data"][0]["price"]["id"]
    print(f"  Current plan: {current_plan}")
    
    # TODO: Update your database with new subscription status
    # Handle plan upgrades/downgrades


def handle_subscription_deleted(subscription):
    """
    Handle subscription cancellation.
    This is called when a subscription is fully cancelled.
    """
    print(f"Subscription cancelled: {subscription.id}")
    print(f"  Customer: {subscription.customer}")
    
    # TODO: Revoke access to premium features
    # Update database to reflect cancelled status
    # Optionally send a feedback survey or win-back email


def handle_invoice_paid(invoice):
    """
    Handle successful invoice payment.
    Called for both initial and renewal payments.
    """
    print(f"Invoice paid: {invoice.id}")
    print(f"  Customer: {invoice.customer}")
    print(f"  Amount: {invoice.amount_paid / 100} {invoice.currency.upper()}")
    print(f"  Subscription: {invoice.subscription}")
    
    # TODO: Record payment in your system
    # Extend subscription access period


def handle_invoice_payment_failed(invoice):
    """
    Handle failed invoice payment.
    Implement dunning logic here.
    """
    print(f"Invoice payment failed: {invoice.id}")
    print(f"  Customer: {invoice.customer}")
    print(f"  Attempt count: {invoice.attempt_count}")
    
    # TODO: Implement dunning logic
    # - Send payment failure notification
    # - Update UI to show payment issue
    # - After X failures, potentially suspend account


def handle_customer_subscription_trial_will_end(subscription):
    """
    Handle trial ending soon notification.
    Sent 3 days before trial ends by default.
    """
    print(f"Trial ending soon: {subscription.id}")
    print(f"  Customer: {subscription.customer}")
    print(f"  Trial end: {subscription.trial_end}")
    
    # TODO: Send reminder email about trial ending


# ============================================================================
# Webhook Endpoint
# ============================================================================

@app.route("/webhook", methods=["POST"])
@verify_webhook
def webhook_handler(event):
    """Main webhook endpoint."""
    event_type = event["type"]
    data = event["data"]["object"]
    
    print(f"\n{'='*50}")
    print(f"Received event: {event_type}")
    print(f"Event ID: {event.id}")
    print(f"{'='*50}")
    
    # Route to appropriate handler
    handlers = {
        "checkout.session.completed": handle_checkout_completed,
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_invoice_payment_failed,
        "customer.subscription.trial_will_end": handle_customer_subscription_trial_will_end,
    }
    
    handler = handlers.get(event_type)
    if handler:
        try:
            handler(data)
        except Exception as e:
            print(f"Error handling {event_type}: {e}")
            # In production, you might want to:
            # - Log to error tracking service
            # - Return 500 to trigger Stripe retry
            # For now, we acknowledge receipt to prevent retries
            return jsonify({"error": str(e)}), 500
    else:
        print(f"Unhandled event type: {event_type}")
    
    return jsonify({"status": "success"})


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


# ============================================================================
# Cloud Function Export (for Firebase/GCP deployment)
# ============================================================================

def stripe_webhook(request):
    """
    Cloud Function entry point.
    Deploy with: gcloud functions deploy stripe_webhook --runtime python39 --trigger-http
    """
    with app.test_request_context(
        path=request.path,
        method=request.method,
        headers=dict(request.headers),
        data=request.get_data()
    ):
        try:
            rv = webhook_handler()
            return rv
        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Starting Stripe Webhook Handler...")
    print(f"Webhook secret configured: {'Yes' if WEBHOOK_SECRET else 'No'}")
    print("\nFor local testing, run:")
    print("  stripe listen --forward-to localhost:5000/webhook")
    print("\nEndpoints:")
    print("  POST /webhook - Stripe webhook endpoint")
    print("  GET  /health  - Health check")
    app.run(host="0.0.0.0", port=5000, debug=True)
