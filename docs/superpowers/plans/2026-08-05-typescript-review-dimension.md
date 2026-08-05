# TypeScript Review Dimension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give TypeScript a dedicated type-safety review dimension at full parity with React: a `type-safety-auditor` agent, a 20-rule `type-safety-rules` skill, a `/review-typescript` command, and conditional wiring in `/senior-review:team-review` and `/senior-review:code-review`.

**Architecture:** Mirror of the React shape. The specialist reviewer lives in the domain plugin (`typescript-development`), `senior-review` spawns it as a conditional dimension and degrades with a skip note when the plugin is absent. `typescript-development` is already in senior-review's `optionalDependencies` and stays a leaf plugin, so the dependency graph does not change.

**Tech Stack:** Markdown plugin content only. Verification is mechanical: the four stdlib-only Python CI scripts plus structural greps.

**Spec:** `docs/superpowers/specs/2026-08-05-typescript-review-dimension-design.md`

## Global Constraints

- No dash-asides anywhere in authored content: no em dash, no ` -- `, no spaced-hyphen parentheticals. Use colons, parentheses, or separate sentences. Hyphenated compounds (`type-safety`, `read-if-present`) are fine.
- Agent frontmatter: `model: inherit`, `color` from the allowed set (`blue` here), long descriptions in YAML `>` form with TRIGGER WHEN and DO NOT TRIGGER WHEN clauses, kebab-case name matching the filename.
- Body style: terse keyword lists, imperative tone, markdown headers.
- Dimension id everywhere: `ts-safety`. Dimension display name: `TypeScript type safety`. Agent reference: `typescript-development:type-safety-auditor`.
- Versions: `typescript-development` 2.1.4 to 2.2.0, `senior-review` 7.2.0 to 7.3.0, `metadata.version` 18.0.0 to 18.1.0. If master moved since this plan was written, re-read the current values and bump the same increments.
- Single final commit: CLAUDE.md's marketplace workflow overrides the per-task commit habit. Tasks 1 through 11 only write files; Task 12 stages plugin files, `marketplace.json`, `exports/`, and docs together in ONE commit and pushes.
- This repo has no runtime tests. Each task ends with a mechanical verification step instead of a test run.
- Every new senior-review spawn site of the optional agent MUST carry a nearby skip note, or `lint_dependency_graph.py` fails its degrade-notes check.

---

### Task 1: `type-safety-rules` skill scaffolding

**Files:**
- Create: `plugins/typescript-development/skills/type-safety-rules/SKILL.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/_template.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/_sections.md`

**Interfaces:**
- Produces: the skill name `type-safety-rules`, the seven section prefixes (`any-`, `cast-`, `boundary-`, `assert-`, `config-`, `exhaust-`, `generics-`), and the 20 rule ids listed in SKILL.md. Tasks 2 to 4 create exactly these rule files; Tasks 5 and 6 cite these rule ids verbatim.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: type-safety-rules
description: >
  TypeScript type-safety review rules: 20 rules across 7 categories covering any erosion, unsound casts, missing boundary validation, assertion abuse, tsconfig strictness, exhaustiveness, and generics soundness.
  TRIGGER WHEN: reviewing TypeScript for type-safety issues, hardening types in existing code, or auditing a codebase for type-system erosion.
  DO NOT TRIGGER WHEN: style and naming review (use typescript-write), React performance (use react-development), or dead-code detection (use knip).
---

# TypeScript Type-Safety Rules

Review-oriented rule set for hunting type-system erosion in TypeScript codebases. 20 rules across 7 categories, prioritized by blast radius. Used as the audit checklist by the `type-safety-auditor` agent and usable standalone while writing or hardening TypeScript.

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Any Erosion | CRITICAL | `any-` |
| 2 | Unsound Casts | CRITICAL | `cast-` |
| 3 | Boundary Validation | CRITICAL | `boundary-` |
| 4 | Assertion Abuse | HIGH | `assert-` |
| 5 | Compiler Configuration | HIGH | `config-` |
| 6 | Exhaustiveness | MEDIUM-HIGH | `exhaust-` |
| 7 | Generics Soundness | MEDIUM | `generics-` |

## Quick Reference

### 1. Any Erosion (CRITICAL)

- `any-explicit` - Replace explicit `any` with `unknown` plus narrowing
- `any-implicit-boundary` - Type the results of `JSON.parse`, `response.json()`, and `catch` immediately
- `any-generic-default` - Never default a type parameter to `any`

### 2. Unsound Casts (CRITICAL)

- `cast-as-unsound` - An `as` cast that changes the shape needs a runtime check instead
- `cast-double` - `as unknown as X` is a type-system bypass; write a guard or converter
- `cast-const-assertion` - Use `as const` for literal narrowing instead of widening annotations

### 3. Boundary Validation (CRITICAL)

- `boundary-http` - Parse HTTP payloads with a schema at the edge
- `boundary-queue` - Validate queue and event messages before processing
- `boundary-storage` - Validate and version storage reads (localStorage, files, DB JSON)
- `boundary-env` - Access environment variables through one validated config module

### 4. Assertion Abuse (HIGH)

- `assert-non-null` - `!` needs an adjacent invariant justification or a fail-fast check
- `assert-ts-expect-error` - Use `@ts-expect-error` with a reason, never `@ts-ignore`

### 5. Compiler Configuration (HIGH)

- `config-strict` - `"strict": true` is the baseline
- `config-unchecked-index` - Enable `noUncheckedIndexedAccess`
- `config-exact-optional` - Enable `exactOptionalPropertyTypes`
- `config-skiplibcheck` - `skipLibCheck` may speed up third-party types, never hide first-party errors

### 6. Exhaustiveness (MEDIUM-HIGH)

- `exhaust-switch-never` - Discriminated unions get a `never` assertion in the default branch
- `exhaust-satisfies-record` - Use `satisfies Record<K, V>` for complete lookup tables

### 7. Generics Soundness (MEDIUM)

- `generics-constraint` - Constrain type parameters on public APIs
- `generics-type-guards` - A type predicate must verify the whole shape it claims

## How to Use

Read individual rule files in the `rules/` directory for detailed explanations and code examples. Each rule file contains a brief explanation, an incorrect example, a correct example, and a detection hint for reviewers.
```

- [ ] **Step 2: Write rules/_template.md**

````markdown
---
title: Rule Title Here
impact: MEDIUM
impactDescription: Optional description of impact (e.g., "prevents a class of runtime crashes")
tags: tag1, tag2
---

## Rule Title Here

**Impact: MEDIUM (optional impact description)**

Brief explanation of the rule and why it matters. Explain what breaks at runtime when the rule is violated.

**Incorrect (description of what's wrong):**

```typescript
// Bad code example here
const bad = example()
```

**Correct (description of what's right):**

```typescript
// Good code example here
const good = example()
```

**Detection:** How a reviewer finds violations (grep pattern or reading heuristic).
````

- [ ] **Step 3: Write rules/_sections.md**

```markdown
# Sections

Ordered by review priority. The prefix is the filename prefix of every rule in the section.

