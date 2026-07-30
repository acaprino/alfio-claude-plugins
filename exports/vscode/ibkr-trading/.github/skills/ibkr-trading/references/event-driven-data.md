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
- **ib_async initializes `Ticker.bid` / `Ticker.ask` to `NaN`, not `None`.** A price-readiness check of `if price is None` passes immediately and hands a `NaN`/`0.0` placeholder to whatever consumes it (position sizing especially). Validate with `value is not None and not math.isnan(value) and value > 0`. This single wrong assumption seeded a whole family of sizing bugs: see `venue-boundary-failure-modes.md`.
- **A snapshot/price wait must abort on terminal market-data codes** for the contract: `{200, 354, 10089, 10090, 10197}`, tracked per `conId`. Otherwise the wait exits instantly (on the NaN-vs-None bug above) and returns a placeholder instead of a real price.
- **Forex CFDs serve no market or historical data** (error 2127 then 366). Pull data from the underlying spot Forex (IDEALPRO) contract while keeping the CFD for orders. See `venue-boundary-failure-modes.md`.
- **Historical FX bars contain session-anchored stub bars at the reopen** that the live stream never delivers. See the dedicated section below -- they corrupt any replay/bootstrap that consumes historical bars as if they were live ones.
- **Daily market open/close transitions resonate with dedup layers.** Session transitions recur every ~24 h with seconds of polling jitter. Any downstream deduplication keyed on `(symbol, is_open)` with a TTL at or above the cycle period will suppress a *genuine* daily event that arrives a few seconds earlier than yesterday's -- and a swallowed CLOSE then makes the next real OPEN look like a duplicate too (cascading stale state: consumers stuck on "market closed", entry signals dropped). A dedup TTL must bound only the true duplicate window (seconds to minutes), never the daily cycle.

## Session-Anchored Stub Bars (historical FX data off the bar grid)

`reqHistoricalData` on spot FX (IDEALPRO) returns bars **anchored to the session open** around the daily/weekly reopen (17:15 ET). At that boundary the response contains bars time-stamped at :15/:45 instead of the clock-aligned :00/:30 grid of the requested bar size. Three properties make them dangerous:

- **The live stream never delivers them.** Live aggregated bars stay on the :00/:30 grid, so any replay/bootstrap that walks historical bars evaluates bars the runtime path never saw -- and can latch state onto one of them.
- **A synthetic `time_close = time_open + bar_size` mislabels them.** The stub covers less than a full bar (e.g. 15 minutes of a 30-min bar) but your close-time arithmetic silently stretches it to full width.
- **They are frequent, not rare.** The reopen stub recurs daily; over a multi-week backfill window on larger bar sizes (e.g. 4-hour) off-grid bars can exceed 10% of the response.

**Mitigations:**

- **Drop off-grid bars** (bar `time_open` not an exact multiple of the bar size) from historical responses -- **intraday sizes only**: daily and larger bars are date-labeled at midnight venue time and legitimately sit off the UTC grid.
- **Over-fetch and top up.** Dropping bars shortens the response below the requested count; inflate the request and run a bounded top-up loop (with a hard round cap) so consumers relying on "N bars" still get N. On exhaustion return short with an explicit error rather than raising.
- **Escalate when *all* bars come back off-grid** -- that is a contract/timezone bug on your side, not stub noise.
- **Log the drop counts** (raw fetched / on-grid kept / dropped / top-up rounds). Silent filtering reads as "full coverage" when it is not.
- **Guard state reconciliation against replayed bars.** Before a bootstrap/replay bar is allowed to complete a state transition (confirm a pending setup, fill a slot in a state machine), validate its chronology: the bar must close *after* the state's last update, and any confirmation window derived from it must not already be elapsed. A weeks-old reopen stub passing as "the next bar" is exactly how a replay silently completes and instantly expires a live setup.

## Event Listener Contracts (eventkit swallows your exceptions)

ib_async dispatches events through **eventkit**, which catches every exception raised inside a listener and logs it via `logging.getLogger("eventkit.event")` -- the emission then dies, silently from your application's point of view. Two consequences bite production:

- **A handler with the wrong signature fails on every single emission.** Example: `positionEvent` emits one `Position` namedtuple, but a handler declared with the raw-wrapper 4-argument signature raises `TypeError` inside eventkit on every position update -- position deltas simply "never fire", forever, with zero trace in your logs.
- **If your logging pipeline only ships your own loggers** (a dedicated app logger to CloudWatch or similar), the `eventkit.event` and `ib_async` std-logger records land in stdout/stderr at best -- invisible to all remote debugging.

**Rules:**

- **Pin every handler signature with a contract test** that emits the real event object through the real event (`ib.positionEvent.emit(Position(...))`) and asserts the handler body executed. Arity bugs are permanent until tested.
- **Route the third-party std loggers** (`eventkit`, `ib_async`) into the same sink as your application logs.
- **Diagnostic heuristic:** if an event handler "never fires" but the Gateway log proves the server delivered the message, suspect a swallowed listener exception before suspecting the subscription.

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

- `venue-boundary-failure-modes.md` -- NaN-safe price reads, terminal-code aborts, data-contract vs order-contract split
- `tws-api-architecture.md` -- connection setup, clientId strategy
- `order-execution.md` -- the same event-pattern applied to order updates
- `reconnection-resilience.md` -- handling 1101/1102 and reconciling data gaps
