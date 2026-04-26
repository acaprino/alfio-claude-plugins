# Diagnostics and troubleshooting

The two halves: **why a site doesn't generate results** ("I have GA4 but no bookings come in") and **why an installation is broken**. Plus the EU-specific data-thresholding workarounds and the Clarity-with-Consent-Mode wiring.

## When to use

Diagnosing low conversion, debugging missing events, or hardening a fresh install. For installation steps, see `gtm-setup.md` and `framework-integration.md`.

## The fundamental diagnostic split: traffic or conversion?

After GA4 has been collecting for **at least 2-4 weeks** (minimum 100 sessions for any pattern to be statistically meaningful):

### Scenario A -- nobody visits (traffic problem)

Reports → Acquisition → Traffic Acquisition. Users/Sessions near zero over 30 days = problem is upstream of GA4.

Check: Search Console (`site:example.com` query, indexing, impressions/CTR/position), Google Business Profile (claimed, complete, photos/reviews), inbound links (OTAs, directories, social).

**Hand off to**: `seo-specialist` agent -- traffic problems are SEO problems, need their own tooling.

### Scenario B -- people visit but don't convert (conversion problem)

Reports → Engagement → Events. Sessions exist (>100/month) but Key Events count is zero or very low.

Check: build a **Funnel Exploration** (Explore → Funnel Exploration), find the drop-off step. Compare mobile vs desktop bounce (delta > 20pts = mobile UX problem). Reports → Engagement → Pages and Screens to see if visitors reach the conversion page. Reports → Engagement → Landing Page to see entry points. Install **Microsoft Clarity** for the "why" GA4 can't show.

**Hand off to**: `content-marketer` (CTA, copy) and/or `premium-web-consultant` skill in the `frontend` plugin (UX).

## Funnel templates

- **Hospitality**: homepage → gallery/details → contact/prenota → `generate_lead`
- **Ecommerce**: `view_item_list` → `view_item` → `add_to_cart` → `begin_checkout` → `purchase`
- **SaaS**: homepage → pricing → sign up → `sign_up`

The biggest drop-off step IS the priority. 80% reach the form but 5% submit it = the form is the problem (too long, broken, asks too much).

## Data thresholding for low-traffic sites (the EEA workaround)

GA4 hides report rows when user counts are too low (orange triangle warning). Aggressive when: **Google Signals enabled** (biggest factor), demographic dimensions used, narrow date ranges, segments < 50 users.

### Workarounds

1. **Disable Google Signals** in Admin → Data Settings → Data Collection (recommended for EEA anyway for GDPR)
2. **Use 30+ day windows** in reports
3. **Avoid demographic dimensions** (Age, Gender) -- they trigger thresholding hard
4. **Switch Reporting Identity to Device-based** (Admin → Reporting Identity) -- sacrifices some attribution for less thresholding
5. **Avoid very narrow segments** -- prefer fewer, broader

For sites under 1000 sessions/month, thresholding is constant. Below 100/month, standard reports are too sparse to act on -- focus on Realtime, DebugView, and Microsoft Clarity instead.

## Microsoft Clarity (the free heatmap+session-replay tool that fills GA4's gaps)

Free, no traffic limits. Heatmaps + session recordings show **why** users don't convert in a way GA4 can't.

Install: clarity.microsoft.com → create project → paste embed in `<head>` of every page (same as GA4). Optional: Clarity → Settings → Setup → Google Analytics integration to link recordings to GA4 segments. Clarity and GA4 coexist without conflicts.

### GDPR consent for Clarity (the local-rule worth keeping)

Clarity sets non-essential cookies (`_clck`, `_clsk`, `CLID`, `MUID`) and **requires consent in EU** just like GA4. **From 31 October 2025, Microsoft applies consent-signal requirements for EEA users on Clarity.**

Place Clarity in the same "Analytics" category in your CMP and ensure it is blocked until consent is given:

- **iubenda / Cookiebot autoblocking**: automatic, nothing to do.
- **Orestbida CookieConsent**: mark the Clarity script tag with `type="text/plain" data-category="analytics"`.

### What to look for in Clarity

- **Rage clicks** -- rapid clicks in the same spot → broken button or expected interactivity that doesn't exist
- **Dead clicks** -- click on element that doesn't respond → misleading visual cue
- **Excessive scrolling** -- can't find what they're looking for
- **Quick backs** -- page didn't match expectation
- **JS errors** -- Clarity logs them in recordings; useful for catching prod bugs

## Google Search Console (the missing piece)

Measures what happens **before** the user arrives: impressions, CTR, average position, search queries (which GA4 cannot see), indexing status, crawl errors, Core Web Vitals, mobile usability.

For "no bookings come in" diagnosis, **Search Console is the FIRST tool** to check if the problem is that Google doesn't find or doesn't show the site.

Verification options: HTML file at site root, `<meta name="google-site-verification">`, DNS TXT record, or Google Tag (auto-verify if GA4 already installed via the same account).

Linking: GA4 → Admin → Product Links → Search Console Links → Link → publish "Search Console" collection in Reports Library. Then Reports → Search Console → Queries shows the queries users searched -- the only place to see them in GA4.

## Industry benchmarks (rough -- prefer historical-comparison)

Hospitality / travel: engagement rate 50-60%, avg engagement 1-3 min, views/session 2-4, mobile-vs-desktop bounce delta < 10pts.

Ecommerce: engagement rate 55-65%, avg engagement 2-5 min, cart-to-purchase 1-3% (varies vertical), add-to-cart-to-checkout 30-50%.

