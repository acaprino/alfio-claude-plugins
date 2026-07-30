# Essential Duplication Patterns

Twelve canonical cases where centralizing duplicated logic into a unified layer is the right move. Each pattern is *essential duplication*: the duplicated sites share a single concern that must change together. Leaving them duplicated guarantees drift, security gaps, or data-correctness bugs.

For each pattern: structural signature (what the duplicated code looks like), why unification is right (which forces want it to change together), the suggested target layer, common pitfalls when implementing the unification.

The Rule of Three (see `theory.md`) still applies: do not promote a pattern with fewer than three call sites. Two may diverge; three signals a real shape.

---

## P1. External-service / SDK wrapper

**Structural signature:** Multiple call sites instantiate the same vendor SDK (OpenAI, Anthropic, Gemini, Stripe, Twilio, SendGrid, AWS S3) and pass the same configuration: API key from environment, model or service identifier as a raw string, temperature or precision flag, max tokens or retry count, timeout. Each call site repeats the auth header construction, error-to-domain mapping, and logging of cost or quota usage. A search for the SDK constructor returns ten, twenty, fifty hits across the codebase.

**Forces that want this to change together:** Authentication (rotating the API key, switching to per-tenant keys, adding a secret manager). Retry policy (the vendor adds a new transient error code; the team standardizes on jittered exponential backoff). Cost tracking (finance needs per-call token or unit cost emitted to a metrics pipeline). Vendor switching (a cheaper or more compliant provider appears and the team wants to A/B test it without rewriting every feature). Observability (every call needs a trace span with vendor-name and operation-name attributes).

**Suggested target layer:** A vendor-agnostic service object, for example `LLMService`, `PaymentGateway`, `EmailDispatcher`, `ObjectStorage`. The service exposes named domain operations parameterized by a preset (`Preset.LEGAL_SUMMARIZATION`, `Preset.TRANSACTIONAL_EMAIL`) instead of raw vendor parameters. Features call the service with intent; the service owns model selection, temperature, retry, cost emission, and translation of vendor errors into a stable domain-error type.

**Common pitfalls:**
- Swallowing the prompt or payload into the service. Prompts and payloads belong to features because they carry product intent; the service owns the *envelope* (auth, retry, cost), not the *contents*.
- Letting the service become a god service of named domain operations (`LLMService.summarize_contract`, `LLMService.classify_invoice`, `LLMService.translate_chat`). The service exposes generic primitives plus presets; domain methods belong on domain services.
- Hard-coding the vendor name in the service interface. A `OpenAIService` that pretends to be vendor-agnostic blocks future provider switching.
- Leaking vendor-specific exception types through the public surface (see also P11 retry policy and the leaky-abstraction anti-pattern).

**Retrospective indicator that you did this right:** Rotating the API key takes one PR, not 47. Adding a new vendor (or A/B testing two vendors) is a config change behind a single feature flag, not a multi-week refactor. The day finance asks for per-tenant cost attribution, the dashboard query runs against one well-defined emission point.

---

## P2. Schema validation at boundaries

**Structural signature:** The same payload shape enters the system from multiple sources: an HTTP API endpoint, a message-queue consumer, a CSV or JSON file ingestion job, an inbound webhook from a third party. Each entry point re-parses the payload, often with slight variations: one endpoint coerces strings to integers silently, another rejects them; one webhook tolerates missing optional fields, another raises. Several entry points share copy-pasted Pydantic, Zod, or Joi declarations that have already drifted in field names or required-versus-optional status.

**Forces that want this to change together:** Field-shape changes (a new optional field, a renamed key, a tightened format constraint). Validation strictness (the team decides numeric strings should fail fast rather than coerce, or vice versa). Error-message consistency (the API needs a stable machine-readable error code for each validation failure, and the queue consumer needs the same code so retries are correctly routed). Security (input sanitization rules, length caps, regex constraints to block injection or DoS payloads).

**Suggested target layer:** A schema module per bounded context that owns the canonical model definitions, imported by every entry point. For Pydantic: a `schemas/` package with one module per aggregate. For Zod: a shared schemas package consumed by every route handler, queue worker, and ingestion job. Validation runs at the *boundary* of the system; internal layers receive parsed, typed objects and assume their invariants hold.

