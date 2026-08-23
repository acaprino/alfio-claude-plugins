# Case: tier-bands

## Run
Two fresh sessions, scratch directory.
Run A: `/research:team-research "Compare Pydantic v2 and attrs for a data-validation layer" --auto --depth quick`
Run B: `/research:team-research "How should a small team evaluate, adopt and govern AI coding assistants in 2026: productivity evidence, security and IP risk, licensing, and rollout practice?" --auto --depth deep`

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Run A spawns 1-2 deep-researcher instances and no second wave |
| 2 | MUST | Run B spawns 6-12 deep-researcher instances in total, across at most two waves, all instances of a wave in one message |
| 3 | MUST | Every spawn prompt in B carries a Budget line matching the deep tier (25 searches / 20 pages / 6 rounds) |
| 4 | MUST | Run B's header reports pages read and researchers per wave |
| 5 | SHOULD | Run B's pages read is 100 or more |
