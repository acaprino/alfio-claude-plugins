# OOP Principles and Patterns for Maintainable Code

This guide promotes **Object-Oriented Programming** principles to avoid spaghetti code and maintain well-structured, modular codebases.

---

## Core Principle

**AVOID SCRIPT-LIKE CODE** - Transform procedural, script-style code into well-organized, OOP-based architecture with clear responsibilities, proper encapsulation, and modular structure.

---

## OOP vs Script-Like Code

### Script-Like Code (AVOID)
```python
# BAD: Everything in one file, global state, no structure
import requests

# Global variables
API_URL = "https://api.example.com"
users_cache = {}
last_request_time = None

# Scattered functions with no cohesion
def fetch_user(user_id):
    global users_cache, last_request_time
    if user_id in users_cache:
        return users_cache[user_id]

    response = requests.get(f"{API_URL}/users/{user_id}")
    data = response.json()
    users_cache[user_id] = data
    last_request_time = time.time()
    return data

def get_user_posts(user_id):
    global last_request_time
    user = fetch_user(user_id)
    response = requests.get(f"{API_URL}/posts?user={user_id}")
    last_request_time = time.time()
    return response.json()

def process_user_data(user_id):
    user = fetch_user(user_id)
    posts = get_user_posts(user_id)
    # ... 100 lines of processing logic
    return processed_data

# Executing code at module level
if __name__ == "__main__":
    result = process_user_data(123)
    print(result)
```

**Problems:**
- ❌ Global state (`users_cache`, `last_request_time`)
- ❌ No encapsulation
- ❌ Functions scattered without cohesion
- ❌ Hard to test (depends on globals)
- ❌ No clear boundaries or responsibilities
- ❌ Difficult to extend or modify
- ❌ No reusability

### OOP-Based Code (GOOD)
```python
# GOOD: Well-structured, modular, OOP-based

# models/user.py
from dataclasses import dataclass
from typing import List

@dataclass
class User:
    """User domain model."""
    id: int
    name: str
    email: str

    def is_valid(self) -> bool:
        """Validate user data."""
        return bool(self.email and '@' in self.email)


@dataclass
class Post:
    """Post domain model."""
    id: int
    user_id: int
    title: str
    content: str


# repositories/user_repository.py
from typing import Optional, Protocol
from models.user import User

class UserRepositoryInterface(Protocol):
    """Interface for user data access."""
    def get_by_id(self, user_id: int) -> Optional[User]: ...
    def save(self, user: User) -> bool: ...


class UserRepository:
    """Concrete implementation of user repository."""

    def __init__(self, api_client: 'APIClient'):
        self._api_client = api_client
        self._cache: dict[int, User] = {}

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by ID with caching."""
        if user_id in self._cache:
            return self._cache[user_id]

        data = self._api_client.get(f"/users/{user_id}")
        if data:
            user = User(**data)
            self._cache[user_id] = user
            return user
        return None

    def save(self, user: User) -> bool:
        """Save user data."""
        result = self._api_client.post("/users", user.__dict__)
        if result:
            self._cache[user.id] = user
        return result


# services/api_client.py
from typing import Optional, Any
import requests
from datetime import datetime

class APIClient:
    """HTTP client for API communication."""

    def __init__(self, base_url: str):
        self._base_url = base_url
        self._last_request_time: Optional[datetime] = None

    def get(self, endpoint: str) -> Optional[dict]:
        """Perform GET request."""
        self._update_request_time()
        response = requests.get(f"{self._base_url}{endpoint}")
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: dict) -> bool:
        """Perform POST request."""
        self._update_request_time()
        response = requests.post(f"{self._base_url}{endpoint}", json=data)
        return response.status_code == 200

    def _update_request_time(self) -> None:
        """Track last request time."""
        self._last_request_time = datetime.now()


# services/user_service.py
class UserService:
    """Business logic for user operations."""

    def __init__(self, user_repository: UserRepositoryInterface):
        self._user_repo = user_repository

    def get_user_with_validation(self, user_id: int) -> Optional[User]:
        """Get user and validate data."""
        user = self._user_repo.get_by_id(user_id)
        if user and user.is_valid():
            return user
        return None

    def process_user_data(self, user_id: int) -> dict:
        """Process user data for output."""
        user = self.get_user_with_validation(user_id)
        if not user:
            return {'error': 'User not found or invalid'}

        return {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }


# main.py
def main():
    """Application entry point."""
    # Dependency injection
    api_client = APIClient("https://api.example.com")
    user_repo = UserRepository(api_client)
    user_service = UserService(user_repo)

    # Use service
    result = user_service.process_user_data(123)
    print(result)


if __name__ == "__main__":
    main()
```

