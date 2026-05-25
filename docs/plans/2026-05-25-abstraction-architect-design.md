# abstraction-architect plugin design

**Date:** 2026-05-25
**Status:** Approved (brainstorming phase complete, ready for implementation plan)
**Source material:** This conversation. Synthesizes the user's recurring architectural question ("are there logics that could be abstracted into a unified layer instead of being repeated in many call sites?") into a marketplace plugin. The knowledge base derives from canonical sources verified during the brainstorming pass: Sandi Metz's "The Wrong Abstraction", Kent Beck's *Tidy First?*, Kent C. Dodds' AHA, Carson Gross's Locality of Behaviour, Dan North's CUPID, Martin Fowler's bounded contexts, Mike Acton's data-oriented critique, and the Italian-language DDD canon (Avanscoperta, MokaByte).

## Goal

Add a marketplace plugin `abstraction-architect` that audits a codebase for the two failure modes of *pure architecture*: **missed unification** (the same cross-cutting concern duplicated across many call sites that should be a single layer) and **wrong abstraction** (a layer that should be inlined or decomposed because it has become a god service, a flag-soup function, a premature interface, or a leaky abstraction). The plugin is report-only and reasons over the structured output produced by `deep-dive-analysis`, so its findings come grounded in module structure, public interfaces, call flows, and semantic responsibilities rather than lexical pattern-matching.

## Scope

Covered in v1:

1. **Missed unification detection** across call flows: cross-cutting concerns repeated across many sites (auth headers, retry, logging, rate limiting, cost tracking), external-service calls scattered with hardcoded parameters (the canonical *LLMService* case the user raised), domain validation duplicated, authorization checks duplicated (security-flavored finding), money/date handling done inconsistently.
2. **Wrong-abstraction detection** across module structure and public interfaces: god service, catch-all `utils.py` / `helpers/` / `common/` modules, flag-soup functions (parametrize-the-difference smell), premature interfaces with a single implementation, speculative generality, leaky abstractions exposing vendor-specific types, "shared library" dumping grounds in monorepos.
3. **Boundary violations**: business logic in infrastructure modules, infrastructure concerns in domain modules, bounded-context fusion (two contexts that should remain separate sharing the same model).
4. **Knowledge base** consumable on demand by the agent and by the user: theory layer (Rule of Three, DRY vs WET vs AHA, Wrong Abstraction, Locality of Behaviour, bounded contexts, Tidy First options framing), 12 canonical "essential duplication" cases that justify unification, 12 canonical "wrong abstraction" cases that justify inlining or decomposition, decision frame for runtime classification, verified further-reading list.
5. **Auto-orchestration** of `deep-dive-analysis`: the audit command launches deep-dive automatically when its output is missing, then proceeds. Single hands-off entry point.

Not covered in v1 (intentional, route elsewhere or defer):

