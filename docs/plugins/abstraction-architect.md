# Abstraction Architect Plugin

> Pure-architecture auditor for the two opposite failure modes of abstraction: missed unification (cross-cutting concerns scattered across call sites that should be a single layer) and wrong abstractions (god services, flag-soup functions, premature interfaces, leaky abstractions). Report-only, grounded in canonical theory (Metz's Wrong Abstraction, Beck's Tidy First, Fowler's bounded contexts, Gross's Locality of Behaviour).

## Prerequisites

The `deep-dive-analysis` plugin is a hard dependency: the global audit consumes `.deep-dive/` output and `/abstraction-architect:audit` auto-launches deep-dive when that output is missing. Diff mode degrades gracefully without it.

## Agents

### `abstraction-architect`

Adversarial auditor with two modes. Global mode reads `.deep-dive/` output and hunts whole-codebase failures. Diff mode anchors on newly written code and searches the rest of the codebase for prior art, answering one question: was this code already available, or did it just become the occurrence that justifies unifying?

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Glob, Grep, Bash, Write |
| **Use for** | Missed-unification and wrong-abstraction audits, prior-art checks on changed code, bounded-context fusion detection |

**Invocation:**
```
Use the abstraction-architect agent to audit [path] for missed unification and wrong abstractions
```
Also spawned by `/abstraction-architect:audit` and, in diff mode, as the Abstraction dimension of `/agent-teams:team-review` and `/senior-review:code-review`.

**Key behaviors (global mode):**
- Reads `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`, plus `08-interconnect-map.md` when `/agent-teams:team-deep-dive` produced it
- Three passes: missed unification (call-site clusters sharing a structural shape), wrong abstraction (god services, `utils` dumping grounds, flag-soup functions, premature interfaces), boundary violations (responsibility vs dependency mismatches, bounded-context fusion)
- Applies the Rule of Three: clusters with fewer than three sites are downgraded or dropped
- Writes the report to `.abstraction-architect/findings.md`

**Key behaviors (diff mode):**
- Extracts the added units from the diff, then hunts prior art three ways: by name (near-synonym identifiers), by shape (distinctive literals: regexes, magic numbers, endpoint paths, error strings), by call (same external call with the same parameters)
- Classifies each added unit: R1 exact prior art, R2 near prior art, R3 third occurrence (the Rule of Three fires on this diff), R4 second occurrence (noted, not flagged), R5 new wrong abstraction
- Search space is the whole codebase, never just the changed files: the prior art it hunts is by definition outside the diff
- Needs only `01-structure.md` and `02-interfaces.md` (lite deep-dive is enough); runs on Glob and Grep alone at reduced confidence when no deep-dive output exists
- Opens and compares every claimed prior-art site before reporting; matching names alone are never enough
- Writes the report to `.abstraction-architect/findings-diff.md`, or wherever the calling review pipeline directs it

**Severity model:** High for security, data-correctness, or operational risk (in diff mode, R1/R3 findings touching auth, money, or data correctness); Medium for maintenance drag (default); Low for code smell without concrete pressure.

## Skills

### `abstraction-architect`

Knowledge base for the unify-versus-duplicate decision. Covers the canonical theory (Rule of Three, DRY/WET/AHA, Wrong Abstraction, Locality of Behaviour, Bounded Contexts, Tidy First options framing, CUPID vs SOLID), 12 essential-duplication patterns that justify unification, 12 wrong-abstraction patterns that justify inlining or decomposition, an operational decision frame, and a verified reading list.

References, loaded on demand by the agent: `theory.md`, `unification-patterns.md`, `anti-patterns.md`, `decision-frame.md`, `further-reading.md`.

## Commands

### `/audit`

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --diff                             # did the code I just wrote already exist?
/abstraction-architect:audit --diff origin/master               # same, against an explicit base ref
/abstraction-architect:audit --severity-floor high --focus unification
```

| Flag | Effect |
|------|--------|
| `--diff [<base-ref>]` | Diff-anchored mode: prior-art hunt for the changed code instead of a whole-codebase audit. Skips the deep-dive auto-launch. Base ref defaults to the merge base with the default branch |
| `--scope <subpath>` | Limit findings to a subtree |
| `--severity-floor low\|medium\|high` | Drop findings below this severity (default `medium`) |
| `--focus unification\|wrong-abstraction\|both` | Restrict to one category (default `both`). Under `--diff`, `unification` maps to classes R1-R4 and `wrong-abstraction` to R5 |

Without `--diff`, the command checks for `.deep-dive/` and auto-launches `/deep-dive-analysis:deep-dive-analysis` when it is missing or incomplete. Report-only: no file outside `.abstraction-architect/` is ever edited, and the suggested direction in each finding is one sentence, not a refactoring plan.

## Ecosystem integration

- **`/agent-teams:team-review`** activates the agent in diff mode as the conditional Abstraction dimension whenever the review target resolves to a diff that adds code and this plugin is installed. Plain file/directory targets skip the dimension and point here instead.
- **`/senior-review:code-review`** runs it as Agent J (Abstraction & Reuse Review) under the same conditions.
- **`senior-review:code-auditor`** keeps the single-file abstraction smells (leaky abstractions, premature interfaces, god objects); this agent owns the cross-file reuse question. The dedup boundary is declared on both sides.
- **`/agent-teams:team-deep-dive`** adds `08-interconnect-map.md` to the deep-dive output, which enables the bounded-context fusion findings in global mode.

**Related:** [deep-dive-analysis](deep-dive-analysis.md) (produces the `.deep-dive/` input) | [agent-teams](agent-teams.md) (`/team-review` Abstraction dimension) | [senior-review](senior-review.md) (code-review Agent J, code-auditor dedup boundary) | [clean-code](clean-code.md) (readability cleanup, different concern)
