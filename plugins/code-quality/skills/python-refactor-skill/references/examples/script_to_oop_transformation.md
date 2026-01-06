# Script-Like to OOP Transformation: Complete Example

This document demonstrates a complete transformation from script-like, procedural "spaghetti code" to clean, well-structured OOP architecture.

## Overview

**Before:**
- Single file with scattered functions
- Global state
- No clear structure or boundaries
- Difficult to test, maintain, and extend

**After:**
- Organized modules with clear responsibilities
- Proper class hierarchy with encapsulation
- Dependency injection
- Testable, maintainable, extensible

---

## BEFORE: Script-Like Code (Spaghetti Code)

### File: `user_processor.py` (Single file, ~200 lines)

```python
"""
Script to process user data from API and generate reports.
"""
import requests
import json
from datetime import datetime

# Global state - DANGER!
users_cache = {}
failed_users = []
CONFIG = None
db_connection = None
API_BASE_URL = "https://api.example.com"
RETRY_COUNT = 3
TIMEOUT = 30

def init():
    """Initialize global state."""
    global CONFIG, db_connection
    with open('config.json') as f:
        CONFIG = json.load(f)
    db_connection = create_db_connection()

def create_db_connection():
    """Create database connection."""
    # Direct database access
    import psycopg2
    return psycopg2.connect(
        host=CONFIG['db_host'],
        database=CONFIG['db_name'],
        user=CONFIG['db_user'],
        password=CONFIG['db_pass']
    )

def fetch_user(user_id):
    """Fetch user from API."""
    global users_cache

    # Check cache
    if user_id in users_cache:
        return users_cache[user_id]

    # Make API call
    url = f"{API_BASE_URL}/users/{user_id}"
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                users_cache[user_id] = data
                return data
            elif response.status_code == 404:
                return None
        except:
            if attempt == RETRY_COUNT - 1:
                return None
            continue
    return None

def validate_user(user_data):
    """Validate user data."""
    if not user_data:
        return False
    if not user_data.get('email'):
        return False
    if '@' not in user_data['email']:
        return False
    if not user_data.get('status'):
        return False
    if user_data['status'] not in ['active', 'inactive', 'pending']:
        return False
    return True

def process_user(user_id):
    """Process a single user."""
    global failed_users, db_connection

    # Fetch user
    user = fetch_user(user_id)
    if not user:
        failed_users.append(user_id)
        return None

    # Validate
    if not validate_user(user):
        failed_users.append(user_id)
        return None

    # Transform data
    processed = {
        'user_id': user['id'],
        'email': user['email'],
        'name': user.get('first_name', '') + ' ' + user.get('last_name', ''),
        'status': user['status'],
        'created_at': user.get('created_at'),
        'last_login': user.get('last_login'),
        'is_premium': user.get('subscription_tier') == 'premium'
    }

    # Save to database
    cursor = db_connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO processed_users
            (user_id, email, name, status, created_at, last_login, is_premium)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                email = EXCLUDED.email,
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                last_login = EXCLUDED.last_login,
                is_premium = EXCLUDED.is_premium
        """, (
            processed['user_id'],
            processed['email'],
            processed['name'],
            processed['status'],
            processed['created_at'],
            processed['last_login'],
            processed['is_premium']
        ))
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        failed_users.append(user_id)
        return None

    return processed

def process_users_batch(user_ids):
    """Process multiple users."""
    results = []
    for user_id in user_ids:
        result = process_user(user_id)
        if result:
            results.append(result)
    return results

def generate_report():
    """Generate processing report."""
    global users_cache, failed_users

    total_cached = len(users_cache)
    total_failed = len(failed_users)
    total_processed = total_cached - total_failed

    report = {
        'timestamp': datetime.now().isoformat(),
        'total_processed': total_processed,
        'total_failed': total_failed,
        'success_rate': (total_processed / total_cached * 100) if total_cached > 0 else 0,
        'failed_user_ids': failed_users
    }

    # Save report
    with open(f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(report, f, indent=2)

    return report

def cleanup():
    """Cleanup resources."""
    global db_connection, users_cache, failed_users
    if db_connection:
        db_connection.close()
    users_cache.clear()
    failed_users.clear()

# Script execution
if __name__ == "__main__":
    try:
        init()

        # Get user IDs from file
        with open('user_ids.txt') as f:
            user_ids = [int(line.strip()) for line in f if line.strip()]

        # Process users
        results = process_users_batch(user_ids)

        # Generate report
        report = generate_report()
        print(f"Processed {report['total_processed']} users")
        print(f"Failed: {report['total_failed']}")
        print(f"Success rate: {report['success_rate']:.1f}%")

    finally:
        cleanup()
```

