# Audit Mode Examples

Two complete audit reports demonstrating the audit workflow output.

---

## Example 1: Utility Module with Mixed-Quality Comments

### Input Code

```python
"""Utility functions."""

import hashlib
import time
import os

# Constants
MAX_RETRIES = 3
TIMEOUT = 30

def hash_password(password):
    # Hash the password
    salt = os.urandom(16)
    # Use SHA-256
    hashed = hashlib.sha256(salt + password.encode()).hexdigest()
    return salt.hex() + ":" + hashed

def verify_password(password, stored):
    salt_hex, expected_hash = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.sha256(salt + password.encode()).hexdigest()
    return hashed == expected_hash

# def hash_password_v1(password):
#     return hashlib.md5(password.encode()).hexdigest()

def retry(func, max_retries=MAX_RETRIES):
    # Retry the function
    for i in range(max_retries):
        try:
            return func()
        except Exception:
            # TODO: add logging
            time.sleep(1)
    raise RuntimeError("Max retries exceeded")

# Helper function
def format_duration(seconds):
    # Convert seconds to human readable format
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
```

### Audit Report

```
## Comment Audit Report

### Summary
- **Files analyzed:** 1
- **Total comments:** 9 (docstrings: 1, inline: 8)
- **Comment density:** 21 comments per 100 LOC
- **Type distribution:** Type 1: 1, Type 6: 1, Type 7: 5, Type 8: 1, Type 9: 1
- **Quality score:** 3/10

### Critical Gaps
- [ ] utils.py:11 - `hash_password()` - Missing Type 1 (Function) docstring - SECURITY: password hashing function must document algorithm, salt handling, and limitations
- [ ] utils.py:18 - `verify_password()` - Missing Type 1 (Function) docstring - SECURITY: must document expected format and timing safety
- [ ] utils.py:25 - `retry()` - Missing Type 1 (Function) docstring - Must document retry behavior, exceptions, and backoff strategy
- [ ] utils.py:35 - `format_duration()` - Missing Type 1 (Function) docstring - Public function without documentation
- [ ] utils.py:11 - `hash_password()` - Missing Type 3 (Why) comment - Why SHA-256 with simple salt? No key stretching (bcrypt/scrypt/argon2)?

### Issues Found

#### Negative Comments (fix or remove)
- utils.py:12 - Type 7 (Trivial) - "# Hash the password" - Action: delete (restates function name)
- utils.py:14 - Type 7 (Trivial) - "# Use SHA-256" - Action: delete (code shows hashlib.sha256)
- utils.py:23-24 - Type 9 (Backup) - Commented-out `hash_password_v1` using MD5 - Action: delete (git history preserves it)
- utils.py:27 - Type 7 (Trivial) - "# Retry the function" - Action: delete (restates function name)
- utils.py:31 - Type 8 (Debt) - "# TODO: add logging" - Action: resolve or create ticket (no owner, no ticket reference, vague)
- utils.py:34 - Type 7 (Trivial) - "# Helper function" - Action: delete (adds no information)
- utils.py:36 - Type 7 (Trivial) - "# Convert seconds to human readable format" - Action: delete (obvious from function name and code)

#### Quality Issues
- utils.py:1 - Type 1 (Module docstring) - "Utility functions." - Quality: poor. Too vague, does not describe what utilities or for what purpose
- utils.py:8 - Type 6 (Guide) - "# Constants" - Quality: adequate but section is only 2 lines, guide comment is unnecessary at this scale

### Coverage Metrics
| Scope | With Docstring | Without | Coverage |
|-------|---------------|---------|----------|
| Modules | 1 | 0 | 100% |
| Classes | 0 | 0 | N/A |
| Public functions | 0 | 4 | 0% |
| Public methods | 0 | 0 | N/A |

### Recommendations
1. **Priority 1:** Add Type 1 docstrings to all 4 public functions - 0% coverage is critical
2. **Priority 2:** Add Type 3 (Why) comment to `hash_password` explaining SHA-256 choice and acknowledging lack of key stretching (security concern)
3. **Priority 3:** Delete 5 trivial comments and 1 backup code block - they add noise
4. **Priority 4:** Resolve or ticket-track the TODO in `retry()`, add owner and reference
5. **Priority 5:** Improve module docstring - describe the module's purpose and scope

### Comment Style
- **Detected style:** None (no function docstrings exist)
- **Consistency:** N/A
- **Recommendation:** Adopt Google style for new docstrings
```

---

## Example 2: Class with Complex Method and Missing Documentation

### Input Code

