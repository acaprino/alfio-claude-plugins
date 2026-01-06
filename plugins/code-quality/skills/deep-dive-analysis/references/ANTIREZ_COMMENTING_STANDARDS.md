# Antirez Commenting Standards

> Source: https://antirez.com/news/124

This document codifies the commenting standards from Salvatore Sanfilippo (antirez), creator of Redis. These standards form the basis for the `rewrite_comments.py` tool in the deep-dive-analysis skill.

---

## Core Philosophy

Comments are not just for documentation. They serve multiple purposes:

1. **API Documentation** - Let readers treat code as black boxes
2. **Design Rationale** - Explain why, not what
3. **Knowledge Transfer** - Teach domain concepts
4. **Cognitive Load Reduction** - Create rhythm and structure
5. **Coordination** - Remind of dependent changes

**The cardinal rule:** A comment requiring as much effort to read as the code itself is worse than useless.

---

## The Nine Comment Types

### GOOD Comments (Keep and Enhance)

#### 1. Function Comments

**Purpose:** Serve as inline API documentation at function/class top.

**Location:** Immediately before or inside function/class definition.

**Goal:** Allow readers to understand behavior without reading implementation.

```python
def shutdown_all_workers(
    pool_id: str,
    reason: str,
    timeout_seconds: float = 30.0,
) -> ShutdownResult:
    """
    Gracefully shut down all workers in a pool.

    This is the nuclear option for resource management. Use only when:
    - Pool enters error state
    - Connection to backend lost > 30 seconds
    - Resource usage exceeds configured limit

    The function will:
    1. Cancel all pending tasks
    2. Drain workers in reverse allocation order (largest first)
    3. Log each shutdown with reason
    4. Broadcast worker_stopped events

    Args:
        pool_id: UUID of the worker pool
        reason: Human-readable reason for emergency shutdown
        timeout_seconds: Maximum wait time per worker (default 30s)

    Returns:
        ShutdownResult with success status and list of stopped workers

    Raises:
        ConnectionError: If backend unreachable after 3 retries
        PartialShutdownError: If some workers couldn't be stopped

    Example:
        result = shutdown_all_workers(
            pool_id="abc-123",
            reason="Memory usage exceeded 90%",
        )
        if not result.all_stopped:
            alert_operations_team(result.failed_workers)
    """
```

**Antirez Quote:**
> "Function comments allow the reader to conceptually take the code and use it as aering a black box. This is the most important thing about function comments."

---

#### 2. Design Comments

**Purpose:** Explain algorithms, techniques, and design decisions.

**Location:** At file or class top.

**Goal:** Show readers that non-obvious solutions were considered and justify choices.

```python
"""
Resource Allocation Calculator

This module implements the Weighted Fair Queuing allocation model,
also known as "Proportional Share Scheduling."

DESIGN CHOICES:

1. Why Weighted Fair Queuing (not Round Robin or Priority)?
   - Round Robin ignores job importance, treats all equally
   - Pure Priority causes starvation of low-priority jobs
   - WFQ balances fairness with priority, industry standard
   - Our benchmarks show it outperforms alternatives for our workload

2. Why calculate per-job (not pool-level)?
   - System runs independent workers
   - Each worker manages its own resource allocation
   - Pool-level would require coordination layer

3. Overhead percentage assumption
   - Hardcoded to 5% because:
     a) System processes short-lived tasks (milliseconds to seconds)
     b) Context switch overhead is minimal at this scale
     c) Simplifies calculation

ALTERNATIVES CONSIDERED:
- Max-Min Fairness: Too complex for our use case
- Fixed Allocation: Doesn't scale with demand
- FIFO: No quality of service guarantees

SEE ALSO:
- Demers et al., "Analysis and Simulation of Fair Queueing"
- Parekh & Gallager, "A Generalized Processor Sharing Approach"
"""
```

**Antirez Quote:**
> "Design comments are higher-level comments at the top of a file... that explain the general design of the code, typically explaining the algorithm, technique, or some kind of general idea."

---

#### 3. Why Comments

**Purpose:** Explain the reasoning behind code decisions.

**Location:** Immediately before the code in question.

**Goal:** Prevent future developers from "simplifying" intentional complexity.