### Problems with the Script-Like Approach:

1. **Global State Everywhere** - `users_cache`, `failed_users`, `CONFIG`, `db_connection`
2. **No Structure** - Everything in one file
3. **No Separation of Concerns** - HTTP, validation, database, reporting all mixed
4. **Impossible to Test** - Functions depend on global state
5. **No Dependency Injection** - Hard-coded dependencies
6. **Poor Error Handling** - Generic exceptions, silent failures
7. **No Type Safety** - No type hints
8. **Poor Reusability** - Can't reuse components
9. **Difficult to Extend** - Adding features affects everything
10. **No Clear Boundaries** - Function responsibilities unclear

---

## AFTER: OOP-Based Architecture

### Project Structure

```
user_processor/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── user.py
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py
│   └── database_repository.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── report_service.py
├── clients/
│   ├── __init__.py
│   └── api_client.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── main.py
```

### 1. Models (Domain Objects)

**File: `models/user.py`**

```python
"""User domain models."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserStatus(Enum):
    """User status enumeration."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'


@dataclass
class User:
    """User domain model."""
    id: int
    email: str
    first_name: str
    last_name: str
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime]
    subscription_tier: str

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription."""
        return self.subscription_tier == 'premium'

    def is_valid(self) -> bool:
        """Validate user data."""
        if not self.email or '@' not in self.email:
            return False
        if not self.status:
            return False
        return True


@dataclass
class ProcessedUser:
    """Processed user result."""
    user_id: int
    email: str
    name: str
    status: str
    created_at: datetime
    last_login: Optional[datetime]
    is_premium: bool

    @classmethod
    def from_user(cls, user: User) -> 'ProcessedUser':
        """Create from User domain model."""
        return cls(
            user_id=user.id,
            email=user.email,
            name=user.full_name,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
            is_premium=user.is_premium
        )
```

### 2. Configuration

**File: `config/settings.py`**

```python
"""Application settings."""
from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    database: str
    user: str
    password: str
    port: int = 5432


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str
    timeout: int = 30
    retry_count: int = 3


@dataclass
class Settings:
    """Application settings."""
    database: DatabaseConfig
    api: APIConfig

    @classmethod
    def load_from_file(cls, config_path: str = 'config.json') -> 'Settings':
        """Load settings from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Settings instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(path) as f:
                data = json.load(f)

            return cls(
                database=DatabaseConfig(
                    host=data['db_host'],
                    database=data['db_name'],
                    user=data['db_user'],
                    password=data['db_pass'],
                    port=data.get('db_port', 5432)
                ),
                api=APIConfig(
                    base_url=data.get('api_base_url', 'https://api.example.com'),
                    timeout=data.get('api_timeout', 30),
                    retry_count=data.get('api_retry_count', 3)
                )
            )
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid config file: {e}")
```

### 3. API Client (External Service Access)

**File: `clients/api_client.py`**

```python
"""HTTP API client."""
import requests
from typing import Optional, Dict, Any
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class APIClient:
    """HTTP API client with retry logic."""

    def __init__(self, base_url: str, timeout: int = 30, retry_count: int = 3):
        """Initialize API client.

        Args:
            base_url: Base URL for API
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts
        """
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._session = self._create_session(retry_count)

    def _create_session(self, retry_count: int) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=retry_count,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make GET request.

        Args:
            endpoint: API endpoint (e.g., '/users/123')

        Returns:
            Response data as dictionary, or None if not found

        Raises:
            APIError: If request fails
        """
        url = f"{self._base_url}{endpoint}"

        try:
            response = self._session.get(url, timeout=self._timeout)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.info(f"Resource not found: {url}")
                return None
            else:
                logger.error(f"API request failed: {response.status_code} - {url}")
                raise APIError(f"API returned status {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise APIError(f"Request failed: {e}")

    def close(self):
        """Close session and cleanup resources."""
        self._session.close()


class APIError(Exception):
    """API-related error."""
    pass
```

### 4. Repositories (Data Access)

**File: `repositories/user_repository.py`**

