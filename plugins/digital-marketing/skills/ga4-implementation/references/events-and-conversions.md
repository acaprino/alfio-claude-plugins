# Events, conversions, audiences

The measurement layer: which events to fire, the GTM trigger recipes that map clicks to events, custom dimensions, Key Events (renamed from Conversions in March 2024), audiences for remarketing, Google Ads link, and EEA-specific reporting choices.

## When to use

Configuring tracking AFTER GTM is installed -- adding events, marking Key Events, building remarketing audiences, linking Google Ads. For the install itself, see `gtm-setup.md` and `framework-integration.md`.

## What GA4 tracks automatically (Enhanced Measurement)

Default-enabled when the data stream is created:

| Event | Trigger |
|-------|---------|
| `page_view` | Every page load (incl. SPA virtual page views with the right GTM trigger) |
| `session_start`, `first_visit`, `user_engagement` | Auto |
| `scroll` | At 90% page scroll (toggleable) |
| `click` (outbound) | Click on link to different domain (toggleable) |
| `view_search_results` | URL contains a known search param (toggleable, customizable) |
| `video_start`/`progress`/`complete` | Embedded YouTube with JS API (toggleable) |
| `file_download` | Click on link with known file extension (toggleable) |

Layer custom events on top for actionable conversion data.

## GTM click-trigger recipes (the local cookbook)

The 6 patterns worth memorizing. All use a GTM **trigger** + a **GA4 Event tag** wired to the existing GA4 Google Tag (or measurement ID).

### Book / Reserve button click

- Trigger: **Click - All Elements**, Some Clicks, `Click Text` contains `Prenota` (or `Book`/`Reserve`)
- Optional: also match `Click Classes` if the button has a unique class
- Tag: GA4 Event, name `book_now_click`, params `button_text = {{Click Text}}`

### WhatsApp link

- Trigger: **Click - Just Links**, Wait for tags = yes, `Click URL` contains `wa.me`
- Tag: name `whatsapp_click`, param `link_url = {{Click URL}}`

### Phone (`tel:`)

- Trigger: **Click - Just Links**, `Click URL` starts with `tel:`
- Tag: name `phone_click`, param `phone_number = {{Click URL}}`

### Email (`mailto:`)

- Trigger: **Click - Just Links**, `Click URL` starts with `mailto:`
- Tag: name `email_click`

### Form submission

Two reliable approaches:

- **A. Native form + thank-you redirect**: trigger on `Page Path equals /grazie`, fire `generate_lead` with `method=contact_form`.
- **B. AJAX form, no redirect**: form library pushes `dataLayer.push({event:'form_submit_success', form_name:'contact'})` on success. Trigger on Custom Event `form_submit_success`, fire `generate_lead` with `method=contact_form`, `form_name = {{DLV - form_name}}`.

### External OTA / booking platform click

- Trigger: **Click - Just Links**, `Click URL` contains `booking.com` OR `airbnb`
- Tag: name `booking_platform_click`, param `platform` = a Custom JS Variable that returns `'booking'` or `'airbnb'` based on the URL

## Custom dimensions

Event parameters do NOT appear in GA4 reports automatically. Each parameter that you want to filter/group/break down by must be **registered**:

GA4 → Admin → Data Display → Custom Definitions → Create custom dimension. Scope **Event** (User scope is for user properties). Event parameter name is **case-sensitive** and must match the GTM tag exactly.

- Up to 24h to appear in reports.
- **NOT retroactive** -- only sees values collected after registration.
- Hard limit: **50 event-scoped + 25 user-scoped per property**. Don't register every parameter -- only the ones you'll actually slice by.

## Key Events (formerly Conversions)

Renamed March 2024. "Conversion" is now Google-Ads-only. Functionally identical: a flag on an event that makes it a primary success metric.

To mark: GA4 → Admin → Data Display → Events → toggle "Mark as key event". The event must have fired at least once to appear in the list.

### Suggested Key Events for hospitality / service business

- `generate_lead` (form submission) -- primary
- `book_now_click` -- primary
- `whatsapp_click`, `email_click`, `phone_click` -- primary
- `booking_platform_click` -- secondary (micro-conversion: user left to a 3rd party)

For ecommerce: primary `purchase`, secondary `begin_checkout`, `add_payment_info`, `add_to_cart`.

## Recommended events (for ecommerce: use the standard names)

GA4 has a fixed list of "recommended events" mapped to standard reports (Monetization, Funnel). Using the official names instead of inventing custom ones unlocks built-in reports for free. Full list and required parameters: https://support.google.com/analytics/answer/9267735.

The `items[]` array shape and the `ecommerce` dataLayer object structure are documented at https://developers.google.com/tag-platform/gtagjs/reference/events. In GTM, on a "GA4 Event" tag with name `purchase`, enable More Settings → Ecommerce → "Send Ecommerce data" with source "Data Layer" -- GTM picks up the `ecommerce` object automatically.

