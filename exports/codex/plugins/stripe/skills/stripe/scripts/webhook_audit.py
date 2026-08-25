#!/usr/bin/env python3
"""
Stripe Webhook Audit

Enumerates webhook endpoints on a Stripe account and reports gaps against
the must-have event catalog for common features (subscriptions, trials,
entitlements, billing meters, Connect).

Companion to the `stripe-webhooks-auditor` agent, which combines this
Stripe-side report with codebase-side signature/idempotency analysis.

Usage:
    export STRIPE_SECRET_KEY=rk_live_...
    python webhook_audit.py                       # text report
    python webhook_audit.py --json                # machine-readable
    python webhook_audit.py --features meters,entitlements
    python webhook_audit.py --account acct_xxx    # Connect platform

Exit codes:
    0   No critical gaps
    1   Missing base events (subscriptions / payment)
    2   Missing feature-specific events (soft warning)
"""

import argparse
import json
import os
import sys
from typing import Any

import stripe

BASE_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_failed",
}

# Either invoice.payment_succeeded or invoice.paid -- accept either
PAYMENT_SUCCESS_EVENTS = {"invoice.payment_succeeded", "invoice.paid"}

FEATURE_EVENTS = {
    "trials": {"customer.subscription.trial_will_end"},
    "entitlements": {"entitlements.active_entitlement_summary.updated"},
    "meters": {
        "v1.billing.meter.error_report_triggered",
        "v1.billing.meter.no_meter_found",
    },
    "connect": {
        "account.updated",
        "account.application.deauthorized",
        "charge.dispute.created",
        "charge.dispute.closed",
    },
}


def list_endpoints(stripe_account: str | None = None) -> list[dict[str, Any]]:
    """Return all webhook endpoints for the account."""
    kwargs: dict[str, Any] = {"limit": 100}
    if stripe_account:
        kwargs["stripe_account"] = stripe_account
    endpoints = []
    for ep in stripe.WebhookEndpoint.list(**kwargs).auto_paging_iter():
        endpoints.append(
            {
                "id": ep.id,
                "url": ep.url,
                "status": ep.status,
                "enabled_events": list(ep.enabled_events),
                "api_version": ep.api_version,
                "description": ep.description,
            }
        )
    return endpoints


def union_enabled(endpoints: list[dict[str, Any]]) -> set[str]:
    """All events enabled across enabled endpoints."""
    enabled: set[str] = set()
    for ep in endpoints:
        if ep["status"] != "enabled":
            continue
        if "*" in ep["enabled_events"]:
            # Wildcard subscription -- counts as covering everything but
            # is itself an anti-pattern; callers can surface it separately.
            return {"*"}
        enabled.update(ep["enabled_events"])
    return enabled


def compute_gaps(enabled: set[str], features: set[str]) -> dict[str, Any]:
    """Diff enabled events against required catalog."""
    if "*" in enabled:
        return {
            "wildcard": True,
            "missing_base": [],
            "missing_feature": {},
            "missing_payment_success": False,
        }

    missing_base = sorted(BASE_EVENTS - enabled)
    missing_payment_success = not (enabled & PAYMENT_SUCCESS_EVENTS)

    missing_feature: dict[str, list[str]] = {}
    for feat in features:
        required = FEATURE_EVENTS.get(feat, set())
        gap = sorted(required - enabled)
        if gap:
            missing_feature[feat] = gap

    return {
        "wildcard": False,
        "missing_base": missing_base,
        "missing_feature": missing_feature,
        "missing_payment_success": missing_payment_success,
    }


def find_stale_endpoints(endpoints: list[dict[str, Any]]) -> list[str]:
    """Disabled endpoints hint at rotted integrations."""
    return [ep["id"] for ep in endpoints if ep["status"] != "enabled"]


def api_version_drift(endpoints: list[dict[str, Any]]) -> bool:
    """True if endpoints are pinned to different API versions."""
    versions = {ep["api_version"] for ep in endpoints if ep["api_version"]}
    return len(versions) > 1