```python
"""User data repository."""
from typing import Optional, Dict
import logging
from ..models.user import User, UserStatus
from ..clients.api_client import APIClient, APIError
from datetime import datetime


logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for accessing user data from API."""

    def __init__(self, api_client: APIClient):
        """Initialize user repository.

        Args:
            api_client: API client for making HTTP requests
        """
        self._api_client = api_client
        self._cache: Dict[int, User] = {}

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User instance if found, None otherwise

        Raises:
            UserRepositoryError: If data access fails
        """
        # Check cache first
        if user_id in self._cache:
            logger.debug(f"User {user_id} found in cache")
            return self._cache[user_id]

        # Fetch from API
        try:
            data = self._api_client.get(f"/users/{user_id}")
            if not data:
                logger.info(f"User {user_id} not found")
                return None

            # Convert to domain model
            user = self._data_to_user(data)

            # Cache result
            self._cache[user_id] = user

            return user

        except APIError as e:
            logger.error(f"Failed to fetch user {user_id}: {e}")
            raise UserRepositoryError(f"Failed to fetch user: {e}")

    def _data_to_user(self, data: dict) -> User:
        """Convert API data to User domain model."""
        return User(
            id=data['id'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            status=UserStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            subscription_tier=data.get('subscription_tier', 'free')
        )

    def clear_cache(self):
        """Clear user cache."""
        self._cache.clear()


class UserRepositoryError(Exception):
    """User repository error."""
    pass
```

**File: `repositories/database_repository.py`**

```python
"""Database repository for storing processed users."""
import psycopg2
from typing import Optional, List
import logging
from ..models.user import ProcessedUser
from ..config.settings import DatabaseConfig


logger = logging.getLogger(__name__)


class DatabaseRepository:
    """Repository for database operations."""

    def __init__(self, config: DatabaseConfig):
        """Initialize database repository.

        Args:
            config: Database configuration
        """
        self._config = config
        self._connection = None

    def connect(self):
        """Establish database connection."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    host=self._config.host,
                    database=self._config.database,
                    user=self._config.user,
                    password=self._config.password,
                    port=self._config.port
                )
                logger.info("Database connection established")
            except psycopg2.Error as e:
                logger.error(f"Database connection failed: {e}")
                raise DatabaseError(f"Connection failed: {e}")

    def save_user(self, user: ProcessedUser) -> bool:
        """Save processed user to database.

        Args:
            user: Processed user data

        Returns:
            True if successful, False otherwise
        """
        if not self._connection or self._connection.closed:
            raise DatabaseError("No database connection")

        cursor = self._connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO processed_users
                (user_id, email, name, status, created_at, last_login, is_premium)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    email = EXCLUDED.email,
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    last_login = EXCLUDED.last_login,
                    is_premium = EXCLUDED.is_premium
            """, (
                user.user_id,
                user.email,
                user.name,
                user.status,
                user.created_at,
                user.last_login,
                user.is_premium
            ))
            self._connection.commit()
            logger.debug(f"Saved user {user.user_id} to database")
            return True

        except psycopg2.Error as e:
            self._connection.rollback()
            logger.error(f"Failed to save user {user.user_id}: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")


class DatabaseError(Exception):
    """Database operation error."""
    pass
```

### 5. Services (Business Logic)

**File: `services/user_service.py`**

```python
"""User processing service."""
from typing import List, Optional
import logging
from ..models.user import User, ProcessedUser
from ..repositories.user_repository import UserRepository, UserRepositoryError
from ..repositories.database_repository import DatabaseRepository


logger = logging.getLogger(__name__)


class UserService:
    """Service for processing users."""

    def __init__(
        self,
        user_repository: UserRepository,
        database_repository: DatabaseRepository
    ):
        """Initialize user service.

        Args:
            user_repository: Repository for fetching user data
            database_repository: Repository for storing processed users
        """
        self._user_repo = user_repository
        self._db_repo = database_repository
        self._failed_user_ids: List[int] = []

    def process_user(self, user_id: int) -> Optional[ProcessedUser]:
        """Process a single user.

        Args:
            user_id: User identifier

        Returns:
            ProcessedUser if successful, None otherwise
        """
        try:
            # Fetch user
            user = self._user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                self._failed_user_ids.append(user_id)
                return None

            # Validate
            if not user.is_valid():
                logger.warning(f"User {user_id} validation failed")
                self._failed_user_ids.append(user_id)
                return None

            # Transform
            processed = ProcessedUser.from_user(user)

            # Save
            if not self._db_repo.save_user(processed):
                logger.error(f"Failed to save user {user_id}")
                self._failed_user_ids.append(user_id)
                return None

            logger.info(f"Successfully processed user {user_id}")
            return processed

        except UserRepositoryError as e:
            logger.error(f"Error processing user {user_id}: {e}")
            self._failed_user_ids.append(user_id)
            return None

    def process_batch(self, user_ids: List[int]) -> List[ProcessedUser]:
        """Process multiple users.

        Args:
            user_ids: List of user identifiers

        Returns:
            List of successfully processed users
        """
        results = []

        for user_id in user_ids:
            result = self.process_user(user_id)
            if result:
                results.append(result)

        logger.info(f"Processed {len(results)} of {len(user_ids)} users")
        return results

    @property
    def failed_user_ids(self) -> List[int]:
        """Get list of failed user IDs."""
        return self._failed_user_ids.copy()

    def clear_failed(self):
        """Clear failed user IDs list."""
        self._failed_user_ids.clear()
```