| Order | Section | Prefix | Impact | Rules |
|-------|---------|--------|--------|-------|
| 1 | Any Erosion | `any-` | CRITICAL | 3 |
| 2 | Unsound Casts | `cast-` | CRITICAL | 3 |
| 3 | Boundary Validation | `boundary-` | CRITICAL | 4 |
| 4 | Assertion Abuse | `assert-` | HIGH | 2 |
| 5 | Compiler Configuration | `config-` | HIGH | 4 |
| 6 | Exhaustiveness | `exhaust-` | MEDIUM-HIGH | 2 |
| 7 | Generics Soundness | `generics-` | MEDIUM | 2 |
```

- [ ] **Step 4: Verify**

Run: `ls plugins/typescript-development/skills/type-safety-rules/rules/`
Expected: `_template.md` and `_sections.md` exist; SKILL.md exists one level up. Confirm SKILL.md `name:` equals the directory name `type-safety-rules`.

---

### Task 2: Any Erosion and Unsound Casts rules (6 files)

**Files:**
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/any-explicit.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/any-implicit-boundary.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/any-generic-default.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/cast-as-unsound.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/cast-double.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/cast-const-assertion.md`

**Interfaces:**
- Consumes: the template from Task 1 (frontmatter fields `title`, `impact`, `impactDescription`, `tags`).
- Produces: rule files whose ids Tasks 5 and 6 cite.

- [ ] **Step 1: Write any-explicit.md**

````markdown
---
title: Replace explicit any with unknown plus narrowing
impact: CRITICAL
impactDescription: an any on a shared surface disables checking for every consumer
tags: any, unknown, narrowing
---

## Replace explicit any with unknown plus narrowing

**Impact: CRITICAL (an any on a shared surface disables checking for every consumer)**

`any` switches the compiler off for every expression it touches and propagates through assignments and returns. `unknown` keeps the compiler on: you must narrow before use, so mistakes surface at the boundary instead of deep in consuming code.

**Incorrect (any silences every downstream check):**

```typescript
function parseMessage(data: any) {
  return data.payload.items // no checking, crashes at runtime if shape differs
}
```

**Correct (unknown forces narrowing at the entry):**

```typescript
function parseMessage(data: unknown) {
  if (!isMessage(data)) throw new Error('malformed message')
  return data.payload.items
}
```

**Detection:** `rg -n ': any\b|<any>|as any\b' --type ts --glob '!*.d.ts'`. Severity rises with export visibility: an `any` on an exported function outranks one in a local helper.
````

- [ ] **Step 2: Write any-implicit-boundary.md**

````markdown
---
title: Type the results of JSON.parse, response.json(), and catch immediately
impact: CRITICAL
impactDescription: untyped ingress makes every downstream type a lie
tags: any, boundary, json
---

## Type the results of JSON.parse, response.json(), and catch immediately

**Impact: CRITICAL (untyped ingress makes every downstream type a lie)**

`JSON.parse` and `response.json()` return `any`. Assigning that result to a typed variable is an unchecked cast in disguise: the annotation asserts a shape nobody verified. Route the value through `unknown` and a schema or guard before it reaches typed code.

**Incorrect (the annotation asserts, nothing verifies):**

```typescript
const config: AppConfig = JSON.parse(raw)
startServer(config.port) // port may be undefined or a string
```

**Correct (parse to unknown, validate, then trust the type):**

```typescript
const parsed: unknown = JSON.parse(raw)
const config = AppConfigSchema.parse(parsed) // throws with a precise error on drift
startServer(config.port)
```

**Detection:** `rg -n 'JSON\.parse\(|\.json\(\)' --type ts`. Flag any hit whose result lands in a typed binding without a schema parse or guard between.
````

- [ ] **Step 3: Write any-generic-default.md**

````markdown
---
title: Never default a type parameter to any
impact: HIGH
impactDescription: the default silently applies wherever the caller omits the argument
tags: any, generics
---

## Never default a type parameter to any

**Impact: HIGH (the default silently applies wherever the caller omits the argument)**

`<T = any>` looks like flexibility but means every call site that omits the type argument gets unchecked results without opting in. Require the parameter, constrain it, or derive it from a runtime schema argument so the type and the validation cannot diverge.

**Incorrect (omitting the type argument silently yields any):**

```typescript
function loadCache<T = any>(key: string): T {
  return store.get(key)
}
const user = loadCache('user') // user: any
```

**Correct (the schema argument fixes T and validates at runtime):**

```typescript
function loadCache<T>(key: string, schema: z.ZodType<T>): T {
  return schema.parse(store.get(key))
}
const user = loadCache('user', UserSchema)
```

**Detection:** `rg -n '= any>' --type ts`. Also flag `<T = unknown>` on functions that then cast internally.
````

- [ ] **Step 4: Write cast-as-unsound.md**

````markdown
---
title: An as cast that changes the shape needs a runtime check instead
impact: CRITICAL
impactDescription: the cast asserts what only a check can know
tags: cast, as, validation
---

## An as cast that changes the shape needs a runtime check instead

**Impact: CRITICAL (the cast asserts what only a check can know)**

`value as T` tells the compiler to trust you without evidence. For data that originates outside the current module (API responses, deserialized payloads, DOM values), the honest options are a schema parse or a type guard. Reserve `as` for directions the compiler already knows are safe (widening to a supertype, `as const`).

**Incorrect (the response shape is asserted, never checked):**

```typescript
const user = (await res.json()) as User
sendEmail(user.email) // email may be missing entirely
```

**Correct (the schema proves the shape the type claims):**

```typescript
const user = UserSchema.parse(await res.json())
sendEmail(user.email)
```

**Detection:** `rg -n ' as [A-Z]' --type ts --glob '!*.test.*'`. Read each hit: casts of external data are findings; widening casts and `as const` are not.
````

- [ ] **Step 5: Write cast-double.md**

````markdown
---
title: as unknown as X is a type-system bypass
impact: CRITICAL
impactDescription: defeats assignability checking entirely between any two types
tags: cast, unknown, bypass
---

## as unknown as X is a type-system bypass

**Impact: CRITICAL (defeats assignability checking entirely between any two types)**

The compiler rejects a direct `as` between unrelated types precisely because it is never safe. `as unknown as X` launders the value through `unknown` to silence that rejection. Whatever made the direct cast illegal is still true at runtime. Write a converter function or a guard that constructs the target shape explicitly.

**Incorrect (two unrelated types force-bridged):**

```typescript
const req = event as unknown as HttpRequest
handle(req.headers) // headers does not exist on event
```

**Correct (an explicit converter states and checks the mapping):**

```typescript
function toHttpRequest(event: LambdaEvent): HttpRequest {
  return { headers: event.rawHeaders ?? {}, body: event.body ?? '' }
}
handle(toHttpRequest(event).headers)
```

**Detection:** `rg -n 'as unknown as' --type ts`. Every hit is a finding; the only acceptable ones live in test doubles, and even those deserve a comment.
````

- [ ] **Step 6: Write cast-const-assertion.md**

````markdown
---
title: Use as const for literal narrowing instead of widening annotations
impact: MEDIUM
impactDescription: preserves literal types that unions and lookups depend on
tags: cast, const, literals
---

## Use as const for literal narrowing instead of widening annotations

**Impact: MEDIUM (preserves literal types that unions and lookups depend on)**

Annotating a literal with a wide type (`string[]`, `Record<string, string>`) throws away the literal information the compiler inferred. `as const` keeps it, giving you free union types and readonly guarantees that downstream exhaustiveness checks rely on.

**Incorrect (the annotation widens and loses the literals):**

