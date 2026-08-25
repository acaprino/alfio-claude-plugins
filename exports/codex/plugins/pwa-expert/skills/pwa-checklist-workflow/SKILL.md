---
description: >
  Walks the production deploy checklist, reporting pass, fail or N/A per category against the codebase and an optional URL.
  TRIGGER WHEN: checking PWA launch readiness, or walking a deterministic go/no-go list before deploying.
  DO NOT TRIGGER WHEN: an open-ended adversarial audit fits better (use /pwa-expert:pwa-audit).
argument-hint: "[path or URL]"
---

# /pwa-expert:pwa-checklist

Walk the production deploy checklist from `references/production-checklist.md` interactively against the current project (or the provided URL).

Delegate to `pwa-architect`. The agent reads `production-checklist.md` upfront (this is one of the few cases where preloading a reference is correct, because the command IS the checklist), then walks every item.

## Modes

- If `$ARGUMENTS` is a URL: walk the checklist against the live deployment via `playwright-skill` where applicable, plus the codebase for items that can only be verified in source.
- If `$ARGUMENTS` is a path or omitted: walk against the codebase only.

## How the walk works

For every item in every category of `production-checklist.md`:

1. State the item verbatim.
2. Verify it. Use `Read`, `Grep`, `Glob`, `Bash`, or `playwright-skill` tools as appropriate.
3. Record the result as one of: **PASS**, **FAIL**, **N/A** (with a reason for N/A).

## Output format

Produce a markdown report:

```
# Production Checklist Report

**Target:** <path or URL>
**Date:** YYYY-MM-DD

## Summary

| Category | Pass | Fail | N/A | Score |
|---|---|---|---|---|
| Manifest | X | Y | Z | X / (X+Y) |
| iOS-specific | ... |
| Service Worker | ... |
| Security | ... |
| Performance | ... |
| Push | ... |
| Storage | ... |
| Testing | ... |
| Distribution | ... |
| Monitoring | ... |
| **Overall** | ... |

## Manifest

- [PASS] id is explicit (not implied from start_url). Found in `public/manifest.webmanifest:2`.
- [FAIL] Icons: 192 PNG purpose: "maskable" missing. Add via /pwa-expert:pwa-scaffold or by hand.
- ...

(... and so on for every category, every item)

## Recommended next actions

(Numbered list of the highest-impact fails, ordered by severity.)
```

## Difference from /pwa-expert:pwa-audit

- `pwa-audit` is open-ended and adversarial. It uses domain knowledge to find defects the checklist does not enumerate.
- `pwa-checklist` is deterministic. The output maps 1:1 to the source guide's deploy checklist sections. Two runs on the same target produce structurally identical reports.

Use `pwa-checklist` for release gates and CI integration. Use `pwa-audit` for design reviews and pre-launch deep-dives.

## CI integration

The deterministic, structured output makes this command suitable as a release gate:

1. Run `/pwa-expert:pwa-checklist <path-or-URL>` from a CI step that invokes Claude Code.
2. Parse the Summary table for the **Overall** row.
3. Fail the build if `Fail > 0` for any category that the team has flagged as blocking (typically Manifest, Service Worker, Security).
4. Treat `N/A` as informational, not failing.

## Category-to-reference map for FAIL remediation

When recording a FAIL, point the user at the matching reference so they can self-serve the fix:

| Checklist category | Reference file |
|---|---|
| Manifest, iOS-specific | `references/manifest.md` |
| Service Worker | `references/service-workers.md` |
| Security | `references/security.md` |
| Performance | `references/performance.md` |
| Push | `references/push-notifications.md` |
| Storage | `references/storage-persistence.md` |
| Testing | `references/frameworks-tooling.md` (debugging surface) |
| Distribution | `references/distribution.md` |
| Monitoring | `references/performance.md` (CrUX / RUM) and `references/push-notifications.md` (pushsubscriptionchange) |

## Output rules

- No emojis. Status indicators are text only: `[PASS]`, `[FAIL]`, `[N/A]`.
- Cite a file and line for every PASS / FAIL where possible (local mode) or a URL fragment / manifest field (live mode).
- Recommend the matching reference file from the knowledge base for every FAIL, so the user can self-serve the fix.
