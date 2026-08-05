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
