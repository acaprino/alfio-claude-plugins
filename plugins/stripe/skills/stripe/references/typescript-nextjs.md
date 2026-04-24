# TypeScript and Next.js

Canonical TypeScript reference. Counterweight to the Python-heavy rest of this skill.

## Setup

```bash
pnpm add stripe @stripe/stripe-js @stripe/react-stripe-js
```

Pin the API version on the server client: `new Stripe(key, { apiVersion: '2026-04-22.dahlia', typescript: true })`.

Env var hygiene: `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` server-only; `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` is the *only* key prefixed with `NEXT_PUBLIC_`. Never prefix a secret this way -- it ships to the browser.

## Gotchas specific to Next.js

- **Webhooks must run on Node.** Set `export const runtime = 'nodejs'` and `export const dynamic = 'force-dynamic'` on `app/api/webhooks/stripe/route.ts`. Edge runtime breaks raw-body handling silently.
- **Read body with `req.text()`, not `req.json()`.** Re-serialization breaks signature verification.
- **Don't call Stripe from Client Components.** Importing `lib/stripe.ts` into a `'use client'` tree leaks the secret key into the browser bundle. Keep Stripe imports server-only (API routes, Server Actions, Server Components).
- **`redirect()` in Server Actions must be outside try/catch.** It throws `NEXT_REDIRECT`; catching it swallows the redirect.
- **Don't grant access on the success page.** The page runs with query params; anyone can forge `session_id`. Grant access from the `checkout.session.completed` webhook. Success page is read-only UI.
- **Middleware runs on Edge by default.** Don't put Stripe calls in `middleware.ts`. Auth checks only.
- **Static caching on the return page.** Wrap in `export const dynamic = 'force-dynamic'` or use Suspense streaming; otherwise `searchParams` can be stale.

## Type-narrowed event handling

`Stripe.Event` is a discriminated union. `switch (event.type)` narrows `event.data.object` per case -- no casts needed. If the compiler doesn't narrow, your SDK is behind the API version you're pinning; upgrade rather than cast.

## Preferred patterns

- **Server Actions** for triggering Checkout from forms.
- **Route Handlers** (`app/api/.../route.ts`) for webhooks.
- **Discriminated-union `switch`** for event routing.
- **Return-page reads `checkout.sessions.retrieve`** for confirmation UI, but webhook is the source of truth for access.

## Official docs

- Node SDK reference: https://docs.stripe.com/api?lang=node
- Next.js + Stripe quickstart: https://docs.stripe.com/payments/checkout/how-checkout-works (language switcher: Node)
- Sample Next.js app: https://github.com/stripe-samples/nextjs-typescript-react-stripe-js
- Webhooks in Node: https://docs.stripe.com/webhooks/quickstart

## Related

- `webhooks-production.md` -- runtime + signature + idempotency checklist
- `embedded-checkout.md` -- client-mountable Checkout in React
- `stripe.md` -- core patterns (overlap with this file is intentional)
