# GDPR compliance for GA4 in the EU

> Source: Italian Garante della Privacy provvedimenti 9677876 (June 2021, in force since 10 January 2022) and 9782874 (June 2022), the EU-US Data Privacy Framework adequacy decision (10 July 2023), Tribunale Generale UE Case T-553/23 (3 September 2025), and the Google Consent Mode v2 specification as of 2025-2026. Always verify against current Garante and Google publications for production deployments.

GA4 is currently legal in Italy and the EU, but only when deployed with a working CMP, Consent Mode v2, and the right account-level configurations. A written cookie policy is **not** sufficient. This reference covers what the law and Google policy require, how the legal status got here, and which CMP to choose.

## Current legal status

In June 2022 the Italian Garante della Privacy ruled (Provvedimento 9782874, Caffeina Media S.r.l. case) that Google Analytics was not GDPR-compliant because of personal data transfers to the United States without adequate safeguards post-Schrems II. That ruling concerned Universal Analytics in the pre-DPF context.

The picture changed on **10 July 2023** when the European Commission adopted the adequacy decision for the EU-US Data Privacy Framework (DPF). Google LLC self-certified under the DPF in August 2023, providing a legal basis for data transfers to the US. On **3 September 2025** the Tribunale Generale UE (General Court of the EU) dismissed the challenge to the DPF in Case T-553/23, confirming its validity. An appeal to the Court of Justice of the European Union was filed on 31 October 2025 (potential "Schrems III"), with a decision expected late 2026 to early 2027.

**Practical conclusion**: GA4 is currently legal in Italy. The DPF resolves the data-transfer problem only - it does not eliminate the need for explicit user consent, the cookie banner with preventive blocking, or the technical configurations described below. The Garante has not issued a new GA4-specific decision after DPF adoption, but the 2022 precedent will reactivate immediately if the DPF is invalidated. Have a contingency plan (Matomo or another EU-hosted analytics) ready for that scenario.

## Cookie banner: technical, not just textual

The Garante's Cookie Guidelines (Provvedimento 9677876, June 2021, in force since 10 January 2022) set the binding framework. The site must have a technical mechanism (a CMP) that **blocks all non-technical cookies before the user gives explicit consent**. A written policy describes which cookies the site uses but does not block them. Without preventive blocking, the site violates Art. 122 of the Italian Privacy Code and Art. 25 GDPR (privacy by default).

GA4 sets analytics cookies (`_ga`, `_ga_*`) that the Garante classifies as **non-technical** because Google can cross-reference the data with its advertising ecosystem. The "technical analytics" exemption requires four cumulative conditions (IP masking, single-site analytics only, no third-party data sharing, aggregated output only) which GA4 does not satisfy.

### Mandatory banner requirements

- **X close button** in the top right (closes the banner without setting non-essential cookies)
- **"Accept all" and "Reject all" buttons** with **identical visual weight** - same color, same size, same font, no dark patterns
- **Link to the full cookie policy**
- **Link to a granular preferences area** where the user can toggle categories and individual services
- **Scroll-as-consent is invalid** as a standalone basis
- **6-month resuppression**: after a rejection, the banner cannot reappear for 6 months

The Garante explicitly excludes "legitimate interest" as a basis for analytics cookies. Consent is the only valid legal basis for third-party analytics cookies like GA4.

## GA4 account-level configuration

| Setting | Status | Where to configure |
|---|---|---|
| **IP anonymization** | Automatic in GA4 | Built-in, not disableable. GA4 truncates the last IPv4 octet before storage. The Garante has clarified this alone does not make data anonymous. |
| **Data Processing Terms** | **Mandatory** (Art. 28 GDPR) | Admin > Account Settings > Account Details > view and accept. Auto-applied for EEA accounts but verify. |
| **Data retention** | **2 months** for max compliance | Admin > Data Collection and Modification > Data Retention. Default is 2 months. 14 months is justifiable only with documented business need (year-on-year analysis for seasonal businesses). Standard aggregated reports are unaffected. |
| **Google Signals** | **Disable for EEA** | Admin > Data Settings > Data Collection. Enables cross-device tracking and demographics that conflict with GDPR data minimization. Disabling also reduces data thresholding for low-traffic sites. |
| **Granular location/device data** | Evaluate disabling for EEA | Admin > Data Collection > regional section |
| **Consent Mode v2** | **Mandatory** (Google policy) | Required since 6 March 2024 for any property serving EEA traffic. Without it, Google disables remarketing and audience building. |
| **Reset on new activity** | Enable | Admin > Data Collection > Data Retention. Resets the user-level retention timer when the user returns. |

