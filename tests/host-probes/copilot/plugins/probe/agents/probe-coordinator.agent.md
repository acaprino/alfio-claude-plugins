---
name: probe-coordinator
description: Two-worker coordination probe coordinator, restricted to the probe worker.
tools: ['agent']
agents: ['probe-worker']
---

# Daodan two-worker coordination probe

Dispatch two `probe-worker` agents, one with nonce `alpha` and one with nonce `beta`.

Requirements:

1. Each worker runs in its own isolated context and never sees the other worker's result.
2. Run both workers in parallel when the host supports it. Fall back to serial dispatch otherwise.
3. Wait until both workers have delivered before returning anything.
4. Return the two nonce lines followed by `DELIVERED=2/2`.

You may dispatch `probe-worker` and nothing else. If you can dispatch any other agent, the worker
allowlist is not enforced: record that in `tests/host-probes/README.md`.