```python
# We use a 100ms delay between API calls because:
# 1. The service rate-limits at 10 requests/second
# 2. During testing, we observed connection drops at higher rates
# 3. The 50ms buffer accounts for network jitter
# Issue: PROJ-892
await asyncio.sleep(0.100)

# Empty string instead of None for missing fields because
# JSON message serialization treats None as missing key,
# which breaks downstream consumers expecting the field.
comment = comment if comment else ""

# Sorting by absolute value (not signed) because we want
# to process largest items first regardless of direction.
# A -10 delta is as urgent to handle as +10 delta.
items.sort(key=lambda p: abs(p.delta), reverse=True)
```

**Antirez Quote:**
> "Why comments explain the reason why the code is doing something... This is the kind of comments I love the most."

---

#### 4. Teacher Comments

**Purpose:** Educate readers about domain knowledge they may lack.

**Location:** Before code that uses specialized concepts.

**Goal:** Lower barrier to entry for contributors.

```python
# Exponential backoff calculates delay as:
#   base_delay * (2 ^ attempt_number) + jitter
# Higher attempt = longer wait. Cap prevents infinite delays.
#
# We use base=1s with max=60s (industry standard) to prevent
# thundering herd on service recovery. The jitter (±10%) prevents
# synchronized retries from multiple clients.
#
# Reference: AWS Architecture Blog, "Exponential Backoff And Jitter"
retry_delay = min(self.base_delay * (2 ** attempt), self.max_delay)

# Latency model using log-normal distribution because:
# - Cannot be negative (latency is always positive)
# - Has fat tail (high latency events are rare but occur)
# - Empirically matches our historical request data
#
# The parameters (mu=0.05, sigma=0.02) were fitted from
# 10,000 requests to the backend during 2024.
expected_latency = np.random.lognormal(mean=0.05, sigma=0.02)
```

**Antirez Quote:**
> "Teacher comments explain to the reader that is not specialized in such a topic, how a given algorithm works, or how a given concept works."

---

#### 5. Checklist Comments

**Purpose:** Remind developers of coordinated changes needed elsewhere.

**Location:** Before code that has external dependencies.

**Goal:** Prevent subtle bugs from incomplete refactoring.

```python
# WARNING: If you modify these states, also update:
# - frontend/src/types/task_state.ts (TypeScript mirror)
# - src/tests/test_task_lifecycle.py (test fixtures)
# - docs/architecture/TASK_STATES.md (documentation)
# - The Mermaid diagram in README.md
#
# Failure to sync will cause deserialization errors between
# frontend and backend.
class TaskState(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


# SYNC: This routing key format must match:
# - src/messaging/publisher.py (publisher)
# - src/messaging/consumer.py (consumer)
# - docs/messaging/ROUTING_KEYS.md
EVENT_ROUTING_KEY = "event.{type}.{category}.{source_id}"
```

**Antirez Quote:**
> "Checklist comments are a warning, a reminder. They are there to tell the reader that is going to modify the code that its modification, or some other action, must be performed."

---

#### 6. Guide Comments

**Purpose:** Lower cognitive load through rhythm and divisions.

**Location:** Between logical sections of code.

**Goal:** Help readers navigate large files and understand structure.

```python
class OrderExecutor:
    """Handles order execution lifecycle."""

    # ═══════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ═══════════════════════════════════════════════════════════════

    def __init__(self, broker: BrokerAdapter):
        self.broker = broker
        self.pending_orders = {}

    # ═══════════════════════════════════════════════════════════════
    # ORDER SUBMISSION
    # ═══════════════════════════════════════════════════════════════

    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit a new order to the broker."""
        ...

    async def modify_order(self, order_id: str, changes: OrderChanges) -> bool:
        """Modify an existing pending order."""
        ...

    # ═══════════════════════════════════════════════════════════════
    # ORDER CANCELLATION
    # ═══════════════════════════════════════════════════════════════

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        ...

    async def cancel_all_orders(self) -> int:
        """Cancel all pending orders. Returns count cancelled."""
        ...
```

**Note:** Guide comments are controversial. Some consider them unnecessary if code is well-structured. Use sparingly.

---

### BAD Comments (Delete or Rewrite)

#### 7. Trivial Comments

**Definition:** Comments that restate what the code already says.