```typescript
const ROLES: string[] = ['admin', 'editor', 'viewer']
type Role = string // any string passes
```

**Correct (as const keeps the literals and derives the union):**

```typescript
const ROLES = ['admin', 'editor', 'viewer'] as const
type Role = (typeof ROLES)[number] // 'admin' | 'editor' | 'viewer'
```

**Detection:** Reading heuristic: literal arrays and objects annotated with wide types, then compared with `===` against specific members elsewhere.
````

- [ ] **Step 7: Verify**

Run: `ls plugins/typescript-development/skills/type-safety-rules/rules/ | grep -cE '^(any|cast)-'`
Expected: `6`

---

### Task 3: Boundary Validation and Assertion Abuse rules (6 files)

**Files:**
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/boundary-http.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/boundary-queue.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/boundary-storage.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/boundary-env.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/assert-non-null.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/assert-ts-expect-error.md`

**Interfaces:**
- Consumes: the template from Task 1.
- Produces: rule files whose ids Tasks 5 and 6 cite.

- [ ] **Step 1: Write boundary-http.md**

````markdown
---
title: Parse HTTP payloads with a schema at the edge
impact: CRITICAL
impactDescription: the API contract is enforced where the data enters, not assumed
tags: boundary, http, zod
---

## Parse HTTP payloads with a schema at the edge

**Impact: CRITICAL (the API contract is enforced where the data enters, not assumed)**

Request bodies and response payloads are `unknown` at runtime no matter what the client types say. One schema parse at the boundary turns drift into a precise error at the edge; without it, drift becomes an undefined-property crash three modules deep.

**Incorrect (the handler trusts the wire format):**

```typescript
app.post('/orders', (req) => {
  const order = req.body as Order
  charge(order.total) // total arrives as a string from this client
})
```

**Correct (the schema is the contract, parsed once at ingress):**

```typescript
app.post('/orders', (req) => {
  const order = OrderSchema.parse(req.body)
  charge(order.total)
})
```

**Detection:** Locate route handlers and API clients (`rg -n 'req\.body|\.json\(\)' --type ts`); flag any that reach typed code without a schema parse or guard.
````

- [ ] **Step 2: Write boundary-queue.md**

````markdown
---
title: Validate queue and event messages before processing
impact: CRITICAL
impactDescription: producers and consumers deploy independently; the schema is the only contract
tags: boundary, queue, events
---

## Validate queue and event messages before processing

**Impact: CRITICAL (producers and consumers deploy independently; the schema is the only contract)**

A queue consumer receives whatever an older or newer producer serialized. Typing the handler parameter is an assumption about a foreign deployment. Validate every message on receipt and route failures to a dead-letter path instead of letting a malformed message poison the handler mid-flight.

**Incorrect (the parameter type asserts a foreign producer's behavior):**

```typescript
channel.consume('orders', (msg: OrderCreated) => {
  reserveStock(msg.items)
})
```

**Correct (validate on receipt, dead-letter on failure):**

```typescript
channel.consume('orders', (raw: unknown) => {
  const result = OrderCreatedSchema.safeParse(raw)
  if (!result.success) return deadLetter(raw, result.error)
  reserveStock(result.data.items)
})
```

**Detection:** `rg -n 'consume\(|subscribe\(|on\(.message' --type ts`; flag handlers whose parameter is a domain type with no parse in the body.
````

- [ ] **Step 3: Write boundary-storage.md**

````markdown
---
title: Validate and version storage reads
impact: HIGH
impactDescription: stored data outlives the code that wrote it
tags: boundary, storage, localstorage
---

## Validate and version storage reads

**Impact: HIGH (stored data outlives the code that wrote it)**

localStorage, files, and JSON columns hold whatever an older version of the code serialized. A read is a boundary crossing: validate it like network input and version the shape so migrations are explicit rather than accidental.

**Incorrect (yesterday's shape crashes today's code):**

```typescript
const prefs = JSON.parse(localStorage.getItem('prefs') ?? '{}') as Prefs
render(prefs.theme.accent) // theme was a string in the previous release
```

**Correct (validate on read, fall back on drift):**

```typescript
const raw: unknown = JSON.parse(localStorage.getItem('prefs') ?? '{}')
const prefs = PrefsSchema.catch(DEFAULT_PREFS).parse(raw)
render(prefs.theme.accent)
```

**Detection:** `rg -n 'localStorage|sessionStorage|readFileSync.*json|JSON\.parse' --type ts`; flag reads that land in typed bindings unvalidated.
````

- [ ] **Step 4: Write boundary-env.md**

````markdown
---
title: Access environment variables through one validated config module
impact: HIGH
impactDescription: turns deploy-time misconfiguration into a startup error instead of a mid-request crash
tags: boundary, env, config
---

## Access environment variables through one validated config module

**Impact: HIGH (turns deploy-time misconfiguration into a startup error instead of a mid-request crash)**

`process.env.X` is `string | undefined` everywhere, which breeds scattered `!` assertions and silent fallbacks. One module that parses the whole environment at startup fails fast with a complete list of what is missing, and every consumer imports typed values.

**Incorrect (scattered access, assertion-silenced):**

```typescript
const db = connect(process.env.DATABASE_URL!)
const port = Number(process.env.PORT) // NaN when unset
```

**Correct (one schema, parsed once at startup):**

```typescript
// config.ts
export const env = z.object({
  DATABASE_URL: z.string().url(),
  PORT: z.coerce.number().default(3000),
}).parse(process.env)

// elsewhere
const db = connect(env.DATABASE_URL)
```

**Detection:** `rg -n 'process\.env\.' --type ts --glob '!**/config*'`; hits outside the config module are findings.
````

- [ ] **Step 5: Write assert-non-null.md**

````markdown
---
title: A non-null assertion needs an invariant justification or a fail-fast check
impact: MEDIUM
impactDescription: each unjustified ! is a deferred TypeError with no context
tags: assert, non-null
---

## A non-null assertion needs an invariant justification or a fail-fast check

**Impact: MEDIUM (each unjustified ! is a deferred TypeError with no context)**

`!` erases the compiler's warning that a value may be absent. When the invariant is real, state it in an adjacent comment. When it is not provable, replace the assertion with a check that throws a described error at the site instead of an anonymous TypeError later.

**Incorrect (the assertion hides the failure mode):**

```typescript
const user = users.get(id)!
notify(user.email) // TypeError far from the cause when id is stale
```

**Correct (fail fast with context, or justify the invariant):**

```typescript
const user = users.get(id)
if (!user) throw new Error(`unknown user id: ${id}`)
notify(user.email)
```

**Detection:** `rg -n '\w+!(\.|\)|,|;)' --type ts`. Hits without an adjacent invariant comment are findings; `!` immediately after a populate step with a stated invariant passes.
````

- [ ] **Step 6: Write assert-ts-expect-error.md**

````markdown
---
title: Use @ts-expect-error with a reason, never @ts-ignore
impact: HIGH
impactDescription: expect-error self-heals; ignore rots silently
tags: assert, suppression
---

## Use @ts-expect-error with a reason, never @ts-ignore

**Impact: HIGH (expect-error self-heals; ignore rots silently)**

`@ts-ignore` suppresses whatever error happens to be on the next line, forever, including new errors introduced later. `@ts-expect-error` fails the build when the suppressed error disappears, so stale suppressions clean themselves up. The reason text tells the next reader what was being suppressed and why.

**Incorrect (suppresses today's error and every future one):**

```typescript
// @ts-ignore
legacyInit(options)
```

**Correct (scoped, reasoned, self-expiring):**

```typescript
// @ts-expect-error legacyInit's .d.ts lags v4; remove after upstream #123
legacyInit(options)
```

**Detection:** `rg -n '@ts-ignore|@ts-nocheck' --type ts`: every hit is a finding. `rg -n '@ts-expect-error$' --type ts`: expect-error with no reason text is a lesser finding.
````

- [ ] **Step 7: Verify**

Run: `ls plugins/typescript-development/skills/type-safety-rules/rules/ | grep -cE '^(boundary|assert)-'`
Expected: `6`

---

### Task 4: Compiler Configuration, Exhaustiveness, and Generics rules (8 files)

**Files:**
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/config-strict.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/config-unchecked-index.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/config-exact-optional.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/config-skiplibcheck.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/exhaust-switch-never.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/exhaust-satisfies-record.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/generics-constraint.md`
- Create: `plugins/typescript-development/skills/type-safety-rules/rules/generics-type-guards.md`

