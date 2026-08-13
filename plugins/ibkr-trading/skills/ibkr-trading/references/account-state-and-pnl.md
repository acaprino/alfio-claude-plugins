# Account State, Positions and PnL

The surfaces that answer "what do I actually hold, and what is it worth", and why they disagree.

There are five of them, they update at different rates, two of them compute PnL from different sources
with different reset schedules, and none is a trade ledger. A system that treats any single one as the
truth will be wrong in a specific, predictable way. This file is about picking the right surface per
question and knowing what each one cannot tell you.

## The five surfaces

| Request | What it carries | Update behaviour | Scope |
|---|---|---|---|
| `reqPositions` | `account`, `Contract`, signed `position`, `avgCost` | Full snapshot, then `positionEnd`, then **only on change** | All associated accounts |
| `reqAccountUpdates` | `updateAccountValue`, `updatePortfolio`, `updateAccountTime`, `accountDownloadEnd` | Full state, then on position change **or every 3 minutes** | **One account at a time** |
| `reqAccountSummary` | The TWS Account Summary window values, by tag | Initial values, then changed values **every 3 minutes** | One or all managed accounts |
| `reqPnL` / `reqPnLSingle` | `dailyPnL`, `unrealizedPnL`, `realizedPnL` (plus `position`, `value` for single) | `pnlSingle` documented as **approximately once per second** | Account / model, or one `conId` |
| `reqExecutions` + `commissionReport` | Individual fills and their fees | Event-driven, on every full or partial fill | Current day (see below) |

**Only the last one is a ledger.** Positions and PnL are current-state views that overwrite themselves;
executions are the append-only record of how you got there. Any question of the form "what happened"
belongs to executions, and any question of the form "where am I now" belongs to the position feed.

## Three-minute data is not risk data

`reqAccountSummary` and `reqAccountUpdates` both push changed values on a **three-minute** cadence, and
IBKR states plainly that the summary's "update frequency of 3 minutes is the same as the TWS Account
Window and cannot be changed". Margin headroom read from these surfaces can therefore be three minutes
stale, which is an eternity in the only market conditions where headroom matters.

Consequences worth designing around:

- **Never gate an order on a three-minute margin figure alone.** For a pre-trade check, `whatIf=True`
  returns the venue's own margin projection for that specific order (`venue-questions-and-probes.md`).
- **`accountReady` is a documented staleness flag, and almost nobody reads it.** It arrives on
  `updateAccountValue`; when it is `false`, "the IB server is in the process of resetting at that
  moment" and the values may be "out of date or incorrect". Treat a `false` as a hold signal, not as
  data.
- **A second `reqAccountUpdates` silently replaces the first.** Only one account subscription can be
  active, and attempting another "will not yield any error message although it will override the
  already subscribed account with the new one". Two components each subscribing for their own account
  therefore leave one of them reading someone else's account, with nothing in the logs. Use
  `reqAccountUpdatesMulti` when more than one account or model is involved.

## Two PnL feeds that are allowed to disagree

This is the single most confusing part of the account surface, and it is documented rather than
mysterious: **the Account Window and the Portfolio Window compute PnL differently.** IBKR's wording is
that the two "will sometimes differ because there is a different source of information and a different
reset schedule".

| | `reqAccountUpdates` (Account Window) | `reqPnL` / `reqPnLSingle` (Portfolio Window) |
|---|---|---|
| Unrealized PnL updates | On a trade in that instrument, **or every 3 minutes** | `pnlSingle` approximately once per second |
| Realized PnL reset | **Reset to zero once per day** | Follows the reset schedule in TWS Global Configuration, instrument-specific by default |

So "realized PnL" without a stated source is not a number, it is a question. Two rules follow:

- **Name the surface in your own field names** (`account_window_realized_pnl`, not `realized_pnl`).
  Reconciling two feeds that were never meant to agree wastes a debugging session per occurrence.
- **The reset schedule is terminal configuration**, which puts daily-PnL semantics in the same category
  as order presets and the FX pip setting: an unversioned local input that changes your numbers without
  changing your code. Audit it per deployment.

Account-level PnL also has a prerequisite that fails silently: the TWS setting **"Prepare portfolio PnL
data when downloading positions"** must be checked, or account PnL subscriptions do not work properly.
On advisor structures with many subaccounts, aggregated PnL "can take several seconds" to compute, so a
timeout tuned for a single account will read as a failure there.

## Executions: current day, and less than you think under Gateway

`reqExecutions` with an empty `ExecutionFilter` does **not** backfill history. IBKR documents the
default as "only those executions occurring since midnight for that particular account", extensible "up
to last 7 days" only by adjusting the TWS Trade Log setting "Show trades for ...".

