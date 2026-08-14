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

## What counts as a broker-integration plugin

This contract applies to a plugin whose subject is a specific access path to specific brokers,
whether one (`single-broker`) or the set behind one piece of platform software
(`multi-broker-platform`). The category `algotrading` in `marketplace.json` is the linter's
roster, and it is broader than that: it is where any algorithmic-trading plugin belongs, and
membership in the category alone does not commit a plugin to the broker-integration shape this
file describes. What a future non-broker-integration plugin in that category should declare is
not decided here.

A multi-venue client library or aggregator, in the CCXT style, is not a broker-integration
plugin, and `multi-broker-platform` is the wrong scope for it even though it touches many
brokers. `multi-broker-platform` describes brokers that sit **behind** the subject, each
configuring its own instance of software the subject *is*. An aggregator sits **in front of**
venues that were built with no knowledge of it, wrapping their independent APIs into one
vocabulary of its own invention. Its facts split into two kinds this contract does not try to
unify: facts about the library itself (its retry behaviour, its own rate limiting, its own error
taxonomy) and facts about each wrapped venue, which the library did not create and cannot make
uniform. Level base item 5, one vendor-vocabulary mapping, is unbounded for a plugin wrapping N
vendor vocabularies, which is the mechanical symptom of the same mismatch. A plugin of that shape
needs a contract of its own; this one marks it out of scope rather than stretching to fit it.

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
4. The plugin declares one or more of the five canonical archetype names from
   `trading-broker-connectivity` (`direct-api`, `local-terminal`, `vendor-gateway`, `bridge`,
   `in-platform`), comma-separated if the plugin genuinely covers more than one access path to
   its subject. Pick the archetypes the integration actually uses; do not default to
   `local-terminal` because the two plugins that exist today both are it, and do not narrow what
   the plugin covers (for instance in its `DO NOT TRIGGER WHEN` clause) just to make a single
   archetype true of a smaller subject than the plugin actually documents.
5. The plugin uses the reference model's names for order states, and where the vendor uses
   different ones it maps them explicitly, rather than silently substituting one vocabulary
   for the other. `order-lifecycle-reference-model.md` in `trading-broker-connectivity` names
   the target vocabulary and states the procedure for writing the mapping. On a
   `multi-broker-platform` plugin, the mapping also states whether it varies per broker:
   execution mode alone can change which states are reachable at all, and a mapping silent on
   that question reads as one fixed mapping whether or not it is one.
