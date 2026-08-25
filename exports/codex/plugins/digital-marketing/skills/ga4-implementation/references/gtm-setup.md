# GTM setup walkthrough

How to install GTM correctly with Consent Mode v2 ordering, and the EEA-specific account-level lockdown to do BEFORE deploying. Property/container creation steps and the verification routine live upstream; this file is the rationale + the load-bearing rules.

## When to use

Setting up a fresh GA4 + GTM install. Read `gdpr-compliance-eu.md` FIRST if the site doesn't have a working CMP -- GTM should not be deployed without one.

## Why GTM, not gtag.js direct

Even on a small static site, GTM wins for three reasons:

1. **Consent Mode v2 is dramatically easier with GTM** thanks to CMP templates in the Community Template Gallery and the GTM debug tools that show consent state per tag fire.
2. **Future Google Ads work needs zero code changes** -- conversion tags, remarketing tags, Floodlight all configured in the GTM web UI.
3. **For non-developer site owners**, every tracking change after initial setup happens in the GTM UI, not in the codebase.

Exceptions where gtag.js direct is acceptable: developer-only project with strong reasons to avoid extra script tags, single-tag deployment that will never grow, tight landing page where every byte matters. Default to GTM otherwise.

The official Google docs (March 2026) recommend the same: *"If you're unfamiliar with javascript, we recommend using Google Tag Manager instead of gtag.js."*

## EEA account-level lockdown (do this before publishing the container)

Configure these BEFORE the container goes live. Changing them later is harder and some changes don't apply retroactively.

| Setting | Path | Value |
|---------|------|-------|
| **Data retention** | Admin → Data Collection and Modification → Data Retention | **14 months** (or 2 months for max compliance), enable **"Reset user data on new activity"** |
| **Google Signals** | Admin → Data Settings → Data Collection | **Disabled** for EEA properties |
| **Attribution model** | Admin → Data Display → Attribution Settings | Data-driven (default), set lookback to fit business cycle (90d travel, 30d ecommerce) |
| **DPA** | Admin → Account Settings | Accept Data Processing Terms (Art. 28 GDPR) |
| **Country at signup** | Admin → Account Settings | **Italy** (or relevant EU country) so EU-specific terms apply |

Disabling Google Signals is the single biggest GDPR-compliance lever and also reduces data thresholding on low-traffic properties. See `gdpr-compliance-eu.md` for the full rationale.

## The two snippets (every page)

GTM provides two snippets. Both must be present on **every page**.

```html
<!-- Snippet 1: in <head>, as high as possible -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
```

```html
<!-- Snippet 2: immediately after opening <body> -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
```

Replace `GTM-XXXXXXX` with the actual container ID.

## The `<head>` ordering template (the load-bearing rule)

If the CMP doesn't auto-handle Consent Mode v2 defaults (iubenda does), insert the default block **before** the GTM head snippet. Complete order:

```html
<head>
  <!-- 1. Consent Mode v2 defaults (skip if CMP handles automatically) -->
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('consent', 'default', {
      'ad_storage': 'denied',
      'ad_user_data': 'denied',
      'ad_personalization': 'denied',
      'analytics_storage': 'denied',
      'wait_for_update': 500
    });
  </script>

  <!-- 2. CMP loader (iubenda embed, Cookiebot autoblock, Orestbida config) -->

  <!-- 3. GTM head snippet -->
  <script>(function(w,d,s,l,i){...})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>

  <meta charset="UTF-8">
  <!-- ... -->
</head>
<body>
  <!-- GTM noscript iframe HERE, never inside <head> -->
  <noscript><iframe src="..."></iframe></noscript>
  <!-- page content -->
</body>
```

For frameworks (Next.js, React, WordPress) instead of vanilla HTML, see `framework-integration.md`.

## Initialization - All Pages (the trigger that catches everyone)

When configuring the GA4 Google Tag inside GTM:

- Tag type: **Google Tag** (not the older "Google Analytics: GA4 Configuration" -- still exists but Google Tag is current).
- Trigger: **Initialization - All Pages**, NOT "All Pages".

**Why**: the Initialization trigger fires before all other triggers, which is critical for Consent Mode -- the Google tag must initialize before any tag that depends on consent state. Wrong trigger choice = tags fire before consent updates → Consent Mode v2 reports show all-denied even after acceptance. This is one of the top install errors (see `diagnostics-troubleshooting.md` #10).

## Gotchas

- **Don't paste the snippet only on `index.html`.** Centralize via layout/include and grep the build output for the container ID on every deploy. The #1 static-site error.
- **Don't have both gtag.js and GTM injecting the same Measurement ID** -- silent double tracking. Hard to detect because there are no errors, the data just looks "good" until you compare with another source. Historical data corrupted by double tracking is **not recoverable**.
- **Smart quotes (`"` and `"`)** copied from a word processor break the script silently. Always copy from the GTM/GA4 web UI, never retype.
- **Snippet inside a `<div>`, after `</head>`, or buried under many other scripts** = lost early page interactions, especially `session_start` and the first `page_view`.
- **The DPA acceptance is a separate click** in Admin → Account Settings. It's NOT the Terms of Service. Without it you don't have an Art. 28 GDPR compliant data-processor relationship with Google.
- **Country selection at signup matters** -- it determines which Terms of Service variant applies. Choosing Italy (or your EU country) at signup is a one-shot decision; can't easily change later.

## Container backups (cheap insurance)

Admin → Containers → Export Container → save the JSON in your project repo as `gtm-backup-YYYY-MM-DD.json`. Restore: Admin → Import Container → Overwrite or Merge. Good practice before major changes and useful for staging→production migration.

## Environments (overkill for small sites)

GTM Environments (Admin → Environments → New) give per-environment snippet variants with `&environment_auth=...` parameters. Worth it for sites with multiple stakeholders or strict change control; for small sites publish directly to the default environment.

## Standard reports timeline

Realtime works immediately after the first event. **Standard GA4 reports** (Acquisition, Engagement, etc.) take **24-48 hours** to populate. Don't panic if Reports → Engagement → Pages and Screens is empty for the first day -- check Realtime instead.

## Official docs

- GTM official quickstart: https://support.google.com/tagmanager/answer/6103696
- GA4 setup quickstart: https://support.google.com/analytics/answer/9304153
- Google Tag (vs older GA4 Config tag): https://support.google.com/tagmanager/answer/12382666
- Initialization triggers: https://support.google.com/tagmanager/answer/7679319
- Consent Mode v2: https://developers.google.com/tag-platform/security/guides/consent
- Tag Assistant: https://tagassistant.google.com
- DebugView: https://support.google.com/analytics/answer/7201382
- Tag Coverage report: https://support.google.com/analytics/answer/14066363
- Data retention: https://support.google.com/analytics/answer/7667196
- Container Import/Export: https://support.google.com/tagmanager/answer/6106997
- Environments: https://support.google.com/tagmanager/answer/6311518

## Related

- `framework-integration.md` -- the framework-specific install (Next.js, React, WordPress, ...)
- `events-and-conversions.md` -- the events to wire up after the install works
- `gdpr-compliance-eu.md` -- the compliance layer that comes BEFORE this
- `diagnostics-troubleshooting.md` -- the 10 errors that break installations
