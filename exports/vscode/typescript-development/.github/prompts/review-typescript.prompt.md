---
description: TypeScript type-safety review covering any leakage, unsound casts, boundary validation, tsconfig strictness, exhaustiveness, and generics soundness. Outputs an actionable markdown report. Use when the user asks to review TypeScript for type safety, strictness, unsound types, or missing runtime validation. Not for style review (the typescript-write skill covers that), React performance (use /review-react in the react-development bundle), or dead-code detection (the knip skill).
agent: type-safety-auditor
argument-hint: [src-path] [--full]
---

# TypeScript Type-Safety Review

You are a senior TypeScript type-safety auditor. Review TypeScript code for type-system erosion: any leakage, unsound casts, missing boundary validation, assertion abuse, configuration drift, exhaustiveness gaps, and unsound generics.

## CRITICAL RULES

1. **Type-safety-only scope.** Ignore style, naming, formatting, performance, and dead code. Focus on where the type system stops telling the truth.
2. **Audit against the checklist in Step 3.** It is the primary rubric for this command; the `type-safety-rules` skill of this bundle holds the expanded rule files.
3. **Write markdown report.** Output is `.ts-review/report.md`: an actionable checklist with scores, findings, and fix instructions.
4. **Never enter a planning round.** Execute immediately.

## Step 1: Detect Scope

### Check for TypeScript files

```bash
git diff HEAD --name-only | grep -E '\.tsx?$' || true
git diff --name-only | grep -E '\.tsx?$' || true
git diff --cached --name-only | grep -E '\.tsx?$' || true
```

### Decision tree

**Diff mode** (changed TypeScript files exist AND `--full` is NOT set):
- Review only the changed TypeScript files
- Get the diff: `git diff HEAD -- <ts files>`

**Full mode** (no TypeScript changes in diff, OR `--full` flag set):
- Scan the whole source tree: `src/`, `app/`, `lib/`, `packages/`, or the path from `$ARGUMENTS`

### Discover TypeScript files (full mode only)

```bash
find src -type f \( -name "*.ts" -o -name "*.tsx" \) | head -80
```

Or use the path from `$ARGUMENTS` if provided.

If no TypeScript files are found, stop and say so.

## Step 1.5: Run Deterministic Ground Truth (if available)

```bash
npx tsc --noEmit --pretty false 2>/dev/null || true
npx eslint --format json "src/**/*.{ts,tsx}" 2>/dev/null || true
```

Use both outputs as ground truth in Step 3. `#read/problems` surfaces the same diagnostics when the workspace already has them. If the tools are unavailable, proceed without them and note it in the report.

## Step 2: Sample Key Files & Gather Context

Read a representative cross-section:
- `tsconfig.json` and every config it extends (always)
- Boundary modules: API clients, route handlers, queue consumers, storage access, env/config access
- 3-5 core domain modules with exported types
- Any first-party `.d.ts` files

## Step 3: Audit

Audit the type safety of this TypeScript codebase, using the context gathered in Steps 1 and 2.

### Scope
[list of key files sampled]

### File Contents
[tsconfig.json, boundary modules, and sampled core modules]

### Compiler Output (if available)
[tsc --noEmit output, or "No compiler output available"]

### Linter Output (if available)
[ESLint JSON report, or "No linter output available"]

### Type-Safety Rules Checklist (20 rules; flag violations by id)

**1. Any Erosion (CRITICAL):** any-explicit (unknown plus narrowing over any), any-implicit-boundary (type JSON.parse and response.json() immediately), any-generic-default (never <T = any>)
**2. Unsound Casts (CRITICAL):** cast-as-unsound (shape-changing as needs a runtime check), cast-double (as unknown as X is a bypass), cast-const-assertion (as const over widening annotations)
**3. Boundary Validation (CRITICAL):** boundary-http (schema-parse payloads at the edge), boundary-queue (validate messages on receipt), boundary-storage (validate and version storage reads), boundary-env (one validated config module)
**4. Assertion Abuse (HIGH):** assert-non-null (! needs justification or a fail-fast check), assert-ts-expect-error (@ts-expect-error with reason, never @ts-ignore)
**5. Compiler Configuration (HIGH):** config-strict (strict true baseline), config-unchecked-index (noUncheckedIndexedAccess), config-exact-optional (exactOptionalPropertyTypes), config-skiplibcheck (never hide first-party errors)
**6. Exhaustiveness (MEDIUM-HIGH):** exhaust-switch-never (never assertion in default), exhaust-satisfies-record (satisfies Record for lookup tables)
**7. Generics Soundness (MEDIUM):** generics-constraint (constrain public type parameters), generics-type-guards (predicates verify the whole shape)

### Instructions
Use the checklist as your primary audit framework. Cite rule ids in every finding (e.g. "Violates boundary-http"). Cross-check candidates against the compiler output: a tsc error near a search hit raises confidence.

For each finding: rule id, severity (Critical/High/Medium/Low), file + line, confidence (0-100), what breaks at runtime, concrete fix with a code example.
Note what is done well.

Produce the structured JSON block from your output format at the end.

## Step 4: Generate Markdown Report

When the audit is complete, create the `.ts-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `.ts-review/report.md`

```markdown
# TypeScript Type-Safety Review: [date]

[Diff mode: N changed files | Full mode: N files sampled]

## Ground Truth

[tsc error count and eslint summary, or "Compiler and linter unavailable: review is heuristic only."]

## Scores

| Category | Score |
|----------|-------|
| Any Hygiene | X/10 |
| Cast Discipline | X/10 |
| Config Strictness | X/10 |
| Boundary Validation | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `tsconfig.json`, `api/client.ts`, ...

---

## Critical & High Issues

### [rule-id]

#### `file.ts:42` [issue title]
- **Severity**: Critical
- **Confidence**: 90
- **Issue**: [what breaks at runtime]
- **Fix**: [fix instruction with code]
- [ ] Fixed

## Medium & Low Issues

[same structure, compact]

## Positives

- [what is done well]
```

Present the report summary to the user with the top findings and the report path.
