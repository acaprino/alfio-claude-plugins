# trading-broker-connectivity: a shared vocabulary for broker plugins

Date: 2026-08-13
Plugins: `trading-broker-connectivity` (new), `ibkr-trading` (modified), `mt5-trading` (modified)
Status: design agreed in discussion, spec awaiting review. No implementation plan exists yet.

## Context

This marketplace has two broker plugins. `ibkr-trading` (2.8.0) carries 15 reference files, an
evidence ladder with provenance tags, probe tooling that provisions a disposable paper Gateway, and a
classified catalog of 458 published message codes. `mt5-trading` (1.1.5) carries 5 reference files
and none of those things.

They are structurally parallel by accident of authorship rather than by contract: each has a
`<broker>-architect` agent, a `<broker>-audit` command, and one skill with a `references/` directory.
Nothing in the repository states that shape as a requirement, so a third broker plugin will diverge in
a third direction, and the divergence will only be visible to whoever happens to read both.

The more expensive gap is a different one. Both plugins integrate against a **mandatory local
terminal**: IB Gateway for one, the MetaTrader terminal for the other. That single fact predicts a
large shared failure surface: what dies when the terminal dies, whether it can run headless, how
authentication survives without a human, session exclusivity when a second client logs in, scheduled
restart windows, and which order handling the terminal performs itself rather than relaying. Neither
plugin says which archetype it belongs to, so each rediscovered those problems in its own vocabulary,
and a reader of one gets no help from the other.

A ten-section Perplexity research program will supply landscape content that neither plugin can derive
on its own: protocols, local components, client libraries, limits, market data, simulation
environments. It has not been run yet. Everything in this design that does not depend on its output is
phase 1. Everything that does is phase 2, listed in Section 6.

## Two load-bearing distinctions

**Vendor-specific versus archetype-generic.** A rule is archetype-generic when it would still be true
for a different vendor of the same archetype. "The terminal simulates some order types locally, so
their behaviour changes if the terminal dies" is archetype-generic. "Stop orders on this venue are
held at the broker rather than at the exchange" is vendor-specific. The generic plugin owns the first
kind. Each broker plugin keeps the second, in full, including any local restatement of the generic
rule that it needs to stay readable on its own.

**User knowledge versus authoring rules.** Content a user loads while writing trading code belongs in
a plugin. Rules about how a plugin in this repository must be shaped belong in `.claude/skills/`,
where this repository already keeps `external-repo-intake`, `upstream-sync`, `custom-plugin-refresh`
and `downstream-exports`. The two halves were conceived together and are deliberately separated, so
that no user installs the repository's own maintenance rules along with a knowledge base.

## Section 1: what the plugin is

`plugins/trading-broker-connectivity/`, containing **one skill, no agents and no commands**.

Skill-only is a deliberate limit. A generic `broker-architect` agent would overlap `ibkr-architect`
and `mt5-architect` without adding a capability, and with two brokers in the repository there is no
sample large enough to abstract over. Add an agent when a third broker exists and the overlap is
measurable, not before.

`skills/trading-broker-connectivity/SKILL.md` plus four references:

| Reference | Contents |
|---|---|
| `access-archetypes.md` | The five archetypes below. Per archetype: where session state lives, what dies with what, what the developer is responsible for running, and the failure surface the archetype adds. Closes by placing IBKR and MT5, both `local-terminal`, which is why they share half their problems |
| `order-lifecycle-reference-model.md` | The FIX-derived state machine as shared vocabulary: states, legal transitions, the three layers that can accept or refuse (transport, broker validation, venue), the identifier taxonomy (client order ID, broker order ID, execution ID), and what a successful place call actually proves. Vendor-neutral, so that one plugin's term can be mapped onto another's |
| `session-and-recovery.md` | The problems every integration has regardless of vendor: session exclusivity, unattended authentication, reconnection and the connection that reports healthy while dead, reconciliation of ground truth after a gap, what must be persisted to recover |
| `evidence-and-probes.md` | The evidence ladder and provenance tags (below), the rule that a declared capability list is never sufficient on its own, how to design a probe that answers one question, and which classes of question a demo environment can and cannot settle |

