# Case: synthetic-retry-storm (temporal-resilience)

Synthetic. Materialize into a scratch repo (`sync/replicator.py`), commit, review the diff that added the replicator.

## Buggy code

```python
# sync/replicator.py
async def replicate_forever(source, target):
    while True:
        try:
            batch = await source.fetch_batch()      # no timeout
            await target.write(batch)               # full batch, not resumable
            await notify_ops(f"replicated {len(batch)} rows")
        except Exception:
            logger.debug("replication failed, retrying")
        await asyncio.sleep(5)
```

## Ground truth (4 bugs)

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | Retry every 5s with no backoff, no cap, no give-up state: a persistently failing target retries 17,280 times/day, re-fetching and re-writing the full batch each time | temporal-resilience |
| 2 | The failure is logged at DEBUG and swallowed: at default log levels a replication outage is invisible for as long as it lasts, while `notify_ops` messages simply stop arriving with nothing saying why | temporal-resilience (silence) |
| 3 | `fetch_batch` has no timeout: a black-holed source hangs the loop forever inside `await`, and the process keeps running with replication silently dead | temporal-resilience |
| 4 | Success notifies ops on EVERY batch (notification flood on the happy path) while failure notifies nobody: the signal-to-damage mapping is inverted | temporal-resilience / architecture |

## Scoring notes

- The three-horizon question is the test: t0 (one failure: swallowed), t+1h (720 identical retries), t+24h (silent dead subsystem). A reviewer that flags "broad except" without the time-axis consequence gets `partial` on bug 2.
