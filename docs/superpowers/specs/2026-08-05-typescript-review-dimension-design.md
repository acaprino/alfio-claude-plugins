# TypeScript Review Dimension Design

Date: 2026-08-05
Status: approved, pending implementation plan

## Goal

Bring TypeScript to full parity with React in the review layer. React today has a specialist reviewer agent in its domain plugin, a granular rules skill, a standalone review command, and conditional wiring in both `/senior-review:team-review` and `/senior-review:code-review`. TypeScript has only read-if-present knowledge-base pointers. This design gives TypeScript the same four-piece shape.

## Decisions taken during brainstorming

1. **Charter: type-safety auditor.** The dimension hunts type-system erosion only. Style belongs to `typescript-write`, performance to `react-development`, dead code to `knip` and the hygiene dimension. A narrow charter mirrors React's performance-only charter and keeps findings orthogonal to the always-on dimensions.
2. **A dedicated rules skill is created.** Full structural symmetry with `react-best-practices` (one file per rule) rather than reusing `typescript-write` or extending it with a review mode.
3. **Full mirror of the React shape** (approach 1 of 3): agent, rules skill, standalone command, and senior-review wiring. Dimension-only and auditor-inside-senior-review variants were rejected because they break parity or the 16.0.0 dependency-tree shape.

## Components

### 1. Agent: `plugins/typescript-development/agents/type-safety-auditor.md`

Adversarial reviewer with a narrow charter. Frontmatter: `model: inherit`, `color: blue` (matching `typescript-engineer`), `tools: Read, Write, Glob, Grep, Bash`, description in YAML `>` form with TRIGGER WHEN and DO NOT TRIGGER WHEN clauses.

Hunts, in order of severity:

- `any` erosion: explicit `any`, implicit `any` at untyped boundaries (`JSON.parse`, `fetch`, `catch` clauses), `any` as generic default
- Unsound casts: `as` casts that change the type without a runtime check, double casts (`as unknown as X`)
- Assertion abuse: non-null assertion `!` without an adjacent invariant justification, `@ts-ignore` (prefer `@ts-expect-error` with reason)
- tsconfig strictness drift: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` missing or disabled; `skipLibCheck` used to mask first-party errors
- Non-exhaustive handling: discriminated unions switched without a `never` default; record completeness without `satisfies`
- Missing runtime validation at boundaries: HTTP payloads, queue and event messages, storage and file reads, `process.env` access without a schema (Zod or Valibot)
- Generics misuse: unconstrained type parameters leaking into public APIs, unsound type guards and predicates

DO NOT TRIGGER WHEN: style and naming review (use `typescript-write`), React performance (use `react-development:react-performance-optimizer`), dead-code hunting (use the `knip` skill or the hygiene dimension).

Output: the structured findings format that team-review consolidates (finding title, file:line, severity, confidence, concrete fix). Loads the `type-safety-rules` skill as its knowledge base and may consult `mastering-typescript` references.

### 2. Skill: `plugins/typescript-development/skills/type-safety-rules/`

Mirrors the `react-best-practices` layout: `SKILL.md` index with TRIGGER WHEN frontmatter, `rules/_template.md`, `rules/_sections.md`, and one file per rule with a wrong example, a right example, and a detection hint. Initial set of 20 rules across 7 sections:

| Section | Rules |
|---|---|
| any | `any-explicit`, `any-implicit-boundary`, `any-generic-default` |
| cast | `cast-as-unsound`, `cast-double`, `cast-const-assertion` |
| assert | `assert-non-null`, `assert-ts-expect-error` |
| config | `config-strict`, `config-unchecked-index`, `config-exact-optional`, `config-skiplibcheck` |
| exhaust | `exhaust-switch-never`, `exhaust-satisfies-record` |
| boundary | `boundary-http`, `boundary-queue`, `boundary-storage`, `boundary-env` |
| generics | `generics-constraint`, `generics-type-guards` |

The skill is usable standalone (a user can load it while writing TS) and is the agent's rule source during review.

### 3. Command: `plugins/typescript-development/commands/review-typescript.md`

Mirror of `/react-development:review-react`, adapted to the type-safety charter:

- **Step 1, scope detection**: diff mode when `git diff` shows changed `.ts`/`.tsx` files and `--full` is not set; full mode otherwise (scan `src/` or the path from `$ARGUMENTS`). Stop with a message if no TypeScript files are found.
- **Step 1.5, deterministic ground truth**: `npx tsc --noEmit` and ESLint JSON output when available; pass both to the agent. If the tools are unavailable, proceed without and note it in the report.
- **Step 2, sample key files**: `tsconfig.json`, boundary modules (API clients, queue consumers, storage access), representative core modules.
- **Step 3, spawn** `typescript-development:type-safety-auditor` with the samples and ground truth.
- **Step 4, report**: actionable markdown checklist in `.ts-review/report.md` with scores, findings, and fix instructions. Never enter plan mode.

Frontmatter: description with TRIGGER WHEN and DO NOT TRIGGER WHEN, `argument-hint: "[src-path] [--full]"`.

### 4. senior-review wiring

Two spawn sites, both with the skip note the dependency-graph linter requires (degrade-notes check):

- **`team-review.md`**: new row in the conditional-dimensions table. Signal: **TypeScript project**; detection rule: changed files match `\.tsx?$` AND `tsconfig.json` exists at the project root; requires the `typescript-development` plugin: when it is not installed, skip and note it under Skipped instead of spawning (the spawn would fail). Dimension activated: **TypeScript type safety**; agent: `typescript-development:type-safety-auditor`. The detection-implementation snippet gains one line (`echo "$CHANGED_FILES" | grep -qE '\.tsx?$' && [ -f tsconfig.json ] && echo "TS_PROJECT=true"`). The paragraph stating that four conditional dimensions live in optional-dependency plugins changes to five. The dimension-to-agent mapping table and the detection display example gain the `ts-safety` entry.
- **`code-review.md`**: new conditional agent block next to the React one, following the existing agent-letter sequence. Run only if the diff touches `.ts` or `.tsx` files AND `tsconfig.json` exists. Skip with the "optionalDependency, spawn would fail, report as skipped" note when the plugin is absent, exactly like the React block.

No `marketplace.json` dependency change: `typescript-development` is already listed in senior-review's `optionalDependencies`, and it remains a leaf plugin (no dependencies of its own), so no cycle is possible.

## Detection and flow

- Dimension id: `ts-safety` (consistent with `react-perf`, `ui-races`). Findings file: `.team-review/findings-ts-safety.md`.
- Findings pass through Phase 4 (dedup) and Phase 4b (adversarial verification) like every other dimension.
- On a React project both `react-perf` and `ts-safety` activate. This is intentional: the charters are orthogonal (performance vs type safety) and the consolidation phase deduplicates any collision.
- Degrade path: plugin absent produces `Skipped, plugin not installed: ts-safety (typescript-development)` in the detection display.

## Marketplace, exports, and docs impact

All in one commit, per the marketplace update workflow:

1. `plugins[].version`: `typescript-development` 2.1.4 to 2.2.0 (new agent, skill, and command registered in its manifest entry; description extended with the review capability); `senior-review` 7.2.0 to 7.3.0 (new conditional dimension).
2. `metadata.version`: minor bump (18.0.0 to 18.1.0 at the time of writing; use the current value at implementation time).
3. `exports/vscode/`: mirror both bundles by loading the `downstream-exports` skill; regenerate the extension manifest (a new agent and a new prompt are contributed); bump `exports/vscode/package.json`; add the changelog entry.
4. Docs: update `docs/plugins/typescript-development.md` and `docs/plugins/senior-review.md`.

## Verification

The repo has no runtime tests; verification is the four CI scripts, all green before commit:

1. `python scripts/lint_dependency_graph.py` (the two new spawn edges resolve against the existing optionalDependency; skip notes satisfy the degrade-notes check)
2. `python .claude/skills/downstream-exports/scripts/check_export.py`
3. `python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check`
4. `python scripts/check_version_bumps.py <base-rev>`

## Out of scope

- A CSS or design review dimension (delegated to impeccable upstream; deliberate blind spot of team-review)
- knip integration inside the dimension (dead code stays with the hygiene dimension and the standalone skill)
- TypeScript performance rules (JS performance rules already live in `react-best-practices`)
- Python parity (python-development has the same read-if-present status; a future pass can clone this shape)