**That extension is unavailable to the deployment this plugin recommends.** IB Gateway cannot modify
Trade Log settings, so a Gateway-based system is restricted to midnight-onward executions, permanently.
The consequence is not subtle: **your durable trade ledger must be yours.** Persist every
`execDetails` and `commissionReport` as they arrive, keyed by full `execId` (corrections re-deliver the
same execution changing only the digits after the final period, see `order-lifecycle-contracts.md`),
and use Flex for anything older than today.

`ExecutionFilter` narrows by client id, account, time, symbol, secType, exchange and side, with the time
field documented as "only those executions reported after the specified time will be returned" in
`yyyymmdd hh:mm:ss` form. Use it to bound a reconnect reconciliation window rather than pulling
everything and filtering client-side.

## Positions: keying, and the shapes that are not events

`reqPositions` returns every associated account, so **the durable key is `(account, conId)`**, never
`conId` alone. Two properties bite:

- **There is no close event.** A partial close is a `position` callback with a smaller absolute
  quantity, and a flat position is a callback with zero. A reaper hooked on "position closed" misses
  both unless it interprets quantities (`order-lifecycle-contracts.md` has the netted-close hazard that
  follows from this).
- **`positionEnd` fires after the initial snapshot only.** It is the marker that says "you now have
  everything"; nothing similar arrives again, so any later gap is yours to detect.

**Above 50 subaccounts, `reqPositions` is not available at all.** IBKR documents it as unavailable "in
Introducing Broker or Financial Advisor master accounts that have very large numbers of subaccounts
(> 50)", with `reqPositionsMulti` as the per-subaccount replacement (it also carries `modelCode`). A
system that grows into an FA structure loses the call it was built on, so isolate the position feed
behind an interface from the start.

What IBKR does **not** document here, and what therefore needs measuring for your account:
`avgCost` unit semantics per class (whether a future's is per unit or notional, whether an option's
includes the multiplier, whether either includes commissions), the reporting currency and FX-translation
rule for the PnL fields, and whether every full closure emits a zero row. Each is a probe in
`venue-questions-and-probes.md` terms: cheap to run, expensive to assume.

## Account Summary tags worth knowing

The documented tag list includes `AccountType`, `NetLiquidation`, `TotalCashValue`, `SettledCash`,
`AccruedCash`, `BuyingPower`, `EquityWithLoanValue`, `GrossPositionValue`, `ReqTEquity`, `ReqTMargin`,
`SMA`, `InitMarginReq`, `MaintMarginReq`, `AvailableFunds`, `ExcessLiquidity`, `Cushion`,
`DayTradesRemaining` and `Leverage`, plus the `$LEDGER` family (`$LEDGER:USD` for one currency,
`$LEDGER:ALL` for every currency in the account) for per-currency cash rows.

Two practical notes: pass `"All"` as the group in non-advisor structures, and expect an **empty string**
rather than a number where a value has no price. A parser that assumes float breaks on the first such
row.

## Flex Web Service: the reconciliation source, not a feed

Flex is a standalone HTTP API that generates instances of query templates built by hand in Client
Portal. Its token lasts from six hours to one year, can be IP-restricted, and on linked accounts is
visible only from the master account.

It is the right tool for end-of-day and historical reconciliation, and the wrong tool for intraday
state: it is report-oriented and polled, not subscribed. What IBKR does not document, and what you must
therefore establish before depending on it, is how quickly a trade appears in Flex after execution and
whether every Flex trade row maps one-to-one onto a TWS `execId`. Measure both before making Flex the
arbiter of a disagreement.

## Restart behaviour

Every surface above is a subscription with an explicit cancel (`cancelPositions`, `cancelAccountSummary`,
`cancelPnL`, and the `subscribe=False` form of `reqAccountUpdates`), and IBKR documents no replay or
persistence contract across a reconnect. Treat a reconnected Gateway as a new session: re-issue every
subscription, wait for the snapshot markers (`positionEnd`, `accountDownloadEnd`) before trusting the
state, and reconcile the gap from your own ledger plus a bounded `reqExecutions` window. The reconnect
checklist lives in `reconnection-resilience.md`.

## Related

- `order-lifecycle-contracts.md` - the execution ledger's identity rules and the netted-close hazard
- `reconnection-resilience.md` - what to re-request after a drop, and in what order
- `order-execution.md` - where fills arrive from and why `execDetails` is authoritative
- `venue-questions-and-probes.md` - how to turn the undocumented items above into measurements
