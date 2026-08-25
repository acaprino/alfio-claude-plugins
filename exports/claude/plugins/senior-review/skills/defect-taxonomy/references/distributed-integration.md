# Distributed Systems + Communication + Integration Errors

Reference for defect taxonomy categories 8, 9, 10, and 11.

---

## Category 8: API and Contract Errors

### 8.1 API Misuse - Wrong Argument Order/Types
- **CWE**: 628, 683
- **Pattern**: Swapped boolean params, wrong units (ms vs s), mismatched enum values
- **Detection**: Type-safe wrappers, IDE parameter hints, code review
- **Fix**: Builder pattern, parameter objects, `Duration`/`TimeUnit` types, named parameters
- **Difficulty**: Medium-High
- **Signature**: `createUser(email, name)` called as `createUser(name, email)`, `setTimeout(fn, 5)` (5ms not 5s)

### 8.2 Contract Violations
- **CWE**: 573, 476
- **Pattern**: Null where non-null expected, violating preconditions, invariant breaches
- **Detection**: NullAway, Infer, `@NonNull`/`@Nullable` annotations, contracts (Kotlin)
- **Fix**: Nullability annotations, `Optional`, newtypes, precondition checks (`Objects.requireNonNull`)
- **Difficulty**: Medium

### 8.3 Incorrect Method Overriding
- **CWE**: 684, 581
- **Pattern**: Missing `@Override`, `equals()` without `hashCode()`, wrong signature (overload not override)
- **Detection**: `-Xlint:overrides`, SpotBugs `HE_EQUALS_USE_HASHCODE`, `@Override` enforcement
- **Fix**: Always use `@Override`, generate `equals`/`hashCode` together, IDE code generation
- **Difficulty**: Low-Medium

### 8.4 Breaking Interface Changes
- **CWE**: 439
- **Pattern**: Backward-incompatible API modifications without version bump
- **Detection**: `japicmp` (Java), `api-extractor` (TS), `cargo-semver-checks` (Rust)
- **Fix**: SemVer discipline, `@Deprecated` before removal, API versioning (URL or header)
- **Difficulty**: Medium

### 8.5 Callback / Promise Contract Violations
- **CWE**: 672
- **Pattern**: Calling callback twice, not calling callback at all, resolving and rejecting same promise
- **Detection**: Code review, runtime assertions, callback wrapper libraries
- **Fix**: Promises/async-await over callbacks, `once()` wrapper, `AbortController` for cancellation
- **Difficulty**: Medium-High

### 8.6 Iterator Invalidation
- **CWE**: 664
- **Pattern**: Modifying collection while iterating -- `ConcurrentModificationException` (Java), C++ UB
- **Detection**: Runtime exceptions, ASan (C++), SpotBugs
- **Fix**: `Iterator.remove()`, erase-remove idiom (C++), iterate over copy, `removeIf()`
- **Difficulty**: Medium
- **Signature**: `for (item in list) { list.remove(item) }`

---

## Category 9: Distributed Systems Errors

### 9.1 Network Partition Handling
- **CWE**: N/A
- **Pattern**: Missing timeouts on RPCs, no fallback when downstream unavailable
- **Detection**: Chaos engineering (Chaos Monkey), network fault injection, timeout analysis
- **Fix**: Explicit timeouts on all RPCs, fallback responses (cached/default), bulkhead isolation
- **Difficulty**: Medium

### 9.2 Split-Brain
- **CWE**: N/A
- **Pattern**: Multiple nodes believe they are leader, data divergence under partition
- **Detection**: Jepsen testing, leader election monitoring, split-brain detectors
- **Fix**: Quorum-based consensus, fencing tokens (STONITH), Raft/Paxos protocols
- **Difficulty**: Hard

### 9.3 Inconsistent Distributed State
- **CWE**: N/A
- **Pattern**: Replicas diverge due to concurrent updates, partial failures
- **Detection**: Anti-entropy protocols, consistency checkers, read-your-writes tests
- **Fix**: CRDTs, version vectors, Merkle trees for reconciliation, last-writer-wins with vector clocks
- **Difficulty**: Hard