For non-ecommerce: `login`, `sign_up`, `search`, `share` are also worth using when applicable.

## Audiences (build them on day one)

Audiences populate **only from creation date forward** -- they are NOT retroactive. Create them as soon as the property is set up, before campaigns launch.

### Standard audience set (the local recipe)

| Audience | Definition | Membership |
|----------|------------|-----------|
| All visitors 30 days | `session_start` triggered | 30d |
| All visitors 180 days | `session_start` triggered | 180d |
| Engaged visitors | session > 60s AND pageviews > 2 | 90d |
| Visitors to booking page | `page_location` contains `/prenota` or `/book` | 30d |
| Visitors to gallery | `page_location` contains `/gallery` or `/foto` | 30d |
| **High-intent no-conversion** | fired `book_now_click` OR `whatsapp_click` but NOT `generate_lead` | 30d |
| Cart abandoners (ecommerce) | fired `begin_checkout` but NOT `purchase` | 30d |
| Past purchasers (ecommerce) | fired `purchase` | 540d (max) |

The high-intent-no-conversion audience is the most valuable single audience for retargeting -- people who showed booking intent but didn't complete.

Create: GA4 → Admin → Data Display → Audiences → New → Custom audience. Optionally attach an audience trigger (custom event when user joins).

## Google Ads link (do this even before campaigns)

GA4 → Admin → Product Links → Google Ads Links → Link. Linker needs admin on both sides. Enable "Personalized advertising".

Once linked: Ads cost data shows in GA4 Acquisition reports, audiences auto-export to Google Ads Audience Manager, **Key Events become importable as Conversion Actions** (Google Ads → Goals → Conversions → Import → GA4 properties → Web).

## Enhanced Conversions (raise conversion-rate signal)

Improves attribution by matching first-party hashed user data (email, phone) submitted in forms/checkout against Google's data.

Enable: GA4 → Admin → Data Streams → select stream → Configure tag settings → Show all → Allow user-provided data capabilities → ON. In GTM, on the GA4 Google Tag or the conversion event tag, configure user-provided data with selectors for the email/phone fields.

Material lift on Smart Bidding signal quality for Google Ads with form-based conversions.

## EEA reporting identity (the EU-specific local choice)

GA4 → Admin → Reporting Identity offers three modes:

- **Blended** (default) -- combines User-ID, Google Signals, Device-ID, modeling. Best accuracy when Google Signals is enabled.
- **Observed** -- User-ID, Google Signals, Device-ID without modeling.
- **Device-based** -- only Device-ID.

**For EU sites with Google Signals disabled** (the GDPR-recommended setup), **Device-based often gives the most useful low-traffic reports**. Modeling and Google Signals data trigger thresholding aggressively below 1k sessions/month -- Device-based avoids that entirely. The trade-off is some attribution accuracy.

## Internal traffic exclusion (the gotcha that pollutes data forever)

Owner visits skew everything. Steps:

1. GA4 → Admin → Data Streams → stream → Configure tag settings → Show all → **Define internal traffic** → Create rule "Owner IP", traffic_type = `internal`, "IP equals" → enter your IP.
2. GA4 → Admin → Data Settings → **Data Filters** → find "Internal Traffic" filter → change state from **Testing** to **Active**.

Once active, internal traffic is permanently excluded from all reports AND **disappears from DebugView** -- disable temporarily for debug sessions or use a different device. For dynamic IPs (most home connections) the rule must be updated periodically.

## Attribution settings

GA4 → Admin → Data Display → Attribution Settings:

- **Model**: data-driven (default). Don't change manually -- with low traffic GA4 falls back to last-click.
- **Conversion lookback**: 30d for fast-cycle ecommerce, **90d for travel/hospitality**, B2B SaaS, anything with long decision cycles.
- **Engagement lookback**: 30d.

## Official docs

- All recommended events: https://support.google.com/analytics/answer/9267735
- gtag/dataLayer event reference: https://developers.google.com/tag-platform/gtagjs/reference/events
- Custom dimensions: https://support.google.com/analytics/answer/10075209
- Audiences: https://support.google.com/analytics/answer/9267572
- Audience triggers: https://support.google.com/analytics/answer/9744267
- Key Events (renamed from Conversions): https://support.google.com/analytics/answer/9267568
- Google Ads link: https://support.google.com/analytics/answer/9379420
- Enhanced Conversions: https://support.google.com/google-ads/answer/13258081
- Reporting Identity: https://support.google.com/analytics/answer/10978788
- Data filtering / internal traffic: https://support.google.com/analytics/answer/10108813
- Attribution models: https://support.google.com/analytics/answer/10597962

## Related

- `gtm-setup.md` -- the install this file builds on
- `framework-integration.md` -- per-framework GTM placement
- `gdpr-compliance-eu.md` -- why Google Signals is disabled in EEA setups (the EU differentiator)
- `diagnostics-troubleshooting.md` -- when the events don't show up
