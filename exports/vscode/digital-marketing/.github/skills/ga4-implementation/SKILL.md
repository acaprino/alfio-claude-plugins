---
name: ga4-implementation
description: >
  Knowledge base for implementing Google Analytics 4 (GA4) and Google Tag Manager (GTM) on
  websites, with deep coverage of EU/GDPR Consent Mode v2 compliance, CMP selection (iubenda,
  Orestbida CookieConsent), event taxonomy, conversion (Key Event) configuration, remarketing
  audiences, framework-specific integration (vanilla HTML, Next.js, React, WordPress), Microsoft
  Clarity and Search Console integration, and diagnostic patterns for low-traffic sites. Use when
  implementing or auditing GA4, GTM, gtag, dataLayer, Consent Mode v2, cookie banner, conversion
  tracking, Key Events, remarketing audiences, Google Ads conversion import, Enhanced Conversions,
  or diagnosing why a site has traffic but no conversions. Not for the task involves non-Google
  analytics (Matomo, Plausible, Fathom), server-side analytics infrastructure unrelated to
  GA4/GTM, BigQuery export pipelines, or pure SEO work without a measurement layer.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: digital-marketing
---

# GA4 Implementation

This skill is the knowledge base behind the `ga4-implementation-expert` agent. It covers everything needed to deploy Google Analytics 4 with Google Tag Manager on a real website: the legal/compliance layer that is mandatory in the EU, the technical installation across frameworks, the event and conversion taxonomy, the audiences for remarketing, and the diagnostic patterns to figure out why a site is not converting.

## Compliance is the blocking prerequisite

GA4 cannot be legally deployed in Italy or the EU without all of the following:

1. A technical Consent Management Platform (CMP) that **blocks GA4 cookies before user consent**, not just a written cookie policy
2. A cookie banner that meets the Italian Garante requirements (equal-weight Accept/Reject, granular preferences, no scroll-as-consent, 6-month resuppression)
3. **Google Consent Mode v2** with all four signals (`analytics_storage`, `ad_storage`, `ad_user_data`, `ad_personalization`) set to `denied` by default
4. Accepted Data Processing Terms (Art. 28 GDPR) in the GA4 account settings
5. Google Signals **disabled** for EEA traffic

A cookie policy page that describes which cookies the site uses **does not satisfy the law**. The site must have a technical mechanism that prevents the cookies from being set in the first place. This is the most common compliance failure on Italian and EU sites.

For non-EU traffic the legal bar is lower, but Consent Mode v2 is still mandatory by Google policy since 6 March 2024 for any property serving any EEA user. Without it, Google disables remarketing and audience building.

## How to use this guide

Most GA4 implementation tasks follow this sequence:

1. **Audit compliance first** - read [`references/gdpr-compliance-eu.md`](references/gdpr-compliance-eu.md). If the CMP and Consent Mode v2 layer is not in place, fix that before touching tags.
2. **Install GTM and the GA4 tag** - read [`references/gtm-setup.md`](references/gtm-setup.md) for the step-by-step walkthrough including snippet placement order.
3. **Map business goals to events** - read [`references/events-and-conversions.md`](references/events-and-conversions.md) for the standard event taxonomy, custom dimensions, Key Events marking, and audience patterns.
4. **Apply the framework-specific integration** - read [`references/framework-integration.md`](references/framework-integration.md) for vanilla HTML, Next.js (App + Pages Router), React, and WordPress patterns.
5. **Verify and diagnose** - read [`references/diagnostics-troubleshooting.md`](references/diagnostics-troubleshooting.md) for verification tools, the traffic-vs-conversion diagnostic split, industry benchmarks, and the common errors checklist.

For diagnostic-only tasks ("why isn't my site converting"), jump straight to step 5.

## Reference index

### [`gdpr-compliance-eu.md`](references/gdpr-compliance-eu.md)

The legal layer. Italian Garante decisions timeline (2022 Caffeina, 2023 DPF adequacy, 2025 T-553/23, pending Schrems III appeal), cookie banner mandatory requirements, GA4 account-level mandatory configurations, the four Consent Mode v2 signals and their defaults, Basic vs Advanced mode trade-off, CMP selection (iubenda recommended for non-technical users, Orestbida CookieConsent v3 as the free open-source alternative), and ready-to-paste code snippets.

### [`gtm-setup.md`](references/gtm-setup.md)

The technical installation walkthrough. Why GTM is preferred over gtag.js direct, step-by-step GA4 property creation, GTM container creation, snippet installation in correct order (Consent Mode v2 default block → CMP loader → GTM head snippet → GTM noscript body snippet), GA4 Google Tag configuration with the Initialization - All Pages trigger, container publishing, and the verification checklist (Realtime, Tag Assistant, DebugView, DevTools Network).

### [`events-and-conversions.md`](references/events-and-conversions.md)

The measurement layer. Enhanced Measurement auto-events, custom event patterns via GTM (book button clicks, tel/mailto/wa.me link clicks, form submissions, external OTA clicks), the GA4 recommended events list with item array structure for ecommerce, custom dimensions registration walkthrough, Key Events marking (formerly Conversions), the standard audience pattern set, Google Ads link procedure, Enhanced Conversions, and attribution settings.

### [`framework-integration.md`](references/framework-integration.md)

The per-framework implementation patterns. Vanilla HTML and static site generators (Jekyll, Hugo, Eleventy), Next.js (App Router with `@next/third-parties/google`, Pages Router with `_document.tsx` and `next/script`, route change tracking), CRA/Vite React with router listeners, WordPress (theme `functions.php` action hooks vs plugins like Site Kit and GTM4WP), and common pitfalls (hydration mismatches, double-firing on Strict Mode, caching plugins stripping snippets).

### [`diagnostics-troubleshooting.md`](references/diagnostics-troubleshooting.md)

The diagnostic and troubleshooting layer. The traffic-vs-conversion split (Scenario A: nobody visits / Scenario B: people visit but don't convert) with the GA4 reports to check for each, Acquisition report interpretation, Funnel Exploration setup, hospitality and travel benchmarks, data thresholding workarounds for low-traffic sites, Microsoft Clarity integration, Google Search Console integration, and the common errors checklist (snippet on one page only, double tracking, wrong placement, Measurement ID typos, internal IP exclusion).

## What this skill does not cover

- **Server-side GTM (sGTM)**: out of scope. If the user needs server-side tagging, point them to Google's official documentation.
- **Universal Analytics → GA4 migration**: UA is sunset since July 2023. Historical UA data is read-only and cannot be migrated; GA4 must be set up fresh.
- **BigQuery export**: advanced topic, link the user to the GA4 BigQuery linking docs when they ask.
- **Looker Studio dashboard templates**: GA4 has built-in reports that suffice for most cases; Looker Studio is a follow-on layer.
- **Non-Google analytics**: Matomo, Plausible, Fathom, etc. The DPF-fallback contingency note in `gdpr-compliance-eu.md` mentions Matomo briefly as the EU-hosted alternative if the DPF is invalidated, but this skill is GA4-specific.

## Source attribution

The legal and compliance content reflects Italian Garante guidance (Provvedimenti 9677876 and 9782874), the EU-US Data Privacy Framework adequacy decision (10 July 2023), the Tribunale Generale UE ruling on Case T-553/23 (3 September 2025), and the Google Consent Mode v2 specification as of 2025-2026. Verify against current Garante and Google publications when implementing for production sites, especially if a "Schrems III" decision lands at the Court of Justice in late 2026 or early 2027.