**Interfaces:**
- Consumes: the template from Task 1.
- Produces: rule files whose ids Tasks 5 and 6 cite. Total rule count after this task: 20.

- [ ] **Step 1: Write config-strict.md**

````markdown
---
title: strict true is the baseline
impact: HIGH
impactDescription: without it every other type-safety rule is advisory
tags: config, strict
---

## strict true is the baseline

**Impact: HIGH (without it every other type-safety rule is advisory)**

`"strict": true` enables the checks the rest of this rule set assumes: `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `useUnknownInCatchVariables`, and the rest of the family. A codebase without it has null-safety and implicit-any holes everywhere the annotations look fine.

**Incorrect (defaults leave the compiler permissive):**

```json
{ "compilerOptions": { "target": "ES2022" } }
```

**Correct (strict on, gaps opted out locally and visibly if truly needed):**

```json
{ "compilerOptions": { "target": "ES2022", "strict": true } }
```

**Detection:** Read `tsconfig.json` and every config it extends. Missing or false `strict` is a finding; individual `strictXxx: false` overrides are findings each.
````

- [ ] **Step 2: Write config-unchecked-index.md**

````markdown
---
title: Enable noUncheckedIndexedAccess
impact: HIGH
impactDescription: makes index access tell the truth about absence
tags: config, index-access
---

## Enable noUncheckedIndexedAccess

**Impact: HIGH (makes index access tell the truth about absence)**

Without this flag, `arr[i]` and `record[key]` type as `T` even when the element does not exist, which is exactly how out-of-bounds and missing-key bugs pass review. With it, index access types as `T | undefined` and the compiler forces the check the runtime always required.

**Incorrect (the type claims presence the runtime does not guarantee):**

```typescript
const first = rows[0] // typed Row, is undefined for an empty result
render(first.id)
```

**Correct (with the flag on, absence must be handled):**

```typescript
const first = rows[0] // typed Row | undefined
if (!first) return renderEmpty()
render(first.id)
```

**Detection:** Read `tsconfig.json`: `noUncheckedIndexedAccess` absent or false is a finding. It is not part of `strict`, so check it explicitly.
````

- [ ] **Step 3: Write config-exact-optional.md**

````markdown
---
title: Enable exactOptionalPropertyTypes
impact: MEDIUM
impactDescription: distinguishes a missing property from one explicitly set to undefined
tags: config, optional
---

## Enable exactOptionalPropertyTypes

**Impact: MEDIUM (distinguishes a missing property from one explicitly set to undefined)**

Without the flag, `{ retries?: number }` accepts `{ retries: undefined }`, which spreads and serializes differently from an absent key (`'retries' in obj`, `Object.keys`, JSON output). APIs that distinguish "not provided" from "explicitly cleared" break silently.

**Incorrect (explicit undefined sneaks into an optional slot):**

```typescript
const opts: RetryOpts = { retries: undefined } // accepted without the flag
JSON.stringify(opts) // '{}' vs '{"retries":null}' surprises downstream
```

**Correct (with the flag, absence is expressed by omission):**

```typescript
const opts: RetryOpts = {} // retries genuinely absent
```

**Detection:** Read `tsconfig.json`: `exactOptionalPropertyTypes` absent or false is a finding, severity Medium.
````

- [ ] **Step 4: Write config-skiplibcheck.md**

````markdown
---
title: skipLibCheck may speed up third-party types, never hide first-party errors
impact: MEDIUM
impactDescription: your own declaration files must stay inside the checked perimeter
tags: config, declarations
---

## skipLibCheck may speed up third-party types, never hide first-party errors

**Impact: MEDIUM (your own declaration files must stay inside the checked perimeter)**

`skipLibCheck: true` skips ALL `.d.ts` files, including the ones this repository authors. That is an acceptable trade for `node_modules` compile time, but hand-written declarations and generated API types silently stop being checked. Keep first-party `.d.ts` content in `.ts` files where possible, or accept the flag knowingly with a comment.

**Incorrect (first-party declarations drift unchecked):**

```typescript
// src/types/api.d.ts, skipped by skipLibCheck, contradicts the runtime
declare interface ApiUser { id: number }
```

**Correct (first-party types live in checked .ts modules):**

```typescript
// src/types/api.ts, always checked
export interface ApiUser { id: string }
```

**Detection:** If `skipLibCheck` is true, `rg --files -g '*.d.ts' -g '!node_modules'`: each first-party `.d.ts` carrying hand-written declarations is a finding.
````

- [ ] **Step 5: Write exhaust-switch-never.md**

````markdown
---
title: Discriminated unions get a never assertion in the default branch
impact: MEDIUM
impactDescription: adding a variant becomes a compile error at every switch instead of a silent fallthrough
tags: exhaust, unions, never
---

## Discriminated unions get a never assertion in the default branch

**Impact: MEDIUM (adding a variant becomes a compile error at every switch instead of a silent fallthrough)**

A switch over a discriminated union that lacks a `never` default compiles cleanly when a new variant is added and simply does nothing for it at runtime. The `never` assertion turns every unhandled variant into a compile error listing exactly the switches to update.

**Incorrect (the new 'refunded' status falls through silently):**

```typescript
switch (order.status) {
  case 'pending': return queue(order)
  case 'paid': return ship(order)
}
```

**Correct (the compiler enumerates unhandled variants):**

```typescript
switch (order.status) {
  case 'pending': return queue(order)
  case 'paid': return ship(order)
  default: {
    const unhandled: never = order.status
    throw new Error(`unhandled status: ${unhandled}`)
  }
}
```

**Detection:** `rg -n 'switch \(' --type ts` on files defining union types; flag switches over a discriminant with no `never`-typed default.
````

- [ ] **Step 6: Write exhaust-satisfies-record.md**

````markdown
---
title: Use satisfies Record for complete lookup tables
impact: MEDIUM
impactDescription: a missing key becomes a compile error instead of an undefined handler
tags: exhaust, satisfies, records
---

## Use satisfies Record for complete lookup tables

**Impact: MEDIUM (a missing key becomes a compile error instead of an undefined handler)**

A lookup table keyed by a union should be provably complete. An annotation (`: Record<Kind, Handler>`) achieves that but widens the value types; `satisfies` checks completeness while preserving the precise inferred types of each entry.

**Incorrect (unchecked table, the new kind resolves to undefined):**

```typescript
const handlers = {
  created: onCreated,
  deleted: onDeleted,
}
handlers[event.kind](event) // 'updated' added to the union, not here
```

**Correct (satisfies proves completeness, inference stays precise):**

```typescript
const handlers = {
  created: onCreated,
  updated: onUpdated,
  deleted: onDeleted,
} satisfies Record<EventKind, (e: AppEvent) => void>
```

**Detection:** Reading heuristic: object literals indexed by a union-typed key (`table[x.kind]`) without `satisfies` or a `Record` annotation.
````

- [ ] **Step 7: Write generics-constraint.md**

````markdown
---
title: Constrain type parameters on public APIs
impact: MEDIUM
impactDescription: an unconstrained T pushes impossible types and bad inference onto every caller
tags: generics, constraints
---

## Constrain type parameters on public APIs

**Impact: MEDIUM (an unconstrained T pushes impossible types and bad inference onto every caller)**

An unconstrained `<T>` on an exported function accepts types the implementation cannot actually handle, and gives callers `unknown`-quality inference on the way out. Constrain the parameter to what the implementation truly requires, and let inference flow from a value argument whenever possible.

**Incorrect (T admits primitives the implementation will crash on):**

```typescript
export function merge<T>(base: T, patch: Partial<T>): T {
  return { ...base, ...patch } // spread of a number compiles here
}
```

**Correct (the constraint states the real requirement):**

```typescript
export function merge<T extends object>(base: T, patch: Partial<T>): T {
  return { ...base, ...patch }
}
```

**Detection:** `rg -n 'export function \w+<T[,>]' --type ts`; flag exported generics with bare `<T>` whose bodies spread, index, or iterate the value.
````

- [ ] **Step 8: Write generics-type-guards.md**

````markdown
---
title: A type predicate must verify the whole shape it claims
impact: HIGH
impactDescription: an unsound guard converts unknown to a trusted type on false evidence
tags: generics, type-guards, predicates
---

## A type predicate must verify the whole shape it claims

**Impact: HIGH (an unsound guard converts unknown to a trusted type on false evidence)**

`x is T` is a promise the compiler takes on faith: after a true return, `x` IS `T` everywhere downstream. A guard that checks one field and claims the whole shape is a cast wearing a disguise. Check every field the consuming code relies on, or delegate to a schema's `safeParse` so the check and the type cannot drift.

**Incorrect (one field checked, whole shape claimed):**

```typescript
function isUser(x: unknown): x is User {
  return typeof x === 'object' && x !== null && 'id' in x
}
// passes for { id: 1 }; user.email.toLowerCase() then throws
```

**Correct (the schema is the guard; check and type share one source):**

```typescript
function isUser(x: unknown): x is User {
  return UserSchema.safeParse(x).success
}
```

**Detection:** `rg -n '\): \w+ is ' --type ts`; read each predicate body and compare the checks against the claimed type's required fields.
````

- [ ] **Step 9: Verify the full rule set**

Run: `ls plugins/typescript-development/skills/type-safety-rules/rules/ | grep -v '^_' | wc -l`
Expected: `20`. Cross-check the 20 filenames against the Quick Reference list in SKILL.md: they must match exactly.

---

### Task 5: `type-safety-auditor` agent

**Files:**
- Create: `plugins/typescript-development/agents/type-safety-auditor.md`

**Interfaces:**
- Consumes: the skill name `type-safety-rules` and the 20 rule ids from Tasks 1 to 4.
- Produces: the agent reference `typescript-development:type-safety-auditor` and its JSON findings format (`rule`, `severity`, `file`, `line`, `confidence`, `issue`, `fix`, plus `positives` and `score` with keys `any_hygiene`, `cast_discipline`, `config_strictness`, `boundary_validation`, `overall`). Tasks 6, 7, and 8 spawn this agent and rely on this format.

- [ ] **Step 1: Write the agent file**

````markdown
---
name: type-safety-auditor
description: >
  Adversarial TypeScript type-safety reviewer. Hunts type-system erosion: any leakage, unsound casts, missing runtime validation at boundaries, assertion abuse, tsconfig strictness drift, non-exhaustive handling, and unsound generics or type guards.
  TRIGGER WHEN: reviewing TypeScript changes or codebases for type safety, auditing strict-mode compliance, or hunting unsound types before a release.
  DO NOT TRIGGER WHEN: style and naming review (use the typescript-write skill), React performance (use react-development:react-performance-optimizer), or dead-code detection (use the knip skill).
tools: Read, Write, Glob, Grep, Bash
model: inherit
color: blue
---

# TypeScript Type-Safety Auditor

Adversarial reviewer with one charter: find the places where the type system stops telling the truth. Assume every `any`, cast, suppression, and assertion is hiding a bug until the surrounding code proves otherwise.

**Scope guard.** Type safety only. Style and naming belong to `typescript-write`, performance to `react-development`, dead code to `knip`. Note out-of-scope observations in one line each; never expand them.

<core_philosophy>
- The compiler is the first reviewer: anything that silences it must justify itself
- An unvalidated boundary makes every downstream type a lie
- `unknown` plus narrowing beats `any`; a schema beats both
- Severity follows blast radius: an `any` on an exported surface outranks one in a test helper
</core_philosophy>

## Knowledge base

Load the `typescript-development:type-safety-rules` skill and use its 20 rules as the audit checklist. Cite rule ids in findings (e.g. "Violates cast-double"). Consult `typescript-development:mastering-typescript` references for deep type-system questions. Both skills ship in this plugin, so they are always installed alongside this agent.

## Workflow

1. **Config first**: read `tsconfig.json` and every config it extends. Record findings for config-strict, config-unchecked-index, config-exact-optional, config-skiplibcheck.
2. **Mechanical sweep**: run the detection greps below. Each hit is a candidate, not a finding.
3. **Boundary pass**: locate modules touching HTTP, queues, storage, and env access; verify schema validation on every ingress (boundary-http, boundary-queue, boundary-storage, boundary-env).
4. **Read flagged files**: confirm or dismiss each candidate in context; assign severity and confidence.
5. **Report** in the output format below.

## Detection greps

```bash
rg -n ': any\b|<any>|as any\b' --type ts --glob '!*.d.ts'
rg -n 'as unknown as' --type ts
rg -n '@ts-ignore|@ts-nocheck' --type ts
rg -n '\w+!(\.|\)|,|;)' --type ts
rg -n 'JSON\.parse\(|\.json\(\)' --type ts
rg -n 'process\.env\.' --type ts
rg -n '\): \w+ is ' --type ts
rg -n '= any>' --type ts
```

## Severity calibration

| Severity | Criteria |
|----------|----------|
| Critical | Unvalidated external input flowing into typed code (boundary rules); `any` or unsound cast on a shared or exported surface |
| High | `as unknown as`, `@ts-ignore`, unsound type guards, `strict` off, `any` generic defaults |
| Medium | Unjustified non-null assertions, missing exhaustiveness, missing strict sub-flags (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`) |
| Low | `any` confined to test helpers, missed `as const` or `satisfies` opportunities, generic constraint hygiene |