### 9.4 Missing Idempotency
- **CWE**: N/A
- **Pattern**: Retried operations cause duplicate charges, duplicate records, double-sends
- **Detection**: Retry testing, duplicate detection monitoring
- **Fix**: Idempotency keys (client-generated UUID), `INSERT ... ON CONFLICT`, deduplication windows
- **Difficulty**: Medium
- **Signature**: `POST /payments` without idempotency key, retried after timeout

### 9.5 Retry Storms / Thundering Herd
- **CWE**: N/A
- **Pattern**: All clients retry simultaneously, no backoff, amplifying failure
- **Detection**: Request rate monitoring during failures, retry metric tracking
- **Fix**: Exponential backoff with jitter, circuit breakers, retry budgets (max 10% of requests)
- **Difficulty**: Medium

### 9.6 Clock Skew / Ordering Violations
- **CWE**: N/A
- **Pattern**: Using wall-clock time for cross-machine ordering, NTP drift
- **Detection**: Clock skew monitoring, timestamp consistency checks
- **Fix**: Logical clocks (Lamport), hybrid logical clocks (HLC), Google TrueTime, event sequence IDs
- **Difficulty**: Hard

### 9.7 Consensus Protocol Bugs
- **CWE**: N/A
- **Pattern**: Incorrect term/epoch handling, unsafe leader transitions, log truncation errors
- **Detection**: Jepsen, TLA+ model checking, Maelstrom
- **Fix**: Use battle-tested libraries (etcd/Raft, ZooKeeper/ZAB), formal verification
- **Difficulty**: Very Hard

### 9.8 Message Ordering Violations
- **CWE**: N/A
- **Pattern**: Assuming FIFO delivery across partitions, out-of-order processing
- **Detection**: Sequence number gap detection, event ordering tests
- **Fix**: Sequence numbers per entity, single-partition ordering (Kafka partition key), causal ordering
- **Difficulty**: Medium

### 9.9 Circuit Breaker Misconfiguration
- **CWE**: N/A
- **Pattern**: Wrong failure thresholds, missing half-open state, never recovering
- **Detection**: Circuit breaker state monitoring, recovery time tracking
- **Fix**: Tune thresholds via load testing, ensure half-open trial requests, per-endpoint breakers
- **Difficulty**: Medium

### 9.10 Eventual Consistency Violations
- **CWE**: N/A
- **Pattern**: Read-your-own-writes failures, stale reads after writes
- **Detection**: Consistency tests, user-visible staleness monitoring
- **Fix**: Sticky sessions, read-from-primary after write, causal consistency tokens
- **Difficulty**: Medium

### 9.11 Two-Phase Commit Failures
- **CWE**: N/A
- **Pattern**: Coordinator crashes between prepare and commit -- participants block indefinitely
- **Detection**: Transaction timeout monitoring, heuristic resolution alerts
- **Fix**: Saga pattern (preferred), 3PC, persistent recovery logs, transaction timeout limits
- **Difficulty**: Hard

### 9.12 Saga Compensation Errors
- **CWE**: N/A
- **Pattern**: Missing compensating transactions, non-idempotent compensations, incomplete rollback
- **Detection**: Saga state machine auditing, compensation coverage analysis
- **Fix**: Every step has compensating action, compensations must be idempotent, persistent orchestrator state log
- **Difficulty**: Hard

---

## Category 10: Communication and Protocol Errors

### 10.1 Protocol Version Mismatches
- **CWE**: N/A
- **Pattern**: Client/server disagree on protocol version, no negotiation mechanism
- **Fix**: Explicit version negotiation, `Accept`/`Content-Type` versioning, backward-compatible evolution
- **Difficulty**: Medium

### 10.2 Serialization Format Incompatibilities
- **CWE**: N/A
- **Pattern**: Schema evolution errors -- renamed fields, removed required fields, type changes
- **Fix**: Schema registries (Confluent), never remove required fields, additive-only changes, field IDs (Protobuf)
- **Difficulty**: Medium

### 10.3 Missing Heartbeat / Keepalive
- **CWE**: N/A
- **Pattern**: Zombie connections undetected, half-open TCP connections
- **Fix**: TCP keepalive (`SO_KEEPALIVE`), application-level heartbeats/pings, connection health checks
- **Difficulty**: Medium