```python
class OrderProcessor:
    PRIORITY_MULTIPLIER = 1.5
    MAX_BATCH = 100

    def __init__(self, db, payment_gateway, notifier):
        self.db = db
        self.gateway = payment_gateway
        self.notifier = notifier
        self._cache = {}

    def process_batch(self, order_ids):
        results = []
        failed = []
        for oid in order_ids[:self.MAX_BATCH]:
            try:
                order = self.db.get_order(oid)
                if not order:
                    failed.append((oid, "not found"))
                    continue

                if order.status != "pending":
                    continue

                if order.is_priority:
                    order.total *= self.PRIORITY_MULTIPLIER

                if order.total > 10000:
                    if not order.customer.is_verified:
                        order.status = "review"
                        self.db.save(order)
                        self.notifier.alert_compliance(order)
                        failed.append((oid, "compliance review"))
                        continue

                # Process payment
                result = self.gateway.charge(
                    order.customer.payment_method,
                    order.total,
                    idempotency_key=f"order-{oid}"
                )

                if result.success:
                    order.status = "completed"
                    order.payment_id = result.payment_id
                    self.db.save(order)
                    self.notifier.send_confirmation(order)
                    results.append(oid)
                else:
                    order.status = "payment_failed"
                    order.error = result.error
                    self.db.save(order)
                    failed.append((oid, result.error))

            except Exception as e:
                failed.append((oid, str(e)))

        return {"processed": results, "failed": failed}

    def get_order_summary(self, oid):
        if oid in self._cache:
            return self._cache[oid]
        order = self.db.get_order(oid)
        if not order:
            return None
        summary = {
            "id": order.id,
            "status": order.status,
            "total": order.total,
            "customer": order.customer.name
        }
        self._cache[oid] = summary
        return summary
```

### Audit Report

```
## Comment Audit Report

### Summary
- **Files analyzed:** 1
- **Total comments:** 1 (docstrings: 0, inline: 1)
- **Comment density:** 1.4 comments per 100 LOC
- **Type distribution:** Type 7: 1
- **Quality score:** 1/10

### Critical Gaps
- [ ] order_processor.py:1 - `OrderProcessor` - Missing Type 1 (Class) docstring - Core domain class with no documentation
- [ ] order_processor.py:2-3 - `PRIORITY_MULTIPLIER`, `MAX_BATCH` - Missing Type 3 (Why) - Why 1.5x? Why 100? Business rules undocumented
- [ ] order_processor.py:12 - `process_batch()` - Missing Type 1 (Function) docstring - Complex 50-line method with multiple code paths, zero documentation
- [ ] order_processor.py:12 - `process_batch()` - Missing Type 5 (Checklist) comments - Multi-step order processing with implicit ordering requirements
- [ ] order_processor.py:27-33 - Compliance check block - Missing Type 3 (Why) - Why is 10000 the threshold? Why must customer be verified? Regulatory requirement?
- [ ] order_processor.py:24 - Priority multiplier application - Missing Type 3 (Why) - Why multiply total? Business rule for priority surcharge?
- [ ] order_processor.py:55 - `get_order_summary()` - Missing Type 1 (Function) docstring - Public method without documentation
- [ ] order_processor.py:5 - `__init__()` - Missing Type 2 (Design) - What are the dependencies? Why cache?

### Issues Found

#### Negative Comments (fix or remove)
- order_processor.py:35 - Type 7 (Trivial) - "# Process payment" - Action: delete (next line is `self.gateway.charge()`, comment adds nothing)

#### Quality Issues
- No positive-type comments exist in the entire file

### Coverage Metrics
| Scope | With Docstring | Without | Coverage |
|-------|---------------|---------|----------|
| Modules | 0 | 1 | 0% |
| Classes | 0 | 1 | 0% |
| Public functions | 0 | 0 | N/A |
| Public methods | 0 | 2 | 0% |

### Recommendations
1. **Priority 1:** Add Type 1 docstring to `OrderProcessor` class - document purpose, dependencies, and usage
2. **Priority 2:** Add Type 1 docstring to `process_batch()` - document return format, failure modes, and side effects (sends notifications, updates DB)
3. **Priority 3:** Add Type 3 (Why) comments to the compliance check (line 27) - document the 10000 threshold source (regulation? policy?) and verification requirement
4. **Priority 4:** Add Type 3 (Why) for `PRIORITY_MULTIPLIER = 1.5` and `MAX_BATCH = 100` - these are business rules that need context
5. **Priority 5:** Add Type 5 (Checklist) comments to `process_batch()` marking the processing stages: validate → priority adjust → compliance check → payment → status update
6. **Priority 6:** Delete the trivial "# Process payment" comment
7. **Priority 7:** Add Type 1 docstring to `get_order_summary()` including cache behavior documentation

### Comment Style
- **Detected style:** None (no docstrings exist)
- **Consistency:** N/A
- **Recommendation:** Adopt Google style for new docstrings

### Severity Assessment
- **Critical (blocks release):** `process_batch()` handles payments and compliance with zero documentation. New developer could misunderstand the compliance flow and introduce financial risk.
- **High:** Business rule constants (1.5x multiplier, 10000 threshold, 100 batch limit) are undocumented magic numbers with no traceability to requirements.
- **Medium:** Cache behavior in `get_order_summary()` undocumented - caller doesn't know results may be stale.
```