### The five canonical archetype names

This is a closed vocabulary. The linter validates declarations against exactly these names.

| Name | Meaning |
|---|---|
| `direct-api` | A cloud API reached over the network. No vendor component runs on your machine |
| `local-terminal` | A vendor application must run locally, holds session state, and may perform order handling itself rather than relaying it |
| `vendor-gateway` | A vendor-operated gateway or protocol engine you connect to, usually behind onboarding or conformance certification |
| `bridge` | Third-party software sitting between a platform and a broker, operated by neither of them |
| `in-platform` | Code that runs inside the vendor's own application rather than beside it |

### The evidence ladder and provenance tags

Adopted from `ibkr-trading` unchanged in structure and generalized only in wording, replacing
IBKR-specific nouns with vendor-neutral ones. The direction matters and is a design decision rather
than an accident: the mature version already exists inside the vendor plugin, so the generic plugin
takes it rather than inventing a parallel scheme that would then have to be reconciled.

The ladder has **six ranks**, from a probe transcript of your own down to a search-engine or AI
summary, which is explicitly not evidence at any strength. The provenance tags are **three**:
`MEASURED`, `DOCUMENTED`, `ASSUMED`.

Two clauses inside it are the ones a later tidy-up would soften, and must not be:

- **Rank 4: a client library's source code is proof about the library, never about the broker.** It is
  a hypothesis about the broker, and must be labelled as which of the two it is claiming.
- **Silence is a finding.** "The documentation says nothing about this" is a recorded result with a
  date and a URL, not a failed search.

### The binding constraint on cross-references

`access-archetypes.md` names Interactive Brokers and MetaTrader 5 in order to place them in the map.
It must **never** instruct a reader to load `ibkr-trading` or `mt5-trading`.

A prose pointer is not a dependency; an instruction to load a skill is, under the dependency policy in
`CLAUDE.md`. Adding one would give the generic plugin two hard local dependencies, invert the intended
direction of the graph, and force anyone who wants only the map to install two vendor knowledge bases.
The boundary is: describe freely, never dispatch. This constraint is restated in the contract, because
it is exactly the kind of edge a later pass adds for convenience.

## Section 2: the contract and its two levels

`.claude/skills/broker-plugin-contract/`, loaded when authoring or reviewing a broker plugin and
shipped to nobody.

Throughout, `<broker>` is the plugin's directory name with the `-trading` suffix removed:
`ibkr-trading` yields `ibkr-architect`, `ibkr-audit`, `ibkr-verify`. The linter derives it the same
way, so the token is unambiguous rather than conventional.

**Level `base`**, required of every broker plugin:

- Structure: a `<broker>-architect` agent, a `<broker>-audit` command, one skill with a `references/`
  directory. All three registered in `marketplace.json`, not merely present on disk.
- The skill `description` carries both `TRIGGER WHEN` and `DO NOT TRIGGER WHEN`.
- The `SKILL.md` carries: a Quick start, a Key decision points table, a Symptoms to entry points
  table, and a Reference materials list with one descriptive line per file.
- The plugin declares its archetype using one of the five canonical names.
- The plugin uses the reference model's names for order states, and where the vendor uses different
  ones it maps them explicitly rather than silently substituting them.

**Level `verified`**, in addition to all of the above:

- A `<broker>-verify` command with probe scripts that measure against a demo or paper environment.
- A register of open questions, each paired with the experiment that would settle it.
- Every fact tagged `MEASURED` carries the date and the instrument that measured it.
- The probe tooling refuses production structurally rather than by configuration.

**Declaration.** One fixed line in the `SKILL.md` body: `**Contract level:** verified`. It is visible
to a human reading the file and readable by the linter. `ibkr-trading` declares `verified`,
`mt5-trading` declares `base`.

The two levels exist so that a plugin that has not yet earned verification is **visibly** at base
rather than silently non-compliant. A contract that every plugin fails on the day it is written stops
being enforced within a release or two.

## Section 3: the linter

