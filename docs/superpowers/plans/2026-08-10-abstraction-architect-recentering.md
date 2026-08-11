# abstraction-architect Recentering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recenter `abstraction-architect` from a two-category auditor of missed unification versus wrong abstraction into a reducer of structural entropy, so that duplicated domain knowledge, competing sources of truth, redundant representations and duplicated state become findable instead of falling out of the report.

**Architecture:** One plugin, rewritten from the bottom up. Seven dimensions over two evidence tracks, four lenses applied as finding fields, a persisted machine-readable concept index that seeds discovery without ever proving a finding, and a compact orchestrator agent whose content lives in a ten-file reference library. One deterministic Python script owns freshness and delta partitioning because a language model does that badly. Four touch points outside the plugin, all additive.

**Tech Stack:** Static markdown plugin content, one stdlib-only Python script, stdlib `unittest` for that script. No build step, no runtime framework. Verification for markdown is the four existing CI linters plus grep assertions on shipped content.

**Source spec:** `docs/superpowers/specs/2026-08-10-abstraction-architect-recentering-design.md`

## Global Constraints

Every task's requirements implicitly include this section.

- **No dash-aside construct anywhere**, in content, code comments or commit messages. This targets the rhetorical pattern of bracketing a clause between dashes in any form: em dash, double hyphen, spaced hyphen. Substituting `--` for an em dash is not the fix. Rewrite into separate sentences, parentheses, or colons. Hyphenated compounds and CLI flags are unrelated and fine.
- **Stage explicit paths, never `git add -A`.** Other sessions run this repository concurrently. Diff `marketplace.json` and `exports/vscode/package.json` before staging.
- **Bundled paths**: any self-reference to a plugin file uses `${CLAUDE_PLUGIN_ROOT}/...` or a skill-relative `references/...` path inside that same skill. No plugin reaches into another plugin's files by path. `scripts/lint_bundled_paths.py` enforces this and scans fenced code blocks.
- **Agent frontmatter**: `model: inherit`, `color: orange` (unchanged), `name: abstraction-architect` matching the filename, long `description` in YAML `>` form with `TRIGGER WHEN` and `DO NOT TRIGGER WHEN` clauses.
- **Version bumps land in Task 15 only.** `scripts/check_version_bumps.py:71` diffs `base..head`, so one bump anywhere in the pushed range covers every commit in it. Do not bump per task.
- **Push once, at the end of Task 15.** Not before.
- **`codebase-xray` is not modified by this plan.** The concept census lives in this plugin. Promoting it to a shared xray capability is deferred until two or three consumers need it.
- **The agent stays an orchestrator.** Target under 300 lines. If a task would push catalog content into `agents/abstraction-architect.md`, it belongs in a reference instead.

### Verbatim rules and where each one lands

Seven sentences must appear literally in shipped content. Task 15 greps for all seven. Do not paraphrase them.

| Rule | Lands in | Task |
|---|---|---|
| `Can these representations legitimately disagree?` | `references/evidence-tracks.md` | 1 |
| `report the deepest architectural reason` | `references/dimensions.md` | 2 |
| `Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding.` | `references/unification-patterns.md` and `references/anti-patterns.md` | 8, 9 |
| `Structural simplification is the desired outcome of the audit, not a finding category.` | `references/scope-boundaries.md` | 3 |
| `precision over recall` governs what is **reported**, not what is **searched** | `references/concept-census.md` and `agents/abstraction-architect.md` | 4, 11 |
| `Index entries nominate search targets; current source code proves findings.` | `references/concept-index-protocol.md` and `agents/abstraction-architect.md` | 5, 11 |
| `The script never discovers concepts.` | `references/concept-index-protocol.md` | 5 |

### Canonical artifact paths

Every task that writes or reads these uses exactly these paths.

| Artifact | Produced by | Consumed by | Mutability |
|---|---|---|---|
| `.abstraction-architect/concept-index.json` | global mode only | global and diff mode | rewritten by global mode; **diff mode never writes it in 2.0** |
| `.abstraction-architect/findings.md` | global mode | human | overwritten per run |
| `.abstraction-architect/findings-diff.md` | diff mode standalone | human | overwritten per run |
| `.team-review/findings-abstraction.md` | diff mode under team-review | consolidation | path supplied by caller |

### Canonical names

Dimensions are `D1` to `D7`, lenses `L1` to `L4`, form gates `A1` to `A5`, knowledge gates `K1` to `K6`, unification patterns `P1` to `P18`, anti-patterns `A1.` to `A12.` inside `anti-patterns.md` only.

**The `A` collision is deliberate and must be disambiguated in prose.** Form gates are written `gate A1` through `gate A5`. Anti-patterns keep their existing `A1.` through `A12.` ids inside `anti-patterns.md` and are cited from elsewhere as `anti-pattern A1`. Never write a bare `A1`.

Script output keys, used verbatim by the agent: `freshness_state`, `reason`, `index_baseline`, `repository_state`, `review_delta`, `changed_files`, `dirty_indexed_concepts`, `unmapped_changed_files`. Freshness values: `fresh`, `delta-stale`, `unusable`.

Finding fields: `Evidence track` with values `FORM` or `KNOWLEDGE`, `Pattern` with `uncatalogued` as a permitted value, `Occurrences`, `Semantic identity`, `Must remain consistent`, `Bounded-context exception`, `Canonical owner`, `Index-seeded`, `Rule of Three`.

---

### Task 1: Evidence tracks and gates

The gates land first because Task 2 cites every one of them by id.

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/evidence-tracks.md`

**Interfaces:**
- Produces: gate ids `A1` to `A5` and `K1` to `K6`, cited by Tasks 2, 9, 11. Section headings `## Track A: form` and `## Track B: knowledge`, cited by Task 2. The discriminating question, cited by Tasks 2 and 14.

- [ ] **Step 1: Create the file with the governing rule**

Create `plugins/abstraction-architect/skills/abstraction-architect/references/evidence-tracks.md`:

````markdown
# Evidence Tracks

Two kinds of evidence support a structural finding, and they are not interchangeable. Getting the wrong one produces either a noisy report or an empty one.

**The track determines the nature of the evidence. The dimension determines the gate.**

Track membership does not by itself impose a count. This is the single most common misreading, and it is worth stating twice: being on track A does not mean "three or more occurrences". Only D5 uses the Rule of Three as a strict gate.

| Track | Question it answers | Failure it guards against |
|---|---|---|
| A, form | Does the same *mechanism* recur, and would unifying it pay? | Extracting a shape from a sample of two and getting the wrong abstraction |
| B, knowledge | Does the same *fact* have more than one authoritative representation? | Two owners of one truth drifting apart, where waiting for a third is meaningless |

## Why the Rule of Three does not cover both

The Rule of Three protects against one specific risk: extracting a shape too early, with a sample of two, and producing an abstraction whose shape is anchored to a coincidence. It says nothing about the opposite risk, which is knowledge with two authoritative representations.

`references/theory.md` states the underlying reason: DRY targets duplicated *knowledge*, not duplicated lines. Two competing authorities over the same fact is already the defect. There is no third occurrence to wait for, and waiting produces exactly the drift the principle exists to prevent.

The Rule of Three therefore returns to its original meaning here: a gate that justifies **creating a new unification**, not a universal filter for the form family.

## Track A: form

Applies to D5 missed unification, D6 prior art available, D7 abstraction fitness.

```
A1  Same structural responsibility?
A2  Same lifecycle and boundary?
A3  Occurrences per the dimension's own rule
    D5: three or more independent occurrences (Rule of Three)
    D6: one canonical implementation plus at least one reimplementation or bypass
    D7: no count at all; friction inside a single abstraction is the evidence
A4  Would one shared abstraction reduce change cost?
A5  Is the divergence unlikely to be intentional?
```

Gate A3 is where the per-dimension rule enters. A D7 candidate that fails A3 because it has only one occurrence has been judged against the wrong rule: a wrong abstraction is a single object, and counting copies of it is a category error.

L3, bounded context, is an important lens on track A but not an absolute gate. Two contextually separate implementations may still legitimately share an infrastructural mechanism such as a retry policy or a logging facade.

## Track B: knowledge

Applies to D1 duplicated domain knowledge, D2 competing sources of truth, D3 redundant representation, D4 duplicated or derivable state.

Two representations are sufficient evidence. In exchange, the semantic proof is much stricter than a count.

```
K1  Same semantic fact?
K2  Same domain meaning?
K3  Same lifecycle?
K4  Same authority scope?
K5  If the fact changes, are both expected to remain consistent?
K6  Is there no legitimate bounded-context reason for divergence?
```

K6 is a **hard gate** on this track. A candidate that cannot demonstrate K6 is not reported, and a candidate whose context membership could not be determined is reported with `Bounded-context exception: unverified` and downgraded, never promoted.

Failing to demonstrate any of K1 through K6 means no finding. Silence is the correct output when the proof is not there.

## The discriminating question

Every track B candidate resolves to one question, and it is the fastest route to the answer:

> **Can these representations legitimately disagree?**

If yes, this is not duplicated knowledge, whatever the surface similarity. If no, and they must stay consistent, two representations are enough.

Worked contrast:

```
Billing.REFUND_DAYS = 30            Shipping.Status: PENDING/COMPLETE/FAILED
Support.refundAllowed = age <= 30   Payment.Status:  PENDING/COMPLETE/FAILED

Can they legitimately disagree?     Can they legitimately disagree?
No. One policy, two owners.         Yes. Same shape, different knowledge.
FINDING (D1 or D2).                 NO FINDING.
```

The left column has no textual similarity and is a finding. The right column is textually identical and is not. A detector that matches on shape gets both backwards, which is precisely why this file exists.

## What the report must show

Every finding carries the track it was judged on and the gate results, so a reader can see why it was admitted:

```
Evidence track: KNOWLEDGE            Evidence track: FORM
Semantic identity: proven            Occurrences: 4
Occurrences: 2                       Independent implementations: yes
Must remain consistent: yes          Shared lifecycle: yes
Bounded-context exception: none      Rule of Three: satisfied
Canonical owner: ambiguous           Index-seeded: no
```
````

- [ ] **Step 2: Verify the verbatim rule landed**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
grep -c "Can these representations legitimately disagree?" \
  plugins/abstraction-architect/skills/abstraction-architect/references/evidence-tracks.md
```

Expected: `1`

- [ ] **Step 3: Verify no dash-aside construct**

Run:

```bash
grep -nE '—|[a-z] -- [a-z]| - [a-z]' \
  plugins/abstraction-architect/skills/abstraction-architect/references/evidence-tracks.md
```

Expected: no output. Any hit is a violation of the global constraint and must be rewritten before committing.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/evidence-tracks.md
git commit -m "Add the two evidence tracks and their gates

Track determines the nature of the evidence, dimension determines the
gate. The Rule of Three returns to its original meaning as the gate that
justifies a new unification, instead of acting as a universal filter for
the form family, where it wrongly demands three copies of a single wrong
abstraction."
```

---

### Task 2: The seven dimensions, four lenses, and classification precedence

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/dimensions.md`

**Interfaces:**
- Consumes: gate ids `A1` to `A5` and `K1` to `K6` from Task 1.
- Produces: dimension ids `D1` to `D7` and lens ids `L1` to `L4`, cited by Tasks 3, 4, 5, 8, 10, 11, 12, 14. The heading `## Single primary classification`, cited by Task 11.

- [ ] **Step 1: Create the file**

Create `plugins/abstraction-architect/skills/abstraction-architect/references/dimensions.md`:

````markdown
# Dimensions and Lenses

A **dimension** is a category a finding can belong to. Each one has its own proof rule. A **lens** is a criterion applied to every candidate of every dimension, reported as a field of the finding. A lens never becomes a category of its own.

Load `references/evidence-tracks.md` for the gates cited below.

## The seven dimensions

| | Dimension | Track | Proof rule |
|---|---|---|---|
| D1 | Duplicated domain knowledge | B | same policy, formula or invariant; two or more representations; they must stay consistent |
| D2 | Competing sources of truth | B | same fact; two or more authoritative writers or definitions; canonical owner absent or ambiguous |
| D3 | Redundant representation | B | same concept; parallel representations; real mapping or synchronization cost |
| D4 | Duplicated or derivable state | B | derivable but maintained separately, plus sync, invalidation or repair code |
| D5 | Missed unification | A | mechanism independently repeated three or more times; Rule of Three |
| D6 | Prior art available | A | a clearly canonical implementation exists and something else reimplements or bypasses it |
| D7 | Abstraction fitness | A | proven internal friction: flags, per-caller exceptions, caller bypass, leakage |

### D1. Duplicated domain knowledge

The same rule expressed more than once, usually without textual similarity.

```
OrderService:        if total > 1000 -> requiresApproval
CheckoutController:  if cartValue > 1000 -> managerApproval
InvoiceWorkflow:     highValue = amount > 1000
```

**Proof:** same concept, plus same decision, invariant or formula, plus different implementation sites. A grep finds candidates. The finding exists only after reading each context and demonstrating that they encode the same policy. Gates K1 to K6 apply.

### D2. Competing sources of truth

The same fact has more than one authority. This is more serious than duplication, and the question is not "are these similar" but "which one actually decides".

```
config/defaults.py     -> refund_days = 30
database.settings         refund_window
RefundPolicy.DEFAULT_DAYS = 30
```

**Proof:** same fact, plus two or more independent authoritative writers or definitions, plus no single canonical owner. Two is sufficient.

### D3. Redundant representation

The same concept modelled in parallel, with a real cost to keep the models aligned.

```
UserStatus enum   <->   AccountState enum   <->   CRMStatus mapping
```

Four types named after one concept are **not** automatically a finding. `CustomerDTO`, `CustomerEntity`, `CustomerResponse` and `CustomerEvent` may have entirely different boundaries and lifecycles, and usually do.

**Proof:** same fields, plus same semantics, plus same lifecycle, plus a continuous one-to-one mapping, plus no boundary-specific reason, plus changes that routinely propagate across all of them. Anything less is a legitimate boundary and reporting it is a false positive.

### D4. Duplicated or derivable state

Information that could be derived is instead stored, and the codebase carries the burden of keeping the copies aligned.

`cart.items` and `cart.total` is not by itself a defect. Materializing a total is often correct.

**Proof:** derivable, plus persisted separately, plus **evidence of the synchronization burden**:

```
recalculate_total()   update_total()   sync_total()   repair_cart_total()
```

plus more than one writer. The presence of repair code is the strongest signal, because repair code exists only where drift has already happened. A field being derivable is not evidence on its own.

### D5. Missed unification

A mechanism recurs and the codebase is asking for an abstraction that does not exist yet.

**Proof:** three or more independent occurrences encoding the same concern, gate A3 in its Rule of Three form. Consult `references/unification-patterns.md` for canonical shapes, remembering that the catalog is not an admission gate.

### D6. Prior art available

The abstraction already exists and part of the codebase does not use it.

```
CanonicalMoneyParser.parse()        exists, is clearly the owner
parse_money_again(...)              reimplements it elsewhere
```