**File: `services/report_service.py`**

```python
"""Report generation service."""
from dataclasses import dataclass
from datetime import datetime
from typing import List
import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class ProcessingReport:
    """Report of user processing results."""
    timestamp: datetime
    total_processed: int
    total_failed: int
    success_rate: float
    failed_user_ids: List[int]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_processed': self.total_processed,
            'total_failed': self.total_failed,
            'success_rate': self.success_rate,
            'failed_user_ids': self.failed_user_ids
        }


class ReportService:
    """Service for generating processing reports."""

    def __init__(self, output_dir: str = '.'):
        """Initialize report service.

        Args:
            output_dir: Directory for saving reports
        """
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(exist_ok=True)

    def generate_report(
        self,
        total_processed: int,
        failed_user_ids: List[int]
    ) -> ProcessingReport:
        """Generate processing report.

        Args:
            total_processed: Number of successfully processed users
            failed_user_ids: List of failed user IDs

        Returns:
            Processing report
        """
        total_failed = len(failed_user_ids)
        total_users = total_processed + total_failed

        success_rate = (
            (total_processed / total_users * 100)
            if total_users > 0
            else 0.0
        )

        report = ProcessingReport(
            timestamp=datetime.now(),
            total_processed=total_processed,
            total_failed=total_failed,
            success_rate=success_rate,
            failed_user_ids=failed_user_ids
        )

        # Save to file
        self._save_report(report)

        return report

    def _save_report(self, report: ProcessingReport):
        """Save report to file."""
        filename = f"report_{report.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self._output_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            logger.info(f"Report saved to {filepath}")
        except IOError as e:
            logger.error(f"Failed to save report: {e}")
```

### 6. Main Application

**File: `main.py`**

```python
"""Main application entry point."""
import logging
from pathlib import Path
from typing import List

from .config.settings import Settings
from .clients.api_client import APIClient
from .repositories.user_repository import UserRepository
from .repositories.database_repository import DatabaseRepository
from .services.user_service import UserService
from .services.report_service import ReportService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Application:
    """Main application class."""

    def __init__(self, config_path: str = 'config.json'):
        """Initialize application.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.settings = Settings.load_from_file(config_path)

        # Initialize components
        self.api_client = APIClient(
            base_url=self.settings.api.base_url,
            timeout=self.settings.api.timeout,
            retry_count=self.settings.api.retry_count
        )

        self.user_repository = UserRepository(self.api_client)

        self.db_repository = DatabaseRepository(self.settings.database)

        self.user_service = UserService(
            user_repository=self.user_repository,
            database_repository=self.db_repository
        )

        self.report_service = ReportService()

    def run(self, user_ids_file: str = 'user_ids.txt'):
        """Run user processing.

        Args:
            user_ids_file: Path to file containing user IDs
        """
        try:
            # Connect to database
            self.db_repository.connect()

            # Load user IDs
            user_ids = self._load_user_ids(user_ids_file)
            logger.info(f"Loaded {len(user_ids)} user IDs")

            # Process users
            results = self.user_service.process_batch(user_ids)
            logger.info(f"Processed {len(results)} users")

            # Generate report
            report = self.report_service.generate_report(
                total_processed=len(results),
                failed_user_ids=self.user_service.failed_user_ids
            )

            # Print summary
            print(f"\nProcessing Summary:")
            print(f"  Total processed: {report.total_processed}")
            print(f"  Total failed: {report.total_failed}")
            print(f"  Success rate: {report.success_rate:.1f}%")

            if report.failed_user_ids:
                print(f"\nFailed user IDs: {report.failed_user_ids}")

        finally:
            # Cleanup
            self.cleanup()

    def _load_user_ids(self, filepath: str) -> List[int]:
        """Load user IDs from file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"User IDs file not found: {filepath}")

        with open(path) as f:
            user_ids = [
                int(line.strip())
                for line in f
                if line.strip() and line.strip().isdigit()
            ]

        return user_ids

    def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up resources...")
        self.api_client.close()
        self.db_repository.close()
        self.user_repository.clear_cache()
        logger.info("Cleanup complete")


def main():
    """Application entry point."""
    try:
        app = Application()
        app.run()
    except Exception as e:
        logger.exception(f"Application failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
```

