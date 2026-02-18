# SEO Audit

Use the `seo-specialist` agent to perform a comprehensive technical SEO audit for:

$ARGUMENTS

## Workflow

Execute this audit as a structured, multi-phase process. Use Playwright browser tools for live page analysis (DOM inspection, console errors, network requests, responsive testing, screenshots). Fall back to WebFetch/curl for simpler checks. Use WebSearch for competitive benchmarking and best-practice validation.

### Phase 1: Discovery

Gather baseline information before auditing.

1. **Fetch target** — navigate to the URL with Playwright, capture initial snapshot
2. **Robots.txt** — fetch `/robots.txt`, check rules, disallow patterns, crawl-delay
3. **Sitemap** — fetch `/sitemap.xml` (and sitemap index), count URLs, check lastmod dates
4. **Tech detection** — identify CMS/framework from response headers, meta generators, DOM patterns (WordPress, Next.js, Shopify, etc.)
5. **Site structure** — map primary navigation, count pages in sitemap, identify page types (home, product, blog, category, landing)

Present discovery summary and confirm scope before proceeding.

### Phase 2: Technical Audit

Run every check below. Use Playwright `browser_snapshot` to extract DOM, `browser_evaluate` for JS-based checks, `browser_network_requests` for resource analysis, `browser_console_messages` for errors, `browser_resize` for responsive testing.

**Core SEO**
- Meta title: present, unique, 50-60 chars, keyword in first half
- Meta description: present, 120-160 chars, includes CTA or value prop
- Canonical URL: present, self-referencing or correct target
- Open Graph: og:title, og:description, og:image (1200x630), og:type, og:url, og:site_name
- Twitter Cards: twitter:card, twitter:title, twitter:description, twitter:image (1200x675)

**Headings**
- Exactly 1 H1 per page
- Heading hierarchy: no skips (H1→H2→H3, not H1→H3)
- Primary keyword in H1
- Subheadings descriptive, not generic

**Links**
- Internal link structure: important pages reachable within 3 clicks
- Broken links: check status codes with curl/fetch (sample top 20)
- Redirect chains: detect 301→301→200 chains (max 1 redirect)
- Orphan pages: pages in sitemap but not linked from navigation
- External links: nofollow where appropriate, open in new tab

**Images**
- Alt text: present and descriptive (not "image1.jpg")
- Filename: descriptive, hyphenated (not DSC_0001.jpg)
- Lazy loading: loading="lazy" on below-fold images
- Format: WebP/AVIF preferred over JPEG/PNG
- Dimensions: width/height attributes to prevent layout shift

**Performance**
- Page load: total transfer size, number of requests (via network_requests)
- Core Web Vitals hints: large DOM size, render-blocking resources, unoptimized images
- Caching: Cache-Control headers on static assets
- Compression: gzip/brotli on HTML/CSS/JS
- Resource sizes: flag files > 500KB

**Security**
- HTTPS: enforced, no mixed content (check console warnings)
- Security headers: Content-Security-Policy, Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- Mixed content: HTTP resources on HTTPS pages

**Structured Data**
- JSON-LD present: extract and validate type (Organization, Product, Article, BreadcrumbList, FAQ, etc.)
- Required properties: check against schema.org requirements for detected type
- Rich Results eligibility: does the markup qualify for search features?

**Mobile**
- Viewport meta tag: present, width=device-width
- Responsive: test at 375px (mobile), 768px (tablet), 1280px (desktop) using browser_resize
- Touch targets: buttons/links at least 44x44px
- Font size: base >= 16px, readable without zoom
- No horizontal scroll at mobile widths

**Crawlability**
- robots.txt: not blocking important pages
- Sitemap: valid XML, all URLs return 200, lastmod accurate
- noindex/nofollow: only on intended pages
- Pagination: rel="next"/rel="prev" or proper handling
- JavaScript rendering: critical content in initial HTML (not JS-only)

**Content Quality**
- Word count: flag thin content (< 300 words on important pages)
- Duplicate titles/descriptions across pages
- Keyword stuffing: unnatural density (> 3%)
- Content freshness: lastmod dates, copyright year

**URL Structure**
- Clean slugs: lowercase, hyphens, no special characters
- Length: under 75 characters
- Keywords in URL path
- Consistent structure (no mixing /page and /page.html)

**Accessibility**
- ARIA landmarks: main, nav, banner, contentinfo
- Alt text on all images (overlaps with Images section)
- Color contrast: check key text against background
- Skip navigation link
- Form labels associated with inputs
- Focus indicators visible

**E-E-A-T Signals**
- Author information: bylines, author pages
- About page: exists, substantive
- Contact page: exists, real contact info
- Trust signals: privacy policy, terms of service, secure checkout badges
- Citations and sources in content

**Local SEO** (if applicable)
- NAP consistency: name, address, phone match across pages
- LocalBusiness schema markup
- Google Business Profile link
- Geo meta tags

**Internationalization** (if applicable)
- hreflang tags: present, valid language codes, reciprocal
- lang attribute on html element
- Content translation quality

### Phase 3: Score & Prioritize

Calculate and present results.

1. **Health score**: 0-100 with letter grade (A: 90+, B: 80+, C: 70+, D: 60+, F: <60)
2. **Category breakdown**: score each section (Core SEO, Headings, Links, Images, Performance, Security, Schema, Mobile, Crawlability, Content, URLs, Accessibility, E-E-A-T)
3. **Issue severity**: classify each finding as:
   - **Error** (red): broken functionality, missing critical elements, security issues
   - **Warning** (yellow): suboptimal but functional, missed opportunities
   - **Notice** (blue): nice-to-have improvements, best practices
4. **Prioritized fix list**: rank by impact × effort, group into quick wins / medium effort / major projects

Present the scorecard and fix list. **Wait for user approval** before proceeding to fixes.

### Phase 4: Fix & Iterate

Apply approved fixes only.

1. **Batch fixes**: group related changes, apply in logical order
2. **Re-audit**: re-check changed pages/elements after fixes
3. **Before/after**: show what changed and the impact on scores
4. **Loop**: repeat until target score reached or only human-judgment items remain (e.g., content rewriting, design changes)

### Phase 5: Report

Generate final audit report.

1. **Summary table**: category scores before and after, overall grade improvement
2. **Issues fixed**: what was changed, where, and why
3. **Remaining items**: issues requiring manual intervention (content rewrites, design decisions, server config)
4. **Monitoring**: recommendations for ongoing SEO health (tools, frequency, key metrics to track)
5. **Next steps**: prioritized roadmap for continued improvement

## Quick Examples

- `/seo-audit https://example.com` — Full technical SEO audit of a live website
- `/seo-audit https://example.com/products` — Audit a specific section
- `/seo-audit src/pages --local` — Audit local HTML/template files for SEO best practices
- `/seo-audit https://example.com --focus security,performance` — Focused audit on specific categories
- `/seo-audit https://example.com --competitor https://rival.com` — Comparative audit against a competitor