**Common pitfalls:**
- Validators that silently coerce instead of failing fast. A schema that accepts both `"42"` and `42` for an integer field looks tolerant but hides upstream bugs and produces inconsistent reads downstream.
- Sharing the same schema across bounded contexts that should have separate models (P2 is unification *inside* a context; cross-context fusion is a wrong abstraction).
- Re-parsing already-validated objects deep inside the application as a defensive habit. The boundary should be the only validation point; internal mistrust is a code smell.
- Embedding business rules into the schema (e.g. "amount must be a multiple of 5"). Schemas validate *shape*; domain services validate *rules*.

**Retrospective indicator that you did this right:** Adding a new field to a payload requires editing one schema file and one entry-point handler, not searching the codebase for every place the field is read. Rejected inputs return a uniform error envelope regardless of whether the payload arrived via HTTP, queue, or webhook.

---

## P3. Authorization / permission checks

**Structural signature:** Endpoints and command handlers begin with an inline check: `if not user.has_permission("orders.read"): raise Forbidden`. Some endpoints check by role string, others by permission constant, others by querying the database directly. Several routes that should be guarded have no check at all; a recent feature added a new endpoint and the author forgot the guard because the pattern was not enforced anywhere.

**Forces that want this to change together:** New permission grammar (the team migrates from string roles to scoped permissions like `tenant:42:orders:read`). Audit logging (every denied access needs a structured log line with user, resource, action, decision, reason). Multi-tenant scoping (a single tenant boundary check that applies to every request). Policy changes (a customer demands a "read-only Saturday" mode and the rule must fire across the system).

**Suggested target layer:** A single authorization gate, often a decorator, middleware, or policy object: `@requires_permission("orders.read")` on every handler, plus an `AuthGate.can(user, action, resource)` predicate for use inside services. The gate emits audit logs uniformly. The codebase has *no other path* to authorize an action.

**Common pitfalls:**
- Making the gate optional via a "convenience" call path. The moment one internal helper bypasses the gate "for performance" or "for the migration script", duplicated checks reappear and the next forgotten guard is a security hole.
- Mixing authorization with authentication. The gate decides *can this user do X*; authentication decides *who is this user*. They share infrastructure but the abstractions are independent.
- Putting business-rule conditions inside the gate (e.g. "users can edit their own orders only on weekdays before 5pm"). The gate decides on a permission grammar; complex business rules belong in the domain service and call the gate as one of their inputs.

**Retrospective indicator that you did this right:** A security review can answer "which actions require authorization, by what rule, with what audit trail" by reading one file, not by grep-walking every endpoint. Adding a new permission is a config change plus one decorator per affected handler. The day a regulator asks for the audit log of denied accesses, the query runs against one structured stream.

---

## P4. Money arithmetic

**Structural signature:** Prices, fees, totals, taxes, and discounts are computed in multiple modules. Some use floating-point arithmetic, some use `Decimal`, some pass currency around as a free-form string. Rounding rules differ: one module rounds half-up, another truncates, a third rounds half-even. Currency conversion happens in two places with slightly different exchange-rate fetch logic. A quiet bug appears at the boundary: the invoice total differs from the sum of line items by a cent.