### 10.4 Timeout Misconfigurations
- **CWE**: N/A
- **Pattern**: Too short (premature failures), too long (resource holding), missing (indefinite block), cascading
- **Fix**: Explicit timeouts on every I/O operation, cascading timeout budgets (inner < outer), connect + read timeouts separately
- **Difficulty**: Low-Medium
- **Signature**: `requests.get(url)` without `timeout=`, downstream timeout > upstream timeout

### 10.5 Connection Pool Exhaustion
- **CWE**: N/A
- **Pattern**: Leaked connections, pool too small for load, no health checking
- **Detection**: HikariCP metrics, pool utilization monitoring, connection leak detection
- **Fix**: `try-with-resources` / `defer` for connections, leak detection enabled, pool sizing via load testing
- **Difficulty**: Easy

### 10.6 Message Queue Poisoning
- **CWE**: N/A
- **Pattern**: Poison message blocks consumer, no dead letter queue, infinite redelivery
- **Fix**: Dead letter queues (DLQ), max retry limits, message TTL, poison message detection
- **Difficulty**: Medium

### 10.7 gRPC / REST Contract Drift
- **CWE**: N/A
- **Pattern**: Server and client schemas diverge, breaking changes undetected until runtime
- **Fix**: Centralized proto/OpenAPI registry, consumer-driven contract tests (Pact), CI schema checks
- **Difficulty**: Medium

### 10.8 WebSocket Lifecycle Errors
- **CWE**: N/A
- **Pattern**: Missing close handlers, reconnect storms, no backoff on reconnection, zombie sockets
- **Fix**: Proper `onclose`/`onerror` handlers, exponential backoff reconnection, connection state machine
- **Difficulty**: Medium

---

## Category 11: Integration and Component Interaction Errors

### 11.1 Dependency Version Conflicts
- **CWE**: N/A
- **Pattern**: Diamond dependency, transitive version conflicts, `NoSuchMethodError` at runtime
- **Detection**: `mvn dependency:tree`, `npm ls --all`, `pip check`, `go mod graph`
- **Fix**: BOM (Bill of Materials), explicit version pinning, dependency exclusions, lock files
- **Difficulty**: Medium

### 11.2 Circular Dependencies
- **CWE**: N/A
- **Pattern**: Python `ImportError` from circular imports, service A calls B calls A
- **Detection**: ArchUnit, `madge` (JS), `import-linter` (Python), service call graph analysis
- **Fix**: Dependency inversion principle, interface extraction, event-driven decoupling, lazy imports
- **Difficulty**: Low-Medium

### 11.3 Interface Mismatch
- **CWE**: N/A
- **Pattern**: DTO field name/type mismatches between services, enum value gaps
- **Detection**: Contract testing (Pact), integration tests, OpenAPI validation
- **Fix**: API-first design, shared schema definitions, consumer-driven contracts
- **Difficulty**: Medium

### 11.4 Configuration Drift
- **CWE**: N/A
- **Pattern**: Hardcoded environment assumptions, works-on-my-machine, env-specific behavior
- **Detection**: Config audits, environment parity checks
- **Fix**: 12-factor app principles, externalized config, startup validation of required config
- **Difficulty**: Easy

### 11.5 Feature Flag Interaction Bugs
- **CWE**: N/A
- **Pattern**: Conflicting flags, stale flags never removed, untested flag combinations
- **Detection**: Flag usage tracking, stale flag alerts, combinatorial flag testing
- **Fix**: Mandatory flag expiry dates, automated stale-flag alerts, flag cleanup sprints, flag dependency documentation
- **Difficulty**: Medium

### 11.6 Service Mesh Misconfiguration
- **CWE**: N/A
- **Pattern**: Sidecar routing errors, mTLS certificate issues, retry policy conflicts with app-level retries
- **Detection**: Service mesh observability (Kiali), certificate expiry monitoring
- **Fix**: Policy-as-code (OPA/Gatekeeper), automated cert rotation, mesh-level retry vs app-level retry alignment
- **Difficulty**: Hard

### 11.7 Database Migration Inconsistencies
- **CWE**: N/A
- **Pattern**: Out-of-order migrations, missing rollback scripts, destructive changes in single step
- **Detection**: Migration history audit, CI migration testing against production-like data
- **Fix**: Expand-and-contract pattern, never drop/rename in single step, backward-compatible migrations, rollback scripts
- **Difficulty**: Medium
