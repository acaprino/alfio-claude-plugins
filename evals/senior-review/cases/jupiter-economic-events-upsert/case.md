# Case: jupiter-economic-events-upsert

- **Repo:** `D:\Projects\jupiter`
- **Review rev:** `77381da4~1`
- **Fix rev (do not show the reviewer):** `77381da4` (fix(core): upsert economic events on unique_id so provider revisions land)
- **Review scope:** `jupiter-core/jupiter_core/services/beanie/economic_event_repository.py`

## Ground truth

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | Economic events are inserted without upserting on their natural key (`unique_id`): a provider revision of an already-stored event either duplicates it or is dropped instead of updating the stored row; identity lives in the application's assumptions, not in the write path | data-integrity |

## Scoring notes

- This is the target case for the data-integrity dimension (uniqueness assumed, not enforced at the write). `partial` for flagging duplicate risk without the revision-update consequence.
