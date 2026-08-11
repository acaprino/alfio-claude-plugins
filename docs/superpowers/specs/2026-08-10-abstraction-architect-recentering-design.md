# abstraction-architect: recentering on structural entropy

**Status:** approved, implementation plan pending
**Date:** 2026-08-10
**Plugin:** `abstraction-architect` 1.1.6 to 2.0.0
**Marketplace:** 19.1.3 to 20.0.0

## 1. Problem

The plugin today is centered on a two-category question: missed unification versus wrong abstraction. That center is declared in the agent ROLE, in the skill description, in the report structure (sections A and B), and in the diff-mode taxonomy (classes R1 to R5). The center is too narrow for what the plugin should do, and the narrowness has a concrete mechanism rather than being a matter of taste.

Three defects, each verifiable in the current files.

**The theory and the process contradict each other.** `references/theory.md:25` states the correct principle: "The load-bearing word is *knowledge*. DRY targets duplicated knowledge, not duplicated lines of code", and gives the canonical example of a sales-tax rule appearing in a checkout page and an invoice generator with no textual duplication at all. `agents/abstraction-architect.md:49` then instructs the global process to look for "call sites that share a **structural shape**" and to match them against `references/unification-patterns.md`. The plugin knows the right thing in its theory and does the other thing in its process.

**The pattern catalog has no domain half.** The twelve unification patterns are SDK wrapper, schema validation, authorization, money, timezone, pagination, connection pool, logging, error envelope, feature flags, retry, observability. All twelve are infrastructural cross-cutting concerns. A business rule expressed three different ways has no pattern to match against, so it falls out of the report at step 3. This is the mechanism by which the theory defect actually bites.

**The evidence budget forbids the search.** `agents/abstraction-architect.md:14` restricts the agent to reasoning over `.deep-dive/` output and permits opening source files "only to verify a candidate finding's file:line citations". The four consumed deep-dive files inventory modules, interfaces, call graphs and responsibilities. None of them carries a census of concepts, which is what a claim like "this policy has three authoritative representations" requires.

A fourth issue is structural rather than defective: the Rule of Three is a hard gate in three places (`agents/abstraction-architect.md:189`, `references/decision-frame.md:18`, `references/theory.md:19`). It is the correct gate against extracting a shape prematurely. It is the wrong gate against knowledge having two authorities, because two competing authorities over the same fact is already the defect and waiting for a third is meaningless.

## 2. Identity and scope contract

The plugin becomes a reducer of structural entropy. The governing sentence, which goes into the agent ROLE:

> Where the same concept is represented, owned, computed or implemented more than once, and what it costs when that concept changes.

Two modes with different queries, not with different coverage:

| Mode | Question | Evidence source |
|---|---|---|
| `global` | What structural entropy **exists** in this codebase? | xray seed map plus the agent's own concept census |
| `diff` | Does this change **introduce or aggravate** entropy relative to the existing codebase? | diff as anchor, concept index, targeted search |

The plugin keeps the name `abstraction-architect`. Abstraction remains the central lens (D5, D6 and D7 are literally abstraction questions) and a rename would cost two spawn sites, the marketplace entry, the export directory, the docs and every installed plugin id, without buying proportionate clarity.

### Non-goals

A `Scope boundaries / Non-goals` section becomes part of the skill, naming each excluded dimension and its owner. Exclusions are written down rather than merely omitted, so that a future pass does not silently re-add them.

| Excluded | Owner | Permitted role here |
|---|---|---|
| Dependency structure (cycles, missed inversions, depth) | `senior-review:code-auditor`, `senior-review:chicken-egg-detector` | may appear as supporting evidence for D1 to D7, never as an autonomous finding |
| Responsibility cohesion inside a module | `senior-review:code-auditor` | two modules owning the same policy is evidence of D2, but "this class does too much" is not ours |
| API surface size and contract drift | `senior-review:api-contract-auditor`, `senior-review:cleanup-auditor` D4 | may appear incidentally in a D7 remediation, never as a category |
| Indirection cost | absorbed as lens L2 | contributes to D7, never opens a finding alone |
| Structural simplification | none, it is the goal | see the literal rule below |

