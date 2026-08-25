# Data & Persistence + Design Patterns + Build & Deploy + Testing & Observability

Reference for defect taxonomy categories 12, 14, 15, and 16.

---

## Category 12: Data and Persistence Errors

### 12.1 N+1 Queries
- **CWE**: N/A
- **Pattern**: ORM lazy-loads related entities in loop -- 1 query + N queries per item
- **Detection**: `nplusone` (Python), `bullet` (Ruby), Django Debug Toolbar, Hibernate SQL logging
- **Fix**: Eager loading (`select_related`/`prefetch_related`, `JOIN FETCH`), DataLoader pattern (GraphQL), batch queries
- **Difficulty**: Easy
- **Signature**: Loop body triggers SQL query per iteration, query count scales with result set size

### 12.2 Missing Indexes
- **CWE**: N/A
- **Pattern**: Full table scans hidden by small dev datasets, slow queries in production
- **Detection**: `EXPLAIN ANALYZE`, slow query logs, `pg_stat_user_tables` (seq_scan count)
- **Fix**: B-tree indexes on filter/join columns, composite indexes for multi-column queries, GIN for full-text/JSONB
- **Difficulty**: Easy
- **Signature**: Sequential scan on large table, queries > 100ms on indexed-looking WHERE clauses

### 12.3 Transaction Isolation Bugs
- **CWE**: N/A
- **Pattern**: Wrong isolation level causes phantom reads, non-repeatable reads, write skew
- **Isolation levels**: READ UNCOMMITTED < READ COMMITTED < REPEATABLE READ < SERIALIZABLE
- **Fix**: Match isolation to invariant requirements, SERIALIZABLE for financial/inventory, optimistic locking as alternative
- **Difficulty**: Hard
- **Signature**: Balance check + debit in READ COMMITTED allows negative balance under concurrency

### 12.4 Lost Updates / Dirty Reads
- **CWE**: N/A
- **Pattern**: Concurrent read-then-write overwrites other's changes, last-writer-wins silently
- **Detection**: Concurrent update tests, version mismatch monitoring
- **Fix**: Optimistic concurrency (version column + `WHERE version = ?`), `SELECT FOR UPDATE`, compare-and-swap
- **Difficulty**: Medium
- **Signature**: `UPDATE ... SET x = computed_value` without version check, two users editing same record

### 12.5 ORM Mapping Errors
- **CWE**: N/A
- **Pattern**: Wrong cardinality (`@OneToMany` vs `@ManyToMany`), missing cascade config, orphan records
- **Detection**: Schema comparison tools, integration tests against real DB
- **Fix**: Audit mappings against ER diagrams, explicit cascade settings, orphan removal config
- **Difficulty**: Medium

### 12.6 Cache Coherence / Invalidation
- **CWE**: N/A
- **Pattern**: Stale cache after write, cache stampede (thundering herd on expiry)
- **Detection**: Cache hit rate monitoring, staleness detection, stampede metrics
- **Fix**: Write-through/write-behind cache, TTL with jitter (prevent synchronized expiry), single-flight/coalesce locks
- **Difficulty**: Medium
- **Signature**: User updates profile but sees old data, all cache entries expire at same second

### 12.7 Concurrent Write Corruption
- **CWE**: N/A
- **Pattern**: Race condition in upserts, duplicate records from concurrent inserts, missing unique constraints
- **Detection**: Concurrent insert tests, duplicate record monitoring
- **Fix**: DB-level unique constraints + `ON CONFLICT` / `MERGE`, advisory locks for complex operations
- **Difficulty**: Medium

### 12.8 Schema Evolution Errors
- **CWE**: N/A
- **Pattern**: Dropping columns used by old code, changing column types, adding NOT NULL without defaults
- **Detection**: Schema diff tools, migration CI against running app version
- **Fix**: Expand-and-contract pattern, add nullable columns with defaults first, backfill then add constraint
- **Difficulty**: Medium

---

## Category 14: Design Pattern Misuse

### 14.1 Singleton Thread-Safety
- **CWE**: 543, 609
- **Pattern**: Double-checked locking without `volatile` (Java), race in lazy init
- **Fix**:
  - Java: Enum singleton or holder class pattern
  - Go: `sync.Once`
  - C++11: Meyers Singleton (function-local static)
  - Python: Module-level instance (import system handles)
- **Difficulty**: Medium-High
- **Signature**: `if (instance == null) { synchronized { if (instance == null) ... } }` without `volatile`

