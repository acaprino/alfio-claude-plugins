---
description: End-to-end Google Analytics 4 + GTM audit with browser-driven verification of dataLayer events, Consent Mode v2 state, conversion (Key Event) configuration, remarketing audiences, and Ads linking - outputs a prioritized fix list with concrete code. Use when the user asks to audit GA4, verify GTM setup, check Consent Mode compliance, debug missing conversions, review remarketing audiences, validate dataLayer events, or check "why isn't my site converting". Not for general SEO, which /seo-audit covers, content and CTA optimization, which /content-strategy covers, or server-side analytics infrastructure unrelated to GA4 and GTM.
argument-hint: <url or local path> [--gtm <container-id>] [--strict-mode]
---

# GA4 + GTM Audit

Comprehensive audit of a website's GA4 + GTM setup with live Playwright verification. Produces `.ga4-audit/REPORT.md` with prioritized fixes.

## CRITICAL RULES

1. **Verify live, not just code**. Use the playwright-mcp browser tools to load the site, inspect `dataLayer`, network requests to `google-analytics.com`/`googletagmanager.com`, and the cookie banner state.
2. **Check Consent Mode v2 compliance**. Analytics must not fire before consent on EU visitors; verify default `analytics_storage: 'denied'` and correct `update` calls.
3. **Never fabricate IDs**. If you cannot see the GA4 Measurement ID, GTM Container ID, or Ads Conversion ID, say so -- do not guess.
4. **Write output to `.ga4-audit/`** for persistence and re-runs.

## Pre-flight

### Dependency check

Every live check in Phase 2 needs the playwright-mcp browser tools (`browser_navigate`, `browser_evaluate`, `browser_network_requests`). If they are not available, warn the user:

```
Playwright MCP tools are not available.

Live verification needs them to inspect dataLayer, network requests,
cookies, and the consent banner state in a real browser. Without them,
the audit is limited to reading source code.

Add the playwright-mcp server under Settings > AI > Manage MCP Servers,
then re-run.

  https://github.com/microsoft/playwright-mcp
```

Degraded fallback without Playwright: run a source-only audit (grep the codebase, fetch raw HTML via `#web/fetch`). Report every check that needs a live browser as **NOT VERIFIED**, never as pass or fail. Say so explicitly in the report header so no reader mistakes an unrun check for a passing one.

### Flags

- `--gtm <GTM-ID>` -- skip container detection in Phase 1 and audit the given container ID. Still flag any *other* container ID found in the source as a duplicate.
- `--strict-mode` -- treat every Warning as Critical in the final report and print an explicit `VERDICT: FAIL` line when any remains. Report text only; the command never sets a process exit code.

## Phase 1 -- Discovery

Identify the target:
- Live URL, or an already-running local dev server. To find one, read the project's dev script and its configured port, or ask the user for the URL. Never start a dev server and never claim one was started.
- Extract GTM container ID (`GTM-XXXXXX`) from `<script src="...gtm.js?id=GTM-...">` or `<iframe src="...ns.html?id=GTM-...">`. With `--gtm <GTM-ID>`, use the supplied ID instead and skip this step
- Extract GA4 Measurement ID (`G-XXXXXXXX`) from gtag config or dataLayer events
- Detect CMP: iubenda, Cookiebot, Orestbida CookieConsent, OneTrust, Axeptio, custom
- Detect Consent Mode v2 integration: look for `gtag('consent', 'default', {...})` and `gtag('consent', 'update', {...})` calls

Write discovery artifacts to `.ga4-audit/01-discovery.md`.

## Phase 2 -- Live Verification with Playwright

Open the site in Playwright, capture:

### Pre-consent state
- Before accepting cookies, record `dataLayer` contents and any network requests to `g/collect` (GA4) or `ads/ga-audiences` (Ads)
- Expected: no hits unless Consent Mode defaults allow (e.g., `ad_user_data: 'denied', analytics_storage: 'denied'`)
- Flag if `g/collect` fires before consent -- GDPR violation

### Post-consent state
- Accept cookies, record the `gtag('consent', 'update', ...)` call payload
- Record subsequent `g/collect` hits, their parameters (`en`, `tid`, `cid`, `dl`)
- Confirm GTM is live: inspect `window.dataLayer` contents and the network requests to `googletagmanager.com/gtm.js`
- Verify GA4 cookies are set: `_ga`, plus `_ga_<ID>` where `<ID>` is the Measurement ID with the `G-` prefix stripped (`G-ABC123` produces `_ga_ABC123`)