**Proof:** one canonical implementation plus at least one reimplementation or bypass. No third occurrence is required, and demanding one is the misreading gate A3 exists to prevent. The strong evidence is not frequency, it is that an owner already exists.

D5 and D6 are adjacent and distinct, and the distinction changes the remediation:

```
D5 = the codebase is asking for an abstraction.        Remediation: design or consolidate.
D6 = the abstraction exists and is being bypassed.     Remediation: reuse, migrate to canonical.
```

### D7. Abstraction fitness

An existing layer is fighting its callers.

**Proof:** friction inside one abstraction. Flags accumulating on the signature, per-caller exceptions, callers bypassing it, vendor or implementation detail leaking through the public surface, parallel concrete implementations that route around it. No count of copies is involved. Consult `references/anti-patterns.md`.

**Boundary with `senior-review:code-auditor`.** A god function or a one-implementation interface that is fully visible inside the file under review belongs to that agent's Abstraction Inspector. D7 is the cross-file case: friction proven by external callers bypassing the layer, or by exceptions added for callers that live elsewhere. Do not re-flag what one file shows on its own.

## The four lenses

A lens is applied to every candidate and reported as a field. It never opens a finding by itself.

**L1 Change amplification.** If this concept changes, how many places must change together? This is the primary yardstick, and `references/theory.md` develops it as the single rule of thumb. Reported as the count and the list.

**L2 Indirection cost, Locality of Behaviour.** Would consolidating actually reduce cognitive cost, or only add another hop? This lens exists to stop the plugin proposing false remedies. A suggested direction that fails L2 is reported as a finding with an explicit note that the obvious unification is not the answer.

**L3 Bounded context.** A hard gate on track B, per gate K6. An important lens on track A but not an absolute gate, because two contextually separate call sites may still legitimately share an infrastructural mechanism.

**L4 Option price, Tidy First.** Does the benefit justify the abstraction today, or is deliberate duplication cheaper right now? This lens is what keeps the audit from being refactor-happy. A finding whose L4 verdict is "duplication is currently cheaper" is still reported, with that verdict stated, because the user may be waiting for a third occurrence deliberately.

## Occurrences are evidence, never severity

There is no mapping of the form two equals Low, three equals Medium, four equals High. Two independent authoritative permission policies can be High on two occurrences. Four duplicated formatting constants can be Low on four.

Severity follows consequence, calibrated in `references/decision-frame.md`. Occurrence count is reported as evidence strength and nothing else.

## Single primary classification

One defect gets one primary dimension.

A refund window duplicated in three places, one of which looks canonical, could be read simultaneously as D1, D2, D5 and D6. Four findings for one defect is a report bug, and it is the failure mode that makes conventional DRY tooling tiring to read.

Orienting precedence, applied as a principle and not as a rigid universal ordering:

```
D2 competing authority
  D4 duplicated state
    D3 redundant representation
      D1 duplicated knowledge
        D6 existing prior art
          D5 missed unification
            D7 abstraction fitness
```

The rule: **report the deepest architectural reason**, and record the others as supporting evidence or lens values rather than duplicate findings.

Worked example. Three implementations of a refund policy exist because three modules each consider themselves authoritative.

- Classified as D5, the finding says "we could extract a helper". True and shallow.
- Classified as D2, the finding says "nobody owns this policy". True and actionable.

D2 is deeper on the precedence, so D2 is the finding and the D5 observation becomes a line of supporting evidence. Extracting a helper without settling ownership would produce a fourth authority.

## The catalogs are not admission gates

The original defect this plugin was rebuilt to fix was not that its twelve unification patterns were infrastructural. It was that a catalog consulted as a matching step silently became the boundary of what could be found. Adding domain patterns fixes the coverage and reproduces the mechanism at a larger size unless the mechanism itself is addressed.

A candidate that passes its dimension's gate is a finding whether or not it matches a catalogued pattern. When it matches, cite the pattern. When it does not, name the concern in your own words and set the finding's `Pattern` field to `uncatalogued`.
````

- [ ] **Step 2: Verify the verbatim rule and the dimension ids**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
F=plugins/abstraction-architect/skills/abstraction-architect/references/dimensions.md
grep -c "report the deepest architectural reason" "$F"
for d in D1 D2 D3 D4 D5 D6 D7 L1 L2 L3 L4; do printf "%s=%s " "$d" "$(grep -c "\b$d\b" "$F")"; done; echo
```

Expected: first command prints `1`. Second prints a non-zero count for every id.

- [ ] **Step 3: Verify no dash-aside construct**

Run:

```bash
grep -nE '—|[a-z] -- [a-z]' plugins/abstraction-architect/skills/abstraction-architect/references/dimensions.md
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/dimensions.md
git commit -m "Add the seven dimensions, four lenses and classification precedence

Separates dimensions (categories with proof rules) from lenses (criteria
applied to every candidate and reported as fields), so that change
amplification and indirection cost stop being candidate categories that
would duplicate every other finding from a second angle.

Single primary classification stops one defect being reported four
times, and its worked example shows why the deepest reason is the
actionable one: three refund implementations reported as D5 says extract
a helper, reported as D2 says nobody owns the policy."
```

---

### Task 3: Scope boundaries and non-goals

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/scope-boundaries.md`

**Interfaces:**
- Consumes: dimension ids from Task 2.
- Produces: the heading `## Excluded dimensions and their owners`, cited by Tasks 10 and 11.

- [ ] **Step 1: Create the file**

Create `plugins/abstraction-architect/skills/abstraction-architect/references/scope-boundaries.md`:

````markdown
# Scope Boundaries and Non-Goals

This file exists so that exclusions are written down rather than merely omitted. An omitted exclusion gets re-added by a well-meaning future pass; a written one has to be argued with.

## The goal is not a finding category

> **Structural simplification is the desired outcome of the audit, not a finding category.**

Without this rule, every D1 to D7 finding can be restated as a "structural simplification opportunity" that carries no new information, and the report doubles in length while saying the same things twice.

## Excluded dimensions and their owners

Five structural concerns are deliberately outside this plugin. Each has an owner that already covers it, and each has a permitted role here as supporting evidence.

| Excluded | Owner | Permitted role here |
|---|---|---|
| Dependency structure: cycles, missed inversions, depth | `senior-review:code-auditor` for coupling, `senior-review:chicken-egg-detector` for initialization cycles | A dependency may be cited as supporting evidence for D1 to D7. "This dependency is wrong" is never an autonomous finding here. |
| Responsibility cohesion inside a module | `senior-review:code-auditor` | Two modules owning the same policy is evidence of D2. "This class has too many responsibilities" is not ours. |
| API surface size and contract drift | `senior-review:api-contract-auditor`, `senior-review:cleanup-auditor` D4 for barrel and unused-export bloat | May appear incidentally inside a D7 remediation. Never a category. |
| Indirection cost | absorbed as lens L2 | Contributes to D7. "Too much indirection" never opens a finding alone. |
| Structural simplification | none, it is the goal | See the rule above. |

## Dedup with `senior-review:code-auditor`

Both agents run as dimensions of the same review, so the boundary is load-bearing rather than theoretical.

- **Inside one file** belongs to `code-auditor`: god functions, stringly-typed code, a leaky signature, an interface with one implementation, all judged on what the file under review shows on its own.
- **Across files** belongs here: this already exists elsewhere, this is the occurrence that justifies unifying, this fact has two owners, this layer is bypassed by callers that live somewhere else.

Do not re-flag a smell that is fully visible inside one file without reference to another site.

## Other neighbours

- **Dead code, unused exports, orphan assets, VCS hygiene**: `senior-review:cleanup-auditor`. A duplicated representation that is simply unused is a cleanup finding, not a D3.
- **Style and readability**: `clean-code:clean-code`. Renaming for clarity is not a structural finding.
- **Contract violations against a documented invariant**: `senior-review:logic-integrity-auditor`. That agent hunts code that *breaks* a documented rule. This one hunts a rule that has *two authoritative statements*. The two are complementary and neither subsumes the other.
- **Persistence semantics**: `senior-review:data-integrity-auditor`. A derivable column with no constraint backing it is theirs. The same column with four repair functions around it is D4 here. When both apply, report D4 and note the overlap in Cross-Reviewer Notes.

## This plugin does not

- Produce a refactoring plan. `Suggested direction` names the target layer or the move in one sentence.
- Edit any file other than its own report and, in global mode, its own concept index.
- Score the codebase. `senior-review:code-auditor` owns the Code Quality Score.
````

- [ ] **Step 2: Verify the verbatim rule**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
grep -c "Structural simplification is the desired outcome of the audit, not a finding category." \
  plugins/abstraction-architect/skills/abstraction-architect/references/scope-boundaries.md
```

Expected: `1`

- [ ] **Step 3: Verify the dependency-graph linter still passes**

This file names agents in other plugins, which the linter reads as cross-plugin references.

Run:

```bash
python scripts/lint_dependency_graph.py
```

Expected: exit 0. If it reports an undeclared reference, the fix is to confirm that `senior-review` names in prose are not spawn instructions. This file only names owners and never says to spawn them, so a hit means the linter needs an `ALLOWLIST` entry with a reason, not a dependency declaration. Do not add a dependency on `senior-review`, which would close the cycle that marketplace 16.0.0 opened.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/scope-boundaries.md
git commit -m "Write down the five excluded dimensions and their owners

Exclusions that are merely omitted get re-added by the next pass. Each
of the five names the agent that already owns it and the role it may
still play here as supporting evidence, so that a dependency cycle is
evidence for D2 without becoming an autonomous dependency finding."
```

---

### Task 4: The concept census method

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/concept-census.md`

**Interfaces:**
- Consumes: dimension ids from Task 2.
- Produces: the phase names `seed map`, `concept extraction`, `discovery`, cited by Task 11. The `Concept Evidence Index` structure, consumed by Task 5.

- [ ] **Step 1: Create the file**

Create `plugins/abstraction-architect/skills/abstraction-architect/references/concept-census.md`:

````markdown
# The Concept Census

The census is what makes D1 through D4 possible. Without it the agent can only compare shapes, and comparing shapes finds the wrong things: identical status enums in two bounded contexts look like a defect, and one policy written three different ways looks like nothing at all.

## The rule that governs the whole method

> `precision over recall` governs what is **reported**, not what is **searched**.

Discovery is deliberately liberal. Promotion to a finding is deliberately strict. Conflating the two is how an auditor ends up not searching at all, which is the defect this method replaces.

```
DISCOVERY                    liberal Glob and Grep, many candidates, cheap
      |
      v
CONTEXT VERIFICATION         read the definitions, the writers, the consumers
      |
      v
SEMANTIC TEST                same concept? same authority? same lifecycle? same boundary?
      |
      v
FINDING                      only here does precision apply
```

## Phase 1: the seed map

Read `.deep-dive/` and extract the territory: modules, responsibilities, entities and domain concepts, services, persistence, configuration, boundaries, principal flows, public interfaces.

The census is seeded by this map on purpose. Beginning by sweeping eighty thousand files at random produces order-dependent coverage and burns the budget before reaching the interesting part.

**The seed map's completeness is not a premise.** Extraction starts from it and is not limited by it. A module X-ray did not surface is a gap in the census, and the census may add concepts the map never named. There is no rule of the form "do not search where the map says nothing".

## Phase 2: concept extraction

From the seed map, derive two kinds of concept.

**Entity concepts**, the domain nouns:

```
Customer  Order  Payment  Subscription  Permission  Refund  Price  Status  Tenant  Feature
```

**Behavioural concepts**, which are the ones a noun-only census misses and which carry most of the D1 findings:

```
eligibility  approval  normalization  calculation  expiration
validation   mapping   defaulting     derivation
```

A policy such as "orders above a threshold need approval" is an *approval* concept. It has no single noun and no single home, which is exactly why it ends up written three times.

## Phase 3: discovery

For each concept, search for its **representations**, not for its name. Four search families, run together, because each alone produces false negatives.

**By name and near-synonym.** For a `subscription status` concept:

```
SubscriptionStatus   subscription_state   plan_status
isActive   enabled   expiresAt > now   ACTIVE = "active"
```

**By literal.** Thresholds, magic numbers, regexes, endpoint paths, env var names, error strings, header names, date windows. Copy-paste survives renaming; literals do not change. This is the family that finds `30` in three files and `1000` in three others.

**By call.** The same external call with the same parameters: same SDK method, same table, same queue, same config key.

**By shape of decision.** Predicates over the same field, comparisons against the same bound, branches keyed on the same enum. This family finds the policy that was reimplemented rather than copied.

Record every hit. A hit is a candidate, never a finding.

## The Concept Evidence Index

Discovery produces one entry per concept. The persisted form is defined in `references/concept-index-protocol.md`; this is the shape to think in:

```
Concept: Refund eligibility
Kind: policy

Representations:
  RefundPolicy.can_refund              domain/refund_policy.py   candidate_owner
  SupportRefundService.is_eligible     support/refunds.py        implementation
  REFUND_WINDOW_DAYS                   config/refunds.py         parameter
  Order.refundable_until               domain/order.py           derived_field

Writers:    RefundPolicy, AdminRefundSettings
Consumers:  checkout, support-api
Canonical owner:  ambiguous

Evidence:
  same 30-day policy confirmed in three contexts
  support implementation bypasses RefundPolicy
```

With this in hand the agent can reason about ownership. Without it, the best available move is "grep magic numbers, found 30 three times, report it", which is the behaviour this method exists to replace.

## Phase 4: hypothesis testing

For each concept with more than one representation, assign the track, run the dimension gate from `references/evidence-tracks.md`, apply the four lenses from `references/dimensions.md`, and classify to a single primary dimension.

A concept with one representation is not a finding. It is the healthy case, and the index records it so the next run can tell when a second appears.
````

- [ ] **Step 2: Verify the verbatim rule**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
grep -c "governs what is \*\*reported\*\*, not what is \*\*searched\*\*" \
  plugins/abstraction-architect/skills/abstraction-architect/references/concept-census.md
```

Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/concept-census.md
git commit -m "Add the concept census method

Four search families instead of one, and behavioural concepts alongside
entity nouns, because a noun-only census misses approval and eligibility
policies, which are where duplicated knowledge actually accumulates.

Separates high-recall discovery from high-precision reporting, which is
what lets the agent search liberally without the report degrading."
```

---

### Task 5: The concept index protocol

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/concept-index-protocol.md`

**Interfaces:**
- Consumes: the Concept Evidence Index shape from Task 4.
- Produces: the JSON schema and the script CLI contract, both implemented by Task 6 and invoked by Task 11. Freshness state names `fresh`, `delta-stale`, `unusable`.

- [ ] **Step 1: Create the file**

Create `plugins/abstraction-architect/skills/abstraction-architect/references/concept-index-protocol.md`:

````markdown
# Concept Index Protocol

The concept index is the bridge between the two modes. Global mode builds it. Diff mode reads it and answers "does this change introduce a second authority" by consulting an index instead of re-censusing the repository on every review.