### 14.2 Observer Memory Leaks
- **CWE**: 401, 772
- **Pattern**: Lapsed listener problem -- registered observers never unregistered, `.bind(this)` creates new function preventing removal
- **Detection**: Listener count growth monitoring, heap dump analysis for event-related objects
- **Fix**: Symmetric register/unregister lifecycle, `WeakReference` listeners, `AbortController` signal for cleanup
- **Difficulty**: Medium-High
- **Signature**: `emitter.on('event', this.handler.bind(this))` -- can never `removeListener`

### 14.3 Incorrect Factory / Builder
- **CWE**: 665, 908
- **Pattern**: Builder without enforcing required fields, factory returning wrong subtype, incomplete initialization
- **Detection**: Unit tests for required field validation, builder coverage tests
- **Fix**: Mandatory fields in constructor (not builder), Step Builder pattern, validation in `build()` method
- **Difficulty**: Medium
- **Signature**: `builder.build()` succeeds without setting `name` (a required field)

### 14.4 Strategy with Shared Mutable State
- **CWE**: 362, 567
- **Pattern**: Strategy implementations registered as singletons but contain mutable instance fields
- **Detection**: Concurrency tests, field mutation analysis on singleton-scoped beans
- **Fix**: Stateless strategies, pass context through method parameters, prototype scope in DI container
- **Difficulty**: Medium-High
- **Signature**: `@Component class PricingStrategy { private BigDecimal discount; }` -- shared across requests

### 14.5 Broken Chain of Responsibility
- **CWE**: 691
- **Pattern**: Missing terminal/default handler, infinite loops in chain, handler modifies request mutably
- **Detection**: Chain configuration tests, dead letter / unhandled request monitoring
- **Fix**: Mandatory default handler at chain end, immutable request objects, chain length limits
- **Difficulty**: Medium

---

## Category 15: Build and Deployment Errors

### 15.1 Classpath / Module Conflicts
- **CWE**: N/A
- **Pattern**: `NoSuchMethodError` at runtime, DLL hell, conflicting transitive dependency versions
- **Detection**: `mvn dependency:tree`, Maven Enforcer Plugin, `npm ls --all`, `go mod graph`
- **Fix**: BOM / platform dependencies, dependency exclusions, shading (Maven Shade), lock files
- **Difficulty**: Medium

### 15.2 Environment-Specific Code
- **CWE**: N/A
- **Pattern**: Hardcoded URLs, locale assumptions (`MM/dd` vs `dd/MM`), timezone assumptions (server local time)
- **Detection**: Config audit, grep for hardcoded URLs/IPs, locale-sensitive test failures
- **Fix**: 12-factor app, externalized config, explicit `Locale`/`TimeZone` parameters, UTC internally
- **Difficulty**: Easy

### 15.3 Feature Flag Stale States
- **CWE**: N/A
- **Pattern**: Flags left on/off indefinitely, dead code behind permanent flags
- **Detection**: Flag age tracking, unused code analysis, flag inventory audits
- **Fix**: Mandatory expiry dates, automated stale-flag alerts, quarterly cleanup sprints
- **Difficulty**: Easy

### 15.4 Configuration Injection Errors
- **CWE**: N/A
- **Pattern**: Missing env vars at runtime, unresolved `${DB_URL}` placeholders, typos in config keys
- **Detection**: Startup smoke tests, config validation in CI
- **Fix**: Fail-fast startup validation, typed config classes (`@ConfigurationProperties`), required field checks
- **Difficulty**: Easy
- **Signature**: `${DB_URL}` literal in connection string, `NullPointerException` on missing config

### 15.5 Secret Management Failures
- **CWE**: 798
- **Pattern**: Secrets in build logs, secrets baked into Docker layers, secrets in version control
- **Detection**: GitLeaks, TruffleHog, pre-commit hooks, Docker layer analysis
- **Fix**: Vault systems (HashiCorp Vault, AWS Secrets Manager), env var injection at runtime, multi-stage Docker builds
- **Difficulty**: Easy

---

## Category 16: Testing and Observability Gaps

### 16.1 Flaky Tests
- **CWE**: N/A
- **Pattern**: Timing-dependent, shared state between tests, execution order dependency, external service calls
- **Detection**: Flaky test tracking (TestGrid, CI dashboards), test quarantine, retry analysis
- **Fix**: Isolate state per test, deterministic clocks/fakes, container isolation (Testcontainers), no shared DB state
- **Difficulty**: Medium

### 16.2 Missing Edge Case Coverage
- **CWE**: N/A
- **Pattern**: Only happy-path tests, missing null/empty/boundary/error cases
- **Detection**: Mutation testing (PIT/Java, Stryker/JS), property-based testing (QuickCheck, Hypothesis, fast-check)
- **Fix**: Boundary value analysis, equivalence partitioning, mutation testing in CI, property-based tests
- **Difficulty**: Medium