Red flags: engagement < 40-45%, avg engagement < 30-60s, single-page bounce, mobile/desktop delta > 20pts, cart-to-purchase < 0.5%, ATC-to-checkout < 15%.

## The 10 most common installation errors (the local cookbook)

In order of frequency:

### 1. Snippet on only one page (most common static-site error)

Symptom: Reports → Engagement → Pages and Screens shows only one page (typically homepage). Tag Coverage report flags missing pages.

Fix: paste in every page, or centralize via layout/include. Grep the build output to verify.

### 2. Double tracking (silent and insidious)

Symptom: every metric appears 2x. Hard to detect -- no errors, just "good-looking" data until you compare with another source.

Cause: gtag.js AND GTM both injecting the same Measurement ID, or the same snippet pasted twice.

Detection: DevTools → Network → filter `collect` -- one request per page_view, not two. View-source for `G-XXXXXXXXXX` and `GTM-XXXXXXX` -- exactly one of each. Tag Assistant warns about duplicates.

Fix: remove one. **Historical data corrupted by double tracking is NOT recoverable.** Mark the recovery date and treat older data as suspect.

### 3. Snippet in the wrong position

Symptom: missing early page interactions, especially `session_start` and first `page_view`.

Fix: snippet must be the very first script in `<head>`. The GTM noscript iframe goes immediately after `<body>`, never inside `<head>`.

### 4. Wrong Measurement ID

Symptom: data goes to wrong property or nowhere. Realtime empty.

Cause: typo, extra spaces, or smart quotes (`"` and `"`) copied from a word processor instead of straight quotes (`"`).

Fix: copy-paste directly from GA4 → Admin → Data Streams. Verify byte-for-byte. **Never retype an ID.**

### 5. Internal traffic not excluded

Symptom: numbers bigger than they should be, especially homepage. Owner visits skew data.

Fix: see "Internal traffic exclusion" in `events-and-conversions.md`.

### 6. CMP loads after GTM (the Consent Mode v2 trap)

Symptom: tags fire before consent state updates. Consent Mode v2 reports show all-denied even after user accepted.

Cause: Consent Mode default block runs after the GTM snippet, OR the CMP loader runs after GTM.

Fix: enforce `<head>` order: (1) Consent Mode v2 default block → (2) CMP loader → (3) GTM snippet. See `gtm-setup.md` for the template.

### 7. WordPress caching plugin stripping the snippet

Symptom: works in admin/preview but not in incognito on the live front-end.

Cause: W3 Total Cache, WP Rocket, LiteSpeed, WP Super Cache -- HTML minification or "delay JavaScript execution".

Fix: flush cache. Add `googletagmanager.com` and `gtm.js` to the "do not minify" / "exclude from delay" list.

### 8. Hydration mismatch (Next.js, React)

Symptom: console warnings about hydration mismatch.

Cause: GTM injected via `dangerouslySetInnerHTML` in a server component without unique `id`.

Fix: `next/script` or `@next/third-parties/google`'s `<GoogleTagManager>` instead.

### 9. Ad blockers blocking GA4

Symptom: missing data for some users (estimates: 10-30% of users in Italy block trackers).

Cause: uBlock Origin, Ghostery, Brave Shields, Firefox tracking protection.

Fix: not directly fixable. Server-side GTM (sGTM) is the production-grade workaround. For most sites, accept the loss.

### 10. Wrong trigger type for the GA4 Google Tag

Symptom: tags fire in the wrong order, especially with Consent Mode.

Cause: trigger set to "All Pages" instead of "**Initialization - All Pages**".

Fix: in GTM, edit the GA4 Google Tag, change the trigger to **Initialization - All Pages** (under "Other"). Republish.

## Verification routine after every change

Run this BEFORE considering a change live:

1. Preview mode in GTM (Tag Assistant)
2. Publish with meaningful version name + description
3. Realtime report (verify event appears within minutes)
4. DebugView (verify parameters populated)
5. Wait 24-48h for standard reports
6. Standard reports (verify count looks reasonable)
7. Test on mobile (many issues only show on mobile)
8. Test in incognito with no ad blocker (cleanest environment)

## Official docs

- GA4 Realtime: https://support.google.com/analytics/answer/9271392
- DebugView: https://support.google.com/analytics/answer/7201382
- Tag Coverage report: https://support.google.com/analytics/answer/14066363
- Tag Assistant: https://tagassistant.google.com
- Funnel Explorations: https://support.google.com/analytics/answer/9327974
- Microsoft Clarity: https://clarity.microsoft.com (docs: https://learn.microsoft.com/en-us/clarity/)
- Clarity Consent Mode (Oct 2025 EEA requirements): https://learn.microsoft.com/en-us/clarity/setup-and-installation/cookie-consent
- Search Console verification: https://support.google.com/webmasters/answer/9008080
- Search Console + GA4 link: https://support.google.com/analytics/answer/10737381
- Data thresholding explained: https://support.google.com/analytics/answer/13109118
- Reporting Identity: https://support.google.com/analytics/answer/10978788

## Related

- `gtm-setup.md` -- the install + EEA lockdown that prevents many of these issues
- `framework-integration.md` -- the per-framework install gotchas
- `events-and-conversions.md` -- internal traffic exclusion + EEA reporting identity choice
- `gdpr-compliance-eu.md` -- the compliance layer (why Google Signals is off in EEA setups)
