# abstraction-architect Plugin Implementation Plan

> **For agentic workers:** Use subagent-driven execution (if subagents available) or ai-tooling:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new marketplace plugin `abstraction-architect` that audits a codebase for missed unification opportunities and wrong abstractions, reasoning over `.deep-dive/` output. One skill (5 reference files + SKILL.md), one auditor agent, one command with auto-launched deep-dive, marketplace registration, CLAUDE.md plugin-count update.

**Architecture:** Single-agent + 1 command + knowledge-base skill (same shape as `clean-code` with the skill addition of `pwa-expert`). All content is markdown. No build step, no runtime, no tests beyond markdown structural checks and `marketplace.json` JSON validation.

**Tech Stack:** Markdown only. YAML frontmatter. Plugin registered in `.claude-plugin/marketplace.json` with `dependencies: ["deep-dive-analysis"]`.

**Source spec:** `docs/plans/2026-05-25-abstraction-architect-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| `plugins/abstraction-architect/skills/abstraction-architect/SKILL.md` | Knowledge-base entry point with TRIGGER WHEN / DO NOT TRIGGER WHEN and reference index |
| `plugins/abstraction-architect/skills/abstraction-architect/references/theory.md` | Rule of Three, DRY/WET/AHA, Wrong Abstraction, Locality of Behaviour, Bounded Contexts, Tidy First options framing, CUPID vs SOLID |
| `plugins/abstraction-architect/skills/abstraction-architect/references/unification-patterns.md` | 12 canonical "essential duplication" cases that justify unification |
| `plugins/abstraction-architect/skills/abstraction-architect/references/anti-patterns.md` | 12 canonical "wrong abstraction" cases that justify inlining or decomposition |
| `plugins/abstraction-architect/skills/abstraction-architect/references/decision-frame.md` | Operational classifier with pre-flight questions and runtime severity rules |
| `plugins/abstraction-architect/skills/abstraction-architect/references/further-reading.md` | Verified URL list grouped by canonical / war stories / recent / Italian / books / talks |
| `plugins/abstraction-architect/agents/abstraction-architect.md` | Auditor agent — frontmatter + system-prompt body that reads deep-dive output, loads the skill, produces findings |
| `plugins/abstraction-architect/commands/audit.md` | Slash command `/abstraction-architect:audit` with auto-launched deep-dive |
| `.claude-plugin/marketplace.json` | Plugin registration with `dependencies: ["deep-dive-analysis"]`, bump `metadata.version` to `6.23.0`, fix stale `metadata.description` plugin count (43→45 since pwa-expert raised it to 44 and this raises it to 45) |
| `CLAUDE.md` | Plugin count 44→45, add `abstraction-architect` to the plugin list, add Moderate freshness-class row in the custom-plugin maintenance section |

---

## Universal verification snippet

Every file-creation task ends with this verification (saves repetition):

```bash
FILE="plugins/abstraction-architect/<path>"
wc -l "$FILE"

# Check for forbidden dash-aside construct (em dash, double hyphen, spaced hyphen as parenthetical asides)
grep -nE ' — | -- ' "$FILE" | head -20
grep -nE ' - [A-Z]' "$FILE" | head -20

# Check for emojis (rough Unicode range)
grep -nP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' "$FILE" | head -5

# Verify no Italian leftovers (common giveaway words). Plugin content must be English.
grep -niE '\b(che|della|dello|delle|degli|sono|essere|questo|questa|quando|perché|anche|tutto|tutta|tutti|abbiamo|hanno)\b' "$FILE" | head -5
```

If any of those greps return content (other than legitimate hyphenated compounds like `file-handlers`, `cross-cutting`, or list-item dashes at line start), fix the file before moving on.

Frontmatter validation for skill/agent/command files:

```bash
# YAML frontmatter must parse and have required fields
python3 -c "
import sys, yaml
with open('$FILE') as f:
    text = f.read()
if not text.startswith('---'):
    sys.exit('Missing frontmatter')
parts = text.split('---', 2)
fm = yaml.safe_load(parts[1])
required = ['name', 'description']
for k in required:
    if k not in fm:
        sys.exit(f'Missing required field: {k}')
print('Frontmatter OK:', fm.get('name'))
"
```

---

## Task ordering rationale

Reference files first (the agent and command depend on them being indexable). Within references: theory before patterns (patterns cite theory); decision-frame after patterns (uses pattern names); further-reading last (verified URLs already collected from the deep-research pass).

Then orchestration files (SKILL.md indexes references, agent calls SKILL.md, command calls agent).

Then marketplace registration as the single integration point.

Single final commit (project convention from CLAUDE.md: "stage both the plugin files and `marketplace.json` in one commit").

---

### Task 1: Create plugin skeleton and theory.md

**Why first:** the directory tree must exist before any file. Theory is foundational and used by every other reference.

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/theory.md`

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p plugins/abstraction-architect/agents
mkdir -p plugins/abstraction-architect/commands
mkdir -p plugins/abstraction-architect/skills/abstraction-architect/references
```

- [ ] **Step 2: Write theory.md**

Cover seven principles. Each principle: title + 2 paragraphs maximum + one-line operational rule at the end. Strict word budget: target 600-900 lines total.

Principles to cover (in this order):

1. **Rule of Three** — Origin: Don Roberts and Ralph Johnson, "Evolving Frameworks" (1996), popularized by Martin Fowler in *Refactoring*. Two similar pieces of code may diverge later under different requirements; three indicates a real pattern. The rule is a *gate* against premature abstraction, not a quota for refactoring.
2. **DRY** — Hunt and Thomas, *The Pragmatic Programmer* (1999). DRY targets duplicated *knowledge*, not duplicated *lines*. Misreading it as "no two lines should look alike" is the most common source of wrong abstractions.
3. **WET / AHA** — Kent C. Dodds, "AHA Programming" (2020). *Avoid Hasty Abstractions*. Frames the choice as: prefer two clear duplicates over one unclear abstraction; let the third occurrence reveal the true shape.
4. **The Wrong Abstraction** — Sandi Metz, "All the Little Things" (RailsConf 2014) and the 2016 blog post. Load-bearing claim: duplication is *far cheaper* than the wrong abstraction. Escape route: re-inline the abstraction back to duplication and let the real pattern emerge.
5. **Locality of Behaviour** — Carson Gross (htmx.org, 2020). Counter-force to DRY: if unifying code forces a reader to chase definitions across files, the abstraction has a hidden cognitive cost that may outweigh the deduplication.
6. **Bounded Contexts** — Eric Evans, *Domain-Driven Design* (2003), and Martin Fowler's bliki entry. Two domains may share a concept name (`Customer`, `Order`, `User`) but should keep separate models. Bounded contexts are the seam for *what NOT to unify even when it looks identical*.
7. **Tidy First options framing** — Kent Beck, *Tidy First?* (2024). An abstraction is a financial option: it has an upfront cost (coupling, indirection, mental overhead) and a future value (cheap change when the option pays off). Both must be estimated before paying the cost.
8. **CUPID vs SOLID** — Dan North, "CUPID for joyful coding" (2022). SOLID is a binary checklist; CUPID is a set of continuous properties. For abstraction decisions, the CUPID lens ("how composable, predictable, idiomatic is this layer?") works better than the SOLID lens ("does it satisfy the Open/Closed Principle?").

End the file with a section "The single rule of thumb" containing one paragraph: *when X changes, where do I have to touch? if N grows with features, candidate for unification; if every new requirement adds a flag, branch, or parameter to a shared layer, that layer is a wrong abstraction.*

- [ ] **Step 3: Verify**

Run the universal verification snippet against the file.

---

### Task 2: Write unification-patterns.md

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/unification-patterns.md`