`scripts/lint_broker_plugins.py`, stdlib only, runnable from the repository root, added to
`.github/workflows/consistency.yml` as the eighth Python check.

What it checks, all mechanically decidable:

1. **Which plugins are broker plugins.** A plugin is one if its `SKILL.md` carries the
   `**Contract level:**` line. Additionally, every plugin of category `algotrading` in
   `marketplace.json` other than `trading-broker-connectivity` itself must carry that line. This
   second half closes the only way a self-declaring contract can fail silently, which is by omission.
2. **Base level.** The `<broker>-architect` agent and `<broker>-audit` command exist on disk and are
   registered in `marketplace.json`. The four required `SKILL.md` sections exist: Quick start, Key
   decision points, Symptoms to entry points, Reference materials. Heading matching is
   **case-insensitive on the exact phrase**, because the two existing plugins already disagree on
   capitalisation and normalising that is cosmetics, not conformance. The `description` contains both
   `TRIGGER WHEN` and `DO NOT TRIGGER WHEN`. Every file in `references/` is listed in the `SKILL.md`
   and every listed entry exists on disk, checked in both directions. The declared archetype is one of
   the five canonical names.
3. **Verified level.** A plugin declaring `verified` has a `<broker>-verify` command present on disk
   **and** registered in `marketplace.json`, has probe scripts, and has the open-questions register
   section.

What it deliberately does not check, stated here so that a later pass does not read the gap as an
oversight: it cannot judge whether a fact genuinely has the provenance it claims, and it cannot judge
whether the shared vocabulary is used correctly inside prose. Those are held by the contract in prose
and by `lint_fact_anchors.py`, which compares duplicated values across files. A linter that pretends
to check semantics is worse than one that states its limits.

An `ALLOWLIST` with a stated reason per entry handles heuristic misreads, matching the other checks.

## Section 4: realigning the two existing plugins

**`ibkr-trading`, 2.8.0 to 2.9.0.** Adds the `**Contract level:** verified` line. Names its archetype
(`local-terminal`). Aligns the wording of its evidence ladder with the generic reference. The changes
are small by design: this plugin is the source of the doctrine, not its target, and a large diff here
would mean the generic plugin had invented something instead of extracting it.

**`mt5-trading`, 1.1.5 to 1.2.0.** Adds the `**Contract level:** base` line. Names its archetype
(`local-terminal`, the same as IBKR, which is the single most useful sentence this work adds to that
plugin). Adds the `DO NOT TRIGGER WHEN` clause its description currently lacks, an asymmetry given
that `ibkr-trading` already routes away to it. Adds the Symptoms to entry points table, currently
absent.

On separators: `mt5-trading` contains 61 occurrences of ` -- ` across 7 files. Most are list
separators rather than clauses bracketed between two dashes, so most are not violations of the
`CLAUDE.md` rule, which targets the bracketing construct. They are a style divergence from
`ibkr-trading`, which uses ` - ` in the same position. Genuine bracketed asides do exist among them.
The exact count is established during implementation rather than asserted here, and both the
divergence and the true violations are fixed in the same pass.

**Explicitly out of scope for phase 1:** retrofitting provenance tags onto every fact in
`mt5-trading`'s five references. That is the bulk of the work of promoting it to `verified`, and the
declared level already makes the gap visible instead of hiding it, which was the purpose of having two
levels.

## Section 5: marketplace, CI and export consequences

**Versions**, all in one commit or `check_version_bumps.py` fails the range:

| Target | From | To |
|---|---|---|
| `trading-broker-connectivity` | new | 1.0.0 |
| `ibkr-trading` | 2.8.0 | 2.9.0 |
| `mt5-trading` | 1.1.5 | 1.2.0 |
| `metadata.version` | 22.6.0 | 23.0.0 |

A new plugin is a major bump, following marketplace 22.0.0 for `repo-hygiene`.

**Registration.** The new skill is declared in `marketplace.json`, or `lint_plugin_registration.py`
reports it present on disk and absent from the registry. That check exists because a file that is not
registered does not exist at runtime.

