---
description: End-to-end Google Analytics 4 + GTM audit with browser-driven verification of dataLayer events, Consent Mode v2 state, conversion (Key Event) configuration, remarketing audiences, and Ads linking - outputs a prioritized fix list with concrete code. Use when the user asks to audit GA4, verify GTM setup, check Consent Mode compliance, debug missing conversions, review remarketing audiences, validate dataLayer events, or check "why isn't my site converting". Not for general SEO, which /seo-audit covers, content and CTA optimization, which /content-strategy covers, or server-side analytics infrastructure unrelated to GA4 and GTM.
argument-hint: <url or local path> [--gtm <container-id>] [--competitor <url>] [--strict-mode]
---

# GA4 + GTM Audit

Comprehensive audit of a website's GA4 + GTM setup with live Playwright verification. Produces `.ga4-audit/REPORT.md` with prioritized fixes.

## CRITICAL RULES

1. **Verify live, not just code**. Use the playwright-mcp browser tools to load the site, inspect `dataLayer`, network requests to `google-analytics.com`/`googletagmanager.com`, and the cookie banner state.
2. **Check Consent Mode v2 compliance**. Analytics must not fire before consent on EU visitors; verify default `analytics_storage: 'denied'` and correct `update` calls.
3. **Never fabricate IDs**. If you cannot see the GA4 Measurement ID, GTM Container ID, or Ads Conversion ID, say so -- do not guess.
4. **Write output to `.ga4-audit/`** for persistence and re-runs.

## Phase 1 -- Discovery

Identify the target:
- Live URL or local dev server (start the dev server yourself with `#execute/runInTerminal` if needed)
- Extract GTM container ID (`GTM-XXXXXX`) from `<script src="...gtm.js?id=GTM-...">` or `<iframe src="...ns.html?id=GTM-...">`
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
- Verify `sessionStorage.getItem('_gtmSession')` / GA cookies (`_ga`, `_ga_<MEASUREMENT_ID>`) set correctly

### Event coverage
For each page type (home, product, checkout, thank-you), capture:
- `dataLayer.push({event: 'page_view', ...})` -- implicit if autotracking
- Custom events: `add_to_cart`, `purchase`, `sign_up`, `lead`, etc.
- Enhanced E-commerce items array for `purchase`

Write to `.ga4-audit/02-verification.md`.

## Phase 3 -- Configuration Audit

Using GA4 Admin API (if `gcloud` auth available) or manual walkthrough, verify:

### GA4 Property
- [ ] Data streams configured (Web, iOS, Android as needed)
- [ ] Enhanced Measurement enabled for relevant events (scroll, outbound clicks, site search, video, file download, form interactions)
- [ ] Data retention set (14 months recommended for paid users)
- [ ] IP anonymization on (EU requirement even though GA4 defaults to it)
- [ ] Google Signals enabled only if remarketing is needed AND consent has `ad_user_data: 'granted'`

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
  functionality_storage: 'denied',
  personalization_storage: 'denied',
  security_storage: 'granted',  // always granted
  wait_for_update: 500          // ms
});
```

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