def text_report(
    endpoints: list[dict[str, Any]],
    gaps: dict[str, Any],
    features: set[str],
) -> str:
    lines: list[str] = []
    lines.append("# Stripe Webhook Audit")
    lines.append("")
    lines.append(f"Endpoints: {len(endpoints)}")
    lines.append(f"Features declared: {sorted(features) or ['(base only)']}")
    lines.append("")

    lines.append("## Endpoints")
    for ep in endpoints:
        lines.append(
            f"- {ep['url']} [{ep['status']}, api={ep['api_version'] or 'default'}, "
            f"events={len(ep['enabled_events'])}]"
        )
    lines.append("")

    lines.append("## Gaps")
    if gaps["wildcard"]:
        lines.append("- WARNING: endpoint subscribed to '*' (all events) -- noisy, hides signal.")
    if gaps["missing_base"]:
        lines.append("- CRITICAL missing base events:")
        for ev in gaps["missing_base"]:
            lines.append(f"    - {ev}")
    if gaps["missing_payment_success"]:
        lines.append(
            "- HIGH: no payment-success event (subscribe to either "
            "invoice.payment_succeeded or invoice.paid)"
        )
    for feat, missing in gaps["missing_feature"].items():
        lines.append(f"- MEDIUM missing {feat} events:")
        for ev in missing:
            lines.append(f"    - {ev}")
    if not any(
        [
            gaps["missing_base"],
            gaps["missing_payment_success"],
            gaps["missing_feature"],
            gaps["wildcard"],
        ]
    ):
        lines.append("- OK: no gaps detected for declared features.")
    lines.append("")

    stale = find_stale_endpoints(endpoints)
    if stale:
        lines.append("## Stale endpoints (disabled)")
        for eid in stale:
            lines.append(f"- {eid}")
        lines.append("")

    if api_version_drift(endpoints):
        lines.append("## API version drift")
        lines.append(
            "- LOW: endpoints pinned to different API versions -- align for consistent payloads."
        )
        lines.append("")

    return "\n".join(lines)


def severity_exit_code(gaps: dict[str, Any]) -> int:
    if gaps["missing_base"] or gaps["missing_payment_success"]:
        return 1
    if gaps["missing_feature"]:
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Stripe webhook endpoints.")
    parser.add_argument(
        "--features",
        default="",
        help="Comma-separated features in use: trials,entitlements,meters,connect",
    )
    parser.add_argument(
        "--account",
        default=None,
        help="Connected account ID (Connect platforms)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text",
    )
    args = parser.parse_args()

    api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_RESTRICTED_KEY")
    if not api_key:
        print("error: set STRIPE_SECRET_KEY or STRIPE_RESTRICTED_KEY", file=sys.stderr)
        return 3
    stripe.api_key = api_key

    features = {f.strip() for f in args.features.split(",") if f.strip()}
    unknown = features - FEATURE_EVENTS.keys()
    if unknown:
        print(
            f"error: unknown features: {sorted(unknown)}. "
            f"Valid: {sorted(FEATURE_EVENTS.keys())}",
            file=sys.stderr,
        )
        return 3

    try:
        endpoints = list_endpoints(stripe_account=args.account)
    except stripe.error.StripeError as e:
        print(f"error: Stripe API failed: {e}", file=sys.stderr)
        return 3

    enabled = union_enabled(endpoints)
    gaps = compute_gaps(enabled, features)

    if args.json:
        print(
            json.dumps(
                {
                    "endpoints": endpoints,
                    "gaps": gaps,
                    "features": sorted(features),
                    "stale": find_stale_endpoints(endpoints),
                    "api_version_drift": api_version_drift(endpoints),
                },
                indent=2,
            )
        )
    else:
        print(text_report(endpoints, gaps, features))

    return severity_exit_code(gaps)


if __name__ == "__main__":
    sys.exit(main())
