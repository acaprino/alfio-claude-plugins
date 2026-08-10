# Case: jupiter-position-notice-owner

- **Repo:** `D:\Projects\jupiter`
- **Review rev:** `1d988c53~1`
- **Fix rev (do not show the reviewer):** `1d988c53` (fix(telegram): address a position notice to the owning account only)
- **Review scope:** `jupiter-channel-telegram/**/telegram_channel_event.py`

## Ground truth

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | A position notice is delivered beyond the owning account: recipients other than the position's owner receive another account's position information, an authorization/addressing defect in the notification fan-out | security / logic-integrity |

## Scoring notes

- Credit `found` for identifying the missing owner filter on the recipient set; the privacy consequence (cross-account position disclosure) should be stated for full credit.
