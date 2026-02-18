# Write Mode Examples

Before/after examples for each positive comment type (1-6) and fixes for negative types (7-9).

---

## Type 1: Function Comment

### Before (missing docstring)

```python
def calculate_compound_interest(principal, rate, periods, contributions=0):
    if rate == 0:
        return principal + contributions * periods
    factor = (1 + rate) ** periods
    base = principal * factor
    annuity = contributions * (factor - 1) / rate
    return base + annuity
```

### After

```python
def calculate_compound_interest(
    principal: float,
    rate: float,
    periods: int,
    contributions: float = 0,
) -> float:
    """Calculate future value with compound interest and regular contributions.

    Uses the standard compound interest formula with an optional annuity
    component for periodic contributions.

    Args:
        principal: Initial investment amount. Must be non-negative.
        rate: Interest rate per period as a decimal (e.g., 0.05 for 5%).
            Use 0 for simple accumulation without interest.
        periods: Number of compounding periods. Must be positive.
        contributions: Fixed amount added at the end of each period.

    Returns:
        Total future value including compounded principal and contributions.
    """
    if rate == 0:
        return principal + contributions * periods
    factor = (1 + rate) ** periods
    base = principal * factor
    annuity = contributions * (factor - 1) / rate
    return base + annuity
```

**What makes this correct:** Explains the financial concept (annuity component), documents semantic meaning of `rate` (per-period decimal, not percentage), and notes the edge case (rate=0).

---

## Type 2: Design Comment

### Before (missing rationale)

```python
class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)
        self._queue = deque()
        self._processing = False

    def emit(self, event_type, data):
        self._queue.append((event_type, data))
        if not self._processing:
            self._drain_queue()
```

### After

```python
class EventBus:
    """In-process event bus with queued dispatch.

    Events are queued rather than dispatched inline to prevent re-entrancy
    issues. If handler A emits event B during processing, B is queued and
    processed after A's handler completes. This avoids stack overflow from
    circular event chains and ensures handlers see consistent state.

    Alternative considered: async dispatch with asyncio.Queue. Rejected
    because most consumers are synchronous and adding async would force
    the entire call chain to be async.
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: deque[tuple[str, Any]] = deque()
        self._processing: bool = False

    def emit(self, event_type: str, data: Any) -> None:
        """Queue an event for dispatch.

        Args:
            event_type: Event name. Handlers registered for this type
                will be called in registration order.
            data: Arbitrary payload passed to handlers.
        """
        self._queue.append((event_type, data))
        if not self._processing:
            self._drain_queue()
```

**What makes this correct:** Explains the queuing design choice, names the problem it solves (re-entrancy), and documents the rejected alternative.

---

## Type 3: Why Comment

### Before (no explanation for non-obvious code)

```python
def parse_csv_record(line: str) -> list[str]:
    fields = line.split(",")
    if len(fields) > 0 and fields[-1].endswith("\r"):
        fields[-1] = fields[-1][:-1]
    return fields
```

### After

```python
def parse_csv_record(line: str) -> list[str]:
    fields = line.split(",")
    # Strip trailing \r because files transferred from Windows retain CRLF
    # line endings even after Python's universal newline mode strips \n.
    # Without this, the last field silently carries a \r that breaks
    # downstream string comparisons.
    if len(fields) > 0 and fields[-1].endswith("\r"):
        fields[-1] = fields[-1][:-1]
    return fields
```

**What makes this correct:** Explains the *reason* (Windows CRLF transfer issue), the *mechanism* (universal newlines strips \n but not \r), and the *consequence* if removed (broken string comparisons).

---

## Type 4: Teacher Comment

### Before (algorithm without context)

```python
def find_closest_points(points: list[tuple[float, float]], k: int) -> list:
    heap = []
    for x, y in points:
        dist = -(x * x + y * y)
        if len(heap) < k:
            heapq.heappush(heap, (dist, (x, y)))
        elif dist > heap[0][0]:
            heapq.heapreplace(heap, (dist, (x, y)))
    return [p for _, p in heap]
```

### After

```python
def find_closest_points(
    points: list[tuple[float, float]], k: int
) -> list[tuple[float, float]]:
    """Return the k points closest to the origin.

    Uses a max-heap of size k for O(n log k) time, which is more
    efficient than sorting all points (O(n log n)) when k << n.

    Args:
        points: 2D points as (x, y) tuples.
        k: Number of closest points to return. Must be <= len(points).

    Returns:
        The k closest points in arbitrary order.
    """
    # Max-heap trick: Python's heapq is a min-heap, so we negate distances
    # to get max-heap behavior. This lets us efficiently evict the farthest
    # point in our k-sized candidate set.
    heap: list[tuple[float, tuple[float, float]]] = []
    for x, y in points:
        dist = -(x * x + y * y)
        if len(heap) < k:
            heapq.heappush(heap, (dist, (x, y)))
        elif dist > heap[0][0]:
            heapq.heapreplace(heap, (dist, (x, y)))
    return [p for _, p in heap]
```

