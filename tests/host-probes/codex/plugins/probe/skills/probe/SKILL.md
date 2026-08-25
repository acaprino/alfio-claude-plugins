---
name: probe
description: Single-worker output-contract probe, plus the two-worker coordination probe. TRIGGER WHEN: running the disposable Daodan host protocol probe.
---

# Daodan single-worker probe

Return exactly DAODAN_PROBE_OK.

Do not add commentary, formatting or any other text.

# Daodan two-worker coordination probe

When asked for the coordination probe instead, dispatch two workers, one with nonce `alpha` and one
with nonce `beta`. Prefer the packaged `probe` role in `.codex/agents/probe.toml`. If that role is not
discoverable, supply this role body inline to a runtime subagent:

```text
You are given exactly one nonce value. Return exactly NONCE=<value> and nothing else.
Do not read another worker's result.
```

Requirements:

1. Each worker runs in its own isolated context and never sees the other worker's result.
2. Run both workers in parallel when the host supports it. Fall back to serial dispatch otherwise.
3. Wait until both workers have delivered before returning anything.
4. Return the two nonce lines followed by `DELIVERED=2/2`.

State which role-delivery path answered, packaged or inline, in `tests/host-probes/README.md`.