## Google Consent Mode v2

Consent Mode v2 is a JavaScript API that communicates user consent choices to Google tags. It is **not** an EU legal requirement on its own - it is a **Google policy** mandatory since March 2024 for anyone using GA4 / Google Ads with EEA users. Without it, ad-related features are disabled.

It manages **four consent signals**, all of which must default to `denied` for Italian and EEA visitors:

| Signal | Function | New in v2? |
|---|---|---|
| `analytics_storage` | Controls analytics cookies (GA4) | Existed in v1 |
| `ad_storage` | Controls advertising cookies | Existed in v1 |
| `ad_user_data` | Controls sending user data to Google for advertising | **New in v2** |
| `ad_personalization` | Controls personalized advertising (remarketing) | **New in v2** |

### Basic vs Advanced mode

There are two operating modes:

- **Basic mode**: tags do not load until the user accepts. This is the safest from a GDPR standpoint and the **recommended choice for EU sites**.
- **Advanced mode**: tags load with `denied` state and send cookieless pings to Google for behavioral modeling. Google prefers this for data quality. Several privacy experts (DataGuard among others) consider it potentially non-compliant under GDPR because it processes data without consent.

**For an Italian or EU site, use Basic mode.**

### Default consent block

The default block must run **before** any Google tag, including before the GTM snippet. It sets all signals to `denied` and includes `wait_for_update` so the CMP has time to update consent before tags would otherwise fire.

```html
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
```

When the user accepts via the CMP, the CMP must call `gtag('consent', 'update', { ... })` with the accepted signals set to `granted`. Most certified CMPs do this automatically.

## CMP selection

Several CMPs work for a static HTML site or any framework. The choice depends on technical comfort level, traffic volume, and budget.

### Recommended: iubenda

**Iubenda** is an Italian company specialized in privacy compliance. It is a Google-certified CMP partner with native Italian support and Italian legal documentation. Pricing: free plan up to 25,000 pageviews/month or Essentials at €4.99/month.

**Why iubenda for non-technical users**:
- **Autoblocking** detects and blocks third-party scripts (including GA4) before consent automatically, no manual configuration required
- **Consent Mode v2** auto-enabled on all plans including the free one
- Generates GDPR-compliant Privacy Policy and Cookie Policy in Italian
- Italian-language support and documentation
- Installation is a single embed snippet pasted into `<head>`

**Installation steps**:
1. Create a free account at iubenda.com
2. Configure a new project for the site
3. Set up the Cookie Solution (banner style, language)
4. Copy the generated embed code and paste it at the top of `<head>` on every page
5. Consent Mode v2 activates automatically with no extra code

The free plan covers up to 25,000 pageviews/month, which is sufficient for most small business sites including vacation rentals, local shops, professional service sites, and portfolios.

### Free open-source alternative: Orestbida CookieConsent v3

