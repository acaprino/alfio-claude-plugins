# API Endpoint Security

Every API endpoint your application exposes is discoverable. Assuming obscurity provides protection is a recipe for catastrophe.

## MUST

- **Authenticate and authorize every API endpoint.** Enforce server-side access control on every route. Never expose admin endpoints without VPN/IP restrictions and strong authentication layered on top.

- **Implement rate limiting** on all endpoints, especially authentication, search, data export, and password reset. Without rate limiting, attackers can brute-force credentials, scrape data at scale, or denial-of-service your backend.

- **Configure CORS restrictively.** Whitelist only specific, known origins. Never use `Access-Control-Allow-Origin: *` with credentials. On SPA/PWA, all API calls are visible in the browser's Network tab -- CORS is your primary line of defense against cross-origin abuse.

## Case Studies

- **Peloton (2021):** API was entirely unauthenticated, exposing user IDs, locations, workout statistics, age, and gender for all 3+ million subscribers -- including users with private profiles. When Peloton added authentication, they initially failed to add authorization, so any authenticated user could still access any other user's data (OWASP API1: Broken Object Level Authorization).

- **Parler (January 2021):** Complete data scrape because its API lacked rate limiting and used sequential post IDs that made enumeration trivial. Also failed to strip EXIF metadata from uploaded photos, exposing GPS coordinates for millions of users.

## DO

- Minimize data in API responses -- return only what the client needs, not everything the database provides (OWASP API3: Excessive Data Exposure).
- Use API gateways for centralized auth, rate limiting, and monitoring.
- Validate request payloads against a schema (OpenAPI/JSON Schema).
- Version your APIs and deprecate insecure older versions.

## DON'T

- Return verbose error messages exposing stack traces, database schemas, or internal paths.
- Expose GraphQL introspection in production.
- Rely on obscurity -- "nobody will find this endpoint" is not a security strategy.