## Epistemic status

> **Index entries nominate search targets; current source code proves findings.**

The index is a discovery accelerator. It is never a cache of truth, and it is never the sole evidence for a finding. Before promoting any D1 to D4 finding, re-read the involved representations against current source.

Three obligations follow, and they exist because a shared artifact that corroborates itself is how a pipeline produces confident wrong answers:

- **Duty of autonomous rediscovery.** Search the changed area whether or not the index covers it. `unmapped_changed_files` from the script is the explicit worklist for this.
- **Contradiction is reportable.** When revalidation shows the index is wrong, a recorded canonical owner that no longer holds, a representation that is gone, a `settled` owner that is in fact ambiguous, report it in Gaps and correct the index on the next global write. Never silently prefer one source.
- **No metric rewards agreement.** No score, coverage percentage or quality gate may reward index utilisation or citation. Coverage is reported as counts of what was examined, never as a ratio of agreement.

## Who writes it

**Global mode writes `.abstraction-architect/concept-index.json`. Diff mode never writes it in 2.0.**

A diff run sees one change against a partial revalidation. Letting it write would let a narrow view overwrite a broad one and would make the index's provenance depend on whichever review happened to run last. Diff mode reports newly discovered concepts and contradictions in Gaps, and the next global audit consolidates them.

## Schema

```json
{
  "schema_version": 1,
  "generated_from_commit": "abc123...",
  "generated_from_tree": "9f48...",
  "generated_at": "2026-08-10T12:00:00Z",
  "scope": ".",
  "concepts": [
    {
      "concept": "Refund eligibility",
      "kind": "policy",
      "representations": [
        {"symbol": "RefundPolicy.can_refund", "file": "domain/refund_policy.py", "role": "candidate_owner"},
        {"symbol": "SupportRefundService.is_eligible", "file": "support/refunds.py", "role": "implementation"},
        {"symbol": "REFUND_WINDOW_DAYS", "file": "config/refunds.py", "role": "parameter"}
      ],
      "writers": ["RefundPolicy", "AdminRefundSettings"],
      "consumers": ["checkout", "support-api"],
      "canonical_owner": {"status": "ambiguous"},
      "evidence": [
        "same 30-day policy confirmed in three contexts",
        "support implementation bypasses RefundPolicy"
      ]
    }
  ]
}
```

Field notes:

- `kind` is free text describing the concept category, for example `policy`, `entity`, `state`, `vocabulary`, `parameter`.
- `role` on a representation is one of `candidate_owner`, `implementation`, `parameter`, `derived_field`, `mapping`, `consumer`.
- `canonical_owner.status` is one of `settled`, `ambiguous`, `absent`. When `settled`, add `"symbol"` naming the owner.
- `generated_at` is informational and is **never** used as a freshness criterion.
- JSON only. There is no Markdown twin: the report is the human-readable layer, and duplicating the index in prose creates two truths that drift.

## Three distinct notions of change

Freshness and review scope are different questions. Collapsing them produces false freshness.

```
INDEX BASELINE      the commit and tree the index was generated from
REPOSITORY STATE    HEAD plus staged plus working tree, right now
REVIEW DELTA        the change actually under review
```

The hazard a `baseline..HEAD` comparison misses is common and silent: the indexed tree can equal the HEAD tree while uncommitted local modifications are exactly what is under review. That reports `fresh` for an index that does not describe the code being judged. Staged-only work has the same shape.

**Freshness is computed against the repository state. The revalidation set is the union of the index-to-repository drift and the review delta**, because a concept can need revalidation either because the index is behind or because the review touches it.

## Freshness states

Computed from the **tree hash**, never from the date. An index from yesterday can be perfectly valid; one from thirty seconds ago can be stale after a commit. Two commits with the same tree do not make an index semantically stale.

| State | Condition | Behaviour |
|---|---|---|
| `fresh` | indexed tree equals the current tree for the recorded `scope`, and the worktree is clean within that scope | use as a reliable evidence seed |
| `delta-stale` | baseline commit reachable and the delta is computable | the normal case: mark touched concepts dirty, revalidate their neighbourhoods, treat the rest as seed |
| `unusable` | baseline unreachable, history rewritten, incompatible `schema_version`, different `scope`, malformed JSON, not a git repository, or the delta cannot be determined | degrade to diff-anchored discovery and say so in Gaps |

Freshness is never binary. Discarding the whole index on any HEAD movement throws away most of the benefit.

## The script

`${CLAUDE_PLUGIN_ROOT}/skills/abstraction-architect/scripts/concept_index.py`

**The script never discovers concepts.** It validates the schema, resolves the three notions of change above, intersects the delta with indexed file paths, and emits the partition. Every semantic judgement belongs to the agent.

```
SCRIPT (deterministic, Python)          AGENT (semantic, model)
  freshness_state                         semantic discovery over
  index_baseline                            unmapped_changed_files
  repository_state                        new concepts
  review_delta                            semantic neighbourhood of
  changed_files                             dirty_indexed_concepts
  dirty_indexed_concepts                  every promotion to a finding
  unmapped_changed_files
```

`unmapped_changed_files` is what makes the duty of autonomous rediscovery mechanical rather than aspirational. It is the explicit list of changed files that no indexed concept claims, handed over as work to do. Without it, "discover concepts the index does not contain" is an instruction that quietly evaporates on a busy run.

### Invocation

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/abstraction-architect/scripts/concept_index.py" \
  status --index .abstraction-architect/concept-index.json --repo . \
  --changed-files /tmp/changed.txt
```

Modes:

```
validate --index PATH
status   --index PATH [--repo PATH] [--base REF] [--head REF]
                      [--working-tree] [--changed-files PATH]
```

Review delta sources, in precedence order: `--changed-files` (one path per line, which is how `senior-review` passes scope), then `--base` with optional `--head`, then `--working-tree`. With none of them the review delta is empty and only the baseline drift drives revalidation.

### Output

```json
{
  "freshness_state": "delta-stale",
  "reason": "indexed tree 9f48 does not match current tree 3c21",
  "index_baseline": {"commit": "a13fe2", "tree": "9f48", "scope": "."},
  "repository_state": {"head_commit": "92ac10", "head_tree": "3c21", "dirty": false},
  "review_delta": {"source": "changed-files", "files": ["support/refunds.py"]},
  "changed_files": ["config/refunds.py", "support/refunds.py"],
  "dirty_indexed_concepts": ["Refund eligibility"],
  "unmapped_changed_files": []
}
```

Exit code 0 on success including `unusable`, 2 on bad invocation. An `unusable` result is a normal outcome, not an error: the agent degrades and reports it.

**On script failure or missing Python, treat the index as `unusable`.** Never assume `fresh`.

## What Gaps must say

Report numbers, not adjectives:

```
Concept index baseline: a13fe2      Current HEAD: 92ac10
Delta determined: yes               Indexed concepts revalidated: 4
Unindexed changed concepts discovered: 2
```

Or, degraded:

```
Concept index unavailable (baseline commit a13fe2 not reachable).
Knowledge-track coverage used diff-anchored discovery only;
global competing-authority coverage was not attempted.
```
````

- [ ] **Step 2: Verify both verbatim rules**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
F=plugins/abstraction-architect/skills/abstraction-architect/references/concept-index-protocol.md
grep -c "Index entries nominate search targets; current source code proves findings." "$F"
grep -c "The script never discovers concepts." "$F"
```

Expected: `1` and `1`.

- [ ] **Step 3: Verify the bundled-path linter passes**

The file contains a `${CLAUDE_PLUGIN_ROOT}` path inside a fenced block, which the linter scans deliberately.

Run:

```bash
python scripts/lint_bundled_paths.py
```

Expected: exit 0. A failure means a `plugins/...` path leaked into the file; replace it with `${CLAUDE_PLUGIN_ROOT}/...`.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/concept-index-protocol.md
git commit -m "Define the concept index protocol

Schema, the three distinct notions of change, and three freshness states
computed from tree hashes rather than dates. Separating index baseline
from repository state from review delta closes a silent hazard: an
indexed tree can equal the HEAD tree while the uncommitted work is
exactly what is under review, which a baseline..HEAD comparison reports
as fresh.

The index nominates search targets and never proves a finding, and no
metric may reward agreement with it."
```

---

### Task 6: The concept_index.py script

This is the only executable artifact in the plan and the only task with real tests. The tests live outside the plugin so they are neither shipped to users nor mirrored into `exports/`.

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/scripts/concept_index.py`
- Create: `tests/test_concept_index.py`

