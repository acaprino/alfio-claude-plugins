# Python Docstring Styles Reference

Three major docstring styles in the Python ecosystem. Choose one per project and use it consistently.

---

## Google Style (Recommended Default)

Readable without rendering. Clean indentation. Best for most projects.

```python
def send_notification(
    user: User,
    message: str,
    channel: str = "email",
    priority: int = 0,
) -> NotificationResult:
    """Send a notification to a user through the specified channel.

    Validates the channel, formats the message according to channel
    requirements, and dispatches asynchronously. Falls back to email
    if the preferred channel is unavailable.

    Args:
        user: Target user. Must have a verified contact for the channel.
        message: Notification body. Supports markdown for email channel,
            plain text for SMS and push.
        channel: Delivery channel. One of "email", "sms", "push".
        priority: Dispatch priority (0=normal, 1=high, 2=urgent).
            High and urgent skip batching and send immediately.

    Returns:
        Result object with delivery status and message ID.
        Status is "queued" for normal priority, "sent" for high/urgent.

    Raises:
        ChannelUnavailableError: If channel is down and no fallback exists.
        InvalidRecipientError: If user has no verified contact for channel.

    Example:
        >>> result = send_notification(user, "Deploy complete", channel="push")
        >>> result.status
        'queued'
    """
```

---

## NumPy Style

Wider sections with underlines. Preferred in data science / scientific computing.

```python
def send_notification(
    user: User,
    message: str,
    channel: str = "email",
    priority: int = 0,
) -> NotificationResult:
    """Send a notification to a user through the specified channel.

    Validates the channel, formats the message according to channel
    requirements, and dispatches asynchronously. Falls back to email
    if the preferred channel is unavailable.

    Parameters
    ----------
    user : User
        Target user. Must have a verified contact for the channel.
    message : str
        Notification body. Supports markdown for email channel,
        plain text for SMS and push.
    channel : str, default "email"
        Delivery channel. One of "email", "sms", "push".
    priority : int, default 0
        Dispatch priority (0=normal, 1=high, 2=urgent).
        High and urgent skip batching and send immediately.

    Returns
    -------
    NotificationResult
        Result object with delivery status and message ID.
        Status is "queued" for normal priority, "sent" for high/urgent.

    Raises
    ------
    ChannelUnavailableError
        If channel is down and no fallback exists.
    InvalidRecipientError
        If user has no verified contact for channel.

    Examples
    --------
    >>> result = send_notification(user, "Deploy complete", channel="push")
    >>> result.status
    'queued'
    """
```

---

## Sphinx/reST Style

Uses reStructuredText directives. Best when generating HTML docs with Sphinx.

```python
def send_notification(
    user: User,
    message: str,
    channel: str = "email",
    priority: int = 0,
) -> NotificationResult:
    """Send a notification to a user through the specified channel.

    Validates the channel, formats the message according to channel
    requirements, and dispatches asynchronously. Falls back to email
    if the preferred channel is unavailable.

    :param user: Target user. Must have a verified contact for the channel.
    :type user: User
    :param message: Notification body. Supports markdown for email channel,
        plain text for SMS and push.
    :type message: str
    :param channel: Delivery channel. One of "email", "sms", "push".
    :type channel: str
    :param priority: Dispatch priority (0=normal, 1=high, 2=urgent).
        High and urgent skip batching and send immediately.
    :type priority: int
    :returns: Result object with delivery status and message ID.
    :rtype: NotificationResult
    :raises ChannelUnavailableError: If channel is down and no fallback exists.
    :raises InvalidRecipientError: If user has no verified contact for channel.

    .. code-block:: python

        result = send_notification(user, "Deploy complete", channel="push")
        assert result.status == "queued"
    """
```

---

## Decision Table

| Project Type | Recommended Style | Rationale |
|-------------|-------------------|-----------|
| Web app / API | **Google** | Clean, readable, widely understood |
| Data science / ML | **NumPy** | Matches pandas, numpy, scikit-learn conventions |
| Library with Sphinx docs | **Sphinx/reST** | Native Sphinx rendering, `:param:` directives |
| Open source (general) | **Google** | Lowest barrier for contributors |
| Existing project | **Match existing** | Consistency over preference |

**Rule:** If the project already has docstrings, match their style. If starting fresh, default to Google.

---

## Type Hints + Docstrings Interaction

With type hints, docstrings should document **semantics**, not **types**.

### Do: Document Semantics

```python
def calculate_risk_score(
    transactions: list[Transaction],
    lookback_days: int = 30,
) -> float:
    """Calculate fraud risk score from recent transaction patterns.

    Analyzes velocity, amount distribution, and geographic spread
    of transactions within the lookback window.

    Args:
        transactions: Recent transactions, ordered by timestamp
            (oldest first). Empty list returns score of 0.0.
        lookback_days: Only consider transactions within this many
            days from the most recent. Must be positive.

    Returns:
        Risk score between 0.0 (no risk) and 1.0 (certain fraud).
        Scores above 0.7 trigger manual review.
    """
```

### Don't: Duplicate Type Information

```python
# BAD - every line duplicates type hints
def calculate_risk_score(
    transactions: list[Transaction],
    lookback_days: int = 30,
) -> float:
    """Calculate fraud risk score.

    Args:
        transactions (list[Transaction]): A list of Transaction objects.
        lookback_days (int): An integer for the number of days. Default 30.

    Returns:
        float: A float representing the risk score.
    """
```

### One-Line Docstrings

Use for simple, self-explanatory functions where the name + type hints tell the full story:

```python
def is_expired(token: AuthToken) -> bool:
    """Check if the authentication token has passed its expiry time."""

def full_name(first: str, last: str) -> str:
    """Return the user's full name as 'First Last'."""
```

Do NOT write one-line docstrings for complex functions. If you need more than one sentence of explanation, use the multi-line format.

---

## Tooling

### pydocstyle

Checks docstring style compliance.

```bash
pip install pydocstyle

# Check Google style
pydocstyle --convention=google src/

# Check NumPy style
pydocstyle --convention=numpy src/

# Ignore specific rules
pydocstyle --add-ignore=D100,D104 src/
```

Common codes:
- `D100` - Missing module docstring
- `D101` - Missing class docstring
- `D102` - Missing method docstring
- `D103` - Missing function docstring
- `D104` - Missing `__init__.py` docstring
- `D400` - First line should end with a period
- `D401` - First line should be in imperative mood

### interrogate

Measures docstring coverage as a percentage.

```bash
pip install interrogate

# Check coverage
interrogate -v src/

# Enforce minimum coverage in CI
interrogate --fail-under=80 src/

# Generate badge
interrogate --generate-badge docs/
```

Configuration in `pyproject.toml`:

```toml
[tool.interrogate]
ignore-init-method = true
ignore-init-module = true
ignore-magic = true
ignore-semiprivate = false
ignore-private = true
ignore-property-decorators = true
fail-under = 80
verbose = 1
```

### ruff

Can enforce docstring-related rules via the `D` rule set (pydocstyle):

```toml
[tool.ruff.lint]
select = ["D"]

[tool.ruff.lint.pydocstyle]
convention = "google"  # or "numpy"
```