The following sentence is written verbatim into the skill:

> Structural simplification is the desired outcome of the audit, not a finding category.

Without it, every D1 to D7 finding can be restated as a D8 "structural simplification opportunity" that carries no new information.

## 3. Classification model

### Dimensions

Seven dimensions. The track determines the **nature** of the evidence. The dimension determines the **gate**. Track membership does not by itself impose a cardinality, which is the single most common misreading to guard against.

| | Dimension | Track | Proof rule |
|---|---|---|---|
| D1 | Duplicated domain knowledge | B | same policy, formula or invariant; N greater than or equal to 2; the representations must stay consistent |
| D2 | Competing sources of truth | B | same fact; two or more authoritative writers or definitions; canonical owner absent or ambiguous |
| D3 | Redundant representation | B | same concept; parallel representations; real mapping or synchronization cost |
| D4 | Duplicated or derivable state | B | derivable but maintained separately, plus evidence of sync, invalidation or repair code |
| D5 | Missed unification | A | mechanism independently repeated three or more times; Rule of Three |
| D6 | Prior art available | A | a clearly canonical implementation exists and something else reimplements or bypasses it |
| D7 | Abstraction fitness | A | proven internal friction: flags, per-caller exceptions, caller bypass, leakage |

Only D5 uses the Rule of Three as a strict gate. The rule returns to its original meaning: a gate that justifies **creating a new unification**, not a universal filter for the form family. D6 needs a canonical owner plus one reimplementation. D7 needs friction inside a single abstraction and no count at all.

D5 and D6 are adjacent and distinct, and the distinction changes the remediation:

```
D5 = the codebase is asking for an abstraction, because the mechanism recurs.
     Remediation: design or consolidate.

D6 = the abstraction already exists, and part of the codebase does not use it.
     Remediation: reuse, migrate to the canonical.
```

### Lenses

Four lenses. A lens is applied to every candidate of every dimension, is reported as a field of the finding, and never becomes a category of its own.

- **L1 Change amplification.** If this concept changes, how many places must change together? This is the primary yardstick and it is already `references/theory.md:95`.
- **L2 Indirection cost, Locality of Behaviour.** Would consolidating actually reduce cognitive cost, or only add another hop? Guards against false remedies.
- **L3 Bounded context.** A hard gate on track B. On track A it is an important lens but not an absolute gate, because two contextually separate implementations may still legitimately share an infrastructural mechanism.
- **L4 Option price, Tidy First.** Does the benefit justify the abstraction today, or is deliberate duplication cheaper? This is what keeps the plugin from being refactor-happy.

### Track gates

**Track A, form.**

```
A1 Same structural responsibility?
A2 Same lifecycle and boundary?
A3 Occurrences per the dimension's own rule (three for D5, not for D6 and D7)
A4 Would one shared abstraction reduce change cost?
A5 Is the divergence unlikely to be intentional?
```

**Track B, knowledge.**

```
K1 Same semantic fact?
K2 Same domain meaning?
K3 Same lifecycle?
K4 Same authority scope?
K5 If the fact changes, are both expected to remain consistent?
K6 Is there no legitimate bounded-context reason for divergence?
```

The discriminating question for track B, stated in the agent and in the reference:

> **Can these representations legitimately disagree?**

If yes, this is not duplicated knowledge, whatever the surface similarity. If no, and they must stay consistent, N equal to 2 is sufficient evidence.

The worked contrast that goes into the reference:

```
Billing.REFUND_DAYS = 30            Shipping.Status: PENDING/COMPLETE/FAILED
Support.refundAllowed = age <= 30   Payment.Status:  PENDING/COMPLETE/FAILED

Can they legitimately disagree?     Can they legitimately disagree?
No. Same knowledge, two owners.     Yes. Same shape, different knowledge.
FINDING (D1 or D2).                 NO FINDING.
```

