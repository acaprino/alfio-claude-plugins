---
name: broker-vocabulary
description: >
  Vendor-neutral vocabulary for programmatic broker integration: the five access archetypes, the
  second axis separating a single broker from a multi-broker platform, the reference order state
  machine, session and recovery, and the evidence ladder that decides what a claim about a venue is
  worth.
  Use when comparing brokers or integration paths, starting an integration against a broker with
  no dedicated skill, or naming what kind of access path a system uses. Not for a specific broker
  that already has its own skill, or for strategy, backtesting, or portfolio construction.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: trading-broker-integration
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
recovery story is available to you. A vendor is not an archetype: the same broker can be `direct-api`
for one product and `local-terminal` for another (`access-archetypes.md` has IBKR as its own
counterexample), so state the archetype of the path you are on, not the vendor's name. With that
caveat, Interactive Brokers and MetaTrader 5 are both `local-terminal` on the paths this marketplace
documents, which is why their operational problems are the same problems. Sharing an archetype
transfers operational lessons; it does not transfer facts.

A second axis, independent of the archetype, separates a `single-broker` subject from a
`multi-broker-platform` one sitting many independent brokers behind the same software. IBKR is
`single-broker` and MetaTrader 5 is `multi-broker-platform`, and a fact measured on one broker is not
even guaranteed to hold for the next broker on the same platform.

## Evidence

Claims about venue behaviour are ranked on an evidence ladder, from your own probe transcript down to
a search-engine or AI summary that is not evidence at any strength. The ladder has **six ranks**, and
every claim about broker behaviour in a repository carries one of three provenance tags: `MEASURED`,
`DOCUMENTED` or `ASSUMED`.

## Reference materials

- `access-archetypes.md`: the five archetypes, what changes between them (session state, blast radius,
  what you must keep alive, the failure surface each adds), the second axis separating a single
  broker from a multi-broker platform, and where the two integrated brokers sit on both
- `order-lifecycle-reference-model.md`: the reference state machine keyed on who has acknowledged what,
  the three layers that can refuse an order, the three identifiers and what survives a cancel or a
  replace, what a successful place call proves, and how to map a vendor's vocabulary onto this one
- `session-and-recovery.md`: the three session-exclusivity regimes, authentication with no human in the
  loop, the connection flag that lies, reconciling ground truth after a gap, and what must be persisted
- `evidence-and-probes.md`: the evidence ladder, the provenance tags, how to design a probe that
  answers something, and the question classes a demo environment cannot settle

## Adding a vendor skill

A new vendor skill in this bundle (alongside `ibkr` and `mt5`) earns its place by using this
vocabulary rather than reinventing one. It should carry four sections, in the shape the two
existing vendor skills already use: **Quick start** (the handful of decisions that get someone
running today), **Key decision points** (default versus when to deviate, as a table), **Symptoms
to entry points** (a table from what a user is seeing to the reference file that explains it),
and **Reference materials** (what each reference file covers, so a reader can pick the right one
without opening several).

Two things carry across every vendor skill regardless of section structure. First, state
provenance on any fact that matters: whether it was measured against a real account, read and
quoted from documentation, or assumed. An unmarked claim reads as more certain than it is, and
the reader has no way to tell a fact worth trusting from one worth re-checking. Second, map the
vendor's own order-state and order-type vocabulary onto `order-lifecycle-reference-model.md`'s
names, explicitly, rather than silently writing in the vendor's words and leaving the reader to
translate. `ibkr` and `mt5` both carry a table doing exactly this; follow their shape.