### Event coverage
For each page type (home, product, checkout, thank-you), capture:
- `dataLayer.push({event: 'page_view', ...})` -- implicit if autotracking
- Custom events: `add_to_cart`, `purchase`, `sign_up`, `lead`, etc.
- Enhanced E-commerce items array for `purchase`

Write to `.ga4-audit/02-verification.md`.

## Phase 3 -- Configuration Audit

Using the GA4 Admin API (if the user has API credentials configured for it) or a manual walkthrough of the GA4 admin UI with the user, verify:

### GA4 Property
- [ ] Data streams configured (Web, iOS, Android as needed)
- [ ] Enhanced Measurement enabled for relevant events (scroll, outbound clicks, site search, video, file download, form interactions)
- [ ] Data retention set (2 months is the default and the safe EU choice; 14 months only with a documented business justification)
- [ ] Google Signals enabled only if remarketing is needed AND consent has `ad_user_data: 'granted'`

IP anonymization needs no verification. GA4 truncates IPs by design and exposes no setting to check or toggle (see `gdpr-compliance-eu.md`).

### Key Events (Conversions)
- [ ] `purchase` marked as Key Event (always)
- [ ] Business-specific events marked (form_submit, begin_checkout, generate_lead)
- [ ] No double-counting (avoid marking both `click` and `generate_lead` for the same action)
- [ ] Key Event value set where monetary (`value` parameter)

### Audiences (for Remarketing)
- [ ] "All Users" audience exists (GA4 default)
- [ ] Retargeting audiences: cart abandoners, high-intent visitors, past purchasers
- [ ] Predictive audiences (likely-to-purchase, likely-to-churn) enabled -- note 28-day backfill (not immediate)
- [ ] Audience triggers fire on correct events

### Ads Linking
- [ ] GA4 property linked to Google Ads account
- [ ] Key Events imported into Ads as Conversions
- [ ] Enhanced Conversions enabled for key event imports (hashed email, phone)
- [ ] Consent signals propagated to Ads (`ad_storage`, `ad_user_data`, `ad_personalization`)

Write to `.ga4-audit/03-config.md`.

## Phase 4 -- Consent Mode v2 Deep Check

Consent Mode v2 is mandatory for EU traffic since March 2024.

### Default state
```javascript
// Required BEFORE gtag('config', 'G-...') or GTM load
gtag('consent', 'default', {
  ad_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied',
  analytics_storage: 'denied',
  wait_for_update: 500          // ms, optional but strongly recommended
});
```

Consent Mode v2 requires exactly these four signals. `functionality_storage`, `personalization_storage`, and `security_storage` are optional extras: accept them if the CMP sets them, never flag them as missing.

### Update on acceptance
```javascript
// After user accepts
gtag('consent', 'update', {
  ad_storage: 'granted',
  ad_user_data: 'granted',
  ad_personalization: 'granted',
  analytics_storage: 'granted'
});
```

Flag:
- [ ] Default call missing -> all traffic denied by default; no modeled conversions
- [ ] Default call fires AFTER GTM/gtag load -> race condition
- [ ] Granular consent categories not mapped (EU requires 4 separate signals, not just one "analytics")
- [ ] `wait_for_update` missing -> events fire with denied before update arrives

Write to `.ga4-audit/04-consent.md`.

## Phase 5 -- Report

Generate `.ga4-audit/REPORT.md`:

```markdown
# GA4 + GTM Audit Report -- <url> -- <date>

## Summary
- GTM Container: <GTM-XXXXXX>
- GA4 Property: <G-XXXXXXXX>
- CMP Detected: <iubenda / Cookiebot / etc.>
- Consent Mode v2: [COMPLIANT | PARTIAL | MISSING]
- Live verification: [PLAYWRIGHT | SOURCE-ONLY, live checks NOT VERIFIED]
- VERDICT: [PASS | FAIL]   <!-- with --strict-mode, any Warning promotes to Critical and forces FAIL -->

## Critical (GDPR / data-loss risk)
- ...

## High (breaking measurement)
- ...

## Medium (best-practice gaps)
- ...

## Nice-to-have
- ...

## Auto-implementable fixes
Code snippets ready to paste for each fix.
```

## Synergies

- Browser-based verification -> the playwright-mcp MCP server
- GA4/GTM knowledge base -> `ga4-implementation` skill
- Cookie banner (CMP) selection + config -> `privacy-doc-generator` in the `business` bundle
- Full SEO audit (separate) -> `/seo-audit`
