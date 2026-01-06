# Flake8 Plugins Guide for Human-Readable Code

This guide explains all 16 curated plugins, organized by priority, with examples of what they catch and why it matters for readability.

---

## 🥇 ESSENTIAL Plugins (Install These First!)

These 5 plugins have the **highest impact** on code readability and should be installed immediately.

### 1. flake8-bugbear (B codes)

**Purpose:** Finds likely bugs and design problems that confuse developers.

**Why Essential:** Prevents subtle bugs that make code hard to understand and debug.

**Examples:**

**B006 - Mutable default arguments:**
```python
# BAD - Confusing shared state
def add_item(item, lst=[]):  # B006
    lst.append(item)
    return lst

# First call
result1 = add_item(1)  # [1]
# Second call - SURPRISE!
result2 = add_item(2)  # [1, 2] - not [2]!

# GOOD - Clear behavior
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

**B001 - Bare except:**
```python
# BAD - Hides all errors
try:
    process_data()
except:  # B001 - Too broad!
    pass

# GOOD - Explicit error handling
try:
    process_data()
except ValueError as e:
    logger.error(f"Invalid data: {e}")
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

**B008 - Function calls in argument defaults:**
```python
# BAD - Called once at definition time
def process(timestamp=datetime.now()):  # B008
    # Always uses same timestamp!
    pass

# GOOD - Evaluated each call
def process(timestamp=None):
    if timestamp is None:
        timestamp = datetime.now()
    # Fresh timestamp each call
```

**Install:**
```bash
pip install flake8-bugbear
```

---

### 2. flake8-simplify (SIM codes)

**Purpose:** Suggests simpler, more Pythonic alternatives to complex patterns.

**Why Essential:** Dramatically improves code clarity by removing unnecessary complexity.

**Examples:**

**SIM102 - Nested if statements:**
```python
# BAD - Nested complexity
if condition_a:
    if condition_b:
        return True
return False

# GOOD - Simplified
return condition_a and condition_b
```

**SIM105 - Use contextlib.suppress:**
```python
# BAD - Try/except/pass pattern
try:
    os.remove(file)
except FileNotFoundError:
    pass

# GOOD - More explicit intent
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove(file)
```

**SIM108 - Use ternary operator:**
```python
# BAD - Unnecessary if/else
if condition:
    value = "yes"
else:
    value = "no"

# GOOD - Clearer
value = "yes" if condition else "no"
```

**SIM118 - Use 'in dict' instead of 'in dict.keys()':**
```python
# BAD - Redundant .keys()
if key in my_dict.keys():  # SIM118
    ...

# GOOD - More Pythonic
if key in my_dict:
    ...
```

**Install:**
```bash
pip install flake8-simplify
```

---

### 3. flake8-cognitive-complexity (CCR codes)

**Purpose:** Measures how HARD code is to understand (cognitive load), not just how complex.

**Why Essential:** Better metric than cyclomatic complexity for human readability.

**Difference from Cyclomatic Complexity:**
- Cyclomatic: Counts decision points (if, for, while)
- Cognitive: Measures mental effort to understand

**Example:**

```python
# High cyclomatic (7) BUT low cognitive (4) - Easy to read
def process_user(user):
    if not user:
        return None
    if not user.active:
        return None
    if not user.verified:
        return None
    if not user.permissions:
        return None
    return do_process(user)

# Lower cyclomatic (4) BUT high cognitive (10+) - Hard to read!
def complex_logic(data):
    if data:
        if data.is_valid:
            for item in data.items:
                if item.enabled:
                    if item.has_permission():
                        return item.process()
    return None
```

**Configuration:**
```ini
# .flake8
[flake8]
max-cognitive-complexity = 10  # Recommended threshold
```

**Install:**
```bash
pip install flake8-cognitive-complexity
```

---

### 4. pep8-naming (N codes)

**Purpose:** Enforces PEP 8 naming conventions for consistency.

**Why Essential:** Good naming is critical for instant comprehension.

**Examples:**

**N802 - Function name should be lowercase:**
```python
# BAD - Looks like a class
def CalculateTotal(items):  # N802
    pass

# GOOD - Clear function
def calculate_total(items):
    pass
```

**N803 - Argument name should be lowercase:**
```python
# BAD - Confusing
def process(UserData):  # N803
    pass

# GOOD - Clear
def process(user_data):
    pass
```

**N806 - Variable should be lowercase:**
```python
# BAD - Looks like constant
def calculate():
    TotalAmount = 100  # N806
    return TotalAmount

# GOOD - Clear variable
def calculate():
    total_amount = 100
    return total_amount
```

**N815 - Mixed case variable:**
```python
# BAD - Inconsistent
userName = "john"  # N815 (camelCase in Python)

# GOOD - Snake case
user_name = "john"
```

