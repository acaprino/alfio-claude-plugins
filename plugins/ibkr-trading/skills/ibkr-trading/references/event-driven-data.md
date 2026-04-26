# Event-Driven Market Data and Historical Data

Subscriptions and historical pulls via TWS API. The choice of subscription type depends on resilience needs and bar size; the gotchas around pacing and reconnection are what bite production.

## When to use

Streaming Level 1 quotes, bar updates, individual ticks, or pulling historical OHLCV. For order monitoring (which uses similar event-driven patterns), see `order-execution.md`.

## Subscription type cheat sheet

| Function | Granularity | Resilience after reconnect | Limits |
|----------|-------------|----------------------------|--------|
| `reqMktData` | Time-sampled L1 ticks | Lost ticks not backfilled | 1 market data line |
| `reqRealTimeBars` | 5-second bars **only** | **Backfilled automatically** | 1 line, list grows in memory |
| `reqTickByTickData` | Every tick | Lost ticks not backfilled | **Max 3 subscriptions** per connection |
| `reqHistoricalData` (`keepUpToDate=True`) | Any standard bar size | "Leaves the entire API inoperable after a network interruption" (per ib_insync docs) | 1 line per subscription |

**Production rule**: for real-time bars in production, **prefer `reqRealTimeBars` over `reqHistoricalData + keepUpToDate`** -- the second was officially flagged as unreliable across reconnections. For non-standard timeframes (7-min, etc.), aggregate from 5-sec bars locally.

## Gotchas

- **`reqRealTimeBars` returns *only* 5-second bars** -- the `barSize` parameter must be 5; any other value is rejected. The bars list grows unbounded -- trim periodically: `if len(bars) > 2000: del bars[:len(bars)-1000]`.
- **NBBO filtering on historical data.** IB historical excludes odd lots, combo legs, block trades. Historical volume is **lower** than unfiltered real-time. Don't compare them as if they're the same series.
- **Forex has no `TRADES` data** -- always `whatToShow='MIDPOINT'` for FX. Indices have only `TRADES` (no BID/ASK/MIDPOINT). Stocks: `TRADES` for live, `ADJUSTED_LAST` for backtests with dividends.
- **`BID_ASK` requests count double** toward the 60-per-10-min pacing limit.
- **Futures daily-bar close = settlement price**, not last trade -- arrives hours after close, on Friday possibly Saturday.
- **Pacing violation (error 162)** triggers when: identical request within 15 sec, 6+ requests for same contract/exchange/tick-type in 2 sec, **>60 requests in any 10-min window**, or >50 simultaneous open historical requests. Recovery: queue + rate limit, never blind-retry.
- **Error 354 ("not subscribed")** vs **error 10197 ("using delayed data")** -- the second is informational, your code can keep working with the delayed feed; the first means you have nothing.
- **Market data lines are shared with TWS** (default 100, expand with Quote Booster Pack). Each streaming sub consumes 1 line. Check current usage in TWS with **Ctrl+Alt+=**.
- **`reqMarketDataType(3)`** = delayed (free, 15-20 min), `1` = live (paid). Forex and crypto don't need subscriptions.
- **On disconnect: error 1101 ("data lost") and 1102 ("data restored")** -- use them as triggers to reconcile via historical request for the gap window (see `reconnection-resilience.md`).

## Throttled request queue (the local pattern worth keeping)

```python
import asyncio

class HistoricalDataThrottle:
    def __init__(self, max_per_10min=50, min_interval=11):
        self.semaphore = asyncio.Semaphore(max_per_10min)
        self.min_interval = min_interval
        self.last_request = 0

    async def request(self, ib, contract, **kwargs):
        async with self.semaphore:
            now = asyncio.get_event_loop().time()
            wait = self.min_interval - (now - self.last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_request = asyncio.get_event_loop().time()
            return await ib.reqHistoricalDataAsync(contract, **kwargs)
```

## Hybrid OHLCV feed (production-grade)

The pattern that survives disconnects:

1. **Startup**: backfill from local cache to last timestamp, then to `now` via historical request.
2. **Live**: subscribe to `reqRealTimeBars` (resilient across reconnects).
3. **Local aggregation**: aggregate 5-sec bars into the strategy timeframe.
4. **Periodic reconciliation**: compare with historical to detect gaps.
5. **Reconnect handling**: on error 1101/1102, request historical data for the gap window.

```python
def on_bar_update(bars, hasNewBar):
    if hasNewBar:
        completed = bars[-2]   # the just-closed bar; bars[-1] is still forming
        # strategy logic
    if len(bars) > 1000:
        del bars[:len(bars)-500]
```

## Official docs

- Market data subscriptions: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#market-data
- Historical data + bar sizes + pacing: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#historical-data
- whatToShow values: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-ref/#hist-bar-types
- Error code reference: https://www.interactivebrokers.com/campus/ibkr-api-page/tws-api-error-codes/

## Related

- `tws-api-architecture.md` -- connection setup, clientId strategy
- `order-execution.md` -- the same event-pattern applied to order updates
- `reconnection-resilience.md` -- handling 1101/1102 and reconciling data gaps
