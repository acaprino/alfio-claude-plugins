# TWS API Architecture and ib_async

The TWS API is a local TCP socket protocol (Protocol Buffers since 10.40) between Python and TWS or IB Gateway. Current production version: **10.44** (Feb 2026), minimum supported 10.30. Use `ib_async` (the maintained successor to ib_insync) for all new code unless you have a specific reason to use the official ibapi.

## When to use

Building a Python algotrading system that talks to Interactive Brokers. For account management or reporting in cloud contexts (without active trading), the IBKR Web API + OAuth is a separate path -- not this file.

## TWS vs IB Gateway (the only choice that matters)

**Use IB Gateway in production** -- ~40% less RAM/CPU than TWS, smaller attack surface, API enabled by default. TWS is for development when you want the GUI alongside.

| Aspect | TWS | IB Gateway |
|--------|-----|------------|
| Default ports (live/paper) | 7496 / 7497 | 4001 / 4002 |
| API enabled by default | No (manual toggle) | **Yes** |
| Auto-update | Yes | Offline version only |

Both: max 32 simultaneous connections, manual login required (use IBC for automation), use the **offline/standalone build in production** -- the auto-updater silently breaks bots.

## Gotchas

- **Never `time.sleep()` in a TWS API callback.** It blocks the entire event loop and freezes message processing. Use `ib.sleep(seconds)` or `asyncio.sleep()`. CPU work in callbacks goes through `loop.run_in_executor()`.
- **`clientId=0` is special** -- it merges with manual TWS trading and sees orders placed by hand. Bots should use dedicated non-zero IDs (1=data, 2=orders, 3=monitoring). Configure a Master Client ID in TWS to receive updates from all clients.
- **Error 326 = "clientId already in use."** Restart-safe IDs require a dedicated assignment scheme.
- **Web API has a 10 req/sec global limit** with a 10-15 minute IP penalty box. Useless for active trading -- TWS API socket is the only serious choice.
- **`ib_insync` is archived** (March 2024, after the author's passing). Migration to `ib_async` is nearly drop-in: `from ib_async import *`.
- **Official ibapi on PyPI is from 2020 (9.81.1) -- outdated.** If you need it, install from the TWS API download, not PyPI.
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

- IBKR API Home: https://www.interactivebrokers.com/campus/ibkr-api-page/ibkr-api-home/
- TWS API docs: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/
- API Reference: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-ref/
- Changelog: https://www.interactivebrokers.com/campus/ibkr-api-page/tws-api-changelog-2/
- 2026 release notes: https://ibkrguides.com/releasenotes/prod-2026.htm
- ib_async repo: https://github.com/ib-api-reloaded/ib_async
- ib_async docs: https://ib-api-reloaded.github.io/ib_async/

## Related libraries

- **IBC** (https://github.com/IbcAlpha/IBC) -- login automation for TWS/Gateway, 2FA handling, auto-restart. **Essential for production.**
- **gnzsnz/ib-gateway-docker** -- Docker image with IB Gateway + IBC, supports simultaneous live+paper.
- **NautilusTrader** -- professional platform with IB adapter, backtest + live in one framework.

## Related

- `event-driven-data.md` -- subscribing to ticks, bars, ticks-by-tick
- `order-execution.md` -- placing orders, brackets, execDetails monitoring
- `reconnection-resilience.md` -- daily reset, IBC, recovery patterns
