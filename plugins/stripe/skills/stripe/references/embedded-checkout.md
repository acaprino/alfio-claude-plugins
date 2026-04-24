# Embedded Checkout

Stripe Checkout that mounts inside your React tree instead of redirecting. The middle option between hosted redirect and fully custom Payment Element.

## Decision matrix

| Mode | When |
|------|------|
| **Hosted redirect** | Fastest ship; no UI work. User leaves your domain. |
| **Embedded** (`ui_mode: 'embedded'`) | SPA feel, stays on your domain, Stripe controls payment form visuals. |
| **Custom Payment Element** | Full layout control, multi-step checkout, you handle SCA and error states. |

Default to hosted redirect for v0. Migrate to embedded when a full redirect breaks your UX. Go custom only when embedded's layout constraints are actually blocking.

Two embedded sub-modes: `ui_mode: 'embedded'` for inline mount within an existing page, `ui_mode: 'embedded_page'` for dedicated full-page embeds (SPA route that would otherwise be a redirect target).

## Gotchas

- **Return `client_secret` to the client, not `session.id`.** Anyone with the session ID can retrieve metadata. Only `client_secret` is safe in the browser.
- **`session.url` is null in embedded mode.** The `url` field works only for hosted redirect.
- **`fetchClientSecret` runs at mount time.** Don't pre-fetch -- the secret ages on the client. Fetch-on-mount.
- **`return_url` and `onComplete` are mutually exclusive.** Pick one: `return_url` redirects after success; `onComplete` fires a JS callback for modal/drawer flows.
- **Apple Pay / Google Pay need domain verification** when your domain is in the flow (embedded does this; hosted doesn't). Call `stripe.paymentMethodDomains.create` + `.validate` once per production domain. Test on a real device -- desktop Chrome hides the issue.
- **Grant access from the webhook, not the return page.** Return page is read-only UI; query params can be forged.
- **`payment_method_configuration` over hardcoded `payment_method_types`.** Lets you manage the PM list from Dashboard without redeploying.
- **Adaptive Pricing** (local-currency presentment) is a Dashboard toggle. Watch for refund/proration rounding deltas in non-default currencies.

## Official docs

- Quickstart with full code (server + React mount): https://docs.stripe.com/checkout/embedded/quickstart
- Embedded vs hosted vs custom: https://docs.stripe.com/payments/checkout/how-checkout-works
- React component reference: https://docs.stripe.com/checkout/embedded/react
- Apple Pay / Google Pay domain setup: https://docs.stripe.com/payments/payment-methods/pmd-registration
- Adaptive Pricing: https://docs.stripe.com/payments/checkout/adaptive-pricing
- `payment_method_configuration`: https://docs.stripe.com/payments/payment-method-configurations

## Related

- `typescript-nextjs.md` -- broader App Router patterns
- `webhooks-production.md` -- `checkout.session.completed` handling
- `checkout-optimization.md` -- conversion patterns (fields, trust signals)
