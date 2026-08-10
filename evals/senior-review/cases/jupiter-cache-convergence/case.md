# Case: jupiter-cache-convergence

- **Repo:** `D:\Projects\jupiter`
- **Review rev:** `cea26146~1`
- **Fix rev (do not show the reviewer):** `cea26146` (fix(core): converge the market-state cache from generators after a middleware restart)
- **Review scope:** `jupiter-core/jupiter_core/agents/alive_agent.py`, `jupiter-common/jupiter_common/utils/backoff.py`, plus the market-state notifier path the diff touches

## Ground truth

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | After a middleware restart the market-state cache diverges from the generators and nothing re-converges it: consumers keep reading pre-restart state indefinitely, with no signal that it is stale | data-integrity (cache divergence) / temporal-resilience (no recovery path after restart) |

## Scoring notes

- Dual-dimension case on purpose: it sits exactly on the data-integrity / temporal-resilience seam. Track WHICH dimension reports it; both claiming it should deduplicate to one finding in consolidation.
