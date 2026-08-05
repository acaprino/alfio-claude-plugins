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
