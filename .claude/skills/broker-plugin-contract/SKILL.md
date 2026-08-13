---
name: broker-plugin-contract
description: >
  What a broker-integration plugin in this marketplace must contain to reach contract level
  base or verified: the checklist for each level, the two declaration lines and how <broker>
  is derived from the plugin name, the describe-but-never-dispatch dependency rule, and what
  `scripts/lint_broker_plugins.py` enforces mechanically versus what stays prose-reviewed.
  TRIGGER WHEN: creating a new broker-integration plugin, bringing an existing one onto the
  contract, reviewing whether a broker plugin qualifies for base or verified, or interpreting
  a failure from `scripts/lint_broker_plugins.py`.
  DO NOT TRIGGER WHEN: the question is about the shared vocabulary itself rather than a
  specific plugin's conformance (use `trading-broker-connectivity`), or the plugin in question
  is not a broker integration (any category other than `algotrading`).
---

# Broker plugin contract

Every broker-integration plugin in this marketplace (category `algotrading`, one plugin per
vendor: `ibkr-trading`, `mt5-trading`, and any that follow) states its conformance to one of
two levels, in its own words, at the top of its main skill. This file is the checklist behind
that statement. `plugins/trading-broker-connectivity/` is the vocabulary a broker plugin draws
on to satisfy it: the five archetypes, the reference order-lifecycle model, and the evidence
ladder with its three provenance tags. Read that skill first if the vocabulary itself, rather
than a specific plugin's conformance, is the open question.

## The two levels

`base` is a plugin that is well formed and correctly slotted into the shared vocabulary: it
exists in the right shape, is registered where the marketplace needs it to be, and describes
itself honestly. `verified` adds the harder claim: that specific facts in it were measured
against a real broker environment rather than assumed or merely read from documentation, and
that the tooling making those measurements cannot reach a production account.

A plugin registered under category `algotrading` must declare one of the two levels;
`trading-broker-connectivity` itself is the one exception, since it is the vocabulary rather
than an integration. Skipping the declaration entirely fails the linter the same way declaring
a level or archetype that does not exist does.

A plugin does not have to reach `verified`. `base` is a complete, honest, shippable state on
its own. `verified` is for a plugin whose author has done the probing work described in
`trading-broker-connectivity`'s evidence ladder and wants the plugin to say so credibly rather
than by assertion.

## Level base

All five, as a checklist:

1. A `<broker>-architect` agent, a `<broker>-audit` command, and one skill with a
   `references/` directory, all three registered in `.claude-plugin/marketplace.json`, not
   merely present on disk. A file the marketplace does not list does not load.
2. The skill's `description` frontmatter carries both `TRIGGER WHEN` and `DO NOT TRIGGER
   WHEN`, the routing pair every skill in this marketplace uses.
3. The `SKILL.md` carries four sections: Quick start, Key decision points, Symptoms to entry
   points, Reference materials.
4. The plugin declares one of the five canonical archetype names from
   `trading-broker-connectivity` (`direct-api`, `local-terminal`, `vendor-gateway`, `bridge`,
   `in-platform`). Pick the one the integration actually uses; do not default to
   `local-terminal` because the two plugins that exist today both are it.
5. The plugin uses the reference model's names for order states, and where the vendor uses
   different ones it maps them explicitly, rather than silently substituting one vocabulary
   for the other. `order-lifecycle-reference-model.md` in `trading-broker-connectivity` names
   the target vocabulary and states the procedure for writing the mapping.

## Level verified

Everything in Level base, plus four more:

1. A `<broker>-verify` command with probe scripts that measure against a demo or paper
   environment, in the shape `evidence-and-probes.md` describes: a claim stated so it can
   fail, the cheapest instrument that can answer it, and a kept transcript.
2. A register of open questions, each paired with the experiment that would settle it, kept in
   a reference file rather than left as a comment or in an issue tracker only the author reads.
3. Every `MEASURED` fact carries its date and the instrument that measured it, so a reader can
   tell a probe run today from one run a year ago against a since-changed venue.
4. The probe tooling refuses production structurally, not by configuration. A flag that
   defaults to safe and can be flipped is not the same guarantee as code with no path to a
   production endpoint at all; the second is what this level requires.

## How a plugin declares its level

Two lines, placed immediately after the skill's `# Title` heading and before its first `##`
section:

```
**Contract level:** <base|verified>
**Archetype:** <name>
```

`<broker>` in the checklists above is the plugin directory name with a trailing `-trading`
removed: `ibkr-trading` becomes `ibkr`, `mt5-trading` becomes `mt5`. A plugin whose directory
name does not end in `-trading` keeps its name unchanged.

## The describe-but-never-dispatch rule

A broker plugin may name another plugin in prose. A comparison, an aside noting that another
plugin shares the same archetype, a pointer to `trading-broker-connectivity` for the
vocabulary it is using: none of that is a dependency, and none of it needs declaring.

What crosses the line is an instruction that makes something run: a `subagent_type:` spawn
naming another plugin's agent, or an instruction to load a skill from another plugin. The
moment a broker plugin's body carries either shape, it has taken on a real dependency on that
other plugin, and this marketplace's standing policy (`CLAUDE.md`, "Dependency policy: every
internal dependency is mandatory") says a local dependency is always declared in
`dependencies`, never left optional or unstated. `scripts/lint_dependency_graph.py` already
enforces this for every plugin in the marketplace, broker plugins included; this contract adds
nothing to that mechanism, it only names the consequence for this family of plugin.

The generic plugin, `trading-broker-connectivity`, must never dispatch into a broker plugin at
all: no agent spawn, no skill load, in either direction. It exists to be read by broker
plugins that do not know about each other, so a broker plugin depending on it is the intended
shape of the tree. The reverse, the generic plugin spawning or skill-loading something inside
`ibkr-trading` or `mt5-trading`, would make the shared vocabulary depend on one specific
vendor and invert that tree: every broker plugin would risk pulling in every other broker
plugin's install through the one thing they all share.

## What the linter checks and what it cannot

`scripts/lint_broker_plugins.py` decides the parts of the checklists above that are questions
about a directory listing, a marketplace entry, or a regular-expression match. It cannot
decide the parts that are questions about meaning:

- Whether a fact tagged `MEASURED` genuinely has the provenance it claims (Level verified
  item 3): the linter reads no probe transcript and forms no opinion on whether a date and an
  instrument are honest. It does not even search for the tag.
- Whether the shared vocabulary is used correctly inside prose (Level base item 5): the linter
  confirms the two declaration lines exist and name a real level and a real archetype; it does
  not read the rest of the file to confirm the order-state names are the reference model's own
  or that a vendor mapping is both present and correct.
- Whether an open-questions register (Level verified item 2) genuinely pairs each question
  with a settling experiment, or is a heading with an empty list under it: the linter looks
  for the heading, not the pairing.
- Whether the probe tooling refuses production structurally rather than by a flag that
  defaults to safe (Level verified item 4): the linter confirms a script matching
  `*probe*.py` exists under the skill's `scripts/` directory. It does not read the script.

Two more limits are honest gaps rather than deliberate scope, named here rather than left to
surprise a future maintainer. The linter confirms the `<broker>-architect` agent and
`<broker>-audit` command are registered in `.claude-plugin/marketplace.json`, but it does not
cross-check that the skill directory itself appears in that plugin's `skills` array: it finds
`SKILL.md` files by walking the plugin's directory on disk, not by reading the manifest. It
also does not require a `references/` directory to exist at all; it only checks that whatever
a skill's `references/` holds matches whatever its `SKILL.md` lists, so a skill with neither
has nothing to disagree about. Closing either gap is future work, not a claim this version
makes.

A failure from the linter is fixed by changing the plugin, never by adding an entry to the
linter's `ALLOWLIST`. That constant exists for heuristic misreads, and a broker plugin
correctly reported as non-conformant is not one.