**What makes this correct:** Teaches the max-heap-via-negation trick that a reader unfamiliar with Python's heapq would not know. The docstring adds complexity context (O(n log k) vs O(n log n)).

---

## Type 5: Checklist Comment

### Before (multi-step process without order markers)

```python
def rotate_api_key(service: str) -> str:
    new_key = generate_api_key()
    store_key(service, new_key, status="pending")
    update_service_config(service, new_key)
    health_check(service)
    mark_key_active(service, new_key)
    revoke_old_keys(service, except_key=new_key)
    return new_key
```

### After

```python
def rotate_api_key(service: str) -> str:
    """Rotate the API key for a service with zero-downtime rollover.

    Args:
        service: Service identifier whose key is being rotated.

    Returns:
        The new active API key.
    """
    # 1. Generate new key (does not affect running service)
    new_key = generate_api_key()

    # 2. Store as "pending" - both old and new keys are valid at this point
    store_key(service, new_key, status="pending")

    # 3. Push new key to service config (service now accepts both keys)
    update_service_config(service, new_key)

    # 4. Health check MUST pass before proceeding - if the service can't
    #    use the new key, we abort and the old key remains active
    health_check(service)

    # 5. Mark new key active only after health check confirms it works
    mark_key_active(service, new_key)

    # 6. Revoke old keys LAST - revoking before step 4-5 would cause outage
    revoke_old_keys(service, except_key=new_key)

    return new_key
```

**What makes this correct:** Numbers each step, explains why ordering matters (steps 4-5 before 6), and notes the consequence of misordering (outage).

---

## Type 6: Guide Comment

### Before (long module without navigation)

```python
import os
import json
from dataclasses import dataclass
from enum import Enum

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class Task:
    title: str
    priority: Priority
    done: bool = False

class TaskRepository:
    def __init__(self, path: str):
        self._path = path
    def load(self) -> list[Task]: ...
    def save(self, tasks: list[Task]) -> None: ...

class TaskService:
    def __init__(self, repo: TaskRepository):
        self._repo = repo
    def add(self, title: str, priority: Priority) -> Task: ...
    def complete(self, title: str) -> None: ...
    def list_pending(self) -> list[Task]: ...

class TaskCLI:
    def __init__(self, service: TaskService):
        self._service = service
    def run(self, args: list[str]) -> None: ...
```

### After

```python
"""Task management module with CLI interface.

Provides CRUD operations for tasks with file-based persistence
and a command-line interface.
"""

import os
import json
from dataclasses import dataclass
from enum import Enum

# --- Domain Models ---

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class Task:
    title: str
    priority: Priority
    done: bool = False

# --- Persistence ---

class TaskRepository:
    def __init__(self, path: str):
        self._path = path
    def load(self) -> list[Task]: ...
    def save(self, tasks: list[Task]) -> None: ...

# --- Business Logic ---

class TaskService:
    def __init__(self, repo: TaskRepository):
        self._repo = repo
    def add(self, title: str, priority: Priority) -> Task: ...
    def complete(self, title: str) -> None: ...
    def list_pending(self) -> list[Task]: ...

# --- CLI Interface ---

class TaskCLI:
    def __init__(self, service: TaskService):
        self._service = service
    def run(self, args: list[str]) -> None: ...
```

**What makes this correct:** Consistent `# --- Section ---` format. Sections match the actual code organization. Module docstring added for context.

---

## Fixing Negative Types

### Type 7 Fix: Delete Trivial Comments

```python
# BEFORE
# Initialize the cache
cache = {}

# Get the user from the database
user = db.get_user(user_id)

# Check if user exists
if user is None:
    # Return None
    return None

# AFTER (comments deleted, code is self-explanatory)
cache = {}
user = db.get_user(user_id)
if user is None:
    return None
```

### Type 8 Fix: Resolve or Track Debt

```python
# BEFORE
# TODO: handle edge case
if len(items) > 0:
    process(items)

# AFTER (option A: resolve the debt)
if not items:
    return ProcessResult.empty()
process(items)

# AFTER (option B: track with ticket if can't resolve now)
# TODO(alice): Handle empty items list - currently skips silently [PROJ-892]
if len(items) > 0:
    process(items)
```

### Type 9 Fix: Delete Backup Code

```python
# BEFORE
def process(data):
    # result = old_process(data)
    # if result.status == "error":
    #     result = fallback_process(data)
    return new_process(data)

# AFTER (backup code deleted - git history preserves it)
def process(data):
    return new_process(data)
```
