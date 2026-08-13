---
name: trading-broker-connectivity
description: >
  Vendor-neutral vocabulary for programmatic broker integration: the five access archetypes, the
  reference order state machine, session and recovery, and the evidence ladder that decides what a
  claim about a venue is worth.
  TRIGGER WHEN: comparing brokers or integration paths, starting an integration against a broker with
  no dedicated plugin, or naming what kind of access path a system uses.
  DO NOT TRIGGER WHEN: the question is about one specific broker that has its own plugin, or about
  strategy, backtesting, or portfolio construction.
---

# Broker Connectivity

The vocabulary that is the same for every broker. Use it to name what kind of access path a system has,
to model an order's life without borrowing one vendor's words for it, and to say what a claim about a
venue is actually worth.

It exists because broker knowledge is written per vendor and therefore reads as if every problem were
unique. Most are not. Session exclusivity, a login built for a human, a connection flag that lies, a
place call that proves nothing, and a fact everybody repeats that nobody measured are properties of the
access path, and they recur across brokers that share nothing else.

## The five archetypes

| Archetype | Meaning |
|---|---|
| `direct-api` | A cloud API. No vendor component on your machine |
| `local-terminal` | A vendor application runs locally, holds the session, and may handle orders itself |
| `vendor-gateway` | A vendor-operated gateway or protocol engine, usually behind certification |
| `bridge` | Third-party software between a platform and a broker, operated by neither |
| `in-platform` | Code running inside the vendor's own application |

Name the archetype before designing anything. It decides what must run, what dies with what, and which
recovery story is available to you. Interactive Brokers and MetaTrader 5 are both `local-terminal`,
which is why their operational problems are the same problems.

## Evidence

Claims about venue behaviour are ranked on a six-rank ladder, from your own probe transcript down to a
search-engine or AI summary that is not evidence at any strength, and every claim in a repository
carries one of three provenance tags: `MEASURED`, `DOCUMENTED` or `ASSUMED`.

## Reference materials

- `access-archetypes.md`: the five archetypes, what changes between them (session state, blast radius,
  what you must keep alive, the failure surface each adds), and where the two integrated brokers sit
- `order-lifecycle-reference-model.md`: the reference state machine keyed on who has acknowledged what,
  the three layers that can refuse an order, the three identifiers and what survives a cancel or a
  replace, what a successful place call proves, and how to map a vendor's vocabulary onto this one
- `session-and-recovery.md`: the three session-exclusivity regimes, authentication with no human in the
  loop, the connection flag that lies, reconciling ground truth after a gap, and what must be persisted
- `evidence-and-probes.md`: the evidence ladder, the provenance tags, how to design a probe that
  answers something, and the question classes a demo environment cannot settle