### 16.3 Incorrect Mocking
- **CWE**: N/A
- **Pattern**: Mocks don't match real behavior, over-mocking hides integration bugs, mock returns stale schema
- **Detection**: Contract tests, integration test failures that unit tests miss
- **Fix**: Prefer fakes over mocks, contract tests (Pact), Testcontainers for real dependencies, mock verification
- **Difficulty**: Medium

### 16.4 Missing Observability
- **CWE**: N/A
- **Pattern**: No metrics, no distributed tracing, no health checks, unstructured logs
- **Detection**: Observability audit checklist, incident postmortem gaps
- **Fix**:
  - Logging: Structured (JSON), correlation IDs, log levels
  - Metrics: RED (Rate, Errors, Duration), USE (Utilization, Saturation, Errors)
  - Tracing: OpenTelemetry, distributed trace context propagation
  - Health: Liveness + readiness probes, dependency health checks
- **Difficulty**: Easy

### 16.5 Log Injection
- **CWE**: 117
- **Pattern**: CRLF injection in log messages, log forging, log4shell-style attacks
- **Detection**: CodeQL, Semgrep, log output analysis for injected newlines
- **Fix**: Sanitize CR/LF characters, parameterized log messages (SLF4J `{}`), structured logging (JSON)
- **Difficulty**: Easy
- **Signature**: `logger.info("User logged in: " + username)` where username contains `\r\n`

### 16.6 Test Infrastructure Design Flaws
- **CWE**: N/A
- **Pattern**: Heavy dependency mocks placed in sub-directory conftest files instead of root conftest; test collection loads real modules into `sys.modules` before sub-conftest runs, breaking `if mod not in sys.modules` guards
- **Detection**: Grep for mock/patch of heavy deps (ortools, scipy, prometheus_client, ML libs) in sub-directory conftest files; verify root `tests/conftest.py` has them instead
- **Fix**: Centralize ALL heavy dependency mocks in root `tests/conftest.py` (executed first by pytest); remove duplicates from sub-conftest files
- **Difficulty**: Medium
- **Signature**: `sys.modules["ortools"]` in `tests/unit/conftest.py` but NOT in `tests/conftest.py`; root-level test files import modules that depend on heavy libs
- **Root cause**: pytest collection order -- root conftest runs first, sub-directory conftest files run only when that directory's tests are collected; root-level test files trigger imports during collection before any sub-conftest executes

### 16.7 Environment/Platform Compatibility in Tests
- **CWE**: N/A
- **Pattern**: Platform API hangs block test execution; pytest plugins call `platform.platform()`, `platform.processor()`, or similar before any conftest.py runs; native dependencies (scipy, BLAS/Fortran extensions) hang on import due to OS-level service issues (e.g., WMI on Windows 11 + Python 3.13)
- **Detection**: Check pytest plugin list for plugins that call `platform.*` functions (pyreadline3, pytest-metadata); check for top-level imports of heavy native deps in conftest; test on target platform
- **Fix**: Monkey-patch platform internals (e.g., `platform._wmi_query`) in test runner script BEFORE `pytest.main()`; mock heavy native deps instead of importing them; use `run_tests.py` wrapper for platform workarounds
- **Difficulty**: Hard (requires understanding pytest plugin initialization order)
- **Signature**: pytest hangs indefinitely before any test runs; `platform._wmi_query()` or `import scipy.optimize` blocks; works on Linux but hangs on Windows

### 16.8 Mock Target and Coverage Errors
- **CWE**: N/A
- **Pattern**: (A) Lazy import mock targeting -- `monkeypatch.setattr("app.module.func", ...)` fails with AttributeError because `func` is imported inside a function (lazy import), not at module level. Must patch at definition site. (B) Incomplete external service mocking -- integration conftest mocks DB, auth, rate limits but misses other external services (cloud storage, email, payment); unmocked calls trigger real API calls, subprocess spawns, or credential lookups that hang
- **Detection**: (A) Verify patched path resolves to an actual module-level attribute; check if target function uses lazy imports. (B) Audit all production `import` statements for external services; cross-reference with integration conftest mock list
- **Fix**: (A) For lazy imports, patch at the module where the function is DEFINED, not where it is used. (B) Add autouse fixtures for every external service in integration conftest
- **Difficulty**: Medium
- **Signature**: (A) `AttributeError: <module> does not have the attribute 'func'` in test. (B) Test hangs calling `google.auth.default()`, `subprocess gcloud`, or similar credential/API lookups