### Single primary classification

One defect gets one primary dimension. A refund window duplicated in three places with one apparently canonical site could be read simultaneously as D1, D2, D5 and D6. Four findings for one defect is a report bug.

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

The rule in one line: **report the deepest architectural reason, and record the others as supporting evidence or lens values rather than duplicate findings.** If three implementations of a refund policy exist because three modules each consider themselves authoritative, the important finding is D2 (nobody owns the policy), not D5 (we could extract a helper). The second answer is the wrong one and it is what a conventional DRY detector would produce.

### Occurrences are evidence, never severity

No mapping of the form 2 equals Low, 3 equals Medium, 4 equals High. Two independent authoritative permission policies can be High on two occurrences. Two duplicated formatting constants can be Low on four. Severity follows consequence, using the existing calibration in `references/decision-frame.md` (security, data correctness, operational risk for High; maintenance drag for Medium; smell without pressure for Low). Occurrence count is reported as evidence strength.

### The catalogs are not admission gates

The original defect analysed in Section 1 was not that the twelve unification patterns were infrastructural. It was that an infrastructural catalog, consulted as a matching step, silently became the boundary of what could be found. Adding six domain patterns fixes the coverage and reproduces the mechanism at a larger size unless the mechanism itself is addressed.

The following sentence is written verbatim into `unification-patterns.md` and `anti-patterns.md`:

> Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding.

Operationally: a candidate that passes its dimension's gate is a finding whether or not it matches a catalogued pattern. When it matches, the finding cites the pattern. When it does not, the finding names the concern in its own words and the `Pattern` field reads `uncatalogued`. A strange semantic policy that fits none of P1 to P18 must not disappear from the report a second time.

## 4. Pipelines

### Global audit

```
0  load deep-dive        01-structure, 02-interfaces, 03-flows, 04-semantics
                         [, 08-interconnect-map when present]
1  seed map              modules, responsibilities, entities, services, persistence,
                         configuration, boundaries, principal flows, public interfaces
2  concept extraction    domain nouns (Customer, Order, Payment, Subscription, Permission,
                         Refund, Price, Status, Tenant, Feature) AND behavioural concepts
                         (eligibility, approval, normalization, calculation, expiration,
                         validation, mapping, defaulting, derivation)
3  discovery             HIGH RECALL: Glob and Grep over names, symbols, literals,
                         thresholds, fields, types, enums, mappings, configuration
                         -> Concept Evidence Index
4  hypothesis testing    per concept: assign track, run the dimension gate, apply lenses
5  report                HIGH PRECISION: proven findings only, plus the persisted index
```

Step 2 is seeded by step 1 deliberately. The census must not begin by sweeping eighty thousand files at random; the seed map tells it where the territory is. Step 3 then searches for representations of those concepts rather than for identical names. For a `subscription status` concept the candidates include `SubscriptionStatus`, `subscription_state`, `isActive`, `enabled`, `expiresAt > now`, `plan_status`, `ACTIVE = "active"`. Whether they are the same knowledge is decided in step 4, never in step 3.

### Diff review

```
0  resolve diff and      STRUCTURAL units: functions, methods, classes, modules,
   extract changed       constant tables, inline blocks longer than roughly five lines
   units                 SEMANTIC units: new or modified rules and policies, predicates
                         and thresholds, persisted fields and state, models, DTOs, types
                         and enums, mappings, configuration and defaults, formulas and
                         transformations
1  load index            plus freshness check (script)
2  map                   changed files and symbols -> indexed concepts, marked dirty
3  discover              concepts NEW to the index, introduced by this diff
4  revalidate            re-read the neighbourhood of dirty concepts against current source
5  test D1-D7            each reformulated as "introduced or aggravated by this change"
6  report                new concepts and index contradictions go to Gaps, never to the
                         index: diff mode does not write it in 2.0
```