**Benefits:**
- ✅ Clear separation of concerns (models, repositories, services)
- ✅ No global state
- ✅ Dependency injection (testable)
- ✅ Interfaces/protocols for flexibility
- ✅ Encapsulation (private members with `_`)
- ✅ Single Responsibility Principle
- ✅ Easy to test, extend, and maintain
- ✅ Reusable components

---

## SOLID Principles

### 1. Single Responsibility Principle (SRP)

**Rule:** Each class should have ONE reason to change.

```python
# BAD: Class doing too much
class UserManager:
    def get_user(self, user_id):
        # Database access
        pass

    def validate_user(self, user):
        # Validation logic
        pass

    def send_email(self, user, message):
        # Email sending
        pass

    def generate_report(self, user):
        # Report generation
        pass

# GOOD: Separated responsibilities
class UserRepository:
    """Handles data access."""
    def get_user(self, user_id): pass

class UserValidator:
    """Handles validation."""
    def validate(self, user): pass

class EmailService:
    """Handles email."""
    def send(self, user, message): pass

class ReportGenerator:
    """Handles reports."""
    def generate(self, user): pass
```

---

### 2. Open/Closed Principle (OCP)

**Rule:** Open for extension, closed for modification.

```python
# BAD: Must modify class to add payment methods
class PaymentProcessor:
    def process(self, payment_type, amount):
        if payment_type == "credit_card":
            # Process credit card
            pass
        elif payment_type == "paypal":
            # Process PayPal
            pass
        # Need to modify this class for new payment types!

# GOOD: Extensible through inheritance/composition
from abc import ABC, abstractmethod

class PaymentMethod(ABC):
    """Abstract payment method."""
    @abstractmethod
    def process(self, amount: float) -> bool:
        pass

class CreditCardPayment(PaymentMethod):
    def process(self, amount: float) -> bool:
        # Process credit card
        return True

class PayPalPayment(PaymentMethod):
    def process(self, amount: float) -> bool:
        # Process PayPal
        return True

class PaymentProcessor:
    """Process payments using any payment method."""
    def process(self, payment_method: PaymentMethod, amount: float) -> bool:
        return payment_method.process(amount)

# Add new payment type WITHOUT modifying existing code
class CryptoPayment(PaymentMethod):
    def process(self, amount: float) -> bool:
        # Process crypto
        return True
```

---

### 3. Liskov Substitution Principle (LSP)

**Rule:** Derived classes must be substitutable for their base classes.

```python
# BAD: Violates LSP
class Bird:
    def fly(self):
        return "Flying"

class Penguin(Bird):
    def fly(self):
        raise NotImplementedError("Penguins can't fly!")  # Breaks contract!

# GOOD: Proper abstraction
class Bird(ABC):
    @abstractmethod
    def move(self):
        pass

class FlyingBird(Bird):
    def move(self):
        return "Flying"

    def fly(self):
        return "Flying"

class Penguin(Bird):
    def move(self):
        return "Swimming"

    def swim(self):
        return "Swimming"
```

---

### 4. Interface Segregation Principle (ISP)

**Rule:** Don't force clients to depend on methods they don't use.

```python
# BAD: Fat interface
class Worker(ABC):
    @abstractmethod
    def work(self): pass

    @abstractmethod
    def eat(self): pass

    @abstractmethod
    def sleep(self): pass

class Robot(Worker):
    def work(self): return "Working"
    def eat(self): pass  # Robots don't eat!
    def sleep(self): pass  # Robots don't sleep!

# GOOD: Segregated interfaces
class Workable(ABC):
    @abstractmethod
    def work(self): pass

class Eatable(ABC):
    @abstractmethod
    def eat(self): pass

class Sleepable(ABC):
    @abstractmethod
    def sleep(self): pass

class Human(Workable, Eatable, Sleepable):
    def work(self): return "Working"
    def eat(self): return "Eating"
    def sleep(self): return "Sleeping"

class Robot(Workable):
    def work(self): return "Working"
```

---

### 5. Dependency Inversion Principle (DIP)

**Rule:** Depend on abstractions, not concretions.

```python
# BAD: High-level depends on low-level
class MySQLDatabase:
    def query(self, sql):
        # MySQL specific code
        pass

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # Tightly coupled!

    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id={user_id}")

# GOOD: Both depend on abstraction
from typing import Protocol

class DatabaseInterface(Protocol):
    """Database abstraction."""
    def query(self, sql: str) -> list: ...

class MySQLDatabase:
    """MySQL implementation."""
    def query(self, sql: str) -> list:
        # MySQL specific code
        pass

class PostgreSQLDatabase:
    """PostgreSQL implementation."""
    def query(self, sql: str) -> list:
        # PostgreSQL specific code
        pass

class UserService:
    """Service depends on abstraction."""
    def __init__(self, database: DatabaseInterface):
        self._db = database  # Loosely coupled!

    def get_user(self, user_id: int):
        return self._db.query(f"SELECT * FROM users WHERE id={user_id}")

# Can easily swap implementations
user_service = UserService(MySQLDatabase())
# or
user_service = UserService(PostgreSQLDatabase())
```

