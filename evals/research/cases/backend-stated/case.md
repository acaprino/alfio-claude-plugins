# Case: backend-stated

## Run
Two fresh sessions, scratch directory, with `SERPER_API_KEY` UNSET in both.
Run A: `/research:team-research "Current status of WebGPU support across browsers" --auto --depth quick`
Run B: `/research:team-research "Current status of WebGPU support across browsers" --auto --backend serper`

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Run A's plan and report header both state `Backend: websearch` |
| 2 | MUST | Run B stops before any researcher is spawned and prints the websearch.py setup line (names `SERPER_API_KEY`) |
| 3 | MUST | Run A's spawn prompts each carry a `Backend:` line |
| 4 | SHOULD | If a key IS available on the machine, a third run with `--backend auto` states `Backend: serper` in plan and header (n/a otherwise) |