Step 0 extracts two kinds of unit, and the second kind is the load-bearing addition. Extracting structural units alone is the current model, and under it a diff that changes a threshold from 1000 to 1500, adds a field to a persisted model, or introduces a new status enum produces no unit at all. D1 to D4 would then be unable to form the hypothesis in the first place, and the recentering would be strong in global mode while diff mode stayed where it is. A changed literal inside an existing function is a semantic unit even when no structural unit changed.

All seven dimensions mirror into diff mode, including D5. In diff mode D5 is the current R3 class, "this diff is the third occurrence and the Rule of Three fires now, on this commit", and it is the only moment at which the Rule of Three can be applied in real time rather than retrospectively. It is among the most useful outputs the plugin produces inside a code review and it is not dropped.

The diff questions, stated as the reformulation:

| Global | Diff |
|---|---|
| D1 Is this policy duplicated? | Does this diff add another representation of an existing policy? |
| D2 Who owns this fact? | Does this diff create a second authority over an existing fact? |
| D3 Are these representations redundant? | Does this diff add a parallel representation of an existing concept? |
| D4 Is this state derivable? | Does this diff store something already derivable from existing state? |
| D5 Is this mechanism repeated? | Is this diff the third occurrence? |
| D6 Does a canonical exist? | Was this already available? |
| D7 Is this abstraction fighting its callers? | Does this diff introduce or worsen abstraction friction? |

### The rule that governs both

Written literally into the agent, because it is the core of the design:

> `precision over recall` governs what is **reported**, not what is **searched**.

Discovery is deliberately liberal. Promotion to a finding is deliberately strict. The current agent conflates the two and pays for it by not searching at all.

## 5. Artifacts and the concept index

```
.abstraction-architect/
  concept-index.json      machine-readable contract, the only artifact consumed as input
  findings.md             global report
  findings-diff.md        diff report
```

No twin Markdown copy of the index. The report is the human-readable layer; duplicating the index in prose creates two truths that drift.

**Only global mode writes `concept-index.json`, in 2.0.** Diff mode reads it and never updates it. Concepts the diff discovers and contradictions it finds are reported in Gaps, and the next global audit consolidates them. The reason is that a diff run sees one change against a partial revalidation, so letting it write would let a narrow view overwrite a broad one, and would make the index's provenance depend on whichever review ran last. Making diff mode a writer is a candidate for a later version, once the global writer has proven stable.

### Schema

```yaml
schema_version: 1
generated_from_commit: abc123
generated_from_tree: 9f48...
generated_at: 2026-08-10T12:00:00Z   # informational, never a gate
scope: "."
concepts:
  - concept: Refund eligibility
    kind: policy
    representations:
      - symbol: RefundPolicy.can_refund
        file: domain/refund_policy.py
        role: candidate_owner
      - symbol: SupportRefundService.is_eligible
        file: support/refunds.py
        role: implementation
      - symbol: REFUND_WINDOW_DAYS
        file: config/refunds.py
        role: parameter
    writers: [RefundPolicy, AdminRefundSettings]
    consumers: [checkout, support-api]
    canonical_owner:
      status: ambiguous
    evidence:
      - same 30-day policy confirmed in three contexts
      - support implementation bypasses RefundPolicy
```

### Three distinct notions of "what changed"

Freshness and review scope are not the same question, and collapsing them produces false freshness. Three separate things must be tracked:

```
INDEX BASELINE      the commit and tree the concept index was generated from
REPOSITORY STATE    HEAD plus staged plus working tree, as it exists right now
REVIEW DELTA        the change actually under review (base branch to HEAD, a PR range,
                    uncommitted work, or an explicit changed-files list)
```

A comparison of `baseline..HEAD` alone answers none of them completely. The hazard it misses is common and silent: the indexed tree can equal the HEAD tree while uncommitted local modifications are exactly what is under review, which reports **fresh** for an index that does not describe the code being judged. Staged-only work has the same shape.

