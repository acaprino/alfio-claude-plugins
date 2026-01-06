# Refactoring Patterns Reference

This document provides detailed refactoring patterns with complete before/after examples across multiple languages.

## Table of Contents

1. [Complexity Reduction Patterns](#complexity-reduction-patterns)
2. [Naming Improvement Patterns](#naming-improvement-patterns)
3. [Documentation Patterns](#documentation-patterns)
4. [Structure Improvement Patterns](#structure-improvement-patterns)

---

## Complexity Reduction Patterns

### 1. Guard Clauses (Early Returns)

**Problem:** Deep nesting makes code hard to follow. Each nested level increases cognitive load.

**Solution:** Use guard clauses to handle error cases and edge conditions early, reducing nesting.

#### Python Example

```python
# BEFORE: Deep nesting
def process_payment(user, amount, payment_method):
    if user is not None:
        if user.is_active:
            if amount > 0:
                if payment_method in ['credit', 'debit']:
                    if user.balance >= amount:
                        user.balance -= amount
                        return create_transaction(user, amount)
                    else:
                        return {'error': 'Insufficient balance'}
                else:
                    return {'error': 'Invalid payment method'}
            else:
                return {'error': 'Invalid amount'}
        else:
            return {'error': 'User not active'}
    else:
        return {'error': 'User not found'}

# AFTER: Guard clauses
def process_payment(user, amount, payment_method):
    """Process a payment transaction for a user.

    Args:
        user: User object making the payment
        amount: Payment amount (must be positive)
        payment_method: Payment method ('credit' or 'debit')

    Returns:
        Transaction object on success, error dict on failure
    """
    if user is None:
        return {'error': 'User not found'}

    if not user.is_active:
        return {'error': 'User not active'}

    if amount <= 0:
        return {'error': 'Invalid amount'}

    if payment_method not in ['credit', 'debit']:
        return {'error': 'Invalid payment method'}

    if user.balance < amount:
        return {'error': 'Insufficient balance'}

    user.balance -= amount
    return create_transaction(user, amount)
```

#### TypeScript Example

```typescript
// BEFORE: Deep nesting
function validateUserInput(data: any): ValidationResult {
    if (data) {
        if (data.email) {
            if (data.email.includes('@')) {
                if (data.password) {
                    if (data.password.length >= 8) {
                        return { valid: true };
                    } else {
                        return { valid: false, error: 'Password too short' };
                    }
                } else {
                    return { valid: false, error: 'Password required' };
                }
            } else {
                return { valid: false, error: 'Invalid email format' };
            }
        } else {
            return { valid: false, error: 'Email required' };
        }
    } else {
        return { valid: false, error: 'No data provided' };
    }
}

// AFTER: Guard clauses
function validateUserInput(data: any): ValidationResult {
    if (!data) {
        return { valid: false, error: 'No data provided' };
    }

    if (!data.email) {
        return { valid: false, error: 'Email required' };
    }

    if (!data.email.includes('@')) {
        return { valid: false, error: 'Invalid email format' };
    }

    if (!data.password) {
        return { valid: false, error: 'Password required' };
    }

    if (data.password.length < 8) {
        return { valid: false, error: 'Password too short' };
    }

    return { valid: true };
}
```

**Metrics Impact:**
- Nesting depth: 5 → 1 (80% reduction)
- Cyclomatic complexity: Similar, but easier to understand
- Readability: Significantly improved

---

### 2. Extract Method

**Problem:** Long functions that do multiple things are hard to understand and test.

**Solution:** Extract logical chunks into well-named helper functions.

#### Python Example

```python
# BEFORE: 60-line function doing everything
def process_order(order_id):
    # Fetch order (10 lines of error handling and DB logic)
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        log.error(f"Order not found: {order_id}")
        return None

    # Validate order (15 lines of validation logic)
    if not order.items:
        log.error(f"Empty order: {order_id}")
        return None
    for item in order.items:
        if item.quantity <= 0:
            log.error(f"Invalid quantity: {item.quantity}")
            return None
        product = db.query(Product).filter_by(id=item.product_id).first()
        if not product or product.stock < item.quantity:
            log.error(f"Insufficient stock for product: {item.product_id}")
            return None

    # Calculate total (10 lines of price calculation)
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * 0.08
    shipping = 10.0 if subtotal < 50 else 0.0
    total = subtotal + tax + shipping

    # Process payment (15 lines of payment logic)
    payment_method = order.payment_method
    if payment_method == 'credit':
        result = process_credit_card(order.card_token, total)
    elif payment_method == 'paypal':
        result = process_paypal(order.paypal_email, total)
    else:
        log.error(f"Invalid payment method: {payment_method}")
        return None

    if not result.success:
        log.error(f"Payment failed: {result.error}")
        return None

    # Update database (10 lines of DB updates)
    order.status = 'completed'
    order.total = total
    order.payment_id = result.payment_id
    for item in order.items:
        product = db.query(Product).filter_by(id=item.product_id).first()
        product.stock -= item.quantity
    db.commit()

    return order


# AFTER: Extracted into focused functions
def process_order(order_id: int) -> Optional[Order]:
    """Process an order from validation through payment.

    Args:
        order_id: ID of the order to process

    Returns:
        Completed order object, or None if processing failed
    """
    order = fetch_order(order_id)
    if not order:
        return None

    if not validate_order(order):
        return None

    total = calculate_order_total(order)

    payment_result = charge_payment(order, total)
    if not payment_result:
        return None

    return finalize_order(order, total, payment_result)


def fetch_order(order_id: int) -> Optional[Order]:
    """Fetch order from database with error handling."""
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        log.error(f"Order not found: {order_id}")
        return None
    return order


def validate_order(order: Order) -> bool:
    """Validate order has items and sufficient stock."""
    if not order.items:
        log.error(f"Empty order: {order.id}")
        return False

    for item in order.items:
        if not validate_order_item(item):
            return False

    return True


def validate_order_item(item: OrderItem) -> bool:
    """Validate a single order item has valid quantity and stock."""
    if item.quantity <= 0:
        log.error(f"Invalid quantity: {item.quantity}")
        return False

    product = db.query(Product).filter_by(id=item.product_id).first()
    if not product or product.stock < item.quantity:
        log.error(f"Insufficient stock for product: {item.product_id}")
        return False

    return True


def calculate_order_total(order: Order) -> float:
    """Calculate order total including tax and shipping."""
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * TAX_RATE
    shipping = FREE_SHIPPING_THRESHOLD if subtotal < 50 else 0.0
    return subtotal + tax + shipping


def charge_payment(order: Order, total: float) -> Optional[PaymentResult]:
    """Charge payment using order's payment method."""
    method = order.payment_method

    if method == 'credit':
        result = process_credit_card(order.card_token, total)
    elif method == 'paypal':
        result = process_paypal(order.paypal_email, total)
    else:
        log.error(f"Invalid payment method: {method}")
        return None

    if not result.success:
        log.error(f"Payment failed: {result.error}")
        return None

    return result


def finalize_order(order: Order, total: float, payment: PaymentResult) -> Order:
    """Update order and inventory after successful payment."""
    order.status = 'completed'
    order.total = total
    order.payment_id = payment.payment_id

    for item in order.items:
        deduct_inventory(item.product_id, item.quantity)

    db.commit()
    return order


def deduct_inventory(product_id: int, quantity: int):
    """Deduct quantity from product inventory."""
    product = db.query(Product).filter_by(id=product_id).first()
    product.stock -= quantity
```

**Metrics Impact:**
- Main function length: 60 lines → 12 lines (80% reduction)
- Avg function length: 60 lines → 8 lines
- Cyclomatic complexity: 15 → 3 per function
- Testability: Can now test each step independently

---

### 3. Replace Complex Conditional with Named Function

**Problem:** Complex boolean expressions are hard to understand.

**Solution:** Extract conditional logic into well-named boolean functions.

#### Python Example

```python
# BEFORE: Cryptic conditionals
def can_approve_loan(applicant):
    if ((applicant.credit_score > 650 and applicant.income > 50000 and
         applicant.employment_years >= 2) or
        (applicant.credit_score > 700 and applicant.has_collateral) or
        (applicant.is_existing_customer and applicant.credit_score > 600 and
         applicant.payment_history_good)):
        return True
    return False

# AFTER: Named boolean functions
def can_approve_loan(applicant: Applicant) -> bool:
    """Determine if loan application should be approved."""
    return (meets_standard_criteria(applicant) or
            meets_collateral_criteria(applicant) or
            meets_existing_customer_criteria(applicant))


def meets_standard_criteria(applicant: Applicant) -> bool:
    """Check if applicant meets standard approval criteria."""
    return (applicant.credit_score > 650 and
            applicant.income > 50000 and
            applicant.employment_years >= 2)


def meets_collateral_criteria(applicant: Applicant) -> bool:
    """Check if applicant qualifies with collateral."""
    return applicant.credit_score > 700 and applicant.has_collateral


def meets_existing_customer_criteria(applicant: Applicant) -> bool:
    """Check if existing customer qualifies for preferential terms."""
    return (applicant.is_existing_customer and
            applicant.credit_score > 600 and
            applicant.payment_history_good)
```

**Metrics Impact:**
- Readability: Self-documenting business logic
- Testability: Can test each criterion independently
- Maintainability: Easy to add new approval criteria

---

### 4. Simplify Loop Logic

**Problem:** Complex loop logic with nested conditions is hard to follow.

**Solution:** Use continue for early loop iteration exit, extract loop body to function.

#### Python Example

```python
# BEFORE: Complex nested loop
def process_transactions(transactions):
    results = []
    for transaction in transactions:
        if transaction.amount > 0:
            if transaction.status == 'pending':
                if transaction.user.is_verified:
                    if transaction.type in ['deposit', 'withdrawal']:
                        # Process transaction
                        result = {
                            'id': transaction.id,
                            'processed': True,
                            'fee': calculate_fee(transaction)
                        }
                        results.append(result)
                        transaction.status = 'completed'
    return results

# AFTER: Simplified with guard clauses
def process_transactions(transactions: List[Transaction]) -> List[dict]:
    """Process all valid pending transactions."""
    results = []

    for transaction in transactions:
        result = process_single_transaction(transaction)
        if result:
            results.append(result)

    return results


def process_single_transaction(transaction: Transaction) -> Optional[dict]:
    """Process a single transaction if valid.

    Returns:
        Processing result dict, or None if transaction was skipped
    """
    # Skip invalid transactions
    if transaction.amount <= 0:
        return None

    if transaction.status != 'pending':
        return None

    if not transaction.user.is_verified:
        return None

    if transaction.type not in ['deposit', 'withdrawal']:
        return None

    # Process valid transaction
    fee = calculate_fee(transaction)
    transaction.status = 'completed'

    return {
        'id': transaction.id,
        'processed': True,
        'fee': fee
    }
```

---

## Naming Improvement Patterns

### 1. Meaningful Variable Names

**Problem:** Cryptic abbreviations and single-letter names obscure meaning.

**Solution:** Use full, descriptive names that explain purpose.

```python
# BEFORE: Cryptic names
def calc(d, r, t):
    p = d * (1 + r) ** t
    return p

# AFTER: Descriptive names
def calculate_compound_interest(principal: float, rate: float, time_years: int) -> float:
    """Calculate compound interest.

    Args:
        principal: Initial investment amount
        rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
        time_years: Number of years to compound

    Returns:
        Final amount after compound interest
    """
    final_amount = principal * (1 + rate) ** time_years
    return final_amount
```

### 2. Boolean Naming Conventions

**Problem:** Boolean variables don't clearly indicate they hold true/false values.

**Solution:** Use is_, has_, can_, should_ prefixes.

```python
# BEFORE: Unclear boolean meaning
def check_user(user):
    verified = user.email_confirmed
    admin = user.role == 'admin'
    expired = user.subscription_end < datetime.now()

    if verified and admin and not expired:
        return True
    return False

# AFTER: Clear boolean names
def can_access_admin_panel(user: User) -> bool:
    """Check if user can access admin panel."""
    is_verified = user.email_confirmed
    is_admin = user.role == 'admin'
    has_active_subscription = user.subscription_end >= datetime.now()

    return is_verified and is_admin and has_active_subscription
```

### 3. Extract Magic Numbers to Named Constants

**Problem:** Numbers scattered through code lack context.

**Solution:** Define named constants at module level.

```python
# BEFORE: Magic numbers everywhere
def calculate_shipping(weight, distance):
    if weight < 5:
        base = 10
    elif weight < 20:
        base = 15
    else:
        base = 25

    if distance > 500:
        base *= 1.5

    if weight > 50:
        base += weight * 0.5

    return base

# AFTER: Named constants
# Shipping cost configuration
LIGHT_PACKAGE_MAX_LBS = 5
LIGHT_PACKAGE_BASE_COST = 10.0

MEDIUM_PACKAGE_MAX_LBS = 20
MEDIUM_PACKAGE_BASE_COST = 15.0

HEAVY_PACKAGE_BASE_COST = 25.0

LONG_DISTANCE_THRESHOLD_MILES = 500
LONG_DISTANCE_MULTIPLIER = 1.5

OVERSIZE_WEIGHT_THRESHOLD_LBS = 50
OVERSIZE_COST_PER_LB = 0.5


def calculate_shipping_cost(weight_lbs: float, distance_miles: float) -> float:
    """Calculate shipping cost based on weight and distance.

    Args:
        weight_lbs: Package weight in pounds
        distance_miles: Shipping distance in miles

    Returns:
        Shipping cost in dollars
    """
    base_cost = determine_base_cost(weight_lbs)

    if is_long_distance(distance_miles):
        base_cost *= LONG_DISTANCE_MULTIPLIER

    if is_oversize_package(weight_lbs):
        base_cost += calculate_oversize_fee(weight_lbs)

    return base_cost


def determine_base_cost(weight_lbs: float) -> float:
    """Determine base shipping cost from weight."""
    if weight_lbs < LIGHT_PACKAGE_MAX_LBS:
        return LIGHT_PACKAGE_BASE_COST
    elif weight_lbs < MEDIUM_PACKAGE_MAX_LBS:
        return MEDIUM_PACKAGE_BASE_COST
    else:
        return HEAVY_PACKAGE_BASE_COST


def is_long_distance(distance_miles: float) -> bool:
    """Check if distance qualifies as long-distance shipping."""
    return distance_miles > LONG_DISTANCE_THRESHOLD_MILES


def is_oversize_package(weight_lbs: float) -> bool:
    """Check if package qualifies as oversize."""
    return weight_lbs > OVERSIZE_WEIGHT_THRESHOLD_LBS


def calculate_oversize_fee(weight_lbs: float) -> float:
    """Calculate additional fee for oversize packages."""
    return weight_lbs * OVERSIZE_COST_PER_LB
```

---

## Documentation Patterns

### 1. Comprehensive Function Docstrings

**Pattern:** Document purpose, arguments, returns, exceptions, and side effects.

```python
def transfer_funds(
    from_account: Account,
    to_account: Account,
    amount: Decimal,
    reference: Optional[str] = None
) -> Transaction:
    """Transfer funds between two accounts.

    This function performs a validated transfer of funds from one account
    to another, creating a transaction record and updating both account
    balances atomically.

    Args:
        from_account: Source account (must have sufficient balance)
        to_account: Destination account (must be active)
        amount: Transfer amount (must be positive)
        reference: Optional reference note for the transaction

    Returns:
        Created transaction object with transfer details

    Raises:
        ValueError: If amount is not positive
        InsufficientFundsError: If source account lacks sufficient balance
        AccountInactiveError: If destination account is inactive
        DatabaseError: If transaction cannot be committed

    Side Effects:
        - Deducts amount from from_account balance
        - Adds amount to to_account balance
        - Creates transaction record in database
        - Sends notification to both account holders

    Example:
        >>> transfer = transfer_funds(
        ...     checking_account,
        ...     savings_account,
        ...     Decimal('1000.00'),
        ...     reference='Monthly savings'
        ... )
        >>> print(transfer.status)
        'completed'
    """
    # Implementation
```

### 2. Module-Level Documentation

**Pattern:** Explain module purpose, dependencies, and key concepts at top of file.

```python
"""User authentication and session management module.

This module provides functionality for:
- User login and logout
- Session token generation and validation
- Password hashing and verification
- Multi-factor authentication (MFA)

Dependencies:
    - bcrypt: Password hashing
    - jwt: Session token encoding
    - redis: Session storage

Key Concepts:
    Session tokens are JWT-encoded and stored in Redis with a 24-hour TTL.
    Passwords are hashed using bcrypt with work factor 12.
    MFA uses TOTP with 30-second time windows.

Example:
    from auth import authenticate_user, create_session

    user = authenticate_user(email, password)
    if user:
        session_token = create_session(user)

Security Notes:
    - Never log or expose session tokens
    - Always use constant-time comparison for tokens
    - Rate limit authentication attempts
"""

import bcrypt
import jwt
from redis import Redis
# ... rest of module
```

---

## Structure Improvement Patterns

### 1. Separate Concerns into Layers

**Problem:** Mixed data access, business logic, and presentation in one function.

**Solution:** Organize code into distinct layers with clear responsibilities.

```python
# BEFORE: Everything mixed together
def show_user_dashboard(user_id):
    # Data access
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_row = cursor.fetchone()

    cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT 10", (user_id,))
    order_rows = cursor.fetchall()

    # Business logic
    total_spent = sum(row[3] for row in order_rows)  # amount column
    avg_order = total_spent / len(order_rows) if order_rows else 0
    loyalty_tier = 'gold' if total_spent > 1000 else 'silver' if total_spent > 500 else 'bronze'

    # Presentation
    html = f"""
    <html>
        <body>
            <h1>Welcome, {user_row[1]}</h1>  <!-- name column -->
            <p>Total Spent: ${total_spent}</p>
            <p>Loyalty Tier: {loyalty_tier}</p>
            <h2>Recent Orders</h2>
            <ul>
    """
    for order in order_rows:
        html += f"<li>Order #{order[0]}: ${order[3]}</li>"
    html += "</ul></body></html>"

    return html


# AFTER: Separated into layers

# Data Layer (data_access.py)
class UserRepository:
    """Data access for user entities."""

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by ID from database."""
        # Clean data access logic

    def get_recent_orders(self, user_id: int, limit: int = 10) -> List[Order]:
        """Fetch user's recent orders."""
        # Clean data access logic


# Business Logic Layer (services.py)
class UserService:
    """Business logic for user operations."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_user_stats(self, user_id: int) -> UserStats:
        """Calculate user statistics and loyalty tier."""
        user = self.user_repo.get_by_id(user_id)
        orders = self.user_repo.get_recent_orders(user_id)

        total_spent = sum(order.amount for order in orders)
        avg_order = total_spent / len(orders) if orders else 0
        loyalty_tier = self._calculate_loyalty_tier(total_spent)

        return UserStats(
            user=user,
            total_spent=total_spent,
            avg_order_value=avg_order,
            loyalty_tier=loyalty_tier,
            recent_orders=orders
        )

    def _calculate_loyalty_tier(self, total_spent: Decimal) -> str:
        """Determine loyalty tier from spending."""
        if total_spent > 1000:
            return 'gold'
        elif total_spent > 500:
            return 'silver'
        else:
            return 'bronze'


# Presentation Layer (views.py)
class UserDashboardView:
    """Render user dashboard HTML."""

    def render(self, stats: UserStats) -> str:
        """Render dashboard from user stats."""
        return render_template(
            'dashboard.html',
            user=stats.user,
            total_spent=stats.total_spent,
            loyalty_tier=stats.loyalty_tier,
            recent_orders=stats.recent_orders
        )


# Controller/Route (routes.py)
def show_user_dashboard(user_id: int) -> str:
    """Show user dashboard page."""
    user_service = UserService(UserRepository())
    stats = user_service.get_user_stats(user_id)

    view = UserDashboardView()
    return view.render(stats)
```

**Benefits:**
- Data access is isolated and testable
- Business logic is independent of database or presentation
- Presentation is separated from logic
- Each layer can be tested independently
- Changes to database don't affect business logic
- Changes to HTML don't affect logic

---

### 2. Consistent Abstraction Levels

**Problem:** Mixing high-level and low-level operations in same function.

**Solution:** Keep functions at consistent abstraction level; delegate details to helpers.

```python
# BEFORE: Mixed abstraction levels
def process_order(order_id):
    # High-level: get order
    order = get_order(order_id)

    # Low-level: manual string formatting and validation
    if not order.email or '@' not in order.email:
        raise ValueError("Invalid email")

    email_parts = order.email.split('@')
    if len(email_parts) != 2 or not email_parts[0] or not email_parts[1]:
        raise ValueError("Malformed email")

    # High-level: charge payment
    charge_payment(order)

    # Low-level: manual SQL update
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = %s WHERE id = %s", ('completed', order_id))
    conn.commit()

    # High-level: send notification
    send_confirmation_email(order)


# AFTER: Consistent abstraction level
def process_order(order_id: int):
    """Process order from validation through completion."""
    order = get_order(order_id)

    validate_order_email(order.email)  # Same level of abstraction
    charge_payment(order)               # Same level
    mark_order_completed(order_id)      # Same level
    send_confirmation_email(order)      # Same level


def validate_order_email(email: str):
    """Validate email format for order."""
    if not email or '@' not in email:
        raise ValueError("Invalid email")

    email_parts = email.split('@')
    if len(email_parts) != 2 or not email_parts[0] or not email_parts[1]:
        raise ValueError("Malformed email")


def mark_order_completed(order_id: int):
    """Update order status to completed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = %s WHERE id = %s",
        ('completed', order_id)
    )
    conn.commit()
```

---

## Summary

These patterns form the foundation of readable, maintainable code:

1. **Reduce complexity** through guard clauses, method extraction, and named conditionals
2. **Improve naming** with descriptive variables, boolean conventions, and named constants
3. **Document thoroughly** with comprehensive docstrings and module documentation
4. **Structure clearly** by separating concerns and maintaining consistent abstraction levels

Apply these patterns systematically during refactoring to transform hard-to-understand code into clear, maintainable code that teams can confidently modify.
