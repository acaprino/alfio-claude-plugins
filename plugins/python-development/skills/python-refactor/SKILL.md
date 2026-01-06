---
name: python-refactor
description: Systematic code refactoring skill that transforms complex, hard-to-understand code into clear, well-documented, maintainable code while preserving correctness. Use when users request "readable", "maintainable", or "clean" code, during code reviews flagging comprehension issues, for legacy code modernization, or in educational/onboarding contexts. Applies structured refactoring patterns with validation.
---

# Python Refactor

## Purpose

Transform complex, hard-to-understand code into clear, well-documented, maintainable code while preserving correctness. This skill guides systematic refactoring that prioritizes human comprehension without sacrificing correctness or reasonable performance.

## When to Invoke

Invoke this skill when:
- User explicitly requests "human", "readable", "maintainable", "clean", or "refactor" code improvements
- Code review processes flag comprehension or maintainability issues
- Working with legacy code that needs modernization
- Preparing code for team onboarding or educational contexts
- Code complexity metrics exceed reasonable thresholds
- Functions or modules are difficult to understand or modify
- **🚨 RED FLAG: You see any of these spaghetti code indicators:**
  - File >500 lines with scattered functions and global state
  - Multiple `global` statements throughout the code
  - Functions with hard-coded dependencies (no dependency injection)
  - No clear module/class organization
  - Dict/list manipulation instead of proper domain objects
  - Configuration mixed with business logic

Do NOT invoke this skill when:
- Code is performance-critical and profiling shows optimization is needed first
- Code is scheduled for deletion or replacement
- External dependencies require upstream contributions instead
- User explicitly requests performance optimization over readability

## Core Principles

Follow these principles in priority order:

1. **CLASS-BASED ARCHITECTURE IS MANDATORY** - **ALWAYS prefer proper class-based OOP architecture over long messy spaghetti code scripts.** Transform any procedural "script-like" code into well-structured OOP with proper classes, modules, and interfaces. This is NON-NEGOTIABLE.
   - ❌ **NEVER accept**: Globals, scattered functions, 1000+ line scripts, no clear structure
   - ✅ **ALWAYS create**: Classes with clear responsibilities, dependency injection, proper modules
2. **Clarity over cleverness** - Explicit, obvious code beats implicit, clever code
3. **Preserve correctness** - All tests must pass; behavior must remain identical
4. **Single Responsibility** - Each class and function should do one thing well (SOLID principles)
5. **Self-documenting structure** - Code structure tells what, comments explain why
6. **Progressive disclosure** - Reveal complexity in layers, not all at once
7. **Reasonable performance** - Never sacrifice >2x performance without explicit approval

## Key Constraints

ALWAYS observe these constraints:

- **SAFETY BY DESIGN** - Use mandatory migration checklists for destructive changes. Create new structure → Search all usages → Migrate all → Verify → Only then remove old code. NEVER remove code before 100% migration verified.
- **STATIC ANALYSIS FIRST** - Run `flake8 --select=F821,E0602` before tests to catch NameErrors immediately
- **OOP-ORIENTED ARCHITECTURE** - Transform script-like code into proper OOP with classes, modules, and clear boundaries. Avoid global state, scattered functions, and spaghetti code
- **PRESERVE BEHAVIOR** - All existing tests must pass after refactoring
- **NO PERFORMANCE REGRESSION** - Never degrade performance >2x without explicit user approval
- **NO API CHANGES** - Public APIs remain unchanged unless explicitly requested and documented
- **NO OVER-ENGINEERING** - Simple code stays simple; don't add unnecessary abstraction (but DO structure code properly)
- **NO MAGIC** - No framework magic, no metaprogramming unless absolutely necessary
- **VALIDATE CONTINUOUSLY** - Run static analysis + tests after each logical change

## ⛔ REGRESSION PREVENTION (MANDATORY)

**IL REFACTORING NON DEVE MAI INTRODURRE REGRESSIONI TECNICHE, LOGICHE O FUNZIONALI.**

Prima di qualsiasi refactoring, leggi e applica `references/REGRESSION_PREVENTION.md`.

### Quick Safety Checklist

**PRIMA di ogni sessione di refactoring:**
```
□ Test suite passa al 100%?
□ Coverage >= 80% su codice target? (se no → scrivi test PRIMA)
□ Golden outputs catturati per edge cases critici?
□ Static analysis baseline salvata?
```

**DOPO ogni micro-cambiamento (non alla fine, OGNI SINGOLO!):**
```
□ flake8 --select=F821,E999 → 0 errori?
□ pytest -x → tutti passano?
□ Comportamento invariato? (spot check 1 edge case)
```

**Se QUALSIASI check fallisce:**
```
→ STOP → REVERT → ANALYZE → FIX APPROACH → RETRY
```

### Le regole fondamentali:
1. **Test coverage >= 80%** sulle funzioni target, altrimenti scrivi test PRIMA
2. **Golden outputs catturati** per edge cases critici prima di toccare il codice
3. **Static analysis PRIMA dei test** dopo ogni micro-change: `flake8 --select=F821,E999`
4. **Rollback immediato** se qualsiasi test fallisce - non procedere mai

```
⛔ QUALSIASI REGRESSIONE = FALLIMENTO TOTALE DEL REFACTORING ⛔
```

## Refactoring Workflow

Execute refactoring in four phases with validation at each step.

### Phase 1: Analysis

Before making any changes, analyze the code comprehensively:

**CRITICAL FIRST CHECK - Script vs OOP Architecture:**

Ask yourself: "Is this code structured as a proper OOP system or is it a messy script?"

```python
# ❌ UNACCEPTABLE - Script-like spaghetti code
# 1500-line file with:
users_cache = {}  # Global state
API_URL = "https://..."  # Global config

def fetch_user(user_id):  # Scattered function
    global users_cache
    # ...

def validate_user(data):  # Another scattered function
    # ...

def save_to_db(data):  # Yet another scattered function
    # Hard-coded dependencies
    # ...

# 50+ more scattered functions...
```

