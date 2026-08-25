# Pytest Infrastructure Patterns

Patterns for test infrastructure that prevent environment hangs, mock ordering bugs, and incomplete service isolation.

## 1. Conftest Execution Order

### How pytest discovers conftest files

pytest processes conftest.py files top-down by directory depth:

1. `tests/conftest.py` (root) -- runs FIRST
2. `tests/unit/conftest.py` -- runs when unit/ tests are collected
3. `tests/unit/handlers/conftest.py` -- runs when handlers/ tests are collected

### The sys.modules race condition

```
tests/
  conftest.py                  # (A) runs FIRST -- but has NO heavy mocks
  test_csp_ortools.py          # (B) collected EARLY -- triggers `import ortools` at collection time
  unit/
    conftest.py                # (C) runs SECOND -- tries to mock ortools, but sys.modules already has real ortools
    test_optimizer.py
```

Step by step:
1. pytest discovers `tests/conftest.py` (A) and executes it
2. pytest collects `tests/test_csp_ortools.py` (B) -- Python executes module-level imports, loading real `ortools` into `sys.modules`
3. pytest discovers `tests/unit/conftest.py` (C) and executes it -- the guard `if "ortools" not in sys.modules` sees the real module and skips mocking
4. Tests fail because they get the real module instead of the mock

### Rule: All heavy mocks in root conftest

```python
# tests/conftest.py (ROOT -- runs first, before any test collection)
import sys
from unittest.mock import MagicMock

# Mock heavy native deps BEFORE any test file imports them
for _mod in ("ortools", "ortools.sat", "ortools.sat.python", "ortools.sat.python.cp_model",
             "scipy", "scipy.optimize", "prometheus_client"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
```

## 2. Heavy Native Dependency Strategy

### Dependencies that require mocking by default

| Category | Examples | Risk |
|----------|----------|------|
| Scientific computing | scipy, ortools, numpy (heavy parts) | Import hang, slow init |
| ML frameworks | torch, tensorflow, transformers | GPU init, massive import time |
| Monitoring | prometheus_client, opentelemetry | Global state, collectors |
| Cloud SDKs | google.cloud.*, boto3, firebase_admin | Auth checks, credential subprocess |

### Opting in to real deps

Tests needing the real dependency must be marked:

```python
pytestmark = pytest.mark.slow

# or per-test:
@pytest.mark.slow
def test_optimization_with_real_scipy():
    from scipy.optimize import minimize
    result = minimize(objective, x0)
    assert result.success
```

Default `addopts` in pyproject.toml: `-m 'not slow and not e2e'`

## 3. Platform and Environment Safety

### Known platform traps

| Trap | Environment | Symptom |
|------|-------------|---------|
| `platform._wmi_query()` | Python 3.13 + Windows 11 | Infinite hang before conftest |
| `google.auth.default()` | No gcloud credentials | Subprocess hang |
| `subprocess.run("gcloud ...")` | CI without SDK | Timeout |

### Pre-pytest monkey-patching

```python
# run_tests.py -- execute BEFORE pytest.main()
import platform
# Prevent WMI hang on Windows 11 + Python 3.13
if hasattr(platform, "_wmi_query"):
    platform._wmi_query = lambda *a, **kw: ""

import pytest
sys.exit(pytest.main(sys.argv[1:]))
```

### conftest.py is too late for plugin-level calls

Plugins like pyreadline3 and pytest-metadata execute during pytest's own initialization, before any conftest.py runs. If they call `platform.platform()` or `platform.processor()`, conftest cannot intercept them. The only fix is a test runner wrapper.

## 4. Mock Target Decision Tree

### Standard import (module-level)

```python
# app/services/user_service.py
from app.clients.stripe import charge_customer  # module-level import

# Test: patch where USED
@patch("app.services.user_service.charge_customer")
```

### Lazy import (inside function)

```python
# app/services/user_service.py
def process_payment():
    from app.clients.stripe import charge_customer  # lazy import
    return charge_customer(...)

# Test: patch where DEFINED
@patch("app.clients.stripe.charge_customer")
```

### Decision rule

1. Find the import statement for the dependency
2. Is it at module top-level? -- Patch where used (the importing module)
3. Is it inside a function body? -- Patch where defined (the source module)
4. If `monkeypatch.setattr` raises AttributeError -- the target is a lazy import, switch to definition site

## 5. External Service Audit Checklist

Before finalizing an integration test conftest, enumerate every external service:

- [ ] Database connections (MongoDB, PostgreSQL, Redis)
- [ ] Authentication providers (Firebase Auth, Auth0, OAuth)
- [ ] Cloud storage (Firebase Storage, S3, GCS)
- [ ] Message queues (RabbitMQ, Kafka, SQS)
- [ ] Payment processors (Stripe, PayPal)
- [ ] Email/SMS services (SendGrid, Twilio)
- [ ] Search engines (Elasticsearch, Algolia)
- [ ] Monitoring/telemetry (Prometheus, DataDog, Sentry)
- [ ] External APIs (Google Maps, OpenAI, etc.)

For each, verify the mock exists in conftest and uses `autouse=True`.

### Audit technique

```bash
# Find all external service imports in the app
grep -rn "import.*firebase\|import.*google\|import.*boto3\|import.*stripe\|import.*mongo\|import.*redis" src/
```

Cross-reference against conftest mocks. Every match must have a corresponding mock.