**Install:**
```bash
pip install pep8-naming
```

---

### 5. flake8-docstrings (D codes)

**Purpose:** Ensures code is documented with proper docstrings.

**Why Essential:** Documentation is key to understanding code intent.

**Examples:**

**D103 - Missing docstring in public function:**
```python
# BAD - No documentation
def calculate_discount(price, user_tier):  # D103
    return price * get_discount_rate(user_tier)

# GOOD - Clear documentation
def calculate_discount(price: float, user_tier: str) -> float:
    """Calculate discount amount based on user tier.

    Args:
        price: Original price before discount
        user_tier: User membership tier ('bronze', 'silver', 'gold')

    Returns:
        Discount amount to subtract from price
    """
    return price * get_discount_rate(user_tier)
```

**D100 - Missing docstring in public module:**
```python
# BAD - No module documentation
import requests

def fetch_data():
    pass

# GOOD - Module documented
"""User data fetching module.

This module provides functions for fetching and processing
user data from the external API.
"""
import requests

def fetch_data():
    """Fetch user data from API."""
    pass
```

**Configuration:**
```ini
# .flake8
[flake8]
docstring-convention = google  # or numpy, pep257
```

**Install:**
```bash
pip install flake8-docstrings
```

---

## 🥈 RECOMMENDED Plugins (Strong Impact)

These 5 plugins significantly improve readability and should be installed after the essentials.

### 6. flake8-comprehensions (C4 codes)

**Purpose:** Promotes cleaner, more Pythonic comprehensions.

**Examples:**

**C400 - Unnecessary list comprehension:**
```python
# BAD
list([x for x in items])  # C400

# GOOD
[x for x in items]
```

**C402 - Unnecessary dict/set call:**
```python
# BAD
dict([(k, v) for k, v in pairs])  # C402

# GOOD
{k: v for k, v in pairs}
```

**Install:**
```bash
pip install flake8-comprehensions
```

---

### 7. flake8-expression-complexity (ECE codes)

**Purpose:** Prevents incomprehensible one-liners.

**Example:**

```python
# BAD - Too complex to understand quickly
result = [x for x in items if x.is_valid() and x.price > 100 and x.category in ['A', 'B'] and not x.is_expired() or x.is_special]  # ECE001

# GOOD - Broken down
valid_items = [x for x in items if x.is_valid()]
expensive_items = [x for x in valid_items if x.price > 100]
filtered_items = [
    x for x in expensive_items
    if x.category in ['A', 'B'] and not x.is_expired()
]
```

**Configuration:**
```ini
# .flake8
[flake8]
max-expression-complexity = 7  # Recommended
```

**Install:**
```bash
pip install flake8-expression-complexity
```

---

### 8. flake8-functions (CFQ codes)

**Purpose:** Validates function parameters and complexity.

**Examples:**

**CFQ002 - Too many arguments:**
```python
# BAD - Hard to call
def create_user(name, email, age, address, phone, country, city, zip_code):  # CFQ002
    pass

# GOOD - Grouped data
from dataclasses import dataclass

@dataclass
class UserData:
    name: str
    email: str
    age: int
    address: Address

def create_user(user_data: UserData):
    pass
```

**Install:**
```bash
pip install flake8-functions
```

---

### 9. flake8-variables-names (VNE codes)

**Purpose:** Promotes descriptive variable naming.

**Examples:**

**VNE001 - Single letter variable:**
```python
# BAD - Unclear
d = calculate()  # VNE001
l = fetch_items()  # VNE001

# GOOD - Descriptive
discount = calculate()
items_list = fetch_items()
```

**VNE003 - Too short:**
```python
# BAD
usr = get_user()  # VNE003

# GOOD
user = get_user()
```

**Install:**
```bash
pip install flake8-variables-names
```

---

### 10. tryceratops (TC codes)

**Purpose:** Prevents exception-handling anti-patterns.

**Examples:**

**TC101 - Bare except:**
```python
# BAD
try:
    risky_operation()
except:  # TC101
    handle_error()

# GOOD
try:
    risky_operation()
except SpecificError as e:
    handle_error(e)
```

**TC201 - Long try:**
```python
# BAD - Too much in try block
try:  # TC201
    # 50 lines of code
    # Only last line can actually raise
    risky_operation()
except ValueError:
    handle()

# GOOD - Minimal try scope
prepare_data()
validate_input()
try:
    risky_operation()  # Only risky part
except ValueError:
    handle()
```

**Install:**
```bash
pip install tryceratops
```

---

## 🥉 OPTIONAL Plugins (Nice to Have)

These 6 plugins add extra polish and catch edge cases.

### 11. flake8-builtins (A codes)

**Purpose:** Prevents shadowing Python built-ins.

**Example:**

```python
# BAD - Shadows built-in
def process(list, dict):  # A002
    pass

# GOOD - Clear names
def process(items_list, config_dict):
    pass
```