```python
# ✅ REQUIRED - Proper class-based architecture
# Organized modules:
# project/
#   models/user.py
#   repositories/user_repository.py
#   services/user_service.py
#   clients/api_client.py

from dataclasses import dataclass
from typing import Protocol

@dataclass
class User:
    id: int
    email: str

class UserRepository:
    def __init__(self, api_client: APIClient):
        self._api_client = api_client
        self._cache: dict[int, User] = {}

    def get_by_id(self, user_id: int) -> Optional[User]:
        # Encapsulated state, clear responsibility
        pass

class UserService:
    def __init__(self, user_repo: UserRepository, db_repo: DatabaseRepository):
        self._user_repo = user_repo
        self._db_repo = db_repo

    def process_user(self, user_id: int):
        # Dependency injection, testable, clear
        pass
```

**If you find script-like code → Transformation to OOP is MANDATORY, not optional!**

1. **Read the entire codebase section** being refactored to understand context
2. **Identify readability issues** using the anti-patterns reference (see `references/anti-patterns.md`):
   - **CRITICAL**: Check for script-like/procedural code (anti-pattern #1) - global state, scattered functions, no clear structure
   - **CRITICAL**: Check for God Objects/Classes (anti-pattern #2) - classes doing too much
   - Complex nested conditionals, long functions, magic numbers, cryptic names, etc.
3. **Assess OOP architecture** (see `references/oop_principles.md`):
   - Is code organized in proper classes and modules?
   - Is there global state that should be encapsulated?
   - Are responsibilities properly separated (models, repositories, services)?
   - Are SOLID principles followed?
   - Is dependency injection used instead of hard-coded dependencies?
4. **Measure current metrics**:
   - Cyclomatic complexity per function (use `scripts/measure_complexity.py`)
   - Function length (lines of code)
   - Documentation coverage (docstrings, type hints)
   - Nesting depth
5. **Run flake8 analysis** for comprehensive code quality assessment:
   ```bash
   python scripts/analyze_with_flake8.py <target> \
       --output before_flake8.json \
       --html before_flake8.html
   ```
   This provides:
   - Style violations (PEP 8)
   - Potential bugs (Bugbear plugin)
   - Complexity issues (McCabe, Cognitive)
   - Missing docstrings (pydocstyle)
   - Type annotation coverage
   - Code simplification opportunities
   - Naming convention violations
5. **Check test coverage** - Identify gaps that need filling before refactoring
6. **Document findings** using the analysis template (see `assets/templates/analysis_template.md`)

**Output:** Prioritized list of issues by impact and risk, including flake8 report.

### Phase 2: Planning

Plan the refactoring approach systematically with **safety-by-design**:

1. **Identify changes by type:**
   - **Non-destructive:** Renames, documentation, type hints → Low risk
   - **Destructive:** Removing globals, deleting functions, replacing APIs → High risk

2. **For DESTRUCTIVE changes - CREATE MIGRATION PLAN (MANDATORY):**
   ```bash
   # For each element to be removed, search for ALL usages
   grep -rn "<element_name>" --include="*.py" > migration_plan_<element>.txt
   grep -rn "<element_name>\[" --include="*.py" >> migration_plan_<element>.txt
   grep -rn "<element_name>\." --include="*.py" >> migration_plan_<element>.txt
   ```

   Document findings:
   ```markdown
   ## Removal Plan: <element_name>

   ### Total Usages Found: X
   ### Files Affected: Y
   ### Estimated Migration Effort: Z hours

   ### Detailed Usage List:
   - file.py:123 - function_name() - [usage type]
   - file.py:456 - another_function() - [usage type]
   ...

   ### Migration Strategy:
   1. Create replacement structure
   2. Migrate usages in this order: [list]
   3. Verify with static analysis
   4. Remove old code

   ### Risk Level: [High/Medium/Low]
   ```

   **PROHIBITION:** If you cannot create this migration plan with complete usage accounting,
   you CANNOT proceed with the destructive change. Defer it or choose safer approach.

3. **Risk assessment** for each proposed change (Low/Medium/High)
4. **Dependency identification** - What else depends on this code?
5. **Test strategy** - What tests are needed? What might break?
6. **Change ordering** - Sequence changes from safest to riskiest
7. **Expected outcomes** - Document what metrics should improve and by how much

**Output:** Refactoring plan with:
- Sequenced changes with risk levels
- Complete migration plans for ALL destructive changes (with usage counts)
- Test strategy
- Fallback/rollback plan

### Phase 3: Execution

Apply refactoring patterns using **safety-by-design workflow** that prevents incomplete migration:

#### Safe Refactoring Workflow (MANDATORY ORDER)

**For NON-DESTRUCTIVE changes (safe to do anytime):**
1. Rename variables/functions for clarity
2. Extract magic numbers/strings to named constants
3. Add/improve documentation and type hints
4. Add guard clauses to reduce nesting

**For DESTRUCTIVE changes (removing/replacing code) - STRICT PROTOCOL:**

This protocol makes incomplete migration **structurally impossible**:

**Step 1: CREATE new structure (no removal yet)**
- Write new classes/functions/services
- Add tests for new structure
- DO NOT remove or modify old code yet

**Step 2: SEARCH comprehensively for ALL usages**
```bash
# Example: Removing global variable "sse_connections"

# Search for exact name
grep -rn "sse_connections" --include="*.py" > migration_checklist.txt

# Search for common access patterns
grep -rn "sse_connections\[" --include="*.py" >> migration_checklist.txt
grep -rn "sse_connections\." --include="*.py" >> migration_checklist.txt
grep -rn "_get_sse_connections" --include="*.py" >> migration_checklist.txt

# Review ALL results - every line must be accounted for
```

**Step 3: CREATE migration checklist**
```markdown
## Migration: sse_connections → SSEManagerService._connections

### Found Usages (from grep):
- [ ] rest_api_channel_api.py:456 - broadcast_sse_event() - helper function
- [ ] rest_api_channel_api.py:1234 - cleanup_sse_connections() - helper function
- [ ] rest_api_channel_api.py:1916 - stream_positions() route - DIRECT ACCESS
- [ ] rest_api_channel_api.py:1945 - stream_signals() route - DIRECT ACCESS
- [ ] rest_api_channel_api.py:1978 - stream_agents() route - DIRECT ACCESS
- [ ] rest_api_channel_api.py:2001 - stream_orders() route - DIRECT ACCESS

Total: 6 locations requiring migration

### Migration Status: 0/6 complete - CANNOT REMOVE YET
```

**Step 4: MIGRATE one usage at a time**
- Update ONE usage to use new structure
- Check off in migration checklist
- Run static analysis: `flake8 <file> --select=F821,E0602`
- Run tests
- Commit with message: "refactor: migrate broadcast_sse_event to SSEManagerService (1/6)"

**Step 5: VERIFY complete migration**
- Checklist shows 6/6 complete
- Re-run original grep searches - should find ZERO matches (except in new code)
- Run static analysis one final time before removal

**Step 6: REMOVE old code (ONLY after 100% migration verified)**
- Comment out old code first (safety net)
- Run static analysis: `flake8 <file> --select=F821,E0602` - MUST show zero errors
- Run full test suite - MUST pass 100%
- If both pass, permanently delete commented code
- Commit with message: "refactor: remove obsolete sse_connections global (migration complete)"

#### Execution Rules

1. **NEVER skip the migration checklist** - Attempting to remove code without a verified checklist is PROHIBITED
2. **Run static analysis BEFORE tests** - Catch NameErrors immediately, don't wait for runtime
3. **One pattern at a time** - Never mix multiple refactoring patterns in one change
4. **Atomic commits** - Each migration step gets its own commit
5. **Stop on ANY error** - Static analysis errors OR test failures require immediate fix/revert

**Refactoring order (MANDATORY sequence):**

1. **FIRST: Transform script-like code to proper OOP architecture** (NON-NEGOTIABLE if code is procedural)
   - This is NOT optional - spaghetti code MUST be restructured
   - Identify ALL global state and encapsulate in classes
   - Group ALL scattered functions into proper classes (repositories, services, managers)
   - Create proper domain models (dataclasses, enums)
   - Apply dependency injection everywhere
   - Organize into proper modules with clear boundaries
   - See `references/examples/script_to_oop_transformation.md` for complete guide

2. Rename variables/functions for clarity (within the new OOP structure)

3. Extract magic numbers/strings to named constants (as class constants or enums)

4. Add/improve documentation and type hints

5. Extract methods to reduce function length

6. Simplify conditionals with guard clauses

7. Reduce nesting depth

8. Final review: Ensure separation of concerns is clean (should be done in step 1)

**Output:** Refactored code passing all tests with clear commit history.

### Phase 4: Validation

Validate improvements objectively:

1. **Run static analysis FIRST** (catch errors before tests):
   ```bash
   # Check for undefined names/variables (NameError prevention)
   flake8 <file> --select=F821,E0602

   # Check for unused imports (cleanup verification)
   flake8 <file> --select=F401

   # Full quality check
   flake8 <file>
   ```
   **MANDATORY:** Zero F821 (undefined name) and E0602 (undefined variable) errors required
2. **Run full test suite** - 100% pass rate required
3. **Validate OOP architecture improvements**:
   - Confirm global state has been eliminated or properly encapsulated
   - Verify code is organized in proper modules/classes
   - Check that responsibilities are properly separated
   - Ensure dependency injection is used where appropriate
   - Validate against SOLID principles (see `references/oop_principles.md`)
3. **Compare before/after metrics** using `scripts/measure_complexity.py`
4. **Run flake8 analysis again** to measure code quality improvements:
   ```bash
   python scripts/analyze_with_flake8.py <target> \
       --output after_flake8.json \
       --html after_flake8.html
   ```
5. **Compare flake8 reports** to quantify improvements:
   ```bash
   python scripts/compare_flake8_reports.py \
       before_flake8.json \
       after_flake8.json \
       --html flake8_comparison.html
   ```
   Validates:
   - Total issue reduction
   - Severity-level improvements (high/medium/low)
   - Category improvements (bugs, complexity, style, docs)
   - Fixed vs new issues
   - Code quality trend
6. **Performance regression check** - Run `scripts/benchmark_changes.py` for hot paths
7. **Generate summary report** using format from `assets/templates/summary_template.md`
8. **Flag for human review** if:
   - Performance degraded >10%
   - Public API signatures changed
   - Test coverage decreased
   - Significant architectural changes were made
   - Flake8 issues increased (regression)

**Output:** Comprehensive validation report with:
- Test results
- Complexity metrics comparison
- Flake8 before/after comparison
- Performance benchmarks
- Overall quality improvement summary

## Refactoring Patterns

Apply these patterns systematically. Each pattern is documented in detail in `references/patterns.md`.

### Complexity Reduction Patterns

**Guard Clauses** - Replace nested conditionals with early returns:
```python
# Before
def process(data):
    if data:
        if data.is_valid():
            if data.has_permission():
                return data.process()
    return None

# After
def process(data):
    if not data:
        return None
    if not data.is_valid():
        return None
    if not data.has_permission():
        return None
    return data.process()
```

**Extract Method** - Split large functions into focused units:
```python
# Before: 50-line function doing validation, transformation, and storage

# After: 3 focused functions
def validate_input(data): ...
def transform_data(data): ...
def store_result(data): ...
```

**Replace Complex Conditionals** - Use named boolean methods:
```python
# Before
if user.age >= 18 and user.verified and not user.banned:
    ...

# After
def can_access_feature(user):
    return user.age >= 18 and user.verified and not user.banned

if can_access_feature(user):
    ...
```

### Cognitive Complexity Reduction Patterns

See `references/cognitive_complexity_guide.md` for complete details on calculation rules and patterns.

**Dictionary Dispatch** - Eliminate if-elif chains:
```python
# BEFORE: Cognitive Complexity = 8
def process(action, data):
    if action == "create":    # +1
        return create(data)
    elif action == "update":  # +1
        return update(data)
    elif action == "delete":  # +1
        return delete(data)
    # ... altri 5 elif ...
    else:                     # +1
        raise ValueError(f"Unknown: {action}")

# AFTER: Cognitive Complexity = 1
HANDLERS = {
    "create": create,
    "update": update,
    "delete": delete,
}

def process(action, data):
    handler = HANDLERS.get(action)
    if handler is None:       # +1 unico branch
        raise ValueError(f"Unknown: {action}")
    return handler(data)
```

**Match Statement** (Python 3.10+) - Switch conta UNA VOLTA:
```python
# BEFORE: Cognitive Complexity = 4
def get_status_message(status):
    if status == "pending":      # +1
        return "In attesa"
    elif status == "approved":   # +1
        return "Approvato"
    elif status == "rejected":   # +1
        return "Rifiutato"
    else:                        # +1
        return "Sconosciuto"

# AFTER: Cognitive Complexity = 1
def get_status_message(status):
    match status:                # +1 totale!
        case "pending":
            return "In attesa"
        case "approved":
            return "Approvato"
        case "rejected":
            return "Rifiutato"
        case _:
            return "Sconosciuto"
```

**Extract Method** - Resetta il nesting counter (pattern più potente!):
```python
# BEFORE: Cognitive Complexity = 6
def process_items(items):
    for item in items:        # +1, nesting +1
        if item.valid:        # +2 (1 + nesting)
            if item.ready:    # +3 (1 + 2×nesting)
                handle(item)

# AFTER: Cognitive Complexity = 3 totale
def process_items(items):
    for item in items:        # +1
        process_item(item)

def process_item(item):       # Nesting RESETTATO a 0!
    if not item.valid:        # +1 (no nesting penalty)
        return
    if not item.ready:        # +1 (no nesting penalty)
        return
    handle(item)
```

**Named Boolean Conditions** - Chiarisce condizioni complesse:
```python
# BEFORE: Cognitive Complexity = 3 (cambio operatore and→or)
if user.active and user.verified or user.is_admin and not user.banned:
    grant_access()

# AFTER: Cognitive Complexity = 1
is_regular_user_ok = user.active and user.verified
is_admin_ok = user.is_admin and not user.banned
if is_regular_user_ok or is_admin_ok:
    grant_access()
```

**Reduce Nesting** - Maximum 3 levels deep:
```python
# Before: 5 levels of nesting

# After: Extract inner logic to helper functions
```

### Naming Improvement Patterns

Apply these naming conventions consistently:

**Variables:**
- Descriptive names (no `x`, `tmp`, `data` unless trivial scope)
- Booleans: `is_active`, `has_permission`, `can_edit`, `should_retry`
- Collections: plural nouns (`users`, `transactions`, `events`)

**Functions:**
- Verb + object pattern (`calculate_total`, `validate_email`, `fetch_user`)
- Boolean queries: `is_valid()`, `has_items()`, `can_proceed()`

**Constants:**
- `UPPERCASE_WITH_UNDERSCORES`
- Magic numbers → `MAX_RETRY_COUNT = 3`
- Magic strings → `DEFAULT_ENCODING = 'utf-8'`

**Classes:**
- PascalCase nouns (`UserAccount`, `PaymentProcessor`)

### Documentation Patterns

**Function Docstrings** - Document purpose, not implementation:
```python
def calculate_discount(price: float, user_tier: str) -> float:
    """Calculate discount amount based on user tier.

    Args:
        price: Original price before discount
        user_tier: User membership tier ('bronze', 'silver', 'gold')

    Returns:
        Discount amount to subtract from price

    Raises:
        ValueError: If user_tier is not recognized
    """
```

**Module Documentation** - Purpose and key dependencies:
```python
"""User authentication and authorization module.

This module handles user login, session management, and permission
checking. Depends on the database module for user persistence and
the crypto module for password hashing.
"""
```

**Inline Comments** - Only for non-obvious "why":
```python
# Use exponential backoff to avoid overwhelming the API during outages
time.sleep(2 ** retry_count)
```

**Type Hints** - All public APIs and complex internals:
```python
from typing import List, Optional, Dict

def process_users(
    users: List[User],
    filters: Optional[Dict[str, Any]] = None
) -> List[ProcessedUser]:
    ...
```

### Structure Improvement Patterns

**Extract Nested Logic:**
```python
# Before: nested helper logic inline
def main_function():
    data = fetch_data()
    # 10 lines of transformation logic
    result = transformed_data
    return result

# After: extracted to helper
def main_function():
    data = fetch_data()
    result = transform_data(data)
    return result

def transform_data(data):
    # 10 lines of transformation logic
    return transformed_data
```

**Group Related Functionality:**
```python
# Before: scattered validation logic

# After: grouped in validation module or class
class UserValidator:
    def validate_email(self, email): ...
    def validate_age(self, age): ...
    def validate_permissions(self, user): ...
```

**Separate Concerns:**
```python
# Before: mixed data fetching, business logic, and presentation

# After:
def fetch_user_data(user_id): ...        # Data layer
def calculate_user_metrics(data): ...    # Business logic
def format_user_display(metrics): ...    # Presentation
```

**Consistent Abstraction Levels:**
```python
# Before: mixing high-level and low-level operations
def process_order():
    validate_order()
    # Low-level: manual SQL query here
    # High-level: call payment service

# After: consistent abstraction level
def process_order():
    validate_order()
    save_order_to_database()
    charge_payment()
```

### OOP Transformation Patterns

Transform script-like "spaghetti code" into well-structured OOP architecture. See `references/examples/script_to_oop_transformation.md` for complete example.

**Encapsulate Global State in Classes:**
```python
# Before: Script-like with global state
users_cache = {}  # Global!
API_URL = "https://api.example.com"

def fetch_user(user_id):
    global users_cache
    # ...

# After: OOP with encapsulation
class UserRepository:
    def __init__(self, api_client: APIClient):
        self._api_client = api_client
        self._cache: dict[int, User] = {}

    def get_by_id(self, user_id: int) -> Optional[User]:
        # Encapsulated state
        pass
```

**Group Related Functions into Classes:**
```python
# Before: Scattered functions
def fetch_user(user_id): pass
def validate_user(user_data): pass
def save_user(user_data): pass

# After: Organized in classes by responsibility
class UserRepository:
    def get_by_id(self, user_id): pass

class UserValidator:
    def is_valid(self, user): pass

class DatabaseRepository:
    def save_user(self, user): pass
```

**Create Domain Models:**
```python
# Before: Using primitives and dicts
def process_user(user_id, email, status):
    user_dict = {'id': user_id, 'email': email, 'status': status}
    # ...

# After: Rich domain models
from dataclasses import dataclass
from enum import Enum

class UserStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

@dataclass
class User:
    id: int
    email: str
    status: UserStatus

    def is_valid(self) -> bool:
        return '@' in self.email and self.status == UserStatus.ACTIVE
```

**Apply Dependency Injection:**
```python
# Before: Hard-coded dependencies
def process_user(user_id):
    user = fetch_user(user_id)  # Hard-coded!
    save_to_db(user)  # Hard-coded!

# After: Injected dependencies
class UserService:
    def __init__(self, user_repo: UserRepository, db_repo: DatabaseRepository):
        self._user_repo = user_repo
        self._db_repo = db_repo

    def process_user(self, user_id: int):
        user = self._user_repo.get_by_id(user_id)
        self._db_repo.save_user(user)
```

**Organize into Layered Architecture:**
```
Before (script):            After (OOP):
user_script.py              project/
                           ├── models/
                           │   └── user.py
                           ├── repositories/
                           │   ├── user_repository.py
                           │   └── database_repository.py
                           ├── services/
                           │   └── user_service.py
                           ├── clients/
                           │   └── api_client.py
                           └── main.py
```

**Key OOP Principles to Apply:**
- **Single Responsibility** (SRP): One class, one responsibility
- **Open/Closed** (OCP): Open for extension, closed for modification
- **Liskov Substitution** (LSP): Subtypes must be substitutable
- **Interface Segregation** (ISP): Many specific interfaces over one general
- **Dependency Inversion** (DIP): Depend on abstractions, not concretions

See `references/oop_principles.md` for comprehensive guide with examples.

## Common Refactoring Mistakes (CRITICAL - MUST AVOID)

These are catastrophic mistakes that break code. **NEVER make these errors:**

### 1. Incomplete Migration (CRITICAL BUG GENERATOR)

**The Problem:** Removing old code before ALL usages are migrated.

**Example Failure:**
```python
# Step 1: Create new service (GOOD)
class SSEManagerService:
    def __init__(self):
        self._connections = {}
        self._lock = asyncio.Lock()

# Step 2: Remove globals (DANGEROUS - TOO EARLY!)
# ❌ WRONG: Removed these before checking all usages
# global sse_connections  # REMOVED
# global _sse_lock  # REMOVED

# Step 3: Update some usages (INCOMPLETE)
def broadcast_event():
    # ✅ Updated to use service
    sse_manager.broadcast(event)

# MISSED: Route still using removed globals
@app.route('/stream')
async def stream():
    async with _sse_lock:  # ❌ NameError: _sse_lock undefined!
        sse_connections[id].append(queue)  # ❌ NameError: sse_connections undefined!
```

**Prevention Protocol:**
1. **BEFORE removing any code element**, run comprehensive searches:
   ```bash
   # Search for variable name
   grep -r "sse_connections" --include="*.py"

   # Search for related patterns
   grep -r "_sse_lock\|sse_global_connections\|sse_event_buffer" --include="*.py"

   # Search for common access patterns
   grep -r "sse_connections\[.*\]\|sse_connections\..*" --include="*.py"
   ```

2. **Document EVERY found usage:**
   ```markdown
   ## Migration Checklist for sse_connections removal

   Found usages:
   - [ ] rest_api_channel_api.py:1234 - broadcast_sse_event() - MIGRATED
   - [ ] rest_api_channel_api.py:1916 - stream_positions() - NOT MIGRATED
   - [ ] rest_api_channel_api.py:1945 - stream_signals() - NOT MIGRATED
   - [ ] rest_api_channel_api.py:1978 - stream_agents() - NOT MIGRATED

   Status: 1/4 usages migrated - CANNOT REMOVE YET
   ```

3. **Migrate ALL usages before removal**

4. **Run static analysis to verify:**
   ```bash
   flake8 <file> --select=F821  # Check for undefined names
   pylint <file> --disable=all --enable=E0602  # Check for undefined variables
   ```

5. **Only then remove old code**

### 2. Partial Pattern Application

**The Problem:** Applying refactoring pattern to some functions but not others.

**Prevention:** Use grep to find ALL instances of the pattern, create checklist, migrate all.

### 3. Breaking Public APIs Without Documentation

**The Problem:** Changing function signatures used by external code.

**Prevention:** Search for all callers before changing signatures. Document breaking changes.

### 4. Assuming Tests Cover Everything

**The Problem:** Tests pass but runtime errors occur (like NameError).

**Prevention:** Run static analysis (flake8, pylint, mypy) after every change.

## Anti-Patterns to Fix

Identify and fix these common anti-patterns. See `references/anti-patterns.md` for detailed examples.

**CRITICAL Priority Fixes (Must Fix First):**
1. **Script-like / Procedural Code** - Global state, scattered functions, no OOP structure (See `references/examples/script_to_oop_transformation.md`)
2. **God Object / God Class** - Single class responsible for too many unrelated things

**High-Priority Fixes:**
3. Complex nested conditionals (>3 levels)
4. Long functions (>30 lines doing multiple things)
5. Magic numbers and strings
6. Cryptic variable names (`x`, `tmp`, `data`, `d`)
7. Missing type hints on public APIs
8. Missing or inadequate docstrings
9. Unclear error handling
10. Mixed abstraction levels in single function

**Medium-Priority Fixes:**
11. Duplicate code (violates DRY)
12. Primitive obsession (should use domain objects)
13. Long parameter lists (>5 parameters)
14. Comments explaining "what" instead of "why"

**Low-Priority Fixes:**
15. Inconsistent naming conventions
16. Redundant comments (obvious statements)
17. Unused imports or variables

## Validation Framework

Use the provided validation scripts to measure improvements objectively.

### Multi-Metric Analysis (RECOMMENDED)

**Non affidarti a una sola metrica. Combina:**

| Metrica | Tool | Uso |
|---------|------|-----|
| Cognitive Complexity | **complexipy** | Comprensibilità umana |
| Cyclomatic Complexity | **ruff** (C901), radon | Test planning |
| Maintainability Index | radon | Salute generale codice |

#### Stack Raccomandato: Ruff + Complexipy

```bash
# Setup completo
pip install ruff complexipy radon wily

# Workflow quotidiano
ruff check src/                              # Linting veloce (Rust, 150-200x flake8)
complexipy src/ --max-complexity-allowed 15  # Cognitive complexity (Rust)
radon mi src/ -s                             # Maintainability Index
```

#### Perché Ruff + Complexipy?

| Tool | Vantaggi |
|------|----------|
| **Ruff** | Standard de facto, 800+ regole, velocissimo (Rust), sostituisce flake8+plugins |
| **Complexipy** | Cognitive complexity dedicata, attivamente mantenuta (2025), Rust, ecosistema completo |

#### Configurazione (pyproject.toml)

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E", "W",     # pycodestyle
    "F",          # Pyflakes
    "C90",        # McCabe cyclomatic complexity
    "B",          # flake8-bugbear
    "SIM",        # flake8-simplify
    "N",          # pep8-naming
    "UP",         # pyupgrade
    "I",          # isort
]

[tool.ruff.lint.mccabe]
max-complexity = 10  # Cyclomatic complexity

[tool.complexipy]
paths = ["src"]
max-complexity-allowed = 15    # SonarQube default
exclude = ["tests", "migrations"]
```

#### CLI Complexipy

```bash
# Analisi base
complexipy src/

# Output JSON per CI
complexipy src/ --output-json

# Per legacy code: snapshot baseline
complexipy src/ --snapshot-create --max-complexity-allowed 15

# Blocca solo regressioni (confronta con snapshot)
complexipy src/ --max-complexity-allowed 15
```

#### API Python

```python
from complexipy import file_complexity, code_complexity

# Analizza file
result = file_complexity("src/user_service.py")
for func in result.functions:
    if func.complexity > 15:
        print(f"⚠️ {func.name}: {func.complexity} (line {func.line_start})")
```

#### Pre-commit Hook

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/rohaquinlop/complexipy-pre-commit
    rev: v3.0.0
    hooks:
      - id: complexipy
        args: [--max-complexity-allowed, "15"]
```

#### GitHub Actions

```yaml
- name: Ruff
  uses: astral-sh/ruff-action@v1

- name: Cognitive Complexity
  uses: rohaquinlop/complexipy-action@v2
  with:
    paths: src/
    max_complexity_allowed: 15
```

### Cognitive Complexity: Dettagli Importanti

Vedi `references/cognitive_complexity_guide.md` per la guida completa. Punti chiave:

**Regole di calcolo:**
- +1 per ogni break nel flusso (if, for, while, except)
- +1 EXTRA per ogni livello di nesting (ESPONENZIALE!)
- Boolean sequences: stesso operatore = gratis, cambio operatore = +1
- match/switch = +1 TOTALE (non per branch)

### Historical Tracking con Wily

**Monitora i trend nel tempo, non solo i threshold:**

```bash
# Setup (una volta)
wily build src/ -n 50  # Analizza ultimi 50 commit

# Report per file
wily report src/module.py

# Diff tra commit
wily diff src/ -r HEAD~5..HEAD

# Rank file più complessi
wily rank src/ complexity

# Grafico trend (apre browser)
wily graph src/module.py complexity
```

**Integrazione CI per trend check:**
```bash
# Fail se complessità AUMENTATA rispetto a commit precedente
wily diff src/ -r HEAD~1..HEAD
```

### Threshold Progressivi per Legacy Code

**Non applicare threshold stretti immediatamente su legacy:**

```ini
# Fase 1: Baseline (blocca solo casi estremi)
max-cognitive-complexity = 25

# Fase 2: Riduzione graduale
max-cognitive-complexity = 20

# Fase 3: Standard (target finale)
max-cognitive-complexity = 15

# Fase 4: Strict (solo nuovo codice via pre-commit)
max-cognitive-complexity = 10
```

**Strategia "Changed Files Only":**
```bash
# Strict solo per file modificati
CHANGED=$(git diff --name-only origin/main...HEAD -- '*.py')
for f in $CHANGED; do
    flake8 "$f" --max-cognitive-complexity=10  # Strict
done
```

### Complexity Measurement

```bash
python scripts/measure_complexity.py <file_path>
```

**Targets:**
- Cyclomatic complexity: <10 per function (warning at 15, error at 20)
- Cognitive complexity: <15 per function (SonarQube default, warning at 20)
- Function length: <30 lines (warning at 50)
- Nesting depth: ≤3 levels

### Documentation Coverage

```bash
python scripts/check_documentation.py <file_path>
```

**Targets:**
- Docstring coverage: >80% for public functions
- Type hint coverage: >90% for public APIs
- Module-level documentation: Required

### Before/After Comparison

```bash
python scripts/compare_metrics.py <before_file> <after_file>
```

Generates comparison report showing improvements in all metrics.

### Performance Validation

```bash
python scripts/benchmark_changes.py <before_file> <after_file> <test_module>
```

Ensures no performance regression >10% (configurable threshold).

### Flake8 Code Quality Analysis

```bash
python scripts/analyze_with_flake8.py <file_or_directory> \
    --output report.json \
    --html report.html
```

**Three-tier plugin system (16 curated plugins for maximum readability):**

**ESSENTIAL (Must-Have - Install First):**
1. **flake8-bugbear**: Finds likely bugs and design problems (B codes)
2. **flake8-simplify**: Suggests simpler, clearer code (SIM codes)
3. **flake8-cognitive-complexity**: Measures cognitive load (CCR codes)
4. **pep8-naming**: Enforces clear naming conventions (N codes)
5. **flake8-docstrings**: Ensures documentation (D codes)

**RECOMMENDED (Strong Readability Impact):**
6. **flake8-comprehensions**: Cleaner comprehensions (C4 codes)
7. **flake8-expression-complexity**: Prevents complex expressions (ECE codes)
8. **flake8-functions**: Simpler function signatures (CFQ codes)
9. **flake8-variables-names**: Better variable naming (VNE codes)
10. **tryceratops**: Clean exception handling (TC codes)

**OPTIONAL (Nice to Have):**
11. **flake8-builtins**: Prevents shadowing built-ins (A codes)
12. **flake8-eradicate**: Finds commented-out code (E800 codes)
13. **flake8-unused-arguments**: Flags unused parameters (U codes)
14. **flake8-annotations**: Validates type hints (ANN codes)
15. **pydoclint**: Complete docstrings (DOC codes)
16. **flake8-spellcheck**: Catches typos (SC codes)

**Install essential plugins (minimum):**
```bash
pip install flake8 flake8-bugbear flake8-simplify \
    flake8-cognitive-complexity pep8-naming flake8-docstrings
```

**Install all recommended plugins (full suite):**
```bash
pip install flake8 flake8-bugbear flake8-simplify \
    flake8-cognitive-complexity pep8-naming flake8-docstrings \
    flake8-comprehensions flake8-expression-complexity \
    flake8-functions flake8-variables-names tryceratops \
    flake8-builtins flake8-eradicate flake8-unused-arguments \
    flake8-annotations pydoclint flake8-spellcheck
```

**Analysis provides:**
- Issue severity classification (high/medium/low)
- Issues by category (bugs, complexity, style, docs, naming)
- Potential bug detection (Bugbear plugin)
- Code simplification opportunities
- Missing documentation and type hints
- Style and naming violations
- HTML and JSON reports for tracking

**Configuration:**
Use the provided `.flake8` configuration file (`assets/.flake8`) for consistent analysis.

### Flake8 Before/After Comparison

```bash
python scripts/compare_flake8_reports.py before.json after.json \
    --html comparison.html
```

**Comparison shows:**
- Total issue reduction (count and percentage)
- Improvements by severity level (high/medium/low)
- Improvements by category (bugs, complexity, style, docs)
- Fixed issues vs new issues
- Net improvement score
- Detailed issue-by-issue analysis

**Targets:**
- Zero high-severity issues (bugs, runtime errors)
- <10 medium-severity issues (complexity, naming)
- Continuous reduction in all issue counts
- No regression in any category

## Language-Specific Guidelines

Apply language-appropriate idioms and conventions.

### Python

- **Type hints**: Use for all public APIs and complex internals
- **Docstrings**: Google style preferred
- **Data structures**: Use `dataclasses` for data containers
- **Path handling**: Use `pathlib` over `os.path`
- **Error handling**: Specific exceptions, not bare `except`
- **Modern features**: f-strings, context managers, comprehensions (when clear)

### JavaScript/TypeScript

- **Types**: Explicit TypeScript types for all public APIs
- **Async**: Prefer `async/await` over callbacks or raw promises
- **Destructuring**: Use for clarity, not just brevity
- **Immutability**: Prefer `const`, avoid mutation when practical
- **Error handling**: Try/catch for async, explicit error types

### Java

- **Interfaces**: Define contracts for implementations
- **Streams**: Use for collection operations (when clear)
- **Optional**: Handle nullability explicitly
- **Exceptions**: Checked for recoverable, unchecked for programming errors

### Go

- **Error handling**: Explicit error checking, no silent failures
- **Defer**: Use for resource cleanup
- **Names**: Short names in small scopes, longer in broad scopes
- **Interfaces**: Small, focused interfaces

## Output Format

Structure refactoring output consistently using the template from `assets/templates/summary_template.md`.

### Summary Structure

```markdown
## Refactoring Summary

**File:** `path/to/file.py`
**Date:** YYYY-MM-DD
**Risk Level:** [Low/Medium/High]

### Changes Made

1. **Extracted method `validate_user_input`** from `process_request`
   - Rationale: Function was 85 lines, violated SRP
   - Risk: Low (pure extraction, no logic changes)

2. **Renamed `d` → `discount_percentage`**
   - Rationale: Improved clarity
   - Risk: Low (local variable)

3. **Added guard clauses** to reduce nesting from 5 to 2 levels
   - Rationale: Improved readability, eliminated arrow code
   - Risk: Low (behavior preserved, tests pass)

### Metrics Improvement

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Avg Cyclomatic Complexity | 18.5 | 7.2 | -61% ✓ |
| Avg Function Length | 47 lines | 22 lines | -53% ✓ |
| Max Nesting Depth | 5 | 2 | -60% ✓ |
| Docstring Coverage | 45% | 92% | +104% ✓ |
| Type Hint Coverage | 30% | 95% | +217% ✓ |

### Test Results

- All 47 tests passing ✓
- No new test failures
- Test coverage maintained at 87%

### Performance Impact

- Benchmarked hot paths: No measurable difference (<2% variance)
- No performance-critical code modified

### Risk Assessment

**Overall Risk: Low**

- No public API changes
- All tests passing
- No performance regression
- Changes are mechanical refactorings

### Human Review Needed

**No** - Changes are low-risk mechanical improvements with full test coverage.

*If yes, specify areas:*
- [N/A]
```

## Integration with Same-Package Skills

This skill works in synergy with other skills in `python-development`:

### python-testing-patterns
- **Before refactoring:** Use `python-testing-patterns` to set up comprehensive pytest fixtures, mocking, and coverage
- **During refactoring:** Reference test patterns for writing validation tests
- **After refactoring:** Validate test coverage hasn't decreased
- **Invoke:** For detailed pytest patterns, fixtures, parameterization → use `python-testing-patterns` skill

### python-performance-optimization
- **Before refactoring:** Use `python-performance-optimization` for deep profiling with cProfile, py-spy, memory_profiler
- **After refactoring:** Run benchmark validation using profiling patterns
- **Note:** This skill's `benchmark_changes.py` script is for quick regression checks; use the performance skill for deep analysis
- **Invoke:** For runtime profiling, memory analysis, optimization → use `python-performance-optimization` skill

### python-packaging
- **After refactoring:** If refactoring a library, use `python-packaging` for proper pyproject.toml and distribution setup
- **Invoke:** For packaging, publishing to PyPI → use `python-packaging` skill

### uv-package-manager
- Use `uv` commands referenced in this skill (`uv run ruff`, `uv run complexipy`)
- **Invoke:** For dependency management, virtual environments → use `uv-package-manager` skill

### async-python-patterns
- When refactoring async code, reference async patterns for proper async/await structure
- **Invoke:** For asyncio patterns, concurrent programming → use `async-python-patterns` skill

### External Integration
- **Security Auditing:** After refactoring, run security audit to ensure no new vulnerabilities introduced
- **Documentation Generation:** Refactored code with better docstrings improves generated documentation

## Edge Cases and Limitations

### When NOT to Refactor

**Performance-Critical Code:**
- Profile first - if code is in hot path and optimized, readability may need to compromise
- Get explicit approval before refactoring performance-sensitive code
- Benchmark before and after

**Scheduled for Deletion:**
- Don't refactor code about to be removed or replaced
- Focus efforts on code with long-term value

**External Dependencies:**
- If the problematic code is in external libraries, contribute upstream
- Don't refactor vendored dependencies without tracking changes

**Stable, Working Legacy Code:**
- "If it ain't broke, don't fix it" applies when:
  - No one needs to modify it
  - It has no maintainability issues affecting development
  - Risk of introducing bugs outweighs readability benefits

### Limitations

**Algorithmic Complexity:**
- Cannot improve O(n²) to O(n log n) - that's algorithm change, not refactoring
- This skill focuses on code structure, not algorithmic optimization

**Domain Knowledge:**
- Cannot add domain knowledge that doesn't exist in code or comments
- Rename variables accurately only if their purpose is clear from context

**Test Coverage:**
- Cannot guarantee correctness without comprehensive tests
- Refactoring without tests is risky - add tests first when coverage is poor

**Subjective Preferences:**
- Code style preferences vary - this skill applies widely-accepted practices
- Be prepared to adjust based on team conventions

## Examples

See `references/examples/` for comprehensive before/after examples across different scenarios:

- **`examples/script_to_oop_transformation.md`** - **Complete transformation from script-like "spaghetti code" to clean OOP architecture (MUST READ)**
- `examples/python_complexity_reduction.md` - Nested conditionals and long functions
- `examples/typescript_naming_improvements.md` - Variable and function renaming with TypeScript patterns

See `references/` for comprehensive guides:

- **`REGRESSION_PREVENTION.md`** - **Mandatory checklist to prevent regressions (MUST READ)**
- **`cognitive_complexity_guide.md`** - Complete guide to cognitive complexity calculation, patterns, and tools
- `patterns.md` - All refactoring patterns with examples
- `anti-patterns.md` - Common anti-patterns to fix
- `oop_principles.md` - SOLID principles and OOP best practices
- `flake8_plugins_guide.md` - Plugin ecosystem for code quality

## Success Criteria

Refactoring is successful when:

1. ✓ **ZERO REGRESSIONI** - All existing tests pass, behavior unchanged
2. ✓ **Golden master match** - Output identico per casi critici documentati
3. ✓ Complexity metrics improved (documented in summary)
4. ✓ No performance regression >10% (or explicit approval obtained)
5. ✓ Documentation coverage improved
6. ✓ Code is easier for humans to understand (subjective but validated by metrics)
7. ✓ No new security vulnerabilities introduced
8. ✓ Changes are atomic and well-documented in git history
9. ✓ **Wily trend** - Complessità non aumentata rispetto a commit precedente
10. ✓ Static analysis shows improvement (flake8 issues reduced)

## Conclusion

Apply this skill systematically to transform hard-to-maintain code into clear, well-documented, maintainable code. Follow the four-phase workflow, apply patterns incrementally, validate continuously, and know when to stop. Balance readability with pragmatism - the goal is code that humans can confidently modify, not perfect code that no one dares touch.