---

## Comparison: Benefits of OOP Approach

| Aspect | Script-Like | OOP-Based |
|--------|-------------|-----------|
| **Structure** | Single file, scattered functions | Organized modules with clear boundaries |
| **State Management** | Global variables | Encapsulated in classes |
| **Testing** | Impossible (global state) | Easy (dependency injection) |
| **Reusability** | Functions tied to globals | Components can be reused anywhere |
| **Maintainability** | Changes affect everything | Changes isolated to modules |
| **Extensibility** | Difficult to add features | Easy to extend with new classes |
| **Error Handling** | Generic, silent failures | Specific exceptions with context |
| **Type Safety** | No type hints | Comprehensive type hints |
| **Dependency Management** | Hard-coded dependencies | Injected dependencies |
| **Readability** | Must read entire file | Clear from class/module names |
| **Separation of Concerns** | All mixed together | Clear layers (models, repos, services) |
| **Configuration** | Global variables | Typed configuration classes |

---

## Key OOP Principles Applied

### 1. Single Responsibility Principle (SRP)
- Each class has one clear responsibility
- `UserRepository` only fetches user data
- `DatabaseRepository` only handles database operations
- `UserService` only contains business logic
- `ReportService` only generates reports

### 2. Dependency Injection
- Dependencies passed through constructors
- No hard-coded dependencies
- Easy to test with mocks
- Easy to swap implementations

### 3. Separation of Concerns
- **Models**: Domain objects and data structures
- **Repositories**: Data access layer
- **Services**: Business logic layer
- **Clients**: External service access
- **Config**: Configuration management

### 4. Encapsulation
- Private state (`_cache`, `_connection`)
- Public interfaces only
- Implementation details hidden

### 5. Domain-Driven Design
- Rich domain models (`User`, `ProcessedUser`)
- Value objects (`UserStatus`)
- Clear domain language

### 6. Layered Architecture
```
┌─────────────────────────┐
│   Application Layer     │  ← main.py
│   (Orchestration)       │
├─────────────────────────┤
│   Service Layer         │  ← Business Logic
│   (Business Logic)      │
├─────────────────────────┤
│   Repository Layer      │  ← Data Access
│   (Data Access)         │
├─────────────────────────┤
│   Infrastructure Layer  │  ← External Services
│   (API, Database)       │
└─────────────────────────┘
```

---

## Testing Comparison

### Script-Like Testing (Impossible)

```python
# Can't test - depends on globals!
def test_process_user():
    global users_cache, failed_users, db_connection
    # How do we mock these?
    result = process_user(123)
    # What if it makes real API calls?
```

### OOP Testing (Easy)

```python
from unittest.mock import Mock
import pytest

def test_user_service_process_user_success():
    # Arrange
    mock_user_repo = Mock(spec=UserRepository)
    mock_db_repo = Mock(spec=DatabaseRepository)

    user = User(
        id=123,
        email='test@example.com',
        first_name='John',
        last_name='Doe',
        status=UserStatus.ACTIVE,
        # ...
    )
    mock_user_repo.get_by_id.return_value = user
    mock_db_repo.save_user.return_value = True

    service = UserService(mock_user_repo, mock_db_repo)

    # Act
    result = service.process_user(123)

    # Assert
    assert result is not None
    assert result.user_id == 123
    mock_user_repo.get_by_id.assert_called_once_with(123)
    mock_db_repo.save_user.assert_called_once()


def test_user_service_process_user_not_found():
    # Arrange
    mock_user_repo = Mock(spec=UserRepository)
    mock_db_repo = Mock(spec=DatabaseRepository)

    mock_user_repo.get_by_id.return_value = None

    service = UserService(mock_user_repo, mock_db_repo)

    # Act
    result = service.process_user(999)

    # Assert
    assert result is None
    assert 999 in service.failed_user_ids
```

---

## Summary

**Script-Like Code Problems:**
- Global state everywhere
- No structure or organization
- Impossible to test
- Difficult to maintain and extend
- Poor error handling
- No reusability

**OOP Architecture Benefits:**
- Clear structure and organization
- Proper encapsulation and boundaries
- Easy to test with dependency injection
- Maintainable and extensible
- Proper error handling with typed exceptions
- Reusable components
- Type-safe with comprehensive type hints
- Follows SOLID principles
- Clean separation of concerns

**The transformation demonstrates how OOP principles create code that is:**
1. **Readable** - Clear structure and naming
2. **Maintainable** - Changes isolated to specific modules
3. **Testable** - Dependencies can be mocked
4. **Extensible** - Easy to add new features
5. **Professional** - Industry-standard architecture patterns