- [ ] **Step 1: Write the file**

File header:

```markdown
# Essential Duplication Patterns

Twelve canonical cases where centralizing duplicated logic into a unified layer is the right move. Each pattern is *essential duplication*: the duplicated sites share a single concern that must change together. Leaving them duplicated guarantees drift, security gaps, or data-correctness bugs.

For each pattern: structural signature (what the duplicated code looks like), why unification is right (which forces want it to change together), the suggested target layer, common pitfalls when implementing the unification.

The Rule of Three (see `theory.md`) still applies: do not promote a pattern with fewer than three call sites. Two may diverge; three signals a real shape.

---
```

Then one section per pattern, in this order. Each section uses this template:

```markdown
## P<N>. <Pattern name>

**Structural signature:** <what the duplication looks like in code>

**Forces that want this to change together:** <which concerns are coupled — e.g. auth, retry, cost tracking, vendor switching>

**Suggested target layer:** <e.g. `LLMService`, `MoneyArithmetic`, `AuthGate`, `PaginationCursor`>

**Common pitfalls:**
- <implementation trap 1>
- <implementation trap 2>

**Retrospective indicator that you did this right:** <if X happens in the future, you will be glad you unified — e.g. "rotating the API key takes one PR, not 47">
```

The 12 patterns:

1. **External-service / SDK wrapper** — auth, retry, timeout, cost tracking, vendor switch, logging. The user's canonical example: `LLMService` that wraps OpenAI / Anthropic / Gemini calls, exposes presets like `Preset.LEGAL_SUMMARIZATION` instead of raw model + temperature + max_tokens. Pitfalls: do not swallow the prompt (prompts belong to features), do not become a god service of named domain operations.
2. **Schema validation at boundaries** — Pydantic, Zod. The same payload entering from API, queue, file, or webhook must be parsed by a single schema. Pitfall: validators that silently coerce instead of failing fast.
3. **Authorization / permission checks** — who can do what. Duplicated checks become security holes the moment one endpoint forgets a guard. Pitfall: making the gate optional via "convenience" call paths.
4. **Money arithmetic** — Decimal, precision, rounding mode, currency conversion. Duplicated = fiscal bugs. Pitfall: passing currency as a string instead of a typed value object.
5. **Date and timezone boundary** — one conversion point to UTC on input, one back to local on output. Pitfall: storing local time anywhere except the rendering layer.
6. **Pagination and cursor encoding** — third independent cursor format means you already have three incompatible APIs. Pitfall: leaking the cursor implementation (offset vs keyset) into the client.
7. **Connection pool and unit of work** — transaction lifecycle, retry on connection drop, cross-repository commits. Pitfall: hiding the pool inside repositories such that two repositories cannot share a transaction.
8. **Structured logging and correlation IDs** — uniformity is the value; without it cross-service correlation is impossible. Pitfall: logging the same event with different field names per service.
9. **Error envelope toward clients** — error code, machine-readable type, user-facing message, retry-after hint. Pitfall: letting controllers craft ad-hoc error shapes.
10. **Feature flag and config reader** — a single source of truth with types and defaults. Pitfall: scattering `os.getenv` calls across modules.
11. **Retry and backoff policy** — exponential, capped, jittered, with a circuit breaker around the unified policy. Pitfall: per-service custom retry loops that diverge in their definition of "retriable".
12. **Observability — metrics and tracing context propagation** — span creation, attribute conventions, context propagation across queues / RPCs. Pitfall: instrumenting at the wrong layer (too low or too high) such that key business operations are not spans.

- [ ] **Step 2: Verify**

Run the universal verification snippet against the file. Confirm there are exactly 12 `## P<N>.` headings:

```bash
grep -c '^## P[0-9]' plugins/abstraction-architect/skills/abstraction-architect/references/unification-patterns.md
# Expected: 12
```

---

### Task 3: Write anti-patterns.md

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/anti-patterns.md`

- [ ] **Step 1: Write the file**

File header:

```markdown
# Wrong Abstraction Patterns

Twelve canonical cases where an existing abstraction has gone bad and should be inlined or decomposed. Each pattern is *false unification*: the unified layer hides forces that want to evolve independently. The longer the layer survives, the higher the eventual cost of breaking it apart.

For each pattern: structural signature, why it is wrong, how to escape (inline, decompose, replace with explicit duplication), retrospective indicator that the abstraction has gone bad.

The escape move is almost always *temporarily worse-looking*: you will have more total lines after re-inlining, but the call sites become honest about what they do, which lets the real pattern reveal itself later.

---
```

Then one section per pattern, in this order. Each section uses this template:

```markdown
## A<N>. <Pattern name>

**Structural signature:** <what the bad abstraction looks like in code>

**Why it is wrong:** <which forces are being hidden, what drift this creates>

**Escape move:** <inline / decompose into N units / replace with explicit duplication>