---

## Design Patterns for Avoiding Spaghetti Code

### 1. Repository Pattern

**Purpose:** Separate data access logic from business logic.

```python
# repositories/user_repository.py
from typing import Optional, List
from models.user import User

class UserRepository:
    """Handles all user data access."""

    def __init__(self, db_connection):
        self._db = db_connection

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID."""
        pass

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        pass

    def save(self, user: User) -> bool:
        """Save user to database."""
        pass

    def delete(self, user_id: int) -> bool:
        """Delete user."""
        pass
```

---

### 2. Service Layer Pattern

**Purpose:** Encapsulate business logic separate from data access and presentation.

```python
# services/user_service.py
class UserService:
    """Business logic for user operations."""

    def __init__(
        self,
        user_repo: UserRepository,
        email_service: EmailService,
        validator: UserValidator
    ):
        self._user_repo = user_repo
        self._email_service = email_service
        self._validator = validator

    def register_user(self, user_data: dict) -> User:
        """Register new user with validation and notification."""
        # Validate
        if not self._validator.validate_registration(user_data):
            raise ValidationError("Invalid user data")

        # Create user
        user = User(**user_data)

        # Save
        if not self._user_repo.save(user):
            raise DatabaseError("Failed to save user")

        # Send welcome email
        self._email_service.send_welcome_email(user)

        return user
```

---

### 3. Factory Pattern

**Purpose:** Create objects without specifying exact class.

```python
# factories/payment_factory.py
from typing import Dict, Type
from models.payments import PaymentMethod, CreditCard, PayPal, Crypto

class PaymentFactory:
    """Factory for creating payment method instances."""

    _payment_types: Dict[str, Type[PaymentMethod]] = {
        'credit_card': CreditCard,
        'paypal': PayPal,
        'crypto': Crypto
    }

    @classmethod
    def create(cls, payment_type: str, **kwargs) -> PaymentMethod:
        """Create payment method instance."""
        payment_class = cls._payment_types.get(payment_type)
        if not payment_class:
            raise ValueError(f"Unknown payment type: {payment_type}")
        return payment_class(**kwargs)

# Usage
payment = PaymentFactory.create('credit_card', card_number='1234')
```

---

### 4. Strategy Pattern

**Purpose:** Define family of algorithms, encapsulate each one, make them interchangeable.

```python
# strategies/discount_strategy.py
from abc import ABC, abstractmethod

class DiscountStrategy(ABC):
    """Abstract discount strategy."""
    @abstractmethod
    def calculate(self, amount: float) -> float:
        pass

class NoDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return amount

class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: float):
        self._percentage = percentage

    def calculate(self, amount: float) -> float:
        return amount * (1 - self._percentage)

class FixedDiscount(DiscountStrategy):
    def __init__(self, discount_amount: float):
        self._discount = discount_amount

    def calculate(self, amount: float) -> float:
        return max(0, amount - self._discount)

# Usage in Order class
class Order:
    def __init__(self, discount_strategy: DiscountStrategy):
        self._discount_strategy = discount_strategy
        self._items = []

    def calculate_total(self) -> float:
        subtotal = sum(item.price for item in self._items)
        return self._discount_strategy.calculate(subtotal)
```

---

## Project Structure

### Well-Organized OOP Project

```
project/
├── models/                 # Domain models
│   ├── __init__.py
│   ├── user.py
│   ├── product.py
│   └── order.py
├── repositories/           # Data access layer
│   ├── __init__.py
│   ├── base_repository.py
│   ├── user_repository.py
│   └── product_repository.py
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── user_service.py
│   ├── order_service.py
│   └── payment_service.py
├── interfaces/            # Abstract interfaces/protocols
│   ├── __init__.py
│   ├── repository_interface.py
│   └── payment_interface.py
├── factories/             # Object creation
│   ├── __init__.py
│   └── payment_factory.py
├── strategies/            # Strategy implementations
│   ├── __init__.py
│   └── discount_strategy.py
├── validators/            # Validation logic
│   ├── __init__.py
│   └── user_validator.py
├── exceptions/            # Custom exceptions
│   ├── __init__.py
│   └── custom_exceptions.py
├── utils/                 # Utility functions (minimal!)
│   ├── __init__.py
│   └── helpers.py
├── config/                # Configuration
│   ├── __init__.py
│   └── settings.py
├── tests/                 # Mirror structure
│   ├── test_models/
│   ├── test_repositories/
│   └── test_services/
└── main.py               # Entry point
```

