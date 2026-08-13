# Event-Driven Market Data and Historical Data

Subscriptions and historical pulls via TWS API. The choice of subscription type depends on resilience needs and bar size; the gotchas around pacing and reconnection are what bite production.

## When to use

Streaming Level 1 quotes, bar updates, individual ticks, or pulling historical OHLCV. For order monitoring (which uses similar event-driven patterns), see `order-execution.md`.

## Subscription type cheat sheet

| Function | Granularity | Resilience after reconnect | Limits |
|----------|-------------|----------------------------|--------|
| `reqMktData` | Time-sampled L1 ticks | Lost ticks not backfilled | 1 market data line |
| `reqRealTimeBars` | 5-second bars **only** | **Backfilled automatically** | 1 line, list grows in memory; opening subscriptions draws on the historical 60-per-600 s pacing bucket (documented) |
| `reqTickByTickData` | Every tick | Lost ticks not backfilled | Simultaneous subscriptions capped at **5% of your total market data lines** (so 5 on the default 100); max 1 request per instrument per 15 s; needs an L1 top-of-book subscription |
| `reqHistoricalData` (`keepUpToDate=True`) | Bar sizes 5 s and larger | The archived ib_insync docs warned it "leaves the entire API inoperable after a network interruption"; the warning is historical but the reconnect fragility is still observed | 1 line per subscription; documented as TRADES/MIDPOINT/BID/ASK only with `endDateTime` empty; an uncancelled subscription can survive an ungraceful client exit server-side and throttle the account (observed) |

**Production rule**: for real-time bars in production, **prefer `reqRealTimeBars` over `reqHistoricalData + keepUpToDate`** -- the second was officially flagged as unreliable across reconnections. For non-standard timeframes (7-min, etc.), aggregate from 5-sec bars locally.

## Gotchas