**Retrospective indicator that this abstraction has gone bad:** <warning sign — e.g. "every new feature adds a boolean flag", "the abstraction's interface keeps growing without a clear shape">
```

The 12 anti-patterns:

1. **God service / utils dumping ground** — `utils.py`, `helpers/`, `common/`, `shared/`. Modules where unrelated functions accumulate. Escape: re-home each function to its caller or its concept; the resulting empty module is the success state.
2. **Flag-soup function** — function with 8+ boolean parameters: `do_thing(is_async, with_cache, legacy_mode, skip_validation, verbose, ...)`. Escape: split into two or three explicit functions with clear names.
3. **Premature interface / abstract class with one implementation** — `interface UserRepository { ... }` with `class PostgresUserRepository implements UserRepository`. No substitution use case has ever materialized. Escape: delete the interface, inline the concrete class.
4. **Generic Repository<T>** — `findById`, `findAll`, `save`, `delete` on every entity. Works until `findByEmailWithProfileAndLastLogin` shows up. Escape: replace with entity-specific repositories that own their queries explicitly.
5. **Speculative generality** — extension points (hooks, virtual methods, subclass templates) never used. Escape: inline the hooks back into the call sites.
6. **Leaky abstraction exposing vendor types** — a "vendor-neutral" interface that exposes `OpenAIError`, `pg::Connection`, or `aws_sdk::S3Error` through its public surface. Escape: introduce a real translation layer or drop the pretense of neutrality.
7. **Strategy pattern for two strategies** — interface + two classes + factory where `if/else` was enough. Escape: inline back to `if/else`, document the two cases.
8. **Premature event bus / pub-sub between two modules** — disaccoppling cousins that change together. Result: impossible-to-trace flow. Escape: replace events with direct calls; reintroduce pub-sub only when more than two subscribers genuinely emerge.
9. **Internal DSL or rules engine for a finite hardcoded case set** — a mini-language with parser and validator to avoid writing four `if`s. Escape: replace with four `if`s and a table-driven test.
10. **Test setup helpers grown into 12-parameter factories** — `setupUserWithOrdersAndPaymentsAndDiscounts(options)`. Tests cannot be read in isolation. Escape: split into focused factories; let tests be slightly more verbose.
11. **Universal entity/DTO mapper via reflection** — runtime mapping that explodes the moment a computed field or rename appears. Escape: write explicit `UserDTO.fromUser(user)` mappers per entity.
12. **Configuration abstraction that hides important runtime choices** — `RulesEngine.evaluate(context)` where the rules are buried in YAML files that nobody can audit. Escape: surface the runtime choices as named, typed code paths.

- [ ] **Step 2: Verify**

Run the universal verification snippet against the file. Confirm there are exactly 12 `## A<N>.` headings:

```bash
grep -c '^## A[0-9]' plugins/abstraction-architect/skills/abstraction-architect/references/anti-patterns.md
# Expected: 12
```

---

### Task 4: Write decision-frame.md

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/decision-frame.md`

- [ ] **Step 1: Write the file**

Structure:

```markdown
# Decision Frame

The operational classifier the auditor uses to promote a candidate to a finding. Use it as a checklist; if a candidate fails any of the gates, it does not become a high-severity finding.

## Pre-flight questions (run in order)

1. **When this concern changes, where do I have to touch?** Count the call sites. If N grows linearly with features, this is a unification candidate. If N stays at 1, this is already a layer.

2. **Has this pattern appeared three or more times?** The Rule of Three. Two is coincidence; three is a pattern. A finding with fewer than three sites is downgraded to Low or omitted.

3. **Will the two sites realistically diverge under future requirements?** If yes, the duplication is essential to the design, not accidental. Leave it. Examples of essential divergence: two retry policies serving different SLOs; two `User` models in different bounded contexts.

4. **Are these sites in different bounded contexts?** If yes, do not unify even when the code looks identical today. Bounded-context fusion is the most expensive form of wrong abstraction because it leaks domain concerns across team boundaries.

5. **Does every new feature add a flag, branch, or parameter to a shared layer?** If yes, the layer is a wrong abstraction. The growth pattern of a healthy abstraction is "callers use it as-is and the layer rarely changes"; the growth pattern of a wrong abstraction is "every caller pushes another knob onto the layer".

6. **Can a future reader understand a call site without chasing definitions across files?** Locality of Behaviour gate. If no, the abstraction has a hidden cognitive cost that may outweigh the deduplication value. Weigh that cost against the change-coupling benefit.

## Severity calibration

Default to **Medium**. Escalate or de-escalate only when the evidence supports it.

- **High** when the missed unification or wrong abstraction creates:
  - **Security risk** — duplicated authorization checks, scattered token storage, inconsistent input validation.
  - **Data-correctness risk** — money arithmetic, date/timezone handling, currency conversion.
  - **Operational risk** — multiple incompatible retry policies on the same external service, inconsistent error handling for the same failure mode.

- **Medium** (default) when the pattern creates maintenance drag — god service, flag soup, premature interface, leaky abstraction — but no immediate failure mode.

- **Low** when the pattern is a code smell with no concrete pressure to fix it now (e.g. a strategy-pattern-for-two-strategies that is stable and small).

## Gates against false positives

- Findings citing fewer than three sites under unification are auto-downgraded to Low or omitted (Rule of Three).
- Findings whose evidence comes from a single deep-dive file are marked Medium-confidence in the report.
- Findings where the bounded-context check has not been performed must be explicitly flagged: "context-membership unverified".
```

- [ ] **Step 2: Verify**

Run the universal verification snippet against the file.

---

### Task 5: Write further-reading.md

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/references/further-reading.md`

- [ ] **Step 1: Write the file**

This file is verbatim-sourced from the deep-research pass earlier in the brainstorming conversation. Group the URLs by category. Mark URLs that were search-snippet-only with a verify-before-citing note.

File template:

