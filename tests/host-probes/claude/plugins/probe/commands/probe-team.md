---
description: Two-worker coordination probe for Claude Code.
argument-hint: "[none]"
---

# Daodan two-worker coordination probe

Dispatch two `daodan-probe:probe-worker` workers, one with nonce `alpha` and one with nonce `beta`.

Requirements:

1. Each worker runs in its own isolated context and never sees the other worker's result.
2. Run both workers in parallel when the host supports it. Fall back to serial dispatch otherwise.
3. Wait until both workers have delivered before returning anything.
4. Return the two nonce lines followed by `DELIVERED=2/2`.

If native Agent Teams are available, run the probe once through a team and once through plain isolated
subagents, and report which mechanisms answered. Record the result in `tests/host-probes/README.md`.