- **`reqRealTimeBars` returns *only* 5-second bars** -- the `barSize` parameter must be 5; any other value is rejected. The bars list grows unbounded -- trim periodically: `if len(bars) > 2000: del bars[:len(bars)-1000]`.
- **NBBO filtering on historical data.** Documented: history is "filtered for trade types which occur away from the NBBO such as combo legs, block trades, and derivative trades" (odd lots stay out of TRADES bars too, consistent with tick 233's non-reportable coverage). Historical volume is **lower** than unfiltered real-time and VWAP differs; don't compare them as the same series.
- **Forex has no `TRADES` data** -- always `whatToShow='MIDPOINT'` for FX. Indices have only `TRADES` (no BID/ASK/MIDPOINT). Stocks: `TRADES` for live, `ADJUSTED_LAST` for backtests with dividends.
- **`BID_ASK` requests count double** toward the 60-per-10-min pacing limit.
- **Futures daily-bar close = settlement price**, not last trade -- arrives hours after close, on Friday possibly Saturday.
- **Pacing violations** trigger when: identical request within 15 sec, 6+ requests for same contract/exchange/tick-type in 2 sec, **>60 requests in any 10-min window**, or >50 simultaneous open historical requests. Recovery: queue + rate limit, never blind-retry. Error **162** is the *generic* historical-data service error; pacing is only one of its causes -- and a pacing violation can also surface as a silent empty response with no error at all (see "Historical silence has three causes" below). `reqRealTimeBars` subscriptions are documented to share this same 60-per-600 s bucket: budget them together. The trio is headlined for bars of 30 s and smaller; for 1-minute-and-larger bars the legacy page documents the hard limit as lifted with a soft server-side throttle in its place, so treat the numbers as binding for small bars and advisory above. The socket-wide message rate is a separate limit with its own documented formula (max market data lines divided by 2 per second, hence 50/s at the default 100): track both counters independently.
- **`reqHeadTimeStamp` is not a lightweight metadata call.** Documented: it counts as an ongoing historical request (cancel it with `cancelHeadTimestamp`) and it is paced in the small-bar class "regardless of which bar size value has been requested". Bulk head-timestamp discovery across a symbol universe must be paced like small-bar history.
- **The documented never-available list** (quote-verified 2026-08-13): bars of 30 s or less older than six months; expired futures beyond two years from expiry; expired options, FOPs, warrants and structured products entirely; EOD data for those same classes; expired future spreads; securities no longer trading; native combo history (the sum of legs is what you get); pre-move history for securities that changed exchange (the SOXX example), SMART included; studies and indicators; Time & Sales beyond 3 years. Interior gaps inside nominally-covered ranges are also observed in the wild: absence is mapped by probing, never inferred from the rules.
- **Bar-size and duration ceilings**: 1-second bars stop at a 2000 S duration; every size from 5 s up shares documented ceilings of 86400 S / 365 D / 52 W / 12 M / 68 Y (a request-string cap, not a data-availability promise). IBKR's current and legacy step-size tables disagree in granularity; where they conflict, trust the stricter legacy row or probe. `formatDate` is per-function: for bars, 1 is an exchange-zone string and 2 is epoch; for `reqHeadTimeStamp`, 1 is documented as UTC. UTC datetime strings use the hyphen form `YYYYMMDD-hh:mm:ss`; operator and exchange-zone strings use a space plus zone id, and a wrong delimiter is read as the wrong zone rather than rejected.
- **Historical volume scale is a terminal setting**: "Send market data in lots for US Stocks for dual-mode API clients" flips US-stock volume between round lots and shares for the same request, another unversioned GUI input to pin per deployment. IBKR's legacy page also documents history as adjusted, compressed and filtered by default, with re-requests at different times allowed to differ: never assume bit-identical re-pulls.
- **Historical via API needs the live L1 entitlement even where the TWS chart works**: documented, "the API always requires Level 1 streaming real time data to return historical data", while the GUI silently falls back to delayed charts. A chart that renders proves nothing about the API path.
- **`reqHistoricalTicks` has its own contract**: at most 1000 ticks per call, exactly one of start/end datetime set (page by walking the boundary), `whatToShow` limited to Trades, Midpoint and Bid_Ask, `ignoreSize` meaningful for Bid_Ask only, and single-session responses (legacy-documented).
- **Error 354 ("not subscribed")** means you have nothing. **Error 10197 means "no market data during competing session"**: the same user is logged into live and paper simultaneously and requesting live data on both; the live side gets preference. It is *not* a delayed-data notice, and there is no error code that means "you are now receiving delayed data" -- that is signalled by the `marketDataType` callback (see below). Related subscription codes: **10089** "API data requires subscription" (the account's data does not extend to API use), **10090** "part of requested market data is not subscribed", **10186** "delayed market data is not enabled". Treat all of these as terminal for that contract's snapshot wait.
- **Market data lines are shared with TWS** (default 100). The allowance is documented as the greater of USD monthly commissions divided by 8 and USD equity times 100 per million, never below 100; Quote Booster packs add 100 lines each (USD 30/month, at most 10 packs). Each streaming sub consumes 1 line **per instrument**: the same symbol open in TWS and several API clients counts once (IBKR-staff statement on the API forum). Tick-by-tick runs from a separate pool at 5% of lines, and market depth from another (minimum 3 concurrent, roughly one more per 100 lines above 400, maximum 60, documented). Check current usage in TWS with **Ctrl+Alt+=**; overflow errors: **101** max tickers, **10190** max tick-by-tick (observed in logs, absent from the published table).
- **`reqMktData` is a sampled feed, not prints.** IBKR aggregates top-of-book updates, with no cadence number documented (the widely-quoted 250 ms is not traceable to an IBKR page). `reqTickByTickData` is the print-level feed, with documented limits: type strings are case-sensitive (`Last`, `AllLast`, `BidAsk`, `MidPoint`), options tick-by-tick is historical-only, indices only on CME, combos not at all. One dated single-source report measures even `BidAsk` tick-by-tick arriving in batched bursts; unreplicated, so treat sub-100 ms latency assumptions as unverified in either direction.
- **Three "volume" numbers, none interchangeable (documented):** plain `Volume` (tick 8) includes delayed prints, busted trades and combos but does not update on every tick; `RTVolume` (generic tick 233) updates per trade and includes odd lots and other non-reportable trades; `RTTradeVolume` (375) carries only `Last`-grade prints, matching charts and historical bars. A volume-based signal must pick one deliberately.
- **Zero price plus zero size is a signal, not noise**: with `pastLimit` set it is the documented `Halted` tick, and the same shape immediately after a Halted tick means `Unhalted` (TWS and API 10.15+). Tick validation must not discard these as bad data.
- **Depth is its own budget and its own shape**: `reqMktDepthExchanges` lists venues (rows with `isL2=True` reach `updateMktDepthL2`), `isSmartDepth=True` returns the aggregated BookTrader-style book, and concurrent depth requests are capped by the lines formula above. The depth-overflow error code is undocumented; measure it before relying on it.
- **Market data types**: `1` live (paid), `2` frozen (last recorded value at close; needs the same subscriptions as live), `3` delayed (free where available), `4` delayed-frozen. Requesting a non-live type does not switch you permanently: TWS keeps sending regular data as the default and adds the requested type when live is unavailable, announcing the actual type per request through the **`marketDataType` callback**. Read that callback rather than inferring the feed from error codes. IBKR also grants a small monthly allowance of free snapshot quotes (100/month at time of writing, documented on the non-US entity pages) before snapshots are billed; **regulatory snapshots** (the snapshot flag on US stocks and options) bill USD 0.01 each, are paced at one per second, are documented to bill **paper accounts identically**, and auto-convert into the corresponding network subscription when a month's fees reach its price. Spot Forex needs no market-data subscription; crypto generally requires one -- verify your entitlements before assuming it is free.
- **Do not harvest ticks by polling `waitOnUpdate()`.** The library's own docstring warns ticks "can go missing" that way (verified on 2.1.0); consume `ticker.updateEvent` / `pendingTickersEvent` instead, and remember both fire once per processed network packet, so several wire-level changes can arrive coalesced into one update.
- **Give the socket a beat before disconnecting**: the official ib_async recipes recommend `ib.sleep(1)` before `disconnect()` on short-lived connections, so unflushed messages are not lost.
- **On disconnect: error 1101 ("data lost") and 1102 ("data restored")** -- use them as triggers to reconcile via historical request for the gap window (see `reconnection-resilience.md`).
- **ib_async initializes `Ticker.bid` / `Ticker.ask` to `NaN`, not `None`.** A price-readiness check of `if price is None` passes immediately and hands a `NaN`/`0.0` placeholder to whatever consumes it (position sizing especially). Validate with `value is not None and not math.isnan(value) and value > 0`. This single wrong assumption seeded a whole family of sizing bugs: see `venue-boundary-failure-modes.md`.
- **A snapshot/price wait must abort on terminal market-data codes** for the contract: `{200, 354, 10089, 10090, 10197}`, tracked per `conId`. Otherwise the wait exits instantly (on the NaN-vs-None bug above) and returns a placeholder instead of a real price.
- **Forex CFDs serve no market or historical data** (error 2127 then 366). Pull data from the underlying spot Forex (IDEALPRO) contract while keeping the CFD for orders. See `venue-boundary-failure-modes.md`.
- **Historical FX bars contain session-anchored stub bars at the reopen** that the live stream never delivers. See the dedicated section below -- they corrupt any replay/bootstrap that consumes historical bars as if they were live ones.
- **Daily market open/close transitions resonate with dedup layers.** Session transitions recur every ~24 h with seconds of polling jitter. Any downstream deduplication keyed on `(symbol, is_open)` with a TTL at or above the cycle period will suppress a *genuine* daily event that arrives a few seconds earlier than yesterday's -- and a swallowed CLOSE then makes the next real OPEN look like a duplicate too (cascading stale state: consumers stuck on "market closed", entry signals dropped). A dedup TTL must bound only the true duplicate window (seconds to minutes), never the daily cycle. This session-event layer is a *different* dedup than the seconds-scale order-rejection dedup in `venue-boundary-failure-modes.md` (sized to the errorEvent/orderStatusEvent race); size each to its own duplicate window and never share one TTL.

## Market state is data too (`is_market_open` must be tri-state)

`reqContractDetails` returns `tradingHours` as a string of **concrete dated segments covering only about a week**. Two production failures, in opposite directions:

- **Assumed-open**: returning `True` when trading hours are missing poisons the state seed -- a Sunday-closed market is treated as open and the first session transition is missed.
- **Assumed-closed (the worse one)**: a long-lived connection outlives the dated window, after which every check lands beyond the last segment and reports the market **permanently closed** -- forever, silently. A confident `False` from a broker that cannot actually see the market is indistinguishable from a genuine closure, and downstream it becomes a seeded CLOSED that silently halts an executor.

**Rules:**

- Make the check **tri-state**: `True` / `False` only inside the covered window, `None` (unknown) beyond it or when data is missing. Consumers must treat `None` as "refresh or hold", never as closed.
- Track `coverage_end` explicitly; a `check_time` past it returns `None`, never `False`.
- Refresh `tradingHours` on a TTL (~12 h) keyed on the **last attempt**, not the last success, so a persistently failing refetch retries once per TTL instead of hammering on every call.

## Historical silence has three causes

An empty bar response is **not** an error at the API surface, and at least three unrelated causes are indistinguishable there:

1. **Duration over the per-barSize cap.** Each bar size has a maximum `durationStr` (e.g. 4-hour bars cap around 1 year). Exceeding it does not error; it returns an empty set. Symptom: a request for N bars returns 0, with no error on any channel.
2. **Pacing on the identical-request tuple.** The same `(contract, barSize, whatToShow, useRTH)` is limited to one request per 15 s -- **across processes on the same login**, not just within one client. A violation is a silent empty response, not error 162. The shape that triggers it is several sibling processes issuing the same request within a few seconds of each other.
3. **Past-retention windows.** Requests reaching beyond IBKR's retained history also come back empty.

**Retry shape that distinguishes them:** retry the **same** `(endDateTime, durationStr)` after 15/30/45 s, but only for continuation batches (`batch_idx >= 1`); an empty **first** batch means "no data here", not pacing, and retrying it just burns pacing budget. Wrap bootstrap in an outer ladder (30/60/120/300/600 s). On exhaustion return short with an explicit error log rather than raising: past-retention is indistinguishable from pacing, and a hard raise turns a data boundary into an outage.

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

### Stub attrition starves the replay window

The stub-drop mitigation has a second-order failure of its own: there is one reopen stub per trading day regardless of bar size, so the attrition fraction is `bar_size / session_length` -- roughly 1 in 6 on 4-hour bars, 1 in 24 on hourly -- and a fixed-count fetch **under-delivers** after filtering. The delivered pool can fall hundreds of bars short of a bootstrap replay window, which falsely expires live forming signals as regressions on every restart. Ship the producer and consumer fixes together: the fetch inflates its pagination plan by the matching factor (7/6 for 4-hour bars; compute it for your size) and tops up in bounded rounds, and the bootstrap independently guards against a replay window that comes back empty or thin instead of trusting "I asked for N".

### The forming bar (the last row is not closed)

`reqHistoricalData` returns the **currently-forming bar as the last row**. MetaTrader does not, so code migrated from MT5 that assumes "last row = last closed bar" seeds the forming bar into indicator state at bootstrap; the first live tick then re-supplies the same bar and the indicator state is corrupted from that point on (every read returns nothing, with no error). This is distinct from the session-stub problem above, and both drops belong in the same ingestion method: **drop any bar whose synthesized `time_close` is in the future**.

## Event Listener Contracts (eventkit swallows your exceptions)

ib_async dispatches events through **eventkit** (installed as the `aeventkit` fork; import and logger names unchanged), which catches every exception raised inside a listener and logs it via `logging.getLogger("eventkit.event")` -- the emission then dies, silently from your application's point of view. Two consequences bite production:

- **A handler with the wrong signature fails on every single emission.** Example: `positionEvent` emits one `Position` namedtuple, but a handler declared with the raw-wrapper 4-argument signature raises `TypeError` inside eventkit on every position update -- position deltas simply "never fire", forever, with zero trace in your logs.
- **If your logging pipeline only ships your own loggers** (a dedicated application logger shipped to a remote aggregator), the `eventkit.event` and `ib_async` std-logger records land in stdout/stderr at best -- invisible to all remote debugging.

**Rules:**

- **Pin every handler signature with a contract test** that emits the real event object through the real event (`ib.positionEvent.emit(Position(...))`) and asserts the handler body executed. Arity bugs are permanent until tested.
- **Route the third-party std loggers at broker construction**: attach `ib_async`, `ib_insync`, and `eventkit` to the same sink as your application logs (one helper that attaches your handlers to those named loggers). This routing is routinely what exposes a handler `TypeError` that has been silently killing an event stream. Pair it with process-wide hooks: an asyncio loop exception handler and `threading.excepthook` that escalate to your critical logger, because unhandled task/loop/thread exceptions otherwise die on local stderr.
- **The decoder is a third failure channel.** ib_async message-decode failures ("Error handling fields:" records) never reach `errorEvent`; they surface only on the ib_async stdlib logger, with no reqId and no contract attached. A reconnect burst can drop contract-data messages for every operating contract this way. An error that reaches your log aggregator only by accident is not an error you observe -- which is exactly why the logger routing above is mandatory, and why decode errors during a reconnect window deserve an explicit triage (was the qualified-contract cache refreshed after them?).
- **Diagnostic heuristic:** if an event handler "never fires" but the Gateway log proves the server delivered the message, suspect a swallowed listener exception before suspecting the subscription.

## Throttled request queue (the local pattern worth keeping)

```python
import asyncio

class HistoricalDataThrottle:
    # Two independent brakes, named for what they actually do:
    # - max_concurrent bounds simultaneous open requests (venue cap: 50)
    # - min_interval spaces request starts; 11 s keeps a single client under
    #   the 60-per-10-min window (600 s / 11 s ~= 54). Use 22 s for BID_ASK,
    #   which counts double.
    def __init__(self, max_concurrent=6, min_interval=11):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.min_interval = min_interval
        self.last_request = 0

    async def request(self, ib, contract, **kwargs):
        async with self.semaphore:
            now = asyncio.get_running_loop().time()
            wait = self.min_interval - (now - self.last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_request = asyncio.get_running_loop().time()
            return await ib.reqHistoricalDataAsync(contract, **kwargs)
```

The interval throttle is per-process; the identical-request 15 s rule is enforced per login **across processes** (see "Historical silence has three causes").

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
    if len(bars) > 2000:
        del bars[:len(bars)-1000]
```

**Schema parity is the adapter's job.** IBKR bars carry no `time_close`; synthesize it (`time_open + bar_size`) at the adapter so downstream code has one schema. And ib_async returns `datetime.date` objects for daily-and-larger bars but `datetime` for intraday: convert both explicitly and **raise** on any unsupported timestamp type -- a silent fallback to `now()` once collapsed every daily bar onto the current day.

## Official docs

- Market data subscriptions: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#market-data
- Historical data + bar sizes + pacing: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#historical-data
- whatToShow values: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-ref/#hist-bar-types
- Error code reference: https://www.interactivebrokers.com/campus/ibkr-api-page/tws-api-error-codes/

## Related

- `venue-boundary-failure-modes.md` -- NaN-safe price reads, terminal-code aborts, data-contract vs order-contract split
- `tws-api-architecture.md` -- connection setup, clientId strategy
- `order-execution.md` -- the same event-pattern applied to order updates
- `order-lifecycle-contracts.md` -- verdict windows, warning-grade codes, attribution traps
- `reconnection-resilience.md` -- handling 1101/1102 and reconciling data gaps
