---
name: pydantic-v2
description: >
  Deep reference for the data layer of a production service.
  TRIGGER WHEN: writing or refactoring Pydantic v2 models in Python 3.10+; migrating a codebase from Pydantic v1 to v2; choosing between `Annotated[Decimal, ...]` and `condecimal` for money; hitting v2 validator, serialization or performance surprises; designing FastAPI request/response schemas or error envelopes.
  DO NOT TRIGGER WHEN: the task is Python testing (use python-tdd) or non-Python schema work (use typescript-development).
---

# Pydantic v2

Pydantic v2 (released 2023-06, current stable **2.13** as of 2026-04-19, paired with Python 3.10-3.14 including 3.14 free-threaded builds) is a near-complete rewrite on `pydantic-core` (Rust). API is similar but not identical to v1 -- several v1 patterns silently break or behave differently. This skill documents the v2 idioms, the v1 migration gotchas, and the FastAPI integration surface.

Notable recent releases:
- **2.11** (2025): 2x schema build-time improvements, 2-5x memory reduction for nested models, PEP 695/696 generic syntax, experimental free-threaded Python 3.13, `validate_by_alias` / `validate_by_name` / `serialize_by_alias` config (`populate_by_name` pending v3 deprecation), `Path` and `deque` no longer accept constraints ([2.11 release](https://pydantic.dev/articles/pydantic-v2-11-release)).
- **2.12**: Python 3.14 support (PEP 649/749 annotations), experimental `MISSING` sentinel, `exclude_if` on fields, `ensure_ascii` on JSON output, `serialize_as_any` unified behavior, `@model_validator(mode="after")` classmethod deprecated -- write as instance method ([2.12 release](https://pydantic.dev/articles/pydantic-v2-12-release)).
- **2.13** (April 2026): **Polymorphic serialization** (`model_dump(polymorphic_serialization=True)`), `exclude_if` extended to computed fields, `ascii_only` in `StringConstraints`, `model_fields_set` tracks post-instantiation extras ([2.13 release](https://pydantic.dev/articles/pydantic-v2-13-release)).

## When to load which section

- Writing a new model from scratch -> "Core model patterns" + "Validators"
- Migrating from v1 -> "v1 -> v2 migration checklist"
- Working with money / decimals -> "Monetary precision (CWE-681 defense)"
- FastAPI request/response models -> "FastAPI integration"
- Performance-sensitive hot path -> "Performance notes"
- Secret handling / redaction -> "Security and secrets"
- Validation observability or LLM agents -> "PydanticAI and Logfire"

## Core model patterns

```python
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
    model_validator,
)

# Type aliases with constraints -- preferred in v2 over `constr()` / `conint()`
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
USDAmount = Annotated[Decimal, Field(max_digits=14, decimal_places=2, ge=0)]

class LineItem(BaseModel):
    # model_config replaces inner `Config` class
    model_config = ConfigDict(
        strict=True,               # refuse string "1" for int field
        frozen=True,               # hashable + immutable
        populate_by_name=True,     # accept alias AND field name
        str_strip_whitespace=True, # strip on all str fields
        extra="forbid",            # reject unknown keys
    )

    sku: NonEmptyStr
    quantity: int = Field(ge=1)
    unit_price: USDAmount
    currency: Literal["USD", "EUR", "GBP"] = "USD"

    @computed_field
    @property
    def total(self) -> USDAmount:
        return self.unit_price * self.quantity

    @field_validator("sku")
    @classmethod
    def sku_format(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("sku must be alphanumeric")
        return v.upper()

    @model_validator(mode="after")
    def cross_field_check(self) -> "LineItem":
        if self.currency == "USD" and self.unit_price > Decimal("10000"):
            raise ValueError("USD line item exceeds single-item limit")
        return self
```

### Key points

- `model_config = ConfigDict(...)` replaces the v1 inner `class Config:` pattern. Importing `ConfigDict` gives you autocomplete.
- `Annotated[T, Field(...)]` or `Annotated[T, StringConstraints(...)]` is the idiomatic v2 way to attach constraints -- prefer over `constr()`, `conint()`, `condecimal()` wrappers (still supported, but Annotated composes better with Python's type system).
- `@computed_field` replaces the v1 `@property` + `validator(always=True)` dance; shows up in `model_dump()` automatically.
- `@field_validator("field_name")` replaces v1 `@validator("field_name")`. Decorator is classmethod; must have `@classmethod` decorator after `@field_validator`.
- `@model_validator(mode="before" | "after")` replaces v1 `@root_validator(pre=True | False)`. In `mode="after"` the method returns `self`, not a dict. **Note (2.12+): `@classmethod` on `mode="after"` is deprecated -- write as a plain instance method.**
- **Prefer `validate_by_alias` / `validate_by_name` / `serialize_by_alias`** (2.11+) over the legacy `populate_by_name=True`. The latter is pending deprecation in v3.
- `Path` and `deque` no longer accept Field constraints (2.11+) -- use a custom validator for length / pattern checks.
- `MISSING` sentinel (2.12, experimental) lets you distinguish "not provided" from "explicit default" at validator time.

## Validators

### Mode decision rules

| Mode | When to use | Performance | Returns |
|------|------------|-------------|---------|
| `after` (default) | 90% of cases -- logic on already-coerced value | Fast | Same type as field |
| `before` | Reshape raw input (string split, legacy key mapping) | Python callback overhead | Any (will be type-coerced afterward) |
| `wrap` | Catch `ValidationError`, add logging, force `PydanticUseDefault` | Slowest -- materializes data in Python | Same type as field |
| `plain` | Fully custom, no coercion, no downstream validators | N/A (terminates validation) | **Trusted as-is** -- dangerous for type safety |

**Performance rule:** express constraints in `Field(...)` or Annotated metadata whenever possible -- the Rust engine handles them. Python-level validators (`@field_validator`, `mode="before"`, `mode="wrap"`) incur per-value Python-call overhead ([Performance guide](https://pydantic.dev/docs/validation/latest/concepts/performance/)).

### Field validators

```python
from pydantic import BaseModel, ValidationInfo, field_validator

class User(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str, info: ValidationInfo) -> str:
        # info.data: already-validated fields (in declaration order -- cannot access later fields)
        # info.context: user-supplied dict via Model.model_validate(data, context={...})
        # info.mode: "python" | "json" | "strings"
        # info.field_name: the field being validated
        if len(v) < 12:
            raise ValueError("password must be at least 12 chars")
        return v
```

### Annotated validators (reusable pattern)

Prefer Annotated metadata over decorator validators when the same logic applies across multiple models:

```python
from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, WrapValidator, BaseModel

def lower(v: str) -> str:
    return v.lower()

def ensure_https(v: str) -> str:
    if not v.startswith("https://"):
        raise ValueError("URL must be https")
    return v

LowerStr = Annotated[str, AfterValidator(lower)]
HttpsUrl = Annotated[str, AfterValidator(ensure_https)]

# Reuse across any model
class User(BaseModel):
    email: LowerStr
    avatar_url: HttpsUrl
```

**Ordering rule:** `Before` and `Wrap` validators run right-to-left; `After` validators run left-to-right; decorator-style `@field_validator`s are appended last.

### ValidationInfo and info.context

Stable API across 2.x. Context passes through to custom serializers (2.7+):

```python
user = User.model_validate(payload, context={"tenant_id": request.tenant_id})
# Inside a field_validator / model_validator / field_serializer:
#   info.context["tenant_id"] is available
```

Use context for tenant-aware validation, feature flags, or bypass switches -- NOT for data that should be on the model.

### Model validators

```python
@model_validator(mode="before")
@classmethod
def normalize_input(cls, data: dict) -> dict:
    # mode="before": classmethod, first arg cls, receives raw input (often dict)
    # Do NOT mutate then raise -- mutations leak to downstream validators
    if isinstance(data, dict) and "userEmail" in data and "user_email" not in data:
        data["user_email"] = data.pop("userEmail")
    return data

@model_validator(mode="after")
def check_date_order(self) -> "Event":
    # mode="after": INSTANCE method (not classmethod; @classmethod deprecated in 2.12)
    # returns self, not a dict
    if self.start_date > self.end_date:
        raise ValueError("start_date must be <= end_date")
    return self
```

### Error customization

```python
from pydantic_core import PydanticCustomError

@field_validator("sku")
@classmethod
def sku_format(cls, v: str) -> str:
    if not v.isalnum():
        raise PydanticCustomError(
            "invalid_sku",              # machine-readable error type
            "{field} must be alphanumeric",  # template (formatted by Pydantic)
            {"field": "sku"},           # context dict
        )
    return v
```

- Raising `ValueError` auto-wraps into a Pydantic error -- simplest path.
- Avoid `assert` -- skipped under `python -O`.
- `loc` (error location) is determined by validator position; not user-editable at raise site.

### Inheritance

Base-class model validators run on subclass instances. Overriding in a subclass **replaces** (does not extend) the parent. Prefer composition via Annotated validators over deep inheritance.

## Serialization: `model_dump`, `model_dump_json`, `model_validate`

v2 renamed the v1 methods:

| v1 | v2 |
|----|----|
| `model.dict()` | `model.model_dump()` |
| `model.json()` | `model.model_dump_json()` |
| `Model.parse_obj(...)` | `Model.model_validate(...)` |
| `Model.parse_raw(...)` | `Model.model_validate_json(...)` |
| `Model.construct(...)` | `Model.model_construct(...)` |
| `Model.schema()` | `Model.model_json_schema()` |
| `Model.__fields__` | `Model.model_fields` |

All deprecated v1 names still work with deprecation warnings. Production: use the v2 names.

### Serialization modes

```python
model.model_dump(mode="python")   # native Python types (Decimal stays Decimal)
model.model_dump(mode="json")     # JSON-compatible types (Decimal -> str, UUID -> str, datetime -> ISO)
model.model_dump(mode="strings")  # everything coerced to str (CSV / form encodings)

model.model_dump(exclude={"password_hash"})
model.model_dump(include={"id", "name"})
model.model_dump(exclude_none=True)
model.model_dump(by_alias=True)   # use field aliases as keys
model.model_dump(round_trip=True) # output can be fed back into model_validate

# 2.13+ polymorphic: subclass instances serialize by their actual type, exposing subclass-only fields
model.model_dump(polymorphic_serialization=True)
```

### Custom serializers

Three flavors, use the one that matches the shape:

```python
from typing import Annotated
from pydantic import (
    BaseModel, field_serializer, model_serializer,
    PlainSerializer, WrapSerializer,
    SerializerFunctionWrapHandler,
)

class Order(BaseModel):
    total: Decimal
    created_at: datetime

    # Per-field decorator
    @field_serializer("total", when_used="json")
    def serialize_total(self, v: Decimal) -> str:
        return f"${v:.2f}"

    # Whole-model wrap: call handler() for default output, then post-process
    @model_serializer(mode="wrap")
    def add_envelope(self, handler: SerializerFunctionWrapHandler) -> dict:
        return {"version": 1, "data": handler(self)}

# Reusable Annotated serializers
UsdAmount = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"${v:.2f}", return_type=str, when_used="json"),
]
```

`when_used` values: `"always"` (default), `"json"`, `"json-unless-none"`, `"unless-none"`.

### JSON Schema modes

`model_json_schema(mode="validation" | "serialization")` returns different shapes:

```python
Model.model_json_schema(mode="validation")     # request shape -- computed_fields absent, input-only aliases
Model.model_json_schema(mode="serialization")  # response shape -- computed_fields required, output aliases
```

**FastAPI uses both:** validation mode for request schemas, serialization mode for response schemas. Pydantic v2 targets OpenAPI 3.1 natively.

### Aliases: three flavors

| Field arg | Affects |
|-----------|---------|
| `alias="x"` | Both validation input AND serialization output |
| `validation_alias="x"` | Input only |
| `serialization_alias="x"` | Output only |

Pydantic 2.11 added per-config control:

```python
class ApiResponse(BaseModel):
    model_config = ConfigDict(
        validate_by_alias=True,    # accept aliases in input
        validate_by_name=True,     # also accept field names in input
        serialize_by_alias=True,   # emit aliases in output
    )
    user_id: str = Field(alias="userId")
```

`populate_by_name` still works but is pending v3 deprecation -- migrate now.

### Fast JSON emission

For hot paths, skip the Python dict materialization:

```python
# Standard
raw = model.model_dump_json()             # already faster than json.dumps(model.model_dump())

# Fast-path: bytes directly from Rust
raw_bytes = MyModel.__pydantic_serializer__.to_json(model)
```

Cache `__pydantic_serializer__` at module scope for ultra-hot paths (SSE, WebSocket, bulk export).

### Round-tripping

`model.model_dump(round_trip=True)` guarantees `Model.model_validate(dumped)` yields an equivalent instance for `RootModel`s, discriminated unions, and aliased fields. Mutable cached state (computed_fields with side-effects) is not guaranteed to survive round-trip.

## Discriminated unions

The pattern for "this field determines which model to parse":

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class EmailEvent(BaseModel):
    type: Literal["email"]
    to: str
    subject: str

class SmsEvent(BaseModel):
    type: Literal["sms"]
    to: str
    body: str

Event = Annotated[Union[EmailEvent, SmsEvent], Field(discriminator="type")]

class Envelope(BaseModel):
    id: str
    event: Event

Envelope.model_validate({"id": "1", "event": {"type": "email", "to": "x@y", "subject": "hi"}})
```

Faster than v1 unions (pydantic-core picks the variant without trying each) and produces cleaner error messages.

## Monetary precision (CWE-681 defense)

Never use `float` for money. Two idiomatic v2 options:

```python
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, condecimal

# Option A (preferred): Annotated with Field constraints
USDAmount = Annotated[Decimal, Field(max_digits=14, decimal_places=2, ge=0)]

# Option B: condecimal() wrapper (still supported)
USDAmountV1Style = condecimal(max_digits=14, decimal_places=2, ge=0)

class Invoice(BaseModel):
    subtotal: USDAmount
    tax: USDAmount
    total: USDAmount
```

For currency arithmetic, pair with `decimal.getcontext()` for rounding mode:

```python
from decimal import ROUND_HALF_EVEN, getcontext
getcontext().rounding = ROUND_HALF_EVEN  # banker's rounding for financial totals
```

See `senior-review:defect-taxonomy` CWE-681 / CWE-682 for the full monetary-precision rules.

## Settings management (`pydantic-settings`)

v2 extracted settings into a separate package `pydantic-settings`:

```python
# pip install pydantic-settings
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
    )

    database_url: str
    stripe_secret_key: SecretStr  # redacted in repr / model_dump_json
    debug: bool = False
    port: int = Field(default=8000, ge=1, le=65535)

settings = AppSettings()
```

- `SecretStr` / `SecretBytes` hide the value in logs / tracebacks -- use for every API key, password, or token
- Reading the value: `settings.stripe_secret_key.get_secret_value()`
- Source priority (high -> low): init args > env vars > .env file > defaults

## FastAPI integration

### Response models

```python
from fastapi import FastAPI
from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    email: str

class UserDB(UserOut):
    password_hash: str  # server-side only, never exposed

app = FastAPI()

@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int) -> UserDB:
    # Returning the broader UserDB is fine; FastAPI projects through UserOut.
    return await fetch_user(user_id)
```

FastAPI uses the `response_model` for serialization, which strips `password_hash`. Prefer this to manual dict construction.

### Request validation and custom error envelopes

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_failed",
            "details": exc.errors(),   # Pydantic v2 error format
            "request_id": request.headers.get("x-request-id"),
        },
    )
```

v2 error shape differs from v1: `ctx`, `input`, and `url` fields changed. If you serialize errors to clients, pin the shape in an integration test.

### Streaming / long-lived response models

`model_dump_json()` is faster than `json.dumps(model.model_dump())` for streaming. For SSE / WebSocket, cache the serializer:

```python
from typing import Any
serializer = MyModel.__pydantic_serializer__
raw = serializer.to_json(instance)  # bytes
```

## Performance notes

Ordered guide from the [official Performance concept](https://pydantic.dev/docs/validation/latest/concepts/performance/):

1. **`model_validate_json(raw_bytes)` over `model_validate(json.loads(raw_bytes))`** -- skips Python dict materialization; pydantic-core streams directly from bytes.
2. **Instantiate `TypeAdapter` at module scope**, never inside request handlers. Each instantiation rebuilds validators.
3. **Concrete types beat abstract ones** -- `list[int]` beats `Sequence[int]`; `dict` beats `Mapping`.
4. **Discriminated unions >> untagged unions** -- direct lookup via the tag field, no scoring of all variants.
5. **`TypedDict`** via `TypeAdapter` is ~2.5x faster than an equivalent nested `BaseModel` for pure-data shapes.
6. **Avoid wrap validators in hot paths** -- they materialize data in Python.
7. **Core-side constraints (`Field(ge=...)`) >> Python `@field_validator`** -- express ranges, lengths, regex patterns as metadata.
8. **`FailFast` annotation on sequences** (2.8+) stops validation on first failure instead of collecting all errors:
   ```python
   from typing import Annotated
   from pydantic import FailFast
   ids: Annotated[list[int], FailFast()]
   ```
9. **`cache_strings="all"` (default)** -- Pydantic caches repeated strings across validation calls. Memory-safe for typical API payloads; set to `"none"` only for adversarial input with high string entropy.
10. **`defer_build=True`** in `ConfigDict` -- delay schema build until first validation. Useful when you define many models at import but use only a subset per request. 2.11 extended to `@validate_call`; 2.8 added experimental `TypeAdapter` support. Harmful if you want startup-time errors on malformed schemas.
11. **`MyModel.__pydantic_serializer__.to_json(instance)`** -- bytes fast-path for SSE / WebSocket / bulk export. Cache the serializer at module scope.
12. **`model_construct(**data)`** -- skips all validation and coercion. Safe for already-validated data (DB rows matching schema, internal cloning, test fixtures). Unsafe for any input that has crossed a trust boundary.

### Free-threaded Python (3.13+)

Pydantic 2.11 added *experimental* free-threaded (nogil) build support; 2.12 ships official builds for Python 3.14 free-threaded. Treat as preview, not production, until a stability signal from the Pydantic team.

### `model_rebuild()`

Needed when a forward-referenced model is defined out of order or when forward refs haven't resolved. Harmful if called in a hot path -- rebuilds the Rust-side schema from scratch.

## Security and secrets

### `SecretStr` / `SecretBytes`

```python
from pydantic import BaseModel, SecretStr

class Credentials(BaseModel):
    api_key: SecretStr

c = Credentials(api_key="sk-real-secret-123")
print(c)                   # api_key=SecretStr('**********')
print(c.model_dump_json()) # {"api_key":"**********"}
c.api_key.get_secret_value()  # the real value, use only at the trusted sink
```

Redacted in `repr()` and JSON output by default -- stops accidental logging and traceback leaks. To expose to a trusted sink (secret manager persistence), use a custom `@field_serializer("api_key", when_used="always")` that calls `.get_secret_value()`.

### Untrusted input safety

- `TypeAdapter.validate_python(untrusted)` has the same safety model as `BaseModel.model_validate` -- no more, no less permissive.
- `model_validate_json(raw_bytes)` streams through pydantic-core with built-in depth / size bounds; prefer over `json.loads` + `model_validate`.
- Deep recursive models: pydantic-core has Rust-side stack safety for JSON traversal, but Python-level validators at depth can still overflow. Cap recursion via a `mode="before"` validator that counts.
- Mutable nested objects in `model_dump()` output alias back to the model (shallow copy) -- see gotcha above.

## PydanticAI and Logfire

Two first-party tools worth knowing when building LLM-driven features:

- **[Logfire](https://logfire.pydantic.dev/)** -- Pydantic's observability tool. `logfire.instrument_pydantic(record="failure")` traces every failed validation in production with span metadata; `record="all"` traces successful validations too (use sparingly). `logfire.instrument_pydantic_ai()` instruments PydanticAI agents end-to-end (tool calls, LLM requests, token usage).
- **[PydanticAI](https://ai.pydantic.dev/)** -- type-safe LLM agent framework built on Pydantic models. Supports OpenAI, Anthropic, Gemini, DeepSeek, Grok, Cohere, Mistral, Perplexity, Azure, Bedrock, Vertex, Ollama, Groq, OpenRouter, Together, Fireworks. Features: durable-agent execution (resume after failure), built-in evals, MCP support, Logfire tracing. Use when your domain models are already Pydantic and you want agent outputs validated against those same models.

## v1 -> v2 migration checklist

Run `bump-pydantic` for the mechanical transforms:

```bash
uvx bump-pydantic src/
```

Then handle the cases the bot can't:

- `@validator` -> `@field_validator` + `@classmethod` decorator above the validator
- `@root_validator(pre=True)` -> `@model_validator(mode="before")`, method is classmethod, first arg is `cls`, takes raw dict
- `@root_validator` (no pre) -> `@model_validator(mode="after")`, method **returns `self`** and is a **plain instance method** (2.12+ deprecated the classmethod form)
- `Config.allow_population_by_field_name` -> `ConfigDict(validate_by_name=True)` (and `validate_by_alias=True`, `serialize_by_alias=True` as needed). The older `populate_by_name=True` still works but is pending v3 deprecation.
- `Config.orm_mode` -> `model_config = ConfigDict(from_attributes=True)`
- `Config.schema_extra` -> `model_config = ConfigDict(json_schema_extra={...})`
- `Config.extra = "allow"|"forbid"|"ignore"` -> `ConfigDict(extra=...)`
- `parse_obj` -> `model_validate`; `parse_raw` -> `model_validate_json`; `dict()` -> `model_dump()`; `json()` -> `model_dump_json()`
- Generic `BaseModel[T]` -- v2 uses native Python generics, not `GenericModel`; PEP 695 syntax supported since 2.11
- `Field(..., env="FOO")` in settings -> moved to `pydantic-settings` package (`BaseSettings` is no longer in `pydantic`)
- `__fields__` -> `model_fields` (the shape changed: `FieldInfo` objects, not `ModelField`)
- `__root__` model -> use `RootModel[T]` (`from pydantic import RootModel`)
- `Optional[X] = None` without default -> still optional but now must have default; v1 allowed no default on Optional, v2 requires it
- `smart_union` -> default behavior in v2; old `smart_union=True` is a no-op
- `ValidationError.errors()` format changed: `msg`, `type`, `loc`, `input`, `ctx`, `url` -- regenerate any error-envelope tests
- `parse_obj_as(list[Foo], data)` -> `TypeAdapter(list[Foo]).validate_python(data)` (instantiate adapter at module scope)

### What `bump-pydantic` misses

Requires manual conversion:

- Custom `__get_validators__` / `__modify_schema__` -> `__get_pydantic_core_schema__` + `__get_pydantic_json_schema__`
- `each_item=True` validators on sequence fields
- Custom `json_encoders` in `Config` -> `@field_serializer` or Annotated `PlainSerializer`
- Complex wrap validators with branching logic
- `@validator(always=True)` on computed fields -> `@computed_field`

Always diff the changes manually after running `bump-pydantic`.

## Common gotchas

- **`strict=True` breaks JSON API boundaries**: by default, FastAPI coerces `"1"` -> `1` for path/query params. If you set `strict=True` globally, int query params must be sent as JSON numbers. Apply strict selectively (per-field or per-call).
- **`extra="forbid"` + evolving clients**: rejects unknown fields. Fine for internal APIs, risky for public APIs where clients may send forward-compatible fields. Use `"ignore"` (default) for public ingress.
- **`extra="allow"` + `model_dump()`**: v2 **excludes** extras from dumps by default (v1 included them). 2.13 tracks post-instantiation extra assignments in `model_fields_set`; set `ConfigDict(extra="allow")` and explicitly include extras when needed ([issue #5683](https://github.com/pydantic/pydantic/issues/5683)).
- **`@computed_field` with expensive work**: runs on every `model_dump()`. Cache if expensive, or use a regular property (which won't be serialized).
- **Frozen models are hashable**: useful for use as dict keys / in sets, but `model_copy(update={...})` is now required to "change" one -- can't just assign.
- **`model_validate_json` raw bytes vs str**: accepts both; bytes path avoids decode cost on hot paths.
- **Discriminator must be a `Literal`, not `str`**: `Field(discriminator="type")` requires each union member to declare `type: Literal["..."]`, not `type: str`.
- **v2 does NOT validate on `__setattr__` by default**: assigning to a mutable model attribute after construction skips validation. Set `ConfigDict(validate_assignment=True)` if you need it.
- **`@model_validator(mode="after")` classmethod is deprecated** (2.12+): write as a plain instance method returning `self`.
- **`populate_by_name` pending v3 deprecation**: use `validate_by_name=True` (and optionally `validate_by_alias=True`, `serialize_by_alias=True`) instead.
- **UTC / timezone handling**: `AwareDatetime` coerces naive input by treating it as local time then converting to UTC; `NaiveDatetime` rejects tz-aware input. Date-only strings (`YYYY-MM-DD`) can produce surprising aware datetimes -- pin test cases ([issue #8859](https://github.com/pydantic/pydantic/issues/8859)). 2.12 added explicit timestamp-unit control (seconds vs ms) -- no more ambiguous inference.
- **`model_dump()` is shallow**: mutating a nested custom-class object in the dumped dict mutates the original model instance. Use `model.model_copy(deep=True).model_dump()` if downstream code mutates ([issue #10735](https://github.com/pydantic/pydantic/issues/10735)).
- **`Path` and `deque` no longer accept constraints** (2.11+): use a custom validator for length / pattern checks.
- **`arbitrary_types_allowed=True` is a pass-through**: the attached value receives no validation. Necessary for stdlib types Pydantic doesn't know and third-party ORM rows; dangerous because it bypasses the safety model.
- **`from __future__ import annotations` (PEP 563)**: may require `model_rebuild()` or module-scope model definitions for forward refs to resolve. Pyright handles it cleanly; mypy may need the plugin.
- **Mutable defaults**: v2 deep-copies unhashable defaults per instance -- safer than stdlib dataclasses. Still prefer `Field(default_factory=list)` for readability.

## Integration

- Python architecture / API design that uses Pydantic v2 -> `python-development:python-engineer` agent
- Testing Pydantic models -> `python-development:python-tdd` skill
- FastAPI project scaffolding with v2 defaults -> `python-development:python-scaffold` command (`--type fastapi`)
- Monetary precision patterns -> `senior-review:defect-taxonomy` (CWE-681 / CWE-682)
- TypeScript equivalent (Zod / valibot) -> `typescript-development:mastering-typescript` skill

## References

### Concept docs (live)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Pydantic v2 Core Concepts -- Models](https://docs.pydantic.dev/latest/concepts/models/)
- [Validators concept](https://pydantic.dev/docs/validation/latest/concepts/validators/)
- [Serialization concept](https://pydantic.dev/docs/validation/latest/concepts/serialization/)
- [Strict mode](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/)
- [Performance guide](https://pydantic.dev/docs/validation/latest/concepts/performance/)
- [JSON Schema modes](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)
- [Unions and discriminators](https://docs.pydantic.dev/latest/concepts/unions/)
- [Configuration API (defer_build, cache_strings, etc.)](https://docs.pydantic.dev/latest/api/config/)
- [Functional Validators API](https://docs.pydantic.dev/latest/api/functional_validators/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Secret Types](https://docs.pydantic.dev/2.0/usage/types/secrets/)

### Release notes
- [Pydantic 2.13 release (2026-04)](https://pydantic.dev/articles/pydantic-v2-13-release)
- [Pydantic 2.12 release](https://pydantic.dev/articles/pydantic-v2-12-release)
- [Pydantic 2.11 release (2025)](https://pydantic.dev/articles/pydantic-v2-11-release)
- [Pydantic 2.8 release](https://pydantic.dev/articles/pydantic-v2-8-release)
- [Pydantic 2.7 release](https://pydantic.dev/articles/pydantic-v2-7-release)
- [Pydantic changelog](https://docs.pydantic.dev/latest/changelog/)
- [Pydantic releases on GitHub](https://github.com/pydantic/pydantic/releases)

### Tooling and ecosystem
- [bump-pydantic migration tool](https://github.com/pydantic/bump-pydantic)
- [Logfire Pydantic integration](https://logfire.pydantic.dev/docs/integrations/pydantic/)
- [PydanticAI docs](https://ai.pydantic.dev/)
- [PydanticAI GitHub](https://github.com/pydantic/pydantic-ai)

### FastAPI
- [FastAPI + Pydantic v2 response models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [FastAPI migrate from Pydantic v1 to v2](https://fastapi.tiangolo.com/how-to/migrate-from-pydantic-v1-to-pydantic-v2/)
- [FastAPI SSE tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [FastAPI settings](https://fastapi.tiangolo.com/advanced/settings/)

### Known issues referenced above
- [#8859 -- YYYY-MM-DD datetime UTC conversion](https://github.com/pydantic/pydantic/issues/8859)
- [#10735 -- model_dump shallow-copy trap](https://github.com/pydantic/pydantic/issues/10735)
- [#5683 -- extra=allow dump behavior v1 vs v2](https://github.com/pydantic/pydantic/issues/5683)
