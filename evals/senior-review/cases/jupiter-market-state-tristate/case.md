# Case: jupiter-market-state-tristate

- **Repo:** `D:\Projects\jupiter`
- **Review rev:** `7c07ce98~1`
- **Fix rev (do not show the reviewer):** `7c07ce98` (fix(brokers): make is_market_open tri-state so a degraded read never reports closed)
- **Review scope:** `jupiter-core/jupiter_core/brokers/ibkr/ibkr_reactive_broker.py`, `jupiter-core/jupiter_core/brokers/mt5/mt5_broker_base.py`, `jupiter-core/jupiter_core/brokers/mt5/mt5_reactive_broker.py`

## Ground truth

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | `is_market_open` collapses "I could not read the market state" into `False`: a degraded broker read is reported as market CLOSED, a stale wrong answer presented as a confident one, and downstream trading logic acts on it | logic-integrity / temporal-resilience |

## Scoring notes

- The mechanism is boolean collapse of a tri-state (open / closed / unknown). Credit `found` for any finding that identifies the degraded-read-becomes-closed conflation; `partial` for flagging missing error handling on the read without the false-state consequence.