```markdown
# Further Reading

Curated reading list on the abstraction-vs-duplication question. Grouped by category; URLs marked `(snippet-only)` were found via search but not opened end-to-end during research and should be verified before citing.

## The single must-read first

- **Sandi Metz, "The Wrong Abstraction" (2016)** — https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction. Four paragraphs. The load-bearing essay of the whole modern debate. *"Duplication is far cheaper than the wrong abstraction."*

- **Sandi Metz, "All the Little Things" (RailsConf 2014)** — https://www.youtube.com/watch?v=8bZh5LMaSmE. Where the line above was first spoken. The blog post is the executive summary; the talk is the long form.

## Canonical principles

- **Kent C. Dodds, "AHA Programming"** — https://kentcdodds.com/blog/aha-programming. *Avoid Hasty Abstractions* — the operational rule of thumb for the Rule of Three in modern frontend.

- **Carson Gross, "Locality of Behaviour" (2020)** — https://htmx.org/essays/locality-of-behaviour/. The cognitive counter-force to DRY.

- **Dan North, "CUPID for joyful coding" (2022)** — https://dannorth.net/blog/cupid-for-joyful-coding/. The SOLID critique and the properties-vs-principles framing.

- **Martin Fowler, "Bounded Context"** — https://www.martinfowler.com/bliki/BoundedContext.html. The seam for *what NOT to unify*.

- **Refactoring.guru, "Speculative Generality"** — https://refactoring.guru/smells/speculative-generality. Short canonical reference to the code smell.

- **Eoin Noble, "Origins of the Rule of Three"** — https://eoinnoble.com/posts/origins-of-the-rule-of-three/. Traces the lineage to Roberts & Johnson, "Evolving Frameworks" (1996).

- **Kent Beck on preparatory refactoring** — https://martinfowler.com/articles/preparatory-refactoring-example.html (Fowler) and the original tweet https://twitter.com/KentBeck/status/250733358307500032 ("first make the change easy, then make the easy change").

## Practitioner war stories

- **Dan Abramov, "Goodbye, Clean Code"** — https://overreacted.io/goodbye-clean-code/. The most-shared personal anecdote of a clean abstraction that was reverted the next day.

- **Hacker News, 2016 thread on Metz** — https://news.ycombinator.com/item?id=12061453. The HN consensus comment: *"I'm willing to duplicate code if it makes the code less complex."* Also the 2020 revisit: https://news.ycombinator.com/item?id=23739596.

- **Jason Swett, "Why I don't buy 'duplication is cheaper than the wrong abstraction'"** — https://www.codewithjason.com/duplication-cheaper-wrong-abstraction/. The most-cited respectful dissent. Read after Metz to test your position.

- **Matt Rickard, "DRY Considered Harmful"** — https://mattrickard.com/dry-considered-harmful. Microservices-flavored take.

- **DEV, "A Case Against Abstraction"** — https://dev.to/puritanic/a-case-against-abstraction-118o. Practitioner overview with code examples.

- **DEV, "The 'Shared' Library is a Lie: Fixing Your Nx Monorepo Architecture"** — https://dev.to/abdelaaziz_ouakala/the-shared-library-is-a-lie-fixing-your-nx-monorepo-architecture-3mie. Modern monorepo war story.

## Recent (2023-2026) framings

- **Kent Beck, *Tidy First?* substack** — https://tidyfirst.substack.com/. The financial-options framing of abstraction cost. Companion to the book.

- **Henrik Warne, *Tidy First?* review** — https://henrikwarne.com/2024/01/10/tidy-first/.

- **Dan Lebrero, *Tidy First?* book notes** — https://danlebrero.com/2024/08/07/tidy-first-summary/.

- **Frontend at Scale, "Too General Too Soon" (2024)** — https://frontendatscale.com/issues/15/. Frontend-flavored speculative-generality cases.

- **Code With Seb, "WET vs AHA: Avoiding Premature Abstraction in Frontend Development" (April 2025)** — https://www.codewithseb.com/blog/wet-vs-aha-avoiding-premature-abstraction-in-frontend-development.

- **Java Code Geeks, "The Dark Side of Clean Code" (May 2026)** *(snippet-only)* — https://www.javacodegeeks.com/2026/05/the-dark-side-of-clean-code-when-solid-and-dry-principles-actively-hurt-you.html.

- **Piotr Sikora, "DRY, WET, AHA: Finding the Right Balance" (January 2026)** *(snippet-only)* — https://www.piotr-sikora.com/blog/2026-01-28-dry-wet-aha.

## Counter-current from game and performance communities

- **Mike Acton, "Data-Oriented Design and C++" (CppCon 2014)** — https://www.youtube.com/watch?v=rX0ItVEVjHc. The strongest non-overlapping critique of OOP-style abstraction.

- **Marcell Juhasz, "Cost of C++ Abstractions in Embedded Systems" (CppCon 2024)** — https://isocpp.org/blog/2025/06/cppcon-2024-cost-of-cpp-abstractions-in-c-embedded-systems-marcell-juhasz. Current numbers complementing Acton.

## Italian-language resources (DDD-flavored)

- **Avanscoperta, "Domain-Driven Design: una questione tecnica?" (2023)** — https://blog.avanscoperta.it/2023/01/03/domain-driven-design-una-questione-tecnica/.
- **Avanscoperta, "DDD Open Space: Bounded Context" (2021)** — https://blog.avanscoperta.it/2021/06/17/ddd-open-space-bounded-context/.
- **Avanscoperta, "Microservices e Domain-Driven Design" (2024)** — https://blog.avanscoperta.it/2024/03/19/microservices-e-domain-driven-design/.
- **MokaByte, "DDD, microservizi e architetture evolutive" (2024)** — https://mokabyte.it/2024/01/11/architettureevolutive-3/.
- **Intre.it, "DDD, microservizi: strategic patterns" (May 2025)** — https://www.intre.it/2025/05/21/ddd-microservizi-strategic-patterns/.
- **Wikipedia IT, "Regola del tre (programmazione)"** — https://it.wikipedia.org/wiki/Regola_del_tre_(programmazione).

## Books

- **Sandi Metz, Katrina Owen, TJ Stankus, *99 Bottles of OOP* (2nd ed.)** — https://sandimetz.com/99bottles. Book-length expansion with the "Shameless Green" pattern.
- **Kent Beck, *Tidy First?* (2024)** — ~100 pages. The options framing of abstraction cost.
- **Eric Evans, *Domain-Driven Design* (Blue Book, 2003)** — strategic chapters for what NOT to unify.
- **Vaughn Vernon, *Implementing Domain-Driven Design* (2013)** — operational counterpart with concrete bounded-context examples.
- **Martin Fowler, *Refactoring* (2nd ed., 2018)** — Rule of Three, *Speculative Generality*, *Inline Method*, *Inline Class*.

## Conference talks

- **Sandi Metz, "All the Little Things" — RailsConf 2014** — https://www.youtube.com/watch?v=8bZh5LMaSmE.
- **Mike Acton, "Data-Oriented Design and C++" — CppCon 2014** — https://www.youtube.com/watch?v=rX0ItVEVjHc.
- **Kent Beck, "Tidy First?" — InfoQ** — https://www.infoq.com/presentations/refactoring-cleaning-code/ and https://www.youtube.com/watch?v=XmsyvStDuqI.
- **Kent C. Dodds, "AHA Programming" — GitNation** — https://gitnation.com/contents/aha-programming.
- **Eric Evans on Bounded Contexts — DDD Europe 2019 (InfoQ)** — https://www.infoq.com/news/2019/06/bounded-context-eric-evans/.

## Minimum reading path (~3 hours)

1. Metz, "The Wrong Abstraction" (4 paragraphs)
2. Metz, "All the Little Things" — RailsConf 2014 (~30 min)
3. Abramov, "Goodbye, Clean Code" (~10 min)
4. Gross, "Locality of Behaviour" (~5 min)
5. Beck, *Tidy First?* (book or substack, ~2 hours)
6. Swett, "Why I don't buy..." (~10 min, to test the position)
```

- [ ] **Step 2: Verify**

Run the universal verification snippet against the file.

---

### Task 6: Write SKILL.md

**Files:**
- Create: `plugins/abstraction-architect/skills/abstraction-architect/SKILL.md`

- [ ] **Step 1: Write the file**

Full content:

