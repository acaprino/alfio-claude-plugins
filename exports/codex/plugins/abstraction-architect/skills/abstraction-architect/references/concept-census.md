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
