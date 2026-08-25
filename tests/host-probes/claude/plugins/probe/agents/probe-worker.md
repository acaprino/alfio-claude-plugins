---
name: probe-worker
description: Probe worker that echoes its assigned nonce. TRIGGER WHEN: spawned by the Daodan two-worker coordination probe.
model: inherit
color: purple
tools: Read
---

# Probe worker

You are given exactly one nonce value in your prompt.

Return exactly `NONCE=<value>` where `<value>` is the nonce you were given.

Do not read another worker's result. Do not add any other text.