**Interfaces:**
- Consumes: the schema and CLI contract from Task 5.
- Produces: the CLI `validate` and `status` subcommands and the eight output keys, invoked by Task 11 and by the CI step added in Task 15.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_concept_index.py`:

```python
"""Tests for the abstraction-architect concept index script.

Stdlib only. Each test builds a real throwaway git repository, because the
script's whole job is to answer questions about git state and a mocked git
would test the mock.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (REPO_ROOT / "plugins" / "abstraction-architect" / "skills"
          / "abstraction-architect" / "scripts" / "concept_index.py")


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


def make_repo(tmp):
    git(tmp, "init", "-q")
    git(tmp, "config", "user.email", "t@example.com")
    git(tmp, "config", "user.name", "T")
    return tmp


def write(repo, rel, text):
    path = Path(repo) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit_all(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                          capture_output=True, text=True).stdout.strip()


def tree_of(repo, rev="HEAD"):
    return subprocess.run(["git", "rev-parse", f"{rev}^{{tree}}"], cwd=repo,
                          capture_output=True, text=True).stdout.strip()


def write_index(repo, commit, tree, concepts=None, scope=".", schema_version=1):
    index = {
        "schema_version": schema_version,
        "generated_from_commit": commit,
        "generated_from_tree": tree,
        "generated_at": "2026-08-10T12:00:00Z",
        "scope": scope,
        "concepts": concepts if concepts is not None else [],
    }
    path = Path(repo) / ".abstraction-architect" / "concept-index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index), encoding="utf-8")
    return str(path)


def run_status(repo, index_path, *extra):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "status", "--index", index_path,
         "--repo", str(repo), *extra],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


REFUND_CONCEPT = {
    "concept": "Refund eligibility",
    "kind": "policy",
    "representations": [
        {"symbol": "RefundPolicy.can_refund",
         "file": "domain/refund_policy.py", "role": "candidate_owner"},
        {"symbol": "REFUND_WINDOW_DAYS",
         "file": "config/refunds.py", "role": "parameter"},
    ],
    "writers": ["RefundPolicy"],
    "consumers": ["checkout"],
    "canonical_owner": {"status": "ambiguous"},
    "evidence": ["same 30-day policy in two places"],
}


class ConceptIndexStatus(unittest.TestCase):

    def test_missing_index_is_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "a.py", "x = 1\n")
            commit_all(tmp, "init")
            out = run_status(tmp, str(Path(tmp) / "nope.json"))
            self.assertEqual(out["freshness_state"], "unusable")

    def test_incompatible_schema_version_is_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "a.py", "x = 1\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), schema_version=99)
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "unusable")
            self.assertIn("schema_version", out["reason"])

    def test_matching_tree_and_clean_worktree_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "fresh")
            self.assertEqual(out["changed_files"], [])

    def test_matching_tree_with_uncommitted_change_is_not_fresh(self):
        """The false-freshness hazard: HEAD tree matches, but the
        uncommitted work is exactly what is under review."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "domain/refund_policy.py", "def can_refund(): return 1\n")
            out = run_status(tmp, idx)
            self.assertNotEqual(out["freshness_state"], "fresh")
            self.assertEqual(out["freshness_state"], "delta-stale")
            self.assertTrue(out["repository_state"]["dirty"])
            self.assertIn("domain/refund_policy.py", out["changed_files"])

    def test_advanced_head_with_reachable_baseline_is_delta_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            base = commit_all(tmp, "init")
            base_tree = tree_of(tmp)
            idx = write_index(tmp, base, base_tree, [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            commit_all(tmp, "add config")
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "delta-stale")
            self.assertIn("config/refunds.py", out["changed_files"])

    def test_unreachable_baseline_is_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "a.py", "x = 1\n")
            commit_all(tmp, "init")
            idx = write_index(tmp, "0" * 40, "1" * 40, [REFUND_CONCEPT])
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "unusable")
            self.assertIn("not reachable", out["reason"])

    def test_partition_splits_indexed_from_unmapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            base = commit_all(tmp, "init")
            idx = write_index(tmp, base, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            write(tmp, "support/new_thing.py", "x = 1\n")
            commit_all(tmp, "two files")
            out = run_status(tmp, idx)
            self.assertEqual(out["dirty_indexed_concepts"], ["Refund eligibility"])
            self.assertEqual(out["unmapped_changed_files"], ["support/new_thing.py"])

    def test_changed_files_input_is_unioned_with_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            write(tmp, "unrelated/other.py", "y = 2\n")
            base = commit_all(tmp, "init")
            idx = write_index(tmp, base, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            commit_all(tmp, "drift")
            listing = Path(tmp) / "changed.txt"
            listing.write_text("unrelated/other.py\n", encoding="utf-8")
            out = run_status(tmp, idx, "--changed-files", str(listing))
            self.assertIn("config/refunds.py", out["changed_files"])
            self.assertIn("unrelated/other.py", out["changed_files"])
            self.assertEqual(out["review_delta"]["source"], "changed-files")


class ConceptIndexValidate(unittest.TestCase):

    def test_validate_rejects_missing_required_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--index", str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("generated_from_commit", result.stdout + result.stderr)

    def test_validate_accepts_a_well_formed_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "generated_from_commit": "a" * 40,
                "generated_from_tree": "b" * 40,
                "generated_at": "2026-08-10T12:00:00Z",
                "scope": ".",
                "concepts": [REFUND_CONCEPT],
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--index", str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
python -m unittest tests.test_concept_index -v
```

Expected: every test errors, because `concept_index.py` does not exist yet. The failure text mentions the missing script path.

- [ ] **Step 3: Write the script**

Create `plugins/abstraction-architect/skills/abstraction-architect/scripts/concept_index.py`:

```python
#!/usr/bin/env python3
"""Concept index freshness and delta partitioning for abstraction-architect.

Stdlib only, deterministic work only. This script never discovers concepts.
It validates the index schema, resolves the three distinct notions of change
(index baseline, repository state, review delta), and partitions the changed
files into those an indexed concept already claims and those it does not.

Every semantic judgement, including whether two representations encode the
same knowledge, belongs to the agent.

Usage:

    concept_index.py validate --index PATH
    concept_index.py status   --index PATH [--repo PATH]
                              [--base REF] [--head REF]
                              [--working-tree] [--changed-files PATH]

status prints one JSON object on stdout. Exit code 0 on success, including
the unusable state, which is a normal outcome and not an error. Exit 1 when
validate rejects an index. Exit 2 on bad invocation.
"""
import argparse
import json
import subprocess
import sys

SCHEMA_VERSION = 1
REQUIRED_KEYS = ("schema_version", "generated_from_commit",
                 "generated_from_tree", "scope", "concepts")


def git(repo, *args):
    """Run git in repo. Returns (ok, stdout_stripped)."""
    result = subprocess.run(["git", *args], cwd=repo,
                            capture_output=True, text=True, encoding="utf-8")
    return result.returncode == 0, result.stdout.strip()


def load_index(path):
    """Returns (index, error_message). One of the two is always None."""
    try:
        with open(path, encoding="utf-8") as handle:
            index = json.load(handle)
    except FileNotFoundError:
        return None, f"index not found at {path}"
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"index at {path} is not readable JSON: {exc}"
    if not isinstance(index, dict):
        return None, "index root is not an object"
    missing = [key for key in REQUIRED_KEYS if key not in index]
    if missing:
        return None, f"index is missing required keys: {', '.join(missing)}"
    if index["schema_version"] != SCHEMA_VERSION:
        return None, (f"incompatible schema_version {index['schema_version']}, "
                      f"this script speaks {SCHEMA_VERSION}")
    return index, None


def scope_tree(repo, rev, scope):
    """Tree hash of scope at rev, or None when it cannot be resolved."""
    if scope in (".", "", None):
        ok, out = git(repo, "rev-parse", f"{rev}^{{tree}}")
        return out if ok and out else None
    ok, out = git(repo, "rev-parse", f"{rev}:{scope}")
    return out if ok and out else None


def commit_exists(repo, rev):
    ok, _ = git(repo, "cat-file", "-e", f"{rev}^{{commit}}")
    return ok


def pathspec(scope):
    return [] if scope in (".", "", None) else [scope]


def diff_files(repo, base, head, scope):
    ok, out = git(repo, "diff", "--name-only", base, head, "--", *pathspec(scope))
    return [line for line in out.splitlines() if line] if ok else []


def worktree_files(repo, scope):
    """Staged, unstaged and untracked paths within scope."""
    ok, out = git(repo, "status", "--porcelain", "--", *pathspec(scope))
    if not ok:
        return []
    files = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:            # rename: take the destination
            path = path.split(" -> ", 1)[1]
        files.append(path.strip().strip('"'))
    return files


def partition(index, changed_files):
    """Split changed files into indexed concepts touched and unclaimed files."""
    changed = set(changed_files)
    claimed = set()
    dirty = []
    for concept in index.get("concepts", []):
        files = {rep.get("file") for rep in concept.get("representations", [])
                 if rep.get("file")}
        claimed |= files
        if files & changed:
            dirty.append(concept.get("concept"))
    unmapped = sorted(path for path in changed if path not in claimed)
    return sorted(name for name in dirty if name), unmapped


def resolve_review_delta(repo, args, scope):
    if args.changed_files:
        try:
            with open(args.changed_files, encoding="utf-8") as handle:
                files = [line.strip() for line in handle if line.strip()]
        except OSError as exc:
            return {"source": "changed-files", "files": [],
                    "error": f"cannot read {args.changed_files}: {exc}"}
        return {"source": "changed-files", "files": files}
    if args.base:
        head = args.head or "HEAD"
        return {"source": f"{args.base}..{head}",
                "files": diff_files(repo, args.base, head, scope)}
    if args.working_tree:
        return {"source": "working-tree", "files": worktree_files(repo, scope)}
    return {"source": "none", "files": []}


def unusable(reason, index_baseline=None, review_delta=None):
    return {
        "freshness_state": "unusable",
        "reason": reason,
        "index_baseline": index_baseline or {},
        "repository_state": {},
        "review_delta": review_delta or {"source": "none", "files": []},
        "changed_files": [],
        "dirty_indexed_concepts": [],
        "unmapped_changed_files": [],
    }


def status(args):
    repo = args.repo
    index, error = load_index(args.index)
    if error:
        return unusable(error)

    scope = index.get("scope", ".")
    baseline = {
        "commit": index["generated_from_commit"],
        "tree": index["generated_from_tree"],
        "scope": scope,
    }

    ok, head_commit = git(repo, "rev-parse", "HEAD")
    if not ok or not head_commit:
        return unusable(f"{repo} is not a git repository with a HEAD commit",
                        baseline)

    head_tree = scope_tree(repo, "HEAD", scope)
    if head_tree is None:
        return unusable(f"scope {scope!r} does not resolve at HEAD", baseline)

    dirty_paths = worktree_files(repo, scope)
    repository_state = {
        "head_commit": head_commit,
        "head_tree": head_tree,
        "dirty": bool(dirty_paths),
    }

    review_delta = resolve_review_delta(repo, args, scope)

    if not commit_exists(repo, baseline["commit"]):
        result = unusable(
            f"index baseline commit {baseline['commit'][:7]} is not reachable",
            baseline, review_delta)
        result["repository_state"] = repository_state
        return result

    drift = diff_files(repo, baseline["commit"], "HEAD", scope) + dirty_paths
    changed_files = sorted(set(drift) | set(review_delta["files"]))

    if baseline["tree"] == head_tree and not dirty_paths:
        state = "fresh"
        reason = f"indexed tree matches current tree for scope {scope!r}"
    else:
        state = "delta-stale"
        if dirty_paths and baseline["tree"] == head_tree:
            reason = ("indexed tree matches HEAD but the worktree carries "
                      f"{len(dirty_paths)} uncommitted change(s)")
        else:
            reason = (f"indexed tree {baseline['tree'][:4]} does not match "
                      f"current tree {head_tree[:4]}")

    dirty_concepts, unmapped = partition(index, changed_files)
    return {
        "freshness_state": state,
        "reason": reason,
        "index_baseline": baseline,
        "repository_state": repository_state,
        "review_delta": review_delta,
        "changed_files": changed_files,
        "dirty_indexed_concepts": dirty_concepts,
        "unmapped_changed_files": unmapped,
    }


def validate(args):
    index, error = load_index(args.index)
    if error:
        print(f"FAIL  {error}")
        return 1
    problems = []
    for position, concept in enumerate(index["concepts"]):
        label = concept.get("concept") or f"concepts[{position}]"
        if not concept.get("concept"):
            problems.append(f"{label}: missing 'concept' name")
        representations = concept.get("representations")
        if not isinstance(representations, list) or not representations:
            problems.append(f"{label}: 'representations' must be a non-empty list")
            continue
        for rep in representations:
            if not rep.get("file"):
                problems.append(f"{label}: a representation has no 'file'")
    if problems:
        print("FAIL  concept index:")
        for problem in problems:
            print("        ", problem)
        return 1
    print(f"ok    concept index: {len(index['concepts'])} concept(s), "
          f"schema {index['schema_version']}, baseline "
          f"{index['generated_from_commit'][:7]}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--index", required=True)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--index", required=True)
    status_parser.add_argument("--repo", default=".")
    status_parser.add_argument("--base")
    status_parser.add_argument("--head")
    status_parser.add_argument("--working-tree", action="store_true")
    status_parser.add_argument("--changed-files")

    args = parser.parse_args()
    if args.command == "validate":
        return validate(args)
    print(json.dumps(status(args), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
python -m unittest tests.test_concept_index -v
```

Expected: `Ran 10 tests` and `OK`.

If `test_matching_tree_with_uncommitted_change_is_not_fresh` fails, the freshness computation is ignoring the worktree. That is the exact defect this test exists to catch; fix `status` rather than the test.

- [ ] **Step 5: Verify the bundled-path linter passes**

Run:

```bash
python scripts/lint_bundled_paths.py
```

Expected: exit 0.

- [ ] **Step 6: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/scripts/concept_index.py tests/test_concept_index.py
git commit -m "Add concept_index.py and its tests

Freshness and delta partitioning are deterministic work that a language
model does badly, so they move into Python. The script answers three
separate questions (index baseline, repository state, review delta) and
never discovers concepts.

Tests build real throwaway git repositories rather than mocking git,
since a mocked git would test the mock. The load-bearing case is the one
where the HEAD tree matches the indexed tree while uncommitted work is
under review: that must not report fresh."
```

---

### Task 7: Extend theory.md with the form versus knowledge distinction

**Files:**
- Modify: `plugins/abstraction-architect/skills/abstraction-architect/references/theory.md` (insert a section before `## The single rule of thumb` at `:93`)

**Interfaces:**
- Consumes: track names from Task 1.
- Produces: the heading `## 9. Form versus knowledge`, cited by Task 10.

- [ ] **Step 1: Read the current file to locate the insertion point**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
grep -n "^## " plugins/abstraction-architect/skills/abstraction-architect/references/theory.md
```

Expected: the last two headings are `## 8. CUPID vs SOLID` and `## The single rule of thumb`. Insert between them.

- [ ] **Step 2: Insert the new section**

Insert immediately before the line `## The single rule of thumb`:

```markdown
## 9. Form versus knowledge

The eight principles above are usually taught as if they addressed one problem. They address two, and conflating them is what makes a codebase audit either noisy or blind.

**Duplicated form** is the same mechanism written more than once: three retry loops, four pagination encoders, five ways to build the same SDK client. The risk here is premature extraction. Two similar mechanisms may be a coincidence and may diverge under requirements that have not arrived yet, so unifying on a sample of two produces an abstraction anchored to an accident. The Rule of Three, AHA and the Tidy First option price all speak to this risk, and the count is the right instrument for it.

**Duplicated knowledge** is the same fact holding more than one authoritative representation: a refund window in a config file and in a policy class, an approval threshold restated in three services, a status vocabulary maintained in an enum and in a database table. The risk here is the opposite one. There is no premature extraction to fear, because the fact is already singular in the domain; what exists is two owners of one truth, and they will drift. Waiting for a third representation before acting means waiting for the drift to get worse.

DRY, read as its authors wrote it, is about the second kind. Section 2 of this file quotes the formal statement: every piece of knowledge must have a single, unambiguous, authoritative representation. The load-bearing word is knowledge. The popular misreading, that no two lines should look alike, collapses the two problems into one and then applies the instrument of the first to both.

Three consequences the auditor works with directly:

- **The count is the right instrument for form and the wrong one for knowledge.** Two authoritative representations of one fact is already a defect. Three similar mechanisms is a signal, and two is not.
- **Textual similarity is evidence for neither.** Two identical status enums in different bounded contexts are not duplicated knowledge. One policy written three different ways, with no shared token between them, is.
- **The remediations differ.** Duplicated form wants a shared mechanism. Duplicated knowledge wants an owner. Extracting a helper without settling ownership creates one more authority rather than fewer.

`references/evidence-tracks.md` turns this distinction into the two gates the auditor actually runs.

---
```

- [ ] **Step 3: Verify the section landed and the file still reads in order**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
grep -n "^## " plugins/abstraction-architect/skills/abstraction-architect/references/theory.md
```

Expected: headings 1 through 9 in order, then `## The single rule of thumb` last.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/theory.md
git commit -m "Add the form versus knowledge distinction to the theory

The file already stated that DRY targets knowledge rather than lines,
and the audit process still hunted structural shape. This section names
the two risks explicitly, notes that the count is the right instrument
for one and the wrong one for the other, and hands off to the two
evidence tracks."
```

---

### Task 8: Domain patterns P13 to P18 and the non-exhaustiveness rule

**Files:**
- Modify: `plugins/abstraction-architect/skills/abstraction-architect/references/unification-patterns.md` (header block at `:1-8`, then append after `:223`)

**Interfaces:**
- Produces: pattern ids `P13` to `P18`, cited by Task 11.

- [ ] **Step 1: Add the non-exhaustiveness rule to the header**

Replace the paragraph at `:7` that currently reads:

```markdown
The Rule of Three (see `theory.md`) still applies: do not promote a pattern with fewer than three call sites. Two may diverge; three signals a real shape.
```

with:

```markdown
The Rule of Three (see `theory.md`) applies to **D5 missed unification**, which is the dimension this catalog primarily serves: do not promote a D5 finding with fewer than three call sites. Two may diverge; three signals a real shape. It does not apply to D6 or D7, and it does not apply to the knowledge track at all. See `references/evidence-tracks.md`.

> Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding.

This rule is load-bearing. The defect that motivated rewriting this plugin was not that the first twelve patterns were infrastructural. It was that a catalog consulted as a matching step silently became the boundary of what could be found: a duplicated business rule matched nothing, so it fell out of the report. Adding six domain patterns fixes the coverage and would reproduce the same mechanism at a larger size if the rule above were not stated.

A candidate that passes its dimension's gate is a finding whether or not it matches anything here. When it matches, cite the pattern. When it does not, name the concern in your own words and set the finding's `Pattern` field to `uncatalogued`.

**P1 to P12 are infrastructural. P13 to P18 are domain-facing and deliberately broad**, written as illustrations of a kind of concern rather than as an enumeration of the concerns that exist.
```

- [ ] **Step 2: Append the six domain patterns**

Append to the end of the file:

````markdown

---

## P13. Business rule or policy threshold

**Structural signature:** A numeric or categorical bound that encodes a business decision appears in more than one place, usually without textual similarity. An order value above which approval is required, a refund window in days, a retry budget a customer is entitled to, a discount tier boundary, a rate limit tied to a plan. One site holds it as a named constant, another inlines the literal, a third derives it from a config key, a fourth restates it as a differently phrased predicate.

```
OrderService:        if total > 1000 -> requiresApproval
CheckoutController:  if cartValue > 1000 -> managerApproval
InvoiceWorkflow:     highValue = amount > 1000
```

**Forces that want this to change together:** The business changes the number, which happens routinely and without engineering involvement. The rule gains a dimension (a threshold per currency, per tenant, per plan). Audit needs to state what the policy was on a given date. Regulation requires the bound to be documented and evidenced.

**Suggested target layer:** A named policy object that owns both the value and the predicate, for example `ApprovalPolicy.requires_approval(order)`. Call sites ask the policy rather than comparing numbers. The value lives in one place, the predicate lives with it, and a change is one edit with one test.

**Common pitfalls:**
- Extracting the constant but leaving the predicate duplicated. Three sites comparing against one shared constant still encode three copies of the rule, and the next requirement ("above 1000 *and* the customer is not trusted") has to be applied three times.
- Putting the policy in a shared kernel used by two bounded contexts whose thresholds only coincidentally agree today.
- Making the policy read configuration at every call without a documented default, which trades a duplicated literal for an undocumented runtime dependency.

**Retrospective indicator that you did this right:** Finance changes the approval threshold and one pull request delivers it. The question "what was our approval rule in March" is answered by reading one file's history.

---

## P14. Eligibility predicate

**Structural signature:** A question of the form "is this thing allowed to do that" is answered independently in several places. Can this order be refunded, can this user access this feature, is this account in good standing, is this shipment cancellable. Each site assembles the answer from raw fields, and the assemblies have already drifted: one checks state and age, another checks state, age and payment status, a third forgot the payment check.

**Forces that want this to change together:** A new condition is added to the rule and must reach every caller. A support tool must show the user *why* something is not eligible, which requires a structured reason rather than a boolean. The rule must be evaluated in a context that has no request (a batch job, a report), so it must not depend on request-scoped state.

**Suggested target layer:** An eligibility function that returns a reason rather than a boolean: `RefundEligibility.check(order) -> Eligible | Ineligible(reason)`. Callers branch on the result and display the reason. The rule has one implementation and one test suite.

**Common pitfalls:**
- Returning a bare boolean, which forces every caller that needs to explain the answer to reimplement the rule in order to derive the reason.
- Folding authorization into eligibility. "Is this refundable" and "may this user issue it" are different questions with different owners; see P3.
- Letting the predicate reach into infrastructure to fetch what it needs, which makes it unusable from a batch context and untestable without a database.

**Retrospective indicator that you did this right:** The support portal and the customer-facing API give the same answer with the same wording. Adding a condition is one edit.

---

## P15. State machine transition table

**Structural signature:** The legal transitions of a lifecycle are encoded implicitly across the code that performs them. Order status moves through `pending`, `paid`, `shipped`, `cancelled`, `refunded`, and the rules about which move is legal live inside the handlers that make the moves. Some handlers guard, some do not. Nothing states the full set of transitions, so nobody can answer whether a cancelled order can become paid without reading every handler.

**Forces that want this to change together:** A new state is added and every guard must be reconsidered. An audit needs the state history and the reason for each transition. A bug report claims an impossible state was reached, and answering it requires knowing what was possible. A terminal state must become genuinely terminal.

**Suggested target layer:** An explicit transition table plus one `transition(entity, to_state, reason)` entry point that consults it. Handlers request a transition and receive a refusal when it is illegal. The table is readable in one screen and is the answer to "what can happen to an order".

**Common pitfalls:**
- Encoding the table and leaving the old inline guards in place, which produces two authorities and a D2 finding on the next audit.
- Building a general workflow engine for six states, which is anti-pattern A9.
- Forgetting that retries and idempotent replays traverse transitions twice, so the table must say whether a self-transition is legal.

**Retrospective indicator that you did this right:** "Can a refunded order ship" is answered by reading one table. Adding a state produces a compile error or a test failure at every place that must consider it.

---

## P16. Pricing or discount computation

**Structural signature:** The amount a customer pays is computed in more than one place: the cart preview, the checkout confirmation, the invoice, the accounting export, the analytics job. Each applies discounts, taxes and rounding in its own order. The preview and the invoice disagree by a cent, and which one is right depends on who is asking.

**Forces that want this to change together:** A new discount type is introduced and must apply everywhere consistently. The order of operations changes, for example discount before tax rather than after, which is a legal question with one right answer per jurisdiction. Rounding policy changes. A reconciliation report must tie the invoice total to the line items.

**Suggested target layer:** One pricing pipeline that takes a cart and a context and returns a priced result with its breakdown. Every surface renders that result; none recomputes it. Related to P4 money arithmetic, which owns the representation, while this pattern owns the sequence of operations.

**Common pitfalls:**
- Letting the presentation layer round for display and then persisting the rounded figure.
- Recomputing on the invoice "to be safe" instead of storing the priced result, which guarantees the two will diverge the moment the pipeline changes.
- Treating tax as a discount, which produces the wrong answer for jurisdictions where tax applies to the pre-discount amount.

**Retrospective indicator that you did this right:** The cart, the invoice and the accounting export agree to the cent, by construction rather than by testing.

---

## P17. Identifier and code format

**Structural signature:** A structured identifier has a format that is parsed, validated, generated or rendered in several places with slightly different rules. An invoice number, a SKU, a tenant slug, an external reference, a coupon code. One validator accepts lowercase, another rejects it. The generator pads to eight digits; a parser assumes seven. A display function inserts separators that the parser does not tolerate on the way back in.

**Forces that want this to change together:** The format gains a segment (a year prefix, a region code, a check digit). A migration must accept both the old and the new format for a period. Validation must be identical at every entry point or data arrives that later reads cannot parse. Rendering for humans and storing for machines must round-trip.

**Suggested target layer:** A value object owning `parse`, `validate`, `generate` and `format` for that identifier, with the regex or grammar stated once. Nothing else constructs or destructures the identifier as a string.

**Common pitfalls:**
- Sharing one identifier type across two contexts that only coincidentally use the same shape today.
- Validating on write and not on read, so that data written before the rule tightened crashes the reader.
- Putting the display separators in the stored value.

**Retrospective indicator that you did this right:** Adding a check digit is one class change plus a migration. No entry point accepts an identifier that another rejects.

---

## P18. Status or lifecycle vocabulary

**Structural signature:** The set of allowed values for a status is declared more than once and the declarations have drifted. A TypeScript union, a database `CHECK` constraint, a Python enum, a set of magic strings in a front-end switch, and a mapping table for an external CRM. Adding a value requires finding all five, and the last one added is missing from two of them.

**Forces that want this to change together:** A value is added, renamed or retired. The external system's vocabulary changes and the mapping must move with it. A report groups by status and must not silently drop an unmapped value. Exhaustiveness checking must actually fail when a case is unhandled.

**Suggested target layer:** One declaration that the others are derived from or validated against: an enum that generates the database constraint, or a schema that both sides import. Where derivation is impossible across a language boundary, one test that asserts the two declarations agree, so drift fails the build rather than production.

**Common pitfalls:**
- Unifying a status vocabulary across bounded contexts because the values coincide today. `Shipping.Status` and `Payment.Status` may both read `PENDING`, `COMPLETE`, `FAILED` and still be different knowledge; see `references/evidence-tracks.md`.
- Mapping to an external vocabulary with a silent default, which turns an unmapped new value into a wrong value rather than an error.
- Adding a value without deciding what existing rows mean.

**Retrospective indicator that you did this right:** Adding a status breaks the build in every place that must handle it and nowhere else. The CRM mapping is exhaustive by construction.
````

- [ ] **Step 3: Verify the rule and the pattern ids**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
F=plugins/abstraction-architect/skills/abstraction-architect/references/unification-patterns.md
grep -c "Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding." "$F"
grep -c "^## P1[3-8]\." "$F"
```

Expected: `1` and `6`.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/unification-patterns.md
git commit -m "Add six domain patterns and the non-exhaustiveness rule

The twelve existing patterns are all infrastructural, so a duplicated
business rule matched nothing and fell out of the report. P13 to P18
cover thresholds, eligibility, transitions, pricing, identifiers and
status vocabularies.

The rule matters more than the six: a catalog consulted as a matching
step becomes the boundary of the findable, and a bigger allowlist is
still an allowlist. A candidate that passes its gate is a finding with
Pattern: uncatalogued when nothing here fits."
```

---

### Task 9: anti-patterns.md and decision-frame.md

Two small edits to existing files, grouped because neither is worth a reviewer's separate gate.

**Files:**
- Modify: `plugins/abstraction-architect/skills/abstraction-architect/references/anti-patterns.md` (header at `:1-8`)
- Modify: `plugins/abstraction-architect/skills/abstraction-architect/references/decision-frame.md` (whole file)

**Interfaces:**
- Consumes: gate ids from Task 1, dimension ids from Task 2.
- Produces: the severity calibration, cited by Tasks 2 and 11.

- [ ] **Step 1: Add the non-exhaustiveness rule to anti-patterns.md**

Insert after the paragraph at `:7` that ends `...which lets the real pattern reveal itself later.`:

```markdown
> Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding.

These twelve serve **D7 abstraction fitness**, whose proof is friction inside one abstraction and not a count of copies. An abstraction that is fighting its callers in a way none of these describes is still a D7 finding, reported with `Pattern: uncatalogued`.

Anti-patterns keep their `A1.` to `A12.` ids inside this file. Elsewhere they are cited as `anti-pattern A1` to avoid colliding with the form gates `A1` to `A5` in `references/evidence-tracks.md`.
```

- [ ] **Step 2: Rewrite decision-frame.md**

Replace the entire contents of `plugins/abstraction-architect/skills/abstraction-architect/references/decision-frame.md` with:

````markdown
# Decision Frame

What happens **after** a candidate has passed its dimension's gate: whether it is promoted, at what severity, and how the remediation is framed.

This file does not restate the gates. Track A gates `A1` to `A5` and track B gates `K1` to `K6` live in `references/evidence-tracks.md`, and duplicating them here would create two authorities over one rule, which is the D2 defect this plugin exists to find.

## Promotion

A candidate becomes a finding when all three hold:

1. **Its dimension's gate passed**, per `references/evidence-tracks.md`.
2. **Every cited representation has been read against current source.** A finding whose prior art you have not opened and compared is not reportable. Near-identical names routinely hide different behaviour, and an index entry is a search target rather than a proof.
3. **The lenses have been applied and recorded**, per `references/dimensions.md`. A lens does not veto, with one exception: an L2 verdict of "consolidating adds a hop and saves nothing" changes the suggested direction rather than the finding.

A candidate that fails any of the three is dropped. Silence is the correct output when the proof is not there.

## Severity calibration

Default to **Medium**. Escalate or de-escalate only when the evidence supports it. Reserve High for findings you can argue for in one paragraph. Reserve Low for smells with no concrete pressure.

**Severity follows consequence, never occurrence count.** There is no mapping of the form two equals Low, three equals Medium. Two independent authoritative permission policies can be High on two occurrences; four duplicated formatting constants can be Low on four.

- **High** when the finding creates:
  - **Security risk**: duplicated authorization rules, scattered token handling, an eligibility predicate that guards access and disagrees with itself, competing authorities over a permission fact.
  - **Data-correctness risk**: money arithmetic, rounding or pricing sequence, date and timezone handling, derivable state with repair code, two authorities over a value that reconciliation depends on.
  - **Operational risk**: incompatible retry or timeout policies on the same dependency, a status vocabulary that drifts between a producer and a consumer, a transition rule enforced in one path and not another.
- **Medium**, the default, when the finding creates maintenance drag: a mechanism repeated three times, a layer that is accumulating flags, a redundant representation with a real but bounded mapping cost. The cost is paid in change velocity, not in incidents.
- **Low** when the pattern is a smell with no concrete pressure. A stable strategy-for-two on a cold path. A second occurrence noted so the third is recognisable.

## Confidence

Severity says how much it matters. Confidence says how sure you are, and they are reported separately.

- **High confidence**: every cited representation was read on current source, and the dimension gate passed on evidence from more than one signal.
- **Medium confidence**: the gate passed but one input was unavailable, for example a missing deep-dive file or an `unusable` concept index.
- **Low confidence**: a single signal, worth manual verification. Say what would raise it.

Two flags are mandatory when they apply, because they mark the failure modes that cost the most:

- **`Bounded-context exception: unverified`** when context membership could not be determined. On track B this caps the finding at Low confidence and it is never promoted above Medium severity, because unifying across a context boundary is the most expensive wrong move available.
- **`Index-seeded: yes`** when a concept index entry pointed at the evidence. This is provenance, not a quality signal, and nothing in the report or in any consuming pipeline may reward it.

## Remediation framing

`Suggested direction` names the target layer or the move in one sentence. It is not a refactoring plan, a file list or a migration sequence.

Frame it with L4, the option price, when the recommendation is contested:

> The upfront cost of unifying these three sites is one module plus indirection at each call site. The future value is that a threshold change becomes one edit rather than three, and finance has changed it twice this year. Recommendation: unify.

Frame the reverse the same way. An abstraction whose expected value no longer covers its cost gets an inline recommendation, and the intermediate state is supposed to look worse than both endpoints.

Match the remediation to the dimension. This is the difference between an actionable finding and a shallow one:

| Dimension | The move |
|---|---|
| D1 | Give the knowledge one authoritative statement, then have the others call it |
| D2 | Name the canonical owner first. Extracting a helper before ownership is settled adds an authority |
| D3 | Collapse the representations, or document the boundary that justifies keeping them |
| D4 | Derive instead of storing, or make one copy authoritative and the other a cache with a stated invalidation rule |
| D5 | Design the shared mechanism |
| D6 | Migrate to the canonical implementation and delete the reimplementation |
| D7 | Inline the abstraction back to its call sites, then redesign from what they reveal |
````

- [ ] **Step 3: Verify decision-frame no longer restates the gates**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
F=plugins/abstraction-architect/skills/abstraction-architect/references/decision-frame.md
grep -nE '^\s*(A[1-5]|K[1-6])\s' "$F"
```

Expected: no output. The gates are referenced by name in prose but never re-listed.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/references/anti-patterns.md plugins/abstraction-architect/skills/abstraction-architect/references/decision-frame.md
git commit -m "Narrow decision-frame to promotion, severity and remediation

The gates now live in evidence-tracks.md, and restating them here would
create two authorities over one rule, which is the D2 defect this plugin
hunts. What remains is what this file alone owns, plus a remediation
table that matches the move to the dimension: D2 says name the owner
first, because extracting a helper before ownership is settled adds an
authority rather than removing one.

anti-patterns.md gains the same non-exhaustiveness rule and a note on
the deliberate A-id collision."
```

---

### Task 10: Rewrite SKILL.md

**Files:**
- Modify: `plugins/abstraction-architect/skills/abstraction-architect/SKILL.md` (whole file)

**Interfaces:**
- Consumes: every reference filename from Tasks 1 to 9.
- Produces: the reference index the agent loads on demand.

- [ ] **Step 1: Replace the whole file**

Replace the contents of `plugins/abstraction-architect/skills/abstraction-architect/SKILL.md` with:

````markdown
---
name: abstraction-architect
description: >
  Knowledge base for structural entropy: where the same concept is represented, owned, computed or implemented more than once, and what it costs when that concept changes. Covers seven finding dimensions over two evidence tracks (form, judged by recurrence; knowledge, judged by semantic identity and ownership), four lenses applied to every candidate, the concept census method, the concept index protocol, eighteen unification patterns, twelve wrong-abstraction patterns, the canonical theory (Rule of Three, DRY/WET/AHA, Wrong Abstraction, Locality of Behaviour, Bounded Contexts, Tidy First, CUPID), and the written scope boundaries against neighbouring reviewers.
  TRIGGER WHEN: deciding whether to centralize, extract or remove a layer; asking who canonically owns a fact, a policy or a piece of state; auditing a codebase for duplicated knowledge, competing sources of truth, redundant models or derivable state that is stored anyway; reviewing an abstraction for premature generality; spawned by the abstraction-architect agent during /abstraction-architect:audit or as the Abstraction dimension of /senior-review:team-review or /senior-review:code-review; the user asks "should I extract this", "who owns this rule", "is this DRY enough", "is this the wrong abstraction".
  DO NOT TRIGGER WHEN: the task is code formatting and readability cleanup (use clean-code:clean-code), Python-specific refactoring with metrics (use python-development:python-refactor), dead-code removal (use /senior-review:code-review --fix), security review (use senior-review:security-auditor), dependency cycles or module cohesion (use senior-review:code-auditor and senior-review:chicken-egg-detector), or single-file pattern-consistency review with no cross-file question (use senior-review:code-auditor).
---

# Abstraction Architect Knowledge Base

The question this knowledge base answers:

> Where is the same concept represented, owned, computed or implemented more than once, and what does it cost when that concept changes?

Structural entropy accumulates in ways that look locally reasonable. A support team implements an eligibility check because the domain one was hard to reach. A config value is added next to the code that reads it. A DTO is copied because the original had a field the new caller did not want. Each decision is defensible; the sum is a codebase where a single conceptual change touches nine files and misses two.

## The two evidence tracks

Everything here rests on one distinction, developed in `references/theory.md` section 9 and operationalized in `references/evidence-tracks.md`.

**The track determines the nature of the evidence. The dimension determines the gate.**

- **Form** is the same mechanism written more than once. The risk is premature extraction, the instrument is the count, and the Rule of Three is the gate for D5.
- **Knowledge** is the same fact holding more than one authoritative representation. The risk is drift between owners, the count is the wrong instrument, and two representations are sufficient behind a much stricter semantic proof.

The discriminating question for the knowledge track: **can these representations legitimately disagree?** If yes, there is no finding, whatever the surface similarity. If no, two is enough.

## When to use this skill

Load it when:

- Deciding whether to extract, centralize or inline
- Asking who canonically owns a fact, a policy, a threshold or a piece of state
- Auditing for duplicated knowledge, competing authorities, redundant models, or stored state that is derivable
- Evaluating whether an existing abstraction is paying for itself
- Running `/abstraction-architect:audit`, which spawns the auditor agent that loads this skill

Do not load it for the concerns listed in `references/scope-boundaries.md`, which names the owner of each.

## Reference index

Load on demand, not all up front.

| File | Read it when |
|---|---|
| `references/dimensions.md` | Classifying a candidate. D1 to D7 with proof rules, lenses L1 to L4, the single-primary-classification precedence. **Start here.** |
| `references/evidence-tracks.md` | Deciding whether a candidate has enough evidence. Tracks A and B, gates `A1` to `A5` and `K1` to `K6`. |
| `references/concept-census.md` | Running a global audit. Seed map, concept extraction, the four search families, the Concept Evidence Index. |
| `references/concept-index-protocol.md` | Reading or writing `.abstraction-architect/concept-index.json`. Schema, freshness states, the script contract. |
| `references/decision-frame.md` | Promoting a candidate, calibrating severity, framing the remediation. |
| `references/unification-patterns.md` | Matching a form candidate. P1 to P12 infrastructural, P13 to P18 domain-facing. Not an admission gate. |
| `references/anti-patterns.md` | Judging D7. Twelve wrong-abstraction shapes, cited as `anti-pattern A1` to `A12`. Not an admission gate. |
| `references/scope-boundaries.md` | Deciding whether a concern belongs here at all. The five exclusions and their owners. |
| `references/theory.md` | Arguing a position, or when the user asks why this matters. Nine principles plus the single rule of thumb. |
| `references/further-reading.md` | Citing a source. Verified URLs. |

## The single rule of thumb

When this concern changes, where do you have to touch?

- If N grows linearly with features, the concern is a unification candidate.
- If every new requirement adds a flag, branch or parameter to a shared layer, that layer is a wrong abstraction.
- If N is greater than one and the sites must agree but nothing makes them agree, you have found a competing authority, and that is the more serious finding.

## Two rules that are easy to lose

> Structural simplification is the desired outcome of the audit, not a finding category.

> Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding.
````

- [ ] **Step 2: Verify every referenced file exists**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
D=plugins/abstraction-architect/skills/abstraction-architect
for f in $(grep -oE 'references/[a-z-]+\.md' "$D/SKILL.md" | sort -u); do
  test -f "$D/$f" && echo "ok   $f" || echo "MISSING $f"
done
```

Expected: ten `ok` lines, no `MISSING`.

- [ ] **Step 3: Commit**

```bash
git add plugins/abstraction-architect/skills/abstraction-architect/SKILL.md
git commit -m "Rewrite SKILL.md around structural entropy

Reference index grows from five files to ten and leads with dimensions
rather than theory, since classification is what a loading agent needs
first. The description frontmatter now states the ownership question,
which is what makes this skill findable for 'who owns this rule' rather
than only for 'should I extract this'."
```

---

### Task 11: Rewrite the agent

The centerpiece. It stays an orchestrator: no catalog content, no theory, no pattern definitions.

**Files:**
- Modify: `plugins/abstraction-architect/agents/abstraction-architect.md` (whole file)

**Interfaces:**
- Consumes: every reference from Tasks 1 to 10, and the script CLI from Task 6.
- Produces: the input names `concept_index_path` and `mode`, consumed by Task 12 and Task 13. The report section letters, consumed by Task 14.

- [ ] **Step 1: Replace the whole file**

Replace the contents of `plugins/abstraction-architect/agents/abstraction-architect.md` with:

````markdown
---
name: abstraction-architect
description: >
  Adversarial auditor for structural entropy: where the same concept is represented, owned, computed or implemented more than once, and what it costs when that concept changes. Global mode censuses the codebase's concepts from .deep-dive/ plus its own discovery pass and reports seven dimensions of finding: duplicated domain knowledge, competing sources of truth, redundant representation, duplicated or derivable state, missed unification, prior art available, and abstraction fitness. Diff mode takes changed code as the anchor and asks the same seven questions as "introduced or aggravated by this change", seeded by a persisted concept index. Report-only, grounded in canonical theory (Metz, Beck, Fowler, Gross, North, DDD).
  TRIGGER WHEN: spawned by /abstraction-architect:audit; spawned as the abstraction dimension of /senior-review:team-review or /senior-review:code-review; the user asks who canonically owns a fact, policy or piece of state, asks to audit a codebase for duplicated knowledge, competing sources of truth, redundant models or derivable state stored anyway, asks about missed unification or wrong abstractions, or asks whether the code they just wrote was already available elsewhere.
  DO NOT TRIGGER WHEN: the task is implementation, code formatting, security-only review (use senior-review:security-auditor), distributed-flow tracing (use senior-review:distributed-flow-auditor), dead code and unused export removal (use senior-review:cleanup-auditor), dependency cycles or module cohesion (use senior-review:code-auditor and senior-review:chicken-egg-detector), or single-file pattern-consistency review with no cross-file question (use senior-review:code-auditor).
tools: Read, Write, Glob, Grep, Bash
model: inherit
color: orange
---

# ROLE

Adversarial auditor for structural entropy. The question you answer:

> Where is the same concept represented, owned, computed or implemented more than once, and what does it cost when that concept changes?

Two governing rules, both load-bearing.

> **`precision over recall` governs what is reported, not what is searched.**

Search liberally. Report strictly. The predecessor of this agent was forbidden from searching and therefore found only what a structural map had already surfaced, which is why duplicated business rules never appeared in its reports.

> **Index entries nominate search targets; current source code proves findings.**

A concept index accelerates discovery. It never proves anything. Before promoting any knowledge-track finding, re-read the involved representations against current source.

Load the skill `abstraction-architect:abstraction-architect`. Read `references/dimensions.md` first; read the rest on demand.

# INPUTS

- `codebase_path` — the codebase root.
- `mode` (optional, default `global`) — `global` audits the whole codebase. `diff` audits what just changed. Separate PROCESS sections below.
- `deep_dive_path` — path to `.deep-dive/`. Required for `global`, optional for `diff`.
- `concept_index_path` (optional) — path to `concept-index.json`. Defaults to `<codebase_path>/.abstraction-architect/concept-index.json`. Absent or unusable is a supported condition, not an error.
- `changed_files` (optional) — required when `mode` is `diff`: the list of files under review, or a git ref range to derive them from.
- `report_path` (optional) — defaults per mode, see PROCESS.
- `scope` (optional) — a subpath. Only emit findings whose evidence falls inside it.
- `severity_floor` (optional, default `medium`).
- `focus` (optional, default `all`) — restrict to a dimension subset: `knowledge` (D1 to D4), `form` (D5 to D7), a single dimension id, or `all`.

# REQUIRED DEEP-DIVE FILES

Read from `deep_dive_path`. Missing files reduce confidence; they do not abort the audit.

- `01-structure.md` — modules, classes, file sizes. Seeds the concept census and finds god modules.
- `02-interfaces.md` — public APIs. Seeds representation discovery for types, DTOs and enums.
- `03-flows.md` — call graphs. Finds writers and consumers per concept, which is what D2 needs.
- `04-semantics.md` — responsibilities and intent. The strongest seed for behavioural concepts.
- `08-interconnect-map.md` (optional) — cross-partition contracts. Enables the bounded-context check that gate K6 requires.

Mode `diff` needs only `01-structure.md` and `02-interfaces.md`, both produced by `--depth=lite`. With no deep-dive output at all, `diff` runs on the concept index plus `Glob` and `Grep`, at reduced confidence, and says so in Gaps.

# PROCESS (mode = global)

1. **Load the skill.** Read `SKILL.md`, then `references/dimensions.md`.
2. **Read deep-dive files.** Record missing ones in Gaps.
3. **Build the seed map.** Modules, responsibilities, entities, services, persistence, configuration, boundaries, flows, public interfaces. Per `references/concept-census.md`, the map seeds the census and does not bound it.
4. **Extract candidate concepts.** Entity nouns and behavioural concepts. The behavioural ones carry most of the knowledge-track findings.
5. **Discovery.** For each concept, run all four search families from `references/concept-census.md`: by name and near-synonym, by literal, by call, by shape of decision. High recall. Every hit is a candidate.
6. **Build the Concept Evidence Index.** One entry per concept: representations with roles, writers, consumers, canonical owner status, evidence.
7. **Test hypotheses.** For each concept with more than one representation: assign the track, run the dimension gate from `references/evidence-tracks.md`, apply lenses L1 to L4, classify to a single primary dimension using the precedence in `references/dimensions.md`.
8. **Promote and calibrate.** Per `references/decision-frame.md`. Re-read every cited representation on current source before promoting. Severity follows consequence; occurrence count is evidence strength only.
9. **Write the index** to `concept_index_path`, per the schema in `references/concept-index-protocol.md`. Record `generated_from_commit` and `generated_from_tree` from the current HEAD.
10. **Write the report** to `report_path`, default `<codebase_path>/.abstraction-architect/findings.md`.

# PROCESS (mode = diff)

This mode answers: **does this change introduce or aggravate structural entropy relative to the codebase that already exists?** The diff is the anchor. Most of what matters is outside it, so never restrict the search to changed files.

1. **Load the skill.** Same as global.
2. **Resolve the diff and extract changed units.** Two kinds, and the second is not optional:
   - **Structural units**: new functions, methods, classes, modules, constant tables, inline blocks longer than roughly five lines.
   - **Semantic units**: new or modified rules and policies, predicates and thresholds, persisted fields and state, models, DTOs, types and enums, mappings, configuration and defaults, formulas and transformations.

   A changed literal inside an existing function is a semantic unit even when no structural unit changed. A diff that moves a threshold from 1000 to 1500, adds a field to a persisted model, or introduces an enum value produces no structural unit at all, and without semantic extraction D1 to D4 cannot form a hypothesis.

   Ignore pure renames, formatting and deletions.
3. **Load the concept index and check freshness.** Run the script:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/abstraction-architect/scripts/concept_index.py" \
     status --index <concept_index_path> --repo <codebase_path> \
     --changed-files <file listing changed_files, one per line>
   ```

   Read `freshness_state`, `dirty_indexed_concepts` and `unmapped_changed_files` from its JSON. On `unusable`, on a script failure, or with no Python available, proceed without the index and record the specific condition in Gaps. Never assume `fresh`.
4. **Map changed units to indexed concepts.** The script gives the file-level mapping. You decide which changed *unit* belongs to which concept.
5. **Discover new concepts.** Work through `unmapped_changed_files` explicitly. These are the changed files no indexed concept claims, and they are where a diff introduces a concept the codebase has never had. This step is a duty, not an optimisation: there is no rule of the form "do not search where the index says nothing".
6. **Revalidate dirty concepts.** For each concept in `dirty_indexed_concepts`, re-read its representations on current source. The index said where to look; the source says what is true. When the source contradicts the index, report the contradiction in Gaps.
7. **Test D1 to D7 as introduced or aggravated.** Each dimension reformulated:

   | Dimension | The diff-mode question |
   |---|---|
   | D1 | Does this diff add another representation of an existing policy? |
   | D2 | Does this diff create a second authority over an existing fact? |
   | D3 | Does this diff add a parallel representation of an existing concept? |
   | D4 | Does this diff store something already derivable from existing state? |
   | D5 | Is this diff the third occurrence, so the Rule of Three fires now, on this commit? |
   | D6 | Was this already available? |
   | D7 | Does this diff introduce or worsen abstraction friction? |

8. **Promote and calibrate.** Per `references/decision-frame.md`, including the mandatory re-read of every cited representation.
9. **Write the report** to `report_path`, default `<codebase_path>/.abstraction-architect/findings-diff.md`. **Do not write the concept index.** New concepts and contradictions go in Gaps; the next global audit consolidates them.

# REPORT STRUCTURE

Both modes use the same section letters so consolidation is uniform. Omit an empty section.

```markdown
# Abstraction-architect findings[ (diff-anchored)]

**Generated:** <ISO timestamp>
**Mode:** global | diff
**Scope:** <codebase_path[/scope]>
**Deep-dive source:** <deep_dive_path | none>
**Concept index:** <path> (<fresh | delta-stale | unusable: reason>)
**Severity floor:** <low | medium | high>
**Focus:** <all | knowledge | form | Dn>

## Summary
- N findings (H high, M medium, L low)
- Concepts censused: <n>  |  with more than one representation: <n>
- Top three findings, one line each

## A. Competing sources of truth (D2)
## B. Duplicated or derivable state (D4)
## C. Redundant representation (D3)
## D. Duplicated domain knowledge (D1)
## E. Prior art available (D6)
## F. Missed unification (D5)
## G. Abstraction fitness (D7)

### <Section letter><n>. <one-line title> — <severity>

- **Dimension:** <Dn name>
- **Pattern:** <catalog id and name, or `uncatalogued`>
- **Evidence:**
  - <path/file.ext>:<line-range> — <role: candidate_owner | implementation | parameter | ...>
  - <path/file.ext>:<line-range> — <role>
- **Why this is a problem:** <one or two sentences naming the force that makes these change together>
- **Change amplification (L1):** <count> sites must change when this concept changes
- **Suggested direction:** <target layer or move, one sentence, per the remediation table>

```
Evidence track: KNOWLEDGE            Evidence track: FORM
Semantic identity: proven            Occurrences: 4
Occurrences: 2                       Independent implementations: yes
Must remain consistent: yes          Shared lifecycle: yes
Bounded-context exception: none      Rule of Three: satisfied
Canonical owner: ambiguous           Index-seeded: no
```

## H. Second occurrences noted, not flagged

One line per pair, exempt from `severity_floor`, so the next occurrence is recognisable. Form-track pairs only: a knowledge-track pair that passed its gate is a finding above, not a note here.

## I. Confidence and Gaps

- **Coverage:** concepts censused, representations read, searches run per concept
- **Concept index:**
  ```
  Concept index baseline: <sha>      Current HEAD: <sha>
  Delta determined: <yes|no>         Indexed concepts revalidated: <n>
  Unindexed changed concepts discovered: <n>
  ```
  Or, when degraded, the specific condition and what coverage was lost.
- **Index contradictions:** entries the source disproved, with what the source says
- **Gaps:** deep-dive files missing, directories not covered, units skipped and why
```

# CONSTRAINTS

- **Report-only.** Edit nothing except `report_path` and, in global mode only, `concept_index_path`.
- **Diff mode never writes the concept index.**
- **Never restrict the diff search to changed files.** What you are looking for is by definition outside the diff.
- **Re-read before promoting.** A finding whose cited representations you have not opened on current source is not reportable, and an index entry is never a substitute.
- **No metric rewards agreement with the index or the seed map.** Report coverage as counts of what you examined, never as a ratio of agreement.
- **One defect, one primary dimension.** Use the precedence in `references/dimensions.md`.
- **Occurrence count is evidence strength, never severity.**
- **A candidate that matches no catalogued pattern is still a finding** when its gate passes. Set `Pattern: uncatalogued`.
- **Dedup with `senior-review:code-auditor`**, which runs as the Architecture dimension of the same review and owns smells visible inside one file. Yours is the cross-file question. See `references/scope-boundaries.md`.
- `Suggested direction` names the target layer or move. It does not produce code, file lists or migration steps.
- Report tight line ranges, not whole files.

# OUTPUT

Return to the caller: the absolute report path, summary counts, the concept index state, and the top three findings as one-line previews. Do not paste the full report into the message.

# ANTI-PATTERNS FOR YOU

- Do not apply the Rule of Three to D6 or D7. A wrong abstraction is a single object; counting copies of it is a category error.
- Do not apply a count to the knowledge track at all. Two authorities over one fact is the defect.
- Do not call two units duplicates because their names match. `formatDate` in billing and `formatDate` in a log formatter usually have different contracts.
- Do not call two units distinct because their names differ. `requiresApproval`, `managerApproval` and `highValue` share no token and may be one policy.
- Do not push a unification across bounded contexts because the code looks alike. Similar shape plus different owner equals essential duplication.
- Do not report the same defect under two dimensions. Report the deepest reason and demote the rest to supporting evidence.
- Do not treat a derivable field as a D4 finding on its own. Without sync, invalidation or repair code, materialising a value is a normal design choice.
- Do not trust the index over the source. When they disagree, the source wins and the disagreement is reportable.
- Do not skip `unmapped_changed_files` because the index looked complete. Completeness of an upstream artifact is never a premise.
- Do not produce a refactoring plan. One sentence of direction.
- Do not echo deep-dive content. The report is your synthesis.
````

- [ ] **Step 2: Verify both verbatim rules and the line budget**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
F=plugins/abstraction-architect/agents/abstraction-architect.md
grep -c "governs what is reported, not what is searched" "$F"
grep -c "Index entries nominate search targets; current source code proves findings." "$F"
wc -l "$F"
```

Expected: `1`, `1`, and a line count under 300. If it exceeds 300, catalog content has leaked in; move it to a reference.

- [ ] **Step 3: Verify the bundled-path linter passes**

The agent invokes the script through `${CLAUDE_PLUGIN_ROOT}` inside a fenced block, which the linter scans.

Run:

```bash
python scripts/lint_bundled_paths.py
```

Expected: exit 0.

- [ ] **Step 4: Verify the dependency-graph linter passes**

The agent names `senior-review` agents in dedup prose. It must not read as a spawn.

Run:

```bash
python scripts/lint_dependency_graph.py
```

Expected: exit 0. If it reports an undeclared `senior-review` edge, rephrase the dedup note so it names the agent as an owner rather than as something to invoke. Do not add a `senior-review` dependency: that closes the cycle marketplace 16.0.0 opened.

- [ ] **Step 5: Commit**

```bash
git add plugins/abstraction-architect/agents/abstraction-architect.md
git commit -m "Rewrite the agent around structural entropy

The agent becomes an orchestrator: two pipelines, the input contract, the
report shape, the constraints. Every catalog and every gate now lives in
a reference loaded on demand.

Diff mode extracts semantic units alongside structural ones, so that a
threshold change or a new enum value produces a hypothesis instead of
nothing, and it works through unmapped_changed_files explicitly so that
the duty of autonomous rediscovery survives a busy run."
```

---

### Task 12: Update the audit command

**Files:**
- Modify: `plugins/abstraction-architect/commands/audit.md` (whole file)

**Interfaces:**
- Consumes: the agent input names from Task 11 and the script CLI from Task 6.

- [ ] **Step 1: Replace the frontmatter and the opening**

Replace `:1-8` with:

```markdown
---
description: Audit a codebase for structural entropy (where the same concept is represented, owned, computed or implemented more than once) across seven dimensions, or check with --diff whether a change introduces new entropy. Auto-launches /codebase-xray:analyze when .deep-dive/ is missing. Report-only.
argument-hint: "[path] [--diff [<base-ref>]] [--scope <subpath>] [--severity-floor low|medium|high] [--focus all|knowledge|form|D1..D7] [--no-index] [--rebuild-index]"
---

# /abstraction-architect:audit

Audit a codebase for structural entropy: duplicated domain knowledge, competing sources of truth, redundant representations, duplicated or derivable state, missed unification, prior art that already exists, and abstractions that are fighting their callers. Report-only.
```

The parenthetical in `description` is deliberate. A dash there would be the exact construct the global constraint forbids, and this field is where it is easiest to reintroduce by habit.

- [ ] **Step 2: Replace the Usage block**

Replace the fenced usage block with:

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --severity-floor high              # only high-severity findings
/abstraction-architect:audit --focus knowledge                  # D1-D4 only
/abstraction-architect:audit --focus D2                         # competing sources of truth only
/abstraction-architect:audit --diff                             # does my change add entropy?
/abstraction-architect:audit --diff origin/master               # same, against an explicit base ref
/abstraction-architect:audit --rebuild-index                    # ignore any existing concept index
```

- [ ] **Step 3: Replace the Arguments section**

```markdown
## Arguments

- `[path]` (optional) — codebase root. Default: current working directory.
- `--diff [<base-ref>]` (optional) — run diff-anchored instead of a whole-codebase audit. Asks the same seven questions as "introduced or aggravated by this change". Base ref defaults to the merge base with the default branch, falling back to `HEAD` for uncommitted work.
- `--scope <subpath>` (optional) — limit findings to a subtree. Deep-dive still runs on the full codebase.
- `--severity-floor low|medium|high` (optional) — default `medium`.
- `--focus all|knowledge|form|D1..D7` (optional) — default `all`. `knowledge` is D1 to D4, `form` is D5 to D7, or name a single dimension.
- `--no-index` (optional) — do not read or write `concept-index.json`. Use when auditing a directory that is not a git repository, or to measure what the audit finds without a seed.
- `--rebuild-index` (optional, global mode only) — ignore any existing index and census the codebase from scratch. Use after a large refactor or a history rewrite.
```

- [ ] **Step 4: Replace the "What this command does" section**

```markdown
## What this command does

1. **Resolves the target path.** Defaults to the current working directory.

2. **Checks for `.deep-dive/`.** Looks for `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`. The optional `08-interconnect-map.md` enables the bounded-context check; without it, knowledge-track findings carry `Bounded-context exception: unverified`.

3. **Auto-launches deep-dive if needed.** If `.deep-dive/` is missing or incomplete, prints *"No deep-dive output found at `.deep-dive/`. Launching `/codebase-xray:analyze` first. This may take several minutes on a large codebase."* then invokes it without a confirmation prompt. Aborts with the log path if deep-dive fails.

   Under `--diff` this step is skipped. Diff mode consumes only `01-structure.md` and `02-interfaces.md`, uses whatever is on disk, and runs on the concept index plus `Glob` and `Grep` when nothing is.

4. **Resolves the concept index.** Unless `--no-index`, checks `<path>/.abstraction-architect/concept-index.json` and runs the freshness script. Reports the state to the user before spawning, so a `delta-stale` index is visible rather than silent:

   ```
   Concept index: delta-stale (baseline a13fe2, HEAD 92ac10, 4 concepts to revalidate)
   ```

   An absent or unusable index is not an error. The audit proceeds and declares the reduced coverage in its Gaps section.

5. **Resolves the diff (`--diff` only).** Runs `git diff --name-only <base-ref>...HEAD` plus `git diff --name-only` for uncommitted work, and passes the union as `changed_files`. Aborts with a clear message when the path is not a git repository.

6. **Spawns the `abstraction-architect` agent** via the `Agent` tool with `codebase_path`, `mode`, `deep_dive_path`, `concept_index_path`, `changed_files` under `--diff`, and the parsed scope, severity-floor and focus flags.

7. **The agent writes the report** to `<path>/.abstraction-architect/findings.md`, or `findings-diff.md` under `--diff`. In global mode it also rewrites `concept-index.json`. **Diff mode never writes the index.**

8. **Prints to the user:** the report path, summary counts, the concept index state, and the top three findings as one-line previews.

The full report stays in the file so the user opens it deliberately.
```

- [ ] **Step 5: Verify no dash-aside survived and the typo is fixed**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
F=plugins/abstraction-architect/commands/audit.md
grep -nE 'entropy - where|[a-z] -- [a-z]' "$F"
```

Expected: no output.

Note on the em dashes already in this file: the `— ` characters in the Arguments list are pre-existing house style for command files, separating a flag name from its gloss inside a list item rather than bracketing a clause. They are not the forbidden construct and this step deliberately does not flag them. What the grep targets is a dash pair wrapping a parenthetical, which is what the `description` field invites.

- [ ] **Step 6: Commit**

```bash
git add plugins/abstraction-architect/commands/audit.md
git commit -m "Update the audit command for the seven dimensions and the index

Adds --focus by dimension or track, --no-index for non-git targets, and
--rebuild-index after a refactor. The command reports the concept index
state before spawning, so that a delta-stale index is visible to the
user rather than a silent degradation inside the agent."
```

---

### Task 13: senior-review integration

Three files outside the plugin, all additive. No `subagent_type` changes, so the skip-if-not-installed handling stays as it is.

**Files:**
- Modify: `plugins/senior-review/commands/team-review.md:300-315`
- Modify: `plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md:620-641`
- Modify: `plugins/senior-review/agents/code-auditor.md:95`

**Interfaces:**
- Consumes: `concept_index_path` from Task 11.

- [ ] **Step 1: Add the index input to the team-review addendum**

In `plugins/senior-review/commands/team-review.md`, inside the fenced input block at `:302-309`, add one line after `deep_dive_path`:

```
concept_index_path: {target root}/.abstraction-architect/concept-index.json
```

Then extend the three-bullet note that follows at `:311-315` with a fourth bullet:

```markdown
- It reads a **concept index** at `.abstraction-architect/concept-index.json` when one exists, which is what makes its knowledge-track dimensions (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated state) worth running on a diff. The index is produced by `/abstraction-architect:audit` in global mode. When it is absent or stale the reviewer degrades to diff-anchored discovery and declares the reduced coverage; it never blocks. This reviewer never writes the index.
```

- [ ] **Step 2: Add the index input to the code-review Agent J block**

In `plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md`, inside the prompt block at `:636-641`, add after `deep_dive_path`:

```
concept_index_path: [repo root]/.abstraction-architect/concept-index.json
```

Then extend the paragraph at `:624` that begins "This is the only agent that answers..." with:

```markdown
Since abstraction-architect 2.0 it answers more than that. It also asks whether the diff creates a second authority over a fact the codebase already owns, adds a parallel representation of an existing concept, or stores state that existing state already determines. Those questions are seeded by a concept index at `.abstraction-architect/concept-index.json` when one exists; without it the agent degrades to diff-anchored discovery and says so.
```

- [ ] **Step 3: Reword the code-auditor boundary note**

Replace `plugins/senior-review/agents/code-auditor.md:95` with:

```markdown
NB: this inspector is scoped to smells you can see **inside one file**. The cross-file question belongs to `abstraction-architect:abstraction-architect`, which runs as the Abstraction dimension of the same review: this new helper already exists in `src/lib/`, this diff is the third copy of the same shape, this fact has two authoritative owners, this layer is bypassed by callers that live elsewhere. Do NOT duplicate its findings here, and do not go hunting for prior art in unchanged files; flag only what the file under review shows on its own. One consequence worth stating: a premature interface or a leaky signature you can see in the file is yours, while the same abstraction judged by **external callers bypassing it** is theirs.
```

- [ ] **Step 4: Verify the linters pass**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
```

Expected: both exit 0. `abstraction-architect` is already an `optionalDependency` of `senior-review`, so the reference is declared. The `.abstraction-architect/` path is a runtime artifact directory and not a bundled plugin path, so the second linter has nothing to say about it.

- [ ] **Step 5: Commit**

```bash
git add plugins/senior-review/commands/team-review.md plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md plugins/senior-review/agents/code-auditor.md
git commit -m "Pass the concept index into the abstraction review dimension

Both spawn sites gain concept_index_path. Nothing else changes: the
subagent_type is the same and the skip-if-not-installed handling is
untouched.

code-auditor's boundary note gains the case that moved: an abstraction
judged by external callers bypassing it is cross-file and belongs to
abstraction-architect, while the same smell visible inside the file
under review stays with the Abstraction Inspector."
```

---

### Task 14: The eval layer

Behavioural invariants, following `evals/ai-tooling/`. This plugin has no ground-truth bug list to recall; what a future edit can silently remove is a philosophy.

**Files:**
- Create: `evals/abstraction-architect/README.md`
- Create: `evals/abstraction-architect/cases/` with twelve case files
- Create: `evals/abstraction-architect/scorecard-template.md`

**Interfaces:**
- Consumes: every rule from Tasks 1 to 12.

- [ ] **Step 1: Read the sibling harness for its shape**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
cat evals/ai-tooling/README.md
ls evals/ai-tooling/cases/
cat evals/ai-tooling/cases/$(ls evals/ai-tooling/cases/ | head -1)
```

Match its case-file structure. Do not invent a second format.

- [ ] **Step 2: Write the README**

Create `evals/abstraction-architect/README.md`:

````markdown
# abstraction-architect evals

Twelve behavioural invariants. This plugin has no ground-truth bug list to measure recall against, so these assert the **philosophy** the 2.0 recentering installed, in the same shape as `evals/ai-tooling/`.

Two standing rules, inherited from that harness:

- **Assertions target the philosophy, never the wording.** A case fails when the behaviour is gone, not when a sentence was rephrased.
- **A case that fails once keeps its case forever.** Cases are never retired for being green.

Source spec: `docs/superpowers/specs/2026-08-10-abstraction-architect-recentering-design.md`.

## Why these twelve

Each one guards a mechanism that a well-meaning future edit removes without noticing. Cases 1 and 2 guard the two-track model, which reads like an inconsistency to anyone who has just learned the Rule of Three. Cases 9 and 10 come from the epistemic-independence doctrine and guard the concept index against becoming a self-confirming truth. Cases 11 and 12 guard the two mechanisms this recentering exists to break: a diff extractor that only sees code shapes, and a catalog that quietly becomes the boundary of the findable.

## Running

Each case states a stimulus and an assertion. Run the stimulus against the installed plugin, then score against the assertion. Record results in a dated copy of `scorecard-template.md`.

**Verify the installed version first.** `evals/ai-tooling/RESULTS.md` records a sweep that was nearly invalidated by scoring a stale install. Check that the installed `abstraction-architect` is the version under test before scoring anything.
````

- [ ] **Step 3: Write the twelve case files**

Create one file per case in `evals/abstraction-architect/cases/`, named `01-rule-of-three-not-universal.md` through `12-uncatalogued-still-reported.md`. Each follows this template, shown filled for case 1:

````markdown
# Case 1: The Rule of Three is not a universal gate for track A

**Guards:** `references/evidence-tracks.md` gate A3, `references/dimensions.md` D6 and D7.

**Why it decays:** the Rule of Three is the most memorable thing in the plugin's theory. A future editor tidying the gates will be tempted to hoist it from D5 up to track A, which reads as a simplification and silently removes D6 and D7.

**Stimulus:**

> A codebase has exactly one `UniversalRepository` class with seven boolean parameters, per-caller exception branches for three callers, and two consumers that bypass it entirely. Elsewhere, `CanonicalMoneyParser.parse()` exists and one module reimplements the same parsing inline. Audit it.

**Assertion (PASS):** both are reported. The `UniversalRepository` finding is D7 and cites friction, not a count. The parser finding is D6 and cites the existence of a canonical owner plus one reimplementation.

**Assertion (FAIL):** either finding is dropped, downgraded, or justified with a reference to having fewer than three occurrences.
````

The remaining eleven, with their guard, decay reason, stimulus and pass condition:

| # | Filename | Invariant |
|---|---|---|
| 2 | `02-knowledge-track-n2-behind-k6.md` | A track B finding with two representations is admitted, but only after gate K6 is demonstrated. Stimulus: `Billing.REFUND_DAYS = 30` and `Support.refundAllowed = age <= 30` in the same context (PASS: reported), against `Shipping.Status` and `Payment.Status` sharing `PENDING/COMPLETE/FAILED` in different contexts (PASS: not reported). FAIL: both reported, or neither. |
| 3 | `03-occurrences-never-severity.md` | Occurrence count never determines severity. Stimulus: two competing authorities over a permission fact, and four duplicated date-format constants on a cold path. PASS: the pair is High, the quartet is Low. FAIL: severity tracks the count in either direction. |
| 4 | `04-single-primary-dimension.md` | One defect gets one dimension. Stimulus: a refund window duplicated in three places, one apparently canonical. PASS: exactly one finding, classified D2, with the D1, D5 and D6 readings present as supporting evidence. FAIL: two or more findings for the same defect. |
| 5 | `05-index-never-sole-evidence.md` | The index never proves a finding. Stimulus: an index entry claims `RefundPolicy` owns the refund window, but the current source shows it was deleted last week. PASS: no finding rests on the stale entry, and the contradiction appears in Gaps. FAIL: a finding cites the index entry as evidence. |
| 6 | `06-discovery-stays-high-recall.md` | Discovery stays liberal even when the report is empty. Stimulus: a small, genuinely clean codebase. PASS: the report is empty or near-empty AND the Gaps section shows a real census was run, with concepts counted. FAIL: the run reports "nothing found" without evidence that searching happened. |
| 7 | `07-excluded-dimensions-stay-out.md` | None of the five excluded dimensions produces an autonomous finding. Stimulus: a codebase with an obvious circular dependency, a god class, and an oversized public API surface. PASS: none of the three is a finding here; any of them may appear as supporting evidence or in Cross-Reviewer Notes. FAIL: a standalone "circular dependency" or "this class has too many responsibilities" finding. |
| 8 | `08-missing-index-does-not-block.md` | An absent index does not block diff mode. Stimulus: run diff mode on a repo with no `.abstraction-architect/` directory. PASS: the review completes, findings are produced, and Gaps names the reduced coverage specifically. FAIL: the run aborts, or reports "index required". |
| 9 | `09-agent-can-contradict-its-index.md` | The agent can contradict the index and reports it. Stimulus: an index whose `canonical_owner.status` is `settled` for a concept that current source shows has three writers. PASS: the finding is reported and the Gaps section states the index was wrong. FAIL: the agent defers to the index, or silently corrects it without reporting. |
| 10 | `10-no-metric-rewards-index-agreement.md` | No score or gate rewards agreement with the index or the seed map. Stimulus: inspect the shipped report template and any scoring language. PASS: coverage is reported as counts of what was examined. FAIL: any percentage, ratio or score that rises with index utilisation or citation. |
| 11 | `11-semantic-units-extracted-from-diff.md` | A diff with no structural change still produces a hypothesis. Stimulus: a one-line diff changing `HIGH_VALUE_THRESHOLD = 1000` to `1500`, in a codebase where two other files compare against 1000. PASS: a D1 or D2 finding, or at minimum a stated hypothesis in the report. FAIL: "no added units to examine" or an empty report. |
| 12 | `12-uncatalogued-still-reported.md` | A concern matching no catalogued pattern is still reported. Stimulus: a domain-specific policy duplicated across three services that fits none of P1 to P18, for example a bespoke seniority calculation for support ticket routing. PASS: reported with `Pattern: uncatalogued`. FAIL: dropped, or forced into the nearest pattern with a poor fit. |

- [ ] **Step 4: Write the scorecard template**

Create `evals/abstraction-architect/scorecard-template.md`:

````markdown
# abstraction-architect eval scorecard

**Date:**
**Plugin version under test:**
**Installed version verified:** yes | no
**Target codebase:**

| # | Case | Result | Notes |
|---|---|---|---|
| 1 | Rule of Three not universal | PASS / FAIL | |
| 2 | Knowledge track N=2 behind K6 | PASS / FAIL | |
| 3 | Occurrences never severity | PASS / FAIL | |
| 4 | Single primary dimension | PASS / FAIL | |
| 5 | Index never sole evidence | PASS / FAIL | |
| 6 | Discovery stays high-recall | PASS / FAIL | |
| 7 | Excluded dimensions stay out | PASS / FAIL | |
| 8 | Missing index does not block | PASS / FAIL | |
| 9 | Agent can contradict its index | PASS / FAIL | |
| 10 | No metric rewards index agreement | PASS / FAIL | |
| 11 | Semantic units extracted from diff | PASS / FAIL | |
| 12 | Uncatalogued still reported | PASS / FAIL | |

**Score:** n/12

## Failures

For each FAIL: what the plugin did, what the case required, and the file and line that would need to change.
````

- [ ] **Step 5: Verify the case count**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
ls evals/abstraction-architect/cases/ | wc -l
```

Expected: `12`

- [ ] **Step 6: Commit**

```bash
git add evals/abstraction-architect/
git commit -m "Add the abstraction-architect eval layer

Twelve behavioural invariants in the evals/ai-tooling shape, because
this plugin has no ground-truth bug list and what a future edit removes
is a philosophy rather than a fix.

Cases 1 and 2 guard the two-track model, which reads like an
inconsistency to anyone who has just learned the Rule of Three. Cases 9
and 10 come from the epistemic-independence doctrine. Cases 11 and 12
guard the two mechanisms the recentering exists to break."
```

---

### Task 15: Release

Version bumps, export mirror, CI step for the new tests, full verification, push. This is the only task that bumps versions and the only one that pushes.

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `exports/vscode/_pipelines/.github/agents/review-abstraction-architect.agent.md`
- Modify: `exports/vscode/_pipelines/.github/skills/abstraction-architect/**`
- Modify: `.github/workflows/consistency.yml`

- [ ] **Step 1: Verify all seven verbatim rules landed**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
D=plugins/abstraction-architect
check() { n=$(grep -rc "$1" $2 2>/dev/null | awk -F: '{s+=$2} END {print s+0}'); echo "$n  $1"; }
check "Can these representations legitimately disagree?" "$D/skills/abstraction-architect/references/evidence-tracks.md"
check "report the deepest architectural reason" "$D/skills/abstraction-architect/references/dimensions.md"
check "Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding." "$D/skills/abstraction-architect/references/"
check "Structural simplification is the desired outcome of the audit, not a finding category." "$D/skills/abstraction-architect/references/scope-boundaries.md"
check "Index entries nominate search targets; current source code proves findings." "$D"
check "The script never discovers concepts." "$D/skills/abstraction-architect/references/concept-index-protocol.md"
```

Expected counts: 1, 1, 2, 1, 2, 1. Any zero means a task did not land its rule.

- [ ] **Step 2: Bump the marketplace**

In `.claude-plugin/marketplace.json`, set the `abstraction-architect` entry's `version` to `2.0.0`, set `metadata.version` to `20.0.0`, and replace that plugin's `description` with:

```
Structural entropy auditor: finds where the same concept is represented, owned, computed or implemented more than once, and what it costs when that concept changes. Seven dimensions over two evidence tracks. Knowledge track (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated or derivable state) is judged by semantic identity and ownership, so two representations suffice behind a strict gate. Form track (missed unification, prior art available, abstraction fitness) is judged by recurrence, where the Rule of Three applies to missed unification only. Global mode censuses the codebase and persists a concept index; diff mode asks the same seven questions as "introduced or aggravated by this change" and runs as the Abstraction dimension of /senior-review:team-review and /senior-review:code-review. Report-only, grounded in canonical theory (Metz, Beck, Fowler, Gross, North, DDD).
```

Extend `keywords` with `structural-entropy`, `source-of-truth`, `semantic-duplication`, `derivable-state`, `knowledge-duplication`.

- [ ] **Step 3: Add the test step to CI**

In `.github/workflows/consistency.yml`, add to the `consistency` job after the "Bundled path lint" step:

```yaml
      - name: Concept index script tests
        run: python -m unittest discover -s tests -v
```

Update the file's opening comment, which currently claims there is no test job, to:

```yaml
# Marketplace consistency checks. Content in this repo is static markdown with
# a small number of stdlib-only helper scripts, so there is no build job: these
# are the mechanical versions of the contracts documented in CLAUDE.md, plus
# unit tests for the helper scripts that have branching logic. Every script is
# stdlib-only Python and runs from the repository root, so failures reproduce
# locally with the same commands.
```

- [ ] **Step 4: Mirror into the VS Code export**

Load the `downstream-exports` skill and follow its source map and adaptations. The bundle is `_pipelines`, which carries this plugin alongside `codebase-xray` and `senior-review`.

Files to mirror:
- `plugins/abstraction-architect/agents/abstraction-architect.md` into `exports/vscode/_pipelines/.github/agents/review-abstraction-architect.agent.md`
- the whole of `plugins/abstraction-architect/skills/abstraction-architect/` into `exports/vscode/_pipelines/.github/skills/abstraction-architect/`, including the new `scripts/` directory

Apply the skill's standard adaptations. Do not mirror `tests/`, which lives outside the plugin precisely so it does not ship.

- [ ] **Step 5: Run every check**

Run:

```bash
cd /d/Projects/alfio-claude-plugins
python -m unittest discover -s tests -v
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/check_version_bumps.py origin/master HEAD
```

Expected: tests `OK`, and all five checks exit 0.

`gen_extension_manifest.py --check` should pass without regeneration, because no agent or prompt was added, renamed or removed. If it fails, run it without `--check` and bump `version` in `exports/vscode/package.json`.

If `check_version_bumps.py` fails, the bump in Step 2 did not land. It evaluates the whole range, so one bump covers every commit from Task 1 onward.

- [ ] **Step 6: Verify the working tree holds only this work**

Other sessions run this repository concurrently.

Run:

```bash
git status --porcelain
git diff --stat .claude-plugin/marketplace.json
```

Stage explicit paths only. Never `git add -A`.

- [ ] **Step 7: Commit and push**

```bash
git add .claude-plugin/marketplace.json .github/workflows/consistency.yml exports/vscode/_pipelines/
git commit -m "Release abstraction-architect 2.0.0, marketplace 20.0.0

Recenters the plugin on structural entropy: seven dimensions over two
evidence tracks, four lenses, a persisted concept index, and a global
audit that becomes the primary product with diff mode mirroring it.

Mirrors the agent and the skill into the _pipelines bundle, and adds a
CI step for the concept index script tests, the repository's first
helper script with branching logic worth testing."
git push
```

- [ ] **Step 8: Confirm CI is green**

Run:

```bash
gh run list --limit 1
```

Wait for the run to complete and confirm both jobs pass. A red `version-bumps` job means the pushed range did not include the bump.

---

## Self-Review

**Spec coverage.** Every section of the spec maps to a task: Section 2 identity to Tasks 10 and 11, non-goals to Task 3; Section 3 classification to Tasks 1, 2, 8, 9; Section 4 pipelines to Task 11, with the seed map and search families in Task 4; Section 5 artifacts to Tasks 5 and 6; Section 6 epistemic independence to Task 5 for the written obligations and Task 14 cases 9 and 10 for the guard; Section 7 degradation to Tasks 5, 11 and 12; Section 8 file layout to Tasks 1 through 9 plus 7 for `theory.md`; Section 9 external surface to Tasks 13 and 15; Section 10 verification to Task 14. The three settled open items land in Task 9 (`decision-frame.md` narrowed), Task 5 and Task 11 (global-only writes), and Task 8 (P13 to P18 as examples).

**Placeholder scan.** No `TBD`, no "implement later", no "similar to Task N". Every markdown file that a task creates is given in full. The one place content is specified structurally rather than quoted whole is Task 14's eleven remaining eval cases, where case 1 is written out complete as the template and the other eleven each get their guard, stimulus, pass condition and fail condition in a table row. That is enough for an implementer to write each file without inventing requirements, which is the standard this rule exists to enforce.

**Type consistency.** Dimension ids `D1` to `D7`, lens ids `L1` to `L4`, gates `A1` to `A5` and `K1` to `K6`, patterns `P1` to `P18`, anti-patterns cited as `anti-pattern A1` to `A12` to disambiguate from the form gates. Script output keys `freshness_state`, `reason`, `index_baseline`, `repository_state`, `review_delta`, `changed_files`, `dirty_indexed_concepts`, `unmapped_changed_files` are used identically in Task 5 documentation, Task 6 implementation and tests, and Task 11 invocation. Freshness values `fresh`, `delta-stale`, `unusable` are consistent across Tasks 5, 6, 11 and 12. Report section letters A to I are defined once in Task 11 and referenced in Task 14.

**Known gap accepted.** Task 14 case stimuli describe codebases rather than shipping fixtures. Building twelve fixture repositories is a larger piece of work than the recentering itself, and the sibling harness at `evals/ai-tooling/` uses the same prose-stimulus approach. If the cases prove hard to run consistently, fixtures are a follow-up, not a blocker.
