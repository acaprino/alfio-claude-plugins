# Framework integration patterns

How to install GTM + the Consent Mode v2 default block correctly per framework. The framework-specific code samples (Next.js App vs Pages Router, React Router, etc.) live upstream; this file is the ordering rules and the gotchas that actually break installations.

## When to use

Installing GTM in a Next.js / React / WordPress / static-site / SSR-app codebase. For the snippet content itself and the `<head>` ordering rationale, see `gtm-setup.md`. For the EU compliance layer that must precede this, see `gdpr-compliance-eu.md`.

## The non-negotiable rule (every framework)

Order in `<head>`, top to bottom:

1. **Consent Mode v2 default block** (sets all signals to `denied`, `wait_for_update: 500`)
2. **CMP loader** (iubenda embed, Cookiebot autoblock script, Orestbida config)
3. **GTM head snippet**

The GTM noscript iframe goes immediately after `<body>`, never inside `<head>`.

## Per-framework cheat sheet

### Next.js App Router (13.4+)

Use `@next/third-parties/google`:

```bash
npm install @next/third-parties
```

```tsx
import { GoogleTagManager } from '@next/third-parties/google';
// In app/layout.tsx <html>...<GoogleTagManager gtmId="GTM-XXXXXXX" /></html>
```

For the Consent Mode v2 default block, paste an inline `<script dangerouslySetInnerHTML={{__html: ...}}>` in `<head>` BEFORE `<GoogleTagManager>`. There is no `beforeInteractive` strategy in App Router -- inline is the only way to guarantee execution before GTM loads.

For SPA route changes, GA4 page_view fires automatically when the GTM Google Tag uses `Initialization - All Pages`. For finer control, push `dataLayer` page_view events from a `usePathname()` + `useEffect()` client component.

Docs: https://nextjs.org/docs/app/building-your-application/optimizing/third-party-libraries

### Next.js Pages Router

Use `next/script` in `pages/_document.tsx` for the Consent Mode default with `strategy="beforeInteractive"` (this is the ONLY component where `beforeInteractive` works), and another `<Script strategy="afterInteractive">` for the GTM head snippet. The noscript iframe goes in the `<body>` JSX with `style={{display:'none', visibility:'hidden'}}`.

For SPA routing, listen to `Router.events.routeChangeComplete` in `pages/_app.tsx` and push `page_view` to dataLayer.

Docs: https://nextjs.org/docs/pages/api-reference/components/script

### React (CRA, Vite, non-Next)

Snippet directly in `public/index.html` (CRA) or `index.html` (Vite). Same head-order rules.

For React Router SPAs, use `useLocation()` in a `<PageViewTracker />` mounted once inside `<BrowserRouter>` and push `page_view` to `dataLayer` on location change.

### WordPress

Three paths:

- **Approach A (technical)**: `add_action('wp_head', ..., 1)` + `add_action('wp_body_open', ...)` in a child theme's `functions.php`. Priority `1` ensures early execution. `wp_body_open` was added in WP 5.2 -- older themes need a `header.php` edit.
- **Approach B (simple)**: edit `header.php` directly. Works but fragile -- theme updates can overwrite. Use a child theme.
- **Approach C (non-technical)**: Site Kit by Google (limited but guided), GTM4WP (most powerful, dataLayer for WooCommerce / CF7 / Gravity / scroll / video), or a CMP plugin (Complianz, iubenda WP) that handles the entire installation. **The CMP plugin and GTM plugin must be coordinated** so the CMP fires Consent Mode v2 updates that GTM listens for.

### SSR apps (Rails, Django, Laravel)

Insert in the base layout template (`application.html.erb`, `base.html`, `app.blade.php`). Same head-order rules. For Hotwire/Turbo/Inertia/Livewire SPAs, listen to the equivalent of `turbo:load` and push virtual `page_view` events.

### Static site generators

Most have a layout/partial system: Jekyll `_includes/head.html`, Hugo `layouts/partials/head.html` (also has built-in `{{ template "_internal/google_tag_manager.html" . }}`), Eleventy `_includes/layout.njk`, Astro `src/layouts/Layout.astro`, Gatsby `gatsby-plugin-google-tagmanager` in `gatsby-config.js`.

After every build, **verify with grep**:

```bash
grep -l "GTM-XXXXXXX" public/**/*.html
```

If a file is missing, the layout was not applied uniformly.

## Gotchas (the real production bites)

- **WordPress caching plugins strip the GTM snippet.** W3 Total Cache, WP Rocket, LiteSpeed, WP Super Cache -- especially with HTML minification or "delay JavaScript execution" turned on. Symptom: works in admin/preview but not in incognito on the live front-end. Fix: flush cache, add `googletagmanager.com` + `gtm.js` to the "do not minify" / "exclude from delay" list. **Always re-verify after enabling/updating any cache plugin.**
- **`strategy="beforeInteractive"` only works in `_document.tsx`** (Pages Router) -- not in pages or app components. In App Router, there's no equivalent; the Consent Mode default must be inline in `<head>`.
- **React Strict Mode double-fires `page_view` in development only.** Effects run twice in dev, prod is fine. Verify with DebugView in **production**, not local dev.
- **Hydration mismatch warnings (Next.js, React)** come from `dangerouslySetInnerHTML` differing between server and client. Use `next/script` or `@next/third-parties/google` -- never raw inline `<script>` for GTM in components.
- **Static export (`next export`)** works with GTM via the same `next/script` patterns. After export, grep the output to confirm the snippet is in every HTML file.
- **Multi-property / multi-container in one project** = data corruption guaranteed. One property and one container per environment; environments are separated via GTM Environments (auth params), not by mixing IDs.
- **Hugo / Astro / Gatsby integrations** can ship without Consent Mode v2 defaults out of the box -- always verify the head order is right after enabling the integration. The integration's "GTM container ID" field is just a convenience; the consent ordering is your responsibility.

## Server-side GTM (sGTM)

Out of scope. Separate Google Cloud deployment that proxies through a first-party domain. Worth it for high-traffic sites with privacy engineering requirements; overkill for most small-business deployments.

Docs: https://developers.google.com/tag-platform/tag-manager/server-side

## Official docs

- `@next/third-parties` (Google integrations): https://nextjs.org/docs/app/building-your-application/optimizing/third-party-libraries
- `next/script` strategies: https://nextjs.org/docs/app/api-reference/components/script
- React Router (`useLocation`): https://reactrouter.com/en/main/hooks/use-location
- WordPress action hooks (`wp_head`, `wp_body_open`): https://developer.wordpress.org/reference/hooks/wp_head/
- GTM4WP plugin: https://gtm4wp.com/
- Site Kit by Google: https://wordpress.org/plugins/google-site-kit/
- Hugo internal GTM template: https://gohugo.io/templates/internal/#google-tag-manager
- Astro Google Analytics integration: https://github.com/codiume/orbit/tree/main/packages/astro-google-analytics
- Gatsby GTM plugin: https://www.gatsbyjs.com/plugins/gatsby-plugin-google-tagmanager/

## Related

- `gtm-setup.md` -- the snippet content + `<head>` ordering rationale
- `events-and-conversions.md` -- the events these snippets enable measuring
- `gdpr-compliance-eu.md` -- EU compliance layer that comes before any of this
- `diagnostics-troubleshooting.md` -- when the install seems wrong, run this checklist