````markdown
---
name: abstraction-architect
description: >
  Knowledge base for pure-architecture decisions on when to unify duplicated logic into a shared abstraction versus leave it duplicated. Covers the canonical theory (Rule of Three, DRY/WET/AHA, Wrong Abstraction, Locality of Behaviour, Bounded Contexts, Tidy First options framing, CUPID vs SOLID), 12 essential-duplication patterns that justify unification, 12 wrong-abstraction patterns that justify inlining or decomposition, an operational decision frame, and a verified reading list.
  TRIGGER WHEN: the user is making an architectural decision about whether to centralize, extract, or remove a layer; reviewing an abstraction for premature generality; auditing scattered cross-cutting concerns; spawned by the abstraction-architect agent during /abstraction-architect:audit; the user asks "should I extract this into a service" / "is this DRY enough" / "is this wrong abstraction".
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
````

- [ ] **Step 2: Verify**

Run the universal verification snippet against the file. Confirm frontmatter parses:

```bash
python3 -c "
import yaml
with open('plugins/abstraction-architect/skills/abstraction-architect/SKILL.md') as f:
    text = f.read()
parts = text.split('---', 2)
fm = yaml.safe_load(parts[1])
assert fm['name'] == 'abstraction-architect'
assert 'TRIGGER WHEN' in fm['description']
assert 'DO NOT TRIGGER WHEN' in fm['description']
print('SKILL.md frontmatter OK')
"
```

---

### Task 7: Write the auditor agent

**Files:**
- Create: `plugins/abstraction-architect/agents/abstraction-architect.md`

- [ ] **Step 1: Write the file**

Full content:

````markdown
---
name: abstraction-architect
description: >
  Adversarial auditor for pure-architecture failures. Reads .deep-dive/ output and produces report-only findings in two categories: missed unification (cross-cutting concerns scattered across call sites that should be a single layer) and wrong abstractions (god services, flag-soup functions, premature interfaces, leaky abstractions, speculative generality). Grounded in canonical theory (Metz, Beck, Fowler, Gross, North, DDD).
  TRIGGER WHEN: spawned by /abstraction-architect:audit after .deep-dive/ output is ready; the user asks to audit a codebase for missed unification, wrong abstractions, god services, or bounded-context violations.
  DO NOT TRIGGER WHEN: the task is implementation, code formatting, security-only review (use senior-review:security-auditor), distributed-flow tracing (use senior-review:distributed-flow-auditor), or pattern-consistency review without an architecture lens (use senior-review:code-auditor).
tools: Read, Glob, Grep, Write
model: opus
color: orange
---

# ROLE

Adversarial auditor for missed unification and wrong abstraction. Primary reasoning is semantic, grounded in `.deep-dive/` structured output rather than lexical pattern-matching on source files. You may open individual source files via `Read` or `Grep` only to verify a candidate finding's file:line citations and confirm the structural shape claimed by deep-dive.

Priority: precision over recall. A wrong finding wastes the user's time and erodes trust in the report. A missed finding is cheap to recover (the user can re-run with a lower severity floor). Default to *not flagging* when unsure.

Load the skill `abstraction-architect:abstraction-architect` for the theory and pattern catalogs. Read references on demand, not all up front.

# INPUTS

You will receive:

- `codebase_path` — the codebase root.
- `deep_dive_path` — path to `.deep-dive/` directory.
- `scope` (optional) — a subpath. If set, only emit findings whose evidence falls inside the scope.
- `severity_floor` (optional, default `medium`) — drop findings below this level from the report.
- `focus` (optional, default `both`) — restrict to `unification`, `wrong-abstraction`, or `both`.

# REQUIRED DEEP-DIVE FILES

Read these files from `deep_dive_path`. Missing files do not abort the audit; they reduce confidence on findings that depended on them.

- `01-structure.md` — modules, classes, file sizes, method counts. Used to find god services and `utils` dumping grounds.
- `02-interfaces.md` — public APIs. Used to find premature interfaces, leaky abstractions, flag-soup functions.
- `03-flows.md` — call graphs. Used to find missed unification: N call sites with the same structural shape across modules.
- `04-semantics.md` — responsibilities and intent. Used to find boundary violations (domain logic in infrastructure, infrastructure in domain).
- `08-interconnect-map.md` (optional, present only when produced by `agent-teams:team-deep-dive`) — cross-partition contracts and invariants. Used to find bounded-context fusion.

# PROCESS

1. **Load skill.** Read `SKILL.md` of `abstraction-architect:abstraction-architect`. Note the reference index for on-demand loading.
2. **Read deep-dive files.** Skim the five files. Record missing files in a Gaps list.
3. **First pass — missed unification.** Walk `03-flows.md` and `02-interfaces.md` looking for call sites that share a structural shape (same external-service call with hardcoded parameters, same validation step, same auth check). For each candidate cluster: count the sites. If fewer than three, downgrade to Low or drop. Load `references/unification-patterns.md` to match the cluster against a canonical pattern.
4. **Second pass — wrong abstraction.** Walk `01-structure.md` and `02-interfaces.md` looking for: god services (high method count, broad responsibility), `utils` modules (catch-all naming), flag-soup functions (parameters with many booleans), premature interfaces (one implementation), leaky abstractions (vendor-specific types in public surface), generic Repository<T> wrappers. Load `references/anti-patterns.md` to match against canonical anti-patterns.
5. **Third pass — boundary violations.** Walk `04-semantics.md` looking for modules whose stated responsibility mismatches their dependencies (infrastructure module that calls domain rules; domain module that talks directly to HTTP / DB / queues). If `08-interconnect-map.md` is available, also look for bounded-context fusion: two contexts sharing a model that the interconnect map says belong to different domains.
6. **Apply the decision frame.** Load `references/decision-frame.md`. For each candidate finding, run the pre-flight questions:
   - When this concern changes, where do you have to touch? (Rule of Three filter)
   - Will the sites realistically diverge under future requirements? (essential vs accidental)
   - Are they in different bounded contexts?
   - Does every new feature add a flag to a shared layer?
   - Can a reader understand the call site without chasing definitions across files?
7. **Calibrate severity** per `references/decision-frame.md`:
   - **High** for security, data-correctness, or operational risk.
   - **Medium** (default) for maintenance drag.
   - **Low** for code smell without concrete pressure.
8. **Verify citations.** For each finding, open the cited files via `Read` if deep-dive did not provide precise line ranges. Report tight line ranges, not whole files.
9. **Write the report** to `<codebase_path>/.abstraction-architect/findings.md`. Create the directory if missing.

# REPORT STRUCTURE

