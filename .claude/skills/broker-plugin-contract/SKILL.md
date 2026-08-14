---
name: broker-plugin-contract
description: >
  What a broker-integration plugin in this marketplace must contain to reach contract level
  base or verified: the checklist for each level, the three declaration lines and how <broker>
  is derived from the plugin name, the single-broker/multi-broker-platform scope axis, the
  describe-but-never-dispatch dependency rule, and what
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
on to satisfy it: the five archetypes, the second axis separating a single broker from a
multi-broker platform, the reference order-lifecycle model, and the evidence ladder with its
three provenance tags. Read that skill first if the vocabulary itself, rather than a specific
plugin's conformance, is the open question.

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

All six, as a checklist:

1. A `<broker>-architect` agent, a `<broker>-audit` command, and one skill with a non-empty
   `references/` directory (at least one `.md` file), all three registered in
   `.claude-plugin/marketplace.json`, not merely present on disk. A file the marketplace does
   not list does not load.
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
6. The plugin declares its scope (`**Scope:**` line, one of the two values
   `trading-broker-connectivity`'s second axis defines), and a plugin whose scope is
   `multi-broker-platform` carries a section naming what varies per broker behind it.

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

### What scope changes about a `MEASURED` fact

On a `single-broker` plugin, a `MEASURED` fact is a fact about the broker: it holds, subject to
entity and entitlement, for every account on it. On a `multi-broker-platform` plugin, the same
tag is a fact about **one broker on that platform**, and the fact must name which broker,
alongside the date and instrument item 3 above already requires. Without the broker, the tag
claims more than the measurement supports: the next broker on that platform may configure the
same instrument, the same fill mode, or the same margin rule differently, and nothing in an
unattributed `MEASURED` warns a reader of that.

## How a plugin declares its level

Three lines, placed immediately after the skill's `# Title` heading and before its first `##`
section:

```
**Contract level:** <base|verified>
**Archetype:** <name>
**Scope:** <single-broker|multi-broker-platform>
```

`<broker>` in the checklists above is the plugin directory name with a trailing `-trading`
removed: `ibkr-trading` becomes `ibkr`, `mt5-trading` becomes `mt5`. A plugin whose directory
name does not end in `-trading` keeps its name unchanged.

`**Scope:**` names one of the two values `trading-broker-connectivity`'s second axis defines,
described in `access-archetypes.md`'s "The second axis: one broker or many" section: whether the
plugin's subject is one broker, or a platform with many independent brokers behind it.

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
  item 3), and on a `multi-broker-platform` plugin, whether it genuinely names the one broker
  it was measured against: the linter reads no probe transcript and forms no opinion on
  whether a date, an instrument or a broker are honest. It does not even search for the tag.
- Whether the shared vocabulary is used correctly inside prose (Level base item 5): the linter
  confirms the three declaration lines exist and name a real level, a real archetype and a
  real scope; it does not read the rest of the file to confirm the order-state names are the
  reference model's own or that a vendor mapping is both present and correct.
- Whether an open-questions register (Level verified item 2) genuinely pairs each question
  with a settling experiment, or is a heading with an empty list under it: the linter looks
  for the heading, not the pairing.
- Whether a `multi-broker-platform` plugin's per-broker-variation section (Level base item 6)
  genuinely names what varies, or is a heading with nothing under it: the linter looks for the
  heading, the same limit as the open-questions register above.
- Whether the probe tooling refuses production structurally rather than by a flag that
  defaults to safe (Level verified item 4): the linter confirms a script matching
  `*probe*.py` exists under the skill's `scripts/` directory. It does not read the script.
- Where exactly the three declaration lines sit in the file: "How a plugin declares its level"
  states a placement convention (immediately after the `# Title` heading, before the first
  `##` section) for readers, not a rule the linter enforces. The regexes that find
  `**Contract level:**`, `**Archetype:**` and `**Scope:**` match anywhere in the file, on
  purpose, so a plugin that is otherwise conformant never fails on where the three lines
  happen to sit.

One more limit is worth naming precisely rather than leaving it to read as a gap: whether the
skill directory itself appears in that plugin's `skills` array in
`.claude-plugin/marketplace.json` is not something `lint_broker_plugins.py` cross-checks; it
finds `SKILL.md` files by walking the plugin's directory on disk, not by reading the manifest.
That declaration is still checked, just not here. `scripts/lint_plugin_registration.py`
already validates every plugin's `agents`, `skills` and `commands` arrays against what is
actually on disk, in both directions, for every plugin in the marketplace, broker plugins
included. Duplicating that check inside this linter would give the same fact two places to
drift apart from each other; it stays a single check owned by a single script.

A failure from the linter is fixed by changing the plugin, never by adding an entry to the
linter's `ALLOWLIST`. That constant exists for heuristic misreads, and a broker plugin
correctly reported as non-conformant is not one.
