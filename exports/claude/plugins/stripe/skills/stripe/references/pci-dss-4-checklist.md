# PCI DSS 4.0 / 4.0.1 for Stripe Merchants

Short version of what changed with PCI DSS 4.0 and what a Stripe merchant on SAQ-A actually has to do. Canonical guidance lives at the PCI SSC and Stripe; this file captures the bits that affect the code you write.

## Scope note: SAQ-A merchants (the common case)

If you use hosted Checkout or Payment Links and **no PAN data ever touches your servers**, you're almost certainly SAQ-A. PCI SSC published a revised SAQ-A in January 2025 that removed Requirements 6.4.3 and 11.6.1 for fully-outsourced merchants and replaced them with an eligibility criterion stating the merchant is still responsible for hardening the *referring page* against script attacks.

If you use Stripe Elements, Payment Element, or Embedded Checkout (anything where Stripe JS runs inside your page), you're likely **SAQ-A-EP** -- the full 6.4.3 and 11.6.1 requirements apply.

Confirm your SAQ type with your acquirer / auditor. Don't self-classify.

## Gotchas

- **6.4.3 (script integrity)** -- every third-party script on a payment page must be authorized, justified, and integrity-checked. Practically: inventory your scripts, add Subresource Integrity (SRI) hashes on `<script>` tags, add a Content Security Policy (CSP) with a strict `script-src`.
- **11.6.1 (change detection on payment pages)** -- detect unauthorized modifications to HTTP headers and script content on payment pages. Practically: a tamper-detection tool (Feroot, Jscrambler, Akamai Page Integrity Manager, Human Security) or a homegrown CSP-report + script-hash pipeline.
- **Deadline context.** PCI DSS 4.0 was effective March 31 2024. The originally "future-dated" requirements (including 6.4.3 and 11.6.1) became mandatory March 31 2025. PCI DSS 4.0.1 is the current point release.
- **12.3.1 (TLS inventory)** -- keep a documented inventory of certificates and cipher suites. Cheap win: use a Qualys SSL Labs scan in your quarterly review cadence.
- **Stripe-hosted means Stripe's problem for those pages, not yours** -- but the page *linking to* Stripe Checkout is still yours. A malicious script on that page can rewrite the link to a phishing target. 6.4.3 and 11.6.1 (or the SAQ-A replacement criterion) apply to that referring page.
- **Dynamic script insertion** -- CSP without `unsafe-inline` breaks a lot of analytics/tag managers. Plan for nonce-based or hash-based CSP early; retrofitting is painful.
- **Don't rely on `defer`/`async` for security** -- they affect load order, not authorization or integrity.
- **SRI breaks on minor vendor bumps.** When a third-party script updates its file (common with analytics), the hash changes. Pin versions or automate hash refresh in CI.

## Concrete checklist

- [ ] Confirm SAQ type (A vs A-EP) with your acquirer.
- [ ] Inventory every `<script>` and external resource on any page that links to or embeds payment UI. Written justification per script.
- [ ] Add SRI hashes to all third-party scripts on those pages.
- [ ] Deploy a strict CSP with `script-src`, `frame-src https://js.stripe.com https://checkout.stripe.com`, `connect-src https://api.stripe.com`, and a CSP report endpoint.
- [ ] Set up change detection (tooling or homegrown with daily script-hash diff).
- [ ] Document TLS versions and cipher suites per public endpoint (Qualys SSL Labs once per quarter).
- [ ] Include the payment page hardening status in your annual SAQ submission.

## Official docs

- PCI DSS 4.0.1 document (registration required): https://www.pcisecuritystandards.org/document_library/
- PCI SSC SAQ A revision (Jan 2025) blog: https://blog.pcisecuritystandards.org/ (search for "SAQ A")
- Stripe PCI compliance guide: https://stripe.com/guides/pci-compliance
- Stripe Elements + PCI docs: https://docs.stripe.com/security/guide
- Stripe CSP guidance (frame/connect sources): https://docs.stripe.com/security/guide (see "content security policy" section)

## Related

- `webhooks-production.md` -- unrelated to PCI, but shares the "what does production-grade actually look like" framing
- `embedded-checkout.md` -- which integration mode puts you in SAQ-A vs SAQ-A-EP
