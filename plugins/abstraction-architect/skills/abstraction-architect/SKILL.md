---
name: abstraction-architect
description: >
  Knowledge base for pure-architecture decisions on when to unify duplicated logic into a shared abstraction versus leave it duplicated. Covers the canonical theory (Rule of Three, DRY/WET/AHA, Wrong Abstraction, Locality of Behaviour, Bounded Contexts, Tidy First options framing, CUPID vs SOLID), 12 essential-duplication patterns that justify unification, 12 wrong-abstraction patterns that justify inlining or decomposition, an operational decision frame, and a verified reading list.
  TRIGGER WHEN: the user is making an architectural decision about whether to centralize, extract, or remove a layer; reviewing an abstraction for premature generality; auditing scattered cross-cutting concerns; spawned by the abstraction-architect agent during /abstraction-architect:audit or as the Abstraction dimension of /agent-teams:team-review or /senior-review:code-review; the user asks "should I extract this into a service" / "is this DRY enough" / "is this wrong abstraction".
  DO NOT TRIGGER WHEN: the task is code formatting and readability cleanup (use clean-code:clean-code), Python-specific refactoring with metrics (use python-development:python-refactor), generic dead-code removal (use senior-review:cleanup-dead-code), security review (use senior-review:security-auditor), or pure pattern-consistency review without an architecture lens (use senior-review:code-auditor).
---

# Abstraction Architect Knowledge Base

This skill gives Claude the conceptual frame for the *pure-architecture* question: when does duplicated logic want to be unified into a layer, and when does an existing layer want to be inlined or decomposed?

Two opposite failure modes coexist in real codebases. Both have well-documented theory:

- **Missed unification.** A cross-cutting concern is duplicated across many call sites. Each site is local-looking but they form a single concern that wants to change together. Drift between sites becomes the source of bugs, security holes, or fiscal errors.
- **Wrong abstraction.** An existing shared layer is fighting its callers. Every new feature adds a flag, branch, or parameter to it. The layer should be inlined back to duplication so the real pattern can emerge later.

The skill exists because both failures look superficially like "the right thing": missed unification is hidden under "we already have similar code elsewhere", and wrong abstraction is defended by "but we DRY'd this last quarter".

## When to use this skill

Load this skill when:

- Deciding whether to extract three similar functions into a shared layer
- Evaluating whether an existing abstraction is paying for itself
- Auditing a codebase for missed unification or wrong abstraction (`/abstraction-architect:audit` spawns the auditor agent which loads this skill)
- Onboarding teammates to the canonical literature on the abstraction-vs-duplication question

Do not load this skill for:

- Style and readability fixes (use `clean-code:clean-code`)
- Python-specific complexity reduction (use `python-development:python-refactor`)
- Dead-code removal (use `senior-review:cleanup-dead-code`)
- Security and authorization review (use `senior-review:security-auditor`)
- Generic code review (use `senior-review:code-auditor`)

## Reference index

Load references on demand, not all up front. Each file is focused on one dimension of the problem.

- **`references/theory.md`** — the principles: Rule of Three, DRY/WET/AHA, Wrong Abstraction, Locality of Behaviour, Bounded Contexts, Tidy First options framing, CUPID vs SOLID. Read this first when the user asks "why does this matter".
- **`references/unification-patterns.md`** — 12 canonical *essential duplication* cases. Read when scanning a codebase for missed unification or when the user asks "should this be a service".
- **`references/anti-patterns.md`** — 12 canonical *wrong abstraction* cases. Read when reviewing an existing shared layer or when the user asks "is this a god service".
- **`references/decision-frame.md`** — the operational classifier with pre-flight questions and severity calibration. Read when promoting a candidate to a finding or deciding whether the gate has been cleared.
- **`references/further-reading.md`** — verified URL list (Metz, Beck, Dodds, Abramov, Gross, North, Acton, Italian-language DDD canon). Read when the user asks for resources or when citing a position in a report.

## The single rule of thumb

When the concern changes, where do you have to touch?

- If N grows linearly with features, the concern is a unification candidate.
- If every new requirement adds a flag, branch, or parameter to a shared layer, that layer is a wrong abstraction.

This question subsumes most of the principles in `theory.md` and is the load-bearing classifier the auditor agent applies.