## Output format

For each finding: rule id, severity, file:line, confidence (0-100), what breaks at runtime, concrete fix with a code example. List what is done well (typed boundaries, exhaustive switches, strict config) under Positives. End with structured JSON:

```json
{
  "findings": [
    { "rule": "boundary-http", "severity": "Critical", "file": "src/api/client.ts", "line": 42, "confidence": 90, "issue": "...", "fix": "..." }
  ],
  "positives": ["..."],
  "score": { "any_hygiene": 0, "cast_discipline": 0, "config_strictness": 0, "boundary_validation": 0, "overall": 0 }
}
```

Scores are 0-10. When spawned by a review pipeline, write findings to the output path given in the prompt using the pipeline's structured format, keeping the rule-id citations.
````

- [ ] **Step 2: Verify**

Run: `head -15 plugins/typescript-development/agents/type-safety-auditor.md`
Expected: frontmatter shows `name: type-safety-auditor`, `model: inherit`, `color: blue`, description contains both TRIGGER WHEN and DO NOT TRIGGER WHEN. Confirm no dash-aside anywhere in the file: `grep -nE ' -- |—' plugins/typescript-development/agents/type-safety-auditor.md` returns nothing.

---

### Task 6: `/review-typescript` command

**Files:**
- Create: `plugins/typescript-development/commands/review-typescript.md`

