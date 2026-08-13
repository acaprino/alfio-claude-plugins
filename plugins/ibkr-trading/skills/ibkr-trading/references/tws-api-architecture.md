# TWS API Architecture and ib_async

The TWS API is a local TCP socket protocol (Protocol Buffers encoding in recent 10.x versions) between Python and TWS or IB Gateway. Current production version: **10.49** (August 2026), the release that also **open-sourced the TWS API under the GPL**. Version 10.47 removed `reqFundamentalData` and its protobuf variants entirely. Use `ib_async` (the maintained successor to ib_insync) for all new code unless you have a specific reason to use the official ibapi.

This file is the only place in this skill that states the TWS API version number. Everywhere else stays version-free on purpose; update it here.

## When to use

Building a Python algotrading system that talks to Interactive Brokers. For account management or reporting in cloud contexts (without active trading), the IBKR Web API + OAuth is a separate path -- not this file.

## TWS vs IB Gateway (the only choice that matters)

**Use IB Gateway in production** -- lighter RAM/CPU footprint than TWS, smaller attack surface, API enabled by default. TWS is for development when you want the GUI alongside.

| Aspect | TWS | IB Gateway |
|--------|-----|------------|
| Default ports (live/paper) | 7496 / 7497 | 4001 / 4002 |
| API enabled by default | No (manual toggle) | **Yes** |
| Auto-update | Yes | Offline version only |

Both: max 32 simultaneous connections, manual login required (use IBC for automation, see `gateway-automation.md`), use the **offline/standalone build in production** -- the auto-updater silently breaks bots.

## Gotchas

- **Never `time.sleep()` in a TWS API callback.** It blocks the entire event loop and freezes message processing. Use `ib.sleep(seconds)` or `asyncio.sleep()`. CPU work in callbacks goes through `loop.run_in_executor()`.
- **The sync API twins are a trap inside async code.** Every `IB.x()` has an `IB.xAsync()` counterpart; the sync form calls `run_until_complete` internally and raises `RuntimeError: This event loop is already running` when invoked from a coroutine. The failure shape is an order-preparation path that crashes on a sync call such as `IB.accountSummary()` and never sends the order. Inside any async context, only the `*Async` forms are safe.
- **`clientId=0` is special** -- it merges with manual TWS trading and sees orders placed by hand. Bots should use dedicated non-zero IDs (1=data, 2=orders, 3=monitoring). Configure a Master Client ID in TWS to receive updates from all clients: the master receives `orderStatus`/`openOrder` for every API client, clientId 0 receives its own plus manual TWS orders, and a master set to 0 receives TWS, FIX and all API orders together. `reqAutoOpenOrders` (auto-binding of new manual orders) works **only** on clientId 0, and binding assigns the manual order an API id (negative by default, per the "Use negative numbers to bind automatic orders" setting).
- **One brokerage session per username, across all IBKR products.** A second login (TWS, Gateway, Client Portal, mobile) can take the session; the losing side is disconnected, and IBKR's own note for error 1100 lists "a competing session" among its causes. Automation needs a dedicated username (additional usernames per account are supported); two processes sharing one username steal the session from each other indefinitely.
- **Do not reuse a bot's username in Client Portal.** Documented consequences, easy to hit while "just checking the account" in a browser: that TWS/Gateway session loses the ability to auto-reconnect after the next disconnection, and a paper session sharing the live user's market data stops receiving data entirely.
- **Error 326 = "clientId already in use."** Restart-safe IDs require a dedicated assignment scheme. A half-open socket left behind by a cancelled connect attempt can also collide with the next attempt (see `reconnection-resilience.md`).
- **IBKR Web API (formerly Client Portal API) has a 10 req/sec global limit**, HTTP 429 on excess, and a roughly 10-minute IP penalty box (repeat violators can be blocked outright). IBKR is merging Client Portal Web API, Digital Account Management, and Flex into one "Web API" brand; older docs use both names for the same product. Useless for active trading -- the TWS API socket is the only serious choice.
- **`ib_insync` is archived** (March 2024, after the author's passing). Migration to `ib_async` is nearly drop-in: `from ib_async import *`.
- **Pin `ib_async` with an upper bound** (`ib_async<3.0.0`) and record why: the library forked from ib_insync in 2024, and a future major could change the `errorEvent` signature or `placeOrder` semantics. A pin forces an explicit upgrade decision instead of passive drift.
- **ib_async's event layer is `aeventkit`**, the ib-api-reloaded fork of eventkit (the original package's PyPI publishing is blocked). The import name and logger names remain `eventkit.*`, so existing logging routing keeps working; only the installed distribution name changed.
- **ib_async normalizes sizes to `float`** (verified on 2.1.0: every `Ticker` size field is typed `float`), while ibapi 10.44+ migrates size fields to `Decimal` on the wire. Sub-share precision can be lost in the client layer; never echo a ticker-derived price or size back into an order without snapping to the market rule and size increment first.
- **Silent-empty is the default failure shape** (verified on 2.1.0): `IB.RaiseRequestErrors` defaults to `False`, so a failed request returns an empty result instead of raising, and `IB.RequestTimeout` defaults to `0`, waiting indefinitely, while `reqHistoricalData` alone carries its own 60 s timeout that returns an empty series. Decide per system, explicitly, which of the three behaviours you want.
- **PyPI `ibapi` is frozen, not merely lagging.** The package is IBKR-authored (author "IBG LLC") but its last upload is 9.81.1.post1 from December 2020 (verified against PyPI metadata 2026-08-13). The current client ships only inside the TWS API download; `ibapi-latest` / `ibapi-stable` on PyPI are unofficial community re-packagers of that source, updated automatically and not IBKR-endorsed. Either build the wheel from the official zip or pin an exact mirror version knowingly.
- **Threading vs asyncio**: ib_async (asyncio) is more robust for production. When integrating with sync frameworks (Flask, Django), put IB work in a dedicated thread with its own asyncio loop and communicate via queues -- mixing event loops cross-thread will eventually deadlock.