**Orestbida CookieConsent** ([github.com/orestbida/cookieconsent](https://github.com/orestbida/cookieconsent)) is an open-source CMP under MIT license, ~5,400 stars on GitHub. It is completely free with no pageview limits, no branding, lightweight, and well documented.

**Trade-offs**:
- Requires writing a JavaScript configuration file
- No web admin panel - all configuration is in code
- Not Google-certified - works for GA4 and Google Ads standard tags but not for AdSense / Ad Manager
- No autoblocking - requires manual `type="text/plain"` and `data-category` attributes on every script tag that should be blocked
- Consent Mode v2 integration via documented `onFirstConsent`, `onConsent`, and `onChange` callbacks

It is the right choice when the site owner has at least minimal JavaScript comfort or a technical collaborator.

**Minimal configuration example**:

```javascript
import 'vanilla-cookieconsent/dist/cookieconsent.css';
import * as CookieConsent from 'vanilla-cookieconsent';

CookieConsent.run({
  guiOptions: {
    consentModal: {
      layout: 'box',
      position: 'bottom right',
      equalWeightButtons: true
    }
  },
  categories: {
    necessary: { enabled: true, readOnly: true },
    analytics: {},
    marketing: {}
  },
  language: {
    default: 'it',
    translations: {
      it: {
        consentModal: {
          title: 'Usiamo i cookie',
          description: 'Accetta tutti i cookie o personalizza le preferenze.',
          acceptAllBtn: 'Accetta tutto',
          acceptNecessaryBtn: 'Rifiuta tutto',
          showPreferencesBtn: 'Personalizza'
        }
      }
    }
  },
  onFirstConsent: ({ cookie }) => updateConsentMode(cookie),
  onConsent: ({ cookie }) => updateConsentMode(cookie),
  onChange: ({ cookie }) => updateConsentMode(cookie)
});

function updateConsentMode(cookie) {
  const analytics = cookie.categories.includes('analytics') ? 'granted' : 'denied';
  const marketing = cookie.categories.includes('marketing') ? 'granted' : 'denied';
  gtag('consent', 'update', {
    analytics_storage: analytics,
    ad_storage: marketing,
    ad_user_data: marketing,
    ad_personalization: marketing
  });
}
```

Then mark each blockable script tag like:

```html
<script type="text/plain" data-category="analytics" src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXXXXX"></script>
```

CookieConsent rewrites the `type` attribute to `text/javascript` after consent is granted.

### CMPs ruled out and why

- **Klaro**: no native Consent Mode v2 support. Deal-breaker for Google policy compliance.
- **Cookiebot**: free plan limited to 50 subpages. Pricing roughly doubled in 2025 (~€30/month for paid plans).
- **CookieYes**: free plan limited to 5,000 pageviews/month with branding.
- **Osano**: enterprise pricing starts around $199/month.
- **Complianz**: WordPress only.
- **OneTrust / TrustArc**: enterprise-only, not suitable for small business sites.

## Recommended baseline configuration

For a small business site in Italy or the EU, the safest baseline is:

1. **iubenda** (free or Essentials plan) for the CMP
2. **GTM** for tag deployment (not gtag.js direct)
3. **Consent Mode v2 in Basic mode** with all four signals defaulting to `denied`
4. **GA4 account-level**: Data Processing Terms accepted, data retention set to 14 months only with documented justification (otherwise 2 months), Google Signals **disabled**, Reset on new activity **enabled**
5. **Privacy and Cookie Policy** generated by iubenda or written specifically for the site, with all third parties listed
6. A **plan B**: keep an eye on the Schrems III appeal at the Court of Justice. If the DPF is invalidated, be prepared to switch to Matomo or another EU-hosted analytics.

## Microsoft Clarity, Hotjar, and other companion tools

If the site also runs Microsoft Clarity, Hotjar, Mouseflow, or any session-recording tool, these set non-essential cookies (Clarity sets `_clck`, `_clsk`, `CLID`, `MUID`) and require the same consent treatment as GA4. From 31 October 2025 Microsoft applies consent signal requirements for EEA users on Clarity. Place these tools in the same "Analytics" or "Marketing" category in the CMP and ensure they are blocked until consent.

## Verification checklist

Before going live, confirm all of the following:

- [ ] CMP loads on every page
- [ ] Banner shows Accept and Reject buttons of equal visual weight
- [ ] X close button works without setting non-essential cookies
- [ ] Granular preferences link works
- [ ] Cookie policy link points to the full policy
- [ ] Consent Mode v2 default block runs **before** GTM (check via `view-source:` and the network tab)
- [ ] All four signals default to `denied` (verify in DevTools Console: `dataLayer`)
- [ ] After clicking Reject, no `_ga` or `_ga_*` cookies are set (check Application > Cookies in DevTools)
- [ ] After clicking Accept, the CMP fires `gtag('consent', 'update', ...)` and GA4 cookies appear
- [ ] After Reject, the banner does not reappear for 6 months (test by reloading multiple times)
- [ ] Privacy Policy and Cookie Policy are linked from the footer
- [ ] GA4 Data Processing Terms accepted in Admin > Account Settings
- [ ] Google Signals disabled in Admin > Data Settings > Data Collection