The script therefore accepts the review delta as an input rather than inferring it:

- `--base <ref> --head <ref>` for a branch or PR range
- `--working-tree` to include staged and unstaged changes in the repository state
- `--changed-files <path>` for an explicit list, which is how `senior-review` already passes scope

Freshness is computed against the **repository state**. The revalidation set is computed from the **union of the index-to-repository drift and the review delta**, because a concept can need revalidation either because the index is behind or because the review touches it.

### Freshness states

Three states, computed from the **tree hash** and not from the date. A date is not a validity criterion: an index from yesterday can be perfectly valid and one from thirty seconds ago can be stale after a commit. Two different commits with the same tree do not make the index semantically stale.

- **fresh.** The indexed tree hash matches the current one for the same `scope` recorded in the index. When `scope` is a subpath, the comparison uses that subtree, so changes outside the audited scope do not invalidate the index.
- **delta-stale, revalidatable.** The baseline is reachable and the delta is computable. This is the normal case and the one to optimise: load the index, compute which files changed, mark the concepts attached to them dirty, revalidate those neighbourhoods, and treat the rest as seed.
- **unusable.** Baseline unreachable, history rewritten, incompatible schema, different scope, corrupt index, or delta not determinable. Degrade.

Freshness is never binary. Discarding the whole index on any HEAD movement would throw away most of the benefit.

### Epistemic status of the index

Written literally into the agent and into the reference:

> **Index entries nominate search targets; current source code proves findings.**

No D1 to D4 finding is promoted without re-reading the involved representations against current source. The index accelerates discovery and coverage. It is never the proof.

## 6. Epistemic independence conformance

This design introduces a new shared artifact into a pipeline, which is the exact object class governed by the standing doctrine in `docs/superpowers/specs/2026-08-10-review-pipeline-epistemic-independence-design.md`:

> Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.

The doctrine prescribes three checks before adding capability. This design answers all three explicitly rather than leaving them to improvisation.

**Check 1: is any shared artifact consumed as settled fact?** No, and the epistemic status is declared rather than implied. The index carries the "nominate, never prove" rule in Section 5, and the diff-mode prompt states it too. Two artifacts are consumed, and both get a declared status: `.deep-dive/` is a **seed map** whose completeness is not assumed, and `concept-index.json` is a **discovery accelerator** whose entries are hypotheses.

**Check 2: does any metric reward agreement with the shared artifact?** No, and this is stated as a prohibition. No score, no coverage percentage and no quality gate may reward index utilisation, seed-map utilisation or citation of either. The doctrine records that `review-quality-gates` context utilization rate was exactly this failure mode, rewarding correlation instead of quality. The Gaps section reports coverage as counts of what was examined, never as a ratio of agreement.

**Check 3: can a downstream consumer contradict the upstream artifact?** Yes, and it is a written duty rather than a permission. Three concrete obligations:

- **Duty of autonomous rediscovery.** Diff-mode step 3 discovers concepts the index does not contain, and it runs on the changed area whether or not the index covers it. There is no rule of the form "do not search where the index says nothing", because that rule is what makes a gap-reporting mechanism unreachable.
- **Contradiction is a reportable outcome.** When revalidation finds that the index is wrong (the recorded canonical owner no longer holds, a representation is gone, a `canonical_owner.status` of `settled` is in fact ambiguous), the agent reports the contradiction in Gaps and corrects the index on write. It does not silently prefer either source.
- **The seed map's completeness is not a premise.** Concept extraction starts from the seed map and is not limited by it. A module xray did not surface is a gap in the census, and the census may add concepts that the seed map never named.

One consequence for the eval layer: a case asserting that the agent can contradict its own index is worth more than a case asserting that it uses it.

## 7. Degradation

The index is never a prerequisite for correctness. Every path has a declared degradation, and Gaps reports numbers rather than adjectives.

