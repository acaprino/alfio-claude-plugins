#!/usr/bin/env python3
"""
Simulate a Subscription Lifecycle with a Test Clock

Walks a test-mode subscription through: creation, trial end, first renewal,
a failed renewal, and recovery. Useful for end-to-end testing your webhook
handlers, dunning emails, and access-gating logic without waiting real days.

Usage:
    export STRIPE_SECRET_KEY=sk_test_...        # TEST MODE ONLY
    python simulate_subscription.py --price price_xxx
    python simulate_subscription.py --price price_xxx --trial-days 14 --cleanup

Requires the target Price to be a recurring monthly price in test mode.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import stripe


def wait_for_clock_ready(clock_id: str, timeout_s: int = 120) -> None:
    """Poll the test clock until advance completes (or timeout)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        clock = stripe.test_helpers.TestClock.retrieve(clock_id)
        if clock.status == "ready":
            return
        if clock.status == "internal_failure":
            raise RuntimeError(f"test clock {clock_id} entered internal_failure")
        time.sleep(2)
    raise TimeoutError(f"test clock {clock_id} did not become ready in {timeout_s}s")


def advance(clock_id: str, to: datetime, label: str) -> None:
    print(f"\n=> advancing to {to.isoformat()}  ({label})")
    stripe.test_helpers.TestClock.advance(clock_id, frozen_time=int(to.timestamp()))
    wait_for_clock_ready(clock_id)
    print(f"   clock ready")


def print_subscription_state(sub_id: str) -> None:
    sub = stripe.Subscription.retrieve(sub_id)
    item = sub["items"]["data"][0]
    period_end = datetime.fromtimestamp(item["current_period_end"], tz=timezone.utc)
    print(f"   status={sub.status}  period_end={period_end.isoformat()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a subscription lifecycle.")
    parser.add_argument("--price", required=True, help="Recurring Price ID (test mode)")
    parser.add_argument(
        "--trial-days", type=int, default=7, help="Free trial length in days"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the test clock (and its customers) at the end",
    )
    args = parser.parse_args()

    api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not api_key:
        print("error: STRIPE_SECRET_KEY not set", file=sys.stderr)
        return 1
    if not api_key.startswith("sk_test_") and not api_key.startswith("rk_test_"):
        print("error: use a TEST-mode key; live keys not allowed here", file=sys.stderr)
        return 1
    stripe.api_key = api_key

    start = datetime.now(tz=timezone.utc).replace(microsecond=0)

    print(f"creating test clock at t0 = {start.isoformat()}")
    clock = stripe.test_helpers.TestClock.create(
        frozen_time=int(start.timestamp()),
        name="simulate_subscription.py",
    )
    print(f"   clock={clock.id}")

    print("creating test customer + payment method")
    customer = stripe.Customer.create(
        email=f"sim-{int(time.time())}@example.test",
        name="Simulated Customer",
        test_clock=clock.id,
        payment_method="pm_card_visa",
        invoice_settings={"default_payment_method": "pm_card_visa"},
    )
    print(f"   customer={customer.id}")

    print("creating subscription with trial")
    sub = stripe.Subscription.create(
        customer=customer.id,
        items=[{"price": args.price}],
        trial_period_days=args.trial_days,
    )
    print(f"   subscription={sub.id}")
    print_subscription_state(sub.id)

    # Advance past trial end
    advance(clock.id, start + timedelta(days=args.trial_days + 1), "trial just ended")
    print_subscription_state(sub.id)

    # Advance one month for first renewal
    advance(clock.id, start + timedelta(days=args.trial_days + 32), "first renewal attempted")
    print_subscription_state(sub.id)

    # Switch payment method to a card that fails, advance past next cycle
    print("\nswapping in a card that will fail renewal")
    stripe.Customer.modify(
        customer.id,
        invoice_settings={"default_payment_method": "pm_card_chargeCustomerFail"},
    )
    advance(clock.id, start + timedelta(days=args.trial_days + 64), "second renewal -- should fail")
    print_subscription_state(sub.id)

    # Recover with a valid card
    print("\nrecovering with a valid card")
    stripe.Customer.modify(
        customer.id,
        invoice_settings={"default_payment_method": "pm_card_visa"},
    )
    # Pay the latest open invoice to recover
    invoices = stripe.Invoice.list(customer=customer.id, status="open", limit=1)
    if invoices.data:
        stripe.Invoice.pay(invoices.data[0].id)
        print(f"   paid invoice {invoices.data[0].id}")
    print_subscription_state(sub.id)

    if args.cleanup:
        print("\ncleaning up test clock and its customers")
        stripe.test_helpers.TestClock.delete(clock.id)
        print("   deleted")
    else:
        print(
            f"\nclock {clock.id} left in place; "
            f"auto-deletes 30 days after creation, or rerun with --cleanup"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