**Interfaces:**
- Consumes: the agent `typescript-development:type-safety-auditor` and its findings JSON (Task 5); the 20 rule ids (Tasks 1 to 4).
- Produces: the command `/typescript-development:review-typescript` and the report path `.ts-review/report.md`.

- [ ] **Step 1: Write the command file**

````markdown
---
description: >
  TypeScript type-safety review: any leakage, unsound casts, boundary validation, tsconfig strictness, exhaustiveness, and generics soundness. Outputs an actionable markdown report.
  TRIGGER WHEN: the user asks to review TypeScript for type safety, strictness, unsound types, or missing runtime validation.
  DO NOT TRIGGER WHEN: style review (use typescript-write), React performance (use /react-development:review-react), or dead-code detection (use the knip skill).
argument-hint: "[src-path] [--full]"
---

# TypeScript Type-Safety Review

You are a senior TypeScript type-safety auditor. Review TypeScript code for type-system erosion: any leakage, unsound casts, missing boundary validation, assertion abuse, configuration drift, exhaustiveness gaps, and unsound generics.

## CRITICAL RULES

1. **Type-safety-only scope.** Ignore style, naming, formatting, performance, and dead code. Focus on where the type system stops telling the truth.
2. **Run the agent.** Fire the type-safety-auditor agent with the full context.
3. **Write markdown report.** Output is `.ts-review/report.md`: an actionable checklist with scores, findings, and fix instructions.
4. **Never enter plan mode.** Execute immediately.

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
find src -type f -name "*.ts" -o -name "*.tsx" | head -80
```

Or use the path from `$ARGUMENTS` if provided.

If no TypeScript files are found, stop and say so.

## Step 1.5: Run Deterministic Ground Truth (if available)

```bash
npx tsc --noEmit --pretty false 2>/dev/null || true
npx eslint --format json "src/**/*.{ts,tsx}" 2>/dev/null || true
```

Pass both outputs to the agent. If the tools are unavailable, proceed without them and note it in the report.

## Step 2: Sample Key Files & Gather Context

Read a representative cross-section:
- `tsconfig.json` and every config it extends (always)
- Boundary modules: API clients, route handlers, queue consumers, storage access, env/config access
- 3-5 core domain modules with exported types
- Any first-party `.d.ts` files

## Step 3: Run Review Agent

```
Task:
  subagent_type: "typescript-development:type-safety-auditor"
  description: "TypeScript type-safety audit"
  prompt: |
    Audit the type safety of this TypeScript codebase.

    ## Scope
    [list of key files sampled]

    ## File Contents
    [paste tsconfig.json, boundary modules, and sampled core modules]

    ## Compiler Output (if available)
    [paste tsc --noEmit output, or "No compiler output available"]

    ## Linter Output (if available)
    [paste ESLint JSON report, or "No linter output available"]

    ## Type-Safety Rules Checklist (20 rules; flag violations by id)

    **1. Any Erosion (CRITICAL):** any-explicit (unknown plus narrowing over any), any-implicit-boundary (type JSON.parse and response.json() immediately), any-generic-default (never <T = any>)
    **2. Unsound Casts (CRITICAL):** cast-as-unsound (shape-changing as needs a runtime check), cast-double (as unknown as X is a bypass), cast-const-assertion (as const over widening annotations)
    **3. Boundary Validation (CRITICAL):** boundary-http (schema-parse payloads at the edge), boundary-queue (validate messages on receipt), boundary-storage (validate and version storage reads), boundary-env (one validated config module)
    **4. Assertion Abuse (HIGH):** assert-non-null (! needs justification or a fail-fast check), assert-ts-expect-error (@ts-expect-error with reason, never @ts-ignore)
    **5. Compiler Configuration (HIGH):** config-strict (strict true baseline), config-unchecked-index (noUncheckedIndexedAccess), config-exact-optional (exactOptionalPropertyTypes), config-skiplibcheck (never hide first-party errors)
    **6. Exhaustiveness (MEDIUM-HIGH):** exhaust-switch-never (never assertion in default), exhaust-satisfies-record (satisfies Record for lookup tables)
    **7. Generics Soundness (MEDIUM):** generics-constraint (constrain public type parameters), generics-type-guards (predicates verify the whole shape)

    ## Instructions
    Use the checklist as your primary audit framework. Cite rule ids in every finding (e.g. "Violates boundary-http"). Cross-check candidates against the compiler output: a tsc error near a grep hit raises confidence.

    For each finding: rule id, severity (Critical/High/Medium/Low), file + line, confidence (0-100), what breaks at runtime, concrete fix with a code example.
    Note what is done well.

    Return the structured JSON block from your output format at the end.
```

## Step 4: Generate Markdown Report

After the agent completes, create the `.ts-review/` directory and write `report.md`.

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
````

- [ ] **Step 2: Verify**

Run: `grep -nE ' -- |—' plugins/typescript-development/commands/review-typescript.md`
Expected: no output (the file contains no dash-asides). Then confirm the 20 rule ids in the checklist section match the filenames from Task 4 Step 9.

---

### Task 7: Wire the dimension into team-review

**Files:**
- Modify: `plugins/senior-review/commands/team-review.md` (five surgical edits: optional-dimensions paragraph near line 112, conditional table near line 117, detection snippet near line 136, display example near line 168, dimension-to-agent mapping near line 243)

**Interfaces:**
- Consumes: `typescript-development:type-safety-auditor` (Task 5), dimension id `ts-safety`.
- Produces: the `ts-safety` conditional dimension contract that Task 10's docs describe.

- [ ] **Step 1: Update the optional-dimensions paragraph**

Edit old_string (the paragraph's opening sentence):

```
Four of these dimensions live in plugins declared as `optionalDependencies` of `senior-review`: React performance (`react-development`), platform compliance (`platform-engineering`), abstraction (`abstraction-architect`), and testing quality (`testing`).
```

new_string:

```
Five of these dimensions live in plugins declared as `optionalDependencies` of `senior-review`: React performance (`react-development`), platform compliance (`platform-engineering`), abstraction (`abstraction-architect`), testing quality (`testing`), and TypeScript type safety (`typescript-development`).
```

In the same paragraph, edit old_string `Testing quality degrades differently from the other three:` to new_string `Testing quality degrades differently from the other four:`.

- [ ] **Step 2: Add the conditional-dimensions table row**

Insert a new row immediately after the **React project** row (the row whose agent is `react-development:react-performance-optimizer`):

```
| **TypeScript project** | Changed files match `\.tsx?$` AND `tsconfig.json` exists at the project root. Requires the `typescript-development` plugin: when it is not installed, skip and note it under Skipped instead of spawning (the spawn would fail) | TypeScript type safety | `typescript-development:type-safety-auditor` |
```

- [ ] **Step 3: Add the detection line to the bash snippet**

In the "Detection implementation" bash block, after the `# 2. Check for React` pair, insert:

```bash
# 2b. Check for a TypeScript project
echo "$CHANGED_FILES" | grep -qE '\.tsx?$' && [ -f tsconfig.json ] && echo "TS_PROJECT=true"
```

- [ ] **Step 4: Update the detection display example**

Edit the example's Detected line, old_string:

```
  - Detected: ui-races (6 .tsx files), react-perf (React project), distributed-flows (API routes + RabbitMQ), abstraction (diff adds 4 units)
```

new_string:

```
  - Detected: ui-races (6 .tsx files), react-perf (React project), ts-safety (TypeScript project), distributed-flows (API routes + RabbitMQ), abstraction (diff adds 4 units)
```

- [ ] **Step 5: Add the dimension-to-agent mapping row**

In the "Dimension-to-agent mapping" table, insert after the React performance row:

```
| TypeScript type safety | `typescript-development:type-safety-auditor` |
```

- [ ] **Step 6: Verify**

Run: `python scripts/lint_dependency_graph.py`
Expected: all checks pass. The new spawn reference resolves against the existing `typescript-development` entry in senior-review's `optionalDependencies`, and the skip note in the table row satisfies the degrade-notes check. Then `grep -c 'type-safety-auditor' plugins/senior-review/commands/team-review.md` returns `2` (table row + mapping row).

---

### Task 8: Wire Agent K into code-review

**Files:**
- Modify: `plugins/senior-review/commands/code-review.md` (insert a new section after Agent J; letters A through J plus B2 are taken, so the new agent is K)

**Interfaces:**
- Consumes: `typescript-development:type-safety-auditor` (Task 5).
- Produces: the Agent K block that Task 10's docs mention.

- [ ] **Step 1: Locate the end of the Agent J section**

Run: `grep -n '^### Agent\|^## ' plugins/senior-review/commands/code-review.md`
Find the heading that follows `### Agent J: Abstraction & Reuse Review (conditional)`. The new Agent K section is inserted immediately before that following heading.

- [ ] **Step 2: Check for agent roster references**

Run: `grep -n 'Agent [A-J]\b' plugins/senior-review/commands/code-review.md`
If any step enumerates the agents to spawn (a roster list or table outside the per-agent sections), mirror the Agent I entry there for Agent K. If the only references are the section headings and inline mentions, no extra edit is needed.

- [ ] **Step 3: Insert the Agent K section**

````markdown
### Agent K: TypeScript Type-Safety Review (conditional)

**Only run this agent if the diff touches `.ts` or `.tsx` files AND `tsconfig.json` exists at the project root.** On React projects both Agent I and Agent K run: the charters are orthogonal (performance vs type safety) and consolidation deduplicates any collision.

**Skip if the `typescript-development` plugin is not installed.** It is an `optionalDependency`, so the spawn fails with "Agent type not found" when it is absent. Report the dimension as skipped for that reason instead, so the gap is visible in the report rather than silent.

```
Agent tool call:
  - description: "TypeScript type-safety review for senior-review command"
  - subagent_type: "typescript-development:type-safety-auditor"
  - run_in_background: true
  - prompt: |
    Review the following TypeScript changes for type-system erosion.

    [Include shared instructions: Intent + Diff Scope]

    ## Changed Files
    [list of changed .ts/.tsx files]

    ## tsconfig
    [paste tsconfig.json and any extended configs]

    ## Full File Contents
    [paste full contents of each changed TypeScript file]

    ## Diff
    [paste the git diff output]

    ## Instructions
    Analyze the CHANGED TypeScript code for:
    1. **Any erosion**: explicit any, untyped JSON.parse and response.json() results, any generic defaults
    2. **Unsound casts**: shape-changing as casts without runtime checks, as unknown as bypasses
    3. **Boundary validation**: HTTP payloads, queue messages, storage reads, and env access reaching typed code without a schema parse or guard
    4. **Assertion abuse**: unjustified non-null assertions, @ts-ignore instead of @ts-expect-error with reason
    5. **Configuration drift**: strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes missing or weakened by this diff
    6. **Exhaustiveness**: discriminated-union switches without never defaults, lookup tables without satisfies
    7. **Generics soundness**: unconstrained exported type parameters, type predicates that do not verify the shape they claim

    Cite rule ids from the type-safety-rules skill in every finding.
    For each finding: severity (Critical/High/Medium/Low), file + line, confidence (0-100),
    description, concrete fix with a code example.
```
````

- [ ] **Step 4: Verify**

Run: `python scripts/lint_dependency_graph.py`
Expected: all checks pass (the new spawn site carries the skip note). Then `grep -n 'Agent K' plugins/senior-review/commands/code-review.md` shows the new section heading.

---

### Task 9: Marketplace manifest update

**Files:**
- Modify: `.claude-plugin/marketplace.json` (typescript-development entry, senior-review version, metadata version)

**Interfaces:**
- Consumes: all files created in Tasks 1 to 6 (their paths are registered here).
- Produces: the version numbers Task 11's export layer and Task 12's version-bump check rely on.

- [ ] **Step 1: Bump and extend the typescript-development entry**

Edit old_string:

```
enterprise-grade TypeScript mastery (type system, generics, React/NestJS integration, Zod validation, modern toolchain)",
      "version": "2.1.4",
```

new_string:

```
enterprise-grade TypeScript mastery (type system, generics, React/NestJS integration, Zod validation, modern toolchain), and a type-safety review layer: adversarial type-safety-auditor agent, 20-rule type-safety-rules skill, and /review-typescript command with tsc/ESLint ground truth",
      "version": "2.2.0",
```

- [ ] **Step 2: Register the new agent, skill, and command**

Edit old_string:

```
      "agents": [
        "./agents/typescript-engineer.md"
      ],
      "skills": [
        "./skills/typescript-write",
        "./skills/knip",
        "./skills/mastering-typescript"
      ]
    },
```

new_string:

```
      "agents": [
        "./agents/typescript-engineer.md",
        "./agents/type-safety-auditor.md"
      ],
      "skills": [
        "./skills/typescript-write",
        "./skills/knip",
        "./skills/mastering-typescript",
        "./skills/type-safety-rules"
      ],
      "commands": [
        "./commands/review-typescript.md"
      ]
    },
```

- [ ] **Step 3: Bump senior-review and extend its description**

Edit old_string:

```
and conditional reviewers for testing quality (the testing plugin's test-suite-auditor when installed, generic fallback otherwise), API contracts, and data migrations.
```

new_string:

```
and conditional reviewers for testing quality (the testing plugin's test-suite-auditor when installed, generic fallback otherwise), TypeScript type safety (the typescript-development plugin's type-safety-auditor when installed), API contracts, and data migrations.
```

Then edit old_string `"version": "7.2.0",` scoped by including the preceding description tail `logic-integrity reference).",` in the old_string, bumping to `"version": "7.3.0",`.

- [ ] **Step 4: Bump the marketplace version**

Edit old_string:

```
    "version": "18.0.0"
  },
```

new_string:

```
    "version": "18.1.0"
  },
```

- [ ] **Step 5: Verify**

Run: `python -c "import json; m=json.load(open('.claude-plugin/marketplace.json')); ts=[p for p in m['plugins'] if p['name']=='typescript-development'][0]; sr=[p for p in m['plugins'] if p['name']=='senior-review'][0]; assert ts['version']=='2.2.0' and sr['version']=='7.3.0' and m['metadata']['version']=='18.1.0' and './commands/review-typescript.md' in ts['commands'] and './agents/type-safety-auditor.md' in ts['agents'] and './skills/type-safety-rules' in ts['skills']; print('manifest ok')"`
Expected: `manifest ok`. Then `python scripts/lint_dependency_graph.py` passes.

---

### Task 10: Documentation updates

**Files:**
- Modify: `docs/plugins/typescript-development.md`
- Modify: `docs/plugins/senior-review.md`
- Modify: `README.md` (only if it describes typescript-development's capabilities; check first)

**Interfaces:**
- Consumes: everything above; documents the shipped surface.

- [ ] **Step 1: Extend docs/plugins/typescript-development.md**

Update the intro blockquote to mention the review layer. Add under `## Agents` (after the typescript-engineer section):

````markdown
### `type-safety-auditor`

Adversarial TypeScript type-safety reviewer. Hunts type-system erosion: any leakage, unsound casts, missing runtime validation at boundaries, assertion abuse, tsconfig strictness drift, exhaustiveness gaps, and unsound generics or type guards. Spawned by `/senior-review:team-review` (dimension `ts-safety`) and `/senior-review:code-review` (Agent K) when this plugin is installed.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Type-safety review of TypeScript changes or codebases, strict-mode compliance audits, pre-release soundness checks |

**Invocation:**
```
Use the type-safety-auditor agent to audit [path] for type-safety issues
```
````

Add under `## Skills`:

```markdown
### `type-safety-rules`

20 review-oriented type-safety rules across 7 categories (any erosion, unsound casts, boundary validation, assertion abuse, compiler configuration, exhaustiveness, generics soundness), one file per rule with incorrect/correct examples and detection hints. The audit checklist of `type-safety-auditor`; also usable standalone.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Type-safety review checklists, hardening existing TypeScript, rule-by-rule guidance |
```

Add a `## Commands` section (the doc has none today):

```markdown
## Commands

### `/typescript-development:review-typescript`

Type-safety review with deterministic ground truth: detects diff vs full scope, runs `tsc --noEmit` and ESLint when available, spawns `type-safety-auditor` with the 20-rule checklist, and writes an actionable report to `.ts-review/report.md`.

Arguments: `[src-path] [--full]`
```

- [ ] **Step 2: Extend docs/plugins/senior-review.md**

Run: `grep -n 'React performance' docs/plugins/senior-review.md` to locate where conditional dimensions are listed, and mirror the React entries with:

```
TypeScript type safety (dimension `ts-safety` in team-review, Agent K in code-review): `typescript-development:type-safety-auditor`, activated when changed files match `\.tsx?$` and `tsconfig.json` exists; skipped with a note when the typescript-development plugin is not installed.
```

Adapt the exact phrasing to the surrounding list or table format found there.

- [ ] **Step 3: Check the README**

Run: `grep -n 'typescript-development' README.md`
If the README describes the plugin's capabilities, append one sentence to that description: `Includes a type-safety review layer (type-safety-auditor agent, 20-rule skill, /review-typescript command) that also powers the ts-safety dimension of /senior-review:team-review.` If the README only links to the plugin doc, no edit.

- [ ] **Step 4: Verify**

Run: `grep -nE ' -- |—' docs/plugins/typescript-development.md`
Expected: no new dash-asides introduced by the edits (pre-existing hits in untouched lines are acceptable; do not rewrite unrelated content).

---

### Task 11: Mirror into exports/vscode

**Files:**
- Modify: `exports/vscode/typescript-development/.github/` (new agent, prompt, and skill directory)
- Modify: `exports/vscode/senior-review/.github/` (updated team-review and code-review prompts)
- Modify: `exports/vscode/package.json` (regenerated contributions plus version bump)
- Modify: `exports/vscode/CHANGELOG.md`

**Interfaces:**
- Consumes: all plugin files from Tasks 1 to 8.
- Produces: the export state that `check_export.py` and `gen_extension_manifest.py --check` verify in Task 12.

- [ ] **Step 1: Load the downstream-exports skill**

Invoke the `downstream-exports` skill BEFORE touching any file under `exports/`. It holds the source map, the mirror adaptations (frontmatter shape, tool-name mapping, file naming like `*.agent.md` and `*.prompt.md`), and the divergences that must survive. Do not improvise the mirror from memory or from this plan: where this plan and that skill disagree about export mechanics, the skill wins.

- [ ] **Step 2: Mirror the typescript-development bundle**

Following the skill's adaptations: add the agent as `exports/vscode/typescript-development/.github/agents/type-safety-auditor.agent.md`, the command as a prompt file under `.github/prompts/`, and the skill directory `.github/skills/type-safety-rules/` (SKILL.md plus the full `rules/` directory). Mirror the senior-review bundle's updated `team-review` and `code-review` prompt files the same way.

- [ ] **Step 3: Regenerate the extension manifest and bump the extension**

Run: `python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py`
Then bump `version` in `exports/vscode/package.json` (minor bump: a new agent and prompt are contributed) and add a CHANGELOG entry describing the TypeScript type-safety review layer, following the format of the existing 18.0.0 entry.

- [ ] **Step 4: Verify**

Run: `python .claude/skills/downstream-exports/scripts/check_export.py && python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check`
Expected: both pass.

---

### Task 12: Full verification, single commit, push

**Files:**
- No new files. Stages everything from Tasks 1 to 11.

- [ ] **Step 1: Run all four CI checks**

```bash
python scripts/lint_dependency_graph.py
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/check_version_bumps.py origin/master
```

Expected: all pass. `check_version_bumps.py` sees the plugin changes alongside the 2.2.0, 7.3.0, and 18.1.0 bumps.

- [ ] **Step 2: Final dash-aside sweep over authored files**

Run: `grep -rnE ' -- |—' plugins/typescript-development/agents/type-safety-auditor.md plugins/typescript-development/commands/review-typescript.md plugins/typescript-development/skills/type-safety-rules/`
Expected: no output.

- [ ] **Step 3: Single commit**

```bash
git add plugins/typescript-development plugins/senior-review .claude-plugin/marketplace.json exports/vscode docs/plugins/typescript-development.md docs/plugins/senior-review.md README.md
git status
```

Confirm the status shows only intended paths, then:

```bash
git commit -m "Add the TypeScript type-safety review dimension at parity with React (v18.1.0)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 4: Push**

```bash
git push
```

Expected: the consistency CI on master runs the same four checks and passes.