```markdown
# Abstraction-architect findings

**Generated:** <ISO timestamp>
**Codebase scope:** <codebase_path[/scope]>
**Deep-dive source:** <deep_dive_path>
**Severity floor:** <medium | low | high>
**Focus:** <both | unification | wrong-abstraction>

## Summary
- N findings total (H high, M medium, L low)
- Top 3 findings by severity (one line each)

## A. Missed Unification

### A1. <Pattern name> — <severity>
- **Pattern:** <canonical name from unification-patterns.md, e.g. "External-service / SDK wrapper">
- **Evidence:**
  - <path/file.ext>:<line-range>
  - <path/file.ext>:<line-range>
  - <path/file.ext>:<line-range>
- **Why this is a problem:** <one or two sentences citing the force that wants these sites to change together>
- **Suggested direction:** <e.g. "extract a vendor-agnostic LLMService that owns model selection, auth, retry, cost tracking">
- **Reference:** `references/unification-patterns.md` -> P1. External-service / SDK wrapper

### A2. ...

## B. Wrong Abstractions

### B1. <Pattern name> — <severity>
- **Pattern:** <canonical name from anti-patterns.md, e.g. "God service / utils dumping ground">
- **Evidence:** <file:line citations>
- **Why this is a problem:** <one or two sentences>
- **Suggested direction:** <inline / decompose into N units / replace with explicit duplication>
- **Reference:** `references/anti-patterns.md` -> A1. God service / utils dumping ground

## C. Confidence and Gaps

- **High confidence:** findings supported by two or more deep-dive files
- **Medium confidence:** findings supported by one deep-dive file
- **Low confidence:** findings flagged by a single signal, worth manual verification
- **Gaps:** deep-dive files that were missing or empty, and the analyses they would have enabled
```

# CONSTRAINTS

- Report-only. You must not edit any file outside `<codebase_path>/.abstraction-architect/`.
- Findings citing fewer than three sites under the missed-unification category must be downgraded to Low or omitted (Rule of Three).
- Suggested direction names the target layer or refactoring move; it does not produce code, file lists, or migration steps.
- File:line citations come from deep-dive output where present. When deep-dive cites a module or class without precise line ranges, open the file via `Read` and report a tight line range covering the relevant block, not the whole file.
- Default to Medium severity when uncertain. High is reserved for findings you can argue for in one paragraph.

# OUTPUT

After writing the report, return a short message to the caller with:

- The absolute path of the report.
- Summary counts (total / high / medium / low).
- The top three high-severity findings as one-line previews.

Do not paste the full report into the message; the caller wants the path and the summary so the user can choose to open the file.

# ANTI-PATTERNS FOR YOU

- Do not flag every cluster you see. Apply the Rule of Three.
- Do not promote a low-confidence cluster to Medium just because it matches a pattern name. Severity requires the decision-frame gates to pass.
- Do not produce a refactoring plan inside the report. Suggested direction is one sentence, not a migration roadmap.
- Do not echo the deep-dive content. The report is your independent synthesis, not a re-export.
````

- [ ] **Step 2: Verify**

```bash
python3 -c "
import yaml
with open('plugins/abstraction-architect/agents/abstraction-architect.md') as f:
    text = f.read()
parts = text.split('---', 2)
fm = yaml.safe_load(parts[1])
assert fm['name'] == 'abstraction-architect'
assert fm['model'] == 'opus'
assert 'Read' in fm['tools'] and 'Write' in fm['tools'] and 'Glob' in fm['tools'] and 'Grep' in fm['tools']
assert 'TRIGGER WHEN' in fm['description']
print('agent frontmatter OK')
"
```

Then run the universal verification snippet against the file.

---

### Task 8: Write the audit command

**Files:**
- Create: `plugins/abstraction-architect/commands/audit.md`

- [ ] **Step 1: Write the file**

Full content:

````markdown
---
description: Audit a codebase for missed unification opportunities and wrong abstractions. Auto-launches /deep-dive-analysis:deep-dive-analysis when .deep-dive/ is missing or incomplete. Report-only.
argument-hint: "[path] [--scope <subpath>] [--severity-floor low|medium|high] [--focus unification|wrong-abstraction|both]"
---

# /abstraction-architect:audit

Audit a codebase for the two failure modes of pure architecture: missed unification (cross-cutting concerns scattered across call sites that should be a single layer) and wrong abstractions (god services, flag-soup functions, premature interfaces, leaky abstractions). Report-only.

## Usage

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --severity-floor high              # only high-severity findings
/abstraction-architect:audit --focus wrong-abstraction          # restrict to one category
/abstraction-architect:audit --scope src/api --focus unification
```

## Arguments

- `[path]` (optional) — codebase root. Default: current working directory.
- `--scope <subpath>` (optional) — limit findings to a subtree. Deep-dive is still run on the full codebase; the agent filters findings by scope.
- `--severity-floor low|medium|high` (optional) — drop findings below this severity. Default: `medium`.
- `--focus unification|wrong-abstraction|both` (optional) — restrict to one finding category. Default: `both`.

## What this command does

1. **Resolves the target path.** Defaults to the current working directory if `[path]` is omitted.

2. **Checks for `.deep-dive/`.** Looks for the required files: `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`. The optional `08-interconnect-map.md` is also checked; if absent the audit proceeds without bounded-context fusion analysis.

3. **Auto-launches deep-dive if needed.** If `.deep-dive/` is missing or incomplete, prints the status message *"No deep-dive output found at `.deep-dive/`. Launching `/deep-dive-analysis:deep-dive-analysis` first. This may take several minutes on a large codebase."* then invokes `/deep-dive-analysis:deep-dive-analysis` automatically without a confirmation prompt. If deep-dive fails, aborts with the path of the deep-dive log.

4. **Spawns the `abstraction-architect` agent** via the `Agent` tool, passing the codebase path, the deep-dive path, and the parsed scope / severity-floor / focus flags.

5. **The agent writes the report** to `<path>/.abstraction-architect/findings.md`.

6. **Prints to the user:**
   - The absolute path of the report.
   - Summary counts: total findings, high / medium / low breakdown.
   - The top three high-severity findings as one-line previews.

The full report stays in the file so the user opens it deliberately.

## Output location

`<path>/.abstraction-architect/findings.md`

The directory is created automatically if missing. Re-running the command overwrites the previous report.

## Prerequisites

- The `deep-dive-analysis` plugin must be installed (declared as a dependency in `marketplace.json`).
- For monorepos large enough to benefit from partitioned analysis, run `/agent-teams:team-deep-dive` first to produce `08-interconnect-map.md`; the auditor will then include bounded-context fusion findings.

## Related commands

- `/deep-dive-analysis:deep-dive-analysis` — produces the `.deep-dive/` input this command consumes. Auto-launched by this command when missing.
- `/agent-teams:team-deep-dive` — partitioned deep-dive for monorepos; adds `08-interconnect-map.md` to the output.
- `/senior-review:code-review` — orthogonal: general code-quality review. Use that for style and pattern consistency; use this for pure-architecture audits.
- `/clean-code:clean-code` — style and readability cleanup. Different concern.

## Out of scope

This command does not produce a refactoring plan. The `suggested direction` field in each finding names the target layer or refactoring move in one sentence. A future `/abstraction-architect:plan-refactor <finding-id>` command will turn a finding into a step-by-step plan.
````

- [ ] **Step 2: Verify**

```bash
python3 -c "
import yaml
with open('plugins/abstraction-architect/commands/audit.md') as f:
    text = f.read()
