# Comment Taxonomy Reference

Based on antirez's "Writing system software: code comments" (9 types), adapted for Python.

---

## Type 1: Function Comments

**Purpose:** Describe what a function, class, or module does.

**Python scope:** Docstrings on modules, classes, functions, methods.

**Quality markers:**
- Imperative mood ("Return", "Calculate", not "Returns", "Calculates" for summary line)
- Covers: purpose, args (semantics, not types if hints exist), returns, raises, side effects
- First line stands alone as summary
- Does not duplicate type hints

**Example:**
```python
def retry_with_backoff(func: Callable, max_retries: int = 3) -> Any:
    """Execute a function with exponential backoff on failure.

    Retries on any exception, doubling the wait time between attempts.
    Useful for flaky network calls where transient failures are expected.

    Args:
        func: Callable to execute. Must take no arguments.
        max_retries: Maximum retry attempts before re-raising.

    Returns:
        The return value of func on success.

    Raises:
        Exception: The last exception if all retries are exhausted.
    """
```

**Bad example (placeholder):**
```python
def retry_with_backoff(func, max_retries=3):
    """Retry with backoff."""  # Adds nothing useful
```

---

## Type 2: Design Comments

**Purpose:** Explain architectural decisions and design rationale.

**Python scope:** Module-level docstrings, class-level docstrings, or inline `#` above complex structures.

**Quality markers:**
- Explains *why this design* over alternatives
- References constraints that drove the decision
- May reference external design docs or ADRs

**Example:**
```python
class ConnectionPool:
    """Thread-safe database connection pool.

    Uses a bounded semaphore rather than a queue to manage connections.
    A queue approach was considered but rejected because it doesn't
    provide backpressure when all connections are in use - callers
    would block indefinitely. The semaphore raises after timeout,
    letting callers handle congestion explicitly.
    """
```

**Example (inline):**
```python
# Store sessions in Redis rather than DB to avoid write amplification
# on every request. Accept the trade-off of losing sessions on Redis restart
# since users can re-authenticate cheaply.
session_store = RedisSessionStore(ttl=3600)
```

---

## Type 3: Why Comments

**Purpose:** Explain non-obvious reasoning behind a specific code decision.

**Python scope:** Inline `#` comments, one line above or at end of the relevant line.

**Quality markers:**
- Answers "why?", not "what?"
- Would not be obvious to a competent developer reading the code
- References the constraint, bug, or requirement that caused the decision

**Example:**
```python
# Use <= instead of < because sensor readings are inclusive on both ends,
# per the hardware spec (Section 4.2.1)
if reading <= threshold:
    trigger_alert(reading)
```

```python
# Sleep before retry to avoid overwhelming the rate-limited API.
# 429 responses include Retry-After but we add jitter to prevent
# thundering herd when multiple workers hit the limit simultaneously.
time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 0.5))
```

**Bad example (restates code):**
```python
# Check if reading is less than or equal to threshold
if reading <= threshold:
```

---

## Type 4: Teacher Comments

**Purpose:** Explain domain knowledge, algorithms, or concepts the reader may not know.

**Python scope:** Inline `#` comments, sometimes multi-line blocks above complex code.

**Quality markers:**
- Teaches a concept, not just labels it
- Accurate domain explanation
- Links to external references when applicable (papers, RFCs, specs)

**Example:**
```python
# Levenshtein distance: minimum single-character edits (insert, delete,
# substitute) to transform one string into another. Used here for
# fuzzy matching user input against known command names.
# Reference: https://en.wikipedia.org/wiki/Levenshtein_distance
def fuzzy_match(input_str: str, candidates: list[str]) -> str | None:
```

```python
# Bloom filter: probabilistic set membership test. False positives possible,
# false negatives impossible. We use it as a fast pre-filter before the
# expensive database lookup - if the filter says "not present", we skip
# the DB query entirely.
if not bloom_filter.might_contain(key):
    return None
```

---

## Type 5: Checklist Comments

**Purpose:** Mark steps in a sequence that must not be skipped or reordered.

**Python scope:** Numbered inline `#` comments within a multi-step procedure.

**Quality markers:**
- Steps are numbered
- Order dependency is explicit
- Consequences of skipping/reordering are noted where non-obvious

