---
description: >
  Runs the stripe-webhooks-auditor agent over the current project.
  TRIGGER WHEN: the user asks to audit or verify a Stripe webhook setup: endpoint configuration, signature verification, idempotency or event coverage.
argument-hint: "[--features trials,entitlements,meters,connect] [--account acct_xxx]"
---

# Audit Stripe webhooks

Runs the `stripe-webhooks-auditor` agent against the current project.

## What happens

1. Spawns the `stripe-webhooks-auditor` agent.
2. Agent enumerates Stripe-side state via `scripts/webhook_audit.py` (reads `STRIPE_SECRET_KEY`; pass `--account` for Connect).
3. Agent greps the codebase for webhook handlers and verifies each against the pass criteria in `references/webhooks-production.md`.
4. Agent produces a prioritized remediation report. Does not modify code or Stripe config.

## Arguments

- `--features <list>` -- declare features in use (`trials`, `entitlements`, `meters`, `connect`). If omitted, inferred from the codebase.
- `--account <acct_id>` -- Connect platform auditing a connected account.

## Prerequisites

- `STRIPE_SECRET_KEY` (or a read-only Restricted API Key) in env.
- Python environment with `stripe` installed (`pip install stripe`).

## When to invoke

- Before a production launch.
- After adding Billing Meters or Entitlements (event list grows).
- Quarterly webhook hygiene.
- During PR review of a webhook route.
- After a webhook-related incident.

## Example

```
/stripe:audit-webhooks --features meters,entitlements,trials
```

## Related

- Agent: `stripe-webhooks-auditor`
- Script: `skills/stripe/scripts/webhook_audit.py`
- Checklist: `skills/stripe/references/webhooks-production.md`