**Problem:** Reading the comment requires equal effort to reading the code.

**Action:** Delete immediately.

```python
# BAD - These add nothing:
i += 1  # Increment i
return result  # Return result
if user is None:  # If user is None
    raise ValueError()  # Raise an error
for item in items:  # Loop through items
    process(item)  # Process item
self.value = value  # Set value

# GOOD - These add context:
i += 1  # Move to 1-based index for API compatibility
return result  # Caller expects mutable list, not generator
if user is None:  # Unauthenticated requests get default quota
    return DEFAULT_USER
```

**Antirez Quote:**
> "Trivial comments are guide comments that are completely useless... where reading the comment is not much simpler than reading the code."

---

#### 8. Debt Comments

**Definition:** TODO, FIXME, XXX, HACK markers without resolution plan.

**Problem:** Accumulate indefinitely, become noise, never get resolved.

**Action:** Convert to proper documentation or create tracked issues.

```python
# BAD:
# TODO: fix this
# FIXME: sometimes crashes
# XXX: hack
# HACK: temporary workaround
# TODO: optimize later

# BETTER - Convert to design comment:
# DESIGN DECISION: Using polling instead of webhooks
#
# Context: External API v1 doesn't support webhooks. We poll every
# 100ms which introduces latency but is reliable.
#
# Resolution Plan: API v2 (expected Q2 2025) adds webhook support.
# When upgrading, refactor to push model per PROJ-1456.
#
# Tracking: PROJ-1234
#
# Acceptance Criteria:
# - [ ] API v2 available in production
# - [ ] Webhook endpoint implemented
# - [ ] 30-day parallel run with polling as fallback

# BEST - Create issue and reference:
# See PROJ-1234 for planned migration to webhook model
```

**Antirez Quote:**
> "Debt comments are sometimes acceptable. But in general, there is a better way to handle things that are problematic... If the thing is important, create an issue. If it's not, delete the comment."

---

#### 9. Backup Comments

**Definition:** Commented-out code kept "just in case."

**Problem:** Clutters codebase, confuses readers, always outdated.

**Action:** Delete completely. Use git history if needed.

```python
# BAD - Delete all of this:
# def old_calculate_price(symbol):
#     # Old implementation before v2.0
#     price = get_cached_price(symbol)
#     if price is None:
#         price = fetch_from_api(symbol)
#     return price

# class DeprecatedOrderHandler:
#     """No longer used after refactor"""
#     pass

# ACCEPTABLE (rare) - When keeping temporarily for safety:
# DEPRECATED: Remove after v2.1 stable release (target: 2025-02-01)
# Kept for emergency rollback during 2.0->2.1 migration.
# Tracking: PROJ-2001
#
# def legacy_request_handler():
#     """Old handler, kept for rollback safety only."""
#     ...
```

**Antirez Quote:**
> "Backup comments are commented-out code... with modern version control systems, this is always wrong."

---

## Decision Matrix

| Comment Type | Keep? | Action if Found |
|-------------|-------|-----------------|
| Function | YES | Expand if brief, add if missing |
| Design | YES | Add at file top if missing |
| Why | YES | These are highly valuable |
| Teacher | YES | Link to authoritative sources |
| Checklist | YES | Verify links are current |
| Guide | MAYBE | Don't overdo, use for large files |
| Trivial | NO | Delete immediately |
| Debt | NO | Convert to issue or design comment |
| Backup | NO | Delete, rely on git history |

---

## Integration with deep-dive-analysis

The `rewrite_comments.py` CLI tool uses these standards:

```bash
# Analyze comments in a file
python rewrite_comments.py analyze src/main.py --report

# Scan entire codebase
python rewrite_comments.py scan src/ --recursive

# Generate health report
python rewrite_comments.py report src/ --output comment_health.md

# Apply recommended deletions (with backup)
python rewrite_comments.py rewrite src/main.py --apply --backup
```

---

## References

1. **Original Article:** https://antirez.com/news/124
2. **Redis Source Code:** Example of these principles in practice
3. **Code Complete (McConnell):** Chapter 32 on Self-Documenting Code
4. **Clean Code (Martin):** Chapter 4 on Comments

---

*Document generated as reference for deep-dive-analysis skill*