| Condition | Behaviour |
|---|---|
| `.deep-dive/` missing in global mode | auto-launch `/codebase-xray:analyze`, as today |
| `.deep-dive/` partial | proceed, list missing files in Gaps with the analyses they would have enabled |
| index missing in diff mode | diff-anchored discovery; Gaps states that global competing-authority coverage was not attempted |
| index unusable | same, naming the specific condition that made it unusable |
| not a git repository | freshness not computable, index treated as unusable |
| script fails or Python unavailable | conservative fallback to unusable, never to an assumed fresh |
| `--scope` does not intersect the index | no seed, full discovery within the scope |

A conforming Gaps block:

```
Concept index baseline: a13fe2      Current HEAD: 92ac10
Delta determined: yes               Indexed concepts revalidated: 4
Unindexed changed concepts discovered: 2
```

Or, in the degraded case:

```
Concept index unavailable.
Knowledge-track coverage used diff-anchored discovery only;
global competing-authority coverage was not attempted.
```

### Finding auditability block

Every finding carries the block that makes the admission decision readable:

```
Evidence track: KNOWLEDGE            Evidence track: FORM
Semantic identity: proven            Occurrences: 4
Occurrences: 2                       Independent implementations: yes
Must remain consistent: yes          Shared lifecycle: yes
Bounded-context exception: none      Rule of Three: satisfied
Canonical owner: ambiguous           Index-seeded: no
```

A reader can see not only what was found but why it was allowed into the report.

## 8. File layout

```
plugins/abstraction-architect/
  agents/abstraction-architect.md       ~280   orchestrator plus report templates
  commands/audit.md                     ~110   index flags added
  skills/abstraction-architect/
    SKILL.md                             ~80   reference index plus the two-track rule
    references/
      theory.md                       103 ->   adds the form versus knowledge section
      dimensions.md                      NEW   D1-D7, L1-L4, classification precedence
      evidence-tracks.md                 NEW   tracks A and B, gates A1-A5 and K1-K6
      concept-census.md                  NEW   seed map to concepts to discovery searches
      concept-index-protocol.md          NEW   schema, three freshness states, revalidation
      unification-patterns.md         222 ->   adds domain patterns P13-P18
      anti-patterns.md                   151   unchanged
      decision-frame.md                 47 ->   narrowed to promotion, severity, remediation
      scope-boundaries.md                NEW   the five exclusions with owners, non-goals
      further-reading.md                  95   unchanged
    scripts/
      concept_index.py                   NEW   schema validation, freshness, delta mapping
```

The agent stays an orchestrator and holds no catalog content: inputs, the pipeline phases, the output contract, the constraints. Content lives in references loaded on demand.

`concept_index.py` exists because freshness and delta computation are deterministic work that a language model does badly. The division of labour is a hard line, and the script's output contract is what enforces it:

```
SCRIPT (deterministic, Python)          AGENT (semantic, model)
  freshness_state                         semantic discovery over
  index_baseline / repository_state         unmapped_changed_files
  review_delta                            new concepts
  changed_files                           semantic neighbourhood of
  dirty_indexed_concepts                    dirty_indexed_concepts
  unmapped_changed_files                  every promotion to a finding
```

`unmapped_changed_files` is the field that keeps the duty of autonomous rediscovery mechanical rather than aspirational: it is the explicit list of changed files that no indexed concept claims, handed to the agent as work to do. Without it, "discover concepts the index does not contain" is an instruction that quietly evaporates on a busy run.

**The script never discovers concepts.** It validates the schema, resolves the three notions of change above, intersects the delta with indexed file paths, and emits the partition. Every semantic judgement, including whether two representations are the same knowledge, belongs to the agent.

It must be invoked through `${CLAUDE_PLUGIN_ROOT}/skills/abstraction-architect/scripts/concept_index.py`, since a `plugins/...` path fails for installed users and `scripts/lint_bundled_paths.py` rejects it in CI.