- Refactoring plan generation (deferred to v2 as a separate command `/abstraction-architect:plan-refactor <finding-id>`)
- Automatic code modification (never; this plugin is report-only by design)
- Language-specific AST detection or syntactic pattern matching (the agent reasons over deep-dive's semantic output, not source files directly)
- Concurrency and async-pattern analysis (route to existing reviewers — `senior-review:ui-race-auditor` and language-specific async skills)
- Security-deep-dive on duplicated authorization checks (the finding flags the pattern; deeper analysis routes to `senior-review:security-auditor`)
- Multiple specialized auditor agents (one agent for v1; split if prompt size becomes a problem)
- Visualizations or graphs (the report is markdown only)

## Approved decisions (from brainstorming questions)

| Dimension | Decision |
|---|---|
| Primary use mode | Proactive auditor + knowledge base. Both together: the auditor uses the knowledge base as its reasoning frame. |
| Deep-dive integration | Hard dependency with auto-orchestration. The command launches deep-dive automatically when `.deep-dive/` is missing or incomplete. No confirmation prompt. |
| Plugin layout | One skill (knowledge base with multi-file references), one agent (auditor), one command (entry point). |
| Findings format | Two sections — Missed Unification and Wrong Abstractions — each with severity, file:line evidence, why-it-is-a-problem narrative, suggested direction (not a refactoring plan), reference link to the matching pattern in the knowledge base. Plus a third section for confidence and gaps. |
| Refactoring guidance | Report-only. Suggested direction names the target layer (e.g. "extract into LLMService") but does not produce code or step-by-step migration. |
| Language | English for all plugin-facing content (frontmatter, trigger keywords, SKILL.md prose, agent prompts, command docs, report output). The agent may respond in Italian or other languages when the user explicitly asks. |

## Plugin layout

```
plugins/abstraction-architect/
  agents/
    abstraction-architect.md
  commands/
    audit.md
  skills/
    abstraction-architect/
      SKILL.md
      references/
        theory.md
        unification-patterns.md
        anti-patterns.md
        decision-frame.md
        further-reading.md
```

## Component specifications

### Skill: `abstraction-architect:abstraction-architect`

Knowledge base, progressively disclosed. `SKILL.md` is the entry point: short frontmatter (name, description with TRIGGER WHEN / DO NOT TRIGGER WHEN), short body that lists the references and tells the consumer which file to load for which question.

**SKILL.md body sections:**
- When to use this skill
- Reference index (one line per reference file describing its purpose)
- The single load-bearing rule of thumb: *"when X changes, where do I have to touch? if N grows with features, candidate for unification; if every new requirement adds a flag to a shared layer, candidate for decomposition"*

**`references/theory.md`** — the principles. Rule of Three (with attribution to Roberts & Johnson 1996 and Fowler's *Refactoring*), DRY vs WET vs AHA, Metz's Wrong Abstraction thesis, Locality of Behaviour as the counter-force to DRY, Bounded Contexts from DDD as the seam for *what NOT to unify*, Beck's Tidy First options-framing (an abstraction has an upfront coupling cost and a future option value; both must be estimated), CUPID as a continuous-properties alternative to SOLID's binary rules. Each principle gets two paragraphs maximum and a one-line operational rule.

**`references/unification-patterns.md`** — 12 canonical "essential duplication" cases that justify unification. Each case: name, structural signature (what the duplicated code looks like), why unification is right (which forces want it to change together), the suggested target layer, common pitfalls when implementing the unification.
1. External-service / SDK wrapper (LLMService, HTTP client) — auth, retry, timeout, cost tracking, vendor switch
2. Schema validation at boundaries (Pydantic / Zod)
3. Authorization / permission checks
4. Money arithmetic (Decimal, precision, rounding mode, currency conversion)
5. Date / timezone boundary conversion
6. Pagination / cursor encoding
7. Connection pool / unit of work
8. Structured logging and correlation IDs
9. Error envelope toward clients
10. Feature flag and config reader
11. Retry / backoff policy
12. Observability (metrics, tracing context propagation)

**`references/anti-patterns.md`** — 12 canonical "wrong abstraction" cases. Each case: name, structural signature, why it is wrong, how to escape (inline, decompose, replace with explicit duplication), retrospective indicator that the abstraction has gone bad.
1. God service / `utils` dumping ground
2. Flag-soup function (8+ boolean parameters)
3. Premature interface (one implementation, no substitution use case)
4. Generic Repository<T> over an ORM
5. Speculative generality (extension points never used)
6. Leaky abstraction exposing vendor-specific types or errors
7. Strategy pattern for two strategies (where if/else was enough)
8. Premature event bus / pub-sub between two modules
9. Internal DSL or rules engine for a finite set of hardcoded cases
10. Test setup helpers grown into 12-parameter fixture factories
11. Universal entity/DTO mapper via reflection
12. Configuration abstraction that hides important runtime choices

**`references/decision-frame.md`** — the operational classifier the agent uses. Pre-flight questions:
- *When X changes, where do I have to touch?* If "N places and N grows with features" → unification candidate.
- *Has this pattern appeared 3 or more times?* The Rule of Three filter. Two is coincidence; three is a pattern.
- *Will the two sites ever diverge under realistic future requirements?* If yes, the duplication is essential, not accidental — leave it.
- *Are these two sites in different bounded contexts?* If yes, do not unify even if they look identical today.
- *Does each new requirement add a flag, branch, or parameter to a shared layer?* If yes, that layer is a wrong abstraction — inline or decompose.
- *Could a future reader understand the call site without chasing definitions across files?* If no, Locality of Behaviour is being violated — consider whether the abstraction is worth its cognitive cost.

**`references/further-reading.md`** — the verified list from the deep-research pass. Canonical (Metz, Dodds, Gross, North, Refactoring.guru on Speculative Generality, Fowler on Bounded Context, Beck on preparatory refactoring), war stories (Abramov "Goodbye Clean Code", HN consensus thread, Swett's respectful dissent, Rickard's "DRY Considered Harmful", DEV "Shared Library is a Lie"), recent framings (Beck's *Tidy First?* substack, Frontend at Scale "Too General Too Soon", CppCon 2024 cost-of-abstractions talk), Italian-language DDD resources (Avanscoperta, MokaByte, Intre.it), books (99 Bottles of OOP, Tidy First?, the Blue Book and IDDD, Refactoring), conference talks (Metz RailsConf 2014, Acton CppCon 2014, Beck on InfoQ). URLs that were search-snippet-only during research are flagged with a verify-before-citing note.

### Agent: `abstraction-architect`

**Role:** adversarial auditor for missed unification and wrong abstraction. Primary reasoning is *semantic*, grounded in deep-dive's structured output rather than lexical pattern-matching on source files. The agent may open individual source files via Read or Grep only to verify a candidate finding's file:line citations and confirm the structural shape claimed by deep-dive.

**Frontmatter:**
- `name: abstraction-architect`
- `description: >` multiline with TRIGGER WHEN (the user asks to audit a codebase for missed unification or wrong abstractions, evaluate architectural debt around layering, find candidates for centralization, find god services to decompose, find premature abstractions to inline; spawned by the `/abstraction-architect:audit` command after deep-dive output is ready) / DO NOT TRIGGER WHEN (the task is implementation, code formatting, security-only review — use `senior-review:security-auditor`, distributed-flow tracing — use `senior-review:distributed-flow-auditor`, or pattern-consistency review without an architecture lens — use `senior-review:code-auditor`).
- `tools: Read, Glob, Grep, Write`
- `model: opus`
- `color: orange`

**Inputs:**
- Path of the codebase root (from the command).
- Path of the `.deep-dive/` directory.
- Optional scope path (limit analysis to a subtree).
- Optional severity floor and focus filter.

**Inputs read from deep-dive:**
- `.deep-dive/01-structure.md` — modules, classes, file sizes, method counts. Used to find god services (high method count, broad responsibility) and `utils` dumping grounds (catch-all naming + high churn).
- `.deep-dive/02-interfaces.md` — public APIs. Used to find premature interfaces (one implementation), leaky abstractions (vendor types crossing the boundary), flag-soup functions (parameters with many boolean flags).
- `.deep-dive/03-flows.md` — call graphs. Used to find missed unification: N call sites following the same structural shape across modules.
- `.deep-dive/04-semantics.md` — responsibilities and intent. Used to find boundary violations (domain logic in infrastructure, infrastructure leak in domain).
- `.deep-dive/08-interconnect-map.md` if present (produced by `team-deep-dive`) — cross-partition contracts and invariants. Used to find bounded-context fusion.

**Process:**
1. Load the `abstraction-architect:abstraction-architect` skill.
2. Read the deep-dive files. If any expected file is missing, record it in Gaps and continue with degraded confidence on findings that depend on it.
3. Walk the structure / interfaces / flows / semantics looking for the 24 canonical patterns (12 unification + 12 anti). For each potential match, apply the decision-frame filter (Rule of Three, "do these sites change together", bounded-context check) before promoting it to a finding.
4. Calibrate severity:
   - **High** when the missed unification or wrong abstraction creates security risk (e.g. authorization check duplicated), data-correctness risk (money / date / currency), or operational risk (multiple incompatible retry policies on the same external service).
   - **Medium** when it creates maintenance drag (god service, flag soup, premature interface) but no immediate failure mode.
   - **Low** when it is a code-smell with no concrete pressure to fix it now.
   - Default to Medium when in doubt. High is reserved for findings the agent can argue for in one paragraph.
5. Write the report to `.abstraction-architect/findings.md`.

**Output report structure:**

```
# Abstraction-architect findings

**Generated:** <ISO timestamp>
**Codebase scope:** <path>
**Deep-dive source:** <.deep-dive/ path>
**Severity floor:** <medium | low | high>
**Focus:** <both | unification | wrong-abstraction>

## Summary
- N findings total (H high, M medium, L low)
- Top 3 findings by severity (one line each)

## A. Missed Unification

### A1. <Pattern name> — <severity>
- **Pattern:** <canonical name from unification-patterns.md>
- **Evidence:**
  - file/path/one.py:42-58
  - file/path/two.py:114-126
  - file/path/three.py:201-220
- **Why this is a problem:** <1-2 sentences citing the force that wants these to change together>
- **Suggested direction:** <e.g. "extract a vendor-agnostic LLMService that owns model selection, auth, retry, cost tracking">
- **Reference:** see `references/unification-patterns.md` -> External-service / SDK wrapper

### A2. ...

## B. Wrong Abstractions

### B1. <Pattern name> — <severity>
- **Pattern:** <canonical name from anti-patterns.md>
- **Evidence:** <file:line citations>
- **Why this is a problem:** <1-2 sentences>
- **Suggested direction:** <inline / decompose / replace with explicit X>
- **Reference:** see `references/anti-patterns.md` -> God service

### B2. ...

## C. Confidence and Gaps

- **High confidence:** findings supported by 2+ deep-dive files
- **Medium confidence:** findings supported by 1 deep-dive file
- **Low confidence / heuristic:** findings flagged by a single signal, worth manual verification
- **Gaps:** deep-dive files that were missing or empty, with the analyses they would have enabled
```

**Constraints:**
- Report-only. The agent must not edit any file outside `.abstraction-architect/`.
- Findings citing fewer than 3 sites under the missed-unification category must be downgraded to Low or omitted (Rule of Three).
- Suggested direction names the target layer or refactoring move; it does not produce code, file lists, or migration steps.
- File:line citations come from deep-dive output where present. When deep-dive cites a module or class without precise line ranges, the agent opens the file via Read and reports a tight line range covering the relevant block, not the whole file.

### Command: `/abstraction-architect:audit`

**Frontmatter:**
- `description:` "Audit a codebase for missed unification opportunities and wrong abstractions. Auto-launches deep-dive-analysis when `.deep-dive/` is missing."
- `argument-hint:` `[path] [--scope <subpath>] [--severity-floor low|medium|high] [--focus unification|wrong-abstraction|both]`

**Flow:**
1. Resolve `[path]` (default: current working directory).
2. Check for `.deep-dive/` containing at minimum `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`.
3. If missing or incomplete:
   - Print status message: "No deep-dive output found at `.deep-dive/`. Launching `/deep-dive-analysis:deep-dive-analysis` first. This may take several minutes on a large codebase."
   - Invoke `/deep-dive-analysis:deep-dive-analysis` automatically. No confirmation prompt.
   - If deep-dive fails, abort with a clear error and the path of the deep-dive log.
4. Spawn the `abstraction-architect` agent via the `Agent` tool, passing the codebase path, the `.deep-dive/` path, and any scope / severity-floor / focus flags.
5. The agent writes `.abstraction-architect/findings.md`.
6. Print to the user:
   - The path of the report.
   - The summary counts (total / high / medium / low).
   - The top 3 high-severity findings as a one-line preview.

**Edge cases:**
- `--scope <subpath>` limits the agent's analysis to a subtree. Deep-dive is still run on the full codebase (deep-dive's own decomposition logic decides scope); the agent filters findings to those whose evidence falls inside `<subpath>`.
- `--severity-floor` defaults to `medium`. Setting it to `low` includes the noise tier.
- `--focus` defaults to `both`. Setting it restricts the agent to one of the two finding categories.

## Marketplace registration

Add to `.claude-plugin/marketplace.json`:

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

Bump `metadata.version` by minor (this is a new plugin: `2.X.0` → `2.(X+1).0`; exact starting value will be read from `marketplace.json` at implementation time).

## Out-of-scope features deferred to v2 or later

- `/abstraction-architect:plan-refactor <finding-id>` — generate a detailed step-by-step refactoring plan for a single finding. Out for v1 because the surface of "how to refactor" is large enough to deserve its own design pass.
- AST-level detection independent of deep-dive (would let the plugin run standalone but doubles the implementation surface).
- Multiple specialized auditor agents (split `abstraction-architect` into `unification-detector` and `wrong-abstraction-detector` if the single-agent prompt grows past comfort). Defer until a real prompt-size pain point appears.
- Web-fetch verification of further-reading URLs at audit time (overkill for a report).
- Integration with `senior-review:full-review` and `agent-teams:team-review` as a registered always-on dimension. Reasonable next step but defer until v1 has run on at least one real codebase.

## Acceptance criteria

The plugin is considered done for v1 when:

1. The directory `plugins/abstraction-architect/` exists with the layout above and all six reference files are populated with real content (no placeholders).
2. The plugin is registered in `.claude-plugin/marketplace.json` with `dependencies: ["deep-dive-analysis"]`.
3. Running `/abstraction-architect:audit` in a codebase that already has `.deep-dive/` produces a `.abstraction-architect/findings.md` that follows the report structure above, with at least one finding correctly classified across both categories on a non-trivial test codebase.
4. Running `/abstraction-architect:audit` in a codebase *without* `.deep-dive/` automatically launches deep-dive first, then produces the findings report. No confirmation prompts.
5. `metadata.version` in `marketplace.json` is bumped and the commit message follows the project convention.

## Open risks

- **Risk of over-flagging in v1.** Without prior calibration on real codebases, the agent may flag too many low-confidence patterns. Mitigation: severity floor defaults to `medium`, the report's Confidence section makes the agent's uncertainty explicit, and findings without 3+ evidence sites are auto-downgraded.
- **Risk of false confidence in deep-dive output.** If deep-dive's semantic analysis is wrong on a given codebase (e.g. misclassifies an infrastructure module as domain), the abstraction-architect agent inherits that mistake. Mitigation: the Confidence and Gaps section flags which deep-dive files were used for each finding, so the user can cross-check.
- **Risk of the suggested direction being too vague to act on.** "Extract into LLMService" without a refactoring plan may not give the user enough to start. Mitigation: this is the intentional v1 / v2 split. The user gets a curated finding list now; the refactoring-plan command comes later.
- **Risk of overlap with `senior-review:code-auditor`.** That agent already does pattern-consistency review and detects some of these patterns at a lower granularity. Mitigation: positioning is different — code-auditor is general code-quality, abstraction-architect is pure-architecture and grounded in the canonical literature. The `description` frontmatter routing on both agents should make this distinction explicit.