**Forces that want this to change together:** Precision (every monetary value must use the same decimal representation, never float). Rounding mode (the team standardizes on banker's rounding for compliance, or half-up for retail). Currency representation (a typed `Money(amount, currency)` value object replacing scattered tuples). FX conversion (one place that fetches rates, caches them, and applies them with a consistent reference date). Tax rules (a single tax-calculation service that knows about jurisdictions, rates, and rounding per jurisdiction).

**Suggested target layer:** A `Money` value object and a `MoneyArithmetic` module that owns precision, rounding, currency conversion, and tax application. Every monetary computation in the system runs through it. Database columns store amount in the smallest currency unit (cents, pence) with a typed currency code; the value object handles the conversion at the boundary.

**Common pitfalls:**
- Passing currency as a string rather than a typed value. `"USD"` and `"usd"` are different strings, and a typo produces a silent fiscal bug.
- Letting one module compute totals with floats "for speed" because the inputs come from a CSV. Floats are never acceptable for money; the conversion belongs at the boundary.
- Burying the rounding rule inside individual computations. Rounding is a property of the value object's operations, not of every caller.
- Mixing display formatting with arithmetic. The value object handles arithmetic and stores precise amounts; presentation layers format for the UI, sometimes with different rules per locale.

**Retrospective indicator that you did this right:** Finance asks for a switch from half-up to banker's rounding and one PR delivers it across the whole product. Adding support for a new currency is a config change, not a code archaeology expedition. The day an audit demands a reconciliation report between invoice totals and line-item sums, the totals match to the cent because there is one rounding rule, applied once.

---

## P5. Date and timezone boundary

**Structural signature:** Some endpoints return ISO 8601 strings with explicit timezone offsets; others return naive timestamps in an implicit server timezone. Database columns are a mix of `TIMESTAMP` and `TIMESTAMPTZ`. Scheduled jobs assume server-local time but run in UTC after a deployment to a different region. Two services compute "yesterday" differently because one normalizes to UTC midnight and the other to local midnight. Daylight-saving transitions produce off-by-one-hour bugs that nobody can reproduce on demand.

**Forces that want this to change together:** Storage representation (all timestamps stored in UTC, period). Input parsing (one place that converts incoming timestamps to UTC, regardless of whether the source is an HTTP request, a queue message, or a CSV row). Display rendering (one rendering layer that converts UTC to the user's locale and DST-aware timezone). Schedule semantics (a job specified as "daily at 02:00" must be unambiguous about whose 02:00).

**Suggested target layer:** A `TimeBoundary` module with two operations: `to_utc(input, source_timezone)` at every entry point, and `to_local(utc, target_timezone)` at every rendering point. The rest of the codebase manipulates UTC `datetime` objects only. Scheduled-job timezone is part of the job specification, not implicit.

**Common pitfalls:**
- Storing local time anywhere except the rendering layer. Even one column with a naive local timestamp poisons every downstream calculation.
- Using the server timezone implicitly. Server-local time is a deployment property, not a domain property; depending on it makes every region deployment risky.
- Treating "date" and "datetime" as the same concept. A user's "birthdate" is a date (no timezone); a user's "last_login" is a datetime in UTC. Mixing them produces confusing bugs at midnight near timezone boundaries.
- Manual DST arithmetic. Always use a timezone-aware library (Python `zoneinfo`, JS `Temporal` or Luxon) that understands DST rules per region.

**Retrospective indicator that you did this right:** Adding support for a new locale or a new server region is a config change. A daylight-saving transition does not produce a flurry of bug reports because every conversion goes through one tested module. The day analytics asks "what time of day do users in Sydney sign up", the query returns Sydney local time without ambiguity.

---

## P6. Pagination and cursor encoding

**Structural signature:** Three list endpoints. The first returns `?page=2&page_size=20` and offsets the SQL query. The second returns `?after=abc123` and decodes the cursor as a base64 JSON blob. The third returns `?next_token=def456` and decodes it as a signed JWT. Clients integrating with the API have to special-case each endpoint. A new endpoint copies whichever pattern the developer noticed first; the inconsistency grows.

**Forces that want this to change together:** Cursor format (the team decides on keyset pagination for stability under inserts and wants every list endpoint to migrate). Maximum page size (a single cap to prevent abuse, applied uniformly). Cursor signing (cursors must be tamper-resistant so clients cannot pass arbitrary values; one signing key, one verification). Total-count semantics (the team decides total counts are expensive and removes them everywhere, or keeps them only for small collections).

**Suggested target layer:** A `Pagination` module that owns cursor encoding, decoding, signing, and page-size limits. List endpoints accept and return cursors via the module; the SQL or storage layer receives a typed `PageRequest(after, limit, direction)` that hides the cursor format.

**Common pitfalls:**
- Leaking the cursor implementation through the public surface. If clients can see that the cursor is base64-encoded JSON containing an offset, they will start constructing cursors themselves and the team cannot migrate to keyset later.
- Mixing pagination modes within the same endpoint (offset for the first page, cursor for subsequent pages). Pick one mode per endpoint and use it consistently.
- Allowing arbitrary page sizes. Every list endpoint needs a cap; the cap belongs in the module, not in every handler.
- Forgetting to sort. Cursor pagination depends on a stable sort order; without it, results jump around as rows are inserted or updated.

**Retrospective indicator that you did this right:** A migration from offset to keyset pagination is a one-module change behind a feature flag, not a per-endpoint rewrite. SDK clients use one pagination pattern across the whole API surface. The day product asks for a new list endpoint, the developer wires it up in minutes by reusing the existing module.

---

## P7. Connection pool and unit of work

**Structural signature:** Repository or DAO classes each call `engine.connect()` or `pool.acquire()` directly inside their methods. There is no shared transaction across repositories; if a use case needs to update two aggregates atomically, the second update has to begin its own transaction and pray nothing fails in between. Reconnection logic is copy-pasted: each repository has its own `try / except / reconnect` block, and they have already drifted on whether to retry on which exception types.

**Forces that want this to change together:** Transaction boundary (a use case spanning two aggregates must succeed or roll back as a unit). Reconnection on connection drop (one place that knows how to identify a stale connection, return it to the pool, and reopen). Connection pool sizing and lifecycle (pool sized for the workload, with proper draining on shutdown). Statement timeouts and lock timeouts (uniform across the application). Read replicas (a routing decision the application makes once, not per-repository).

**Suggested target layer:** A unit of work or session abstraction that owns connection acquisition, transaction scope, reconnection, and statement timeouts. Repositories accept the unit of work as a parameter and run their queries inside it. Use cases open a unit of work, call multiple repositories within it, and commit or roll back as a unit.

**Common pitfalls:**
- Hiding the pool inside repositories such that two repositories cannot share a transaction. This pattern looks like good encapsulation but blocks cross-aggregate atomicity at exactly the moment the business requires it.
- Conflating connection management with transaction management. They are related but separable; some operations need a connection without a transaction (raw reads on a replica), some need a long transaction across multiple connections.
- Per-repository retry loops that diverge on what counts as a retriable error. Reconnection policy belongs at the pool level; retry on a deadlock or transient failure may belong at the use-case level, not the repository.
- Forgetting to close or return connections on the failure path. A leaked connection drains the pool until the process restarts.

**Retrospective indicator that you did this right:** Switching from a single primary to a primary-plus-read-replica routing is a one-module change. The day a transient database failure floods the logs, the reconnection policy is one place to tune. Cross-aggregate consistency works because the unit of work makes the transaction boundary explicit.

---

## P8. Structured logging and correlation IDs

**Structural signature:** Three services emit logs in three formats. Service A logs JSON with `user_id` and `request_id`. Service B logs JSON with `userId` and `requestId`. Service C logs unstructured text. Tracing a single user's request across the system requires three different grep patterns. A correlation ID is generated at the edge but propagated by hand: some services pass it through HTTP headers, some lose it across queue boundaries, some never had it.

**Forces that want this to change together:** Log schema (field names, types, the set of standard attributes on every log line). Severity levels (consistent thresholds for what counts as `WARN` versus `ERROR`). Correlation ID generation and propagation (one ID per request, attached to every log line emitted by every component that handled it). Redaction (PII and secrets stripped uniformly before logs leave the process). Output destination (stdout for the cloud-native deployment, file rotation for the on-prem deployment, both configured once).

**Suggested target layer:** A logging facade per language that wraps the underlying library (`structlog`, `winston`, `slf4j`, `serilog`) with the project's field schema, redaction rules, and correlation-ID extraction. Application code calls the facade with structured key-value pairs; the facade attaches the correlation ID from the current context, applies redaction, and emits to the configured destination.

**Common pitfalls:**
- Logging the same event with different field names across services. `user_id` versus `userId` versus `uid` makes cross-service queries painful and breaks alerting that depends on field shape.
- Losing the correlation ID across asynchronous boundaries (queues, background jobs, scheduled tasks). The ID must be carried explicitly through the message envelope and re-attached on the consumer side.
- Logging sensitive data without redaction. PII, tokens, full request bodies, and stack traces with secrets are easy to leak; the facade should redact by default and require opt-in to log raw fields.
- Mixing log levels arbitrarily. `INFO` should not be used for every event; reserve levels with documented meaning so dashboards and alerts can rely on them.

**Retrospective indicator that you did this right:** A single query in the log aggregator returns every log line for a given request across all services. The day an alerting rule needs a new field, adding it to the schema is a one-module change. PII does not leak because the facade redacts uniformly.

---

## P9. Error envelope toward clients

**Structural signature:** Controllers return errors in three different shapes. Some return `{"error": "not found"}`. Others return `{"code": 404, "message": "..."}`. A third uses RFC 7807 problem details. Clients have to special-case each shape. A new endpoint copies a pattern at random. The mobile app has a switch statement on error strings to decide what UI to show, and the switch is wrong in two places.

**Forces that want this to change together:** Error code taxonomy (a stable set of machine-readable codes that the client can switch on). User-facing message (localized, safe for display, never containing internal details like stack traces or SQL). Retry-after hint (for rate-limited or transient errors, when should the client retry). HTTP status mapping (one consistent mapping from internal error type to HTTP status). Internal correlation ID (so the client report can be matched to the server-side log line).

**Suggested target layer:** An `ErrorEnvelope` type and a single mapping from domain errors to envelope. Controllers do not craft error responses; they raise typed domain errors and the framework's exception handler produces the envelope. The envelope includes: stable code, message, optional details, retry-after when relevant, correlation ID.

**Common pitfalls:**
- Letting controllers craft ad-hoc error shapes. The moment one endpoint deviates, the client SDK has to special-case it, and the deviation spreads.
- Leaking internal details (stack traces, SQL fragments, vendor error codes) into the user-facing message. The envelope has a public message and an optional internal details field that the client SDK never displays.
- Coupling error codes to HTTP status codes too tightly. Some domain errors have no good HTTP mapping; the envelope's `code` field should be the source of truth and HTTP status is derived from it.
- Forgetting to localize. The user-facing message is shown to humans; it must support the user's locale, not the server's.

**Retrospective indicator that you did this right:** Adding a new error type is a one-line addition to the code taxonomy plus an entry in the message catalog. The mobile and web clients share a switch on the same code values. The day support asks "what does error code E_PAYMENT_DECLINED_INSUFFICIENT_FUNDS mean", the answer is in one document.

---

## P10. Feature flag and config reader

**Structural signature:** Several modules call `os.getenv("FEATURE_X")` directly, comparing the result to the strings `"true"`, `"1"`, `"yes"` with different rules per module. Some configuration values have defaults inline; others raise on missing values. Typed config is unusual; most reads return strings that callers parse ad hoc. A misspelled environment variable name is found three months later by a customer.

**Forces that want this to change together:** Type safety (config values have typed accessors; integers and booleans are parsed once and validated). Default policy (every config value has a documented default, and the default is one place). Source precedence (CLI flag overrides env var overrides config file overrides default, applied uniformly). Feature flag lifecycle (flags are temporary; the system should know when a flag is stale). Hot reload (some config values need to be re-read without restart; others are baked at startup).

**Suggested target layer:** A typed `Config` module with one accessor per value, default + validation + documentation in one place. Feature flags route through a separate `FeatureFlags` service backed by a flag platform (LaunchDarkly, Unleash, Statsig) or a typed local table; either way the module is the only path. Modules import the config object; they do not call `getenv` directly.

**Common pitfalls:**
- Scattering `os.getenv` calls across modules. A misspelled name fails silently; a default value duplicated in three places drifts.
- Treating feature flags as eternal. Flags should expire; the codebase needs a "stale flag" check that flags pending removal after a deadline.
- Leaking environment-variable names through public APIs. Internal modules import a typed config object; the mapping from object property to env var name is one place.
- Conflating boot-time config with runtime flags. Boot-time config is set at startup and rarely changes; runtime flags can flip per-request and need a different evaluation path.

**Retrospective indicator that you did this right:** A new config value is one line in the config module plus a documented default. Misspelled environment-variable names fail at startup with a clear error, not three months later in production. The day someone audits the feature flag table, the stale flags are obvious because the module knows their expiry dates.

---

## P11. Retry and backoff policy

**Structural signature:** Three services that call external APIs each have their own retry loop. One retries three times with no backoff. Another retries five times with linear backoff. A third has an unbounded retry loop guarded by a five-minute timeout. Each loop defines "retriable" differently: one retries on 5xx and connection errors; another also retries on 429; a third retries on any exception, including programming errors.

**Forces that want this to change together:** Backoff curve (exponential, capped, jittered, with consistent parameters tuned for the vendor). Maximum attempts (a single ceiling beyond which the operation is declared failed). Retriable classification (a stable predicate that says which exceptions are transient and which are permanent). Circuit breaker (after N consecutive failures, stop calling the vendor for a cooldown period to avoid thundering herd). Idempotency (only retry calls that are safe to repeat, or attach an idempotency key).

**Suggested target layer:** A `RetryPolicy` module with a single `retry(operation, policy)` entry point. Policies are named (`Policy.STANDARD_EXTERNAL_API`, `Policy.IDEMPOTENT_WRITE`, `Policy.CRITICAL_PAYMENT`) and parameterized once. Vendor wrappers (see P1) accept a policy; features call them without knowing the retry details.

**Common pitfalls:**
- Per-service custom retry loops that diverge in their definition of "retriable". A connection-reset error retriable in one service and fatal in another produces inconsistent reliability.
- Retrying non-idempotent operations without an idempotency key. Two retries of "charge the card" can charge the customer twice.
- Combining retry with circuit breaker incorrectly. The circuit breaker counts failures to decide when to stop; the retry loop is inside the breaker, not outside, so a tripped breaker short-circuits without retrying.
- Forgetting jitter. Synchronized retries across many clients produce thundering herd spikes that prolong the outage.

**Retrospective indicator that you did this right:** The day a vendor changes its rate-limit response from 429 to a different code, tuning the predicate is one module change. A new external integration uses one of the existing named policies without writing a new loop. The day a vendor outage hits, the circuit breaker contains the blast radius and the load graphs do not produce a thundering-herd spike.

---

## P12. Observability: metrics and tracing context propagation

**Structural signature:** Trace spans appear in some services but not others. Spans are created at the HTTP layer of the entry service but not propagated across the queue boundary; a downstream service starts a new root trace and the link is lost. Metric names vary: `http_requests_total`, `http.requests.count`, `requests_count`. Attribute conventions differ: one service tags `service.name`, another tags `service`, a third does not tag at all. A business-critical operation (e.g. "place_order") does not appear as a span at all because instrumentation was applied at the framework layer and order placement is a service-method call.

**Forces that want this to change together:** Span creation discipline (every business-critical operation is a span, named consistently). Attribute conventions (the project adopts OpenTelemetry semantic conventions or its own published convention, applied uniformly). Context propagation across boundaries (HTTP headers, queue message envelopes, RPC metadata all carry the trace context). Metric naming (a stable taxonomy that dashboards and alerts can rely on). Sampling (one sampling decision per trace, made at the entry point, respected throughout).

**Suggested target layer:** An observability module that owns span creation, attribute application, context extraction at boundaries, and context injection at egress. Business code calls `with telemetry.span("place_order"): ...` and the module attaches the standard attributes, propagates context, and emits metrics. Boundary code (HTTP middleware, queue consumers and producers, RPC interceptors) handles propagation once, in one place.

**Common pitfalls:**
- Instrumenting at the wrong layer. Framework-level instrumentation captures every HTTP request but misses the business operation. Service-level instrumentation alone misses what happened across a queue boundary. Both layers should be wired through the same module.
- Inconsistent attribute names. `tenant_id` versus `tenant.id` versus `tenantId` breaks cross-service joins in the tracing UI.
- Forgetting to propagate context across asynchronous boundaries. A trace that stops at the queue boundary is half useful.
- Over-instrumenting low-level utilities (string formatting, math helpers) so the trace is noisy and the business operations are buried. Reserve spans for boundaries and business-critical operations.

**Retrospective indicator that you did this right:** The day production has an incident, the on-call engineer can follow one request from HTTP entry through every downstream service in a single trace. Adding a metric or a span to a new operation follows the same pattern as the last one. The dashboard for "p99 latency by business operation" already exists because every operation is a span with a stable name.