---

## Anti-Patterns to Avoid

### 1. God Object

**Problem:** One class doing everything.

```python
# BAD
class Application:
    def __init__(self):
        self.users = []
        self.products = []
        self.orders = []

    def add_user(self): pass
    def delete_user(self): pass
    def validate_user(self): pass
    def send_email(self): pass
    def process_payment(self): pass
    def generate_report(self): pass
    def backup_database(self): pass
    # ... 50 more methods

# GOOD: Separate concerns
class UserManager: pass
class ProductManager: pass
class OrderManager: pass
class EmailService: pass
class PaymentService: pass
class ReportService: pass
class BackupService: pass
```

---

### 2. Anemic Domain Model

**Problem:** Models with no behavior, just data.

```python
# BAD: Anemic model
@dataclass
class Order:
    id: int
    items: List[Item]
    total: float

# All logic elsewhere
def calculate_order_total(order):
    return sum(item.price for item in order.items)

def validate_order(order):
    return len(order.items) > 0

# GOOD: Rich domain model
@dataclass
class Order:
    id: int
    items: List[Item]

    def calculate_total(self) -> float:
        """Calculate order total."""
        return sum(item.price * item.quantity for item in self.items)

    def is_valid(self) -> bool:
        """Validate order."""
        return len(self.items) > 0 and all(item.quantity > 0 for item in self.items)

    def add_item(self, item: Item) -> None:
        """Add item to order."""
        self.items.append(item)
```

---

### 3. Global State

**Problem:** Using global variables instead of proper encapsulation.

```python
# BAD
db_connection = None
current_user = None
app_config = {}

def init_app():
    global db_connection, app_config
    db_connection = connect_to_db()
    app_config = load_config()

# GOOD: Dependency injection
class Application:
    def __init__(self, config: Config, db: Database):
        self._config = config
        self._db = db
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user
```

---

## Encapsulation Best Practices

### Use Private Members

```python
class BankAccount:
    """Properly encapsulated bank account."""

    def __init__(self, account_number: str, initial_balance: float):
        self._account_number = account_number  # Protected
        self.__balance = initial_balance        # Private
        self._transactions: List[Transaction] = []

    @property
    def balance(self) -> float:
        """Read-only access to balance."""
        return self.__balance

    def deposit(self, amount: float) -> None:
        """Deposit money with validation."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.__balance += amount
        self._record_transaction("deposit", amount)

    def withdraw(self, amount: float) -> bool:
        """Withdraw money with validation."""
        if amount > self.__balance:
            return False
        self.__balance -= amount
        self._record_transaction("withdrawal", amount)
        return True

    def _record_transaction(self, type: str, amount: float) -> None:
        """Internal method for recording transactions."""
        self._transactions.append(Transaction(type, amount, datetime.now()))
```

---

## Composition Over Inheritance

```python
# BAD: Deep inheritance hierarchy
class Animal: pass
class Mammal(Animal): pass
class Dog(Mammal): pass
class ServiceDog(Dog): pass
class GuideDog(ServiceDog): pass

# GOOD: Composition
class Animal:
    def __init__(self, locomotion: Locomotion, communication: Communication):
        self._locomotion = locomotion
        self._communication = communication

    def move(self):
        self._locomotion.move()

    def communicate(self):
        self._communication.communicate()

# Flexible composition
dog = Animal(
    locomotion=WalkingLocomotion(),
    communication=BarkingCommunication()
)
```

---

## Summary: OOP Checklist

When refactoring to OOP:

✅ **Separate Concerns**
- Models (domain objects)
- Repositories (data access)
- Services (business logic)
- Controllers/Views (presentation)

✅ **Apply SOLID Principles**
- Single Responsibility
- Open/Closed
- Liskov Substitution
- Interface Segregation
- Dependency Inversion

✅ **Use Design Patterns**
- Repository Pattern
- Service Layer
- Factory Pattern
- Strategy Pattern

✅ **Proper Encapsulation**
- Private members (`__`)
- Protected members (`_`)
- Properties for controlled access
- No global state

✅ **Clear Structure**
- Organized folder structure
- Modules by responsibility
- Clear naming conventions
- Dependency injection

✅ **Avoid Anti-Patterns**
- No God Objects
- No Anemic Models
- No Global State
- No Deep Inheritance
- No Spaghetti Code

**Result:** Maintainable, testable, extensible OOP codebase! 🎯