6. The plugin declares its scope (`**Scope:**` line, one of the two values
   `trading-broker-connectivity`'s second axis defines), and a plugin whose scope is
   `multi-broker-platform` carries a section naming what varies per broker behind it.

## Level verified

Everything in Level base, plus four more:

1. A `<broker>-verify` command with probe scripts that measure against a demo or paper
   environment, in the shape `evidence-and-probes.md` describes: a claim stated so it can
   fail, the cheapest tradable instrument (or no instrument at all, settled instead by a
   validation-only, dry-run or capability call) that can answer it, and a kept transcript.
2. A register of open questions, each paired with the experiment that would settle it, kept in
   a reference file rather than left as a comment or in an issue tracker only the author reads.
3. Every `MEASURED` fact records its date and the shape `evidence-and-probes.md`'s probe-design
   step 4 names: instrument class, order type, time in force, attributes, account type,
   archetype, component version, client library version, broker and account entity. A reader
   must be able to tell a probe run today from one run a year ago against a since-changed venue,
   and to tell which broker or entity a load-bearing fact was measured against. Not every shape
   variable is load-bearing on every plugin; `evidence-and-probes.md` states when broker and
   entity are, and the subsection below states the consequence for this contract's two scope
   values.
4. The probe tooling refuses production structurally, not by configuration. A flag that
   defaults to safe and can be flipped is not the same guarantee as code with no path to a
   production endpoint at all; the second is what this level requires.

### What scope changes at level verified

`evidence-and-probes.md` already makes broker and account entity two of the shape variables a
probe transcript records, each conditionally load-bearing rather than always required. This
contract's scope declaration is what decides which condition applies, so this is a
specialization of the vocabulary's general rule, not a separate broker-naming rule. On a
`multi-broker-platform` plugin, broker is always load-bearing: a fact measured against one
broker on the platform is not evidence about the next, so a `MEASURED` tag that does not name
the broker claims more than the measurement supports. On a `single-broker` plugin, broker is
fixed by the plugin's own scope and does not need repeating in every tag, but account entity is
load-bearing whenever the broker's own rules can differ by entity or entitlement, which is
common enough that this contract's own `single-broker` definition already concedes facts hold
"subject to entity and entitlement." A `MEASURED` fact that never names the entity leaves that
qualifier unfalsifiable.

A `MEASURED` fact about a property that varies per broker is more useful with the runtime query
that reproduces it than with the broker name alone: a reader on a different broker cannot act on
someone else's measurement, but they can run the same query against their own login.
`mt5-trading` names both: its `## What varies per broker` section gives `account_info().margin_mode`
for margin mode, and its `order-execution.md` reference gives `symbol_info().filling_mode` for fill
mode. Prefer that pattern, the runtime query a reader can run against their own login, over a value
table that goes stale the moment one broker changes a setting. The plugin's own `order-execution.md`
carries such a table too ("Broker mode differences," `stops_level` given as "Often 0" for ECN
brokers and "Usually > 0" for market makers): read it as a starting expectation to verify at
runtime, not as the exemplar of the pattern this section recommends.

Probe budget is not spent evenly across a `multi-broker-platform` plugin's surface. What is
worth measuring and tagging `MEASURED` is the platform's own invariants: the API's semantics,
its error codes, the terminal's lifecycle, what a malformed request returns. Those transfer,
because they are the platform's contract with every broker behind it. Broker configuration does
not transfer: fill modes, stops levels, symbol specs and trading hours are settings, not
invariants, and a dated, attributed `MEASURED` tag on one of them makes a fact true of exactly
one login look authoritative, which is the opposite of what the tag is for. Detect configuration
at runtime and document that it must be detected; reserve `MEASURED` for what a probe against any
broker on the platform would confirm.

## How a plugin declares its level

Three lines, placed immediately after the skill's `# Title` heading and before its first `##`
section:

```
**Contract level:** <base|verified>
**Archetype:** <name>[, <name>...]
**Scope:** <single-broker|multi-broker-platform>
```

`<broker>` in the checklists above is the plugin directory name with a trailing `-trading`
removed: `ibkr-trading` becomes `ibkr`, `mt5-trading` becomes `mt5`. A plugin whose directory
name does not end in `-trading` keeps its name unchanged.

`**Archetype:**` names one archetype in the common case and a comma-separated list only when the
plugin genuinely covers more than one access path to its subject, per Level base item 4. Every
token in the list is validated against the same closed set; one bad token among several still
fails the plugin.

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

- **Whether the declared scope or archetype is the true one**, the question the axis exists to
  answer. A `multi-broker-platform` plugin could declare `single-broker` and clear every check
  in this list, because the linter validates that a token is well-formed and in the closed set,
  not that it describes the plugin's actual subject; the same is true of a declared archetype
  that does not match what the plugin's content actually does. Nothing mechanical substitutes
  for a reviewer who knows the broker or platform being described.
- Whether a fact tagged `MEASURED` genuinely has the provenance it claims (Level verified
  item 3), and on a `multi-broker-platform` plugin whether it genuinely names the broker it was
  measured against, or on a `single-broker` plugin whether it genuinely names the account
  entity when that matters: the linter reads no probe transcript and forms no opinion on
  whether a date, a shape variable, a broker or an entity are honest. It does not even search
  for the tag.
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
