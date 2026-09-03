# Case: mapper-scope-in-team-mode

Under team mode the interconnect mapper is scoped to the cross-partition surface: the exports one partition consumes from another, the flows that cross, the contracts marked `<this> <-> <other>`, the risks attributed across. Partition-internal contracts are already in the partition outputs, and a map that re-derives them for a whole monorepo either truncates at its length cap or swamps the reviewer. This case checks that the map stayed on the boundary.

## Setup

The two-package workspace from `team-mode-partition-ownership`, with `web` importing two symbols from `api`, and each package carrying at least three purely internal contracts (a private ordering constraint, an internal invariant, a module-level assumption) that never cross the boundary.

## Run

```
/codebase-xray:team-analyze . --yes
```

Full depth, so the mapper runs. Keep the transcript.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | `08-interconnect-map.md` exists in the run directory and its header names the cross-partition scope |
| 2 | MUST | Every row in `## Call Graph` involves a symbol that crosses the `api` / `web` boundary |
| 3 | MUST | The two consumed `api` symbols appear in `## Contracts` or `## Call Graph` with citations on both sides of the boundary |
| 4 | MUST | None of the six purely internal contracts planted in the setup appears in the map |
| 5 | SHOULD | The map is shorter than the sum of the two partitions' `04-semantics.md` hidden-contract sections |

## Scoring notes

Assertion 4 is the scope check. Each planted internal contract is identifiable by the names it uses; grep the map for them. One appearing because it is genuinely reachable from a crossing edge is a judgement call to record in the observations, not an automatic fail; three appearing is a widened scope and a fail.