parts = text.split('---', 2)
fm = yaml.safe_load(parts[1])
assert 'description' in fm
assert 'argument-hint' in fm
print('command frontmatter OK')
"
```

Then run the universal verification snippet.

---

### Task 9: Register the plugin in marketplace.json and bump versions

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Inspect current state**

```bash
python3 -c "
import json
with open('.claude-plugin/marketplace.json') as f:
    data = json.load(f)
print('Current metadata.version:', data['metadata']['version'])
print('Current plugin count in description:', data['metadata']['description'][:60])
print('Plugin count in array:', len(data['plugins']))
"
```

Expected: metadata.version `6.22.0`, description starts with "Claude Code Daodan -- 43 plugins" (stale), plugin array length 44.

- [ ] **Step 2: Add the new plugin entry**

Find the last entry of the `plugins` array. Add a new entry after it (alphabetical insertion is not the convention in this repo; append is fine). Use this exact JSON, preserving the surrounding comma:

```json
    {
      "name": "abstraction-architect",
      "source": "./plugins/abstraction-architect",
      "description": "Pure-architecture auditor. Finds missed unification opportunities (cross-cutting concerns scattered across call sites that should be a single layer) and wrong abstractions (god services, flag-soup functions, premature interfaces, leaky abstractions that should be inlined or decomposed). Reads .deep-dive/ output and produces report-only findings grounded in canonical theory (Metz's Wrong Abstraction, Beck's Tidy First, Fowler's bounded contexts, Gross's Locality of Behaviour).",
      "version": "1.0.0",
      "author": {"name": "Alfio Caprino"},
      "license": "MIT",
      "keywords": ["architecture", "abstraction", "refactoring", "dry", "wet", "aha", "wrong-abstraction", "god-service", "code-quality", "audit", "metz", "bounded-context"],
      "category": "code-quality",
      "strict": false,
      "agents": "./plugins/abstraction-architect/agents",
      "skills": "./plugins/abstraction-architect/skills",
      "commands": "./plugins/abstraction-architect/commands",
      "dependencies": ["deep-dive-analysis"]
    }
```

- [ ] **Step 3: Bump metadata.version and fix the stale plugin count**

In the `metadata` block:

- Change `"version": "6.22.0"` to `"version": "6.23.0"` (minor bump for a new plugin per CLAUDE.md).
- Change the `description` field's plugin count from `43 plugins` to `45 plugins`. (The pwa-expert addition raised the count from 43 to 44 but did not update the description; this commit brings it to 45 and fixes the prior drift in one go.)

- [ ] **Step 4: Verify JSON validity and counts**

```bash
python3 -c "
import json
with open('.claude-plugin/marketplace.json') as f:
    data = json.load(f)
assert data['metadata']['version'] == '6.23.0', data['metadata']['version']
assert '45 plugins' in data['metadata']['description'], data['metadata']['description'][:60]
assert len(data['plugins']) == 45, len(data['plugins'])
names = [p['name'] for p in data['plugins']]
assert 'abstraction-architect' in names
abs_arch = next(p for p in data['plugins'] if p['name'] == 'abstraction-architect')
assert abs_arch['version'] == '1.0.0'
assert abs_arch['dependencies'] == ['deep-dive-analysis']
assert abs_arch['license'] == 'MIT'
print('marketplace.json OK')
"
```

If the JSON does not parse, run `python3 -m json.tool .claude-plugin/marketplace.json` and fix the syntax.

---

### Task 10: Update CLAUDE.md (plugin count + custom-plugin row)

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the plugin-count line**

Find the line that reads (currently):

```
44 plugins: clean-code, deep-dive-analysis, tauri-development, frontend, react-development, xterm, ai-tooling, python-development, stripe, system-utils, messaging, research, business, project-setup, app-analyzer, typescript-development, csp, digital-marketing, senior-review, obsidian-development, browser-extensions, learning, marketplace-ops, playwright-skill, acp-hooks, prompt-improver, cc-usage, codebase-mapper, git-worktrees, rag-development, docs, testing, platform-engineering, ibkr-trading, mt5-trading, opentelemetry, docker, grabber-development, agent-teams, reverse-engineering, codebase-cleanup, libgdx-development, kotlin-development, pwa-expert.
```

Change `44 plugins` to `45 plugins` and append `, abstraction-architect` before the trailing period:

```
45 plugins: clean-code, ..., pwa-expert, abstraction-architect.
```

- [ ] **Step 2: Add abstraction-architect to the custom-plugin freshness-class table**

Find the section *Custom plugin maintenance* -> *Freshness risk classes* table. In the **Moderate** row (the row for plugins reviewed every 12 months), append `abstraction-architect` to the Examples list.

Rationale: the underlying theory (Metz, Beck, Fowler, Roberts & Johnson, Evans) is stable and changes on the scale of years. The most-likely-to-rot content is the URL list in `further-reading.md`, which should be reverified annually. Moderate is the right class.

- [ ] **Step 3: Verify**

```bash
grep -c '^45 plugins:' CLAUDE.md
# Expected: 1

grep -c 'abstraction-architect' CLAUDE.md
# Expected: at least 2 (plugin list + Moderate row)
```

---

### Task 11: Run the marketplace integrity check

**Files:** none (validation only)

- [ ] **Step 1: Run marketplace health check**

Use the `/marketplace-ops:marketplace-health` skill or run the equivalent manual check. Quick manual check:

```bash
# Every plugin entry's source path exists
python3 -c "
import json, os
with open('.claude-plugin/marketplace.json') as f:
    data = json.load(f)
for p in data['plugins']:
    src = p['source'].lstrip('./')
    assert os.path.isdir(src), f'Missing source dir: {src}'
    for sub in ['agents', 'skills', 'commands', 'hooks']:
        if sub in p:
            sub_path = p[sub].lstrip('./')
            assert os.path.isdir(sub_path), f'Missing subdir: {sub_path} for {p[\"name\"]}'
