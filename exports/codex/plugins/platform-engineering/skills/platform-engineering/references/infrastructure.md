# Infrastructure: Monoliths, Databases, CI/CD, and Feature Flags

## Monolith vs Microservices

### MUST

- **Start with a monolith or modular monolith** unless you have a proven, specific need for microservices. Martin Fowler's MonolithFirst principle: almost all successful microservice stories started with a monolith that outgrew its architecture.

### Case Studies

- **Segment:** migrated to microservices then back to a monolith because premature decomposition drowned them in complexity.
- **Amazon Prime Video (2023):** migrated a monitoring service from microservices back to a monolith, achieving 90% cost reduction.
- **Shopify:** runs one of the largest Rails monoliths (3M+ lines of code) successfully using a modular architecture.

### DO

- Build a modular monolith with clear module boundaries using Domain-Driven Design.
- Move to microservices when: 50+ engineers need team autonomy, components have genuinely different scaling requirements today, deployment coordination is a bottleneck, or regulatory requirements demand physical separation.
- Use the Strangler Fig pattern for gradual migration.

### DON'T

- Create a "distributed monolith" -- services so tightly coupled they deploy in lockstep.
- Split by technical layers (API service, data service) -- split by business capabilities.

## Database Access

### MUST

- **Always place an API layer between clients and the database.** Direct database connections from SPAs, mobile apps, or desktop clients are a critical security vulnerability.
- **Use connection pooling** in production. Creating new connections per request costs ~150ms overhead; a pool reduces this to <1ms. Documented improvement: response time from 150ms to 12ms.
- **Prevent N+1 queries** -- the most common ORM performance killer. 100 blog posts with authors generates 101 queries instead of 2.

### DO

- Use eager loading (`select_related`/`prefetch_related` in Django, `JOIN FETCH` in JPA, `.Include()` in EF) and DataLoader for GraphQL, Bullet for Ruby, Sentry for production detection.
- Set query count budgets -- list page: 2-5 queries, detail page: 1-3.
- Write tests asserting query counts.
- Use read replicas for read-heavy workloads and DTOs/projections for read endpoints.

## CI/CD Pipelines

### MUST

- **Automate all builds, tests, and deployments.** Knight Capital's manual deployment process directly contributed to their $440 million loss in 45 minutes.
- Run automated tests as a pipeline gate.
- Sign artifacts securely -- store signing keys in CI secrets management, never in source code.

### Platform Build Chains

| Platform | Pipeline |
|----------|---------|
| **SPA/PWA** | Vite/Webpack to lint to unit tests to E2E (Playwright/Cypress) to CDN deploy |
| **Android** | Gradle to Fastlane to Play Store |
| **iOS** | macOS runners + Xcode to Fastlane Match to TestFlight |
| **Electron** | electron-builder for cross-platform packaging |
| **Tauri** | `cargo tauri build` with Rust compilation (cache with `swatinem/rust-cache`) |

Mobile apps face 1-3 day App Store review cycles -- you can't "hotfix" like web.

## Environment Separation

### MUST

- **Maintain separate dev/staging/prod environments** with distinct configurations, databases, and API keys.
- Never use production data in development without anonymization.
- Use environment variables for all environment-specific settings (12-Factor App methodology).
- Use versioned database migrations (Flyway, Alembic, Prisma Migrate) run as a separate CI step.

## Observability

### MUST

- **Use structured logging (JSON format)** with consistent fields: `timestamp`, `level`, `message`, `request_id`, `user_id`, `trace_id`.
- Implement error tracking from day one -- Sentry (cross-platform), Firebase Crashlytics (mobile).
- Include correlation/trace IDs in every log entry.

### DO

- Follow the three pillars: Logs (ELK Stack, Grafana Loki), Metrics (Prometheus + Grafana), Traces (OpenTelemetry to Jaeger/Zipkin).
- Use OpenTelemetry as the instrumentation standard to avoid vendor lock-in.

### DON'T

- Log sensitive data (passwords, tokens, PII) -- creates compliance violations.
- Rely on `console.log` in production.

## Feature Flags

### MUST

- **Never reuse a feature flag.** Knight Capital repurposed a flag from 2003 for a 2012 feature. One of eight servers didn't receive the update, the old flag triggered legacy test code that bought high and sold low at maximum speed. In 45 minutes, they lost $440 million and went bankrupt. The SEC report documents this as a direct consequence of flag reuse and dead code.
- **Feature flags must have short lifespans.** Remove flags and associated dead code after rollout is complete.
- **Implement kill switches** -- the ability to instantly disable a feature without redeployment.
- Use role-based access control for flag management.

### Platform Rollout Mechanisms

| Platform | Mechanism |
|----------|----------|
| **SPA/PWA** | Instant percentage rollouts via LaunchDarkly/Statsig/Unleash |
| **Mobile** | Google Play staged rollout (1% to 5% to 20% to 100%) or App Store phased release |
| **Desktop** | Update channels (stable/beta/canary) plus in-app flags |

Always configure fallback/default values when the flag service is unreachable.