New domain patterns P13 to P18 for `unification-patterns.md`, covering the half the catalog currently lacks: business rule or policy threshold, eligibility predicate, state machine transition table, pricing or discount computation, identifier and code format, and status or lifecycle vocabulary. They are written as **general semantic examples, not as a closed taxonomy**, and the file carries the non-exhaustiveness rule stated in Section 3. The six are deliberately broad rather than specific, so that they read as illustrations of a kind of concern rather than as an enumeration of the concerns that exist.

`decision-frame.md` survives as a file and narrows to what it alone owns: promotion, severity calibration and remediation framing. It does not restate A1 to A5 or K1 to K6, which live in `evidence-tracks.md`. This settles the open item recorded in the first draft of this spec.

## 9. External surface

Four touch points outside the plugin.

**Spawn sites.** `plugins/senior-review/commands/team-review.md:303-309` and `plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md:636-641` gain one input line, `concept_index_path`. The `subagent_type` does not change, so `code-review.md:239` row J and the skip-if-not-installed handling stay as they are.

**Boundary note.** `plugins/senior-review/agents/code-auditor.md:95` is reworded. The existing discriminator (smells visible inside one file versus the cross-file question) already holds and does not need renegotiating. The single addition: abstraction friction proven by **external caller bypass** is D7 and belongs to abstraction-architect, while a god function or a one-implementation interface visible within the file under review stays with the Abstraction Inspector.

**Marketplace.** `abstraction-architect` 1.1.6 to 2.0.0, `metadata.version` 19.1.3 to 20.0.0, plugin description rewritten around structural entropy, keywords extended (`structural-entropy`, `source-of-truth`, `semantic-duplication`, `derivable-state`).

**Export mirror.** `exports/vscode/_pipelines/.github/agents/review-abstraction-architect.agent.md` and `exports/vscode/_pipelines/.github/skills/abstraction-architect/`. No new agent is contributed, so `gen_extension_manifest.py` produces no contribution changes and `exports/vscode/package.json` needs no version bump on that account. The `downstream-exports` skill governs the adaptations, and `check_export.py` verifies the result.

## 10. Verification

`evals/abstraction-architect/`, following the `evals/ai-tooling/` shape: thirteen behavioural invariants rather than recall against ground-truth bugs, because what this redesign risks losing is a philosophy, not a bug list. Assertions target the philosophy and never the wording. A case that fails once keeps its case forever.

Initial cases:

1. The Rule of Three is never applied as a universal gate to track A. D6 and D7 remain provable without three occurrences.
2. A track B finding with N equal to 2 is admitted only after the bounded-context gate K6.
3. Occurrence count never determines severity.
4. The same defect never appears under two dimensions.
5. The concept index is never the sole evidence for a finding.
6. Discovery stays high-recall even when the report ends up empty.
7. None of the five excluded dimensions produces an autonomous finding.
8. A missing index does not block diff mode.
9. The agent can contradict its own index and reports the contradiction rather than silently preferring one source.
10. No metric, score or gate rewards agreement with the index or with the seed map.
11. A diff that changes only a threshold, a persisted field or an enum value, with no structural unit added, still produces a semantic unit and a testable hypothesis.
12. A concern that matches none of P1 to P18 still becomes a finding when its dimension gate passes, reported with `Pattern: uncatalogued`.
13. Canonical ownership is assignable per decision, not only per file. Two specifications that each own one fact of the same contract correctly resolve to a D2 with split ownership, never to one source declared authoritative in full and never by ranking the sources.

Cases 9 and 10 come from the epistemic-independence doctrine. Cases 11 and 12 guard the two mechanisms this redesign exists to break: a diff extractor that only sees code shapes, and a catalog that quietly becomes the boundary of the findable. All four are the ones that decay first under a well-meaning future edit.

## 11. Decisions taken, and what was rejected