print('All plugin paths resolve')
"
```

- [ ] **Step 2: Validate skill body conventions**

For the new skill, agent, and command files, verify:

```bash
# No emojis anywhere
for f in $(find plugins/abstraction-architect -name '*.md'); do
  if grep -nP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' "$f" > /dev/null; then
    echo "EMOJI in $f"
    exit 1
  fi
done

# No dash-aside constructs ( -- , — , - capital-letter as bracketed aside)
for f in $(find plugins/abstraction-architect -name '*.md'); do
  matches=$(grep -nE ' (—|--) ' "$f" | grep -v '^\s*[-*]' | head -5)
  if [ -n "$matches" ]; then
    echo "DASH-ASIDE in $f:"
    echo "$matches"
  fi
done

# No Italian leftovers
for f in $(find plugins/abstraction-architect -name '*.md'); do
  matches=$(grep -niE '\b(che|della|dello|delle|degli|sono|essere|questo|questa|quando|perché|anche|tutto|tutta|tutti|abbiamo|hanno)\b' "$f" | head -3)
  if [ -n "$matches" ]; then
    echo "ITALIAN LEFTOVER in $f:"
    echo "$matches"
  fi
done
```

If any check returns content, fix the file before moving on. Some Italian-language URLs in `further-reading.md` are *URLs* and should not be flagged: the grep above looks for *words* in prose, not URL slugs, so it should be safe. If a real prose leak appears, fix it.

- [ ] **Step 3: Confirm directory shape**

```bash
ls plugins/abstraction-architect/
# Expected: agents/  commands/  skills/

ls plugins/abstraction-architect/skills/abstraction-architect/references/
# Expected: theory.md  unification-patterns.md  anti-patterns.md  decision-frame.md  further-reading.md
```

---

### Task 12: Final commit

**Files:**
- Stage: all files under `plugins/abstraction-architect/`, `.claude-plugin/marketplace.json`, `CLAUDE.md`.

- [ ] **Step 1: Inspect what is staged**

```bash
git status --short
git diff --stat
```

Expected: 9 new files under `plugins/abstraction-architect/`, 2 modified files (`.claude-plugin/marketplace.json`, `CLAUDE.md`). 11 total paths touched.

- [ ] **Step 2: Stage and commit**

```bash
git add plugins/abstraction-architect/ .claude-plugin/marketplace.json CLAUDE.md
```

Use this commit message:

```
Add abstraction-architect plugin for pure-architecture audits (v1.0.0)

New marketplace plugin that audits a codebase for the two failure modes
of pure architecture: missed unification (cross-cutting concerns
scattered across call sites that should be a single layer) and wrong
abstractions (god services, flag-soup functions, premature interfaces,
leaky abstractions, speculative generality).

Plugin shape:
- 1 skill (theory + 12 unification patterns + 12 anti-patterns +
  decision frame + verified further-reading URLs from Metz, Beck,
  Dodds, Abramov, Gross, North, Acton, plus Italian-language DDD canon)
- 1 auditor agent that reads .deep-dive/ output and produces
  report-only findings with severity calibration, file:line evidence,
  and references to the canonical pattern catalogs
- 1 command /abstraction-architect:audit with hands-off auto-launch
  of /deep-dive-analysis:deep-dive-analysis when output is missing

Marketplace bookkeeping:
- abstraction-architect declares dependencies: ["deep-dive-analysis"]
- metadata.version 6.22.0 -> 6.23.0 (minor bump for new plugin)
- metadata.description plugin count 43 -> 45 (fixes prior pwa-expert
  drift in the same commit)
- CLAUDE.md plugin list extended (44 -> 45) and abstraction-architect
  added to the Moderate freshness-class row (theory is stable; URL
  list in further-reading.md decays on a yearly cadence)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

- [ ] **Step 3: Verify the commit**

```bash
git log -1 --stat
# Expected: 11 files changed (9 new + 2 modified)
```

- [ ] **Step 4: Smoke-test the plugin shape**

Without actually running deep-dive, confirm the plugin is loadable:

```bash
# Plugin tree is well-formed
ls plugins/abstraction-architect/agents/abstraction-architect.md
ls plugins/abstraction-architect/commands/audit.md
ls plugins/abstraction-architect/skills/abstraction-architect/SKILL.md
ls plugins/abstraction-architect/skills/abstraction-architect/references/

# marketplace.json validates
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "JSON OK"
```

---

## Spec coverage check

Mapping each section of the design spec (`docs/plans/2026-05-25-abstraction-architect-design.md`) to a task that implements it:

| Spec section | Task |
|---|---|
| Goal | Tasks 1-12 collectively |
| Scope: missed-unification detection | Task 2 (unification-patterns.md) + Task 7 (agent process step 3) |
| Scope: wrong-abstraction detection | Task 3 (anti-patterns.md) + Task 7 (agent process step 4) |
| Scope: boundary violations | Task 7 (agent process step 5) |
| Scope: knowledge base | Tasks 1-5 (5 reference files) + Task 6 (SKILL.md) |
| Scope: auto-orchestration of deep-dive | Task 8 (command, step "What this command does" item 3) |
| Plugin layout | Task 1 (directory tree) |
| Skill: SKILL.md content | Task 6 |
| Skill: 5 reference files | Tasks 1, 2, 3, 4, 5 |
| Agent: frontmatter | Task 7 (frontmatter block) |
| Agent: inputs / deep-dive files | Task 7 (INPUTS and REQUIRED DEEP-DIVE FILES) |
| Agent: process | Task 7 (PROCESS) |
| Agent: report structure | Task 7 (REPORT STRUCTURE) |
| Agent: constraints (report-only, Rule of Three, citations) | Task 7 (CONSTRAINTS) |
| Command: frontmatter, flow, arguments | Task 8 |
| Marketplace registration | Task 9 |
| CLAUDE.md updates | Task 10 |
| Acceptance criteria 1 (plugin tree + references populated) | Tasks 1-8 + Task 11 (verification) |
| Acceptance criteria 2 (marketplace registration) | Task 9 |
| Acceptance criteria 3 (audit produces findings) | Manual post-merge test (out of plan scope; verified by user on first real run) |
| Acceptance criteria 4 (auto-launch deep-dive) | Task 8 (command flow) |
| Acceptance criteria 5 (metadata.version bump + commit) | Task 9 + Task 12 |
| Open risks: over-flagging | Task 4 (decision-frame severity gates) + Task 7 (Rule of Three constraint) |
| Open risks: false confidence in deep-dive | Task 7 (Confidence and Gaps section) |
| Open risks: vagueness of suggested direction | Out of scope for v1 (deferred to v2 plan-refactor command, documented in Task 8) |
| Open risks: overlap with senior-review:code-auditor | Task 6 (SKILL.md DO NOT TRIGGER WHEN) + Task 8 (command Related-commands section) |

No spec section is uncovered.