## Connection skeleton

```python
from ib_async import *

async def main():
    ib = IB()
    await ib.connectAsync('127.0.0.1', 4001, clientId=1)
    contract = Stock('AAPL', 'SMART', 'USD')
    await ib.qualifyContractsAsync(contract)
    # ...
    ib.disconnect()

asyncio.run(main())
```

Three event-loop styles: `ib.run()` (sync, simplest standalone bots), `asyncio.run()` with `*Async` methods (max control), `util.startLoop()` (Jupyter via nest_asyncio).

## Official docs

The canonical documentation tree moved to `https://www.interactivebrokers.com/docs/tws-api/doc/` (it blocks automated fetching; browse it interactively). The older IBKR Campus paths below still resolve and coexist with it, and `https://interactivebrokers.github.io/tws-api/` is an official, fetchable reference that may lag the newest codes.

- IBKR API Home: https://www.interactivebrokers.com/campus/ibkr-api-page/ibkr-api-home/
- TWS API docs: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/
- API Reference: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-ref/
- Changelog: https://www.interactivebrokers.com/campus/ibkr-api-page/tws-api-changelog-2/
- Release notes: https://ibkrguides.com/releasenotes/prod-2026.htm (year-stamped URL; bump the year annually)
- ib_async repo: https://github.com/ib-api-reloaded/ib_async
- ib_async docs: https://ib-api-reloaded.github.io/ib_async/

## Related libraries

- **IBC** (https://github.com/IbcAlpha/IBC) -- login automation for TWS/Gateway, 2FA handling, auto-restart. **Essential for production.** See `gateway-automation.md`.
- **gnzsnz/ib-gateway-docker** -- Docker image with IB Gateway + IBC, supports simultaneous live+paper. Actively maintained.
- **NautilusTrader** -- professional platform with IB adapter, backtest + live in one framework.

## Community resources and reference architectures

- **pysystemtrade** (https://github.com/pst-group/pysystemtrade): gold standard reference -- Rob Carver's fully automated futures trading system. Uses **ib_async**. Moved to the `pst-group` GitHub org in January 2026; Andy Geach is primary maintainer (since 2024), jointly owned with Rob Carver.
- **9600dev/mmr** (https://github.com/9600dev/mmr): LLM-native platform with ib_async + ZeroMQ + DuckDB, modern proposal-based order management. Actively maintained.
- AlgoTrading101 -- IB Python Native API: https://algotrading101.com/learn/interactive-brokers-python-api-native-guide/
- AlgoTrading101 -- ib_insync guide (API surface still matches ib_async): https://algotrading101.com/learn/ib_insync-interactive-brokers-api-guide/
- Rob Carver's blog: https://qoppac.blogspot.com/2017/03/interactive-brokers-native-python-api.html (2017 multi-part series, battle-tested)
- Book: "Algorithmic Trading with Interactive Brokers" by Matthew Scarpino
- YouTube -- Part Time Larry: beginner tutorials from the ib_insync era, still API-compatible
- YouTube -- Adi's livestream VODs: the community video resource credited in the ib_async README
- Reddit r/algotrading (~1.9M members): most active for IB + Python discussions
- Elite Trader IB Forum: https://www.elitetrader.com/et/forums/interactive-brokers.10/
- IBKR Campus Quant Blog: https://www.interactivebrokers.com/campus/ibkr-quant-news/
- Stack Overflow (tags: `interactive-brokers`, `ib-insync`): moderate activity, useful for specific problems

## Related

- `event-driven-data.md` -- subscribing to ticks, bars, tick-by-tick
- `order-execution.md` -- placing orders, brackets, execDetails monitoring
- `order-lifecycle-contracts.md` -- what "placed" means, verdict windows, terminal presets
- `reconnection-resilience.md` -- daily reset, zombie connections, recovery patterns
- `gateway-automation.md` -- IBC, launcher patterns, Windows deployment