| Decision | Rejected alternative | Why |
|---|---|---|
| Global is the primary product, diff mirrors it | Forcing all dimensions into a diff-anchored reviewer | Several dimensions are not approximable from a diff; designing around senior-review's limits would cost the plugin its identity |
| Hybrid evidence: xray seed plus own census | A `09-concepts.md` phase inside codebase-xray | It would move the complexity rather than remove it, and would make xray aware of one consumer's needs. Promote later if two or three consumers need it, which is the Rule of Three applied to marketplace design |
| Hybrid evidence | Freeing the agent from deep-dive entirely | Cost, non-determinism, order-dependent coverage, and it would remove the reason codebase-xray is a hard dependency |
| Two evidence tracks, per-dimension gates | Rule of Three everywhere | Would demote to noise exactly the findings this recentering exists to produce |
| Two evidence tracks | A single change-amplification gate | Simpler, but discards a calibration that currently works and invites false positives on the form dimensions |
| Persisted index with three-state freshness | Ephemeral in-run index | The diff mode would stay weak precisely on the knowledge dimensions, since rebuilding the census per review is not sustainable |
| Persisted index | Persisted but human-only, consumed by nothing | Gives up the strongest link between the two modes for no real saving |
| Seven dimensions plus four lenses | Nine dimensions including dependency structure and API surface | Would require rewriting the boundary in two senior-review agents and would produce overlapping findings inside one review |
| Seven dimensions | Six, dropping D6 from global | D5 and D6 are different failure modes with different remediations: design a new abstraction versus migrate to the existing one |
| One agent, orchestrator plus references | Two agents, global and diff | The catalogs must serve both anyway, so the reference library is the same size, and the split would add a marketplace entry, two spawn-site rewrites and a manifest change |
| One agent | Monolith of roughly 700 lines | Starts at the repo's stated ceiling for complex agents with no room to grow |
| Keep the name | Rename to reflect the new identity | Abstraction is still the central lens; a rename costs spawn sites, marketplace entry, export directory, docs and installed ids |

## 12. Open items for the implementation plan

Three items open in the first draft are now settled and recorded in the sections above: `decision-frame.md` survives, narrowed to promotion, severity and remediation (Section 8); only global mode writes the index in 2.0 (Section 5); P13 to P18 ship as general semantic examples under an explicit non-exhaustiveness rule (Sections 3 and 8). What remains:

- Exact wording of the P13 to P18 domain patterns, following the existing five-part shape of P1 to P12 (structural signature, forces, target layer, pitfalls, retrospective indicator), kept deliberately broad per Section 3.
- The precise `--changed-files` input format for `concept_index.py`, which must match what `senior-review` already passes to the agent so the two do not diverge.
- The eval harness needs a target codebase. `D:\Projects\jupiter` is the standing proving ground for this marketplace and is a plausible fixture source.
- **Ownership granularity in the concept index.** The schema gives each concept a single `canonical_owner`. A concept that bundles several independent decisions can have a different rightful owner per decision, and one owner field cannot express that. A real instance arose while building this plugin: two documents both described the `concept_index.py` `validate` command, one owning the output format correctly and the other owning the required schema fields correctly, and the right resolution assigned ownership per decision rather than declaring either document authoritative in full. The schema is deliberately **not** widened for 2.0, because a `facts[]` list under each concept is speculative until a second instance appears. What 2.0 does carry is the behaviour: eval case 13 asserts that the agent resolves this shape as D2 with per-decision ownership, and never by a source-ranking heuristic. If per-decision ownership recurs in real audits, that is the evidence that justifies the schema change, and it is the same Rule of Three this plugin applies to everything else.
- Commit shape. The marketplace workflow requires the plugin files, `marketplace.json` and the `exports/` mirror in a single commit. `evals/` is a development asset and is not registered in `marketplace.json`, so the eval layer can ship as a second commit without breaking `scripts/check_version_bumps.py`. The plan should decide whether to split.
