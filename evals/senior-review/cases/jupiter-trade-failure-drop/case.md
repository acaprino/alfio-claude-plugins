# Case: jupiter-trade-failure-drop

- **Repo:** `D:\Projects\jupiter`
- **Review rev:** `231a0212~1`
- **Fix rev (do not show the reviewer):** `231a0212` (fix(desktop): surface trade failure events instead of dropping them)
- **Review scope:** `jupiter-desktop/src-react/src/hooks/events/useTradeEvents.ts`, `jupiter-desktop/src-tauri/src/amqp/event_routing.rs`

## Ground truth

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | Trade FAILURE events are dropped instead of surfaced: the event routing forwards successes but a failed trade produces nothing on screen, the exact "silence over active damage" signature on the most consequential event class a trading desktop has | temporal-resilience (silent failure) / ui |

## Scoring notes

- Full credit requires the user-visible-consequence framing (operator never learns a trade failed), not just "unhandled event type".
