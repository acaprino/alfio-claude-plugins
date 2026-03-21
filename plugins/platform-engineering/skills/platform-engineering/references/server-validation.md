# Server-Side Validation

The single most important security rule across every platform: **the client is untrusted territory**. Frontend validation exists only to improve UX. Every check -- data type, length, range, format, business logic, authorization -- must be enforced server-side. Attackers bypass client-side validation trivially using browser DevTools, intercepting proxies like Burp Suite, or direct API calls via curl.

## MUST

- **Validate all inputs server-side.** This includes prices, quantities, discount codes, user roles, and any value the client submits.
  - DeepStrike (2023): researchers found a payment system that stored invoice data in a JavaScript variable with frontend-only validation. By intercepting and modifying the price in transit, they submitted fraudulent payments -- the server accepted them without question.
  - In another case, researchers bypassed OTP verification by intercepting the API response and flipping "401 Unauthorized" to "200 OK" because the backend never re-verified the code server-side.

## DO

- Implement frontend validation for instant UX feedback (format hints, required-field indicators, character counters), but always duplicate every check on the backend.
- Validate at every trust boundary: client to API, service to service, and before database writes.

## DON'T

- Trust hidden HTML fields, disabled form elements, JavaScript variables, or client-computed values (totals, discounts, eligibility).
- Assume your API's only consumer is your own frontend -- any HTTP client can call your endpoints.

## Platform Context

| Platform | Bypass difficulty |
|----------|------------------|
| **SPA/PWA** | Code fully visible in browser DevTools -- bypass is trivial |
| **Native mobile** | Binaries decompiled with Frida, jadx, MobSF |
| **Electron** | Readable JavaScript in ASAR archives, extractable with a single command |
| **Tauri** | Compiled Rust backend does not protect against manipulated API requests over the network |