**Install:**
```bash
pip install flake8-builtins
```

---

### 12. flake8-eradicate (E800 codes)

**Purpose:** Finds commented-out code (visual clutter).

**Example:**

```python
# BAD - Dead code confuses readers
def process():
    data = fetch()
    # old_process(data)  # E800
    # return old_result  # E800
    return new_process(data)

# GOOD - Only active code
def process():
    data = fetch()
    return new_process(data)
```

**Install:**
```bash
pip install flake8-eradicate
```

---

### 13. flake8-unused-arguments (U codes)

**Purpose:** Flags unused function parameters.

**Example:**

```python
# BAD - Unused parameter suggests incomplete code
def calculate(price, tax_rate, discount):  # U100
    return price * tax_rate  # discount never used!

# GOOD - Use or remove
def calculate(price, tax_rate):
    return price * tax_rate
```

**Install:**
```bash
pip install flake8-unused-arguments
```

---

### 14. flake8-annotations (ANN codes)

**Purpose:** Validates type hint presence.

**Example:**

```python
# BAD - No type hints
def process(data):  # ANN001, ANN201
    return data.upper()

# GOOD - Clear types
def process(data: str) -> str:
    return data.upper()
```

**Install:**
```bash
pip install flake8-annotations
```

---

### 15. pydoclint (DOC codes)

**Purpose:** Validates docstring completeness.

**Example:**

```python
# BAD - Incomplete docstring
def transfer(from_acc, to_acc, amount):
    """Transfer money."""  # DOC - Missing args/returns
    ...

# GOOD - Complete docstring
def transfer(from_acc: Account, to_acc: Account, amount: float) -> bool:
    """Transfer money between accounts.

    Args:
        from_acc: Source account
        to_acc: Destination account
        amount: Amount to transfer

    Returns:
        True if successful, False otherwise

    Raises:
        InsufficientFundsError: If source lacks funds
    """
    ...
```

**Install:**
```bash
pip install pydoclint
```

---

### 16. flake8-spellcheck (SC codes)

**Purpose:** Catches typos in code and comments.

**Example:**

```python
# BAD - Typos hurt comprehension
def calcualte_totla(itmes):  # SC100, SC100, SC100
    """Calcualte the totla of itmes."""  # SC200
    pass

# GOOD - Clear spelling
def calculate_total(items):
    """Calculate the total of items."""
    pass
```

**Install:**
```bash
pip install flake8-spellcheck
```

---

## Installation Guide

### Minimal Setup (Essential Only)
```bash
pip install flake8 flake8-bugbear flake8-simplify \
    flake8-cognitive-complexity pep8-naming flake8-docstrings
```

### Recommended Setup (Essential + Recommended)
```bash
pip install flake8 flake8-bugbear flake8-simplify \
    flake8-cognitive-complexity pep8-naming flake8-docstrings \
    flake8-comprehensions flake8-expression-complexity \
    flake8-functions flake8-variables-names tryceratops
```

### Full Setup (All 16 Plugins)
```bash
pip install flake8 flake8-bugbear flake8-simplify \
    flake8-cognitive-complexity pep8-naming flake8-docstrings \
    flake8-comprehensions flake8-expression-complexity \
    flake8-functions flake8-variables-names tryceratops \
    flake8-builtins flake8-eradicate flake8-unused-arguments \
    flake8-annotations pydoclint flake8-spellcheck
```

---

## Configuration

Copy `assets/.flake8` to your project root for optimal settings.

**Key settings:**
```ini
[flake8]
max-line-length = 88
max-complexity = 10
max-cognitive-complexity = 10
max-expression-complexity = 7
docstring-convention = google
```

---

## Usage

### Basic Analysis
```bash
python scripts/analyze_with_flake8.py your_code.py
```

### With Reports
```bash
python scripts/analyze_with_flake8.py your_project/ \
    --output before.json \
    --html before.html
```

### Compare Before/After
```bash
# After refactoring
python scripts/analyze_with_flake8.py your_project/ \
    --output after.json \
    --html after.html

# Compare
python scripts/compare_flake8_reports.py before.json after.json \
    --html comparison.html
```

---

## Summary

These 16 plugins work together to create **highly readable, maintainable code** by:

✅ **Preventing bugs** (bugbear, tryceratops)
✅ **Reducing complexity** (simplify, cognitive-complexity, expression-complexity)
✅ **Improving naming** (pep8-naming, variables-names)
✅ **Ensuring documentation** (docstrings, pydoclint, annotations)
✅ **Promoting best practices** (comprehensions, functions, builtins)
✅ **Removing clutter** (eradicate, unused-arguments)
✅ **Catching mistakes** (spellcheck)

**Result:** Code that humans can easily read, understand, and maintain! 🎉
