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