**Fact anchors.** Add anchors covering the shared vocabulary: the five archetype names and the three
provenance tags. Each is stated in the generic plugin and echoed in both broker plugins, which is the
deliberate redundancy `lint_fact_anchors.py` was written for. An anchor makes a later change to the
vocabulary a deliberate edit across all copies rather than a drift between them.

**Dependencies.** None are added, by construction. `trading-broker-connectivity` is a leaf, and
neither broker plugin gains a declaration. Pass 8 of the dependency linter is not engaged because
there is no new hard dependency to justify.

**Documentation.** `docs/plugins/trading-broker-connectivity.md`, since every plugin currently has a
page.

**Export.** The new plugin produces a new bundle under `exports/vscode/`. The mechanical half is
computed by the mirror workflow; the adapted half, which includes the `SKILL.md`, is hand-ported in
the same commit with the `downstream-exports` skill loaded. The `exports/vscode/CHANGELOG.md` section
is written in the same commit that moves the marketplace version, per the release-notes guard.

**`CLAUDE.md`.** The CI section moves from seven Python checks to eight. The repo-workflows table gains
a fifth row for `broker-plugin-contract`. The contract and its two levels are recorded as standing
policy with the reasoning, including the describe-but-never-dispatch constraint from Section 1.

**Staging.** Explicit paths only. Never `git add -A`, which has already published a half-state in this
repository while another session held uncommitted work.

## Section 6: phase 2, after the research returns

Additive to the same plugin, no restructuring: `protocols.md`, `local-components.md`,
`client-libraries.md`, `limits-and-pacing.md`, `market-data-and-symbology.md`,
`simulation-environments.md`.

The research program lives in the session scratchpad as a single seed prompt covering ten sections.
Its section 10 asks explicitly for IBKR and MT5 to be placed inside every dimension of the map, with
archetype-generic behaviour separated from vendor-specific behaviour. That separation is the input
phase 2 needs, and it is also a review pass over phase 1's archetype content.

Phase 2 carries one risk worth naming now: the research may show that five archetypes is the wrong
cut. Because the names are anchored, changing them is a deliberate edit across every copy rather than
a silent divergence, which is the outcome the anchor exists to produce.

## Alternatives considered and rejected

- **One consolidated `trading` plugin** absorbing the map plus both brokers as skills. Rejected: it
  breaks two installed plugins and puts unrelated vendors in one namespace.
- **Lifting all archetype-generic content out of the broker plugins**, leaving them as thin deltas.
  Rejected: it breaks the property that each artifact is readable on its own, which is the reason the
  fact-anchor doctrine tolerates duplication in the first place, and it makes every answer require two
  reads.
- **A hard dependency from the broker plugins onto the generic one**, giving the vocabulary a single
  copy. Rejected: it taxes every IBKR user with a map they rarely need, for a drift problem the anchor
  linter already solves.
- **Waiting for the research before building anything.** Rejected: the standardization work depends on
  no research, and blocking it behind a report is how it does not happen.
- **Writing the landscape chapters now from existing knowledge and verifying later.** Rejected: it
  puts unsourced claims into a knowledge plugin, which is the exact mechanism by which a wrong rate
  limit survived for months in `ibkr-trading`.
- **A scaffold generator for new broker plugins.** Deferred, not rejected. A generator built on a
  sample of two encodes the accidents of two. It pays off at the third broker.
- **Contract in prose with no linter.** Rejected: an unenforced convention in this repository has a
  measured tendency to stop being true.

## Open questions

1. **When does `mt5-trading` get its provenance retrofit and a `verified` level?** It needs an MT5
   terminal and a demo account on this machine, which is not established. Tracked as its own release,
   not blocked by this one.
2. **How many of the 61 ` -- ` occurrences in `mt5-trading` are genuine bracketed asides?** Settled by
   reading them during implementation. It changes the size of the diff, not the design.
3. **Does the linter's archetype check belong in `lint_broker_plugins.py` or in
   `lint_fact_anchors.py`?** Both could hold it. Current answer: the linter validates that a
   declaration is one of the five names, the anchors validate that the five names say the same thing
   everywhere. They check different failures and both stay.