**Example:**
```python
def deploy_schema_migration(migration: Migration) -> None:
    # 1. Acquire advisory lock to prevent concurrent migrations
    lock = acquire_migration_lock(timeout=30)

    # 2. Validate migration hasn't already been applied (idempotency check)
    if is_already_applied(migration.version):
        release_lock(lock)
        return

    # 3. Apply migration in a transaction
    # MUST be after lock acquisition - concurrent apply causes partial schema
    with db.transaction():
        migration.apply()

    # 4. Record migration version BEFORE releasing lock
    # If we release first, another process could re-apply
    record_applied(migration.version)

    # 5. Release lock last
    release_lock(lock)
```

---

## Type 6: Guide Comments

**Purpose:** Help readers navigate long files by marking logical sections.

**Python scope:** `#` section dividers in long modules or complex functions.

**Quality markers:**
- Consistent formatting throughout file
- Matches actual code sections (not outdated)
- Used only when file is long enough to warrant navigation (>100 lines typically)

**Example:**
```python
# --- Configuration ---

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BATCH_SIZE = 100

# --- Data Models ---

@dataclass
class Task:
    id: str
    status: TaskStatus
    created_at: datetime

# --- Repository Layer ---

class TaskRepository:
    ...

# --- Service Layer ---

class TaskService:
    ...
```

---

## Type 7: Trivial Comments (NEGATIVE)

**Purpose:** None. Restates what the code already says.

**Detection heuristics:**
- Comment is a direct English translation of the code
- Removing the comment loses zero information
- Comment uses the same words as the code identifiers

**Examples to delete:**
```python
# Initialize the counter
counter = 0

# Get the user
user = get_user(user_id)

# Return the result
return result

# Loop through items
for item in items:

# Check if valid
if is_valid(data):
```

**Fix:** Delete. If the code needs explanation, rename variables or extract functions instead.

---

## Type 8: Debt Comments (NEGATIVE)

**Purpose:** Mark known issues. Not inherently bad, but problematic when they accumulate.

**Detection heuristics:**
- Contains `TODO`, `FIXME`, `HACK`, `XXX`, `WORKAROUND`
- References a ticket number (good) or is vague (bad)
- Has been in codebase for >6 months without resolution

**Examples:**
```python
# TODO: This should use batch processing for performance  (vague, no owner)
# FIXME: Race condition when multiple workers process same job  (critical, no ticket)
# HACK: Workaround for upstream bug in requests 2.28  (may be resolved by now)
# TODO(alice): Migrate to v2 API before Q3 deprecation [PROJ-1234]  (good: owner + ticket)
```

**Fix strategies:**
- If actionable: Create issue/ticket, add reference to comment, set deadline
- If vague: Clarify the problem and required fix, or delete if no longer relevant
- If stale (>6 months): Investigate if still relevant. Delete or resolve

---

## Type 9: Backup Comments (NEGATIVE)

**Purpose:** None. Preserves old code "just in case."

**Detection heuristics:**
- Commented-out code blocks (not example code in docstrings)
- `# old version:`, `# was:`, `# previously:`
- Entire functions or class methods commented out

**Examples to delete:**
```python
# def process_v1(data):
#     return data.strip().lower()

# result = expensive_computation(data)
# if result > threshold:
#     notify_admin(result)
```

**Fix:** Delete unconditionally. Git history preserves all previous versions. If the code might be needed again, the commit message or a type 8 (debt) comment with a ticket reference is the right way to track it.

---

## Quick Reference Table

| Type | Name | Python Form | Trigger | Quality Test |
|------|------|-------------|---------|-------------|
| 1 | Function | Docstring | New/missing docstring | Covers purpose, args, returns? |
| 2 | Design | Docstring / `#` | Architecture decision | Explains *why this approach*? |
| 3 | Why | Inline `#` | Non-obvious code | Answers "why?", not "what?"? |
| 4 | Teacher | Inline `#` | Domain/algorithm concept | Teaches something new? |
| 5 | Checklist | Numbered `#` | Multi-step procedure | Steps numbered, order enforced? |
| 6 | Guide | Section `#` | Long file (>100 LOC) | Matches actual sections? |
| 7 | Trivial | Any | Restates code | **DELETE** |
| 8 | Debt | `TODO`/`FIXME` | Known issue | Has ticket + owner? |
| 9 | Backup | Commented code | Old code preserved | **DELETE** (git has history) |
